# Phase 2 Session 2F closeout — Options family

## 1. Summary

* **Branch:** `claude/options-family-strategies-buBzh` (merged; can be
  deleted as standard post-merge hygiene)
* **PR:** [#16](https://github.com/ankitjha67/alphakit/pull/16)
* **Merge commit:** `62809a2` (full SHA:
  `62809a299262729b8d080451d91e6fd3c97ef599`)
* **Merge type:** squash (per Session 2D / 2E precedent)
* **Session started:** 2026-04-30
* **Session completed:** 2026-05-01
* **Total session-equivalents:** ~3 (forecast was 2.5–3; bridge fix
  added ~3 hours, Codex P1 fix-up added ~30 min — both within
  budget)
* **`verify-install` on `main`:** 6/6 green (Ubuntu / macOS /
  Windows × py3.11 / py3.12)

## 2. Strategy count

| Bucket | Count |
|---|---|
| Pre-Session-2F `main` | 83 (60 Phase 1 + 13 rates + 10 commodity) |
| Post-Session-2F `main` | **98** (+15 options) |
| Phase 2 strategies on `main` after 2F | 38 (13 rates + 10 commodity + 15 options) |
| Phase 1 strategies on `main` | 60 (unchanged) |
| Phase 2 final target after Session 2G | ~110–113 (honest reduction from original 125) |

## 3. Tests

| Bucket | Count |
|---|---|
| Pre-Session-2F | 1,587 (1,561 passed + 26 skipped) |
| Post-Session-2F (post-Commit-18) | **1,810** (1,784 passed + 26 skipped) |
| Delta | **+223 tests** |

Test composition:

* **Bridge tests:** 13 (was 0; +13 from Commit 1.5, refined in
  Commit 2).
* **Per-strategy tests:** 15 strategies × ~14 tests each = ~210
  strategy tests.
* **Discovery test:** +1 (`test_options_family` in Commit 17).
* **Regression test:** +1
  (`test_truncated_window_emits_trailing_hedge_weights` in
  Commit 18, verifies the Codex P1 fix bidirectionally —
  fails without the trailing-cycle flush, passes with it).

## 4. FeedRegistry state

* 7 feeds on `main`: `cftc-cot`, `eia`, `fred`, `polygon`,
  `synthetic-options`, `yfinance`, `yfinance-futures`.
* **No new feeds in Session 2F.**
* Chain-consuming strategies (13 of 15) use `synthetic-options`
  from Session 2C.
* VIX strategies (`vix_term_structure_roll`, `vix_3m_basis`) use
  `yfinance` (`^VIX`, `^VIX3M` passthrough) + `yfinance-futures`
  (`VIX=F` passthrough).

## 5. Amendments tally

* Pre-Session-2F: 16 amendments.
* Session 2F additions (10):
  * **5 drops** — `diagonal_spread`, `pin_risk_capture`,
    `earnings_vol_crush`, `ratio_spread_put`,
    `dispersion_trade_proxy`.
  * **3 reframes** — `wheel_strategy → bxmp_overlay`,
    `vix_front_back_spread → vix_3m_basis`,
    `weekly_theta_harvest → weekly_short_volatility`.
  * **1 citation refinement** — `vix_term_structure_roll`
    (Whaley 2009 + Simon-Campasano 2014).
  * **1 bridge architecture extension** — `discrete_legs`
    metadata on `StrategyProtocol`.
  * **1 trailing-cycle flush fix-up** — Commit 18, Codex P1
    catch.
* Post-Session-2F: **26 amendments**.

## 6. Strategy slugs (alphabetical)

1. `bxm_replication`
2. `bxmp_overlay`
3. `calendar_spread_atm`
4. `cash_secured_put_systematic`
5. `covered_call_systematic`
6. `delta_hedged_straddle`
7. `gamma_scalping_daily`
8. `iron_condor_monthly`
9. `put_skew_premium`
10. `short_strangle_monthly`
11. `skew_reversal`
12. `variance_risk_premium_synthetic`
13. `vix_3m_basis`
14. `vix_term_structure_roll`
15. `weekly_short_volatility`

## 7. Architectural contributions

* **`discrete_legs` metadata on `StrategyProtocol`** — documented-
  optional pattern via `getattr` fallback to preserve backwards
  compatibility with all 83 pre-existing strategies. Verified
  empirically: declaring the attribute on the runtime-checkable
  Protocol body would have broken `isinstance(strategy,
  StrategyProtocol)` for every strategy that did not redeclare it.
* **`vectorbt_bridge` per-column dispatch** —
  `SizeType.Amount` vs `SizeType.TargetPercent` per column based
  on `get_discrete_legs(strategy)`. Continuous-only path is
  byte-identical to the pre-fix behaviour.
* **6 leg permutations validated:** 1-leg, 2-leg same-side,
  2-leg long-side, 2-leg opposite-side mixed, 4-leg mixed,
  time-varying TargetPercent on underlying.
* **Bridge architecture stable:** zero new bridge changes since
  `868471d` (covered_call_systematic re-implementation). All 14
  subsequent strategy commits routed cleanly through the new
  dispatch.
* **Stateful-coupling primitive:** cycle metadata side-effect
  pattern for `delta_hedged_straddle` and `gamma_scalping_daily`;
  documented contract that `make_legs_prices` must be called
  before `generate_signals`; **trailing-cycle flush invariant
  explicitly maintained per Commit 18**.

## 8. Adversarial review answers

**Q: Did any strategy fabricate Sharpe numbers?**
A: No. `put_skew_premium` and `skew_reversal` explicitly
document "uninformative on synthetic" / "0.0 by design" in their
`benchmark_results_synthetic.json` note fields and
`known_failures.md`. `delta_hedged_straddle` and
`gamma_scalping_daily` document expected negative Sharpe
(-0.3 to -0.1) honestly as long-vol VRP counterparties.

**Q: Did the bridge architecture extension preserve backwards
compatibility?**
A: Yes. All 1,561 pre-existing tests pass unchanged. 73
pre-existing strategies don't declare `discrete_legs` and fall
through to the unchanged `TargetPercent` code path.

**Q: Were citations rigorous?**
A: Yes. All foundational + primary citations verified DOI
(pre-flight check). 7 papers cited by multiple strategies share
single bibtex entries (citation reuse hygiene).

**Q: Did substrate caveats propagate correctly?**
A: Yes. All 4 substrate caveats (flat IV across strikes, no
bid-ask, no volume / OI, single risk-free rate) appear in every
chain-consuming strategy's `paper.md` Data Fidelity section.
Two strategies (`put_skew_premium`, `skew_reversal`) ship with
prominent "uninformative on synthetic" framing for Phase 3
verification.

**Q: Was the Codex P1 finding addressed properly?**
A: Yes. Commit 18 added the trailing-cycle flush in
`delta_hedged_straddle/strategy.py`. Regression test added
(`test_truncated_window_emits_trailing_hedge_weights`) that
verifies the fix bidirectionally — test fails without fix,
passes with fix. `gamma_scalping_daily` inherits the fix via
composition wrapper.

## 9. Three deliberate-redundancy pairs

| Pair | Expected ρ | Differentiation |
|---|---|---|
| `covered_call_systematic` ↔ `cash_secured_put_systematic` | 0.95–1.0 | Put-call parity equivalence on European-style synthetic options |
| `covered_call_systematic` ↔ `bxm_replication` | 0.95–1.0 | Parametric variant: `otm_pct=0`; `bxm_replication` uses ATM strike per Whaley 2002 BXM rules |
| `delta_hedged_straddle` ↔ `gamma_scalping_daily` | 0.95–1.0 | Academic vs practitioner framing of the same trade (Carr-Wu 2009 vs Sinclair 2008) |

Phase 2 cluster-detection methodology will surface these at
v0.2.0; documentation in respective `known_failures.md` is
authoritative.

## 10. Notable mid-session events

* **Bridge fix at `e376049`** (Commit 1.5; ~3 hours added
  overhead, but real architectural contribution to Phase 2).
* **Commit 2 amended once** — initial implementation didn't use
  `discrete_legs`; reset and re-implemented after the bridge fix
  landed.
* **Pre-flight honesty check** — 5 drops, 3 reframes, 1
  citation refinement.
* **Substrate-caveat strategies** (`put_skew_premium`,
  `skew_reversal`) shipped honestly per the "plumbing validation
  vs edge validation" framework.
* **No PR-premature open** — Session 2E lesson applied:
  workspace AND `[project]` dependencies both filed in Commit 1.
* **Local pre-commit gate caught hardcoded slug count drift** —
  Session 2E lesson applied: `pytest packages/ -x` without path
  filter.
* **Codex AI P1 catch on PR #16** —
  `delta_hedged_straddle` missing trailing-cycle flush.
  Addressed in Commit 18 before merge. Verified bidirectionally
  (test fails without fix, passes with fix).

## 11. Process lesson — gate selection should include architectural novelty

Gate 3 review focused on the first strategy in the family
(`covered_call_systematic`) to establish the pattern. Gate 4
spot-check chose strategies based on substrate-caveat and
term-structure novelty. **Neither selection included
`delta_hedged_straddle`, which introduced cycle metadata as a NEW
state primitive at Commit 9.** Codex AI review caught what human
review missed.

**Process improvement for Session 2G and Phase 3:** future
gate-3 selections should include any strategy that introduces a
NEW state primitive (not just the first strategy in the family).
Stateful coupling, cross-leg metadata, time-varying weights —
these are architectural novelties that deserve dedicated review.

The complementary triad:

1. **Human review** identifies architectural novelty.
2. **Spot-check** exercises substrate edge cases.
3. **AI review** catches state-machine completeness.

All three are valid catches.

## 12. Pace summary

* Forecast: 2.5–3 session-equivalents.
* Actual: ~3 session-equivalents.
* Bridge fix overhead: ~3 hours (genuine architectural value).
* Codex P1 fix-up overhead: ~30 min (caught real bug before
  merge).
* Net drift: within budget. The architectural contributions and
  Codex catch are quality improvements, not overhead noise.
* Total Phase 2 forecast revised: ~14–16 session-equivalents at
  Phase 2 completion (Sessions 2A–2H).

## 13. Session 2G readiness

* **15 macro / GTAA strategies planned.**
* Sub-package: `packages/alphakit-strategies-macro/`.
* **No new feeds expected** (uses existing `fred` + `yfinance`
  adapters).
* **No new bridge changes expected** (continuous
  `TargetPercent` semantics throughout for macro / GTAA).
* **Pre-flight honesty check recommended** (per pattern
  established in 2D, 2E, 2F).
* **Gate-3 review selection:** include any strategy that
  introduces a NEW state primitive, not just the first strategy.
* Apply Session 2E lesson: workspace + `[project]` dependencies
  both filed in Commit 1 to prevent premature-PR CI failures.
* Apply Session 2E lesson: local pre-commit gate must run
  `pytest packages/ -x` (no path filter) to exercise
  bench-package tests.
* Apply Session 2F lesson: `grep` for hardcoded slug counts
  AND family enumerations before push of install pipeline.

## 14. v0.2.0 release readiness checklist

* [ ] All Phase 2 strategies on `main` (after Session 2G):
  ~110–113.
* [ ] All Phase 2 amendments documented (currently 26; will
  grow with Session 2G).
* [ ] `discrete_legs` metadata documented as architectural
  deliverable.
* [ ] Cluster-detection methodology runs (surfaces the 3
  deliberate-redundancy pairs from Session 2F + any from future
  sessions).
* [ ] Real-feed benchmark runs (Session 2H — replaces all
  "deferred to 2H" entries in `phase-2.md`).
* [ ] LEAN bridge stub upgrade (Phase 3, NOT v0.2.0).
* [ ] v0.2.0 release notes (architectural extensions:
  `synthetic-options` adapter Session 2C, `discrete_legs`
  Session 2F).
