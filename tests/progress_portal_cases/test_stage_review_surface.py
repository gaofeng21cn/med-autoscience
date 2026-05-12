from __future__ import annotations

import importlib
import json
from pathlib import Path

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


def _write_stage_review_index(study_root: Path) -> None:
    latest = study_root / "artifacts" / "stage_reviews" / "write" / "latest.md"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text("# Write Stage Review\n\n人工审阅页正文留在 workspace artifact。\n", encoding="utf-8")
    index = {
        "surface_kind": "mas_stage_deliverable_index",
        "study_id": "001-risk",
        "stage": "write",
        "review_page_ref": "artifacts/stage_reviews/write/latest.md",
        "source_refs": [
            "studies/001-risk/artifacts/publication_eval/latest.json",
            "studies/001-risk/artifacts/controller_decisions/latest.json",
        ],
        "paper_asset_delta": {
            "delta_types": ["manuscript", "figure"],
            "refs": [
                "studies/001-risk/paper/manuscript.md",
                "studies/001-risk/paper/figures/figure1.png",
            ],
            "summary": "主文与 Figure 1 已刷新。",
        },
        "claim_trace": {
            "impact_state": "changed_scope",
            "claim_refs": ["secondary-endpoint-claim"],
        },
        "freshness_signal": {
            "state": "yellow_refresh_recommended",
            "source_refs": ["studies/001-risk/artifacts/stage_reviews/index.json"],
        },
        "human_review": {
            "state": "annotated",
            "reviewer_notes": "需要人工复核 Figure 1 caption。",
        },
        "next_owner": {
            "owner": "ai_reviewer",
            "next_routes": ["review"],
            "source_ref": "studies/001-risk/artifacts/controller_decisions/latest.json",
        },
        "blockers": [],
    }
    (study_root / "artifacts" / "stage_reviews").mkdir(parents=True, exist_ok=True)
    (study_root / "artifacts" / "stage_reviews" / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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


def test_study_workbench_reads_stage_review_page_and_index_from_artifact_locator(tmp_path: Path) -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_stage_review_index(study_root)

    payload = parts.build_study_workbench_payload(
        progress={
            **_progress_payload(),
            "study_id": "001-risk",
            "study_root": str(study_root),
        },
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    review = payload["stage_review_index"]
    row = review["rows"][0]
    assert review["status"] == "available"
    assert review["deliverable_index_ref"] == "studies/001-risk/artifacts/stage_reviews/index.json"
    assert review["latest_review_page"]["ref"] == "studies/001-risk/artifacts/stage_reviews/write/latest.md"
    assert review["locator_projection"]["artifact_locator"]["read_only"] is True
    assert row["paper_line_index_proof"]["surface_kind"] == "mas_stage_deliverable_index_locator_proof"
    assert row["paper_line_index_proof"]["index_surface_kind"] == "mas_stage_deliverable_index"
    assert row["paper_line_index_proof"]["body_included"] is False
    assert row["latest_review_page_proof"]["status"] == "available"
    assert row["latest_review_page_proof"]["body_included"] is False
    assert row["paper_asset_delta"]["delta_types"] == ["manuscript", "figure"]
    assert row["claim_impact"]["impact_state"] == "changed_scope"
    assert row["human_review_annotation"]["state"] == "annotated"
    assert row["next_owner"]["owner"] == "ai_reviewer"
    assert row["authority"]["can_authorize_artifact_authority"] is False
    assert "studies/001-risk/artifacts/stage_reviews/index.json" in review["source_refs"]
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in review["source_refs"]
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in html
    assert "changed_scope" in html


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


def test_progress_portal_opl_projection_exposes_reference_lanes_as_read_only_drilldown() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_stage_review_payload(),
        "provider_attempt_projection": {
            "attempt_id": "opl-attempt-dm002-001",
            "attempt_owner": "one-person-lab",
            "provider_attempt_is_truth": False,
            "provider_attempt_wrote_workspace": False,
            "source_refs": ["artifacts/provider_attempts/opl-attempt-dm002-001.json"],
        },
        "guarded_apply_proof": {
            "guarded_apply_status": "mas_owner_apply_receipt_observed",
            "summary": {"guarded_apply_performed": True},
            "guarded_apply_receipts": [
                {"ref": "artifacts/autonomy/guarded_apply/receipt-001.json"}
            ],
        },
        "publication_route_memory_final_proof": {
            "status": "final_ref_chain_proven",
            "writeback_receipt_refs": [
                "portfolio/research_memory/publication_route_memory/writeback_receipts/receipt-001.json"
            ],
        },
        "safety_action_receipts": [
            {"audit_ref": "artifacts/runtime/progress_portal/action_receipts/resume-001.json"}
        ],
    }

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        profile_ref="/workspace/ops/medautoscience/profiles/diabetes.toml",
        study_id="001-risk",
        progress_payload=progress,
        runtime_payload={"study_id": "001-risk", "active_run_id": "run-runtime-001"},
        generated_at="2026-05-08T01:05:00+00:00",
    )

    reference = payload["mas_opl_runtime_workbench_projection"]["studies"][0]["reference_projection"]
    assert reference["surface_kind"] == "mas_opl_workbench_reference_projection"
    assert reference["mode"] == "read_only_drilldown"
    assert reference["authority"] == {
        "opl_role": "read_model_drilldown_consumer_only",
        "writes_mas_truth": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_apply_guarded_mutation": False,
        "can_write_memory_body": False,
    }
    lanes = reference["lanes"]
    assert lanes["provider_attempt"]["status"] == "observed"
    assert lanes["provider_attempt"]["attempt_id"] == "opl-attempt-dm002-001"
    assert lanes["provider_attempt"]["provider_attempt_is_truth"] is False
    assert lanes["guarded_apply"]["status"] == "observed"
    assert lanes["guarded_apply"]["guarded_apply_performed"] is True
    assert lanes["guarded_apply"]["paper_closure_authorized"] is False
    assert lanes["stage_review_index"]["status"] == "observed"
    assert lanes["memory_receipt"]["status"] == "observed"
    assert lanes["memory_receipt"]["can_write_memory_body"] is False
    assert lanes["freshness"]["can_authorize_publication_readiness"] is False
    assert lanes["safety_action_receipts"]["can_execute_without_mas_receipt"] is False
    assert "artifacts/provider_attempts/opl-attempt-dm002-001.json" in reference["source_refs"]
    assert "artifacts/autonomy/guarded_apply/receipt-001.json" in reference["source_refs"]
    assert "portfolio/research_memory/publication_route_memory/writeback_receipts/receipt-001.json" in reference[
        "source_refs"
    ]
    assert "artifacts/runtime/progress_portal/action_receipts/resume-001.json" in reference["source_refs"]
    assert reference["typed_blockers"] == []


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
    assert lanes["safety_action_receipts"]["status"] == "pending"
    assert reference["pending_lanes"] == [
        "guarded_apply",
        "stage_review_index",
        "memory_receipt",
        "safety_action_receipts",
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
