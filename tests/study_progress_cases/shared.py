from __future__ import annotations

from . import shared_base as _shared_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared_base)


def write_prediction_study(profile, study_id: str = "001-risk", **kwargs: object) -> Path:
    return write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        **kwargs,
    )


def managed_runtime_execution(
    quest_id: str = "quest-001",
    *,
    auto_entry: bool = True,
) -> dict[str, object]:
    payload: dict[str, object] = {"engine": "med-deepscientist"}
    if auto_entry:
        payload["auto_entry"] = "on_managed_research_intent"
    payload.update({"quest_id": quest_id, "auto_resume": True})
    return payload


def study_macro_state(
    *,
    study_id: str = "001-risk",
    writer_state: str = "parked",
    user_next: str = "inspect",
    reason: str = "unknown",
    details: dict[str, object] | None = None,
    conditions: list[dict[str, object]] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload = {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": study_id,
        "writer_state": writer_state,
        "user_next": user_next,
        "reason": reason,
        "details": details or {},
        "conditions": conditions or [],
    }
    payload.update(overrides)
    return payload


def publication_gate_supervisor_state(
    *,
    supervisor_phase: str = "publishability_gate_blocked",
    upstream_scientific_anchor_ready: bool = True,
    bundle_tasks_downstream_only: bool = True,
    current_required_action: str = "return_to_publishability_gate",
    **overrides: object,
) -> dict[str, object]:
    payload = {
        "supervisor_phase": supervisor_phase,
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": upstream_scientific_anchor_ready,
        "bundle_tasks_downstream_only": bundle_tasks_downstream_only,
        "current_required_action": current_required_action,
    }
    payload.update(overrides)
    return payload


def fresh_supervisor_tick_audit(
    *,
    summary: str = "监管心跳新鲜。",
    next_action_summary: str | None = None,
    latest_recorded_at: str | None = None,
) -> dict[str, object]:
    payload = {"required": True, "status": "fresh", "summary": summary}
    if next_action_summary is not None:
        payload["next_action_summary"] = next_action_summary
    if latest_recorded_at is not None:
        payload["latest_recorded_at"] = latest_recorded_at
    return payload


def progress_projection_payload(
    study_root: Path,
    quest_root: Path | None = None,
    *,
    study_id: str = "001-risk",
    quest_id: str = "quest-001",
    **overrides: object,
) -> dict[str, object]:
    payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
    }
    if quest_root is not None:
        payload["quest_root"] = str(quest_root)
    payload.update(overrides)
    return payload


def managed_research_progress_payload(
    study_root: Path,
    quest_root: Path,
    *,
    study_id: str = "001-risk",
    quest_id: str = "quest-001",
    quest_status: str = "running",
    decision: str = "resume",
    reason: str = "quest_already_running",
    supervisor_state: dict[str, object] | None = None,
    execution: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload = progress_projection_payload(
        study_root,
        quest_root,
        study_id=study_id,
        quest_id=quest_id,
        entry_mode="full_research",
        execution=execution if execution is not None else managed_runtime_execution(quest_id),
        quest_exists=True,
        quest_status=quest_status,
        runtime_status_path=str(
            study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
        ),
        study_completion_contract={},
        decision=decision,
        reason=reason,
        publication_supervisor_state=supervisor_state or publication_gate_supervisor_state(),
    )
    payload.update(overrides)
    return payload


def running_progress_payload(
    study_root: Path,
    quest_root: Path,
    *,
    study_id: str = "001-risk",
    quest_id: str = "quest-001",
    include_execution: bool = True,
    **overrides: object,
) -> dict[str, object]:
    payload = progress_projection_payload(
        study_root,
        quest_root,
        study_id=study_id,
        quest_id=quest_id,
        entry_mode="full_research",
    )
    if include_execution:
        payload["execution"] = {"quest_id": quest_id, "auto_resume": True}
    payload.update(
        {
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
        }
    )
    payload.update(overrides)
    return payload


def status_payload_with_progress_projection(
    study_root: Path,
    *,
    study_id: str = "001-risk",
    quest_id: str = "quest-001",
    **progress_projection: object,
) -> dict[str, object]:
    return {
        "study_id": study_id,
        "publication_supervisor_state": {},
        "progress_projection": progress_projection_payload(
            study_root,
            study_id=study_id,
            quest_id=quest_id,
            **progress_projection,
        ),
    }

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
