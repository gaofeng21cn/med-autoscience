from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


ACCEPTED_OWNER_ANSWER_SHAPES = (
    "domain_owner_receipt_ref",
    "quality_gate_receipt_ref",
    "paper_facing_delta_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_evidence_ref",
)
SUBMISSION_MILESTONE_KIND = "submission_milestone_candidate"
REQUIRED_AUTHORITY_MATERIALIZATION_REFS = (
    "domain_owner_receipt_ref",
    "quality_gate_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "publication_eval_record_ref",
    "current_package_ref",
)
REQUIRED_QUALITY_GATE_REFS = (
    "independent_reviewer_invocation_ref",
    "independent_reviewer_context_ref",
    "reviewer_quality_receipt_ref",
    "review_ledger_delta_ref",
)


def paper_mission_submission_milestone_checklist(
    *,
    output_kinds: Sequence[str],
    owner_blocker_context: bool,
) -> dict[str, Any]:
    included = tuple(dict.fromkeys(output_kinds))
    return {
        "surface_kind": "paper_mission_submission_milestone_checklist",
        "schema_version": 1,
        "milestone_kind": SUBMISSION_MILESTONE_KIND,
        "status": "candidate_ready_with_owner_blocker_context"
        if owner_blocker_context
        else "candidate_ready",
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "authority_materialized": False,
        "mas_automatable_items": [
            _checklist_item(
                item_id="manuscript_patch_plan",
                included="manuscript_patch_plan" in included,
            ),
            _checklist_item(
                item_id="claim_evidence_ledger_delta",
                included="claim_evidence_ledger_delta" in included,
            ),
            _checklist_item(
                item_id="figure_table_caption_delta",
                included="figure_table_caption_delta" in included,
            ),
            _checklist_item(
                item_id="reviewer_gate_response_draft",
                included="reviewer_gate_response_draft" in included,
            ),
            _checklist_item(
                item_id="owner_decision_packet",
                included="owner_decision_packet" in included,
            ),
        ],
        "authority_items": [
            {
                "item_id": "mas_authority_consume",
                "status": "pending_mas_authority",
                "candidate_package_can_satisfy_without_authority": False,
            },
            {
                "item_id": "current_package_materialization",
                "status": "pending_mas_authority",
                "candidate_package_can_satisfy_without_authority": False,
            },
        ],
        "required_authority_materialization_refs": _pending_ref_items(
            REQUIRED_AUTHORITY_MATERIALIZATION_REFS
        ),
        "required_quality_gate_refs": _pending_ref_items(REQUIRED_QUALITY_GATE_REFS),
        "human_objective_metadata_items": [
            {
                "item_id": "author_information",
                "status": "requires_human_objective_metadata",
            },
            {
                "item_id": "funding_numbers",
                "status": "requires_human_objective_metadata",
            },
        ],
        "forbidden_authority_claims": [
            "submission_ready",
            "publication_ready",
            "current_package",
            "owner_receipt_written",
        ],
    }


