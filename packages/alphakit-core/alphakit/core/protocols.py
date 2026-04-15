"""Runtime-checkable protocols defining the AlphaKit engine seam.

These protocols are the *entire* interface that sub-packages must implement.
Keeping this file small, stable and dependency-light is critical to the
project's modular promise: a new engine, strategy or data feed plugs in by
implementing one of these three protocols, nothing more.

Design notes
------------
* ``runtime_checkable`` is enabled so downstream code can ``isinstance``-check
  objects against the protocol without forcing explicit subclassing. The cost
  is that only *method existence* is verified at runtime, not signatures;
  the real contract is enforced statically by mypy strict.
* We accept ``pd.DataFrame`` for prices and return ``pd.DataFrame`` for
  weights because that's the canonical shape for vectorised backtests
  (time × symbols). Signal-list-based strategies are a convenience layer
  built on top of this, not part of the core protocol.
* ``BacktestResult`` is defined here (not in ``metrics/``) because it is
  part of the protocol surface and would create a circular import otherwise.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class BacktestResult(BaseModel):
    """Uniform output of any ``BacktestEngineProtocol.run`` implementation.

    All engine bridges (internal, vectorbt, backtrader, LEAN) are required to
    normalise their native output into this structure so that strategies,
    notebooks and the benchmark runner can treat every engine identically.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    equity_curve: pd.Series
    """Total portfolio equity over time, indexed by bar timestamp."""

    returns: pd.Series
    """Per-bar portfolio returns, aligned to ``equity_curve``."""

    weights: pd.DataFrame
    """Target weights per symbol over time (time × symbols)."""

    metrics: dict[str, float] = Field(default_factory=dict)
    """Headline metrics (sharpe, max_dd, calmar, ...). See ``alphakit.core.metrics``."""

    meta: dict[str, Any] = Field(default_factory=dict)
    """Free-form metadata: engine name, version, commit_sha, runtime."""


@runtime_checkable
class StrategyProtocol(Protocol):
    """The one interface every AlphaKit strategy implements.

    A strategy is a *pure* function of a price panel: given OHLCV data,
    produce a weights DataFrame. The framework handles sizing, execution,
    commissions and bookkeeping.

    Required class-level metadata
    -----------------------------
    * ``name``             — unique slug, e.g. ``"tsmom_12_1"``
    * ``family``           — strategy family, e.g. ``"trend"``
    * ``asset_classes``    — tuple of asset classes this strategy is valid for
    * ``paper_doi``        — DOI, arXiv link, or book ISBN. **Never blank.**
    * ``rebalance_frequency`` — ``"daily"`` | ``"weekly"`` | ``"monthly"`` | ...
    """

    name: str
    family: str
    asset_classes: tuple[str, ...]
    paper_doi: str
    rebalance_frequency: str

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Transform a price panel into a target-weights DataFrame.

        Parameters
        ----------
        prices
            DataFrame indexed by timestamp, columns are instrument symbols,
            values are adjusted closing prices (float). May contain ``NaN``
            for instruments that did not yet trade.

        Returns
        -------
        weights
            DataFrame with the same index and columns as ``prices``. Each
            row is a set of target portfolio weights summing (by convention)
            to 1.0 for long-only strategies, to 0.0 for market-neutral,
            or unconstrained for leveraged/short strategies. ``NaN`` is
            interpreted as zero weight.
        """
        ...


@runtime_checkable
class BacktestEngineProtocol(Protocol):
    """The single entrypoint every engine bridge exposes.

    Implementations include: the internal vectorised engine, vectorbt,
    backtrader, LEAN (Phase 2+), and nautilus (Phase 4+).
    """

    name: str
    """Engine identifier — ``"internal"``, ``"vectorbt"``, ``"backtrader"``, ..."""

    def run(
        self,
        strategy: StrategyProtocol,
        prices: pd.DataFrame,
        *,
        initial_cash: float = 100_000.0,
        commission_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> BacktestResult:
        """Execute ``strategy`` on ``prices`` and return a normalised result."""
        ...


@runtime_checkable
class DataFeedProtocol(Protocol):
    """The interface every data adapter implements.

    Implementations include: yfinance, stooq, polygon, CCXT, Binance,
    Deribit, FRED, and synthetic-data helpers.
    """

    name: str
    """Feed identifier — ``"yfinance"``, ``"ccxt"``, ``"fred"``, ..."""

    def fetch(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """Return a price panel for ``symbols`` between ``start`` and ``end``.

        The returned DataFrame is always timestamp-indexed with one column
        per symbol containing adjusted close prices. Adapters that expose
        full OHLCV return a ``MultiIndex`` on columns (``symbol``, ``field``).
        """
        ...
