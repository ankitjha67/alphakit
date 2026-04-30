"""Contrarian COT speculator-positioning trade on commodity futures.

Implementation notes
====================

Foundational paper
------------------
Bessembinder, H. (1992).
*Systematic risk, hedging pressure, and risk premiums in futures markets*.
Review of Financial Studies, 5(4), 637–667.
https://doi.org/10.1093/rfs/5.4.637

Bessembinder (1992) decomposes the futures-curve risk premium into
hedging-pressure and macro-risk components. The empirical result:
**commercial hedgers earn a discount on their hedge sales /
purchases, and speculators earn the corresponding premium for
taking the other side.** Equivalently — when speculators crowd
into one direction, the premium they earn is competed away and
expected forward returns are negative.

Primary methodology
-------------------
de Roon, F. A., Nijman, T. E. & Veld, C. (2000).
*Hedging pressure effects in futures markets*.
Journal of Finance, 55(3), 1437–1456.
https://doi.org/10.1111/0022-1082.00253

de Roon-Nijman-Veld (2000) directly test the hedging-pressure
hypothesis on the CFTC Commitments of Traders (COT) data and find
that **non-commercial (speculator) net positioning predicts futures
returns with the wrong sign** — i.e. extreme speculator long
positioning forecasts negative returns; extreme speculator short
positioning forecasts positive returns. This is the contrarian COT
signal.

The strategy
------------
For each commodity *c* with a paired COT positioning column:

1. Compute the **historical percentile** of the
   net-speculator-position (long minus short, normalised by open
   interest) over a rolling ``percentile_lookback_weeks`` window
   (default 156 weeks ≈ 3 years).
2. When percentile > ``extreme_long_threshold`` (default 90 →
   speculators in the top decile of their long history) → **short**
   the front contract.
3. When percentile < ``extreme_short_threshold`` (default 10 →
   speculators in the bottom decile / extreme short) → **long**
   the front contract.
4. Otherwise → flat.

Friday-for-Tuesday COT lag
--------------------------
**Critical**: CFTC publishes the Commitments of Traders report
**every Friday at 15:30 ET**, covering positions held as of **the
prior Tuesday close**. The strategy *must* respect this Tuesday-
to-Friday publication lag — if today is Wednesday, the most recent
COT data we may legitimately use is the prior Friday's report
(which covers the Tuesday before that — six days earlier).

This implementation enforces the lag by **shifting the COT-derived
signal forward by ``cot_lag_days`` trading days** (default 3 ≈ a
Tuesday-to-Friday gap with a 1-day buffer for execution lag) before
applying the rule. Users running on real CFTC data should align
their ingestion to publish-Friday and pre-lag the data so the
synthetic shift here matches the live timeline.

A failure to apply the lag in backtests produces ~3-5% spurious
annualised excess returns from forward-looking bias on the
positioning data — the most common error in COT-strategy
research.

Input convention
----------------
The strategy expects a single DataFrame with **paired columns**
per commodity: a price column (e.g. ``"CL=F"``) and a positioning
column (e.g. ``"CL=F_NET_SPEC"``). The constructor parameter
``front_to_position_map`` defines the pairing.

Output is a DataFrame with one column per **traded front symbol**
(the keys of ``front_to_position_map``). Position columns are
consumed for the signal but not traded.

The positioning column should contain the **non-commercial long
fraction of open interest** (range ``(0, 1]``):

    long_fraction(t) = non_commercial_long(t) / open_interest(t)

The strictly-positive convention satisfies vectorbt-bridge price
validation (the bridge treats every input column as a tradeable
price even when the strategy assigns zero weight). Users with raw
**net** positioning data (range ``[-1, +1]``) should shift to
``(net + 1) / 2`` (range ``[0, 1]``, strictly positive after a
small floor) before passing in. The percentile rank used by the
trading rule is invariant to monotonic transformations, so the
shift does not change the signal — only the input scale.

Sign convention
---------------
Output values are in ``{-1.0, 0.0, +1.0}`` per traded leg. Multi-
asset legs are independently sized; the book is **not**
cross-sectionally normalised — a portfolio overlay can scale to
target gross/net.

Edge cases
----------
* Before ``percentile_lookback_weeks * 5`` trading days of history,
  the percentile is undefined and the signal is zero.
* Constant positioning (no historical variation) → percentile
  undefined → zero signal.
* Non-positive values in **any** input column (price or
  positioning) → ``ValueError``. Positioning data must be passed
  in the long-fraction or shifted-net form (range ``(0, 1]`` or
  ``(0, 2]``) so the bridge can validate it as a tradeable
  series.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

_DEFAULT_FRONT_TO_POSITION_MAP: dict[str, str] = {
    "CL=F": "CL=F_NET_SPEC",
    "NG=F": "NG=F_NET_SPEC",
    "GC=F": "GC=F_NET_SPEC",
    "ZC=F": "ZC=F_NET_SPEC",
}


class COTSpeculatorPosition:
    """Contrarian COT speculator-positioning trade.

    Long when speculators are extreme-short (bottom decile of their
    rolling positioning history); short when speculators are
    extreme-long (top decile); flat otherwise. Per de Roon-Nijman-
    Veld (2000) hedging-pressure effects on the CFTC COT data.

    Parameters
    ----------
    front_to_position_map
        Mapping ``{front_symbol: position_column}``. Defaults to a
        4-commodity panel: CL, NG, GC, ZC. The position column
        should contain net-speculator-position normalised by open
        interest.
    percentile_lookback_weeks
        Rolling window for computing the historical percentile of
        the positioning series. Defaults to ``156`` weeks (3 years).
    extreme_long_threshold
        Percentile (0-100) above which speculators are considered
        extreme-long → short the asset. Defaults to ``90``.
    extreme_short_threshold
        Percentile below which speculators are considered
        extreme-short → long the asset. Defaults to ``10``.
    cot_lag_days
        Trading-day lag applied to the positioning signal to respect
        the CFTC Friday-for-Tuesday publication delay. Defaults to
        ``3`` (Tue close → Fri publication + 1-day execution
        buffer).
    """

    name: str = "cot_speculator_position"
    family: str = "commodity"
    asset_classes: tuple[str, ...] = ("commodity",)
    paper_doi: str = "10.1111/0022-1082.00253"  # de Roon-Nijman-Veld 2000
    rebalance_frequency: str = "weekly"

    def __init__(
        self,
        *,
        front_to_position_map: Mapping[str, str] | None = None,
        percentile_lookback_weeks: int = 156,
        extreme_long_threshold: float = 90.0,
        extreme_short_threshold: float = 10.0,
        cot_lag_days: int = 3,
    ) -> None:
        if front_to_position_map is None:
            front_to_position_map = _DEFAULT_FRONT_TO_POSITION_MAP
        if not front_to_position_map:
            raise ValueError("front_to_position_map must be non-empty")
        for front, pos in front_to_position_map.items():
            if not front or not pos:
                raise ValueError(
                    f"front_to_position_map entries must be non-empty strings; "
                    f"got {front!r}: {pos!r}"
                )
            if front == pos:
                raise ValueError(
                    f"front_to_position_map entry maps {front!r} to itself; "
                    f"front and position columns must differ"
                )
        if percentile_lookback_weeks < 4:
            raise ValueError(
                f"percentile_lookback_weeks must be >= 4, got {percentile_lookback_weeks}"
            )
        if not (50.0 < extreme_long_threshold <= 100.0):
            raise ValueError(
                f"extreme_long_threshold must be in (50, 100], got {extreme_long_threshold}"
            )
        if not (0.0 <= extreme_short_threshold < 50.0):
            raise ValueError(
                f"extreme_short_threshold must be in [0, 50), got {extreme_short_threshold}"
            )
        if cot_lag_days < 0:
            raise ValueError(f"cot_lag_days must be non-negative, got {cot_lag_days}")

        self.front_to_position_map = dict(front_to_position_map)
        self.percentile_lookback_weeks = percentile_lookback_weeks
        self.extreme_long_threshold = extreme_long_threshold
        self.extreme_short_threshold = extreme_short_threshold
        self.cot_lag_days = cot_lag_days

    @property
    def front_symbols(self) -> list[str]:
        return list(self.front_to_position_map.keys())

    @property
    def position_columns(self) -> list[str]:
        return list(self.front_to_position_map.values())

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Return a contrarian COT signal DataFrame.

        Parameters
        ----------
        prices
            DataFrame with both price columns (the keys of
            ``front_to_position_map``) and positioning columns (the
            values). Index is daily. Price columns are
            continuous-contract closing prices; positioning columns
            are net-speculator-position normalised by open interest.

        Returns
        -------
        weights
            DataFrame indexed like ``prices``, columns are the front
            symbols (traded legs), values in ``{-1.0, 0.0, +1.0}``.
        """
        if not isinstance(prices, pd.DataFrame):
            raise TypeError(f"prices must be a DataFrame, got {type(prices).__name__}")
        if prices.empty:
            return pd.DataFrame(index=prices.index, columns=self.front_symbols, dtype=float)
        if not isinstance(prices.index, pd.DatetimeIndex):
            raise TypeError(f"prices must have a DatetimeIndex, got {type(prices.index).__name__}")
        required = set(self.front_symbols) | set(self.position_columns)
        missing = required - set(prices.columns)
        if missing:
            raise KeyError(
                f"prices is missing required columns: {sorted(missing)}; "
                f"got columns={list(prices.columns)}"
            )
        if (prices[list(required)] <= 0).any().any():
            raise ValueError("prices must be strictly positive")

        # 1. Apply the Friday-for-Tuesday COT lag to the positioning
        # series before computing the signal.
        positions = prices[self.position_columns].shift(self.cot_lag_days)

        # 2. Rolling percentile per commodity over the lookback window
        # (in trading days; weekly lookback × 5 trading days).
        lookback_days = self.percentile_lookback_weeks * 5
        weights = pd.DataFrame(0.0, index=prices.index, columns=self.front_symbols)

        for front, pos_col in self.front_to_position_map.items():
            series = positions[pos_col]
            # Rolling percentile rank: where in the historical
            # distribution is the current observation? rank(pct=True)
            # within the rolling window.
            rolling_rank = series.rolling(lookback_days, min_periods=lookback_days).apply(
                lambda window: 100.0 * (window.rank(pct=True).iloc[-1]),
                raw=False,
            )
            # Contrarian rule:
            #   percentile > 90 → speculators extreme long → SHORT
            #   percentile < 10 → speculators extreme short → LONG
            short_mask = rolling_rank > self.extreme_long_threshold
            long_mask = rolling_rank < self.extreme_short_threshold

            col = pd.Series(0.0, index=prices.index)
            col[short_mask & np.isfinite(rolling_rank)] = -1.0
            col[long_mask & np.isfinite(rolling_rank)] = +1.0
            weights[front] = col

        return weights
