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


def test_build_gate_report_exposes_submission_minimal_status_when_present(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_root"].endswith("/paper")
    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"].endswith("paper/submission_minimal/submission_manifest.json")
    assert report["paper_bundle_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_present"] is True
    assert report["submission_minimal_docx_present"] is True
    assert report["submission_minimal_pdf_present"] is True


def test_build_gate_report_uses_authoritative_source_markdown_path_for_submission_surface_qc(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        include_submission_authority_inputs=False,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "manuscript_status": "main_text",
                }
            ],
        },
    )
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    worktree_paper_root = worktree_root / "paper"
    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        worktree_paper_root / "paper_bundle_manifest.json",
        projected_paper_root / "paper_bundle_manifest.json",
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_root": str(worktree_paper_root),
        },
    )

    submission_manifest_path = worktree_paper_root / "submission_minimal" / "submission_manifest.json"
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload["manuscript"]["source_markdown_path"] = "paper/submission_minimal/manuscript_submission.md"
    submission_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(worktree_paper_root / "submission_minimal" / "manuscript_submission.md", "# authoritative\n")
    write_text(projected_paper_root / "submission_minimal" / "manuscript_submission.md", "# projected copy\n")

    captured: dict[str, Path] = {}

    def fake_build_submission_manuscript_surface_qc(
        *,
        publication_profile: str,
        source_markdown_path: Path,
        docx_path: Path,
        pdf_path: Path,
        expected_main_figure_count: int,
    ) -> dict[str, object]:
        captured["source_markdown_path"] = source_markdown_path
        captured["docx_path"] = docx_path
        captured["pdf_path"] = pdf_path
        assert publication_profile == "general_medical_journal"
        assert expected_main_figure_count == 1
        return {
            "qc_profile": "submission_manuscript_surface",
            "status": "pass",
            "failures": [],
        }

    monkeypatch.setattr(
        module.submission_minimal,
        "build_submission_manuscript_surface_qc",
        fake_build_submission_manuscript_surface_qc,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"] == str(projected_paper_root / "paper_bundle_manifest.json")
    assert captured["source_markdown_path"] == worktree_paper_root / "submission_minimal" / "manuscript_submission.md"
    assert captured["docx_path"] == worktree_paper_root / "submission_minimal" / "manuscript.docx"
    assert captured["pdf_path"] == worktree_paper_root / "submission_minimal" / "paper.pdf"


def test_build_gate_report_marks_submission_minimal_missing_when_absent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"] is None
    assert report["submission_minimal_present"] is False
    assert report["submission_minimal_docx_present"] is False
    assert report["submission_minimal_pdf_present"] is False


def test_build_gate_report_reports_missing_journal_requirements_for_primary_target(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_primary_target(paper_root)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["primary_journal_target"]["journal_slug"] == "rheumatology-international"
    assert report["journal_requirements_status"] == "missing"
    assert "missing_journal_requirements" in report["blockers"]


def test_build_gate_report_reports_missing_journal_package_when_requirements_exist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    write_primary_target(paper_root)
    write_journal_requirements_snapshot(study_root)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["journal_requirements_status"] == "resolved"
    assert report["journal_package_status"] == "missing"
    assert "missing_journal_package" in report["blockers"]


def test_build_gate_state_uses_latest_parseable_gate_report_when_newer_report_is_malformed(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    reports_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    older_report = reports_root / "2026-04-17T000000Z.json"
    newer_report = reports_root / "2026-04-17T000001Z.json"

    dump_json(
        older_report,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "clear",
            "controller_stage_note": "older parseable report",
        },
    )
    newer_report.parent.mkdir(parents=True, exist_ok=True)
    newer_report.write_text(
        '{"schema_version": 1, "status": "clear"}\n{"schema_version": 1, "status": "blocked"}\n',
        encoding="utf-8",
    )
    os.utime(older_report, (1, 1))
    os.utime(newer_report, (2, 2))

    state = module.build_gate_state(quest_root)

    assert state.latest_gate_path == older_report
    assert state.latest_gate == {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-04-17T00:00:00+00:00",
        "status": "clear",
        "controller_stage_note": "older parseable report",
    }


def test_build_gate_report_supports_finalize_only_paper_bundle_without_main_result(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "paper_bundle"
    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["paper_root"].endswith("/paper")
    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"].endswith("paper/submission_minimal/submission_manifest.json")
    assert report["paper_bundle_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_present"] is True
    assert report["submission_minimal_docx_present"] is True
    assert report["submission_minimal_pdf_present"] is True
    assert report["run_id"] is None
    assert report["headline_metrics"] == {}
    assert report["results_summary"] == "compile report summary"
    assert report["supervisor_phase"] == "bundle_stage_ready"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["phase_owner"] == "publication_gate"


def test_build_gate_report_clears_stale_paper_line_blockers_when_bundle_stage_reopens(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        paper_line_state={
            "paper_root": str(
                (
                    tmp_path
                    / "runtime"
                    / "quests"
                    / "002-early-residual-risk"
                    / ".ds"
                    / "worktrees"
                    / "paper-run-1"
                    / "paper"
                ).resolve()
            ),
            "recommended_action": "branch_upstream_controller_contract_durability_fix",
            "blocking_reasons": [
                "The latest hard-control message supersedes the earlier reopen-write snapshot."
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)
    markdown = module.render_gate_markdown(report)

    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["current_required_action"] == "continue_bundle_stage"
    assert report["paper_line_recommended_action"] == "continue_per_gate"
    assert report["paper_line_blocking_reasons"] == []
    assert "Paper-Line Scientific Blockers" not in markdown
    assert "branch_upstream_controller_contract_durability_fix" not in markdown


def test_build_gate_report_blocks_finalize_only_bundle_without_current_surface_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "paper_bundle"
    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "missing_current_medical_publication_surface_report" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"


def test_build_gate_report_allows_handoff_ready_bundle_with_non_scientific_pageproof_gap(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "display_materialized_draft_bundle_not_submission_ready",
            "checks": [
                {"key": "claim_evidence_alignment", "status": "pass"},
                {"key": "proofing_present", "status": "pass"},
            ],
            "blocking_items": [
                {
                    "key": "full_manuscript_pageproof",
                    "notes": "Rendered page proof is still unavailable.",
                }
            ],
            "handoff_ready": True,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "paper_bundle"
    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["submission_minimal_present"] is False
    assert report["submission_checklist_handoff_ready"] is True
    assert report["non_scientific_handoff_gaps"] == ["full_manuscript_pageproof"]
    assert report["blockers"] == []
    assert report["supervisor_phase"] == "bundle_stage_ready"
    assert report["current_required_action"] == "continue_bundle_stage"


def test_build_gate_report_keeps_handoff_ready_bundle_blocked_for_unknown_submission_gap(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "draft_bundle_with_unresolved_method_gap",
            "blocking_items": [
                {
                    "key": "methods_completeness",
                    "notes": "Methods section still misses a required implementation detail.",
                }
            ],
            "handoff_ready": True,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["submission_checklist_handoff_ready"] is True
    assert report["submission_checklist_unclassified_blocking_items"] == ["methods_completeness"]
    assert "submission_checklist_contains_unclassified_blocking_items" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"


def test_build_gate_report_marks_draft_handoff_sync_missing_when_bundle_is_handoff_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "display_materialized_slice_handoff_not_submission_ready",
            "blocking_items": [
                {
                    "key": "placeholder_heavy_branch_local_draft",
                    "notes": "Current draft is still placeholder-heavy.",
                }
            ],
            "handoff_ready": True,
        },
    )
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": True,
            "status": "missing",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": None,
            "missing_source_paths": [],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["draft_handoff_delivery_required"] is True
    assert report["draft_handoff_delivery_status"] == "missing"
    assert report["draft_handoff_delivery_manifest_path"] is None


def test_run_controller_syncs_draft_handoff_surface_when_missing(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "display_materialized_slice_handoff_not_submission_ready",
            "blocking_items": [
                {
                    "key": "placeholder_heavy_branch_local_draft",
                    "notes": "Current draft is still placeholder-heavy.",
                }
            ],
            "handoff_ready": True,
        },
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "missing",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "delivery_manifest_path": None,
            },
            {
                "applicable": True,
                "status": "current",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            },
        ]
    )
    sync_calls: list[tuple[str, str]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: next(describe_calls),
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": None,
            "missing_source_paths": [],
        },
    )

    def fake_sync(*, paper_root: Path, stage: str, publication_profile: str = "general_medical_journal", promote_to_final: bool = False) -> dict[str, object]:
        sync_calls.append((stage, publication_profile))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("draft_handoff", "general_medical_journal")]
    assert result["draft_handoff_delivery_status"] == "current"
    assert result["draft_handoff_delivery_sync"] == {
        "stage": "draft_handoff",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }


