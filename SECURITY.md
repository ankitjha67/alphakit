# Security Policy

## Scope

This policy covers all first-party AlphaKit packages:

- `alphakit-core`
- `alphakit-bridges`
- `alphakit-data`
- `alphakit-strategies-*` (every family sub-package)

Third-party libraries that AlphaKit depends on (vectorbt, backtrader,
pandas, numpy, ...) are out of scope — please report issues directly to
their maintainers.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report privately by email to:

> **ankit.jha67@gmail.com**

Include as much detail as you can:

- The affected package and version (or commit SHA).
- A clear description of the issue and its potential impact.
- Steps to reproduce, including minimal code and inputs.
- Any suggested mitigation or fix, if you have one.

If you prefer to report via GitHub's private security advisory feature,
please open one at
<https://github.com/ankitjha67/alphakit/security/advisories/new>.

## What to expect

| Timeline | Action |
|---|---|
| **≤ 72 hours** | We will acknowledge receipt of your report. |
| **≤ 14 days** | Initial assessment and severity classification. |
| **≤ 90 days** | Coordinated fix and public disclosure. |

If we need more time for a complex issue we will tell you, explain why,
and propose a revised timeline. We will **never** ask you to delay
disclosure beyond 90 days without a concrete reason.

## Disclosure policy

We follow **coordinated disclosure**. Concretely:

1. Researcher reports privately.
2. Maintainers confirm, triage and develop a fix on a private branch.
3. Fix is released as a patch version (e.g. ``v0.1.1``) with a security
   advisory published on GitHub.
4. After release, the researcher is free to publish their own write-up
   and is credited in the advisory (unless they request anonymity).

## Security-sensitive areas

Please be especially careful when reporting issues in these areas — we
treat findings here as higher severity:

- **Data adapters** that touch the network (e.g. broker API clients,
  credential handling).
- **Execution bridges** to live brokers (any code that can place real
  orders with real money).
- **Deserialization** of untrusted benchmark JSON, config YAML, or
  strategy parameter files.
- **Dependency pinning and supply-chain** — if you spot a typosquatted
  dependency or a confused-deputy issue in our lockfile, please tell us.

## Out of scope

- Performance issues, crashes on invalid input, or logic bugs that
  cannot be used to exploit something — please use a regular bug
  report instead.
- Vulnerabilities in third-party dependencies (report upstream).
- Theoretical attacks on research notebooks or example code.

Thank you for helping keep AlphaKit and its users safe.
