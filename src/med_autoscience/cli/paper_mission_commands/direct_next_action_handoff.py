from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _mapping,
    _optional_text,
    _slug,
    _stable_sha256,
)
from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_transaction import build_paper_mission_transaction
from med_autoscience import study_task_intake
from med_autoscience.study_task_intake_surfaces import latest_task_intake_json_path


def build_direct_next_action_handoff(
    *,
    profile: Any,
    study_id: str,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    workspace_root = str(Path(profile.workspace_root).expanduser().resolve())
    task_intake_context = _direct_next_action_task_intake_context(
        workspace_root=workspace_root,
        study_id=study_id,
    )
    transaction = build_direct_next_action_transaction(
        study_id=study_id,
        inspect_readback=inspect_readback,
        next_action=next_action,
    )
    task_intake_ref = _mapping(task_intake_context.get("task_intake_ref"))
    if task_intake_ref:
        _append_task_intake_refs_to_transaction(
            transaction=transaction,
            task_intake_ref=task_intake_ref,
        )
    carrier = paper_mission_opl_runtime_carrier(transaction)
    route = _mapping(transaction.get("opl_route_command"))
    decision = _mapping(transaction.get("stage_terminal_decision"))
    route_target = _optional_text(route.get("target"))
    owner_consumption = _current_owner_consumption(inspect_readback)
    owner_consumption_status = _optional_text(
        owner_consumption.get("status")
    ) or _optional_text(
        _mapping(
            _mapping(inspect_readback.get("current_opl_runtime_carrier_readback")).get(
                "mas_receipt_consumption"
            )
        ).get("status")
    )
    owner_consumption_readback_ref = _optional_text(
        _mapping(inspect_readback.get("current_opl_runtime_carrier_readback")).get(
            "owner_consumption_readback_ref"
        )
    ) or _optional_text(
        _mapping(inspect_readback.get("receipt_owner_consumption_readback")).get(
            "source_ref"
        )
    ) or _optional_text(
        _mapping(inspect_readback.get("receipt_owner_consumption_readback")).get(
            "decision_ref"
        )
    )
    route_checkpoint_evidence_ref = _optional_text(
        owner_consumption.get("route_checkpoint_evidence_ref")
    )
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
        "owner_consumption_status": owner_consumption_status,
        "owner_consumption_readback_ref": owner_consumption_readback_ref,
        "route_checkpoint_evidence_ref": route_checkpoint_evidence_ref,
        "task_intake_kind": _optional_text(task_intake_context.get("task_intake_kind")),
        "task_intake_ref": task_intake_ref or None,
        "task_intake_summary": _mapping(task_intake_context.get("task_intake_summary"))
        or None,
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
        f"paper-mission::{study_id}::domain-transition::"
        f"{_slug(stage_id)}::{_slug(work_unit_id)}"
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
    successor_epoch = _direct_next_action_successor_epoch(
        inspect_readback=inspect_readback
    )
    idempotency_basis = (
        "domain-transition-direct-stage-attempt::"
        f"{_slug(stage_id)}::{_slug(work_unit_id)}::"
        f"{_stable_sha256(work_unit_fingerprint)[:12]}"
    )
    if successor_epoch is not None:
        idempotency_basis = (
            f"{idempotency_basis}::successor::{_stable_sha256(successor_epoch)[:12]}"
        )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=stage_run_ref,
        terminal_decision=terminal_decision,
        artifact_delta_refs=direct_next_action_refs(next_action),
        paper_audit_pack_refs=direct_next_action_audit_pack_refs(next_action),
        idempotency_basis=idempotency_basis,
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


def _direct_next_action_task_intake_context(
    *, workspace_root: str, study_id: str
) -> dict[str, Any]:
    study_root = Path(workspace_root).expanduser().resolve() / "studies" / study_id
    latest_payload = study_task_intake.read_latest_task_intake(study_root=study_root)
    if not isinstance(latest_payload, dict):
        return {}
    summary = study_task_intake.summarize_task_intake(latest_payload)
    task_intake_ref = {
        "task_id": _optional_text(latest_payload.get("task_id")),
        "study_id": _optional_text(latest_payload.get("study_id")) or study_id,
        "artifact_path": str(latest_task_intake_json_path(study_root=study_root)),
    }
    return {
        "task_intake_kind": _optional_text(latest_payload.get("task_intake_kind")),
        "task_intake_ref": task_intake_ref,
        "task_intake_summary": _compact_task_intake_summary(
            latest_payload=latest_payload,
            summary=summary,
        ),
    }


def _compact_task_intake_summary(
    *,
    latest_payload: Mapping[str, Any],
    summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    summary_mapping = _mapping(summary)
    revision_intake = _mapping(summary_mapping.get("revision_intake"))
    checklist_items = revision_intake.get("checklist_items")
    compact = {
        "task_intake_kind": _optional_text(latest_payload.get("task_intake_kind")),
        "task_id": _optional_text(summary_mapping.get("task_id"))
        or _optional_text(latest_payload.get("task_id")),
        "emitted_at": _optional_text(summary_mapping.get("emitted_at"))
        or _optional_text(latest_payload.get("emitted_at")),
        "task_intent": _optional_text(summary_mapping.get("task_intent")),
        "entry_mode": _optional_text(summary_mapping.get("entry_mode")),
        "constraints": _non_empty_string_list(summary_mapping.get("constraints")),
        "evidence_boundary": _non_empty_string_list(
            summary_mapping.get("evidence_boundary")
        ),
        "trusted_inputs": _non_empty_string_list(summary_mapping.get("trusted_inputs")),
        "first_cycle_outputs": _non_empty_string_list(
            summary_mapping.get("first_cycle_outputs")
        ),
        "reference_papers": _non_empty_string_list(
            summary_mapping.get("reference_papers")
        ),
    }
    if revision_intake:
        compact["revision_checklist"] = _non_empty_string_list(
            revision_intake.get("checklist")
        )
        if isinstance(checklist_items, list):
            compact["revision_checklist_requirements"] = _non_empty_string_list(
                [_mapping(item).get("requirement") for item in checklist_items]
            )
    return {key: value for key, value in compact.items() if value not in (None, [], {})}


def _non_empty_string_list(values: Any) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple)):
        return []
    items: list[str] = []
    for value in values:
        text = _optional_text(value)
        if text is not None:
            items.append(text)
    return items


