from __future__ import annotations

import shlex

from med_autoscience.controllers import mainline_status
from med_autoscience.controllers.product_entry import (
    attention_projection as product_entry_attention,
)
from med_autoscience.controllers.product_entry import workspace_surfaces as product_entry_workspace

from . import shared as _shared
from .repo_shell_entry_assertions import _phase2_loop_without_guarded_fields

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)


def _assert_diagnostic_refresh_policy(policy: dict, command: str) -> None:
    assert policy["command"] == command
    assert policy["surface_role"] == "paper_mission_readback_refresh"
    assert policy["dry_run"] is True
    assert policy["diagnostic_only"] is True
    assert policy["writes_authority"] is False
    assert policy["writes_runtime"] is False
    assert policy["can_select_next_paper_stage"] is False
    assert policy["can_authorize_provider_admission"] is False
    assert policy["counts_as_paper_progress"] is False
    assert policy["default_paper_mission_entry"] is False


def _doctor_report() -> SimpleNamespace:
    return SimpleNamespace(
        workspace_exists=True, runtime_exists=True, studies_exists=True, portfolio_exists=True,
        med_deepscientist_runtime_exists=True, medical_overlay_ready=True,
        external_runtime_contract={"ready": True},
        workspace_domain_route_contract={
            "status": "loaded", "loaded": True,
            "summary": "OPL current_control_state refs-only handoff 已在线。", "drift_reasons": [],
        },
    )


def _workspace_supervision(*, loaded: bool, summary: str) -> dict[str, object]:
    return {
        "manager": "launchd", "status": "loaded" if loaded else "not_loaded",
        "loaded": loaded, "job_exists": True, "summary": summary, "drift_reasons": [],
    }


def _mainline_status(
    *,
    stage_id: str = "phase-x",
    stage_summary: str = "current stage",
    phase_id: str = "phase-y",
    phase_summary: str = "current phase",
    next_focus: list[str] | None = None,
    explicitly_not_now: list[str] | None = None,
) -> dict[str, object]:
    return {
        "program_id": "research-foundry-medical-mainline",
        "current_stage": {"id": stage_id, "status": "in_progress", "summary": stage_summary},
        "current_program_phase": {"id": phase_id, "status": "in_progress", "summary": phase_summary},
        "next_focus": next_focus or [],
        "explicitly_not_now": explicitly_not_now or [],
    }


def _stub_workspace_cockpit_basics(
    monkeypatch,
    *,
    supervision_loaded: bool,
    supervision_summary: str,
    mainline_payload: dict[str, object],
) -> None:
    monkeypatch.setattr(
        product_entry_cockpit_payload_module(),
        "build_doctor_report",
        lambda profile: _doctor_report(),
    )
    monkeypatch.setattr(
        product_entry_cockpit_payload_module(),
        "_inspect_workspace_supervision",
        lambda profile: _workspace_supervision(
            loaded=supervision_loaded,
            summary=supervision_summary,
        ),
    )
    monkeypatch.setattr(mainline_status, "read_mainline_status", lambda: mainline_payload)


