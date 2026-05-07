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


def test_workspace_cockpit_projects_gate_clearing_followthrough_into_attention_and_brief(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    followthrough_command = (
        "uv run python -m med_autoscience.cli study-progress --profile "
        + str(profile_ref.resolve())
        + " --study-id 001-risk"
    )
    followthrough_summary = "当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。"
    next_signal = "看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。"

    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_supervision_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "Hermes-hosted runtime supervision 已在线。",
                "drift_reasons": [],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "loaded",
            "loaded": True,
            "job_exists": True,
            "summary": "Hermes-hosted runtime supervision 已在线。",
            "drift_reasons": [],
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "f4_blocker_closeout", "status": "in_progress", "summary": "继续收口 blocker。"},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前进入 controller-owned gate-clearing followthrough。",
            "current_blockers": ["publication gate 还没有重新回写清障结果。"],
            "next_system_action": "等待新的 publication gate 结论。",
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "继续 gate-clearing followthrough",
                "severity": "warning",
                "summary": "当前在等 gate replay 回写。",
            },
            "operator_verdict": {
                "surface_kind": "study_operator_verdict",
                "verdict_id": "study_operator_verdict::001-risk::quality_floor_blocker",
                "study_id": "001-risk",
                "lane_id": "quality_floor_blocker",
                "severity": "warning",
                "decision_mode": "monitor_only",
                "needs_intervention": False,
                "focus_scope": "study",
                "summary": "当前在等 gate replay 回写。",
                "reason_summary": "当前在等 gate replay 回写。",
                "primary_step_id": "inspect_study_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": followthrough_command,
            },
            "operator_status_card": {
                "surface_kind": "study_operator_status_card",
                "handling_state": "monitor_only",
            },
            "recommended_command": followthrough_command,
            "recommended_commands": [],
            "gate_clearing_followthrough": {
                "surface_kind": "gate_clearing_followthrough",
                "state": "waiting_gate_replay",
                "state_label": "等待 gate replay",
                "summary": followthrough_summary,
                "next_confirmation_signal": next_signal,
                "recommended_step_id": "inspect_gate_clearing_followthrough",
                "recommended_command": followthrough_command,
            },
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:20999",
                "quest_session_api_url": "http://127.0.0.1:20999/api/quests/001-risk/session",
                "active_run_id": "run-001",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {
                "task_intent": "推进 001-risk 到重新过 gate。",
                "journal_target": "BMC Medicine",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    markdown = module.render_workspace_cockpit_markdown(payload)

    assert payload["attention_queue"][0]["summary"] == followthrough_summary
    assert payload["attention_queue"][0]["recommended_step_id"] == "inspect_gate_clearing_followthrough"
    assert payload["operator_brief"]["summary"] == followthrough_summary
    assert payload["operator_brief"]["current_focus"] == next_signal
    assert payload["operator_brief"]["recommended_step_id"] == "inspect_gate_clearing_followthrough"
    assert payload["studies"][0]["gate_clearing_followthrough"]["state_label"] == "等待 gate replay"
    assert (
        "gate-clearing 跟进: 等待 gate replay；当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。；看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。"
        in markdown
    )
