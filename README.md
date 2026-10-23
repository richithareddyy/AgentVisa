# AgentVisa

**Give an agent limited authority without giving it unlimited trust.**

AgentVisa is an external authorization and execution boundary for autonomous agents. A human issues an inspectable, temporary mission contract; the gateway checks each proposed action against exact policy constraints and a separate intent evaluator before a protected tool can run.

This repository is under active construction. The first milestone includes strict contracts, a bounded procurement issuer, deterministic policy, conservative intent evaluation, delegated authority and a durable execution core. API, tests and reproducible evaluation follow in the next milestones.

See [ecosystem research](docs/landscape.md) for existing approaches and the scope of the project. All included tool effects are simulations. The intent baseline supports monitor procurement only and escalates unrecognized text for review.
