from __future__ import annotations

from pathlib import Path


_MAX_LINES = 1000
_TARGETS = (
    Path("src/med_autoscience/display_schema_contract.py"),
    Path("tests/test_display_layout_qc.py"),
    Path("tests/test_display_surface_materialization.py"),
    Path("tests/display_schema_contract_cases/test_data_geometry_input_shapes.py"),
    Path("tests/display_schema_contract_cases/test_matrix_and_omics_input_shapes.py"),
    Path("tests/display_schema_contract_cases/test_effect_and_explanation_input_shapes.py"),
    Path("tests/display_schema_contract_cases/test_clinical_and_publication_input_shapes.py"),
    Path("tests/medical_publication_surface_cases/shared_base.py"),
    Path("tests/medical_publication_surface_cases/quest_factory/__init__.py"),
    Path("tests/medical_publication_surface_cases/test_figure_narrative_and_renderer_contracts.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface/shared_base.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface/asset_scans.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface/catalog_checks.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface/manuscript_checks.py"),
    Path("src/med_autoscience/controllers/medical_publication_surface/reporting.py"),
    Path("src/med_autoscience/controllers/submission_minimal.py"),
    Path("src/med_autoscience/controllers/submission_minimal/shared_base.py"),
    Path("src/med_autoscience/controllers/submission_minimal/authority.py"),
    Path("src/med_autoscience/controllers/submission_minimal/markdown_surface.py"),
    Path("src/med_autoscience/controllers/submission_minimal/profile_builders.py"),
    Path("src/med_autoscience/controllers/submission_minimal/package_builder.py"),
    Path("tests/submission_minimal_cases/shared_base.py"),
    Path("tests/submission_minimal_cases/package_core_and_authority_cases/test_authority_and_sources.py"),
    Path("tests/submission_minimal_cases/package_core_and_authority_cases/test_core_materialization.py"),
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
