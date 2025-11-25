from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from agents import Agent, RunContextWrapper, Runner, function_tool
from agents.models.openai_responses import FileSearchTool
from chatkit.agents import AgentContext
from chatkit.types import ProgressUpdateEvent
from chatkit.widgets import (
    Badge,
    Button,
    Caption,
    Card,
    Col,
    Divider,
    Row,
    Spacer,
    Text,
    Title,
    WidgetRoot,
    Form,
    Input,
)
from dotenv import load_dotenv

from .zoho_auth import ZohoAuth
from .zoho_client import ZohoDeskClient

load_dotenv()

KNOWLEDGE_VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

KNOWLEDGE_ASSISTANT_INSTRUCTIONS = """
Rôle : Agent conversationnel spécialisé pour assister les agents du support client Holson dans la gestion rapide et précise des demandes liées aux tickets Zoho Desk.

Instructions principales :
- Fournissez des réponses précises, synthétiques et faciles à utiliser pour traiter les demandes relatives aux tickets et à l’historique client.
- Posez des questions de clarification à l'agent si nécessaire pour garantir la complétude des informations.
- Écris un draft dans Zoho Desk que si on te le demande explicitement.

Outils disponibles :

1. Outil : get_zoho_ticket(contact_name, email)
   - Utilisez cet outil uniquement lorsque la demande nécessite des informations détaillées sur un ticket.
   - Employez-le chaque fois qu’il est utile pour obtenir ou vérifier un ticket dans Zoho Desk.

2. Documentation procédurale (ex : pneumatique)
   - Recherchez les informations dans les fichiers Zoho Learn suivants uniquement lorsque la demande concerne une procédure où l’immatriculation n’est pas requise :
     - entités-et-agences.html
     - commandes-et-livraisons.html
     - organisation.html
     - maintenances-et-services.html
     - administratif.html
     - aen-et-facturation.html
     - suivi-des-tâches.html

WORKFLOW DE RECHERCHE DE DOCUMENTS (file_search) :
1. Identifiez TOUJOURS l’immatriculation du véhicule (format : XX-XXX-XX ou similaire).
   - L’immatriculation peut être mentionnée dans le sujet, la description ou les conversations du ticket.
   - Si elle n’est pas trouvée, demandez-la à l’utilisateur.
2. Filtrez TOUJOURS les recherches sur « immat » (immatriculation) avant d’utiliser file_search.
   - Les documents sont organisés par immatriculation et nom client dans le vector store.
   - Ce filtrage garantit l’accès uniquement aux documents pertinents pour ce véhicule/client.
3. Utilisez file_search UNIQUEMENT APRÈS avoir identifié l’immatriculation.
   - Cela permet de cibler rapidement les documents liés au véhicule concerné.
   - Exception : Lorsque la demande concerne une procédure où l’immatriculation n’est pas requise (voir liste de fichiers ci-dessus).

Format de réponse : Répondez toujours en texte brut, sauf demande expresse de l’agent pour un autre format.

Output Verbosity :
- Limitez votre réponse à 2 courts paragraphes maximum, ou si la réponse doit être listée, utilisez 6 points ou moins, une ligne chacun.
- Privilégiez des réponses complètes et exploitables sans dépasser cette limite de longueur.

Philosophie :
- Privilégiez la clarté, la rapidité et le respect tout en respectant la limite de longueur ci-dessus.
- Ne rallongez pas la réponse uniquement pour marquer la politesse.
- Préférez la complétude des informations à un retour trop prématuré, même si la demande de l'utilisateur est brève, tant que cela reste dans la limite fixée.
- Si un outil retourne un Widget (comme un formulaire), retournez-le tel quel.
""".strip()


def build_file_search_tool() -> FileSearchTool:
    if not KNOWLEDGE_VECTOR_STORE_ID:
        raise RuntimeError(
            "KNOWLEDGE_VECTOR_STORE_ID is not set. See examples/knowledge_assistant/README.md for setup instructions."
        )
    return FileSearchTool(
        vector_store_ids=[KNOWLEDGE_VECTOR_STORE_ID],
        max_num_results=5,
    )


