from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_ai_repair_lifecycle_and_mcp_compact_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json",
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "external_supervisor_required",
            "top_action": {"action_type": "controller_repair", "repair_kind": "bounded_work_unit_redrive"},
            "auto_apply_allowed": True,
            "last_apply_attempt_at": "2026-05-04T04:36:00+00:00",
            "applied_at": None,
            "blocked_reason": "runtime_recovery_not_authorized",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    )

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
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "control_plane_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    compact = mcp_projection.compact_study_progress_projection(result)

    assert result["ai_repair_lifecycle"]["state"] == "external_supervisor_required"
    assert result["ai_repair_lifecycle"]["blocked_reason"] == "runtime_recovery_not_authorized"
    assert result["refs"]["ai_repair_lifecycle_path"].endswith("artifacts/autonomy/repair_lifecycle/latest.json")
    assert compact["ai_repair_lifecycle"]["next_owner"] == "external_supervisor"
    assert compact["ai_repair_lifecycle"]["external_supervisor_required"] is True


def test_study_progress_suppresses_stale_repair_lifecycle_after_work_unit_evidence_adoption(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json",
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "state": "blocked",
            "top_action": {"action_type": "controller_repair", "repair_kind": "bounded_work_unit_redrive"},
            "blocked_reason": "runtime_recovery_retry_budget_exhausted",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    )

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
            "active_run_id": None,
            "decision": "noop",
            "reason": "controller_work_unit_evidence_adopted",
            "controller_work_unit_next_route": {
                "recommended_next_route": "return_to_publication_gate_recheck",
                "owner": "publication_gate",
                "quality_gate_relaxation_allowed": False,
                "runtime_relaunch_required": False,
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["ai_repair_lifecycle"] is None
    assert result["refs"]["ai_repair_lifecycle_path"] is None
    assert result["supervision"]["health_status"] == "publication_gate_blocked"
    assert result["module_surfaces"]["runtime"]["health_status"] == "publication_gate_blocked"


def test_study_progress_builds_readonly_ai_repair_lifecycle_from_ready_repair_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "bounded_work_unit_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
            "quality_gate_relaxation_allowed": False,
        },
    )

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
            "quest_status": "running",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "control_plane_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_runtime_action": "external_supervisor_required",
                "dispatch_gate": {
                    "state": "blocked",
                    "dispatch_allowed": False,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "route_authorization": {"runtime_recovery_allowed": False},
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["ai_repair_lifecycle"]["state"] == "external_supervisor_required"
    assert result["ai_repair_lifecycle"]["blocked_reason"] == "runtime_recovery_not_authorized"
    assert result["ai_repair_lifecycle"]["next_owner"] == "external_supervisor"
    assert result["ai_repair_lifecycle"]["external_supervisor_required"] is True
    assert result["ai_repair_lifecycle"]["projection_only"] is True
    assert result["refs"]["ai_repair_lifecycle_path"].endswith("artifacts/autonomy/repair_lifecycle/latest.json")
