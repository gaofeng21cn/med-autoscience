from __future__ import annotations

from med_autoscience.controllers.submission_minimal.package_builder import (
    create_submission_minimal_package,
)

from tests.submission_minimal_cases.shared import (
    annotations,
    _shared_base,
    importlib,
    io,
    json,
    os,
    Path,
    shutil,
    zipfile,
    zlib,
    pytest,
    PdfReader,
    dump_json,
    write_text,
    write_png,
    write_open_authority_snapshots,
    remove_authority_snapshots,
    real_submission_exports,
    lightweight_submission_exports,
    make_paper_workspace,
    make_current_draft_workspace,
    make_materialized_submission_source_workspace,
    make_authoritative_worktree_source_workspace,
    make_stage_native_current_body_workspace,
)


def test_create_submission_minimal_package_filters_nested_supplementary_figures_when_canonical_catalog_exists(
    tmp_path: Path,
) -> None:
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

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    figure_ids = [entry["figure_id"] for entry in manifest["figures"]]
    assert figure_ids == ["F1"]
    assert "supplementary_material" not in manifest
