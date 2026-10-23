# AgentVisa

**Give an agent limited authority without giving it unlimited trust.**

AgentVisa is an external authorization and execution boundary for autonomous agents. A human issues an inspectable, temporary mission contract; the gateway checks each proposed action against exact policy constraints and a separate intent evaluator before a protected tool can run.

The implementation includes strict contracts, a bounded procurement issuer, deterministic policy, conservative intent evaluation, delegated authority, a durable execution core and authenticated FastAPI routes. The current 56-test suite covers core invariants, API separation and adversarial bypass attempts. Reproducible evaluation and operator documentation follow in the next milestone.

See [ecosystem research](docs/landscape.md) for existing approaches and the scope of the project. All included tool effects are simulations. The intent baseline supports monitor procurement only and escalates unrecognized text for review.
