# AgentVisa 0.1.0 — portfolio prototype

Release date: October 28, 2026.

This release packages the completed mission-scoped authorization prototype and its submission documentation. It includes temporary contracts, delegated authority, deterministic and intent checks, exact-action human approval, simulated transactional effects, audit verification, HTTP/MCP integration, operator tooling, a local browser dashboard and adversarial evaluation.

Start with the [submission overview](docs/submission-overview.md), then follow the [demonstration guide](docs/demonstration.md). The [requirements review](docs/requirements-review.md) maps the original brief to executable evidence. The [verification record](docs/verification.md) describes the checks and their limits.

## Distribution

- `AgentVisa.zip`: tracked source, tests, documentation and dependency constraints; excludes Git internals, environments, local credentials and databases.
- `agentvisa-0.1.0-py3-none-any.whl`: installable Python package with the bundled evaluation dataset.
- `release-manifest.json`: exact source commit, final CI result, local verification summary and artifact SHA-256 values.
- `SHA256SUMS`: checksums for the ZIP, wheel and manifest. Run `shasum -a 256 -c SHA256SUMS` from the download directory on macOS, or `sha256sum -c SHA256SUMS` on Linux.

Checksums detect accidental file changes relative to the supplied list. They are not signatures or independent proof of publisher identity. The archive and wheel retain version 0.1.0 for this initial prototype release; use the manifest commit and hashes to distinguish it from earlier development exports.

## Installation

The supported environment is Python 3.11 or newer on macOS/Linux with POSIX `O_NOFOLLOW`. Extract the source ZIP, enter its AgentVisa directory, and follow the README’s constrained virtual-environment installation. For a wheel installation from that directory, use:

```sh
python -m pip install /path/to/agentvisa-0.1.0-py3-none-any.whl -c requirements.lock
python -m agentvisa demo
python -m agentvisa evaluate
```

Install the source extras described in the README for tests and MCP. The wheel alone does not install the repository’s documentation, example scripts or tests. No public package-index publication or hosted service is part of this release.

## Verification and scope

The dashboard extension increased the local suite to 339 passing tests, and the 42-case curated evaluation matched every expected decision with zero automatic allows among 33 dangerous/review-required cases. The wheel’s offline commands were checked in a fresh environment outside the checkout. Final remote CI is tied to the exact commit in the release manifest.

This remains a local, single-administrator prototype with simulated effects and a procurement-specific baseline. It has no real payment/email provider, production identity service, tenant isolation or public deployment. The evaluation is a regression dataset, not a general safety estimate. See [SECURITY.md](SECURITY.md) for trusted-host, checkpoint, timeout and deployment assumptions.
