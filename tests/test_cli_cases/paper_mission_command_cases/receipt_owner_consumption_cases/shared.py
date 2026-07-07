from __future__ import annotations


def readback(
    *,
    study_id: str,
    stage_outcome: str,
    transition_kind: str | None,
    package_kind: str,
    can_submit: bool,
    consumption_next_legal_action: str | None = None,
) -> dict[str, object]:
    outcome: dict[str, object] = {
        "kind": stage_outcome,
        "next_legal_action": "record_typed_blocker",
    }
    if transition_kind:
        outcome["transition_kind"] = transition_kind
    if consumption_next_legal_action is None:
        consumption_next_legal_action = (
            "record_typed_blocker"
            if stage_outcome == "typed_blocker"
            else "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
        )
    return {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "study_id": study_id,
        "mission_state": "consumed",
        "current_package": {
            "status": "current",
            "package_kind": package_kind,
            "can_submit": can_submit,
            "quality_gate_status": "clear" if can_submit else "blocked",
            "known_blockers": [] if can_submit else ["bundle_build_allowed_false"],
            "root": f"/tmp/{study_id}/manuscript/current_package",
            "zip_path": f"/tmp/{study_id}/manuscript/current_package.zip",
            "zip_exists": True,
        },
        "stage_closure_decision": {
            "decision_ref": f"mas://paper-mission/{study_id}/stage-closure",
            "outcome": outcome,
        },
        "stage_closure_outcome": stage_outcome,
        "durable_mission_stop_guard": {
            "durable_stop_allowed": False,
        },
        "opl_runtime_carrier_readback": {
            "runtime_readback_status": "terminal_closeout_observed",
            "receipt_evidence": {
                "receipt_kind": "opl_transition_receipt",
                "receipt_ref": "opl://stage-attempts/sat-receipt",
                "impact_receipt_kind": "mas_impact_receipt",
                "impact_receipt_ref": "opl://stage-attempts/sat-receipt/mas-impact",
                "runtime_closeout_ref": (
                    "opl://family-runtime/tasks/frt-receipt/terminal-closeout-readback"
                ),
                "can_claim_paper_progress": False,
            },
            "opl_transition_receipt": {
                "surface_kind": "opl_transition_receipt",
                "receipt_status": "terminal_closeout_observed",
                "role": "transport_receipt_only",
                "task_id": "frt-receipt",
                "task_status": "blocked",
                "stage_attempt_id": "sat-receipt",
                "stage_attempt_ref": "opl://stage-attempts/sat-receipt",
                "closeout_receipt_status": "accepted_typed_closeout",
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                "can_claim_paper_progress": False,
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "next_legal_action": consumption_next_legal_action,
                "forbidden_next_action": "synonymous_route_back_redrive",
                "durable_stop_allowed": False,
                "can_claim_paper_progress": False,
                "can_claim_publication_ready": False,
            },
        },
    }
