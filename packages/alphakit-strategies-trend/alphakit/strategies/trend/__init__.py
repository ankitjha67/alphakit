"""Trend-following strategies.

Phase 0 ships one reference strategy: ``tsmom_12_1`` (Moskowitz, Ooi,
Pedersen 2012). Phase 1 adds 14 more — cross-sectional momentum, dual
momentum, residual momentum, 52-week high, SMA/EMA crosses, Donchian,
Turtle, Ichimoku, SuperTrend — per the master plan section 4.2.
"""

from __future__ import annotations

from alphakit.strategies.trend.tsmom_12_1.strategy import TimeSeriesMomentum12m1m

__all__ = ["TimeSeriesMomentum12m1m"]
