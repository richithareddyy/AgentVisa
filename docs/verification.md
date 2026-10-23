# Verification record

Verified locally on October 23, 2026 using Python 3.14.7 and the dependency versions in `requirements.lock`.

- Editable package installation succeeded with the documented constraints.
- 66 unit/integration tests passed, including concurrent sibling budgets and request idempotency, ancestor revocation/depth changes, approval mutation/expiry, malformed semantic scores, private credential initialization and audit-write rollback.
- The 42-case evaluation matched every expected decision, with zero automatic allows among 33 dangerous or review-required cases. See the evaluation methodology for the narrow scope of this result.
- A real loopback HTTP server passed issuance, human approval, execution, retry, revocation and audit-integrity checks. Temporary credentials and state were removed after the check.
- The demo exercised all six required scenarios, including the transition from pending approval to one committed simulated effect.
- Source/document text, package metadata fields and staged filenames were checked for unintended authorship labels and credential artifacts. No such attribution was intentionally added. This is an inspection of the accessible project files, not a claim that all possible metadata or traces are absent.

The installed Starlette test-client dependency emits one deprecation warning about its current HTTP client integration; it does not fail the tests. Remote semantic services, real external effects and production deployment were not tested. GitHub Actions is configured for Python 3.11 and 3.14; local verification alone does not establish remote CI success.
