from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import quality_repair_batch
from med_autoscience.profiles import WorkspaceProfile


def execute_quality_repair_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any],
    quest_root: Path | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "quest_root": str(quest_root),
        }
    try:
        owner_result = quality_repair_batch.run_quality_repair_batch(
            profile=profile,
            study_id=study_id,
            study_root=profile.studies_root / study_id,
            quest_id=quest_root.name,
            source="domain_owner_action_dispatch",
            authority_route_context=_authority_route_context(dispatch),
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": str(exc) or "quality_repair_batch_failed",
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "quest_root": str(quest_root),
        }
    result_payload = dict(owner_result) if isinstance(owner_result, Mapping) else {}
    handoff_ready = (
        result_payload.get("status") == "handoff_ready"
        and isinstance(result_payload.get("writer_worker_handoff"), Mapping)
    )
    if handoff_ready and _dispatch_consumes_quality_repair_writer_handoff(dispatch):
        blocker = _quality_repair_handoff_blocker(result_payload)
        return {
            "execution_status": "blocked",
            "blocked_reason": blocker,
            "typed_blocker": blocker,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": result_payload,
            "consumed_writer_handoff_empty_spin_blocked": True,
            "required_next_owner": "write",
            "required_output_surface": _text(dispatch.get("required_output_surface"))
            or _text(_mapping(dispatch.get("prompt_contract")).get("required_output_surface")),
            "quest_root": str(quest_root),
        }
    executed = bool(owner_result.get("ok")) if isinstance(owner_result, Mapping) else False
    return {
        "execution_status": "handoff_ready" if handoff_ready else ("executed" if executed else "blocked"),
        "blocked_reason": (
            None
            if executed or handoff_ready
            else _text(result_payload.get("blocked_reason"))
            or _text(result_payload.get("status"))
            or "quality_repair_batch_not_applied"
        ),
        "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
        "owner_result": result_payload if result_payload else owner_result,
        **({"writer_worker_handoff": dict(result_payload["writer_worker_handoff"])} if handoff_ready else {}),
        "quest_root": str(quest_root),
    }


def _authority_route_context(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    next_work_unit_raw = source_action.get("next_work_unit") or dispatch.get("next_work_unit") or prompt_contract.get("next_work_unit")
    next_work_unit = _mapping(next_work_unit_raw)
    work_unit_id = _work_unit_id(next_work_unit_raw)
    work_unit_fingerprint = (
        _text(source_action.get("work_unit_fingerprint"))
        or _text(dispatch.get("work_unit_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
    )
    source_eval_id = _text(source_action.get("source_eval_id")) or _text(
        _mapping(owner_route.get("source_refs")).get("source_eval_id")
    )
    flat_context = {
        "control_surface": "domain_owner_action_dispatch",
        "controller_action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": dict(next_work_unit) if next_work_unit else None,
        "route_target": _text(source_action.get("route_target")) or _text(dispatch.get("route_target")),
        "route_key_question": _text(source_action.get("route_key_question")) or _text(dispatch.get("route_key_question")),
        "route_rationale": _text(source_action.get("route_rationale")) or _text(dispatch.get("route_rationale")),
        "current_owner_route": dict(owner_route) if owner_route else None,
    }
    if work_unit_id is not None:
        flat_context["controller_route_context"] = {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        }
    return {
        **flat_context,
    }


def _dispatch_consumes_quality_repair_writer_handoff(dispatch: Mapping[str, Any]) -> bool:
    if _text(dispatch.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(dispatch.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(dispatch.get("next_executable_owner")) != "write":
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return False
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return False
    route = _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    return _text(route.get("next_owner")) == "write" and route_reason == "manuscript_story_surface_delta_missing"


def _quality_repair_handoff_blocker(result_payload: Mapping[str, Any]) -> str:
    evidence = _mapping(result_payload.get("repair_execution_evidence"))
    for candidate in (
        result_payload.get("blocked_reason"),
        _first_text(evidence.get("blockers")),
        _first_text(_mapping(evidence.get("manuscript_surface_hygiene")).get("blockers")),
        _mapping(result_payload.get("writer_worker_handoff")).get("typed_blocker_if_unresolved"),
    ):
        if text := _text(candidate):
            return text
    return "manuscript_story_surface_delta_missing"


def _first_text(value: object) -> str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if text := _text(item):
            return text
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["execute_quality_repair_batch"]
