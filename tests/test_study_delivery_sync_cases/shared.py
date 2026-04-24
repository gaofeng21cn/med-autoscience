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




















































