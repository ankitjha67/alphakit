"""Unit tests for max_diversification_10asset signal generation.

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
from alphakit.strategies.macro._gtaa10_universe import GTAA10_UNIVERSE
from alphakit.strategies.macro.max_diversification_10asset.strategy import (
    MaxDiversification10Asset,
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
    assert isinstance(MaxDiversification10Asset(), StrategyProtocol)


def test_metadata_is_paper_cited() -> None:
    strategy = MaxDiversification10Asset()
    assert strategy.name == "max_diversification_10asset"
    assert strategy.family == "macro"
    assert strategy.paper_doi == "10.2139/ssrn.1895459"
    assert strategy.rebalance_frequency == "monthly"
    assert len(strategy.asset_classes) > 0


def test_default_universe_is_the_shared_ten() -> None:
    strategy = MaxDiversification10Asset()
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
        ({"max_weight": 0.0}, "max_weight must be in"),
        ({"max_weight": 1.5}, "max_weight must be in"),
        ({"max_weight": -0.2}, "max_weight must be in"),
    ],
)
def test_constructor_rejects_bad_args(kwargs: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        MaxDiversification10Asset(**kwargs)  # type: ignore[arg-type]


def test_constructor_names_the_duplicate_symbols() -> None:
    with pytest.raises(ValueError, match=r"\['SPY'\]"):
        MaxDiversification10Asset(universe=["SPY", "TLT", "SPY", "IEF"])


def test_constructor_accepts_custom_universe() -> None:
    strategy = MaxDiversification10Asset(universe=["AAA", "BBB", "CCC"])
    assert strategy.universe == ("AAA", "BBB", "CCC")
    assert strategy.required_symbols == ("AAA", "BBB", "CCC")


def test_constructor_accepts_shrinkage_alternatives() -> None:
    for method in ("none", "ledoit_wolf", "constant"):
        assert MaxDiversification10Asset(shrinkage=method).shrinkage == method


def test_rejects_non_dataframe_input() -> None:
    with pytest.raises(TypeError, match="prices must be a DataFrame"):
        MaxDiversification10Asset().generate_signals([1, 2, 3])  # type: ignore[arg-type]


def test_rejects_missing_required_symbols() -> None:
    panel = _gbm_panel(symbols=["SPY", "TLT", "DBC"], years=2.0)
    with pytest.raises(KeyError, match="missing required columns"):
        MaxDiversification10Asset().generate_signals(panel)


def test_rejects_non_datetime_index() -> None:
    panel = _gbm_panel(years=2.0)
    panel.index = pd.RangeIndex(len(panel))
    with pytest.raises(TypeError, match="DatetimeIndex"):
        MaxDiversification10Asset().generate_signals(panel)


def test_rejects_non_positive_prices() -> None:
    panel = _gbm_panel(years=2.0)
    panel.iloc[10, 0] = 0.0
    with pytest.raises(ValueError, match="strictly positive"):
        MaxDiversification10Asset().generate_signals(panel)


def test_returns_empty_frame_on_empty_input() -> None:
    empty = pd.DataFrame(index=pd.DatetimeIndex([]), columns=list(GTAA10_UNIVERSE), dtype=float)
    out = MaxDiversification10Asset().generate_signals(empty)
    assert out.empty
    assert list(out.columns) == list(GTAA10_UNIVERSE)


def test_ignores_extra_columns() -> None:
    panel = _gbm_panel(years=3.0)
    panel["UNRELATED"] = 50.0
    out = MaxDiversification10Asset().generate_signals(panel)
    assert list(out.columns) == list(GTAA10_UNIVERSE)


def test_output_is_aligned_to_input() -> None:
    panel = _gbm_panel(years=3.0)
    out = MaxDiversification10Asset().generate_signals(panel)
    assert out.shape == (len(panel), len(GTAA10_UNIVERSE))
    pd.testing.assert_index_equal(out.index, panel.index)


def test_warmup_weights_are_zero() -> None:
    panel = _gbm_panel(years=3.0)
    out = MaxDiversification10Asset().generate_signals(panel)
    assert (out.iloc[0] == 0.0).all()
    assert int((out.sum(axis=1) == 0).sum()) > 0


def test_insufficient_history_yields_all_zero_weights() -> None:
    panel = _gbm_panel(years=0.5)
    out = MaxDiversification10Asset().generate_signals(panel)
    assert out.shape == (len(panel), len(GTAA10_UNIVERSE))
    assert (out.to_numpy() == 0.0).all()


def test_weights_sum_to_one_after_warmup() -> None:
    panel = _gbm_panel(years=5.0)
    out = MaxDiversification10Asset().generate_signals(panel)
    post = out[out.sum(axis=1) > 0]
    assert len(post) > 0
    np.testing.assert_allclose(post.sum(axis=1).to_numpy(), 1.0, atol=1e-6)


def test_weights_non_negative_after_warmup() -> None:
    panel = _gbm_panel(years=5.0)
    out = MaxDiversification10Asset().generate_signals(panel)
    post = out[out.sum(axis=1) > 0]
    assert len(post) > 0
    assert post.to_numpy().min() >= -1e-12, "long-only weights must be non-negative"


def test_deterministic_output() -> None:
    panel = _gbm_panel(years=4.0, seed=3)
    a = MaxDiversification10Asset().generate_signals(panel)
    b = MaxDiversification10Asset().generate_signals(panel)
    pd.testing.assert_frame_equal(a, b)


def test_shrinkage_methods_produce_different_weights() -> None:
    panel = _gbm_panel(years=4.0, seed=5)
    none_w = MaxDiversification10Asset(shrinkage="none").generate_signals(panel)
    lw_w = MaxDiversification10Asset(shrinkage="ledoit_wolf").generate_signals(panel)
    assert not none_w.equals(lw_w)


def test_custom_universe_drives_output_columns() -> None:
    syms = ["AAA", "BBB", "CCC", "DDD"]
    panel = _gbm_panel(symbols=syms, years=3.0)
    out = MaxDiversification10Asset(universe=syms).generate_signals(panel)
    assert list(out.columns) == syms


def test_constructor_rejects_infeasible_max_weight() -> None:
    """A cap below 1/N cannot satisfy the budget constraint."""
    with pytest.raises(ValueError, match="infeasible"):
        MaxDiversification10Asset(max_weight=0.05)


def test_constructor_accepts_feasible_max_weight() -> None:
    strategy = MaxDiversification10Asset(max_weight=0.25)
    assert strategy.max_weight == 0.25


def test_binding_cap_limits_every_weight() -> None:
    panel = _gbm_panel(years=4.0, seed=19)
    weights = MaxDiversification10Asset(max_weight=0.30).generate_signals(panel)
    post = weights[weights.sum(axis=1) > 0]
    assert len(post) > 0
    assert post.to_numpy().max() <= 0.30 + 1e-6
