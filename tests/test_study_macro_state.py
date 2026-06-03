from __future__ import annotations

import importlib
import json
from pathlib import Path


def _module():
    return importlib.import_module("med_autoscience.controllers.study_macro_state")


def _derive(*, study_id: str, status: dict, progress: dict | None = None) -> dict:
    return _module().derive_study_macro_state(
        study_id=study_id,
        status=status,
        progress=progress or {},
    )


def _submit_info_status(*, study_id: str, quest_status: str = "paused", parked_state: str = "package_ready_handoff") -> dict:
    return {
        "study_id": study_id,
        "quest_status": quest_status,
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": parked_state,
            "awaiting_explicit_wakeup": True,
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "parked",
            "blocking_reasons": ["quest_waiting_for_submission_metadata"],
        },
        "study_truth_snapshot": {
            "truth_epoch": f"truth::{study_id}",
            "source_signature": f"source::{study_id}",
            "package_state": {"authority_state": "current"},
        },
        "submission_metadata": {
            "missing_external_info": ["authors", "ethics", "funding"],
        },
    }


def test_delivered_submission_packages_share_submit_info_macro_state() -> None:
    cases = [
        (
            "001-dm-cvd-mortality-risk",
            _submit_info_status(
                study_id="001-dm-cvd-mortality-risk",
                parked_state="external_metadata_pending",
            ),
            {"paper_stage": "bundle_stage_blocked", "format_profile": "generic"},
        ),
        (
            "002-early-residual-risk",
            {
                **_submit_info_status(study_id="002-early-residual-risk", quest_status="completed"),
                "reason": "study_completed",
            },
            {"paper_stage": "bundle_stage_ready", "journal_target": "target_journal"},
        ),
        (
            "003-endocrine-burden-followup",
            _submit_info_status(study_id="003-endocrine-burden-followup"),
            {"paper_stage": "bundle_stage_ready", "format_profile": "journal"},
        ),
    ]

    derived = [_derive(study_id=study_id, status=status, progress=progress) for study_id, status, progress in cases]

    assert {(item["writer_state"], item["user_next"], item["reason"]) for item in derived} == {
        ("parked", "submit_info", "external_info")
    }
    assert all(item["details"]["missing_external_info"] == ["authors", "ethics", "funding"] for item in derived)
    assert derived[0]["details"]["format_profile"] == "generic"
    assert derived[1]["details"]["journal_target"] == "target_journal"
    assert derived[2]["details"]["format_profile"] == "journal"
    assert all(len(item["reason"]) <= 24 for item in derived)


def test_paused_quest_ignores_stale_truth_active_run_id() -> None:
    derived = _derive(
        study_id="002-dm-china-us-mortality-attribution",
        status={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "paused",
            "decision": "resume",
            "reason": "quest_paused",
            "active_run_id": None,
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-000004",
                "source_signature": "truth-snapshot::stale",
                "active_run_id": "run-stale",
                "execution_state": {
                    "state": "paused",
                    "quest_status": "paused",
                    "reason": "quest_paused",
                },
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "active_run_id": None,
                "worker_running": None,
            },
        },
    )

    assert derived["writer_state"] != "live"
    assert derived["details"].get("active_run_id") is None


def test_current_routeback_ignores_stale_truth_active_run_id_on_active_quest() -> None:
    derived = _derive(
        study_id="002-dm-china-us-mortality-attribution",
        status={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "active_run_id": None,
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "next_work_unit": {
                    "unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
                    "lane": "write",
                },
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "source_signature": "truth-snapshot::stale",
                "active_run_id": "mas-run-002-dm-china-us-mortality-attribution-20260519T074054793831Z",
                "execution_owner": {
                    "owner": "opl",
                    "active_run_id": "mas-run-002-dm-china-us-mortality-attribution-20260519T074054793831Z",
                },
            },
            "runtime_liveness_status": "parked",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
            "runtime_health_snapshot": {
                "attempt_state": "escalated",
                "canonical_runtime_action": "escalate_runtime",
                "worker_liveness_state": {"state": "parked"},
            },
        },
    )

    assert derived["writer_state"] == "queued"
    assert derived["user_next"] == "repair"
    assert derived["reason"] == "quality"
    assert derived["details"]["next_work_unit"] == (
        "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
    )
    assert derived["details"].get("active_run_id") is None


