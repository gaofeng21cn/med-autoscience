from __future__ import annotations

from tests.product_entry_cases import shared as _shared
from tests.product_entry_cases import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from tests.product_entry_cases import entry_status_focus_cases as _entry_status_focus_cases


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_entry_status_focus_cases)


def _ready_doctor_report() -> SimpleNamespace:
    return SimpleNamespace(
        workspace_exists=True,
        runtime_exists=True,
        studies_exists=True,
        portfolio_exists=True,
        med_deepscientist_runtime_exists=True,
        medical_overlay_ready=True,
        external_runtime_contract={"ready": True},
        workspace_domain_route_contract={
            "status": "loaded",
            "loaded": True,
            "summary": "OPL provider/runtime manager workspace supervision 已在线。",
            "drift_reasons": [],
        },
    )


def _ready_supervision() -> dict[str, object]:
    return {
        "manager": "launchd",
        "status": "loaded",
        "loaded": True,
        "job_exists": True,
        "summary": "OPL provider/runtime manager workspace supervision 已在线。",
        "drift_reasons": [],
    }


def _ready_mainline_status() -> dict[str, object]:
    return {
        "program_id": "research-foundry-medical-mainline",
        "current_stage": {
            "id": "paper_readiness_product_entry",
            "status": "in_progress",
            "summary": "Medical Paper Readiness surface 正在接入 product entry。",
        },
    }


def _base_progress_payload(*, study_id: str) -> dict[str, object]:
    return {
        "study_id": study_id,
        "current_stage": "publication_supervision",
        "current_stage_summary": "当前 study 处于医学论文能力闭环监管。",
        "current_blockers": [],
        "next_system_action": "继续观察 readiness surface。",
        "recommended_command": "uv run python -m med_autoscience.cli study progress --study-id " + study_id,
        "supervision": {
            "browser_url": "http://127.0.0.1:20999",
            "quest_session_api_url": "http://127.0.0.1:20999/api/quests/" + study_id + "/session",
            "active_run_id": "run-readiness",
            "health_status": "live",
            "supervisor_tick_status": "fresh",
        },
        "progress_freshness": {"status": "fresh"},
    }