def test_build_gate_report_blocks_finalize_only_bundle_when_surface_report_is_stale(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    report_path = quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    bundle_manifest_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    )
    os.utime(report_path, (bundle_manifest_path.stat().st_mtime - 10, bundle_manifest_path.stat().st_mtime - 10))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_current_medical_publication_surface_report" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"


def test_build_gate_report_ignores_stale_blocked_surface_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="blocked",
    )
    report_path = quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    bundle_manifest_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    )
    os.utime(report_path, (bundle_manifest_path.stat().st_mtime - 10, bundle_manifest_path.stat().st_mtime - 10))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_current_medical_publication_surface_report" in report["blockers"]
    assert "medical_publication_surface_blocked" not in report["blockers"]
    assert "claim_evidence_consistency_failed" not in report["blockers"]
    assert report["medical_publication_surface_current"] is False
    assert report["medical_publication_surface_named_blockers"] == []
    assert report["medical_publication_surface_route_back_recommendation"] is None


def test_build_gate_report_keeps_bundle_stage_when_only_submission_minimal_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["blockers"] == ["missing_submission_minimal"]
    assert report["supervisor_phase"] == "bundle_stage_blocked"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["current_required_action"] == "complete_bundle_stage"
    assert report["medical_publication_surface_named_blockers"] == []
    assert report["medical_publication_surface_route_back_recommendation"] is None
    assert report["controller_stage_note"] == "bundle-stage blockers are now on the critical path for this paper line"


def test_build_gate_report_blocks_bundle_when_paper_line_requires_supplementary_completion(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        paper_line_state={
            "paper_root": str(
                (
                    tmp_path
                    / "runtime"
                    / "quests"
                    / "002-early-residual-risk"
                    / ".ds"
                    / "worktrees"
                    / "paper-run-1"
                    / "paper"
                ).resolve()
            ),
            "open_supplementary_count": 2,
            "recommended_action": "complete_required_supplementary",
            "blocking_reasons": ["paper-facing supplementary slices are still pending"],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "paper_line_required_supplementary_pending" in report["blockers"]
    assert report["paper_line_open_supplementary_count"] == 2
    assert report["paper_line_recommended_action"] == "complete_required_supplementary"
    assert report["paper_line_blocking_reasons"] == ["paper-facing supplementary slices are still pending"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"


def test_build_gate_report_blocks_bundle_when_active_figure_floor_is_unmet(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F2", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F3", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {
                    "figure_id": "F4",
                    "paper_role": "appendix_legacy_inactive",
                    "manuscript_status": "appendix_context_only",
                },
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "submission_grade_active_figure_floor_unmet" in report["blockers"]
    assert report["active_manuscript_figure_count"] == 3
    assert report["submission_grade_min_active_figures"] == 4
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"


def test_build_gate_report_surfaces_prebundle_figure_floor_pending_from_main_result(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=True,
        runtime_status="running",
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "main_result"
    assert report["allow_write"] is False
    assert report["active_manuscript_figure_count"] == 1
    assert report["prebundle_display_floor_pending"] is True
    assert report["prebundle_display_floor_gap"] == 3
    assert report["prebundle_display_advisories"] == ["submission_grade_active_figure_floor_unmet"]


def test_build_gate_report_unlocks_write_stage_when_latest_clear_gate_is_current(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=True,
        runtime_status="running",
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
            ],
        },
    )
    main_result_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "experiments"
        / "main"
        / "run-1"
        / "RESULT.json"
    )
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    dump_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "clear",
            "allow_write": False,
            "blockers": [],
        },
    )
    os.utime(main_result_path, (1, 1))
    os.utime(surface_report_path, (2, 2))
    os.utime(gate_report_path, (3, 3))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "main_result"
    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["latest_gate_path"] == str(gate_report_path)
    assert report["supervisor_phase"] == "write_stage_ready"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["current_required_action"] == "continue_write_stage"
    assert report["prebundle_display_floor_pending"] is True
    assert report["prebundle_display_floor_gap"] == 3
    assert report["prebundle_display_advisories"] == ["submission_grade_active_figure_floor_unmet"]