def test_running_quest_with_retry_exhausted_no_worker_requires_opl_runtime_handoff() -> None:
    derived = _derive(
        study_id="002-dm-china-us-mortality-attribution",
        status={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "active",
            "active_run_id": None,
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_status": "none",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "worker_running": False,
                "runtime_audit": {"active_run_id": None, "worker_running": False},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
        },
        progress={
            "owner_route": {
                "next_owner": "one-person-lab",
                "owner_reason": "abnormal_stopped_runtime_resume_required",
                "allowed_actions": ["request_opl_stage_attempt"],
            }
        },
    )

    assert derived["writer_state"] == "queued"
    assert derived["user_next"] == "runtime_handoff"
    assert derived["reason"] == "runtime"
    assert derived["details"].get("active_run_id") is None


def test_stop_loss_and_user_stop_share_reopenable_parked_macro_state() -> None:
    cases = [
        (
            "001-lineage-pfs",
            {
                "quality_state": {"state": "stop_loss_recommended"},
                "package_state": {"authority_state": "not_observed"},
                "canonical_next_action": "stop_runtime",
            },
            {"stop_origin": "mas_early"},
        ),
        (
            "004-invasive-architecture",
            {
                "quality_state": {"state": "stop_loss_recommended"},
                "package_state": {"authority_state": "current"},
                "canonical_next_action": "stop_runtime",
            },
            {"stop_origin": "user_after_package"},
        ),
        (
            "004-dpcc-longitudinal-care-inertia-intensification-gap",
            {
                "quality_state": {"state": "user_stopped"},
                "package_state": {"authority_state": "current"},
                "canonical_next_action": "stop_runtime",
            },
            {"stop_origin": "user_after_package"},
        ),
    ]

    derived = [
        _derive(
            study_id=study_id,
            status={
                "study_id": study_id,
                "quest_status": "paused",
                "active_run_id": None,
                "reason": "publishability_stop_loss_recommended",
                "study_truth_snapshot": truth,
            },
            progress=progress,
        )
        for study_id, truth, progress in cases
    ]

    assert {(item["writer_state"], item["user_next"]) for item in derived} == {("parked", "none")}
    assert {item["reason"] for item in derived} == {"stop_loss", "user_stop"}
    assert all(item["details"]["reopen_allowed"] is True for item in derived)
    assert all(item["details"]["reopen_mode"] == "new_plan_required" for item in derived)
    assert derived[0]["details"]["package_delivered"] is False
    assert derived[1]["details"]["package_delivered"] is True


def test_explicit_final_abandon_stop_loss_is_not_reopenable() -> None:
    state = _derive(
        study_id="001-lineage-pfs",
        status={
            "study_id": "001-lineage-pfs",
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "publishability_stop_loss_recommended",
            "study_truth_snapshot": {
                "quality_state": {"state": "stop_loss_recommended"},
                "package_state": {"authority_state": "not_observed"},
                "final_line_decision": {
                    "decision": "abandon",
                    "reopen_allowed": False,
                    "decided_by": "user",
                    "recorded_at": "2026-05-06T08:00:00+00:00",
                },
            },
        },
        progress={
            "stop_origin": "mas_early",
        },
    )

    assert state["writer_state"] == "parked"
    assert state["user_next"] == "none"
    assert state["reason"] == "stop_loss"
    assert state["details"]["reopen_allowed"] is False
    assert state["details"]["reopen_mode"] == "closed"
    assert state["details"]["final_line_decision"] == {
        "decision": "abandon",
        "reopen_allowed": False,
        "decided_by": "user",
        "recorded_at": "2026-05-06T08:00:00+00:00",
    }
    assert state["conditions"][0]["type"] == "TerminalAbandon"


