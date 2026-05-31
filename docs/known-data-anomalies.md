# Known data anomalies

Substrate-data observations for the data feeds AlphaKit pulls from real
sources. Anomalies here are *not* deviations from the master plan
([`phase-2-amendments.md`](phase-2-amendments.md)) — they're properties of
the underlying market data the adapters surface. This page documents the
specific historical singularities that violate the bridge's
`order.price > 0` invariant and the runner-level **anomaly filter** that
handles them.

## Per-ticker known anomalies

### `CL=F` (WTI front-month continuous, yfinance-futures)

| Date | Symptom | Cause |
|---|---|---|
| 2020-04-20 | Close = **-$37.63**, Low = -$40.32 | The May-2020 contract settled negative for the first time in WTI history — full Cushing storage + looming expiry + leveraged-ETF unwinds. Recovered to +$10.01 on 2020-04-21 (intraday Low briefly touched -$16.74 but settle was positive). One bar, never repeated. |
| Thanksgiving weeks | NaN close on the abbreviated/closed-pit session | US futures markets observe shortened Thanksgiving-week sessions; yfinance occasionally surfaces the closed day as a NaN row rather than dropping it. |

### `GC=F` / `NG=F` (gold / nat gas front-month continuous)

Same Thanksgiving-week NaN pattern as `CL=F`. None have a negative-price
event on record (gold last touched a structural low above $250 in 1999;
nat gas approached but never crossed zero even during the 2020-04 WTI
event because the storage dynamics differ).

### Other commodity futures

`BZ=F` (Brent), `RB=F` (gasoline), `HO=F` (heating oil), `SI=F` (silver),
`HG=F` (copper), `PL=F` (platinum), `ZC=F` (corn), `ZS=F` (soybeans),
`ZW=F` (wheat), `ZM=F` (soybean meal), `ZL=F` (soybean oil): no
non-positive prints in the 2005-01-01 to 2025-12-31 window. Thanksgiving
NaN rows occur sporadically.

## The anomaly filter

The runner's `_apply_anomaly_filter` (Session 2J S2J-2.6) drops rows with
non-positive or NaN values in any tradable column when
`BenchmarkRunner(drop_nonpositive_tradable_bars=True)`. Default off — the
strict-positive contract from the
[2026-05-22 amendment](phase-2-amendments.md) is the runner's default.

### Contract

* **Off (default):** filter is a no-op; `last_anomaly_filter` records
  `{"enabled": False}` and the benchmark JSON does **not** carry an
  `anomaly_filter` section. The bridge's positivity invariant is enforced
  as-is — a single bad bar surfaces as a `ValueError` from
  `_validate_feed_values` (multi-feed path) or as a strategy-level
  positivity check (single-feed shortcut path).
* **On (opt-in):** the runner silently trims any **leading** invalid
  block (pre-inception warm-up for a tradable ticker — same semantics as
  the existing leading-NaN trim) and drops any **mid-panel** rows where
  one or more tradable columns are NaN or `<= 0`. Each mid-panel drop is
  logged with its classification:
  ```text
  Dropped 4 tradable-anomaly bar(s):
    2006-11-24: NaN in CL=F, NG=F (missing data)
    2018-01-29: NaN in GC=F (missing data)
    2020-04-20: -37.63 in CL=F (negative price)
    2023-11-23: NaN in CL=F, GC=F (missing data)
  ```
  and recorded in the benchmark JSON:
  ```json
  "anomaly_filter": {
      "enabled": true,
      "bars_dropped": 4,
      "dropped_dates": ["2006-11-24", "2018-01-29", "2020-04-20", "2023-11-23"]
  }
  ```

### When to enable

Currently turned on **only** by `scripts/regenerate_benchmarks.py commodity --feed real`.
The 7 commodity benchmarks in scope (6 front-month + cot_speculator_position)
would otherwise be unable to span 2005-2025 OOS because the 2020-04-20 WTI
print and a handful of Thanksgiving NaN bars violate the bridge's
positivity invariant. Skipping those bars is methodologically standard for
published crude/commodity backtests (the strategy could not have actually
transacted at a negative price; the NaN bars correspond to closed sessions
with no investable signal).