def test_build_gate_state_prefers_authoritative_worktree_paper_root_when_bundle_manifest_is_projected(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(worktree_paper_root / "paper_bundle_manifest.json", projected_paper_root / "paper_bundle_manifest.json")
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == worktree_paper_root.resolve()


def test_build_gate_state_prefers_paper_line_authority_root_when_no_main_result_exists(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(worktree_paper_root / "paper_bundle_manifest.json", projected_paper_root / "paper_bundle_manifest.json")
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(worktree_paper_root.resolve()),
            "paper_branch": "paper/main",
        },
    )
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == worktree_paper_root.resolve()


def test_build_gate_state_prefers_paper_line_authority_root_over_run_worktree_paper(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    run_worktree_root = quest_root / ".ds" / "worktrees" / "run-main-1"
    run_result_path = run_worktree_root / "experiments" / "main" / "run-1" / "RESULT.json"
    run_worktree_paper_root = run_worktree_root / "paper"

    dump_json(
        run_result_path,
        {
            "quest_id": "002-early-residual-risk",
            "run_id": "run-1",
            "worktree_root": str(run_worktree_root.resolve()),
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
    (paper_worktree_root / "experiments" / "main" / "run-1" / "RESULT.json").unlink()
    (run_worktree_paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (run_worktree_paper_root / "draft.md").write_text("paper-facing placeholder", encoding="utf-8")

    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paper_worktree_root / "paper" / "paper_bundle_manifest.json", projected_paper_root / "paper_bundle_manifest.json")
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str((paper_worktree_root / "paper").resolve()),
            "paper_branch": "paper/main",
        },
    )

    state = module.build_gate_state(quest_root)

    assert state.paper_root == (paper_worktree_root / "paper").resolve()


def test_build_gate_state_prefers_bundle_authority_worktree_when_projected_line_state_switches_to_analysis_slice(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"

    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(authoritative_paper_root / "paper_bundle_manifest.json", projected_manifest)
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(analysis_paper_root.resolve()),
            "paper_branch": "analysis/paper-line-paper-main-outline-001-run/analysis-12bdab30-authority-root-delivery-alignment",
        },
    )
    (analysis_paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (analysis_paper_root / "draft.md").write_text("analysis slice mirror", encoding="utf-8")
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_bundle_manifest_path == projected_manifest
    assert state.paper_root == authoritative_paper_root.resolve()
    assert state.submission_minimal_manifest_path == authoritative_paper_root / "submission_minimal" / "submission_manifest.json"
    assert state.submission_minimal_docx_present is True
    assert state.submission_minimal_pdf_present is True


def test_build_gate_state_reads_authoritative_paper_line_state_when_projected_manifest_is_selected(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
    )
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"

    dump_json(
        authoritative_paper_root / "paper_line_state.json",
        {
            "paper_root": str(authoritative_paper_root.resolve()),
            "paper_branch": "paper/main",
            "open_supplementary_count": 0,
            "recommended_action": "continue_bundle_stage",
            "blocking_reasons": [],
        },
    )
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(authoritative_paper_root / "paper_bundle_manifest.json", projected_manifest)
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(analysis_paper_root.resolve()),
            "paper_branch": "analysis/paper-line-paper-main-outline-001-run/analysis-faea0014-live-submission-package-projection-recovery",
            "open_supplementary_count": 1,
            "recommended_action": "complete_required_supplementary",
            "blocking_reasons": ["analysis mirror still thinks a slice is open"],
        },
    )
    (analysis_paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (analysis_paper_root / "draft.md").write_text("analysis slice mirror", encoding="utf-8")
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == projected_manifest
    assert state.paper_root == authoritative_paper_root.resolve()
    assert state.paper_line_state_path == (authoritative_paper_root / "paper_line_state.json").resolve()
    assert state.paper_line_state == {
        "paper_root": str(authoritative_paper_root.resolve()),
        "paper_branch": "paper/main",
        "open_supplementary_count": 0,
        "recommended_action": "continue_bundle_stage",
        "blocking_reasons": [],
    }
    assert report["paper_line_open_supplementary_count"] == 0
    assert "paper_line_required_supplementary_pending" not in report["blockers"]


def test_build_gate_report_marks_stale_study_delivery_mirror_when_authority_package_disappears(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "current_submission_source_missing",
            "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "missing_source_paths": [
                "/tmp/runtime/quests/002/paper/submission_minimal/submission_manifest.json",
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "missing_submission_minimal" in report["blockers"]
    assert "stale_study_delivery_mirror" in report["blockers"]
    assert report["study_delivery_status"] == "stale_source_missing"
    assert report["study_delivery_stale_reason"] == "current_submission_source_missing"
    assert report["study_delivery_manifest_path"] == "/tmp/studies/002/manuscript/delivery_manifest.json"
    assert report["supervisor_phase"] == "bundle_stage_blocked"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["current_required_action"] == "complete_bundle_stage"


def test_build_gate_report_blocks_stale_submission_minimal_authority_when_paper_inputs_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        figure_catalog={"schema_version": 1, "figures": []},
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(paper_root / "build" / "review_manuscript.md", "# Review Manuscript\n\nOriginal authority draft.\n")
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [],
        },
    )
    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Review Manuscript\n\nAuthority draft updated after submission package generation.\n",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["submission_minimal_authority_status"] == "stale_source_changed"
    assert report["submission_minimal_authority_stale_reason"] == "submission_source_newer_than_manifest"
    assert "stale_submission_minimal_authority" in report["blockers"]


def test_build_gate_report_marks_bundle_tasks_downstream_when_publication_anchor_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="running",
    )
    paper_bundle_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "paper_bundle_manifest.json"
    )
    paper_bundle_manifest_path.unlink()

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "missing"
    assert report["allow_write"] is False
    assert "missing_publication_anchor" in report["blockers"]
    assert report["supervisor_phase"] == "scientific_anchor_missing"
    assert report["phase_owner"] == "publication_gate"
    assert report["upstream_scientific_anchor_ready"] is False
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert report["deferred_downstream_actions"] == []


