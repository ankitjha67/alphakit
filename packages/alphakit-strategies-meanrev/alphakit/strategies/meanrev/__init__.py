"""Mean-reversion strategies.

Phase 1 ships 15 mean-reversion strategies — Bollinger bands, RSI variants,
Z-score, Ornstein-Uhlenbeck, short/long-term reversal, overnight/intraday,
gap fill, crypto basis, and five pair-trading variants — per the master plan
section 4.3.
"""

from __future__ import annotations

from alphakit.strategies.meanrev.bollinger_reversion.strategy import BollingerReversion
from alphakit.strategies.meanrev.rsi_reversion_2.strategy import RSIReversion2
from alphakit.strategies.meanrev.rsi_reversion_14.strategy import RSIReversion14

__all__: list[str] = [
    "BollingerReversion",
    "RSIReversion2",
    "RSIReversion14",
]
