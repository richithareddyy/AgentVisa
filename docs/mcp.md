# MCP agent integration

The optional stdio bridge exposes two tools: `execute_action` forwards an action to the authenticated HTTP gateway, and `get_request_status` reads that agent’s stored request state. It has no direct tool adapters, database access code, human approval route, visa issuance or policy-editing tools.

```text
MCP host → stdio bridge (agent token) → HTTP gateway → policy + intent → simulated effect
Human operator ─────────────────────→ separate HTTP approval/control routes
```

## Install and start

```sh
python -m pip install -e '.[test,mcp]' -c requirements.lock
python -m agentvisa init
python -m agentvisa serve
```

If a private config already exists, skip `init`; it never overwrites credentials. Use the human administrator API to issue a visa for the configured `procurement` identity. The agent needs only its own token and the issued visa ID, never the entire private config.

In your MCP host, configure a stdio server with these fields (replace the placeholders locally):

```json
{
  "command": "/absolute/path/to/AgentVisa/.venv/bin/python",
  "args": ["-m", "agentvisa.mcp_server"],
  "env": {
    "AGENTVISA_GATEWAY_URL": "http://127.0.0.1:8000",
    "AGENTVISA_AGENT_TOKEN": "replace-with-agent-only-credential"
  }
}
```

The outer configuration format varies by host. This object describes the subprocess, not a universal host configuration file. Use the Python interpreter where the MCP extra was installed. Do not commit a config containing real credentials.

## Call the tool

Invoke `execute_action` with an `action` object:

```json
{
  "action": {
    "request_id": "monitor-search-1",
    "visa_id": "replace-with-issued-id",
    "tool": "search_products",
    "resource": "catalog:monitors",
    "arguments": {"query": "monitor"}
  }
}
```

The structured result preserves the gateway's ALLOW, DENY or ASK_HUMAN decision. ALLOW reports a committed simulated effect or replay of an earlier effect. ASK_HUMAN is not permission to execute elsewhere. A human reviews the exact stored action via `/control` and `/approvals`; the agent then retries the identical action and request ID. A changed action must use a new request ID.

To exercise a real SDK client, set `AGENTVISA_AGENT_TOKEN`, `AGENTVISA_GATEWAY_URL` and `AGENTVISA_VISA_ID` in the client environment, then run:

```sh
python examples/mcp_client.py --request-id monitor-search-1
python examples/mcp_client.py --request-id monitor-purchase-1 --purchase
```

The second command requests the $275 monitor and normally requires approval. Re-run it with the same ID after approval. The example has no administrator credentials and cannot approve itself.

## Failure semantics and security

The gateway origin and credential are configured by the operator, not tool arguments. The bridge refuses embedded URL credentials, paths, query strings and fragments. Plain HTTP is limited to literal loopback addresses; other origins require HTTPS. It disables ambient proxy settings, follows no redirects, limits request/response size and applies both network timeouts and a ten-second overall deadline.

HTTP 401/403/413/422 are reported as rejected requests. Other transport failures, malformed responses and timeouts have an **unknown execution outcome**: the gateway may have committed before the connection failed. The bridge returns an MCP tool error, never a fabricated authorization decision, and never executes locally as fallback. Retry the exact request ID to resolve the outcome. Cancellation likewise does not prove that an in-flight gateway call was rolled back.

This is a stdio bridge using MCP Python SDK 2.3.0. It is not an MCP Streamable HTTP endpoint or OAuth authorization server. Modern SDK clients were tested over real stdio; compatibility with every desktop host or older protocol version is not asserted. Tool effects remain simulations.

The stdio host/launcher is trusted to provision the correct agent credential. Run one bridge per identity. OS/container isolation must prevent agent access to administrator credentials, the database and protected providers; sharing an OS account alone does not create that isolation. Local transport resource exhaustion and a hostile process with filesystem access remain outside this prototype's guarantees.

## Sources

The implementation follows the official [SDK v2 API](https://py.sdk.modelcontextprotocol.io/whats-new/) and [stdio transport documentation](https://py.sdk.modelcontextprotocol.io/client/transports/). MCP's [authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) distinguishes environment-provisioned stdio credentials from HTTP authorization. These transport mechanisms complement, rather than replace, mission policy at the gateway.

## Check an uncertain outcome

Invoke `get_request_status` with:

```json
{"request":{"request_id":"monitor-purchase-1"}}
```

The bridge uses its configured agent credential and a fixed GET endpoint. No identity, URL or credential can be supplied in the tool arguments. A successful lookup returns `found: true` with the stored state and historical response. A 404 returns `found: false`, which does not rule out an in-flight commit. Authentication, transport, malformed/oversized responses and other HTTP failures return tool errors rather than a fabricated status.

Status responses are checked for request-ID binding, valid state/decision combinations, boolean execution flags, fingerprint format and consistent review deadline/expiry fields. Reads use the same bounded transport policy as execution: no proxies or redirects, a 256 KiB response cap, network timeouts and a ten-second overall deadline. This schema validation does not authenticate a compromised gateway’s claims.

An approved request still requires retrying the exact original action through `execute_action`; status lookup never executes or approves anything. A completed ALLOW is historical. Keep the original request ID and action when resolving an uncertain outcome.