def test_build_gate_report_marks_bundle_tasks_downstream_when_post_main_gate_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "main_result"
    assert report["allow_write"] is False
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["phase_owner"] == "publication_gate"
    assert report["upstream_scientific_anchor_ready"] is True
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert report["deferred_downstream_actions"] == []


def test_run_controller_handles_finalize_only_bundle_blockers_without_main_metrics(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert "missing_submission_minimal" in result["blockers"]
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1
    assert "missing_submission_minimal" in queue["pending"][0]["content"]


def test_run_controller_materializes_stable_publication_eval_when_apply_clear(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    state = module.build_gate_state(quest_root)
    assert state.paper_root is not None

    monkeypatch.setattr(
        module,
        "build_gate_report",
        lambda gate_state: {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-18T18:12:13+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(gate_state.paper_root / "paper_bundle_manifest.json"),
            "quest_id": "002-early-residual-risk",
            "run_id": "paper-run-1",
            "main_result_path": None,
            "paper_root": str(gate_state.paper_root),
            "compile_report_path": str(gate_state.paper_root / "build" / "compile_report.json"),
            "latest_gate_path": str(
                quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
            ),
            "medical_publication_surface_report_path": str(
                quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
            ),
            "medical_publication_surface_current": True,
            "allow_write": True,
            "recommended_action": "continue_per_gate",
            "status": "clear",
            "blockers": [],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": str(gate_state.paper_root / "paper_bundle_manifest.json"),
            "submission_checklist_path": None,
            "submission_checklist_present": False,
            "submission_checklist_overall_status": None,
            "submission_checklist_handoff_ready": False,
            "submission_checklist_blocking_items": [],
            "submission_checklist_unclassified_blocking_items": [],
            "non_scientific_handoff_gaps": [],
            "closure_bundle_ready": True,
            "submission_minimal_manifest_path": str(
                gate_state.paper_root / "submission_minimal" / "submission_manifest.json"
            ),
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "study_delivery_manifest_path": None,
            "study_delivery_current_package_root": None,
            "study_delivery_current_package_zip": None,
            "study_delivery_missing_source_paths": [],
            "draft_handoff_delivery_required": False,
            "draft_handoff_delivery_status": "current",
            "draft_handoff_delivery_manifest_path": None,
            "draft_handoff_current_package_root": None,
            "draft_handoff_current_package_zip": None,
            "paper_line_open_supplementary_count": 0,
            "paper_line_recommended_action": "continue_per_gate",
            "paper_line_blocking_reasons": [],
            "active_manuscript_figure_count": 5,
            "submission_grade_min_active_figures": 4,
            "prebundle_display_floor_pending": False,
            "prebundle_display_floor_gap": None,
            "prebundle_display_advisories": [],
            "medical_publication_surface_status": "clear",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "bundle-stage work is unlocked and can proceed on the current line",
            "conclusion": "bundle-stage work is unlocked and can proceed on the current line",
            "controller_note": "The controller does not decide scientific publishability by itself.",
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "Publication gate is clear and the current line can continue.",
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert result["status"] == "clear"
    latest_eval_path = (
        tmp_path
        / "studies"
        / "002-early-residual-risk"
        / "artifacts"
        / "publication_eval"
        / "latest.json"
    )
    assert latest_eval_path.is_file()
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert payload["emitted_at"] == "2026-04-18T18:12:13+00:00"
    assert payload["verdict"]["overall_verdict"] == "promising"
    assert payload["recommended_actions"][0]["action_type"] == "bounded_analysis"
    assert payload["runtime_context_refs"]["main_result_ref"] == str(
        quest_root / "artifacts" / "results" / "main_result.json"
    )


def test_run_controller_prefers_finalize_route_when_bundle_stage_is_ready_alongside_main_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=True,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F2", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F3", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F4", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
            ],
        },
    )
    main_result_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "experiments"
        / "main"
        / "run-1"
        / "RESULT.json"
    )
    bundle_manifest_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    dump_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "clear",
            "allow_write": False,
            "blockers": [],
        },
    )
    os.utime(main_result_path, (1, 1))
    os.utime(bundle_manifest_path, (2, 2))
    os.utime(surface_report_path, (3, 3))
    os.utime(gate_report_path, (4, 4))

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert result["status"] == "clear"
    assert result["allow_write"] is True
    assert result["supervisor_phase"] == "bundle_stage_ready"
    assert result["current_required_action"] == "continue_bundle_stage"
    latest_eval_path = (
        tmp_path
        / "studies"
        / "002-early-residual-risk"
        / "artifacts"
        / "publication_eval"
        / "latest.json"
    )
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert payload["recommended_actions"][0]["action_type"] == "continue_same_line"
    assert payload["recommended_actions"][0]["route_target"] == "finalize"