def _append_task_intake_refs_to_transaction(
    *,
    transaction: dict[str, Any],
    task_intake_ref: Mapping[str, Any],
) -> None:
    artifact_path = _optional_text(task_intake_ref.get("artifact_path"))
    if artifact_path is None:
        return
    ref = {
        "ref_id": "study_task_intake::latest",
        "ref_kind": "study_task_intake",
        "uri": artifact_path,
    }
    artifact_delta_refs = transaction.get("artifact_delta_refs")
    if isinstance(artifact_delta_refs, list) and ref not in artifact_delta_refs:
        artifact_delta_refs.append(ref)
    paper_audit_pack_refs = transaction.get("paper_audit_pack_refs")
    if not isinstance(paper_audit_pack_refs, dict):
        return
    for refs in paper_audit_pack_refs.values():
        if isinstance(refs, list) and ref not in refs:
            refs.append(ref)


def _current_owner_consumption(inspect_readback: Mapping[str, Any]) -> dict[str, Any]:
    receipt_owner_consumption = _mapping(
        _mapping(inspect_readback.get("receipt_owner_consumption_readback")).get(
            "mas_receipt_consumption"
        )
    )
    if _owner_consumption_is_materialized(receipt_owner_consumption):
        return receipt_owner_consumption
    current_carrier = _mapping(
        inspect_readback.get("current_opl_runtime_carrier_readback")
    )
    current_owner_consumption = _mapping(current_carrier.get("mas_receipt_consumption"))
    if current_owner_consumption:
        return current_owner_consumption
    return receipt_owner_consumption


def _owner_consumption_is_materialized(owner_consumption: Mapping[str, Any]) -> bool:
    status = _optional_text(owner_consumption.get("status"))
    return bool(status and status.startswith("owner_consumed_"))


def _direct_next_action_successor_epoch(
    *, inspect_readback: Mapping[str, Any]
) -> str | None:
    owner_consumption = _current_owner_consumption(inspect_readback)
    status = _optional_text(owner_consumption.get("status")) or _optional_text(
        _mapping(inspect_readback.get("current_opl_runtime_carrier_readback")).get(
            "owner_consumption_status"
        )
    )
    if not status or not status.startswith("owner_consumed_"):
        return None
    current_carrier = _mapping(
        inspect_readback.get("current_opl_runtime_carrier_readback")
    )
    receipt_readback = _mapping(inspect_readback.get("receipt_owner_consumption_readback"))
    owner_readback_ref = (
        _optional_text(current_carrier.get("owner_consumption_readback_ref"))
        or _optional_text(receipt_readback.get("source_ref"))
        or _optional_text(receipt_readback.get("decision_ref"))
    )
    evidence_ref = (
        _optional_text(owner_consumption.get("route_checkpoint_evidence_ref"))
        or _optional_text(owner_consumption.get("receipt_evidence_ref"))
        or _optional_text(owner_consumption.get("typed_runtime_blocker_ref"))
        or _optional_text(owner_consumption.get("route_back_evidence_ref"))
    )
    if owner_readback_ref is not None and evidence_ref is not None:
        return f"{owner_readback_ref}::{evidence_ref}"
    return owner_readback_ref or evidence_ref or status


__all__ = [
    "build_direct_next_action_handoff",
    "build_direct_next_action_transaction",
    "direct_next_action_audit_pack_refs",
    "direct_next_action_refs",
]