def test_workspace_cockpit_passes_through_medical_paper_readiness_from_study_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    next_action = {
        "action_id": "complete_medical_paper_readiness_surface",
        "surface_key": "literature_scout",
        "summary": "补齐 Literature Scout OS 后再继续自动论文链路。",
    }
    readiness = {
        "surface": "medical_paper_readiness",
        "read_model": "medical_paper_readiness_read_model",
        "authority": "observability_projection_only",
        "overall_status": "blocked",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 2,
        "required_count": 7,
        "next_action": next_action,
        "capability_surfaces": [
            {
                "surface_key": "literature_scout",
                "label": "Literature Scout OS",
                "status": "missing",
                "missing_reason": "missing_canonical_artifact",
                "required_for_ready": True,
            }
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
    markdown = module.render_workspace_cockpit_markdown(payload)

    study_item = payload["studies"][0]
    assert {
        key: study_item["medical_paper_readiness"][key]
        for key in (
            "surface",
            "read_model",
            "authority",
            "overall_status",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
            "ready_count",
            "required_count",
            "next_action",
            "capability_surfaces",
        )
    } == readiness
    assert payload["medical_paper_readiness_state"]["authority"] == "observability_projection_only"
    assert payload["medical_paper_readiness_state"]["counts"]["attention_required"] == 1
    assert payload["medical_paper_readiness_state"]["studies"][0]["overall_status"] == "blocked"
    assert payload["medical_paper_readiness_state"]["studies"][0]["next_action"] == next_action
    action_card = payload["medical_paper_readiness_state"]["studies"][0]["action_cards"][0]
    assert {
        key: action_card[key]
        for key in (
            "action_id",
            "label",
            "summary",
            "surface_key",
            "status",
            "missing_reason",
            "authority",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
        )
    } == {
        "action_id": "complete_literature_scout",
        "label": "补文献",
        "summary": "补齐可审计文献 scout、检索日期、anchor papers、guideline 和近邻文献。",
        "surface_key": "literature_scout",
        "status": "missing",
        "missing_reason": "missing_canonical_artifact",
        "authority": "observability_projection_only",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    assert action_card["guarded_operator_command"]["guard"] == "existing_product_entry_controller_guard"
    assert action_card["authority_contract"]["can_mutate_runtime"] is False
    assert action_card["authority_contract"]["can_authorize_quality"] is False
    attention = [item for item in payload["attention_queue"] if item["code"] == "medical_paper_readiness_gap"]
    assert attention
    assert attention[0]["study_id"] == "001-risk"
    assert attention[0]["medical_paper_readiness"]["quality_claim_authorized"] is False
    assert attention[0]["medical_paper_readiness"]["mechanical_projection_can_authorize_quality"] is False
    assert attention[0]["recommended_step_id"] == "complete_literature_scout"
    assert attention[0]["summary"] == "补齐可审计文献 scout、检索日期、anchor papers、guideline 和近邻文献。"
    assert markdown.strip()


def test_workspace_cockpit_uses_canonical_user_visible_progress_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    progress_payload = {
        **_base_progress_payload(study_id="001-risk"),
        "current_stage": "legacy_stage",
        "current_stage_summary": "legacy summary",
        "current_blockers": ["legacy blocker"],
        "next_system_action": "legacy action",
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "001-risk",
            "writer_state": "parked",
            "user_next": "submit_info",
            "reason": "external_info",
            "details": {"package_delivered": True, "missing_external_info": ["authors"]},
            "conditions": [],
        },
        "user_visible_projection": {
            "surface": "study_progress_user_visible_projection",
            "schema_version": 2,
            "authority": "truth_projection",
            "projection_only": True,
            "study_id": "001-risk",
            "state": "parked/submit_info/external_info",
            "writer_state": "parked",
            "user_next": "submit_info",
            "reason": "external_info",
            "package_delivered": True,
            "actual_write_active": False,
            "user_action_required": True,
            "state_label": "投稿包已交付，等待外部投稿信息",
            "state_summary": "投稿包已交付，系统已自动停驻并释放运行资源；等待补齐外部投稿信息。",
            "current_stage": "parked",
            "current_stage_label": "投稿包已交付，等待外部投稿信息",
            "current_stage_summary": "canonical summary",
            "current_blockers": ["canonical blocker"],
            "next_system_action": "canonical action",
            "evidence": {"latest_events": [], "refs": {}},
            "conditions": [],
        },
    }

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(module.study_progress, "read_study_progress", lambda **kwargs: progress_payload)

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    study = payload["studies"][0]

    assert study["writer_state"] == "parked"
    assert study["user_next"] == "submit_info"
    assert study["package_delivered"] is True
    assert study["actual_write_active"] is False
    assert study["state_label"] == "投稿包已交付，等待外部投稿信息"
    assert study["current_stage"] == "parked"
    assert study["current_stage_summary"] == "canonical summary"
    assert study["current_blockers"] == ["canonical blocker"]
    assert study["next_system_action"] == "canonical action"
    assert payload["workspace_alerts"] == ["canonical blocker"]


def test_workspace_cockpit_builds_medical_paper_readiness_projection_when_progress_lacks_it(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    study_root = write_study(profile.workspace_root, "001-risk")
    built_readiness = {
        "surface": "medical_paper_readiness",
        "overall_status": "missing",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 0,
        "required_count": 7,
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_scout",
            "summary": "补齐 Literature Scout OS 后再继续自动论文链路。",
        },
        "capability_surfaces": [],
    }
    captured_roots: list[Path] = []

    def fake_build_readiness(*, study_root: Path) -> dict[str, object]:
        captured_roots.append(study_root)
        return built_readiness

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(module.medical_paper_readiness, "build_medical_paper_readiness_surface", fake_build_readiness)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: _base_progress_payload(study_id="001-risk"),
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert captured_roots == [study_root]
    assert payload["studies"][0]["medical_paper_readiness"]["overall_status"] == "missing"
    assert payload["studies"][0]["medical_paper_readiness"]["source"] == "read_projection"
    assert payload["studies"][0]["medical_paper_readiness"]["authority"] == "observability_projection_only"
    assert payload["studies"][0]["medical_paper_readiness"]["quality_claim_authorized"] is False
    assert payload["studies"][0]["medical_paper_readiness"]["mechanical_projection_can_authorize_quality"] is False
    assert payload["studies"][0]["medical_paper_readiness"]["action_cards"][0]["label"] == "补文献"
    assert payload["medical_paper_readiness_state"]["status"] == "attention_required"


def test_workspace_cockpit_does_not_emit_action_cards_for_ready_medical_paper_readiness(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = {
        "surface": "medical_paper_readiness",
        "overall_status": "ready",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 7,
        "required_count": 7,
        "next_action": {"action_id": "continue_managed_execution", "summary": "继续托管执行。"},
        "capability_surfaces": [
            {
                "surface_key": "literature_scout",
                "label": "Literature Scout OS",
                "status": "present",
                "required_for_ready": True,
            }
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

    study_readiness = payload["studies"][0]["medical_paper_readiness"]
    assert study_readiness["action_cards"] == []
    attention = [item for item in payload["attention_queue"] if item["code"] == "medical_paper_readiness_gap"]
    assert attention == []
