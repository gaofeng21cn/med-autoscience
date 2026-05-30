from __future__ import annotations

import importlib


def test_progress_portal_opl_projection_projects_workspace_paper_route_lens_per_study() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        cockpit_payload={
            "studies": [
                {
                    "study_id": "001-risk",
                    "display_title": "Risk paper",
                    "paper_route_lens": {
                        "current_route": "journal_resolution_after_ai_review",
                        "route_attempt_counts": {"success": 1, "failure": 1, "blocked": 1},
                        "blocker_refs": ["studies/001-risk/artifacts/blockers/latest.json"],
                        "next_route_refs": ["studies/001-risk/artifacts/routes/journal_resolution/latest.json"],
                        "next_action_refs": ["studies/001-risk/artifacts/supervision/owner_route_handoff/latest.json"],
                        "stage_review_refs": [
                            "studies/001-risk/artifacts/stage_reviews/write/latest.md",
                            "studies/001-risk/artifacts/stage_reviews/index.json",
                        ],
                    },
                },
                {
                    "study_id": "002-obesity",
                    "paper_route_lens": {
                        "current_route": {"route_id": "evidence_refresh"},
                        "route_attempt_counts": {"success": 2, "failure": 0, "blocked": 0},
                        "blocker_refs": [],
                        "next_route_refs": ["studies/002-obesity/artifacts/routes/evidence_refresh/latest.json"],
                        "next_action_refs": ["studies/002-obesity/artifacts/supervision/owner_route_handoff/latest.json"],
                        "stage_review_refs": ["studies/002-obesity/artifacts/stage_reviews/review/latest.md"],
                    },
                },
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    projection = payload["mas_opl_runtime_workbench_projection"]
    risk, obesity = projection["studies"]

    assert risk["paper_route_lens"] == {
        "surface_kind": "mas_opl_paper_route_lens_summary",
        "schema_version": 1,
        "mode": "refs_only_paper_route_lens_summary",
        "body_included": False,
        "claims_publication_ready": False,
        "current_route": {"route_id": "journal_resolution_after_ai_review"},
        "route_attempt_counts": {"success": 1, "failure": 1, "blocked": 1},
        "blocker_refs": ["studies/001-risk/artifacts/blockers/latest.json"],
        "next_route_refs": ["studies/001-risk/artifacts/routes/journal_resolution/latest.json"],
        "next_action_refs": ["studies/001-risk/artifacts/supervision/owner_route_handoff/latest.json"],
        "stage_review_refs": [
            "studies/001-risk/artifacts/stage_reviews/write/latest.md",
            "studies/001-risk/artifacts/stage_reviews/index.json",
        ],
        "authority": {
            "opl_role": "workbench_projection_consumer_only",
            "writes_mas_truth": False,
            "body_free": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
            "can_write_memory_body": False,
        },
    }
    assert obesity["paper_route_lens"]["current_route"] == {"route_id": "evidence_refresh"}
    assert obesity["paper_route_lens"]["route_attempt_counts"] == {"success": 2, "failure": 0, "blocked": 0}
    assert obesity["paper_route_lens"]["body_included"] is False
    assert obesity["paper_route_lens"]["claims_publication_ready"] is False
