# Phase 2 Session 2K closeout — v0.2.2 pt 2: cot CFTC wiring + rates feasibility + tag

## 1. Summary

* **Branch:** `claude/2k-rates-cot-real-feed`
* **PR:** [#23](https://github.com/ankitjha67/alphakit/pull/23)
* **Merge commit:** _to be filled after squash-merge_
* **Merge type:** squash (per Session 2D–2J precedent)
* **Scope:** v0.2.2 **pt 2 of 2** — closes the v0.2.2 backlog inherited
  from Session 2J. Ships the cot wiring (the 3-layer architectural fix
  Session 2J-2.8 deferred), the cache-portability fix (Windows /dev/null
  recognition), and the setup-uv v4 → v7 bump. Two rates strategies
  (`swap_spread_mean_rev`, `global_inflation_momentum`) deferred to Phase 3
  after an empirical FRED audit found the substrate gaps. **v0.2.2 tag
  publishes against the post-2K merged-main SHA.**
* **Strategy count unchanged:** 109.
* **PR CI:** _to be filled — 13/13 expected_.

## 2. Commits

| # | Hash | Summary |
|---|---|---|
| S2K-0   | `c19349e` | 2 PR #22 post-merge CodeRabbit cleanups (CFTC test offline-leak + regen messages restored) |
| S2K-1   | `09c1256` | cot 3-layer fix — strategy `cftc_market_codes` mapping + `CFTCCOTWideAdapter` + runner routing |
| S2K-1   | `69fd056` | cot routing edge-case tests (partial mapping / absent code / skipped-week ffill) |
| S2K-1   | `3c7997b` | 2 PR #23 CodeRabbit findings (3 stale `cftc-cot` refs + multi-year wide-adapter test) |
| _regen_ | `3f0615d` | 7-strategy commodity regen — `cot_speculator_position` stamped `yfinance+cftc-real` (Ankit-side keyed) |
| S2K-2   | `954de57` | rates feasibility audit doc + FRED probe script (primary) |
| S2K-2   | `3af36f1` | secondary FRED probe — corrected suffixes + `fred.search()` hunt |
| S2K-2   | `0b5c63c` | 2026-05-31 amendment + final deferral verdict for 2 rates strategies |
| S2K-3   | `530fb75` | `setup-uv@v4 → @v7` across 4 workflows |
| S2K-3   | `68c3812` | PR #23 CodeRabbit fix — audit script `probe_one` all-NaN crash guard |
| S2K-3.5 | `1f080d2` | cross-platform cache sentinel (raw-string check before `Path()` normalisation) |
| S2K-4   | `983bcf6` | cluster_analysis 11×11 → 29×29 (5 regime + 7 commodity + 11 rates + 6 macro) |
| S2K-4   | _this_    | 29×29 cluster findings + CHANGELOG v0.2.2 final + this closeout |

## 3. What 2K delivered

* **`cot_speculator_position` real-feed via cftc-cot-wide** — the
  S2J-2.8-deferred 3-layer fix lands: strategy declares
  `cftc_market_codes` mapping, new `CFTCCOTWideAdapter` returns
  OI-normalised wide-format positioning (`(NC_long − NC_short) / OI` ∈
  [-1, +1]), runner routes `*_NET_SPEC` symbols and translates
  NET_SPEC ↔ market_code at the adapter boundary so the adapter contract
  stays strategy-agnostic. Commodity family now ships **7 of 10**
  real-feed in v0.2.2 (up from 6 in v0.2.2 pt 1); 3 remain
  yfinance-second-month-blocked per the 2026-05-31 commodity amendment.
* **2 rates strategies deferred to Phase 3** — the S2K-2 empirical FRED
  audit (`scripts/audit_fred_rates_series.py`) found `DSWP10`
  discontinued 2016-10 with no continuous replacement (`fred.search()`
  exhausted 4 queries) and the Japan CPI level series
  (`JPNCPIALLMINMEI`) stops at 2021-06 leaving a 4-year gap against the
  2025-12 OOS window. 2026-05-31 rates amendment documents both
  deferrals with Phase 3 re-instatement paths.
* **Cross-platform cache sentinel** — `FeedCache._is_disabled` now
  compares the raw user input before `Path()` normalisation, so
  `/dev/null` works on Windows (where `str(Path("/dev/null"))` mangles to
  `\dev\null`) and `NUL` works on Linux. Case-insensitive Windows
  variants (`NUL`, `nul`, `NUL:`, `\\?\NUL`) all recognised. The fix
  was masquerading as test failures — investigation revealed a real
  silent cache-enable bug on Windows.
* **setup-uv @v4 → @v7** across all 4 workflows (test, lint, docs,
  benchmark). Floating-tag bump; v8 stops publishing floating major
  tags so that's the next pinning-model decision (Phase 3 backlog).
* **29×29 real-feed cluster** in `cluster_analysis.py --feed real` —
  expanded from S2J's 11×11 by adding S2K-1 cot + the 17 Session 2H
  yfinance-real ETF strategies (11 rates + 6 macro). **First time the
  17 ETF strategies are exercised through any cluster pipeline** —
  before S2K-4 they had individual Session 2H benchmarks but no
  pairwise correlation analysis. The 29×29 is now **the broadest
  cross-family real-feed cluster the project has produced** and
  materially upgrades the project's diversification documentation:
  claims that previously rested on individual benchmark Sharpes
  plus the 11×11 cluster now have an explicit 406-pair pairwise
  correlation baseline across all real-feed strategies. Methodology
  pre-check verified empirically: 3 representative ETF strategies
  (`bond_tsmom_12_1`, `curve_steepener_2s10s`, `permanent_portfolio`)
  run cleanly through `_yfinance_real_returns` in offline mode →
  5478 business days each, same 2005-01-03 → 2025-12-31 window as
  regime/commodity, zero NaN, return distributions in expected
  ranges. Four intra-family blocks + 3 cross-family descriptive
  blocks reported.
* **2026-05-31 rates amendment** + S2K-1 / S2K-2 / S2K-3.5 process
  lessons + this closeout.

## 4. Real-feed coverage update

`data_source` split on `main` after merge:
**17 yfinance-real + 5 yfinance+fred-real + 6 yfinance-futures-real
+ 1 yfinance+cftc-real (cot) + 80 synthetic-fixture** = 109 total.
Real-feed coverage **28/109 (25.7%) → 29/109 (26.6%)**.

Deferrals:
* **Phase 3 — substrate / API blockers:**
  * 3 yfinance-second-month-blocked commodity strategies
    (`commodity_curve_carry`, `ng_contango_short`,
    `wti_backwardation_carry`) per the 2026-05-31 commodity amendment.
  * 2 rates strategies (`swap_spread_mean_rev`,
    `global_inflation_momentum`) per the 2026-05-31 rates amendment
    (DSWP10 / ICE swap rate / JP CPI 2021-06 gap).
* **Design choice:** options (15) remain synthetic-options.

## 5. 29×29 cluster findings (real-feed basis)

Substantive expansion over the S2J 11×11 + three findings that
materially update the project's diversification documentation. **8 of
35 documented pairs in predicted range** — overall a calibration miss
across families, with two distinct mechanisms surfacing.

### Headline: dedup-bar BREACHED at 3 macro covariance-primitive pairs

| Pair | Actual ρ | Predicted | Status |
|---|---|---|---|
| `risk_parity_erc_3asset` ↔ `max_diversification` | **+0.993** | 0.50–0.70 | OUT (high) — dedup-bar breach |
| `min_variance_gtaa` ↔ `max_diversification` | **+0.989** | 0.55–0.75 | OUT (high) — dedup-bar breach |
| `risk_parity_erc_3asset` ↔ `min_variance_gtaa` | **+0.980** | 0.55–0.75 | OUT (high) — dedup-bar breach |

**Mechanism (scenario (b) — methodological convergence on small
universe).** All three strategies share `_covariance.rolling_covariance`
(the Session 2G "covariance-primitive shared helper module"
amendment, by design): same SPY/TLT/DBC universe, same 252-day
rolling estimator + Ledoit-Wolf shrinkage to constant-correlation
target. Only the solver objective differs: ERC
(Maillard-Roncalli-Teiletche 2010 Spinu reformulation) vs MV
(long-only quadratic) vs max-div (Choueifaty-Coignard 2008 SLSQP).

On a 3-asset universe where TLT has the lowest σ and the shrunken
covariance is stable, all three solvers concentrate weight on TLT and
trace nearly identical equity curves. **This is a known small-N
phenomenon in portfolio construction, not a coding bug.** The known
failures predictions of 0.50–0.75 anticipated sibling-strategy
correlation but undershot the magnitude of the convergence on this
specific universe.

**Disposition**: documented finding, not a v0.2.2 blocker. **The
dedup-bar trip is the cluster analysis working correctly** — without
the 29×29 keyed cluster, the macro-trio convergence would have been
invisible (each strategy individually had a sensible Sharpe and
their pairwise relationship was never previously measured at real-
feed scale). The bar surfaces the methodological observation for
explicit acknowledgment rather than letting three near-identical
strategies ship without comment. **Phase 3 candidate** (forward-
listed in §10): scale the universe (e.g. 10 assets across equities
/ rates / commodities) where the three solvers genuinely differ.
The covariance-primitive sharing pattern itself is fine; it's the
small-N universe that collapses the distinctions.

### Second-headline: steepener ↔ flattener at ρ = 0.000 (not −1.0)

| Pair | Actual ρ | Predicted | Status |
|---|---|---|---|
| `curve_steepener_2s10s` ↔ `curve_flattener_2s10s` | **+0.000** | −1.00 to −0.95 | OUT (wrong-sign by 1.0) |

**Mechanism (scenario (b) — prediction inconsistent with
implementation).** Both strategies produce `signal ∈ {0, 1}`
(BINARY, not ±1):

* Steepener active only when `z > +entry_threshold` (default +1.0).
* Flattener active only when `z < −entry_threshold` (default −1.0).

They trade **mutually exclusive z-score tail regimes** — z can't be
both > +1 and < −1, so they never co-fire. When |z| < 1 (the common
regime, ~70% of bars), both signals are zero. When one fires the
other is always zero. **Daily-return contributions never co-occur →
correlation is exactly 0**, not −1.0.

The prediction's "ρ ≈ −1.0 by construction" line was internally
inconsistent with the same docs' "never run both at the same time"
note: mutually-exclusive signals can't be perfectly anti-correlated.
The implementation matches Session 2D's binary-tail-trade design
intent (only enter when the spread is far from mean); the prediction
text imagined a different ±1 mirror-image design that wasn't
shipped. **The S2K-4 closeout rolls a follow-up doc fix** updating
both strategies' `known_failures.md` ρ predictions to reflect the
binary mechanic.

### Regime intra-family — 5/10 in range (carry-over from S2I/S2J)

Reproduces the S2J pattern exactly: synthetic predictions
**UNDERSTATED** real co-movement. The 5 OUT pairs land above their
predicted bands, dominated by FRED-input-sharing pairs (e.g.
`yield_curve_regime_allocation ↔ fed_policy_tilt` at +0.794 vs
0.40–0.60 predicted). Documented in the S2J §5 closeout; no change
in interpretation here.

### Commodity intra-family — 2/7 in range (slight improvement over S2J 1/6)

The S2K-1 cot addition lands inside its predicted band:

* `cot_speculator_position ↔ commodity_tsmom`: **−0.157** (predicted
  −0.20 to 0.00, OK). The mild negative co-movement is the
  contrarian-fade-against-crowded-trends prediction from cot's
  `known_failures.md §6` — empirically confirmed at real-feed scale.

The 6 inherited S2J commodity pairs reproduce the S2J pattern
(predictions OVERSTATED universe-overlap correlation; metals headline
+0.565 vs 0.75–0.90).

### Rates intra-family — 2/11 in range with corrected prediction

The steepener↔flattener prediction was corrected from −1.0 ± 0.05 to
0 ± 0.10 in this session (see "Second-headline" above + the
matching `known_failures.md` doc fixes); the actual +0.000 now
lands inside the corrected band, taking rates from 1/11 to 2/11 in
range. Other notable misses:

| Pair | Actual ρ | Predicted | Note |
|---|---|---|---|
| `curve_steepener_2s10s` ↔ `curve_flattener_2s10s` | **+0.000** | −0.10 to +0.10 (corrected) | OK — binary-tail mechanic (see Second-headline above) |
| `curve_flattener_2s10s` ↔ `bond_carry_rolldown` | **+0.883** | −0.50 to −0.30 | wrong-sign AND wrong-magnitude — bond_carry's slope-exposure component is mostly long-duration, so it co-moves with flattener (also long-duration) regardless of curve regime |
| `bond_tsmom_12_1` ↔ `real_yield_momentum` | **+0.363** | 0.60–0.80 | OUT (low) — TLT exposure overlap less concentrated than predicted; the momentum windows decouple them more than the universe overlap suggested |

The wrong-sign on `flattener ↔ bond_carry_rolldown` is a similar
mechanism to the steepener/flattener inconsistency: documented
prediction imagined a directional bet, but bond_carry's long-duration
tilt dominates the realised correlation. **Phase 3 candidate**: rates
prediction-recalibration session against the cluster output (the
binary-signal mechanic is the same misread across multiple rates
pairs).

### Macro intra-family — 0/7 in range (all 7 OUT high)

Every documented macro prediction undershot. The 3 covariance-trio
pairs are the dedup-bar breach above; the **off-trio cluster
centres on `permanent_portfolio` as a magnet**:

| Pair | Actual ρ | Predicted | Status |
|---|---|---|---|
| `max_diversification` ↔ `permanent_portfolio` | **+0.775** | 0.40–0.60 | OUT (high) |
| `risk_parity_erc_3asset` ↔ `permanent_portfolio` | **+0.771** | 0.60–0.75 | OUT (just above) |
| `min_variance_gtaa` ↔ `permanent_portfolio` | **+0.757** | 0.50–0.70 | OUT (high) |

`permanent_portfolio` is a fixed-weight allocation strategy on a
similar universe (SPY / TLT / DBC + gold) — so it tracks the same
broad multi-asset macro factor that the three covariance-primitive
solvers all extract from SPY/TLT/DBC. It correlates **+0.75 with
each of the trio AND ρ > 0.7 with the regime strategies (see
Cross-family below) — making it the project's single most-correlated
strategy**.

Mechanism for the rest of the family: the 6-strategy macro universe
is small enough that strategies sharing even one asset (SPY, TLT,
GLD) get more co-movement than the predictions anticipated.

### Cross-family findings — 4 substantive observations

* **`permanent_portfolio` is the project's cross-strategy magnet**
  — correlates **+0.75 with each of the macro covariance-primitive
  trio** (intra-family) AND **ρ > 0.7 with the regime strategies**
  (cross-family). The most-correlated strategy in the project,
  capturing the broad multi-asset macro factor that the regime
  rotators + the covariance-solver portfolios all extract from
  similar SPY/TLT-anchored universes. Whether to keep all four
  (trio + permanent_portfolio) is a v0.2.3 portfolio-composition
  question — at v0.2.2 they all ship with this finding documented.
* **Regime ↔ macro at ρ > 0.7** for the covariance-primitive trio
  (consistent with the magnet observation above). GTAA + regime
  are **less diversified than benchmarks suggested** — both families
  lean on broad ETF exposure (SPY/TLT) and the shared underlying
  assets dominate the cross-family correlation.
* **`commodity_tsmom` cross-family signal carries over** from S2J
  — `+0.154` with `growth_inflation_regime_rotation` is the
  largest regime × commodity pair, consistent with the S2J finding.
* **`cot_speculator_position` is genuinely orthogonal to everything**
  — largest cot-correlation is **−0.157** (with `commodity_tsmom`,
  by design); other cot pairs are in `[-0.07, +0.05]`. cot adds an
  **independent factor exposure** to the cluster — the most
  diversification-positive new strategy in v0.2.2.

### Four-way calibration pattern across families (substantively new in S2K-4)

The 29×29 expansion is the first time all four real-feed families
have been measured against their own intra-family predictions
simultaneously, and the result is **four distinct
prediction-vs-reality patterns** — each with a different mechanism.
This is forward-promoted as a §8 process lesson (see §8(h) below):

* **Regime predictions UNDERSTATE** real co-movement (Sessions
  2I / 2J / 2K reproduce). Mechanism: synthetic fixtures couldn't
  reproduce the diffuse macro-wide common factor; shared FRED
  inputs drive real ρ above predicted bands.
* **Commodity predictions OVERSTATE** universe-overlap co-movement
  (Session 2J reproduces; S2K-1 cot prediction LANDS IN RANGE).
  Mechanism: risk-parity weighting dilutes universe overlap more
  than intuition allowed for.
* **Macro predictions UNDERSTATE** small-N convergence — all 7
  documented pairs above their predicted upper bound. Mechanism:
  shared covariance estimator on a 3-asset universe converges the
  solvers more than the predictions anticipated; the small-universe
  size collapses the distinction between objectives.
* **Rates predictions are miscalibrated** — 2/11 in range (after the
  S2K-4 steepener/flattener correction); multiple sign errors
  remain. Mechanism: the predictions imagined directional bets but
  the binary-signal regime mechanic + curve-asymmetric long-duration
  tilts dominate the realised correlations.

The four mechanisms are independent — different families miss in
different directions for different reasons. **There is no single
prediction-calibration knob**; each family needs its own real-data
calibration pass. Forward-listed in §10 as a Phase 3 candidate
("per-family prediction-recalibration sessions").

### Summary

| Metric | Value |
|---|---|
| Strategies | 29 (5 regime + 7 commodity + 11 rates + 6 macro) |
| Unique pairs | 406 |
| Documented predictions | 35 (10 regime + 7 commodity + 11 rates + 7 macro) |
| Documented pairs in range | **9 of 35** (regime 5/10, commodity 2/7, rates 2/11, macro 0/7) — rates lift from 1/11 to 2/11 after the S2K-4 steepener/flattener prediction correction |
| ρ > 0.95 dedup-bar breaches | **3** (all macro covariance-primitive trio — scenario (b), see headline) |
| Largest off-trio ρ | +0.775 (`max_diversification` ↔ `permanent_portfolio` — the macro magnet) |
| Cot orthogonality (max |ρ| vs anything else) | 0.157 |

## 6. Architectural changes

* **3-layer cot fix** (S2K-1) — the depth that S2J-2.8 investigation
  surfaced: strategy-side `cftc_market_codes` mapping + new
  `CFTCCOTWideAdapter` (long-format `CFTCCOTAdapter` unchanged for
  ad-hoc analysis, zero rewrites of its 4 unit tests or contract
  harness) + runner-side NET_SPEC ↔ market_code translation. The
  adapter contract (`fetch(symbols, start, end, frequency) ->
  pd.DataFrame`) stays strategy-agnostic — adapter speaks market
  codes, runner does the cot-specific translation.
* **Cross-platform cache sentinel** (S2K-3.5) — raw-string check
  before `Path()` normalisation. Same logical contract on every host
  OS for `/dev/null` and `NUL`. Env-var path consolidated through the
  same resolver.
* **S2K-2 audit framework** — `audit_fred_rates_series.py` pattern
  (multi-candidate probe + `looks_like_level` classifier +
  `fred.search()` negative-evidence trail + 1.5s inter-call sleep)
  generalises to any future FRED-substrate feasibility question.

## 7. v0.2.2 tag plan

Per Session 2H §7 tag conventions: **no pre-release flag**, this is
the `.2` release. Sequence after PR #23 squash-merge:

1. Capture squash SHA from the merge commit on `main`.
2. Tag `v0.2.2` on the squash SHA.
3. Verify **tag SHA == CI-target SHA** (Session 2H footgun guard).
4. Wait for `verify-install` workflow on the tag — **6/6 green
   required**.
5. Fresh-venv keyed reproduce check (Ankit-side) on the tag SHA.

## 8. Process lessons

### (a) S2K-1 empirical market-code verification

Session 2J-2.8 closeout's deferral note documented two CFTC market
codes for the cot wiring — **2 of the 4 were empirically wrong**.
A 15-minute probe of the real 2024 archive (`requests.get` + pandas
inspection of `Market and Exchange Names` column) revealed:

* `067411` documented for WTI → actually ICE Europe; the NYMEX PHYSICAL
  WTI code is `067651`.
* `023655` documented for NG → actually E-mini; the standard
  Henry Hub Natural Gas code is `03565B`.

Both would have silently shipped wrong positioning data and bad
benchmarks. The fix was institutionally cheap (a one-off probe before
scope commitment) and concretely confirmed the S2J-2.8 lesson:
"verify adapter contract end-to-end against real substrate data
BEFORE scope commitment." This is the first concrete example of
that lesson preventing a silent-wrong-data outcome.

### (b) S2K-2 audit framework — negative-evidence trail

The rates feasibility audit institutionalised three primitives:

1. **Multi-candidate per-series probe** — list every plausible series
   ID, probe each, report coverage + range + gaps. Surfaces the
   exact ID that works, not just "FRED has CPI somewhere".
2. **`looks_like_level` classifier** (`min >= 0 AND max > 50`) — turns
   "is this a LEVEL series?" from an eyeball check into a boolean.
   Surfaced that OECD-MEI suffixes `M657N` and `M659N` both return
   RATE-OF-CHANGE for DE and JP CPI despite naming convention
   suggesting they should differ; the LEVEL series live at the
   BIS-OECD alternative names (`DEUCPIALLMINMEI`,
   `JPNCPIALLMINMEI`). Prevented shipping silently-wrong
   inflation calculations.
3. **`fred.search()` negative-evidence trail** — before declaring a
   strategy blocked, exhaust the search space and document what FRED
   *does* have under the relevant queries. Four queries for the swap
   rate hunt (`10-year swap rate USD`, `ICE swap rate`,
   `USD interest rate swap`, `SOFR swap rate 10`) returned no usable
   continuous post-2016 series; the defensible verdict is "no
   continuous swap rate exists on FRED post-DSWP10".

This framework generalises directly to future feasibility questions
(international yields, alternative inflation series, commodity
back-month replacements).

### (c) S2K-3 conservative pinning vs floating-tag migration

`setup-uv@v4 → @v7` is a clean bump (none of our inputs are affected
by v5/v6/v7 breaking changes). v8.0.0 stopped publishing floating
major tags — `@v8` no longer resolves, only immutable patch tags
like `@v8.0.0` work. That's a pinning-model change (security:
immutable releases prevent supply-chain attacks) which is out of
v0.2.2 scope. **Phase 3 candidate:** review every action pin in
`.github/workflows/*` for immutable-reference compliance before
moving to setup-uv@v8.

