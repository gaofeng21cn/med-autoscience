from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .primitives import _compact_mapping, _dedupe_text, _text


def work_unit_from_action_queue(value: object) -> dict[str, Any] | str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if not isinstance(item, Mapping):
            continue
        unit = work_unit_projection(item.get("next_work_unit"))
        if unit is not None:
            return unit
        for key in ("controller_work_unit_id", "work_unit_id", "action_type"):
            text = _text(item.get(key))
            if text is not None:
                return text
    return None


def work_unit_from_action(action: Mapping[str, Any] | None) -> dict[str, Any] | str | None:
    if action is None:
        return None
    unit = work_unit_projection(action.get("next_work_unit"))
    if unit is not None:
        return unit
    for key in ("controller_work_unit_id", "work_unit_id", "action_type"):
        text = _text(action.get(key))
        if text is not None:
            return text
    return None


def work_unit_from_current_action(action: Mapping[str, Any]) -> dict[str, Any] | str | None:
    work_unit_id = _text(action.get("work_unit_id"))
    if work_unit_id is None:
        return None
    if _text(action.get("source")) == "stage_artifact_index.next_owner_action":
        return {"unit_id": work_unit_id}
    return work_unit_id


def work_unit_projection(value: object) -> dict[str, Any] | str | None:
    if isinstance(value, Mapping):
        return _compact_mapping(
            value,
            (
                "unit_id",
                "lane",
                "summary",
                "owner",
                "route_target",
                "action_type",
            ),
        ) or dict(value)
    return _text(value)


def work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def owner_from_action(action: Mapping[str, Any] | None) -> str | None:
    if action is None:
        return None
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
    )


def explicit_wakeup_hydration_work_unit(launch_policy: Mapping[str, Any]) -> str | None:
    if launch_policy.get("explicit_user_wakeup_recorded") is not True:
        return None
    if launch_policy.get("owner_handoff_hydration_required") is not True:
        return None
    return _text(launch_policy.get("owner_handoff_hydration_action")) or "hydrate_opl_owner_route_from_explicit_resume"


def explicit_wakeup_hydration_owner(launch_policy: Mapping[str, Any]) -> str | None:
    if explicit_wakeup_hydration_work_unit(launch_policy) is None:
        return None
    return _text(launch_policy.get("owner_handoff_hydration_owner")) or "one-person-lab"


def owner_handoff_hydration_projection(launch_policy: Mapping[str, Any]) -> dict[str, Any] | None:
    work_unit = explicit_wakeup_hydration_work_unit(launch_policy)
    if work_unit is None:
        return None
    return {
        "required": True,
        "owner": explicit_wakeup_hydration_owner(launch_policy),
        "action": work_unit,
        "explicit_user_wakeup_ref": _text(launch_policy.get("explicit_user_wakeup_ref")),
        "study_truth_snapshot_ref": _text(launch_policy.get("study_truth_snapshot_ref")),
    }


def source_refs(
    value: object,
    *,
    handoff: Mapping[str, Any],
    latest_terminal_stage_log: Mapping[str, Any],
) -> list[str]:
    refs: list[object] = []
    if isinstance(value, Mapping):
        refs.extend(value.values())
    refs.append(handoff.get("source_path"))
    refs.append(latest_terminal_stage_log.get("source_path"))
    refs.extend(latest_terminal_stage_log.get("closeout_refs") or [])
    return _dedupe_text(refs)[:20]


def running_provider_attempt_ref(
    *,
    running_provider_attempt: bool | None,
    handoff: Mapping[str, Any],
    key: str,
) -> str | None:
    if running_provider_attempt is not True:
        return None
    return _text(handoff.get(key))


def observability_active_run_id(
    *,
    running_provider_attempt: bool | None,
    handoff: Mapping[str, Any],
) -> str | None:
    if running_provider_attempt is True:
        return None
    active_run_id = _text(handoff.get("active_run_id"))
    if active_run_id is None or active_run_id.startswith("opl-stage-attempt://"):
        return None
    return active_run_id


def stale_active_run_id(
    *,
    running_provider_attempt: bool | None,
    payload: Mapping[str, Any],
    supervision: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> str | None:
    if running_provider_attempt is True:
        return None
    observability_run_id = observability_active_run_id(
        running_provider_attempt=running_provider_attempt,
        handoff=handoff,
    )
    for active_run_id in (
        _text(supervision.get("active_run_id")),
        _text(payload.get("active_run_id")),
        _text(handoff.get("active_run_id")),
    ):
        if active_run_id is not None and active_run_id != observability_run_id:
            return active_run_id
    return None


__all__ = [
    "explicit_wakeup_hydration_owner",
    "explicit_wakeup_hydration_work_unit",
    "observability_active_run_id",
    "owner_from_action",
    "owner_handoff_hydration_projection",
    "running_provider_attempt_ref",
    "source_refs",
    "stale_active_run_id",
    "work_unit_from_action",
    "work_unit_from_action_queue",
    "work_unit_from_current_action",
    "work_unit_id",
    "work_unit_projection",
]
