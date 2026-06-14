from __future__ import annotations

import importlib
import json
from pathlib import Path


def _provider_candidate(profile, study_id: str, *, action_fingerprint: str) -> dict[str, object]:
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    identity_key = f"provider-admission::{study_id}::{action_fingerprint}"
    return {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(dispatch_path),
        "stage_packet_ref": str(dispatch_path),
        "stage_packet_refs": [str(dispatch_path)],
        "route_identity_key": identity_key,
        "attempt_idempotency_key": identity_key,
        "idempotency_key": identity_key,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }


def test_provider_admission_current_control_records_retained_pending_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:00:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "mas_provider_admission_identity",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["study_id"] == study_id
    assert decision["action_type"] == "return_to_ai_reviewer_workflow"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == action_fingerprint


def test_provider_admission_current_control_suppresses_candidate_blocked_by_paper_recovery_state(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-14T12:40:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "paper_recovery_state": {
                    "surface_kind": "paper_recovery_state",
                    "phase": "owner_action_ready",
                    "current_authority": {"owner": "write"},
                    "conditions": [
                        {
                            "condition": "current_mas_owner_callable_ready",
                            "reason": "runtime_recovery_retry_budget_exhausted",
                        }
                    ],
                    "next_safe_action": {
                        "kind": "run_mas_owner_callable",
                        "owner": "write",
                        "provider_admission_allowed": False,
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "paper_recovery_state_blocks_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "paper_recovery_state_blocks_provider_admission"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "owner_action_ready"


def test_provider_admission_report_suppresses_candidate_blocked_by_report_paper_recovery_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
    }

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                        },
                    },
                },
            },
            "paper_recovery_states": {
                study_id: {
                    "surface_kind": "paper_recovery_state",
                    "phase": "owner_action_ready",
                    "current_authority": {
                        "owner": "write",
                        "obligation": {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "next_safe_action": {
                        "kind": "run_mas_owner_callable",
                        "owner": "write",
                        "provider_admission_allowed": False,
                    },
                },
            },
        },
        apply=False,
        generated_at="2026-06-14T12:55:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "paper_recovery_state_blocks_provider_admission": 1,
    }
    study = result["studies"][0]
    assert study["paper_recovery_state"]["phase"] == "owner_action_ready"


def test_provider_admission_report_retains_matching_current_action_candidate_over_stale_scan_blocker(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "quest_id": study_id,
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "next_owner": "ai_reviewer",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": candidate["work_unit_id"],
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "owner": "ai_reviewer",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": candidate["work_unit_id"],
                            "work_unit_fingerprint": action_fingerprint,
                            "currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-event-current",
                                "work_unit_id": candidate["work_unit_id"],
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                },
            },
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "decision": "blocked",
                    "reason": "medical_paper_readiness_missing",
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "MedAutoScience",
                        "action_type": "complete_medical_paper_readiness_surface",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_type": "medical_paper_readiness_missing",
                                "owner": "MedAutoScience",
                            },
                        },
                    },
                    "current_executable_owner_action": None,
                    "running_provider_attempt": False,
                }
            ],
        },
        apply=False,
        generated_at="2026-06-12T07:30:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    retained = result["provider_admission_candidates"][0]
    assert retained["study_id"] == study_id
    assert retained["action_type"] == "return_to_ai_reviewer_workflow"
    assert retained["work_unit_id"] == candidate["work_unit_id"]
    assert retained["work_unit_fingerprint"] == action_fingerprint
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }


