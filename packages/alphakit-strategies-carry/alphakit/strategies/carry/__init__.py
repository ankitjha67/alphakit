"""Carry strategies.

Phase 1 ships 10 carry strategies — FX carry (G10, EM), dividend yield,
equity carry, bond carry, vol carry, crypto funding, repo carry, swap
spread carry, and cross-asset carry — per the master plan section 4.4.

Note: carry strategies use price-derived proxies for yield/rate data.
See ADR-001 (docs/adr/001-carry-data-deferred.md) for rationale.
"""

from __future__ import annotations

from alphakit.strategies.carry.bond_carry_roll.strategy import BondCarryRoll
from alphakit.strategies.carry.dividend_yield.strategy import DividendYield
from alphakit.strategies.carry.equity_carry.strategy import EquityCarry
from alphakit.strategies.carry.fx_carry_em.strategy import FXCarryEM
from alphakit.strategies.carry.fx_carry_g10.strategy import FXCarryG10

__all__: list[str] = [
    "BondCarryRoll",
    "DividendYield",
    "EquityCarry",
    "FXCarryEM",
    "FXCarryG10",
]
