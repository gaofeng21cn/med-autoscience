from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_owner_receipt_closeout_consumes_stale_opl_provider_admission_candidate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_attempt_id = "sat_f22f2e9d25d336fa2a2a4306"
    route_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    receipt_ref = f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "owner_receipt_recorded",
        "study_id": study_id,
        "quest_id": quest_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "acceptance_refs": [receipt_ref],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": receipt_ref,
            "provider_admission_pending": False,
        },
    }
    transition_readback = {
        "surface_kind": "opl_domain_progress_transition_runtime_live_readback",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "runtime_owner": "one-person-lab",
        "runtime_readback_status": "complete_transaction",
        "transaction_complete": True,
        "identity": {
            "surface_kind": "opl_domain_progress_transition_identity",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "aggregate_identity": {
                "aggregate_kind": "study_work_unit",
                "aggregate_id": f"{study_id}::{work_unit}",
                "study_id": study_id,
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
            },
            "stage_run_identity": {
                "stage_run_id": f"stage-run:{study_id}:{work_unit}",
                "route_identity_key": route_key,
                "attempt_idempotency_key": route_key,
                "provider_attempt_ref": f"opl://provider-admission/{study_id}/{route_key}",
                "attempt_lease_ref": f"opl://attempt-leases/{route_key}",
                "source_generation": "truth-event-000035",
            },
            "idempotency_key": route_key,
            "event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "outbox_item_id": "dpto_e79fe14bac42132383352fea",
            "transaction_id": "dptx_177b554e6934045f8bfbe7d1",
        },
        "causality": {
            "event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "outbox_item_id": "dpto_e79fe14bac42132383352fea",
            "transaction_id": "dptx_177b554e6934045f8bfbe7d1",
            "same_transaction_event_and_outbox": True,
        },
        "authority_boundary": {
            "runtime_owner": "one-person-lab",
            "opl_can_write_domain_truth": False,
            "provider_completion_is_domain_completion": False,
        },
        "exactly_one_outcome": {
            "selected": True,
            "exactly_one_transition": True,
            "transition_kind": "StartProviderAttempt",
            "outcome_kind": "provider_admission_enqueued_or_blocked",
        },
        "projection_metadata": {
            "derived_from_event_id": "dpte_c65f77b76a85ce6ac325cbb5",
            "lag_status": "current",
        },
    }
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-18T03:44:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "handoff_scan_status": "scanned_provider_admission_pending",
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "current_work_unit": current_work_unit,
                    "current_execution_envelope": {
                        "state_kind": "owner_receipt_recorded",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                    },
                    "provider_admission_candidates": [
                        {
                            "status": "provider_admission_pending",
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": route_key,
                            "attempt_idempotency_key": route_key,
                            "stage_packet_ref": stage_packet_ref,
                            "stage_packet_refs": [stage_packet_ref],
                            "provider_attempt_or_lease_required": True,
                            "provider_completion_is_domain_completion": False,
                            "opl_domain_progress_transition_runtime_live_readback": transition_readback,
                        }
                    ],
                    "action_queue": [],
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "stage_outcome/opl-handoff",
            "generated_at": "2026-06-18T03:44:00Z",
            "status": "closed",
            "execution_status": "owner_receipt_recorded",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": [stage_packet_ref],
            "owner_receipt_ref": receipt_ref,
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                f"{stage_attempt_id}.closeout.json",
                receipt_ref,
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": work_unit,
                "current_owner": "write",
                "problem_summary": "The provider stage is already closed by MAS owner receipt.",
                "stage_goal": "Bind the provider admission to the existing MAS owner receipt.",
                "stage_work_done": ["Observed owner receipt recorded for the same work unit."],
                "paper_work_done": [
                    "No manuscript or publication readiness surface was mutated by this closeout."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                    f"{stage_attempt_id}.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "closed_with_existing_mas_owner_receipt_ref",
                "remaining_blockers": ["provider_completion_is_not_domain_completion"],
                "progress_delta_classification": "platform_repair",
                "next_forced_delta": {
                    "required_delta_kind": "consume_existing_owner_receipt_or_route_to_publication_gate_or_ai_reviewer_owner",
                    "work_unit_id": work_unit,
                    "owner_action": {
                        "next_owner": "MedAutoScience",
                        "action_type": "consume_owner_receipt",
                        "work_unit_id": work_unit,
                    },
                },
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "continue",
            "reason": "owner_receipt_recorded",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
                "runtime_liveness_status": "none",
                "health_status": "none",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    consumed = handoff["provider_admission_terminal_closeout_consumed"]
    assert handoff["provider_admission_pending_count"] == 0
    assert handoff["provider_admission_candidates"] == []
    assert consumed["stage_attempt_id"] == stage_attempt_id
    assert consumed["work_unit_id"] == work_unit
    assert consumed["work_unit_fingerprint"] == fingerprint
    assert consumed["owner_receipt_ref"] == receipt_ref
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 0
    assert result["active_run_id"] is None
    assert result["current_work_unit"]["state"]["provider_admission_pending"] is False


def test_owner_receipt_closeout_consumes_stale_transition_request_candidate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_attempt_id = "sat_f22f2e9d25d336fa2a2a4306"
    route_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    receipt_ref = f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "owner_receipt_recorded",
        "study_id": study_id,
        "quest_id": quest_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "acceptance_refs": [receipt_ref],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": receipt_ref,
            "provider_admission_pending": False,
        },
    }
    transition_candidate = {
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
    }
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-18T03:44:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "handoff_scan_status": "scanned_transition_request_pending",
                    "provider_admission_pending_count": 0,
                    "provider_admission_candidates": [],
                    "transition_request_pending_count": 1,
                    "transition_request_candidates": [transition_candidate],
                    "current_work_unit": current_work_unit,
                    "current_execution_envelope": {
                        "state_kind": "owner_receipt_recorded",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                    },
                    "action_queue": [],
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "stage_outcome/opl-handoff",
            "generated_at": "2026-06-18T03:44:00Z",
            "status": "closed",
            "execution_status": "owner_receipt_recorded",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": [stage_packet_ref],
            "owner_receipt_ref": receipt_ref,
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                f"{stage_attempt_id}.closeout.json",
                receipt_ref,
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": work_unit,
                "current_owner": "write",
                "problem_summary": "The provider transition request is stale after MAS owner receipt.",
                "stage_goal": "Bind the transition request to the existing MAS owner receipt.",
                "stage_work_done": ["Observed owner receipt recorded for the same work unit."],
                "paper_work_done": [
                    "No manuscript or publication readiness surface was mutated by this closeout."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                    f"{stage_attempt_id}.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "closed_with_existing_mas_owner_receipt_ref",
                "remaining_blockers": ["provider_completion_is_not_domain_completion"],
                "progress_delta_classification": "platform_repair",
                "next_forced_delta": {
                    "required_delta_kind": "consume_existing_owner_receipt_or_route_to_publication_gate_or_ai_reviewer_owner",
                    "work_unit_id": work_unit,
                    "owner_action": {
                        "next_owner": "MedAutoScience",
                        "action_type": "consume_owner_receipt",
                        "work_unit_id": work_unit,
                    },
                },
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "continue",
            "reason": "owner_receipt_recorded",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
                "runtime_liveness_status": "none",
                "health_status": "none",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    consumed = handoff["provider_admission_terminal_closeout_consumed"]
    assert handoff["provider_admission_pending_count"] == 0
    assert handoff["provider_admission_candidates"] == []
    assert handoff["transition_request_pending_count"] == 0
    assert handoff["transition_request_candidates"] == []
    assert consumed["stage_attempt_id"] == stage_attempt_id
    assert consumed["work_unit_id"] == work_unit
    assert consumed["work_unit_fingerprint"] == fingerprint
    assert consumed["owner_receipt_ref"] == receipt_ref
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 0
    assert result["transition_request_candidates"] == []
