from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_does_not_keep_ai_reviewer_pending_after_ai_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(
        study_root,
        quest_root,
        recommended_actions=[
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::specific",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Concrete publication anchor targets are present.",
                "requires_controller_decision": True,
                "work_unit_fingerprint": "publication-blockers::specific",
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Publication gate already named concrete targets.",
                },
                "specificity_targets": _specificity_targets(study_root=study_root, quest_root=quest_root),
            }
        ],
        assessment_provenance={"owner": "ai_reviewer", "ai_reviewer_required": False},
    )
    monkeypatch.setattr(
        profiler,
        "profile_study_cycle",
        lambda **_: {
            "autonomy_progress_slo_status": {
                "surface": "autonomy_progress_slo_status",
                "schema_version": 1,
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "state": "ok",
                "breach_types": [],
                "ai_doctor_request_required": False,
                "ai_doctor_state": "not_required",
                "quality_gate_relaxation_allowed": False,
            }
        },
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "product",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "waiting_for_user",
            "decision": "blocked",
            "reason": "quest_waiting_for_user",
            "runtime_liveness_status": "parked",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "parked",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "parked",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            },
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_wait",
                "action": "block",
                "reason_code": "blocked_turn_closeout_waiting_for_owner",
                "requires_user_input": False,
                "next_owner": "ai_reviewer",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["superseded_by_publication_eval"] is True
    assert result["parked_state"] is None
    assert result["current_stage"] == "runtime_blocked"
    assert result["intervention_lane"]["lane_id"] != "auto_runtime_parked"
    assert result["intervention_lane"]["lane_id"] != "publication_gate_specificity_required"
    assert result["operator_status_card"]["handling_state"] != "ai_reviewer_pending"


def _specificity_targets(*, study_root: Path, quest_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "table",
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result",
            "source_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "blocking_reason": "missing_publication_anchor",
        },
    ]
