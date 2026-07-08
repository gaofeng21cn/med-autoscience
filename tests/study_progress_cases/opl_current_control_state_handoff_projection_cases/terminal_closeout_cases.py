from __future__ import annotations

import os

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_anti_loop_typed_closeout_supersedes_newer_stale_latest_execution_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_work_unit = "analysis_claim_evidence_repair"
    stale_fingerprint = "publication-blockers::497d1260db522f01"
    next_work_unit = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    next_fingerprint = "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch"
    source_fingerprint = "mas_owner_callable_adapter_source_77f18f8da1eb6e57139208c1"
    idempotency_key = "idem_cd631f437e1e7f3be53f386e"
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-11T21:28:34+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "provider_admission_pending",
                        "runtime_liveness_status": "not_running",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_quality_repair_batch",
                            "status": "queued",
                            "owner": "analysis-campaign",
                            "work_unit_id": stale_work_unit,
                            "work_unit_fingerprint": stale_fingerprint,
                            "action_fingerprint": stale_fingerprint,
                            "authority": "mas_provider_admission_identity",
                        }
                    ],
                    "next_owner": "one-person-lab",
                    "blocked_reason": "provider_admission_current_control_state_required",
                }
            ],
        },
    )
    execution_root = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
    )
    latest_execution_path = execution_root / "latest.json"
    _write_json(
        latest_execution_path,
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "schema_version": 1,
            "generated_at": "2026-06-11T21:11:35+00:00",
            "study_id": study_id,
            "executions": [
                {
                    "generated_at": "2026-06-11T21:12:35+00:00",
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "paper_stage_log": {
                        "surface_kind": "mas_paper_facing_stage_log_summary",
                        "schema_version": 1,
                        "status": "available",
                        "stage_name": "publication_gate_replay",
                        "current_owner": "gate_clearing_batch",
                        "problem_summary": "Stale gate closeout remains blocked by OPL authorization.",
                        "stage_goal": "Produce gate replay output.",
                        "stage_work_done": ["Recorded a stale gate typed blocker."],
                        "paper_work_done": ["Recorded a stale gate typed blocker."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "outcome": "blocked",
                        "remaining_blockers": ["opl_execution_authorization_required"],
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "publication_gate_replay",
                            "owner_action": {
                                "next_owner": "gate_clearing_batch",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                            },
                        },
                    },
                }
            ],
        },
    )
    anti_loop_closeout_path = execution_root / "sat_82.closeout.json"
    _write_json(
        anti_loop_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": "sat_82",
            "stage_id": "stage_outcome/opl-handoff",
            "generated_at": "2026-06-11T20:11:08Z",
            "source_fingerprint": source_fingerprint,
            "idempotency_key": idempotency_key,
            "status": "closed_with_typed_blocker",
            "outcome": "repeat_suppressed_with_typed_blocker",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": stale_work_unit,
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "blocker_kind": "anti_loop_budget_exhausted",
                "reason": "anti_loop_budget_exhausted",
                "blocker_id": "opl_execution_authorization_required",
                "owner": "one-person-lab",
                "write_permitted": False,
                "required_next_owner": "one-person-lab",
                "anti_loop_budget": {
                    "status": "exhausted",
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": next_work_unit,
                    "work_unit_fingerprint": next_fingerprint,
                    "blocker_reason": "opl_execution_authorization_required",
                    "escalation_route": "publishability_repair_sprint",
                },
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": next_work_unit,
                "current_owner": "write",
                "problem_summary": "Repeated quality repair dispatch hit the anti-loop budget.",
                "stage_goal": "Produce a story-surface delta or stable typed blocker.",
                "stage_work_done": [
                    "Observed MAS domain dispatch result execution_status=repeat_suppressed."
                ],
                "paper_work_done": [
                    "No manuscript, package, publication gate, or readiness surface was modified."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/sat_82.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker_anti_loop_budget_exhausted",
                "remaining_blockers": [
                    "MAS domain dispatch suppressed another run_quality_repair_batch attempt."
                ],
                "duration": {"status": "missing", "seconds": None},
                "token_usage": {"status": "missing", "total_tokens": None},
                "cost": {"status": "missing", "usd": None},
                "usage_refs": [],
                "cost_refs": [],
                "evidence_refs": [
                    f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/sat_82.closeout.json"
                ],
                "progress_delta_classification": "typed_blocker",
                "deliverable_progress_delta": {"count": 0, "token_usage_total": None},
                "paper_progress_delta": {"count": 0, "token_usage_total": None},
                "platform_repair_delta": {"count": 1, "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate",
                    "work_unit_id": next_work_unit,
                    "owner_action": {
                        "next_owner": "one-person-lab",
                        "action_type": "publishability_repair_sprint",
                        "work_unit_id": next_work_unit,
                    },
                    "reason": "anti_loop_budget_exhausted_for_run_quality_repair_batch_same_action_fingerprint",
                },
            },
        },
    )
    os.utime(anti_loop_closeout_path, (100.0, 100.0))
    os.utime(latest_execution_path, (200.0, 200.0))
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
            "decision": "handoff_required",
            "reason": "opl_stage_attempt_admission_required",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-after-anti-loop-closeout",
                "runtime_liveness_status": "none",
                "attempt_state": "blocked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["latest_terminal_stage_log"]["source_path"] == str(anti_loop_closeout_path)
    assert handoff["latest_typed_owner_callable_closeout"]["source_path"] == str(
        anti_loop_closeout_path
    )
    assert handoff["typed_blocker"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert handoff["typed_blocker"]["owner"] == "one-person-lab"
    assert handoff["typed_blocker"]["work_unit_id"] == next_work_unit
    assert handoff["typed_blocker"]["work_unit_fingerprint"] == next_fingerprint
    assert handoff["typed_blocker"]["source_fingerprint"] == source_fingerprint
    assert handoff["typed_blocker"]["idempotency_key"] == idempotency_key
    assert handoff["typed_blocker"]["stage_attempt_id"] == "sat_82"
    assert handoff["consumed_action_queue"][0]["work_unit_id"] == stale_work_unit
    assert handoff["action_queue"] == []
    assert_default_next_action_legacy_surfaces_retired(result)


def test_terminal_closeout_without_owner_answer_fail_closes_stale_running_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = "domain-transition::route_back_same_line::dm003"
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-10T08:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "running",
                    "active_stage_attempt_id": "sat-dm003-terminal",
                    "active_run_id": "opl-stage-attempt://sat-dm003-terminal",
                    "active_workflow_id": "wf-dm003-terminal",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_gate_clearing_batch",
                            "owner": "publication_gate",
                            "next_owner": "publication_gate",
                            "next_work_unit": work_unit,
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "authority": "mas_provider_admission_identity",
                            "stage_attempt_id": "sat-dm003-terminal",
                        }
                    ],
                    "next_owner": "supervisor_only/live_provider_attempt",
                    "blocked_reason": None,
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-dm003-terminal.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": "sat-dm003-terminal",
            "stage_id": "stage_outcome/opl-handoff",
            "action_type": "run_gate_clearing_batch",
            "generated_at": "2026-06-10T08:05:00+00:00",
            "status": "completed",
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "stage_attempt_closeouts/sat-dm003-terminal.json"
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "publication_gate_replay",
                "current_owner": "publication_gate",
                "problem_summary": "Terminal provider attempt did not return a MAS owner answer.",
                "stage_goal": "Consume terminal attempt into owner answer or stable typed blocker.",
                "stage_work_done": ["Observed provider attempt terminal closeout."],
                "paper_work_done": [],
                "outcome": "completed_without_owner_answer",
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
            "quest_status": "running",
            "decision": "continue",
            "reason": "live_managed_runtime",
            "active_run_id": "opl-stage-attempt://sat-dm003-terminal",
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-before-terminal-closeout-consumption",
                "runtime_liveness_status": "live",
                "health_status": "running",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["running_provider_attempt"] is False
    assert handoff["active_run_id"] is None
    assert handoff["runtime_health"]["health_status"] == "terminal"
    assert handoff["blocked_reason"] == "typed_closeout_packet_required"
    assert handoff["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"
    assert handoff["typed_blocker"]["owner"] == "MedAutoScience"
    assert handoff["typed_blocker"]["work_unit_id"] == work_unit
    assert handoff["typed_blocker"]["work_unit_fingerprint"] == fingerprint
    assert handoff["terminal_closeout_consumed"] is True
    assert handoff["consumed_action_queue"][0]["consumption"]["state"] == (
        "consumed_by_terminal_stage_closeout"
    )
    assert handoff["action_queue"] == []
    assert_default_next_action_legacy_surfaces_retired(result)
