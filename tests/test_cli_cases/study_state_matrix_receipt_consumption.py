from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_state_matrix_consumes_bundle_stage_package_closure_receipt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-dm"
    quest_id = study_id
    study_root = workspace_root / "studies" / study_id
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / quest_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    runtime_escalation_ref = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    work_unit_fingerprint = "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002-dm::current",
            "study_id": study_id,
            "quest_id": quest_id,
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "current_required_action": "continue_bundle_stage",
            "runtime_context_refs": {"runtime_escalation_ref": str(runtime_escalation_ref)},
            "recommended_actions": [
                {
                    "action_type": "continue_same_line",
                    "route_target": "finalize",
                    "next_work_unit": {
                        "unit_id": "submission_authority_sync_closure",
                        "lane": "controller",
                        "summary": "Synchronize submission authority and package closure.",
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "decision-bundle-finalize",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Synchronize submission authority and package closure.",
            },
        },
    )
    package_closure_ref = "artifacts/reports/package_closure/20260515T075324Z.submission_authority_sync_closure.json"
    _write_json(
        quest_root / package_closure_ref,
        {
            "schema_version": 1,
            "artifact_kind": "submission_authority_sync_closure",
            "study_id": study_id,
            "quest_id": quest_id,
            "run_id": "mas-run-002-finalize",
            "controller_decision_id": "decision-bundle-finalize",
            "work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "fingerprint": work_unit_fingerprint,
            },
            "authority_closure": {
                "status": "closed_for_bundle_stage",
                "publication_gate_status": "clear",
                "publication_gate_allow_write": True,
                "publication_gate_blockers": [],
                "current_required_action": "continue_bundle_stage",
            },
            "submission_minimal_authority": {
                "status": "current",
                "docx_present": True,
                "pdf_present": True,
            },
            "human_facing_delivery": {
                "status": "current",
                "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
            },
        },
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "turn_closeouts" / "mas-run-002-finalize.json",
        {
            "schema_version": 1,
            "quest_id": quest_id,
            "run_id": "mas-run-002-finalize",
            "status": "completed",
            "completed_at": "2026-05-15T07:56:12Z",
            "meaningful_artifact_delta": True,
            "artifact_refs": [package_closure_ref],
            "blocked_reason": None,
            "next_owner": None,
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_status": "running",
            "active_run_id": "stale-run-002",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    transition = payload["studies"][0]["domain_transition"]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]
    rule = payload["domain_transition_table"]["family_transition_spec"]["transitions"][0]

    assert exit_code == 0
    assert transition["decision_type"] == "completion_receipt_consumed"
    assert transition["route_target"] == "human_gate"
    assert transition["next_work_unit"]["unit_id"] == "package_closure_consumed_handoff"
    assert transition["controller_action"] == "none"
    assert transition["owner"] == "med-autoscience"
    assert transition["completion_receipt_consumption"] == {
        "status": "consumed",
        "receipt_kind": "runtime_turn_closeout_package_closure",
        "consumed_work_unit_id": "submission_authority_sync_closure",
        "consumed_work_unit_fingerprint": work_unit_fingerprint,
        "completion_ref": "artifacts/runtime/turn_closeouts/mas-run-002-finalize.json",
        "artifact_ref": package_closure_ref,
        "next_action": "do_not_redrive_completed_work_unit",
    }
    assert transition["guard_boundary"]["opl_generic_runner_may_resume"] is False
    assert case["expected"]["decision_type"] == "completion_receipt_consumed"
    assert case["expected"]["next_work_unit_id"] == "package_closure_consumed_handoff"
    assert case["context"]["completion_receipt_consumption"]["next_action"] == "do_not_redrive_completed_work_unit"
    assert rule["receipt"]["completion_receipt_consumption"]["receipt_kind"] == "runtime_turn_closeout_package_closure"


