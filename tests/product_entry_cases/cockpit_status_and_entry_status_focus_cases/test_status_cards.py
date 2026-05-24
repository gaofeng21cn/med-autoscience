from __future__ import annotations

from tests.product_entry_cases import shared as _shared
from tests.product_entry_cases import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
from tests.product_entry_cases import entry_status_focus_cases as _entry_status_focus_cases

_module_reexport(_entry_status_focus_cases)

def test_workspace_cockpit_markdown_prefers_human_facing_labels() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    from opl_harness_shared.status_narration import build_status_narration_contract

    payload = {
        "profile_name": "nf-pitnet",
        "workspace_root": "/tmp/nf-pitnet",
        "workspace_status": "attention_required",
        "mainline_snapshot": {
            "program_id": "mas_runtime",
            "current_stage_id": "publication_supervision",
            "current_stage_summary": "当前主线正在推进投稿收口。",
            "current_program_phase_id": "phase_2",
            "current_program_phase_summary": "当前先保证 workspace truth 与人类查看面对齐。",
            "next_focus": ["优先处理 figure loop。"],
        },
        "workspace_supervision": {
            "summary": "当前需要盯住 runtime 监管与投稿包一致性。",
            "service": {
                "summary": "OPL provider/runtime manager workspace supervision 已在线。",
            },
            "study_counts": {
                "supervisor_gap": 0,
                "recovery_required": 1,
                "quality_blocked": 1,
                "progress_stale": 0,
                "progress_missing": 0,
                "needs_physician_decision": 0,
            },
        },
        "operator_brief": {
            "verdict": "attention_required",
            "summary": "当前有一项 study 需要先处理。",
            "should_intervene_now": True,
            "recommended_step_id": "inspect_study_progress",
            "recommended_command": "uv run python -m med_autoscience.cli study progress --profile profile.local.toml --study-id 001-risk",
            "focus_study_id": "001-risk",
            "current_focus": "先确认 figure loop 已停下。",
            "next_confirmation_signal": "看 checkpoint 是否刷新。",
        },
        "attention_queue": [
            {
                "title": "001-risk figure loop",
                "summary": "图表推进陷入重复打磨循环。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                "operator_status_card": {
                    "handling_state": "paper_surface_refresh_in_progress",
                    "next_confirmation_signal": "看 delivery_manifest 是否刷新。",
                },
            }
        ],
        "user_loop": {
            "open_workspace_cockpit": "uv run python -m med_autoscience.cli workspace cockpit --profile profile.local.toml",
        },
        "phase2_user_product_loop": {
            "summary": "先打开 entry_status，再看 workspace inbox。",
            "recommended_step_id": "open_product_entry",
            "recommended_command": "uv run python -m med_autoscience.cli product entry_status --profile profile.local.toml",
            "operator_questions": [],
        },
        "commands": {
            "doctor": "uv run python -m med_autoscience.cli doctor report --profile profile.local.toml",
        },
        "studies": [
            {
                "study_id": "001-risk",
                "monitoring": {
                    "browser_url": "http://127.0.0.1:21001",
                    "active_run_id": "run-001",
                },
                "current_stage": "publication_supervision",
                "status_narration_contract": build_status_narration_contract(
                    contract_id="study-progress::001-risk",
                    surface_kind="study_progress",
                    stage={
                        "current_stage": "publication_supervision",
                        "recommended_next_stage": "bundle_stage_ready",
                    },
                    current_blockers=["图表推进陷入重复打磨循环。"],
                    latest_update="MAS 正在刷新给人看的投稿包镜像。",
                    next_step="先看 study-progress 与 delivery_manifest 是否对齐。",
                ),
                "task_intake": {
                    "task_intent": "推进 001-risk 到可投稿状态。",
                    "journal_target": "BMC Medicine",
                },
                "progress_freshness": {
                    "summary": "最近 12 小时内仍有明确研究推进记录。",
                },
                "intervention_lane": {
                    "title": "继续监督当前 study",
                    "summary": "当前继续监督即可。",
                },
                "operator_verdict": {
                    "decision_mode": "monitor_only",
                    "summary": "当前继续监督即可。",
                },
                "operator_status_card": {
                    "handling_state": "paper_surface_refresh_in_progress",
                    "user_visible_verdict": "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。",
                    "next_confirmation_signal": "看 delivery_manifest 和 current_package 是否被刷新。",
                },
                "recovery_contract": {
                    "action_mode": "inspect_progress",
                },
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                "current_blockers": ["图表推进陷入重复打磨循环。"],
                "commands": {
                    "launch": "uv run python -m med_autoscience.cli study launch --profile profile.local.toml --study-id 001-risk",
                },
            }
        ],
    }

    markdown = module.render_workspace_cockpit_markdown(payload)

    assert markdown.strip()
    assert "workspace_status:" not in markdown
    assert "program_id:" not in markdown
    assert "summary:" not in markdown
    assert "service:" not in markdown
    assert "counts:" not in markdown
    assert "command:" not in markdown
    assert "handling_state:" not in markdown
    assert "next_signal:" not in markdown
    assert "browser_url:" not in markdown
    assert "task_intent:" not in markdown
    assert "journal_target:" not in markdown
    assert "progress_signal:" not in markdown
    assert "intervention_lane:" not in markdown
    assert "intervention_summary:" not in markdown
    assert "recovery_contract:" not in markdown
    assert "blockers:" not in markdown
    assert "launch:" not in markdown


