"""Mean-reversion strategies.

Phase 1 ships 15 mean-reversion strategies — Bollinger bands, RSI variants,
Z-score, Ornstein-Uhlenbeck, short/long-term reversal, overnight/intraday,
gap fill, crypto basis, and five pair-trading variants — per the master plan
section 4.3.
"""

from __future__ import annotations

from alphakit.strategies.meanrev.bollinger_reversion.strategy import BollingerReversion

__all__: list[str] = [
    "BollingerReversion",
]
