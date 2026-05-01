from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_autonomy_progress_slo_triggers_ai_doctor_for_stale_gate_closure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_ai_doctor")
    study_root = tmp_path / "studies" / "003-dpcc"
    quest_root = tmp_path / "runtime" / "quests" / "quest-003"

    payload = module.materialize_autonomy_control_plane_observer(
        study_root=study_root,
        quest_root=quest_root,
        generated_at="2026-04-30T14:30:00+00:00",
        profile_payload={
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "sli_summary": {"duplicate_dispatch_active": False},
            "gate_blocker_summary": {
                "current_blockers": ["stale_submission_minimal_authority"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "publication_gate_replay"},
            },
            "publication_eval_replay_lag": {
                "status": "stale_after_gate_replay",
                "latest_gate_replayed_at": "2026-04-30T12:00:00+00:00",
                "publication_eval_latest_at": "2026-04-30T10:00:00+00:00",
            },
            "autonomy_slo": {
                "progress_health": {"state": "blocked_with_actionable_work"},
                "runtime_failure_classification": {"external_blocker": False},
            },
        },
    )

    status_path = module.stable_slo_status_path(study_root=study_root)
    request_path = module.ai_doctor_requests_root(study_root=study_root) / "latest.json"
    repair_path = module.repair_actions_root(study_root=study_root) / "latest.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    repair = json.loads(repair_path.read_text(encoding="utf-8"))

    assert status_path.exists()
    assert payload["state"] == "breach"
    assert payload["ai_doctor_request_required"] is True
    assert payload["breach_types"] == [
        "gate_closure_drift",
        "no_meaningful_progress",
        "stale_truth_surface",
    ]
    assert request["state"] == "request_ready"
    assert request["default_model_policy"] == "inherit_current_codex_configuration"
    assert request["quality_gate_relaxation_allowed"] is False
    assert "write_medical_conclusion" in request["forbidden_actions"]
    assert repair["state"] == "awaiting_ai_doctor"
    assert repair["actions"][1]["repair_kind"] == "publication_gate_replay_or_authority_sync"


def test_autonomy_progress_slo_does_not_call_ai_for_fresh_actionable_gate_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_ai_doctor")

    payload = module.build_autonomy_control_plane_observer(
        {
            "study_id": "002-dpcc",
            "quest_id": "quest-002",
            "sli_summary": {
                "duplicate_dispatch_active": False,
                "next_work_unit_id": "analysis_claim_evidence_repair",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            },
            "publication_eval_replay_lag": {
                "status": "current_after_gate_replay",
                "latest_gate_replayed_at": "2026-04-30T14:00:00+00:00",
                "publication_eval_latest_at": "2026-04-30T14:01:00+00:00",
            },
            "autonomy_slo": {
                "progress_health": {"state": "blocked_with_actionable_work"},
                "runtime_failure_classification": {"external_blocker": False},
            },
        },
        generated_at="2026-04-30T14:30:00+00:00",
    )

    assert payload["state"] == "met"
    assert payload["breach_types"] == []
    assert payload["ai_doctor_request_required"] is False
    assert payload["ai_doctor_state"] == "not_required"


def test_autonomy_progress_slo_uses_mds_read_churn_without_artifact_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_ai_doctor")
    quest_root = tmp_path / "runtime" / "quests" / "quest-003"
    telemetry_path = quest_root / ".ds" / "runs" / "run-003" / "telemetry.json"
    telemetry_path.parent.mkdir(parents=True, exist_ok=True)
    telemetry_path.write_text(
        json.dumps(
            {
                "run_id": "run-003",
                "read_churn_ratio": 0.75,
                "same_result_reinjection_count": 6,
                "turn_progress_kind": "read_churn_without_artifact_delta",
            }
        ),
        encoding="utf-8",
    )

    payload = module.build_autonomy_control_plane_observer(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "sli_summary": {"duplicate_dispatch_active": False},
            "gate_blocker_summary": {"current_blockers": []},
            "autonomy_slo": {"runtime_failure_classification": {"external_blocker": False}},
        },
        quest_root=quest_root,
        generated_at="2026-04-30T14:30:00+00:00",
    )

    assert payload["breach_types"] == ["read_churn_without_artifact_delta"]
    assert payload["mds_progress_markers"]["same_result_reinjection_count"] == 6
    assert payload["ai_doctor_request_required"] is True


