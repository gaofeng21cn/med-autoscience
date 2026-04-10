from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    manuscript_files: dict[str, str] | None = None,
    submission_checklist: dict[str, object] | None = None,
) -> Path:
    quest_root = tmp_path / "runtime" / "quests" / "002-early-residual-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"

    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "002-early-residual-risk",
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
        },
    )
    if submission_checklist is not None:
        dump_json(
            worktree_root / "paper" / "review" / "submission_checklist.json",
            submission_checklist,
        )
    if include_submission_minimal:
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
        (worktree_root / "paper" / "submission_minimal" / "manuscript.docx").write_text("docx", encoding="utf-8")
        (worktree_root / "paper" / "submission_minimal" / "paper.pdf").write_text("%PDF", encoding="utf-8")
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
        dump_json(
            quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
            {
                "status": medical_publication_surface_status,
                "blockers": [] if medical_publication_surface_status == "clear" else ["claim_evidence_map_missing_or_incomplete"],
            },
        )
    if manuscript_files:
        for relpath, body in manuscript_files.items():
            target = worktree_root / "paper" / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

    return quest_root


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


def test_build_gate_report_supports_finalize_only_paper_bundle_without_main_result(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
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


def test_build_gate_report_accepts_archived_reference_only_legacy_submission_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
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
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
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
