from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_supervisor_scan_routes_adopted_work_unit_evidence_to_publication_gate_recheck(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            }
        ],
    }

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("adopted work unit evidence must not relaunch the runtime worker")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_called)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "active",
                "decision": "noop",
                "reason": "controller_work_unit_evidence_adopted",
                "active_run_id": None,
                "runtime_liveness_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
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
                "controller_work_unit_next_route": {
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "owner": "publication_gate",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": False,
                },
                "controller_work_unit_evidence_adoption": {
                    "already_recorded": True,
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "route_target": "analysis-campaign",
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "result": {
                        "local_traceability_repair_complete": True,
                        "unresolved_local_defect_count": 0,
                    },
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-adopted-work-unit",
                    "source_signature": "truth-source-adopted-work-unit",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "analysis-campaign",
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "ai_repair_lifecycle": {
                    "state": "blocked",
                    "authority": "external_supervisor",
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "projection_only": True,
                },
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["runtime_platform_repair_apply"] is None
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] == "publication_gate_recheck_required"
    assert study["blocked_reason"] == "publication_gate_recheck_required"
    assert study["next_owner"] == "publication_gate"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "publication_gate"
    assert study["owner_route"]["owner_reason"] == "publication_gate_recheck_required"
    assert study["owner_route"]["allowed_actions"] == []
    assert result["queue_history"]["latest_action_count"] == 0
