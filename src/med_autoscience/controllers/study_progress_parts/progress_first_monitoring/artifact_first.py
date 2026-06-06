from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def artifact_first_owner_action(current_action: Mapping[str, Any]) -> bool:
    return _text(current_action.get("source")) == "stage_artifact_index.next_owner_action"


def current_action_from_stage_artifact_index(payload: Mapping[str, Any]) -> dict[str, Any]:
    index = _mapping(payload.get("stage_artifact_index"))
    if _text(index.get("surface_kind")) != "stage_artifact_index":
        return {}
    action = _mapping(index.get("next_owner_action"))
    owner = _text(action.get("next_owner")) or _text(action.get("owner"))
    work_unit_id = _text(action.get("work_unit_id")) or _text(action.get("required_output_surface"))
    allowed_actions = _text_list(action.get("allowed_actions"))
    action_type = _text(action.get("action_type"))
    if not allowed_actions and action_type is not None:
        allowed_actions = [action_type]
    if owner is None and work_unit_id is None and not allowed_actions:
        return {}
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "stage_artifact_index.next_owner_action",
        "next_owner": owner,
        "work_unit_id": work_unit_id,
        "allowed_actions": allowed_actions,
        "owner_receipt_required": bool(action.get("owner_receipt_required", True)),
        "required_delta_kind": _text(action.get("required_delta_kind")) or "stage_artifact_delta",
        "target_surface": _stage_artifact_target_surface(action),
        "target_surface_specificity": _text(action.get("target_surface_specificity"))
        or "artifact_first_stage_target",
        "acceptance_refs": _text_list(action.get("acceptance_refs")),
        "artifact_native_contract_ref": _text(action.get("artifact_native_contract_ref"))
        or _text(index.get("artifact_native_contract_ref")),
        "stage_artifact_contract_refs": _stage_artifact_contract_refs(action),
        "artifact_first_precedence": {
            "stale_platform_repairs_superseded": bool(_sequence(index.get("stale_platform_repairs"))),
            "provider_completion_is_paper_progress": False,
        },
        "authority_boundary": _authority_boundary(action),
    }


def stage_artifact_index_monitoring_projection(value: object) -> dict[str, Any] | None:
    index = _mapping(value)
    if _text(index.get("surface_kind")) != "stage_artifact_index":
        return None
    return {
        "surface_kind": "stage_artifact_index_monitoring_projection",
        "current_stage": index.get("current_stage"),
        "artifact_native_contract_ref": _text(index.get("artifact_native_contract_ref")),
        "next_owner_action_source": (
            "stage_artifact_index.next_owner_action" if _mapping(index.get("next_owner_action")) else None
        ),
        "stale_platform_repair_count": len(_sequence(index.get("stale_platform_repairs"))),
        "authority_boundary": {
            "projection_only": True,
            "can_write_mas_truth": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def terminal_publication_gate_action(stage_artifact_action: Mapping[str, Any]) -> bool:
    return (
        stage_artifact_action.get("terminal_publication_handoff") is True
        or stage_artifact_action.get("action_type") == "publication_handoff_owner_gate"
        or stage_artifact_action.get("required_delta_kind")
        == "publication_handoff_owner_receipt_or_typed_blocker"
    )


def stage_artifact_index_has_precedence_evidence(
    value: object,
    *,
    typed_blocker: Mapping[str, Any],
) -> bool:
    index = _mapping(value)
    if _sequence(index.get("stale_platform_repairs")):
        return True
    if _typed_blocker_is_runtime_or_platform_repair(typed_blocker):
        return False
    for stage in _sequence(index.get("stages")):
        state = _mapping(stage)
        if _sequence(state.get("observed_artifact_refs")):
            return True
    return False


def _typed_blocker_is_runtime_or_platform_repair(typed_blocker: Mapping[str, Any]) -> bool:
    haystack = " ".join(
        value
        for value in (
            _text(typed_blocker.get("blocker_id")),
            _text(typed_blocker.get("blocker_type")),
            _text(typed_blocker.get("reason")),
            _text(typed_blocker.get("reason_code")),
            _text(typed_blocker.get("owner")),
            _text(typed_blocker.get("work_unit_id")),
        )
        if value
    )
    return any(marker in haystack for marker in ("runtime", "platform_repair", "read_model_reconcile"))


def _stage_artifact_target_surface(action: Mapping[str, Any]) -> dict[str, Any] | None:
    target = _mapping(action.get("target_surface"))
    if target:
        return target
    required = _text(action.get("required_output_surface"))
    if required is None:
        return None
    return {
        "ref_kind": "stage_artifact_index_required_output",
        "surface_ref": required,
    }


def _stage_artifact_contract_refs(action: Mapping[str, Any]) -> dict[str, Any]:
    refs = {
        "manifest_ref": _text(action.get("manifest_ref")),
        "receipt_ref": _text(action.get("receipt_ref")),
    }
    return {key: value for key, value in refs.items() if value is not None}


def _authority_boundary(action: Mapping[str, Any]) -> dict[str, bool]:
    boundary = _mapping(action.get("authority_boundary"))
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": bool(boundary.get("can_authorize_quality_verdict", False)),
        "can_authorize_publication_ready": bool(
            boundary.get("can_authorize_publication_readiness", False)
            or boundary.get("can_authorize_publication_ready", False)
        ),
        "stage_artifact_index_is_derived_projection": True,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list | tuple) else []


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _text(item)
        if text is None or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result
