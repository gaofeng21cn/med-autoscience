from __future__ import annotations

import importlib

from med_autoscience.controllers import control_identity


def test_canonical_dispatch_identity_suppresses_residual_action_when_current_work_unit_is_typed_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )

    identity = module.canonical_current_dispatch_identity(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay-current",
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay-current",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                },
            },
        },
        current_execution_envelope={"state_kind": "typed_blocker"},
    )

    assert identity == {
        "blocked": True,
        "source": "current_work_unit",
        "state_kind": "typed_blocker",
    }


def test_canonical_dispatch_identity_allows_owner_gate_route_back_stage_packet_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )

    identity = module.canonical_current_dispatch_identity(
        study_id="002-dm-china-us-mortality-attribution",
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.accepted_owner_gate_decision",
            "authority": "paper_recovery_state.accepted_owner_gate_decision",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "provider_admission_allowed": False,
            "owner_route_currentness_basis": {
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "truth_epoch": "publication-blockers::497d1260db522f01",
                "runtime_health_epoch": "publication-blockers::497d1260db522f01",
            },
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "owner": "one-person-lab",
                },
            },
            "currentness_basis": {
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "truth_epoch": "publication-blockers::497d1260db522f01",
                "runtime_health_epoch": "publication-blockers::497d1260db522f01",
            },
        },
        current_execution_envelope={"state_kind": "typed_blocker"},
    )

    assert identity["source"] == "paper_recovery_state.accepted_owner_gate_decision"
    assert identity["action_type"] == "run_quality_repair_batch"
    assert identity["work_unit_id"] == "analysis_claim_evidence_repair"
    assert identity["work_unit_fingerprint"] == "publication-blockers::497d1260db522f01"


def test_canonical_dispatch_identity_prefers_current_work_unit_over_residual_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )

    identity = module.canonical_current_dispatch_identity(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:stale-residual-action",
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:current-work-unit",
            "currentness_basis": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:current-work-unit",
                "truth_epoch": "truth::current",
                "runtime_health_epoch": "runtime::current",
            },
        },
        current_execution_envelope={"state_kind": "executable_owner_action"},
    )

    assert identity["source"] == "current_work_unit"
    assert identity["action_type"] == "return_to_ai_reviewer_workflow"
    assert identity["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert identity["work_unit_fingerprint"] == "sha256:current-work-unit"


def test_canonical_dispatch_identity_promotes_owner_action_when_executable_work_unit_lacks_fingerprint() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )

    identity = module.canonical_current_dispatch_identity(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "current_executable_owner_action",
            "next_owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:owner-action-current",
            "owner_route_currentness_basis": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:owner-action-current",
                "truth_epoch": "truth::current",
                "runtime_health_epoch": "runtime::current",
            },
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        current_execution_envelope={"state_kind": "executable_owner_action"},
    )

    assert identity["source"] == "current_work_unit"
    assert identity["action_type"] == "return_to_ai_reviewer_workflow"
    assert identity["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert identity["work_unit_fingerprint"] == "sha256:owner-action-current"
    assert identity["owner_route_currentness_basis"]["truth_epoch"] == "truth::current"


def test_canonical_dispatch_identity_derives_route_currentness_when_only_synthetic_ticket_is_present() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = "publication-eval::003::current-ai-reviewer-record"
    expected_fingerprint = control_identity.stable_route_currentness_fingerprint(
        study_id=study_id,
        source="owner_route_currentness_basis",
        work_unit_id=work_unit_id,
        action_type="run_gate_clearing_batch",
        source_eval_id=source_eval_id,
    )

    identity = module.canonical_current_dispatch_identity(
        study_id=study_id,
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "finalize",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": (
                f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::"
                "run_gate_clearing_batch"
            ),
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "finalize",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "currentness_basis": {
                "truth_epoch": "truth-event-current-ai-reviewer-record",
                "runtime_health_epoch": "runtime-health-event-current-gate",
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
            },
        },
        current_execution_envelope={"state_kind": "executable_owner_action"},
    )

    assert identity["source"] == "current_work_unit"
    assert identity["action_type"] == "run_gate_clearing_batch"
    assert identity["work_unit_id"] == work_unit_id
    assert identity["work_unit_fingerprint"] == expected_fingerprint
    assert identity["owner_route_currentness_basis"] == {
        "truth_epoch": "truth-event-current-ai-reviewer-record",
        "runtime_health_epoch": "runtime-health-event-current-gate",
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": expected_fingerprint,
    }


def test_current_owner_action_identity_overlays_stale_same_action_dispatch_work_unit() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )

    dispatch = {
        "action_type": "run_quality_repair_batch",
        "next_executable_owner": "write",
        "owner_route": {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_owner": "mas_controller",
            "next_owner": "write",
            "owner_reason": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "truth_epoch": "stage-native-next-action::old",
            "runtime_health_epoch": "stage-native-next-action::old",
            "work_unit_fingerprint": "stage-native-next-action::old-fp",
            "source_fingerprint": "stage-native-next-action::old-fp",
            "source_refs": {
                "work_unit_id": "run_quality_repair_batch",
                "work_unit_fingerprint": "stage-native-next-action::old-fp",
                "owner_route_currentness_basis": {
                    "work_unit_id": "run_quality_repair_batch",
                    "work_unit_fingerprint": "stage-native-next-action::old-fp",
                    "truth_epoch": "stage-native-next-action::old",
                    "runtime_health_epoch": "stage-native-next-action::old",
                },
            },
        },
        "prompt_contract": {
            "action_type": "run_quality_repair_batch",
            "owner_route": {
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "run_quality_repair_batch",
                    "work_unit_fingerprint": "stage-native-next-action::old-fp",
                },
            },
        },
    }
    current_owner_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
        "owner_route_currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "source_eval_id": "publication-eval::current",
        },
    }
    canonical_identity = {
        "source": "current_work_unit",
        "action_type": "run_quality_repair_batch",
        "action_ids": ["run_quality_repair_batch", "medical_prose_write_repair"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "owner_route_currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "source_eval_id": "publication-eval::current",
        },
    }

    updated = module.dispatch_with_current_owner_action_identity(
        dispatch=dispatch,
        current_owner_action=current_owner_action,
        canonical_identity=canonical_identity,
    )

    owner_route = updated["owner_route"]
    assert owner_route["owner_reason"] == "medical_prose_write_repair"
    assert owner_route["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert owner_route["truth_epoch"] == "truth-event-current"
    assert owner_route["runtime_health_epoch"] == "runtime-health-current"
    assert owner_route["source_refs"]["owner_route_currentness_basis"] == {
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
        "source_eval_id": "publication-eval::current",
    }
