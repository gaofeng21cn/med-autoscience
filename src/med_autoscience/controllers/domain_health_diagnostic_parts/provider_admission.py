from __future__ import annotations

from typing import Any, Mapping


def materialized_record_only_provider_handoff(materialize_result: Mapping[str, Any]) -> bool:
    return bool(materialized_record_only_provider_handoffs(materialize_result))


def materialized_record_only_provider_handoffs(materialize_result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    handoffs: list[Mapping[str, Any]] = []
    for item in materialize_result.get("default_executor_dispatches") or []:
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("dispatch_status")) != "ready":
            continue
        if _non_empty_text(item.get("dispatch_authority")) != "ai_reviewer_record_production_handoff":
            continue
        handoffs.append(item)
    return handoffs


def provider_admission_pending_dispatch_result(
    *,
    materialize_result: Mapping[str, Any],
) -> dict[str, Any]:
    executions: list[dict[str, Any]] = []
    for handoff in materialized_record_only_provider_handoffs(materialize_result):
        executions.append(
            {
                "surface": "default_executor_dispatch_execution",
                "study_id": _non_empty_text(handoff.get("study_id")),
                "quest_id": _non_empty_text(handoff.get("quest_id")),
                "action_type": _non_empty_text(handoff.get("action_type")),
                "work_unit_id": handoff_work_unit_id(handoff),
                "dispatch_path": handoff_dispatch_path(handoff),
                "dispatch_authority": _non_empty_text(handoff.get("dispatch_authority")),
                "execution_status": "provider_admission_pending",
                "blocked_reason": None,
                "next_executable_owner": _non_empty_text(handoff.get("next_executable_owner")),
                "required_output_surface": _non_empty_text(handoff.get("required_output_surface")),
                "will_start_llm": False,
                "provider_attempt_or_lease_required": True,
                "provider_completion_is_domain_completion": False,
            }
        )
    return {
        "surface": "domain_owner_action_dispatch",
        "schema_version": 1,
        "execution_count": 0,
        "executed_count": 0,
        "blocked_count": 0,
        "repeat_suppressed_count": 0,
        "dry_run_count": 0,
        "codex_dispatch_count": 0,
        "suppressed_dispatch_count": len(executions),
        "provider_admission_pending_count": len(executions),
        "executions": executions,
        "written_files": [],
    }


def handoff_dispatch_path(handoff: Mapping[str, Any]) -> str | None:
    refs = _mapping(handoff.get("refs"))
    return _non_empty_text(refs.get("stage_packet_path")) or _non_empty_text(
        refs.get("immutable_dispatch_path")
    ) or _non_empty_text(refs.get("dispatch_path"))


def handoff_work_unit_id(handoff: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(handoff.get("owner_route")) or _mapping(
        _mapping(handoff.get("prompt_contract")).get("owner_route")
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(owner_route.get("work_unit_id"))
        or _non_empty_text(basis.get("work_unit_id"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
    )


def provider_probe_has_matching_attempt(
    scan_result: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_study_id = _non_empty_text(identity.get("study_id"))
    for study in scan_result.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        if expected_study_id is not None and _non_empty_text(study.get("study_id")) != expected_study_id:
            continue
        if not study_has_running_provider_attempt(study):
            continue
        live_attempt = _mapping(study.get("opl_provider_attempt")) or study
        if provider_attempt_matches_identity(live_attempt, identity=identity):
            return True
    return False


def study_has_running_provider_attempt(study: Mapping[str, Any]) -> bool:
    return study.get("running_provider_attempt") is True and (
        _non_empty_text(study.get("active_stage_attempt_id"))
        or _non_empty_text(study.get("active_run_id"))
        or _non_empty_text(study.get("active_workflow_id"))
    ) is not None


def provider_attempt_matches_identity(
    live_attempt: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_action = _non_empty_text(identity.get("action_type"))
    if expected_action is not None and _non_empty_text(live_attempt.get("action_type")) != expected_action:
        return False
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if expected_work_unit is not None and _non_empty_text(live_attempt.get("work_unit_id")) != expected_work_unit:
        return False
    expected_dispatch = _non_empty_text(identity.get("dispatch_path"))
    live_dispatch = _non_empty_text(live_attempt.get("dispatch_ref")) or _non_empty_text(live_attempt.get("dispatch_path"))
    if expected_dispatch is None or live_dispatch is None:
        return True
    normalized_expected = expected_dispatch.replace("\\", "/")
    normalized_live = live_dispatch.replace("\\", "/")
    return normalized_expected == normalized_live or normalized_expected.endswith(f"/{normalized_live}")


def provider_probe_has_non_running_actions(scan_result: Mapping[str, Any]) -> bool:
    running_study_ids = {
        study_id
        for study in scan_result.get("studies") or []
        if isinstance(study, Mapping)
        and study.get("running_provider_attempt") is True
        and (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    for action in scan_result.get("action_queue") or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None or study_id not in running_study_ids:
            return True
    return False


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
