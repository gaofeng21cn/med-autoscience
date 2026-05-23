from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path
import zipfile


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+aRX0AAAAASUVORK5CYII="
)


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(PNG_1X1_BASE64))


def make_package_workspace(tmp_path: Path) -> tuple[Path, Path]:
    study_root = tmp_path / "studies" / "001-guideline-aligned-triple-trend"
    paper_root = study_root / "paper"
    write_text(study_root / "study.yaml", "study_id: 001-guideline-aligned-triple-trend\n")
    write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx")
    write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    write_text(paper_root / "submission_minimal" / "figures" / "Figure1.pdf", "%PDF-1.4\n")
    write_png(paper_root / "submission_minimal" / "figures" / "Figure1.png")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.csv", "a,b\n1,2\n")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.md", "| a | b |\n| --- | --- |\n| 1 | 2 |\n")
    dump_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
            "source_signature": "source::fixture",
            "source_contract": {
                "source_signature": "source::fixture",
                "source_paths": [
                    "paper/build/review_manuscript.md",
                    "paper/figures/Figure1.png",
                ],
                "source_files": [
                    {
                        "path": "paper/build/review_manuscript.md",
                        "sha256": "review-sha",
                    },
                    {
                        "path": "paper/figures/Figure1.png",
                        "sha256": "figure-sha",
                    },
                ],
            },
            "front_matter_placeholders": {
                "authors": "pending",
                "ethics": "pending",
            },
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )
    return paper_root, study_root


def write_rheumatology_requirements(study_root: Path) -> None:
    requirements_module = importlib.import_module("med_autoscience.journal_requirements")
    requirements_module.write_journal_requirements(
        study_root=study_root,
        requirements=requirements_module.JournalRequirements(
            journal_name="Rheumatology International",
            journal_slug="rheumatology-international",
            official_guidelines_url="https://example.org/ri-guide",
            publication_profile="general_medical_journal",
            abstract_word_cap=250,
            title_word_cap=None,
            keyword_limit=None,
            main_text_word_cap=None,
            main_display_budget=6,
            table_budget=2,
            figure_budget=4,
            supplementary_allowed=True,
            title_page_required=True,
            blinded_main_document=False,
            reference_style_family="AMA",
            required_sections=(),
            declaration_requirements=(),
            submission_checklist_items=(),
            template_assets=(),
        ),
    )


