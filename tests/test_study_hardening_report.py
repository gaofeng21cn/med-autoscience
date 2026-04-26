from __future__ import annotations

import importlib


def test_study_hardening_report_answers_quality_gate_timing_and_replay_manifest() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_hardening_report")
    replay_case = {
        "surface": "study_soak_replay_case",
        "schema_version": 1,
        "study_id": "001-risk",
        "case_id": "study-soak-replay::001-risk::same_line_quality_gate_fast_lane",
        "case_family": "same_line_quality_gate_fast_lane",
        "required_truth_surfaces": [
            "study_runtime_status",
            "runtime_watch",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "study_charter",
        ],
        "must_assert": [
            "same_line_quality_repair_stays_controller_owned",
            "publication_gate_replay_follows_repair_batch",
            "quality_gate_relaxation_allowed_false",
        ],
        "edits_paper_body": False,
        "gate_relaxation_allowed": False,
    }
    profile_payload = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "profiling_window": {
            "since": "2026-04-25T00:00:00+00:00",
            "until": "2026-04-25T04:00:00+00:00",
            "event_count": 7,
        },
        "category_windows": {
            "controller_decision": {
                "event_count": 3,
                "first_at": "2026-04-25T00:30:00+00:00",
                "latest_at": "2026-04-25T01:30:00+00:00",
                "duration_seconds": 3600,
                "latest_event_path": "/tmp/decisions/2.json",
            },
            "publication_eval": {
                "event_count": 1,
                "first_at": "2026-04-25T03:00:00+00:00",
                "latest_at": "2026-04-25T03:00:00+00:00",
                "duration_seconds": 0,
                "latest_event_path": "/tmp/publication_eval/latest.json",
            },
        },
        "runtime_transition_summary": {"health_status_counts": {"live": 4}},
        "controller_decision_fingerprints": {
            "top_repeats": [
                {
                    "fingerprint": "abc",
                    "count": 3,
                    "latest_event_at": "2026-04-25T01:30:00+00:00",
                    "decision": {
                        "decision_type": "bounded_analysis",
                        "route_target": "analysis-campaign",
                    },
                }
            ]
        },
        "runtime_watch_wakeup_dedupe_summary": {"status": "not_confirmed"},
        "gate_blocker_summary": {
            "status": "blocked",
            "current_blockers": ["claim_evidence_consistency_failed"],
            "actionability_status": "actionable",
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
        },
        "package_currentness": {
            "status": "stale",
            "status_reason": "content_authority_newer_than_current_package",
            "authority_latest_mtime": "2026-04-25T03:30:00+00:00",
            "current_package_latest_mtime": "2026-04-25T03:00:00+00:00",
            "stale_seconds": 1800,
        },
        "step_timings": [
            {
                "from_step": "task_intake",
                "to_step": "run_start",
                "from_at": "2026-04-25T00:00:00+00:00",
                "to_at": "2026-04-25T00:20:00+00:00",
                "duration_seconds": 1200,
            },
            {
                "from_step": "controller_decision",
                "to_step": "gate_refresh",
                "from_at": "2026-04-25T01:00:00+00:00",
                "to_at": "2026-04-25T03:00:00+00:00",
                "duration_seconds": 7200,
            },
        ],
        "eta_confidence_band": {
            "classification": "claim_evidence",
            "label": "claim-evidence",
            "confidence": "medium",
            "min_seconds": 7200,
            "max_seconds": 21600,
        },
        "bottlenecks": [
            {"bottleneck_id": "repeated_controller_decision", "severity": "medium"},
            {"bottleneck_id": "publication_gate_blocked", "severity": "high"},
        ],
        "autonomy_slo": {
            "runtime_failure_classification": {
                "blocker_class": "none",
                "action_mode": "continue_slo_policy",
                "external_blocker": False,
                "requires_human_gate": False,
            },
            "slo_execution_plan": {"state": "ready_for_controller_execution"},
        },
        "study_soak_replay_case": replay_case,
    }

    report = module.build_study_hardening_report(profile_payload)

    assert report["surface"] == "study_hardening_report"
    assert report["answers"]["where_stuck"]["primary_gate"] == "quality_gate"
    assert report["answers"]["where_stuck"]["stuck_at"] == "publication_gate"
    assert report["answers"]["gate_assessment"] == {
        "runtime_gate": False,
        "provider_gate": False,
        "human_gate": False,
        "quality_gate": True,
        "delivery_gate": True,
        "primary_gate": "quality_gate",
    }
    assert report["answers"]["timing"]["window_seconds"] == 14400
    assert report["answers"]["timing"]["slowest_step"]["duration_seconds"] == 7200
    assert report["answers"]["timing"]["package_stale_seconds"] == 1800
    assert report["answers"]["controller_events"]["repeated_dispatch_count"] == 2
    assert report["answers"]["eta"]["classification"] == "claim_evidence"
    assert report["regression_manifest"]["cases"] == [replay_case]
    assert report["regression_manifest"]["required_truth_surfaces"] == [
        "controller_decisions/latest.json",
        "publication_eval/latest.json",
        "runtime_watch",
        "study_charter",
        "study_runtime_status",
    ]
    assert report["regression_manifest"]["gate_relaxation_allowed"] is False
    assert report["regression_manifest"]["edits_paper_body"] is False

    rendered = module.render_study_hardening_report_markdown(report)
    assert "卡点: publication_gate / quality_gate" in rendered
    assert "ETA: claim_evidence" in rendered
    assert "Regression manifest: 1 case" in rendered


def test_study_hardening_report_classifies_external_provider_and_human_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_hardening_report")
    report = module.build_study_hardening_report(
        {
            "study_id": "002-provider",
            "quest_id": "quest-002",
            "profiling_window": {"since": None, "until": None, "event_count": 1},
            "runtime_transition_summary": {"health_status_counts": {"recovering": 1}},
            "gate_blocker_summary": {"current_blockers": []},
            "package_currentness": {"status": "fresh", "stale_seconds": 0},
            "eta_confidence_band": {
                "classification": "runtime_recovering",
                "label": "runtime recovering",
                "confidence": "medium",
            },
            "bottlenecks": [{"bottleneck_id": "runtime_recovery_churn", "severity": "high"}],
            "autonomy_slo": {
                "runtime_failure_classification": {
                    "diagnosis_code": "provider_env_missing",
                    "blocker_class": "external_provider_account_blocker",
                    "action_mode": "external_fix_required",
                    "external_blocker": True,
                    "requires_human_gate": True,
                },
                "slo_execution_plan": {"state": "blocked_by_external_runtime"},
            },
            "study_soak_replay_case": {
                "case_id": "study-soak-replay::002-provider::runtime_recovery_taxonomy",
                "required_truth_surfaces": ["runtime_watch"],
                "must_assert": ["external_runtime_blocker_is_not_retried_as_mas_work"],
                "gate_relaxation_allowed": False,
                "edits_paper_body": False,
            },
        }
    )

    assert report["answers"]["where_stuck"]["primary_gate"] == "provider_gate"
    assert report["answers"]["where_stuck"]["stuck_at"] == "external_provider"
    assert report["answers"]["gate_assessment"]["runtime_gate"] is True
    assert report["answers"]["gate_assessment"]["provider_gate"] is True
    assert report["answers"]["gate_assessment"]["human_gate"] is True
    assert report["answers"]["gate_assessment"]["quality_gate"] is False
    assert report["regression_manifest"]["must_assert"] == [
        "external_runtime_blocker_is_not_retried_as_mas_work"
    ]
