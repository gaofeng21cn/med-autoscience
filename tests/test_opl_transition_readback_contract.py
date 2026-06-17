from __future__ import annotations

import importlib


def _trusted_readback() -> dict[str, object]:
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": "opl-domain-progress-event:003-write",
        "outbox_item_id": "opl-domain-progress-outbox:003-write",
        "stage_run_identity": {
            "stage_run_id": "sat_003_write",
            "stage_run_identity_ref": "stage-run-identity:003-write",
            "observed_generation": "publication-blockers::0915410f804b3697",
        },
        "identity": {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "route_identity_key": (
                "provider-admission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "publication-blockers::0915410f804b3697"
            ),
            "attempt_idempotency_key": (
                "provider-admission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "publication-blockers::0915410f804b3697"
            ),
        },
        "causality": {
            "mas_transition_request_idempotency_key": "paper-policy-request:003-write",
            "source_generation": "publication-blockers::0915410f804b3697",
            "expected_version": "publication-blockers::0915410f804b3697",
            "derived_from_request": True,
        },
        "authority_boundary": {
            "runtime_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
            "mas_can_authorize_provider_admission": False,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
            "provider_completion_is_domain_completion": False,
        },
        "exactly_one_outcome": {
            "selected": "provider_admission_pending",
            "allowed": [
                "provider_admission_pending",
                "running_provider_attempt",
                "owner_receipt_ref",
                "typed_blocker_ref",
                "human_gate_ref",
                "route_back_evidence_ref",
            ],
        },
        "projection_metadata": {
            "authority": False,
            "projection_owner": "one-person-lab",
            "consumer": "med-autoscience",
            "observed_generation": "publication-blockers::0915410f804b3697",
        },
    }


def test_trusted_opl_transition_readback_requires_full_runtime_shape() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )

    assert module.valid_opl_transition_readback(_trusted_readback()) is True

    weak_readback = {
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "outcome_kind": "provider_admission_pending",
        "event_id": "opl-domain-progress-event:003-write",
        "stage_run_id": "sat_003_write",
    }

    assert module.valid_opl_transition_readback(weak_readback) is False
    assert module.candidate_opl_transition_readback(
        {
            "opl_domain_progress_transition_result": weak_readback,
            "deprecated_opl_transition_projection": weak_readback,
        }
    ) == {}


def test_provider_admission_requires_structured_opl_readback_not_deprecated_projection() -> None:
    identity = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
        "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
        },
        "deprecated_opl_transition_projection": {
            "runtime_owner": "one-person-lab",
            "runtime_kind": "DomainProgressTransitionRuntime",
            "outcome_kind": "provider_admission_pending",
            "event_id": "legacy-event-only",
            "stage_run_id": "legacy-stage-run-only",
        },
    }

    pending = identity.provider_admission_current_control_action(candidate)
    assert pending["status"] == "transition_request_pending"
    assert pending["provider_admission_pending"] is False
    assert pending["provider_admission_requires_opl_runtime_result"] is True
    assert "opl_domain_progress_transition_result" not in pending

    admitted = identity.provider_admission_current_control_action(
        {**candidate, "opl_domain_progress_transition_result": _trusted_readback()}
    )
    assert admitted["status"] == "queued"
    assert admitted["provider_admission_pending"] is True
    assert admitted["provider_attempt_or_lease_required"] is True
    assert admitted["provider_completion_is_domain_completion"] is False
    assert admitted["opl_domain_progress_transition_result"]["identity"]["study_id"] == study_id


