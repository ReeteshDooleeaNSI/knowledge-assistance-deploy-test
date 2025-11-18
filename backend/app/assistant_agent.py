from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timezone
from typing import Any

from agents import Agent, RunContextWrapper, function_tool
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
)
from dotenv import load_dotenv

from .zoho_auth import ZohoAuth
from .zoho_client import ZohoDeskClient

load_dotenv()

KNOWLEDGE_VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

KNOWLEDGE_ASSISTANT_INSTRUCTIONS = """
Vous êtes un agent conversationnel qui aide les agents du support client d'Holson à répondre rapidement et précisément aux demandes concernant les tickets Zoho Desk.

Lorsque vous avez besoin d'informations détaillées sur le ticket le plus récent d'un client, utilisez l'outil suivant :
- Outil : get_zoho_ticket(contact_name, email)
- Utilisez-le uniquement si la demande de l'agent nécessite des informations sur un ticket, ou si vous n'avez pas déjà le détail du dernier ticket.

WORKFLOW DE RECHERCHE DE DOCUMENTS (file_search) :
1. TOUJOURS identifier l'immatriculation dans le ticket Zoho (format: GH-XXX-XX ou similaire)
   - L'immatriculation peut être mentionnée dans le sujet, la description, ou les conversations du ticket
   - Si l'immatriculation n'est pas trouvée, demandez à l'agent de la fournir
2. TOUJOURS filtrer les recherches sur "immat" (immatriculation) avant d'utiliser file_search
   - Les documents sont organisés par immatriculation dans le vector store
   - Filtrer par immatriculation garantit que vous ne récupérez que les documents pertinents pour ce véhicule/client
3. Utiliser file_search uniquement après avoir identifié l'immatriculation
   - Cela permet de trouver rapidement les documents liés au véhicule concerné

Votre objectif est de donner des réponses précises, synthétiques et faciles à utiliser pour traiter les demandes liées aux tickets et à l'historique client. Posez des questions de clarification à l'agent si nécessaire. Utilisez l'outil get_zoho_ticket chaque fois qu'il est utile d'obtenir ou de vérifier un ticket dans Zoho Desk.

Répondez en texte brut, sauf si l'agent demande un format spécifique.
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


def extract_conversation_snippet(conversations: list[dict[str, Any]]) -> tuple[str, str]:
    """Extract last update time and snippet from most recent conversation."""
    if not conversations:
        return "N/A", "No updates"
    
    most_recent = max(
        conversations,
        key=lambda c: c.get("modifiedTime", c.get("createdTime", "")),
        default={}
    )
    
    last_update_time = format_datetime(
        most_recent.get("modifiedTime") or most_recent.get("createdTime")
    )
    
    content = most_recent.get("content", "")
    if isinstance(content, str):
        plain_text = _strip_html(content)
        snippet = plain_text[:100].strip()
        if len(plain_text) > 100:
            snippet += "..."
    else:
        plain_text = _strip_html(str(content) if content else "")
        snippet = plain_text[:100].strip() if plain_text else "No content"
    
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


def extract_ticket_data(ticket: dict[str, Any]) -> dict[str, Any]:
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
    
    contact = ticket.get("contact", {})
    if isinstance(contact, dict):
        first_name = contact.get("firstName", "")
        last_name = contact.get("lastName", "")
        contact_name = f"{first_name} {last_name}".strip() or "Unknown"
        account_name = contact.get("accountName", contact.get("account", {}).get("accountName", "N/A"))
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
    
    conversations = ticket.get("conversations", [])
    last_update_time, last_update_snippet = extract_conversation_snippet(conversations)
    
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
                                    label=f"Overdue {ticket_data['overdueBy']}",
                                    color="danger",
                                )
                                if ticket_data["overdue"] and ticket_data["overdueBy"]
                                else Badge(
                                    label="On time",
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
                            Caption(value=f"Last update • {ticket_data['lastUpdateTime']}"),
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
                            Caption(value="Due"),
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
                            Caption(value="Department"),
                            Spacer(),
                            Text(value=ticket_data["departmentName"], size="sm", maxLines=1),
                        ]
                    ),
                    Row(
                        children=[
                            Caption(value="Modified"),
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
                        label="Open in Zoho Desk",
                        style="primary",
                        onClickAction={
                            "type": "ticket.open",
                            "payload": {"id": ticket_data["ticketId"], "url": ticket_data["webUrl"]},
                        },
                    ),
                    Button(
                        label="Add note",
                        variant="outline",
                        onClickAction={
                            "type": "ticket.add_note",
                            "payload": {"id": ticket_data["ticketId"]},
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
) -> dict[str, Any]:
    """Get the latest ticket from Zoho Desk, optionally filtered by account name or email.

    Args:
        contact_name: Optional. Filter tickets by account name (company/client name).
        email: Optional. Filter tickets by contact email address.
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
        
        ticket = await client.get_latest_ticket(contact_name=contact_name, email=email)
        
        if not ticket:
            search_term = email or contact_name or ""
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
        
        ticket_data = extract_ticket_data(ticket)
        
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


assistant_agent = Agent[AgentContext](
   #model="gpt-5.1-chat-latest",
    model="gpt-4.1-mini",
    name="Federal Reserve Knowledge Assistant",
    instructions=KNOWLEDGE_ASSISTANT_INSTRUCTIONS,
    tools=[build_file_search_tool(), get_zoho_ticket], #mendatory_tool
)

title_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Thread Title Generator",
    instructions="Generate a concise, descriptive title (3-6 words) for the conversation thread based on the user's message. Return only the title text, nothing else.",
)
