# Verification record

Verified locally on October 23, 2026 using Python 3.14.7 and the dependency versions in `requirements.lock`.

- Editable package installation succeeded with the documented constraints.
- 135 unit/integration tests passed with the MCP extra installed, including concurrent sibling budgets and request idempotency, ancestor revocation/depth changes, approval mutation/expiry, malformed semantic scores, private credential initialization and audit-write rollback.
- The 42-case evaluation matched every expected decision, with zero automatic allows among 33 dangerous or review-required cases. See the evaluation methodology for the narrow scope of this result.
- A real loopback HTTP server passed issuance, human approval, execution, retry, revocation and audit-integrity checks. Temporary credentials and state were removed after the check.
- A real MCP SDK client launched the stdio bridge and verified tool discovery, search, mutated-request rejection, human approval, execution, idempotent replay and revocation through the live HTTP gateway. Transport tests cover redirects, invalid origins, malformed/unbound responses, oversized messages and timeouts.
- The human operator CLI was exercised as a subprocess against a real HTTP gateway: draft, issue, inspect, fingerprint-bound approval, revocation and audit checks passed. Wrong-role credentials, stale/expired reviews, mismatched fingerprints, draft overwrite attempts and credential leakage checks were also covered.
- Bounded read tests cover stable audit traversal while new events arrive, sparse filters, empty pages, mutable approval queues, server-clock expiry, exact lookup, cursor validation, SQL-injection-shaped filters and administrator-only access. The operator CLI was checked to avoid the legacy full snapshot.
- The demo exercised all six required scenarios, including the transition from pending approval to one committed simulated effect.
- Source/document text, package metadata fields and staged filenames were checked for unintended authorship labels and credential artifacts. No such attribution was intentionally added. This is an inspection of the accessible project files, not a claim that all possible metadata or traces are absent.

The full run with the MCP extra completed without test warnings. A base-only installation may emit a Starlette deprecation warning about its older HTTP client integration. Remote semantic services, real external effects and production deployment were not tested. GitHub Actions is configured for Python 3.11 and 3.14; local verification alone does not establish remote CI success.
