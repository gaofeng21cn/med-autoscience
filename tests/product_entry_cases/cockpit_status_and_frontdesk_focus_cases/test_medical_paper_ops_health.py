from __future__ import annotations

from tests.product_entry_cases.cockpit_status_and_frontdesk_focus_cases.test_medical_paper_readiness import (
    _base_progress_payload,
    _ready_doctor_report,
    _ready_mainline_status,
    _ready_supervision,
    make_profile,
    write_study,
)
from tests.test_medical_paper_ops_health import _readiness


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
    readiness = _readiness()

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
    assert "## v5 运营健康闭环 / Medical Paper Ops Health" in markdown
    assert "`001-risk` ops health: `blocked`" in markdown


def test_product_frontdesk_projects_workspace_v5_ops_health(monkeypatch, tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _readiness()

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
    assert "Medical paper ops health:" in markdown
    assert "`001-risk` ops health: blocked" in markdown
