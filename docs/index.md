# AlphaKit

> The most comprehensive, researcher-defensible, multi-asset,
> plug-and-play open-source quant strategy library.

[![CI](https://img.shields.io/badge/CI-pending-lightgrey)](https://github.com/ankitjha67/alphakit/actions)
[![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey)](https://github.com/ankitjha67/alphakit)
[![PyPI](https://img.shields.io/badge/pypi-v0.0.1-blue)](https://pypi.org/project/alphakit/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](https://github.com/ankitjha67/alphakit/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

AlphaKit is a modular monorepo of paper-cited, benchmarked,
production-grade trading strategies covering 14+ asset classes. The
architecture is a **thin core** (`StrategyProtocol`, data schemas,
metrics, adapters) with **independent sub-packages** by strategy family.
Every strategy ships with paper citation, parameter defaults, OOS
benchmarks, documented failure modes, and unit + integration tests.

## Why AlphaKit?

- **Paper-cited.** Every strategy has a DOI, arXiv link, or book ISBN.
  No blog posts. No "I heard this from a friend."
- **Benchmarked honestly.** Every strategy ships with
  `benchmark_results.json` from a 5+ year OOS run.
- **Failure modes documented.** "Dies in 2022 rate shock" beats silence.
- **One interface, multiple engines.** `StrategyProtocol` runs on the
  internal vectorised engine, vectorbt, backtrader, and (Phase 2+) LEAN.
- **Modular install.** `pip install alphakit[crypto]` does not pull
  equities or rates dependencies.
- **Tested.** ≥ 85% coverage is a CI hard gate.

## Quick links

- [:material-rocket-launch: **Quickstart**](quickstart.md) — install and
  run the reference strategy in 10 lines.
- [:material-sitemap: **Architecture**](architecture.md) — how the core,
  bridges and strategy families fit together.
- [:material-certificate: **Strategy contract**](strategy_contract.md) —
  the non-negotiable spec every strategy ships with.
- [:material-github: **Contributing**](https://github.com/ankitjha67/alphakit/blob/main/CONTRIBUTING.md)
  — how to add a strategy.
- [:material-shield-lock: **Security policy**](https://github.com/ankitjha67/alphakit/blob/main/SECURITY.md)
  — how to report a vulnerability.

## Roadmap

| Phase | Strategies | Version |
|---|---|---|
| 0 — Foundation | 1 reference | v0.0.1 |
| 1 — Core families | 60 | v0.1.0 |
| 2 — Asset breadth | 125 | v0.2.0 |
| 3 — ML / RL | 165 | v0.3.0 |
| 4 — Long tail | 500+ | v1.0.0 |
| 5 — Multi-language | + C# / R | v1.1+ |

## License

Apache License 2.0. See
[`LICENSE`](https://github.com/ankitjha67/alphakit/blob/main/LICENSE).