def test_stop_state_can_mark_delivered_milestone_package_without_quality_ready_authority() -> None:
    state = _derive(
        study_id="004-dpcc-longitudinal-care-inertia-intensification-gap",
        status={
            "study_id": "004-dpcc-longitudinal-care-inertia-intensification-gap",
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "delivered_package": {
                "observed": True,
                "surface": "manuscript/current_package",
                "authority_role": "user_visible_milestone_package_not_quality_authority",
            },
            "study_truth_snapshot": {
                "quality_state": {"state": "user_stopped"},
                "package_state": {"authority_state": "not_observed"},
            },
        },
        progress={"paper_stage": "manual_hold"},
    )

    assert state["writer_state"] == "parked"
    assert state["user_next"] == "none"
    assert state["reason"] == "user_stop"
    assert state["details"]["package_delivered"] is True
    assert state["details"]["reopen_mode"] == "new_plan_required"


def test_completed_submission_package_without_metadata_details_still_maps_to_submit_info() -> None:
    state = _derive(
        study_id="002-early-residual-risk",
        status={
            "study_id": "002-early-residual-risk",
            "quest_status": "completed",
            "decision": "completed",
            "reason": "quest_already_completed",
            "study_completion_contract": {"ready": True, "completion_status": "completed"},
            "study_truth_snapshot": {
                "truth_epoch": "truth-002",
                "package_state": {"authority_state": "not_observed"},
            },
        },
        progress={"current_stage": "study_completed", "paper_stage": "write"},
    )

    assert state["writer_state"] == "parked"
    assert state["user_next"] == "submit_info"
    assert state["reason"] == "external_info"
    assert state["details"]["package_delivered"] is True


def test_manual_hold_for_new_plan_maps_to_user_stop_reopenable_state() -> None:
    state = _derive(
        study_id="004-dpcc-longitudinal-care-inertia-intensification-gap",
        status={
            "study_id": "004-dpcc-longitudinal-care-inertia-intensification-gap",
            "quest_status": "paused",
            "decision": "blocked",
            "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "auto_runtime_parked": {"parked": True, "parked_state": "manual_hold"},
            "publication_supervisor_state": {
                "supervisor_phase": "manual_hold",
                "current_required_action": "hold_until_explicit_wakeup",
            },
        },
        progress={"paper_stage": "manual_hold"},
    )

    assert state["writer_state"] == "parked"
    assert state["user_next"] == "none"
    assert state["reason"] == "user_stop"
    assert state["details"]["reopen_allowed"] is True
    assert state["details"]["reopen_mode"] == "new_plan_required"


def test_running_and_repairable_studies_are_not_collapsed_into_parked_states() -> None:
    live = _derive(
        study_id="002-dm-china-us-mortality-attribution",
        status={
            "quest_status": "running",
            "active_run_id": "run-dm002",
            "runtime_health_snapshot": {"canonical_runtime_action": "continue_supervising_runtime"},
        },
    )
    queued = _derive(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        status={
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "runtime_controller_redrive_required",
            "runtime_health_snapshot": {"canonical_runtime_action": "recover_runtime"},
        },
        progress={
            "owner_route": {
                "next_owner": "one-person-lab",
                "allowed_actions": ["request_opl_stage_attempt"],
                "owner_reason": "runtime_controller_redrive_required",
            }
        },
    )

    assert live["writer_state"] == "live"
    assert live["user_next"] == "watch"
    assert live["reason"] == "runtime"
    assert queued["writer_state"] == "queued"
    assert queued["user_next"] == "runtime_handoff"
    assert queued["reason"] == "runtime"


