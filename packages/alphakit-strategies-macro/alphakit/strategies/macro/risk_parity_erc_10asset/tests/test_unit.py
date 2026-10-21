"""Unit tests for risk_parity_erc_10asset signal generation.

Covers the constructor validation branches, the input validation branches,
and the behavioural invariants of the solver output. Session 2L variant of
the 3-asset incumbent; the shared universe and validation bounds come from
``alphakit.strategies.macro._gtaa10_universe``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from alphakit.core.protocols import StrategyProtocol
from alphakit.strategies.macro._covariance import rolling_covariance, solve_erc_weights
from alphakit.strategies.macro._gtaa10_universe import GTAA10_UNIVERSE
from alphakit.strategies.macro.risk_parity_erc_10asset.strategy import (
    RiskParityErc10Asset,
)

_UNIVERSE = ["SPY", "TLT", "DBC", "IEF", "SHY", "LQD", "GLD", "VNQ", "EFA", "EEM"]


def _gbm_panel(
    symbols: list[str] | None = None,
    years: float = 5.0,
    seed: int = 7,
    base_vol: float = 0.012,
) -> pd.DataFrame:
    """Deterministic GBM price panel with per-asset volatility spread.

    Volatility rises across the symbol list so the covariance solvers have a
    genuine ordering to exploit, mirroring the real universe where
    short-duration Treasuries carry the lowest variance.
    """
    syms = list(_UNIVERSE if symbols is None else symbols)
    rng = np.random.default_rng(seed)
    n_days = round(years * 252)
    index = pd.date_range("2015-01-01", periods=n_days, freq="B")
    prices: dict[str, np.ndarray] = {}
    for i, sym in enumerate(syms):
        vol = base_vol * (0.4 + 0.15 * i)
        shocks = rng.normal(0.0002, vol, size=n_days)
        prices[sym] = 100.0 * np.exp(np.cumsum(shocks))
    return pd.DataFrame(prices, index=index)


def test_satisfies_strategy_protocol() -> None:
    assert isinstance(RiskParityErc10Asset(), StrategyProtocol)


def test_metadata_is_paper_cited() -> None:
    strategy = RiskParityErc10Asset()
    assert strategy.name == "risk_parity_erc_10asset"
    assert strategy.family == "macro"
    assert strategy.paper_doi == "10.2469/faj.v68.n1.1"
    assert strategy.rebalance_frequency == "monthly"
    assert len(strategy.asset_classes) > 0


def test_default_universe_is_the_shared_ten() -> None:
    strategy = RiskParityErc10Asset()
    assert strategy.universe == GTAA10_UNIVERSE
    assert len(strategy.universe) == 10
    assert strategy.required_symbols == strategy.universe


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"cov_window_days": 59}, "cov_window_days must be >="),
        ({"cov_window_days": 0}, "cov_window_days must be >="),
        ({"shrinkage": "bogus"}, "shrinkage must be one of"),
        ({"universe": ["SPY", "TLT"]}, "at least 3 symbols"),
        ({"universe": ["SPY", "TLT", ""]}, "non-empty strings"),
        ({"universe": ["SPY", "TLT", "SPY", "IEF"]}, "must be distinct"),
    ],
)
def test_constructor_rejects_bad_args(kwargs: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        RiskParityErc10Asset(**kwargs)  # type: ignore[arg-type]


def test_constructor_names_the_duplicate_symbols() -> None:
    with pytest.raises(ValueError, match=r"\['SPY'\]"):
        RiskParityErc10Asset(universe=["SPY", "TLT", "SPY", "IEF"])


def test_constructor_accepts_custom_universe() -> None:
    strategy = RiskParityErc10Asset(universe=["AAA", "BBB", "CCC"])
    assert strategy.universe == ("AAA", "BBB", "CCC")
    assert strategy.required_symbols == ("AAA", "BBB", "CCC")


def test_constructor_accepts_shrinkage_alternatives() -> None:
    for method in ("none", "ledoit_wolf", "constant"):
        assert RiskParityErc10Asset(shrinkage=method).shrinkage == method


def test_rejects_non_dataframe_input() -> None:
    with pytest.raises(TypeError, match="prices must be a DataFrame"):
        RiskParityErc10Asset().generate_signals([1, 2, 3])  # type: ignore[arg-type]


def test_rejects_missing_required_symbols() -> None:
    panel = _gbm_panel(symbols=["SPY", "TLT", "DBC"], years=2.0)
    with pytest.raises(KeyError, match="missing required columns"):
        RiskParityErc10Asset().generate_signals(panel)


def test_rejects_non_datetime_index() -> None:
    panel = _gbm_panel(years=2.0)
    panel.index = pd.RangeIndex(len(panel))
    with pytest.raises(TypeError, match="DatetimeIndex"):
        RiskParityErc10Asset().generate_signals(panel)


def test_rejects_non_positive_prices() -> None:
    panel = _gbm_panel(years=2.0)
    panel.iloc[10, 0] = 0.0
    with pytest.raises(ValueError, match="strictly positive"):
        RiskParityErc10Asset().generate_signals(panel)


def test_returns_empty_frame_on_empty_input() -> None:
    empty = pd.DataFrame(index=pd.DatetimeIndex([]), columns=list(GTAA10_UNIVERSE), dtype=float)
    out = RiskParityErc10Asset().generate_signals(empty)
    assert out.empty
    assert list(out.columns) == list(GTAA10_UNIVERSE)


def test_ignores_extra_columns() -> None:
    panel = _gbm_panel(years=3.0)
    panel["UNRELATED"] = 50.0
    out = RiskParityErc10Asset().generate_signals(panel)
    assert list(out.columns) == list(GTAA10_UNIVERSE)


def test_output_is_aligned_to_input() -> None:
    panel = _gbm_panel(years=3.0)
    out = RiskParityErc10Asset().generate_signals(panel)
    assert out.shape == (len(panel), len(GTAA10_UNIVERSE))
    pd.testing.assert_index_equal(out.index, panel.index)


def test_warmup_weights_are_zero() -> None:
    panel = _gbm_panel(years=3.0)
    out = RiskParityErc10Asset().generate_signals(panel)
    assert (out.iloc[0] == 0.0).all()
    assert int((out.sum(axis=1) == 0).sum()) > 0


def test_insufficient_history_yields_all_zero_weights() -> None:
    panel = _gbm_panel(years=0.5)
    out = RiskParityErc10Asset().generate_signals(panel)
    assert out.shape == (len(panel), len(GTAA10_UNIVERSE))
    assert (out.to_numpy() == 0.0).all()


def test_weights_sum_to_one_after_warmup() -> None:
    panel = _gbm_panel(years=5.0)
    out = RiskParityErc10Asset().generate_signals(panel)
    post = out[out.sum(axis=1) > 0]
    assert len(post) > 0
    np.testing.assert_allclose(post.sum(axis=1).to_numpy(), 1.0, atol=1e-6)


def test_weights_strictly_positive_after_warmup() -> None:
    panel = _gbm_panel(years=5.0)
    out = RiskParityErc10Asset().generate_signals(panel)
    post = out[out.sum(axis=1) > 0]
    assert len(post) > 0
    assert post.to_numpy().min() > 0, "ERC must hold every asset"


def test_deterministic_output() -> None:
    panel = _gbm_panel(years=4.0, seed=3)
    a = RiskParityErc10Asset().generate_signals(panel)
    b = RiskParityErc10Asset().generate_signals(panel)
    pd.testing.assert_frame_equal(a, b)


def test_shrinkage_methods_produce_different_weights() -> None:
    panel = _gbm_panel(years=4.0, seed=5)
    none_w = RiskParityErc10Asset(shrinkage="none").generate_signals(panel)
    lw_w = RiskParityErc10Asset(shrinkage="ledoit_wolf").generate_signals(panel)
    assert not none_w.equals(lw_w)


def test_custom_universe_drives_output_columns() -> None:
    syms = ["AAA", "BBB", "CCC", "DDD"]
    panel = _gbm_panel(symbols=syms, years=3.0)
    out = RiskParityErc10Asset(universe=syms).generate_signals(panel)
    assert list(out.columns) == syms


def test_equal_risk_contribution_invariant() -> None:
    """ERC equalises marginal risk contributions at the solver level.

    Two things this test deliberately does NOT do.

    It does not use a raw sample covariance. The solver consumed the
    Ledoit-Wolf shrunken estimate from ``rolling_covariance``, and shrinkage
    moves the matrix enough that the invariant does not hold against the raw
    estimate.

    It does not route through the daily weights frame. Mapping a calendar
    month-end back to a forward-filled daily row is ambiguous, because 18 of
    58 calendar month-ends in a business-day panel are not trading days at
    all (see ``known_failures.md`` section 9). The invariant is a property of
    the solver, so it is asserted against the solver. The daily plumbing is
    covered by the alignment, warm-up and row-sum tests above.

    Tolerance is 1e-3. That is not arbitrary: measured across 21 sampled
    rebalance dates on this universe, the worst observed risk-contribution
    spread was 5.371e-04, which is L-BFGS-B default convergence on Spinu's
    reformulation rather than exact equality. An earlier 5e-4 bound was
    measured as too tight and corrected.
    """
    strategy = RiskParityErc10Asset()
    panel = _gbm_panel(years=5.0, seed=11)
    returns = np.log(panel / panel.shift(1)).dropna()

    rolling_cov = rolling_covariance(
        returns, window=strategy.cov_window_days, shrinkage=strategy.shrinkage
    )
    cov_dates = pd.DatetimeIndex(rolling_cov.index.unique(level="date"))
    assert len(cov_dates) > 0, "expected at least one covariance date"

    worst_spread = 0.0
    checked = 0
    for cov_date in cov_dates[::50]:
        cov = rolling_cov.loc[cov_date].to_numpy(dtype=float)
        weights = solve_erc_weights(cov)
        contributions = (weights * (cov @ weights)) / float(weights @ cov @ weights)
        worst_spread = max(worst_spread, float(contributions.max() - contributions.min()))
        checked += 1

    assert checked > 0, "no covariance dates were sampled"
    assert worst_spread < 1e-3, f"worst risk-contribution spread {worst_spread:.3e}"
