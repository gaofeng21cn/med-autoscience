from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared
from tests.test_domain_health_diagnostic_cases.supervisor_and_progress_cases_cases.test_obligation_actuator_postcondition import (
    _assert_exactly_one_dhd_apply_outcome,
)
from tests.provider_admission_current_control_helpers import opl_transition_readback

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_domain_health_diagnostic_apply_accepts_stable_typed_blocker_as_closed_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    typed_blocker = {
        "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
        "owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "ai_reviewer_record_gate_consumption",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption",
        "typed_blocker_ref": "artifacts/supervision/consumer/default_executor_execution/sat_67e10.closeout.json",
    }
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "domain_blocked",
        "current_authority": {
            "obligation": {
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption",
            }
        },
        "next_safe_action": {
            "kind": "resolve_typed_blocker",
            "owner": "one-person-lab",
            "provider_admission_allowed": False,
        },
        "supervisor_decision": {"decision": "stop_with_stable_typed_blocker"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {study_id: recovery_state},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "study_root": str(study_root),
                    "paper_recovery_state": recovery_state,
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "ai_reviewer_record_gate_consumption",
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
                        ),
                        "state": {"typed_blocker": typed_blocker},
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {"surface": "opl_current_control_state_handoff"},
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "typed_blocker_ref")
    assert outcome["typed_blocker_ref"] == typed_blocker["typed_blocker_ref"]
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is True


def test_domain_health_diagnostic_apply_rejects_unconsumed_owner_receipt_as_closed_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    obligation_ref = (
        "paper-autonomy::003::publication_supervision::run_quality_repair_batch::"
        "medical_prose_write_repair::publication-blockers::0915410f804b3697"
    )
    supervisor_decision_id = (
        f"supervisor-decision::stop_with_owner_receipt::{obligation_ref}::owner-receipt"
    )
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_receipt_recorded",
        "evidence_refs": [receipt_ref],
        "current_authority": {
            "obligation": {
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            }
        },
        "next_safe_action": {
            "kind": "consume_owner_receipt",
            "owner": "write",
            "provider_admission_allowed": False,
            "owner_receipt_ref": receipt_ref,
        },
        "supervisor_decision": {
            "surface_kind": "paper_autonomy_supervisor_decision",
            "decision": "stop_with_owner_receipt",
            "decision_id": supervisor_decision_id,
            "paper_autonomy_obligation_ref": obligation_ref,
            "paper_autonomy_obligation": {
                "paper_autonomy_obligation_id": obligation_ref,
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "publication_supervision",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "route_identity_key": "route::003::quality-repair",
                "attempt_idempotency_key": "attempt::003::quality-repair",
            },
        },
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {"surface": "opl_current_control_state_handoff"},
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "typed_blocker_ref")
    _assert_supervisor_transaction_binding(
        outcome,
        expected_decision_id=supervisor_decision_id,
        expected_decision_kind="stop_with_owner_receipt",
        expected_obligation_ref=obligation_ref,
    )
    blocker = outcome["typed_control_blocker"]
    assert blocker["blocker_type"] == "non_advancing_apply"
    assert blocker["non_advancing_apply"] is True
    assert blocker["paper_progress_policy_result"]["recommended_opl_transition_kind"] == (
        "NonAdvancingApply"
    )
    assert blocker["authority_boundary"]["provider_admission_requires_opl_runtime_result"] is True
    assert "provider_admission_pending_requires_mas_transition_request" not in blocker[
        "authority_boundary"
    ]
    assert outcome["typed_control_blocker"]["next_safe_action_kind"] == "consume_owner_receipt"
    postcondition = report["managed_study_actions"][0]["dhd_apply_postcondition"]
    assert postcondition["ok"] is False
    assert postcondition["paper_autonomy_supervisor_decision_id"] == supervisor_decision_id
    assert postcondition["paper_autonomy_supervisor_decision_kind"] == "stop_with_owner_receipt"
    assert postcondition["paper_autonomy_obligation_ref"] == obligation_ref


