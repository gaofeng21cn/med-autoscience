from __future__ import annotations

import importlib

from tests.test_progress_portal import _progress_payload


def _stage_review_payload() -> dict[str, object]:
    return {
        **_progress_payload(),
        "stage_deliverable_review": {
            "surface_kind": "mas_stage_human_review_page_projection",
            "stage": "write",
            "review_page_ref": "studies/001-risk/artifacts/stage_reviews/write/latest.md",
            "deliverable_index_ref": "studies/001-risk/artifacts/stage_reviews/index.json",
            "source_refs": [
                "studies/001-risk/artifacts/stage_reviews/write/latest.md",
                "studies/001-risk/artifacts/stage_reviews/index.json",
                "studies/001-risk/artifacts/publication_eval/latest.json",
            ],
            "paper_asset_delta": {
                "delta_types": ["manuscript", "table"],
                "refs": [
                    "studies/001-risk/paper/manuscript.md",
                    "studies/001-risk/paper/tables/table1.csv",
                ],
            },
            "source_grounding": {
                "source_map_refs": ["studies/001-risk/artifacts/source_maps/write/latest.json"],
                "page_block_anchor_refs": ["studies/001-risk/artifacts/source_maps/write/page-blocks.json"],
                "figure_near_claim_refs": ["studies/001-risk/artifacts/source_maps/write/figure-near-claims.json"],
            },
            "paper_presentation_note": {
                "ref": "studies/001-risk/artifacts/presentations/write/evidence-spine.pptx",
                "evidence_spine_refs": ["studies/001-risk/artifacts/presentations/write/evidence-spine.json"],
                "summary": "主结果、Table 1 和 Figure 2 按 evidence spine 排列。",
            },
            "claim_trace": {
                "impact_state": "strengthened",
                "claim_refs": ["primary-outcome-claim"],
                "summary": "主结果 claim 得到新增亚组敏感性分析支持。",
            },
            "freshness_signal": {
                "state": "green_current",
                "summary": "审阅页、证据账本和 publication eval 来自同一刷新批次。",
                "source_refs": [
                    "studies/001-risk/artifacts/stage_reviews/write/latest.md",
                    "studies/001-risk/artifacts/publication_eval/latest.json",
                ],
            },
            "human_review": {
                "state": "needs_revision",
                "reviewer_notes": "表 1 已更新，但主文结果段仍需同步数值。",
            },
            "next_owner": {
                "owner": "MedAutoScience",
                "next_routes": ["review"],
                "source_ref": "studies/001-risk/artifacts/controller_decisions/latest.json",
            },
            "blockers": ["主文结果段尚未同步 Table 1 数值"],
        },
    }


def test_study_workbench_projects_stage_review_page_index_as_human_audit_table() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress=_stage_review_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    assert {"id": "stage_review", "label": "Stage 交付审阅", "status": "available"} in payload["tabs"]
    review = payload["stage_review_index"]
    assert review["surface_kind"] == "mas_progress_portal_stage_review_index"
    assert review["status"] == "available"
    assert review["authority"]["writes_authority_surface"] is False
    assert review["authority"]["can_authorize_quality_verdict"] is False
    assert review["authority"]["can_authorize_submission_readiness"] is False
    assert review["authority"]["can_mark_publication_ready"] is False
    assert review["current_stage"] == "write"
    assert review["latest_review_page"]["ref"] == "studies/001-risk/artifacts/stage_reviews/write/latest.md"
    assert review["deliverable_index_ref"] == "studies/001-risk/artifacts/stage_reviews/index.json"
    assert review["rows"][0]["stage"] == "write"
    assert [item["role"] for item in review["rows"][0]["deliverable_index"]["input_refs"]] == [
        "stage_knowledge_packet",
        "active_study_charter",
        "stage_entry_conditions",
    ]
    assert review["rows"][0]["deliverable_index"]["quality_gate_ref"]["ref"] == "publication_eval/latest.json"
    assert review["rows"][0]["paper_asset_delta"]["delta_types"] == ["manuscript", "table"]
    assert review["rows"][0]["paper_asset_delta"]["body_included"] is False
    assert review["rows"][0]["source_grounding"]["source_map_refs"] == [
        "studies/001-risk/artifacts/source_maps/write/latest.json"
    ]
    assert review["rows"][0]["source_grounding"]["page_block_anchor_refs"] == [
        "studies/001-risk/artifacts/source_maps/write/page-blocks.json"
    ]
    assert review["rows"][0]["source_grounding"]["figure_near_claim_refs"] == [
        "studies/001-risk/artifacts/source_maps/write/figure-near-claims.json"
    ]
    assert review["rows"][0]["source_grounding"]["can_write_mas_truth"] is False
    assert review["rows"][0]["paper_presentation_note"]["mode"] == "optional_deliverable_note"
    assert review["rows"][0]["paper_presentation_note"]["evidence_spine_refs"] == [
        "studies/001-risk/artifacts/presentations/write/evidence-spine.json"
    ]
    assert review["rows"][0]["paper_presentation_note"]["can_authorize_quality_verdict"] is False
    assert review["rows"][0]["paper_presentation_note"]["can_authorize_publication_readiness"] is False
    assert review["rows"][0]["claim_impact"]["impact_state"] == "strengthened"
    assert review["rows"][0]["claim_impact"]["can_authorize_quality_verdict"] is False
    assert review["rows"][0]["freshness_signal"]["state"] == "green_current"
    assert review["rows"][0]["human_review_annotation"]["state"] == "needs_revision"
    assert review["rows"][0]["human_review_annotation"]["blocks_auto_advance"] is False
    assert review["rows"][0]["human_review_annotation"]["can_mark_publication_ready"] is False
    assert review["rows"][0]["continue_state"]["state"] == "stage_review_attention_required"
    assert review["rows"][0]["continue_state"]["auto_advance_authority"] is False
    assert review["rows"][0]["blockers"] == ["主文结果段尚未同步 Table 1 数值"]
    assert "stage_review_page" not in review["conditions"]["missing"]
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in review["source_refs"]

    assert "Stage 交付审阅" in html
    assert "最新审阅页" in html
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in html
    assert "manuscript, table" in html
    assert "studies/001-risk/artifacts/source_maps/write/latest.json" in html
    assert "studies/001-risk/artifacts/presentations/write/evidence-spine.pptx" in html
    assert "strengthened" in html
    assert "needs_revision" in html
    assert "主文结果段尚未同步 Table 1 数值" in html
    assert "质量 verdict" in html


