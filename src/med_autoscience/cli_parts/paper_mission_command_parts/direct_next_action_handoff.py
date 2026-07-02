from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _mapping,
    _optional_text,
    _slug,
    _stable_sha256,
)
from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_transaction import build_paper_mission_transaction


def build_direct_next_action_handoff(
    *,
    profile: Any,
    study_id: str,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = build_direct_next_action_transaction(
        study_id=study_id,
        inspect_readback=inspect_readback,
        next_action=next_action,
    )
    carrier = paper_mission_opl_runtime_carrier(transaction)
    route = _mapping(transaction.get("opl_route_command"))
    decision = _mapping(transaction.get("stage_terminal_decision"))
    route_target = _optional_text(route.get("target"))
    workspace_root = str(Path(profile.workspace_root).expanduser().resolve())
    return {
        "surface_kind": "mas_paper_mission_opl_route_handoff_record",
        "schema_version": 1,
        "handoff_status": "ready_for_opl_route_command",
        "study_id": study_id,
        "mission_id": transaction["mission_id"],
        "paper_mission_transaction_ref": transaction["transaction_id"],
        "stage_terminal_decision_ref": f"{transaction['transaction_id']}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction['transaction_id']}#opl_route_command",
        "stage_run_ref": transaction["stage_run_ref"],
        "stage_id": transaction["stage_id"],
        "work_unit_id": carrier["work_unit_id"],
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "route_command_kind": _optional_text(route.get("command_kind")),
        "route_target": route_target,
        "next_owner": _optional_text(decision.get("next_owner")),
        "can_submit_to_opl_runtime": True,
        "transaction_materialized": True,
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": decision,
        "opl_route_command": route,
        "opl_runtime_carrier": carrier,
        "route_identity_key": carrier["route_identity_key"],
        "attempt_idempotency_key": carrier["attempt_idempotency_key"],
        "request_idempotency_key": carrier["request_idempotency_key"],
        "idempotency_key": carrier["idempotency_key"],
        "workspace_root": workspace_root,
        "domain_workspace_root": workspace_root,
        "source_surface_kind": "mas_domain_transition_next_action",
        "source_ref": _optional_text(next_action.get("outcome_ref"))
        or _optional_text(next_action.get("action_id")),
        "route_back_evidence_ref": _optional_text(next_action.get("outcome_ref")),
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": {
            "surface_role": "domain_transition_direct_opl_route_handoff",
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_write_opl_outbox": False,
            "can_write_opl_event": False,
            "can_write_opl_stage_run": False,
            "can_authorize_provider_admission": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }


def build_direct_next_action_transaction(
    *,
    study_id: str,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    stage_id = (
        _optional_text(next_action.get("stage_id"))
        or _optional_text(next_action.get("owner"))
        or "write"
    )
    work_unit_id = _optional_text(next_action.get("work_unit_id"))
    if work_unit_id is None:
        raise ValueError("domain transition next_action requires work_unit_id")
    work_unit_fingerprint = (
        _optional_text(next_action.get("work_unit_fingerprint"))
        or _optional_text(next_action.get("action_fingerprint"))
        or _optional_text(next_action.get("outcome_ref"))
        or _optional_text(next_action.get("action_id"))
        or work_unit_id
    )
    mission_id = (
        _optional_text(inspect_readback.get("mission_id"))
        or f"paper-mission::{study_id}::domain-transition::{_slug(work_unit_id)}"
    )
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "domain_transition_next_action_ready",
        "reason": (
            "MAS domain transition selected a concrete OPL stage attempt for "
            "the current paper repair work unit."
        ),
        "next_owner": _optional_text(next_action.get("owner")) or stage_id,
        "target_stage_id": stage_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "recommended_next_action": _optional_text(next_action.get("action_family"))
        or _optional_text(next_action.get("action_type")),
        "domain_transition_next_action_ref": _optional_text(
            next_action.get("outcome_ref")
        )
        or _optional_text(next_action.get("action_id")),
    }
    stage_run_ref = (
        f"paper-mission-domain-transition://{study_id}/"
        f"{_slug(stage_id)}/{_slug(work_unit_id)}"
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=stage_run_ref,
        terminal_decision=terminal_decision,
        artifact_delta_refs=direct_next_action_refs(next_action),
        paper_audit_pack_refs=direct_next_action_audit_pack_refs(next_action),
        idempotency_basis=(
            "domain-transition-direct-stage-attempt::"
            f"{_slug(stage_id)}::{_slug(work_unit_id)}::"
            f"{_stable_sha256(work_unit_fingerprint)[:12]}"
        ),
    )


def direct_next_action_refs(next_action: Mapping[str, Any]) -> list[dict[str, Any]]:
    uri = (
        _optional_text(next_action.get("outcome_ref"))
        or _optional_text(next_action.get("action_id"))
        or _optional_text(next_action.get("work_unit_id"))
        or "domain-transition-next-action"
    )
    return [
        {
            "ref_id": "domain_transition_next_action::1",
            "ref_kind": "domain_transition_next_action_ref",
            "uri": uri,
        }
    ]


def direct_next_action_audit_pack_refs(
    next_action: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    refs = direct_next_action_refs(next_action)
    return {
        family: list(refs)
        for family in (
            "analysis_rationale_log",
            "decision_trace",
            "evidence_ledger_delta",
            "review_ledger_delta",
            "revision_log_delta",
            "failed_path_ledger",
            "artifact_lineage",
            "reproducibility_refs",
        )
    }


__all__ = [
    "build_direct_next_action_handoff",
    "build_direct_next_action_transaction",
    "direct_next_action_audit_pack_refs",
    "direct_next_action_refs",
]