def test_autonomy_progress_slo_treats_parked_turn_without_artifact_delta_as_gate_closure_drift(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_ai_doctor")
    study_root = tmp_path / "studies" / "002-dpcc"
    quest_root = tmp_path / "runtime" / "quests" / "quest-002"
    telemetry_path = quest_root / ".ds" / "runs" / "run-parked" / "telemetry.json"
    telemetry_path.parent.mkdir(parents=True, exist_ok=True)
    telemetry_path.write_text(
        json.dumps(
            {
                "run_id": "run-parked",
                "turn_reason": "auto_continue",
                "turn_mode": "parked",
                "turn_progress_kind": "parked_no_artifact_delta",
                "meaningful_artifact_delta_at": None,
                "completed_at": "2026-05-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    payload = module.materialize_autonomy_control_plane_observer(
        study_root=study_root,
        quest_root=quest_root,
        generated_at="2026-05-01T00:20:01+00:00",
        profile_payload={
            "study_id": "002-dpcc",
            "quest_id": "quest-002",
            "sli_summary": {
                "duplicate_dispatch_active": False,
                "next_work_unit_id": "publication_gate_replay",
            },
            "gate_blocker_summary": {
                "current_blockers": ["stale_submission_minimal_authority"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "publication_gate_replay"},
            },
            "autonomy_slo": {
                "progress_health": {"state": "blocked_with_actionable_work"},
                "runtime_failure_classification": {"external_blocker": False},
            },
        },
    )
    repair = json.loads(
        (module.repair_actions_root(study_root=study_root) / "latest.json").read_text(encoding="utf-8")
    )
    repair_kinds = [action["repair_kind"] for action in repair["actions"]]

    assert payload["state"] == "breach"
    assert payload["breach_types"] == ["gate_closure_drift", "no_meaningful_progress"]
    assert payload["ai_doctor_request_required"] is True
    assert payload["mds_progress_markers"]["turn_progress_kind"] == "parked_no_artifact_delta"
    assert payload["mds_progress_markers"]["turn_completed_at"] == "2026-05-01T00:00:00+00:00"
    assert "publication_gate_replay_or_authority_sync" in repair_kinds
    assert "suppress_repeated_long_turn_until_artifact_delta_or_specificity" in repair_kinds


def test_ai_doctor_diagnosis_surface_refuses_gate_relaxation_and_writes_repair_action(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_ai_doctor")
    study_root = tmp_path / "studies" / "003-dpcc"

    try:
        module.materialize_ai_doctor_diagnosis(
            study_root=study_root,
            diagnosis_payload={
                "study_id": "003-dpcc",
                "quality_gate_relaxation_allowed": True,
            },
            recorded_at="2026-04-30T15:00:00+00:00",
        )
    except ValueError as exc:
        assert "cannot relax" in str(exc)
    else:  # pragma: no cover - guards fail-closed behavior
        raise AssertionError("quality gate relaxation must fail")

    diagnosis = module.materialize_ai_doctor_diagnosis(
        study_root=study_root,
        diagnosis_payload={
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "request_id": "ai-doctor-request::003",
            "diagnosis_code": "stale_gate_authority",
            "repair_scope": "controller_repair",
            "recommended_repair_kind": "publication_gate_replay_or_authority_sync",
            "repair_owner": "mas_controller",
            "auto_apply_allowed": True,
        },
        recorded_at="2026-04-30T15:00:00+00:00",
    )
    repair = json.loads((module.repair_actions_root(study_root=study_root) / "latest.json").read_text(encoding="utf-8"))

    assert diagnosis["surface"] == "ai_doctor_diagnosis"
    assert diagnosis["quality_gate_relaxation_allowed"] is False
    assert diagnosis["medical_conclusion_written"] is False
    assert repair["state"] == "ready_for_repair"
    assert repair["actions"][0]["diagnosis_id"] == diagnosis["diagnosis_id"]
