# Security model

The gateway host, database, administrator credential, policy code and adapter metadata are trusted. An adversary may control an agent, arguments and retrieved context; it may replay calls, invent identities, inject instructions, race siblings or delegate excessive authority.

The HTTP API is the supported trust boundary. Direct Python methods are trusted application interfaces, not independently authenticated endpoints. Run agents separately, keep provider credentials and SQLite access out of their environment, and restrict egress so protected services cannot be reached directly.

## Enforced properties

Every simulated effect follows current identity, ancestry and deterministic checks. Costs and destinations come from trusted adapters. Human/semantic decisions cannot bypass hard denials. Approvals bind exact requests; retries do not duplicate simulated effects. Descendants share ancestor budgets and inherit revocation. Unknown arguments cannot execute, unknown intent requires review, and audit failure rolls back the effect.

## Limitations

The intent baseline is narrow and may over-escalate legitimate wording. Scores are not calibrated. Model review may be wrong or adversarially influenced and never overrides deterministic checks.

Static bearer credentials are for local development. There is no OAuth/OIDC, tenant isolation, token rotation service, user-level ownership, rate limiting or production TLS termination. One administrator has global authority. The default server binds to loopback; public deployment requires a separate security design.

An explicitly configured semantic service receives mission/action/context. Use an approved service and consider retention and leakage. HTTPS redirects are refused and response size is bounded. Timeout is per network operation, not a total deadline; slow calls can hold the database writer lock.

Audit data contains arguments/context and is not encrypted at the application layer. Protect file permissions, host storage and backups. A privileged attacker can rewrite or truncate the local hash chain; it is not an externally anchored ledger.

There are no real payments, MCP transport, shell tools, arbitrary URLs, filesystem adapters or general-purpose agents. Regression tests cannot prove containment for tools that do not exist.

Before connecting real services, add verified workload identity, provider credentials held only by the gateway, egress isolation, versioned adapter schemas, confirmed costs, reservations/reconciliation, authenticated human sessions, tenant boundaries, rate limits, observability and independent adversarial review.
