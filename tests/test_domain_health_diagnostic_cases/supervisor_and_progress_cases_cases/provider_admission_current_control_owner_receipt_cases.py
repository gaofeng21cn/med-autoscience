from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_current_control_consumes_owner_receipt_recorded_terminal_closeout() -> None:
    current_control = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(Path("/tmp/mas-provider-admission-owner-receipt-closeout"))
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    candidate = {
        "study_id": study_id,
        "quest_id": study_id,
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "status": "provider_admission_pending",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "next_executable_owner": "write",
        "dispatch_ref": stage_packet_ref,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
        },
        "opl_domain_progress_transition_runtime_live_readback": _opl_transition_live_readback(
            study_id=study_id,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            idempotency_key=idempotency_key,
        ),
    }
    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "accepted_closeout_evidence": [
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "schema_version": 1,
                "stage_attempt_id": "sat_f22f2e9d25d336fa2a2a4306",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_packet_ref": stage_packet_ref,
                "stage_packet_refs": [stage_packet_ref],
                "status": "closed",
                "execution_status": "owner_receipt_recorded",
                "outcome": (
                    "closed_with_existing_mas_owner_receipt_ref; "
                    "provider_completion_is_not_domain_completion"
                ),
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner": "write",
                "owner_receipt_ref": (
                    f"studies/{study_id}/artifacts/controller/"
                    "repair_execution_receipts/latest.json"
                ),
                "paper_stage_log": {
                    "progress_delta_classification": "platform_repair",
                    "outcome": (
                        "closed_with_existing_mas_owner_receipt_ref; "
                        "provider_completion_is_not_domain_completion"
                    ),
                    "remaining_blockers": [
                        "provider_completion_is_not_domain_completion",
                    ],
                },
                "closeout_refs": [
                    f"studies/{study_id}/artifacts/supervision/consumer/"
                    "default_executor_execution/sat_f22f2e9d25d336fa2a2a4306.closeout.json",
                    f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
                ],
            }
        ],
    }

    payload = current_control.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-18T05:30:00+00:00",
        apply=False,
        scanned_studies=[scanned_study],
    )

    assert payload is not None
    assert payload["provider_admission_pending_count"] == 0
    assert payload["provider_admission_candidates"] == []
    assert payload["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = payload["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence"]["execution_status"] == "owner_receipt_recorded"
    assert decision["evidence"]["owner_receipt_ref"].endswith(
        "repair_execution_receipts/latest.json"
    )


def _opl_transition_live_readback(
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
    idempotency_key: str,
) -> dict[str, object]:
    stage_run_identity = {
        "stage_run_id": f"stage-run:{study_id}:{work_unit_id}",
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "source_generation": fingerprint,
    }
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{study_id}::{work_unit_id}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    return {
        "surface_kind": "opl_domain_progress_transition_runtime_live_readback",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "runtime_readback_status": "complete_transaction",
        "transaction_complete": True,
        "identity": {
            "aggregate_identity": aggregate_identity,
            "stage_run_identity": stage_run_identity,
            "latest_event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "latest_outbox_item_id": "dpto_e79fe14bac42132383352fea",
            "latest_transaction_id": "dptx_177b554e6934045f8bfbe7d1",
        },
        "latest_transaction_readback": {
            "command_present": True,
            "event_present": True,
            "outbox_item_present": True,
            "same_transaction_event_and_outbox": True,
        },
        "causality": {
            "transaction_complete": True,
            "runtime_readback_status": "complete_transaction",
            "event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "outbox_item_id": "dpto_e79fe14bac42132383352fea",
            "same_transaction_event_and_outbox": True,
            "source_generation": fingerprint,
            "expected_version": fingerprint,
        },
        "authority_boundary": {
            "runtime_owner": "one-person-lab",
            "authority": False,
            "opl_can_write_domain_truth": False,
            "opl_can_write_mas_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_domain_typed_blocker": False,
            "provider_completion_is_domain_completion": False,
        },
        "exactly_one_outcome": {
            "selected": True,
            "exactly_one_transition": True,
            "stable_outcome": True,
            "fail_closed": False,
            "outcome_kind": "provider_admission_enqueued_or_blocked",
        },
        "projection_metadata": {
            "authority": False,
            "runtime_id": "opl_domain_progress_transition_runtime",
            "read_model_rebuild_owner": "one-person-lab",
            "derived_from_event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "observed_generation": fingerprint,
        },
    }
