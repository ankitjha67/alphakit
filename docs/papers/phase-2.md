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
| [`breakeven_inflation_rotation`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/breakeven_inflation_rotation/) | Campbell/Shiller 1996 | Fleckenstein/Longstaff/Lustig 2014 | [10.1111/jofi.12032](https://doi.org/10.1111/jofi.12032) | fred (DFII10+DGS10) or yfinance (TIP+IEF) | deferred to 2H | 0.3–0.7 (regime-conditional) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/breakeven_inflation_rotation/known_failures.md) |
| [`real_yield_momentum`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/real_yield_momentum/) | Pflueger/Viceira 2011 | Asness/Moskowitz/Pedersen 2013 §V | [10.1111/jofi.12021](https://doi.org/10.1111/jofi.12021) | fred (DFII10) or yfinance (TIP) | deferred to 2H | 0.3–0.5 (single-asset OOS) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/real_yield_momentum/known_failures.md) |
| [`yield_curve_pca_trade`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/yield_curve_pca_trade/) | Litterman/Scheinkman 1991 | Litterman/Scheinkman 1991 | [10.3905/jfi.1991.692347](https://doi.org/10.3905/jfi.1991.692347) | fred (DGS2/3/5/7/10/20/30) or yfinance (SHY+IEI+IEF+TLH+TLT) | deferred to 2H | 0.3–0.6 (idiosyncratic residual mean-reversion) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/yield_curve_pca_trade/known_failures.md) |
| [`g10_bond_carry`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/g10_bond_carry/) | Asness/Moskowitz/Pedersen 2013 §V | Asness/Moskowitz/Pedersen 2013 §V | [10.1111/jofi.12021](https://doi.org/10.1111/jofi.12021) | fred (IRLTLT01XXM156N per country) or yfinance (BWX+IGOV+LEMB) | deferred to 2H | 0.4–0.7 (FX-hedged G10 cross-section; subject to crash risk) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/g10_bond_carry/known_failures.md) |
| [`credit_spread_momentum`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/credit_spread_momentum/) | Jostova et al. 2013 | Jostova et al. 2013 | [10.1093/rfs/hht022](https://doi.org/10.1093/rfs/hht022) | fred (BAMLC0A0CM) or yfinance (LQD) | deferred to 2H | 0.3–0.5 (single-asset IG OOS) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/credit_spread_momentum/known_failures.md) |
| [`swap_spread_mean_rev`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/swap_spread_mean_rev/) | Liu/Longstaff/Mandell 2006 | Duarte/Longstaff/Yu 2007 | [10.1093/rfs/hhl026](https://doi.org/10.1093/rfs/hhl026) | fred (DGS10 + ICE swap rate, swap data adapter pending) | deferred to 2H + new adapter | 0.4–0.7 most months / large negative tail (LTCM, GFC) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/swap_spread_mean_rev/known_failures.md) |
| [`global_inflation_momentum`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/global_inflation_momentum/) | Ilmanen 2011 (book, Ch 12) | Ilmanen/Maloney/Ross 2014 | [10.3905/jpm.2014.40.3.087](https://doi.org/10.3905/jpm.2014.40.3.087) | fred (CPI series + per-country bond yields) | deferred to 2H | 0.3–0.6 (G7 cross-section; regime-conditional) | [`known_failures.md`](../../packages/alphakit-strategies-rates/alphakit/strategies/rates/global_inflation_momentum/known_failures.md) |

---

## Commodity family

Sub-package: `packages/alphakit-strategies-commodity/`. Target: **10
strategies** (reduced from the originally-planned 15 — see
[`../phase-2-amendments.md`](../phase-2-amendments.md) Session 2E
drop entries for `energy_weather_premium`, `henry_hub_ttf_spread`,
`inventory_surprise`, `calendar_spread_corn`, and
`coffee_weather_asymmetry`).

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|
| [`commodity_tsmom`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/commodity_tsmom/) | Moskowitz/Ooi/Pedersen 2012 | Asness/Moskowitz/Pedersen 2013 §V | [10.1111/jofi.12021](https://doi.org/10.1111/jofi.12021) | yfinance-futures (CL=F, NG=F, GC=F, SI=F, HG=F, ZC=F, ZS=F, ZW=F) | deferred to 2H | 0.4–0.7 (panel OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/commodity_tsmom/known_failures.md) |
| [`metals_momentum`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/metals_momentum/) | Moskowitz/Ooi/Pedersen 2012 | Asness/Moskowitz/Pedersen 2013 §V (metals subset) | [10.1111/jofi.12021](https://doi.org/10.1111/jofi.12021) | yfinance-futures (GC=F, SI=F, HG=F, PL=F) | deferred to 2H | 0.2–0.5 (metals OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/metals_momentum/known_failures.md) |
| [`wti_backwardation_carry`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/wti_backwardation_carry/) | Gorton/Rouwenhorst 2006 | Erb/Harvey 2006 §III | [10.2469/faj.v62.n2.4084](https://doi.org/10.2469/faj.v62.n2.4084) | yfinance-futures (CL=F, CL2=F) | deferred to 2H | 0.2–0.4 (long-only OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/wti_backwardation_carry/known_failures.md) |
| [`ng_contango_short`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/ng_contango_short/) | Bessembinder 1992 | Erb/Harvey 2006 §III (NG specifically) | [10.2469/faj.v62.n2.4084](https://doi.org/10.2469/faj.v62.n2.4084) | yfinance-futures (NG=F, NG2=F) | deferred to 2H | 0.2–0.5 (short-only OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/ng_contango_short/known_failures.md) |
| [`commodity_curve_carry`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/commodity_curve_carry/) | Erb/Harvey 2006 §III | KMPV 2018 §IV | [10.1016/j.jfineco.2017.11.002](https://doi.org/10.1016/j.jfineco.2017.11.002) | yfinance-futures (8 fronts + 8 next-months) | deferred to 2H | 0.3–0.5 (cross-sectional OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/commodity_curve_carry/known_failures.md) |
| [`cot_speculator_position`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/cot_speculator_position/) | Bessembinder 1992 | de Roon/Nijman/Veld 2000 | [10.1111/0022-1082.00253](https://doi.org/10.1111/0022-1082.00253) | CFTC COT + yfinance-futures (CL/NG/GC/ZC + paired NET_SPEC) | deferred to 2H | 0.3–0.5 (contrarian OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/cot_speculator_position/known_failures.md) |
| [`grain_seasonality`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/grain_seasonality/) | Fama/French 1987 | Sørensen 2002 §III | [10.1002/fut.10017](https://doi.org/10.1002/fut.10017) | yfinance-futures (ZC=F, ZS=F, ZW=F) | deferred to 2H | 0.2–0.5 (calendar OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/grain_seasonality/known_failures.md) |

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
