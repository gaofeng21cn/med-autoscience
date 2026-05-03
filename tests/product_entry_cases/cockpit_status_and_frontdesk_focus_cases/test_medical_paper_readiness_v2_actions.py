from __future__ import annotations

from tests.product_entry_cases.cockpit_status_and_frontdesk_focus_cases.test_medical_paper_readiness import (
    _base_progress_payload,
    _ready_doctor_report,
    _ready_mainline_status,
    _ready_supervision,
    make_profile,
    write_study,
)


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