def test_provider_admission_report_sync_updates_managed_action_candidate_surface(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    current_candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint="sha256:current-ai-reviewer",
    )
    stale_candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint="sha256:stale-gate-replay",
        ),
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [stale_candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [stale_candidate],
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "provider_admission_candidates": [stale_candidate],
                    "provider_admission_state": {
                        "status": "pending",
                        "candidate_count": 1,
                    },
                }
            ],
        },
        "managed_study_actions": [
            {
                "study_id": study_id,
                "provider_admission_candidates": [stale_candidate],
                "provider_admission_state": {
                    "status": "pending",
                    "candidate_count": 1,
                },
            }
        ],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [current_candidate],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == [current_candidate]
    assert report["current_execution_evidence"]["provider_admission_candidates"] == [current_candidate]
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == [current_candidate]
    assert action["provider_admission_state"]["candidate_count"] == 1
    assert action["provider_admission_state"]["running_provider_attempt"] is False
    assert action["provider_admission_state"]["status"] == "pending"
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == [current_candidate]
    assert evidence_action["provider_admission_state"]["candidate_count"] == 1


def test_provider_admission_report_sync_clears_stale_managed_action_pending_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stale_candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint="sha256:stale-ai-reviewer",
    )
    stale_action = {
        "study_id": study_id,
        "provider_admission_candidates": [stale_candidate],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [stale_candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [stale_candidate],
            "managed_study_actions": [stale_action],
        },
        "managed_study_actions": [stale_action],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action


def test_provider_admission_report_sync_clears_pending_when_managed_action_is_running(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint="publication-blockers::0915410f804b3697",
        ),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
    }
    running_action = {
        "study_id": study_id,
        "running_provider_attempt": True,
        "active_stage_attempt_id": "sat-running",
        "active_run_id": "opl-stage-attempt://sat-running",
        "active_workflow_id": "wf-running",
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "running_provider_attempt",
            "owner": "publication_gate",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        },
        "provider_admission_candidates": [candidate],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
            "running_provider_attempt": True,
        },
        "paper_recovery_state": {
            "phase": "attempt_running",
            "next_safe_action": {
                "kind": "watch_running_attempt",
                "owner": "publication_gate",
                "provider_admission_allowed": False,
            },
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [candidate],
            "managed_study_actions": [dict(running_action)],
        },
        "managed_study_actions": [dict(running_action)],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [candidate],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    assert report["current_execution_evidence"]["provider_admission_candidates"] == []
    synced_action = report["managed_study_actions"][0]
    assert synced_action["running_provider_attempt"] is True
    assert synced_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in synced_action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["running_provider_attempt"] is True
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action


def test_provider_admission_current_control_runtime_health_live_attempt_suppresses_pending(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-14T13:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "runtime_health_snapshot": {
                    "worker_liveness_state": {
                        "state": "live",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "opl-stage-attempt://sat-running",
                        "active_stage_attempt_id": "sat-running",
                        "active_workflow_id": "wf-running",
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "running_identity_observed": 1,
    }
    study = result["studies"][0]
    assert study["running_provider_attempt"] is True
    assert study["active_stage_attempt_id"] == "sat-running"
    assert study["current_work_unit"]["status"] == "running_provider_attempt"
    assert study["current_execution_envelope"]["state_kind"] == "running_provider_attempt"


def test_provider_admission_report_sync_clears_domain_blocked_recovery_pending_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint="publication-blockers::497d1260db522f01",
        ),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
        "action_fingerprint": "publication-blockers::497d1260db522f01",
    }
    action = {
        "study_id": study_id,
        "decision": "blocked",
        "reason": "stage_packet_not_current_selected_dispatch",
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "analysis-campaign",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "owner": "analysis-campaign",
                },
            },
        },
        "provider_admission_candidates": [candidate],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
            "running_provider_attempt": False,
        },
        "paper_recovery_state": {
            "phase": "domain_blocked",
            "conditions": [
                {
                    "condition": "current_work_unit_typed_blocker",
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                }
            ],
            "next_safe_action": {
                "kind": "resolve_typed_blocker",
                "owner": "analysis-campaign",
                "provider_admission_allowed": False,
            },
            "suppressed_surfaces": [
                "current_executable_owner_action",
                "provider_admission_candidates",
            ],
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [candidate],
            "managed_study_actions": [dict(action)],
        },
        "managed_study_actions": [dict(action)],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [candidate],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    assert report["current_execution_evidence"]["provider_admission_candidates"] == []
    synced_action = report["managed_study_actions"][0]
    assert synced_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in synced_action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action


