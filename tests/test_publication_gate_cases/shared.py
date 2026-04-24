from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import shutil
from textwrap import dedent


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_quest(
    tmp_path: Path,
    *,
    include_submission_minimal: bool,
    include_main_result: bool = True,
    runtime_status: str = "running",
    include_unmanaged_submission_surface: bool = False,
    archive_legacy_submission_surface: bool = False,
    include_current_medical_publication_surface_report: bool = False,
    medical_publication_surface_status: str = "clear",
    medical_publication_surface_report: dict[str, object] | None = None,
    manuscript_files: dict[str, str] | None = None,
    submission_checklist: dict[str, object] | None = None,
    paper_line_state: dict[str, object] | None = None,
    figure_catalog: dict[str, object] | None = None,
    table_catalog: dict[str, object] | None = None,
    include_submission_authority_inputs: bool = True,
) -> Path:
    quest_id = "002-early-residual-risk"
    study_id = quest_id
    quest_root = tmp_path / "ops" / "med-deepscientist" / "runtime" / "quests" / "002-early-residual-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    study_root = tmp_path / "studies" / study_id

    worktree_root.mkdir(parents=True, exist_ok=True)
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 002-early-residual-risk\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text("quest_id: 002-early-residual-risk\n", encoding="utf-8")
    (quest_root / "quest.yaml").write_text(
        dedent(
            """
            quest_id: 002-early-residual-risk
            study_id: 002-early-residual-risk
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (worktree_root / "quest.yaml").write_text(
        dedent(
            """
            quest_id: 002-early-residual-risk
            study_id: 002-early-residual-risk
            """
        ).lstrip(),
        encoding="utf-8",
    )
    dump_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "schema_version": 1,
            "charter_id": "charter::002-early-residual-risk::v1",
            "study_id": study_id,
            "publication_objective": "risk stratification external validation",
        },
    )

    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": quest_id,
            "status": runtime_status,
            "active_run_id": "run-1" if include_main_result else None,
        },
    )
    if include_main_result:
        dump_json(
            worktree_root / "experiments" / "main" / "run-1" / "RESULT.json",
            {
                "quest_id": "002-early-residual-risk",
                "run_id": "run-1",
                "worktree_root": str(worktree_root),
                "metric_contract": {
                    "required_non_scalar_deliverables": [],
                },
                "metrics_summary": {
                    "roc_auc": 0.81,
                    "average_precision": 0.45,
                    "brier_score": 0.11,
                    "calibration_intercept": 0.02,
                    "calibration_slope": 1.01,
                },
                "baseline_comparisons": {"items": []},
                "results_summary": "summary",
                "conclusion": "conclusion",
            },
        )
    dump_json(
        worktree_root / "paper" / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "summary": "paper bundle summary",
            "paper_branch": "paper/main",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )
    dump_json(
        worktree_root / "paper" / "build" / "compile_report.json",
        {
            "schema_version": 1,
            "status": "compiled_with_open_submission_items",
            "summary": "compile report summary",
            "bibliography_entry_count": 21,
            "author_metadata_status": "placeholder_external_input_required",
            "source_markdown_path": "paper/build/review_manuscript.md",
        },
    )
    if include_submission_authority_inputs:
        write_text(
            worktree_root / "paper" / "build" / "review_manuscript.md",
            "# Review Manuscript\n\nCurrent authority draft.\n",
        )
        write_text(
            worktree_root / "paper" / "references.bib",
            "@article{ref1,title={Ref}}\n",
        )
    if paper_line_state is not None:
        dump_json(
            worktree_root / "paper" / "paper_line_state.json",
            paper_line_state,
        )
    if figure_catalog is not None:
        dump_json(
            worktree_root / "paper" / "figures" / "figure_catalog.json",
            figure_catalog,
        )
    elif include_submission_authority_inputs:
        dump_json(
            worktree_root / "paper" / "figures" / "figure_catalog.json",
            {
                "schema_version": 1,
                "figures": [
                    {
                        "figure_id": f"F{index}",
                        "paper_role": "main_text",
                        "manuscript_status": "locked_main_text_evidence",
                    }
                    for index in range(1, 5)
                ],
            },
        )
    if table_catalog is not None:
        dump_json(
            worktree_root / "paper" / "tables" / "table_catalog.json",
            table_catalog,
        )
    elif include_submission_authority_inputs:
        dump_json(
            worktree_root / "paper" / "tables" / "table_catalog.json",
            {
                "schema_version": 1,
                "tables": [],
            },
        )
    if submission_checklist is not None:
        dump_json(
            worktree_root / "paper" / "review" / "submission_checklist.json",
            submission_checklist,
        )
    if include_submission_minimal:
        (worktree_root / "paper" / "submission_minimal").mkdir(parents=True, exist_ok=True)
        (worktree_root / "paper" / "submission_minimal" / "manuscript.docx").write_text("docx", encoding="utf-8")
        (worktree_root / "paper" / "submission_minimal" / "paper.pdf").write_text("%PDF", encoding="utf-8")
        if include_submission_authority_inputs:
            (worktree_root / "paper" / "submission_minimal" / "references.bib").write_text(
                "@article{ref1,title={Ref}}\n",
                encoding="utf-8",
            )
        dump_json(
            worktree_root / "paper" / "submission_minimal" / "submission_manifest.json",
            {
                "schema_version": 1,
                "publication_profile": "general_medical_journal",
                "manuscript": {
                    "docx_path": "paper/submission_minimal/manuscript.docx",
                    "pdf_path": "paper/submission_minimal/paper.pdf",
                },
            },
        )
    if include_unmanaged_submission_surface:
        (worktree_root / "paper" / "submission_pituitary").mkdir(parents=True, exist_ok=True)
        dump_json(
            worktree_root / "paper" / "submission_pituitary" / "submission_manifest.json",
            (
                {
                    "schema_version": 1,
                    "surface_status": "archived_reference_only",
                    "archive_reason": "Retained only as a historical journal-target package.",
                    "active_managed_submission_manifest_path": "paper/submission_minimal/submission_manifest.json",
                }
                if archive_legacy_submission_surface
                else {}
            ),
        )
    if include_current_medical_publication_surface_report:
        surface_report = {
            "status": medical_publication_surface_status,
            "blockers": [] if medical_publication_surface_status == "clear" else ["claim_evidence_map_missing_or_incomplete"],
        }
        if medical_publication_surface_report:
            surface_report.update(medical_publication_surface_report)
        dump_json(
            quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
            surface_report,
        )
    if manuscript_files:
        for relpath, body in manuscript_files.items():
            target = worktree_root / "paper" / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

    return quest_root


def write_primary_target(paper_root: Path) -> None:
    dump_json(
        paper_root / "submission_targets.resolved.json",
        {
            "schema_version": 1,
            "decision_kind": "journal_selected",
            "decision_source": "controller_explicit",
            "primary_target": {
                "journal_name": "Rheumatology International",
                "publication_profile": "general_medical_journal",
                "citation_style": "AMA",
                "official_guidelines_url": "https://example.org/ri-guide",
                "package_required": True,
                "resolution_status": "resolved",
            },
            "blocked_items": [],
        },
    )


def write_journal_requirements_snapshot(study_root: Path) -> None:
    dump_json(
        study_root / "paper" / "journal_requirements" / "rheumatology-international" / "requirements.json",
        {
            "schema_version": 1,
            "generated_at": "2026-04-19T02:00:00+00:00",
            "journal_name": "Rheumatology International",
            "journal_slug": "rheumatology-international",
            "official_guidelines_url": "https://example.org/ri-guide",
            "publication_profile": "general_medical_journal",
            "abstract_word_cap": 250,
            "title_page_required": True,
        },
    )
    write_text(
        study_root / "paper" / "journal_requirements" / "rheumatology-international" / "requirements.md",
        "# Requirements\n",
    )






























































































































