from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _specificity_targets(study_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
    ]


def test_scan_domain_routes_does_not_count_control_surface_progress_as_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    previous_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "work_unit_fingerprint": "publication-blockers::control-only",
        "current_owner": "managed_runtime",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_assessment_required",
        "active_run_id": "run-dm002",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "idempotency_key": "owner-route::control-only",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": previous_route, "meaningful_artifact_delta": False}],
            "action_queue": [],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "active_run_id": "run-dm002",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-dm002",
                "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-dm002"},
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-control-only",
                "canonical_runtime_action": "observe_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
            },
            "publication_eval": {
                "schema_version": 1,
                "eval_id": "publication-eval::control-only",
                "study_id": study_id,
                "quest_id": "quest-dm002",
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::control-only",
                        "action_type": "return_to_controller",
                        "work_unit_fingerprint": "publication-blockers::control-only",
                        "specificity_targets": _specificity_targets(study_root),
                    }
                ],
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-control-only",
                "source_signature": "truth-source-control-only",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
            "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "missing",
                    "latest_progress_at": None,
                    "latest_progress_source": "mds_artifact_delta",
                }
            },
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": "run-dm002", "health_status": "live"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    study = result["studies"][0]
    assert study["meaningful_artifact_delta"] is False
    assert study["artifact_delta"]["status"] == "not_observed"
    assert study["repeat_suppression"]["repeat_suppressed"] is False
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"


def test_repeat_suppression_ignores_last_meaningful_progress_without_artifact_delta() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")

    assert module.meaningful_artifact_delta_observed(
        {
            "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "missing",
                    "latest_progress_at": None,
                    "latest_progress_source": "mds_artifact_delta",
                }
            },
        }
    ) is False


def test_repeat_suppression_consumes_recorded_failed_path_refs_without_authority() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")

    guard = module.scan_repeat_suppression(
        previous_payload=None,
        study_id="002-dm-china-us-mortality-attribution",
        owner_route={
            "work_unit_fingerprint": "negative-result-stoploss::primary-analysis",
            "next_owner": "analysis_harmonization_owner",
            "owner_reason": "negative_result_cannot_support_original_claim",
            "allowed_actions": ["methodology_reframe_route_decision"],
            "failed_path_ledger": {
                "surface_kind": "mas_failed_path_refs_projection",
                "refs": [
                    "studies/002-dm-china-us-mortality-attribution/artifacts/research/negative_failed_path_ledger/latest.json",
                ],
                "consumed_refs": [
                    "studies/002-dm-china-us-mortality-attribution/artifacts/research/negative_failed_path_ledger/latest.json",
                ],
                "body_included": False,
                "route_authority": False,
            },
            "repeated_failed_path_suppressed": True,
        },
        current_meaningful_artifact_delta=False,
    )

    assert guard["repeat_suppressed"] is True
    assert guard["why_not_applied"] == "repeat_suppressed"
    assert guard["suppression_source"] == "owner_route_recorded_failed_path_refs"
    assert guard["failed_path_consumption"] == {
        "status": "recorded_failed_path_consumed",
        "refs": [
            "studies/002-dm-china-us-mortality-attribution/artifacts/research/negative_failed_path_ledger/latest.json",
        ],
        "route_authority": False,
    }


def test_owner_route_consumes_negative_result_refs_before_repeat_guard() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_route")
    negative_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/research/"
        "negative_failed_path_ledger/latest.json"
    )

    owner_route, actions = module.route_and_decorate_actions(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status={
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-negative",
                "source_signature": "truth-source-negative",
            },
            "negative_result_ledger": {
                "summary": "Primary analysis cannot support the original route.",
                "negative_result_refs": [negative_ref],
                "body": "private negative-result body must not be consumed",
            },
        },
        progress={},
        actions=[
            {
                "study_id": "002-dm-china-us-mortality-attribution",
                "action_type": "methodology_reframe_route_decision",
                "owner": "analysis_harmonization_owner",
                "consumes_failed_path_refs": [negative_ref],
                "work_unit_fingerprint": "negative-result-stoploss::primary-analysis",
            }
        ],
        blocked_reason="negative_result_cannot_support_original_claim",
        next_owner="analysis_harmonization_owner",
        active_run_id=None,
    )

    assert actions == []
    assert owner_route["repeated_failed_path_suppressed"] is True
    assert owner_route["failed_path_ledger"] == {
        "surface_kind": "mas_failed_path_refs_projection",
        "summary": "Primary analysis cannot support the original route.",
        "refs": [negative_ref],
        "consumed_refs": [negative_ref],
        "body_included": False,
        "route_authority": False,
    }
    assert "private negative-result body" not in str(owner_route)


