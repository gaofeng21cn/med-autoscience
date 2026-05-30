from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.progress_portal_cases.helpers import _progress_payload


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


def test_stage_review_projects_paper_facing_stage_log_summary_without_paper_body_write() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    progress = _stage_review_payload()
    progress["stage_log_summary"] = {
        "stage_name": "write",
        "current_owner": "write",
        "problem_summary": "Methods and results needed a clearer validation-cohort narrative.",
        "stage_goal": "Make the current manuscript explain cohort derivation and Table 2 estimates.",
        "paper_work_done": [
            "Methods text now describes the validation cohort.",
            "Results text now points readers to Table 2.",
        ],
        "changed_paper_surfaces": [
            "studies/001-risk/paper/draft.md",
            "studies/001-risk/paper/tables/generated/T2_time_to_event_performance_summary.md",
        ],
        "outcome": "writer_handoff_ready",
        "remaining_blockers": ["AI reviewer recheck still pending"],
        "evidence_refs": [
            "studies/001-risk/artifacts/controller/quality_repair_batch/latest.json",
            "studies/001-risk/artifacts/controller/repair_execution_evidence/latest.json",
        ],
    }

    payload = parts.build_study_workbench_payload(
        progress=progress,
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    summary = payload["stage_review_index"]["stage_log_summary"]
    assert summary["surface_kind"] == "mas_paper_facing_stage_log_summary"
    assert summary["stage_name"] == "write"
    assert summary["current_owner"] == "write"
    assert summary["problem_summary"] == "Methods and results needed a clearer validation-cohort narrative."
    assert summary["stage_goal"] == "Make the current manuscript explain cohort derivation and Table 2 estimates."
    assert summary["paper_work_done"] == [
        "Methods text now describes the validation cohort.",
        "Results text now points readers to Table 2.",
    ]
    assert summary["changed_paper_surfaces"] == [
        "studies/001-risk/paper/draft.md",
        "studies/001-risk/paper/tables/generated/T2_time_to_event_performance_summary.md",
    ]
    assert summary["outcome"] == "writer_handoff_ready"
    assert summary["remaining_blockers"] == ["AI reviewer recheck still pending"]
    assert summary["language_boundary"] == {
        "paper_body_included": False,
        "paper_body_target": False,
        "internal_review_language_allowed_in_paper_body": False,
        "summary_scope": "stage_log_read_model_only",
    }
    assert summary["authority"]["writes_authority_surface"] is False
    assert summary["authority"]["can_write_paper"] is False
    assert summary["authority"]["can_write_publication_eval"] is False
    assert summary["authority"]["can_write_controller_decision"] is False
    assert summary["authority"]["can_authorize_quality_verdict"] is False
    assert "Stage Log 摘要" in html
    assert "Methods and results needed a clearer validation-cohort narrative." in html
    assert "studies/001-risk/artifacts/controller/repair_execution_evidence/latest.json" in html


def test_stage_review_derives_stage_log_summary_from_repair_execution_evidence() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_stage_review_payload(),
        "quality_repair_batch_followthrough": {
            "surface_kind": "quality_repair_batch_followthrough",
            "status": "handoff_ready",
            "summary": "最近一轮 quality-repair batch 已记录正文和证据账本变化。",
            "next_owner": "write",
            "latest_record_path": "studies/001-risk/artifacts/controller/quality_repair_batch/latest.json",
            "repair_execution_evidence_path": (
                "studies/001-risk/artifacts/controller/repair_execution_evidence/latest.json"
            ),
            "repair_execution_evidence": {
                "surface": "repair_execution_evidence",
                "status": "progress_delta_candidate",
                "blockers": ["AI reviewer recheck request still pending"],
                "source_refs": ["studies/001-risk/artifacts/publication_eval/latest.json"],
                "canonical_artifact_delta": {
                    "meaningful_artifact_delta": True,
                    "artifact_refs": [
                        {"path": "studies/001-risk/paper/draft.md"},
                        {
                            "path": (
                                "studies/001-risk/paper/tables/generated/"
                                "T2_time_to_event_performance_summary.md"
                            )
                        },
                    ],
                },
                "evidence_ledger_update_done": True,
                "review_ledger_update_done": True,
                "ai_reviewer_recheck_done": False,
                "evidence_ledger_ref": "studies/001-risk/paper/evidence_ledger.json",
                "review_ledger_ref": "studies/001-risk/paper/review/review_ledger.json",
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

    summary = payload["study_workbench"]["stage_review_index"]["stage_log_summary"]
    assert summary["status"] == "available"
    assert summary["stage_name"] == "write"
    assert summary["current_owner"] == "MedAutoScience"
    assert summary["problem_summary"] == "AI reviewer 要求补充 subgroup sensitivity analysis。"
    assert summary["stage_goal"] == "补充 subgroup 分析并更新 review ledger。"
    assert summary["paper_work_done"] == [
        "manuscript surface updated",
        "table surface updated",
        "canonical paper evidence delta recorded",
        "evidence ledger updated",
        "review ledger updated",
    ]
    assert summary["changed_paper_surfaces"] == [
        "studies/001-risk/paper/manuscript.md",
        "studies/001-risk/paper/tables/table1.csv",
        "studies/001-risk/paper/draft.md",
        "studies/001-risk/paper/tables/generated/T2_time_to_event_performance_summary.md",
        "studies/001-risk/paper/evidence_ledger.json",
        "studies/001-risk/paper/review/review_ledger.json",
    ]
    assert summary["outcome"] == "paper_progress_delta_recorded"
    assert summary["progress_delta_classification"] == "deliverable_progress"
    assert summary["deliverable_progress_delta"] == {"count": 1, "token_usage_total": 0}
    assert summary["paper_progress_delta"] == {"count": 1, "token_usage_total": 0}
    assert summary["platform_repair_delta"] == {"count": 0, "token_usage_total": 0}
    assert "AI reviewer recheck request still pending" in summary["remaining_blockers"]
    assert (
        "studies/001-risk/artifacts/controller/repair_execution_evidence/latest.json"
        in summary["evidence_refs"]
    )
    lane_summary = payload["mas_opl_runtime_workbench_projection"]["studies"][0]["reference_projection"]["lanes"][
        "stage_review_index"
    ]["stage_log_summary"]
    assert lane_summary["outcome"] == "paper_progress_delta_recorded"
    assert lane_summary["progress_delta_classification"] == "deliverable_progress"
    assert lane_summary["deliverable_progress_delta"] == {"count": 1, "token_usage_total": 0}
    assert lane_summary["paper_progress_delta"] == {"count": 1, "token_usage_total": 0}
    assert lane_summary["platform_repair_delta"] == {"count": 0, "token_usage_total": 0}
    assert lane_summary["authority"]["can_write_paper"] is False


def test_stage_review_explicit_summary_without_platform_signals_stays_paper_delta() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    progress = _stage_review_payload()
    progress["stage_log_summary"] = {
        "stage_name": "write",
        "current_owner": "write",
        "problem_summary": "Update manuscript wording after reviewer feedback.",
        "stage_goal": "Polish methods prose and keep figures aligned.",
        "paper_work_done": ["Updated manuscript wording."],
        "changed_paper_surfaces": ["studies/001-risk/paper/draft.md"],
        "remaining_blockers": [],
        "outcome": "writer_handoff_ready",
        "stage_progress_log": {"attempt_count": 2},
    }
    payload = parts.build_study_workbench_payload(
        progress=progress,
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    summary = payload["stage_review_index"]["stage_log_summary"]
    assert summary["progress_delta_classification"] == "deliverable_progress"
    assert summary["deliverable_progress_delta"] == {"count": 1, "token_usage_total": 0}
    assert summary["paper_progress_delta"] == {"count": 1, "token_usage_total": 0}
    assert summary["platform_repair_delta"] == {"count": 0, "token_usage_total": 0}


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


def test_stage_review_materializer_writes_review_page_and_machine_index(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal_parts.stage_review")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    result = module.materialize_stage_review_deliverable_index(
        study_root=study_root,
        study_id="001-risk",
        stage="write",
        payload={
            "owner_receipt_refs": [
                "artifacts/stage_knowledge/memory_write_router_receipts/write-closeout.json",
            ],
            "ledger_refs": [
                "artifacts/evidence_ledger/latest.json",
                "artifacts/review_ledger/latest.json",
            ],
            "quality_refs": [
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "artifact_refs": [
                "artifacts/stage_knowledge/write/latest.json",
                "artifacts/stage_knowledge/write/closeouts/write-closeout.json",
            ],
            "paper_asset_delta": {
                "delta_types": ["manuscript", "table"],
                "refs": ["paper/manuscript.md", "paper/tables/table1.csv"],
                "summary": "Manuscript and Table 1 locator refs changed; bodies are not embedded.",
            },
            "claim_trace": {
                "impact_state": "strengthened",
                "claim_refs": ["primary-outcome-claim"],
                "summary": "Primary claim now links to refreshed evidence refs.",
            },
            "freshness_signal": {
                "state": "green_current",
                "summary": "Owner receipt, ledgers, and quality refs are from the same closeout batch.",
                "source_refs": ["artifacts/publication_eval/latest.json"],
            },
            "human_review": {
                "state": "needs_revision",
                "reviewer_notes": "Result paragraph still needs a numeric sync pass.",
            },
            "next_owner": {
                "owner": "MedAutoScience",
                "next_routes": ["review"],
                "source_ref": "artifacts/controller_decisions/latest.json",
            },
        },
        generated_at="2026-05-12T10:30:00+08:00",
    )

    review_page_path = study_root / "artifacts" / "stage_reviews" / "write" / "latest.md"
    index_path = study_root / "artifacts" / "stage_reviews" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    review_page = review_page_path.read_text(encoding="utf-8")

    assert result["status"] == "available"
    assert result["review_page_path"] == str(review_page_path)
    assert result["index_path"] == str(index_path)
    assert index["surface_kind"] == "mas_stage_deliverable_index"
    assert index["study_id"] == "001-risk"
    assert index["stage"] == "write"
    assert index["status"] == "available"
    assert index["review_page_ref"] == "artifacts/stage_reviews/write/latest.md"
    assert index["deliverable_index_ref"] == "artifacts/stage_reviews/index.json"
    assert index["conditions"]["missing"] == []
    assert index["deliverable_index"]["source_refs"] == index["source_refs"]
    assert index["paper_asset_delta"]["delta_types"] == ["manuscript", "table"]
    assert index["paper_asset_delta"]["body_included"] is False
    assert index["claim_trace"]["impact_state"] == "strengthened"
    assert index["freshness_signal"]["state"] == "green_current"
    assert index["human_review"]["state"] == "needs_revision"
    assert index["next_owner"]["owner"] == "MedAutoScience"
    assert index["authority"]["writes_authority_surface"] is False
    assert index["authority"]["can_authorize_quality_verdict"] is False
    assert index["authority"]["can_authorize_submission_readiness"] is False
    assert "artifacts/publication_eval/latest.json" in index["source_refs"]
    assert "artifacts/controller_decisions/latest.json" in index["source_refs"]
    assert review_page.startswith("# Stage Review: write\n")
    assert "Manuscript and Table 1 locator refs changed" in review_page
    assert "paper/manuscript.md" in review_page
    assert not (study_root / "artifacts" / "publication_eval").exists()
    assert not (study_root / "artifacts" / "controller_decisions").exists()
    assert not (study_root / ".ds").exists()


def test_stage_review_materializer_fails_closed_when_required_refs_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal_parts.stage_review")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    result = module.materialize_stage_review_deliverable_index(
        study_root=study_root,
        study_id="001-risk",
        stage="write",
        payload={
            "paper_asset_delta": {"delta_types": ["manuscript"]},
            "claim_trace": {"impact_state": "strengthened"},
            "freshness_signal": {"state": "green_current"},
            "next_owner": {"owner": "MedAutoScience", "next_routes": ["review"]},
        },
        generated_at="2026-05-12T10:40:00+08:00",
    )

    index_path = study_root / "artifacts" / "stage_reviews" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    review_page = (study_root / "artifacts" / "stage_reviews" / "write" / "latest.md").read_text(encoding="utf-8")

    assert result["status"] == "missing"
    assert index["status"] == "missing"
    assert index["conditions"]["missing"] == [
        "owner_receipt_refs",
        "ledger_refs",
        "quality_refs",
        "artifact_refs",
    ]
    assert index["paper_asset_delta"]["delta_types"] == []
    assert index["claim_trace"]["impact_state"] == "no_claim_change"
    assert index["freshness_signal"]["state"] == "red_stale_or_inconsistent"
    assert index["human_review"]["state"] == "not_recorded"
    assert "Missing conditions" in review_page
    assert "owner_receipt_refs" in review_page
    assert "strengthened" not in review_page
    assert not (study_root / "artifacts" / "publication_eval").exists()
    assert not (study_root / "artifacts" / "controller_decisions").exists()


def test_stage_review_index_summarizes_cross_stage_paper_judgment_without_authority_transfer() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress={
            **_stage_review_payload(),
            "stage_review_index": {
                "surface_kind": "mas_stage_deliverable_index",
                "study_id": "001-risk",
                "stage": "review",
                "review_page_ref": "studies/001-risk/artifacts/stage_reviews/review/latest.md",
                "deliverable_index_ref": "studies/001-risk/artifacts/stage_reviews/index.json",
                "source_refs": ["studies/001-risk/artifacts/stage_reviews/index.json"],
                "paper_line_stage_reviews": [
                    {
                        "stage": "write",
                        "review_page_ref": "studies/001-risk/artifacts/stage_reviews/write/latest.md",
                        "paper_asset_delta": {"delta_types": ["manuscript", "table"]},
                        "claim_trace": {
                            "impact_state": "strengthened",
                            "claim_refs": ["primary-outcome-claim"],
                        },
                        "freshness_signal": {"state": "green_current"},
                        "human_review": {"state": "accept_for_next_stage"},
                        "next_owner": {"owner": "ai_reviewer"},
                    },
                    {
                        "stage": "review",
                        "review_page_ref": "studies/001-risk/artifacts/stage_reviews/review/latest.md",
                        "paper_asset_delta": {"delta_types": ["review_record"]},
                        "claim_trace": {
                            "impact_state": "newly_blocked",
                            "claim_refs": ["secondary-endpoint-claim"],
                        },
                        "freshness_signal": {"state": "red_stale_or_inconsistent"},
                        "human_review": {
                            "state": "human_gate_required",
                            "human_gate_boundary_triggered": True,
                        },
                        "blockers": ["secondary endpoint evidence ledger stale"],
                        "next_owner": {"owner": "MedAutoScience controller"},
                    },
                    {
                        "stage": "finalize",
                        "review_page_ref": "studies/001-risk/artifacts/stage_reviews/finalize/latest.md",
                        "paper_asset_delta": {"delta_types": ["package_delivery"]},
                        "claim_impact": {
                            "impact_state": "weakened",
                            "claim_refs": ["sensitivity-claim"],
                        },
                        "freshness_signal": {"state": "yellow_refresh_recommended"},
                        "human_review_annotation": {"state": "route_back"},
                        "blockers": ["final package proof needs refresh"],
                        "next_owner": {"owner": "MedAutoScience controller"},
                    },
                ],
            },
        },
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )

    summary = payload["stage_review_index"]["paper_line_summary"]
    assert summary["surface_kind"] == "mas_stage_review_paper_line_summary"
    assert summary["stage_count"] == 3
    assert summary["claim_impact_by_state"] == {
        "newly_blocked": ["secondary-endpoint-claim"],
        "strengthened": ["primary-outcome-claim"],
        "weakened": ["sensitivity-claim"],
    }
    assert summary["paper_asset_delta_types"] == ["manuscript", "package_delivery", "review_record", "table"]
    assert summary["freshness_rollup"]["state"] == "red_stale_or_inconsistent"
    assert summary["human_review_rollup"]["states"] == ["accept_for_next_stage", "human_gate_required", "route_back"]
    assert summary["human_review_rollup"]["blocks_auto_advance"] is True
    assert summary["blockers"] == ["final package proof needs refresh", "secondary endpoint evidence ledger stale"]
    assert summary["authority"]["writes_authority_surface"] is False
    assert summary["authority"]["can_authorize_quality_verdict"] is False
    assert summary["authority"]["can_authorize_submission_readiness"] is False
    assert summary["authority"]["can_mark_publication_ready"] is False


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
        "runtime_owner_route_handoffs": [
            {"ref": "artifacts/supervision/owner_route_handoff/latest.json"}
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
    assert lanes["stage_review_index"]["freshness_state"] == "green_current"
    assert lanes["stage_review_index"]["paper_asset_delta_types"] == ["manuscript", "table"]
    assert lanes["stage_review_index"]["claim_impact_state"] == "strengthened"
    assert lanes["stage_review_index"]["human_review_state"] == "needs_revision"
    assert lanes["stage_review_index"]["next_owner"] == "MedAutoScience"
    assert lanes["stage_review_index"]["blockers"] == ["主文结果段尚未同步 Table 1 数值"]
    assert lanes["stage_review_index"]["continue_state"] == "stage_review_attention_required"
    assert lanes["stage_review_index"]["can_authorize_quality_verdict"] is False
    assert lanes["stage_review_index"]["can_mark_publication_ready"] is False
    assert lanes["memory_receipt"]["status"] == "observed"
    assert lanes["memory_receipt"]["can_write_memory_body"] is False
    assert lanes["freshness"]["can_authorize_publication_readiness"] is False
    assert lanes["runtime_owner_route_handoffs"]["can_execute_without_mas_receipt"] is False
    assert lanes["runtime_owner_route_handoffs"]["owner_route_handoff_policy"] == {
        "policy": "safe_action_requires_owner_receipt",
        "required_receipt_surface": "mas_runtime_owner_route_handoff",
        "action_transport_owner": "OPL provider transport",
        "domain_owner": "MedAutoScience",
        "can_execute_without_mas_receipt": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_mutation": False,
    }
    assert "artifacts/provider_attempts/opl-attempt-dm002-001.json" in reference["source_refs"]
    assert "artifacts/autonomy/guarded_apply/receipt-001.json" in reference["source_refs"]
    assert "portfolio/research_memory/publication_route_memory/writeback_receipts/receipt-001.json" in reference[
        "source_refs"
    ]
    assert "artifacts/supervision/owner_route_handoff/latest.json" in reference["source_refs"]
    assert reference["typed_blockers"] == []


def test_progress_portal_opl_projection_exposes_refs_only_paper_route_lens() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_stage_review_payload(),
        "paper_route_lens": {
            "current_route": {
                "route_id": "journal_resolution_after_ai_review",
                "status": "blocked",
                "owner": "MedAutoScience",
                "source_ref": "studies/001-risk/artifacts/controller_decisions/latest.json",
                "next_route_refs": ["studies/001-risk/artifacts/routes/journal_resolution/latest.json"],
                "next_action_refs": ["studies/001-risk/artifacts/supervision/owner_route_handoff/latest.json"],
            },
            "route_attempts": [
                {
                    "attempt_id": "attempt-success",
                    "route_id": "analysis_harmonization",
                    "status": "success",
                    "owner_receipt_refs": [
                        "studies/001-risk/artifacts/owner_receipts/analysis_harmonization.json"
                    ],
                    "artifact_refs": ["studies/001-risk/artifacts/analysis/harmonized_results.json"],
                    "source_refs": ["studies/001-risk/artifacts/routes/analysis_harmonization.json"],
                },
                {
                    "attempt_id": "attempt-failure",
                    "route_id": "submission_package_refresh",
                    "status": "failure",
                    "reviewer_gate_refs": [
                        "studies/001-risk/artifacts/publication_eval/latest.json"
                    ],
                    "source_refs": ["studies/001-risk/artifacts/routes/package_refresh.json"],
                },
                {
                    "attempt_id": "attempt-blocked",
                    "route_id": "journal_resolution_after_ai_review",
                    "status": "blocked",
                    "typed_blocker_refs": [
                        "studies/001-risk/artifacts/blockers/journal_resolution_blocker.json"
                    ],
                    "workspace_refs": ["studies/001-risk"],
                    "next_route_refs": ["studies/001-risk/artifacts/routes/journal_resolution/latest.json"],
                    "next_action_refs": [
                        "studies/001-risk/artifacts/supervision/owner_route_handoff/latest.json"
                    ],
                    "source_refs": ["studies/001-risk/artifacts/routes/journal_resolution_attempt.json"],
                },
            ],
            "owner_receipt_refs": ["studies/001-risk/artifacts/owner_receipts/latest.json"],
            "typed_blocker_refs": ["studies/001-risk/artifacts/blockers/latest.json"],
            "reviewer_gate_refs": ["studies/001-risk/artifacts/review_gate/latest.json"],
            "workspace_refs": ["studies/001-risk"],
            "next_route_refs": ["studies/001-risk/artifacts/routes/journal_resolution/latest.json"],
            "next_action_refs": ["studies/001-risk/artifacts/supervision/owner_route_handoff/latest.json"],
        },
        "artifact_locators": [
            {"group": "draft", "ref": "studies/001-risk/paper/build/review_manuscript.md"},
            {"group": "current_package", "ref": "studies/001-risk/manuscript/current_package"},
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

    study = payload["mas_opl_runtime_workbench_projection"]["studies"][0]
    lens = study["paper_route_lens"]
    assert lens == study["reference_projection"]["lanes"]["paper_route_lens"]
    assert lens["surface_kind"] == "mas_opl_paper_route_lens"
    assert lens["mode"] == "refs_only_paper_route_lens"
    assert lens["body_included"] is False
    assert lens["manuscript_body_included"] is False
    assert lens["artifact_body_included"] is False
    assert lens["claims_publication_ready"] is False
    assert lens["publication_ready_authorized"] is False
    assert lens["current_route"]["route_id"] == "journal_resolution_after_ai_review"
    assert lens["route_attempt_counts"] == {
        "total": 3,
        "success": 1,
        "failure": 1,
        "blocked": 1,
        "explored": 0,
        "unknown": 0,
    }
    assert [attempt["status"] for attempt in lens["route_attempts"]] == ["success", "failure", "blocked"]
    assert "studies/001-risk/artifacts/owner_receipts/latest.json" in lens["owner_receipt_refs"]
    assert lens["blocker_refs"] == [
        "studies/001-risk/artifacts/blockers/latest.json",
        "studies/001-risk/artifacts/blockers/journal_resolution_blocker.json",
    ]
    assert "studies/001-risk/artifacts/blockers/latest.json" in lens["typed_blocker_refs"]
    assert "studies/001-risk/artifacts/review_gate/latest.json" in lens["reviewer_gate_refs"]
    assert lens["stage_review_refs"] == [
        "studies/001-risk/artifacts/stage_reviews/write/latest.md",
        "studies/001-risk/artifacts/stage_reviews/index.json",
    ]
    assert "studies/001-risk/paper/build/review_manuscript.md" in lens["artifact_refs"]
    assert "studies/001-risk" in lens["workspace_refs"]
    assert "studies/001-risk/artifacts/routes/journal_resolution/latest.json" in lens["next_route_refs"]
    assert "studies/001-risk/artifacts/supervision/owner_route_handoff/latest.json" in lens["next_action_refs"]
    assert lens["conditions"]["missing"] == []
    assert lens["authority"] == {
        "opl_role": "workbench_projection_consumer_only",
        "writes_mas_truth": False,
        "body_free": True,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_artifact_mutation": False,
        "can_write_memory_body": False,
    }
