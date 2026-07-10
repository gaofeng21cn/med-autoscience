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

import med_autoscience.controllers.submission_minimal.package_builder as package_builder
from med_autoscience.controllers.submission_minimal.authority import (
    describe_submission_minimal_authority,
)
from med_autoscience.controllers.submission_minimal.package_builder import (
    create_submission_minimal_package,
)

pytestmark = pytest.mark.submission_heavy


def test_create_submission_minimal_package_creates_output_directory_and_copies_pdf(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert submission_root.exists()
    assert (submission_root / "paper.pdf").exists()
    assert manifest["output_root"] == "paper/submission_minimal"


def test_create_submission_minimal_package_uses_delivery_layout_v2(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert manifest["delivery_layout"]["layout_version"] == "submission-package.v2"
    assert manifest["delivery_layout"]["audit_root"] == "paper/submission_minimal/audit"
    assert manifest["delivery_layout"]["reproducibility_root"] == "paper/submission_minimal/reproducibility"
    assert not (submission_root / "submission_manifest.json").exists()
    assert not (submission_root / "evidence_ledger.json").exists()
    assert (submission_root / "audit" / "submission_manifest.json").exists()
    assert (submission_root / "audit" / "evidence_ledger.json").exists()
    assert (submission_root / "reproducibility" / "source_signature.json").exists()
    assert (submission_root / "reproducibility" / "source_relative_paths.json").exists()


def test_create_submission_minimal_package_route_gate_blocks_materialization(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    shutil.rmtree(paper_root / "submission_minimal", ignore_errors=True)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "dispatch_gate": {
                    "state": "blocked",
                    "dispatch_allowed": False,
                    "blocking_reasons": ["execution_owner_guard.supervisor_only"],
                },
                "route_authorization": {
                    "authorized": False,
                    "paper_write_allowed": False,
                    "bundle_build_allowed": False,
                    "runtime_recovery_allowed": True,
                },
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
            }
        },
    )

    assert result["status"] == "authority_route_blocked"
    assert result["authority_route_gate"]["allowed"] is False
    assert "paper_write_allowed_false" in result["authority_route_gate"]["blocking_reasons"]
    assert not (paper_root / "submission_minimal").exists()


def test_create_submission_minimal_package_materializes_audit_package_when_authority_snapshot_missing(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    shutil.rmtree(paper_root / "submission_minimal", ignore_errors=True)
    shutil.rmtree(paper_root.parent / "artifacts", ignore_errors=True)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "audit" / "submission_manifest.json"
    assert result["authority_route_gate"]["allowed"] is False
    assert result["submission_materialization_status"]["can_submit"] is False
    assert result["submission_materialization_status"]["quality_gate_status"] == "blocked"
    assert result["submission_materialization_status"]["known_blockers"] == [
        "authority_snapshot_missing"
    ]
    assert (submission_root / "paper.pdf").exists()
    assert manifest_path.exists()


def test_create_submission_minimal_package_materializes_audit_package_for_submission_human_gate(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "control_state": "ready",
                "canonical_next_action": "await_submission_authority_or_human_gate_closeout",
                "dispatch_gate": {
                    "state": "blocked",
                    "dispatch_allowed": False,
                    "blocking_reasons": ["submission_authority_or_human_gate_closeout_required"],
                },
                "route_authorization": {
                    "authorized": True,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": False,
                    "runtime_recovery_allowed": True,
                },
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
            }
        },
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "audit" / "submission_manifest.json"
    assert result["authority_route_gate"]["allowed"] is False
    assert result["submission_materialization_status"]["can_submit"] is False
    assert result["submission_materialization_status"]["quality_gate_status"] == "blocked"
    assert result["submission_materialization_status"]["known_blockers"] == [
        "dispatch_gate_blocked",
        "submission_authority_or_human_gate_closeout_required",
    ]
    assert (submission_root / "paper.pdf").exists()
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["submission_materialization_status"] == result["submission_materialization_status"]


