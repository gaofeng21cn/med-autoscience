from __future__ import annotations

import importlib

from tests.test_medical_paper_ops_health import _readiness


def _progress_payload() -> dict[str, object]:
    return {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "current_stage": "publication_supervision",
        "paper_stage": "drafting",
        "medical_paper_readiness": _readiness(),
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


def test_mcp_and_study_progress_markdown_render_v5_ops_health() -> None:
    mcp_module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")

    mcp_markdown = mcp_module.render_mcp_study_progress_markdown(_progress_payload())
    progress_markdown = progress_module.render_study_progress_markdown(_progress_payload())

    assert "## Medical Paper v5 Ops Health" in mcp_markdown
    assert "- provider_health: `ready` (clear)" in mcp_markdown
    assert "- stat_guideline_health: `blocked` (missing_external_validation_plan)" in mcp_markdown
    assert "- quality/submission/finalize authority: `False/False/False`" in mcp_markdown
    assert "## v5 运营健康闭环 / Medical Paper Ops Health" in progress_markdown
    assert "- provider_health: `ready`（clear）" in progress_markdown
    assert "- stat_guideline_health: `blocked`（missing_external_validation_plan）" in progress_markdown
    assert "- authority: projection-only；quality/submission/finalize authorization: `False/False/False`" in progress_markdown