def test_domain_health_diagnostic_apply_accepts_opl_provider_admission_result_as_closed_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    recovery_state = _ready_provider_recovery_state()

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "action_id": "provider-admission:003-write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "opl_domain_progress_transition_request": _mas_transition_request(
                        study_id=study_id,
                        action_type="run_quality_repair_batch",
                        work_unit_id="medical_prose_write_repair",
                        work_unit_fingerprint="publication-blockers::0915410f804b3697",
                    ),
                    "opl_domain_progress_transition_result": opl_transition_readback(
                        study_id,
                        action_fingerprint="publication-blockers::0915410f804b3697",
                        work_unit_id="medical_prose_write_repair",
                        request_idempotency_key=f"provider-admission::{study_id}::medical_prose_write_repair",
                        stage_run_id="sat_003_write",
                    ),
                }
            ],
            "running_provider_attempt": False,
        },
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "provider_admission_pending")
    assert outcome["details"]["opl_runtime_result"]["event_id"].startswith(
        "opl-domain-progress-event::"
    )
    assert outcome["authority_boundary"]["can_authorize_provider_admission"] is False
    assert outcome["authority_boundary"]["opl_transition_runtime_owner"] == "one-person-lab"
    assert outcome["authority_boundary"]["can_store_recovery_obligation"] is False
    assert outcome["authority_boundary"]["can_run_supervisor_decision_engine"] is False
    assert outcome["authority_boundary"]["can_create_opl_command_event_or_outbox"] is False
    assert outcome["authority_boundary"]["can_execute_mas_owner_callable"] is False
    assert outcome["authority_boundary"]["accepts_opl_stage_run_readback"] is True
    assert outcome["authority_boundary"]["accepts_mas_owner_answer_result"] is True
    assert outcome["authority_boundary"]["provider_admission_requires_opl_runtime_result"] is True
    foundation = outcome["opl_foundation_readback_boundary"]
    assert foundation["source_family"] == "opl_runtime_readback"
    assert foundation["success_source_family"] == "opl_runtime_readback"
    assert foundation["success_source_family_required"] is True
    assert foundation["mas_can_run_supervisor_decision_engine"] is False
    assert foundation["mas_policy_request_projection_can_satisfy_success"] is False
    consume_only = outcome["consume_only_readback_boundary"]
    assert consume_only["opl_runtime_owner"] == "one-person-lab"
    assert consume_only["opl_supervisor_decision_engine_owner"] == "one-person-lab"
    assert consume_only["mas_role"] == "policy_and_authority_readback_consumer"
    assert consume_only["mas_can_run_supervisor_decision_engine"] is False
    assert consume_only["mas_can_store_recovery_obligation"] is False
    assert consume_only["mas_can_generate_human_gate_resume_token"] is False
    assert consume_only["request_projection_is_success_outcome"] is False
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is True
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"][
        "consume_only_readback_boundary"
    ] == consume_only
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"][
        "opl_foundation_readback_boundary"
    ] == foundation
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["authority_boundary"][
        "provider_admission_requires_opl_runtime_result"
    ] is True
    summary = report["managed_study_obligation_actuator_summary"]
    assert summary["consume_only_readback_boundary"] == consume_only


