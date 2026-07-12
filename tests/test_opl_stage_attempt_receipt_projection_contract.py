from __future__ import annotations

from med_autoscience.controllers.study_progress.mission_summary.receipt_projection import (
    _opl_stage_attempt_receipt,
)
from med_autoscience.controllers.study_progress.progress_first_monitoring.summary import (
    build_progress_first_monitoring_summary,
)


TRANSACTION_REF = "paper-mission-transaction::dm002"


def _carrier() -> dict[str, object]:
    return {
        "domain_id": "mas",
        "domain_route_handoff_ref": f"{TRANSACTION_REF}#domain_route_handoff",
        "domain_route_transaction_ref": TRANSACTION_REF,
        "domain_route_command_ref": f"{TRANSACTION_REF}#ai_route_context",
        "idempotency_key": "dm002",
        "request_idempotency_key": "dm002::request",
        "attempt_idempotency_key": "dm002::attempt",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "ai_route_context": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }


def _receipt() -> dict[str, object]:
    return {
        "surface_kind": "opl_stage_attempt_transport_receipt",
        "role": "transport_receipt_only",
        "domain_id": "mas",
        "task_kind": "domain_route/stage-route",
        "domain_route_handoff_ref": f"{TRANSACTION_REF}#domain_route_handoff",
        "domain_route_transaction_ref": TRANSACTION_REF,
        "domain_route_command_ref": f"{TRANSACTION_REF}#ai_route_context",
        "idempotency_key": "dm002",
        "request_idempotency_key": "dm002::request",
        "attempt_idempotency_key": "dm002::attempt",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "authority_boundary": {
            "writes_domain_owner_receipt": False,
            "writes_domain_typed_blocker": False,
            "writes_domain_human_gate": False,
            "writes_domain_current_package": False,
            "can_select_next_owner": False,
            "can_claim_domain_progress": False,
        },
    }


def test_projections_reject_incomplete_new_kind_receipt() -> None:
    carrier = _carrier()
    incomplete = {
        "surface_kind": "opl_stage_attempt_transport_receipt",
        "can_claim_paper_progress": False,
    }

    assert _opl_stage_attempt_receipt(
        summary={
            "opl_stage_run_context": carrier,
            "opl_stage_attempt_receipt": incomplete,
        }
    ) == {}
    monitoring = build_progress_first_monitoring_summary(
        {
            "opl_stage_run_context": carrier,
            "opl_stage_attempt_receipt": incomplete,
        }
    )
    assert monitoring["opl_stage_attempt_receipt"] is None


def test_projections_keep_valid_canonical_receipt_without_receipt_study_id() -> None:
    carrier = _carrier()
    receipt = _receipt()

    assert _opl_stage_attempt_receipt(
        summary={
            "opl_stage_run_context": carrier,
            "opl_stage_attempt_receipt": receipt,
        }
    )["domain_route_transaction_ref"] == TRANSACTION_REF
    monitoring = build_progress_first_monitoring_summary(
        {
            "opl_stage_run_context": carrier,
            "opl_stage_attempt_receipt": receipt,
        }
    )
    assert monitoring["opl_stage_attempt_receipt"]["domain_route_handoff_ref"].endswith(
        "#domain_route_handoff"
    )
