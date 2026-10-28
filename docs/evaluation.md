# Evaluation methodology

Run `python -m agentvisa evaluate --output evaluation/results.json`. The command exits nonzero on any decision-label mismatch or dangerous false allow. Each case uses a new temporary database and fixed logical clock; latency uses the host's performance counter. Setup/cleanup are excluded.

The 42 hand-authored cases contain 9 expected allows, 4 expected human reviews and 29 expected denials. All 33 non-ALLOW cases are labeled dangerous or review-required, including ambiguous actions. An automatic allow for any of them counts as a false allow.

| Metric | Definition |
| --- | --- |
| Dangerous false allow | Actual ALLOW / dangerous or review-required cases |
| Exact decision accuracy | Matching three-way decisions / all cases |
| False deny | Actual DENY / expected ALLOW cases |
| Unnecessary review | Actual ASK_HUMAN / expected ALLOW cases |
| Mission-drift detection | Actual DENY / mission-drift cases |
| Injection containment | Actual non-ALLOW / injection cases |
| Delegation prevention | Actual DENY / escalation cases |
| Gateway latency | Complete execution/delegation including local commit and audit |
| Policy latency | Instrumented ancestry policy loop, excluding parsing, intent, commit and delegation checks |

The reference run uses the offline baseline. Requests rejected before the policy loop contribute zero policy time. The p95 is a lower discrete percentile on a small sample without warm-up or load testing. These timings are not production performance estimates.

The fixtures were developed alongside the implementation. They are not independently labeled, representative or held out. Zero observed false allows is not an estimate of an attacker's success probability. Injection tests exercise attempted effects, not a live compromised model. Unit/integration tests separately cover races, replay, persistence and audit failure.

Broader evaluation needs independently authored held-out missions, paraphrases, multilingual actions, multi-step traces, new adapters, realistic human reviews and calibrated model evaluation. Report category denominators and uncertainty before drawing population-level conclusions.

The default dataset is packaged at `agentvisa/data/cases.json` and loaded through package resources. Evaluation no longer depends on the current working directory. Use `python -m agentvisa evaluate --dataset /absolute/path/to/custom.json` for an explicit custom dataset.
