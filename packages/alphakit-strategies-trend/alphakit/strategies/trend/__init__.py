"""Trend-following strategies.

Phase 0 ships one reference strategy: ``tsmom_12_1`` (Moskowitz, Ooi,
Pedersen 2012). Phase 1 adds 14 more — cross-sectional momentum, dual
momentum, residual momentum, 52-week high, SMA/EMA crosses, Donchian,
Turtle, Ichimoku, SuperTrend — per the master plan section 4.2.
"""

from __future__ import annotations

from alphakit.strategies.trend.tsmom_12_1.strategy import TimeSeriesMomentum12m1m
from alphakit.strategies.trend.tsmom_volscaled.strategy import TimeSeriesMomentumVolScaled
from alphakit.strategies.trend.xs_momentum_jt.strategy import CrossSectionalMomentumJT

__all__ = [
    "CrossSectionalMomentumJT",
    "TimeSeriesMomentum12m1m",
    "TimeSeriesMomentumVolScaled",
]
