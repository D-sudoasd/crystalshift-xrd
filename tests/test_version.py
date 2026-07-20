from __future__ import annotations

import tomllib
from pathlib import Path

from orthoxrd import __version__
from orthoxrd.export_schema import EXPORT_SCHEMA_VERSION


def test_package_and_export_versions_are_aligned() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert __version__ == "2.3.0"
    assert pyproject["project"]["version"] == __version__
    assert EXPORT_SCHEMA_VERSION == "2.4"
