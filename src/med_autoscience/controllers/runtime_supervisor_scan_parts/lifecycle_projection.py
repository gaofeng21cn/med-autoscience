from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import action_projection
from med_autoscience.controllers.runtime_supervisor_scan_parts import block_state
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode


def maybe_blocked_lifecycle_from_scan(
    *,
    developer_mode: DeveloperSupervisorMode,
    lifecycle: Mapping[str, Any],
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    control_allowed_write_surfaces: list[str],
    request_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> Mapping[str, Any]:
    blocked_reason = action_projection.blocked_reason_from_scan(
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    if blocked_reason is None and block_state.ai_reviewer_lifecycle_resolved(
        lifecycle=lifecycle,
        ai_reviewer_assessment=ai_reviewer_assessment,
    ):
        return {}
    if not should_refresh_blocked_lifecycle(
        developer_mode=developer_mode,
        lifecycle=lifecycle,
        blocked_reason=blocked_reason,
    ):
        return lifecycle
    repair_payload = repair_action_payload(study_root=study_root)
    if repair_payload is None or blocked_reason is None:
        return lifecycle
    return blocked_lifecycle_from_repair(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        repair_payload=repair_payload,
        blocked_reason=blocked_reason,
        next_owner=block_state.next_owner_for_blocked_reason(blocked_reason),
        control_allowed_write_surfaces=control_allowed_write_surfaces,
        request_allowed_write_surfaces=request_allowed_write_surfaces,
        forbidden_actions=forbidden_actions,
    ) or {}


def should_refresh_blocked_lifecycle(
    *,
    developer_mode: DeveloperSupervisorMode,
    lifecycle: Mapping[str, Any],
    blocked_reason: str | None,
) -> bool:
    if not developer_mode.safe_actions_enabled:
        return False
    if not lifecycle:
        return True
    return bool(
        blocked_reason is not None
        and (
            lifecycle.get("projection_only") is True
            or _text(lifecycle.get("blocked_reason")) != blocked_reason
            or (
                blocked_reason == "publication_gate_specificity_required"
                and (
                    lifecycle.get("external_supervisor_required") is True
                    or _text(lifecycle.get("authority")) == "external_supervisor"
                    or _text(lifecycle.get("next_owner")) != "publication_gate"
                )
            )
        )
    )


def repair_action_payload(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json")


def blocked_lifecycle_from_repair(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    repair_payload: Mapping[str, Any],
    blocked_reason: str,
    next_owner: str,
    control_allowed_write_surfaces: list[str],
    request_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> dict[str, Any] | None:
    action = first_repair_action(repair_payload)
    if action is None:
        return None
    safe_action = sanitize_repair_action_for_supervision(
        action,
        request_allowed_write_surfaces=request_allowed_write_surfaces,
        forbidden_actions=forbidden_actions,
    )
    authority = "external_supervisor" if next_owner == "external_supervisor" else "observability_only"
    payload = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": _text(repair_payload.get("study_id")) or study_id,
        "quest_id": _text(repair_payload.get("quest_id")) or quest_id,
        "state": "blocked",
        "authority": authority,
        "allowed_write_surfaces": list(control_allowed_write_surfaces),
        "forbidden_actions": list(forbidden_actions),
        "top_action": safe_action,
        "auto_apply_allowed": bool(safe_action.get("auto_apply_allowed")),
        "last_apply_attempt_at": utc_now(),
        "applied_at": None,
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": authority == "external_supervisor",
        "quality_gate_relaxation_allowed": False,
        "last_apply_attempt": {
            "state": "blocked",
            "dispatch_status": "not_dispatched",
            "reason": blocked_reason,
            "source": "runtime_supervisor_scan",
        },
        "refs": {
            "repair_action_path": str(study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"),
        },
    }
    _write_json(study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json", payload)
    return payload


def first_repair_action(repair_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if _text(repair_payload.get("state")) != "ready_for_repair":
        return None
    actions = repair_payload.get("actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if isinstance(action, Mapping):
            return dict(action)
    return None


def sanitize_repair_action_for_supervision(
    action: Mapping[str, Any],
    *,
    request_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> dict[str, Any]:
    sanitized = dict(action)
    sanitized["paper_package_mutation_allowed"] = False
    sanitized["manual_study_patch_allowed"] = False
    sanitized["quality_gate_relaxation_allowed"] = False
    sanitized["medical_claim_authoring_allowed"] = False
    sanitized["requested_write_surfaces"] = list(request_allowed_write_surfaces)
    sanitized["forbidden_actions"] = list(forbidden_actions)
    return sanitized


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "blocked_lifecycle_from_repair",
    "first_repair_action",
    "maybe_blocked_lifecycle_from_scan",
    "repair_action_payload",
    "sanitize_repair_action_for_supervision",
    "should_refresh_blocked_lifecycle",
]
