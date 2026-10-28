# Submission requirements review

Review date: October 28, 2026. Scope: the portfolio prototype requested in the original brief, with simulated effects and monitor procurement as the supported mission. This review maps requirements to implementation and executable evidence; it is not an independent security certification.

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Ecosystem and differentiated scope | Dated first-party research and explicit overlap/limitations | [Ecosystem review](landscape.md) |
| Inspectable, editable mission contracts | Strict contracts, bounded draft parser, human issue/modify APIs and CLI | `models.py`, `tests/test_operator.py`, `tests/test_api.py` |
| External enforcement boundary | Authenticated execute route calls closed adapters only after policy/intent checks | `api.py`, `gateway.py`, `tests/test_api.py`, `tests/test_mcp.py` |
| Deterministic enforcement | Tool/resource restrictions, transaction/aggregate budget, action count, expiration and depth checks across ancestors | `policy.py`, `tests/test_gateway.py`, `tests/test_execution_expiry.py` |
| Separate intent evaluation | Structured evaluator interface, conservative procurement baseline, optional remote reviewer that can only tighten it | `intent.py`, `semantic.py`, `tests/test_semantic.py`, `tests/test_intent_validation.py` |
| Human → A → B → C delegation | Stored parent chain, attenuated child contracts, shared ancestor accounting and inherited revocation | `tests/test_submission_acceptance.py`, `tests/test_review_invalidation.py` |
| Exact-action human approval | Inspect action/mission/impact/risk/reason, fingerprint-bound review, expiry, single-effect retries | `queries.py`, `operator.py`, `tests/test_api.py`, `tests/test_operator.py` |
| Reconstructable audit | Lifecycle and decision records, ancestry, diagnostics, hash chain, checkpoint export and offline verification | `gateway.py`, `tests/test_audit_export.py` |
| Normal search/comparison | Both actions demonstrated | `demo.py`, `tests/test_submission_acceptance.py` |
| Budget violation | $450 purchase rejected under $300 authority | `demo.py`, `tests/test_gateway.py` |
| Human approval scenario | $275 purchase waits for review, then commits one simulated effect | `demo.py`, `tests/test_submission_acceptance.py` |
| Mission drift despite tool permission | Vendor email passes deterministic checks but intent denies payroll request | `tests/test_submission_acceptance.py` |
| Prompt-injection attempt | Proposed file upload violates tool/resource constraints and is denied | `demo.py`, `tests/test_gateway.py` |
| Delegation escalation | B can delegate another hop but cannot widen its budget for C | `tests/test_submission_acceptance.py` |
| Adversarial evaluation | 42 curated cases, false-allow-first reporting, label validation, dataset digest and explicit denominators | `agentvisa/data/cases.json`, `tests/test_dataset.py`, `tests/test_evaluation_provenance.py` |
| Usable integration and packaging | Agent-only MCP tools, human CLI, explicit-ID agent example, bundled dataset, clean-wheel checks | `tests/test_mcp.py`, `tests/test_agent_example.py`, `scripts/check_wheel.py` |

Paths in the evidence column are repository-relative; core modules are under `agentvisa/`. Commands to reproduce the main evidence:

```sh
python -m pytest -q
python -m agentvisa demo
python -m agentvisa evaluate
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/check_wheel.py dist/agentvisa-0.1.0-py3-none-any.whl
```

## Findings addressed

The demo previously showed search but not comparison. It now includes both. Its delegation escalation was previously denied by exhausted depth before reaching the spending check. The revised chain permits a third agent at a narrower depth and specifically rejects the attempted budget increase. Acceptance tests assert the reason, prove semantic denial after all deterministic checks pass, and exercise successful three-agent accounting followed by ancestor revocation.

## Declared scope limits

The issuer accepts a bounded monitor-purchase grammar, not arbitrary mission interpretation. The default intent evaluator is a reviewed domain heuristic, not a general natural-language model. Remote semantic calls are optional and tested with stubs; live model reliability has not been established.

Protected effects are SQLite simulation records. Real payments, email delivery, operating-system isolation, provider credentials, external idempotency and reconciliation require a separate design. Agents must be deployed outside the trusted gateway process without direct database/tool access.

Static bearer tokens, one administrator and POSIX file checks serve the local prototype. There is no production identity provider, tenant isolation, public deployment or browser console. The console was optional in the brief; the authenticated API and CLI supply the control surface. Audit checkpoints are unsigned and need separately protected storage. Tests and curated evaluation results are evidence for the implemented scope, not guarantees against arbitrary attacks.

## Submission closeout

The requirements review and demonstration/submission guides are complete. The final release procedure verifies local tests, clean-wheel installation and remote CI, then records the exact source commit and artifact hashes in the accompanying release manifest. No additional product features are planned for this submission. This closeout does not imply production readiness.
