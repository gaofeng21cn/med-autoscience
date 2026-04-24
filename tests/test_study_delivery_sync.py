from __future__ import annotations

import base64
import importlib
import json
import os
from pathlib import Path
import shutil

import pytest


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


def write_review_ledger(path: Path) -> None:
    dump_json(
        path,
        {
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer_1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
    )


def write_study_charter(study_root: Path, *, study_id: str = "002-early-residual-risk") -> Path:
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    dump_json(
        charter_path,
        {
            "schema_version": 1,
            "charter_id": f"charter::{study_id}::v1",
            "study_id": study_id,
            "publication_objective": "Deliver a manuscript-safe residual-risk paper package.",
            "paper_quality_contract": {
                "frozen_at_startup": True,
                "downstream_contract_roles": {
                    "evidence_ledger": "records evidence against evidence expectations",
                    "review_ledger": "records review closure against review expectations",
                    "final_audit": "audits readiness against the charter contract",
                },
            },
        },
    )
    return charter_path


def make_delivery_workspace(
    tmp_path: Path,
    *,
    quest_id: str = "002-early-residual-risk",
    runtime_reentry_study_id: str | None = None,
    nest_runtime_reentry_under_startup_contract: bool = False,
) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    quest_root = repo_root / "ops" / "med-deepscientist" / "runtime" / "quests" / quest_id
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-12345678"
    paper_root = worktree_root / "paper"
    study_root = repo_root / "studies" / "002-early-residual-risk"

    quest_yaml_lines = [
        f"quest_id: {quest_id}",
        "quest_root: /tmp/fake-quest-root",
    ]
    if runtime_reentry_study_id:
        if nest_runtime_reentry_under_startup_contract:
            quest_yaml_lines.extend(
                [
                    "startup_contract:",
                    "  runtime_reentry_gate:",
                    f"    study_id: {runtime_reentry_study_id}",
                ]
            )
        else:
            quest_yaml_lines.extend(
                [
                    "runtime_reentry_gate:",
                    f"  study_id: {runtime_reentry_study_id}",
                ]
            )
    write_text(worktree_root / "quest.yaml", "\n".join(quest_yaml_lines) + "\n")
    write_text(worktree_root / "SUMMARY.md", "# Summary\nStudy complete.\n")
    write_text(worktree_root / "status.md", "# Status\nCompleted.\n")

    write_text(study_root / "study.yaml", "study_id: 002-early-residual-risk\n")
    write_text(study_root / "manuscript" / "README.md", "manuscript\n")
    write_text(study_root / "artifacts" / "README.md", "artifacts\n")
    write_study_charter(study_root)

    write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx")
    write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    dump_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "generated_at": "2026-03-29T04:16:28+00:00",
            "citation_style": "AMA",
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )
    write_text(paper_root / "submission_minimal" / "figures" / "Figure1.pdf", "%PDF-1.4\n")
    write_png(paper_root / "submission_minimal" / "figures" / "Figure1.png")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.csv", "a,b\n1,2\n")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.md", "| a | b |\n| --- | --- |\n| 1 | 2 |\n")
    write_text(paper_root / "build" / "review_manuscript.md", "# Review Manuscript\n\nCurrent authority draft.\n")
    dump_json(
        paper_root / "review" / "submission_checklist.json",
        {
            "overall_status": "write_review_maintenance_nonfinal",
            "handoff_ready": False,
            "blocking_items": [
                {
                    "key": "figure_export_not_materialized_in_submission_minimal",
                    "notes": "Preview only; formal submission export is incomplete.",
                }
            ],
        },
    )
    write_review_ledger(paper_root / "review" / "review_ledger.json")
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "export_paths": [
                        "paper/figures/generated/F1_authority_preview.pdf",
                        "paper/figures/generated/F1_authority_preview.png",
                    ],
                }
            ],
        },
    )
    write_text(paper_root / "figures" / "generated" / "F1_authority_preview.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "generated" / "F1_authority_preview.png")
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "asset_paths": [
                        "paper/tables/generated/T1_authority_preview.csv",
                        "paper/tables/generated/T1_authority_preview.md",
                    ],
                }
            ],
        },
    )
    write_text(paper_root / "tables" / "generated" / "T1_authority_preview.csv", "x,y\n3,4\n")
    write_text(
        paper_root / "tables" / "generated" / "T1_authority_preview.md",
        "| x | y |\n| --- | --- |\n| 3 | 4 |\n",
    )

    write_text(paper_root / "final_claim_ledger.md", "# Final Claim Ledger\n")
    dump_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Primary manuscript-facing claim stays coupled to explicit evidence and gap tracking.",
                    "status": "supported",
                    "submission_scope": "main_text",
                    "evidence": [
                        {
                            "evidence_id": "EV1",
                            "kind": "display",
                            "source_paths": ["paper/figures/figure_catalog.json"],
                            "support_level": "direct",
                            "summary": "Figure and table authority assets support the retained main-text route.",
                        }
                    ],
                    "gaps": [
                        {
                            "gap_id": "G1",
                            "description": "External validation remains pending.",
                            "submission_impact": "Keep the claim inside a conservative interpretation boundary.",
                        }
                    ],
                    "recommended_actions": [
                        {
                            "action_id": "A1",
                            "priority": "required",
                            "description": "Carry the validation gap forward into reviewer-facing materials.",
                        }
                    ],
                }
            ],
        },
    )
    write_text(paper_root / "finalize_resume_packet.md", "# Finalize Resume Packet\n")
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
            },
        },
    )
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown": "paper/build/review_manuscript.md",
            "output_pdf": "paper/paper.pdf",
        },
    )

    return paper_root, study_root


