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
            control_plane_route_context=_control_plane_route_context(dispatch),
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


def _control_plane_route_context(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    next_work_unit_raw = source_action.get("next_work_unit") or dispatch.get("next_work_unit") or prompt_contract.get("next_work_unit")
    next_work_unit = _mapping(next_work_unit_raw)
    work_unit_id = _work_unit_id(next_work_unit_raw)
    return {
        "control_surface": "domain_owner_action_dispatch",
        "controller_action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": (
            _text(source_action.get("work_unit_fingerprint"))
            or _text(dispatch.get("work_unit_fingerprint"))
            or _text(_mapping(dispatch.get("owner_route")).get("work_unit_fingerprint"))
        ),
        "next_work_unit": dict(next_work_unit) if next_work_unit else None,
        "route_target": _text(source_action.get("route_target")) or _text(dispatch.get("route_target")),
        "route_key_question": _text(source_action.get("route_key_question")) or _text(dispatch.get("route_key_question")),
        "route_rationale": _text(source_action.get("route_rationale")) or _text(dispatch.get("route_rationale")),
    }


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
