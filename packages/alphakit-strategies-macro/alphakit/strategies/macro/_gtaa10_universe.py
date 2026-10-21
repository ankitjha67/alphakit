"""Shared universe and validation bounds for the 10-asset covariance variants.

Package-private. Consumed by ``risk_parity_erc_10asset``,
``min_variance_gtaa_10asset``, and ``max_diversification_10asset``.

Follows the same pattern as ``_covariance.py``, established by the Session
2G amendment "covariance-primitive shared helper module": where several
strategies in this family must agree on an input, the agreement lives in
one package-private module rather than being duplicated per strategy or
imported across strategy directories.

Why one shared universe matters here
------------------------------------
The Session 2L comparison under test is **solver objective at fixed
universe**. Session 2K-4 found the three 3-asset covariance strategies
correlating at rho 0.980 to 0.993 because they shared one universe and one
covariance estimator and differed only in objective. Testing whether a
wider universe separates those objectives requires that the three variants
keep sharing exactly one universe. If the three drifted to different
ticker lists, any change in their pairwise correlation would be confounded
between "the objectives separate at higher N" and "the universes differ".
Centralising the tuple here makes that drift impossible by construction.

Substrate measurement (2026-10-21, yfinance, probe window 1990 to 2026,
via ``scripts/audit_etf_universe.py``):

    ticker  first observation  sleeve
    SPY     1993-01-29         US large-cap equity
    EFA     2001-08-27         developed ex-US equity
    TLT     2002-07-30         20+ year Treasuries
    IEF     2002-07-30         7-10 year Treasuries
    SHY     2002-07-30         1-3 year Treasuries
    LQD     2002-07-30         investment-grade corporate credit
    EEM     2003-04-14         emerging-market equity
    VNQ     2004-09-29         US real estate
    GLD     2004-11-18         gold
    DBC     2006-02-06         broad commodities

Every ticker returned data with zero non-positive bars, a maximum
consecutive missing run of 2 business days, and 195 missing business days
out of 5478 across 2005 to 2025 (9.75 per year, consistent with the US
market holiday calendar). The S2J-2.6 anomaly filter is therefore not
required for this universe.

DBC at 2006-02-06 is the binding constraint on the complete-rows
intersection, giving an effective panel start of 2006-02-06 across 5008
complete rows. The 3-asset incumbents (SPY/TLT/DBC) are bound by the same
ticker to the same date and the same row count, so the 10-asset variants
run on an identical window. That identity is what makes the cardinality
comparison controlled rather than confounded.
"""

from __future__ import annotations

# Ten tickers across six sleeves: US equity, developed ex-US equity,
# emerging equity, three Treasury durations, corporate credit, broad
# commodities, gold, real estate.
#
# Ordering is fixed and load-bearing for reproducibility: the solvers
# return weight vectors positionally, so a reordering would silently
# relabel every stored weight. Append, never reorder.
GTAA10_UNIVERSE: tuple[str, ...] = (
    "SPY",
    "TLT",
    "DBC",
    "IEF",
    "SHY",
    "LQD",
    "GLD",
    "VNQ",
    "EFA",
    "EEM",
)

# Below three assets a cross-sectional covariance construction degenerates:
# at N=2 ERC reduces to inverse-volatility weighting and at N=1 every
# objective returns the constant 1.0.
MIN_UNIVERSE_SIZE = 3

# Minimum sample for a stable covariance estimate, matching the 3-asset
# incumbents.
MIN_COV_WINDOW_DAYS = 60

VALID_SHRINKAGE: tuple[str, ...] = ("none", "ledoit_wolf", "constant")

__all__ = [
    "GTAA10_UNIVERSE",
    "MIN_COV_WINDOW_DAYS",
    "MIN_UNIVERSE_SIZE",
    "VALID_SHRINKAGE",
]
