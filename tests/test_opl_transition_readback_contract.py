from __future__ import annotations

import copy
import importlib

from tests.provider_admission_current_control_helpers import opl_transition_readback


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WORK_UNIT_ID = "medical_prose_write_repair"
FINGERPRINT = "publication-blockers::0915410f804b3697"


def _live_readback() -> dict[str, object]:
    return opl_transition_readback(
        STUDY_ID,
        action_fingerprint=FINGERPRINT,
        work_unit_id=WORK_UNIT_ID,
        request_idempotency_key=f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
    )


def _legacy_result() -> dict[str, object]:
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "outcome_kind": "provider_admission_pending",
        "event_id": "legacy-event",
        "outbox_item_id": "legacy-outbox",
        "stage_run_identity": {
            "stage_run_id": "legacy-stage-run",
            "observed_generation": FINGERPRINT,
        },
        "identity": {
            "study_id": STUDY_ID,
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": FINGERPRINT,
            "route_identity_key": f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
            "attempt_idempotency_key": f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
        },
        "causality": {
            "mas_transition_request_idempotency_key": f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
            "source_generation": FINGERPRINT,
            "expected_version": FINGERPRINT,
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
            "allowed": ["provider_admission_pending"],
        },
        "projection_metadata": {
            "authority": False,
            "projection_owner": "one-person-lab",
            "consumer": "med-autoscience",
            "observed_generation": FINGERPRINT,
        },
    }


def test_trusted_opl_transition_live_readback_requires_full_transaction_shape() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    contract = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    trusted = _live_readback()

    assert module.required_opl_transition_readback_shape() == contract.required_readback_shape()
    assert module.required_opl_transition_readback_shape()["surface_kind"] == contract.LIVE_READBACK_SURFACE
    assert module.required_opl_transition_readback_shape()["transaction_consistency"] == (
        contract.live_readback_transaction_consistency()
    )
    assert module.required_opl_transition_readback_shape()["identity_transaction_refs"] == list(
        contract.LIVE_READBACK_IDENTITY_TRANSACTION_REFS
    )
    assert module.required_opl_transition_readback_shape()["latest_transaction_required_flags"] == list(
        contract.LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS
    )
    assert module.valid_opl_transition_readback(trusted) is True
    assert module.candidate_opl_transition_readback(
        {"opl_domain_progress_transition_live_readback": trusted}
    ) == trusted
    assert module.candidate_opl_transition_readback(
        {"opl_domain_progress_transition_result": trusted}
    ) == trusted

    incomplete = dict(trusted)
    incomplete["runtime_readback_status"] = "incomplete_transaction"
    incomplete["transaction_complete"] = False
    assert module.valid_opl_transition_readback(incomplete) is False

    missing_outbox = dict(trusted)
    missing_outbox["latest_transaction_readback"] = {
        **dict(trusted["latest_transaction_readback"]),
        "outbox_item_present": False,
    }
    assert module.valid_opl_transition_readback(missing_outbox) is False

    stage_identity_without_run_ref = copy.deepcopy(trusted)
    stage_identity_without_run_ref["identity"]["stage_run_identity"].pop("stage_run_id")
    assert module.valid_opl_transition_readback(stage_identity_without_run_ref) is False

    latest_event_mismatch = copy.deepcopy(trusted)
    latest_event_mismatch["latest_transaction_readback"]["event_id"] = "dpte-stale"
    assert module.valid_opl_transition_readback(latest_event_mismatch) is False

    latest_transaction_mismatch = copy.deepcopy(trusted)
    latest_transaction_mismatch["latest_transaction_readback"][
        "transaction_id"
    ] = "dptx-stale"
    assert module.valid_opl_transition_readback(latest_transaction_mismatch) is False

    causality_outbox_mismatch = copy.deepcopy(trusted)
    causality_outbox_mismatch["causality"]["outbox_item_id"] = "dpto-stale"
    assert module.valid_opl_transition_readback(causality_outbox_mismatch) is False

    projection_event_mismatch = copy.deepcopy(trusted)
    projection_event_mismatch["projection_metadata"]["derived_from_event_id"] = "dpte-stale"
    assert module.valid_opl_transition_readback(projection_event_mismatch) is False


def test_legacy_transition_result_and_bare_projection_are_not_trusted() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    weak_readback = {
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "outcome_kind": "provider_admission_pending",
        "event_id": "legacy-event-only",
        "stage_run_id": "legacy-stage-run-only",
    }
    legacy_result = _legacy_result()

    assert module.valid_opl_transition_readback(legacy_result) is False
    assert module.valid_opl_transition_readback(weak_readback) is False
    assert module.candidate_opl_transition_readback(
        {
            "opl_domain_progress_transition_result": legacy_result,
            "deprecated_opl_transition_projection": weak_readback,
        }
    ) == {}


