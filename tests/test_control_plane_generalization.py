from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    write_study,
    write_text,
)


def test_publication_work_unit_identity_ignores_downstream_delivery_churn() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_identity")

    with_delivery_churn = module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=[
            "claim_evidence_consistency_failed",
            "medical_publication_surface_blocked",
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "submission_surface_qc_failure_present",
        ],
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
        },
        action_type="run_gate_clearing_batch",
    )
    claim_only = module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=[
            "claim_evidence_consistency_failed",
            "medical_publication_surface_blocked",
        ],
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
        },
        action_type="run_gate_clearing_batch",
    )

    assert with_delivery_churn.effective_blockers == ("claim_evidence_consistency_failed",)
    assert with_delivery_churn.fingerprint == claim_only.fingerprint
    assert with_delivery_churn.dispatch_key == (
        f"{claim_only.fingerprint}::analysis_claim_evidence_repair::run_gate_clearing_batch"
    )


def test_work_unit_ledger_appends_replayable_events(tmp_path: Path) -> None:
    identity_module = importlib.import_module("med_autoscience.controllers.control_identity")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    identity = identity_module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=["claim_evidence_consistency_failed"],
        next_work_unit={"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        action_type="run_gate_clearing_batch",
    )
    study_root = tmp_path / "studies" / "003-dpcc"

    proposed = ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="proposed",
        payload={"source": "publication_gate"},
        recorded_at="2026-04-26T00:00:00+00:00",
    )
    dispatched = ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "runtime_watch"},
        recorded_at="2026-04-26T00:01:00+00:00",
    )

    events = ledger.read_events(study_root=study_root)

    assert [event["event_type"] for event in events] == ["proposed", "dispatched"]
    assert proposed["event_id"] != dispatched["event_id"]
    assert events[-1]["identity"]["dispatch_key"] == identity.dispatch_key
    assert ledger.latest_event(study_root=study_root, dispatch_key=identity.dispatch_key)["event_type"] == "dispatched"


def test_profile_sli_summary_separates_active_duplicate_dispatch_from_history() -> None:
    module = importlib.import_module("med_autoscience.controllers.profile_sli")

    summary = module.build_sli_summary(
        {
            "runtime_transition_summary": {
                "event_count": 10,
                "health_status_counts": {"live": 8, "recovering": 2},
                "transition_counts": {"live->recovering": 1, "recovering->live": 1},
            },
            "runtime_watch_wakeup_dedupe_summary": {
                "status": "dedupe_confirmed",
                "outcome": "skipped_matching_work_unit",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            },
            "package_currentness": {"status": "stale"},
        }
    )

    assert summary["runtime_live_ratio"] == 0.8
    assert summary["runtime_recovery_observations"] == 2
    assert summary["duplicate_dispatch_active"] is False
    assert summary["next_work_unit_id"] == "analysis_claim_evidence_repair"
    assert summary["package_stale_is_current_bottleneck"] is False


def test_mds_worker_activity_normalizes_runtime_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_worker_activity")

    live = module.normalize_activity(
        {
            "quest_status": "running",
            "runtime_liveness_audit": {"status": "live", "active_run_id": "run-123"},
            "autonomous_runtime_notice": {"browser_url": "http://127.0.0.1:20999"},
        }
    )
    recovering = module.normalize_activity(
        {
            "quest_status": "running",
            "runtime_liveness_status": None,
            "reason": "quest_marked_running_but_no_live_session",
        }
    )

    assert live["worker"] == "MDS"
    assert live["activity_state"] == "running"
    assert live["heartbeat_state"] == "live"
    assert live["active_run_id"] == "run-123"
    assert live["monitoring_url"] == "http://127.0.0.1:20999"
    assert recovering["activity_state"] == "recovering"
    assert recovering["heartbeat_state"] == "missing_live_session"