def test_materialize_journal_package_writes_stable_shallow_package(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    paper_root, study_root = make_package_workspace(tmp_path)

    write_rheumatology_requirements(study_root)

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    package_root = study_root / "submission_packages" / "rheumatology-international"
    assert result["status"] == "materialized"
    assert (package_root / "main_manuscript.docx").exists()
    assert (package_root / "main_manuscript.pdf").exists()
    assert (package_root / "audit" / "submission_manifest.json").exists()
    assert (package_root / "audit" / "journal_requirements_snapshot.json").exists()
    assert (package_root / "reproducibility" / "source_signature.json").exists()
    assert (package_root / "reproducibility" / "source_relative_paths.json").exists()
    assert (package_root / "reproducibility" / "analysis_manifest.json").exists()
    assert not (package_root / "submission_manifest.json").exists()
    assert not (package_root / "journal_requirements_snapshot.json").exists()
    assert (package_root / "SUBMISSION_TODO.md").exists()
    assert (package_root / "rheumatology-international_submission_package.zip").exists()
    package_status = importlib.import_module("med_autoscience.journal_requirements").describe_journal_submission_package(
        study_root=study_root,
        journal_slug="rheumatology-international",
    )
    assert package_status["status"] == "current"
    assert package_status["journal_requirements_snapshot_path"] == str(
        package_root / "audit" / "journal_requirements_snapshot.json"
    )
    assert package_status["missing_files"] == []
    manifest = json.loads((package_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8"))
    assert manifest["package_role"] == "journal_targeted_projection"
    assert manifest["default_human_facing_package_root"] == str(study_root / "manuscript" / "current_package")
    assert manifest["source_authority"]["authority_kind"] == "study_canonical_paper"
    assert manifest["source_authority"]["is_study_canonical_paper_root"] is True
    assert manifest["journal_target_authority"]["confirmation_status"] == "unconfirmed"
    assert manifest["formatting_boundary"]["journal_submission_ready_claim_allowed"] is False
    assert manifest["paths"]["requirements_snapshot"] == str(
        package_root / "audit" / "journal_requirements_snapshot.json"
    )
    assert manifest["delivery_layout"]["audit_paths"]["submission_manifest"] == str(
        package_root / "audit" / "submission_manifest.json"
    )
    assert manifest["delivery_layout"]["audit_paths"]["journal_requirements_snapshot"] == str(
        package_root / "audit" / "journal_requirements_snapshot.json"
    )
    assert manifest["delivery_layout"]["reproducibility_paths"]["source_signature"] == str(
        package_root / "reproducibility" / "source_signature.json"
    )
    source_signature = json.loads(
        (package_root / "reproducibility" / "source_signature.json").read_text(encoding="utf-8")
    )
    assert source_signature["package_role"] == "journal_targeted_projection"
    assert source_signature["source_signature"] == "source::fixture"
    source_relative_paths = json.loads(
        (package_root / "reproducibility" / "source_relative_paths.json").read_text(encoding="utf-8")
    )
    assert source_relative_paths["source_relative_paths"] == [
        "paper/build/review_manuscript.md",
        "paper/figures/Figure1.png",
    ]
    analysis_manifest = json.loads(
        (package_root / "reproducibility" / "analysis_manifest.json").read_text(encoding="utf-8")
    )
    assert analysis_manifest["package_role"] == "journal_targeted_projection"
    assert analysis_manifest["analysis_manifest_present"] is False
    readme = (package_root / "README.md").read_text(encoding="utf-8")
    assert "Default human-facing package: `manuscript/current_package/`" in readme
    assert "derived target-journal projection" in readme


def test_materialize_journal_package_route_gate_blocks_zip_materialization(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    paper_root, study_root = make_package_workspace(tmp_path)
    write_rheumatology_requirements(study_root)

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
        route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "dispatch_gate": {
                    "state": "open",
                    "dispatch_allowed": True,
                    "blocking_reasons": [],
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

    package_root = study_root / "submission_packages" / "rheumatology-international"
    assert result["status"] == "authority_route_blocked"
    assert result["authority_route_gate"]["allowed"] is False
    assert not package_root.exists()


def test_materialize_journal_package_marks_runtime_worktree_preview_until_target_confirmed(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    study_root = tmp_path / "studies" / "001-guideline-aligned-triple-trend"
    paper_root = tmp_path / "runtime" / "quests" / "001" / ".ds" / "worktrees" / "paper-run-1" / "paper"
    source_root = paper_root / "submission_minimal"
    write_text(study_root / "study.yaml", "study_id: 001-guideline-aligned-triple-trend\n")
    write_text(source_root / "manuscript.docx", "docx")
    write_text(source_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(
        source_root / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
            "front_matter_placeholders": {},
        },
    )
    dump_json(
        paper_root / "submission_targets.resolved.json",
        {
            "schema_version": 1,
            "decision_kind": "journal_shortlist_candidate",
            "decision_source": "study_yaml",
            "primary_target": {
                "journal_name": "Rheumatology International",
                "journal_slug": "rheumatology-international",
                "publication_profile": "general_medical_journal",
                "official_guidelines_url": "https://example.org/ri-guide",
                "resolution_status": "resolved",
            },
        },
    )
    write_rheumatology_requirements(study_root)

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    manifest = json.loads(Path(result["submission_manifest_path"]).read_text(encoding="utf-8"))
    assert result["source_authority_kind"] == "runtime_worktree_paper"
    assert result["target_confirmation_status"] == "unconfirmed"
    assert manifest["source_authority"]["is_study_canonical_paper_root"] is False
    assert manifest["journal_target_authority"]["decision_source"] == "study_yaml"
    assert manifest["journal_target_authority"]["user_confirmed"] is False
    assert manifest["formatting_boundary"]["boundary_reason"] == "target_not_user_confirmed"


def test_materialize_journal_package_can_record_explicit_confirmed_target(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    paper_root, study_root = make_package_workspace(tmp_path)
    write_rheumatology_requirements(study_root)

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
        confirmed_target=True,
    )

    manifest = json.loads(Path(result["submission_manifest_path"]).read_text(encoding="utf-8"))
    assert result["target_confirmation_status"] == "confirmed"
    assert manifest["journal_target_authority"]["user_confirmed"] is True
    assert manifest["journal_target_authority"]["confirmation_basis"] == "explicit_controller_argument"
    assert manifest["formatting_boundary"]["journal_submission_ready_claim_allowed"] is True


def test_materialized_journal_package_survives_manuscript_delivery_sync_refresh(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    delivery_sync = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_package_workspace(tmp_path)

    write_rheumatology_requirements(study_root)
    package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (
        study_root / "submission_packages" / "rheumatology-international" / "audit" / "submission_manifest.json"
    ).exists()


def test_materialize_journal_package_reads_legacy_submission_manifest_without_rewriting_root_audit_json(
    tmp_path: Path,
) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    paper_root, study_root = make_package_workspace(tmp_path)
    source_root = paper_root / "submission_minimal"
    legacy_manifest_path = source_root / "submission_manifest.json"
    legacy_manifest = json.loads(legacy_manifest_path.read_text(encoding="utf-8"))
    legacy_manifest["source_signature"] = "source::legacy-root"
    legacy_manifest_path.write_text(
        json.dumps(legacy_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_rheumatology_requirements(study_root)

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    package_root = study_root / "submission_packages" / "rheumatology-international"
    assert result["status"] == "materialized"
    assert result["submission_manifest_path"] == str(package_root / "audit" / "submission_manifest.json")
    assert not (package_root / "submission_manifest.json").exists()
    assert not (package_root / "journal_requirements_snapshot.json").exists()
    manifest = json.loads((package_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_submission_manifest_path"] == str(legacy_manifest_path)
    assert manifest["delivery_layout"]["legacy_input_status"] == "legacy_root_manifest_read"
    source_signature = json.loads(
        (package_root / "reproducibility" / "source_signature.json").read_text(encoding="utf-8")
    )
    assert source_signature["source_signature"] == "source::legacy-root"


def test_materialize_journal_package_writes_shallow_zip_without_root_audit_manifest(
    tmp_path: Path,
) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    paper_root, study_root = make_package_workspace(tmp_path)
    write_rheumatology_requirements(study_root)

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    package_root = study_root / "submission_packages" / "rheumatology-international"
    manifest_path = package_root / "audit" / "submission_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with zipfile.ZipFile(package_root / "rheumatology-international_submission_package.zip") as archive:
        names = set(archive.namelist())

    assert result["submission_manifest_path"] == str(manifest_path)
    assert result["zip_path"] == str(package_root / "rheumatology-international_submission_package.zip")
    assert result["status"] == "materialized"
    assert manifest["delivery_layout"]["layout_version"] == "submission-package.v2"
    assert manifest["delivery_layout"]["package_role"] == "journal_targeted_projection"
    assert manifest["delivery_layout"]["human_package_root"] == str(package_root)
    assert not (package_root / "submission_manifest.json").exists()
    assert "audit/submission_manifest.json" in names
    assert "audit/journal_requirements_snapshot.json" in names
    assert "reproducibility/source_signature.json" in names
    assert "submission_manifest.json" not in names
    assert "journal_requirements_snapshot.json" not in names
    assert not any(name.startswith(("rheumatology-international/", "submission_packages/")) for name in names)
