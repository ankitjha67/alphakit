"""Strategy discovery — find and instantiate strategies by slug or family.

Uses the filesystem layout convention:
  packages/alphakit-strategies-{family}/alphakit/strategies/{family}/{slug}/

Each strategy directory must contain:
  - __init__.py exporting the strategy class
  - config.yaml with universe, parameters, and rebalance frequency
  - strategy.py with the implementation
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml
from alphakit.core.protocols import StrategyProtocol

# Root of the monorepo packages directory
_PACKAGES_ROOT = Path(__file__).resolve().parents[4] / "packages"

FAMILIES = ("trend", "meanrev", "carry", "value", "volatility")


def _strategy_dirs() -> list[tuple[str, str, Path]]:
    """Yield (family, slug, path) for every strategy directory."""
    results: list[tuple[str, str, Path]] = []
    for family in FAMILIES:
        pkg_name = f"alphakit-strategies-{family}"
        family_dir = _PACKAGES_ROOT / pkg_name / "alphakit" / "strategies" / family
        if not family_dir.is_dir():
            continue
        for child in sorted(family_dir.iterdir()):
            if child.is_dir() and (child / "strategy.py").exists():
                results.append((family, child.name, child))
    return results


def discover_slugs(family: str | None = None) -> list[str]:
    """Return all strategy slugs, optionally filtered by family."""
    return [
        slug
        for fam, slug, _ in _strategy_dirs()
        if family is None or fam == family
    ]


def load_config(family: str, slug: str) -> dict[str, Any]:
    """Load a strategy's config.yaml as a dict."""
    pkg_name = f"alphakit-strategies-{family}"
    config_path = (
        _PACKAGES_ROOT / pkg_name / "alphakit" / "strategies" / family / slug / "config.yaml"
    )
    if not config_path.exists():
        raise FileNotFoundError(f"No config.yaml for {family}/{slug} at {config_path}")
    with open(config_path) as f:
        return dict(yaml.safe_load(f))


def instantiate(family: str, slug: str) -> StrategyProtocol:
    """Import and instantiate a strategy by family and slug.

    Imports from ``alphakit.strategies.{family}.{slug}`` and finds the
    first exported class that satisfies StrategyProtocol.
    """
    module_path = f"alphakit.strategies.{family}.{slug}"
    try:
        mod = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(f"Cannot import strategy {family}/{slug}: {exc}") from exc

    # Find the strategy class from __all__
    for name in getattr(mod, "__all__", []):
        cls = getattr(mod, name, None)
        if cls is not None and isinstance(cls, type):
            instance = cls()
            if isinstance(instance, StrategyProtocol):
                return instance
    raise RuntimeError(
        f"No StrategyProtocol-conforming class found in {module_path}.__all__"
    )


def find_strategy(slug: str) -> tuple[str, str]:
    """Find the family for a given slug. Returns (family, slug)."""
    for family, s, _ in _strategy_dirs():
        if s == slug:
            return (family, s)
    raise KeyError(f"Strategy slug '{slug}' not found in any family")


def benchmark_results_path(family: str, slug: str) -> Path:
    """Return the path to a strategy's benchmark_results.json."""
    pkg_name = f"alphakit-strategies-{family}"
    return (
        _PACKAGES_ROOT
        / pkg_name
        / "alphakit"
        / "strategies"
        / family
        / slug
        / "benchmark_results.json"
    )
