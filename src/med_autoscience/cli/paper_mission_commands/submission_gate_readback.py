from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import _mapping
from med_autoscience.cli.paper_mission_commands.transaction_readback import (
    _submission_authority_owner_gate_readback,
)


def apply_submission_authority_owner_gate_readback(
    *,
    study_root: Path,
    study_id: str,
    transaction_output_fields: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    output_fields = dict(transaction_output_fields)
    submission_gate_readback = _submission_authority_owner_gate_readback(
        study_root=study_root,
        study_id=study_id,
        next_action=_mapping(output_fields.get("next_action")),
    )
    if submission_gate_readback is None:
        return output_fields, (
            dict(typed_blocker_resolution_readback)
            if typed_blocker_resolution_readback is not None
            else None
        ), None

    output_fields.pop("next_action", None)
    readback_payload = _mapping(output_fields.get("paper_mission_transaction_readback"))
    if readback_payload:
        readback_payload.pop("next_action", None)
        output_fields["paper_mission_transaction_readback"] = readback_payload

    typed_blocker_readback = (
        {
            **typed_blocker_resolution_readback,
            "next_owner_action": None,
            "submission_authority_owner_gate_readback": submission_gate_readback,
        }
        if typed_blocker_resolution_readback is not None
        else None
    )
    return output_fields, typed_blocker_readback, submission_gate_readback


__all__ = ["apply_submission_authority_owner_gate_readback"]