def paper_mission_owner_blocker_packet(
    *,
    readback: Mapping[str, Any],
    foreground_owner_decision_summary: Mapping[str, Any],
    mission_executor_handoff: Mapping[str, Any],
    forbidden_authority_writes: Sequence[str],
    forbidden_authority_claims: Sequence[str],
) -> dict[str, Any]:
    terminal_decision = _mapping(readback.get("stage_terminal_decision"))
    route_command = _mapping(readback.get("opl_route_command"))
    terminal_owner_gate = _mapping(readback.get("terminal_owner_gate"))
    next_decision = _mapping(readback.get("next_owner_or_human_decision"))
    next_owner = _first_text(
        next_decision.get("next_owner"),
        foreground_owner_decision_summary.get("next_owner"),
        mission_executor_handoff.get("next_owner"),
    )
    blocker_kind = _owner_blocker_kind(
        readback=readback,
        terminal_decision=terminal_decision,
        terminal_owner_gate=terminal_owner_gate,
    )
    is_owner_blocker = blocker_kind != "route_back_without_blocker"
    blocked_reason = _first_text(
        terminal_owner_gate.get("blocked_reason"),
        terminal_decision.get("blocker_id"),
        terminal_decision.get("reason"),
        "owner_decision_required",
    ) or "owner_decision_required"
    required_owner_resolution = _required_owner_resolution(
        blocker_kind=blocker_kind,
        terminal_decision=terminal_decision,
        next_owner=_first_text(
            next_decision.get("next_owner"),
            foreground_owner_decision_summary.get("next_owner"),
            "mas_authority_kernel",
        )
        or "mas_authority_kernel",
    )
    return {
        "surface_kind": "paper_mission_owner_blocker_packet",
        "schema_version": 1,
        "status": "owner_blocker_candidate_ready" if is_owner_blocker else "context_only",
        "blocker_kind": blocker_kind,
        "candidate_is_authority": False,
        "authority_materialized": False,
        "counts_as_paper_progress": False,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "next_owner": next_owner,
        "current_terminal_decision": {
            "decision_kind": terminal_decision.get("decision_kind"),
            "status": terminal_decision.get("status"),
            "reason": terminal_decision.get("reason"),
            "blocker_id": terminal_decision.get("blocker_id"),
            "unblock_condition": terminal_decision.get("unblock_condition"),
            "route_command": route_command.get("command_kind"),
            "route_target": route_command.get("target"),
        },
        "terminal_owner_gate": terminal_owner_gate or None,
        "terminal_owner_gate_materialized": bool(terminal_owner_gate),
        "typed_blocker_authority_materialized": False,
        "human_gate_materialized": False,
        "required_authority_materialization_refs": _pending_ref_items(
            REQUIRED_AUTHORITY_MATERIALIZATION_REFS
        ),
        "required_quality_gate_refs": _pending_ref_items(REQUIRED_QUALITY_GATE_REFS),
        "runtime_touchpoint": {
            "opl_runtime_readback_status": readback.get("opl_runtime_readback_status"),
            "opl_runtime_carrier_readback": readback.get("opl_runtime_carrier_readback"),
        },
        "required_owner_resolution": required_owner_resolution,
        "owner_question": _owner_question(
            blocker_kind=blocker_kind,
            next_owner=next_owner or "mission_executor",
            blocked_reason=blocked_reason,
            route_back_evidence_ref=_text(
                terminal_decision.get("route_back_evidence_ref")
            ),
        ),
        "next_legal_action": _next_legal_action(blocker_kind=blocker_kind),
        "next_legal_command": _next_legal_command(
            study_id=_text(readback.get("study_id")),
            candidate_manifest_ref=None,
        ),
        "evidence_refs": _owner_evidence_refs(
            readback=readback,
            terminal_decision=terminal_decision,
            terminal_owner_gate=terminal_owner_gate,
        ),
        "requested_answer_shape": list(ACCEPTED_OWNER_ANSWER_SHAPES),
        "accepted_owner_answer_shapes": list(ACCEPTED_OWNER_ANSWER_SHAPES),
        "authority_boundary": _authority_boundary(),
        "forbidden_authority_writes": list(forbidden_authority_writes),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def paper_mission_owner_consumption_request(
    *,
    readback: Mapping[str, Any],
    candidate_manifest: Mapping[str, Any],
    owner_decision_packet: Mapping[str, Any],
    foreground_owner_decision_summary: Mapping[str, Any],
    mission_executor_handoff: Mapping[str, Any],
    paper_facing_candidate_delta: Mapping[str, Any],
    owner_blocker_packet: Mapping[str, Any],
    candidate_refs: Mapping[str, Any],
    forbidden_authority_writes: Sequence[str],
    forbidden_authority_claims: Sequence[str],
) -> dict[str, Any]:
    status, request_kind = _consumption_status_and_kind(
        mission_executor_handoff=mission_executor_handoff,
        owner_blocker_packet=owner_blocker_packet,
    )
    next_owner = _first_text(
        mission_executor_handoff.get("next_owner"),
        foreground_owner_decision_summary.get("next_owner"),
        owner_decision_packet.get("next_owner"),
        candidate_manifest.get("next_owner"),
    )
    owner_blocker_kind = _text(owner_blocker_packet.get("blocker_kind")) or (
        "route_back_without_blocker"
    )
    return {
        "surface_kind": "paper_mission_owner_consumption_request",
        "schema_version": 1,
        "status": status,
        "request_kind": request_kind,
        "candidate_is_authority": False,
        "authority_materialized": False,
        "counts_as_paper_progress": False,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "next_owner": next_owner,
        "candidate_refs": dict(candidate_refs),
        "owner_decision_packet_id": owner_decision_packet.get("packet_id"),
        "paper_facing_candidate_delta_status": paper_facing_candidate_delta.get("status"),
        "current_terminal_decision": foreground_owner_decision_summary.get(
            "current_terminal_decision",
            {},
        ),
        "required_owner_action": foreground_owner_decision_summary.get(
            "required_owner_action"
        ),
        "remaining_owner_gap": foreground_owner_decision_summary.get(
            "remaining_owner_gap"
        ),
        "owner_question": _owner_question(
            blocker_kind=owner_blocker_kind,
            next_owner=next_owner or "mission_executor",
            blocked_reason=_first_text(
                owner_blocker_packet.get("blocker_kind"),
                _mapping(
                    foreground_owner_decision_summary.get(
                        "current_terminal_decision"
                    )
                ).get("reason"),
                foreground_owner_decision_summary.get("blocked_reason"),
                "owner_decision_required",
            )
            or "owner_decision_required",
            route_back_evidence_ref=_text(
                _mapping(owner_blocker_packet.get("evidence_refs")).get(
                    "route_back_evidence_ref"
                )
            ),
        ),
        "next_legal_action": _next_legal_action(blocker_kind=owner_blocker_kind),
        "next_legal_command": _next_legal_command(
            study_id=_text(readback.get("study_id")),
            candidate_manifest_ref=_text(candidate_refs.get("package_manifest")),
        ),
        "evidence_refs": _owner_evidence_refs(
            readback=readback,
            terminal_decision=_mapping(readback.get("stage_terminal_decision")),
            terminal_owner_gate=_mapping(readback.get("terminal_owner_gate")),
        ),
        "requested_answer_shape": list(ACCEPTED_OWNER_ANSWER_SHAPES),
        "accepted_owner_answer_shapes": list(ACCEPTED_OWNER_ANSWER_SHAPES),
        "consume_path": {
            "surface": "MAS authority consume path",
            "authority_materialized_by_this_request": False,
            "allowed_results": [
                "accepted_owner_decision_packet",
                "route_back",
                "human_gate",
                "stable_typed_blocker",
            ],
            "required_authority_materialization_refs": list(
                REQUIRED_AUTHORITY_MATERIALIZATION_REFS
            ),
            "required_quality_gate_refs": list(REQUIRED_QUALITY_GATE_REFS),
        },
        "authority_boundary": _authority_boundary(),
        "forbidden_authority_writes": list(forbidden_authority_writes),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def _consumption_status_and_kind(
    *,
    mission_executor_handoff: Mapping[str, Any],
    owner_blocker_packet: Mapping[str, Any],
) -> tuple[str, str]:
    if _text(mission_executor_handoff.get("status")) == "ready_for_mission_executor":
        return (
            "ready_for_mas_authority_consume",
            "route_back_candidate_delta_consumption",
        )
    if _text(owner_blocker_packet.get("status")) == "owner_blocker_candidate_ready":
        return "owner_blocker_packet_required", "owner_blocker_resolution"
    return "owner_review_required", "owner_decision_consumption"


def _owner_blocker_kind(
    *,
    readback: Mapping[str, Any],
    terminal_decision: Mapping[str, Any],
    terminal_owner_gate: Mapping[str, Any],
) -> str:
    decision_kind = _text(terminal_decision.get("decision_kind"))
    consume_status = _text(readback.get("consume_candidate_status"))
    runtime_status = _text(readback.get("opl_runtime_readback_status"))
    if terminal_owner_gate:
        return _text(terminal_owner_gate.get("gate_kind")) or "terminal_owner_gate"
    if decision_kind == "typed_blocker" or consume_status == "typed_blocker":
        if runtime_status == "waiting_for_opl_runtime_live_readback":
            return "missing_opl_runtime_readback"
        return "typed_blocker_owner_resolution"
    return "route_back_without_blocker"


def _required_owner_resolution(
    *,
    blocker_kind: str,
    terminal_decision: Mapping[str, Any],
    next_owner: str,
) -> str:
    if blocker_kind == "missing_opl_runtime_readback":
        return (
            f"{next_owner} must provide matching OPL stage-route terminal readback "
            "or return a governed owner answer shape before the mission can advance."
        )
    if blocker_kind == "typed_blocker_owner_resolution":
        blocker = _first_text(
            terminal_decision.get("blocker_id"),
            terminal_decision.get("reason"),
            "typed_blocker",
        )
        return (
            f"{next_owner} must materialize or reject the governed typed blocker "
            f"candidate for `{blocker}`."
        )
    if blocker_kind == "domain_gate":
        return (
            "MAS authority kernel must consume the domain gate as an owner receipt, "
            "typed blocker, human gate, or route-back evidence."
        )
    return (
        "No owner blocker is materialized in this package; owner review can consume "
        "the candidate bundle, route it back, block it, or ask a human question."
    )


def _owner_question(
    *,
    blocker_kind: str,
    next_owner: str,
    blocked_reason: str,
    route_back_evidence_ref: str | None,
) -> str:
    evidence_suffix = (
        f" using route-back evidence `{route_back_evidence_ref}`"
        if route_back_evidence_ref
        else ""
    )
    if blocker_kind == "domain_gate":
        return (
            f"{next_owner}: should `{blocked_reason}` be resolved as a "
            "domain_owner_receipt_ref, quality_gate_receipt_ref, typed_blocker_ref, "
            f"human_gate_ref, or route_back_evidence_ref{evidence_suffix}?"
        )
    if blocker_kind == "missing_opl_runtime_readback":
        return (
            f"{next_owner}: can you provide matching OPL terminal readback for "
            f"`{blocked_reason}`, or return one accepted owner answer shape?"
        )
    if blocker_kind == "typed_blocker_owner_resolution":
        return (
            f"{next_owner}: should `{blocked_reason}` be materialized as a governed "
            "typed_blocker_ref, rejected with route_back_evidence_ref, or escalated "
            "as human_gate_ref?"
        )
    return (
        f"{next_owner}: should the candidate for `{blocked_reason}` be consumed, "
        "routed back, blocked with a typed_blocker_ref, or escalated with a "
        "human_gate_ref?"
    )


def _next_legal_action(*, blocker_kind: str) -> str:
    if blocker_kind == "missing_opl_runtime_readback":
        return "provide_opl_terminal_readback_or_governed_owner_answer"
    if blocker_kind in {"domain_gate", "typed_blocker_owner_resolution"}:
        return "return_governed_owner_answer_shape"
    return "consume_candidate_or_return_owner_answer_shape"


def _next_legal_command(
    *,
    study_id: str | None,
    candidate_manifest_ref: str | None,
) -> dict[str, Any]:
    return {
        "command_kind": "paper_mission/consume_candidate",
        "argv_template": [
            "medautosci",
            "paper-mission",
            "consume-candidate",
            "--profile",
            "<profile>",
            "--study-id",
            study_id or "<study_id>",
            "--candidate",
            candidate_manifest_ref or "<package_manifest_ref>",
            "--output-root",
            "<workspace>/ops/medautoscience/paper_mission_consumption_ledger/<run_id>",
            "--format",
            "json",
        ],
        "authority_materialized_by_this_command": False,
        "requires_owner_answer_shape": list(ACCEPTED_OWNER_ANSWER_SHAPES),
    }


def _owner_evidence_refs(
    *,
    readback: Mapping[str, Any],
    terminal_decision: Mapping[str, Any],
    terminal_owner_gate: Mapping[str, Any],
) -> dict[str, Any]:
    refs: dict[str, Any] = {
        "materialized_mission_ref": readback.get("materialized_mission_ref"),
        "candidate_manifest_ref": readback.get("candidate_manifest_ref"),
    }
    if route_back_ref := _text(terminal_decision.get("route_back_evidence_ref")):
        refs["route_back_evidence_ref"] = route_back_ref
    if terminal_owner_gate:
        refs["terminal_owner_gate"] = terminal_owner_gate
    return {key: value for key, value in refs.items() if value}


def _authority_boundary() -> dict[str, bool]:
    return {
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_update_current_package": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
    }


def _checklist_item(*, item_id: str, included: bool) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "status": "candidate_included" if included else "candidate_missing",
    }


def _pending_ref_items(refs: Sequence[str]) -> list[dict[str, Any]]:
    return [
        {
            "ref_kind": ref,
            "status": "pending_owner_authority",
            "candidate_package_can_satisfy_without_authority": False,
        }
        for ref in refs
    ]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ACCEPTED_OWNER_ANSWER_SHAPES",
    "REQUIRED_AUTHORITY_MATERIALIZATION_REFS",
    "REQUIRED_QUALITY_GATE_REFS",
    "SUBMISSION_MILESTONE_KIND",
    "paper_mission_owner_blocker_packet",
    "paper_mission_owner_consumption_request",
    "paper_mission_submission_milestone_checklist",
]
