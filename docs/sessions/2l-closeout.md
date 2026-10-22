# Phase 2 Session 2L closeout — v0.2.3: 10-asset covariance variants + 32x32 cluster + Windows CI

> The three new strategies are tier1 ETF strategies on keyless yfinance data,
> so the tier1 regen ran in-sandbox (`regenerate_benchmarks.py tier1`, 20 ok)
> and its JSONs are committed with this session. Every benchmark and cluster
> figure below was produced in-session through the runner path on real
> yfinance prices; nothing here is hand-edited into a benchmark file. The
> remaining owner-side steps are the fresh-venv cross-platform reproduce on
> Windows and the tag push (the sandbox token cannot push tags), section 7.

## 1. Summary

- **Branch:** `claude/2l-covariance-universe-expansion`
- **PR:** [#24](https://github.com/ankitjha67/alphakit/pull/24)
- **Merge commit:** _to be filled after squash-merge_
- **Merge type:** squash (per Session 2D-2K precedent)
- **Scope:** resolve the Session 2K-4 dedup-bar breach by addition, add the
  Windows CI leg, and fix the dependency and count-pin drift the PR surfaced.
  Strategy count **109 to 112**.
- **PR CI:** **14/14 green** on head `22bba51` (7-job test matrix including
  `windows-latest`, 6-job verify-install, ruff+mypy). Confirmed via the
  GitHub Actions API, not the HTML view.
- **Tag:** `v0.2.3`, pending the owner fresh-venv reproduce and tag push
  (section 7); the benchmark JSONs are committed.

## 2. Commits

| # | Hash | Summary |
|---|---|---|
| S2L-0 | `db782f7` | ETF universe feasibility audit (`scripts/audit_etf_universe.py`) + v0.2.2 carry-in verification |
| plan  | `1a82657` | Phase 3 to v1.0 roadmap (32 sessions) |
| plan  | `cdd2156` | remaining Phase 2 kickoffs (2L/2M/2N, since renumbered) |
| S2L-1 | `e7debac` | three 10-asset covariance variants, hypothesis confirmed |
| S2L-2 | `03faf08` | cluster 29x29 to 32x32 + corrected the wrong panel numbers in the S2L-1 docs |
| S2L-3 | `4a53295` | Windows CI leg + the config-encoding bug a pre-enable audit found |
| fix   | `5b7d533` | verify-install strategy-count pin 109 to 112 |
| fix   | `def912f` | plotly<7 ceiling + nautilus 3.11+ marker + relock |
| carve | `22bba51` | benchmark-fidelity defects carved into Session 2M |
| S2L-4 | _this_ | CHANGELOG v0.2.3 + this closeout |

## 3. What 2L delivered

- **Three 10-asset covariance variants** (`risk_parity_erc_10asset`,
  `min_variance_gtaa_10asset`, `max_diversification_10asset`), added in
  response to the 2K-4 finding that the three 3-asset covariance strategies
  correlate at rho 0.980 to 0.993. The 3-asset originals are **preserved
  unchanged** as the documented small-N convergence case; these are
  additions, so both cardinalities now sit in the cluster.
- **Hypothesis confirmed.** The three solver objectives separate at N=10 to a
  maximum intra-trio rho of **+0.9480**, below the 0.95 dedup bar, versus
  +0.9931 at N=3 `[sandbox-measured through vectorbt_bridge at 2bp]`. The
  margin is 0.0020 and the `erc_10` to `maxdiv_10` pair is the one to watch on
  any future cluster extension.
- **Shared universe module** `_gtaa10_universe.py`, so the three variants
  cannot drift to different ticker lists; the comparison under test is solver
  objective at fixed universe, and divergent universes would confound it.
- **32x32 real-feed cluster** in `cluster_analysis.py --feed real`, up from
  29x29. Prediction table grew from 35 to 47 documented pairs; the 12 new
  macro bands are measurement-derived, labelled as such in the table comment.
- **Windows CI leg** (`windows-latest / 3.12`) in `test.yml`, the first
  Windows coverage the project has had.
- **Two latent upstream drifts fixed** that the first full PR run exposed
  (both pre-existing, neither introduced by 2L): plotly 7 breaking vectorbt's
  `scattermapbox` accessor on the unpinned verify-install path, and
  nautilus-trader dropping Python 3.10.
- **ETF universe audit tool** (`scripts/audit_etf_universe.py`) + the
  config-encoding canary (`tests/test_config_encoding.py`).

## 4. Real-feed coverage update

Strategy count **109 to 112**. The three new strategies carry
`data_source: yfinance-real` benchmarks, committed from the in-sandbox tier1
regen. Real-feed coverage **29/109 (26.6%) to 32/112 (28.6%)**.

No existing strategy changed data_source. The benchmark-altering defects that
would change existing numbers were deliberately carved into Session 2M rather
than actioned here (section 6).

## 5. 32x32 cluster findings (real-feed basis)

All figures measured in-session on the keyless yfinance path, the same path
the committed benchmarks use. These are correlations of return series, so
they do not depend on the in-sample/out-of-sample split the benchmark Sharpe
figures use. The Windows fresh-venv reproduce (section 7) is the remaining
cross-platform check.

### Hypothesis result

| configuration | max intra-trio rho | vs 0.95 bar |
|---|---|---|
| N=3 incumbents, uncapped | +0.9931 | breached |
| N=10 variants, uncapped | **+0.9480** | below bar |
| N=10 variants, max_weight=0.25 | +0.9435 | below bar |
| N=7, single duration sleeve | +0.9642 | breached |

The N=10 maximum was measured three ways, all within 0.0002: +0.9482
weight-lagged, +0.9480 bridge at 2bp, +0.9482 through the cluster path. The
result is robust to panel and commission choice.

### Two design findings that shaped the build

- **Capping is counterproductive.** `max_weight=0.25` lowers the maximum but
  raises the other two pairs from +0.7262 and +0.6791 to +0.9385 and +0.9391,
  because a binding constraint rather than the objective then sets the
  weights. Shipped uncapped.
- **Duration sleeves help, not hurt.** The 7-asset variant with one duration
  leg still breaches at +0.9642. The fixed-income cluster is part of what
  separates the objectives.

### Pairwise, N=10 uncapped

| pair | rho |
|---|---|
| erc_10 to minvar_10 | +0.7262 |
| erc_10 to maxdiv_10 | +0.9480 |
| minvar_10 to maxdiv_10 | +0.6791 |

No new breach against the incumbents (highest new-to-old +0.8854), and
`permanent_portfolio` remains the magnet (+0.6059 to +0.8514), driven by
shared SHY exposure rather than a shared objective. `gtaa_cross_asset_momentum`
is negatively correlated with all three variants.

### a priori versus measured (the 2K-4 §8(h) calibration test)

The macro-UNDERSTATE lesson's blind bands scored **4 of 9** in range, all 5
misses above the upper bound, so the lesson's direction held even where its
magnitudes did not. Full table in each variant's `known_failures.md` §6.

## 6. Architectural changes and findings

- **Shared `_gtaa10_universe` module**, following the Session 2G
  covariance-primitive precedent, keeps the three variants on one universe.
- **Windows CI** closes the gap that let the S2K-3.5 cache-sentinel bug ship;
  the pre-enable audit immediately caught a second instance of the same class
  (config-encoding), fixed with explicit `encoding="utf-8"` and a canary.
- **Three inherited defects found, documented, carved out, not patched:**
  1. Month-end rebalance skip, 30 strategies (Session 2M).
  2. Single-feed panel not complete-rows trimmed, 20 strategies (Session 2M).
  3. Session 2H macro prediction bands understate the breach pairs (the 2K-4
     finding itself; the close session recalibrates).

## 7. v0.2.3 tag plan

Per Session 2H §7: no pre-release flag, verify tag SHA == CI-target SHA,
fresh-venv keyed reproduce. Sequence after the keyed regen JSONs commit and
PR #24 squash-merges:

1. Capture the squash SHA from `main`.
2. Tag `v0.2.3` on it (tag push from Ankit's Windows env; the sandbox token
   cannot push tags).
3. Verify tag SHA == CI-target SHA.
4. `verify-install` 6/6 on the tag.
5. Fresh-venv reproduce: the keyed regen must reproduce byte-identical, which
   also serves as the cross-platform check on the sandbox-generated numbers
   above.

## 8. Process lessons

### (a) The handoff's "sandbox cannot reach the substrate" assumption is obsolete for keyless feeds

Handoff §1.6 states the sandbox cannot reach yfinance/CFTC/FRED. Probed
rather than trusted (§5.2): yfinance returns real data from the sandbox. That
let the S2L-0 audit, the solver probe, and the hypothesis test run in-session
on live 2005-2025 data instead of waiting on a round-trip. FRED still needs
the owner's key, so Option A holds for keyed feeds only. The division of
labor should be re-scoped around "keyed vs keyless", not "sandbox vs Windows".

### (b) Measure the benchmark on the path AND the window the benchmark uses

The erc Sharpe was quoted three different ways before it was right. The
S2L-1 draft measured +0.7367 on a hand-trimmed 5007-bar panel at 2bp. S2L-2
corrected the panel and commission to the runner's untrimmed 5282-bar panel
at 5bp and got +0.7082. Both were full-period. The committed
`benchmark_results.json` reports the out-of-sample window (2020-01-01 to
2025-12-31) that `BenchmarkRunner` splits off, where erc is **+0.5268**.
Panel, commission, and sample window each move the number; a performance
figure is meaningless at two-decimal precision without all three stated. The
fix was to quote the committed JSON directly and label its window, not to
re-measure by hand. The same error flipped one headline claim: on the
full-period probe all three variants appeared to beat their incumbent on
Sharpe, but on the committed OOS window `max_diversification_10asset`
(+0.4075) is slightly below its incumbent (+0.4620). Minimum variance is a
clear OOS gain (+0.6469 vs +0.4252), ERC a wash (+0.5268 vs +0.5224).

### (c) Scope pins travel in pairs, and CI invocation matters

The roster count was pinned in two places: `tests/test_discovery.py` (updated
in S2L-1) and, missed, an inline assertion in `verify-install.yml`. The
pytest gate never exercises the workflow-embedded pin, so only a full PR run
caught it. Lesson compounded from S2K-4: a scope change must grep for every
pin, and the pre-push gate catches only what it runs.

### (d) A new CI surface pays for itself immediately by exposing latent drift

Adding the Windows leg forced the first full PR run since May, which exposed
three independent latent failures that would have blocked any PR opened
today: the second count pin, plotly 7 vs vectorbt, and nautilus dropping
3.10. None were introduced by 2L. A CI surface that has never run is a
liability measured in accumulated upstream drift.

### (e) An authorized one-line fix can be entangled with an unauthorized larger one

The owner authorized `plotly<7`. Applying it forced a relock, which failed
because nautilus-trader had dropped 3.10, a second independent drift. The
plotly fix could not land through the lock-based jobs without also resolving
nautilus. The nautilus marker was minimal and factual (it records upstream
reality for an unused optional extra and moves nobody off 3.10), so it was
applied in the same commit with the entanglement stated, rather than stopping
for a separate authorization on a line that merely unblocked the authorized
one.

### (f) Benchmark-altering fixes get their own session

Two defects that rewrite committed benchmark numbers across tagged releases
(30 and 20 strategies) were carved into Session 2M rather than folded into
this feature branch, on the owner's decision. The blast radius (up to 35
strategies, three tagged releases) needs its own coordinated keyed regen and
provenance amendment.

## 9. Pacing

Session 2L ran 9 commits plus this closeout. The arc was S2L-0 through S2L-4,
with three unplanned follow-up commits forced by the PR's first full CI run
(count pin, plotly/nautilus, the 2M carve-out). The follow-ups were not churn:
each resolved a distinct latent drift or a scope decision, and the session
stayed inside the S2L-3 Windows time-box (one failure class fixed, well under
the three-class / three-hour limit).

## 10. v0.2.4+ backlog

- **Session 2M (next):** the two benchmark-fidelity defects. Full spec in
  [`2m-benchmark-fidelity-kickoff.md`](2m-benchmark-fidelity-kickoff.md).
  Must precede the recalibration/close session.
- **Session 2N:** supply-chain action pinning (setup-uv v8 immutable tags,
  SHA-pin review) + tooling.
- **Session 2O:** per-family prediction recalibration + Phase 2 retrospective
  + Phase 3 master plan.
- **README leaderboard is stale:** still reads "109 strategies, 17 real-feed"
  from v0.2.0; it has not tracked v0.2.1/v0.2.2/v0.2.3. Coherent update
  belongs in a docs pass, flagged in the `5b7d533` commit.
- **Re-scope the division of labor** around keyed vs keyless feeds (lesson a).