def test_stale_active_run_does_not_make_macro_state_live_when_provider_attempt_is_not_running() -> None:
    state = _derive(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        status={
            "quest_status": "active",
            "active_run_id": "opl-stage-attempt://sat_stale",
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "publication_gate",
                },
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
            },
            "opl_current_control_state_handoff": {
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "running_provider_attempt": False,
            },
        },
        progress={
            "active_run_id": "opl-stage-attempt://sat_stale",
            "progress_first_monitoring_summary": {
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "next_owner": "gate_clearing_batch",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
        },
    )

    assert state["writer_state"] == "queued"
    assert state["user_next"] == "repair"
    assert state["reason"] == "quality"
    assert state["details"]["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert state["details"].get("active_run_id") is None


def test_controller_stop_truth_conflict_takes_priority_over_stale_active_run() -> None:
    state = _derive(
        study_id="001-dm-cvd-mortality-risk",
        status={
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_status": "running",
            "active_run_id": "run-stale",
            "study_truth_snapshot": {
                "execution_owner": {"owner": "controller_stop"},
                "active_run_id": "run-stale",
                "truth_epoch": "truth-stopped",
            },
        },
    )

    assert state["writer_state"] == "conflict"
    assert state["user_next"] == "inspect"
    assert state["reason"] == "truth_conflict"


def test_materialize_study_macro_state_writes_file_authority_without_runtime_index(tmp_path: Path) -> None:
    module = _module()
    study_root = tmp_path / "studies" / "001-risk"
    db_path = tmp_path / "artifacts" / "runtime" / "domain_authority_refs.sqlite"
    state = _derive(
        study_id="001-risk",
        status={
            "quest_status": "paused",
            "reason": "quest_waiting_for_submission_metadata",
            "auto_runtime_parked": {"parked_state": "external_metadata_pending"},
            "submission_metadata": {"missing_external_info": ["authors"]},
        },
    )

    result = module.materialize_study_macro_state_snapshot(study_root=study_root, snapshot=state, db_path=db_path)

    snapshot_path = study_root / "artifacts" / "runtime" / "study_macro_state" / "latest.json"
    assert result["snapshot_path"] == str(snapshot_path.resolve())
    assert result["index"] is None
    assert result["index_status"] == "file_authority_only"
    assert result["ignored_db_path"] == str(db_path.resolve())
    persisted = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert persisted == {
        **state,
        "snapshot_id": state["source_fingerprint"],
    }
    assert not db_path.exists()


def test_macro_state_uses_short_primary_enums_and_conditions_for_detail() -> None:
    state = _derive(
        study_id="001-dm-cvd-mortality-risk",
        status=_submit_info_status(study_id="001-dm-cvd-mortality-risk"),
    )

    assert state["surface"] == "study_macro_state"
    assert state["writer_state"] in {"live", "queued", "parked", "conflict"}
    assert state["user_next"] in {"watch", "submit_info", "repair", "revise", "runtime_handoff", "none", "inspect"}
    assert len(state["writer_state"]) <= 12
    assert len(state["user_next"]) <= 16
    assert len(state["reason"]) <= 24
    assert state["conditions"][0]["type"] == "ExternalInfoPending"


def test_long_runtime_status_reason_stays_diagnostic_not_macro_reason() -> None:
    state = _derive(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        status={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_status": "active",
            "active_run_id": None,
            "reason": "domain_transition_ai_reviewer_re_eval",
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "review",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
            "runtime_liveness_status": "parked",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"active_run_id": None, "worker_running": False},
            },
            "runtime_health_snapshot": {
                "attempt_state": "escalated",
                "canonical_runtime_action": "escalate_runtime",
                "blocking_reasons": ["domain_transition_ai_reviewer_re_eval"],
            },
        },
    )

    assert state["writer_state"] == "queued"
    assert state["user_next"] == "repair"
    assert state["reason"] == "quality"
    assert state["reason"] != "domain_transition_ai_reviewer_re_eval"
    assert state["details"]["reason_separation"] == {
        "control_reason_policy": "stable_macro_reason_enum",
        "diagnostic_reason_policy": "runtime_status_reason_detail_only",
        "status_reason": "domain_transition_ai_reviewer_re_eval",
        "runtime_blocking_reasons": ["domain_transition_ai_reviewer_re_eval"],
        "domain_transition_decision_type": "ai_reviewer_re_eval",
    }
