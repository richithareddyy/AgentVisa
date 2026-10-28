# Human operator workflow

The operator CLI uses only authenticated human-control routes. It never calls `/execute` and never reads or writes the gateway database directly. It can use an administrator-only JSON file containing `admin_token`, or `AGENTVISA_ADMIN_TOKEN` from its environment. Do not put credentials in command-line arguments, source control or agent configuration.

For a local development session, the private config created by `python -m agentvisa init` is also accepted. Start the gateway in another terminal with `python -m agentvisa serve`.

All examples assume the repository root and activated virtual environment. Global flags precede the command. Add `--url https://your-gateway.example` before the command for a trusted remote origin; loopback `http://127.0.0.1:8000` is the default.

## Draft, inspect and issue a visa

```sh
python -m agentvisa.operator --config .agentvisa.local.json draft \
  --agent procurement --mission 'Buy a monitor under $300.' --output monitor-contract.json
```

Open the contract file and review tools, resources, spending limit, maximum transaction, approval threshold, expiration and delegation depth. Monetary values are integer USD cents. The draft file uses owner-only permissions and is never overwritten by the draft command. Drafting does not issue authority.

After reviewing or editing it:

```sh
python -m agentvisa.operator --config .agentvisa.local.json issue --contract monitor-contract.json
python -m agentvisa.operator --config .agentvisa.local.json visas
```

Give the returned visa ID and its own credential to the agent. Do not give it the human config.

## Inspect pending actions

```sh
python -m agentvisa.operator --config .agentvisa.local.json approvals
python -m agentvisa.operator --config .agentvisa.local.json inspect \
  --agent procurement --request-id monitor-purchase-1
```

Inspection displays the exact action and arguments, mission, visa status, approval deadline, cost, impact, reason, intent diagnostics, deterministic checks and a 64-character action fingerprint. Untrusted content is JSON-escaped so embedded terminal control characters are printed as data.

The fingerprint identifies the exact stored action, not a model's claim or a policy override. Exact-request inspection is a snapshot using the server clock for expiration. Policy is rechecked when the agent retries, even after a human approves.

## Approve or reject once

Copy the fingerprint from inspection into the command:

```sh
python -m agentvisa.operator --config .agentvisa.local.json approve \
  --agent procurement --request-id monitor-purchase-1 --fingerprint EXACT_HASH_FROM_INSPECT
```

Replace `approve` with `reject` to deny the request. The CLI refuses a mismatched hash, expired request or non-pending request before sending approval. The API also checks the expected fingerprint atomically against the pending record, closing the gap between inspection and submission. The recorded human-review event includes the fingerprint.

Approval does not execute the tool. The agent must retry its identical action and request ID through HTTP or MCP. Hard constraints and semantic denial still apply. A rejected or invalidated request cannot be reused to execute; a new proposal needs a new request ID.

## Modify, revoke and inspect delegation

```sh
python -m agentvisa.operator --config .agentvisa.local.json modify \
  --visa VISA_ID --contract revised-contract.json
python -m agentvisa.operator --config .agentvisa.local.json revoke --visa VISA_ID
python -m agentvisa.operator --config .agentvisa.local.json delegations
```

Modification submits a complete reviewed contract and preserves the existing identity/mission. Edits invalidate outstanding approvals for the affected subtree. Revocation blocks new descendant effects. Delegation output includes visa IDs, parent pointers, agents, status and cumulative spending; it does not create child credentials.

## Investigate decisions

```sh
python -m agentvisa.operator --config .agentvisa.local.json audit --limit 25
python -m agentvisa.operator --config .agentvisa.local.json audit --blocked --limit 25
python -m agentvisa.operator --config .agentvisa.local.json integrity
```

Limits range from 1 to 100. Lists return one oldest-first page plus `has_more`, `next_after` and `through`; continue with `--after` and `--through` using unchanged filters. Filtering happens in the database. `visas`, `approvals` and `delegations` support the same paging flags and `--agent`; approval queues also support `--include-expired`. See [pagination semantics](pagination.md), including mutable queues and database maintenance limitations. Integrity failure exits nonzero. The local audit hash chain is not externally anchored or tamper-proof.

## Failures and credentials

Commands exit nonzero on invalid input, stale reviews, authentication errors or transport failure. Error output does not echo bearer tokens or upstream response bodies. Redirects and ambient proxies are disabled; HTTP is restricted to literal loopback addresses. No command automatically retries a mutation. A response lost after issuing a visa or changing policy can leave an unknown outcome: inspect current state before repeating it. Issuance itself does not have an idempotency key.

This is a single-administrator development control plane, not a multi-user identity system. The fingerprint requirement is enforced by both the CLI and HTTP API for approvals and rejections. Older HTTP clients must inspect the exact outstanding request and submit its fingerprint. This binds the review to an action; it does not prove that a human read or understood it.

See [audit exports and independently held checkpoints](audit-exports.md) for offline prefix verification and its trust limitations.

## Inspect inherited authority

```sh
python -m agentvisa.operator --config .agentvisa.local.json inspect-visa --visa VISA_ID
```

This reads one visa and its ancestors in a consistent database snapshot, ordered from leaf to root. Each node includes its contract, status, usage, remaining budget/actions and expiration. `effective_limits` takes the smallest remaining allowance, transaction cap, approval threshold and expiration across the chain. Tool/resource sets intersect all allowed sets and remove every ancestor’s forbidden entries. Usage above a newly reduced cap is displayed as zero remaining, never a negative allowance.

`blockers` identifies inactive or expired ancestors, exceeded delegation depth and exhausted action counts. It is not an exhaustive explanation for a proposed action. Zero remaining budget can still permit a zero-cost action; transaction, tool, resource and intent checks still apply. The snapshot grants no authority and reserves nothing. Parent or sibling activity can consume the displayed allowance immediately after the read; pending reviews do not reserve budget. All actual execution continues through the gateway.
