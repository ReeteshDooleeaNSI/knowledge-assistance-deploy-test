from __future__ import annotations

import asyncio
import os
from typing import Any

from agents import Agent, RunContextWrapper, function_tool
from agents.models.openai_responses import FileSearchTool
from chatkit.agents import AgentContext
from chatkit.types import ProgressUpdateEvent
from dotenv import load_dotenv

from .zoho_auth import ZohoAuth
from .zoho_client import ZohoDeskClient

load_dotenv()

KNOWLEDGE_VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

KNOWLEDGE_ASSISTANT_INSTRUCTIONS = """
Vous êtes un agent conversationnel qui aide les agents du support client d'Holson à répondre rapidement et précisément aux demandes concernant les tickets Zoho Desk.

Lorsque vous avez besoin d'informations détaillées sur le ticket le plus récent d'un client, utilisez l'outil suivant :
- Outil : get_zoho_ticket(contact_name, email)
- Utilisez-le uniquement si la demande de l’agent nécessite des informations sur un ticket, ou si vous n’avez pas déjà le détail du dernier ticket.

Votre objectif est de donner des réponses précises, synthétiques et faciles à utiliser pour traiter les demandes liées aux tickets et à l’historique client. Posez des questions de clarification à l’agent si nécessaire. Utilisez l’outil get_zoho_ticket chaque fois qu’il est utile d’obtenir ou de vérifier un ticket dans Zoho Desk.

Répondez en texte brut, sauf si l’agent demande un format spécifique.
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
        print("ticket_id: ", ticket.get("id"))
        conversations = ticket.get("conversations", [])
        print("conversations: ", conversations)
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
