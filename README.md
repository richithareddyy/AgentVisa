# AgentVisa

**Give an agent limited authority without giving it unlimited trust.**

AgentVisa is an external authorization and execution boundary for autonomous agents. A human issues an inspectable, temporary mission contract; each proposed action passes exact policy checks and a separate intent evaluator before a protected tool can run.

```text
Agent → Gateway → Identity + contract + ancestors → Policy + intent
                                                        |
                                           ALLOW / DENY / ASK_HUMAN
                                                        |
                                              Protected tool adapter
```

This is a working prototype with **simulated tool effects**, durable state, an authenticated FastAPI boundary and a procurement-specific intent baseline. It does not claim production readiness or general protection against prompt injection. See the [ecosystem review](docs/landscape.md) for substantial existing work.

## Run locally

Requires Python 3.11 or newer on a POSIX host (such as macOS or Linux) with `O_NOFOLLOW` support. From this repository:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]' -c requirements.lock
python -m pytest -q
python -m agentvisa demo
python -m agentvisa evaluate
python -m agentvisa init
python -m agentvisa serve
```

Initialization creates `.agentvisa.local.json` with random, separate administrator and agent credentials and owner-only permissions. It refuses to overwrite an existing file. Credentials and databases are ignored by Git. Database files are created with owner-only permissions; existing unsafe files are rejected. See [private storage requirements](docs/storage.md) before reusing an older database. Keep the config private; an agent receives only its own token.

The API binds to `127.0.0.1:8000`; interactive endpoint documentation is at `http://127.0.0.1:8000/docs`. The configured agent is `procurement`. Use the [operator CLI](docs/operator.md) to draft and issue visas, inspect exact pending actions, approve or reject requests, revoke authority and review audits. The [API walkthrough](docs/api.md) documents direct calls.

## Implemented behavior

- Human-reviewed contracts: exact tools/resources, budgets, transaction limits, expiration, approval thresholds, action counts and delegation depth.
- HTTP body reads have a five-second total deadline, including chunked uploads.
- HTTP requests reject duplicate JSON fields, nonfinite numbers, invalid Unicode and excessive nesting before authorization.
- Server-derived prices, destinations and impact; caller-supplied cost overrides and unexpected arguments are rejected.
- Every action checks the entire delegation chain. Child spending consumes every ancestor's allowance, including across siblings.
- Visa and review expiration are rechecked after intent evaluation so slow evaluation cannot use authority already expired at the final check.
- Hard policy denials cannot be overridden by human approval or semantic recommendations.
- HTTP approvals and rejections require the inspected action fingerprint; missing or mismatched fingerprints cannot change review state.
- Exact-action approvals expire within five minutes, are rechecked before execution and cannot produce duplicate effects. Policy edits invalidate affected outstanding approvals.
- Durable idempotency, transactional simulated effects, structured decision logging and a locally verifiable audit hash chain.
- Visa inspection shows the complete ancestor chain, inherited restrictions and remaining shared allowances in a read-only snapshot.
- A human operator CLI supports reviewed contract files, fingerprint-bound approvals, revocation, delegation inspection and bounded audit/review pages with exact filters.
- An agent-only MCP stdio bridge forwards actions to the gateway, with exact-response binding, bounded transport and no human-control tools.
- Optional HTTPS semantic review can tighten the baseline. Uncertainty, malformed evaluator results or service failure requires human review. No remote service is enabled by default.

| Scenario | Result |
| --- | --- |
| Search and compare monitors | ALLOW |
| $450 purchase under a $300 visa | DENY |
| $275 purchase with a $250 approval threshold | ASK_HUMAN |
| Email employee information using a permitted email tool | DENY |
| Follow webpage instructions to upload local files | DENY |
| Delegate greater authority than the parent possesses | DENY |

## Validation and scope

Tests cover HTTP authorization separation, input manipulation, approval replay, budget races, delegation escalation, revocation, persistence, evaluator failure and transactional rollback. The [42-case dataset](evaluation/cases.json) includes legitimate, ambiguous, malicious and drifting actions. The [reference results](evaluation/results.json) record zero automatic allows among 33 cases labeled dangerous or review-required. These curated regression results are not a production false-allow estimate or held-out benchmark. See [metric definitions and limitations](docs/evaluation.md).

The focused stack is Python, FastAPI, SQLite and a small custom policy engine. SQLite transactions make shared budgets and simulated effects inspectable on one host. A separate policy service, Redis and a frontend framework are unnecessary for this scope.

The offline intent baseline combines trusted catalog categories with narrow reviewed text patterns. Its scores are heuristic diagnostics, not calibrated probabilities. It supports monitor procurement only. The human-approved `purpose` field is canonical; mission text is explanatory. Arbitrary natural-language mission interpretation is not implemented.

- [Architecture and transaction semantics](docs/architecture.md)
- [API walkthrough](docs/api.md)
- [Human operator CLI](docs/operator.md)
- [Bounded reads and pagination](docs/pagination.md)
- [MCP agent integration](docs/mcp.md)
- [Optional semantic service protocol](docs/semantic.md)
- [Security assumptions and production gaps](SECURITY.md)

An optional MCP stdio bridge is available with `pip install -e '.[mcp]' -c requirements.lock`. There is no MCP Streamable HTTP endpoint, OAuth issuer, real payment adapter or browser console in this version. The API and operator snapshot provide the control surface. Agents must run outside the trusted gateway process, without direct tool credentials or database access.

See [audit exports and independently held checkpoints](docs/audit-exports.md) for offline prefix verification and its trust limitations.