def test_run_controller_materializes_stale_study_delivery_notice_when_apply_enabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "current_submission_source_missing",
            "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "missing_source_paths": [
                "/tmp/runtime/quests/002/paper/submission_minimal/submission_manifest.json",
            ],
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: calls.append(kwargs)
        or {
            "status": "stale_source_missing",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert len(calls) == 1
    assert calls[0]["stale_reason"] == "current_submission_source_missing"
    assert calls[0]["missing_source_paths"] == [
        "/tmp/runtime/quests/002/paper/submission_minimal/submission_manifest.json",
    ]
    assert result["study_delivery_stale_sync"]["status"] == "stale_source_missing"


def test_run_controller_resyncs_delivery_when_only_current_package_projection_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_projection_missing",
                "stale_reason": "delivery_projection_missing",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("projection-missing should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["study_delivery_stale_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }


def test_run_controller_unlocks_write_after_main_result_stale_delivery_resync(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=True,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    main_result_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "experiments"
        / "main"
        / "run-1"
        / "RESULT.json"
    )
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    dump_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_study_delivery_mirror"],
        },
    )
    os.utime(main_result_path, (1, 1))
    os.utime(gate_report_path, (2, 2))

    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_projection_missing",
                "stale_reason": "delivery_projection_missing",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("projection-missing should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["allow_write"] is True
    assert result["supervisor_phase"] == "bundle_stage_ready"
    assert result["current_required_action"] == "continue_bundle_stage"


def test_run_controller_resyncs_delivery_when_authority_package_changes_without_root_change(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_source_changed",
                "stale_reason": "delivery_manifest_source_changed",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("source-changed should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["study_delivery_stale_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }

def test_run_controller_resyncs_delivery_when_authority_package_source_mismatch_is_reported(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_source_mismatch",
                "stale_reason": "delivery_manifest_source_mismatch",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("source-mismatch should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["study_delivery_stale_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }


def test_run_controller_refreshes_stale_journal_package_when_source_submission_manifest_advances(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    journal_package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    requirements_module = importlib.import_module("med_autoscience.journal_requirements")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    journal_slug = "rheumatology-international"

    dump_json(
        paper_root / "submission_targets.resolved.json",
        {
            "schema_version": 1,
            "updated_at": "2026-04-06T00:00:00+00:00",
            "decision_kind": "journal_selected",
            "decision_source": "controller_explicit",
            "primary_target": {
                "journal_name": "Rheumatology International",
                "journal_slug": journal_slug,
                "publication_profile": "general_medical_journal",
                "official_guidelines_url": "https://example.org/ri-guide",
                "package_required": True,
                "resolution_status": "resolved",
            },
            "blocked_items": [],
        },
    )
    requirements_module.write_journal_requirements(
        study_root=study_root,
        requirements=requirements_module.JournalRequirements(
            journal_name="Rheumatology International",
            journal_slug=journal_slug,
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
    journal_package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug=journal_slug,
        publication_profile="general_medical_journal",
    )
    source_manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    source_manifest_payload = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest_payload["generated_at"] = "2026-04-06T00:00:01+00:00"
    source_manifest_path.write_text(
        json.dumps(source_manifest_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": True,
            "status": "current",
            "stale_reason": None,
            "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            "missing_source_paths": [],
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert result["status"] == "clear"
    assert result["allow_write"] is True
    assert result["current_required_action"] == "continue_bundle_stage"
    assert result["journal_package_sync"] == {
        "status": "materialized",
        "study_root": str(study_root.resolve()),
        "paper_root": str(paper_root.resolve()),
        "journal_slug": journal_slug,
        "journal_name": "Rheumatology International",
        "publication_profile": "general_medical_journal",
        "package_root": str((study_root / "submission_packages" / journal_slug).resolve()),
        "submission_manifest_path": str((study_root / "submission_packages" / journal_slug / "submission_manifest.json").resolve()),
        "zip_path": str((study_root / "submission_packages" / journal_slug / f"{journal_slug}_submission_package.zip").resolve()),
        "package_status": "current",
    }
def test_build_gate_report_blocks_unmanaged_submission_surface_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_unmanaged_submission_surface=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "unmanaged_submission_surface_present" in report["blockers"]
    assert report["unmanaged_submission_surface_roots"] == [
        str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_pituitary").resolve())
    ]


def test_build_gate_report_accepts_archived_reference_only_legacy_submission_surface(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_unmanaged_submission_surface=True,
        archive_legacy_submission_surface=True,
        include_current_medical_publication_surface_report=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert report["unmanaged_submission_surface_roots"] == []
    assert report["archived_submission_surface_roots"] == [
        str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_pituitary").resolve())
    ]


def test_build_gate_report_blocks_archived_reference_only_surface_when_target_manifest_is_outside_current_paper(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_unmanaged_submission_surface=True,
        archive_legacy_submission_surface=True,
    )
    external_manifest = tmp_path / "external" / "paper" / "submission_minimal" / "submission_manifest.json"
    dump_json(
        external_manifest,
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    archived_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "submission_pituitary"
        / "submission_manifest.json"
    )
    payload = json.loads(archived_manifest_path.read_text(encoding="utf-8"))
    payload["active_managed_submission_manifest_path"] = str(external_manifest.resolve())
    dump_json(archived_manifest_path, payload)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "unmanaged_submission_surface_present" in report["blockers"]
    assert report["archived_submission_surface_roots"] == []
    assert report["unmanaged_submission_surface_roots"] == [
        str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_pituitary").resolve())
    ]


def test_build_gate_report_blocks_forbidden_manuscript_terminology(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "build/review_manuscript.md": "Methods: we analyzed the locked v2026-03-31 dataset.\n",
            "submission_minimal/tables/Table1.md": (
                "Note: the paper-facing mainline analysis used the workspace cohort and "
                "the 2024-06-30 follow-up freeze.\n"
            ),
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terminology" in report["blockers"]
    violations = report["manuscript_terminology_violations"]
    assert any(
        item["path"].endswith("build/review_manuscript.md")
        and item["label"] == "locked_dataset_version_label"
        and item["match"] == "locked v2026-03-31"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "internal_editorial_label"
        and item["match"] == "paper-facing"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "internal_editorial_label"
        and item["match"] == "mainline"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "workspace_cohort_label"
        and item["match"] == "workspace cohort"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "followup_freeze_label"
        and item["match"] == "follow-up freeze"
        for item in violations
    )


def test_build_gate_report_blocks_submission_surface_qc_failures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        figure_catalog={
            "schema_version": 1,
            "figures": [],
        },
    )
    submission_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "submission_minimal"
        / "submission_manifest.json"
    )
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload["figures"] = [
        {
            "figure_id": "GA1",
            "template_id": "submission_graphical_abstract",
            "qc_profile": "submission_graphical_abstract",
            "qc_result": {
                "status": "fail",
                "qc_profile": "submission_graphical_abstract",
                "failure_reason": "panel_text_out_of_panel",
                "audit_classes": ["layout"],
            },
        }
    ]
    submission_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "submission_surface_qc_failure_present" in report["blockers"]
    assert report["submission_surface_qc_failures"] == [
        {
            "collection": "figures",
            "item_id": "GA1",
            "descriptor": "submission_graphical_abstract",
            "qc_profile": "submission_graphical_abstract",
            "failure_reason": "panel_text_out_of_panel",
            "audit_classes": ["layout"],
        }
    ]


def test_build_gate_report_blocks_submission_manuscript_surface_without_embedded_figures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        include_submission_authority_inputs=False,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "manuscript_status": "main_text",
                }
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "submission_surface_qc_failure_present" in report["blockers"]
    failure_reasons = {item["failure_reason"] for item in report["submission_surface_qc_failures"]}
    assert "submission_source_markdown_missing" in failure_reasons
    assert "submission_docx_missing_embedded_figures" in failure_reasons
    assert "submission_pdf_missing_embedded_figures" in failure_reasons


def test_build_gate_report_infers_general_profile_for_legacy_submission_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                }
            ],
        },
    )
    submission_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "submission_minimal"
        / "submission_manifest.json"
    )
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload.pop("publication_profile", None)
    payload["manuscript"] = {
        "docx_path": "paper/submission_minimal/manuscript.docx",
        "pdf_path": "paper/submission_minimal/paper.pdf",
    }
    submission_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    failure_reasons = {item["failure_reason"] for item in report["submission_surface_qc_failures"]}
    assert "submission_source_markdown_missing" in failure_reasons
    assert "submission_docx_missing_embedded_figures" in failure_reasons
    assert "submission_pdf_missing_embedded_figures" in failure_reasons


def test_build_gate_report_inherits_blocked_medical_publication_surface_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
        {
            "status": "blocked",
            "blockers": ["figure_catalog_missing_or_incomplete"],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["medical_publication_surface_status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert report["medical_publication_surface_report_path"].endswith(
        "artifacts/reports/medical_publication_surface/2026-04-05T15:29:32Z.json"
    )

def test_build_gate_report_blocks_when_study_charter_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    (study_root / "artifacts" / "controller" / "study_charter.json").unlink()

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["charter_contract_linkage_status"] == "study_charter_missing"
    assert "study_charter_missing" in report["blockers"]
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert "stable study charter artifact is missing" in report["controller_stage_note"]


def test_build_gate_report_blocks_when_study_charter_is_invalid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    (study_root / "artifacts" / "controller" / "study_charter.json").write_text("{invalid\n", encoding="utf-8")

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["charter_contract_linkage_status"] == "study_charter_invalid"
    assert "study_charter_invalid" in report["blockers"]
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert "stable study charter artifact is invalid" in report["controller_stage_note"]
def test_build_gate_report_maps_surface_signals_to_named_controller_blockers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": [
                "review_ledger_missing_or_incomplete",
                "claim_evidence_map_missing_or_incomplete",
                "public_evidence_decisions_missing_or_incomplete",
            ],
            "review_ledger_valid": False,
            "claim_evidence_map_valid": False,
            "evidence_ledger_valid": False,
            "medical_story_contract_valid": False,
            "public_evidence_decision_count": 0,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert "reviewer_first_concerns_unresolved" in report["blockers"]
    assert "claim_evidence_consistency_failed" in report["blockers"]
    assert "submission_hardening_incomplete" in report["blockers"]
    assert report["medical_publication_surface_named_blockers"] == [
        "reviewer_first_concerns_unresolved",
        "claim_evidence_consistency_failed",
        "submission_hardening_incomplete",
    ]
    assert report["medical_publication_surface_route_back_recommendation"] == "return_to_write"
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert "route back to `write` to close reviewer-first publication-surface concerns" in report[
        "controller_stage_note"
    ]
    assert "reviewer-first hardening" not in report["controller_stage_note"]


def test_build_gate_report_projects_surface_charter_expectation_gaps(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    evidence_gap_text = "External validation evidence package is durably archived for the manuscript route."
    review_gap_text = "Residual-risk framing is defended against calibration drift before submission."
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["charter_expectation_closure_incomplete"],
            "charter_expectation_closure_summary": {
                "status": "blocked",
                "blocking_items": [
                    {
                        "expectation_key": "minimum_sci_ready_evidence_package",
                        "expectation_text": evidence_gap_text,
                        "ledger_name": "evidence_ledger",
                        "ledger_path": "paper/evidence_ledger.json",
                        "contract_json_pointer": (
                            "/paper_quality_contract/evidence_expectations/minimum_sci_ready_evidence_package"
                        ),
                        "closure_status": "blocked",
                        "recorded": True,
                        "record_count": 1,
                        "blocker": True,
                    },
                    {
                        "expectation_key": "scientific_followup_questions",
                        "expectation_text": review_gap_text,
                        "ledger_name": "review_ledger",
                        "ledger_path": "paper/review/review_ledger.json",
                        "contract_json_pointer": (
                            "/paper_quality_contract/review_expectations/scientific_followup_questions"
                        ),
                        "closure_status": "open",
                        "recorded": True,
                        "record_count": 1,
                        "blocker": True,
                    },
                ],
            },
        },
    )

    report = module.build_gate_report(module.build_gate_state(quest_root))
    gaps = report["medical_publication_surface_expectation_gaps"]

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert "charter_expectation_closure_incomplete" in report["blockers"]
    assert report["medical_publication_surface_named_blockers"] == [
        "reviewer_first_concerns_unresolved",
        "claim_evidence_consistency_failed",
    ]
    assert report["medical_publication_surface_route_back_recommendation"] == "return_to_write"
    assert [gap["expectation_key"] for gap in gaps] == [
        "minimum_sci_ready_evidence_package",
        "scientific_followup_questions",
    ]
    assert {gap["expectation_text"] for gap in gaps} == {evidence_gap_text, review_gap_text}
    assert {gap["ledger_name"] for gap in gaps} == {"evidence_ledger", "review_ledger"}
    assert {gap["closure_status"] for gap in gaps} == {"blocked", "open"}
    assert {gap["contract_json_pointer"] for gap in gaps} == {
        "/paper_quality_contract/evidence_expectations/minimum_sci_ready_evidence_package",
        "/paper_quality_contract/review_expectations/scientific_followup_questions",
    }

    markdown = module.render_gate_markdown(report)
    assert "## Medical Publication Surface Expectation Gaps" in markdown
    assert evidence_gap_text in markdown
    assert review_gap_text in markdown
    assert "contract_json_pointer=`/paper_quality_contract/evidence_expectations/minimum_sci_ready_evidence_package`" in markdown
    assert "contract_json_pointer=`/paper_quality_contract/review_expectations/scientific_followup_questions`" in markdown
    assert "ledger=`evidence_ledger`" in markdown
    assert "ledger=`review_ledger`" in markdown


