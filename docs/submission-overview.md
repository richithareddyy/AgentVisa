# AgentVisa: mission-scoped authority for agents

**Give an agent limited authority without giving it unlimited trust.**

AgentVisa is a working security-infrastructure prototype that places an authorization and execution boundary between an agent and protected tools. A human issues a temporary mission contract. Every proposed action is checked against that contract and its delegation ancestors before a simulated effect can be committed.

## Problem and approach

Permission to call a tool does not establish that a particular use serves the authorized mission. An agent buying a monitor may be allowed to email an approved vendor, yet a message requesting payroll information is outside that purpose. AgentVisa combines exact constraints with a separate intent evaluator to distinguish these cases.

The outcome is ALLOW, DENY or ASK_HUMAN. Deterministic checks enforce identity, tools, resources, budget, transaction size, action count, expiration and delegation depth. The intent layer supplies structured alignment/risk diagnostics and can require human review or deny an otherwise permitted action. It cannot override a hard policy failure.

## What the implementation demonstrates

- **Human control:** inspectable contract drafts, explicit issuance, editable restrictions, revocation and fingerprint-bound review of an exact action.
- **Delegation:** Human → Agent A → Agent B → Agent C, with narrower authority at every hop. Spending consumes every ancestor’s allowance; siblings cannot collectively exceed a shared budget.
- **Execution safety:** durable request IDs, exact-action binding, transactional simulated effects, policy rechecks after approval, and expiry checks after intent evaluation.
- **Accountability:** lifecycle and decision audit records, bounded inspection APIs, inherited-limit views, audit export and offline verification against separately held checkpoints.
- **Integration:** a FastAPI boundary, human operator CLI, an agent client with explicit retry IDs, and MCP stdio tools for execution and read-only request status.
- **Evaluation:** validated adversarial fixtures, exact dataset hashes, explicit metric denominators and reproducible packaged offline commands.

## Architecture and engineering choices

The focused stack is Python, FastAPI and SQLite, with optional MCP integration. Contracts are server-held records; agents receive opaque visa IDs. The gateway derives prices and destinations from trusted adapter metadata rather than accepting agent-supplied cost claims.

SQLite serializes writers so budget updates, request state, simulated effects and audit records commit together. This makes the prototype’s accounting and failure behavior inspectable on one host. Real external services would need provider idempotency, durable reservations and reconciliation; replacing a database insert with an HTTP call would break the present atomicity guarantee.

The default intent evaluator is a conservative procurement-specific heuristic. An optional HTTPS reviewer can tighten it. Unknown meaning or evaluator failure requires human review; scores are diagnostics, not calibrated probabilities. The issuer supports a bounded monitor-purchase grammar. These choices keep the demonstrated authority boundaries explicit rather than implying general mission understanding.

## Evidence and interpretation

The local suite contains 337 passing tests at the requirements-review milestone. It covers authorization bypass attempts, shared budgets, approval replay, expiry, revocation, malformed inputs, rollback, HTTP/MCP integration and packaging.

The bundled 42-case regression set produces 42 matching decisions: 9 ALLOW, 4 ASK_HUMAN and 29 DENY. There are zero automatic allows among 33 cases labeled dangerous or review-required. These fixtures were developed with the implementation; they are not held out, representative of production traffic, or evidence of a general zero false-allow rate.

The [demonstration guide](demonstration.md) provides commands and expected results. The [requirements review](requirements-review.md) maps the original brief to implementation and tests. The [verification record](verification.md) distinguishes local checks from remote CI, and the [evaluation methodology](evaluation.md) explains metric definitions and limitations.

## Scope and differentiation

Agent identity, OAuth, attenuated capabilities and tool-call guardrails are established areas. The [ecosystem review](landscape.md) documents overlap; AgentVisa makes no uniqueness claim. Its portfolio contribution is the integration of mission contracts, ancestry-wide accounting, exact-action approval and adversarial evaluation in a compact runnable system.

This is a local prototype with simulated effects, static bearer credentials and one administrator. It has no real payment/email provider, public deployment, tenant isolation, general-purpose model agent. The [local dashboard](dashboard.md) supports human-operated missions, simulated proposals, exact-action review and audit inspection. Agents must run outside the trusted gateway process without direct tool/database access. Audit checkpoints are unsigned and must be protected separately. Full assumptions and remaining production work are in [SECURITY.md](../SECURITY.md).
