from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_routes_specificity_terminal_to_publication_gate_not_platform_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    _write_json(
        study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json",
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "runtime_recovery_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
        },
    )
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::dm002",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::dm002",
                "reason": "Publication gate must name the remaining metric target.",
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "summary": "Name concrete claim, figure, table, metric, and source-path targets.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "table",
                        "target_id": "submission_minimal_authority",
                        "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
                        "blocking_reason": "stale_submission_minimal_authority",
                    },
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("specificity terminal must not be treated as a platform relaunch repair")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_called)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "reason": "quest_marked_running_but_no_live_session",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {"status": "none", "worker_running": False, "active_run_id": None},
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
            "resume_postcondition": {
                "effective": False,
                "failure_mode": "no_live_run_started",
                "snapshot_status": "active",
                "active_run_id": None,
                "scheduled": False,
                "started": False,
                "queued": False,
                "blocked_reason": "needs_specificity",
                "terminal_reason": "needs_specificity",
                "terminal_source": "controller_work_unit_authorization",
            },
            "publication_eval": publication_eval,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "authority": "external_supervisor",
                "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    study = result["studies"][0]
    lifecycle = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert [item["action_type"] for item in study["action_queue"]] == ["publication_gate_specificity_required"]
    assert study["runtime_platform_repair_apply"] is None
    assert study["why_not_applied"] == "publication_gate_specificity_required"
    assert study["blocked_reason"] == "publication_gate_specificity_required"
    assert study["next_owner"] == "publication_gate"
    assert study["external_supervisor_required"] is False
    assert study["gate_specificity"]["missing_target_kinds"] == ["metric"]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert lifecycle["authority"] == "observability_only"
    assert lifecycle["blocked_reason"] == "publication_gate_specificity_required"
    assert lifecycle["next_owner"] == "publication_gate"
    assert lifecycle["external_supervisor_required"] is False
