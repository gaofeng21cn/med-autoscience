from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)
from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    gate_replay_consumed_by_source_eval,
)


def action_consumed_by_dispatch_receipt(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    consumption = _mapping(_mapping(progress.get("progress_first_monitoring_summary")).get("dispatch_consumption"))
    if not consumption:
        consumption = _mapping(progress.get("dispatch_consumption"))
    if _text(consumption.get("consumption_status")) not in {"consumed", "receipt_consumed"}:
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    consumed_work_unit = _work_unit_id(consumption.get("work_unit_id"))
    if action_work_unit is None or consumed_work_unit != action_work_unit:
        return False
    action_fingerprints = {
        text
        for value in (
            action.get("work_unit_fingerprint"),
            action.get("action_fingerprint"),
            action.get("fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if not action_fingerprints:
        current_action = _mapping(progress.get("current_executable_owner_action"))
        current_action_work_unit = _work_unit_id(current_action.get("work_unit_id")) or _work_unit_id(
            current_action.get("next_work_unit")
        )
        if (
            current_action_work_unit == action_work_unit
            and _text(current_action.get("action_type")) == _text(action.get("action_type"))
        ):
            action_fingerprints.update(
                text
                for value in (
                    current_action.get("work_unit_fingerprint"),
                    current_action.get("action_fingerprint"),
                    current_action.get("fingerprint"),
                )
                if (text := _text(value)) is not None
            )
    consumed_fingerprints = {
        text
        for value in (
            consumption.get("work_unit_fingerprint"),
            consumption.get("action_fingerprint"),
            _mapping(consumption.get("canonical_work_unit_identity")).get("work_unit_fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if not action_fingerprints or not consumed_fingerprints:
        return False
    if action_fingerprints.intersection(consumed_fingerprints):
        return True
    return gate_replay_consumed_by_source_eval(
        action=action,
        consumption=consumption,
        mapping=_mapping,
        text=_text,
    )


__all__ = ["action_consumed_by_dispatch_receipt"]
