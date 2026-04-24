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
    Path("tests/test_medical_publication_surface.py"),
    Path("tests/medical_publication_surface_cases/shared_base.py"),
    Path("tests/medical_publication_surface_cases/quest_factory.py"),
    Path("tests/medical_publication_surface_cases/chunk_01.py"),
    Path("tests/medical_publication_surface_cases/chunk_02.py"),
    Path("tests/medical_publication_surface_cases/chunk_03.py"),
    Path("tests/medical_publication_surface_cases/chunk_04.py"),
    Path("tests/medical_publication_surface_cases/chunk_05.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface_parts/shared_base.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface_parts/asset_scans.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface_parts/catalog_checks.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface_parts/manuscript_checks.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface_parts/reporting.py"),
    Path("src/med_autoscience/controllers/submission_minimal.py"),
    Path("src/med_autoscience/controllers/submission_minimal_parts/shared_base.py"),
    Path("src/med_autoscience/controllers/submission_minimal_parts/authority.py"),
    Path("src/med_autoscience/controllers/submission_minimal_parts/markdown_surface.py"),
    Path("src/med_autoscience/controllers/submission_minimal_parts/profile_builders.py"),
    Path("src/med_autoscience/controllers/submission_minimal_parts/package_builder.py"),
    Path("tests/test_submission_minimal.py"),
    Path("tests/submission_minimal_cases/shared_base.py"),
    Path("tests/submission_minimal_cases/chunk_01.py"),
    Path("tests/submission_minimal_cases/chunk_02.py"),
    Path("tests/submission_minimal_cases/chunk_03.py"),
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
