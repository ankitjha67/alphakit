"""Integration tests for max_diversification_10asset.

Mocks ``YFinanceAdapter.fetch`` to return a deterministic synthetic
10-ETF panel, runs the strategy through the vectorbt bridge, and asserts
the returned :class:`BacktestResult` is internally consistent. Network is
never touched.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from alphakit.bridges import vectorbt_bridge
from alphakit.core.protocols import BacktestResult
from alphakit.data.equities.yfinance_adapter import YFinanceAdapter
from alphakit.strategies.macro._gtaa10_universe import GTAA10_UNIVERSE
from alphakit.strategies.macro.max_diversification_10asset.strategy import (
    MaxDiversification10Asset,
)


def _synthetic_10_asset_panel(seed: int = 42, years: float = 6.0) -> pd.DataFrame:
    """Deterministic 10-ETF panel with a volatility spread across sleeves.

    Volatilities are ordered to mirror the real universe, where the
    short-duration Treasury leg carries the lowest variance and the
    emerging-market equity leg the highest.
    """
    rng = np.random.default_rng(seed)
    n_days = round(years * 252)
    index = pd.date_range("2015-01-01", periods=n_days, freq="B")
    vols = {
        "SHY": 0.0015,
        "IEF": 0.0035,
        "LQD": 0.0040,
        "TLT": 0.0085,
        "GLD": 0.0090,
        "SPY": 0.0105,
        "EFA": 0.0115,
        "DBC": 0.0120,
        "VNQ": 0.0135,
        "EEM": 0.0145,
    }
    prices: dict[str, np.ndarray] = {}
    for symbol in GTAA10_UNIVERSE:
        shocks = rng.normal(0.00025, vols[symbol], size=n_days)
        prices[symbol] = 100.0 * np.exp(np.cumsum(shocks))
    frame = pd.DataFrame(prices, index=index)
    ordered: pd.DataFrame = frame.loc[:, list(GTAA10_UNIVERSE)]
    return ordered


@pytest.mark.integration
def test_backtest_runs_end_to_end_with_mocked_yfinance() -> None:
    panel = _synthetic_10_asset_panel(seed=42, years=6.0)

    with patch.object(YFinanceAdapter, "fetch", return_value=panel) as mock_fetch:
        adapter = YFinanceAdapter()
        prices = adapter.fetch(
            symbols=list(panel.columns),
            start=datetime(2015, 1, 1),
            end=datetime(2021, 1, 1),
        )
        assert mock_fetch.called

    strategy = MaxDiversification10Asset()
    result = vectorbt_bridge.run(
        strategy=strategy,
        prices=prices,
        initial_cash=100_000.0,
        commission_bps=2.0,
        slippage_bps=1.0,
    )

    assert isinstance(result, BacktestResult)
    assert result.meta["engine"] == "vectorbt"
    assert result.meta["strategy"] == "max_diversification_10asset"
    assert result.meta["paper_doi"] == "10.2139/ssrn.1895459"

    assert len(result.equity_curve) == len(prices)
    assert len(result.returns) == len(prices)
    assert result.weights.shape == prices.shape

    for key in ("sharpe", "sortino", "calmar", "max_drawdown", "final_equity"):
        assert key in result.metrics, f"missing metric: {key}"
        assert np.isfinite(result.metrics[key]), f"non-finite metric: {key}"

    assert result.metrics["max_drawdown"] <= 0.0


@pytest.mark.integration
def test_backtest_is_deterministic_with_mocked_yfinance() -> None:
    panel = _synthetic_10_asset_panel(seed=123, years=5.0)

    with patch.object(YFinanceAdapter, "fetch", return_value=panel):
        adapter = YFinanceAdapter()
        prices_a = adapter.fetch(
            symbols=list(panel.columns),
            start=datetime(2015, 1, 1),
            end=datetime(2020, 1, 1),
        )
        prices_b = adapter.fetch(
            symbols=list(panel.columns),
            start=datetime(2015, 1, 1),
            end=datetime(2020, 1, 1),
        )
    pd.testing.assert_frame_equal(prices_a, prices_b)

    strategy = MaxDiversification10Asset()
    result_a = vectorbt_bridge.run(strategy=strategy, prices=prices_a)
    result_b = vectorbt_bridge.run(strategy=strategy, prices=prices_b)

    pd.testing.assert_series_equal(result_a.equity_curve, result_b.equity_curve)
    pd.testing.assert_frame_equal(result_a.weights, result_b.weights)
    for key, value in result_a.metrics.items():
        assert result_b.metrics[key] == pytest.approx(value)


@pytest.mark.integration
def test_backtest_rejects_empty_prices() -> None:
    empty = pd.DataFrame(
        index=pd.DatetimeIndex([]),
        columns=list(GTAA10_UNIVERSE),
        dtype=float,
    )
    with pytest.raises(ValueError, match="empty"):
        vectorbt_bridge.run(strategy=MaxDiversification10Asset(), prices=empty)
