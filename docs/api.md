# API walkthrough

Run `python -m agentvisa init`, then `python -m agentvisa serve`. The private config contains an `admin_token` and agent-token-to-identity mapping. Keep administrator credentials out of agent clients. Authorize requests using `Authorization: Bearer <credential>`.

## Draft and issue

POST `/drafts` as administrator:

```json
{"mission":"Buy a monitor under $300.","agent_id":"procurement"}
```

Inspect/edit the returned `contract`; `requires_human_review` is true. Money is integer USD cents and bounds are inclusive. POST only that contract object to `/visas` as administrator and save the returned `visa_id`. The draft parser deliberately supports only its documented monitor-purchase grammar.

## Execute

POST `/execute` as the agent:

```json
{
  "request_id":"monitor-search-1",
  "visa_id":"replace-with-issued-id",
  "tool":"search_products",
  "resource":"catalog:monitors",
  "arguments":{"query":"monitor"}
}
```

For a purchase, use a new request ID, tool `purchase`, resource `vendor:approved`, and arguments `{"product_id":"monitor-pro","quantity":1}`. The server derives $275 from the catalog. With the default $250 threshold this returns ASK_HUMAN, including reason, checks, intent diagnostics, cost, impact and deadline. No effect exists yet.

## Human review and edits

Use administrator-only GET `/visas`, `/approvals` and `/audit/events` for bounded lists. GET `/approvals/inspect?agent=procurement&request_id=monitor-purchase-1` returns the exact action, mission, fingerprint and current review state. See [pagination](pagination.md). The legacy `/control` snapshot remains available for local diagnostics.

POST `/approvals` as administrator:

```json
{"agent_id":"procurement","request_id":"monitor-purchase-1","approve":true,"expected_fingerprint":"replace-with-64-character-fingerprint-from-control"}
```

The optional `expected_fingerprint` is checked against the stored action; the operator CLI always requires it. Omit the field only for legacy clients that do not implement this review check. Use false to reject. The agent retries the identical action after approval. Policy is rechecked, and subsequent successful retries return the stored result with `replayed: true`.

PUT the complete replacement contract to `/visas/{visa_id}` as administrator to edit policy. Mission and identity are immutable; changes require a new visa. Edits invalidate affected approvals. POST `/visas/{visa_id}/revoke` prevents new effects under the visa and descendants.

## Delegation

POST a full child contract to `/visas/{visa_id}/delegate` using the parent's agent credential. Keep mission/purpose, narrow allowed sets, retain forbidden sets, decrease depth and never increase bounds. Child credentials are independently provisioned in server configuration; delegation does not mint credentials.

## Status and retries

| Response | Meaning |
| --- | --- |
| 401/403 | Missing or wrong-role credential; no execution |
| 413/422 | Oversized/malformed input; no execution |
| 200 + DENY | Authorization denial; no execution |
| 200 + ASK_HUMAN | Pending review; no execution |
| 200 + ALLOW | Simulated effect committed, or prior result replayed |
| 503 | Store failure; execution not confirmed; retry the same request ID |

Correcting an action needs a new request ID. Never change IDs just to resolve an unknown execution outcome. GET `/audit/integrity` as administrator verifies the local hash chain. `/health` is public liveness with simulation mode only. `/control` is an unpaginated local development snapshot, not a production monitoring API.

The standalone `examples/agent_client.py` uses only agent credentials and calls only the gateway.

## HTTP request format

Nonempty request bodies require exactly one Content-Type header naming `application/json` or an `application/*+json` media type. Bodies must be UTF-8 JSON, at most 64 KiB, with no duplicate object keys (including escaped equivalents), nonfinite numbers, lone Unicode surrogates, or more than 64 nested containers. Chunked bodies follow the same rules. Empty bodies remain supported for routes such as revocation; schema-required bodies still undergo normal route validation.

Unsupported/missing media types return 415; malformed or ambiguous JSON returns a generic 400; oversized bodies return 413. Schema violations continue to return 422. These checks run before route authorization and state changes and do not echo submitted values. They do not create decision audit records; deployments needing boundary-failure telemetry must add redacted access monitoring. Body reading has a five-second total deadline measured with a monotonic clock from entry into the HTTP middleware. Each chunk consumes the same deadline; timeouts return a generic 408 before route execution. Disconnects stop reading without invoking the route. The body deadline ends before JSON validation and route execution; it does not cancel ongoing authorized work. It adds no rate limit, header-read timeout, connection cap, or total execution timeout.
