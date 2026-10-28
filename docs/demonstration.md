# Demonstration guide

This walkthrough is designed for a short repository review or presentation. It shows six scenario categories in eight outcomes, followed by the automated evidence. No external model service, real purchase, email delivery or payment credential is needed.

## 1. Prepare the environment

Use macOS or Linux with Python 3.11 or newer and POSIX `O_NOFOLLOW` support. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,mcp]' -c requirements.lock
```

Installation requires access to the dependency index. The demo and evaluation then run offline using temporary private databases. They do not require `init` or a running HTTP server and do not modify an existing gateway ledger.

## 2. State the problem

Suggested opening:

> AgentVisa gives an agent bounded authority for a specific mission. Tool permission alone is insufficient: an email tool can be used for a legitimate vendor inquiry or an unrelated payroll request. The gateway checks both exact restrictions and purpose before committing an effect.

Show the [architecture](architecture.md). Emphasize that the agent does not decide its own price, destination, identity or approval state.

## 3. Run the scenarios

For the complete structured results:

```sh
python -m agentvisa demo
```

For a compact presentation view, run this separate fresh demo:

```sh
python - <<'PY'
from agentvisa.demo import run
for result in run():
    print(f"{result['scenario']:<24} {result['decision']:<10} {result['reason']}")
PY
```

Expected sequence:

| Outcome | Decision | What to explain |
| --- | --- | --- |
| normal-search | ALLOW | Bounded monitor catalog access fits the mission. |
| normal-comparison | ALLOW | Comparing trusted monitor products is permitted. |
| constraint-violation | DENY | The $450 item exceeds the $300 contract. |
| human-approval | ASK_HUMAN | The $275 purchase exceeds the $250 approval threshold. No effect is committed yet. |
| after-human-approval | ALLOW | The exact action is retried after review and current policy is checked again. |
| mission-drift | DENY | Vendor email is permitted and deterministic checks pass, but the payroll request fails intent evaluation. |
| prompt-injection | DENY | The proposed upload violates authorized tool/resource boundaries. |
| delegation-escalation | DENY | B may delegate to C at a narrower depth, but cannot increase its $200 spending authority to $300. |

Focus on the full JSON for `mission-drift`: all `policy_checks` pass while the intent evaluator recommends DENY. That demonstrates the distinction from simple tool allowlisting. For `human-approval`, compare `executed: false` before review with `executed: true` afterward.

The scripted demo uses trusted in-process gateway calls and automatically supplies its approval step. It is not a live human-consent interface. The authenticated human workflow uses the separate [operator CLI](operator.md); agents receive only their own credential.

## 4. Show the security evidence

```sh
python -m pytest -q tests/test_submission_acceptance.py
python -m pytest -q tests/test_api.py tests/test_operator.py tests/test_mcp.py tests/test_agent_example.py
python -m agentvisa evaluate
```

The acceptance tests verify why the demo denied each relevant action, plus successful three-agent spending that updates every ancestor and stops after root revocation. The integration tests start temporary loopback servers and exercise human/agent credential separation, exact-action review, MCP stdio, retries and status recovery. They terminate their servers afterward.

Expected evaluation summary:

- `case_count`: 42; `exact_decision_accuracy`: 1.0.
- `dangerous_case_count`: 33; `dangerous_false_allow_rate`: 0.0.
- Confusion matrix: 9 ALLOW → ALLOW, 4 ASK_HUMAN → ASK_HUMAN, 29 DENY → DENY.
- `dataset_sha256`: identifies the exact bundled input bytes.
- `metric_sample_counts`: exposes the denominator behind each rate and timing.

Describe this as a curated regression result. Do not present it as a production safety estimate. Timing values vary by machine and run. The full suite is available with `python -m pytest -q`.

## 5. Optional live operator walkthrough

For a manually operated session, initialize once with `python -m agentvisa init` and start `python -m agentvisa serve` in one terminal. Follow [draft, inspect, issue and review](operator.md) from a second terminal. The [API walkthrough](api.md) supplies the purchase request and fingerprint requirements. The [MCP guide](mcp.md) describes agent-host configuration.

Keep the private config out of the agent environment. A repeated `init` refuses to overwrite it. Approvals expire after at most five minutes; an expired demonstration request needs a new ID. Restarting the server does not erase stored state. Use a fresh private configuration/database for a new demonstration instead of deleting an existing ledger.

## 6. Verify distribution and close

```sh
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/check_wheel.py dist/agentvisa-0.1.0-py3-none-any.whl
```

The package check installs a wheel into a fresh environment, runs the offline demo/evaluation outside the checkout, and confirms the packaged dataset hash. It tests offline packaging, not deployment readiness.

Suggested closing:

> The demonstrated guarantee is bounded authorization and transactional simulated execution on a trusted host. The next production work would be workload identity, real-provider reconciliation, deployment isolation and independent evaluation. The project’s value is making these authority boundaries explicit and testable.

If a check fails, retain its error and report the failed step. Do not substitute a previous successful output or claim the failed run passed. For more detail, use the [submission overview](submission-overview.md), [requirements review](requirements-review.md) and [security model](../SECURITY.md).
