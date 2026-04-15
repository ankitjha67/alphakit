"""Bridge to the `vectorbt <https://vectorbt.dev>`_ backtester.

Vectorbt is the fastest open-source Python backtester for daily-ish
strategies: it compiles signals into NumPy/Numba kernels that run in the
low-millisecond range for thousands of symbols.

This bridge adapts any :class:`~alphakit.core.protocols.StrategyProtocol`
that emits a weights DataFrame into a ``vbt.Portfolio.from_orders`` call,
then normalises the result into :class:`BacktestResult`.

Design notes
------------
* The import of ``vectorbt`` is local to :func:`run` so that simply
  loading ``alphakit.bridges`` does not pull in Numba / NumPy ABI
  compatibility issues.
* We route via ``from_orders`` (not ``from_signals``) because weights are
  the strategy's native output; converting to entry/exit booleans would
  lose information.
* Commission and slippage are expressed in **basis points** of notional
  to match the rest of AlphaKit, then translated into vectorbt's
  fractional representation at call time.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
from alphakit.core.metrics.drawdown import max_drawdown
from alphakit.core.metrics.returns import calmar_ratio, sharpe_ratio, sortino_ratio
from alphakit.core.protocols import BacktestResult, StrategyProtocol

NAME: str = "vectorbt"


def _import_vectorbt() -> Any:
    """Import vectorbt lazily, raising a helpful error on failure."""
    try:
        import vectorbt as vbt
    except ImportError as exc:  # pragma: no cover - exercised only w/o vbt
        raise ImportError(
            "vectorbt is required for the vectorbt_bridge. "
            "Install with `pip install 'alphakit-bridges[vectorbt]'` "
            "or `pip install vectorbt`."
        ) from exc
    return vbt


def run(
    strategy: StrategyProtocol,
    prices: pd.DataFrame,
    *,
    initial_cash: float = 100_000.0,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
    frequency: str = "1D",
) -> BacktestResult:
    """Backtest ``strategy`` on ``prices`` with vectorbt.

    Parameters
    ----------
    strategy
        Any object satisfying :class:`StrategyProtocol`.
    prices
        DataFrame indexed by timestamp, columns are instrument symbols,
        values are adjusted close prices.
    initial_cash
        Starting cash balance in the portfolio base currency.
    commission_bps
        Round-trip commission in basis points of notional.
    slippage_bps
        Execution slippage in basis points of notional.
    frequency
        Pandas offset alias describing the bar frequency — passed to
        vectorbt for annualisation.
    """
    if prices.empty:
        raise ValueError("prices DataFrame is empty")
    if commission_bps < 0 or slippage_bps < 0:
        raise ValueError("commission_bps and slippage_bps must be non-negative")
    if initial_cash <= 0:
        raise ValueError(f"initial_cash must be positive, got {initial_cash}")

    vbt = _import_vectorbt()

    # 1. Ask the strategy for a target-weights panel and align it to prices.
    weights = strategy.generate_signals(prices)
    weights = weights.reindex_like(prices).fillna(0.0)

    # 2. Translate weights into size orders interpretable by vectorbt:
    #    we use target-percent orders, one per bar, on every symbol.
    size_type = vbt.portfolio.enums.SizeType.TargetPercent

    fees = commission_bps / 10_000.0
    slippage = slippage_bps / 10_000.0

    portfolio = vbt.Portfolio.from_orders(
        close=prices,
        size=weights,
        size_type=size_type,
        init_cash=initial_cash,
        fees=fees,
        slippage=slippage,
        freq=frequency,
        group_by=True,  # treat all symbols as a single portfolio
        cash_sharing=True,
    )

    # 3. Extract the equity curve and per-bar returns as pandas objects.
    equity_raw = portfolio.value()
    equity_curve = cast(
        pd.Series, equity_raw.squeeze() if hasattr(equity_raw, "squeeze") else equity_raw
    )
    if not isinstance(equity_curve, pd.Series):
        equity_curve = pd.Series(equity_curve, index=prices.index)
    equity_curve = equity_curve.astype(float)
    equity_curve.name = "equity"

    returns = equity_curve.pct_change().fillna(0.0)
    returns.name = "returns"

    # 4. Headline metrics from our own implementation (not vbt's) so that
    #    every engine reports the same numbers.
    returns_arr = returns.to_numpy()
    metrics: dict[str, float] = {
        "sharpe": sharpe_ratio(returns_arr),
        "sortino": sortino_ratio(returns_arr),
        "calmar": calmar_ratio(returns_arr),
        "max_drawdown": max_drawdown(returns_arr),
        "final_equity": float(equity_curve.iloc[-1]),
        "total_return": float(equity_curve.iloc[-1] / initial_cash - 1.0),
    }
    if np.isfinite(returns_arr).any():
        metrics["annualized_return"] = float(np.mean(returns_arr) * 252)
        metrics["annualized_vol"] = float(np.std(returns_arr, ddof=1) * np.sqrt(252))
    else:
        metrics["annualized_return"] = 0.0
        metrics["annualized_vol"] = 0.0

    return BacktestResult(
        equity_curve=equity_curve,
        returns=returns,
        weights=weights,
        metrics=metrics,
        meta={
            "engine": NAME,
            "initial_cash": initial_cash,
            "commission_bps": commission_bps,
            "slippage_bps": slippage_bps,
            "frequency": frequency,
            "strategy": strategy.name,
            "family": strategy.family,
            "paper_doi": strategy.paper_doi,
        },
    )
