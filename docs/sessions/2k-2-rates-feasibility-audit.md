# S2K-2 — Rates real-feed feasibility audit

> Status: **primary probe complete, secondary probe pending Ankit re-run**.
> No code beyond `scripts/audit_fred_rates_series.py` was written. This
> document records the methodology determination, candidate FRED series IDs,
> known-architecture-of-the-strategies findings, and the verdict per
> strategy under the conservative (yield-only) and ambitious (cross-substrate)
> interpretations.

## Primary probe (2026-05-31) — outcomes

`scripts/audit_fred_rates_series.py` at `954de57` returned:

* **swap_spread_mean_rev** — BLOCKED at first probe:
  - `DSWP10` confirmed discontinued ~2016-10 (consistent with H.15 release notice).
  - `ICERATES1100USD10Y` returned "series does not exist" — the ICE
    replacement isn't at the kickoff-expected series ID.
  - `DGS10` control series works as expected.
* **global_inflation_momentum** — PARTIAL, needs corrected suffixes:
  - `CPALTT01{DE,JP}M657N` returned values consistent with rate-of-change,
    not LEVEL (negative values impossible for a Index=100 base CPI level).
  - `CPALTT01JPM657N` hit FRED rate limit (one of several probes too
    close together — fixed by 1.5s sleep in the secondary script).
  - `IRLTLT01{US,DE,JP}M156N` 10Y yields all clean, continuous 2005-2026,
    DE+JP went negative 2015-2022 (confirms duration-approximation
    engineering is required, as predicted in the methodology section).

The secondary probe re-runs with corrected suffixes (`M659N`),
BIS-OECD alternative naming (`DEUCPIALLMINMEI` / `JPNCPIALLMINMEI`),
inter-call sleep, and a free-text `fred.search()` hunt for any
continuous post-2016 swap rate series we haven't tried.

## Methodology determination (from strategy code, not vendor PR)

Both rates strategies were read end-to-end (`strategy.py`,
`known_failures.md`, `README.md`) before any FRED probe. The hard
constraints are baked into `generate_signals` validation:

### `swap_spread_mean_rev`
* **Input contract** — 2-column DataFrame `[treasury_proxy, swap_proxy]`,
  validated by `prices.shape[1] == 2` and `(prices <= 0).any().any() →
  raise`.
* **Signal math** — `log(P_treasury) − log(P_swap)`, z-scored on 252-day
  window. **Price-like series required**: yields cannot be substituted
  directly because (a) `log` of a yield is dimensionally wrong, and
  (b) negative yields (rare for US 10Y but possible at the front-end)
  would crash the strict-positive guard.
* **What known_failures.md §3+§6 already says** — "construct the
  swap-rate proxy from FRED's ICE swap rate and the duration approximation"
  and "IRS_10Y is not a real ticker". Real-feed wiring requires an
  engineering layer that converts yield → duration-scaled price proxy.

### `global_inflation_momentum`
* **Input contract** — paired columns `CPI_<country>` + `BOND_<country>`
  ; same `(prices <= 0)` guard.
* **CPI side** — strict-positive LEVEL series (Index = 2015 = 100 type),
  not rate-of-change. Strategy computes `log(level_t / level_{t-12mo})`
  internally; passing a pre-computed YoY rate breaks the log-ratio math.
* **BOND side** — strict-positive bond PRICE proxies, not yields.
  Germany + Japan 10Y yields went **negative for years** (DE: 2019-2022
  intermittently; JP: 2016-2022 persistently). The strict-positive guard
  would fail-loud on the QE-era cross-section, and even if it didn't,
  *yield-change ≠ bond return* semantically. Strategy needs a bond-price
  proxy series.

**Critical methodology answer to the user's pre-build question**:
> "Yield-only methodology vs total-return methodology?"

