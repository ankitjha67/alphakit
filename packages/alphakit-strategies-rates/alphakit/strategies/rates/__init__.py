"""Rates strategies — Phase 2 Session 2D.

Phase 2 target: 13 strategies on US Treasury yield curves, breakeven
inflation, real yields, sovereign cross-section carry, IG credit spreads,
swap-Treasury spreads, and global inflation differentials.

Strategy classes are added to ``__all__`` as each per-strategy commit
lands within Session 2D. The shipping count is 13 rather than the
originally-planned 15: ``fed_funds_surprise`` and ``fra_ois_spread``
were dropped under the Phase 2 honesty-check (no fed-funds-futures
data on FRED; FRA-OIS is a stress indicator, not a systematic
strategy with a citable rule). See ``docs/phase-2-amendments.md`` for
the full audit trail.
"""

from __future__ import annotations

from alphakit.strategies.rates.bond_carry_rolldown.strategy import BondCarryRolldown
from alphakit.strategies.rates.bond_tsmom_12_1.strategy import BondTSMOM12m1m
from alphakit.strategies.rates.breakeven_inflation_rotation.strategy import (
    BreakevenInflationRotation,
)
from alphakit.strategies.rates.curve_butterfly_2s5s10s.strategy import CurveButterfly2s5s10s
from alphakit.strategies.rates.curve_flattener_2s10s.strategy import CurveFlattener2s10s
from alphakit.strategies.rates.curve_steepener_2s10s.strategy import CurveSteepener2s10s
from alphakit.strategies.rates.duration_targeted_momentum.strategy import (
    DurationTargetedMomentum,
)

__all__ = [
    "BondCarryRolldown",
    "BondTSMOM12m1m",
    "BreakevenInflationRotation",
    "CurveButterfly2s5s10s",
    "CurveFlattener2s10s",
    "CurveSteepener2s10s",
    "DurationTargetedMomentum",
]
