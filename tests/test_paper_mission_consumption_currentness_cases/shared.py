from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_transaction import build_paper_mission_transaction


AUDIT_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)


def _write_ledger(
    *,
    workspace_root: Path,
    study_id: str,
    run_id: str,
    transaction_ref: str,
    fingerprint: str,
    external_delta_ref: str | None = None,
    paper_facing_delta_ref: str | None = None,
    milestone_kind: str | None = None,
    relative_candidate_ref: bool = False,
) -> Path:
    ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / run_id
        / study_id
    )
    ledger_root.mkdir(parents=True)
    transaction = _transaction(
        study_id=study_id,
        run_id=run_id,
        transaction_ref=transaction_ref,
        fingerprint=fingerprint,
    )
    carrier = paper_mission_opl_runtime_carrier(transaction)
    candidate_manifest = ledger_root / "package_manifest.json"
    if relative_candidate_ref:
        candidate_manifest = (
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_candidate_package"
            / run_id
            / study_id
            / "package_manifest.json"
        )
        candidate_manifest.parent.mkdir(parents=True, exist_ok=True)
    candidate_ref = candidate_manifest
    if relative_candidate_ref:
        candidate_ref = candidate_ref.relative_to(workspace_root)
    consume_record = {
        "surface_kind": "mas_paper_mission_candidate_consumption_record",
        "schema_version": 1,
        "study_id": study_id,
        "candidate_ref": str(candidate_ref),
        "candidate_id": f"candidate::{run_id}",
        "status": "accepted_candidate",
        "selected_outcome": "accepted_candidate",
        "route_handoff_status": "ready_for_opl_route_command",
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "counts_as_stage_terminalizer_evidence": True,
        "counts_as_opl_route_handoff_evidence": True,
        "authority_materialized": False,
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": _authority_boundary(),
    }
    if paper_facing_delta_ref:
        consume_record["consume_result"] = {
            "status": "accepted",
            "outcome": "accepted_candidate",
            "authority_materialized": False,
            "paper_facing_delta_ref": paper_facing_delta_ref,
        }
    handoff = {
        "surface_kind": "mas_paper_mission_opl_route_handoff_record",
        "schema_version": 1,
        "study_id": study_id,
        "mission_id": transaction["mission_id"],
        "candidate_ref": str(candidate_ref),
        "handoff_status": "ready_for_opl_route_command",
        "next_owner": "mission_executor",
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "stage_terminal_decision": transaction["stage_terminal_decision"],
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "opl_route_command": transaction["opl_route_command"],
        "opl_runtime_carrier": carrier,
        "route_command_kind": "route_back",
        "route_target": "paper-stage::gate-clearing",
        "transaction_materialized": True,
        "can_submit_to_opl_runtime": True,
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": _authority_boundary(),
    }
    (ledger_root / "consume_record.json").write_text(
        json.dumps(consume_record),
        encoding="utf-8",
    )
    candidate_manifest.write_text(
        json.dumps(
            {
                "milestone_kind": milestone_kind,
                "adopted_external_paper_delta_ref": external_delta_ref,
                "paper_facing_candidate_delta_ref": paper_facing_delta_ref,
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "consume_readback.json").write_text(
        json.dumps({"paper_mission_transaction": transaction}),
        encoding="utf-8",
    )
    (ledger_root / "stage_terminal_decision.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_stage_terminal_decision_packet",
                "study_id": study_id,
                "candidate_ref": str(candidate_ref),
                "paper_mission_transaction_ref": transaction_ref,
                "stage_terminal_decision_ref": (
                    f"{transaction_ref}#stage_terminal_decision"
                ),
                "transaction_state": transaction["stage_terminal_decision"]["status"],
                "stage_id": transaction["stage_id"],
                "stage_run_ref": transaction["stage_run_ref"],
                "stage_terminal_decision": transaction["stage_terminal_decision"],
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_command.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_command_packet",
                "study_id": study_id,
                "candidate_ref": str(candidate_ref),
                "paper_mission_transaction_ref": transaction_ref,
                "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
                "opl_route_command": transaction["opl_route_command"],
                "opl_runtime_carrier": carrier,
                **transaction["opl_route_command"],
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_handoff.json").write_text(
        json.dumps(handoff),
        encoding="utf-8",
    )
    return ledger_root / "consume_record.json"


def _transaction(
    *,
    study_id: str,
    run_id: str,
    transaction_ref: str,
    fingerprint: str,
) -> dict[str, object]:
    transaction = build_paper_mission_transaction(
        mission_id=f"paper-mission::{study_id}::{run_id}",
        study_id=study_id,
        stage_id="paper-stage::gate-clearing",
        stage_run_ref=f"opl-stage-run://{study_id}/{run_id}",
        terminal_decision={
            "decision_kind": "route_back",
            "status": "terminal_decision_recorded",
            "reason": "candidate needs a claim/evidence repair pass",
            "next_owner": "mission_executor",
            "target_stage_id": "paper-stage::gate-clearing",
            "repair_scope": "claim-evidence-repair",
        },
        artifact_delta_refs=[
            {
                "ref_id": f"artifact-delta::{run_id}",
                "ref_kind": "candidate_artifact_delta",
                "uri": f"mission://{study_id}/{run_id}/artifact-delta",
            }
        ],
        paper_audit_pack_refs={
            family: [
                {
                    "ref_id": f"{family}::{run_id}",
                    "ref_kind": family,
                    "uri": f"mission://{study_id}/{run_id}/{family}",
                }
            ]
            for family in AUDIT_FAMILIES
        },
        idempotency_basis=run_id,
    )
    transaction["transaction_id"] = transaction_ref
    transaction["opl_route_command"][
        "source_terminal_decision_ref"
    ] = f"{transaction_ref}#stage_terminal_decision"
    transaction["idempotency"]["transaction_fingerprint"] = fingerprint
    return transaction


def _receipt_owner_consumption_payload(
    *,
    study_id: str,
    checkpoint_ref: str,
) -> dict[str, object]:
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "owner_consumption_applied",
        "study_id": study_id,
        "authority_materialized": True,
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "owner_consumed_route_checkpoint",
            "route_checkpoint_evidence_ref": checkpoint_ref,
        },
        "stage_closure_decision": {
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "route_checkpoint_evidence_ref": checkpoint_ref,
            },
            "authority_boundary": {
                "writes_owner_receipt": False,
                "writes_human_gate": False,
                "writes_current_package": False,
                "writes_submission_ready_package": False,
                "writes_runtime_queue_or_provider_attempt": False,
            },
        },
    }


def _patch_json(path: Path, updates: dict[str, object]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(payload.get(key), dict):
            payload[key].update(value)
        else:
            payload[key] = value
    path.write_text(json.dumps(payload), encoding="utf-8")


def _authority_boundary() -> dict[str, bool]:
    return {
        "writes_authority_surface": False,
        "writes_publication_eval": False,
        "writes_controller_decision": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_write_paper_body": False,
        "can_write_runtime_queue": False,
        "can_write_opl_outbox": False,
        "can_write_opl_event": False,
        "can_write_opl_stage_run": False,
        "can_write_provider_attempt": False,
    }
