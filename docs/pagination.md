# Bounded operator APIs

The operator CLI uses bounded, administrator-only queries instead of the legacy full `/control` snapshot. Page sizes range from 1 to 100 records, defaulting to 25. All list results are ordered by increasing insertion cursor, oldest first.

| Route | Additional filters |
| --- | --- |
| `GET /audit/events` | `agent`, `visa`, `decision`, `blocked` |
| `GET /visas` | `agent` |
| `GET /approvals` | `agent`, `include_expired` |
| `GET /approvals/inspect` | Required `agent` and `request_id`; returns one outstanding review |

Each list accepts `after` (exclusive lower cursor), `through` (inclusive upper cursor), and `limit`. Omit `through` on the first call to capture the current upper bound. Example:

```text
GET /audit/events?limit=25&blocked=true
```

```json
{
  "items": [],
  "has_more": false,
  "next_after": null,
  "through": 42
}
```

When `has_more` is true, repeat the same filters with `after=next_after` and the original `through`. Stop when `has_more` is false. An empty page is a normal result. Fetches use `LIMIT limit+1`, returning at most `limit` records without loading the whole table into application memory.

## Consistency

The upper bound prevents later inserts from entering a traversal. Audit records are append-only through the application, so a fixed upper bound and unchanged filters produce an ordered traversal without overlap. To poll for later events after finishing, use `after` equal to the old `through` and omit `through` to capture a new bound.

Visa and request rows can change. Their upper bound fixes insertion membership, not contents. An approval can be resolved, invalidated or expire between pages and therefore disappear from a filtered queue. Review a specific action again before approving; neither pagination nor a displayed status grants execution authority.

Approval pages omit expired pending/approved records by default. `include_expired=true` includes them with an `expired` flag. Exact inspection also returns expired outstanding records and the server time. Expiration uses the gateway clock, not the operator workstation's clock. Requests already rejected, invalidated or completed are not outstanding reviews; inspection returns 404 and their history remains in the audit.

Cursors are navigation positions, not credentials. All queries require administrator authorization. They refer to the same database and insertion order; do not reuse them after a database rebuild, row-ID-changing maintenance or restoring unrelated data. Visa/request cursors use SQLite row IDs; audit cursors use the explicit sequence column.

## Filter semantics

Audit `agent`, `visa` and `decision` match their exact top-level event fields. They do not infer ancestry, scan argument text or retroactively enrich older lifecycle events that lack a field. `blocked=true` includes DENY decisions and delegation-denied events. Combining filters means logical AND. A blocked page combined with `decision=ALLOW` is empty.

Values are parameterized in SQL. Agent strings cannot alter SQL structure. Additive indexes support common decision/agent and queue-state lookups. Sparse or combined JSON filters can still scan many records: response bounds are not a guarantee of constant database CPU time. A production service needs query budgets, retention and workload testing.

## CLI

```sh
python -m agentvisa.operator --config .agentvisa.local.json audit --limit 25 --blocked
python -m agentvisa.operator --config .agentvisa.local.json audit --limit 25 --after CURSOR --through UPPER_BOUND --blocked
python -m agentvisa.operator --config .agentvisa.local.json visas --agent procurement --limit 10
python -m agentvisa.operator --config .agentvisa.local.json approvals --include-expired --limit 10
```

CLI output uses `audit`, `visas`, `approvals` or `delegations` as its item key and retains `has_more`, `next_after` and `through`. It fetches one page per command and never silently fetches all pages. Audit output is now oldest-first within the selected cursor range, rather than the earlier CLI's last-N snapshot behavior.

The legacy `/control` endpoint remains administrator-only for backward compatibility and local diagnostics. It is unbounded and no longer used by the operator CLI. Full audit integrity checking is still an entire-chain operation; paginated output alone does not verify chain integrity or prevent privileged tampering.
