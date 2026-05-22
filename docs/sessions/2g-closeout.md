# Phase 2 Session 2G closeout — Macro / GTAA family

## 1. Summary

* **Branch:** `claude/2g-macro-family` (merged; can be deleted as
  standard post-merge hygiene)
* **PR:** [#18](https://github.com/ankitjha67/alphakit/pull/18)
* **Merge commit:** `d1fe5d2` (full SHA:
  `d1fe5d24f630edf6b00a36de3056e025ca5e7dbe`)
* **Merge type:** squash (per Session 2D / 2E / 2F precedent)
* **Commits on the branch:** 13 (scaffold, `_covariance` helper,
  11 strategy commits, install-pipeline wiring) + 1 docs-fix
  (stale-forward-reference correction)
* **`verify-install` on the branch:** 6/6 green (Ubuntu / macOS ×
  py3.10 / 3.11 / 3.12) after re-dispatch with the correct branch
  ref — see §10.
* **PR CI:** 7/7 green (test.yml ×6 + lint.yml ×1).

## 2. Strategy count

| Bucket | Count |
|---|---|
| Pre-Session-2G `main` | 98 (60 Phase 1 + 13 rates + 10 commodity + 15 options) |
| Post-Session-2G `main` | **109** (+11 macro) |
| Phase 2 strategies on `main` after 2G | 49 (13 rates + 10 commodity + 15 options + 11 macro) |
| Phase 1 strategies on `main` | 60 (unchanged) |
| Phase 2 remaining | 1 family (Session 2H scope) |

The macro family ships **11**, an honest reduction from the
originally-planned 15 — 4 drops at the Gate-1 honesty check (see §5).

## 3. Tests

| Bucket | Count |
|---|---|
| Pre-Session-2G (post-Commit-18 Session 2F) | 1,810 |
| Post-Session-2G | **2,177** |
| Delta | **+367 tests** |

Test composition:

* **Covariance-helper tests:** 41 (Commit 1.5, package-level
  `tests/test_covariance.py`) with analytic-known-result anchors —
  ERC inverse-vol on uncorrelated assets, ERC equal-risk on a
  non-diagonal covariance, long-only MV constraint binding,
  Ledoit-Wolf shrinkage α in the unit interval, MDP equal-correlation
  equal-vol.
* **Per-strategy tests:** 11 strategies × ~30–36 unit + integration
  tests each (constructor invariants, regime classification,
  publication-lag forensics, informational-column zero-weight
  invariant, warm-up, weight-sum, determinism, empty-input
  rejection).
* **Discovery test:** +1 (`test_macro_family` in Commit 13 —
  FAMILIES membership + 11-slug roster).

Test progression by commit:

| After | Tests |
|---|---|
| Commit 1.5 (helper) | 1,849 |
| Commit 2 (permanent_portfolio) | 1,860 |
| Commit 5 (ERC) | 1,949 |
| Commit 7 (covariance group complete) | 2,001 |
| Commit 8 (recession) | 2,041 |
| Commit 12 (regime group complete) | 2,176 |
| Commit 13 (install pipeline) | 2,177 |

## 4. FeedRegistry state

* 7 feeds on `main`: `cftc-cot`, `eia`, `fred`, `polygon`,
  `synthetic-options`, `yfinance`, `yfinance-futures`.
* **No new feeds in Session 2G.**
* Tradable ETF legs (SPY / TLT / GLD / DBC / SHY) use `yfinance`.
* Regime-state strategies read FRED informational columns
  (`RECPROUSM156N`, `CPIAUCSL`, `GDPC1`, `DGS10`, `DGS2`,
  `FEDFUNDS`) via the existing `fred` adapter as zero-weight input
  columns.

## 5. Amendments tally

Session 2G additions to `docs/phase-2-amendments.md`:

* **4 substantive amendment entries:**
  1. Covariance-primitive shared-helper architecture (shared
     estimator preserves cluster-prediction integrity).
  2. AlphaKit-wide rebalance-cadence convention
     (`SizeType.TargetPercent` → ~63 daily drift-correction events
     per asset per year, not 12 discrete monthly rebalances;
     Sharpe-equivalent under reasonable cost models).
  3. Bridge-positivity constraint for FRED informational columns
     (pass raw positive level / index / rate series, compute derived
     signals internally; **DGS2 over DGS3MO** because DGS3MO prints
     exactly 0.0 on ZIRP days).
  4. Reframe `risk_parity_3asset → risk_parity_erc_3asset`
     (Bridgewater All-Weather folklore dropped; MRT 2010 + AFP 2012
     substituted as peer-reviewed anchors).
* **Gate-1 honesty-check audit trail (Commit 1):**
  * **4 drops** — `cape_country_rotation` (cluster duplicate of
    Phase 1 `country_cape_rotation`), `dollar_strength_tilt` (no
    peer-reviewed anchor), `dual_momentum_gtaa` (cluster duplicate
    of Phase 1 `dual_momentum_gem`), `inflation_tilt_60_40_overlay`
    (borderline cluster duplicate of `inflation_regime_allocation`).
  * **5 reframes** — `risk_parity_3asset → risk_parity_erc_3asset`,
    `economic_regime_rotation → growth_inflation_regime_rotation`,
    `yield_curve_regime_asset_allocation →
    yield_curve_regime_allocation`, `global_macro_momentum →
    gtaa_cross_asset_momentum`, `5_asset_tactical →
    vigilant_asset_allocation_5`.

The authoritative running tally lives in
`docs/phase-2-amendments.md`.

## 6. Strategy slugs (alphabetical)

1. `fed_policy_tilt`
2. `growth_inflation_regime_rotation`
3. `gtaa_cross_asset_momentum`
4. `inflation_regime_allocation`
5. `max_diversification`
6. `min_variance_gtaa`
7. `permanent_portfolio`
8. `recession_probability_rotation`
9. `risk_parity_erc_3asset`
10. `vigilant_asset_allocation_5`
11. `yield_curve_regime_allocation`

## 7. Architectural contributions

* **Shared `_covariance` helper module** (`Commit 1.5`,
  `alphakit.strategies.macro._covariance`) — Ledoit-Wolf 2004
  shrinkage, rolling-window covariance, and three convex/SLSQP
  solvers (ERC via Spinu 2013 reformulation, long-only minimum
  variance, maximum diversification) plus a diversification-ratio
  helper. Consumed by the covariance trio (Commits 5–7). The shared
  estimator means the three strategies differ only in their
  objective, not their covariance input — keeping the
  cluster-prediction story honest.
* **Informational-column pattern** — FRED macro series enter
  `generate_signals` as zero-weight input columns alongside tradable
  ETF prices; only the ETFs carry regime weights. A defensive
  end-of-function zeroing of every informational column is applied
  across all 5 regime strategies as a belt-and-suspenders invariant.
* **Publication-lag handling** — `.shift(lag_months)` is applied to
  every FRED column *before* any derived signal (YoY, slope, delta)
  is computed, preventing look-ahead. The **lag-before-derived-signal
  ordering is load-bearing** and is verified empirically in every
  regime strategy.
* **No bridge changes.** Macro / GTAA uses continuous
  `TargetPercent` semantics throughout; the bridge is byte-identical
  to its post-Session-2F state.

## 8. Adversarial review answers

**Q: Did any strategy fabricate Sharpe numbers?**
A: No. Every `benchmark_results.json` is explicitly labeled
`synthetic-fixture` with a note that real-feed verification is
deferred to Session 2H, and that synthetic Sharpes differ from the
papers' published ranges. No paper Sharpe is presented as an in-repo
result.

**Q: Were substrate deviations from the source papers documented?**
A: Yes, each in three places (paper.md "Implementation deviations"
+ known_failures.md + amendments.md): `yield_curve_regime_allocation`
uses the 2s10s slope (DGS10−DGS2) instead of EH 1991's 10y-3m
because DGS3MO prints 0.0 in ZIRP; `growth_inflation_regime_rotation`
consumes the GDP *level* (GDPC1) instead of the growth-*rate* series
because the rate goes negative and would trip the bridge. The 2s10s
↔ 10y-3m ~0.9 correlation is documented so the ρ≈0.50–0.70 cluster
prediction survives the substitution.

**Q: Was the publication-lag discipline actually enforced?**
A: Yes, and tested. `test_publication_lag_applied_to_cpi_column`
(growth_inflation) and `test_publication_lag_applied_before_yoy`
(inflation_regime) verify that `lag=0` and `lag=1` produce different
regime classifications around a sharp signal move, proving the lag
is applied before the YoY computation.

**Q: Did the install-pipeline wiring preserve backwards
compatibility?**
A: Yes. All 98 pre-Session-2G strategies remain discoverable and
unchanged; the only discovery change is appending `"macro"` to
`FAMILIES` and bumping the count guard 98 → 109. The pip-installed
layout was validated 6/6 on `verify-install`.

**Q: Were citations rigorous?**
A: Yes. All foundational + primary DOIs were verified at the Gate-1
pre-flight; folklore attributions (Bridgewater All-Weather) were
dropped in favour of peer-reviewed anchors. Reused papers
(Ilmanen-Maloney-Ross 2014) share a single bibtex entry.

## 9. Deliberate-redundancy pairs

| Pair | Expected ρ | Differentiation |
|---|---|---|
| `risk_parity_erc_3asset` ↔ `permanent_portfolio` | 0.60–0.75 | Both multi-asset allocators with a low-vol-overweight tilt; ERC adapts to the rolling covariance while PP is static 25/25/25/25 |
| `recession_probability_rotation` ↔ `yield_curve_regime_allocation` | 0.50–0.70 | The yield-curve slope is a primary input to the Cleveland Fed recession-probability model, so the two trade overlapping signal; bidirectionally documented in both `known_failures.md` files |

Both pairs sit well below the Phase 2 master plan §10
deduplication-review bar (ρ > 0.95) and are documented as deliberate
methodology pairs. Cluster-detection methodology will surface these
at v0.2.0.

## 10. Notable mid-session events

* **Commit 2 bridge-cadence methodology pause** — discovered that
  forward-filling target weights to every bar makes the bridge
  perform daily drift-correction, not discrete monthly rebalancing.
  Chose to *document the reality* as an AlphaKit-wide convention
  (Option B) rather than re-architect; flagged a sparse-rebalance
  protocol as a Phase 3 candidate.
* **Commit 9 bridge-positivity fix** — the GDP growth-rate series
  (A191RL1Q225SBEA) goes negative in recessions and tripped the
  vectorbt `order.price > 0` assertion. Switched to the GDPC1 level
  and compute YoY internally.
* **Commit 10 bridge-positivity fix** — DGS3MO prints exactly 0.0 on
  ZIRP days; switched the short leg to DGS2 (always carries a term
  premium). The general rule (pass positive raw series, derive
  signals internally) was promoted to a project-wide amendment.
* **Stale-forward-reference catch** — Commit 9's known_failures.md
  forward-referenced Commit 10 with the pre-decision `T10Y3M` spec;
  caught and corrected (`20f4454`) at the pre-Commit-13 spot-check.
* **Test-assertion footgun** — `pandas.Series == pytest.approx(scalar)`
  does not compare element-wise (returns all-False); switched to
  direct float equality for exactly-assigned regime weights, and to
  calendar-month-aligned synthetic panels to avoid `resample("ME")`
  / 21-day-block misalignment.
* **CI dispatch-input mistake** — the first `verify-install`
  dispatch referenced a tag (`v0.1.999-rc-session2g-verify`) that
  was never pushed to origin, so every job failed at `git fetch`.
  Re-dispatching with the branch ref (`claude/2g-macro-family`)
  resolved it; a local repro of the exact git-install sequence had
  already proven the branch installs cleanly (12/12 packages, macro
  import OK, discovery 109).

## 11. Process lesson — substrate-deviation discipline and sibling forward-references

Two complementary lessons reinforced this session:

1. **Substrate-deviation discipline.** When the data feed or bridge
   forces a deviation from a paper's exact specification, the
   deviation must be documented in three places (paper.md
   "Implementation deviations", the strategy's known_failures.md, and
   docs/phase-2-amendments.md) **and** the deviation's effect on any
   cross-strategy cluster prediction must be re-confirmed. The
   DGS3MO→DGS2 substitution is the canonical example: it is only
   defensible because 2s10s is ~0.9-correlated with 10y-3m, which
   preserves the documented ρ≈0.50–0.70 with
   `recession_probability_rotation`.

2. **Sibling forward-references go stale.** A known_failures.md that
   forward-references a not-yet-implemented sibling commit will
   describe the *planned* decision, which can diverge from the
   *shipped* decision. The fix: at session close (or at the gate
   before the install-pipeline commit), grep sibling cross-references
   for the slug names finalized later in the session and reconcile
   them. This session's `T10Y3M` catch is the example.

Inherited and applied from Session 2F: gate-3 review should include
any strategy that introduces a NEW state primitive (here, the
informational-column + publication-lag pattern was reviewed at the
first regime-state strategy, `recession_probability_rotation`).

## 12. CI configuration item (v0.2.0 release-prep candidate — NOT actioned in 2G)

* **CI-trigger gap:** `verify-install.yml` runs only on
  `push: tags: v*` and `workflow_dispatch`, so it does not auto-run
  on PRs to `main` and requires manual dispatch at PR time.
* **Dispatch-input lesson:** a `workflow_dispatch` `tag` input must
  reference a ref that exists on origin. The branch-ref dispatch
  (`tag=claude/2g-macro-family`) is the clean, documented workaround
  — it validates the exact branch SHA without leaving a throwaway tag
  on origin.
* **Proposed fix (deferred to v0.2.0):** add a `pull_request: [main]`
  trigger to `verify-install.yml` (~30 min/PR added compute, 6 jobs)
  to eliminate the manual-dispatch dependency.
* **Decision:** tracked here as a v0.2.0 release-prep candidate; not
  a Session 2G amendment and not actioned in this PR.

## 13. Pace summary

* Forecast: ~12–14 hours.
* Actual: ~14–16 hours.
* Overhead from three investigations: the Commit 2 bridge-cadence
  methodology pause, the Commit 9/10 bridge-positivity deviations
  (GDP rate→level, DGS3MO→DGS2), and the Commit 13 CI dispatch-input
  issue.
* Net drift: modest and within tolerance; the overhead was genuine
  correctness / documentation work, not noise.

## 14. Session 2H readiness

* **1 strategy family remaining** to complete Phase 2.
* **Real-feed benchmark run (Session 2H)** replaces all "deferred to
  2H" entries in `docs/papers/phase-2.md`, including the macro
  family's synthetic-fixture benchmarks.
* **Cluster-detection methodology** should surface the two
  deliberate-redundancy pairs from §9 (plus prior-session pairs).
* **No new feeds expected** for the remaining family unless its
  signal requires one.
* Apply the substrate-deviation and sibling-forward-reference
  lessons from §11.

## 15. v0.2.0 release readiness checklist

* [ ] Final Phase 2 family shipped (Session 2H).
* [ ] All Phase 2 amendments documented (running tally in
  `docs/phase-2-amendments.md`).
* [ ] Cluster-detection methodology runs (surfaces all
  deliberate-redundancy pairs across Sessions 2D–2H).
* [ ] Real-feed benchmark runs (Session 2H — replaces all
  "deferred to 2H" entries in `phase-2.md`).
* [ ] **Add `pull_request: [main]` trigger to `verify-install.yml`**
  (CI-trigger gap from §12).
* [ ] v0.2.0 release notes (architectural extensions: covariance
  helper Session 2G, informational-column + publication-lag pattern
  Session 2G, `synthetic-options` adapter Session 2C, `discrete_legs`
  Session 2F).
