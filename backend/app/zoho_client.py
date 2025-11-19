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
            )
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
        limit: int = 1,
        org_id: str | None = None,
    ) -> dict[str, Any]:

        url=f"https://www.zohoapis.eu/crm/v7/functions/nsi_rd_getdeskticketbyaccountname/actions/execute?auth_type=apikey&zapikey=1003.f1aab887657143c4b44bdf9b08e40337.78f84abd7879879b61d7af3b87236ecf&accountName={account_name}"
        tickets_response = await self._request_url("GET", url)
        tickets_output = tickets_response.get("details", {}).get("output", {})
        return json.loads(tickets_output)

    async def get_latest_ticket(
        self,
        contact_name: str | None = None,
        email: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any] | None:
        print("contact_name: ", contact_name)
        print("email: ", email)
        if contact_name or email:
            print("contact_name or email: ", contact_name or email)
            response = await self.search_tickets_by_account(
                account_name=contact_name,
                email=email,
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

