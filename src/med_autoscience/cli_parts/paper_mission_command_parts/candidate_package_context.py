from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def mission_executor_handoff(
    *,
    readback: Mapping[str, Any],
    foreground_owner_decision_summary: Mapping[str, Any],
    candidate_package_forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    terminal_decision = _mapping(readback.get("stage_terminal_decision"))
    route_command = _mapping(readback.get("opl_route_command"))
    next_decision = _mapping(readback.get("next_owner_or_human_decision"))
    next_owner = _first_text(
        next_decision.get("next_owner"),
        foreground_owner_decision_summary.get("next_owner"),
        terminal_decision.get("next_owner"),
    )
    decision_kind = _optional_text(terminal_decision.get("decision_kind"))
    is_route_back = decision_kind == "route_back" or next_owner == "mission_executor"
    handoff_status = (
        "ready_for_mission_executor"
        if is_route_back
        else "not_routed_to_mission_executor"
    )
    return {
        "surface_kind": "paper_mission_executor_handoff",
        "schema_version": 1,
        "status": handoff_status,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "next_owner": next_owner,
        "handoff_reason": _first_text(
            terminal_decision.get("reason"),
            foreground_owner_decision_summary.get("blocked_reason"),
            readback.get("consume_candidate_status"),
        ),
        "route_back_evidence_ref": terminal_decision.get("route_back_evidence_ref"),
        "repair_scope": terminal_decision.get("repair_scope"),
        "target_stage_id": terminal_decision.get("target_stage_id")
        or terminal_decision.get("next_stage_id"),
        "current_terminal_decision": {
            "decision_kind": decision_kind,
            "status": terminal_decision.get("status"),
            "route_command": route_command.get("command_kind"),
            "source_terminal_decision_ref": route_command.get(
                "source_terminal_decision_ref"
            ),
        },
        "input_refs": foreground_owner_decision_summary.get("input_refs", {}),
        "runtime_touchpoint": foreground_owner_decision_summary.get(
            "runtime_touchpoint", {}
        ),
        "expected_paper_facing_outputs": [
            {
                "kind": "manuscript_patch_plan",
                "required": True,
                "authority_note": "candidate plan only until MAS consumes it",
            },
            {
                "kind": "claim_evidence_ledger_delta",
                "required": True,
                "authority_note": "candidate delta only until MAS consumes it",
            },
            {
                "kind": "figure_table_caption_delta",
                "required": True,
                "authority_note": "candidate delta only until MAS consumes it",
            },
            {
                "kind": "reviewer_gate_response_draft",
                "required": True,
                "authority_note": "candidate response only until MAS consumes it",
            },
            {
                "kind": "owner_decision_packet",
                "required": True,
                "authority_note": "submit through MAS authority consume path",
            },
        ],
        "resume_path": (
            "Mission executor should use this handoff to produce a paper-facing "
            "candidate artifact delta and owner decision packet; MAS remains the "
            "authority that accepts, rejects, routes back, blocks, or asks a human."
        ),
        "authority_boundary": {
            "candidate_is_authority": False,
            "authority_materialized_by_this_handoff": False,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_authorize_provider_admission": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
        "forbidden_authority_writes": list(candidate_package_forbidden_authority_writes),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def foreground_owner_decision_summary(
    *,
    readback: Mapping[str, Any],
    candidate_manifest: Mapping[str, Any],
    candidate_artifact_delta: Mapping[str, Any],
    owner_decision_packet: Mapping[str, Any],
    candidate_package_forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    terminal_decision = _mapping(readback.get("stage_terminal_decision"))
    next_decision = _mapping(readback.get("next_owner_or_human_decision"))
    terminal_owner_gate = _mapping(readback.get("terminal_owner_gate"))
    owner_packet_next_owner = _optional_text(owner_decision_packet.get("next_owner"))
    candidate_next_owner = _optional_text(candidate_manifest.get("next_owner"))
    decision_next_owner = _optional_text(terminal_decision.get("next_owner"))
    selected_next_owner = _first_text(
        next_decision.get("next_owner"),
        terminal_owner_gate.get("owner"),
        decision_next_owner,
        owner_packet_next_owner,
        candidate_next_owner,
        "mas_authority_kernel",
    )
    blocked_reason = _first_text(
        terminal_owner_gate.get("blocked_reason"),
        terminal_decision.get("blocker_id"),
        terminal_decision.get("reason"),
        readback.get("consume_candidate_status"),
        "owner_decision_required",
    )
    required_owner_action = required_owner_action_for_candidate_package(
        readback=readback,
        next_owner=selected_next_owner or "mas_authority_kernel",
        blocked_reason=blocked_reason or "owner_decision_required",
    )
    return {
        "surface_kind": "paper_mission_foreground_owner_decision_summary",
        "schema_version": 1,
        "candidate_is_authority": False,
        "governed_runtime_truth": False,
        "authority_materialized_by_this_packet": False,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "objective": readback.get("objective"),
        "input_refs": {
            "profile_ref": _mapping(readback.get("profile")).get("profile_ref"),
            "materialized_mission_ref": readback.get("materialized_mission_ref"),
            "candidate_manifest_ref": readback.get("candidate_manifest_ref"),
            "candidate_id": candidate_manifest.get("candidate_id"),
            "artifact_delta_ref": candidate_artifact_delta.get("artifact_ref"),
            "owner_decision_packet_id": owner_decision_packet.get("packet_id"),
            "source_readiness_refs": candidate_manifest.get("source_readiness_refs", []),
        },
        "current_terminal_decision": {
            "decision_kind": terminal_decision.get("decision_kind"),
            "status": terminal_decision.get("status"),
            "reason": terminal_decision.get("reason"),
            "next_owner": decision_next_owner,
            "next_stage_id": terminal_decision.get("next_stage_id"),
            "target_stage_id": terminal_decision.get("target_stage_id"),
            "next_work_unit": terminal_decision.get("next_work_unit"),
            "work_unit_id": terminal_decision.get("work_unit_id"),
            "repair_scope": terminal_decision.get("repair_scope"),
            "blocker_id": terminal_decision.get("blocker_id"),
            "unblock_condition": terminal_decision.get("unblock_condition"),
        },
        "runtime_touchpoint": {
            "opl_runtime_readback_status": readback.get("opl_runtime_readback_status"),
            "terminal_owner_gate": terminal_owner_gate or None,
            "next_owner_or_human_decision": next_decision,
        },
        "next_owner": selected_next_owner,
        "blocked_reason": blocked_reason,
        "required_owner_action": required_owner_action,
        "remaining_owner_gap": (
            "MAS/OPL owner surface must consume, route back, materialize a governed "
            "typed blocker or human gate, or accept an owner receipt before this "
            "candidate can be treated as runtime truth."
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(candidate_package_forbidden_authority_writes),
    }


def required_owner_action_for_candidate_package(
    *,
    readback: Mapping[str, Any],
    next_owner: str,
    blocked_reason: str,
) -> str:
    consume_status = _optional_text(readback.get("consume_candidate_status"))
    if consume_status == "accepted":
        return (
            f"{next_owner} must consume the accepted candidate through governed "
            "MAS authority or route it back with a governed receipt; foreground "
            "package alone does not authorize paper progress."
        )
    if consume_status == "typed_blocker":
        return (
            f"{next_owner} must materialize or reject the governed typed blocker "
            f"request for `{blocked_reason}`."
        )
    if consume_status == "human_gate":
        return (
            f"{next_owner} must record the governed human-gate decision for "
            f"`{blocked_reason}`."
        )
    return (
        f"{next_owner} must decide whether to consume, route back, block, or ask a "
        f"human question for `{blocked_reason}`."
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
