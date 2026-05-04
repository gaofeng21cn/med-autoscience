from __future__ import annotations

from copy import deepcopy

from tests.product_entry_cases.cockpit_status_and_frontdesk_focus_cases.test_medical_paper_readiness import (
    _base_progress_payload,
    _ready_doctor_report,
    _ready_mainline_status,
    _ready_supervision,
    make_profile,
    write_study,
)
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


def _patch_ready_workspace(module, monkeypatch) -> None:
    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)


def test_workspace_cockpit_projects_v5_ops_health(monkeypatch, tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _research_loop_readiness()

    _patch_ready_workspace(module, monkeypatch)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    study_health = payload["studies"][0]["medical_paper_ops_health"]
    workspace_health = payload["medical_paper_ops_health_state"]
    markdown = module.render_workspace_cockpit_markdown(payload)

    assert study_health["surface"] == "medical_paper_ops_health"
    assert study_health["overall_status"] == "blocked"
    assert study_health["health"]["provider_health"]["status"] == "ready"
    assert study_health["health"]["stat_guideline_health"]["status"] == "blocked"
    assert study_health["authority_contract"]["can_authorize_quality"] is False
    assert workspace_health["surface"] == "workspace_medical_paper_ops_health"
    assert workspace_health["status"] == "blocked"
    assert workspace_health["counts"] == {"study_count": 1, "ready": 0, "partial": 0, "blocked": 1}
    assert workspace_health["last_green_at"] == "2026-05-04T01:00:00Z"
    research_loop = payload["studies"][0]["medical_paper_research_loop"]
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
    workspace_loop = payload["medical_paper_research_loop_state"]
    assert workspace_loop["surface"] == "workspace_medical_paper_research_loop"
    assert workspace_loop["status"] == "blocked"
    readiness_state = payload["medical_paper_readiness_state"]
    study_readiness = readiness_state["studies"][0]
    assert [card["label"] for card in study_readiness["action_cards"]] == ["处理统计 blocker"]
    workflow_by_title = {step["title"]: step for step in study_readiness["workflow_steps"]}
    assert {
        "处理统计 blocker",
        "运行真实 soak",
        "路线裁决",
        "止损/换线",
        "启动返修",
        "授权写作",
    }.issubset(workflow_by_title)
    assert workflow_by_title["路线裁决"]["status"] == "partial"
    assert workflow_by_title["路线裁决"]["missing_reason"] == "switch_line_decision_pending"
    assert workflow_by_title["止损/换线"]["status"] == "blocked"
    assert workflow_by_title["启动返修"]["status"] == "partial"
    assert workflow_by_title["授权写作"]["action_result"]["missing_reason"] == "ai_reviewer_provenance_missing"
    assert_projection_authority_false(study_health)
    assert_projection_authority_false(workspace_health)
    assert_projection_authority_false(research_loop)
    assert_projection_authority_false(workspace_loop)
    assert "## v5 运营健康闭环 / Medical Paper Ops Health" in markdown
    assert "## 自动论文科研闭环 / Medical Paper Research Loop" in markdown
    assert "动作卡: 处理统计 blocker [blocked / missing_external_validation_plan]" in markdown
    assert "路线裁决 [partial / switch_line_decision_pending]" in markdown
    assert "止损/换线 [blocked / weak_result_requires_stop_loss]" in markdown
    assert "启动返修 [partial / ai_reviewer_recheck_pending]" in markdown
    assert "授权写作 [blocked / ai_reviewer_provenance_missing]" in markdown
    assert "文献缺口 / Literature: `ready`" in markdown
    assert "路线裁决 / Study Line Decision: `partial`" in markdown
    assert "统计 blocker / Statistical Discipline: `blocked`" in markdown
    assert "止损/换线 / Stop-loss or Switch-line: `blocked`" in markdown
    assert "返修/写作授权 / Revision and Authoring: `blocked`" in markdown
    assert "真实 soak / Real Soak: `partial`" in markdown
    assert "ref `artifacts/medical_paper/stop_loss_memo.json`" in markdown
    assert "authority contract: quality/submission/finalize/mechanical-quality `False/False/False/False`" in markdown
    assert "`001-risk` ops health: `blocked`" in markdown


def test_product_frontdesk_projects_workspace_v5_ops_health(monkeypatch, tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _research_loop_readiness()

    _patch_ready_workspace(module, monkeypatch)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
    markdown = module.render_product_frontdesk_markdown(payload)

    ops_health = payload["workspace_medical_paper_ops_health"]
    assert ops_health["surface"] == "workspace_medical_paper_ops_health"
    assert ops_health["status"] == "blocked"
    assert ops_health["authority_contract"]["can_authorize_quality"] is False
    assert ops_health["authority_contract"]["can_authorize_submission"] is False
    assert ops_health["authority_contract"]["can_authorize_finalize"] is False
    research_loop = payload["workspace_medical_paper_research_loop"]
    assert research_loop["surface"] == "workspace_medical_paper_research_loop"
    assert research_loop["status"] == "blocked"
    assert research_loop["counts"] == {"study_count": 1, "ready": 0, "partial": 0, "blocked": 1}
    assert research_loop["authority_contract"]["can_authorize_quality"] is False
    assert research_loop["authority_contract"]["can_authorize_submission"] is False
    assert research_loop["authority_contract"]["can_authorize_finalize"] is False
    assert research_loop["authority_contract"]["mechanical_projection_can_authorize_quality"] is False
    readiness = payload["workspace_medical_paper_readiness"]
    workflow_steps = readiness["studies"][0]["workflow_steps"]
    assert len(workflow_steps) >= 6
    assert all(step["authority_contract"]["can_authorize_quality"] is False for step in workflow_steps)
    assert {step["title"] for step in workflow_steps}.issuperset(
        {"处理统计 blocker", "路线裁决", "止损/换线", "启动返修", "授权写作", "运行真实 soak"}
    )
    assert_projection_authority_false(ops_health)
    assert_projection_authority_false(research_loop)
    assert "Medical paper ops health:" in markdown
    assert "Medical Paper Research Loop:" in markdown
    assert "`001-risk` research loop: blocked" in markdown
    assert "authority contract: quality/submission/finalize/mechanical-quality `False/False/False/False`" in markdown
    assert "`001-risk` ops health: blocked" in markdown
