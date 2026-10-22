# Session 2M — Benchmark fidelity: runner panel construction

> Carved out of Session 2L. Two runner-level panel-construction defects were
> found during 2L while adding the covariance variants. Both alter committed
> benchmark numbers across already-tagged releases, so neither was patched in
> 2L. This session fixes them under one coordinated keyed regen.
>
> Ordering constraint: **this session must land before the recalibration /
> Phase 2 close session**, because that session re-runs the real-feed cluster
> against these benchmarks. Running recalibration first would calibrate
> against numbers this session then changes. It is independent of the
> supply-chain session and may run before or after it.

Prepend §3 Standing Discipline and §2 Definition of Done from
[`../roadmap-phase-3-to-v1.md`](../roadmap-phase-3-to-v1.md). The DoD item
"benchmark produced by the runner, never hand-edited" is the spine of this
session.

Branch: `claude/2m-benchmark-fidelity`.

---

## Why this is its own session

Both defects change what the benchmark runner computes, so fixing either one
re-writes `benchmark_results.json` for every affected strategy. Those files
are committed and tagged (v0.2.0, v0.2.1, v0.2.2). Changing published numbers
is legitimate when the old numbers were computed by defective machinery, but
it demands: a single coordinated keyed regen, an amendment that records the
before and after, and verification that the change is the fix and nothing
else. That is too large a blast radius to ride inside a feature session.

Measured blast radius (2026-10-21):

| Defect | Strategies affected | Tagged releases touched |
|---|---|---|
| 1. Month-end rebalance skip | 30 | v0.2.0 (trend), v0.2.1 (regime), v0.2.2 (commodity + cot) |
| 2. Single-feed panel not trimmed | 20 tier1 ETF strategies | v0.2.1, v0.2.2 |

The two sets overlap (a strategy can hit both), so the union needing regen is
on the order of 30 to 35 strategies. This is the largest benchmark change
since v0.2.0.

---

## Defect 1 — 31% of monthly rebalances are silently skipped

### Evidence (measured in 2L, do not re-derive)

Every monthly-rebalanced strategy solves weights at calendar month-ends via
`prices.resample("ME").last()`, builds a monthly weights frame indexed by
those calendar month-end labels, then maps it onto the daily index with
`monthly_weights.reindex(daily_index).ffill()`.

