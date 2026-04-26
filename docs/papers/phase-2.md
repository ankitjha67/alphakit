# Phase 2 Strategy Paper Manifest

This document is the authoritative cross-reference between AlphaKit
Phase 2 strategy slugs and the academic literature each strategy
implements. Each row is committed *in the same commit* that ships the
strategy folder, per Phase 2 master plan Section 5 ("hard contract").
The Session 2H audit reconciles row count here with strategy folder
count under `packages/alphakit-strategies-*/`.

For Phase 1 strategies (60 in total — trend, meanrev, carry, value,
volatility) the equivalent cross-reference lives in each strategy's
`paper.md`. Phase 2 consolidates the cross-reference into this file.

A machine-readable BibTeX counterpart lives in
[`phase-2.bib`](phase-2.bib).

## Column legend

| Column | Meaning |
|---|---|
| Slug | Strategy folder name under `packages/alphakit-strategies-<family>/alphakit/strategies/<family>/<slug>/` |
| Paper (foundational) | Original-inspiration citation (often a survey, seminal study, or the paper that motivated the family of strategies). Maps to the **"Initial inspiration: ..."** line in the strategy's `paper.md`. |
| Paper (primary) | Implementation-anchor citation — the methodology actually replicated in `strategy.py`. Maps to the **"Primary methodology: ..."** line in the strategy's `paper.md`. The `paper_doi` class attribute on the strategy points at this paper. |
| DOI | Stable identifier for the primary paper (or arXiv URL where no DOI exists) |
| Feed | Data feed required for the real-feed benchmark (FRED, yfinance, EIA, CFTC, synthetic-options, ...) |
| Real-data | Whether `benchmark_results.json` (real-feed) ships in this session, vs deferred to Session 2H |
| Sharpe range | Plausible synthetic-benchmark Sharpe band (not a forward-looking guarantee — see strategy `known_failures.md` for regime breakdowns) |
| Known failures | Relative path link to the strategy's `known_failures.md` |

When two papers are cited, the "Initial inspiration: ... / Primary
methodology: ..." pattern in the strategy's `paper.md` preserves the
audit trail from the original Session 2D plan to the actual
implementation anchor.

---

## Rates family

Sub-package: `packages/alphakit-strategies-rates/`. Target: **13
strategies** (reduced from the originally-planned 15 — see
[`../phase-2-amendments.md`](../phase-2-amendments.md) Session 2D
drop entries for `fed_funds_surprise` and `fra_ois_spread`).

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|

---

## Commodity family

Sub-package: `packages/alphakit-strategies-commodity/`. Target: 15
strategies (Session 2E).

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|

---

## Options family

Sub-package: `packages/alphakit-strategies-options/`. Target: 20
strategies (Session 2F). All synthetic-chain benchmarks per ADR-005.

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|

---

## Macro family

Sub-package: `packages/alphakit-strategies-macro/`. Target: 15
strategies (Session 2G).

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|