Reading `generate_signals` confirms: **the strategy is bond-price
based, not yield-based**. The bond columns are weighted dollar-neutral
and the runner downstream computes PnL from price returns. Passing raw
yields produces (a) wrong PnL sign/magnitude (yield-change is the
negative of return × duration) and (b) immediate guard failure during
QE-era negative-yield windows.

Two ways forward:
1. **Yield-from-FRED + duration approximation** — convert each yield
   series `y_t` to a price-equivalent `P_t = exp(−y_t × D)` (with
   `D ≈ 8.5y` for 10Y bonds). For the swap_spread strategy this is
   benign for z-score logic (duration scales cancel in the variance
   normalisation) and for PnL (return ≈ −D × Δy).
2. **Bond ETF via yfinance** — IEF / TLT (US), IBTM.L or EUNH.DE
   (Germany Bund ETF), 1306.T (Japan JGB ETF). Cross-substrate
   routing analogous to the cot S2K-1 pattern.

Path 1 is **lower architectural cost** (FRED-only, single adapter)
but **methodologically opinionated** — assumes 10Y duration ≈ 8.5y
for all countries, which is approximately true at issuance but drifts
with rate level. Path 2 is **lower methodology cost** (actual bond
ETF returns) but **higher engineering cost** (multi-substrate +
foreign-ticker availability check).

For S2K-2 v0.2.2 scope, Path 1 is the appropriate choice: it follows
the same pattern as known_failures.md §3 ("duration approximation to
convert to a price-equivalent series") and ships in the FRED substrate
already proven in Session 2I.

## FRED series candidates (no live probe yet — see §"Empirical probe")

### swap_spread_mean_rev — 10Y USD swap-rate substrate

| Series ID | Description | Expected coverage | Status |
|---|---|---|---|
| `DSWP10` | 10Y swap rate, H.15 (LEGACY) | 2000-07-03 → ~2016-10-31 | discontinued — H.15 release notice |
| `ICERATES1100USD10Y` | ICE Swap Rate, 11:00 London, USD, 10Y | ~2014-08-04 → present | replacement |
| `DGS10` | 10Y Treasury Constant Maturity | 1962-01-02 → present | continuous (control, already wired Session 2I) |

**Coverage hypothesis**: DSWP10 ends ~2016-10; ICERATES1100USD10Y begins
~2014-08 → **2-year overlap window** for splice validation, **continuous
2005-01 → 2025-12 via concatenation**.

**Splice methodology if both check out**:
* Use DSWP10 outright for 2005-01 → 2014-08.
* Use ICERATES1100USD10Y for 2014-08 → 2025-12.
* In the overlap window, compute the cross-source spread per day and
  verify it is small (< 5 bps) and unbiased (mean ≈ 0). If true, the
  splice is methodologically clean; if not, document the level bias
  and apply a one-time additive adjustment at the splice date.

### global_inflation_momentum — CPI + bond-yield-proxy substrate

| Series ID | Description | Expected coverage |
|---|---|---|
| `CPIAUCSL` | US CPI All Items, SA (LEVEL) | 1947-01 → present (control) |
| `CPALTT01DEM657N` | Germany CPI All Items, Index 2015=100, NSA | OECD MEI — verify suffix |
| `CPALTT01JPM657N` | Japan CPI All Items, Index 2015=100, NSA | OECD MEI — verify suffix |
| `IRLTLT01USM156N` | US 10Y LT Gov Bond Yield (OECD analogue) | 1953+ |
| `IRLTLT01DEM156N` | Germany 10Y LT Gov Bond Yield | ~1956+ |
| `IRLTLT01JPM156N` | Japan 10Y LT Gov Bond Yield | ~1989+ |

**Coverage hypothesis** — all continuous monthly 2005-01 → 2025-12.

**Critical pre-build verification**:
1. The `M657N` suffix convention: FRED's OECD-MEI series typically use
   `M657N` (Index 2015=100, monthly, NSA) for the LEVEL. The probe
   script verifies this by printing the value range — a LEVEL series
   sits in `[~90, ~140]` for 2005-2025; a rate-of-change series sits
   in `[−2, 10]`. If the range is rate-of-change-like, swap to the
   matching `M661N` / `M553N` / sibling level series.
2. Germany + Japan 10Y yields **will probe negative** in the OECD
   series — the probe's `went_negative: true` field confirms the
   yield-not-price methodology issue.

## Empirical probe — `scripts/audit_fred_rates_series.py`

Run from Ankit's Windows env (FRED_API_KEY in shell, NEVER pasted into
chat):