`resample("ME")` labels each period at the calendar month-end (for example
2015-01-31), even when it selects the last real observation inside the month
(Friday 2015-01-30's price). The covariance is therefore computed from
correct data. The failure is in the label: a calendar month-end that is not a
trading day (2015-01-31 is a Saturday) is absent from the daily index, so
`reindex` drops that month's weight row entirely and the previous month's
weights forward-fill through. That month never rebalances.

Measured on a 1260-bar business-day panel: 18 of 58 calendar month-ends
(31%) were not trading days. The effective rebalance cadence is nearer every
1.45 months than every month.

30 strategies use this pattern, confirmed by
`grep -rln 'resample("ME")' --include=strategy.py packages/`:

- trend (7): `tsmom_12_1`, `tsmom_volscaled`, `dual_momentum_gem`,
  `fifty_two_week_high`, `frog_in_the_pan`, `residual_momentum`,
  `xs_momentum_jt`
- rates (7): `bond_tsmom_12_1`, `credit_spread_momentum`,
  `duration_targeted_momentum`, `g10_bond_carry`, `global_inflation_momentum`,
  `real_yield_momentum`, `yield_curve_pca_trade`
- commodity (3): `commodity_tsmom`, `metals_momentum`,
  `commodity_curve_carry`
- macro (13): the 3 covariance originals + 3 Session 2L variants +
  `permanent_portfolio`'s siblings `gtaa_cross_asset_momentum`,
  `vigilant_asset_allocation_5`, and the 5 regime strategies
  (`fed_policy_tilt`, `growth_inflation_regime_rotation`,
  `inflation_regime_allocation`, `recession_probability_rotation`,
  `yield_curve_regime_allocation`)

This is documented as section 9 in each Session 2L variant's
`known_failures.md`.

### Fix

Rebalance on the last actual trading day of each month, not the calendar
month-end label. The weight computed from end-of-month data must land on a
date that exists in the daily index. One correct idiom:

```python
# last trading day per calendar month, as real index entries
month_end_days = prices.groupby(prices.index.to_period("M")).tail(1).index
```

then index the monthly weights by `month_end_days` so the reindex onto the
daily index never drops a rebalance. Verify the fix by asserting the number
of distinct rebalance dates equals the number of months in the window, not
69% of them.

### This is genuinely benchmark-altering

Fixing it changes the rebalance timing for all 30 strategies, so every
affected `benchmark_results.json` changes. That is expected and correct: the
old numbers were produced by a strategy that rebalanced less often than its
stated cadence. Do not preserve the old numbers.

Open question for the session to decide, not assume: a small number of these
strategies may rebalance on a cadence other than monthly (check each
`rebalance_frequency`). The fix applies only to monthly rebalancers; confirm
the pattern is monthly before changing each one.

---

## Defect 2 — single-feed ETF panels are not complete-rows trimmed

### Evidence (measured in 2L)

`BenchmarkRunner._fetch_prices` takes a single-feed shortcut for an ETF-only
strategy with no informational columns: it returns the panel straight after
the anomaly filter, with no complete-rows trim. The comment there states it
is deliberately byte-identical to the pre-S2J path. The multi-feed path, by
contrast, trims to the first row where every column is present.

Consequence, measured on the 10-asset universe: a `dropna(how="any")` panel
holds 5008 rows from 2006-02-06 (DBC-bound), but the runner hands the
strategy 5282 rows from 2005-01-03 with 275 NaN-bearing rows. The strategies
handle those rows safely, because `(prices <= 0).any().any()` does not reject
NaN and `rolling_covariance` is fed `daily_log_returns.dropna()`, so no
covariance is estimated from incomplete data. The visible effect is a longer
flat-equity warm-up.

Documented as section 4 in each Session 2L variant's `known_failures.md`.

### This one carries a design decision, and its benchmark impact is conditional

Unlike defect 1, this is not unambiguously a bug. Two defensible positions:

1. **Make single-feed trim like multi-feed.** The inconsistency between the
   two paths is the defect; a strategy's panel should not depend on which
   internal branch the runner took. This changes the benchmark for all 20
   tier1 ETF strategies (panel 5282 to 5008 rows for the 10-asset case,
   different warm-up, Sharpe shifts by roughly 0.03 at 2bp on the probe
   panel).
2. **Document that single-feed intentionally does not trim, and it is safe.**
   The numbers are correct for what the runner does; the NaN rows are handled
   safely; only the docs that claimed a 2006 start were wrong, and those were
   corrected in 2L. Under this position defect 2 is doc-only and does not
   touch benchmarks.

The session must decide 1 vs 2 before any regen, because it determines
whether 20 benchmarks change. Recommendation to weigh: position 1 is more
honest about the contract ("a strategy sees the same panel regardless of
runner internals") but is a larger change; position 2 is cheaper and already
substantially done. Present the decision with the measured Sharpe deltas
before committing either way.

---

## Session plan

**S2M-0 — carry-in + scope confirmation.**
- Verify the preceding tag's `verify-install` is green via GitHub MCP.
- Re-run the two blast-radius greps against live `main` after 2L merges, in
  case the strategy set shifted. Confirm the 30 / 20 counts.
- Runner-determinism baseline (measured in 2L, do not re-derive): a plain
  `regenerate_benchmarks.py tier1` re-run in the 2L sandbox reproduced the 17
  existing tier1 benchmarks to within 0.0001 (only `breakeven_inflation_rotation`
  -0.2366 to -0.2365 and `g10_bond_carry` +0.0724 to +0.0723 moved, both
  last-digit rounding; every other metric was byte-identical apart from
  `benchmark_date` and `commit_sha`). So any metric move larger than 0.0001
  that 2M's regen produces is the fix, not re-run noise. Those 17 re-run
  deltas were discarded in 2L as out of scope; 2M owns them.
- Decide defect 2 position 1 vs 2 (present Sharpe deltas). **Pause for owner
  decision.**

**S2M-1 — fix defect 1 (month-end rebalance).**
- Fix the resample-to-trading-day idiom. If the pattern is duplicated across
  30 strategy files, consider extracting a single shared helper rather than
  editing 30 copies, so the fix cannot drift. Flag that as a design call: a
  shared helper is cleaner but touches more files at once.
- Add a test asserting rebalance-date count equals month count, not 69% of
  it, on a panel with Saturday month-ends.
- Gate with `uv run pytest` (no path arg).

**S2M-2 — fix defect 2 (if position 1 chosen).**
- Make the single-feed path trim complete-rows, matching the multi-feed path.
- Add a test that a single-feed ETF panel with a late-inception ticker starts
  at the complete-rows intersection.
- If position 2 chosen, this step is doc-only reconciliation instead.

**S2M-3 — coordinated keyed regen (Ankit, Windows).**
- The single largest regen since v0.2.0: up to 35 strategies across trend,
  rates, commodity, macro. Give the exact command set per tier.
- Clear `~/.alphakit/cache` first. Real-feed strategies need the keyed path;
  synthetic-fixture strategies regen offline.
- Commit the regenerated JSONs before any dependent session reads them.

**S2M-4 — amendment + cluster re-run + closeout + tag.**
- Amendment recording: both defects, the fix for each, the before/after on a
  representative strategy per family, and the 30/20 blast radius. This is the
  provenance trail for changing tagged benchmark numbers.
- Re-run the real-feed cluster; the correlations will shift because rebalance
  timing changed. Record the new matrix.
- CHANGELOG, closeout, tag. Version bump is a `.PATCH` or `.MINOR` call for
  the owner, since it changes published benchmark numbers without changing
  the strategy roster.

---

## What this session must not do

- Do not change any strategy's signal logic or paper methodology. The signals
  are correct; only the rebalance-date placement and the panel-trim contract
  are in scope.
- Do not hand-edit a single benchmark number. Every changed JSON comes from
  the runner.
- Do not fold in the Session 2K-4 prediction-band recalibration. That is the
  close session's job and depends on this session's output.