The 17 yfinance-real Tier-1 benchmarks (Session 2H) and the 5 yfinance+fred
regime benchmarks (Session 2I) do **not** enable the filter — their data
is clean enough that the strict invariant holds end-to-end.

### Auditing what was filtered

Open the benchmark JSON and read `result["anomaly_filter"]`. If the section
is absent, the filter was off. If present, `dropped_dates` is the exact list
of bars excluded from the backtest. Cross-reference against this document to
identify the underlying cause.

## Deferred to Session 2K

### `cot_speculator_position` — CFTC adapter architectural gap

`cot_speculator_position` was originally scoped for the v0.2.2 commodity
real-feed pass (Session 2J), but empirical investigation in S2J-2.8 surfaced
**three independent architectural mismatches** between cot's expected input
shape and the CFTC adapter's actual contract:

1. **Schema drift (fixed in S2J-2.8).** The CFTC archive moved from
   `/dea/newcot/` to `/files/dea/history/`; the new layout's `annual.txt`
   uses long column names with spaces (`"As of Date in Form YYYY-MM-DD"`,
   `"CFTC Contract Market Code"`, `"Noncommercial Positions-Long (All)"`,
   etc.) rather than the legacy `Report_Date_as_YYYY-MM-DD` /
   `CFTC_Contract_Market_Code` / `NonComm_Positions_*` underscore names.
   The adapter's column constants are now corrected; a network-gated test
   (`test_real_cftc_archive_schema`) guards against future drift.
2. **No symbol → market-code mapping.** Session 2J's per-role router
   passes the `*_NET_SPEC` names (e.g. `"CL=F_NET_SPEC"`) to the adapter,
   but CFTC market codes are numeric strings (WTI = `067411`, NYMEX nat gas
   = `023655`, COMEX gold = `088691`, CBOT corn = `002602`, plus multiple
   sub-products per commodity that need disambiguation). Neither
   `cot_speculator_position`'s config nor the adapter knows the mapping.
3. **Long-vs-wide shape mismatch.** The CFTC adapter returns long-format
   (`columns: date, market_code, long_positions, …`; one row per
   `(date, market)` pair), while every other adapter and the runner's
   multi-feed merge expect wide format (`columns = requested symbols`,
   rows = dates).

Layers 2 and 3 are the same class of work as the **Session 2K rates
symbol-mapping** (`swap_spread_mean_rev`'s ICE-swap-rate construction,
`global_inflation_momentum`'s per-country CPI / bond mapping), so the
three deferrals get bundled. cot's `benchmark_results.json` stays
`synthetic-fixture` for v0.2.2; the Session 2G informational-column
declarations on the strategy (added in S2J-1) remain in place because
they're still the right architectural pattern — the missing piece is the
adapter-side translation, not the strategy-side declaration.

The S2J-1 mocked integration test for cot
(`TestCotIntegrationMultiFeed`) returned wide-format CFTC data from its
mock — i.e. it tested an *intended* contract the real adapter never
implemented. That test is preserved (it still validates the runner's
routing dispatch independent of the adapter's output shape) but flagged
in the closeout as a process lesson: when an adapter's output shape
differs from what callers consume, the mock must mirror the real shape
or the test isn't actually validating the integration.

## Cross-references

* [`phase-2-amendments.md`](phase-2-amendments.md) — the 2026-05-22 entry
  defines the dual-contract validation (tradable strictly positive,
  informational finite-only) the filter complements. The filter is the
  *operational* handling for the rare tradable-anomaly bars that violate
  that contract; the amendment is the *contract* itself.
* `docs/sessions/2j-closeout.md` — the Session 2J closeout where the
  filter was introduced (S2J-2.6) and the architectural principle behind
  it is documented.