def test_scan_domain_routes_observes_only_fresh_artifact_delta_as_meaningful() -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile_parts.artifact_freshness")

    stale_progress = {
        "progress_freshness": {
            "meaningful_artifact_delta_freshness": {
                "status": "stale",
                "latest_progress_at": "2026-05-12T10:40:22+00:00",
                "latest_progress_source": "runtime_turn_closeout",
            }
        }
    }
    fresh_progress = {
        "progress_freshness": {
            "meaningful_artifact_delta_freshness": {
                "status": "fresh",
                "latest_progress_at": "2026-05-13T16:51:40+00:00",
                "latest_progress_source": "runtime_turn_closeout",
            }
        }
    }

    assert module.artifact_delta(stale_progress)["status"] == "stale"
    assert module.meaningful_artifact_delta_observed(stale_progress) is False
    assert module.meaningful_artifact_delta_observed(fresh_progress) is True


def test_repeat_suppression_does_not_override_owner_handoff_projection() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")

    guard = module.scan_repeat_suppression(
        previous_payload={
            "studies": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "meaningful_artifact_delta": False,
                    "owner_route": {
                        "work_unit_fingerprint": "truth-snapshot::owner-handoff",
                    },
                }
            ]
        },
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        owner_route={
            "work_unit_fingerprint": "truth-snapshot::owner-handoff",
            "owner_reason": "controller_work_unit_owner_handoff_required",
            "failure_signature": "controller_work_unit_owner_handoff_required",
            "next_owner": "write/ai_reviewer",
            "allowed_actions": [],
        },
        current_meaningful_artifact_delta=False,
    )

    assert guard["repeat_suppressed"] is False
    assert guard["why_not_applied"] is None
    assert guard["work_unit_fingerprint"] == "truth-snapshot::owner-handoff"


def test_repeat_suppression_does_not_override_clean_migration_ai_reviewer_handoff() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")

    guard = module.scan_repeat_suppression(
        previous_payload={
            "studies": [
                {
                    "study_id": "004-dpcc-longitudinal-care-inertia-intensification-gap",
                    "meaningful_artifact_delta": False,
                    "owner_route": {
                        "work_unit_fingerprint": "truth-snapshot::clean-migration",
                    },
                }
            ]
        },
        study_id="004-dpcc-longitudinal-care-inertia-intensification-gap",
        owner_route={
            "work_unit_fingerprint": "truth-snapshot::clean-migration",
            "owner_reason": "paper_authority_clean_migration_required",
            "failure_signature": "paper_authority_clean_migration_required",
            "next_owner": "ai_reviewer",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
        },
        current_meaningful_artifact_delta=False,
    )

    assert guard["repeat_suppressed"] is False
    assert guard["why_not_applied"] is None
    assert guard["work_unit_fingerprint"] == "truth-snapshot::clean-migration"


def test_repeat_suppression_keeps_unconsumed_scan_action_visible() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")
    owner_route = {
        "work_unit_fingerprint": "publication-blockers::submission-refresh",
        "next_owner": "artifact_os",
        "owner_reason": "current_package_freshness_required",
        "allowed_actions": ["current_package_freshness_required"],
    }

    guard = module.scan_repeat_suppression(
        previous_payload={
            "studies": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "meaningful_artifact_delta": False,
                    "owner_route": owner_route,
                }
            ],
            "action_queue": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "current_package_freshness_required",
                    "owner_route": owner_route,
                    "consumption": {"state": "unconsumed"},
                }
            ],
        },
        study_id="002-dm-china-us-mortality-attribution",
        owner_route=owner_route,
        current_meaningful_artifact_delta=False,
    )

    assert guard["repeat_suppressed"] is False
    assert guard["why_not_applied"] is None
    assert guard["work_unit_fingerprint"] == "publication-blockers::submission-refresh"