def test_opl_transition_runtime_log_entries_rebuild_trusted_readback() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{study_id}::{work_unit_id}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    stage_run_identity = {
        "stage_run_id": f"stage-run:{study_id}:{work_unit_id}",
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "provider_attempt_ref": f"opl://provider-admission/{study_id}/{idempotency_key}",
        "attempt_lease_ref": f"opl://attempt-leases/{idempotency_key}",
        "source_generation": "truth-event-000035-39f0b8e96689a623",
    }
    command_entry = {
        "entry_kind": "command",
        "transaction_id": "dptx_177b554e6934045f8bfbe7d1",
        "idempotency_key": idempotency_key,
        "aggregate_identity": aggregate_identity,
        "aggregate_version": 1,
        "payload": {
            "surface_kind": "opl_domain_progress_transition_command",
            "runtime_owner": "one-person-lab",
            "runtime_kind": "DomainProgressTransitionRuntime",
            "transition_kind": "StartProviderAttempt",
            "command_id": "dptc_4130794f3bdfb3a48b34ca78",
            "idempotency_key": idempotency_key,
            "source_generation": "truth-event-000035-39f0b8e96689a623",
            "expected_version": "truth-event-000035-39f0b8e96689a623",
            "stage_run_identity": stage_run_identity,
            "postcondition": {
                "kind": "provider_admission_enqueued_or_blocked",
                "outcome_owner": "one-person-lab",
                "domain_state_owner": "med-autoscience",
                "exactly_one_transition_required": True,
                "non_advancing_apply_on_no_outcome": True,
            },
            "authority_boundary": {
                "opl_can_write_domain_truth": False,
                "opl_can_create_domain_owner_receipt": False,
                "opl_can_create_domain_typed_blocker": False,
                "provider_completion_is_domain_completion": False,
            },
        },
    }
    event_entry = {
        "entry_kind": "event",
        "transaction_id": "dptx_177b554e6934045f8bfbe7d1",
        "event_id": "dpte_c65f77b76a85ce6ac325cbb5",
        "idempotency_key": idempotency_key,
        "aggregate_identity": aggregate_identity,
        "aggregate_version": 1,
        "payload": {
            "surface_kind": "opl_domain_progress_transition_event",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "runtime_owner": "one-person-lab",
            "module_id": "runway",
            "transition_kind": "StartProviderAttempt",
            "command_id": "dptc_4130794f3bdfb3a48b34ca78",
            "event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "idempotency_key": idempotency_key,
            "source_generation": "truth-event-000035-39f0b8e96689a623",
            "expected_version": "truth-event-000035-39f0b8e96689a623",
            "stage_run_identity": stage_run_identity,
            "outcome": {
                "kind": "provider_admission_enqueued_or_blocked",
                "stable_outcome": True,
            },
            "postcondition": command_entry["payload"]["postcondition"],
            "authority_boundary": command_entry["payload"]["authority_boundary"],
        },
    }
    outbox_entry = {
        "entry_kind": "outbox_item",
        "transaction_id": "dptx_177b554e6934045f8bfbe7d1",
        "outbox_item_id": "dpto_e79fe14bac42132383352fea",
        "idempotency_key": idempotency_key,
        "aggregate_identity": aggregate_identity,
        "aggregate_version": 1,
        "payload": {
            "surface_kind": "opl_domain_progress_transition_outbox_item",
            "outbox_item_id": "dpto_e79fe14bac42132383352fea",
            "transition_event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "outbox_kind": "start_provider_attempt",
            "idempotency_key": idempotency_key,
            "stage_run_identity": stage_run_identity,
            "dispatch_allowed": True,
            "domain_truth_mutation_allowed": False,
        },
    }

    readback = module.opl_transition_readback_from_log_entries(
        [command_entry, event_entry, outbox_entry],
        idempotency_key=idempotency_key,
        study_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
    )

    assert module.valid_opl_transition_readback(readback) is True
    assert readback["event_id"] == "dpte_c65f77b76a85ce6ac325cbb5"
    assert readback["outbox_item_id"] == "dpto_e79fe14bac42132383352fea"
    assert readback["identity"]["attempt_idempotency_key"] == idempotency_key
    assert readback["causality"]["mas_transition_request_idempotency_key"] == idempotency_key
    assert readback["projection_metadata"]["derived_from_event_id"] == "dpte_c65f77b76a85ce6ac325cbb5"


def test_opl_transition_runtime_log_readback_falls_back_to_aggregate_identity_when_request_key_drifts() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    opl_idempotency_key = "paper-policy-request:from-opl-transaction"
    consumer_idempotency_key = "paper-policy-request:consumer-recomputed"
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{study_id}::{work_unit_id}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    stage_run_identity = {
        "stage_run_id": f"stage-run:{study_id}:{work_unit_id}",
        "route_identity_key": opl_idempotency_key,
        "attempt_idempotency_key": opl_idempotency_key,
        "source_generation": "truth-event-000035-39f0b8e96689a623",
    }
    entries = [
        {
            "entry_kind": "command",
            "transaction_id": "dptx_drifted_key",
            "idempotency_key": opl_idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": "dptc_drifted_key",
                "source_generation": "truth-event-000035-39f0b8e96689a623",
                "expected_version": "truth-event-000035-39f0b8e96689a623",
                "stage_run_identity": stage_run_identity,
            },
        },
        {
            "entry_kind": "event",
            "transaction_id": "dptx_drifted_key",
            "event_id": "dpte_drifted_key",
            "idempotency_key": opl_idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": "dptc_drifted_key",
                "event_id": "dpte_drifted_key",
                "source_generation": "truth-event-000035-39f0b8e96689a623",
                "expected_version": "truth-event-000035-39f0b8e96689a623",
                "stage_run_identity": stage_run_identity,
                "outcome": {"kind": "provider_admission_enqueued_or_blocked"},
            },
        },
        {
            "entry_kind": "outbox_item",
            "transaction_id": "dptx_drifted_key",
            "outbox_item_id": "dpto_drifted_key",
            "idempotency_key": opl_idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "outbox_item_id": "dpto_drifted_key",
                "transition_event_id": "dpte_drifted_key",
                "stage_run_identity": stage_run_identity,
            },
        },
    ]

    readback = module.opl_transition_readback_from_log_entries(
        entries,
        idempotency_key=consumer_idempotency_key,
        study_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
    )

    assert module.valid_opl_transition_readback(readback) is True
    assert readback["event_id"] == "dpte_drifted_key"
    assert readback["causality"]["mas_transition_request_idempotency_key"] == opl_idempotency_key
    assert readback["causality"]["consumer_requested_idempotency_key"] == consumer_idempotency_key
    assert (
        module.opl_transition_readback_from_log_entries(
            entries[:2],
            idempotency_key=consumer_idempotency_key,
            study_id=study_id,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=fingerprint,
        )
        == {}
    )
    assert (
        module.opl_transition_readback_from_log_entries(
            entries,
            idempotency_key=consumer_idempotency_key,
            study_id=study_id,
            work_unit_id=work_unit_id,
            work_unit_fingerprint="publication-blockers::other",
        )
        == {}
    )
