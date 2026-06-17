from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study

from ..shared import _write_json


def _opl_transition_result(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "publication_gate_replay",
    fingerprint: str = "sha256:6423b231114cbec0e8d1ccb0b69adb117d0f2d8fa58d72751627c049a0dc10e4",
    stage_run_id: str = "stage-run-gate-replay",
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": f"opl-domain-progress-event::{study_id}::{fingerprint}",
        "outbox_item_id": f"opl-domain-progress-outbox::{study_id}::{fingerprint}",
        "stage_run_identity": {
            "stage_run_id": stage_run_id,
            "stage_run_identity_ref": f"stage-run-identity::{study_id}::{fingerprint}",
            "observed_generation": fingerprint,
        },
        "identity": {
            "study_id": study_id,
            "quest_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
        },
        "causality": {
            "mas_transition_request_idempotency_key": route_key,
            "source_generation": fingerprint,
            "expected_version": fingerprint,
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
            "observed_generation": fingerprint,
        },
    }


def test_existing_projection_refresh_replays_gate_admission_after_recovery_state_materializes(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:6423b231114cbec0e8d1ccb0b69adb117d0f2d8fa58d72751627c049a0dc10e4"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "opl_domain_progress_transition_result": _opl_transition_result(),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    )
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "owner_receipt_required": True,
                "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
                "source_ref": str(
                    study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
                ),
                "repair_progress_precedence": {
                    "paper_delta_observed": True,
                    "accepted_owner_receipt": True,
                    "source_work_unit_id": "medical_prose_write_repair",
                    "source_fingerprint": fingerprint,
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "publication_supervision",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                    "next_work_unit": "publication_gate_replay",
                    "owner_answer_missing": False,
                    "owner_answer_still_required": False,
                    "provider_admission_pending": False,
                },
                "currentness_basis": {
                    "source_eval_id": source_eval_id,
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
                "typed_blocker": None,
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "study_id": study_id,
                "quest_id": study_id,
                "phase": "admission_pending",
                "current_authority": {
                    "owner": "gate_clearing_batch",
                    "authority": "med-autoscience",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "currentness_basis": {
                            "source_eval_id": source_eval_id,
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-event-current",
                        },
                    },
                },
                "conditions": [{"condition": "provider_admission_pending"}],
                "next_safe_action": {
                    "kind": "admit_provider_attempt",
                    "owner": "gate_clearing_batch",
                    "provider_admission_allowed": True,
                },
                "supervisor_decision": {
                    "surface_kind": "paper_autonomy_supervisor_decision",
                    "schema_version": 1,
                    "decision": "materialize_recovery_action",
                    "identity_match": True,
                    "source_paper_recovery_phase": "admission_pending",
                    "missing_evidence_refs": ["complete_paper_autonomy_obligation_identity"],
                    "forbidden_interpretations": [
                        "provider_admission_pending_count=0",
                        "action_queue=[]",
                    ],
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "action_queue": [],
                "blocked_reason": "provider_admission_current_control_state_required",
            },
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    assert result["paper_recovery_state"]["phase"] == "admission_pending"
    admission = result["owner_action_admission"]
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_running_proven"] is False
    assert result["provider_admission_pending_count"] == 1
    candidate = result["provider_admission_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == "publication_gate_replay"
    assert candidate["work_unit_fingerprint"] == fingerprint
