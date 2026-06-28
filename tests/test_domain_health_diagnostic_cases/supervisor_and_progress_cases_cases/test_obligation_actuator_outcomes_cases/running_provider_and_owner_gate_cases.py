from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_domain_health_diagnostic_cases.shared import dump_json
from tests.test_domain_health_diagnostic_cases.supervisor_and_progress_cases_cases.test_obligation_actuator_outcomes import (
    _assert_exactly_one_dhd_apply_outcome,
    _legacy_opl_current_control_command,
    _ready_provider_recovery_state,
    _runtime_report_with_recovery_action,
)

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


def test_domain_health_diagnostic_apply_rejects_read_model_human_gate_and_route_back_refs(
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
    assert outcomes[0]["outcome_kind"] == "route_back_evidence_ref"
    assert outcomes[1]["outcome_kind"] == "human_gate_ref"
    assert outcomes[0]["route_back_evidence_ref"] == "route_back:owner-gate-decision:002"
    assert outcomes[1]["human_gate_ref"] == "human_gate:owner-gate-decision:003"
    assert outcomes[0]["paper_autonomy_supervisor_outcome_allowed"] is True
    assert outcomes[1]["paper_autonomy_supervisor_outcome_allowed"] is True
    assert outcomes[0]["postcondition_ok"] is False
    assert outcomes[1]["postcondition_ok"] is False
    assert "dhd_apply_success_proof" not in outcomes[0]
    assert "dhd_apply_success_proof" not in outcomes[1]
    assert "consumed_obligation_readback_identity" not in outcomes[0]
    assert "consumed_obligation_readback_identity" not in outcomes[1]
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is False
    assert report["managed_study_actions"][1]["dhd_apply_postcondition"]["ok"] is False


def test_domain_health_diagnostic_apply_accepts_owner_gate_authority_payload_refs(
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
    route_back_decision = {
        "decision": "route_back_to_mas_packet_materialization_bug",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "route-back-fingerprint",
        "route_back_evidence_ref": "route_back:owner-gate-decision:002",
        "owner_gate_decision_ref": "owner-gate-decision:002",
    }
    human_gate_decision = {
        "decision": "wait_for_owner_with_resume_token",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "human-gate-fingerprint",
        "human_gate_ref": "human_gate:owner-gate-decision:003",
        "owner_gate_decision_ref": "owner-gate-decision:003",
    }
    route_back_recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "next_safe_action": {
            "kind": "route_back_to_owner_or_repair_materialization",
            "accepted_owner_gate_decision": route_back_decision,
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
    }
    human_gate_recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "human_gate",
        "next_safe_action": {
            "kind": "resolve_owner_gate_decision",
            "accepted_owner_gate_decision": human_gate_decision,
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
    assert report["managed_study_actions"][0]["dhd_apply_postcondition"]["ok"] is True
    assert report["managed_study_actions"][1]["dhd_apply_postcondition"]["ok"] is True
