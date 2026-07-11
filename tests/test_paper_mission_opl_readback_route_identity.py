from __future__ import annotations

from med_autoscience.paper_mission_opl_readback.route_identity import (
    matches_carrier,
)


def _carrier() -> dict[str, object]:
    transaction_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap"
        "::write::dm003_calendar_year_revision"
    )
    return {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "stage_id": "write",
        "work_unit_id": "dm003_calendar_year_revision",
        "work_unit_fingerprint": "sha256:current-revision",
        "paper_mission_transaction_ref": transaction_ref,
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "idempotency_key": "003::write::calendar-year",
        "request_idempotency_key": "003::write::calendar-year::opl-request",
        "attempt_idempotency_key": "003::write::calendar-year::opl-attempt",
        "command_kind": "route_back",
        "route_target": "write",
    }


def _record_only_boundary() -> dict[str, bool]:
    return {
        "record_only_surface": True,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_current_package": False,
        "writes_publication_eval": False,
        "writes_controller_decision": False,
        "writes_owner_receipt": False,
        "writes_typed_blocker": False,
        "writes_human_gate": False,
        "writes_runtime_queue_or_provider_attempt": False,
        "can_claim_paper_progress": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
    }


def test_matches_carrier_accepts_provider_opaque_closeout_idempotency_when_route_bound() -> None:
    carrier = _carrier()
    closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "study_id": carrier["study_id"],
        "stage_id": "write",
        "work_unit_id": carrier["work_unit_id"],
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "paper_mission_transaction_ref": carrier["paper_mission_transaction_ref"],
        "opl_route_command_ref": carrier["opl_route_command_ref"],
        "stage_attempt_id": "sat_75f897fbb57d888c800b39c5",
        "status": "completed",
        "idempotency_key": "idem_provider_attempt_closeout",
        "authority_boundary": _record_only_boundary(),
    }

    assert matches_carrier(closeout=closeout, carrier=carrier)


def test_matches_carrier_rejects_cross_route_closeout_even_with_opaque_idempotency() -> None:
    carrier = _carrier()
    other_transaction_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap"
        "::write::different_revision"
    )
    closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "study_id": carrier["study_id"],
        "stage_id": "write",
        "work_unit_id": carrier["work_unit_id"],
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "paper_mission_transaction_ref": other_transaction_ref,
        "opl_route_command_ref": f"{other_transaction_ref}#opl_route_command",
        "stage_attempt_id": "sat_stale",
        "status": "completed",
        "idempotency_key": "idem_provider_attempt_closeout",
        "authority_boundary": _record_only_boundary(),
    }

    assert not matches_carrier(closeout=closeout, carrier=carrier)


def test_matches_carrier_accepts_only_canonical_domain_route_refs() -> None:
    transaction_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap"
        "::write::dm003_calendar_year_revision"
    )
    carrier = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "work_unit_id": "dm003_calendar_year_revision",
        "work_unit_fingerprint": "sha256:current-revision",
        "domain_route_handoff_ref": f"{transaction_ref}#domain_route_handoff",
        "domain_route_transaction_ref": transaction_ref,
        "domain_route_command_ref": f"{transaction_ref}#opl_route_command",
        "idempotency_key": "003::write::calendar-year",
        "request_idempotency_key": "003::write::calendar-year::opl-request",
        "attempt_idempotency_key": "003::write::calendar-year::opl-attempt",
        "command_kind": "route_back",
        "route_target": "write",
    }
    closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "study_id": carrier["study_id"],
        "stage_id": "write",
        "work_unit_id": "provider-opaque-work-unit",
        "domain_route_handoff_ref": carrier["domain_route_handoff_ref"],
        "domain_route_transaction_ref": carrier["domain_route_transaction_ref"],
        "domain_route_command_ref": carrier["domain_route_command_ref"],
        "authority_boundary": _record_only_boundary(),
    }

    assert matches_carrier(closeout=closeout, carrier=carrier)


def test_matches_carrier_rejects_wrong_canonical_domain_route_ref() -> None:
    transaction_ref = "paper-mission-transaction::003::write::current"
    carrier = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "work_unit_id": "dm003_calendar_year_revision",
        "work_unit_fingerprint": "sha256:current-revision",
        "domain_route_handoff_ref": f"{transaction_ref}#domain_route_handoff",
        "domain_route_transaction_ref": transaction_ref,
        "domain_route_command_ref": f"{transaction_ref}#opl_route_command",
        "command_kind": "route_back",
        "route_target": "write",
    }
    closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "study_id": carrier["study_id"],
        "stage_id": "write",
        "work_unit_id": carrier["work_unit_id"],
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "domain_route_handoff_ref": "paper-mission-transaction::other#domain_route_handoff",
        "domain_route_transaction_ref": "paper-mission-transaction::other",
        "domain_route_command_ref": "paper-mission-transaction::other#opl_route_command",
        "authority_boundary": _record_only_boundary(),
    }

    assert not matches_carrier(closeout=closeout, carrier=carrier)