def test_workspace_cockpit_projects_operator_status_card_into_study_items_and_attention(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

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
            workspace_domain_route_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "OPL provider/runtime manager workspace supervision 已在线。",
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
            "summary": "OPL provider/runtime manager workspace supervision 已在线。",
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
            "current_stage_summary": "论文主线继续推进。",
            "current_blockers": ["study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。"],
            "next_system_action": "继续刷新投稿包镜像。",
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "优先处理人类查看面刷新",
                "severity": "warning",
                "summary": "给人看的投稿包镜像还没追上当前真相。",
                "recommended_action_id": "inspect_progress",
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
                "summary": "给人看的投稿包镜像还没追上当前真相。",
                "reason_summary": "给人看的投稿包镜像还没追上当前真相。",
                "primary_step_id": "inspect_study_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": (
                    "uv run python -m med_autoscience.cli study progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            "operator_status_card": {
                "surface_kind": "study_operator_status_card",
                "handling_state": "paper_surface_refresh_in_progress",
                "owner_summary": "MAS 正在刷新给人看的投稿包镜像。",
                "current_focus": "优先把人类查看面同步到当前论文真相。",
                "latest_truth_time": "2026-04-12T09:30:00+00:00",
                "latest_truth_source": "publication_eval",
                "human_surface_freshness": "stale",
                "next_confirmation_signal": "看 delivery_manifest 和 current_package 是否被刷新。",
                "user_visible_verdict": "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。",
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "quality_floor_blocker",
                "action_mode": "inspect_progress",
                "summary": "给人看的投稿包镜像还没追上当前真相。",
                "recommended_step_id": "inspect_study_progress",
                "steps": [],
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
                "task_intent": "推进 001-risk 到可投稿状态。",
                "journal_target": "BMC Medicine",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
            "artifact_runtime_proof": {
                "surface": "artifact_runtime_proof",
                "rebuild_status": "current",
                "current_package_from_canonical_source": True,
            },
            "submission_hygiene_truth": {
                "surface": "submission_hygiene_truth",
                "status": "clear",
                "blocking_gate_keys": [],
                "gates": {
                    "citation_grounding": {"status": "pass", "blockers": []},
                    "numeric_grounding": {"status": "pass", "blockers": []},
                    "display_grounding": {"status": "pass", "blockers": []},
                    "internal_language_leakage": {"status": "pass", "blockers": []},
                    "artifact_rebuild": {"status": "pass", "blockers": []},
                },
            },
            "product_recommended_flow": {
                "surface": "product_recommended_flow_projection",
                "recommended_step_id": "inspect_study_progress",
                "summary": "投稿卫生 truth 已清晰，继续通过 study-progress 监管 artifact 与质量门控。",
            },
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    markdown = module.render_workspace_cockpit_markdown(payload)

    assert payload["studies"][0]["operator_status_card"]["handling_state"] == "paper_surface_refresh_in_progress"
    assert payload["studies"][0]["artifact_runtime_proof"]["rebuild_status"] == "current"
    assert payload["studies"][0]["submission_hygiene_truth"]["status"] == "clear"
    assert payload["studies"][0]["product_recommended_flow"]["recommended_step_id"] == "inspect_study_progress"
    assert payload["attention_queue"][0]["operator_status_card"]["handling_state"] == "paper_surface_refresh_in_progress"
    assert payload["attention_queue"][0]["summary"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert payload["operator_brief"]["summary"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert markdown.strip()
