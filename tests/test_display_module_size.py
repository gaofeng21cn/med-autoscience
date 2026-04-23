from __future__ import annotations

from pathlib import Path


_MAX_LINES = 1000
_TARGETS = (
    Path("src/med_autoscience/display_schema_contract.py"),
    Path("tests/test_display_schema_contract.py"),
    Path("tests/test_display_layout_qc.py"),
    Path("tests/test_display_surface_materialization.py"),
    Path("tests/display_schema_contract_cases/chunk_02.py"),
    Path("tests/display_schema_contract_cases/chunk_02_data_geometry.py"),
    Path("tests/display_schema_contract_cases/chunk_02_omics_matrix.py"),
    Path("tests/display_schema_contract_cases/chunk_02_effects_and_explanations.py"),
    Path("tests/display_schema_contract_cases/chunk_02_clinical_and_shells.py"),
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
