from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_provider_admission_current_control_wrappers_preserve_stage_authority_boundary() -> None:
    identity = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity"
    )
    boundaries = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "return_to_ai_reviewer_workflow"
    work_unit_id = "ai_reviewer_medical_prose_quality_review"
    fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    stage_packet_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/c4a596de.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": stage_packet_ref,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "next_executable_owner": "ai_reviewer",
        "provider_attempt_or_lease_required": True,
        "opl_domain_progress_transition_result": opl_transition_readback(
            study_id,
            action_fingerprint=fingerprint,
            work_unit_id=work_unit_id,
            stage_run_id="stage-run-ai-reviewer-quality-review",
        ),
        "provider_completion_is_domain_completion": True,
        "owner_route_current": True,
        "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
        "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "stage_transition_authority_boundary": {
            "stage_transition_authority": "legacy-local-runner",
            "intent_can_write_stage_current_pointer": True,
            "legacy_diagnostic": "kept",
        },
        "authority_boundary": {
            "can_write_current_owner_delta": True,
            "legacy_diagnostic": "kept",
        },
    }

    action = identity.provider_admission_current_control_action(candidate)
    study = identity.provider_admission_current_control_study(candidate)

    expected = boundaries.STAGE_TRANSITION_AUTHORITY_BOUNDARY
    for payload in (
        action,
        action["handoff_packet"],
        study["provider_admission_identity"],
        study["provider_admission_candidates"][0],
        study["action_queue"][0],
    ):
        stage_boundary = payload["stage_transition_authority_boundary"]
        assert stage_boundary == {"legacy_diagnostic": "kept", **expected}
        assert payload["provider_completion_is_domain_completion"] is False
        authority_boundary = payload["authority_boundary"]
        assert authority_boundary["legacy_diagnostic"] == "kept"
        assert authority_boundary["can_write_current_owner_delta"] is False
        assert authority_boundary["can_mark_provider_attempt_running"] is False


def test_provider_admission_candidate_inherits_current_action_currentness_basis() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"

    status_payload = {
        "study_id": study_id,
        "study_progress_generated_at": "2026-06-12T09:30:00+00:00",
        "current_executable_owner_action": {
            "status": "ready",
            "next_owner": "write",
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_eval_id": "publication-eval::003::current-ai-reviewer-record",
            "truth_epoch": "truth::003::current",
            "runtime_health_epoch": "runtime::003::current",
            "allowed_actions": [action_type],
        },
    }
    execution = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": (
            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
            "consumer/default_executor_dispatches/run_quality_repair_batch.json"
        ),
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "owner_route_current": True,
        "next_executable_owner": "write",
        "owner_route": {
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    }

    [candidate] = module.provider_admission_candidates_from_execution_payload(
        {"executions": [execution]},
        execution_ref="studies/003/default_executor_execution/latest.json",
        status_payload=status_payload,
    )

    assert candidate["currentness_basis"] == {
        "source_eval_id": "publication-eval::003::current-ai-reviewer-record",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "truth_epoch": "truth::003::current",
        "runtime_health_epoch": "runtime::003::current",
    }


def test_provider_admission_candidate_allows_current_action_identity_over_prior_typed_blocker(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    action_type = "run_quality_repair_batch"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "next_owner": "analysis-campaign",
        "action_type": action_type,
        "allowed_actions": [action_type],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
    dispatch_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_request",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": action_type,
                "dispatch_status": "ready",
                "dispatch_authority": "consumer_default_executor_dispatch",
                "next_executable_owner": "analysis-campaign",
                "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
                "action_fingerprint": fingerprint,
                "owner_route": {
                    "next_owner": "analysis-campaign",
                    "source_refs": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "owner_route_currentness_basis": {
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                },
                "refs": {"dispatch_path": str(dispatch_path)},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                    "owner": "one-person-lab",
                    "work_unit_id": "publication_gate_replay",
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
        },
        "current_executable_owner_action": current_action,
    }
    [candidate] = module.current_control_provider_admission_candidates(
        {
            "studies": [status_payload],
            "action_queue": [],
        },
        study_root=profile.studies_root / study_id,
        status_payload=status_payload,
    )

    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == action_type
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"


def test_opl_authorization_blocked_execution_requires_fingerprint_bound_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_gate_clearing_batch"
    work_unit_id = "publication_gate_replay"
    current_fingerprint = "sha256:current-gate-replay"
    stale_fingerprint = "sha256:stale-blocked-dispatch"

    candidate = module.provider_admission_candidate_from_execution(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "dispatch_path": (
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
                "consumer/default_executor_dispatches/run_gate_clearing_batch.json"
            ),
            "execution_status": "blocked",
            "blocked_reason": "opl_execution_authorization_required",
            "provider_attempt_or_lease_required": True,
            "owner_route_current": True,
            "next_executable_owner": "gate_clearing_batch",
            "owner_route": {
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": stale_fingerprint,
                },
            },
        },
        execution_ref="studies/003/default_executor_execution/latest.json",
        status_study_id=study_id,
        current_action_identity={
            "action_ids": [action_type, work_unit_id],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": current_fingerprint,
            "work_unit_fingerprints": [current_fingerprint],
            "source": "canonical_current_work_unit",
            "next_owner": "one-person-lab",
            "opl_execution_authorization_required": True,
        },
    )

    assert candidate is None


def test_provider_admission_candidate_does_not_synthesize_stage_packet_from_dispatch_ref() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_gate_clearing_batch"
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:current-gate-replay"

    candidate = module.provider_admission_candidate_from_execution(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": (
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
                "consumer/default_executor_dispatches/run_gate_clearing_batch.json"
            ),
            "dispatch_authority": "consumer_default_executor_dispatch",
            "execution_status": "handoff_ready",
            "provider_attempt_or_lease_required": True,
            "owner_route_current": True,
            "next_executable_owner": "gate_clearing_batch",
            "owner_route": {
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-current",
                    },
                },
            },
        },
        execution_ref="studies/003/default_executor_execution/latest.json",
        status_study_id=study_id,
        current_action_identity={
            "action_ids": [action_type, work_unit_id],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "work_unit_fingerprints": [fingerprint],
            "source": "canonical_current_work_unit",
            "next_owner": "gate_clearing_batch",
        },
    )

    assert candidate is not None
    assert candidate["dispatch_ref"].endswith("default_executor_dispatches/run_gate_clearing_batch.json")
    assert "stage_packet_ref" not in candidate
    assert "stage_packet_refs" not in candidate