def test_build_gate_report_routes_each_surface_blocker_to_core_controller_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    reviewer_first_root = make_quest(
        tmp_path / "reviewer-first",
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["review_ledger_missing_or_incomplete"],
        },
    )
    reviewer_first_report = module.build_gate_report(module.build_gate_state(reviewer_first_root))

    assert reviewer_first_report["medical_publication_surface_named_blockers"] == [
        "reviewer_first_concerns_unresolved"
    ]
    assert reviewer_first_report["medical_publication_surface_route_back_recommendation"] == "return_to_write"
    assert "route back to `write` to close reviewer-first publication-surface concerns" in reviewer_first_report[
        "controller_stage_note"
    ]
    assert "reviewer-first hardening" not in reviewer_first_report["controller_stage_note"]

    claim_evidence_root = make_quest(
        tmp_path / "claim-evidence",
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["claim_evidence_map_missing_or_incomplete"],
        },
    )
    claim_evidence_report = module.build_gate_report(module.build_gate_state(claim_evidence_root))

    assert claim_evidence_report["medical_publication_surface_named_blockers"] == [
        "claim_evidence_consistency_failed"
    ]
    assert (
        claim_evidence_report["medical_publication_surface_route_back_recommendation"]
        == "return_to_analysis_campaign"
    )
    assert "route back to `analysis-campaign` to close claim-evidence consistency gaps" in claim_evidence_report[
        "controller_stage_note"
    ]
    assert "claim-evidence hardening" not in claim_evidence_report["controller_stage_note"]

    submission_hardening_root = make_quest(
        tmp_path / "submission-hardening",
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["public_evidence_decisions_missing_or_incomplete"],
        },
    )
    submission_hardening_report = module.build_gate_report(module.build_gate_state(submission_hardening_root))

    assert submission_hardening_report["medical_publication_surface_named_blockers"] == [
        "submission_hardening_incomplete"
    ]
    assert submission_hardening_report["medical_publication_surface_route_back_recommendation"] == "return_to_finalize"
    assert "route back to `finalize` to close submission-readiness gaps" in submission_hardening_report[
        "controller_stage_note"
    ]
    assert "submission hardening" not in submission_hardening_report["controller_stage_note"]


