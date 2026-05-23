from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.owner_route_reconcile_parts import domain_transition_actions
from tests.study_runtime_test_helpers import make_profile, write_study


def test_domain_transition_routes_medical_prose_write_repair_to_quality_batch() -> None:
    actions = domain_transition_actions.actions(
        {
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair medical journal prose quality.",
                },
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            }
        }
    )

    assert actions is not None
    assert len(actions) == 1
    action = actions[0]
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["owner"] == "write"
    assert action["request_owner"] == "write"
    assert action["recommended_owner"] == "write"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["required_output_surface"] == (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    )


def test_domain_transition_routes_analysis_campaign_medical_prose_write_repair_to_write_owner() -> None:
    actions = domain_transition_actions.actions(
        {
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "analysis-campaign",
                "owner": "analysis-campaign",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair denominator truth, displays, and journal prose from current AI reviewer findings.",
                },
                "guard_boundary": {"opl_generic_runner_may_resume": False},
            }
        }
    )

    assert actions is not None
    assert len(actions) == 1
    action = actions[0]
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["owner"] == "write"
    assert action["request_owner"] == "write"
    assert action["recommended_owner"] == "write"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["controller_work_unit_id"] == "medical_prose_write_repair"
    assert action["executable_work_unit"] == "medical_prose_write_repair"
    assert action["route_target"] == "write"
    assert action["original_route_target"] == "analysis-campaign"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"


def test_scan_routes_medical_prose_write_repair_despite_stale_opl_owner_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair manuscript methods and journal prose.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-medical-prose",
            "source_signature": "truth-source-dm003-medical-prose",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "surface": "ai_repair_lifecycle",
            "state": "owner_route_required",
            "blocked_reason": "runtime_controller_redrive_required",
            "next_owner": "one-person-lab",
            "opl_runtime_owner_route_required": True,
            "dispatch_status": "owner_route_required",
        },
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::medical-prose-routeback",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair manuscript methods and journal prose.",
                },
            }
        ],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
