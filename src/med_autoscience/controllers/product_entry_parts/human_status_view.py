from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import study_progress
from opl_harness_shared.status_narration import (
    build_status_narration_human_view as _build_shared_status_narration_human_view,
)

from .shared_labels import _non_empty_text


def _status_narration_human_view(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _build_shared_status_narration_human_view(
        payload,
        fallback_current_stage=_non_empty_text(payload.get("current_stage"))
        or _non_empty_text(payload.get("current_stage_id")),
        fallback_latest_update=_non_empty_text(payload.get("current_stage_summary"))
        or _non_empty_text(payload.get("summary")),
        fallback_next_step=_non_empty_text(payload.get("next_system_action")),
        fallback_blockers=payload.get("current_blockers") or [],
    )


def _append_human_status_lines(lines: list[str], payload: Mapping[str, Any]) -> None:
    human_view = _status_narration_human_view(payload)
    has_status_contract = isinstance(payload.get("status_narration_contract"), Mapping)
    current_stage = _non_empty_text(human_view.get("current_stage_label")) or _non_empty_text(
        payload.get("current_stage")
    ) or _non_empty_text(payload.get("current_stage_id"))
    if has_status_contract:
        judgment = _non_empty_text(human_view.get("status_summary")) or _non_empty_text(
            human_view.get("latest_update")
        )
    else:
        judgment = _non_empty_text(human_view.get("latest_update")) or _non_empty_text(
            human_view.get("status_summary")
        )
    next_step = _non_empty_text(human_view.get("next_step"))
    if current_stage:
        lines.append(f"- 当前阶段: {current_stage}")
    if judgment:
        lines.append(f"- 当前判断: {judgment}")
    if next_step:
        lines.append(f"- 下一步建议: {next_step}")


def _operator_handling_state_label(payload: Mapping[str, Any]) -> str | None:
    explicit_label = _non_empty_text(payload.get("handling_state_label"))
    if explicit_label is not None:
        return explicit_label
    handling_state = _non_empty_text(payload.get("handling_state"))
    if handling_state is None:
        return None
    return study_progress._OPERATOR_STATUS_HANDLING_LABELS.get(
        handling_state,
        handling_state.replace("_", " "),
    )


def _recovery_action_mode_label(payload: Mapping[str, Any]) -> str | None:
    action_mode = _non_empty_text(payload.get("action_mode"))
    if action_mode is None:
        return None
    return study_progress._RECOVERY_ACTION_MODE_LABELS.get(
        action_mode,
        action_mode.replace("_", " "),
    )