def test_domain_health_diagnostic_apply_projects_transition_request_when_provider_request_has_no_opl_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    recovery_state = _ready_provider_recovery_state()

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "action_id": "provider-admission:003-write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "opl_domain_progress_transition_request": _mas_transition_request(
                        study_id=study_id,
                        action_type="run_quality_repair_batch",
                        work_unit_id="medical_prose_write_repair",
                        work_unit_fingerprint="publication-blockers::0915410f804b3697",
                    ),
                }
            ],
            "running_provider_attempt": False,
        },
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "transition_request_pending")
    assert outcome["transition_request_pending"] == (
        f"provider-admission::{study_id}::medical_prose_write_repair"
    )
    assert outcome["details"]["required_opl_runtime_result"] is True
    assert outcome["success_requires_opl_foundation_readback_boundary"] is True
    foundation = outcome["opl_foundation_readback_boundary"]
    assert foundation["source_family"] == "mas_policy_request_projection"
    assert foundation["success_source_family_required"] is False
    assert foundation["mas_policy_request_projection_can_satisfy_success"] is False
    assert "success_source_family" not in foundation
    blocker = outcome["typed_control_blocker"]
    assert blocker["blocker_type"] == "opl_transition_readback_required"
    assert blocker["surface_kind"] == "mas_domain_typed_blocker"
    assert blocker["owner_answer_shape"] == "typed_blocker_ref"
    assert blocker["mas_authority_result_shape"] == "typed_blocker_ref"
    assert blocker["private_actuator_surface_retired"] is True
    assert blocker["actuator_private_write_authority"] is False
    assert blocker["source"] == "domain_health_diagnostic.obligation_readback_projection"
    assert blocker["non_advancing_apply"] is True
    assert blocker["paper_progress_policy_result"]["recommended_opl_transition_kind"] == (
        "NonAdvancingApply"
    )
    assert outcome["authority_boundary"]["provider_admission_requires_opl_runtime_result"] is True
    assert outcome["authority_boundary"]["can_execute_mas_owner_callable"] is False
    assert "managed_study_mas_owner_callable_actions" not in report
    assert outcome["details"]["opl_transition_request"] == (
        outcome["typed_control_blocker"]["opl_domain_progress_transition_request"]
    )
    assert outcome["typed_control_blocker"]["paper_progress_policy_result"][
        "authority"
    ] == "med_autoscience.paper_progress_policy_adapter"
    assert outcome["typed_control_blocker"]["paper_progress_policy_result"][
        "recommended_opl_transition_kind"
    ] == "NonAdvancingApply"
    assert outcome["typed_control_blocker"]["non_advancing_apply_requirement"] == {
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "mas_can_apply_non_advancing_transition": False,
        "mas_can_persist_opl_event_or_outbox": False,
        "required_outcome": "typed_blocker_ref",
    }
    assert outcome["typed_control_blocker"]["consume_only_readback_boundary"] == (
        outcome["consume_only_readback_boundary"]
    )
    assert outcome["typed_control_blocker"]["consume_only_readback_boundary"][
        "mas_can_run_supervisor_decision_engine"
    ] is False
    assert outcome["authority_boundary"]["can_apply_non_advancing_transition"] is False
    assert outcome["authority_boundary"]["can_replay_obligation"] is False
    assert outcome["authority_boundary"]["can_write_fail_closed_typed_control_blocker"] is False
    assert outcome["authority_boundary"]["fail_closed_typed_blocker_surface"] == (
        "mas_domain_typed_blocker"
    )
    assert outcome["authority_boundary"]["actuator_can_write_private_blocker_surface"] is False
    postcondition = report["managed_study_actions"][0]["dhd_apply_postcondition"]
    assert postcondition["ok"] is False
    assert postcondition["outcome_kind"] == "transition_request_pending"


def test_domain_health_diagnostic_apply_rejects_runtime_polluted_mas_transition_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    recovery_state = _ready_provider_recovery_state()
    polluted_request = _mas_transition_request(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="publication-blockers::0915410f804b3697",
    )
    polluted_request["projection_metadata"] = {"authority": False}

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "action_id": "provider-admission:003-write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "opl_domain_progress_transition_request": polluted_request,
                    "opl_domain_progress_transition_result": {
                        "surface_kind": "opl_domain_progress_transition_result",
                        "runtime_owner": "one-person-lab",
                        "runtime_kind": "DomainProgressTransitionRuntime",
                        "transition_kind": "StartProviderAttempt",
                        "outcome_kind": "provider_admission_pending",
                        "event_id": "opl-domain-progress-event:003-write",
                    },
                }
            ],
            "running_provider_attempt": False,
        },
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "typed_blocker_ref")
    assert outcome["typed_control_blocker"]["blocker_type"] == "non_advancing_apply"


