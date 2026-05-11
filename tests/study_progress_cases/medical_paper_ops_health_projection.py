from __future__ import annotations

from copy import deepcopy
import importlib

from tests.test_medical_paper_ops_health import _readiness, assert_projection_authority_false


def _research_loop_readiness() -> dict[str, object]:
    readiness = deepcopy(_readiness())
    readiness["next_action"] = {
        "summary": "处理统计 blocker 后决定 stop-loss/switch-line 或写作授权",
        "action_id": "resolve_statistical_blockers",
    }
    readiness["capability_surfaces"].extend(
        [
            {
                "surface_key": "route_decision_orchestrator",
                "status": "partial",
                "missing_reason": "switch_line_decision_pending",
                "artifact_path": "artifacts/controller_decisions/latest.json",
                "evidence_refs": ["artifacts/controller_decisions/latest.json"],
                "required_for_ready": True,
            },
            {
                "surface_key": "stop_loss_memo",
                "status": "blocked",
                "missing_reason": "weak_result_requires_stop_loss",
                "artifact_path": "artifacts/medical_paper/stop_loss_memo.json",
                "evidence_refs": ["artifacts/medical_paper/stop_loss_memo.json"],
                "required_for_ready": True,
            },
            {
                "surface_key": "revision_rebuttal_loop",
                "status": "partial",
                "missing_reason": "ai_reviewer_recheck_pending",
                "artifact_path": "artifacts/medical_paper/revision_rebuttal_loop.json",
                "evidence_refs": ["artifacts/medical_paper/revision_rebuttal_loop.json"],
                "required_for_ready": True,
            },
            {
                "surface_key": "authoring_runtime_authorization",
                "status": "blocked",
                "missing_reason": "ai_reviewer_provenance_missing",
                "artifact_path": "artifacts/medical_paper/authoring_runtime_authorization.json",
                "evidence_refs": ["artifacts/medical_paper/authoring_runtime_authorization.json"],
                "required_for_ready": True,
            },
        ]
    )
    return readiness


def _progress_payload() -> dict[str, object]:
    return {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "current_stage": "publication_supervision",
        "paper_stage": "drafting",
        "medical_paper_readiness": _research_loop_readiness(),
    }


def test_compact_mcp_progress_projection_preserves_v5_ops_health() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(_progress_payload())
    ops_health = compact["medical_paper_readiness"]["ops_health"]

    assert ops_health["surface"] == "medical_paper_ops_health"
    assert ops_health["overall_status"] == "blocked"
    assert ops_health["last_green_at"] == "2026-05-04T01:00:00Z"
    assert ops_health["health"]["provider_health"]["status"] == "ready"
    assert ops_health["health"]["stat_guideline_health"]["status"] == "blocked"
    assert ops_health["authority_contract"]["can_authorize_quality"] is False
    assert ops_health["authority_contract"]["can_authorize_submission"] is False
    assert ops_health["authority_contract"]["can_authorize_finalize"] is False
    research_loop = compact["medical_paper_readiness"]["research_loop"]
    assert research_loop["surface"] == "medical_paper_research_loop"
    assert research_loop["facets"]["literature"]["status"] == "ready"
    assert research_loop["facets"]["route_decision"]["status"] == "partial"
    assert research_loop["facets"]["statistical_discipline"]["status"] == "blocked"
    assert research_loop["facets"]["stop_loss_switch_line"]["durable_refs"] == [
        "artifacts/medical_paper/stop_loss_memo.json"
    ]
    assert research_loop["facets"]["revision_authoring"]["status"] == "blocked"
    assert research_loop["facets"]["real_soak"]["status"] == "partial"
    assert research_loop["authority_contract"]["can_authorize_quality"] is False
    assert research_loop["authority_contract"]["can_authorize_submission"] is False
    assert research_loop["authority_contract"]["can_authorize_finalize"] is False
    assert research_loop["authority_contract"]["mechanical_projection_can_authorize_quality"] is False
    assert_projection_authority_false(compact["medical_paper_readiness"])


def test_mcp_and_study_progress_markdown_render_v5_ops_health() -> None:
    mcp_module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")

    mcp_markdown = mcp_module.render_mcp_study_progress_markdown(_progress_payload())
    progress_markdown = progress_module.render_study_progress_markdown(_progress_payload())

    assert mcp_markdown.strip()
    assert progress_markdown.strip()