```powershell
uv run --with fredapi python scripts/audit_fred_rates_series.py
```

Output (one block per strategy) lists per-series:
* `coverage: <start> -> <end>  (n=..., covers 2005-2025: True/False)`
* `range: [min, max]  (went negative: True/False)`
* `gaps:` any mid-window gaps over the daily/monthly tolerance.

Tolerances: 14 days (daily series) / 45 days (monthly series). Anything
exceeding these surfaces a true publishing gap, not normal weekends/
holidays/release lag.

## Decision matrix (filled in after probe report)

| Strategy | Path 1 feasible? | Path 1 verdict | Engineering layer | S2K-2 build estimate |
|---|---|---|---|---|
| `swap_spread_mean_rev` | DSWP10 + ICERATES1100USD10Y continuous via splice + DGS10 OK → **YES** | splice methodology + duration approximation | new `fred-duration-bond` adapter OR strategy-side preprocessor | 3-4h |
| `global_inflation_momentum` | 3 CPI levels + 3 yields all continuous + LEVEL series for CPI confirmed → **YES** | duration approximation per country | reuse same `fred-duration-bond` adapter | 2-3h (shared layer with swap_spread) |

**If both probe results confirm continuous coverage**:
* S2K-2 build: 2 strategies, ~5-7h combined (shared duration-
  approximation adapter amortises the engineering cost).
* Coverage: 31/109 real-feed (28.4%) post-S2K-1.

**If swap concat fails (e.g. ICE series stopped early or coverage gap)**:
* Build global_inflation_momentum only.
* 30/109 real-feed (27.5%).

**If both CPI level suffixes are wrong AND yield series probe negative**:
* Architectural choice: build the duration-approximation adapter +
  hunt the correct CPI level series IDs (likely `CPALTT01DEM659N` →
  `CPALTT01DEM661N` swap), OR defer global_inflation_momentum and
  ship swap_spread only.

## Methodological caveats to surface before build

1. **Duration approximation is a modelling choice**, not "real" data.
   Worth a `data_source` suffix like `"yfinance+fred-duration-real"`
   to distinguish from raw FRED.
2. **Splice methodology for DSWP10 → ICERATES1100USD10Y** is a
   methodology decision (additive bias correction? regime weighting?
   straight concatenation?). Default proposal: straight concatenation
   IFF overlap-window mean spread < 5 bps; otherwise additive shift to
   align the levels at the splice point. Document in the strategy's
   `known_failures.md` §3 update.
3. **CPI release lag** — known_failures.md §3 of global_inflation_momentum
   already documents that the strategy assumes month-end CPI is known
   at month-end (look-ahead). The S2H-prep note there says "real-feed
   benchmarks must lag the CPI column by 1 month". S2K-2 build must
   apply this lag (likely in the strategy's preprocessing, not the
   adapter) — call this out as a build-time decision.
4. **Country-panel size** — known_failures.md §6 says "at least G7" for
   adequate rank dispersion. S2K-2's US/DE/JP triplet is 3 countries =
   coarse rank (the middle country gets zero weight every month).
   Whether this is acceptable for v0.2.2 or whether S2K-2 should
   defer to G7 in a later session is a scope question. Recommend
   shipping 3-country v0.2.2 with a documented caveat; expand to G7
   in a separate session.

## Verdict (final, post-secondary-probe 2026-05-31)

Both strategies **deferred to Phase 3** under the v0.2.2 FRED-only path.
S2K-2 ships 0 rates strategies real-feed. Coverage remains 29/109 (26.6%)
post-S2K-1, unchanged.