def test_create_submission_minimal_package_writes_manifest_and_docx_path(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "audit" / "submission_manifest.json"
    docx_path = submission_root / "manuscript.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["publication_profile"] == "general_medical_journal"
    assert manifest_payload["citation_style"] == "AMA"
    assert manifest_payload["output_root"] == "paper/submission_minimal"
    assert manifest_payload["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"
    assert manifest_payload["manuscript"]["docx_path"] == "paper/submission_minimal/manuscript.docx"
    assert manifest_payload["manuscript"]["pdf_rendering"] == {
        "profile_id": "general_medical_reader_pdf_v1",
        "renderer_family": "pandoc_xelatex",
        "pdf_engine": "xelatex",
        "template_family": "mas_professional_medical_article",
        "layout_role": "human_reading_default",
        "journal_specific": False,
    }
    assert manifest_payload["naming_map"]["figures"] == {
        "F1": "Figure1",
        "FS1": "SupplementaryFigureS1",
    }
    assert manifest_payload["naming_map"]["tables"] == {
        "T1": "Table1",
    }
    assert manifest_payload["figures"][0]["source_paths"] == [
        "paper/figures/F1_main.pdf",
        "paper/figures/F1_main.png",
    ]
    assert manifest_payload["tables"][0]["source_paths"] == [
        "paper/tables/T1_summary.csv",
        "paper/tables/T1_summary.md",
    ]
    assert manifest_payload == manifest


def test_create_submission_minimal_package_preserves_existing_package_when_materialization_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_root = make_paper_workspace(tmp_path)

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "audit" / "submission_manifest.json"
    pdf_path = submission_root / "paper.pdf"
    docx_path = submission_root / "manuscript.docx"

    old_manifest = '{"sentinel":"old-manifest"}\n'
    old_pdf = b"%PDF-1.4\n%old-pdf\n"
    old_docx = b"old-docx"
    manifest_path.write_text(old_manifest, encoding="utf-8")
    pdf_path.write_bytes(old_pdf)
    docx_path.write_bytes(old_docx)

    original_export_pdf = package_builder.export_pdf

    def failing_export_pdf(*args, **kwargs):
        original_export_pdf(*args, **kwargs)
        raise RuntimeError("simulated pdf export failure")

    monkeypatch.setattr(package_builder, "export_pdf", failing_export_pdf)

    with pytest.raises(RuntimeError, match="simulated pdf export failure"):
        create_submission_minimal_package(
            paper_root=paper_root,
            publication_profile="general_medical_journal",
        )

    assert submission_root.exists()
    assert manifest_path.read_text(encoding="utf-8") == old_manifest
    assert pdf_path.read_bytes() == old_pdf
    assert docx_path.read_bytes() == old_docx


def test_create_submission_minimal_package_defaults_to_ama_citation_style(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["citation_style"] == "AMA"


def test_create_submission_minimal_package_copies_figures_and_tables(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    expected_paths = [
        submission_root / "figures" / "Figure1.pdf",
        submission_root / "figures" / "Figure1.png",
        submission_root / "figures" / "SupplementaryFigureS1.pdf",
        submission_root / "figures" / "SupplementaryFigureS1.png",
        submission_root / "tables" / "Table1.csv",
        submission_root / "tables" / "Table1.md",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_create_submission_minimal_package_uses_existing_figure_exports_when_catalog_lists_missing_alternative(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "title": "Main figure",
                    "export_paths": [
                        "paper/figures/F1_main.png",
                        "paper/figures/F1_main.pdf",
                        "paper/figures/F1_main.svg",
                    ],
                }
            ],
        },
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "figures" / "Figure1.png").exists()
    assert (submission_root / "figures" / "Figure1.pdf").exists()
    assert not (submission_root / "figures" / "Figure1.svg").exists()
    assert manifest["figures"][0]["source_paths"] == [
        "paper/figures/F1_main.png",
        "paper/figures/F1_main.pdf",
    ]
    source_contract_paths = [item["path"] for item in manifest["source_contract"]["source_files"]]
    assert "paper/figures/F1_main.png" in source_contract_paths
    assert "paper/figures/F1_main.pdf" in source_contract_paths
    assert "paper/figures/F1_main.svg" not in source_contract_paths

    authority = describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"
    assert authority["missing_source_paths"] == []


def test_create_submission_minimal_package_accepts_current_figure_and_table_catalog_shape(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "figure1",
                    "role": "paper_main",
                    "planned_exports": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "table1",
                    "path": "paper/tables/T1_summary.md",
                }
            ],
        },
    )

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "figures" / "figure1.pdf").exists()
    assert (submission_root / "figures" / "figure1.png").exists()
    assert (submission_root / "tables" / "table1.md").exists()
