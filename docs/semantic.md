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

Scores must be finite numbers in [0,1]. Decisions are ALLOW, DENY or ASK_HUMAN. Evidence and response sizes are bounded. Invalid responses or service failures cause review at the gateway.

Composition takes the lower alignment, higher risk and stricter decision of the baseline and service. A service cannot promote baseline uncertainty to automatic permission. Alignment below 0.9 or risk at least 0.7 requires review. Hard policy denial short-circuits remote review. A semantic DENY remains a denial after human approval.

Tests use local stubs; live provider availability and model quality are unverified. The endpoint is administrator configuration, never agent input. See SECURITY.md for privacy and timeout limitations and architecture.md for transaction contention.