def test_build_gate_report_keeps_named_surface_blockers_clear_when_surface_is_clear(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "clear",
            "blockers": [],
            "review_ledger_valid": True,
            "claim_evidence_map_valid": True,
            "evidence_ledger_valid": True,
            "medical_story_contract_valid": True,
            "public_evidence_decision_count": 2,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "clear"
    assert "medical_publication_surface_blocked" not in report["blockers"]
    assert "reviewer_first_concerns_unresolved" not in report["blockers"]
    assert "claim_evidence_consistency_failed" not in report["blockers"]
    assert "submission_hardening_incomplete" not in report["blockers"]
    assert report["medical_publication_surface_named_blockers"] == []
    assert report["medical_publication_surface_route_back_recommendation"] is None


def test_build_gate_report_ignores_newer_surface_report_from_other_paper_line(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
    )
    current_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    anchor_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    dump_json(
        quest_root / "paper" / "paper_line_state.json",
        {
            "paper_root": str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper").resolve()),
        },
    )
    dump_json(
        current_report_path,
        {
            "paper_root": str((quest_root / "paper").resolve()),
            "status": "clear",
            "blockers": [],
        },
    )
    current_time = anchor_path.stat().st_mtime + 1
    os.utime(current_report_path, (current_time, current_time))

    stale_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:33Z.json"
    )
    dump_json(
        stale_report_path,
        {
            "paper_root": str(
                (quest_root / ".ds" / "worktrees" / "analysis-public-evidence-run-2" / "paper").resolve()
            ),
            "status": "blocked",
            "blockers": ["figure_catalog_missing_or_incomplete"],
        },
    )
    stale_time = current_time + 10
    os.utime(stale_report_path, (stale_time, stale_time))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["medical_publication_surface_status"] == "clear"
    assert report["medical_publication_surface_current"] is True
    assert "medical_publication_surface_blocked" not in report["blockers"]
    assert report["medical_publication_surface_report_path"].endswith(
        "artifacts/reports/medical_publication_surface/2026-04-05T15:29:32Z.json"
    )