def test_domain_health_diagnostic_apply_does_not_accept_provider_admission_without_transition_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    recovery_state = _ready_provider_recovery_state()

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "action_id": "provider-admission:003-write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "legacy_opl_current_control_command": _legacy_opl_current_control_command(
                        study_id=study_id,
                        action_type="run_quality_repair_batch",
                        work_unit_id="medical_prose_write_repair",
                        work_unit_fingerprint="publication-blockers::0915410f804b3697",
                    ),
                }
            ],
            "running_provider_attempt": False,
        },
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "typed_blocker_ref")
    assert outcome["typed_control_blocker"]["blocker_type"] == (
        "non_advancing_apply"
    )
    assert outcome["typed_control_blocker"]["surface_kind"] == "mas_domain_typed_blocker"
    assert outcome["typed_control_blocker"]["owner_answer_shape"] == "typed_blocker_ref"
    assert outcome["typed_control_blocker"]["mas_authority_result_shape"] == (
        "typed_blocker_ref"
    )
    assert outcome["typed_control_blocker"]["private_actuator_surface_retired"] is True
    assert outcome["typed_control_blocker"]["actuator_private_write_authority"] is False
    assert outcome["typed_control_blocker"]["authority_boundary"][
        "provider_admission_requires_opl_runtime_result"
    ] is True
    assert outcome["typed_control_blocker"]["authority_boundary"][
        "can_write_fail_closed_typed_control_blocker"
    ] is False
    assert (
        "provider_admission_pending_requires_mas_transition_request"
        not in outcome["typed_control_blocker"]["authority_boundary"]
    )
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is False


def test_domain_health_diagnostic_apply_accepts_running_provider_attempt_as_closed_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    recovery_state = _ready_provider_recovery_state()

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "study_id": study_id,
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat_003_write",
            "active_run_id": "opl-stage-attempt://sat_003_write",
            "runtime_owner": "one-person-lab",
            "provider_attempt_owner": "one-person-lab",
            "runtime_health": {
                "runtime_liveness_status": "live",
                "health_status": "running",
                "strict_live": True,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "authority_boundary": {
                "mas_can_authorize_provider_admission": False,
                "mas_can_create_opl_stage_run": False,
            },
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        },
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "running_provider_attempt")
    assert outcome["running_provider_attempt"] == "sat_003_write"
    assert outcome["details"]["opl_running_provider_attempt"]["provider_attempt_owner"] == (
        "one-person-lab"
    )


def test_domain_health_diagnostic_apply_rejects_weak_mas_running_flag_without_opl_proof(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    recovery_state = _ready_provider_recovery_state()

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: _runtime_report_with_recovery_action(
            study_id=study_id,
            study_root=study_root,
            recovery_state=recovery_state,
        ),
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {
            "surface": "opl_current_control_state_handoff",
            "study_id": study_id,
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat_003_write",
            "active_run_id": "opl-stage-attempt://sat_003_write",
            "runtime_health": {"runtime_liveness_status": "live"},
        },
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "typed_blocker_ref")
    assert outcome["typed_control_blocker"]["blocker_type"] == "non_advancing_apply"
    assert "running_provider_attempt" not in outcome


