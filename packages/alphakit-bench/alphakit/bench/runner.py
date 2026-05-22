"""BenchmarkRunner — orchestrates strategy benchmarking end-to-end.

Loads a strategy via its slug, fetches price data, splits into
train/OOS periods, runs backtest via vectorbt_bridge, computes
extended metrics, and writes benchmark_results.json atomically.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from alphakit.bench import discovery, metrics
from alphakit.bridges import vectorbt_bridge


def _get_commit_sha() -> str | None:
    """Get current git commit SHA, or None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


class BenchmarkRunner:
    """Run a strategy benchmark and produce benchmark_results.json.

    Parameters
    ----------
    commission_bps
        Round-trip commission in basis points.
    data_start
        Start date for price data (training begins here).
    in_sample_end
        End of in-sample / start of out-of-sample.
    out_of_sample_end
        End of out-of-sample period.
    initial_cash
        Starting cash for the backtest.
    strict_feed
        Feed-resolution policy. ``False`` (default) preserves the
        CI/test-safe behavior: if a real feed is unavailable (missing
        package, unconfigured ``FRED_API_KEY``, offline mode, network
        failure), the runner falls back to deterministic fixtures.
        ``True`` (set by ``scripts/regenerate_benchmarks.py --feed
        real``) makes any such failure raise loudly rather than
        silently substituting fixtures — per the Session 2H
        "silent fixture fallback is a trap" lesson.
    """

    def __init__(
        self,
        *,
        commission_bps: float = 5.0,
        data_start: str = "2005-01-01",
        in_sample_end: str = "2019-12-31",
        out_of_sample_end: str = "2025-12-31",
        initial_cash: float = 100_000.0,
        strict_feed: bool = False,
    ) -> None:
        self.commission_bps = commission_bps
        self.data_start = data_start
        self.in_sample_end = in_sample_end
        self.out_of_sample_end = out_of_sample_end
        self.initial_cash = initial_cash
        self.strict_feed = strict_feed

    def run_single(
        self,
        slug: str,
        prices: pd.DataFrame | None = None,
        *,
        family: str | None = None,
    ) -> dict[str, Any]:
        """Benchmark a single strategy, returning the Appendix C dict.

        Parameters
        ----------
        slug
            Strategy slug (e.g. ``"tsmom_12_1"``).
        prices
            Optional pre-loaded price DataFrame. If None, attempts to
            load from alphakit-data fixtures or yfinance.
        family
            Strategy family. Auto-detected from slug if not provided.
        """
        if family is None:
            family, slug = discovery.find_strategy(slug)

        strategy = discovery.instantiate(family, slug)
        config = discovery.load_config(family, slug)
        universe = config.get("universe", ["SPY", "EFA", "AGG"])

        # Get price data
        if prices is None:
            prices = self._fetch_prices(universe, strategy=strategy)

        # Filter to OOS period only for benchmark metrics
        oos_start = pd.Timestamp(self.in_sample_end) + pd.Timedelta(days=1)
        oos_end = pd.Timestamp(self.out_of_sample_end)

        # But we need the full history for warm-up — run on all data,
        # then slice metrics to OOS period
        full_result = vectorbt_bridge.run(
            strategy=strategy,
            prices=prices,
            initial_cash=self.initial_cash,
            commission_bps=self.commission_bps,
        )

        # Slice to OOS period for metrics
        oos_mask = (full_result.returns.index >= oos_start) & (full_result.returns.index <= oos_end)
        oos_returns = full_result.returns[oos_mask]
        oos_weights = full_result.weights[oos_mask]

        # If not enough OOS data, fall back to full period
        if len(oos_returns) < 60:
            oos_returns = full_result.returns
            oos_weights = full_result.weights

        # Compute metrics
        returns_arr = oos_returns.to_numpy()
        from alphakit.core.metrics.drawdown import max_drawdown
        from alphakit.core.metrics.returns import calmar_ratio, sharpe_ratio, sortino_ratio

        sharpe = sharpe_ratio(returns_arr)
        sortino = sortino_ratio(returns_arr)
        calmar = calmar_ratio(returns_arr)
        mdd = max_drawdown(returns_arr)
        ann_ret = float(np.mean(returns_arr) * 252) if len(returns_arr) > 0 else 0.0
        ann_vol = float(np.std(returns_arr, ddof=1) * np.sqrt(252)) if len(returns_arr) > 1 else 0.0

        # Extended metrics
        to = metrics.turnover_annual(oos_weights)
        cap = metrics.capacity_estimate_bn(to)
        regime = metrics.regime_performance(oos_returns)

        result = {
            "slug": slug,
            "status": "populated",
            "note": "Generated by alphakit-bench BenchmarkRunner.",
            "benchmark_date": date.today().isoformat(),
            "data_start": self.data_start,
            "in_sample_end": self.in_sample_end,
            "out_of_sample_end": self.out_of_sample_end,
            "universe": universe,
            "metrics": {
                "sharpe": round(sharpe, 4),
                "sortino": round(sortino, 4),
                "calmar": round(calmar, 4),
                "max_drawdown": round(mdd, 4),
                "annualized_return": round(ann_ret, 4),
                "annualized_vol": round(ann_vol, 4),
                "turnover_annual": round(to, 2),
                "capacity_usd_bn": round(cap, 1),
            },
            "regime_performance": {k: round(v, 4) for k, v in regime.items()},
            "transaction_costs_assumed_bps": self.commission_bps,
            "commit_sha": _get_commit_sha(),
            "engine": "vectorbt",
        }
        return result

    def write_benchmark(
        self,
        slug: str,
        result: dict[str, Any],
        *,
        family: str | None = None,
    ) -> Path:
        """Write benchmark_results.json atomically with backup.

        Returns the path to the written file.
        """
        if family is None:
            family, slug = discovery.find_strategy(slug)

        path = discovery.benchmark_results_path(family, slug)

        # Backup existing file
        if path.exists():
            backup = path.with_suffix(".json.bak")
            shutil.copy2(path, backup)

        # Atomic write via temp file
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(result, f, indent=2, default=str)
            f.write("\n")
        tmp.rename(path)
        return path

    def _informational_columns(self, strategy: object | None, universe: list[str]) -> list[str]:
        """Return the universe symbols that are informational (non-tradable).

        A strategy that exposes both ``tradable_symbols`` and
        ``required_symbols`` (the Session 2G informational-column pattern)
        routes its non-tradable inputs (e.g. FRED series) to the FRED feed.
        Strategies lacking either property — i.e. every non-regime strategy —
        return ``[]`` and take the single-feed path unchanged.
        """
        tradable = getattr(strategy, "tradable_symbols", None)
        required = getattr(strategy, "required_symbols", None)
        if not tradable or not required:
            return []
        tradable_set = set(tradable)
        return [s for s in universe if s not in tradable_set]

    def _fetch_prices(self, universe: list[str], strategy: object | None = None) -> pd.DataFrame:
        """Fetch a price panel for ``universe``, routing per feed.

        If ``strategy`` declares informational (non-tradable) columns, those
        are fetched from FRED and the tradable columns from yfinance, then
        aligned (FRED reindexed onto the daily tradable index and
        forward-filled) and merged. Otherwise the whole universe takes the
        single-feed (yfinance → fixture) path. See ``strict_feed``.
        """
        informational = self._informational_columns(strategy, universe)
        if not informational:
            return self._fetch_feed(universe, "yfinance", self._yfinance_fetch)

        tradable = [s for s in universe if s not in set(informational)]
        etf = self._fetch_feed(tradable, "yfinance", self._yfinance_fetch)
        fred = self._fetch_feed(informational, "fred", self._fred_fetch)

        # Align FRED (native freq, e.g. monthly CPI / quarterly GDP) onto the
        # daily tradable index via as-of forward-fill: each daily bar takes the
        # most recent FRED observation on-or-before it. ``method="ffill"`` (not
        # plain reindex + ffill) is required because FRED observations are dated
        # on the 1st of the month/quarter, which is frequently a weekend and so
        # absent from the business-day index — plain reindex would drop those.
        # No back-fill: that would inject look-ahead. Publication lag is the
        # strategy's concern (.shift), not the runner's — FRED returns
        # reference-period-dated observations.
        fred_aligned = fred.sort_index().reindex(etf.index, method="ffill")
        merged = pd.concat([etf, fred_aligned], axis=1)
        merged = merged.loc[:, universe]

        # Trim leading rows where any column is still NaN (warm-up before the
        # first observation of some column), so the bridge never sees a
        # non-finite close. ffill guarantees no mid-panel gaps in FRED columns.
        complete = merged.notna().all(axis=1)
        if not complete.any():
            raise ValueError(f"no rows where all of {universe} are simultaneously present")
        merged = merged.loc[complete.idxmax() :]

        self._validate_positive(merged)
        return cast(pd.DataFrame, merged)

    def _yfinance_fetch(self, symbols: list[str]) -> pd.DataFrame:
        from alphakit.data.equities.yfinance_adapter import YFinanceAdapter

        return YFinanceAdapter().fetch(
            symbols=symbols,
            start=datetime.fromisoformat(self.data_start),
            end=datetime.fromisoformat(self.out_of_sample_end),
        )

    def _fred_fetch(self, symbols: list[str]) -> pd.DataFrame:
        from alphakit.data.rates.fred_adapter import FREDAdapter

        return FREDAdapter().fetch(
            symbols=symbols,
            start=datetime.fromisoformat(self.data_start),
            end=datetime.fromisoformat(self.out_of_sample_end),
        )

    def _fetch_feed(
        self,
        symbols: list[str],
        feed_name: str,
        real_fetch: Callable[[list[str]], pd.DataFrame],
    ) -> pd.DataFrame:
        """Fetch ``symbols`` from a real feed, or fixtures per ``strict_feed``.

        ``strict_feed=True`` re-raises any real-feed failure (missing package,
        unconfigured key, offline, network, empty result). ``strict_feed=False``
        falls back to deterministic fixtures (CI/test-safe).
        """
        try:
            df = real_fetch(symbols)
            if df.empty:
                raise RuntimeError(f"{feed_name!r} returned an empty DataFrame")
            return df
        except Exception:
            if self.strict_feed:
                raise
            from alphakit.data.fixtures.generator import generate_fixture_prices

            return generate_fixture_prices(
                symbols=symbols,
                start=self.data_start,
                end=self.out_of_sample_end,
            )

    @staticmethod
    def _validate_positive(panel: pd.DataFrame) -> None:
        """Fail loud if any column has a non-finite or non-positive value.

        Enforces the vectorbt bridge constraint (``order.price`` finite and
        > 0) on every column — tradable *and* informational — per the
        2026-05-16 amendment. The bridge treats informational columns as
        ``close`` prices too.
        """
        arr = panel.to_numpy(dtype=float)
        if not np.isfinite(arr).all():
            bad = [c for c in panel.columns if not np.isfinite(panel[c]).all()]
            raise ValueError(f"non-finite values in feed columns: {bad}")
        if not (arr > 0).all():
            bad = [c for c in panel.columns if not (panel[c] > 0).all()]
            raise ValueError(
                f"non-positive values in feed columns {bad}; the vectorbt bridge "
                "requires every column (incl. informational) to be strictly "
                "positive — pass raw positive level/index series and derive "
                "signals internally (see docs/phase-2-amendments.md 2026-05-16)"
            )
