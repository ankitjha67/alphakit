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

__all__: list[str] = []
