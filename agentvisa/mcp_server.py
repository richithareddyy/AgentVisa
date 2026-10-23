"""Agent-only MCP stdio bridge. The HTTP gateway remains the enforcement boundary."""
import asyncio
import json
import os
from urllib.parse import urlsplit
from typing import Any

import httpx2
from mcp.server import MCPServer

from .api import ActionBody


class GatewayCallError(RuntimeError):
    """Sanitized transport failure; never invent an authorization decision."""


class GatewayClient:
    def __init__(self, base_url: str, agent_token: str, *, transport=None):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in ("https", "http") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or any(c.isspace() for c in base_url)):
            raise ValueError("gateway URL must be a plain HTTPS origin or loopback HTTP origin")
        if parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "::1"):
            raise ValueError("plain HTTP is permitted only for literal loopback addresses")
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError("invalid gateway port")
        if len(agent_token) < 32 or not agent_token.isascii() or any(c.isspace() for c in agent_token):
            raise ValueError("a nonempty agent credential of at least 32 ASCII characters is required")
        self.endpoint = base_url.rstrip("/") + "/execute"
        self._token, self._transport = agent_token, transport

    async def execute(self, action: ActionBody) -> dict:
        # Fixed URL and credentials never come from tool arguments. No ambient proxy
        # credentials, redirects, automatic retries, or local tool fallbacks.
        payload = action.model_dump()
        try:
            encoded = json.dumps(payload, allow_nan=False).encode()
        except (ValueError, TypeError):
            raise GatewayCallError("Invalid action JSON; no request sent") from None
        if len(encoded) > 65536:
            raise GatewayCallError("Action exceeds gateway size limit; no request sent")
        try:
            async with asyncio.timeout(10):
                async with httpx2.AsyncClient(transport=self._transport, trust_env=False,
                                             follow_redirects=False, timeout=5.0) as client:
                    async with client.stream("POST", self.endpoint, content=encoded,
                                             headers={"Authorization": "Bearer " + self._token,
                                                      "Content-Type": "application/json"}) as response:
                        if response.status_code in (401, 403, 413, 422):
                            raise GatewayCallError(f"Gateway rejected request (HTTP {response.status_code}); no execution")
                        if response.status_code != 200:
                            raise GatewayCallError("Gateway result unavailable; execution outcome is unknown. Retry the same request_id")
                        data = bytearray()
                        async for chunk in response.aiter_bytes(chunk_size=16384):
                            data.extend(chunk)
                            if len(data) > 262144:
                                raise GatewayCallError("Gateway response too large; outcome unknown. Retry the same request_id")
            result = json.loads(data)
            if (not isinstance(result, dict) or result.get("decision") not in ("ALLOW", "DENY", "ASK_HUMAN")
                    or type(result.get("executed")) is not bool
                    or result["executed"] != (result["decision"] == "ALLOW")
                    or result.get("request_id") != action.request_id
                    or result.get("visa_id") != action.visa_id):
                raise ValueError("invalid decision response")
            return result
        except (httpx2.HTTPError, TimeoutError, ValueError, TypeError):
            raise GatewayCallError("Gateway result unavailable or invalid; outcome unknown. Retry the same request_id") from None


def create_mcp(client: GatewayClient) -> MCPServer:
    server = MCPServer("AgentVisa", instructions=(
        "Submit protected actions through execute_action. DENY and ASK_HUMAN do not execute. "
        "Only a human administrator can approve via the separate HTTP control API. "
        "On transport failure, outcome is unknown; retry the identical request_id and action. "
        "Never assume a failed response means the effect did not occur."))

    @server.tool(structured_output=True)
    async def execute_action(action: ActionBody) -> dict[str, Any]:
        """Authorize and execute one exact action through the AgentVisa gateway.

        Prices, destinations, identity, ancestry and approvals are checked by the
        gateway. Keep the same request_id for retries; new actions need new IDs.
        """
        return await client.execute(action)

    return server


def main():
    try:
        token = os.environ["AGENTVISA_AGENT_TOKEN"]
        client = GatewayClient(os.environ.get("AGENTVISA_GATEWAY_URL", "http://127.0.0.1:8000"), token)
    except (KeyError, ValueError):
        raise SystemExit("Configure AGENTVISA_AGENT_TOKEN and a valid AGENTVISA_GATEWAY_URL") from None
    # stdout is reserved for MCP protocol messages.
    create_mcp(client).run(transport="stdio")


if __name__ == "__main__":
    main()