def test_study_state_matrix_marks_default_executor_execution_receipt_supersession(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "003-dpcc"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    supersession = {
        "source_surface": "default_executor_execution/latest.json",
        "source_path": str(
            study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"
        ),
        "superseded_run_id": "run-old",
        "execution_id": "execution::003-dpcc::return_to_ai_reviewer_workflow::2026-05-15T07:48:49+00:00",
        "action_type": "return_to_ai_reviewer_workflow",
        "execution_status": "executed",
        "generated_at": "2026-05-15T07:48:49+00:00",
        "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
    }
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "domain_ready_verdict": "ai_reviewer_re_eval",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
            },
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
            "blocked_turn_closeout_supersession": supersession,
            "continuation_state": {
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    transition = payload["studies"][0]["domain_transition"]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]

    assert exit_code == 0
    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["completion_receipt_consumption"] == {
        "status": "superseded_stale_closeout",
        "receipt_kind": "default_executor_execution",
        "superseded_run_id": "run-old",
        "execution_id": "execution::003-dpcc::return_to_ai_reviewer_workflow::2026-05-15T07:48:49+00:00",
        "action_type": "return_to_ai_reviewer_workflow",
        "source_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
        "next_action": "honor_newer_owner_execution_receipt",
    }
    assert case["expected"]["decision_type"] == "ai_reviewer_re_eval"
    assert case["context"]["completion_receipt_consumption"]["status"] == "superseded_stale_closeout"
    assert case["context"]["completion_receipt_consumption"]["next_action"] == "honor_newer_owner_execution_receipt"


def test_study_state_matrix_consumes_mas_owner_apply_receipt_as_artifact_delta(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-dm"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {
            "surface": "paper_repair_owner_receipt",
            "accepted": True,
            "execution_status": "executed",
            "canonical_artifact_delta_refs": [{"path": str(study_root / "paper" / "manuscript.md")}],
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "progress_delta_candidate": True,
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    transition = payload["studies"][0]["domain_transition"]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]
    rule = payload["domain_transition_table"]["family_transition_spec"]["transitions"][0]

    assert exit_code == 0
    assert transition["decision_type"] == "owner_apply_receipt_consumed"
    assert transition["route_target"] == "finalize"
    assert transition["next_work_unit"]["unit_id"] == "provider_hosted_guarded_apply"
    assert transition["controller_action"] == "paper_autonomy_guarded_apply"
    assert transition["owner"] == "med-autoscience"
    assert transition["completion_receipt_consumption"] == {
        "status": "consumed",
        "receipt_kind": "mas_owner_apply_receipt",
        "apply_result": "artifact_delta",
        "receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
        "evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        "next_action": "allow_mas_owner_guarded_apply",
    }
    assert transition["guard_boundary"]["mas_owner_apply_receipt_required"] is True
    assert case["expected"]["decision_type"] == "owner_apply_receipt_consumed"
    assert case["context"]["completion_receipt_consumption"]["receipt_kind"] == "mas_owner_apply_receipt"
    assert rule["receipt"]["completion_receipt_consumption"]["apply_result"] == "artifact_delta"


def test_study_state_matrix_consumes_controller_decision_owner_receipt_as_stable_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-dm"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "route_decision": "stable_blocker",
            "runtime_decision": "blocked",
            "blocked_reason": "owner surface blocked by publication gate specificity",
            "next_owner": "publication_gate",
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    transition = payload["studies"][0]["domain_transition"]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]

    assert exit_code == 0
    assert transition["decision_type"] == "owner_apply_receipt_consumed"
    assert transition["route_target"] == "finalize"
    assert transition["next_work_unit"]["unit_id"] == "provider_hosted_guarded_apply"
    assert transition["controller_action"] == "paper_autonomy_guarded_apply"
    assert transition["completion_receipt_consumption"] == {
        "status": "consumed",
        "receipt_kind": "mas_owner_apply_receipt",
        "apply_result": "stable_blocker",
        "receipt_ref": "artifacts/controller_decisions/latest.json",
        "next_action": "record_mas_owner_stable_blocker",
    }
    assert transition["guard_boundary"]["mas_owner_apply_receipt_required"] is True
    assert case["context"]["completion_receipt_consumption"]["apply_result"] == "stable_blocker"


def test_study_state_matrix_consumes_controller_route_decision_owner_receipt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-dm"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "route_decision": "switch_line",
            "route_target": "scout",
            "selected_line_id": "dm-biomarker-line",
            "requires_human_confirmation": False,
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    transition = payload["studies"][0]["domain_transition"]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]

    assert exit_code == 0
    assert transition["decision_type"] == "owner_apply_receipt_consumed"
    assert transition["route_target"] == "finalize"
    assert transition["next_work_unit"]["unit_id"] == "provider_hosted_guarded_apply"
    assert transition["completion_receipt_consumption"] == {
        "status": "consumed",
        "receipt_kind": "mas_owner_apply_receipt",
        "apply_result": "route_decision",
        "receipt_ref": "artifacts/controller_decisions/latest.json",
        "next_action": "record_mas_owner_route_decision",
    }
    assert transition["guard_boundary"]["mas_owner_apply_receipt_required"] is True
    assert case["expected"]["decision_type"] == "owner_apply_receipt_consumed"
    assert case["context"]["completion_receipt_consumption"]["apply_result"] == "route_decision"
