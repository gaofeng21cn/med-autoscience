from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.command_metadata import (
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    action_intent as _action_intent,
)
from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _mapping,
    _optional_text,
)
from med_autoscience.controllers.study_domain_transition_guard import (
    redrive_block_payload as _domain_transition_redrive_block_payload,
)


def drive_domain_transition_redrive_stop_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: Path,
    source: str,
    inspect_readback: Mapping[str, Any] | None,
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any] | None:
    readback = _mapping(inspect_readback)
    block = drive_domain_transition_redrive_block_payload(readback)
    if block is None:
        return None
    next_action = _mapping(readback.get("next_action"))
    drive_result = {
        "surface_kind": "paper_mission_drive_result",
        "status": "domain_transition_auto_redrive_halted",
        **block,
        "can_submit_to_opl_runtime": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "drive_mode": "domain_transition_auto_redrive_halted",
        "dry_run": False,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "mission_id": readback.get("mission_id"),
        "objective": readback.get("objective"),
        "output_root": str(output_root),
        "inspect_readback": dict(readback),
        "domain_transition": _mapping(readback.get("domain_transition")) or None,
        "receipt_owner_consumption_readback": _mapping(
            readback.get("receipt_owner_consumption_readback")
        )
        or None,
        "stage_closure_decision": _mapping(readback.get("stage_closure_decision"))
        or None,
        **({"next_action": dict(next_action)} if next_action else {}),
        "drive_result": drive_result,
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": False,
            "writes_yang_ops_consumption_ledger": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": True,
        },
        "output_manifest": {
            "mode": "paper_mission_drive_domain_transition_auto_redrive_halted",
            "output_root": str(output_root),
            "candidate_package": None,
            "consumption_ledger": None,
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_runtime": False,
            "writes_candidate_workspace": False,
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def drive_domain_transition_redrive_block_payload(
    readback: Mapping[str, Any],
) -> dict[str, Any] | None:
    block = _domain_transition_redrive_block_payload(readback)
    if block is None:
        return None
    if _optional_text(block.get("domain_transition_decision_type")) != (
        "owner_apply_receipt_consumed"
    ):
        return None
    return block


__all__ = [
    "drive_domain_transition_redrive_block_payload",
    "drive_domain_transition_redrive_stop_readback",
]
