"""S2L-0 feasibility probe — ETF universe coverage audit for the covariance trio.

Mirrors the Session 2K-2 ``audit_fred_rates_series.py`` pattern (per-candidate
probe + machine-checkable classifier + summary table) for the yfinance ETF
substrate, so the Session 2L universe decision rests on measured inception
dates rather than assumed ones.

Usage::

    uv run --with yfinance python scripts/audit_etf_universe.py

Context (Session 2L S2L-0)
--------------------------
Session 2K-4's 29x29 real-feed cluster surfaced a dedup-review-bar breach:
``risk_parity_erc_3asset`` / ``min_variance_gtaa`` / ``max_diversification``
correlate at rho 0.980-0.993. All three share
``_covariance.rolling_covariance`` on the same SPY/TLT/DBC universe and differ
only in solver objective; on a 3-asset universe where TLT carries the lowest
sigma, all three concentrate on TLT and trace near-identical curves
(``docs/sessions/2k-closeout.md`` section 5).

Session 2L resolves this by adding **new** N-asset variants alongside the
preserved 3-asset originals. This script measures whether the candidate
universe actually delivers the history the strategies need, before any
strategy code is written.

What is measured
----------------
Per candidate ticker:

* ``first_obs`` / ``last_obs`` — the ACTUAL first and last bars yfinance
  serves, discovered by requesting a deliberately over-wide window
  (1990-2026) rather than assuming an inception date. The Session 2K-1
  lesson applies: an external assertion about a data source is
  feasibility-uncertain until probed. (The kickoff's "DBC ~2006-02" is a
  hypothesis this script tests, not an input it trusts.)
* ``covers_audit_window`` — whether the ticker spans 2005-01-01 to
  2025-12-31 outright.
* ``missing_bdays`` / ``max_consecutive_gap`` — business days absent from
  the ticker's own live range. A couple of hundred missing days over 20
  years is NORMAL (market holidays, ~9-10/yr); the signal worth acting on
  is ``max_consecutive_gap``, where anything beyond a long weekend points
  at a real publication gap.
* ``n_nonpositive`` — bars at or below zero, which the bridge's
  ``order.price > 0`` invariant rejects and the S2J-2.6 anomaly filter
  would have to drop.

Then, for each candidate universe, the **complete-rows intersection**: the
first date on which every member simultaneously has data. This is exactly
what ``BenchmarkRunner._fetch_prices`` computes via
``complete = merged.notna().all(axis=1); merged.loc[complete.idxmax():]``,
so the number printed here is the effective panel start the new strategies
will actually get.

Three universes are reported so the decision is a direct comparison:

* ``current-trio`` — SPY/TLT/DBC, what the 3-asset originals run on today.
  Establishes the comparability baseline; the originals are themselves
  DBC-bound, so "the new variants start later than 2005" is only a
  regression if they start later than THIS.
* ``candidate-10`` — the full 10-asset universe including DBC.
* ``candidate-9-ex-DBC`` — drops DBC, trading the commodity leg for
  history.

Probes go through ``YFinanceAdapter`` (not raw yfinance) so what is measured
is what ``BenchmarkRunner`` will see, including the S2J-2.5 MultiIndex
flatten. Caching is disabled via the null-device sentinel so an audit can
never read a stale panel — a deliberate exercise of the S2K-3.5
cross-platform sentinel fix, which is what makes that line work on Windows.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Audit window — matches the benchmark runner's configured span.
AUDIT_START = datetime(2005, 1, 1)
AUDIT_END = datetime(2025, 12, 31)

# Deliberately over-wide probe window so inception dates are discovered,
# not clipped by the request. Every candidate ETF post-dates 1990.
PROBE_START = datetime(1990, 1, 1)
PROBE_END = datetime(2026, 12, 31)

# Consecutive-missing-business-day run beyond which a gap stops looking
# like a market holiday and starts looking like a data problem. US market
# holidays are 1 day; the Christmas/New-Year cluster never exceeds 2
# consecutive business days.
SUSPICIOUS_GAP_BDAYS = 5

# Politeness delay between yfinance calls (it is an unofficial scraper of a
# free endpoint; the S2K-2 probe used the same discipline against FRED).
SLEEP_BETWEEN_CALLS_SEC = 1.0


@dataclass(frozen=True)
class TickerProbe:
    ticker: str
    sleeve: str
    description: str


CANDIDATES: list[TickerProbe] = [
    TickerProbe("SPY", "equity-us", "SPDR S&P 500 — US large-cap (incumbent)"),
    TickerProbe("TLT", "rates-long", "iShares 20+ Year Treasury (incumbent)"),
    TickerProbe("DBC", "commodity", "Invesco DB Commodity Index (incumbent)"),
    TickerProbe("IEF", "rates-mid", "iShares 7-10 Year Treasury"),
    TickerProbe("SHY", "rates-short", "iShares 1-3 Year Treasury"),
    TickerProbe("LQD", "credit-ig", "iShares iBoxx $ Investment Grade Corporate"),
    TickerProbe("GLD", "commodity-gold", "SPDR Gold Shares"),
    TickerProbe("VNQ", "real-assets", "Vanguard Real Estate"),
    TickerProbe("EFA", "equity-dm", "iShares MSCI EAFE — developed ex-US"),
    TickerProbe("EEM", "equity-em", "iShares MSCI Emerging Markets"),
]

# Universes to evaluate for the complete-rows intersection. The current trio
# is included so the new variants' effective start can be compared against
# the incumbents' rather than against the nominal data_start.
UNIVERSES: dict[str, list[str]] = {
    "current-trio (incumbent 3-asset)": ["SPY", "TLT", "DBC"],
    "candidate-10 (incl. DBC)": [p.ticker for p in CANDIDATES],
    "candidate-9-ex-DBC": [p.ticker for p in CANDIDATES if p.ticker != "DBC"],
}


def _fetch(symbols: list[str]) -> pd.DataFrame:
    """Fetch via the registered adapter over the over-wide probe window."""
    from alphakit.data.registry import FeedRegistry

    adapter = FeedRegistry.get("yfinance")
    return adapter.fetch(symbols, PROBE_START, PROBE_END)


def probe_one(probe: TickerProbe) -> dict[str, object]:
    """Fetch one ticker; return a coverage summary dict."""
    try:
        frame = _fetch([probe.ticker])
    except Exception as exc:
        return {"ticker": probe.ticker, "status": f"FETCH_FAILED: {type(exc).__name__}: {exc}"}

    if frame.empty or probe.ticker not in frame.columns:
        return {"ticker": probe.ticker, "status": "EMPTY_RESPONSE"}

    series = frame[probe.ticker].dropna().sort_index()
    if series.empty:
        return {"ticker": probe.ticker, "status": "ALL_NAN"}

    first_obs, last_obs = series.index[0], series.index[-1]
    covers = first_obs <= pd.Timestamp(AUDIT_START) and last_obs >= pd.Timestamp(AUDIT_END)

    # Gap analysis over the ticker's own live range intersected with the
    # audit window — measuring absence before inception would just restate
    # the inception date.
    win_start = max(first_obs, pd.Timestamp(AUDIT_START))
    win_end = min(last_obs, pd.Timestamp(AUDIT_END))
    in_window = series.loc[win_start:win_end]
    expected = pd.bdate_range(win_start, win_end)
    missing = expected.difference(in_window.index)

    # Longest run of consecutive missing business days: holidays are 1-2,
    # anything longer is a real publication gap worth naming.
    max_run = 0
    run = 0
    prev: pd.Timestamp | None = None
    for day in missing:
        if prev is not None and len(pd.bdate_range(prev, day)) == 2:
            run += 1
        else:
            run = 1
        max_run = max(max_run, run)
        prev = day

    nonpositive = int((in_window <= 0).sum())

    return {
        "ticker": probe.ticker,
        "status": "OK",
        "first_obs": str(first_obs.date()),
        "last_obs": str(last_obs.date()),
        "covers_2005_2025": covers,
        "n_obs_in_window": len(in_window),
        "expected_bdays": len(expected),
        "missing_bdays": len(missing),
        "max_consecutive_gap": max_run,
        "gap_suspicious": max_run >= SUSPICIOUS_GAP_BDAYS,
        "n_nonpositive": nonpositive,
        "min_price": float(in_window.min()),
        "max_price": float(in_window.max()),
    }


def report_universe(label: str, symbols: list[str]) -> dict[str, object]:
    """Complete-rows intersection for one candidate universe.

    Mirrors ``BenchmarkRunner._fetch_prices``: the effective panel starts at
    the first bar where every member is simultaneously present.
    """
    try:
        frame = _fetch(symbols)
    except Exception as exc:
        return {"label": label, "status": f"FETCH_FAILED: {type(exc).__name__}: {exc}"}

    missing_cols = [s for s in symbols if s not in frame.columns]
    if missing_cols:
        return {"label": label, "status": f"MISSING_COLUMNS: {missing_cols}"}

    panel = frame[symbols]
    complete = panel.dropna(how="any")
    if complete.empty:
        return {"label": label, "status": "NO_COMPLETE_ROWS"}

    in_window = complete.loc[pd.Timestamp(AUDIT_START) : pd.Timestamp(AUDIT_END)]
    binding = max(
        symbols,
        key=lambda s: (
            panel[s].dropna().index[0] if not panel[s].dropna().empty else pd.Timestamp.min
        ),
    )

    return {
        "label": label,
        "status": "OK",
        "n_members": len(symbols),
        "complete_start": str(complete.index[0].date()),
        "complete_end": str(complete.index[-1].date()),
        "binding_ticker": binding,
        "binding_inception": str(panel[binding].dropna().index[0].date()),
        "n_complete_rows_in_window": len(in_window),
        "effective_window_start": str(in_window.index[0].date()) if len(in_window) else "n/a",
    }


def main() -> int:
    # An offline run would silently return synthetic fixtures shaped like
    # real data — the audit would "succeed" and report inception dates that
    # are pure fiction. Fail loud instead.
    from alphakit.data.offline import is_offline

    if is_offline():
        print(
            "ERROR: ALPHAKIT_OFFLINE is set. This audit measures the real "
            "yfinance substrate; offline mode would return synthetic fixtures "
            "and produce fabricated inception dates. Unset ALPHAKIT_OFFLINE "
            "and re-run.",
            file=sys.stderr,
        )
        return 2

    try:
        import yfinance  # noqa: F401
    except ImportError:
        print(
            "ERROR: yfinance not installed. Run with: "
            "uv run --with yfinance python scripts/audit_etf_universe.py",
            file=sys.stderr,
        )
        return 2

    # Null-device sentinel disables the parquet cache for the whole audit, so
    # a stale panel can never masquerade as a fresh probe (S2J section 8(e)
    # cache-staleness lesson). Works on Windows and POSIX alike thanks to the
    # S2K-3.5 cross-platform sentinel fix.
    os.environ["ALPHAKIT_CACHE_DIR"] = "NUL" if os.name == "nt" else "/dev/null"

    print(f"ETF universe audit — probe window {PROBE_START.date()} to {PROBE_END.date()}")
    print(f"Audit window (benchmark span): {AUDIT_START.date()} to {AUDIT_END.date()}\n")

    print("=== Per-ticker coverage ===")
    results: list[tuple[TickerProbe, dict[str, object]]] = []
    for probe in CANDIDATES:
        res = probe_one(probe)
        results.append((probe, res))
        print(f"\n  [{probe.ticker}] {probe.description}  (sleeve: {probe.sleeve})")
        if res.get("status") != "OK":
            print(f"    STATUS: {res.get('status')}")
        else:
            print(
                f"    coverage: {res['first_obs']} -> {res['last_obs']}  "
                f"(covers 2005-2025: {res['covers_2005_2025']})"
            )
            print(
                f"    in-window bars: {res['n_obs_in_window']} of "
                f"{res['expected_bdays']} bdays  "
                f"(missing {res['missing_bdays']}, "
                f"max consecutive gap {res['max_consecutive_gap']}"
                f"{' SUSPICIOUS' if res['gap_suspicious'] else ''})"
            )
            lo = cast(float, res["min_price"])
            hi = cast(float, res["max_price"])
            print(
                f"    price range: [{lo:.2f}, {hi:.2f}]  nonpositive bars: {res['n_nonpositive']}"
            )
        time.sleep(SLEEP_BETWEEN_CALLS_SEC)

    print("\n\n=== Inception summary (sorted latest-first: the binding constraint) ===")
    ok = [(p, r) for p, r in results if r.get("status") == "OK"]
    for probe, res in sorted(ok, key=lambda t: str(t[1]["first_obs"]), reverse=True):
        flag = "" if res["covers_2005_2025"] else "  <-- post-dates 2005-01-01"
        print(f"  {res['first_obs']}  {probe.ticker:<5} {probe.sleeve:<16}{flag}")

    print("\n\n=== Complete-rows intersection per candidate universe ===")
    print("(what BenchmarkRunner._fetch_prices will actually hand the strategy)\n")
    for label, symbols in UNIVERSES.items():
        res = report_universe(label, symbols)
        print(f"  {label}")
        if res.get("status") != "OK":
            print(f"    STATUS: {res.get('status')}")
        else:
            print(f"    members: {res['n_members']}  ({', '.join(symbols)})")
            print(
                f"    binding ticker: {res['binding_ticker']} "
                f"(inception {res['binding_inception']})"
            )
            print(
                f"    effective panel start: {res['effective_window_start']}  "
                f"complete rows in window: {res['n_complete_rows_in_window']}"
            )
        print()
        time.sleep(SLEEP_BETWEEN_CALLS_SEC)

    print("Decision inputs:")
    print("  (a) 10-asset incl. DBC  — keeps the commodity sleeve; effective start")
    print("      is whatever 'candidate-10' reports above.")
    print("  (b) 9-asset ex-DBC      — longer history; drops the commodity sleeve.")
    print("  Compare BOTH against 'current-trio': the incumbents are themselves")
    print("  DBC-bound, so a later start is only a regression relative to that.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
