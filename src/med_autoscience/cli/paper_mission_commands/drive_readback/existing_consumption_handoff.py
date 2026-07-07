from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_commands.command_metadata import (
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    action_intent as _action_intent,
)
from med_autoscience.cli.paper_mission_commands.common import (
    _load_json_object,
    _mapping,
    _optional_text,
)
from med_autoscience.cli.paper_mission_commands.drive_helpers import (
    paper_mission_drive_followthrough_empty as _paper_mission_drive_followthrough_empty,
    paper_mission_drive_result as _paper_mission_drive_result,
)
from med_autoscience.cli.paper_mission_commands.opl_runtime_submission import (
    opl_runtime_submission_readback as _opl_runtime_submission_readback,
    refresh_consume_readback_after_opl_submission as _refresh_consume_readback_after_opl_submission,
)


def existing_consumption_handoff_drive_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: Path,
    submit_opl_runtime: bool | None,
    opl_bin: str | Path | None,
    source: str,
    handoff: Mapping[str, Any],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    source_ref = _optional_text(handoff.get("source_ref"))
    consume_readback = _load_existing_consumption_readback(source_ref)
    if not consume_readback:
        consume_readback = {
            "surface_kind": "paper_mission_existing_consumption_handoff_readback",
            "schema_version": 1,
            "mission_id": _optional_text(handoff.get("mission_id"))
            or "paper-mission::unknown",
            "objective": "reuse latest paper mission consumption route handoff",
            "study_id": study_id,
            "study_root": str(Path(profile.studies_root) / study_id),
            "candidate_ref": _optional_text(handoff.get("candidate_ref")),
            "paper_mission_transaction": _mapping(
                handoff.get("paper_mission_transaction")
            ),
            "stage_terminal_decision": _mapping(
                handoff.get("stage_terminal_decision")
            ),
            "opl_route_command": _mapping(handoff.get("opl_route_command")),
            "opl_runtime_carrier": _mapping(handoff.get("opl_runtime_carrier")),
            "transaction_state": _optional_text(handoff.get("transaction_state"))
            or "ready_for_opl_route_command",
            "consume_candidate_status": _optional_text(handoff.get("status"))
            or "accepted_candidate",
            "next_action": _mapping(handoff.get("next_action")),
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": _optional_text(handoff.get("next_owner")),
                "human_decision_required": False,
                "summary": "Reuse latest materialized paper mission route handoff.",
                "can_execute": False,
                "can_authorize_provider_admission": False,
            },
            "consume_output_manifest": {
                "mode": "existing_consumption_handoff",
                "opl_route_handoff": dict(handoff),
                "opl_route_handoff_ref": source_ref,
                "route_handoff_status": _optional_text(handoff.get("handoff_status")),
                "next_owner": _optional_text(handoff.get("next_owner")),
                "writes_authority": False,
                "writes_runtime": False,
                "writes_yang_authority": False,
            },
        }
    if "objective" not in consume_readback:
        decision = _mapping(consume_readback.get("stage_terminal_decision"))
        consume_readback = {
            **consume_readback,
            "objective": _optional_text(decision.get("next_work_unit"))
            or "reuse latest paper mission consumption route handoff",
        }
    if "next_owner_or_human_decision" not in consume_readback:
        decision = _mapping(consume_readback.get("stage_terminal_decision"))
        consume_readback = {
            **consume_readback,
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": _optional_text(decision.get("next_owner"))
                or _optional_text(handoff.get("next_owner")),
                "human_decision_required": False,
                "summary": _optional_text(decision.get("reason"))
                or "Reuse latest materialized paper mission route handoff.",
                "can_execute": False,
                "can_authorize_provider_admission": False,
            },
        }
    if "consume_output_manifest" not in consume_readback:
        consume_readback = {
            **consume_readback,
            "consume_output_manifest": {
                "mode": "existing_consumption_handoff",
                "opl_route_handoff": dict(handoff),
                "opl_route_handoff_ref": source_ref,
                "route_handoff_status": _optional_text(handoff.get("handoff_status")),
                "next_owner": _optional_text(handoff.get("next_owner")),
                "writes_authority": False,
                "writes_runtime": False,
                "writes_yang_authority": False,
            },
        }
    runtime_submit_requested = submit_opl_runtime is not False
    opl_runtime_submission = _opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=runtime_submit_requested,
        opl_bin=opl_bin,
    )
    refreshed_consume_readback = _refresh_consume_readback_after_opl_submission(
        consume_readback=consume_readback,
        opl_runtime_submission=opl_runtime_submission,
    )
    drive_result = _paper_mission_drive_result(
        consume_readback=refreshed_consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
    )
    package_readback = {
        "surface_kind": "paper_mission_existing_consumption_handoff_package_readback",
        "schema_version": 1,
        "status": "skipped_existing_consumption_handoff",
        "reason": (
            "A materialized consumption route handoff already exists; drive reused "
            "it instead of requiring a one-shot migration package."
        ),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "output_manifest": {
            "mode": "existing_consumption_handoff",
            "package_manifest_ref": _optional_text(handoff.get("candidate_ref")),
            "opl_route_handoff_ref": source_ref,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
        },
    }
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "drive_mode": "existing_consumption_handoff",
        "dry_run": False,
        "profile": package_readback["profile"],
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": package_readback["study_root"],
        "study_root_exists": package_readback["study_root_exists"],
        "mission_id": refreshed_consume_readback["mission_id"],
        "objective": refreshed_consume_readback["objective"],
        "output_root": str(output_root),
        "candidate_package_readback": package_readback,
        "authority_consume_readback": refreshed_consume_readback.get(
            "authority_consume_readback"
        ),
        "consume_readback": refreshed_consume_readback,
        "stage_terminal_decision": refreshed_consume_readback["stage_terminal_decision"],
        "opl_route_command": refreshed_consume_readback["opl_route_command"],
        "opl_runtime_carrier": refreshed_consume_readback["opl_runtime_carrier"],
        "opl_runtime_carrier_readback": refreshed_consume_readback.get(
            "opl_runtime_carrier_readback"
        )
        or {},
        "opl_runtime_readback_status": refreshed_consume_readback.get(
            "opl_runtime_readback_status"
        )
        or "not_requested",
        "terminal_owner_gate": refreshed_consume_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": refreshed_consume_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": refreshed_consume_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "semantic_progress_signature": refreshed_consume_readback.get(
            "semantic_progress_signature"
        ),
        "route_back_budget": refreshed_consume_readback.get("route_back_budget"),
        "mission_executor_fallback_action": refreshed_consume_readback.get(
            "mission_executor_fallback_action"
        ),
        "carry_forward_risk_receipt_ref": refreshed_consume_readback.get(
            "carry_forward_risk_receipt_ref"
        ),
        "opl_route_handoff": dict(handoff),
        "opl_runtime_submission": opl_runtime_submission,
        "followthrough": _paper_mission_drive_followthrough_empty(
            route_back_budget_ledger={},
            route_back_budget_ledger_ref=output_root / "route_back_budget.json",
            progress_guard={},
            stage_closure_decision={},
            stop_reason="existing_consumption_handoff_reused",
        ),
        "drive_result": drive_result,
        "transaction_state": refreshed_consume_readback["transaction_state"],
        "consume_candidate_status": refreshed_consume_readback[
            "consume_candidate_status"
        ],
        "next_owner_or_human_decision": refreshed_consume_readback[
            "next_owner_or_human_decision"
        ],
        "next_action": refreshed_consume_readback.get("next_action"),
        "stage_closure_decision": None,
        "stage_closure_decision_ref": None,
        "stage_closure_outcome": None,
        "durable_mission_stop_guard": {
            "surface_kind": "paper_mission_durable_stop_guard",
            "accepted_submission_milestone_candidate_is_durable_stop": False,
            "durable_stop_allowed": False,
            "can_claim_paper_progress": False,
        },
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": bool(opl_runtime_submission.get("writes_runtime")),
            "writes_yang_authority": False,
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "output_manifest": {
            "mode": "paper_mission_drive_existing_consumption_handoff",
            "output_root": str(output_root),
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_runtime": bool(opl_runtime_submission.get("writes_runtime")),
            "consumption_ledger": refreshed_consume_readback.get(
                "consume_output_manifest"
            ),
            "candidate_package": package_readback.get("output_manifest"),
        },
    }


def _load_existing_consumption_readback(source_ref: str | None) -> dict[str, Any]:
    if source_ref is None:
        return {}
    handoff_path = Path(source_ref).expanduser()
    if handoff_path.name != "opl_route_handoff.json":
        return {}
    readback_path = handoff_path.with_name("consume_readback.json")
    try:
        payload = _load_json_object(readback_path)
    except (OSError, ValueError):
        return {}
    return _mapping(payload)