def test_study_runtime_status_exposes_mds_worker_activity(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstudy_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-live"}\n')
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.managed_runtime_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {"worker_running": True, "active_run_id": "run-live"},
            "bash_session_audit": {"status": "live"},
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk", include_progress_projection=False)

    assert result["mds_worker_activity"] == {
        "worker": "MDS",
        "activity_state": "running",
        "heartbeat_state": "live",
        "quest_status": "running",
        "active_run_id": "run-live",
        "monitoring_url": result["autonomous_runtime_notice"]["browser_url"],
        "reason": "quest_already_running",
    }


def test_autonomy_incident_candidates_are_structured_and_writable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_incidents")
    profile_payload = {
        "study_id": "003-dpcc",
        "bottlenecks": [
            {"bottleneck_id": "runtime_recovery_churn", "severity": "high"},
            {"bottleneck_id": "publication_gate_blocked", "severity": "high"},
        ],
        "sli_summary": {
            "runtime_live_ratio": 0.75,
            "duplicate_dispatch_active": False,
        },
        "gate_blocker_summary": {
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
        },
    }

    candidates = module.incident_candidates_from_profile(profile_payload)
    written = module.write_incident_record(
        study_root=tmp_path / "studies" / "003-dpcc",
        candidate=candidates[0],
        recorded_at="2026-04-26T00:00:00+00:00",
    )

    assert [candidate["incident_type"] for candidate in candidates] == [
        "runtime_recovery_churn",
        "publication_gate_blocked",
    ]
    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["incident_id"].startswith("autonomy-incident::003-dpcc::")
    assert payload["source"] == "profile-cycle"


def test_autonomy_slo_signals_prioritize_recovery_without_relaxing_quality_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_slo")

    payload = module.build_autonomy_slo_signals(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "sli_summary": {
                "runtime_live_ratio": 0.75,
                "runtime_recovery_observations": 2,
                "runtime_flapping_transitions": 1,
                "duplicate_dispatch_active": False,
                "next_work_unit_id": "analysis_claim_evidence_repair",
            },
            "mds_worker_activity": {
                "activity_state": "recovering",
                "heartbeat_state": "missing_live_session",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            },
            "bottlenecks": [
                {"bottleneck_id": "runtime_recovery_churn", "severity": "high"},
                {"bottleneck_id": "publication_gate_blocked", "severity": "high"},
            ],
            "autonomy_incident_candidates": [
                {
                    "incident_id": "incident-runtime",
                    "incident_type": "runtime_recovery_churn",
                    "severity": "high",
                    "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
                }
            ],
        }
    )

    assert payload["surface"] == "autonomy_slo"
    assert payload["long_run_health"]["state"] == "breach"
    assert payload["incident_loop"]["top_action_type"] == "probe_runtime_recovery"
    assert payload["recovery_actions"][0]["quality_gate_relaxation_allowed"] is False
    assert payload["quality_constraint"]["gate_relaxation_allowed"] is False
    assert "publication_eval/latest.json" in payload["quality_constraint"]["must_preserve_authority_surfaces"]


def test_autonomy_slo_signals_block_fast_lane_for_non_actionable_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_slo")

    payload = module.build_autonomy_slo_signals(
        {
            "study_id": "004-pituitary",
            "sli_summary": {
                "runtime_live_ratio": 1.0,
                "runtime_recovery_observations": 0,
                "runtime_flapping_transitions": 0,
                "duplicate_dispatch_active": False,
            },
            "gate_blocker_summary": {
                "current_blockers": ["publication_gate_blocked"],
                "actionability_status": "blocked_by_non_actionable_gate",
                "next_work_unit": None,
            },
            "bottlenecks": [{"bottleneck_id": "non_actionable_gate", "severity": "high"}],
        }
    )

    assert payload["progress_health"]["no_progress_candidate"] is True
    assert payload["quality_constraint"]["requires_concrete_publication_blocker"] is True
    assert payload["incident_loop"]["top_action_type"] == "request_gate_specificity"
    assert payload["quality_constraint"]["gate_relaxation_allowed"] is False


