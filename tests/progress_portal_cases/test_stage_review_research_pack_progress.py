from __future__ import annotations

import importlib

from tests.progress_portal_cases.test_stage_review_surface import _stage_review_payload


def test_stage_review_projects_research_pack_progress_summary_body_free() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_stage_review_payload(),
        "research_evidence_pack_summary": {
            "surface_kind": "mas_research_evidence_pack_summary",
            "progress_summary": {
                "surface_kind": "mas_research_pack_progress_summary",
                "body_included": False,
                "paper_body_included": False,
                "deliverable_progress_delta": {
                    "count": 2,
                    "refs": [
                        "studies/001-risk/paper/draft.md",
                        "studies/001-risk/paper/tables/table1.csv",
                    ],
                },
                "paper_progress_delta": {
                    "count": 2,
                    "refs": [
                        "studies/001-risk/paper/draft.md",
                        "studies/001-risk/paper/tables/table1.csv",
                    ],
                },
                "platform_repair_delta": {
                    "count": 1,
                    "refs": ["studies/001-risk/artifacts/controller/currentness/latest.json"],
                    "counts_as_paper_progress": False,
                },
                "negative_result_count": 3,
                "negative_failed_path_refs": [
                    "studies/001-risk/artifacts/negative_paths/path-1.json",
                    "studies/001-risk/artifacts/negative_paths/path-2.json",
                    "studies/001-risk/artifacts/negative_paths/path-3.json",
                ],
                "route_switch_count": 1,
                "route_switch_refs": ["studies/001-risk/artifacts/routes/switch-1.json"],
                "missing_reproducibility_refs": [
                    "software_environment_refs",
                    "parameter_seed_refs",
                ],
                "single_next_owner_blocker": {
                    "status": "blocked",
                    "ref": "studies/001-risk/artifacts/blockers/next-owner.json",
                    "candidate_count": 1,
                    "body_included": False,
                    "is_route_authority": False,
                },
            },
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
    html = module.render_progress_portal_html(payload)

    summary = payload["study_workbench"]["stage_review_index"]["stage_log_summary"][
        "research_pack_progress_summary"
    ]
    assert summary["body_included"] is False
    assert summary["paper_body_included"] is False
    assert summary["deliverable_progress_delta"]["count"] == 2
    assert summary["paper_progress_delta"]["count"] == 2
    assert summary["platform_repair_delta"] == {
        "count": 1,
        "refs": ["studies/001-risk/artifacts/controller/currentness/latest.json"],
        "counts_as_paper_progress": False,
    }
    assert summary["negative_result_count"] == 3
    assert summary["route_switch_count"] == 1
    assert summary["missing_reproducibility_refs"] == [
        "software_environment_refs",
        "parameter_seed_refs",
    ]
    assert summary["single_next_owner_blocker"]["ref"] == (
        "studies/001-risk/artifacts/blockers/next-owner.json"
    )
    assert summary["single_next_owner_blocker"]["is_route_authority"] is False
    assert summary["authority"]["is_route_authority"] is False
    assert summary["authority"]["platform_repair_counts_as_paper_progress"] is False
    stage_review = payload["mas_opl_runtime_workbench_projection"]["studies"][0]["stage_review"]
    assert stage_review["research_pack_progress_summary"] == summary
    lane = payload["mas_opl_runtime_workbench_projection"]["studies"][0]["reference_projection"]["lanes"][
        "stage_review_index"
    ]
    assert lane["research_pack_progress_summary"] == summary
    assert "Research pack 摘要" in html
    assert "paper/deliverable_delta=2" in html
    assert "platform_repair_delta=1" in html
