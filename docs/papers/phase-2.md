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
| [`bond_tsmom_12_1`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/bond_tsmom_12_1/) | Moskowitz/Ooi/Pedersen 2012 | Asness/Moskowitz/Pedersen 2013 §V | [10.1111/jofi.12021](https://doi.org/10.1111/jofi.12021) | fred (DGS10) or yfinance (TLT) | deferred to 2H | 0.4–0.6 (single-asset OOS) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/bond_tsmom_12_1/known_failures.md) |
| [`curve_steepener_2s10s`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/curve_steepener_2s10s/) | Litterman/Scheinkman 1991 | Cochrane/Piazzesi 2005 | [10.1257/0002828053828581](https://doi.org/10.1257/0002828053828581) | fred (DGS2+DGS10) or yfinance (SHY+TLT) | deferred to 2H | 0.3–0.7 (regime-conditional) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/curve_steepener_2s10s/known_failures.md) |
| [`curve_flattener_2s10s`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/curve_flattener_2s10s/) | Litterman/Scheinkman 1991 | Cochrane/Piazzesi 2005 | [10.1257/0002828053828581](https://doi.org/10.1257/0002828053828581) | fred (DGS2+DGS10) or yfinance (SHY+TLT) | deferred to 2H | 0.3–0.7 (regime-conditional, mirror of steepener; ρ ≈ −1.0) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/curve_flattener_2s10s/known_failures.md) |
| [`curve_butterfly_2s5s10s`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/curve_butterfly_2s5s10s/) | Litterman/Scheinkman 1991 | Litterman/Scheinkman 1991 | [10.3905/jfi.1991.692347](https://doi.org/10.3905/jfi.1991.692347) | fred (DGS2+DGS5+DGS10) or yfinance (SHY+IEF+TLT) | deferred to 2H | 0.4–0.8 (PC3 trade) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/curve_butterfly_2s5s10s/known_failures.md) |
| [`bond_carry_rolldown`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/bond_carry_rolldown/) | Fama 1984 | Koijen/Moskowitz/Pedersen/Vrugt 2018 | [10.1016/j.jfineco.2017.11.002](https://doi.org/10.1016/j.jfineco.2017.11.002) | fred (DGS2+DGS10) or yfinance (SHY+TLT) | deferred to 2H | 0.4–0.7 (steep-curve regime-conditional) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/bond_carry_rolldown/known_failures.md) |
| [`duration_targeted_momentum`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/duration_targeted_momentum/) | Durham 2015 | Durham 2015 | [10.17016/FEDS.2015.103](https://doi.org/10.17016/FEDS.2015.103) | fred (DGS2/3/5/7/10/20) or yfinance (SHY+IEF+TLT) | deferred to 2H | 0.3–0.6 (cross-sectional, panel-size-dependent) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/duration_targeted_momentum/known_failures.md) |

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
