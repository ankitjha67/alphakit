"""Tests for alphakit.bench.discovery."""

from __future__ import annotations

from pathlib import Path

import pytest
from alphakit.bench.discovery import (
    FAMILIES,
    benchmark_results_path,
    discover_slugs,
    find_strategy,
    instantiate,
    load_config,
)
from alphakit.core.protocols import StrategyProtocol


class TestDiscoverSlugs:
    def test_all_families(self) -> None:
        slugs = discover_slugs()
        # 60 Phase 1 (trend, meanrev, carry, value, volatility) +
        # 13 Phase 2 Session 2D rates +
        # 10 Phase 2 Session 2E commodity +
        # 15 Phase 2 Session 2F options +
        # 11 Phase 2 Session 2G macro +
        # 3 Phase 2 Session 2L macro 10-asset covariance variants = 112.
        assert len(slugs) == 112

    def test_rates_family(self) -> None:
        slugs = discover_slugs("rates")
        assert len(slugs) == 13

    def test_trend_family(self) -> None:
        slugs = discover_slugs("trend")
        assert len(slugs) == 15
        assert "tsmom_12_1" in slugs

    def test_meanrev_family(self) -> None:
        slugs = discover_slugs("meanrev")
        assert len(slugs) == 15

    def test_carry_family(self) -> None:
        slugs = discover_slugs("carry")
        assert len(slugs) == 10

    def test_value_family(self) -> None:
        slugs = discover_slugs("value")
        assert len(slugs) == 10

    def test_volatility_family(self) -> None:
        slugs = discover_slugs("volatility")
        assert len(slugs) == 10

    def test_commodity_family(self) -> None:
        slugs = discover_slugs("commodity")
        assert len(slugs) == 10

    def test_options_family(self) -> None:
        slugs = discover_slugs("options")
        assert len(slugs) == 15
        assert "covered_call_systematic" in slugs
        assert "vix_term_structure_roll" in slugs

    def test_macro_family(self) -> None:
        assert "macro" in FAMILIES
        slugs = discover_slugs("macro")
        # 11 from Session 2G + 3 Session 2L 10-asset covariance variants.
        # The 2L variants are additions; the 3-asset originals are preserved
        # as the documented small-N convergence case from the Session 2K-4
        # dedup-bar breach.
        assert len(slugs) == 14
        expected = {
            "permanent_portfolio",
            "gtaa_cross_asset_momentum",
            "vigilant_asset_allocation_5",
            "risk_parity_erc_3asset",
            "min_variance_gtaa",
            "max_diversification",
            "risk_parity_erc_10asset",
            "min_variance_gtaa_10asset",
            "max_diversification_10asset",
            "recession_probability_rotation",
            "growth_inflation_regime_rotation",
            "yield_curve_regime_allocation",
            "fed_policy_tilt",
            "inflation_regime_allocation",
        }
        assert set(slugs) == expected

    def test_nonexistent_family(self) -> None:
        slugs = discover_slugs("nonexistent")
        assert slugs == []


class TestFindStrategy:
    def test_known_slug(self) -> None:
        family, slug = find_strategy("tsmom_12_1")
        assert family == "trend"
        assert slug == "tsmom_12_1"

    def test_unknown_slug(self) -> None:
        with pytest.raises(KeyError, match="not found"):
            find_strategy("nonexistent_strategy")


class TestLoadConfig:
    def test_loads_yaml(self) -> None:
        config = load_config("trend", "tsmom_12_1")
        assert config["strategy"] == "tsmom_12_1"
        assert config["family"] == "trend"
        assert "universe" in config

    def test_missing_config(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config("trend", "nonexistent")


class TestInstantiate:
    def test_instantiates_strategy(self) -> None:
        strategy = instantiate("trend", "tsmom_12_1")
        assert isinstance(strategy, StrategyProtocol)
        assert strategy.name == "tsmom_12_1"

    def test_invalid_import(self) -> None:
        with pytest.raises(ImportError):
            instantiate("trend", "nonexistent")


class TestBenchmarkResultsPath:
    def test_returns_path(self) -> None:
        path = benchmark_results_path("trend", "tsmom_12_1")
        assert isinstance(path, Path)
        assert path.name == "benchmark_results.json"
        assert "tsmom_12_1" in str(path)
