# Contributing to AlphaKit

Thank you for your interest in AlphaKit! This guide describes the
per-strategy contract, the PR workflow, and the quality gates every
contribution must satisfy.

## Ground rules (non-negotiable)

1. **Every strategy is paper-cited.** DOI, arXiv link, SSRN ID, or
   book ISBN. No blog posts. No "I heard this from a friend."
2. **Every strategy is benchmarked.** 5+ years of OOS data, results
   committed as `benchmark_results.json`.
3. **Every strategy documents its failure modes.** "This dies in 2022
   rate shock" beats silence. See the `known_failures.md` of the
   reference strategy for the format.
4. **Every strategy implements `StrategyProtocol`.** One interface,
   multiple engines.
5. **Every strategy has tests.** ≥85% line coverage is a CI hard gate.
6. **No fabricated numbers. Ever.** Unbenchmarked strategies are marked
   `experimental` in their metadata until a benchmark exists.
7. **Honest naming.** Slugs describe what the strategy does. No
   "Strategy XX.2 Pro Max Elite".

## Per-strategy contract

Every strategy lives in its own directory under the family package and
must contain the following files:

```
packages/alphakit-strategies-<family>/alphakit/strategies/<family>/<slug>/
├── __init__.py
├── strategy.py              # Implements StrategyProtocol
├── config.yaml              # Default parameters, universe, rebalance
├── paper.md                 # Citation + abstract + original parameters
├── benchmark_results.json   # Auto-generated OOS statistics (Appendix C schema)
├── known_failures.md        # Regimes where the strategy underperforms
├── README.md                # 1-page user guide with a 10-line quickstart
└── tests/
    ├── __init__.py
    ├── test_unit.py         # Logic tests on synthetic data
    └── test_integration.py  # Runs on fixture data through a bridge
```

See [`tsmom_12_1`](packages/alphakit-strategies-trend/alphakit/strategies/trend/tsmom_12_1/)
for a working reference implementation of the contract.

### strategy.py requirements

* Class-level attributes: `name`, `family`, `asset_classes`,
  `paper_doi`, `rebalance_frequency`.
* Implements `generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame`.
* Deterministic: same input → same output. No hidden RNG.
* Full type hints. `mypy --strict` must pass.
* Google-style docstrings on public API.
* Docstring explains any deviation from the published paper.

### paper.md requirements

* Full citation block (title, authors, journal/venue, year, DOI).
* BibTeX block.
* Abstract verbatim from the source.
* Table of published parameters vs. AlphaKit defaults with a note on
  any rescaling.
* In-sample period and out-of-sample period used by the original.
* At least one known replication.

### benchmark_results.json schema

See the [master plan Appendix C](docs/master_plan.md#appendix-c) and the
reference file in `tsmom_12_1/benchmark_results.json`.

### known_failures.md requirements

Prose enumeration of the regimes where the strategy underperforms,
with year ranges and qualitative Sharpe/DD expectations. Reference
published CTA index returns where possible.

## Development workflow

1. **Clone and sync:**
   ```bash
   git clone https://github.com/ankitjha67/alphakit.git
   cd alphakit
   uv sync --extra dev --extra docs
   pre-commit install
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b feat/<family>-<slug>
   ```

3. **Write the strategy test-first:**
   ```bash
   # Unit tests against synthetic data
   uv run pytest packages/alphakit-strategies-<family>/alphakit/strategies/<family>/<slug>/tests/test_unit.py -xvs
   # Integration test through a bridge
   uv run pytest packages/alphakit-strategies-<family>/alphakit/strategies/<family>/<slug>/tests/test_integration.py -xvs
   ```

4. **Run the full quality gates locally:**
   ```bash
   uv run ruff check .
   uv run mypy --strict packages/
   uv run pytest --cov=alphakit --cov-fail-under=85
   ```

5. **Populate the benchmark:**
   ```bash
   uv run python scripts/benchmark_strategy.py <slug>
   ```

6. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat(<family>): add <slug> (<PaperAuthor> <Year>)"
   git push -u origin feat/<family>-<slug>
   ```

7. **Open a PR.** The PR template checklist is the one below.

## PR checklist

Every PR that adds or modifies a strategy must pass every item:

- [ ] Strategy implements `StrategyProtocol`
- [ ] Folder follows the per-strategy contract (files above)
- [ ] Paper citation (DOI or arXiv link) in `paper.md`
- [ ] At least 1 unit test + 1 integration test
- [ ] Benchmark JSON committed (Appendix C schema)
- [ ] Known failure modes documented honestly
- [ ] Asset classes declared in `strategy.asset_classes`
- [ ] `uv run ruff check .` passes with zero errors
- [ ] `uv run mypy --strict packages/` passes with zero errors
- [ ] `uv run pytest` passes with coverage delta ≥85%
- [ ] `CHANGELOG.md` entry added under `[Unreleased]`

## Security-sensitive changes

If your strategy touches network-facing code (a new data adapter, an
execution bridge to a live broker, anything holding credentials),
please read [`SECURITY.md`](SECURITY.md) before opening a PR and
include a note in the PR description describing what you checked.

## Questions?

Open an issue with the `question` label, or (once set up) join the
Discord server.

Thank you for contributing!
