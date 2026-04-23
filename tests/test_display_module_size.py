from __future__ import annotations

from pathlib import Path


_MAX_LINES = 1000
_TARGETS = (
    Path("src/med_autoscience/display_schema_contract.py"),
    Path("tests/test_display_schema_contract.py"),
    Path("tests/test_display_layout_qc.py"),
    Path("tests/test_display_surface_materialization.py"),
)


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def test_display_module_files_stay_within_size_budget() -> None:
    oversized = [
        (str(path), _count_lines(path))
        for path in _TARGETS
        if path.exists() and _count_lines(path) > _MAX_LINES
    ]

    assert oversized == []
