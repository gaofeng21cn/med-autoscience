from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_study_progress_projects_active_quest_without_live_run_as_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": None,
                    "worker_running": True,
                },
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
                "summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要先恢复 MedAutoScience supervisor tick / heartbeat 调度，再继续托管监管与自动恢复。",
                "latest_report_path": str(
                    study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
                ),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "managed_runtime_recovering"
    assert "恢复" in result["current_stage_summary"]


def test_study_progress_projects_output_blocker_impact_from_runtime_continuity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "stale",
            "active_run_id": None,
            "worker_state": "stale",
            "worker_running": False,
            "runtime_session": {
                "worker_state": "stale",
                "freshness_state": "stale",
                "last_known_run_id": "run-stale-001",
                "will_start_llm": False,
            },
            "recovery_intent": {
                "current_action": "safe_reconcile_ready",
                "next_owner": "mas_controller",
                "dedupe_fingerprint": "runtime-continuity-001",
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-001",
                "canonical_runtime_action": "recover_runtime",
                "worker_liveness_state": {"state": "stale"},
                "blocking_reasons": ["same_fingerprint_loop"],
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-001",
                "source_signature": "runtime-continuity-001",
            },
            "owner_route": {
                "next_owner": "mas_controller",
                "owner_reason": "runtime_stale",
                "source_fingerprint": "runtime-continuity-001",
            },
            "paper_progress_stall": {
                "why_not_running": "stale worker blocks paper artifact generation",
                "same_fingerprint_or_handoff": "same_fingerprint",
                "source_refs": [str(study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json")],
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "summary": "supervisor tick stale",
            },
        },
    )

    result = module.read_study_progress(
        profile=profile,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
    )

    impact = result["production_blocker_impact"]
    assert impact["surface_kind"] == "mas_production_blocker_impact_projection"
    assert impact["affects_output"] is True
    assert impact["next_owner"] == "mas_controller"
    assert impact["why_not_running"] == "stale worker blocks paper artifact generation"
    assert impact["same_fingerprint_or_handoff"] == "same_fingerprint"
    assert impact["will_start_llm"] is False
    assert impact["safe_reconcile_command"].endswith("--studies 001-risk --mode developer_apply_safe --dry-run")
    assert impact["route"]["source_fingerprint"] == "runtime-continuity-001"
    assert impact["authority"]["writes_authority_surface"] is False