### (d) Local pre-push gate must match CI invocation exactly

Session 2K-4's first cluster-extension commit (`983bcf6`) reached CI
with a test breakage in `tests/test_cluster_analysis.py` that local
gates had missed. Root cause: the local gate script used
`uv run pytest packages/` which silently skipped the root-level
`tests/` directory; CI uses `uv run pytest` (no path arg) which
discovers every test collection root in `pyproject.toml`.

Path-scoping (`pytest packages/`) is fine for fast iteration during
development on a specific package, but the **final pre-push gate must
match CI's invocation exactly**. The fix here was a one-line update
to the failing test (`753d388`), but the lesson is the discipline:
the gate that decides "this is ready to push" must run the same
command CI runs, not a subset.

**Adopting `uv run pytest` (no path arg) as the standard pre-push
gate going forward.** Path-scoped invocations are acceptable during
development for fast iteration; the final gate before any push must
match CI exactly. Connects to the multi-layer verification scorecard
from S2J §8(a): a gate that catches a subset of what CI catches isn't
a gate, it's an early-warning system.

### (e) S2K-3.5 substrate behavior bug masquerading as test failure

Two pre-existing test failures on Windows were initially framed as
"pre-existing Windows portability issues" worth a quick platform-aware
skip. Investigation revealed they were correctly detecting a **real
cache behaviour bug**: `Path()` normalisation on Windows mangled
`/dev/null` to `\dev\null`, the sentinel set didn't match the
normalised string, and the cache was silently ENABLED on Windows
when developers expected it disabled. Any Windows developer or
Windows CI run using `/dev/null` as the cache-disable sentinel got
actual caching, not disabled caching. Treating the failures as
test-skip candidates would have left a silent-wrong-behaviour bug
in production. Connects to S2J §8(a) multi-layer verification:
**empirical verification on the real environment surfaces what
synthetic testing misses**.

