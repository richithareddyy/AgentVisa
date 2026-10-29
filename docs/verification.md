# Verification record

Verified locally on October 28, 2026 using Python 3.14.7 and the dependency versions in `requirements.lock`.

- Editable package installation succeeded with the documented constraints.
- 337 unit/integration tests passed with the MCP extra installed, including concurrent sibling budgets and request idempotency, ancestor revocation/depth changes, approval mutation/expiry, malformed semantic scores, private credential initialization and audit-write rollback.
- The 42-case evaluation matched every expected decision, with zero automatic allows among 33 dangerous or review-required cases. See the evaluation methodology for the narrow scope of this result.
- A real loopback HTTP server passed issuance, human approval, execution, retry, revocation and audit-integrity checks. Temporary credentials and state were removed after the check.
- A real MCP SDK client launched the stdio bridge and verified tool discovery, search, mutated-request rejection, human approval, execution, idempotent replay and revocation through the live HTTP gateway. Transport tests cover redirects, invalid origins, malformed/unbound responses, oversized messages and timeouts.
- The human operator CLI was exercised as a subprocess against a real HTTP gateway: draft, issue, inspect, fingerprint-bound approval, revocation and audit checks passed. Wrong-role credentials, stale/expired reviews, mismatched fingerprints, draft overwrite attempts and credential leakage checks were also covered.
- Bounded read tests cover stable audit traversal while new events arrive, sparse filters, empty pages, mutable approval queues, server-clock expiry, exact lookup, cursor validation, SQL-injection-shaped filters and administrator-only access. The operator CLI was checked to avoid the legacy full snapshot.
- Audit export tests cover paginated snapshots, offline subprocess verification, exact checkpoint binding, edited and rehashed history, sequence gaps/reordering/duplication, truncation, empty histories, malformed/oversized inputs, administrator access, private files, failed-export cleanup and overwrite refusal.
- Execution freshness tests advance a controlled clock during evaluation, covering before/at/after visa and approval deadlines, evaluator failure, expired new reviews, shortened ancestor expiry, denied-result replay, unchanged budgets and audit integrity.
- Intent schema tests cover malformed custom diagnostics, blank/oversized reasons and evidence, nonfinite and boolean scores, invalid decision types, duplicate remote JSON fields, and valid composition at the remote field-size boundaries.
- Storage tests cover permissive umask creation, unsafe mode rejection without mutation, symbolic/hard links, directories/FIFOs, sidecar permissions, wrong ownership, deleted databases, sanitized HTTP failure, rechecks after permission changes, and SQLite journal permissions.
- HTTP JSON boundary tests cover duplicate and escaped-equivalent keys, nonfinite and overflowing numbers, invalid UTF-8 and lone surrogates, nesting limits, media types, chunked duplicate fields, valid Unicode and absence of state changes on rejection.
- Body deadline tests cover stalled reads and cancellation cleanup, a shared deadline across chunks, disconnects, outer cancellation, invalid timeout settings, non-HTTP passthrough and route execution beyond the body-read deadline.
- HTTP human-review tests cover required fingerprints for approve/reject, malformed and cross-action hashes, unchanged state on failure, one-time review application and audit fingerprint recording. The real HTTP/MCP flow inspects before approving.
- Visa inspection tests cover parent usage, pending-review nonreservation, edited ancestor restrictions, revocation/expiry/depth blockers, exhausted allowances, forbidden-set precedence, administrator access and CLI routing without read side effects.
- Subtree invalidation tests cover pending and approved reviews, preservation of sibling/unrelated branches, repeated revocation counts, completed replay, rejected reviews and full rollback when audit writing fails.
- Agent request-status tests cover identity isolation and same-ID separation, all review states, expiry, historical completed results after revocation, completed denials, identifier validation, no-store headers and read-only behavior.
- MCP status tests cover fixed read-only routing, request binding, malformed state/expiry fields, sanitized failures, redirect refusal, oversized responses and identity-override rejection. The real stdio integration checks missing, pending and completed status.
- Agent-example tests cover required IDs, unbound/inconsistent execution responses, missing-status GET behavior, and a real subprocess flow proving identical-ID retries share one effect while status lookup leaves state unchanged.
- A built wheel was installed into a fresh virtual environment without runtime dependencies and exercised outside the source checkout. Its bundled 42-case evaluation and all demo scenarios passed. This package smoke check covers the offline commands; HTTP/MCP integration is covered separately by the full test environment.
- Dataset validation tests cover malformed labels/shapes, duplicate IDs and keys, unknown fields/preconditions, nonfinite JSON, size limits, validation before state creation, reserved setup IDs, delegation-only metrics, safe-only CLI success and report preservation on invalid input.
- Evaluation provenance tests verify the bundled dataset digest, exact byte hashing, identical-content/different-name behavior, all metric/category denominators, explicit zero-sample metrics and a single read shared by validation and hashing.
- The demo exercised all six required scenario categories in eight outcomes, including normal search/comparison, approval before/after execution and a budget-specific delegation rejection. Acceptance tests also verified successful three-agent accounting and inherited root revocation.
- Source/document text, package metadata fields and staged filenames were checked for unintended authorship labels and credential artifacts. No such attribution was intentionally added. This is an inspection of the accessible project files, not a claim that all possible metadata or traces are absent.

The full run with the MCP extra completed without test warnings. A base-only installation may emit a Starlette deprecation warning about its older HTTP client integration. Remote semantic services, real external effects and production deployment were not tested. GitHub Actions is configured for Python 3.11 and 3.14; local verification alone does not establish remote CI success.

## Final release verification

The final local run on October 28, 2026 passed all 337 tests. `pip check` reported no broken requirements, and the newly built wheel passed its clean-environment demo, evaluation and dataset-hash checks.

The preceding documentation commit `773733c9b2b025d57f8be9062cbb59768e5f4adf` passed [GitHub Actions run 40649558365](https://github.com/richithareddyy/AgentVisa/actions/runs/40649558365). The final package’s exact commit, CI run and SHA-256 values are recorded in the release manifest distributed beside the source ZIP and wheel. Consult that manifest rather than assuming this earlier run applies to a later commit.

Artifact review covers tracked source/document text, Markdown links, wheel contents and package metadata, excluded runtime/configuration files, ZIP comments and extra fields. No unexpected attribution was found in the inspected content. Ordinary archive timestamps and build-tool metadata remain; absence of every possible trace or metadata field is not asserted.

## Dashboard extension

The local dashboard extension passed 339 tests. New coverage checks public static assets without credential disclosure, security response headers, closed asset paths and the fingerprint-bound human review flow with separate agent execution and idempotent replay. A live browser walkthrough in an isolated temporary workspace verified mission preview/issuance, a $275 ASK_HUMAN purchase, explicit approval, execution, replay without a second effect, and a $450 policy denial. The installable wheel includes the HTML, CSS and JavaScript assets. The dashboard guide describes session-only credentials and recovery limits.