def test_study_workbench_stage_review_fails_closed_without_explicit_review_ref() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    review = payload["stage_review_index"]
    assert {"id": "stage_review", "label": "Stage 交付审阅", "status": "missing"} in payload["tabs"]
    assert review["status"] == "missing"
    assert "stage_review_page" in review["conditions"]["missing"]
    assert "stage_deliverable_index_ref" in review["conditions"]["missing"]
    assert review["authority"]["writes_authority_surface"] is False
    assert "缺少 Stage Review Page / Deliverable Index 显式引用" in html
    assert "不从文件名、产物路径或 stage 文案猜测审阅结论" in html


def test_progress_portal_opl_projection_indexes_stage_review_refs_without_authority_transfer() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        profile_ref="/workspace/ops/medautoscience/profiles/diabetes.toml",
        study_id="001-risk",
        progress_payload=_stage_review_payload(),
        runtime_payload={"study_id": "001-risk", "active_run_id": "run-runtime-001"},
        generated_at="2026-05-08T01:05:00+00:00",
    )

    projection = payload["mas_opl_runtime_workbench_projection"]
    study = projection["studies"][0]
    stage_review = study["stage_review"]
    assert stage_review["status"] == "available"
    assert stage_review["latest_review_page_ref"] == "studies/001-risk/artifacts/stage_reviews/write/latest.md"
    assert stage_review["deliverable_index_ref"] == "studies/001-risk/artifacts/stage_reviews/index.json"
    assert stage_review["freshness_state"] == "green_current"
    assert stage_review["paper_asset_delta_types"] == ["manuscript", "table"]
    assert stage_review["source_map_refs"] == ["studies/001-risk/artifacts/source_maps/write/latest.json"]
    assert stage_review["page_block_anchor_refs"] == [
        "studies/001-risk/artifacts/source_maps/write/page-blocks.json"
    ]
    assert stage_review["figure_near_claim_refs"] == [
        "studies/001-risk/artifacts/source_maps/write/figure-near-claims.json"
    ]
    assert stage_review["paper_presentation_note_ref"] == (
        "studies/001-risk/artifacts/presentations/write/evidence-spine.pptx"
    )
    assert stage_review["paper_presentation_evidence_spine_refs"] == [
        "studies/001-risk/artifacts/presentations/write/evidence-spine.json"
    ]
    assert stage_review["claim_impact_state"] == "strengthened"
    assert stage_review["human_review_state"] == "needs_revision"
    assert stage_review["next_owner"] == "MedAutoScience"
    assert stage_review["opl_projection_boundary"] == "read_only_locator_no_truth_write"
    assert stage_review["can_authorize_quality_verdict"] is False
    assert stage_review["can_authorize_submission_readiness"] is False
    assert stage_review["can_mark_publication_ready"] is False
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in study["links"]["artifact_refs"]
    assert "studies/001-risk/artifacts/stage_reviews/index.json" in study["links"]["artifact_refs"]
    assert "studies/001-risk/artifacts/source_maps/write/latest.json" in study["links"]["artifact_refs"]
    assert "studies/001-risk/artifacts/presentations/write/evidence-spine.pptx" in study["links"]["artifact_refs"]
    assert "stage_review_page" not in projection["conditions"]["missing"]


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
