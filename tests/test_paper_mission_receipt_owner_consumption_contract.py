from __future__ import annotations

from copy import deepcopy

from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    materialize_receipt_owner_consumption,
)


STUDY_ID = "002-dm-china-us-mortality-attribution"
TRANSACTION_REF = "paper-mission-transaction::dm002"


def _request_carrier() -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "study_id": STUDY_ID,
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "paper-mission::dm002::publication-gate",
        "domain_route_handoff_ref": f"{TRANSACTION_REF}#domain_route_handoff",
        "domain_route_transaction_ref": TRANSACTION_REF,
        "domain_route_command_ref": f"{TRANSACTION_REF}#opl_route_command",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "idempotency_key": "dm002",
        "request_idempotency_key": "dm002::request",
        "attempt_idempotency_key": "dm002::attempt",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }


def _canonical_receipt() -> dict[str, object]:
    return {
        "surface_kind": "opl_domain_route_transition_receipt",
        "role": "transport_receipt_only",
        "domain_id": "mas",
        "task_kind": "domain_route/stage-route",
        "domain_route_handoff_ref": f"{TRANSACTION_REF}#domain_route_handoff",
        "domain_route_transaction_ref": TRANSACTION_REF,
        "domain_route_command_ref": f"{TRANSACTION_REF}#opl_route_command",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "idempotency_key": "dm002",
        "request_idempotency_key": "dm002::request",
        "attempt_idempotency_key": "dm002::attempt",
        "stage_attempt_ref": "opl://stage-attempts/sat-001",
        "runtime_closeout_ref": "opl://family-runtime/tasks/task-001/terminal-closeout-readback",
        "typed_runtime_blocker_ref": "opl://stage-attempts/sat-001/typed-blocker",
        "can_claim_paper_progress": False,
        "authority_boundary": {
            "writes_domain_owner_receipt": False,
            "writes_domain_typed_blocker": False,
            "writes_domain_human_gate": False,
            "writes_domain_current_package": False,
            "can_select_next_owner": False,
            "can_claim_domain_progress": False,
        },
    }


def _readback() -> dict[str, object]:
    receipt = _canonical_receipt()
    evidence = {
        "surface_kind": "mas_receipt_evidence",
        "receipt_kind": receipt["surface_kind"],
        "receipt_ref": receipt["domain_route_handoff_ref"],
        "domain_route_handoff_ref": receipt["domain_route_handoff_ref"],
        "domain_route_transaction_ref": receipt["domain_route_transaction_ref"],
        "domain_route_command_ref": receipt["domain_route_command_ref"],
        "runtime_closeout_ref": receipt["runtime_closeout_ref"],
        "stage_attempt_ref": receipt["stage_attempt_ref"],
        "typed_runtime_blocker_ref": receipt["typed_runtime_blocker_ref"],
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
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
    consumption = {
        "surface_kind": "mas_receipt_consumption_projection",
        "status": "requires_mas_owner_consumption",
        "next_legal_action": "record_typed_blocker",
        "receipt_evidence_ref": evidence["receipt_ref"],
        "typed_runtime_blocker_ref": receipt["typed_runtime_blocker_ref"],
        "forbidden_next_action": "synonymous_route_back_redrive",
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
    }
    return {
        "study_id": STUDY_ID,
        "opl_runtime_carrier": _request_carrier(),
        "opl_runtime_carrier_readback": {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "opl_transition_receipt": receipt,
            "receipt_evidence": evidence,
            "mas_receipt_consumption": consumption,
        },
    }


def test_apply_rejects_canonical_kind_without_required_domain_identity() -> None:
    readback = _readback()
    receipt = readback["opl_runtime_carrier_readback"]["opl_transition_receipt"]
    del receipt["domain_id"]

    result = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=STUDY_ID,
        profile_ref="profiles/workspace.profile.template.toml",
        apply_mode="typed_blocker",
    )

    assert result["status"] == "blocked_missing_consumable_opl_receipt"
    assert result["write_permitted"] is False
    assert result["authority_materialized"] is False


def test_apply_accepts_canonical_receipt_without_receipt_study_id() -> None:
    result = materialize_receipt_owner_consumption(
        paper_mission_readback=deepcopy(_readback()),
        study_id=STUDY_ID,
        profile_ref="profiles/workspace.profile.template.toml",
        apply_mode="typed_blocker",
    )

    assert result["status"] == "owner_consumption_applied"
    assert result["write_permitted"] is True


def test_apply_rejects_unbound_receipt_evidence_reference() -> None:
    readback = _readback()
    receipt_carrier = readback["opl_runtime_carrier_readback"]
    receipt_carrier["receipt_evidence"].pop("receipt_ref")
    receipt_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = None

    result = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=STUDY_ID,
        profile_ref="profiles/workspace.profile.template.toml",
        apply_mode="typed_blocker",
    )

    assert result["status"] == "blocked_missing_consumable_opl_receipt"
    assert result["write_permitted"] is False
