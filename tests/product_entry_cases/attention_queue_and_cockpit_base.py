from __future__ import annotations

from . import shared as _shared

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)

def test_attention_queue_prefers_route_repair_focus_for_quality_blockers() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    queue = module._attention_queue(
        workspace_status="ready",
        workspace_supervision={
            "service": {"loaded": True, "drift_reasons": []},
            "study_counts": {},
        },
        studies=[
            {
                "study_id": "001-risk",
                "monitoring": {"supervisor_tick_status": "fresh"},
                "progress_freshness": {"status": "fresh"},
                "current_stage_summary": "论文可发表性监管。",
                "next_system_action": "继续当前质量修复。",
                "current_blockers": ["论文叙事或方法/结果书写面仍有硬阻塞。"],
                "intervention_lane": {
                    "lane_id": "quality_floor_blocker",
                    "repair_mode": "same_line_route_back",
                    "route_target_label": "论文写作与结果收紧",
                    "route_summary": "回到“论文写作与结果收紧”，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。",
                },
                "operator_verdict": {
                    "summary": "generic quality summary",
                    "primary_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                },
                "operator_status_card": {
                    "user_visible_verdict": "MAS 正在处理论文可发表性硬阻塞。",
                },
                "quality_closure_truth": {
                    "summary": "核心科学质量还没有闭环；当前仍需先补齐论文质量缺口。",
                },
                "quality_execution_lane": {
                    "lane_id": "claim_evidence",
                    "route_key_question": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                    "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。",
                },
                "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_quality_floor_blocker"
    assert queue[0]["title"] == "001-risk 当前需要回到论文写作与结果收紧修复质量阻塞"
    assert (
        queue[0]["summary"]
        == "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。"
    )
    assert queue[0]["quality_closure_truth"]["summary"] == "核心科学质量还没有闭环；当前仍需先补齐论文质量缺口。"
    assert queue[0]["quality_execution_lane"]["route_key_question"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"


def test_attention_queue_uses_quality_execution_lane_for_generic_study_blocked() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    queue = module._attention_queue(
        workspace_status="attention_required",
        workspace_supervision={
            "service": {"loaded": True, "drift_reasons": []},
            "study_counts": {},
        },
        studies=[
            {
                "study_id": "001-risk",
                "monitoring": {"supervisor_tick_status": "fresh"},
                "progress_freshness": {"status": "fresh"},
                "current_stage_summary": "当前先做 finalize 收口。",
                "next_system_action": "继续当前论文线。",
                "current_blockers": ["当前论文线仍有 finalize / bundle 收口项。"],
                "intervention_lane": {"lane_id": "monitor_only"},
                "operator_verdict": {
                    "summary": "generic summary",
                    "primary_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                },
                "operator_status_card": {},
                "same_line_route_truth": {
                    "surface_kind": "same_line_route_truth",
                    "same_line_state": "finalize_only_remaining",
                    "same_line_state_label": "同线定稿与投稿包收尾",
                    "route_mode": "return",
                    "route_target": "finalize",
                    "route_target_label": "定稿与投稿收尾",
                    "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
                    "current_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                },
                "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_blocked"
    assert queue[0]["title"] == "001-risk 当前已进入同线定稿与投稿包收尾"
    assert (
        queue[0]["summary"]
        == "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。"
    )


def test_attention_queue_projects_manual_finishing_without_generic_blocker_wording() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    queue = module._attention_queue(
        workspace_status="attention_required",
        workspace_supervision={
            "service": {"loaded": True, "drift_reasons": []},
            "study_counts": {},
        },
        studies=[
            {
                "study_id": "001-risk",
                "monitoring": {"supervisor_tick_status": "fresh"},
                "progress_freshness": {"status": "fresh"},
                "current_stage_summary": "当前 study 已停在投稿包里程碑保护。",
                "next_system_action": "继续保持兼容性与监督入口；如需继续，显式恢复同一论文线。",
                "current_blockers": ["当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。"],
                "intervention_lane": {
                    "lane_id": "manual_finishing",
                    "title": "保持人工收尾兼容保护",
                    "severity": "observe",
                    "summary": "投稿包里程碑已达成；MAS 只保持人工收尾兼容保护和监督入口。",
                    "recommended_action_id": "maintain_compatibility_guard",
                },
                "operator_verdict": {
                    "summary": "旧的阻塞摘要不应覆盖人工收尾语义。",
                    "primary_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                },
                "operator_status_card": {
                    "handling_state": "manual_finishing",
                    "handling_state_label": "人工收尾兼容保护",
                    "user_visible_verdict": "MAS 当前保持人工收尾兼容保护，并继续提供监督入口。",
                    "current_focus": "继续保持人工收尾兼容保护，不把投稿包里程碑 parked 解释为 runtime failure。",
                    "next_confirmation_signal": "看人工收尾是否写出新的明确结论，或兼容保护是否仍然保持 active。",
                },
                "autonomy_contract": {
                    "autonomy_state": "compatibility_guard",
                    "summary": "投稿包里程碑已达成；MAS 只保持人工收尾兼容保护和监督入口。",
                },
                "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_manual_finishing"
    assert queue[0]["title"] == "001-risk 当前保持人工收尾兼容保护"
    assert queue[0]["summary"] == "投稿包里程碑已达成；MAS 只保持人工收尾兼容保护和监督入口。"
    assert queue[0]["recommended_step_id"] == "inspect_study_progress"
    assert queue[0]["operator_status_card"]["handling_state"] == "manual_finishing"


def test_attention_queue_prefers_autonomy_contract_summary_for_runtime_recovery() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    queue = module._attention_queue(
        workspace_status="ready",
        workspace_supervision={
            "service": {"loaded": True, "drift_reasons": []},
            "study_counts": {},
        },
        studies=[
            {
                "study_id": "001-risk",
                "monitoring": {"supervisor_tick_status": "fresh"},
                "progress_freshness": {"status": "fresh"},
                "current_stage_summary": "托管运行恢复中。",
                "next_system_action": "请回到 MAS 控制面确认当前托管运行策略，并决定是否暂停、重启或接管。",
                "current_blockers": ["托管运行时已连续两次恢复失败，必须人工介入。"],
                "intervention_lane": {
                    "lane_id": "runtime_recovery_required",
                    "title": "优先恢复托管运行",
                    "severity": "critical",
                    "summary": "旧的恢复摘要。",
                },
                "autonomy_contract": {
                    "summary": "恢复点已冻结；当前停在 resume_from_checkpoint，下一次确认看恢复信号。",
                },
                "operator_verdict": {
                    "summary": "generic runtime recovery summary",
                    "primary_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                },
                "operator_status_card": {
                    "user_visible_verdict": "MAS 正在恢复托管运行。",
                },
                "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_runtime_recovery_required"
    assert queue[0]["summary"] == "恢复点已冻结；当前停在 resume_from_checkpoint，下一次确认看恢复信号。"


def test_attention_queue_prefers_gate_clearing_followthrough_for_quality_blockers() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    followthrough_command = (
        "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk --format json"
    )

    queue = module._attention_queue(
        workspace_status="attention_required",
        workspace_supervision={
            "service": {"loaded": True, "drift_reasons": []},
            "study_counts": {},
        },
        studies=[
            {
                "study_id": "001-risk",
                "monitoring": {"supervisor_tick_status": "fresh"},
                "progress_freshness": {"status": "fresh"},
                "current_stage_summary": "当前进入 controller-owned gate-clearing followthrough。",
                "next_system_action": "等待新的 publication gate 结论。",
                "current_blockers": ["publication gate 还没有重新回写清障结果。"],
                "intervention_lane": {
                    "lane_id": "quality_floor_blocker",
                    "repair_mode": "bounded_analysis",
                    "route_target_label": "analysis-campaign",
                },
                "operator_verdict": {
                    "summary": "generic gate-clearing summary",
                    "primary_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                },
                "operator_status_card": {},
                "quality_execution_lane": {
                    "lane_id": "claim_evidence",
                    "summary": "旧的质量执行线摘要。",
                },
                "gate_clearing_followthrough": {
                    "surface_kind": "gate_clearing_followthrough",
                    "state": "waiting_gate_replay",
                    "state_label": "等待 gate replay",
                    "summary": "当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。",
                    "next_confirmation_signal": "看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。",
                    "recommended_step_id": "inspect_gate_clearing_followthrough",
                    "recommended_command": followthrough_command,
                },
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_quality_floor_blocker"
    assert queue[0]["summary"] == "当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。"
    assert queue[0]["recommended_step_id"] == "inspect_gate_clearing_followthrough"
    assert queue[0]["recommended_command"] == followthrough_command
    assert queue[0]["gate_clearing_followthrough"]["state_label"] == "等待 gate replay"
    assert (
        queue[0]["gate_clearing_followthrough"]["next_confirmation_signal"]
        == "看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。"
    )


def test_study_item_normalizes_gate_clearing_batch_followthrough_from_progress_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = Path("profile.local.toml").resolve()

    item = module._study_item(
        progress_payload={
            "study_id": "001-risk",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "summary": "最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。",
                "gate_replay_status": "blocked",
                "blocking_issue_count": 2,
                "failed_unit_count": 0,
                "next_confirmation_signal": "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。",
                "user_intervention_required_now": False,
                "latest_record_path": "/tmp/gate_clearing_batch/latest.json",
            },
        },
        profile_ref=profile_ref,
    )

    assert item["gate_clearing_followthrough"] == {
        "surface_kind": "gate_clearing_followthrough",
        "state": "waiting_gate_replay",
        "state_label": "等待 gate replay",
        "summary": "最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。",
        "next_confirmation_signal": "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。",
        "recommended_step_id": "inspect_gate_clearing_followthrough",
        "recommended_command": (
            "uv run python -m med_autoscience.cli study-progress --profile "
            + str(profile_ref)
            + " --study-id 001-risk"
        ),
        "gate_replay_status": "blocked",
        "failed_unit_count": 0,
        "blocking_issue_count": 2,
        "latest_record_path": "/tmp/gate_clearing_batch/latest.json",
        "user_intervention_required_now": False,
    }


def test_workspace_cockpit_summarizes_alerts_and_user_commands(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    write_study(profile.workspace_root, "002-risk")

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
            "status": "not_loaded",
            "loaded": False,
            "job_exists": True,
            "summary": "Hermes-hosted runtime supervision 已注册，但当前未处于调度中。",
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {
                "id": "f4_blocker_closeout",
                "status": "in_progress",
                "summary": "当前主线仍在 blocker 收口与 product-entry hardening。",
            },
            "current_program_phase": {
                "id": "phase_1_mainline_established",
                "status": "in_progress",
                "summary": "当前仍在第一阶段尾声。",
            },
            "next_focus": [
                "continue hardening user-visible product-entry surfaces so task, progress, supervision, and stuck-state truth stay visible",
            ],
            "explicitly_not_now": [
                "physical migration or cross-repo rewrite",
            ],
        },
    )

    def fake_progress(
        *,
        profile,
        profile_ref=None,
        study_id: str | None = None,
        study_root: Path | None = None,
        entry_mode=None,
    ) -> dict:
        resolved_study_id = study_id or Path(study_root).name
        if resolved_study_id == "001-risk":
            return {
                "study_id": resolved_study_id,
                "current_stage": "managed_runtime_supervision_gap",
                "current_stage_summary": "Hermes-hosted 托管监管存在缺口。",
                "current_blockers": ["Hermes-hosted 托管监管存在缺口。"],
                "next_system_action": "先恢复 supervisor loop，再继续托管推进。",
                "intervention_lane": {
                    "lane_id": "workspace_supervision_gap",
                    "title": "优先恢复 Hermes-hosted 托管监管",
                    "severity": "critical",
                    "summary": "Hermes-hosted 托管监管存在缺口。",
                    "recommended_action_id": "refresh_supervision",
                },
                "operator_verdict": {
                    "surface_kind": "study_operator_verdict",
                    "verdict_id": "study_operator_verdict::001-risk::workspace_supervision_gap",
                    "study_id": "001-risk",
                    "lane_id": "workspace_supervision_gap",
                    "severity": "critical",
                    "decision_mode": "intervene_now",
                    "needs_intervention": True,
                    "focus_scope": "workspace",
                    "summary": "Hermes-hosted 托管监管存在缺口。",
                    "reason_summary": "Hermes-hosted 托管监管存在缺口。",
                    "primary_step_id": "refresh_supervision",
                    "primary_surface_kind": "runtime_watch_refresh",
                    "primary_command": (
                        "uv run python -m med_autoscience.cli watch --runtime-root "
                        + str(profile.runtime_root)
                        + " --profile "
                        + str(profile_ref.resolve())
                        + " --ensure-study-runtimes --apply"
                    ),
                },
                "recommended_command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply"
                ),
                "recommended_commands": [
                    {
                        "step_id": "refresh_supervision",
                        "title": "刷新 Hermes-hosted supervision tick",
                        "surface_kind": "runtime_watch_refresh",
                        "command": (
                            "uv run python -m med_autoscience.cli watch --runtime-root "
                            + str(profile.runtime_root)
                            + " --profile "
                            + str(profile_ref.resolve())
                            + " --ensure-study-runtimes --apply"
                        ),
                    }
                ],
                "recovery_contract": {
                    "contract_kind": "study_recovery_contract",
                    "lane_id": "workspace_supervision_gap",
                    "action_mode": "refresh_supervision",
                    "summary": "Hermes-hosted 托管监管存在缺口。",
                    "recommended_step_id": "refresh_supervision",
                    "steps": [
                        {
                            "step_id": "refresh_supervision",
                            "title": "刷新 Hermes-hosted supervision tick",
                            "surface_kind": "runtime_watch_refresh",
                            "command": (
                                "uv run python -m med_autoscience.cli watch --runtime-root "
                                + str(profile.runtime_root)
                                + " --profile "
                                + str(profile_ref.resolve())
                                + " --ensure-study-runtimes --apply"
                            ),
                        }
                    ],
                },
                "needs_physician_decision": False,
                "supervision": {
                    "browser_url": None,
                    "quest_session_api_url": None,
                    "active_run_id": None,
                    "health_status": "unknown",
                    "supervisor_tick_status": "stale",
                },
                "task_intake": {
                    "task_intent": "先恢复自动监管与持续进度，再决定是否继续推进论文主线。",
                    "journal_target": "BMC Medicine",
                },
                "progress_freshness": {
                    "status": "stale",
                    "summary": "距离上一次明确研究推进已经超过 12 小时，当前要重点排查是否卡住或空转。",
                },
            }
        return {
            "study_id": resolved_study_id,
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": ["图表推进陷入重复打磨循环，当前 run 应被拉回主线。"],
            "next_system_action": "先停止当前 figure-polish loop，再回到主线。",
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "优先收口质量硬阻塞",
                "severity": "critical",
                "summary": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
                "recommended_action_id": "inspect_progress",
            },
            "operator_verdict": {
                "surface_kind": "study_operator_verdict",
                "verdict_id": "study_operator_verdict::002-risk::monitor_only",
                "study_id": "002-risk",
                "lane_id": "quality_floor_blocker",
                "severity": "critical",
                "decision_mode": "monitor_only",
                "needs_intervention": False,
                "focus_scope": "study",
                "summary": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
                "reason_summary": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
                "primary_step_id": "inspect_study_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 002-risk"
                ),
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 002-risk"
            ),
            "recommended_commands": [
                {
                    "step_id": "inspect_study_progress",
                    "title": "读取当前研究进度",
                    "surface_kind": "study_progress",
                    "command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id 002-risk"
                    ),
                }
            ],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "quality_floor_blocker",
                "action_mode": "inspect_progress",
                "summary": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
                "recommended_step_id": "inspect_study_progress",
                "steps": [
                    {
                        "step_id": "inspect_study_progress",
                        "title": "读取当前研究进度",
                        "surface_kind": "study_progress",
                        "command": (
                            "uv run python -m med_autoscience.cli study-progress --profile "
                            + str(profile_ref.resolve())
                            + " --study-id 002-risk"
                        ),
                    }
                ],
            },
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:20999",
                "quest_session_api_url": "http://127.0.0.1:20999/api/quests/002-risk/session",
                "active_run_id": "run-002",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {
                "task_intent": "把当前研究收口到 SCI-ready 投稿标准，并优先补齐证据链。",
                "journal_target": "The Lancet Digital Health",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        }

    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_progress)

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert payload["workspace_status"] == "attention_required"
    assert payload["mainline_snapshot"]["current_stage_id"] == "f4_blocker_closeout"
    assert payload["mainline_snapshot"]["current_program_phase_id"] == "phase_1_mainline_established"
    assert "Hermes-hosted 托管监管存在缺口。" in payload["workspace_alerts"]
    assert "图表推进陷入重复打磨循环，当前 run 应被拉回主线。" in payload["workspace_alerts"]
    assert any("距离上一次明确研究推进已经超过 12 小时" in item for item in payload["workspace_alerts"])
    assert payload["workspace_supervision"]["service"]["status"] == "not_loaded"
    assert payload["workspace_supervision"]["study_counts"]["progress_stale"] == 1
    assert payload["workspace_supervision"]["study_counts"]["recovery_required"] == 0
    assert payload["workspace_supervision"]["study_counts"]["quality_blocked"] == 1
    assert payload["operator_brief"] == {
        "surface_kind": "workspace_operator_brief",
        "verdict": "attention_required",
        "summary": "Hermes-hosted runtime supervision 已注册，但当前未处于调度中。",
        "should_intervene_now": True,
        "focus_scope": "workspace",
        "focus_study_id": None,
        "recommended_step_id": "inspect_supervision_service",
        "recommended_command": (
            "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
            + str(profile_ref.resolve())
        ),
    }
    assert payload["attention_queue"][0]["code"] == "workspace_supervisor_service_not_loaded"
    assert payload["attention_queue"][0]["recommended_command"].endswith(
        "runtime-supervision-status --profile " + str(profile_ref.resolve())
    )
    assert any(
        item["study_id"] == "001-risk"
        and item["code"] == "study_supervision_gap"
        and item["recommended_command"].endswith("--ensure-study-runtimes --apply")
        for item in payload["attention_queue"]
    )
    assert any(
        item["study_id"] == "002-risk"
        and item["code"] == "study_quality_floor_blocker"
        and item["recommended_command"].endswith("--study-id 002-risk")
        for item in payload["attention_queue"]
    )
    assert [item["study_id"] for item in payload["studies"]] == ["001-risk", "002-risk"]
    assert payload["studies"][0]["commands"]["launch"].endswith("--study-id 001-risk")
    assert payload["studies"][0]["task_intake"]["journal_target"] == "BMC Medicine"
    assert payload["studies"][0]["intervention_lane"]["lane_id"] == "workspace_supervision_gap"
    assert payload["studies"][0]["operator_verdict"]["decision_mode"] == "intervene_now"
    assert payload["studies"][0]["recommended_command"].endswith("--ensure-study-runtimes --apply")
    assert payload["studies"][0]["recovery_contract"]["action_mode"] == "refresh_supervision"
    assert payload["studies"][1]["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert payload["studies"][1]["operator_verdict"]["summary"] == "图表推进陷入重复打磨循环，当前 run 应被拉回主线。"
    assert payload["studies"][1]["recommended_commands"][0]["surface_kind"] == "study_progress"
    assert payload["studies"][1]["monitoring"]["browser_url"] == "http://127.0.0.1:20999"
    assert "mainline-phase --phase current" in payload["user_loop"]["phase_status_current"]
    assert "submit-study-task" in payload["user_loop"]["submit_task_template"]
    assert "study-progress" in payload["user_loop"]["watch_progress_template"]
    assert payload["phase2_user_product_loop"]["surface_kind"] == "phase2_user_product_loop_lane"
    assert payload["phase2_user_product_loop"]["recommended_step_id"] == "open_frontdesk"
    assert payload["phase2_user_product_loop"]["recommended_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["phase2_user_product_loop"]["single_path"][1]["step_id"] == "inspect_workspace_inbox"
    assert payload["phase2_user_product_loop"]["single_path"][4]["command"].endswith(
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert payload["phase2_user_product_loop"]["operator_questions"] == [
        {
            "question": "用户现在怎么启动 MAS？",
            "answer_surface_kind": "product_frontdesk",
            "command": "uv run python -m med_autoscience.cli product-frontdesk --profile " + str(profile_ref.resolve()),
        },
        {
            "question": "用户怎么给 study 下任务？",
            "answer_surface_kind": "study_task_intake",
            "command": (
                "uv run python -m med_autoscience.cli submit-study-task --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --task-intent '<task_intent>'"
            ),
        },
        {
            "question": "用户怎么持续看进度和恢复建议？",
            "answer_surface_kind": "study_progress",
            "command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --format json"
            ),
        },
    ]

    markdown = module.render_workspace_cockpit_markdown(payload)
    assert "001-risk" in markdown
    assert "002-risk" in markdown
    assert "Mainline Snapshot" in markdown
    assert "## Now" in markdown
    assert "当前 program phase" in markdown
    assert "下一步焦点" in markdown
    assert "Attention Queue" in markdown
    assert "User Loop" in markdown
    assert "Phase 2 User Loop" in markdown
    assert "当前决策模式" in markdown
    assert "推荐动作" in markdown
    assert "推荐动作命令" in markdown
    assert "图表推进陷入重复打磨循环" in markdown
    assert "The Lancet Digital Health" in markdown
    assert "Hermes-hosted runtime supervision 已注册，但当前未处于调度中。" in markdown
    assert "launch-study" in markdown


def test_workspace_cockpit_reads_study_progress_in_parallel_and_preserves_order(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    write_study(profile.workspace_root, "002-risk")

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
            "current_stage": {"id": "phase-x", "status": "in_progress", "summary": "current stage"},
            "current_program_phase": {"id": "phase-y", "status": "in_progress", "summary": "current phase"},
            "next_focus": [],
            "explicitly_not_now": [],
        },
    )

    second_started = threading.Event()

    def fake_progress(
        *,
        profile,
        profile_ref=None,
        study_id: str | None = None,
        study_root: Path | None = None,
        entry_mode=None,
    ) -> dict[str, object]:
        resolved_study_id = study_id or Path(study_root).name
        if resolved_study_id == "001-risk":
            assert second_started.wait(0.5), "workspace cockpit should fan out study progress reads in parallel"
        else:
            second_started.set()
        return {
            "study_id": resolved_study_id,
            "current_stage": "publication_supervision",
            "current_stage_summary": f"{resolved_study_id} stage",
            "current_blockers": [],
            "next_system_action": f"{resolved_study_id} next",
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id "
                + resolved_study_id
            ),
            "recommended_commands": [],
            "recovery_contract": {},
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": None,
                "quest_session_api_url": None,
                "active_run_id": None,
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {},
            "progress_freshness": {"status": "fresh", "summary": "fresh"},
        }

    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_progress)

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert [item["study_id"] for item in payload["studies"]] == ["001-risk", "002-risk"]
    assert payload["studies"][0]["current_stage_summary"] == "001-risk stage"
    assert payload["studies"][1]["current_stage_summary"] == "002-risk stage"


def test_workspace_cockpit_markdown_prefers_shared_human_status_narration() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    from opl_harness_shared.status_narration import build_status_narration_contract

    payload = {
        "profile_name": "nf-pitnet",
        "workspace_root": "/tmp/nf-pitnet",
        "workspace_status": "ready",
        "workspace_supervision": {},
        "phase2_user_product_loop": {},
        "user_loop": {},
        "commands": {},
        "studies": [
            {
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_stage_summary": "旧版阶段摘要字段",
                "next_system_action": "旧版 next_system_action 字段",
                "current_blockers": ["当前论文交付目录与注册/合同约定不一致，需要先修正交付面。"],
                "status_narration_contract": build_status_narration_contract(
                    contract_id="study-progress::001-risk",
                    surface_kind="study_progress",
                    stage={
                        "current_stage": "publication_supervision",
                        "recommended_next_stage": "bundle_stage_ready",
                    },
                    current_blockers=["当前论文交付目录与注册/合同约定不一致，需要先修正交付面。"],
                    latest_update="论文主体内容已经完成，当前进入投稿打包收口。",
                    next_step="优先核对 submission package 与 studies 目录中的交付面是否一致。",
                ),
            }
        ],
    }

    markdown = module.render_workspace_cockpit_markdown(payload)

    assert "当前阶段: 论文可发表性监管" in markdown
    assert "当前判断: 当前状态：论文可发表性监管；下一阶段：投稿打包就绪；当前卡点：当前论文交付目录与注册/合同约定不一致，需要先修正交付面。" in markdown
    assert "下一步建议: 优先核对 submission package 与 studies 目录中的交付面是否一致。" in markdown
    assert "next_system_action:" not in markdown
    assert "旧版阶段摘要字段" not in markdown
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