def _study_progress_payload(
    *, study_id: str, profile_ref, current_stage_summary: str, next_system_action: str,
    current_blockers: list[str] | None = None,
    top_current_stage: str = "publication_supervision",
    writer_state: str = "queued",
    user_next: str = "watch",
    reason: str = "runtime",
    package_delivered: bool = False,
    actual_write_active: bool = False,
    user_action_required: bool = False,
    state_label: str = "系统排队处理中",
    state_summary: str | None = None,
    projection_current_stage: str = "queued",
    browser_url: str | None = None, quest_session_api_url: str | None = None, active_run_id: str | None = None,
    health_status: str = "live",
    supervisor_tick_status: str = "fresh",
    recommended_command: str | None = None,
    **overrides: object,
) -> dict[str, object]:
    blockers = current_blockers or []
    command = recommended_command or (
        "uv run python -m med_autoscience.cli study progress --profile " + str(profile_ref.resolve()) + " --study-id " + study_id
    )
    details: dict[str, object] = {"package_delivered": package_delivered}
    if active_run_id:
        details["active_run_id"] = active_run_id
    payload: dict[str, object] = {
        "study_id": study_id,
        "current_stage": top_current_stage,
        "current_stage_summary": current_stage_summary,
        "current_blockers": blockers,
        "next_system_action": next_system_action,
        "study_macro_state": {
            "surface": "study_macro_state", "schema_version": 1, "study_id": study_id,
            "writer_state": writer_state, "user_next": user_next, "reason": reason,
            "details": details, "conditions": [],
        },
        "user_visible_projection": {
            "surface": "study_progress_user_visible_projection",
            "schema_version": 2,
            "authority": "truth_projection",
            "projection_only": True,
            "study_id": study_id,
            "state": f"{writer_state}/{user_next}/{reason}",
            "writer_state": writer_state,
            "user_next": user_next,
            "reason": reason,
            "package_delivered": package_delivered,
            "actual_write_active": actual_write_active,
            "user_action_required": user_action_required,
            "state_label": state_label,
            "state_summary": state_summary or current_stage_summary,
            "current_stage": projection_current_stage,
            "current_stage_summary": current_stage_summary,
            "current_blockers": blockers,
            "next_system_action": next_system_action,
            "evidence": {"latest_events": [], "refs": {}},
            "conditions": [],
        },
        "recommended_command": command,
        "recommended_commands": [],
        "recovery_contract": {},
        "needs_physician_decision": False,
        "supervision": {
            "browser_url": browser_url, "quest_session_api_url": quest_session_api_url,
            "active_run_id": active_run_id, "health_status": health_status,
            "supervisor_tick_status": supervisor_tick_status,
        },
        "task_intake": {},
        "progress_freshness": {"status": "fresh", "summary": "fresh"},
    }
    payload.update(overrides)
    return payload


def test_workspace_cockpit_marks_domain_diagnostic_commands_as_diagnostic_only(tmp_path) -> None:
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    payload = product_entry_workspace.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    _assert_diagnostic_refresh_policy(
        payload["commands"]["supervisor_tick_policy"],
        payload["commands"]["supervisor_tick"],
    )
    _assert_diagnostic_refresh_policy(
        payload["user_loop"]["refresh_supervision_policy"],
        payload["user_loop"]["refresh_supervision"],
    )

