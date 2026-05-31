"""S2K-2 feasibility probe — FRED series coverage audit for rates strategies.

Run locally with ``FRED_API_KEY`` in env (Windows side; key NEVER lands in
this repo or any sandbox session) to verify continuous 2005-2025 coverage
of the candidate series identified in the S2K-2 audit report.

Usage::

    uv run --with fredapi python scripts/audit_fred_rates_series.py

Output: per-series coverage table (start, end, gaps, n_obs) + verdict.

The probe is read-only — no benchmark files are touched. Output goes to
stdout so it can be pasted back into the session for the build/no-build
decision (S2K-2 build phase or honest deferral).

Series under audit:

* **swap_spread_mean_rev** — needs continuous 10Y USD swap rate 2005-2025
  - DSWP10: legacy H.15 10Y swap rate (expected discontinued 2016-10-31)
  - ICERATES1100USD10Y: ICE Benchmark Administration replacement (2014+)
  - DGS10: 10Y Treasury constant maturity (Treasury leg, control)

* **global_inflation_momentum** — needs CPI + bond-yield-proxy for >=2
  countries (US/Germany/Japan minimum for cross-section dispersion):
  - CPIAUCSL (US, monthly, control), CPALTT01DEM657N (Germany level),
    CPALTT01JPM657N (Japan level)
  - IRLTLT01USM156N (US 10Y, OECD), IRLTLT01DEM156N (DE 10Y),
    IRLTLT01JPM156N (JP 10Y)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

# Audit window — matches the S2K-2 in-scope backtest period.
AUDIT_START = datetime(2005, 1, 1)
AUDIT_END = datetime(2025, 12, 31)

# Acceptable gap tolerance (in days). Monthly series legitimately have
# 30-31 day gaps between observations — anything beyond that is suspect.
MAX_GAP_DAYS_DAILY = 14  # 2 calendar weeks: allow holiday spans + odd Fed pauses
MAX_GAP_DAYS_MONTHLY = 45  # ~1.5 months: allows for delayed releases


@dataclass(frozen=True)
class SeriesProbe:
    series_id: str
    description: str
    expected_freq: str  # "daily" | "monthly"
    strategy: str
    notes: str = ""


CANDIDATES: list[SeriesProbe] = [
    # ---- swap_spread_mean_rev ----
    SeriesProbe(
        series_id="DSWP10",
        description="10-Year Swap Rate (H.15, LEGACY)",
        expected_freq="daily",
        strategy="swap_spread_mean_rev",
        notes="Expected DISCONTINUED 2016-10-31 per H.15 release notice.",
    ),
    SeriesProbe(
        series_id="ICERATES1100USD10Y",
        description="ICE Swap Rate, 11:00 London, USD, 10Y",
        expected_freq="daily",
        strategy="swap_spread_mean_rev",
        notes="ICE Benchmark Administration replacement series (expected 2014+).",
    ),
    SeriesProbe(
        series_id="DGS10",
        description="10Y Treasury Constant Maturity (control)",
        expected_freq="daily",
        strategy="swap_spread_mean_rev",
        notes="Continuous since 1962; control for sanity-check.",
    ),
    # ---- global_inflation_momentum ----
    SeriesProbe(
        series_id="CPIAUCSL",
        description="CPI All Urban Consumers (US, SA, control)",
        expected_freq="monthly",
        strategy="global_inflation_momentum",
        notes="Continuous since 1947; control series.",
    ),
    SeriesProbe(
        series_id="CPALTT01DEM657N",
        description="CPI All Items (Germany, Index 2015=100, NSA)",
        expected_freq="monthly",
        strategy="global_inflation_momentum",
        notes="OECD MEI source — verify suffix M657N gives LEVEL not rate-of-change.",
    ),
    SeriesProbe(
        series_id="CPALTT01JPM657N",
        description="CPI All Items (Japan, Index 2015=100, NSA)",
        expected_freq="monthly",
        strategy="global_inflation_momentum",
        notes="OECD MEI source.",
    ),
    SeriesProbe(
        series_id="IRLTLT01USM156N",
        description="10Y Long-Term Government Bond Yield (US, OECD/IMF)",
        expected_freq="monthly",
        strategy="global_inflation_momentum",
        notes="OECD analogue of DGS10 — verify continuous coverage.",
    ),
    SeriesProbe(
        series_id="IRLTLT01DEM156N",
        description="10Y Long-Term Government Bond Yield (Germany)",
        expected_freq="monthly",
        strategy="global_inflation_momentum",
        notes="Will go NEGATIVE 2015-2022 — confirms yield-not-price issue.",
    ),
    SeriesProbe(
        series_id="IRLTLT01JPM156N",
        description="10Y Long-Term Government Bond Yield (Japan)",
        expected_freq="monthly",
        strategy="global_inflation_momentum",
        notes="Will go NEGATIVE 2016-2022 — confirms yield-not-price issue.",
    ),
]


def probe_one(fred: object, probe: SeriesProbe) -> dict[str, object]:
    """Fetch ``probe.series_id``; return coverage summary dict."""
    try:
        series = fred.get_series(probe.series_id)  # type: ignore[attr-defined]
    except Exception as exc:
        return {
            "series_id": probe.series_id,
            "status": f"FETCH_FAILED: {type(exc).__name__}: {exc}",
        }

    if series.empty:
        return {
            "series_id": probe.series_id,
            "status": "EMPTY_RESPONSE",
        }

    series = series.sort_index().dropna()
    start, end = series.index[0], series.index[-1]
    covers_audit_window = start <= pd.Timestamp(AUDIT_START) and end >= pd.Timestamp(AUDIT_END)

    # Detect gaps within the audit window.
    in_window = series.loc[pd.Timestamp(AUDIT_START) : pd.Timestamp(AUDIT_END)]
    gaps_days: list[tuple[pd.Timestamp, pd.Timestamp, int]] = []
    if len(in_window) >= 2:
        diffs = in_window.index.to_series().diff().dt.days.dropna()
        max_gap = MAX_GAP_DAYS_DAILY if probe.expected_freq == "daily" else MAX_GAP_DAYS_MONTHLY
        for end_ts, gap in diffs.items():
            if gap > max_gap:
                end_ts_pd = pd.Timestamp(end_ts)
                idx = in_window.index.get_loc(end_ts_pd)
                if isinstance(idx, int) and idx > 0:
                    start_ts = in_window.index[idx - 1]
                    gaps_days.append((start_ts, end_ts_pd, int(gap)))

    finite_min = float(series.min()) if not series.isna().all() else float("nan")
    finite_max = float(series.max()) if not series.isna().all() else float("nan")

    return {
        "series_id": probe.series_id,
        "status": "OK",
        "start": str(start.date()),
        "end": str(end.date()),
        "n_obs": len(series),
        "covers_2005_2025": covers_audit_window,
        "min": finite_min,
        "max": finite_max,
        "went_negative": bool(finite_min < 0.0),
        "n_gaps": len(gaps_days),
        "gaps": [
            f"{s.date()} -> {e.date()} ({g}d)" for s, e, g in gaps_days[:5]
        ],  # truncate to first 5
    }


def main() -> int:
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("ERROR: FRED_API_KEY not set in env.", file=sys.stderr)
        return 2

    try:
        from fredapi import Fred
    except ImportError:
        print(
            "ERROR: fredapi not installed. Run with: "
            "uv run --with fredapi python scripts/audit_fred_rates_series.py",
            file=sys.stderr,
        )
        return 2

    fred = Fred(api_key=api_key)

    by_strategy: dict[str, list[tuple[SeriesProbe, dict[str, object]]]] = {}
    for probe in CANDIDATES:
        result = probe_one(fred, probe)
        by_strategy.setdefault(probe.strategy, []).append((probe, result))

    for strategy, rows in by_strategy.items():
        print(f"\n=== {strategy} ===")
        for probe, r in rows:
            print(f"  [{probe.series_id}] {probe.description}")
            print(f"    notes: {probe.notes}")
            if r.get("status") != "OK":
                print(f"    STATUS: {r.get('status')}")
                continue
            print(
                f"    coverage: {r['start']} -> {r['end']}  "
                f"(n={r['n_obs']}, covers 2005-2025: {r['covers_2005_2025']})"
            )
            min_v = float(r["min"])  # type: ignore[arg-type]
            max_v = float(r["max"])  # type: ignore[arg-type]
            print(f"    range: [{min_v:.4f}, {max_v:.4f}]  (went negative: {r['went_negative']})")
            if r["n_gaps"]:
                print(f"    gaps ({r['n_gaps']} found, first 5 shown):")
                gaps_list = r["gaps"]
                assert isinstance(gaps_list, list)
                for g in gaps_list:
                    print(f"      {g}")
            else:
                print("    gaps: none (within tolerance)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