### `swap_spread_mean_rev` — DEFINITIVELY BLOCKED

* `DSWP10` discontinued 2016-10-28 (confirmed).
* `ICERATES1100USD10Y` returned "Bad Request. The series does not exist."
* `fred.search()` over 4 queries returned no usable continuous 10Y USD
  swap rate series:
  - `"10-year swap rate USD"` — no hits.
  - `"ICE swap rate"` — 4 hits, all mortgage credit spreads
    (`CROASTIER0`-`CROASTIER3`), no interest-rate swaps.
  - `"USD interest rate swap"` — no hits.
  - `"SOFR swap rate 10"` — no hits.

10Y USD swap rates exist at ICE Data Services / Bloomberg / Refinitiv
(subscription only) and the BIS Effective Rate database (research access,
not for systematic backtesting). Same substrate-constraint pattern as the
Session 2F `vix_front_back_spread` and Session 2J commodity back-month
deferrals.

### `global_inflation_momentum` — PARTIALLY BLOCKED by Japan CPI gap

* US (`CPIAUCSL`): LEVEL, continuous 1947-2026. ✓
* US 10Y yield (`IRLTLT01USM156N`): continuous. ✓
* DE 10Y yield (`IRLTLT01DEM156N`): continuous, went negative 2015-2022. ✓
* JP 10Y yield (`IRLTLT01JPM156N`): continuous, went negative 2016-2022. ✓
* DE CPI LEVEL: `DEUCPIALLMINMEI` (BIS-OECD naming) — range
  `[20.75, 127.78]`, LEVEL confirmed, continuous 1955-01 → 2025-03. ✓
* JP CPI LEVEL: `JPNCPIALLMINMEI` (BIS-OECD naming) — range
  `[16.73, 102.32]`, LEVEL confirmed BUT stops at **2021-06**. ✗

The OECD MEI suffix variants (`M657N`, `M659N`) both return
RATE-OF-CHANGE series for Germany and Japan despite the naming
convention typically distinguishing them — the LEVEL series live at the
BIS-OECD names. Discovery of this substrate-boundary quirk is itself a
finding (prevents shipping silently-wrong inflation calculations under
the wrong-suffix interpretation).

Japan CPI gap of 4 years (2021-07 → 2025-12) on a strategy whose OOS
window extends to 2025-12-31. Options considered:

* **A**: Truncate OOS to 2021-06 → 1.5y OOS test, methodologically weak.
* **B**: Hunt for alternative JP CPI series with 2025+ coverage —
  uncertain outcome, extends Session 2K beyond the agreed scope.
* **C**: Reframe to US + DE 2-country — mathematically workable but
  methodologically thin (rank at N=2 is just "is US > DE", strategy's
  cross-sectional rank loses its rationale).
* **D**: **Defer to Phase 3 with amendment**. ← selected

### Phase 3 re-instatement paths

* **swap_spread_mean_rev**: BIS rate-database systematic-backtest access
  probe; ICE Data Services / Bloomberg / Refinitiv subscription-feed
  adapter (commercial-feed adapter architecture, out of v1.0
  silent-build scope); or synthetic swap rate from forward-rate-curve
  construction (technically valid but a fundamentally different
  strategy).
* **global_inflation_momentum**: probe for JP CPI alternative with
  2025+ coverage (Statistics Bureau Japan analogue, BLS international
  comparable series). If found: ship 3-country via the duration adapter.
  If not: document the substrate gap and ship 2-country (US/DE) as
  alternative scope.

### Manifest impact

* S2K-2 ships 0 strategies real-feed.
* Coverage **29/109 (26.6%)** unchanged from S2K-1.
* Rates family: 0/2 real-feed in v0.2.2 pt 2.
* Proceed directly to S2K-3 (setup-uv version bump).

See the 2026-05-31 Session 2K rates-deferral amendment in
`docs/phase-2-amendments.md` for the formal record.