def format_datetime(dt_str: str | None) -> str:
    """Format Zoho datetime string to 'YYYY-MM-DD HH:MM UTC' format."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return dt_str


def calculate_overdue(due_date_str: str | None) -> tuple[bool, str]:
    """Calculate if ticket is overdue and by how much."""
    if not due_date_str:
        return False, ""
    
    try:
        due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if due_date > now:
            return False, ""
        
        delta = now - due_date
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            return True, f"{days} day{'s' if days != 1 else ''}"
        elif hours > 0:
            return True, f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return True, "Less than 1 hour"
    except (ValueError, AttributeError):
        return False, ""


def _strip_html(html_content: str) -> str:
    """Remove HTML tags and decode HTML entities to get plain text."""
    if not html_content:
        return ""
    
    text = html_content
    
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&apos;", "'")
    
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def extract_conversation_snippet(
    ticket: dict[str, Any]
) -> tuple[str, str]:
    """Extract last update time and snippet from ticket data."""
    conversations = ticket.get("conversations", [])
    
    if not conversations:
        last_update_time = format_datetime(ticket.get("modifiedTime"))
        return last_update_time, "No updates"
    
    most_recent = max(
        conversations,
        key=lambda c: c.get("modifiedTime", c.get("createdTime", "")),
        default={}
    )
    
    last_update_time = format_datetime(
        most_recent.get("modifiedTime") or most_recent.get("createdTime")
    )
    
    try:
        ticket_json = json.dumps(ticket, ensure_ascii=False, indent=2)
        print(ticket_json)
        input_text = f"Extract a concise summary (max 100 characters) from this ticket data:\n\n{ticket_json}"
        run = await Runner.run(snippet_agent, input=input_text)
        snippet = run.final_output.strip() if run.final_output else "No content"
        if len(snippet) > 100:
            snippet = snippet[:100].strip() + "..."
    except Exception as e:
        print(f"Failed to generate snippet with LLM: {e}")
        content = most_recent.get("content", "")
        if isinstance(content, str):
            plain_text = _strip_html(content)
        else:
            plain_text = _strip_html(str(content) if content else "")
        snippet = plain_text[:100].strip() if plain_text else "No content"
        if len(plain_text) > 100:
            snippet += "..."
    
    return last_update_time, snippet


def _extract_string_value(value: Any, default: str = "N/A") -> str:
    """Extract string value from potentially nested dict/object."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("name", value.get("label", value.get("value", default)))
    return str(value) if value else default


async def extract_ticket_data(
    ticket: dict[str, Any]
) -> dict[str, Any]:
    """Extract and format all ticket data needed for the widget."""
    ticket_id = str(ticket.get("id", ""))
    ticket_number = str(ticket.get("ticketNumber", "N/A"))
    subject = str(ticket.get("subject", "No subject"))
    status = _extract_string_value(ticket.get("status"), "Unknown")
    status_type = _extract_string_value(
        ticket.get("statusType") or ticket.get("statusTypeName"), "Unknown"
    )
    channel = _extract_string_value(ticket.get("channel"), "Unknown")
    product = _extract_string_value(
        ticket.get("product") or ticket.get("productName"), "N/A"
    )
    
    contact = ticket.get("contact") or {}
    if isinstance(contact, dict):
        first_name = contact.get("firstName", "")
        last_name = contact.get("lastName", "")
        contact_name = f"{first_name} {last_name}".strip() or "Unknown"
        
        account = contact.get("account") or {}
        account_name = contact.get("accountName") or account.get("accountName", "N/A")
    else:
        contact_name = "Unknown"
        account_name = "N/A"
    
    department = ticket.get("department", {})
    if isinstance(department, dict):
        department_name = department.get("name", "N/A")
    else:
        department_name = ticket.get("departmentName", "N/A")
    
    due_date_str = ticket.get("dueDate") or ticket.get("dueDateTime")
    due_date = format_datetime(due_date_str)
    overdue, overdue_by = calculate_overdue(due_date_str)
    
    modified_time = format_datetime(ticket.get("modifiedTime"))
    
    last_update_time, last_update_snippet = await extract_conversation_snippet(
        ticket
    )
    
    web_url = f"https://support.holson.fr/support/holson/ShowHomePage.do#Cases/dv/{ticket_id}"
    
    return {
        "ticketId": ticket_id,
        "ticketNumber": ticket_number,
        "subject": subject,
        "status": status,
        "statusType": status_type,
        "channel": channel,
        "product": product,
        "contactName": contact_name,
        "accountName": account_name,
        "departmentName": department_name,
        "dueDate": due_date,
        "overdue": overdue,
        "overdueBy": overdue_by,
        "lastUpdateTime": last_update_time,
        "lastUpdateSnippet": last_update_snippet,
        "modifiedTime": modified_time,
        "webUrl": web_url,
    }


