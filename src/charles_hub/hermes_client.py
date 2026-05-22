"""HTTP client for communicating with Hermes Agent gateway (:9119)."""
import httpx
from dataclasses import dataclass


@dataclass
class HermesResponse:
    success: bool
    data: dict | None
    error: str | None = None


class HermesClient:
    def __init__(self, base_url: str = "http://127.0.0.1:9119"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def send_message(self, agent: str, content: str,
                           chat_id: str, reply_to: str | None = None) -> HermesResponse:
        payload = {
            "agent": agent,
            "content": content,
            "chat_id": chat_id,
        }
        if reply_to:
            payload["reply_to"] = reply_to
        try:
            resp = await self._client.post(
                f"{self.base_url}/api/message",
                json=payload,
            )
            return HermesResponse(
                success=resp.is_success,
                data=resp.json() if resp.is_success else None,
                error=None if resp.is_success else resp.text,
            )
        except httpx.RequestError as e:
            return HermesResponse(success=False, data=None, error=str(e))

    async def query_agent_status(self, agent: str) -> HermesResponse:
        try:
            resp = await self._client.get(
                f"{self.base_url}/api/agent/{agent}/status",
            )
            return HermesResponse(
                success=resp.is_success,
                data=resp.json() if resp.is_success else None,
            )
        except httpx.RequestError as e:
            return HermesResponse(success=False, data=None, error=str(e))

    async def close(self):
        await self._client.aclose()