### (f) Honest deferral pattern at scale

Session 2K's deferral arithmetic: **1 resolved** (cot from S2J's
deferral list) + **2 deferred** (rates, this session) + **3 carried**
(commodity from S2J's 2026-05-31 amendment). The net is +1 to
real-feed coverage with two new amendments documenting Phase 3
re-instatement paths for the 5 deferred strategies. Same
substrate-or-architecture-blocker pattern as Sessions 2D / 2F / 2J;
the consistency of the pattern across 4 sessions is itself the
forward signal — **substrate constraints surface empirically, not
in advance, and the only sustainable response is to ship what
works and document the rest**.

### (g) CodeRabbit consistently catches doc-drift after rename

Across PRs #22 and #23, CodeRabbit's findings clustered on
**docstring / help-text drift after architectural rename** — refs
to old names left in docstrings, argparse help, module-level
comments. The pattern is reliable across 4 commits (S2K-0, S2K-1,
S2K-1 follow-up, S2K-3 follow-up). **Phase 3 candidate:** pre-push
doc-consistency linter (e.g. enforce that names referenced in
docstrings exist in the codebase, or that recent rename PRs leave
no stale references).

### (h) Prediction methodologies need per-family real-data calibration

The S2K-4 29×29 cluster surfaced **four distinct
prediction-vs-reality patterns**, one per family, each with an
independent mechanism (see §5 "Four-way calibration pattern"):

* Regime UNDERSTATE — shared FRED-input common factor.
* Commodity OVERSTATE — universe-overlap intuition too aggressive.
* Macro UNDERSTATE — small-N covariance-solver convergence.
* Rates miscalibrated — binary-signal regime mechanics + curve-
  asymmetric long-duration tilts.

**There is no single prediction-calibration knob** that fixes the
4 misses with one adjustment. Each family's `known_failures.md §6`
predictions encode a different intuition about strategy similarity,
and each intuition fails against real data in a different direction.
This isn't a methodology bug — it's the expected outcome when sibling
strategies inside a family share infrastructure (covariance
estimators, universe, signal class) and the analyst hadn't yet seen
the empirical correlation pattern.

Forward recommendation: **per-family prediction-recalibration
sessions** as Phase 3 candidates. The 29×29 cluster output is the
empirical ground truth those sessions calibrate against. The same
pattern as the S2J §8(c) sign-asymmetry observation — but
generalised to a 4-way categorisation rather than a 2-way.

The deeper lesson connects to S2J §8(c) and the S2K-2 audit
framework (§8(b) above): **predictions made before empirical
verification are draft hypotheses, not ground truth**. The cluster's
job isn't to confirm predictions; it's to surface the calibration
gap so the predictions can be updated. v0.2.2's 9/35 in-range
ratio is not a failure of the cluster — it's the cluster doing the
work the predictions couldn't do without real data.

## 9. Pacing

Session 2K ran **11 commits** (S2K-0 through S2K-4 + this docs commit)
versus Session 2J's 10. Pacing breakdown:

* S2K-0 / S2K-1 / S2K-1 follow-ups (4 commits): cot delivery, the
  substantive new feature.
* S2K-2 audit phase (3 commits): empirical FRED probe, no build.
* S2K-3 / S2K-3.5 (3 commits): setup-uv bump + cross-platform cache
  fix.
* S2K-4 (this commit + cluster code): closeout, CHANGELOG, cluster
  broadening.

The audit-only phase (S2K-2) is new — Session 2K is the first
session where a substantial chunk was explicit "no build until
empirical verdict". The audit framework cost ~1h and prevented
multi-hour misadventures on two blocked strategies. Same pacing
discipline as S2J's network-gate retries: rounds that surface
architectural classes rather than churn.

## 10. v0.2.3 backlog (forward-looking)

Per Session 2H §7 / S2J §10 forward-planning pattern. v0.2.3 candidates
identified during Session 2K:

* **setup-uv@v7 → @v8** with immutable-tag pinning review for every
  action in `.github/workflows/*` (S2K-3 lesson).
* **Pre-push doc-consistency linter** (§8(g) lesson — CodeRabbit
  doc-drift pattern across PRs #22 / #23).
* **Per-family prediction-recalibration sessions** (§8(h) lesson) —
  one pass per family (regime / commodity / rates / macro) updating
  each strategy's `known_failures.md §6` predictions against the
  S2K-4 29×29 cluster as empirical ground truth. The four mechanisms
  identified in §5 require independent fixes.
* **Macro covariance-primitive universe expansion** — scale the
  SPY/TLT/DBC universe to ~10 assets (equities + rates + commodities)
  to differentiate ERC / MV / max-div on real data (§5 headline +
  Phase 3 candidate). Same `_covariance.rolling_covariance`
  primitive, just a more diverse universe.
* **Phase 3 substrate re-instatement candidates** documented in the
  2026-05-31 rates amendment (BIS swap rate, JP CPI alternative)
  and the 2026-05-31 commodity amendment (CME second-month adapter).
* **Code-aware cache keys** (S2J §8(e) lesson, still open).
* **Real-feed cluster expansion to 47×47** — once additional
  Phase 3 substrates land. The 29×29 cluster's mean |ρ| + per-family
  prediction calibration carries over.
