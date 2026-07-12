from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_stage_run_readback.primitives import (
    first_mapping as _first_mapping,
    first_text as _first_text,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_stage_run_readback.receipt_events import (
    OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_SURFACE_KIND,
    matches_opl_stage_attempt_receipt,
)


def terminal_closeout_readback(
    *,
    closeout: Mapping[str, Any],
    closeout_ref: str,
    carrier: Mapping[str, Any],
) -> dict[str, Any]:
    opl_stage_attempt_receipt = opl_stage_attempt_receipt_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
        carrier=carrier,
    )
    receipt_evidence = receipt_evidence_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
        opl_stage_attempt_receipt=opl_stage_attempt_receipt,
    )
    mas_receipt_consumption = mas_receipt_consumption_readback(
        receipt_evidence=receipt_evidence,
    )
    paper_stage_log = _mapping(closeout.get("paper_stage_log"))
    duration = accounting_mapping(
        closeout=closeout,
        paper_stage_log=paper_stage_log,
        field="duration",
        missing_reason_field="missing_duration_reason",
        missing_reason="stage_attempt_closeout_packet_duration_missing",
    )
    token_usage = accounting_mapping(
        closeout=closeout,
        paper_stage_log=paper_stage_log,
        field="token_usage",
        missing_reason_field="missing_token_usage_reason",
        missing_reason="stage_attempt_closeout_packet_token_usage_missing",
        null_fields={"total_tokens": None},
    )
    cost = accounting_mapping(
        closeout=closeout,
        paper_stage_log=paper_stage_log,
        field="cost",
        missing_reason_field="missing_cost_reason",
        missing_reason="stage_attempt_closeout_packet_cost_missing",
        null_fields={"usd": None},
    )
    route_impact = _mapping(closeout.get("route_impact"))
    status = _first_text(closeout.get("status"), closeout.get("closeout_status"))
    return {
        "surface_kind": _text(closeout.get("surface_kind")),
        "closeout_ref": closeout_ref,
        "status": status,
        "closeout_status": _text(closeout.get("closeout_status")),
        "study_id": _text(closeout.get("study_id")),
        "stage_id": _text(closeout.get("stage_id")),
        "stage_attempt_id": _text(closeout.get("stage_attempt_id")),
        "work_unit_id": _text(closeout.get("work_unit_id")),
        "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(closeout.get("stage_packet_ref")),
        "provider_attempt_ref": _text(closeout.get("provider_attempt_ref")),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "typed_blocker_ref": _text(closeout.get("typed_blocker_ref")),
        "blocked_reason": _text(closeout.get("blocked_reason")),
        "closeout_refs": _text_list(closeout.get("closeout_refs")),
        **(
            {"opl_stage_attempt_receipt": opl_stage_attempt_receipt}
            if opl_stage_attempt_receipt
            else {}
        ),
        **({"receipt_evidence": receipt_evidence} if receipt_evidence else {}),
        **(
            {"mas_receipt_consumption": mas_receipt_consumption}
            if mas_receipt_consumption
            else {}
        ),
        **({"route_impact": route_impact} if route_impact else {}),
        "duration": duration,
        "token_usage": token_usage,
        "cost": cost,
        "paper_stage_log": paper_stage_log,
        "task_id": _text(closeout.get("task_id")),
        "task_status": _text(closeout.get("task_status")),
        "closeout_receipt_status": _text(closeout.get("closeout_receipt_status")),
        "runtime_readback_source": _text(closeout.get("runtime_readback_source")),
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def opl_stage_attempt_receipt_readback(
    *,
    closeout: Mapping[str, Any],
    closeout_ref: str,
    carrier: Mapping[str, Any],
) -> dict[str, Any] | None:
    receipt = _mapping(closeout.get("opl_stage_attempt_receipt"))
    if not matches_opl_stage_attempt_receipt(receipt=receipt, carrier=carrier):
        return None
    return {
        **dict(receipt),
        "role": "transport_receipt_only",
        "runtime_closeout_readback_ref": closeout_ref,
        "can_change_stage_terminal_decision": False,
        "can_select_next_owner": False,
        "can_claim_paper_progress": False,
    }


def receipt_evidence_readback(
    *,
    closeout: Mapping[str, Any],
    closeout_ref: str,
    opl_stage_attempt_receipt: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    receipt = _mapping(opl_stage_attempt_receipt)
    if (
        _text(receipt.get("surface_kind"))
        != OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_SURFACE_KIND
    ):
        return None
    impact = _mapping(closeout.get("mas_impact_receipt"))
    route_back_evidence_ref = _first_text(
        receipt.get("route_back_evidence_ref"),
        _route_back_evidence_ref(closeout),
    )
    return {
        "surface_kind": "mas_receipt_evidence",
        "schema_version": 1,
        "receipt_kind": OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_SURFACE_KIND,
        "receipt_ref": _first_text(
            receipt.get("domain_route_handoff_ref"),
            receipt.get("stage_attempt_ref"),
            receipt.get("runtime_closeout_ref"),
            closeout_ref,
        ),
        "domain_route_handoff_ref": _text(receipt.get("domain_route_handoff_ref")),
        "domain_route_transaction_ref": _text(
            receipt.get("domain_route_transaction_ref")
        ),
        "domain_route_command_ref": _text(receipt.get("domain_route_command_ref")),
        "runtime_closeout_ref": _first_text(
            receipt.get("runtime_closeout_ref"),
            closeout_ref,
        ),
        "stage_attempt_ref": _text(receipt.get("stage_attempt_ref")),
        "typed_runtime_blocker_ref": _text(receipt.get("typed_runtime_blocker_ref")),
        "route_back_evidence_ref": route_back_evidence_ref,
        "impact_receipt_kind": _text(impact.get("surface_kind")),
        "impact_receipt_ref": _text(impact.get("receipt_ref")),
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "durable_stop_allowed": False,
        "authority_boundary": {
            "receipt_is_input_ref_only": True,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_write_current_package": False,
            "can_claim_paper_progress": False,
            "can_claim_publication_ready": False,
        },
    }


def mas_receipt_consumption_readback(
    *,
    receipt_evidence: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    evidence = _mapping(receipt_evidence)
    if _text(evidence.get("surface_kind")) != "mas_receipt_evidence":
        return None
    route_back_evidence_ref = _text(evidence.get("route_back_evidence_ref"))
    typed_runtime_blocker_ref = _text(evidence.get("typed_runtime_blocker_ref"))
    return {
        "surface_kind": "mas_receipt_consumption_projection",
        "schema_version": 1,
        "status": "requires_mas_owner_consumption",
        "next_legal_action": (
            "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            if route_back_evidence_ref
            else "record_typed_blocker"
            if typed_runtime_blocker_ref
            else "consume_opl_stage_attempt_receipt"
        ),
        "receipt_evidence_ref": _text(evidence.get("receipt_ref")),
        "typed_runtime_blocker_ref": typed_runtime_blocker_ref,
        "route_back_evidence_ref": route_back_evidence_ref,
        "durable_stop_allowed": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
    }


def _route_back_evidence_ref(closeout: Mapping[str, Any]) -> str | None:
    direct_ref = _text(closeout.get("route_back_evidence_ref"))
    if direct_ref is not None:
        return direct_ref
    stage_attempt_receipt = _mapping(closeout.get("opl_stage_attempt_receipt"))
    route_impact = _mapping(closeout.get("route_impact")) or _mapping(
        stage_attempt_receipt.get("route_impact")
    )
    evidence_ref = _first_text(
        route_impact.get("route_back_evidence_ref"),
        _mapping(route_impact.get("stage_log_summary")).get("route_back_evidence_ref"),
        _mapping(route_impact.get("user_stage_log")).get("route_back_evidence_ref"),
        stage_attempt_receipt.get("route_back_evidence_ref"),
    )
    if evidence_ref is not None:
        return evidence_ref
    route_back_requested = (
        _text(route_impact.get("owner_answer_kind")) == "route_back_evidence_ref"
        or _text(route_impact.get("recommended_next_action"))
        == "consume_route_back_evidence_ref"
        or _text(route_impact.get("next_forced_paper_action")) is not None
    )
    if not route_back_requested:
        return None
    for item in closeout.get("closeout_refs") or ():
        if isinstance(item, str):
            if item.endswith("route_back_evidence_packet.json"):
                return item
            continue
        ref = _mapping(item)
        if _text(ref.get("ref_kind")) == "route_back_evidence_packet":
            return _first_text(
                ref.get("workspace_relative_ref"),
                ref.get("uri"),
                ref.get("ref"),
            )
    for key in ("stage_log_summary", "user_stage_log"):
        summary = _mapping(route_impact.get(key))
        for item in summary.get("evidence_refs") or ():
            ref = _text(item)
            if ref is not None and ref.endswith("route_back_evidence_packet.json"):
                return ref
    return None


def accounting_mapping(
    *,
    closeout: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    field: str,
    missing_reason_field: str,
    missing_reason: str,
    null_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    observed = _first_mapping(
        _mapping(closeout.get(field)),
        _mapping(paper_stage_log.get(field)),
    )
    if observed:
        return observed
    if field not in closeout and field not in paper_stage_log:
        return {}
    return {
        "status": "missing",
        **dict(null_fields or {}),
        missing_reason_field: missing_reason,
    }


def running_attempt_readback(
    *,
    attempt: Mapping[str, Any],
    attempt_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": _text(attempt.get("surface_kind")),
        "attempt_ref": attempt_ref,
        "status": _text(attempt.get("status")),
        "study_id": _text(attempt.get("study_id")),
        "stage_id": _text(attempt.get("stage_id")),
        "stage_attempt_id": _text(attempt.get("stage_attempt_id")),
        "work_unit_id": _text(attempt.get("work_unit_id")),
        "work_unit_fingerprint": _text(attempt.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(attempt.get("stage_packet_ref")),
        "provider_attempt_ref": _text(attempt.get("provider_attempt_ref")),
        "provider_kind": _text(attempt.get("provider_kind")),
        "workflow_id": _text(attempt.get("workflow_id")),
        "provider_status": _text(attempt.get("provider_status")),
        "last_heartbeat_at": _text(attempt.get("last_heartbeat_at")),
        "last_runner_event_kind": _text(attempt.get("last_runner_event_kind")),
        "task_id": _text(attempt.get("task_id")),
        "task_status": _text(attempt.get("task_status")),
        "runtime_readback_source": _text(attempt.get("runtime_readback_source")),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_paper_progress": False,
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }
