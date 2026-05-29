from __future__ import annotations

import importlib

from tests.progress_portal_cases.test_stage_review_surface import _stage_review_payload
from tests.test_progress_portal import _progress_payload


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
    assert study["links"]["progress_payload_ref"] == "artifacts/runtime/progress_portal/latest.json"