def make_reentry_delivery_workspace(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    quest_root = repo_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "002-early-residual-risk-reentry-20260401"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-12345678"
    paper_root = worktree_root / "paper"
    study_root = repo_root / "studies" / "002-early-residual-risk"

    write_text(
        worktree_root / "quest.yaml",
        """quest_id: 002-early-residual-risk-reentry-20260401
quest_root: /tmp/fake-quest-root
status: active
""",
    )
    write_text(
        quest_root / "quest.yaml",
        """quest_id: 002-early-residual-risk-reentry-20260401
runtime_reentry_gate:
  status: ready
  study_id: 002-early-residual-risk
  study_root: /tmp/repo/studies/002-early-residual-risk
""",
    )
    write_text(worktree_root / "SUMMARY.md", "# Summary\nStudy complete.\n")
    write_text(worktree_root / "status.md", "# Status\nCompleted.\n")

    write_text(study_root / "study.yaml", "study_id: 002-early-residual-risk\n")
    write_text(study_root / "manuscript" / "README.md", "manuscript\n")
    write_text(study_root / "artifacts" / "README.md", "artifacts\n")

    write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx")
    write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    dump_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "generated_at": "2026-04-03T01:00:00+00:00",
            "citation_style": "AMA",
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )
    write_text(paper_root / "submission_minimal" / "figures" / "Figure1.pdf", "%PDF-1.4\n")
    write_png(paper_root / "submission_minimal" / "figures" / "Figure1.png")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.csv", "a,b\n1,2\n")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.md", "| a | b |\n| --- | --- |\n| 1 | 2 |\n")

    return paper_root, study_root


def make_draft_handoff_workspace(tmp_path: Path) -> tuple[Path, Path]:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    shutil.rmtree(paper_root / "submission_minimal")
    write_text(paper_root / "draft.md", "# Draft\n\nCurrent draft bundle.\n")
    write_text(paper_root / "references.bib", "@article{ref1,title={Example}}\n")
    write_text(paper_root / "review" / "review.md", "# Review\n")
    write_text(paper_root / "review" / "revision_log.md", "# Revision Log\n")
    dump_json(
        paper_root / "review" / "submission_checklist.json",
        {
            "overall_status": "display_materialized_slice_handoff_not_submission_ready",
            "handoff_ready": True,
            "blocking_items": [
                {
                    "key": "placeholder_heavy_branch_local_draft",
                    "notes": "Current draft is still placeholder-heavy.",
                }
            ],
        },
    )
    write_text(paper_root / "proofing" / "proofing_report.md", "# Proofing Report\n")
    write_text(paper_root / "proofing" / "language_issues.md", "# Language Issues\n")
    write_text(paper_root / "figures" / "figure_catalog.json", "{}\n")
    write_text(paper_root / "figures" / "F1_cohort_flow.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F1_cohort_flow.png")
    write_text(paper_root / "figures" / "cohort_flow.shell.json", "{}\n")
    write_text(paper_root / "tables" / "table_catalog.json", "{}\n")
    write_text(paper_root / "tables" / "T1_baseline_characteristics.csv", "a,b\n1,2\n")
    write_text(
        paper_root / "tables" / "T1_baseline_characteristics.md",
        "| a | b |\n| --- | --- |\n| 1 | 2 |\n",
    )
    write_text(paper_root / "tables" / "baseline_characteristics.shell.json", "{}\n")
    return paper_root, study_root


