from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ZOHO_ORG_ID = os.getenv("ZOHO_ORG_ID")

ZOHO_ACCOUNTS_URL = "https://accounts.zoho.eu"
ZOHO_DESK_API_URL = "https://desk.zoho.eu/api/v1"


class ZohoAuth:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.client_id = client_id or ZOHO_CLIENT_ID
        self.client_secret = client_secret or ZOHO_CLIENT_SECRET
        self.refresh_token = refresh_token or ZOHO_REFRESH_TOKEN
        self._access_token: str | None = None

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError(
                "ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_REFRESH_TOKEN must be set"
            )

    async def get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token",
                data={
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    def get_headers(self, org_id: str | None = None) -> dict[str, str]:
        if not self._access_token:
            raise RuntimeError("Access token not available. Call get_access_token() first.")
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self._access_token}",
        }
        
        if org_id or ZOHO_ORG_ID:
            headers["orgId"] = org_id or ZOHO_ORG_ID or ""
        
        return headers

