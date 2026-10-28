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
{"agent_id":"procurement","request_id":"monitor-purchase-1","approve":true,"expected_fingerprint":"replace-with-64-character-fingerprint-from-inspect"}
```

The required `expected_fingerprint` must match the exact action returned by `/approvals/inspect`. Both approvals and rejections require it. Missing, null, malformed or mismatched fingerprints return 422 without changing review state. Legacy clients that omitted this field must be updated; the operator CLI already supplies it. Use false to reject. The agent retries the identical action after approval. Policy is rechecked, and subsequent successful retries return the stored result with `replayed: true`.

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

The standalone `examples/agent_client.py` uses only agent credentials and calls only the gateway. With `AGENTVISA_AGENT_TOKEN` set privately, run:

```sh
python examples/agent_client.py search --request-id monitor-search-1 --visa VISA_ID
python examples/agent_client.py status --request-id monitor-search-1
```

Search always submits the same fixed monitor-catalog query. The request ID is required; the example no longer generates a new ID on each launch. `--visa` may instead come from `AGENTVISA_VISA_ID`. Status needs no visa and sends only a GET. Set a trusted origin with `--url` before the subcommand if needed. Redirects and ambient proxies are disabled; response size is capped at 256 KiB. The five-second timeout applies per network operation, not to the full command.

After a timeout, preserve the exact original action and ID. Status can return a historical response or an absent snapshot; absence does not rule out an in-flight commit. Retrying search with the same ID and visa is idempotent. A genuinely new search needs a new ID. The example never automatically retries or changes IDs and is a small catalog example, not a general-purpose autonomous agent.

## HTTP request format

Nonempty request bodies require exactly one Content-Type header naming `application/json` or an `application/*+json` media type. Bodies must be UTF-8 JSON, at most 64 KiB, with no duplicate object keys (including escaped equivalents), nonfinite numbers, lone Unicode surrogates, or more than 64 nested containers. Chunked bodies follow the same rules. Empty bodies remain supported for routes such as revocation; schema-required bodies still undergo normal route validation.

Unsupported/missing media types return 415; malformed or ambiguous JSON returns a generic 400; oversized bodies return 413. Schema violations continue to return 422. These checks run before route authorization and state changes and do not echo submitted values. They do not create decision audit records; deployments needing boundary-failure telemetry must add redacted access monitoring. Body reading has a five-second total deadline measured with a monotonic clock from entry into the HTTP middleware. Each chunk consumes the same deadline; timeouts return a generic 408 before route execution. Disconnects stop reading without invoking the route. The body deadline ends before JSON validation and route execution; it does not cancel ongoing authorized work. It adds no rate limit, header-read timeout, connection cap, or total execution timeout.

## Visa inspection

Administrator-only GET `/visas/inspect?visa_id=VISA_ID` returns a bounded ancestor chain, `server_time`, inherited `effective_limits` and per-ancestor `blockers`. Unknown visas return 404; invalid identifiers return 422. Reads have no audit or policy side effects. See the operator inspection documentation for shared-budget and snapshot limitations. An empty blocker list is not an ALLOW decision.

Revocation and policy modification invalidate pending and approved reviews for the selected visa and all descendants in the same transaction as the policy change and audit event. Invalidated reviews disappear from outstanding lists and exact review inspection returns 404. Their stored request history remains, and retries cannot reuse the invalidated approval. The lifecycle audit event includes `invalidated_reviews`. Completed request replay still returns its original historical result without creating another effect.

## Agent request status

After an uncertain transport outcome, GET `/requests/status?request_id=monitor-purchase-1` using the same agent credential that submitted the action. The endpoint derives identity from the credential; it accepts no identity override. A request belonging to another identity is indistinguishable from a missing request (404). Administrator credentials cannot use this agent-only endpoint.

The result contains `request_id`, the canonical action `fingerprint`, current `state`, `last_response`, `server_time`, and review deadline/expiry fields. States are `pending`, `approved`, `rejected`, `invalidated` or `completed`. Expiry is reported separately without mutating the stored state. `last_response` is historical: an approved request still has its prior ASK_HUMAN response until the agent retries the identical action. Approval status alone is not fresh authorization; current policy and deadlines still apply at execution.

Status reads create no effects or audit events and return `Cache-Control: no-store`. A completed ALLOW describes an already committed simulated effect, even if the visa was later revoked. A 404 only means the request was absent from this read snapshot: another in-flight call may still commit. Preserve the same request ID and exact action when resolving uncertainty; never submit a new ID merely because status was missing. This endpoint does not cancel in-flight work or reserve authority. It is available through HTTP and the MCP bridge’s `get_request_status` tool.
