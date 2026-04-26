from __future__ import annotations

import importlib


def test_paper_line_delivery_metrics_reports_dora_eta_and_trace_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_line_delivery_metrics")

    payload = module.build_paper_line_delivery_metrics(
        {
            "study_id": "004-invasive-architecture",
            "quest_id": "quest-004",
            "trace_identity": {
                "active_run_id": "run-004",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "actionability_status": "actionable",
            },
            "paper_line_events": [
                {"event_type": "task_intake", "at": "2026-04-25T00:00:00+00:00"},
                {"event_type": "first_draft", "at": "2026-04-25T01:00:00+00:00"},
                {"event_type": "quality_gate", "status": "blocked", "at": "2026-04-25T01:15:00+00:00"},
                {"event_type": "quality_gate", "status": "clear", "at": "2026-04-25T03:00:00+00:00"},
                {"event_type": "quality_gate", "status": "blocked", "at": "2026-04-25T03:30:00+00:00"},
                {"event_type": "quality_gate", "status": "clear", "at": "2026-04-25T04:00:00+00:00"},
                {"event_type": "package_refresh", "at": "2026-04-25T05:00:00+00:00"},
                {
                    "event_type": "runtime_supervision",
                    "status": "blocked",
                    "blocker_type": "runtime_recovering",
                    "at": "2026-04-25T02:00:00+00:00",
                },
                {
                    "event_type": "runtime_supervision",
                    "status": "recovered",
                    "at": "2026-04-25T02:30:00+00:00",
                },
                {
                    "event_type": "manual_gate",
                    "gate_type": "author_metadata",
                    "at": "2026-04-25T02:45:00+00:00",
                },
                {"event_type": "fast_lane", "status": "success", "at": "2026-04-25T03:10:00+00:00"},
                {"event_type": "fast_lane", "status": "failed", "at": "2026-04-25T03:20:00+00:00"},
            ],
        }
    )

    metrics = payload["delivery_dora_metrics"]
    assert metrics["lead_times"]["intake_to_first_draft_seconds"] == 3600
    assert metrics["lead_times"]["draft_to_quality_close_seconds"] == 7200
    assert metrics["lead_times"]["quality_close_to_package_seconds"] == 3600
    assert metrics["recovery"]["blocked_to_recovered_seconds"] == {
        "count": 1,
        "min_seconds": 1800,
        "max_seconds": 1800,
    }
    assert metrics["manual_gate_count"] == 1
    assert metrics["quality_reopen_rate"] == 0.5
    assert metrics["fast_lane_success_rate"] == 0.5
    assert payload["eta_interval"]["classification"] == "claim_evidence"
    assert payload["eta_interval"]["min_seconds"] == 7200
    assert payload["eta_interval"]["max_seconds"] > payload["eta_interval"]["min_seconds"]
    assert payload["eta_interval"]["basis"]["observed_duration_keys"] == ["draft_to_quality_close_seconds"]
    assert payload["trace_identity"]["trace_scope"] == (
        "study:004-invasive-architecture|quest:quest-004|run:run-004|"
        "work_unit:analysis_claim_evidence_repair"
    )
    assert payload["trace_identity"]["trace_id"].startswith("paper-line::")


def test_cycle_observability_embeds_trace_identity_and_delivery_metrics() -> None:
    observability = importlib.import_module("med_autoscience.controllers.autonomy_observability")

    payload = observability.build_cycle_observability(
        {
            "study_id": "004-invasive-architecture",
            "quest_id": "quest-004",
            "trace_identity": {"run_id": "run-004", "work_unit_id": "submission_minimal_refresh"},
            "profiling_window": {"event_count": 0},
            "category_windows": {},
            "runtime_transition_summary": {},
            "controller_decision_fingerprints": {},
            "gate_blocker_summary": {},
            "step_timings": [],
            "sli_summary": {},
            "autonomy_slo": {},
            "paper_line_delivery_metrics": {
                "surface": "paper_line_delivery_metrics",
                "delivery_dora_metrics": {"manual_gate_count": 1},
            },
        }
    )

    assert payload["trace_identity"]["trace_scope"] == (
        "study:004-invasive-architecture|quest:quest-004|run:run-004|"
        "work_unit:submission_minimal_refresh"
    )
    assert payload["paper_line_delivery_metrics"]["delivery_dora_metrics"]["manual_gate_count"] == 1
