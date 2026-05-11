from __future__ import annotations

from copy import deepcopy

from tests.product_entry_cases.cockpit_status_and_entry_status_focus_cases.test_medical_paper_readiness import (
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
                "prompt": "OPS_HEALTH_PROMPT_CANARY",
            },
            {
                "surface_key": "stop_loss_memo",
                "status": "blocked",
                "missing_reason": "weak_result_requires_stop_loss",
                "artifact_path": "artifacts/medical_paper/stop_loss_memo.json",
                "evidence_refs": ["artifacts/medical_paper/stop_loss_memo.json"],
                "required_for_ready": True,
                "raw_terminal_log": "OPS_HEALTH_RAW_LOG_CANARY",
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
                "token_count": 1234,
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
    assert research_loop["facets"]["route_decision"]["missing_reason"] == "switch_line_decision_pending"
    assert research_loop["facets"]["route_decision"]["surface_keys"] == ["route_decision_orchestrator"]
    assert research_loop["facets"]["route_decision"]["durable_refs"] == [
        "artifacts/controller_decisions/latest.json"
    ]
    assert research_loop["facets"]["statistical_discipline"]["status"] == "blocked"
    assert research_loop["facets"]["statistical_discipline"]["missing_reason"] == "missing_external_validation_plan"
    assert research_loop["facets"]["stop_loss_switch_line"]["durable_refs"] == [
        "artifacts/medical_paper/stop_loss_memo.json"
    ]
    assert research_loop["facets"]["stop_loss_switch_line"]["surface_keys"] == ["stop_loss_memo"]
    assert research_loop["facets"]["revision_authoring"]["status"] == "blocked"
    assert research_loop["facets"]["revision_authoring"]["surface_keys"] == [
        "revision_rebuttal_loop",
        "authoring_runtime_authorization",
        "ai_reviewer_outcome_learning_regression",
    ]
    assert research_loop["facets"]["revision_authoring"]["durable_refs"] == [
        "artifacts/medical_paper/revision_rebuttal_loop.json",
        "artifacts/medical_paper/authoring_runtime_authorization.json",
        "ai_reviewer_calibration_corpus#weak_external_validation",
    ]
    assert research_loop["facets"]["real_soak"]["status"] == "partial"
    assert research_loop["durable_refs"] == [
        "artifacts/medical_paper/literature_provider_runtime.json",
        "artifacts/controller_decisions/latest.json",
        "artifacts/medical_paper/statistical_discipline_operations.json",
        "artifacts/medical_paper/stop_loss_memo.json",
        "artifacts/medical_paper/revision_rebuttal_loop.json",
        "artifacts/medical_paper/authoring_runtime_authorization.json",
        "ai_reviewer_calibration_corpus#weak_external_validation",
        "artifacts/runtime/soak_monitor.json",
    ]
    assert research_loop["next_action"] == {
        "facet_key": "route_decision",
        "summary": "处理统计 blocker 后决定 stop-loss/switch-line 或写作授权",
        "missing_reason": "switch_line_decision_pending",
    }
    assert research_loop["authority_contract"]["can_authorize_quality"] is False
    assert research_loop["authority_contract"]["can_authorize_submission"] is False
    assert research_loop["authority_contract"]["can_authorize_finalize"] is False
    assert research_loop["authority_contract"]["mechanical_projection_can_authorize_quality"] is False
    workspace_loop = payload["medical_paper_research_loop_state"]
    assert workspace_loop["surface"] == "workspace_medical_paper_research_loop"
    assert workspace_loop["status"] == "blocked"
    assert workspace_loop["counts"] == {"study_count": 1, "ready": 0, "partial": 0, "blocked": 1}
    assert workspace_loop["studies"][0]["durable_refs"] == research_loop["durable_refs"]
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
    assert markdown
    assert "OPS_HEALTH_PROMPT_CANARY" not in markdown
    assert "OPS_HEALTH_RAW_LOG_CANARY" not in markdown
    assert "token_count" not in markdown


def test_product_entry_status_projects_workspace_v5_ops_health(monkeypatch, tmp_path) -> None:
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

    payload = module.build_product_entry_status(profile=profile, profile_ref=profile_ref)
    markdown = module.render_product_entry_status_markdown(payload)

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
    assert {step["guarded_operator_command"]["surface_key"] for step in workflow_steps}.issuperset(
        {
            "statistical_discipline_operations",
            "route_decision_orchestrator",
            "stop_loss_memo",
            "revision_rebuttal_loop",
            "authoring_runtime_authorization",
            "real_workspace_soak_monitor",
        }
    )
    assert research_loop["studies"][0]["durable_refs"] == [
        "artifacts/medical_paper/literature_provider_runtime.json",
        "artifacts/controller_decisions/latest.json",
        "artifacts/medical_paper/statistical_discipline_operations.json",
        "artifacts/medical_paper/stop_loss_memo.json",
        "artifacts/medical_paper/revision_rebuttal_loop.json",
        "artifacts/medical_paper/authoring_runtime_authorization.json",
        "ai_reviewer_calibration_corpus#weak_external_validation",
        "artifacts/runtime/soak_monitor.json",
    ]
    assert_projection_authority_false(ops_health)
    assert_projection_authority_false(research_loop)
    assert markdown
    assert "OPS_HEALTH_PROMPT_CANARY" not in markdown
    assert "OPS_HEALTH_RAW_LOG_CANARY" not in markdown
    assert "token_count" not in markdown
