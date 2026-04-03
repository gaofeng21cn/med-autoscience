from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path


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


def make_delivery_workspace(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    quest_root = repo_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "002-early-residual-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-12345678"
    paper_root = worktree_root / "paper"
    study_root = repo_root / "studies" / "002-early-residual-risk"

    write_text(
        worktree_root / "quest.yaml",
        """quest_id: 002-early-residual-risk
quest_root: /tmp/fake-quest-root
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

    write_text(paper_root / "final_claim_ledger.md", "# Final Claim Ledger\n")
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


def test_sync_study_delivery_for_submission_minimal_populates_study_final_directories(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (study_root / "manuscript" / "final" / "manuscript.docx").exists()
    assert (study_root / "manuscript" / "final" / "paper.pdf").exists()
    assert (study_root / "manuscript" / "final" / "submission_manifest.json").exists()
    assert (study_root / "manuscript" / "final" / "delivery_manifest.json").exists()
    assert (study_root / "artifacts" / "final" / "figures" / "Figure1.pdf").exists()
    assert (study_root / "artifacts" / "final" / "tables" / "Table1.csv").exists()


def test_sync_study_delivery_for_finalize_copies_closeout_documents(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="finalize",
    )

    assert (study_root / "manuscript" / "final" / "SUMMARY.md").exists()
    assert (study_root / "manuscript" / "final" / "status.md").exists()
    assert (study_root / "manuscript" / "final" / "final_claim_ledger.md").exists()
    assert (study_root / "manuscript" / "final" / "finalize_resume_packet.md").exists()
    assert (study_root / "artifacts" / "final" / "paper_bundle_manifest.json").exists()
    assert (study_root / "artifacts" / "final" / "compile_report.json").exists()


def test_sync_study_delivery_for_finalize_accepts_canonical_handoff_from_worktree(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    (paper_root / "finalize_resume_packet.md").unlink()
    write_text(paper_root.parent / "handoffs" / "finalize_resume_packet.md", "# Canonical Finalize Resume Packet\n")

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="finalize",
    )

    assert (study_root / "manuscript" / "final" / "finalize_resume_packet.md").read_text(encoding="utf-8") == (
        "# Canonical Finalize Resume Packet\n"
    )


def test_sync_study_delivery_for_frontiers_family_creates_family_package_without_resetting_generic_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    write_text(study_root / "manuscript" / "final" / "manuscript.docx", "existing generic package")
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
        study_root / "manuscript" / "final" / "journal_packages" / "frontiers_family_harvard"
    )
    assert (study_root / "manuscript" / "final" / "manuscript.docx").read_text(encoding="utf-8") == "existing generic package"
    assert (journal_package_root / "manuscript.docx").exists()
    assert (journal_package_root / "Supplementary_Material.docx").exists()
    assert (journal_package_root / "README.md").exists()
    assert (study_root / "manuscript" / "final" / "frontiers_family_harvard_submission_package.zip").exists()


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
