# Known failure modes — delta_hedged_straddle

> Phase 2 long-vol VRP counterparty — long ATM straddle with
> daily delta hedge on synthetic chains. Black-Scholes 1973
> foundational + Carr-Wu 2009 primary. The strategy is
> expected to LOSE money on average per Carr-Wu's empirical
> finding; this is its design intent (long-vol exposure for
> portfolio diversification).

## 1. Quiet-vol regimes — VRP cost

When realised vol < implied vol consistently, the strategy
loses (RV − IV) × gamma × notional per cycle. Carr-Wu document
this is the average regime — the variance risk premium.

Expected behaviour in quiet-vol regimes:

* Negative Sharpe (-0.1 to -0.3 per cycle on average).
* Drawdown ramps ~0.5-1 % per cycle in extended quiet windows.
* No recovery within the strategy itself — the negative-VRP
  drag is structural.

The diversification value of the strategy comes from the
*positive correlation with realised vol*: when other risk
assets lose money in vol-spike events, this strategy gains.
Users hold it for that diversification, not for its standalone
positive expected return.

## 2. Vol crash from elevated levels (post-spike normalisation)

After a vol-of-vol spike (where the strategy gains), implied
vol typically remains elevated for weeks while realised vol
re-normalises. This means new positions are written at high
IV, then subsequent realised vol is lower → large negative
P&L on the post-spike cycle.

The 2018 February post-Volmageddon period and the 2020
April-May post-COVID period both produced 3-6 consecutive
losing cycles for delta-hedged-straddle strategies after
their initial spike-week gains. Net long-vol P&L over the
6-month spike-and-recovery window is often *negative* despite
the spike-week gain.

## 3. Daily-rebalance turnover drag

The daily delta hedge requires rebalancing the underlying
position every bar — typically 252 rebalances per year per
cycle. Real bid-ask + market-impact costs scale linearly with
turnover; a delta-hedged-straddle backtest *not* modelling
these costs (synthetic chain doesn't) overstates the strategy's
real-world Sharpe by 0.3-0.5 in retail-execution regimes.

Documented honestly: the synthetic backtest is a
*signal-correctness* verification, not a real-world Sharpe
estimate.

## 4. Cluster overlap with `gamma_scalping_daily`

ρ ≈ 0.85-0.95 — these two strategies are the *same trade*
under slightly different parameterisations. Both:

* Long ATM call + long ATM put
* Daily delta hedge against spot direction
* Hold to monthly expiry

The differentiation:
* `delta_hedged_straddle` (this strategy): Carr-Wu 2009
  academic framing, monthly write, ATM strike per the canonical
  VRP setup.
* `gamma_scalping_daily` (Commit 10): Sinclair 2008 +
  Bouchaud-Potters 2003 practitioner framing, parameterised
  rebalance frequency, optionally ATM±1 strike for "scalping
  buffer".

Both ship as distinct citations / parameterisations of the same
underlying mechanic. Cluster-detection methodology (Phase 2
master plan §6) will surface this pair.

## 5. Cluster overlap with `variance_risk_premium_synthetic`

ρ ≈ 0.70-0.85 (Commit 11). Both target the VRP. VRP-synth uses
the Carr-Wu §2 variance-swap-replication formula (weighted
portfolio across the strike grid); this strategy is the simpler
ATM-straddle approximation. The full variance-swap replication
is *more accurate* in theory but more complex to implement; the
ATM-straddle approximation captures most of the VRP exposure
with lower complexity.

## 6. Stateful-coupling caveat

This strategy stores per-cycle metadata on `self._cycles`
(populated by `make_legs_prices`, consumed by
`generate_signals` for the daily delta hedge). If
`generate_signals` is called *without* a prior
`make_legs_prices` invocation:

* Mode 1 (with leg columns in prices): legs trade per
  `discrete_legs` lifecycle, but the underlying delta-hedge
  weight is 0 throughout. The strategy degenerates to a
  long-straddle-without-hedge (a directional long-vol
  position with spot-direction exposure).
* Mode 2 (only underlying in prices): all weights are 0,
  no-trade backtest.

Documented as a deliberate design choice; users should always
call `make_legs_prices` before invoking the strategy.

## 7. Synthetic-chain substrate caveat

* **Greeks are BS-computed at the chain's per-DTE-bucket
  sigma.** Real-market deltas at OTM strikes diverge from BS
  due to skew; for ATM strikes the divergence is small.
* **Sigma frozen per cycle.** Real vol surfaces evolve daily;
  this approximation under-states intracycle delta drift,
  resulting in *under-hedging* of vol-of-vol moves.

For the **ATM** strike specifically, the synthetic chain's
flat-IV-across-strikes substrate is *closest to truth* (real
ATM IV is the kink of the smile). This makes the
delta-hedged-straddle one of the more substrate-faithful
strategies in the family.

## 8. Standard-benchmark-runner mode caveat (degenerate)

Same as other multi-leg strategies. Mode 2 = no-trade backtest.

## 9. Calendar-month-start writes vs. third-Friday writes

Same convention as siblings.

## 10. yfinance passthrough assumption (Session 2H verification)

Inherited from sibling strategies.