def test_provider_admission_report_refreshes_scanned_typed_blocker_without_candidates(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    blocker_ref = "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    stale_candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint="sha256:stale-ai-reviewer",
    )
    latest_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "surface": "opl_current_control_state_handoff",
                "schema_version": 1,
                "studies": [
                    {
                        "study_id": study_id,
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "ai_reviewer",
                            "next_work_unit": stale_candidate["work_unit_id"],
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "next_owner": "ai_reviewer",
                            "action_type": stale_candidate["action_type"],
                            "work_unit_id": stale_candidate["work_unit_id"],
                            "work_unit_fingerprint": stale_candidate["work_unit_fingerprint"],
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                    }
                ],
                "action_queue": [stale_candidate],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [],
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "decision": "blocked",
                    "reason": "medical_paper_readiness_missing",
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "MedAutoScience",
                        "action_type": "complete_medical_paper_readiness_surface",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "work_unit_fingerprint": f"current-readiness-typed-blocker::{study_id}::fresh",
                        "state": {
                            "state_kind": "typed_blocker",
                            "source": "stage_owner_answer",
                            "typed_blocker": {
                                "blocker_type": "medical_paper_readiness_missing",
                                "owner": "MedAutoScience",
                                "source_ref": blocker_ref,
                            },
                        },
                    },
                    "current_executable_owner_action": None,
                    "running_provider_attempt": False,
                }
            ],
        },
        apply=False,
        generated_at="2026-06-12T07:30:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["candidate_count"] == 0
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert study["current_work_unit"]["status"] == "typed_blocker"
    assert study["current_work_unit"]["owner"] == "MedAutoScience"
    assert study["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert (
        result["current_execution_envelopes"][study_id]["typed_blocker"]["blocker_type"]
        == "medical_paper_readiness_missing"
    )


def test_provider_admission_current_control_terminal_closeout_precedes_stale_live_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:10:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "running",
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-terminal-wins",
                "active_run_id": "run-terminal-wins",
                "active_workflow_id": "wf-terminal-wins",
                "opl_provider_attempt": {
                    "execution_status": "running",
                    "current_attempt_state": "running",
                    "running_provider_attempt": True,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-terminal-wins",
                    "active_run_id": "run-terminal-wins",
                    "active_workflow_id": "wf-terminal-wins",
                    "dispatch_path": candidate["dispatch_path"],
                },
                "default_executor_execution_receipt_consumption": {
                    "execution_status": "executed",
                    "current_attempt_state": "completed",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-terminal-wins",
                    "active_run_id": "run-terminal-wins",
                    "dispatch_path": candidate["dispatch_path"],
                    "typed_blocker_reason": "owner_output_already_current",
                    "typed_blocker_ref": "artifacts/closeouts/sat-terminal-wins.json",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "terminal_closeout_precedes_live_projection": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "terminal_closeout_precedes_live_projection"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "executed"
    assert decision["active_stage_attempt_id"] == "sat-terminal-wins"


def test_provider_admission_current_control_records_running_identity_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-running",
                "active_run_id": "run-running",
                "active_workflow_id": "wf-running",
                "opl_provider_attempt": {
                    "execution_status": "running",
                    "current_attempt_state": "running",
                    "running_provider_attempt": True,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-running",
                    "active_run_id": "run-running",
                    "active_workflow_id": "wf-running",
                    "dispatch_path": candidate["dispatch_path"],
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "running_identity_observed": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "running_identity_observed"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["active_stage_attempt_id"] == "sat-running"


def test_provider_admission_current_control_records_accepted_closeout_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "default_executor_execution_receipt_consumption": {
                    "execution_status": "executed",
                    "current_attempt_state": "completed",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "dispatch_path": candidate["dispatch_path"],
                    "typed_blocker_reason": "owner_output_already_current",
                    "typed_blocker_ref": "artifacts/closeouts/sat-closeout.json",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "executed"


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
