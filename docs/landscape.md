# Ecosystem and project scope

Research date: October 23, 2026. This is a targeted review of first-party documentation and research abstracts, not an exhaustive market census or product benchmark.

| Approach | Existing capability | AgentVisa's relationship |
| --- | --- | --- |
| [Auth0 for agents](https://auth0.com/ai) | Agent identity, scoped access, consent and delegated API access. | Could supply production identity and credential custody. AgentVisa does not replace an identity provider. |
| [MCP authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) | OAuth-based authorization for HTTP transports, resource identification and token handling. | Necessary transport security is distinct from checking whether a specific purchase fits a mission. This prototype exposes HTTP, not an MCP server. |
| [Biscuit](https://www.biscuitsec.org/docs/why-biscuit/) | Capability tokens, offline attenuation, logic-based constraints. | Established precedent for narrowing delegated authority. This prototype instead uses online server-held contracts to simplify revocation and shared budgets. |
| [Invariant Guardrails](https://invariantlabs.ai/blog/guardrails) | Contextual policies, data flow restrictions and tool-call interception. | Significant overlap with intent-sensitive enforcement. AgentVisa emphasizes inspectable mission contracts, transactional budgets and exact-action approvals. |
| [Cerbos RAR](https://www.cerbos.dev/blog/rich-authorization-requests-agent-tokens) | Rich authorization details and policy decisions across agent delegation hops. | A production policy engine could replace the small custom deterministic module. Adding a separate policy language is unnecessary for this bounded prototype. |
| [Authenticated Delegation and Authorized AI Agents](https://arxiv.org/abs/2501.09674) | Research extending established identity protocols with agent credentials and delegation metadata. | Delegation/accountability are established topics, not a novelty claim. |
| [AID-Guard](https://arxiv.org/abs/2608.21159) | Research on stateful delegated authorization across effect lifecycles. | Closely related problem space; review beyond the abstract is needed before making comparative claims. |

The target is an educational integration gap: a compact, runnable implementation connecting temporary mission authority, trusted tool argument interpretation, ancestry-wide budget accounting, revocation, human review and measurable adversarial tests. These sources do not establish that no commercial product combines those features.

The intended pitch is: **Give an agent limited authority without giving it unlimited trust.** The project does not claim to make arbitrary agents trustworthy or to solve prompt injection generally. Supplied survey statistics are not used as verified evidence here.
