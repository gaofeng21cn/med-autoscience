from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)

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
                "summary": "Hermes-hosted runtime supervision 已在线。",
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
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk",
            "focus_study_id": "001-risk",
            "current_focus": "先确认 figure loop 已停下。",
            "next_confirmation_signal": "看 checkpoint 是否刷新。",
        },
        "attention_queue": [
            {
                "title": "001-risk figure loop",
                "summary": "图表推进陷入重复打磨循环。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                "operator_status_card": {
                    "handling_state": "paper_surface_refresh_in_progress",
                    "next_confirmation_signal": "看 delivery_manifest 是否刷新。",
                },
            }
        ],
        "user_loop": {
            "open_workspace_cockpit": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
        },
        "phase2_user_product_loop": {
            "summary": "先打开 frontdesk，再看 workspace inbox。",
            "recommended_step_id": "open_frontdesk",
            "recommended_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
            "operator_questions": [],
        },
        "commands": {
            "doctor": "uv run python -m med_autoscience.cli doctor --profile profile.local.toml",
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
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                "current_blockers": ["图表推进陷入重复打磨循环。"],
                "commands": {
                    "launch": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml --study-id 001-risk",
                },
            }
        ],
    }

    markdown = module.render_workspace_cockpit_markdown(payload)

    assert "当前 workspace 状态" in markdown
    assert "当前 program" in markdown
    assert "当前监管摘要" in markdown
    assert "当前关注项" in markdown
    assert "处理命令" in markdown
    assert "浏览器入口" in markdown
    assert "当前任务意图" in markdown
    assert "当前投稿目标" in markdown
    assert "进度信号" in markdown
    assert "当前介入通道" in markdown
    assert "当前介入摘要" in markdown
    assert "恢复建议" in markdown
    assert "当前卡点" in markdown
    assert "启动命令" in markdown
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
                    "uv run python -m med_autoscience.cli study-progress --profile "
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
                "uv run python -m med_autoscience.cli study-progress --profile "
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
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    markdown = module.render_workspace_cockpit_markdown(payload)

    assert payload["studies"][0]["operator_status_card"]["handling_state"] == "paper_surface_refresh_in_progress"
    assert payload["attention_queue"][0]["operator_status_card"]["handling_state"] == "paper_surface_refresh_in_progress"
    assert payload["attention_queue"][0]["summary"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert payload["operator_brief"]["summary"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert "人类查看面刷新中" in markdown


def test_workspace_cockpit_projects_quality_execution_lane_into_attention_and_brief(
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
            "current_stage_summary": "当前还在同线质量修复。",
            "current_blockers": ["当前稿面仍需最小 claim-evidence 修复。"],
            "next_system_action": "继续当前质量修复。",
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "优先处理 claim-evidence 修复",
                "severity": "warning",
                "summary": "当前稿面仍需最小 claim-evidence 修复。",
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
                "summary": "当前稿面仍需最小 claim-evidence 修复。",
                "reason_summary": "当前稿面仍需最小 claim-evidence 修复。",
                "primary_step_id": "inspect_study_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            "operator_status_card": {
                "surface_kind": "study_operator_status_card",
                "handling_state": "scientific_or_quality_repair_in_progress",
                "owner_summary": "MAS 正在处理当前论文线的质量修复。",
                "latest_truth_time": "2026-04-12T09:30:00+00:00",
                "latest_truth_source": "publication_eval",
                "human_surface_freshness": "fresh",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否继续收窄当前修复线。",
                "user_visible_verdict": "MAS 正在处理当前论文线的质量修复。",
            },
            "quality_closure_truth": {
                "summary": "核心科学质量还没有闭环；当前仍需先补齐论文质量缺口。",
            },
            "quality_execution_lane": {
                "lane_id": "claim_evidence",
                "route_key_question": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。",
            },
            "same_line_route_truth": {
                "surface_kind": "same_line_route_truth",
                "same_line_state": "bounded_analysis",
                "same_line_state_label": "有限补充分析",
                "route_mode": "enter",
                "route_target": "analysis-campaign",
                "route_target_label": "补充分析与稳健性验证",
                "summary": "当前论文线仍在同线质量修复；先进入 analysis-campaign 收口当前最窄 claim-evidence 缺口。",
                "current_focus": "当前稿面最窄的 claim-evidence 修复动作是什么？",
            },
            "research_runtime_control_projection": {
                "surface_kind": "research_runtime_control_projection",
                "restore_point_surface": {
                    "surface_kind": "study_progress",
                    "field_path": "autonomy_contract.restore_point",
                },
                "research_gate_surface": {
                    "surface_kind": "study_progress",
                    "approval_gate_field": "needs_physician_decision",
                    "interrupt_policy_field": "intervention_lane.recommended_action_id",
                },
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "quality_floor_blocker",
                "action_mode": "inspect_progress",
                "summary": "当前稿面仍需最小 claim-evidence 修复。",
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
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert payload["attention_queue"][0]["recommended_step_id"] == "inspect_study_progress"
    assert payload["operator_brief"]["recommended_step_id"] == "inspect_study_progress"
    assert payload["attention_queue"][0]["quality_execution_lane"]["route_key_question"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"
    assert payload["attention_queue"][0]["same_line_route_truth"]["route_target"] == "analysis-campaign"
    assert payload["studies"][0]["research_runtime_control_projection"]["research_gate_surface"]["approval_gate_field"] == (
        "needs_physician_decision"
    )
    assert payload["operator_brief"]["current_focus"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"


def test_workspace_cockpit_projects_autonomy_soak_and_quality_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_workspace_cockpit_markdown(
        {
            "profile_name": "test-profile",
            "workspace_root": "/tmp/test",
            "workspace_status": "ready",
            "workspace_supervision": {"service": {}, "study_counts": {}},
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "monitor_only",
                "summary": "当前没有新的 workspace 级硬告警。",
                "should_intervene_now": False,
                "focus_scope": "study",
                "focus_study_id": "001-risk",
                "recommended_step_id": "inspect_progress",
                "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                "current_focus": "看 publication_eval/latest.json 是否出现新的复评结论。",
            },
            "attention_queue": [
                {
                    "title": "001-risk 当前处在等待系统自动复评",
                    "summary": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
                    "recommended_step_id": "inspect_study_progress",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "autonomy_soak_status": {
                        "summary": "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。",
                    },
                    "quality_review_loop": {
                        "current_phase_label": "等待复评",
                        "recommended_next_phase_label": "发起复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                    },
                    "quality_review_followthrough": {
                        "state_label": "等待复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review。",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论。",
                    },
                }
            ],
            "user_loop": {},
            "phase2_user_product_loop": {},
            "commands": {},
            "studies": [],
        }
    )

    assert "自治 Proof / Soak: 最近一次自治外环已转到“论文写作与结果收紧”" in markdown
    assert "质量复评跟进: 等待复评；当前修订计划已完成，下一步应由 MAS 发起 re-review。；看 publication_eval/latest.json 是否出现新的复评结论。" in markdown


def test_workspace_cockpit_attention_queue_carries_runtime_control_pickup_and_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    payload = {
        "attention_queue": module._attention_queue(
            workspace_status="ready",
            workspace_supervision={"service": {"loaded": True}, "study_counts": {}},
            commands={},
            studies=[
                {
                "study_id": "001-risk",
                "current_stage": "runtime_soak",
                "current_stage_summary": "runtime soak 正在等待 artifact pickup 与 human gate 确认。",
                "current_blockers": ["需要人工确认后恢复。"],
                "next_system_action": "等待 human gate。",
                "intervention_lane": {
                    "lane_id": "wait_for_user",
                    "recommended_action_id": "human_gate",
                    "summary": "恢复前需要人工确认。",
                },
                "operator_status_card": {
                    "surface_kind": "study_operator_status_card",
                    "handling_state": "waiting_for_human_gate",
                    "user_visible_verdict": "恢复点已冻结；等待人工确认。",
                    "current_focus": "确认是否从冻结恢复点继续。",
                    "next_confirmation_signal": "人工批准后再恢复 runtime。",
                },
                "autonomy_contract": {
                    "summary": "当前自治状态停在 human gate。",
                    "restore_point": {
                        "summary": "恢复点已冻结；恢复前仍需人工确认。",
                        "human_gate_required": True,
                    },
                },
                "autonomy_soak_status": {
                    "summary": "最近一次自治外环已完成 soak dispatch。",
                    "next_confirmation_signal": "看 runtime_watch 是否刷新。",
                },
                "quality_closure_truth": {"summary": "质量闭环已进入 bundle-only 收口。"},
                "quality_review_followthrough": {
                    "summary": "复评已完成，等待 pickup。",
                    "next_confirmation_signal": "看 publication_eval/latest.json。",
                },
                "research_runtime_control_projection": {
                    "surface_kind": "research_runtime_control_projection",
                    "restore_point_surface": {
                        "surface_kind": "study_progress",
                        "field_path": "autonomy_contract.restore_point",
                        "summary": "恢复点已冻结；恢复前仍需人工确认。",
                    },
                    "artifact_pickup_surface": {
                        "surface_kind": "study_progress",
                        "field_path": "refs.evaluation_summary_path",
                        "pickup_refs": [
                            {
                                "ref_id": "publication_eval_path",
                                "path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
                            }
                        ],
                    },
                    "research_gate_surface": {
                        "surface_kind": "study_progress",
                        "approval_gate_field": "needs_physician_decision",
                        "approval_gate_required": True,
                        "approval_gate_owner": "mas_controller",
                        "interrupt_policy_field": "intervention_lane.recommended_action_id",
                        "interrupt_policy": "human_gate",
                    },
                },
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                "recommended_commands": [],
                "recovery_contract": {
                    "contract_kind": "study_recovery_contract",
                    "lane_id": "wait_for_user",
                    "action_mode": "monitor_only",
                    "summary": "等待 human gate。",
                    "recommended_step_id": "inspect_study_progress",
                    "steps": [],
                },
                "needs_physician_decision": True,
                "supervision": {},
                "task_intake": {},
                "progress_freshness": {"status": "fresh"},
                }
            ],
        ),
    }
    payload["operator_brief"] = module._workspace_operator_brief(
        workspace_status="ready",
        workspace_alerts=[],
        attention_queue=payload["attention_queue"],
        studies=[],
        user_loop={},
        commands={},
    )

    attention_item = payload["attention_queue"][0]
    assert attention_item["research_runtime_control_projection"]["restore_point_surface"]["field_path"] == (
        "autonomy_contract.restore_point"
    )
    assert attention_item["research_runtime_control_projection"]["artifact_pickup_surface"]["pickup_refs"] == [
        {
            "ref_id": "publication_eval_path",
            "path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
        }
    ]
    assert attention_item["research_runtime_control_projection"]["research_gate_surface"]["approval_gate_required"] is True
    assert (
        payload["operator_brief"]["research_runtime_control_projection"]["research_gate_surface"]["interrupt_policy"]
        == "human_gate"
    )


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


def test_build_product_frontdesk_uses_operator_status_card_for_now_summary(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(
        module,
        "build_product_entry_manifest",
        lambda **kwargs: {
            "surface_kind": "product_entry_manifest",
            "manifest_version": 2,
            "manifest_kind": "med_autoscience_product_entry_manifest",
            "target_domain_id": "med-autoscience",
            "formal_entry": {
                "default": "CLI",
                "supported_protocols": ["MCP"],
                "internal_surface": "controller",
            },
            "workspace_locator": {"profile_name": "test-profile"},
            "product_entry_shell": {
                "product_frontdesk": {
                    "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                    "surface_kind": "product_frontdesk",
                },
                "workspace_cockpit": {
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                    "surface_kind": "workspace_cockpit",
                },
                "submit_study_task": {
                    "command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml",
                    "surface_kind": "study_task_intake",
                },
                "launch_study": {
                    "command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml",
                    "surface_kind": "launch_study",
                },
                "study_progress": {
                    "command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml",
                    "surface_kind": "study_progress",
                },
                "mainline_status": {
                    "command": "uv run python -m med_autoscience.cli mainline-status",
                    "surface_kind": "mainline_status",
                },
                "mainline_phase": {
                    "command": "uv run python -m med_autoscience.cli mainline-phase",
                    "surface_kind": "mainline_phase",
                },
            },
            "shared_handoff": {
                "direct_entry_builder": {
                    "command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct",
                    "entry_mode": "direct",
                }
            },
            "runtime": {"runtime_owner": "upstream_hermes_agent"},
            "product_entry_status": {"summary": "test status"},
            "frontdesk_surface": {
                "surface_kind": "product_frontdesk",
                "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "summary": "open frontdesk",
            },
            "operator_loop_surface": {
                "surface_kind": "workspace_cockpit",
                "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "summary": "open workspace cockpit",
            },
            "operator_loop_actions": {},
            "product_entry_start": {
                "surface_kind": "product_entry_start",
                "summary": "open frontdesk first",
                "recommended_mode_id": "open_frontdesk",
                "modes": [
                    {
                        "mode_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_surface": {
                    "surface_kind": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                    "session_locator_field": "profile_name",
                },
                "human_gate_ids": ["workspace_gate"],
            },
            "product_entry_overview": {
                "surface_kind": "product_entry_overview",
                "summary": "workspace overview",
                "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "progress_surface": {
                    "surface_kind": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                },
                "resume_surface": {
                    "surface_kind": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                    "session_locator_field": "profile_name",
                },
                "recommended_step_id": "open_frontdesk",
                "next_focus": ["open workspace cockpit"],
                "remaining_gaps_count": 0,
                "human_gate_ids": ["workspace_gate"],
            },
            "domain_entry_contract": {
                "entry_adapter": "MedAutoScienceDomainEntry",
                "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry",
                "product_entry_builder_command": "build-product-entry",
                "supported_commands": ["workspace-cockpit"],
                "command_contracts": [
                    {"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}
                ],
            },
            "gateway_interaction_contract": {
                "surface_kind": "gateway_interaction_contract",
                "frontdoor_owner": "opl_gateway_or_domain_gui",
                "user_interaction_mode": "natural_language_frontdoor",
                "user_commands_required": False,
                "command_surfaces_for_agent_consumption_only": True,
                "shared_downstream_entry": "MedAutoScienceDomainEntry",
                "shared_handoff_envelope": ["target_domain_id"],
            },
            "product_entry_preflight": {
                "surface_kind": "product_entry_preflight",
                "summary": "preflight ready",
                "ready_to_try_now": True,
                "recommended_check_command": "uv run python -m med_autoscience.cli doctor",
                "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "blocking_check_ids": [],
                "checks": [],
            },
            "product_entry_readiness": {
                "surface_kind": "product_entry_readiness",
                "verdict": "ready_for_task",
                "usable_now": True,
                "good_to_use_now": True,
                "fully_automatic": False,
                "summary": "workspace ready",
                "recommended_start_surface": "product_frontdesk",
                "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "recommended_loop_surface": "workspace_cockpit",
                "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "blocking_gaps": [],
            },
            "product_entry_quickstart": {
                "surface_kind": "product_entry_quickstart",
                "recommended_step_id": "open_frontdesk",
                "summary": "open frontdesk first",
                "steps": [
                    {
                        "step_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_contract": {
                    "surface_kind": "workspace_cockpit",
                    "session_locator_field": "profile_name",
                },
                "human_gate_ids": ["workspace_gate"],
            },
            "family_orchestration": {
                "human_gates": [{"gate_id": "workspace_gate"}],
                "resume_contract": {
                    "surface_kind": "workspace_cockpit",
                    "session_locator_field": "profile_name",
                },
            },
            "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
            "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            "summary": {
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"
            },
        },
    )
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "attention_required",
                "summary": "generic summary",
                "should_intervene_now": True,
                "focus_scope": "study",
                "focus_study_id": "001-risk",
                "recommended_step_id": "handle_attention_item",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
            },
            "attention_queue": [
                {
                    "scope": "study",
                    "study_id": "001-risk",
                    "code": "study_quality_floor_blocker",
                    "title": "001-risk 当前需要刷新投稿包镜像",
                    "summary": "generic summary",
                    "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                    "operator_status_card": {
                        "surface_kind": "study_operator_status_card",
                        "handling_state": "paper_surface_refresh_in_progress",
                        "current_focus": "优先同步投稿包镜像。",
                        "next_confirmation_signal": "看 delivery_manifest 和 current_package 是否被刷新。",
                        "user_visible_verdict": "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。",
                    },
                }
            ],
        },
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
    markdown = module.render_product_frontdesk_markdown(payload)

    assert payload["operator_brief"]["summary"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert payload["operator_brief"]["focus_study_id"] == "001-risk"
    assert "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。" in markdown


def test_build_product_frontdesk_uses_same_line_route_truth_for_current_focus(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(
        module,
        "build_product_entry_manifest",
        lambda **kwargs: {
            "surface_kind": "product_entry_manifest",
            "manifest_version": 2,
            "manifest_kind": "med_autoscience_product_entry_manifest",
            "target_domain_id": "med-autoscience",
            "formal_entry": {"default": "CLI", "supported_protocols": ["MCP"], "internal_surface": "controller"},
            "workspace_locator": {"profile_name": "test-profile"},
            "product_entry_shell": {
                "product_frontdesk": {"command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk"},
                "workspace_cockpit": {"command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "surface_kind": "workspace_cockpit"},
                "submit_study_task": {"command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml", "surface_kind": "study_task_intake"},
                "launch_study": {"command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml", "surface_kind": "launch_study"},
                "study_progress": {"command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml", "surface_kind": "study_progress"},
                "mainline_status": {"command": "uv run python -m med_autoscience.cli mainline-status", "surface_kind": "mainline_status"},
                "mainline_phase": {"command": "uv run python -m med_autoscience.cli mainline-phase", "surface_kind": "mainline_phase"},
            },
            "shared_handoff": {"direct_entry_builder": {"command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct", "entry_mode": "direct"}},
            "runtime": {"runtime_owner": "upstream_hermes_agent"},
            "product_entry_status": {"summary": "test status"},
            "frontdesk_surface": {"surface_kind": "product_frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "summary": "open frontdesk"},
            "operator_loop_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "summary": "open workspace cockpit"},
            "operator_loop_actions": {},
            "product_entry_start": {
                "surface_kind": "product_entry_start",
                "summary": "open frontdesk first",
                "recommended_mode_id": "open_frontdesk",
                "modes": [
                    {
                        "mode_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"},
                "human_gate_ids": ["workspace_gate"],
            },
            "product_entry_overview": {"surface_kind": "product_entry_overview", "summary": "workspace overview", "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "progress_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"}, "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "recommended_step_id": "open_frontdesk", "next_focus": ["open workspace cockpit"], "remaining_gaps_count": 0, "human_gate_ids": ["workspace_gate"]},
            "domain_entry_contract": {"entry_adapter": "MedAutoScienceDomainEntry", "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry", "product_entry_builder_command": "build-product-entry", "supported_commands": ["workspace-cockpit"], "command_contracts": [{"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}]},
            "gateway_interaction_contract": {"surface_kind": "gateway_interaction_contract", "frontdoor_owner": "opl_gateway_or_domain_gui", "user_interaction_mode": "natural_language_frontdoor", "user_commands_required": False, "command_surfaces_for_agent_consumption_only": True, "shared_downstream_entry": "MedAutoScienceDomainEntry", "shared_handoff_envelope": ["target_domain_id"]},
            "product_entry_preflight": {"surface_kind": "product_entry_preflight", "summary": "preflight ready", "ready_to_try_now": True, "recommended_check_command": "uv run python -m med_autoscience.cli doctor", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "blocking_check_ids": [], "checks": []},
            "product_entry_readiness": {"surface_kind": "product_entry_readiness", "verdict": "ready_for_task", "usable_now": True, "good_to_use_now": True, "fully_automatic": False, "summary": "workspace ready", "recommended_start_surface": "product_frontdesk", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_loop_surface": "workspace_cockpit", "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "blocking_gaps": []},
            "product_entry_quickstart": {
                "surface_kind": "product_entry_quickstart",
                "recommended_step_id": "open_frontdesk",
                "summary": "open frontdesk first",
                "steps": [
                    {
                        "step_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"},
                "human_gate_ids": ["workspace_gate"],
            },
            "family_orchestration": {"human_gates": [{"gate_id": "workspace_gate"}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}},
            "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
            "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            "summary": {"recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"},
        },
    )
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "attention_required",
                "summary": "当前 workspace 有关注项。",
                "should_intervene_now": True,
                "focus_scope": "study",
                "focus_study_id": "001-risk",
                "recommended_step_id": "handle_attention_item",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
            },
            "attention_queue": [
                {
                    "scope": "study",
                    "study_id": "001-risk",
                    "code": "study_quality_floor_blocker",
                    "title": "001-risk 当前先做 claim-evidence 修复",
                    "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。",
                    "recommended_step_id": "inspect_study_progress",
                    "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                    "operator_status_card": {
                        "surface_kind": "study_operator_status_card",
                        "handling_state": "scientific_or_quality_repair_in_progress",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否继续收窄当前修复线。",
                        "user_visible_verdict": "MAS 正在处理当前论文线的质量修复。",
                    },
                    "same_line_route_truth": {
                        "surface_kind": "same_line_route_truth",
                        "same_line_state": "bounded_analysis",
                        "same_line_state_label": "有限补充分析",
                        "route_mode": "enter",
                        "route_target": "analysis-campaign",
                        "route_target_label": "补充分析与稳健性验证",
                        "summary": "当前论文线仍在同线质量修复；先进入 analysis-campaign 收口当前最窄 claim-evidence 缺口。",
                        "current_focus": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                    },
                }
            ],
        },
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["operator_brief"]["recommended_step_id"] == "inspect_study_progress"
    assert payload["operator_brief"]["current_focus"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"


def test_build_product_frontdesk_uses_quality_review_followthrough_for_monitor_focus(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(module, "build_product_entry_manifest", lambda **kwargs: {
        "surface_kind": "product_entry_manifest",
        "manifest_version": 2,
        "manifest_kind": "med_autoscience_product_entry_manifest",
        "target_domain_id": "med-autoscience",
        "formal_entry": {"default": "CLI", "supported_protocols": ["MCP"], "internal_surface": "controller"},
        "workspace_locator": {"profile_name": "test-profile"},
        "product_entry_shell": {
            "product_frontdesk": {"command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk"},
            "workspace_cockpit": {"command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "surface_kind": "workspace_cockpit"},
            "submit_study_task": {"command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml", "surface_kind": "study_task_intake"},
            "launch_study": {"command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml", "surface_kind": "launch_study"},
            "study_progress": {"command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml", "surface_kind": "study_progress"},
            "mainline_status": {"command": "uv run python -m med_autoscience.cli mainline-status", "surface_kind": "mainline_status"},
            "mainline_phase": {"command": "uv run python -m med_autoscience.cli mainline-phase", "surface_kind": "mainline_phase"},
        },
        "shared_handoff": {"direct_entry_builder": {"command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct", "entry_mode": "direct"}},
        "runtime": {"runtime_owner": "upstream_hermes_agent"},
        "product_entry_status": {"summary": "test status"},
        "frontdesk_surface": {"surface_kind": "product_frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "summary": "open frontdesk"},
        "operator_loop_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "summary": "open workspace cockpit"},
        "operator_loop_actions": {},
        "product_entry_start": {"surface_kind": "product_entry_start", "summary": "open frontdesk first", "recommended_mode_id": "open_frontdesk", "modes": [{"mode_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "product_entry_overview": {"surface_kind": "product_entry_overview", "summary": "workspace overview", "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "progress_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"}, "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "recommended_step_id": "open_frontdesk", "next_focus": ["open workspace cockpit"], "remaining_gaps_count": 0, "human_gate_ids": ["workspace_gate"]},
        "domain_entry_contract": {"entry_adapter": "MedAutoScienceDomainEntry", "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry", "product_entry_builder_command": "build-product-entry", "supported_commands": ["workspace-cockpit"], "command_contracts": [{"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}]},
        "gateway_interaction_contract": {"surface_kind": "gateway_interaction_contract", "frontdoor_owner": "opl_gateway_or_domain_gui", "user_interaction_mode": "natural_language_frontdoor", "user_commands_required": False, "command_surfaces_for_agent_consumption_only": True, "shared_downstream_entry": "MedAutoScienceDomainEntry", "shared_handoff_envelope": ["target_domain_id"]},
        "product_entry_preflight": {"surface_kind": "product_entry_preflight", "summary": "preflight ready", "ready_to_try_now": True, "recommended_check_command": "uv run python -m med_autoscience.cli doctor", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "blocking_check_ids": [], "checks": []},
        "product_entry_readiness": {"surface_kind": "product_entry_readiness", "verdict": "ready_for_task", "usable_now": True, "good_to_use_now": True, "fully_automatic": False, "summary": "workspace ready", "recommended_start_surface": "product_frontdesk", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_loop_surface": "workspace_cockpit", "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "blocking_gaps": []},
        "product_entry_quickstart": {"surface_kind": "product_entry_quickstart", "recommended_step_id": "open_frontdesk", "summary": "open frontdesk first", "steps": [{"step_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "family_orchestration": {"human_gates": [{"gate_id": "workspace_gate"}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}},
        "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
        "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
        "summary": {"recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"},
        "single_project_boundary": {"surface_kind": "single_project_boundary", "summary": "summary", "mas_owner_modules": ["controller_charter"], "mds_retained_roles": [{"role_id": "research_backend", "title": "Controlled research backend", "summary": "summary"}], "post_gate_only": ["physical monorepo absorb"], "not_now": ["not now"]},
    })
    monkeypatch.setattr(module, "read_workspace_cockpit", lambda **kwargs: {
        "operator_brief": {
            "surface_kind": "workspace_operator_brief",
            "verdict": "monitor_only",
            "summary": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
            "should_intervene_now": False,
            "focus_scope": "study",
            "focus_study_id": "001-risk",
            "recommended_step_id": "inspect_study_progress",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk",
            "current_focus": "看 publication_eval/latest.json 是否出现新的复评结论。",
        },
        "attention_queue": [],
    })

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["operator_brief"]["recommended_step_id"] == "open_workspace_cockpit"
    assert payload["operator_brief"]["current_focus"] == "看 publication_eval/latest.json 是否出现新的复评结论。"


def test_build_product_frontdesk_uses_gate_clearing_followthrough_for_attention_brief(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    followthrough_command = (
        "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk"
    )
    followthrough_summary = "当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。"
    next_signal = "看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。"

    monkeypatch.setattr(module, "build_product_entry_manifest", lambda **kwargs: {
        "surface_kind": "product_entry_manifest",
        "manifest_version": 2,
        "manifest_kind": "med_autoscience_product_entry_manifest",
        "target_domain_id": "med-autoscience",
        "formal_entry": {"default": "CLI", "supported_protocols": ["MCP"], "internal_surface": "controller"},
        "workspace_locator": {"profile_name": "test-profile"},
        "product_entry_shell": {
            "product_frontdesk": {"command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk"},
            "workspace_cockpit": {"command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "surface_kind": "workspace_cockpit"},
            "submit_study_task": {"command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml", "surface_kind": "study_task_intake"},
            "launch_study": {"command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml", "surface_kind": "launch_study"},
            "study_progress": {"command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml", "surface_kind": "study_progress"},
            "mainline_status": {"command": "uv run python -m med_autoscience.cli mainline-status", "surface_kind": "mainline_status"},
            "mainline_phase": {"command": "uv run python -m med_autoscience.cli mainline-phase", "surface_kind": "mainline_phase"},
        },
        "shared_handoff": {"direct_entry_builder": {"command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct", "entry_mode": "direct"}},
        "runtime": {"runtime_owner": "upstream_hermes_agent"},
        "product_entry_status": {"summary": "test status"},
        "frontdesk_surface": {"surface_kind": "product_frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "summary": "open frontdesk"},
        "operator_loop_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "summary": "open workspace cockpit"},
        "operator_loop_actions": {},
        "product_entry_start": {"surface_kind": "product_entry_start", "summary": "open frontdesk first", "recommended_mode_id": "open_frontdesk", "modes": [{"mode_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "product_entry_overview": {"surface_kind": "product_entry_overview", "summary": "workspace overview", "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "progress_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"}, "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "recommended_step_id": "open_frontdesk", "next_focus": ["open workspace cockpit"], "remaining_gaps_count": 0, "human_gate_ids": ["workspace_gate"]},
        "domain_entry_contract": {"entry_adapter": "MedAutoScienceDomainEntry", "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry", "product_entry_builder_command": "build-product-entry", "supported_commands": ["workspace-cockpit"], "command_contracts": [{"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}]},
        "gateway_interaction_contract": {"surface_kind": "gateway_interaction_contract", "frontdoor_owner": "opl_gateway_or_domain_gui", "user_interaction_mode": "natural_language_frontdoor", "user_commands_required": False, "command_surfaces_for_agent_consumption_only": True, "shared_downstream_entry": "MedAutoScienceDomainEntry", "shared_handoff_envelope": ["target_domain_id"]},
        "product_entry_preflight": {"surface_kind": "product_entry_preflight", "summary": "preflight ready", "ready_to_try_now": True, "recommended_check_command": "uv run python -m med_autoscience.cli doctor", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "blocking_check_ids": [], "checks": []},
        "product_entry_readiness": {"surface_kind": "product_entry_readiness", "verdict": "ready_for_task", "usable_now": True, "good_to_use_now": True, "fully_automatic": False, "summary": "workspace ready", "recommended_start_surface": "product_frontdesk", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_loop_surface": "workspace_cockpit", "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "blocking_gaps": []},
        "product_entry_quickstart": {"surface_kind": "product_entry_quickstart", "recommended_step_id": "open_frontdesk", "summary": "open frontdesk first", "steps": [{"step_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "family_orchestration": {"human_gates": [{"gate_id": "workspace_gate"}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}},
        "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
        "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
        "summary": {"recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"},
        "single_project_boundary": {"surface_kind": "single_project_boundary", "summary": "summary", "mas_owner_modules": ["controller_charter"], "mds_retained_roles": [{"role_id": "research_backend", "title": "Controlled research backend", "summary": "summary"}], "post_gate_only": ["physical monorepo absorb"], "not_now": ["not now"]},
    })
    monkeypatch.setattr(module, "read_workspace_cockpit", lambda **kwargs: {
        "operator_brief": {
            "surface_kind": "workspace_operator_brief",
            "verdict": "attention_required",
            "summary": followthrough_summary,
            "should_intervene_now": True,
            "focus_scope": "study",
            "focus_study_id": "001-risk",
            "recommended_step_id": "inspect_gate_clearing_followthrough",
            "recommended_command": followthrough_command,
            "current_focus": next_signal,
        },
        "attention_queue": [
            {
                "study_id": "001-risk",
                "code": "study_quality_floor_blocker",
                "title": "001-risk 当前进入 gate-clearing followthrough",
                "summary": followthrough_summary,
                "recommended_step_id": "inspect_gate_clearing_followthrough",
                "recommended_command": followthrough_command,
                "operator_status_card": {
                    "handling_state": "monitor_only",
                },
                "gate_clearing_followthrough": {
                    "surface_kind": "gate_clearing_followthrough",
                    "state": "waiting_gate_replay",
                    "state_label": "等待 gate replay",
                    "summary": followthrough_summary,
                    "next_confirmation_signal": next_signal,
                    "recommended_step_id": "inspect_gate_clearing_followthrough",
                    "recommended_command": followthrough_command,
                },
            }
        ],
    })

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["operator_brief"]["summary"] == followthrough_summary
    assert payload["operator_brief"]["recommended_step_id"] == "inspect_gate_clearing_followthrough"
    assert payload["operator_brief"]["recommended_command"] == followthrough_command
    assert payload["operator_brief"]["current_focus"] == next_signal
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
