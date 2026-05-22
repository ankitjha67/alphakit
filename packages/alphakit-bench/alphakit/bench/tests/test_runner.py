"""Tests for alphakit.bench.runner."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from alphakit.bench import discovery
from alphakit.bench.runner import BenchmarkRunner


@pytest.fixture
def runner() -> BenchmarkRunner:
    return BenchmarkRunner(
        commission_bps=5.0,
        data_start="2005-01-01",
        in_sample_end="2019-12-31",
        out_of_sample_end="2025-12-31",
    )


class TestBenchmarkRunner:
    def test_run_single_produces_valid_result(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        assert result["slug"] == "tsmom_12_1"
        assert result["status"] == "populated"
        assert result["engine"] == "vectorbt"

    def test_result_has_all_metric_keys(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        metrics = result["metrics"]
        for key in (
            "sharpe",
            "sortino",
            "calmar",
            "max_drawdown",
            "annualized_return",
            "annualized_vol",
            "turnover_annual",
            "capacity_usd_bn",
        ):
            assert key in metrics
            assert isinstance(metrics[key], float)
            assert np.isfinite(metrics[key])

    def test_result_has_regime_performance(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        regime = result["regime_performance"]
        for key in ("bull_market_sharpe", "bear_market_sharpe", "sideways_sharpe"):
            assert key in regime
            assert isinstance(regime[key], float)

    def test_result_has_metadata(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        assert result["data_start"] == "2005-01-01"
        assert result["in_sample_end"] == "2019-12-31"
        assert result["out_of_sample_end"] == "2025-12-31"
        assert result["transaction_costs_assumed_bps"] == 5.0
        assert isinstance(result["universe"], list)

    def test_result_is_json_serializable(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("tsmom_12_1")
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        assert deserialized["slug"] == "tsmom_12_1"

    def test_write_benchmark(
        self,
        runner: BenchmarkRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Redirect the resolved benchmark path into tmp_path so the write
        # never touches the tracked in-repo benchmark_results.json. (The
        # runner resolves the target via discovery.benchmark_results_path.)
        target = tmp_path / "benchmark_results.json"
        monkeypatch.setattr(discovery, "benchmark_results_path", lambda family, slug: target)

        result = runner.run_single("tsmom_12_1")
        result["slug"] = "tsmom_12_1"

        path = runner.write_benchmark("tsmom_12_1", result, family="trend")
        # Guard: the write must land at the redirected target, not the repo.
        assert path == target
        assert path.exists()
        with open(path) as f:
            written = json.load(f)
        assert written["slug"] == "tsmom_12_1"
        assert written["status"] == "populated"

    def test_write_benchmark_does_not_mutate_repo_file(
        self,
        runner: BenchmarkRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Regression guard for the working-tree-pollution bug: with the
        # benchmark path redirected, write_benchmark must leave the tracked
        # in-repo file byte-for-byte unchanged.
        real_path = discovery.benchmark_results_path("trend", "tsmom_12_1")
        before = real_path.read_bytes()

        target = tmp_path / "benchmark_results.json"
        monkeypatch.setattr(discovery, "benchmark_results_path", lambda family, slug: target)

        result = runner.run_single("tsmom_12_1")
        runner.write_benchmark("tsmom_12_1", result, family="trend")

        assert target.exists(), "redirected write should land in tmp_path"
        assert real_path.read_bytes() == before, "tracked repo file must be untouched"

    def test_auto_detect_family(self, runner: BenchmarkRunner) -> None:
        result = runner.run_single("vol_targeting")
        assert result["slug"] == "vol_targeting"

    def test_deterministic_results(self, runner: BenchmarkRunner) -> None:
        a = runner.run_single("tsmom_12_1")
        b = runner.run_single("tsmom_12_1")
        assert a["metrics"]["sharpe"] == b["metrics"]["sharpe"]
