from __future__ import annotations

import importlib

from tests.progress_portal_cases.test_stage_review_surface import _stage_review_payload
from tests.progress_portal_cases.helpers import _progress_payload


def test_progress_portal_opl_projection_fails_closed_when_reference_proofs_are_missing() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        runtime_payload={"study_id": "001-risk", "active_run_id": "run-runtime-001"},
        generated_at="2026-05-08T01:05:00+00:00",
    )

    reference = payload["mas_opl_runtime_workbench_projection"]["studies"][0]["reference_projection"]
    lanes = reference["lanes"]
    assert lanes["provider_attempt"]["status"] == "typed_blocker"
    assert lanes["provider_attempt"]["typed_blocker"] == {
        "blocker_id": "provider_attempt_proof_missing",
        "required_surface": "provider_attempt_receipt",
        "opl_can_override": False,
    }
    assert lanes["guarded_apply"]["status"] == "pending"
    assert lanes["stage_review_index"]["status"] == "pending"
    assert lanes["memory_receipt"]["status"] == "pending"
    assert lanes["runtime_owner_route_handoffs"]["status"] == "pending"
    assert reference["pending_lanes"] == [
        "guarded_apply",
        "stage_review_index",
        "memory_receipt",
        "runtime_owner_route_handoffs",
        "progress_first",
        "stage_artifact_index",
        "paper_route_lens",
    ]
    assert reference["typed_blockers"][0]["blocker_id"] == "provider_attempt_proof_missing"
    assert reference["authority"]["writes_mas_truth"] is False
    assert reference["authority"]["can_authorize_publication_readiness"] is False


def test_progress_portal_opl_projection_prefers_selected_study_stage_review_over_workspace_row() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_stage_review_payload(),
        cockpit_payload={
            "studies": [
                {
                    "study_id": "001-risk",
                    "state_label": "工作区概要行",
                    "current_stage": "write",
                    "progress_freshness": {"status": "fresh"},
                }
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    projection = payload["mas_opl_runtime_workbench_projection"]
    study = projection["studies"][0]
    assert len(projection["studies"]) == 1
    assert study["study_id"] == "001-risk"
    assert study["stage_review"]["status"] == "available"
    assert study["stage_review"]["latest_review_page_ref"] == "studies/001-risk/artifacts/stage_reviews/write/latest.md"
    assert study["links"]["progress_payload_ref"] == "runtime/artifacts/progress_portal/latest.json"


def test_progress_portal_projects_progress_first_next_delta_to_operator_surfaces() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_progress_payload(),
        "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
        "paper_progress_delta": {"count": 0, "token_usage_total": 0},
        "platform_repair_delta": {"count": 2, "token_usage_total": 4096},
        "progress_delta_classification": "platform_repair",
        "progress_first_sprint_state": {
            "classification": "platform_repair",
            "paper_progress_delta_counted": False,
            "platform_repair_delta_counted": True,
            "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
            "paper_progress_delta": {"count": 0, "token_usage_total": 0},
            "platform_repair_delta": {"count": 2, "token_usage_total": 4096},
        },
        "next_forced_delta": {
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "reason": "platform_repair_does_not_count_as_paper_progress",
            "work_unit_id": "publishability_repair_sprint",
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "write",
                "surface_ref": "canonical_manuscript",
            },
            "acceptance_refs": [
                "canonical_manuscript_delta",
                "ai_reviewer_gate_replay_request",
            ],
            "owner_action": {
                "next_owner": "runtime_mechanism_repair",
                "work_unit_id": "publishability_repair_sprint",
                "allowed_actions": ["paper_autonomy/repair-recheck"],
                "owner_receipt_required": True,
            },
        },
        "progress_first_monitoring_summary": {
            "authority": "refs_only_observability",
            "progress_delta_classification": "platform_repair",
            "paper_progress_delta_counted": False,
            "platform_repair_delta_counted": True,
            "next_forced_delta": {
                "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                "reason": "platform_repair_does_not_count_as_paper_progress",
                "work_unit_id": "publishability_repair_sprint",
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "canonical_manuscript",
                },
                "acceptance_refs": [
                    "canonical_manuscript_delta",
                    "ai_reviewer_gate_replay_request",
                ],
                "owner_action": {
                    "next_owner": "runtime_mechanism_repair",
                    "work_unit_id": "publishability_repair_sprint",
                    "allowed_actions": ["paper_autonomy/repair-recheck"],
                    "owner_receipt_required": True,
                },
            },
            "source_refs": [
                "studies/001-risk/artifacts/supervision/progress-first-monitoring/latest.json"
            ],
        },
    }

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        runtime_payload={"study_id": "001-risk", "active_run_id": "run-runtime-001"},
        generated_at="2026-05-08T01:05:00+00:00",
    )

    top_level = payload["study"]["progress_first"]
    selected_study = payload["mas_opl_runtime_workbench_projection"]["studies"][0]
    lane = selected_study["reference_projection"]["lanes"]["progress_first"]
    assert selected_study["progress_first"] == top_level
    assert lane["status"] == "available"
    assert lane["progress_delta_classification"] == "platform_repair"
    assert lane["deliverable_progress_delta"]["count"] == 0
    assert lane["paper_progress_delta"]["count"] == 0
    assert lane["platform_repair_delta"]["count"] == 2
    assert lane["platform_repair_is_deliverable_progress"] is False
    assert lane["next_forced_delta"]["target_surface"]["surface_ref"] == "canonical_manuscript"
    assert lane["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert lane["next_forced_delta"]["owner_action"]["next_owner"] == "runtime_mechanism_repair"
    assert "studies/001-risk/artifacts/supervision/progress-first-monitoring/latest.json" in lane["source_refs"]
    assert lane["authority"] == {
        "writes_authority_surface": False,
        "display_and_drilldown_only": True,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
    }
