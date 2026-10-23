import asyncio
import json
import socket
import subprocess
import sys
import time

import pytest
pytest.importorskip("mcp")
import httpx2
from mcp import Client, StdioServerParameters
from agentvisa.api import ActionBody
from agentvisa.mcp_server import GatewayClient, GatewayCallError, create_mcp

TOKEN = "agent-" + "x" * 40


def action(**changes):
    return ActionBody(**{"request_id": "one", "visa_id": "v", "tool": "search_products",
                         "resource": "catalog:monitors", "arguments": {"query": "monitor"}, **changes})


def test_fixed_endpoint_identity_and_payload():
    def handle(request):
        assert str(request.url) == "http://127.0.0.1:8000/execute"
        assert request.headers["Authorization"] == "Bearer " + TOKEN
        assert json.loads(request.content) == action().model_dump()
        return httpx2.Response(200, json={"request_id": "one", "visa_id": "v", "decision": "ALLOW", "executed": True})
    client = GatewayClient("http://127.0.0.1:8000", TOKEN, transport=httpx2.MockTransport(handle))
    assert asyncio.run(client.execute(action()))["executed"]


@pytest.mark.parametrize("url", ["http://example.com", "http://localhost", "https://user:pass@example.com", "https://example.com/path", "https://example.com?url=evil", "https://example.com#fragment", "file:///tmp/gateway", "https://example.com:0"])
def test_gateway_origin_restrictions(url):
    with pytest.raises(ValueError):
        GatewayClient(url, TOKEN)


@pytest.mark.parametrize("status", [301, 302, 307, 308, 401, 403, 413, 422, 500, 503])
def test_transport_failures_never_authorize_or_follow_redirects(status):
    requests = []
    def handle(request):
        requests.append(request)
        return httpx2.Response(status, headers={"Location": "https://attacker.example/steal"}, text="private upstream details")
    client = GatewayClient("https://gateway.example", TOKEN, transport=httpx2.MockTransport(handle))
    with pytest.raises(GatewayCallError) as error:
        asyncio.run(client.execute(action()))
    assert len(requests) == 1
    assert TOKEN not in str(error.value)
    assert "private upstream details" not in str(error.value)


@pytest.mark.parametrize("result", [
    {}, {"decision": "ALLOW", "executed": False},
    {"request_id": "different", "visa_id": "v", "decision": "ALLOW", "executed": True},
    {"request_id": "one", "visa_id": "v", "decision": "DENY", "executed": True},
])
def test_invalid_or_unbound_response(result):
    transport = httpx2.MockTransport(lambda _: httpx2.Response(200, json=result))
    with pytest.raises(GatewayCallError):
        asyncio.run(GatewayClient("https://gateway.example", TOKEN, transport=transport).execute(action()))


def test_timeout_reports_unknown_outcome():
    def handle(request):
        raise httpx2.ReadTimeout("sensitive upstream data", request=request)
    client = GatewayClient("https://gateway.example", TOKEN, transport=httpx2.MockTransport(handle))
    with pytest.raises(GatewayCallError, match="outcome unknown"):
        asyncio.run(client.execute(action()))


def test_oversized_request_never_sent():
    def handle(_):
        pytest.fail("oversized request must not reach the network")
    client = GatewayClient("https://gateway.example", TOKEN, transport=httpx2.MockTransport(handle))
    with pytest.raises(GatewayCallError, match="no request sent"):
        asyncio.run(client.execute(action(arguments={"query": "x" * 70000})))


def test_oversized_response_never_authorizes():
    transport = httpx2.MockTransport(lambda _: httpx2.Response(200, content=b"x" * 300000))
    with pytest.raises(GatewayCallError, match="outcome unknown"):
        asyncio.run(GatewayClient("https://gateway.example", TOKEN, transport=transport).execute(action()))


def test_mcp_surface_has_no_human_controls_and_rejects_extra_fields():
    def handle(_):
        pytest.fail("invalid MCP input must not reach gateway")
    server = create_mcp(GatewayClient("https://gateway.example", TOKEN, transport=httpx2.MockTransport(handle)))
    async def check():
        async with Client(server) as client:
            tools = await client.list_tools()
            assert [tool.name for tool in tools.tools] == ["execute_action"]
            result = await client.call_tool("execute_action", {"action": {**action().model_dump(), "agent_id": "admin"}})
            assert result.is_error
    asyncio.run(check())


def test_real_stdio_to_http_approval_replay_and_revocation(tmp_path):
    config_path = tmp_path / "config.json"
    subprocess.run([sys.executable, "-m", "agentvisa", "init", "--config", str(config_path)], check=True, capture_output=True)
    config = json.loads(config_path.read_text())
    config["database"] = str(tmp_path / "state.db")
    config_path.write_text(json.dumps(config))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    process = subprocess.Popen([sys.executable, "-m", "agentvisa", "serve", "--config", str(config_path), "--port", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with httpx2.Client(base_url=origin, timeout=5, trust_env=False) as http:
            for _ in range(100):
                try:
                    if http.get("/health").status_code == 200:
                        break
                except httpx2.ConnectError:
                    pass
                time.sleep(.05)
            else:
                pytest.fail("HTTP gateway failed to start")
            admin = {"Authorization": "Bearer " + config["admin_token"]}
            contract = http.post("/drafts", headers=admin, json={"mission": "Buy a monitor under $300.", "agent_id": "procurement"}).json()["contract"]
            visa = http.post("/visas", headers=admin, json=contract).json()["visa_id"]
            params = StdioServerParameters(command=sys.executable, args=["-m", "agentvisa.mcp_server"],
                                           env={"AGENTVISA_AGENT_TOKEN": next(iter(config["agent_tokens"])), "AGENTVISA_GATEWAY_URL": origin})
            async def exercise():
                async with Client(params) as mcp:
                    assert [tool.name for tool in (await mcp.list_tools()).tools] == ["execute_action"]
                    body = action(visa_id=visa).model_dump()
                    result = await mcp.call_tool("execute_action", {"action": body})
                    assert result.structured_content["decision"] == "ALLOW"
                    modified = {**body, "arguments": {"query": "monitors"}}
                    assert (await mcp.call_tool("execute_action", {"action": modified})).structured_content["decision"] == "DENY"
                    body.update(request_id="buy", tool="purchase", resource="vendor:approved", arguments={"product_id": "monitor-pro", "quantity": 1})
                    assert (await mcp.call_tool("execute_action", {"action": body})).structured_content["decision"] == "ASK_HUMAN"
                    http.post("/approvals", headers=admin, json={"agent_id": "procurement", "request_id": "buy", "approve": True}).raise_for_status()
                    assert (await mcp.call_tool("execute_action", {"action": body})).structured_content["executed"]
                    assert (await mcp.call_tool("execute_action", {"action": body})).structured_content["replayed"]
                    http.post(f"/visas/{visa}/revoke", headers=admin).raise_for_status()
                    body["request_id"] = "revoked"
                    assert (await mcp.call_tool("execute_action", {"action": body})).structured_content["decision"] == "DENY"
                    assert len(http.get("/control", headers=admin).json()["effects"]) == 2
            asyncio.run(exercise())
    finally:
        process.terminate()
        process.wait(timeout=10)
