from __future__ import annotations

from .shared import *


def test_create_submission_minimal_package_filters_nested_supplementary_figures_when_canonical_catalog_exists(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "Figure 1",
                    "title": "Main figure",
                    "source_paths": ["paper/cohort_flow.json"],
                }
            ],
            "deferred_figures": [],
        },
    )

    write_text(paper_root / "cohort_flow.json", "{}\n")
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "title": "Main figure",
                    "export_paths": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
                }
            ],
            "deferred_figures": [
                {
                    "figure_id": "FS1",
                    "paper_role": "supplementary",
                    "display_role": "deferred_context_not_main_evidence",
                    "title": "Supplementary figure",
                    "export_paths": ["paper/figures/FS1_supp.pdf", "paper/figures/FS1_supp.png"],
                }
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    figure_ids = [entry["figure_id"] for entry in manifest["figures"]]
    assert figure_ids == ["F1"]
    assert "supplementary_material" not in manifest
