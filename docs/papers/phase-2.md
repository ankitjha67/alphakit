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
| [`crack_spread`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/crack_spread/) | Geman 2005 §7 | Girma/Paulson 1999 | [10.1002/(SICI)1096-9934(199912)19:8<931::AID-FUT5>3.0.CO;2-L](https://doi.org/10.1002/(SICI)1096-9934(199912)19:8<931::AID-FUT5>3.0.CO;2-L) | yfinance-futures (CL=F, RB=F, HO=F) | deferred to 2H | 0.2–0.4 (mean-reversion OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/crack_spread/known_failures.md) |
| [`crush_spread`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/crush_spread/) | Working 1949 | Simon 1999 | [10.1002/(SICI)1096-9934(199905)19:3<271::AID-FUT2>3.0.CO;2-S](https://doi.org/10.1002/(SICI)1096-9934(199905)19:3<271::AID-FUT2>3.0.CO;2-S) | yfinance-futures (ZS=F, ZM=F, ZL=F) | deferred to 2H | 0.2–0.4 (mean-reversion OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/crush_spread/known_failures.md) |
| [`wti_brent_spread`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/wti_brent_spread/) | Gatev/Goetzmann/Rouwenhorst 2006 | Reboredo 2011 | [10.1016/j.eneco.2011.04.006](https://doi.org/10.1016/j.eneco.2011.04.006) | yfinance-futures (CL=F, BZ=F) | deferred to 2H | 0.2–0.5 (pairs-trade OOS) | [`known_failures.md`](../../packages/alphakit-strategies-commodity/alphakit/strategies/commodity/wti_brent_spread/known_failures.md) |

---

## Options family

Sub-package: `packages/alphakit-strategies-options/`. Target: **15
strategies** (reduced from the originally-planned 20 — see
[`../phase-2-amendments.md`](../phase-2-amendments.md) Session 2F
drop entries for `diagonal_spread`, `pin_risk_capture`,
`earnings_vol_crush`, `ratio_spread_put`, and
`dispersion_trade_proxy`, plus reframe entries for
`wheel_strategy → bxmp_overlay`,
`vix_front_back_spread → vix_3m_basis`, and
`weekly_theta_harvest → weekly_short_volatility`). Chain-consuming
strategies use the synthetic-options adapter per ADR-005; VIX
strategies use `^VIX` / `^VIX3M` (yfinance equity passthrough) and
`VIX=F` (yfinance-futures passthrough).

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|
| [`covered_call_systematic`](../../packages/alphakit-strategies-options/alphakit/strategies/options/covered_call_systematic/) | Whaley 2002 | Israelov/Nielsen 2014 | [10.2469/faj.v70.n6.5](https://doi.org/10.2469/faj.v70.n6.5) | synthetic-options + yfinance | deferred to 2H (Mode 1 covered-call benchmark waits on benchmark-runner extension) | 0.3–0.6 (BXM-style OOS, full 2-leg Mode 1) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/covered_call_systematic/known_failures.md) |
| [`cash_secured_put_systematic`](../../packages/alphakit-strategies-options/alphakit/strategies/options/cash_secured_put_systematic/) | Whaley 2002 | Israelov/Nielsen 2014 | [10.2469/faj.v70.n6.5](https://doi.org/10.2469/faj.v70.n6.5) | synthetic-options + yfinance | deferred to 2H | 0.4–0.7 (CBOE PUT-style OOS, put-call-parity sibling of covered_call_systematic; ρ ≈ 0.95-1.0) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/cash_secured_put_systematic/known_failures.md) |
| [`bxm_replication`](../../packages/alphakit-strategies-options/alphakit/strategies/options/bxm_replication/) | Whaley 2002 | Whaley 2002 | [10.3905/jod.2002.319188](https://doi.org/10.3905/jod.2002.319188) | synthetic-options + yfinance | deferred to 2H | 0.4–0.6 (canonical BXM OOS, ATM Whaley 2002 sole anchor; ρ ≈ 0.95-1.0 with covered_call_systematic) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/bxm_replication/known_failures.md) |
| [`bxmp_overlay`](../../packages/alphakit-strategies-options/alphakit/strategies/options/bxmp_overlay/) | Whaley 2002 | Israelov/Nielsen 2014 | [10.2469/faj.v70.n6.5](https://doi.org/10.2469/faj.v70.n6.5) | synthetic-options + yfinance | deferred to 2H | 0.4–0.7 (CBOE BXMP OOS, combined call+put 3-instrument book; reframed wheel; first multi-discrete-leg) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/bxmp_overlay/known_failures.md) |
| [`iron_condor_monthly`](../../packages/alphakit-strategies-options/alphakit/strategies/options/iron_condor_monthly/) | Hill et al. 2006 | CBOE CNDR methodology | [10.3905/jod.2006.622777](https://doi.org/10.3905/jod.2006.622777) | synthetic-options + yfinance | deferred to 2H | 0.5–0.8 (CNDR OOS, 4-leg defined-risk; first 4-discrete-leg) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/iron_condor_monthly/known_failures.md) |
| [`short_strangle_monthly`](../../packages/alphakit-strategies-options/alphakit/strategies/options/short_strangle_monthly/) | Coval/Shumway 2001 | Bondarenko 2014 | [10.1142/S2010139214500050](https://doi.org/10.1142/S2010139214500050) | synthetic-options + yfinance | deferred to 2H | 0.4–0.7 (Bondarenko OOS, 2-leg uncapped; ρ ≈ 0.85-0.95 with iron_condor_monthly) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/short_strangle_monthly/known_failures.md) |
| [`weekly_short_volatility`](../../packages/alphakit-strategies-options/alphakit/strategies/options/weekly_short_volatility/) | Carr/Wu 2009 | Bondarenko 2014 | [10.1142/S2010139214500050](https://doi.org/10.1142/S2010139214500050) | synthetic-options + yfinance | deferred to 2H | 0.4–0.7 (Bondarenko weekly OOS; reframed weekly_theta_harvest; ρ ≈ 0.65-0.85 with short_strangle_monthly) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/weekly_short_volatility/known_failures.md) |
| [`delta_hedged_straddle`](../../packages/alphakit-strategies-options/alphakit/strategies/options/delta_hedged_straddle/) | Black/Scholes 1973 | Carr/Wu 2009 | [10.1093/rfs/hhn038](https://doi.org/10.1093/rfs/hhn038) | synthetic-options + yfinance | deferred to 2H | -0.3 to -0.1 (long-vol VRP counterparty; expected NEGATIVE return; Greeks-dependent) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/delta_hedged_straddle/known_failures.md) |
| [`gamma_scalping_daily`](../../packages/alphakit-strategies-options/alphakit/strategies/options/gamma_scalping_daily/) | Hull/White 1987 | Sinclair 2008 | ISBN:978-0470181998 | synthetic-options + yfinance | deferred to 2H | -0.3 to -0.1 (Sinclair practitioner framing of delta_hedged_straddle; ρ ≈ 0.95-1.0 with that strategy) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/gamma_scalping_daily/known_failures.md) |
| [`variance_risk_premium_synthetic`](../../packages/alphakit-strategies-options/alphakit/strategies/options/variance_risk_premium_synthetic/) | Bondarenko 2014 | Carr/Wu 2009 §2 | [10.1093/rfs/hhn038](https://doi.org/10.1093/rfs/hhn038) | synthetic-options + yfinance | deferred to 2H | 0.4–0.7 (short ATM straddle; 2-leg approximation of multi-strike Carr-Wu replication; ρ ≈ 0.85-0.95 with short_strangle_monthly) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/variance_risk_premium_synthetic/known_failures.md) |
| [`calendar_spread_atm`](../../packages/alphakit-strategies-options/alphakit/strategies/options/calendar_spread_atm/) | Goyal/Saretto 2009 | Goyal/Saretto 2009 | [10.1111/j.1540-6261.2009.01493.x](https://doi.org/10.1111/j.1540-6261.2009.01493.x) | synthetic-options + yfinance | deferred to 2H | 0.2–0.5 (term-structure normalisation harvest; distinct exposure ρ ≈ 0.30-0.55 with siblings) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/calendar_spread_atm/known_failures.md) |
| [`put_skew_premium`](../../packages/alphakit-strategies-options/alphakit/strategies/options/put_skew_premium/) | Bakshi/Kapadia/Madan 2003 | Garleanu/Pedersen/Poteshman 2009 | [10.1093/rfs/hhp005](https://doi.org/10.1093/rfs/hhp005) | synthetic-options + yfinance | ⚠ SUBSTRATE CAVEAT — flat-IV chain has zero skew premium by construction; Phase 3 Polygon required | uninformative on synthetic | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/put_skew_premium/known_failures.md) |
| [`skew_reversal`](../../packages/alphakit-strategies-options/alphakit/strategies/options/skew_reversal/) | Bakshi/Kapadia/Madan 2003 | Garleanu/Pedersen/Poteshman 2009 | [10.1093/rfs/hhp005](https://doi.org/10.1093/rfs/hhp005) | synthetic-options + yfinance | ⚠ SUBSTRATE CAVEAT — trigger never fires on flat-IV chain; degenerate no-trade backtest; Phase 3 Polygon required | 0.0 by design (no trade) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/skew_reversal/known_failures.md) |
| [`vix_term_structure_roll`](../../packages/alphakit-strategies-options/alphakit/strategies/options/vix_term_structure_roll/) | Whaley 2009 | Simon/Campasano 2014 | [10.3905/jod.2014.21.3.054](https://doi.org/10.3905/jod.2014.21.3.054) | yfinance (^VIX) + yfinance-futures (VIX=F) | deferred to 2H | 0.4–0.7 (Simon-Campasano OOS; differentiated from Phase 1 vix_term_structure RV proxy by real ^VIX/VIX=F data) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/vix_term_structure_roll/known_failures.md) |
| [`vix_3m_basis`](../../packages/alphakit-strategies-options/alphakit/strategies/options/vix_3m_basis/) | Whaley 2009 | Alexander/Korovilas/Kapraun 2015 | [10.1016/j.jimonfin.2015.10.005](https://doi.org/10.1016/j.jimonfin.2015.10.005) | yfinance (^VIX, ^VIX3M passthrough) | deferred to 2H | 0.3–0.6 (Alexander et al. OOS; reframed vix_front_back_spread; ρ ≈ 0.55-0.75 with vix_term_structure_roll) | [`known_failures.md`](../../packages/alphakit-strategies-options/alphakit/strategies/options/vix_3m_basis/known_failures.md) |

---

## Macro family

Sub-package: `packages/alphakit-strategies-macro/`. Target: **11
strategies** (reduced from the originally-planned 15 — see
[`../phase-2-amendments.md`](../phase-2-amendments.md) Session 2G
drop entries for `cape_country_rotation` (cluster duplicate of Phase 1
`country_cape_rotation`), `dollar_strength_tilt` (no peer-reviewed
anchor — folklore), `dual_momentum_gtaa` (cluster duplicate of Phase
1 `dual_momentum_gem`), and `inflation_tilt_60_40_overlay` (borderline
cluster duplicate of `inflation_regime_allocation`); plus reframe
entries for `risk_parity_3asset → risk_parity_erc_3asset`,
`economic_regime_rotation → growth_inflation_regime_rotation`,
`yield_curve_regime_asset_allocation → yield_curve_regime_allocation`,
`global_macro_momentum → gtaa_cross_asset_momentum`, and
`5_asset_tactical → vigilant_asset_allocation_5`). Covariance-based
strategies share the `alphakit.strategies.macro._covariance` helper
(Ledoit-Wolf shrinkage + rolling-window estimation + ERC /
minimum-variance / maximum-diversification solvers). Regime allocators
follow the Session 2D "informational columns with zero weight" pattern
documented in `../phase-2-amendments.md` (FRED series enter as input
DataFrame columns with zero weight in the output; tradable assets
carry the regime-conditional allocation).

| Slug | Paper (foundational) | Paper (primary) | DOI | Feed | Real-data | Sharpe range | Known failures |
|---|---|---|---|---|---|---|---|
| [`permanent_portfolio`](../../packages/alphakit-strategies-macro/alphakit/strategies/macro/permanent_portfolio/) | Browne 1987 (book, ISBN 0-688-06778-6) | Estrada 2018 | [10.2139/ssrn.3168697](https://doi.org/10.2139/ssrn.3168697) | yfinance (SPY+TLT+GLD+SHY) | deferred to 2H | 0.3–0.6 (Estrada OOS) | [`known_failures.md`](../../packages/alphakit-strategies-macro/alphakit/strategies/macro/permanent_portfolio/known_failures.md) |
