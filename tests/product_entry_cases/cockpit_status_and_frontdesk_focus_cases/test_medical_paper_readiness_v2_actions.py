from __future__ import annotations

from tests.product_entry_cases.cockpit_status_and_frontdesk_focus_cases.test_medical_paper_readiness import (
    _base_progress_payload,
    _ready_doctor_report,
    _ready_mainline_status,
    _ready_supervision,
    make_profile,
    write_study,
)


def _v2_workflow_readiness() -> dict[str, object]:
    return {
        "surface": "medical_paper_readiness",
        "overall_status": "blocked",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 0,
        "required_count": 6,
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_provider_runtime",
            "summary": "补齐 provider-backed 文献摄取。",
        },
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "label": "Literature Provider Runtime",
                "status": "missing",
                "missing_reason": "missing_provider_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "route_decision_orchestrator",
                "label": "Route Decision Orchestrator",
                "status": "missing",
                "missing_reason": "missing_controller_decision_projection",
                "required_for_ready": True,
            },
            {
                "surface_key": "statistical_discipline_operations",
                "label": "Statistical Discipline Operations",
                "status": "blocked",
                "missing_reason": "open_precision_and_validation_blockers",
                "required_for_ready": True,
            },
            {
                "surface_key": "revision_rebuttal_loop",
                "label": "Revision / Rebuttal Loop",
                "status": "blocked",
                "missing_reason": "missing_reviewer_comment_intake",
                "required_for_ready": True,
            },
            {
                "surface_key": "authoring_runtime_authorization",
                "label": "Authoring Runtime Authorization",
                "status": "missing",
                "missing_reason": "missing_ai_reviewer_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "real_workspace_soak_monitor",
                "label": "Real Workspace Soak Monitor",
                "status": "partial",
                "missing_reason": "missing_required_archetype",
                "required_for_ready": True,
            },
        ],
    }


def test_workspace_cockpit_exposes_long_horizon_paper_operations_action_cards(
    monkeypatch,
    tmp_path,
) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = {
        "surface": "medical_paper_readiness",
        "overall_status": "blocked",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 0,
        "required_count": 7,
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_provider_runtime",
            "summary": "补齐 provider-backed 文献摄取。",
        },
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "label": "Literature Provider Runtime",
                "status": "missing",
                "missing_reason": "missing_provider_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "revision_rebuttal_loop",
                "label": "Revision / Rebuttal Loop",
                "status": "blocked",
                "missing_reason": "missing_reviewer_comment_intake",
                "required_for_ready": True,
            },
            {
                "surface_key": "real_workspace_soak_monitor",
                "label": "Real Workspace Soak Monitor",
                "status": "partial",
                "missing_reason": "missing_required_archetype",
                "required_for_ready": True,
            },
        ],
    }

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    cards = payload["studies"][0]["medical_paper_readiness"]["action_cards"]

    assert [card["action_id"] for card in cards] == [
        "run_provider_literature_scout",
        "start_revision_rebuttal_loop",
        "run_real_workspace_soak_monitor",
    ]
    assert [card["label"] for card in cards] == ["联网补文献", "启动返修", "运行真实 soak"]
    assert all(card["authority"] == "observability_projection_only" for card in cards)
    assert all(card["quality_claim_authorized"] is False for card in cards)


def test_product_frontdesk_promotes_v2_action_cards_to_workflow_steps(
    monkeypatch,
    tmp_path,
) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _v2_workflow_readiness()

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
    workflow_steps = payload["phase2_user_product_loop"]["workflow_steps"]

    assert [step["step_id"] for step in workflow_steps] == [
        "run_provider_literature_scout",
        "materialize_route_decision",
        "resolve_statistical_blockers",
        "start_revision_rebuttal_loop",
        "authorize_manuscript_drafting",
        "run_real_workspace_soak_monitor",
    ]
    assert [step["title"] for step in workflow_steps] == [
        "联网补文献",
        "写入路线裁决",
        "处理统计 blocker",
        "启动返修",
        "授权写作",
        "运行真实 soak",
    ]
    assert all(step["authority"] == "observability_projection_only" for step in workflow_steps)
    assert all(step["quality_claim_authorized"] is False for step in workflow_steps)
    assert all(step["surface_kind"] == "medical_paper_readiness_action_card" for step in workflow_steps)
    assert workflow_steps[0]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["operator_brief"]["recommended_step_id"] == "run_provider_literature_scout"


def test_workspace_cockpit_markdown_renders_v2_action_card_status_and_missing_reason(
    monkeypatch,
    tmp_path,
) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _v2_workflow_readiness()

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    markdown = module.render_workspace_cockpit_markdown(
        module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    )

    assert "动作卡: 联网补文献 [missing / missing_provider_provenance]" in markdown
    assert "写入路线裁决 [missing / missing_controller_decision_projection]" in markdown
    assert "处理统计 blocker [blocked / open_precision_and_validation_blockers]" in markdown
    assert "运行真实 soak [partial / missing_required_archetype]" in markdown