def test_autonomy_slo_consumes_mds_failure_taxonomy_before_auto_recovery() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_slo")

    payload = module.build_autonomy_slo_signals(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "sli_summary": {
                "runtime_live_ratio": 0.5,
                "runtime_recovery_observations": 2,
                "runtime_flapping_transitions": 1,
                "next_work_unit_id": "analysis_claim_evidence_repair",
            },
            "mds_failure_diagnosis": {
                "diagnosis_code": "codex_upstream_quota_error",
                "retriable": False,
                "problem": "The configured Codex upstream provider account has a quota or billing blocker.",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            },
            "autonomy_incident_candidates": [
                {
                    "incident_id": "incident-runtime",
                    "incident_type": "runtime_recovery_churn",
                    "severity": "high",
                    "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
                }
            ],
        }
    )

    classification = payload["runtime_failure_classification"]
    assert classification["diagnosis_code"] == "codex_upstream_quota_error"
    assert classification["blocker_class"] == "external_provider_account_blocker"
    assert classification["auto_recovery_allowed"] is False
    assert classification["action_mode"] == "external_fix_required"
    assert payload["incident_loop"]["top_action_type"] == "external_runtime_blocker"
    assert payload["slo_execution_plan"]["state"] == "blocked_by_external_runtime"
    assert payload["slo_execution_plan"]["gate_relaxation_allowed"] is False


def test_autonomy_slo_execution_plan_prioritizes_controller_actions_without_quality_relaxation() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_slo")

    payload = module.build_autonomy_slo_signals(
        {
            "study_id": "004-pituitary",
            "sli_summary": {
                "runtime_live_ratio": 0.98,
                "runtime_recovery_observations": 0,
                "runtime_flapping_transitions": 0,
                "next_work_unit_id": "repair_paper_live_paths",
            },
            "gate_blocker_summary": {
                "current_blockers": ["medical_publication_surface_blocked"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "repair_paper_live_paths", "lane": "paper-surface"},
            },
            "autonomy_incident_candidates": [
                {
                    "incident_id": "incident-publication",
                    "incident_type": "publication_gate_blocked",
                    "severity": "high",
                    "next_work_unit": {"unit_id": "repair_paper_live_paths", "lane": "paper-surface"},
                },
                {
                    "incident_id": "incident-package",
                    "incident_type": "stale_current_package",
                    "severity": "medium",
                    "next_work_unit": {"unit_id": "refresh_current_package", "lane": "delivery"},
                },
            ],
        }
    )

    plan = payload["slo_execution_plan"]
    assert plan["state"] == "ready_for_controller_execution"
    assert plan["gate_relaxation_allowed"] is False
    assert [step["action_type"] for step in plan["steps"]] == [
        "run_publication_work_unit",
        "refresh_current_package_after_settle",
    ]
    assert plan["quality_authority_surfaces"] == [
        "study_charter",
        "evidence_ledger",
        "review_ledger",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
    ]


def test_study_soak_replay_case_captures_recent_003_and_004_failure_patterns() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_soak_replay")

    diabetes_case = module.build_study_soak_replay_case(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "bottlenecks": [{"bottleneck_id": "runtime_recovery_churn"}],
            "runtime_failure_classification": {
                "blocker_class": "external_provider_account_blocker",
                "action_mode": "external_fix_required",
            },
        }
    )
    pituitary_case = module.build_study_soak_replay_case(
        {
            "study_id": "004-invasive-architecture",
            "bottlenecks": [{"bottleneck_id": "publication_gate_blocked"}],
            "gate_blocker_summary": {
                "current_blockers": ["submission_surface_qc_failure_present"],
                "next_work_unit": {"unit_id": "create_submission_minimal_package"},
            },
        }
    )

    assert diabetes_case["case_family"] == "runtime_recovery_taxonomy"
    assert diabetes_case["must_assert"] == [
        "external_runtime_blocker_is_not_retried_as_mas_work",
        "quality_gate_relaxation_allowed_false",
        "same_study_progress_truth_surfaces_present",
    ]
    assert pituitary_case["case_family"] == "same_line_quality_gate_fast_lane"
    assert "artifacts/controller/gate_clearing_batch/latest.json" in pituitary_case["required_truth_surfaces"]
