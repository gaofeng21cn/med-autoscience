from __future__ import annotations

import importlib

from tests.mcp_opl_current_control_state_handoff_cases.shared import (
    append_jsonl as _append_jsonl,
    make_profile,
    opl_transition_readback,
    opl_transition_replay_audit_readback,
    write_json as _write_json,
)

def test_live_attempt_merge_replaces_stale_handoff_stage_attempt_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "001-risk",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-previous-closeout",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-previous-closeout",
                "status": "blocked",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "001-risk",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_run_id"] == "opl-stage-attempt://sat-current"
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["active_workflow_id"] == "wf-current"


def test_live_attempt_merge_replaces_stale_handoff_work_unit_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:stale-gate-replay",
            "action_fingerprint": "sha256:stale-gate-replay",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:stale-gate-replay",
                "action_fingerprint": "sha256:stale-gate-replay",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["action_type"] == "run_quality_repair_batch"
    assert merged["work_unit_id"] == "medical_prose_write_repair"
    assert merged["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert merged["action_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert merged["runtime_health"]["action_type"] == "run_quality_repair_batch"
    assert merged["runtime_health"]["work_unit_id"] == "medical_prose_write_repair"
    assert merged["runtime_health"]["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"


def test_live_attempt_merge_keeps_running_over_prior_same_work_unit_terminal_closeout() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": None,
            "active_stage_attempt_id": None,
            "active_workflow_id": None,
            "running_provider_attempt": False,
            "blocked_reason": "opl_execution_authorization_required",
            "next_owner": "one-person-lab",
            "action_queue": [
                {
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                }
            ],
            "latest_terminal_stage_log": {
                "stage_attempt_id": None,
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "status": "blocked",
                "typed_blocker_reason": "opl_execution_authorization_required",
                "source_path": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/owner_callable_adapter_receipt/latest.json",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "stage_progress_log": {
                "planned_work": {
                    "stage_attempt_id": "sat-current",
                    "stage_packet_ref": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/owner_callable_adapters/run_gate_clearing_batch.json",
                }
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_run_id"] == "opl-stage-attempt://sat-current"
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["active_workflow_id"] == "wf-current"
    assert merged["blocked_reason"] is None
    assert "typed_blocker" not in merged


def test_live_attempt_merge_supersedes_unsupported_dispatch_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "running_provider_attempt": False,
            "blocked_reason": "blocked:unsupported_dispatch_surface",
            "next_owner": "one-person-lab",
            "why_not_applied": ["blocked:unsupported_dispatch_surface"],
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["blocked_reason"] is None
    assert merged["why_not_applied"] == []
    assert merged["runtime_owner"] == "one-person-lab"
    assert merged["provider_attempt_owner"] == "one-person-lab"


def test_live_attempt_merge_ignores_prior_typed_closeout_for_different_stage_attempt() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_typed_owner_callable_closeout": {
                "execution_id": "sat-prior",
                "stage_attempt_id": "sat-prior",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "blocked_reason": "blocked:unsupported_dispatch_surface",
                "next_owner": "write",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["runtime_owner"] == "one-person-lab"
    assert "typed_blocker" not in merged
    assert merged.get("blocked_reason") is None


def test_latest_terminal_stage_log_marks_missing_observability(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-05-28T03:44:00+00:00",
            "studies": [{"study_id": "001-risk", "quest_status": "active"}],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "generated_at": "2026-05-28T03:45:25+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-05-28T03:45:25+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "paper_stage_log": {
                        "stage_name": "owner_authorized_publication_gate_replay",
                        "paper_work_done": ["Recorded gate replay receipt."],
                        "outcome": "executed",
                        "remaining_blockers": [],
                        "evidence_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["observability_status"] == "missing"
    assert terminal_log["missing_observability_fields"] == ["duration", "token_usage", "cost"]
    assert terminal_log["duration"] == {
        "status": "missing",
        "seconds": None,
        "missing_duration_reason": "no_terminal_stage_duration_observed",
    }
    assert terminal_log["token_usage"] == {
        "status": "missing",
        "total_tokens": None,
        "missing_token_usage_reason": "no_terminal_stage_token_usage_observed",
    }
    assert terminal_log["cost"] == {
        "status": "missing",
        "usd": None,
        "missing_cost_reason": "no_terminal_stage_cost_observed",
    }


def test_latest_terminal_stage_log_preserves_zero_observability_values(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-05-28T03:44:00+00:00",
            "studies": [{"study_id": "001-risk", "quest_status": "active"}],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "generated_at": "2026-05-28T03:45:25+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-05-28T03:45:25+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "duration_seconds": 0,
                    "token_usage": {"total_tokens": 0},
                    "cost_usd": 0,
                    "paper_stage_log": {
                        "stage_name": "owner_authorized_publication_gate_replay",
                        "paper_work_done": ["Recorded gate replay receipt."],
                        "outcome": "executed",
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["duration"] == {"seconds": 0}
    assert terminal_log["token_usage"] == {"total_tokens": 0}
    assert terminal_log["cost"] == {"usd": 0}
