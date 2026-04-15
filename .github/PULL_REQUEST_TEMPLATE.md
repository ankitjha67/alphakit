<!--
Thank you for contributing to AlphaKit!

Please fill out the sections below. PRs that add or modify a strategy
must pass the per-strategy contract checklist — see CONTRIBUTING.md and
the reference implementation in
packages/alphakit-strategies-trend/.../tsmom_12_1/ for an example.
-->

## Strategy summary

> Delete this section if this PR is not adding or modifying a strategy.

- **Name (slug):**
- **Family:**
- **Asset classes:**
- **Paper citation (DOI or arXiv):**
- **Rebalance frequency:**
- **Key parameters (defaults):**
- **Expected Sharpe range (from paper / known replications):**
- **Known failure regimes:**

## What does this PR change?

<!-- A concise description of the change, why it's needed, and any
design decisions worth flagging for the reviewer. -->

## Strategy contract checklist

- [ ] Strategy implements `StrategyProtocol`
- [ ] Folder follows the per-strategy contract (see `CONTRIBUTING.md`)
- [ ] Paper citation (DOI or arXiv link) in `paper.md`
- [ ] `config.yaml` present with sensible defaults
- [ ] `benchmark_results.json` committed (Appendix C schema)
- [ ] `known_failures.md` documents at least one regime honestly
- [ ] Asset classes declared in `strategy.asset_classes`
- [ ] `README.md` has a 10-line quickstart example
- [ ] At least one unit test + one integration test
- [ ] `CHANGELOG.md` entry added under `[Unreleased]`

## Quality gates (must be green locally before requesting review)

- [ ] `uv run ruff check .` — zero errors
- [ ] `uv run mypy --strict packages/` — zero errors
- [ ] `uv run pytest` — all tests pass
- [ ] Coverage ≥ 85% (`--cov-fail-under=85` must not trip)

## Testing notes

<!-- How did you test this? What edge cases did you check? If you ran
backtests, which engine bridge(s)? Which data vintage? -->

## Related issues / PRs

<!-- Link to the issue this PR closes, plus any related PRs. -->

Closes #
