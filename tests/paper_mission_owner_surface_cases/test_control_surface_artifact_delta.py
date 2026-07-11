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
    module = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        quest_id="quest-dm002",
        with_opl_runtime_handoff=True,
    )
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
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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
    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    study = result["studies"][0]
    assert study["meaningful_artifact_delta"] is False
    assert study["artifact_delta"]["status"] == "not_observed"
    assert "repeat_suppression" not in study
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"


def test_scan_domain_routes_observes_only_fresh_artifact_delta_as_meaningful() -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface.artifact_freshness")

    stale_progress = {
        "progress_freshness": {
            "meaningful_artifact_delta_freshness": {
                "status": "stale",
                "latest_progress_at": "2026-05-12T10:40:22+00:00",
                "latest_progress_source": "opl_transition_receipt",
            }
        }
    }
    fresh_progress = {
        "progress_freshness": {
            "meaningful_artifact_delta_freshness": {
                "status": "fresh",
                "latest_progress_at": "2026-05-13T16:51:40+00:00",
                "latest_progress_source": "opl_transition_receipt",
            }
        }
    }

    assert module.artifact_delta(stale_progress)["status"] == "stale"
    assert module.meaningful_artifact_delta_observed(stale_progress) is False
    assert module.meaningful_artifact_delta_observed(fresh_progress) is True
