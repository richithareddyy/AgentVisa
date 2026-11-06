# AgentVisa

Permission to call a tool doesn't mean a particular call serves the job you gave the agent. An agent buying a monitor may be allowed to email an approved vendor, but a message asking that vendor for payroll data is outside its purpose. AgentVisa sits between the agent and its tools: a human issues a temporary mission contract, and every proposed action is checked against it before anything runs.

```text
Agent → Gateway → Identity + contract + ancestors → Policy + intent
                                                        |
                                           ALLOW / DENY / ASK_HUMAN
                                                        |
                                              Protected tool adapter
```

**[Try the sandbox](https://agentvisa.onrender.com)** (free instance, so it may need a moment to wake up). This is a working prototype: tool effects are simulated, and the intent check only supports monitor procurement. It doesn't claim production readiness or general protection against prompt injection. The [ecosystem review](docs/landscape.md) covers the existing work in this area.

| Scenario | Result |
| --- | --- |
| Search and compare monitors | ALLOW |
| $450 purchase under a $300 visa | DENY |
| $275 purchase with a $250 approval threshold | ASK_HUMAN |
| Email employee information using a permitted email tool | DENY |
| Follow webpage instructions to upload local files | DENY |
| Delegate greater authority than the parent possesses | DENY |

## How it works

- **Hard checks come first.** Identity, tools, resources, budget, transaction size, action count, expiry, and delegation depth are exact checks. A separate intent evaluator can tighten a decision, and neither it nor a human approval can override a hard denial.
- **The agent doesn't get to state the facts.** Prices and destinations come from trusted adapter metadata, and caller-supplied overrides are rejected.
- **Delegation shares a budget.** Every action checks the whole chain, and child spending counts against every ancestor, so sibling agents can't jointly overspend.
- **Approvals cover one exact action.** They're bound to an action fingerprint, expire within five minutes, and execute nothing themselves. The retry is rechecked against current policy, and revocation invalidates outstanding approvals across descendants.
- **Effects and accounting commit together.** The simulated effect, budget updates, and audit record share one SQLite transaction, which is what stops siblings from racing for the same allowance.

Python, FastAPI, and SQLite, with a small custom policy engine and an optional MCP stdio bridge. I kept it to one host because SQLite's single writer makes the accounting easy to inspect, and a separate policy service or Redis wouldn't add anything at this scope. The tradeoff is real: swapping the database insert for an HTTP call to a real provider would break the atomicity, so real payments would need reservations and reconciliation. The [architecture notes](docs/architecture.md) cover this.

## Evaluation

The pytest suite covers authorization bypasses, approval replay, budget races, delegation escalation, revocation, and rollback, and CI runs it on Python 3.11 and 3.14. The [42-case dataset](agentvisa/data/cases.json) mixes legitimate, ambiguous, malicious, and drifting actions, and the [reference results](evaluation/results.json) show zero automatic allows among the 33 cases labeled dangerous or review-required.

Those cases were developed alongside the code, so they work as regression tests. They aren't a held-out benchmark or an estimate of a real false-allow rate. The intent baseline is a narrow heuristic and its scores aren't calibrated. See [metric definitions](docs/evaluation.md) and [security assumptions and production gaps](SECURITY.md).

## Run locally

Requires Python 3.11+ on macOS or Linux.

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

`init` writes `.agentvisa.local.json` with separate administrator and agent credentials; keep it private and give an agent only its own token. The dashboard is at http://127.0.0.1:8000/ and the API docs at `/docs`.

[Demo walkthrough](docs/demonstration.md) · [Dashboard](docs/dashboard.md) · [Operator CLI](docs/operator.md) · [API](docs/api.md) · [MCP](docs/mcp.md) · [Audit exports](docs/audit-exports.md) · [Hosting](docs/hosting.md) · [Release notes](RELEASE.md)
