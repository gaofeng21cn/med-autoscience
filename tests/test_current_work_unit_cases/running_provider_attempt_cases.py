from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module
from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_current_work_unit_accepts_strict_running_provider_proof() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="gate_clearing_batch",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live",
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "work_unit_id": "publication_gate_replay",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live"


def test_current_work_unit_running_attempt_supersedes_ai_reviewer_recheck_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
        },
        blocked_reason="repair_progress_ai_reviewer_recheck_required",
        next_owner="ai_reviewer",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-ai-review",
            "active_stage_attempt_id": "sat-live-ai-review",
            "active_workflow_id": "wf-live-ai-review",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_running_attempt_supersedes_provider_admission_current_control_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="one-person-lab",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
            "active_stage_attempt_id": "sat-live-gate-replay",
            "active_workflow_id": "wf-live-gate-replay",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "live",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["work_unit_fingerprint"] == "domain-transition::route_back_same_line::dpcc"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate-replay"


def test_current_work_unit_running_attempt_supersedes_prior_opl_authorization_terminal_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "outcome": (
                        "blocked:{'blocker_id': 'opl_execution_authorization_required', "
                        "'owner': 'one-person-lab'}"
                    ),
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "source_path": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "supervision/consumer/default_executor_execution/latest.json"
                    ),
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_owner": "gate_clearing_batch",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
                "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            }
        ],
        next_owner="one-person-lab",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
            "active_stage_attempt_id": "sat-live-gate-replay",
            "active_workflow_id": "wf-live-gate-replay",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate-replay"
    assert "typed_blocker" not in work_unit["state"]


def test_running_provider_attempt_uses_currentness_work_unit_before_attempt_identity() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        owner_route={
            "next_work_unit": {
                "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "lane": "finalize",
            }
        },
        next_owner="med-autoscience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-current-gate",
            "active_stage_attempt_id": "sat-live-current-gate",
            "active_workflow_id": "wf-live-current-gate",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["currentness_basis"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-current-gate"
    assert work_unit["work_unit_id"] != work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"]


def test_current_work_unit_running_attempt_supersedes_prior_dispatch_zero_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        blocked_reason="domain_owner_action_dispatch_execution_count_zero",
        next_owner="med-autoscience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-current-gate",
            "active_stage_attempt_id": "sat-live-current-gate",
            "active_workflow_id": "wf-live-current-gate",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": (
                "study-progress-current-owner-ticket::003::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
            ),
            "action_fingerprint": (
                "study-progress-current-owner-ticket::003::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
            ),
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-current-gate"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_running_attempt_supersedes_consumed_gate_replay_blocker() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_a9b2ffcc8f97a24837d729bf::"
        "2026-06-11T12:41:21+00:00"
    )
    fingerprint = "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "publication_gate_replay",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "publication_gate_replay",
                    "current_publication_work_unit_id": "publication_gate_replay",
                    "current_work_unit_fingerprint": fingerprint,
                    "current_actionability_status": "blocked",
                    "lacks_specific_blocker_object": False,
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["publication_gate_replay_blocked"],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.accepted_owner_gate_decision",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
        },
        next_owner="one-person-lab",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat_1f960e7aa4017019d0be2c5b",
            "active_stage_attempt_id": "sat_1f960e7aa4017019d0be2c5b",
            "active_workflow_id": "wf_bf3700ffa605ac9f8f911316",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == (
        "sat_1f960e7aa4017019d0be2c5b"
    )
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_ignores_terminal_log_without_matching_attempt_id() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate",
            "active_stage_attempt_id": "sat-live-gate",
            "active_workflow_id": "wf-live-gate",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": None,
                "status": "blocked",
                "source_path": "studies/003/artifacts/supervision/consumer/default_executor_execution/latest.json",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate"


def test_current_work_unit_does_not_treat_handoff_ready_as_provider_admission_without_opl_readback() -> None:
    module = _module()
    handoff = {
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                "work_unit_fingerprint": "provider-admission::002::repair",
                "action_fingerprint": "provider-admission::002::repair",
            }
        ],
        provider_admission=handoff,
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is False
    assert "pending_provider_admission_evidence" not in work_unit["state"]
    assert work_unit["status"] != "running_provider_attempt"


def test_current_work_unit_treats_opl_transition_readback_as_provider_admission_pending() -> None:
    module = _module()
    handoff = {
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
        "opl_domain_progress_transition_result": opl_transition_readback(
            "002-dm-cvd-mortality-risk",
            action_fingerprint="provider-admission::002::repair",
            work_unit_id="dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            request_idempotency_key="provider-admission::002-dm::run_quality_repair_batch",
        ),
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                "work_unit_fingerprint": "provider-admission::002::repair",
                "action_fingerprint": "provider-admission::002::repair",
            }
        ],
        provider_admission=handoff,
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is True
    evidence = work_unit["state"]["pending_provider_admission_evidence"]
    assert evidence["execution_status"] == "handoff_ready"
    assert evidence["opl_transition_readback_present"] is True
