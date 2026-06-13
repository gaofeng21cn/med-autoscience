from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


def materialized_record_only_provider_handoff(
    materialize_result: Mapping[str, Any],
) -> bool:
    return bool(materialized_record_only_provider_handoffs(materialize_result))


def materialized_record_only_provider_handoffs(
    materialize_result: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
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
    return (
        _non_empty_text(handoff.get("dispatch_path"))
        or _non_empty_text(handoff.get("stage_packet_ref"))
        or _non_empty_text(refs.get("stage_packet_path"))
        or _non_empty_text(refs.get("immutable_dispatch_path"))
        or _non_empty_text(refs.get("dispatch_path"))
    )


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


__all__ = [
    "handoff_dispatch_path",
    "handoff_work_unit_id",
    "materialized_record_only_provider_handoff",
    "materialized_record_only_provider_handoffs",
    "provider_admission_pending_dispatch_result",
]