def test_complete_command_event_outbox_log_is_not_rebuilt_by_mas_consumer() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    idempotency_key = f"provider-admission::{STUDY_ID}::{FINGERPRINT}"
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{STUDY_ID}::{WORK_UNIT_ID}",
        "study_id": STUDY_ID,
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FINGERPRINT,
    }
    stage_run_identity = {
        "stage_run_id": "stage-run-log-derived",
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "source_generation": FINGERPRINT,
    }
    entries = [
        {
            "entry_kind": "command",
            "transaction_id": "dptx_log_derived",
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": "dptc_log_derived",
                "source_generation": FINGERPRINT,
                "expected_version": FINGERPRINT,
                "stage_run_identity": stage_run_identity,
            },
        },
        {
            "entry_kind": "event",
            "transaction_id": "dptx_log_derived",
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": "dptc_log_derived",
                "event_id": "dpte_log_derived",
                "source_generation": FINGERPRINT,
                "expected_version": FINGERPRINT,
                "stage_run_identity": stage_run_identity,
                "outcome": {"kind": "provider_admission_enqueued_or_blocked"},
            },
        },
        {
            "entry_kind": "outbox_item",
            "transaction_id": "dptx_log_derived",
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "outbox_item_id": "dpto_log_derived",
                "transition_event_id": "dpte_log_derived",
                "outbox_kind": "start_provider_attempt",
                "stage_run_identity": stage_run_identity,
            },
        },
    ]

    for entry in entries:
        assert module.candidate_opl_transition_readback(entry) == {}


def test_mas_consumer_rejects_prebuilt_opl_live_readback_in_log_entries() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    idempotency_key = f"provider-admission::{STUDY_ID}::{FINGERPRINT}"
    trusted = _live_readback()
    entries = [
        {
            "entry_kind": "command",
            "idempotency_key": idempotency_key,
            "payload": {"command_id": "dptc-fragment-only"},
        },
        {
            "entry_kind": "read_model_readback",
            "idempotency_key": idempotency_key,
            "payload": {"read_model_readback": trusted["read_model_readback"]},
        },
        {
            "entry_kind": "runtime_live_readback",
            "idempotency_key": idempotency_key,
            "payload": {"opl_domain_progress_transition_runtime_live_readback": trusted},
        },
    ]

    for entry in entries:
        assert module.candidate_opl_transition_readback(entry) == {}

    assert module.candidate_opl_transition_readback(
        {"opl_domain_progress_transition_runtime_live_readback": trusted}
    ) == trusted


def test_mas_consumer_no_longer_exposes_command_event_log_extractors() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    assert not hasattr(module, "opl_transition_readback_from_log_entries")
    assert not hasattr(module, "opl_transition_readback_from_log_file")


def test_mas_consumer_does_not_trust_generic_result_container() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    idempotency_key = f"provider-admission::{STUDY_ID}::{FINGERPRINT}"
    trusted = _live_readback()

    readback = module.candidate_opl_transition_readback(
        {
            "entry_kind": "generic_result",
            "idempotency_key": idempotency_key,
            "payload": {"result": trusted},
        }
    )

    assert readback == {}


def test_provider_admission_requires_trusted_opl_readback_not_weak_projection() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )
    identity = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity"
    )
    candidate = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "next_executable_owner": "write",
        "route_identity_key": f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
        "attempt_idempotency_key": f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "idempotency_key": f"provider-admission::{STUDY_ID}::{FINGERPRINT}",
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
        },
        "opl_domain_progress_transition_result": {
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

    legacy_pending = identity.provider_admission_current_control_action(
        {
            **candidate,
            "opl_domain_progress_transition_result": _legacy_result(),
        }
    )
    assert legacy_pending["status"] == "transition_request_pending"
    assert legacy_pending["provider_admission_pending"] is False
    assert legacy_pending["provider_admission_requires_opl_runtime_result"] is True

    live_admitted = identity.provider_admission_current_control_action(
        {
            **candidate,
            "opl_domain_progress_transition_result": _live_readback(),
        }
    )
    assert live_admitted["status"] == "queued"
    assert live_admitted["provider_admission_pending"] is True
    assert live_admitted["provider_attempt_or_lease_required"] is True
    assert live_admitted["provider_completion_is_domain_completion"] is False
    assert live_admitted["opl_domain_progress_transition_live_readback"]["identity"][
        "aggregate_identity"
    ]["study_id"] == STUDY_ID

    stale_event_readback = copy.deepcopy(_live_readback())
    stale_event_readback["latest_transaction_readback"]["event_id"] = "stale-event"
    stale_event_pending = identity.provider_admission_current_control_action(
        {
            **candidate,
            "opl_domain_progress_transition_result": stale_event_readback,
        }
    )
    assert stale_event_pending["status"] == "transition_request_pending"
    assert stale_event_pending["provider_admission_pending"] is False
    assert stale_event_pending["provider_admission_requires_opl_runtime_result"] is True