def test_domain_health_diagnostic_apply_accepts_human_gate_and_route_back_refs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_ids = (
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    )
    for study_id in study_ids:
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
    human_gate_recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "human_gate",
        "evidence_refs": ["human_gate:owner-gate-decision:003"],
        "next_safe_action": {
            "kind": "record_human_or_owner_gate",
            "human_gate_ref": "human_gate:owner-gate-decision:003",
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }
    route_back_recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "evidence_refs": ["route_back:owner-gate-decision:002"],
        "next_safe_action": {
            "kind": "route_back_to_owner_or_repair_materialization",
            "route_back_evidence_ref": "route_back:owner-gate-decision:002",
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }

    monkeypatch.setattr(
        module,
        "_run_domain_health_diagnostic_for_runtime_impl",
        lambda **kwargs: {
            "surface": "domain_health_diagnostic",
            "action_class": "observe_only",
            "scanned_at": "2026-06-15T00:00:00+00:00",
            "current_execution_evidence": {"progress_currentness": {}},
            "paper_recovery_states": {
                study_ids[0]: route_back_recovery,
                study_ids[1]: human_gate_recovery,
            },
            "managed_study_actions": [
                {
                    "study_id": study_ids[0],
                    "quest_id": study_ids[0],
                    "study_root": str(profile.studies_root / study_ids[0]),
                    "paper_recovery_state": route_back_recovery,
                },
                {
                    "study_id": study_ids[1],
                    "quest_id": study_ids[1],
                    "study_root": str(profile.studies_root / study_ids[1]),
                    "paper_recovery_state": human_gate_recovery,
                },
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "_materialize_report_provider_admission_current_control_state",
        lambda **kwargs: {"surface": "opl_current_control_state_handoff"},
    )
    monkeypatch.setattr(module, "_sync_report_provider_admission_current_control_state", lambda report, **kwargs: None)
    monkeypatch.setattr(module, "_fresh_progress_currentness_for_report", lambda **kwargs: {})

    report = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        study_ids=study_ids,
        request_opl_stage_attempts=True,
    )

    outcomes = report["managed_study_obligation_actuator_outcomes"]
    _assert_exactly_one_dhd_apply_outcome(outcomes[0], "route_back_evidence_ref")
    _assert_exactly_one_dhd_apply_outcome(outcomes[1], "human_gate_ref")
    assert outcomes[0]["route_back_evidence_ref"] == "route_back:owner-gate-decision:002"
    assert outcomes[1]["human_gate_ref"] == "human_gate:owner-gate-decision:003"
    assert outcomes[0]["paper_autonomy_supervisor_outcome_allowed"] is True
    assert outcomes[1]["paper_autonomy_supervisor_outcome_allowed"] is True


def _ready_provider_recovery_state() -> dict[str, object]:
    return {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "current_authority": {
            "obligation": {
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            }
        },
        "next_safe_action": {
            "kind": "materialize_mas_transition_request_or_owner_callable",
            "owner": "write",
            "provider_admission_allowed": True,
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }


def _mas_transition_request(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "target_runtime_owner": "one-person-lab",
        "request_owner": "med-autoscience",
        "authority_role": "domain_policy_request_only",
        "mas_can_create_opl_outbox_record": False,
        "runtime_kind": "DomainProgressTransitionRuntime",
        "recommended_transition_kind": "StartProviderAttempt",
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": f"{study_id}::{work_unit_id}",
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        },
        "action_type": action_type,
        "next_owner": "write",
        "idempotency_key": f"provider-admission::{study_id}::{work_unit_id}",
        "source_generation": work_unit_fingerprint,
        "expected_version": work_unit_fingerprint,
        "required_postcondition": {
            "kind": "provider_admission_enqueued_or_blocked",
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
    }


def _legacy_opl_current_control_command(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> dict[str, object]:
    return {
        "surface_kind": "opl_generic_current_control_command_outbox_record",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "command_kind": "provider_admission_requested",
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": f"{study_id}::{work_unit_id}",
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        },
        "action_type": action_type,
        "work_unit_fingerprint": work_unit_fingerprint,
        "idempotency_key": f"legacy-provider-admission::{study_id}::{work_unit_id}",
        "source_generation": work_unit_fingerprint,
        "expected_version": work_unit_fingerprint,
        "postcondition": {
            "kind": "provider_admission_enqueued_or_blocked",
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
    }


def _runtime_report_with_recovery_action(
    *,
    study_id: str,
    study_root: Path,
    recovery_state: dict[str, object],
) -> dict[str, object]:
    return {
        "surface": "domain_health_diagnostic",
        "action_class": "observe_only",
        "scanned_at": "2026-06-15T00:00:00+00:00",
        "current_execution_evidence": {"progress_currentness": {}},
        "paper_recovery_states": {study_id: recovery_state},
        "managed_study_actions": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "study_root": str(study_root),
                "paper_recovery_state": recovery_state,
                "current_executable_owner_action": {
                    "status": "ready",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
            }
        ],
    }


def _assert_supervisor_transaction_binding(
    outcome: dict[str, object],
    *,
    expected_decision_id: str,
    expected_decision_kind: str,
    expected_obligation_ref: str,
) -> None:
    assert outcome["paper_autonomy_supervisor_decision_id"] == expected_decision_id
    assert outcome["paper_autonomy_supervisor_decision_kind"] == expected_decision_kind
    assert outcome["paper_autonomy_obligation_ref"] == expected_obligation_ref
    identity = outcome["paper_autonomy_obligation_identity"]
    assert identity["study_id"] == outcome["study_id"]
    assert identity["action_type"] == outcome["action_type"]
    assert identity["work_unit_id"] == outcome["work_unit_id"]
    assert identity["work_unit_fingerprint"] == outcome["work_unit_fingerprint"]