def test_attention_queue_prefers_route_repair_focus_for_quality_blockers() -> None:
    queue = product_entry_attention._attention_queue(
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
                    "primary_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
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
                "recommended_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
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
    queue = product_entry_attention._attention_queue(
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
                    "primary_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
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
                "recommended_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
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


def test_attention_queue_projects_manual_finishing_as_package_handoff_without_generic_blocker_wording() -> None:
    queue = product_entry_attention._attention_queue(
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
                    "title": "保持人工收尾显式保护",
                    "severity": "observe",
                    "summary": "投稿包里程碑已达成；MAS 只保持人工收尾显式保护和监督入口。",
                    "recommended_action_id": "maintain_manual_finish_guard",
                },
                "operator_verdict": {
                    "summary": "旧的阻塞摘要不应覆盖人工收尾语义。",
                    "primary_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
                },
                "operator_status_card": {
                    "handling_state": "package_ready_handoff",
                    "handling_state_label": "投稿包/人审包交付停驻",
                    "user_visible_verdict": "MAS 已到投稿包/人审包交付节点，当前停驻等待用户审阅或显式恢复。",
                    "current_focus": "继续保持投稿包/人审包交付停驻，不把投稿包里程碑 parked 解释为 runtime failure。",
                    "next_confirmation_signal": "看用户是否给出审阅意见、显式恢复或新的修订输入。",
                },
                "autonomy_contract": {
                    "autonomy_state": "compatibility_guard",
                    "summary": "投稿包里程碑已达成；MAS 只保持人工收尾显式保护和监督入口。",
                },
                "recommended_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_auto_runtime_parked"
    assert queue[0]["title"] == "001-risk 当前投稿包/人审包交付停驻"
    assert queue[0]["summary"] == "投稿包里程碑已达成；MAS 只保持人工收尾显式保护和监督入口。"
    assert queue[0]["recommended_step_id"] == "inspect_study_progress"
    assert queue[0]["operator_status_card"]["handling_state"] == "package_ready_handoff"


def test_attention_queue_prefers_autonomy_contract_summary_for_runtime_recovery() -> None:
    queue = product_entry_attention._attention_queue(
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
                    "primary_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
                },
                "operator_status_card": {
                    "user_visible_verdict": "MAS 正在恢复托管运行。",
                },
                "recommended_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_runtime_recovery_required"
    assert queue[0]["summary"] == "恢复点已冻结；当前停在 resume_from_checkpoint，下一次确认看恢复信号。"


def test_attention_queue_prefers_gate_clearing_followthrough_for_quality_blockers() -> None:
    followthrough_command = (
        "uv run python -m med_autoscience.cli study progress --profile profile.local.toml --study-id 001-risk --format json"
    )

    queue = product_entry_attention._attention_queue(
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
                    "primary_command": "uv run python -m med_autoscience.cli study progress --study-id 001-risk",
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
    profile_ref = Path("profile.local.toml").resolve()

    item = product_entry_workspace._study_item(
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
            "uv run python -m med_autoscience.cli study progress --profile "
            + shlex.quote(str(profile_ref))
            + " --study-id 001-risk"
        ),
        "gate_replay_status": "blocked",
        "failed_unit_count": 0,
        "blocking_issue_count": 2,
        "latest_record_path": "/tmp/gate_clearing_batch/latest.json",
        "user_intervention_required_now": False,
    }


def test_workspace_cockpit_summarizes_alerts_and_user_commands(monkeypatch, tmp_path: Path) -> None:
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    write_study(profile.workspace_root, "002-risk")

    _stub_workspace_cockpit_basics(
        monkeypatch,
        supervision_loaded=False,
        supervision_summary="OPL current_control_state refs-only handoff 未就绪。",
        mainline_payload=_mainline_status(
            stage_id="f4_blocker_closeout",
            stage_summary="当前主线仍在 blocker 收口与 product-entry hardening。",
            phase_id="phase_1_mainline_established",
            phase_summary="当前仍在第一阶段尾声。",
            next_focus=[
                "continue hardening user-visible product-entry surfaces so task, progress, supervision, and stuck-state truth stay visible",
            ],
            explicitly_not_now=["physical migration or cross-repo rewrite"],
        ),
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
            refresh_command = (
                "uv run python -m med_autoscience.cli paper-mission inspect --profile "
                + str(profile_ref.resolve())
                + " --format json"
            )
            return _study_progress_payload(
                study_id=resolved_study_id,
                profile_ref=profile_ref,
                top_current_stage="managed_opl_runtime_owner_handoff_gap",
                current_stage_summary="OPL runtime manager 托管监管存在缺口。",
                current_blockers=["OPL runtime manager 托管监管存在缺口。"],
                next_system_action="先刷新 domain route tick，再继续托管推进。",
                user_next="repair",
                state_label="质量修复/复审中",
                health_status="unknown",
                supervisor_tick_status="stale",
                recommended_command=refresh_command,
                intervention_lane={
                    "lane_id": "workspace_supervision_gap",
                    "title": "优先刷新 OPL runtime manager 托管监管",
                    "severity": "critical",
                    "summary": "OPL runtime manager 托管监管存在缺口。",
                    "recommended_action_id": "refresh_supervision",
                },
                operator_verdict={
                    "surface_kind": "study_operator_verdict",
                    "verdict_id": "study_operator_verdict::001-risk::workspace_supervision_gap",
                    "study_id": "001-risk",
                    "lane_id": "workspace_supervision_gap",
                    "severity": "critical",
                    "decision_mode": "intervene_now",
                    "needs_intervention": True,
                    "focus_scope": "workspace",
                    "summary": "OPL current_control_state refs-only handoff 未就绪。",
                    "reason_summary": "OPL current_control_state refs-only handoff 未就绪。",
                    "primary_step_id": "refresh_supervision",
                    "primary_surface_kind": "paper_mission_readback_refresh",
                    "primary_command": refresh_command,
                },
                recommended_commands=[
                    {
                        "step_id": "refresh_supervision",
                        "title": "刷新 OPL current_control_state refs-only handoff",
                        "surface_kind": "paper_mission_readback_refresh",
                        "command": refresh_command,
                    }
                ],
                recovery_contract={
                    "contract_kind": "study_recovery_contract",
                    "lane_id": "workspace_supervision_gap",
                    "action_mode": "refresh_supervision",
                    "summary": "OPL current_control_state refs-only handoff 未就绪。",
                    "recommended_step_id": "refresh_supervision",
                    "steps": [
                        {
                            "step_id": "refresh_supervision",
                            "title": "刷新 OPL current_control_state refs-only handoff",
                            "surface_kind": "paper_mission_readback_refresh",
                            "command": refresh_command,
                        }
                    ],
                },
                task_intake={
                    "task_intent": "先恢复自动监管与持续进度，再决定是否继续推进论文主线。",
                    "journal_target": "BMC Medicine",
                },
                progress_freshness={
                    "status": "stale",
                    "summary": "距离上一次明确研究推进已经超过 12 小时，当前要重点排查是否卡住或空转。",
                },
            )
        progress_command = (
            "uv run python -m med_autoscience.cli study progress --profile "
            + str(profile_ref.resolve())
            + " --study-id 002-risk"
        )
        return _study_progress_payload(
            study_id=resolved_study_id,
            profile_ref=profile_ref,
            current_stage_summary="论文可发表性监管。",
            current_blockers=["图表推进陷入重复打磨循环，当前 run 应被拉回主线。"],
            next_system_action="先停止当前 figure-polish loop，再回到主线。",
            writer_state="live",
            actual_write_active=True,
            state_label="自动运行中",
            projection_current_stage="live",
            browser_url="http://127.0.0.1:20999",
            quest_session_api_url="http://127.0.0.1:20999/api/quests/002-risk/session",
            active_run_id="run-002",
            recommended_command=progress_command,
            intervention_lane={
                "lane_id": "quality_floor_blocker",
                "title": "优先收口质量硬阻塞",
                "severity": "critical",
                "summary": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
                "recommended_action_id": "inspect_progress",
            },
            operator_verdict={
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
                "primary_command": progress_command,
            },
            recommended_commands=[
                {
                    "step_id": "inspect_study_progress",
                    "title": "读取当前研究进度",
                    "surface_kind": "study_progress",
                    "command": progress_command,
                }
            ],
            recovery_contract={
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
                            "command": progress_command,
                        }
                    ],
                },
            task_intake={
                "task_intent": "把当前研究收口到 SCI-ready 投稿标准，并优先补齐证据链。",
                "journal_target": "The Lancet Digital Health",
            },
            progress_freshness={
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        )

    monkeypatch.setattr(
        _shared.product_entry_cockpit_payload_module(),
        "_read_study_progress",
        fake_progress,
    )

    payload = product_entry_workspace.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert payload["workspace_status"] == "attention_required"
    assert payload["mainline_snapshot"]["current_stage_id"] == "f4_blocker_closeout"
    assert payload["mainline_snapshot"]["current_program_phase_id"] == "phase_1_mainline_established"
    assert "OPL current_control_state refs-only handoff 未就绪。" in payload["workspace_alerts"]
    assert "图表推进陷入重复打磨循环，当前 run 应被拉回主线。" in payload["workspace_alerts"]
    assert any("距离上一次明确研究推进已经超过 12 小时" in item for item in payload["workspace_alerts"])
    assert payload["workspace_supervision"]["service"]["status"] == "not_loaded"
    assert payload["workspace_supervision"]["study_counts"]["progress_stale"] == 1
    assert payload["workspace_supervision"]["study_counts"]["recovery_required"] == 0
    assert payload["workspace_supervision"]["study_counts"]["quality_blocked"] == 1
    assert payload["operator_brief"] == {
        "surface_kind": "workspace_operator_brief",
        "verdict": "attention_required",
        "summary": "OPL current_control_state refs-only handoff 未就绪。",
        "should_intervene_now": True,
        "focus_scope": "workspace",
        "focus_study_id": None,
        "recommended_step_id": "inspect_supervision_service",
        "recommended_command": (
            "uv run python -m med_autoscience.cli study progress --profile "
            + str(profile_ref.resolve())
            + " --format json"
        ),
    }
    assert payload["attention_queue"][0]["code"] == "workspace_supervisor_service_not_loaded"
    assert payload["attention_queue"][0]["title"] == "先检查 OPL scheduler replacement"
    assert payload["attention_queue"][0]["recommended_command"].endswith(
        "study progress --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert any(
        item["study_id"] == "001-risk"
        and item["code"] == "study_supervision_gap"
        and "paper-mission inspect" in item["recommended_command"]
        and item["recommended_command"].endswith("--format json")
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
    assert "paper-mission inspect" in payload["studies"][0]["recommended_command"]
    assert payload["studies"][0]["recommended_command"].endswith("--format json")
    assert payload["studies"][0]["recovery_contract"]["action_mode"] == "refresh_supervision"
    assert payload["studies"][1]["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert payload["studies"][1]["operator_verdict"]["summary"] == "图表推进陷入重复打磨循环，当前 run 应被拉回主线。"
    assert payload["studies"][1]["recommended_commands"][0]["surface_kind"] == "study_progress"
    assert payload["studies"][1]["monitoring"]["browser_url"] == "http://127.0.0.1:20999"
    assert "doctor mainline-phase --phase current" in payload["user_loop"]["phase_status_current"]
    assert "study submit-task" in payload["user_loop"]["submit_task_template"]
    assert "study progress" in payload["user_loop"]["watch_progress_template"]
    assert payload["phase2_user_product_loop"]["surface_kind"] == "phase2_user_product_loop_lane"
    assert payload["phase2_user_product_loop"]["recommended_step_id"] == "open_product_entry"
    assert payload["phase2_user_product_loop"]["recommended_command"].endswith(
        "opl app product-entry-status --agent med-autoscience --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["phase2_user_product_loop"]["single_path"][1]["step_id"] == "inspect_workspace_inbox"
    assert payload["phase2_user_product_loop"]["single_path"][4]["command"].endswith(
        "study progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert _phase2_loop_without_guarded_fields(payload["phase2_user_product_loop"])[
        "operator_questions"
    ] == [
        {
            "question": "用户现在怎么启动 MAS？",
            "answer_surface_kind": "product_entry_status",
            "command": (
                "opl app product-entry-status --agent med-autoscience --profile "
                + str(profile_ref.resolve())
                + " --format json"
            ),
        },
        {
            "question": "用户怎么给 study 下任务？",
            "answer_surface_kind": "study_task_intake",
            "command": (
                "uv run python -m med_autoscience.cli study submit-task --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --task-intent '<task_intent>'"
            ),
        },
        {
            "question": "用户怎么持续看进度和恢复建议？",
            "answer_surface_kind": "study_progress",
            "command": (
                "uv run python -m med_autoscience.cli study progress --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --format json"
            ),
        },
    ]

    markdown = product_entry_workspace.render_workspace_cockpit_markdown(payload)
    assert markdown.strip()


def test_workspace_cockpit_reads_study_progress_in_parallel_and_preserves_order(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    write_study(profile.workspace_root, "002-risk")

    _stub_workspace_cockpit_basics(
        monkeypatch,
        supervision_loaded=True,
        supervision_summary="OPL current_control_state refs-only handoff 已在线。",
        mainline_payload=_mainline_status(),
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
        return _study_progress_payload(
            study_id=resolved_study_id,
            profile_ref=profile_ref,
            current_stage_summary=f"{resolved_study_id} stage",
            next_system_action=f"{resolved_study_id} next",
        )

    monkeypatch.setattr(
        _shared.product_entry_cockpit_payload_module(),
        "_read_study_progress",
        fake_progress,
    )

    payload = product_entry_workspace.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert [item["study_id"] for item in payload["studies"]] == ["001-risk", "002-risk"]
    assert payload["studies"][0]["current_stage_summary"] == "001-risk stage"
    assert payload["studies"][1]["current_stage_summary"] == "002-risk stage"


def test_workspace_cockpit_markdown_prefers_shared_human_status_narration() -> None:
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

    markdown = product_entry_workspace.render_workspace_cockpit_markdown(payload)

    assert markdown.strip()
    assert "next_system_action:" not in markdown
    assert "旧版阶段摘要字段" not in markdown
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
