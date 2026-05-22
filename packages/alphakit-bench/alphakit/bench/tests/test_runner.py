"""Tests for alphakit.bench.runner."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from alphakit.bench import discovery
from alphakit.bench.runner import BenchmarkRunner
from alphakit.data.errors import FeedNotConfiguredError


@pytest.fixture
def runner() -> BenchmarkRunner:
    return BenchmarkRunner(
        commission_bps=5.0,
        data_start="2005-01-01",
        in_sample_end="2019-12-31",
        out_of_sample_end="2025-12-31",
    )


class TestBenchmarkRunner:
    def test_run_single_produces_valid_result(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        assert result["slug"] == "tsmom_12_1"
        assert result["status"] == "populated"
        assert result["engine"] == "vectorbt"

    def test_result_has_all_metric_keys(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        metrics = result["metrics"]
        for key in (
            "sharpe",
            "sortino",
            "calmar",
            "max_drawdown",
            "annualized_return",
            "annualized_vol",
            "turnover_annual",
            "capacity_usd_bn",
        ):
            assert key in metrics
            assert isinstance(metrics[key], float)
            assert np.isfinite(metrics[key])

    def test_result_has_regime_performance(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        regime = result["regime_performance"]
        for key in ("bull_market_sharpe", "bear_market_sharpe", "sideways_sharpe"):
            assert key in regime
            assert isinstance(regime[key], float)

    def test_result_has_metadata(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        assert result["data_start"] == "2005-01-01"
        assert result["in_sample_end"] == "2019-12-31"
        assert result["out_of_sample_end"] == "2025-12-31"
        assert result["transaction_costs_assumed_bps"] == 5.0
        assert isinstance(result["universe"], list)

    def test_result_is_json_serializable(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        assert deserialized["slug"] == "tsmom_12_1"

    def test_write_benchmark(
        self,
        runner: BenchmarkRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Redirect the resolved benchmark path into tmp_path so the write
        # never touches the tracked in-repo benchmark_results.json. (The
        # runner resolves the target via discovery.benchmark_results_path.)
        target = tmp_path / "benchmark_results.json"
        monkeypatch.setattr(discovery, "benchmark_results_path", lambda family, slug: target)

        result = runner.run_single("tsmom_12_1")
        result["slug"] = "tsmom_12_1"

        path = runner.write_benchmark("tsmom_12_1", result, family="trend")
        # Guard: the write must land at the redirected target, not the repo.
        assert path == target
        assert path.exists()
        with open(path) as f:
            written = json.load(f)
        assert written["slug"] == "tsmom_12_1"
        assert written["status"] == "populated"

    def test_write_benchmark_does_not_mutate_repo_file(
        self,
        runner: BenchmarkRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Regression guard for the working-tree-pollution bug: with the
        # benchmark path redirected, write_benchmark must leave the tracked
        # in-repo file byte-for-byte unchanged.
        real_path = discovery.benchmark_results_path("trend", "tsmom_12_1")
        before = real_path.read_bytes()

        target = tmp_path / "benchmark_results.json"
        monkeypatch.setattr(discovery, "benchmark_results_path", lambda family, slug: target)

        result = runner.run_single("tsmom_12_1")
        runner.write_benchmark("tsmom_12_1", result, family="trend")

        assert target.exists(), "redirected write should land in tmp_path"
        assert real_path.read_bytes() == before, "tracked repo file must be untouched"

    def test_auto_detect_family(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("vol_targeting")
        assert result["slug"] == "vol_targeting"

    def test_deterministic_results(self, runner: BenchmarkRunner) -> None:
        a = runner.run_single("tsmom_12_1")
        b = runner.run_single("tsmom_12_1")
        assert a["metrics"]["sharpe"] == b["metrics"]["sharpe"]


# ---------------------------------------------------------------------------
# Session 2I — multi-feed runner (split routing, FRED alignment, strict_feed)
# ---------------------------------------------------------------------------

_YF_PATH = "alphakit.data.equities.yfinance_adapter.YFinanceAdapter.fetch"
_FRED_PATH = "alphakit.data.rates.fred_adapter.FREDAdapter.fetch"

# Realistic positive magnitudes per FRED series (so regime thresholds behave).
_FRED_MAG: dict[str, tuple[float, float]] = {
    "RECPROUSM156N": (0.1, 0.5),
    "CPIAUCSL": (250.0, 285.0),
    "GDPC1": (20000.0, 23000.0),
    "DGS10": (1.5, 4.0),
    "DGS2": (1.0, 3.0),
    "FEDFUNDS": (0.25, 4.0),
}


class _StubFREDGated:
    """Strategy stub exposing the Session 2G routing properties (has FRED cols)."""

    tradable_symbols = ("SPY", "TLT", "GLD")
    required_symbols = ("SPY", "TLT", "GLD", "DGS10", "DGS2")


class _StubGDP:
    """Strategy stub whose only informational column is quarterly GDPC1."""

    tradable_symbols = ("SPY", "TLT", "GLD", "DBC")
    required_symbols = ("SPY", "TLT", "GLD", "DBC", "GDPC1")


class _StubETFOnly:
    """Strategy stub with no informational columns (single-feed)."""

    tradable_symbols = ("SPY", "TLT", "GLD")
    required_symbols = ("SPY", "TLT", "GLD")


def _bdays(start: str = "2005-01-01", end: str = "2025-12-31") -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="B")


def _etf_panel(symbols: list[str], index: pd.DatetimeIndex) -> pd.DataFrame:
    """Positive daily ETF prices for the requested symbols."""
    return pd.DataFrame(
        {s: np.linspace(100.0, 150.0, len(index)) for s in symbols},
        index=index,
    )


def _fred_panel(symbols: list[str], index: pd.DatetimeIndex) -> pd.DataFrame:
    """Positive FRED series for the requested symbols at the given (native) index.

    A monotonic ramp lo→hi (distinct per row, so each native observation differs
    after ffill) that also crosses each series' regime threshold once.
    """
    n = len(index)
    cols = {}
    for s in symbols:
        lo, hi = _FRED_MAG.get(s, (1.0, 5.0))
        cols[s] = np.linspace(lo, hi, n) if n > 1 else np.full(n, (lo + hi) / 2)
    return pd.DataFrame(cols, index=index)


def _patch_feeds(
    monkeypatch: pytest.MonkeyPatch,
    *,
    etf_index: pd.DatetimeIndex,
    fred_index: pd.DatetimeIndex,
    fred_exc: Exception | None = None,
) -> None:
    """Patch both adapter.fetch methods to return synthetic positive panels."""

    def _yf(
        self: object, symbols: list[str], start: object, end: object, frequency: str = "1d"
    ) -> pd.DataFrame:
        return _etf_panel(list(symbols), etf_index)

    def _fred(
        self: object, symbols: list[str], start: object, end: object, frequency: str = "1d"
    ) -> pd.DataFrame:
        if fred_exc is not None:
            raise fred_exc
        return _fred_panel(list(symbols), fred_index)

    monkeypatch.setattr(_YF_PATH, _yf)
    monkeypatch.setattr(_FRED_PATH, _fred)


class TestInformationalColumnRouting:
    def test_split_for_fred_gated(self, runner: BenchmarkRunner) -> None:
        universe = ["SPY", "TLT", "GLD", "DGS10", "DGS2"]
        assert runner._informational_columns(_StubFREDGated(), universe) == ["DGS10", "DGS2"]

    def test_empty_for_etf_only(self, runner: BenchmarkRunner) -> None:
        assert runner._informational_columns(_StubETFOnly(), ["SPY", "TLT", "GLD"]) == []

    def test_empty_when_no_routing_properties(self, runner: BenchmarkRunner) -> None:
        # A plain object (no tradable_symbols/required_symbols) → single-feed.
        assert runner._informational_columns(object(), ["SPY", "TLT"]) == []


class TestMultiFeedFetch:
    def test_etf_only_never_calls_fred(
        self, runner: BenchmarkRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        called = {"fred": False}

        def _yf(
            self: object, symbols: list[str], start: object, end: object, frequency: str = "1d"
        ) -> pd.DataFrame:
            return _etf_panel(list(symbols), _bdays("2018-01-01", "2020-12-31"))

        def _fred(self: object, *a: object, **k: object) -> pd.DataFrame:
            called["fred"] = True
            raise AssertionError("FRED must not be called for an ETF-only universe")

        monkeypatch.setattr(_YF_PATH, _yf)
        monkeypatch.setattr(_FRED_PATH, _fred)
        panel = runner._fetch_prices(["SPY", "TLT", "GLD"], strategy=_StubETFOnly())
        assert list(panel.columns) == ["SPY", "TLT", "GLD"]
        assert called["fred"] is False

    def test_split_routes_and_merges(
        self, runner: BenchmarkRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = _bdays("2010-01-01", "2015-12-31")
        monthly = pd.date_range("2010-01-01", "2015-12-31", freq="MS")
        _patch_feeds(monkeypatch, etf_index=idx, fred_index=monthly)
        universe = ["SPY", "TLT", "GLD", "DGS10", "DGS2"]
        panel = runner._fetch_prices(universe, strategy=_StubFREDGated())
        # column order preserved == universe; all present, all positive
        assert list(panel.columns) == universe
        assert panel.notna().all().all()
        assert (panel.to_numpy() > 0).all()

    def test_quarterly_gdp_ffill_alignment(
        self, runner: BenchmarkRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = _bdays("2010-01-01", "2012-12-31")
        quarterly = pd.date_range("2010-01-01", "2012-12-31", freq="QS")  # quarter starts
        _patch_feeds(monkeypatch, etf_index=idx, fred_index=quarterly)
        universe = ["SPY", "TLT", "GLD", "DBC", "GDPC1"]
        panel = runner._fetch_prices(universe, strategy=_StubGDP())
        gdp = panel["GDPC1"]
        # No mid-panel gaps after ffill.
        assert gdp.notna().all()
        # ~12 quarterly values spread across ~63 business days each (no bfill:
        # the count of distinct values matches the number of quarters covered).
        assert 8 <= gdp.nunique() <= 13
        # Each distinct value persists for roughly a quarter (~45-70 bdays).
        run_lengths = gdp.groupby((gdp != gdp.shift()).cumsum()).size()
        assert run_lengths.max() <= 75

    def test_zero_trim_when_fred_starts_with_etf(
        self, runner: BenchmarkRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = _bdays("2010-01-04", "2011-12-30")
        # FRED first observation coincides with the first ETF bar → zero trim.
        fred_idx = pd.DatetimeIndex([idx[0], *pd.date_range("2010-02-01", "2011-12-30", freq="MS")])
        _patch_feeds(monkeypatch, etf_index=idx, fred_index=fred_idx)
        panel = runner._fetch_prices(
            ["SPY", "TLT", "GLD", "DGS10", "DGS2"], strategy=_StubFREDGated()
        )
        assert panel.index[0] == idx[0]  # no leading rows trimmed


class TestPositivityValidation:
    def test_negative_informational_raises(
        self, runner: BenchmarkRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = _bdays("2012-01-01", "2014-12-31")
        monthly = pd.date_range("2012-01-01", "2014-12-31", freq="MS")

        def _yf(
            self: object, symbols: list[str], start: object, end: object, frequency: str = "1d"
        ) -> pd.DataFrame:
            return _etf_panel(list(symbols), idx)

        def _fred(
            self: object, symbols: list[str], start: object, end: object, frequency: str = "1d"
        ) -> pd.DataFrame:
            df = _fred_panel(list(symbols), monthly)
            df.iloc[5, 0] = -1.0  # inject a negative informational value
            return df

        monkeypatch.setattr(_YF_PATH, _yf)
        monkeypatch.setattr(_FRED_PATH, _fred)
        with pytest.raises(ValueError, match="non-positive"):
            runner._fetch_prices(["SPY", "TLT", "GLD", "DGS10", "DGS2"], strategy=_StubFREDGated())


class TestStrictFeed:
    def test_strict_true_propagates_fred_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = _bdays("2015-01-01", "2017-12-31")
        _patch_feeds(
            monkeypatch,
            etf_index=idx,
            fred_index=idx,
            fred_exc=FeedNotConfiguredError("fred requires FRED_API_KEY"),
        )
        runner = BenchmarkRunner(strict_feed=True)
        with pytest.raises(FeedNotConfiguredError):
            runner._fetch_prices(["SPY", "TLT", "GLD", "DGS10", "DGS2"], strategy=_StubFREDGated())

    def test_strict_false_falls_back_to_fixtures(self, monkeypatch: pytest.MonkeyPatch) -> None:
        idx = _bdays("2015-01-01", "2017-12-31")
        _patch_feeds(
            monkeypatch,
            etf_index=idx,
            fred_index=idx,
            fred_exc=FeedNotConfiguredError("fred requires FRED_API_KEY"),
        )
        runner = BenchmarkRunner(strict_feed=False)
        panel = runner._fetch_prices(
            ["SPY", "TLT", "GLD", "DGS10", "DGS2"], strategy=_StubFREDGated()
        )
        # Fixture fallback fills the FRED columns with positive synthetic series.
        assert set(panel.columns) == {"SPY", "TLT", "GLD", "DGS10", "DGS2"}
        assert (panel.to_numpy() > 0).all()


class TestMultiFeedIntegration:
    # NOTE: publication-lag is the strategy's concern (.shift on the
    # month-end-resampled series); FRED returns reference-period-dated
    # observations, so the runner is publication-lag-agnostic. No runner-level
    # publication-lag test is needed (would test an unrealistic feed shape).
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "slug",
        [
            "recession_probability_rotation",
            "growth_inflation_regime_rotation",
            "yield_curve_regime_allocation",
            "fed_policy_tilt",
            "inflation_regime_allocation",
        ],
    )
    def test_regime_strategy_end_to_end_multifeed(
        self, runner: BenchmarkRunner, monkeypatch: pytest.MonkeyPatch, slug: str
    ) -> None:
        idx = _bdays("2005-01-01", "2025-12-31")
        monthly = pd.date_range("2005-01-01", "2025-12-31", freq="MS")
        _patch_feeds(monkeypatch, etf_index=idx, fred_index=monthly)
        result = runner.run_single(slug, family="macro")
        assert result["slug"] == slug
        assert np.isfinite(result["metrics"]["sharpe"])
        assert np.isfinite(result["metrics"]["max_drawdown"])