def test_build_gate_report_falls_back_to_same_study_surface_report_when_paper_root_drifted(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
    )
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    drifted_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-2" / "paper"
    drifted_paper_root.mkdir(parents=True, exist_ok=True)
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:34Z.json"
    )
    dump_json(
        surface_report_path,
        {
            "study_root": str(study_root.resolve()),
            "paper_root": str(drifted_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )
    anchor_path = worktree_paper_root / "paper_bundle_manifest.json"
    fresh_time = anchor_path.stat().st_mtime + 10
    os.utime(surface_report_path, (fresh_time, fresh_time))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_root == worktree_paper_root.resolve()
    assert report["medical_publication_surface_report_path"] == str(surface_report_path)
    assert report["medical_publication_surface_status"] == "clear"
    assert report["medical_publication_surface_current"] is True
    assert "missing_current_medical_publication_surface_report" not in report["blockers"]
    assert "medical_publication_surface_blocked" not in report["blockers"]


def test_build_gate_report_uses_authoritative_bundle_manifest_for_surface_currentness_when_projected_mirror_is_newer(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
    )
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    analysis_paper_root.mkdir(parents=True, exist_ok=True)

    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "analysis/paper-drifted",
            "paper_root": str(analysis_paper_root.resolve()),
        },
    )
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    dump_json(
        surface_report_path,
        {
            "paper_root": str(authoritative_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )

    authoritative_manifest_path = authoritative_paper_root / "paper_bundle_manifest.json"
    projected_manifest_path = projected_paper_root / "paper_bundle_manifest.json"
    base_time = authoritative_manifest_path.stat().st_mtime + 10
    os.utime(authoritative_manifest_path, (base_time, base_time))
    os.utime(surface_report_path, (base_time + 10, base_time + 10))
    os.utime(projected_manifest_path, (base_time + 20, base_time + 20))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == projected_manifest_path
    assert state.paper_root == authoritative_paper_root.resolve()
    assert report["medical_publication_surface_report_path"] == str(surface_report_path)
    assert report["medical_publication_surface_current"] is True
    assert "missing_current_medical_publication_surface_report" not in report["blockers"]


def test_build_gate_report_prefers_runtime_paper_worktree_over_stale_projected_mirror(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    current_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    idea_worktree_root = quest_root / ".ds" / "worktrees" / "idea-run-1"

    dump_json(
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "experiments" / "main" / "run-1" / "RESULT.json",
        {
            "quest_id": "002-early-residual-risk",
            "run_id": "run-1",
            "worktree_root": str(idea_worktree_root),
            "metric_contract": {
                "required_non_scalar_deliverables": [],
            },
            "metrics_summary": {
                "roc_auc": 0.81,
            },
            "baseline_comparisons": {"items": []},
            "results_summary": "summary",
            "conclusion": "conclusion",
        },
    )
    dump_json(
        current_paper_root / "paper_line_state.json",
        {
            "paper_root": str(current_paper_root.resolve()),
            "paper_branch": "paper/run-1",
        },
    )
    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/stale-mirror",
            "compile_report_path": "paper/build/compile_report.json",
        },
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "paper_branch": "paper/stale-mirror",
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:33Z.json",
        {
            "paper_root": str(current_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == current_paper_root / "paper_bundle_manifest.json"
    assert report["paper_root"] == str(current_paper_root.resolve())
    assert report["medical_publication_surface_status"] == "clear"
    assert "medical_publication_surface_blocked" not in report["blockers"]


def test_build_gate_report_allows_clinical_cohort_wording_without_internal_labels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "draft.md": (
                "We analyzed the institutional first-surgery NF-PitNET cohort and "
                "ascertained outcomes through June 30, 2024.\n"
            )
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "forbidden_manuscript_terminology" not in report["blockers"]
    assert report["manuscript_terminology_violations"] == []


def test_run_controller_enqueues_message_when_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1
    assert "publishability gate" in queue["pending"][0]["content"]


def test_build_gate_report_keeps_blocker_logic_in_controller_after_adapter_patch(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    monkeypatch.setattr(
        module.quest_state,
        "resolve_active_stdout_path",
        lambda *, quest_root, runtime_state: quest_root / ".ds" / "runs" / "run-1" / "stdout.jsonl",
    )
    monkeypatch.setattr(module.quest_state, "read_recent_stdout_lines", lambda stdout_path: ["route -> write"])
    monkeypatch.setattr(module.paper_artifacts, "resolve_artifact_manifest_from_main_result", lambda main_result: None)
    monkeypatch.setattr(module.paper_artifacts, "resolve_paper_bundle_manifest", lambda quest_root: None)
    monkeypatch.setattr(module.paper_artifacts, "resolve_submission_minimal_manifest", lambda paper_bundle_manifest_path: None)
    monkeypatch.setattr(
        module.paper_artifacts,
        "resolve_submission_minimal_output_paths",
        lambda *, paper_bundle_manifest_path, submission_minimal_manifest: (None, None),
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert "active_run_drifting_into_write_without_gate_approval" in report["blockers"]
    assert "missing_required_non_scalar_deliverables" not in report["blockers"]


def test_build_gate_report_ignores_live_agent_write_drift_when_active_run_differs_from_main_result(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    runtime_state["active_run_id"] = "run-live-agent"
    dump_json(runtime_state_path, runtime_state)
    write_text(
        quest_root / ".ds" / "runs" / "run-live-agent" / "stdout.jsonl",
        json.dumps({"line": "route -> write"}) + "\n",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.active_run_stdout_path is None
    assert state.recent_stdout_lines == []
    assert report["status"] == "blocked"
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert "active_run_drifting_into_write_without_gate_approval" not in report["blockers"]


def test_detect_write_drift_ignores_write_drift_gate_path_noise() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    noisy_line = (
        "progress watchdog note: route change needed after inspection; "
        "cwd=.ds/worktrees/analysis-analysis-d47ce8e6-write-drift-gate"
    )

    assert module.detect_write_drift([noisy_line]) is False


def test_detect_write_drift_ignores_stop_messages_about_write_stage() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    control_line = (
        "Hard control message: immediately stop the current transition into `write` / outline generation."
    )

    assert module.detect_write_drift([control_line]) is False


def test_detect_write_drift_ignores_agent_messages_that_quote_examples() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    quoted_example_line = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "id": "item-1",
                "type": "agent_message",
                "text": "保留 `route -> write` 这类真阳性，但这里是在解释测试，不是真实路由切换。",
            },
        },
        ensure_ascii=False,
    )

    assert module.detect_write_drift([quoted_example_line]) is False


def test_detect_write_drift_ignores_non_artifact_tool_output_examples() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    tool_output_line = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "id": "item-2",
                "type": "mcp_tool_call",
                "server": "bash_exec",
                "tool": "bash_exec",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Next anchor: `write`\nroute -> write",
                        }
                    ]
                },
            },
        },
        ensure_ascii=False,
    )

    assert module.detect_write_drift([tool_output_line]) is False


def test_detect_write_drift_accepts_structured_next_anchor_signal() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    structured_signal_line = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "id": "item-3",
                "type": "mcp_tool_call",
                "server": "artifact",
                "tool": "activate_branch",
                "result": {
                    "structured_content": {
                        "next_anchor": "write",
                    }
                },
            },
        },
        ensure_ascii=False,
    )

    assert module.detect_write_drift([structured_signal_line]) is True


def test_write_gate_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T04:00:00+00:00",
        "quest_id": quest_root.name,
        "run_id": "run-1",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "stop",
        "blockers": ["missing_post_main_publishability_gate"],
        "missing_non_scalar_deliverables": [],
        "paper_bundle_manifest_path": None,
        "submission_minimal_manifest_path": None,
        "submission_minimal_present": False,
        "submission_minimal_docx_present": False,
        "submission_minimal_pdf_present": False,
        "headline_metrics": {},
        "results_summary": "summary",
        "conclusion": "conclusion",
        "controller_note": "note",
    }

    json_path, md_path = module.write_gate_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "publishability_gate"
    assert seen["timestamp"] == "2026-04-03T04:00:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
