# Optional semantic review

The default evaluator uses trusted product categories and a narrow reviewed text grammar. Unknown text requires human review. No model service is contacted by default.

To use an approved model-backed review service, add this object to the private local config:

```json
"semantic_service": {
  "endpoint": "https://your-approved-service.example/evaluate",
  "bearer_token": "replace-with-your-service-credential",
  "timeout": 2.0
}
```

The adapter POSTs protocol `agentvisa.intent.v1`, mission, canonical purpose, action, untrusted context and trusted effect metadata. The service invokes its selected model and returns exactly:

```json
{
  "mission_alignment_score": 0.5,
  "risk_score": 0.6,
  "reason": "The proposed communication needs human context.",
  "evidence": ["Free-form external message"],
  "recommended_decision": "ASK_HUMAN"
}
```

Scores must be finite numbers in [0,1]; booleans are rejected. Decisions must be strings equal to ALLOW, DENY or ASK_HUMAN. Remote reasons must be nonblank strings of at most 2,000 characters. Evidence must be a list of at most 20 nonblank strings, each at most 500 characters. Responses are limited to 16 KiB and must contain exactly the documented fields; duplicate JSON keys and nonfinite numeric constants are rejected.

The gateway also validates results from custom in-process evaluators: the same score, decision and evidence-item rules apply, with limits of 4,096 characters for the reason and 40 evidence items to accommodate composed diagnostics. Invalid responses or service failures cause review at the gateway.

Composition takes the lower alignment, higher risk and stricter decision of the baseline and service. A service cannot promote baseline uncertainty to automatic permission. Alignment below 0.9 or risk at least 0.7 requires review. Hard policy denial short-circuits remote review. A semantic DENY remains a denial after human approval.

Tests use local stubs; live provider availability and model quality are unverified. The endpoint is administrator configuration, never agent input. See SECURITY.md for privacy and timeout limitations and architecture.md for transaction contention.

An invalid result cannot automatically authorize an action. It follows the existing human-review workflow: an already approved exact action may still execute after current policy and deadline checks. Validation constrains shape and size; it does not establish that a reviewer’s claims are true.