def make_draft_handoff_workspace_with_quick_review(tmp_path: Path) -> tuple[Path, Path]:
    paper_root, study_root = make_draft_handoff_workspace(tmp_path)
    write_text(paper_root / "paper.pdf", "%PDF-1.4\n%draft review manuscript\n")
    write_text(paper_root / "manuscript.docx", "docx draft review manuscript")
    write_text(paper_root / "build" / "review_manuscript.md", "# Review Manuscript\n\nCurrent draft bundle.\n")
    return paper_root, study_root


def test_sync_study_delivery_for_submission_minimal_populates_study_final_directories(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(
        tmp_path,
        quest_id="002-early-residual-risk-managed-20260402",
        runtime_reentry_study_id="002-early-residual-risk",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (study_root / "manuscript" / "manuscript.docx").exists()
    manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert manifest["quest_id"] == "002-early-residual-risk-managed-20260402"
    assert (study_root / "manuscript" / "paper.pdf").exists()
    assert (study_root / "manuscript" / "evidence_ledger.json").exists()
    assert (study_root / "manuscript" / "submission_manifest.json").exists()
    assert (study_root / "manuscript" / "delivery_manifest.json").exists()
    assert "This directory: `manuscript/`" in (
        study_root / "manuscript" / "README.md"
    ).read_text(encoding="utf-8")
    assert "paper/submission_minimal/" in (study_root / "manuscript" / "README.md").read_text(encoding="utf-8")
    assert "not part of the human-facing final delivery surface" in (
        study_root / "artifacts" / "README.md"
    ).read_text(encoding="utf-8")
    assert not (study_root / "artifacts" / "final").exists()
    assert not (study_root / "manuscript" / "submission_package").exists()
    assert not (study_root / "manuscript" / "submission_package.zip").exists()
    assert (study_root / "manuscript" / "current_package" / "figures" / "Figure1.pdf").exists()
    assert (study_root / "manuscript" / "current_package" / "evidence_ledger.json").exists()
    assert (study_root / "manuscript" / "current_package" / "tables" / "Table1.csv").exists()
    assert (study_root / "manuscript" / "current_package.zip").exists()
    delivery_manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert delivery_manifest["surface_roles"] == {
        "controller_authorized_paper_root": str(paper_root),
        "controller_authorized_package_source_root": str(paper_root / "submission_minimal"),
        "human_facing_delivery_root": str(study_root / "manuscript"),
        "human_facing_current_package_root": str(study_root / "manuscript" / "current_package"),
        "human_facing_current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        "auxiliary_evidence_root": None,
        "journal_submission_mirror_root": None,
    }
    assert "evidence_ledger.json" in delivery_manifest["source_relative_paths"]


def test_sync_study_delivery_for_submission_minimal_mirrors_review_ledger(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    mirrored_ledger_path = study_root / "manuscript" / "review" / "review_ledger.json"
    current_package_ledger_path = study_root / "manuscript" / "current_package" / "review" / "review_ledger.json"
    source_payload = json.loads((paper_root / "review" / "review_ledger.json").read_text(encoding="utf-8"))
    mirrored_payload = json.loads(mirrored_ledger_path.read_text(encoding="utf-8"))
    current_package_payload = json.loads(current_package_ledger_path.read_text(encoding="utf-8"))

    assert mirrored_payload == source_payload
    assert current_package_payload == source_payload
    delivery_manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert any(
        item["source_path"] == str((paper_root / "review" / "review_ledger.json").resolve())
        and item["target_path"] == str(mirrored_ledger_path.resolve())
        for item in delivery_manifest["copied_files"]
    )


def test_sync_study_delivery_preserves_existing_submission_delivery_when_projection_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    manuscript_root = study_root / "manuscript"
    baseline_manuscript_docx = (manuscript_root / "manuscript.docx").read_text(encoding="utf-8")
    baseline_current_package_docx = (
        manuscript_root / "current_package" / "manuscript.docx"
    ).read_text(encoding="utf-8")
    baseline_current_package_zip = (manuscript_root / "current_package.zip").read_bytes()
    baseline_delivery_manifest = (manuscript_root / "delivery_manifest.json").read_text(encoding="utf-8")

    write_text(paper_root / "submission_minimal" / "manuscript.docx", "updated docx")
    original_build_zip = module.build_zip_from_directory

    def failing_build_zip(*, source_root: Path, output_path: Path) -> None:
        if output_path.name == "current_package.zip":
            raise RuntimeError("simulated current package zip failure")
        original_build_zip(source_root=source_root, output_path=output_path)

    monkeypatch.setattr(module, "build_zip_from_directory", failing_build_zip)

    with pytest.raises(RuntimeError, match="simulated current package zip failure"):
        module.sync_study_delivery(
            paper_root=paper_root,
            stage="submission_minimal",
        )

    assert (manuscript_root / "manuscript.docx").read_text(encoding="utf-8") == baseline_manuscript_docx
    assert (
        manuscript_root / "current_package" / "manuscript.docx"
    ).read_text(encoding="utf-8") == baseline_current_package_docx
    assert (manuscript_root / "current_package.zip").read_bytes() == baseline_current_package_zip
    assert (manuscript_root / "delivery_manifest.json").read_text(encoding="utf-8") == baseline_delivery_manifest


def test_sync_study_delivery_projects_charter_linkage_into_manifest_and_current_package(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    delivery_manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    linkage = delivery_manifest["charter_contract_linkage"]
    readme_text = (study_root / "manuscript" / "current_package" / "README.md").read_text(encoding="utf-8")

    assert linkage["status"] == "linked"
    assert linkage["study_charter_ref"]["charter_id"] == "charter::002-early-residual-risk::v1"
    assert linkage["study_charter_ref"]["artifact_path"] == str(
        study_root / "artifacts" / "controller" / "study_charter.json"
    )
    assert linkage["paper_quality_contract"]["present"] is True
    assert linkage["ledger_linkages"]["evidence_ledger"]["status"] == "linked"
    assert linkage["ledger_linkages"]["review_ledger"]["status"] == "linked"
    assert linkage["study_charter_ref"]["mirrored_artifact_path"] == str(
        study_root / "manuscript" / "current_package" / "controller" / "study_charter.json"
    )
    assert (study_root / "manuscript" / "current_package" / "controller" / "study_charter.json").exists()
    assert "Study charter contract" in readme_text
    assert "charter::002-early-residual-risk::v1" in readme_text
    assert "Mirrored study charter artifact" in readme_text
    assert "Evidence ledger linkage: linked" in readme_text
    assert "Review ledger linkage: linked" in readme_text


def test_sync_study_delivery_writes_submission_todo_for_pending_front_matter(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["front_matter_placeholders"] = {
        "authors": "pending",
        "ethics": "pending",
        "data_availability": "pending",
    }
    dump_json(manifest_path, manifest)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    todo_path = study_root / "manuscript" / "current_package" / "SUBMISSION_TODO.md"
    todo_text = todo_path.read_text(encoding="utf-8")
    assert "# Submission TODO" in todo_text
    assert "- Authors: pending" in todo_text
    assert "- Ethics: pending" in todo_text
    assert "- Data availability: pending" in todo_text
    assert "scientific audit" in todo_text
    delivery_manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert {
        "category": "current_package_submission_todo",
        "path": str(todo_path.resolve()),
    } in delivery_manifest["generated_files"]


def test_sync_study_delivery_writes_submission_todo_from_metadata_closeout_followups(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["metadata_closeout"] = {
        "status": "non_blocking_followup_only",
        "summary": "Administrative follow-up only.",
        "non_blocking_followups": [
            {
                "key": "objective_metadata_closeout",
                "status": "pending_non_blocking",
                "notes": "Authors, affiliations, and declaration wording still need user confirmation.",
            },
            {
                "key": "journal_template_page_proof",
                "status": "conditional",
                "notes": "Only needed after a concrete target journal is chosen.",
            },
        ],
    }
    dump_json(manifest_path, manifest)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    todo_path = study_root / "manuscript" / "current_package" / "SUBMISSION_TODO.md"
    todo_text = todo_path.read_text(encoding="utf-8")
    assert "# Submission TODO" in todo_text
    assert "- Objective metadata closeout: Authors, affiliations, and declaration wording still need user confirmation." in todo_text
    assert "- Journal template page proof: Only needed after a concrete target journal is chosen." in todo_text
    assert "scientific audit" in todo_text


def test_describe_submission_delivery_flags_stale_when_authority_source_disappears(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    shutil.rmtree(paper_root / "submission_minimal")
    write_text(paper_root / "submission_minimal" / "README.md", "# Placeholder\n")
    write_text(paper_root / "submission_minimal" / "journal_declarations.md", "# Placeholder\n")

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "stale_source_missing"
    assert result["stale_reason"] == "current_submission_source_missing"
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")
    assert result["missing_source_paths"] != []


def test_describe_submission_delivery_flags_stale_when_current_package_projection_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    shutil.rmtree(study_root / "manuscript" / "current_package")
    (study_root / "manuscript" / "current_package.zip").unlink()

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["status"] == "stale_projection_missing"
    assert result["stale_reason"] == "delivery_projection_missing"


def test_describe_submission_delivery_flags_stale_when_authority_package_changes_under_same_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    write_text(paper_root / "submission_minimal" / "manuscript.docx", "updated docx")

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "stale_source_changed"
    assert result["stale_reason"] == "delivery_manifest_source_changed"
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_describe_submission_delivery_keeps_current_when_only_authority_source_mtime_changes(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    source_path = paper_root / "submission_minimal" / "manuscript.docx"
    stat = source_path.stat()
    os.utime(source_path, ns=(stat.st_atime_ns + 1_000_000_000, stat.st_mtime_ns + 1_000_000_000))

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "current"
    assert result["stale_reason"] is None
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_describe_submission_delivery_keeps_current_with_generated_current_package_readme(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    (paper_root / "submission_minimal" / "README.md").write_text(
        "# Canonical Submission Package\n\nAuthoritative paper-owned package.\n",
        encoding="utf-8",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "current"
    assert result["stale_reason"] is None
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_describe_submission_delivery_keeps_current_when_evidence_ledger_updated_at_changes_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    evidence_ledger_path = paper_root / "evidence_ledger.json"
    evidence_ledger = json.loads(evidence_ledger_path.read_text(encoding="utf-8"))
    evidence_ledger["updated_at"] = "2026-03-29T04:16:28+00:00"
    evidence_ledger_path.write_text(
        json.dumps(evidence_ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    evidence_ledger["updated_at"] = "2026-03-29T05:16:28+00:00"
    evidence_ledger_path.write_text(
        json.dumps(evidence_ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "current"
    assert result["stale_reason"] is None
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_materialize_submission_delivery_stale_notice_clears_stale_mirror_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    shutil.rmtree(paper_root / "submission_minimal" / "figures")
    shutil.rmtree(paper_root / "submission_minimal" / "tables")

    result = module.describe_submission_delivery(paper_root=paper_root)
    stale_sync = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason=str(result["stale_reason"]),
        missing_source_paths=list(result["missing_source_paths"]),
    )

    manuscript_root = study_root / "manuscript"
    status_path = manuscript_root / "delivery_status.json"

    assert stale_sync["status"] == "stale_source_missing"
    assert stale_sync["current_package_root"] == str(manuscript_root / "current_package")
    assert (manuscript_root / "manuscript.docx").exists()
    assert (manuscript_root / "paper.pdf").exists()
    assert (manuscript_root / "submission_manifest.json").exists()
    assert not (manuscript_root / "submission_package").exists()
    assert not (manuscript_root / "submission_package.zip").exists()
    assert (manuscript_root / "current_package" / "README.md").exists()
    assert (manuscript_root / "current_package.zip").exists()
    assert "audit preview" in (
        manuscript_root / "current_package" / "README.md"
    ).read_text(encoding="utf-8")
    assert (manuscript_root / "current_package" / "review_manuscript.md").exists()
    assert (manuscript_root / "current_package" / "compile_report.json").exists()
    assert (manuscript_root / "current_package" / "submission_checklist.json").exists()
    assert (manuscript_root / "current_package" / "figures" / "figure_catalog.json").exists()
    assert (manuscript_root / "current_package" / "figures" / "F1_authority_preview.pdf").exists()
    assert (manuscript_root / "current_package" / "tables" / "table_catalog.json").exists()
    assert (manuscript_root / "current_package" / "tables" / "T1_authority_preview.csv").exists()
    status_payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert status_payload["status"] == "stale_source_missing"
    assert status_payload["stale_reason"] == "delivery_manifest_sources_missing"
    assert status_payload["preview_mode"] == "authority_audit_preview"
    assert status_payload["submission_ready"] is False
    assert status_payload["active_delivery_manifest_path"] == str(manuscript_root / "delivery_manifest.json")
    assert status_payload["missing_source_paths"] != []


def test_sync_study_delivery_accepts_study_owned_paper_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    quest_paper_root, study_root = make_delivery_workspace(tmp_path)
    study_paper_root = study_root / "paper"
    shutil.copytree(quest_paper_root, study_paper_root)

    module.sync_study_delivery(
        paper_root=study_paper_root,
        stage="submission_minimal",
    )

    assert (study_root / "manuscript" / "manuscript.docx").exists()
    assert (study_root / "manuscript" / "current_package.zip").exists()
    assert not (study_root / "artifacts" / "final").exists()


def test_sync_study_delivery_for_finalize_copies_closeout_documents(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="finalize",
    )

    assert (study_root / "manuscript" / "SUMMARY.md").exists()
    assert (study_root / "manuscript" / "status.md").exists()
    assert (study_root / "manuscript" / "final_claim_ledger.md").exists()
    assert (study_root / "manuscript" / "finalize_resume_packet.md").exists()
    assert "machine-generated finalization evidence only" in (
        study_root / "artifacts" / "final" / "README.md"
    ).read_text(encoding="utf-8")
    assert (study_root / "artifacts" / "final" / "paper_bundle_manifest.json").exists()
    assert (study_root / "artifacts" / "final" / "compile_report.json").exists()
    assert not (study_root / "artifacts" / "final" / "figures").exists()
    assert not (study_root / "artifacts" / "final" / "tables").exists()
    delivery_manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert delivery_manifest["surface_roles"]["auxiliary_evidence_root"] == str(study_root / "artifacts" / "final")


def test_sync_study_delivery_for_finalize_accepts_canonical_handoff_from_worktree(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    (paper_root / "finalize_resume_packet.md").unlink()
    write_text(paper_root.parent / "handoffs" / "finalize_resume_packet.md", "# Canonical Finalize Resume Packet\n")

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="finalize",
    )

    assert (study_root / "manuscript" / "finalize_resume_packet.md").read_text(encoding="utf-8") == (
        "# Canonical Finalize Resume Packet\n"
    )


def test_sync_study_delivery_for_frontiers_family_creates_family_package_without_resetting_generic_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    write_text(study_root / "manuscript" / "manuscript.docx", "existing generic package")
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "manuscript.docx",
        "frontiers manuscript",
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "Supplementary_Material.docx",
        "frontiers supplementary",
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "paper.pdf",
        "%PDF-1.4\n",
    )
    dump_json(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "frontiers_family_harvard",
            "citation_style": "FrontiersHarvard",
        },
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "figures" / "Figure1.pdf",
        "%PDF-1.4\n",
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "tables" / "Table1.csv",
        "a,b\n1,2\n",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        publication_profile="frontiers_family_harvard",
    )

    journal_package_root = (
        study_root / "manuscript" / "journal_packages" / "frontiers_family_harvard"
    )
    delivery_manifest = json.loads((journal_package_root / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert (study_root / "manuscript" / "manuscript.docx").read_text(encoding="utf-8") == "existing generic package"
    assert (journal_package_root / "manuscript.docx").exists()
    assert (journal_package_root / "Supplementary_Material.docx").exists()
    assert (journal_package_root / "README.md").exists()
    assert (study_root / "manuscript" / "frontiers_family_harvard_submission_package.zip").exists()
    assert delivery_manifest["surface_roles"] == {
        "controller_authorized_paper_root": str(paper_root),
        "controller_authorized_package_source_root": str(
            paper_root / "journal_submissions" / "frontiers_family_harvard"
        ),
        "human_facing_delivery_root": str(study_root / "manuscript"),
        "human_facing_current_package_root": str(study_root / "manuscript" / "current_package"),
        "human_facing_current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        "auxiliary_evidence_root": None,
        "journal_submission_mirror_root": None,
    }


def test_sync_study_delivery_can_promote_primary_journal_package_into_study_final(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "manuscript.docx",
        "frontiers manuscript",
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "Supplementary_Material.docx",
        "frontiers supplementary",
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "paper.pdf",
        "%PDF-1.4\n",
    )
    dump_json(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "frontiers_family_harvard",
            "citation_style": "FrontiersHarvard",
        },
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "figures" / "Figure1.svg",
        "<svg><text>flow</text></svg>\n",
    )
    write_png(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "figures" / "Figure1.png"
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "tables" / "Table1.csv",
        "a,b\n1,2\n",
    )
    write_text(
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "tables" / "Table1.md",
        "| a | b |\n| --- | --- |\n| 1 | 2 |\n",
    )
    write_text(
        study_root
        / "manuscript"
        / "journal_packages"
        / "frontiers_family_harvard"
        / "stale.txt",
        "legacy stale package\n",
    )
    write_text(
        study_root / "manuscript" / "frontiers_family_harvard_submission_package.zip",
        "legacy stale zip\n",
    )

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        publication_profile="frontiers_family_harvard",
        promote_to_final=True,
    )

    assert result["stage"] == "frontiers_family_harvard_submission"
    assert (study_root / "manuscript" / "manuscript.docx").read_text(encoding="utf-8") == (
        "frontiers manuscript"
    )
    assert not (study_root / "manuscript" / "submission_package").exists()
    assert not (study_root / "manuscript" / "submission_package.zip").exists()
    assert (study_root / "manuscript" / "current_package" / "manuscript.docx").exists()
    assert (study_root / "manuscript" / "current_package" / "figures" / "Figure1.svg").exists()
    assert (study_root / "manuscript" / "current_package" / "tables" / "Table1.csv").exists()
    assert not (study_root / "artifacts" / "final").exists()
    assert (
        study_root
        / "manuscript"
        / "journal_package_mirrors"
        / "frontiers_family_harvard"
        / "submission_manifest.json"
    ).exists()
    assert not (study_root / "manuscript" / "journal_packages").exists()
    assert not (study_root / "manuscript" / "frontiers_family_harvard_submission_package.zip").exists()


def test_sync_study_delivery_rejects_unsupported_publication_profile(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, _ = make_delivery_workspace(tmp_path)

    try:
        module.sync_study_delivery(
            paper_root=paper_root,
            stage="submission_minimal",
            publication_profile="pituitary",
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected sync_study_delivery to reject unsupported publication profiles")

    assert "unsupported publication profile" in message


def test_sync_study_delivery_accepts_managed_quest_id_when_runtime_reentry_gate_declares_study_id(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(
        tmp_path,
        quest_id="002-early-residual-risk-managed-20260402",
        runtime_reentry_study_id="002-early-residual-risk",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (study_root / "manuscript" / "manuscript.docx").exists()
    delivery_manifest = json.loads((study_root / "manuscript" / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert delivery_manifest["quest_id"] == "002-early-residual-risk-managed-20260402"


def test_sync_study_delivery_accepts_managed_quest_id_when_runtime_reentry_gate_is_nested_in_startup_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(
        tmp_path,
        quest_id="002-early-residual-risk-managed-20260402",
        runtime_reentry_study_id="002-early-residual-risk",
        nest_runtime_reentry_under_startup_contract=True,
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (study_root / "manuscript" / "manuscript.docx").exists()


def test_can_sync_study_delivery_accepts_quest_yaml_with_nested_startup_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, _ = make_delivery_workspace(tmp_path)
    quest_yaml_path = paper_root.parent / "quest.yaml"

    write_text(
        quest_yaml_path,
        """quest_id: 002-early-residual-risk
quest_root: /tmp/fake-quest-root
startup_contract:
  launch_mode: custom
  custom_profile: continue_existing_state
""",
    )

    assert module.can_sync_study_delivery(paper_root=paper_root) is True


def test_sync_study_delivery_maps_reentry_quest_back_to_study_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_reentry_delivery_workspace(tmp_path)

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (study_root / "manuscript" / "manuscript.docx").exists()
    assert (study_root / "manuscript" / "current_package.zip").exists()
    assert manifest["quest_id"] == "002-early-residual-risk-reentry-20260401"
    assert manifest["study_id"] == "002-early-residual-risk"


def test_sync_study_delivery_for_draft_handoff_populates_current_human_package(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_draft_handoff_workspace(tmp_path)

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="draft_handoff",
    )

    assert not (study_root / "manuscript" / "draft_bundle").exists()
    assert not (study_root / "manuscript" / "draft_bundle.zip").exists()
    assert (study_root / "manuscript" / "current_package" / "draft.md").exists()
    assert (study_root / "manuscript" / "current_package" / "review" / "submission_checklist.json").exists()
    assert (study_root / "manuscript" / "current_package" / "proofing" / "proofing_report.md").exists()
    assert (study_root / "manuscript" / "current_package" / "figures" / "F1_cohort_flow.pdf").exists()
    assert (study_root / "manuscript" / "current_package" / "tables" / "T1_baseline_characteristics.csv").exists()
    assert not (study_root / "manuscript" / "current_package" / "figures" / "cohort_flow.shell.json").exists()
    assert not (study_root / "manuscript" / "current_package" / "tables" / "baseline_characteristics.shell.json").exists()
    assert (study_root / "manuscript" / "current_package.zip").exists()
    assert manifest["stage"] == "draft_handoff"
    assert manifest["targets"]["current_package_root"] == str(study_root / "manuscript" / "current_package")
    assert manifest["targets"]["current_package_zip"] == str(study_root / "manuscript" / "current_package.zip")


def test_describe_draft_handoff_delivery_detects_stale_sources(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_draft_handoff_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="draft_handoff",
    )

    current = module.describe_draft_handoff_delivery(paper_root=paper_root)
    assert current["status"] == "current"
    assert current["current_package_root"] == str(study_root / "manuscript" / "current_package")

    write_text(paper_root / "draft.md", "# Draft\n\nUpdated draft bundle.\n")

    stale = module.describe_draft_handoff_delivery(paper_root=paper_root)
    assert stale["status"] == "stale"

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="draft_handoff",
    )
    shutil.rmtree(study_root / "manuscript" / "current_package")
    (study_root / "manuscript" / "current_package.zip").unlink()

    stale_projection = module.describe_draft_handoff_delivery(paper_root=paper_root)
    assert stale_projection["status"] == "stale"


def test_sync_study_delivery_for_draft_handoff_copies_quick_review_manuscript_files_when_present(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_draft_handoff_workspace_with_quick_review(tmp_path)

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="draft_handoff",
    )

    assert (study_root / "manuscript" / "current_package" / "paper.pdf").exists()
    assert (study_root / "manuscript" / "current_package" / "manuscript.docx").exists()
    assert (study_root / "manuscript" / "current_package" / "build" / "review_manuscript.md").exists()
    assert "paper.pdf" in manifest["source_relative_paths"]
    assert "manuscript.docx" in manifest["source_relative_paths"]
    assert "build/review_manuscript.md" in manifest["source_relative_paths"]