def build_ticket_widget(ticket_data: dict[str, Any]) -> WidgetRoot:
    """Build the ticket widget card from ticket data."""
    return Card(
        key="zoho_ticket",
        size="sm",
        children=[
            Col(
                gap=2,
                children=[
                    Row(
                        children=[
                            Title(value=f"Ticket #{ticket_data['ticketNumber']}", size="sm"),
                            Spacer(),
                            (
                                Badge(
                                    label=f"En retard de {ticket_data['overdueBy']}",
                                    color="danger",
                                )
                                if ticket_data["overdue"] and ticket_data["overdueBy"]
                                else Badge(
                                    label="À temps",
                                    color="success",
                                )
                            ),
                        ]
                    ),
                    Text(value=ticket_data["subject"], maxLines=2),
                    Row(
                        gap=2,
                        children=[
                            Badge(label=ticket_data["status"], color="info"),
                            Badge(label=ticket_data["statusType"]),
                            Badge(label=ticket_data["channel"]),
                            Badge(label=ticket_data["product"]),
                        ]
                    ),
                ]
            ),
            Divider(flush=True),
            Col(
                gap=1,
                children=[
                    Row(
                        children=[
                            Caption(value=f"Dernière mise à jour • {ticket_data['lastUpdateTime']}"),
                        ]
                    ),
                    Text(value=ticket_data["lastUpdateSnippet"], size="sm", maxLines=2),
                ]
            ),
            Divider(),
            Col(
                gap=2,
                children=[
                    Row(
                        children=[
                            Caption(value="Contact"),
                            Spacer(),
                            Text(
                                value=f"{ticket_data['contactName']} • {ticket_data['accountName']}",
                                size="sm",
                                maxLines=1,
                            ),
                        ]
                    ),
                    Row(
                        children=[
                            Caption(value="Dû"),
                            Spacer(),
                            Text(
                                value=ticket_data["dueDate"],
                                size="sm",
                                color="danger" if ticket_data["overdue"] else "secondary",
                            ),
                        ]
                    ),
                    Row(
                        children=[
                            Caption(value="Département"),
                            Spacer(),
                            Text(value=ticket_data["departmentName"], size="sm", maxLines=1),
                        ]
                    ),
                    Row(
                        children=[
                            Caption(value="Modifié"),
                            Spacer(),
                            Text(value=ticket_data["modifiedTime"], size="sm"),
                        ]
                    ),
                ]
            ),
            Divider(),
            Row(
                children=[
                    Button(
                        label="Ouvrir dans Zoho Desk",
                        style="primary",
                        onClickAction={
                            "type": "ticket.open",
                            "payload": {"id": ticket_data["ticketId"], "url": ticket_data["webUrl"]},
                            "handler": "server",
                        },
                    ),
                    Button(
                        label="Ajouter une note",
                        variant="outline",
                        onClickAction={
                            "type": "tool",
                            "payload": {
                                "tool": "open_add_note_form",
                                "args": {"ticket_id": ticket_data["ticketId"]},
                            },
                        },
                    ),
                ]
            ),
        ]
    )

