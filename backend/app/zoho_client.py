from __future__ import annotations

from typing import Any

import httpx
import json

from .zoho_auth import ZohoAuth, ZOHO_DESK_API_URL


class ZohoDeskClient:
    def __init__(self, auth: ZohoAuth) -> None:
        self.auth = auth

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        await self.auth.get_access_token()
        headers = self.auth.get_headers(org_id=org_id)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{ZOHO_DESK_API_URL}/{endpoint}",
                headers=headers,
                params=params,
                json=json_body,
            )
            
            if response.status_code >= 400:
                print(f"[ZohoClient] Request failed: {response.status_code} - {response.text}")
                
            response.raise_for_status()
            return response.json()

    async def _request_url(
        self,
        method: str,
        url: str,
    ) -> dict[str, Any]:

        print("url: ", url)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
            )
            response.raise_for_status()
            return response.json()

    async def get_tickets(
        self,
        limit: int = 1,
        sort_by: str = "modifiedTime",
        sort_order: str = "desc",
        contact_name: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "limit": limit,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        if contact_name:
            params["contactName"] = contact_name

        return await self._request("GET", "tickets", params=params, org_id=org_id)

    async def search_tickets_by_account(
        self,
        account_name: str | None = None,
        email: str | None = None,
        ticket_number: str | None = None,
        limit: int = 1,
        org_id: str | None = None,
    ) -> dict[str, Any]:

        # Construct URL with available parameters
        query_params = []
        if account_name:
            query_params.append(f"accountName={account_name}")
        if email:
            query_params.append(f"email={email}")
        if ticket_number:
            query_params.append(f"ticketNumber={ticket_number}")
            
        query_string = "&".join(query_params)
        
        url=f"https://www.zohoapis.eu/crm/v7/functions/nsi_rd_getdeskticketbyaccountname1/actions/execute?auth_type=apikey&zapikey=1003.f1aab887657143c4b44bdf9b08e40337.78f84abd7879879b61d7af3b87236ecf&{query_string}"
        tickets_response = await self._request_url("GET", url)
        tickets_output = tickets_response.get("details", {}).get("output", {})
        return json.loads(tickets_output)

    async def create_ticket_draft(
        self,
        ticket_id: str,
        content: str,
        from_email_address: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a draft email reply for a ticket.
        
        Args:
            ticket_id: The ID of the ticket
            content: The content of the draft reply
            from_email_address: Optional email address to send from
            org_id: Optional organization ID
        """
        body = {
            "channel": "EMAIL",
            "content": content,
            "contentType": "plainText",
        }
        
        if from_email_address:
            body["fromEmailAddress"] = from_email_address
            
        return await self._request(
            "POST", 
            f"tickets/{ticket_id}/draftReply",
            json_body=body,
            org_id=org_id
        )

    async def add_ticket_comment(
        self,
        ticket_id: str,
        content: str,
        is_public: bool = False,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a comment (note) to a ticket."""
        body = {
            "content": content,
            "isPublic": str(is_public).lower(),
            "contentType": "plainText",
        }
        
        return await self._request(
            "POST",
            f"tickets/{ticket_id}/comments",
            json_body=body,
            org_id=org_id
        )

    async def get_latest_ticket(
        self,
        contact_name: str | None = None,
        email: str | None = None,
        ticket_number: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any] | None:
        print("contact_name: ", contact_name)
        print("email: ", email)
        print("ticket_number: ", ticket_number)
        
        if contact_name or email or ticket_number:
            response = await self.search_tickets_by_account(
                account_name=contact_name,
                email=email,
                ticket_number=ticket_number,
                limit=1,
                org_id=org_id,
            )
        else:
            response = await self.get_tickets(
                limit=1,
                org_id=org_id,
            )
        print("response: ", response)
        return response

    async def get_ticket(self, ticket_id: str, org_id: str | None = None) -> dict[str, Any]:
        return await self._request("GET", f"tickets/{ticket_id}", org_id=org_id)

    async def get_ticket_conversations(self, ticket_id: str, org_id: str | None = None) -> dict[str, Any]:
        print("ticket_id: ", ticket_id)
        print("org_id: ", org_id)
        return await self._request("GET", f"tickets/{ticket_id}/conversations", org_id=org_id)

