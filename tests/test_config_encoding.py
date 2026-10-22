"""Cross-platform encoding contract for strategy config files.

This module is the Windows canary for the Session 2L CI expansion. Every
assertion here passes trivially on POSIX and is the point of the file only on
Windows, where Python 3.12 defaults ``open()`` to cp1252 rather than UTF-8.

Why it exists
-------------
Session 2L added a ``windows-latest`` leg to the test matrix. Auditing the
suite before enabling it found that ``discovery.load_config`` read
``config.yaml`` through a bare ``open()``, taking the platform default
encoding. Measured across the 112 strategy configs on 2026-10-21:

* 43 configs carry non-ASCII characters: section markers, Greek sigma,
  arrows, em dashes, multiplication signs, plus-minus and o-slash.
* 3 of those would raise ``UnicodeDecodeError`` under cp1252, because the
  UTF-8 byte 0x81 is undefined in that codepage:
  ``options/gamma_scalping_daily``, ``options/vix_3m_basis``,
  ``options/vix_term_structure_roll``.
* The other 40 would decode without error into mojibake, which is worse than
  a crash because nothing surfaces.
* 11 carry non-ASCII in a parsed *value* rather than only in a comment, so
  the corruption would reach strategy behaviour rather than stopping at
  discarded YAML comments.

The fix was to name the encoding at the read site. These tests pin that fix
so removing it is caught rather than rediscovered.

The same failure class produced the Session 2K-3.5 cache-sentinel bug: a
Windows-specific behaviour that no CI leg exercised. That is the argument for
the Windows leg existing at all.
"""

from __future__ import annotations

import pathlib

import pytest
from alphakit.bench.discovery import FAMILIES, discover_slugs, load_config

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _config_paths() -> list[pathlib.Path]:
    """Every strategy config.yaml in the workspace, sorted for stable ids."""
    return sorted(_REPO_ROOT.glob("packages/*/alphakit/strategies/*/*/config.yaml"))


def test_config_files_are_discoverable() -> None:
    """Guard the glob itself. A broken glob would make every parametrised
    test below vacuously pass, which is the classic way an encoding canary
    stops canarying."""
    paths = _config_paths()
    assert len(paths) >= 112, f"expected at least 112 configs, found {len(paths)}"


@pytest.mark.parametrize("path", _config_paths(), ids=lambda p: p.parent.name)
def test_config_is_valid_utf8(path: pathlib.Path) -> None:
    """Every config.yaml is UTF-8 on disk.

    This pins the on-disk encoding, which is what makes naming ``utf-8`` at
    the read site correct rather than merely convenient.
    """
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        pytest.fail(f"{path} is not valid UTF-8: {exc}")


@pytest.mark.parametrize("path", _config_paths(), ids=lambda p: p.parent.name)
def test_config_non_ascii_survives_load_config(path: pathlib.Path) -> None:
    """Non-ASCII in a parsed value round-trips through ``load_config``.

    This is the assertion that fails on Windows if the explicit
    ``encoding="utf-8"`` is ever removed from ``discovery.load_config``.
    Under cp1252 the loaded value would differ from the UTF-8 truth for the
    11 configs carrying non-ASCII in a value, and 3 configs would not load at
    all. On POSIX it passes either way, which is exactly why it has to be a
    Windows leg rather than a local check.
    """
    family = path.parents[1].name
    slug = path.parent.name
    if family not in FAMILIES:
        pytest.skip(f"{family} is not a registered family")

    truth = path.read_bytes().decode("utf-8")
    non_ascii_in_file = {c for c in truth if ord(c) > 127}
    if not non_ascii_in_file:
        pytest.skip("config is pure ASCII; nothing for the codec to corrupt")

    config = load_config(family, slug)

    def strings(obj: object) -> list[str]:
        if isinstance(obj, str):
            return [obj]
        if isinstance(obj, dict):
            out: list[str] = []
            for key, value in obj.items():
                out += strings(key) + strings(value)
            return out
        if isinstance(obj, list):
            out = []
            for item in obj:
                out += strings(item)
            return out
        return []

    for value in strings(config):
        for char in value:
            if ord(char) > 127:
                assert char in non_ascii_in_file, (
                    f"{slug}: loaded value contains {char!r} (U+{ord(char):04X}) which is "
                    f"absent from the UTF-8 decoding of the file. The reader used the wrong "
                    f"codec; check that discovery.load_config still passes encoding='utf-8'."
                )


def test_every_discovered_slug_loads() -> None:
    """``load_config`` succeeds for every discovered slug.

    On Windows without the encoding fix, three option strategies raise
    ``UnicodeDecodeError`` here rather than returning a config.
    """
    failures: list[str] = []
    for family in FAMILIES:
        for slug in discover_slugs(family):
            try:
                load_config(family, slug)
            except Exception as exc:  # report every failure, not just the first
                failures.append(f"{family}/{slug}: {type(exc).__name__}: {exc}")
    assert not failures, "load_config failed for:\n  " + "\n  ".join(failures)