# @function_tool  
# async def mendatory_tool(ctx: RunContextWrapper[AgentContext]) -> bool:
    
#     """Call this tool before responding to the user.

#     Args:
#         none
#     """
#     await ctx.context.stream(
#         ProgressUpdateEvent(text="Loading a user profile...")
#     )
    
#     await asyncio.sleep(1)
#     print("Mendatory tool called")
#     return True


@function_tool
async def get_zoho_ticket(
    ctx: RunContextWrapper[AgentContext],
    contact_name: str | None = None,
    email: str | None = None,
    ticket_number: str | None = None,
) -> dict[str, Any]:
    """Get the latest ticket from Zoho Desk, optionally filtered by account name, email, or ticket number.

    Args:
        contact_name: Optional. Filter tickets by account name (company/client name).
        email: Optional. Filter tickets by contact email address.
        ticket_number: Optional. Filter tickets by ticket number (e.g., "101").
        If neither is provided, returns the most recent ticket.
    
    Returns:
        A dictionary containing ticket information including subject, status, contact details, conversations, etc.
    """
    try:
        await ctx.context.stream(
            ProgressUpdateEvent(text="Fetching ticket from Zoho Desk...")
        )
        
        auth = ZohoAuth()
        client = ZohoDeskClient(auth)
        
        ticket = await client.get_latest_ticket(contact_name=contact_name, email=email, ticket_number=ticket_number)
        
        if not ticket:
            search_term = ticket_number or email or contact_name or ""
            return {
                "success": False,
                "message": f"No ticket found{f' for: {search_term}' if search_term else ''}",
            }
        
        ticket_id = ticket.get("id")
        print("ticket_id: ", ticket_id)
        
        conversations = ticket.get("conversations", [])
        if not conversations and ticket_id:
            try:
                conversations_response = await client.get_ticket_conversations(ticket_id)
                conversations = conversations_response.get("data", [])
                ticket["conversations"] = conversations
            except Exception as e:
                print(f"Failed to fetch conversations: {e}")
        
        ticket_data = await extract_ticket_data(ticket)
        
        try:
            widget = build_ticket_widget(ticket_data)
            copy_text = f"Ticket #{ticket_data['ticketNumber']}: {ticket_data['subject']} - Status: {ticket_data['status']}"
            
            payload: Any
            try:
                payload = widget.model_dump()
            except AttributeError:
                payload = widget
            
            print("[ZohoTicket] widget payload", payload)
        except Exception as exc:
            print("[ZohoTicket] widget build failed", {"error": str(exc)})
            raise ValueError("Failed to build ticket widget.") from exc
        
        print("[ZohoTicket] streaming widget")
        try:
            await ctx.context.stream_widget(widget, copy_text=copy_text)
        except Exception as exc:
            print("[ZohoTicket] widget stream failed", {"error": str(exc)})
            raise ValueError("Failed to display ticket widget.") from exc
        
        print("[ZohoTicket] widget streamed")
        
        return {
            "success": True,
            "ticket": {
                "id": ticket.get("id"),
                "ticketNumber": ticket.get("ticketNumber"),
                "subject": ticket.get("subject"),
                "status": ticket.get("status"),
                "priority": ticket.get("priority"),
                "channel": ticket.get("channel"),
                "createdTime": ticket.get("createdTime"),
                "modifiedTime": ticket.get("modifiedTime"),
                "conversations": conversations,
                "contact": {
                    "id": ticket.get("contactId"),
                    "email": ticket.get("email"),
                    "firstName": ticket.get("contact", {}).get("firstName") if isinstance(ticket.get("contact"), dict) else None,
                    "lastName": ticket.get("contact", {}).get("lastName") if isinstance(ticket.get("contact"), dict) else None,
                } if ticket.get("contactId") else None,
                "description": ticket.get("description"),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch ticket from Zoho Desk",
        }


@function_tool
async def create_zoho_ticket_draft(
    ctx: RunContextWrapper[AgentContext],
    ticket_id: str,
    content: str,
    from_email_address: str | None = None,
) -> dict[str, Any]:
    """Create a draft reply for a Zoho Desk ticket.

    Args:
        ticket_id: The ID of the ticket to create a draft for.
        content: The content of the draft reply.
        from_email_address: Optional. The email address to send the reply from (must be a configured support email). 
                            If not provided, defaults to 'driver@holson.fr' or ZOHO_DEFAULT_FROM_EMAIL env var.
    """
    try:
        await ctx.context.stream(
            ProgressUpdateEvent(text="Creating draft reply in Zoho Desk...")
        )
        
        auth = ZohoAuth()
        client = ZohoDeskClient(auth)
        
        # Determine from_email_address
        if not from_email_address:
            from_email_address = os.getenv("ZOHO_DEFAULT_FROM_EMAIL", "driver@holson.fr")
        
        result = await client.create_ticket_draft(
            ticket_id, 
            content, 
            from_email_address=from_email_address
        )
        
        return {
            "success": True,
            "message": "Draft reply created successfully.",
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create draft reply.",
        }


@function_tool
async def open_add_note_form(
    ctx: RunContextWrapper[AgentContext],
    ticket_id: str,
) -> str:
    """Open a form to add a note to a ticket.
    
    Args:
        ticket_id: The ID of the ticket.
    """
    form = Form(
        key=f"add_note_form_inner_{ticket_id}",
        title="Ajouter une note",
        submitLabel="Ajouter",
        onSubmitAction={
            "type": "tool",
            "payload": {
                "tool": "add_zoho_ticket_note",
                "args": {"ticket_id": ticket_id},
            },
        },
        children=[
            Input(
                name="note_content",
                label="Note",
                placeholder="Entrez votre note ici...",
                multiline=True,
                required=True,
            ),
            Caption(value="Appuyez sur Entrée pour envoyer la note.", size="sm"),
        ],
    )
    
    # Wrap in Card because stream_widget expects a WidgetItem (Card or ListView)
    card = Card(
        key=f"add_note_card_{ticket_id}",
        children=[form]
    )
    
    await ctx.context.stream_widget(card)
    return "Formulaire d'ajout de note ouvert."


@function_tool
async def add_zoho_ticket_note(
    ctx: RunContextWrapper[AgentContext],
    ticket_id: str,
    note_content: str,
) -> dict[str, Any]:
    """Add a note (private comment) to a Zoho Desk ticket.

    Args:
        ticket_id: The ID of the ticket.
        note_content: The content of the note.
    """
    try:
        await ctx.context.stream(
            ProgressUpdateEvent(text="Adding note to Zoho Desk...")
        )
        
        auth = ZohoAuth()
        client = ZohoDeskClient(auth)
        
        result = await client.add_ticket_comment(ticket_id, note_content, is_public=False)
        
        return {
            "success": True,
            "message": f"Note ajoutée avec succès : \"{note_content}\"",
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to add note.",
        }


assistant_agent = Agent[AgentContext](
    model="gpt-5.1-chat-latest",
    #model="gpt-4.1-mini",
    name="Holson Zoho Desk Assistant",
    instructions=KNOWLEDGE_ASSISTANT_INSTRUCTIONS,
    tools=[build_file_search_tool(), get_zoho_ticket, create_zoho_ticket_draft, open_add_note_form, add_zoho_ticket_note], #mendatory_tool
)

title_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Thread Title Generator",
    instructions="Generate a concise title (3-6 words) for the conversation thread based on the user's message. The title should be a single sentence that captures the main point or intention of the conversation. Return only the title text, nothing else.",
)

snippet_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Conversation Snippet Generator",
    instructions="Extract a concise, informative snippet (maximum 100 characters) from the ticket content. Focus on the key information or main point of the threads of the conversation. Return only the snippet text in french, nothing else.",
)
