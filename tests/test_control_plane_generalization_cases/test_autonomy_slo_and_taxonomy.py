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
            "runtime_worker_activity": {
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
def test_runtime_failure_taxonomy_generalizes_codex_upstream_account_balance_text() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_failure_taxonomy")

    classification = module.classify_mds_failure_diagnosis(
        {
            "diagnosis_code": "codex_upstream_http_403",
            "retriable": False,
            "problem": "403 account balance is negative",
        }
    )

    assert classification["blocker_class"] == "external_provider_account_blocker"
    assert classification["action_mode"] == "external_fix_required"
    assert classification["auto_recovery_allowed"] is False
    assert classification["external_blocker"] is True
def test_runtime_failure_taxonomy_generalizes_codex_upstream_transient_text_without_exact_code() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_failure_taxonomy")

    classification = module.classify_mds_failure_diagnosis(
        {
            "retriable": True,
            "problem": "Codex upstream API returned a transient provider error.",
        }
    )

    assert classification["diagnosis_code"] is None
    assert classification["blocker_class"] == "external_provider_transient"
    assert classification["action_mode"] == "provider_backoff_and_recheck"
    assert classification["auto_recovery_allowed"] is True
    assert classification["external_blocker"] is True
def test_runtime_failure_taxonomy_keeps_non_account_codex_upstream_failures_external_provider() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_failure_taxonomy")

    classification = module.classify_mds_failure_diagnosis(
        {
            "diagnosis_code": "codex_upstream_http_502",
            "retriable": False,
            "problem": "Codex upstream provider returned 502 after retry budget was exhausted.",
        }
    )

    assert classification["blocker_class"] == "external_provider_transient"
    assert classification["action_mode"] == "provider_backoff_and_recheck"
    assert classification["auto_recovery_allowed"] is False
    assert classification["external_blocker"] is True
def test_runtime_failure_taxonomy_generalizes_http_retry_budget_exhaustion() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_failure_taxonomy")

    rate_limited = module.classify_mds_failure_diagnosis(
        {
            "retriable": True,
            "retry_budget_exhausted": True,
            "retry_attempts": 5,
            "retry_after_seconds": 300,
            "problem": "OpenAI API HTTP 429 too many requests after retries exhausted.",
        }
    )
    server_error = module.classify_mds_failure_diagnosis(
        {
            "retriable": False,
            "problem": "Anthropic API HTTP 503 provider unavailable after retry budget was exhausted.",
        }
    )

    assert rate_limited["blocker_class"] == "external_provider_transient"
    assert rate_limited["action_mode"] == "provider_backoff_and_recheck"
    assert rate_limited["auto_recovery_allowed"] is False
    assert rate_limited["retry_budget_exhausted"] is True
    assert rate_limited["retry_attempts"] == 5
    assert rate_limited["retry_after_seconds"] == 300
    assert server_error["blocker_class"] == "external_provider_transient"
    assert server_error["action_mode"] == "provider_backoff_and_recheck"
    assert server_error["auto_recovery_allowed"] is False
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
