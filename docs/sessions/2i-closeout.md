# Phase 2 Session 2I closeout — v0.2.1 real-feed regime validation

## 1. Summary

* **Branch:** `claude/2i-fred-runner`
* **PR:** [#21](https://github.com/ankitjha67/alphakit/pull/21)
* **Merge commit:** _to be filled after squash-merge_
* **Merge type:** squash (per Session 2D–2H precedent)
* **Scope:** v0.2.1 — a multi-feed `BenchmarkRunner` that benchmarks the 5
  FRED-gated regime macro strategies against **real yfinance + FRED** data, the
  three real-feed correctness bugs that surfaced, and the real-feed regime
  cluster pass. **Not a new strategy family.**
* **Strategy count unchanged:** 109 on `main` (60 Phase 1 + 49 Phase 2).
* **PR CI:** 13/13 green — test ×6 + lint ×1 + verify-install ×6.

## 2. Commits

| # | Hash | Summary |
|---|---|---|
| S2I-1 | `7000c4e` | feat(bench): multi-feed runner — route informational columns to FRED |
| S2I-2 | `0d517da` | feat(bench): `--feed real` path in `regenerate_benchmarks` |
| S2I-1.5 | `8e44e0f` | fix(bench,bridges): 3 real-FRED correctness bugs |
| keyed | `6a93bc4` | feat(benchmarks): real-feed regen for the 5 FRED-gated macro strategies |
| S2I-3 | `c0e0fcf` | feat(scripts): `--feed real` regime-cluster mode in `cluster_analysis` |
| S2I-3 | `211bfc7` | docs(changelog): v0.2.1 section |
| S2I-3 | _this_ | docs: 2026-05-22 amendment + real-feed cluster notes + this closeout |

## 3. What 2I delivered

* **Multi-feed `BenchmarkRunner`** — routes a strategy's informational (FRED)
  columns to the FRED feed and tradable columns to yfinance, aligned by an
  as-of forward-fill; `strict_feed` fails loud instead of silently substituting
  fixtures.
* **Real-feed regeneration of the 5 FRED-gated regime strategies** —
  `data_source="yfinance+fred-real"`, 2005-2025. OOS Sharpes: recession 0.847,
  growth_inflation 0.736, yield_curve 0.651, fed_policy 0.618, inflation 1.019.
* **Three correctness bugs fixed (S2I-1.5)** — see §6.
* **Real-feed regime cluster** — `cluster_analysis.py --feed real` + a section
  in `benchmark_notes.md` (§5).
* **Docs** — 2026-05-22 amendment (supersedes 2026-05-16), v0.2.1 CHANGELOG,
  this closeout.

## 4. Real-feed coverage update

`data_source` split is now **17 yfinance-real + 5 yfinance+fred-real + 87
synthetic-fixture** (109 total). The 5 FRED-gated regime strategies moved from
synthetic to real. Deferred to **v0.2.2** (see §10): commodity (10), options
(15, synthetic-options by design), `swap_spread_mean_rev`,
`global_inflation_momentum`.

## 5. Cluster findings (real-feed basis, 5×5)

Full matrix, predicted-vs-actual table and economic interpretation:
`docs/benchmark_notes.md` → "Phase 2 real-feed cluster".

Headline: **5/10 pairs within the Session 2G predicted range**, mean |ρ| 0.585,
max 0.794, no ρ > 0.95 dedup breach. The five out-of-range pairs reveal that
real regime strategies share **more** co-movement than synthetic fixtures
predicted, concentrated around three drivers: (1) Fed policy permeates yield
curves + inflation + policy tilt (yield_curve ↔ fed_policy = 0.794); (2)
inflation drives multiple signals (growth_inflation ↔ inflation = 0.779); (3)
recession indicators are upstream of curve shape and Fed response. Notably the
*deliberate-redundancy* pair Session 2G flagged
(recession ↔ yield_curve) came in at 0.495 — fractionally **below** its
0.50–0.70 band — so the redundancy is a **diffuse macro-wide common factor**,
not the single flagged pair. The synthetic predictions were directionally right
about *which* pair would correlate but wrong about *where* the macro complex's
common factor would show up; they **understated** real co-movement, and the
deliberate-redundancy framework should be widened accordingly. These 5 offer
less diversification than the synthetic basis implied.

## 6. The three real-feed correctness bugs (S2I-1.5)

All three were invisible to the S2I-1 mock-only integration tests (always
positive, single-frequency, publication-lag-free, single-OS panels) and surfaced
only on the keyed real-feed + Windows dev cycle.

1. **Bridge rejected valid informational data.** vectorbt validates
   `order.price must be finite and greater than 0` for *every* column, including
   weight-0 ones, so `RECPROUSM156N = 0.0` crashed the run. Fix: the bridge drops
   identically-zero-weight columns before `from_orders` (P&L-neutral). See the
   2026-05-22 amendment.
2. **FRED alignment dropped real observations.** Mixed-frequency series
   (quarterly GDPC1 on a monthly union index) and daily yields (holiday NaN)
   carried in-place NaN through the index-based `reindex(method="ffill")`. Fix: a
   value-based as-of fill over the union index, which also carries the last value
   across the trailing publication-lag gap.
3. **Atomic write failed on Windows.** `Path.rename` raises `FileExistsError`
   when the target exists; switched to `Path.replace`.

## 7. v0.2.1 tag plan (manual steps) — **not** a pre-release

1. Squash-merge PR #21 to `main`; note the squash SHA.
2. Tag `v0.2.1` on **that exact SHA** via the GitHub UI — **no pre-release flag**
   (this is a patch release, not a preview; per the §7 convention established in
   the v0.2.0 plan).
3. **Verify the tag SHA == the CI-target SHA** (the v0.1.0 footgun).
4. The `v*` tag auto-triggers `verify-install.yml` (git+URL path) — confirm
   6/6 green on the tag.
5. Manual fresh-venv check **with `FRED_API_KEY` set**: from a fresh clone,
   `uv run --with fredapi --with yfinance python scripts/regenerate_benchmarks.py
   tier2 --feed real` reproduces the 5 real-feed benchmarks (data_source
   `yfinance+fred-real`).

## 8. Process lessons

* **Real data + real OS exposed three bugs that mock-only integration tests
  missed.** The S2I-1 mocks verified the multi-feed *architecture* correctly but
  used always-positive, single-frequency, publication-lag-free panels on one OS,
  so they passed over: the RECPROUSM156N zero-value bridge crash, the
  mixed-frequency/holiday alignment NaN, and the Windows atomic-write failure.
  The mocked-fixtures pattern is necessary but not sufficient. **Recommendation:
  include at least one keyed real-feed smoke step in pre-release verification
  going forward.**
* **Synthetic cluster predictions understated real co-movement.** The 5/10
  out-of-range pairs (4 high) show the regime strategies share a diffuse
  macro-wide common factor that hand-crafted synthetic panels — which assumed
  more regime independence — did not capture. Real-feed validation produced a
  truer diversification picture (§5).
* **The 2026-05-16 amendment was superseded, not edited.** Its "honour the
  constraint at the strategy-input level" judgment was right under mocks and
  wrong against real data; the new 2026-05-22 entry records the reversal and the
  cleaner bridge-level fix, preserving the audit trail.
* **Division of labor (Option A) worked.** Claude built every real-feed path
  against mocks in the sandbox; Ankit ran the keyed regen + keyed cluster on a
  machine with `FRED_API_KEY`. No key ever entered the sandbox, chat, or repo.
* **PR-activity subscription remains best-effort** — proactive `get_check_runs`
  at decision points stayed the reliable pattern.

## 9. Pacing

S2I added an unplanned **S2I-1.5** (three bug fixes + tests) between the runner
build and the regen — genuine correctness work driven by the keyed real-feed
cycle, not churn. The cluster real-feed pass also required a script enhancement
(`--feed real`) plus a second keyed run, mirroring the regen division of labor.

## 10. v0.2.2 backlog

* Commodity real-feed pass (yfinance-futures / CFTC COT / EIA adapters) — the
  10 commodity strategies + the 2 excluded from the synthetic cluster
  (`commodity_curve_carry` config schema; `cot_speculator_position` CFTC
  columns).
* Swap-rate adapter for `swap_spread_mean_rev`; FRED-series mapping for
  `global_inflation_momentum`.
* `astral-sh/setup-uv` bump to a confirmed-stable v5/v6 (held at v4).
* Real-feed cluster analysis with broader coverage once the commodity adapters
  exist (the current real pass is the 5 regime strategies only).
