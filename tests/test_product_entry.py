from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study, write_text


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
        "recommended_step_id": "handle_attention_item",
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
    assert "current_program_phase" in markdown
    assert "Attention Queue" in markdown
    assert "User Loop" in markdown
    assert "Phase 2 User Loop" in markdown
    assert "operator_verdict" in markdown
    assert "图表推进陷入重复打磨循环" in markdown
    assert "The Lancet Digital Health" in markdown
    assert "Hermes-hosted runtime supervision 已注册，但当前未处于调度中。" in markdown
    assert "launch-study" in markdown


def test_launch_study_packages_monitoring_progress_and_commands(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": ["论文叙事或方法/结果书写面仍有硬阻塞。"],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [
                {
                    "step_id": "inspect_study_progress",
                    "title": "读取当前研究进度",
                    "surface_kind": "study_progress",
                    "command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id 001-risk"
                    ),
                }
            ],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "quality_floor_blocker",
                "action_mode": "inspect_progress",
                "summary": "论文叙事或方法/结果书写面仍有硬阻塞。",
                "recommended_step_id": "inspect_study_progress",
                "steps": [
                    {
                        "step_id": "inspect_study_progress",
                        "title": "读取当前研究进度",
                        "surface_kind": "study_progress",
                        "command": (
                            "uv run python -m med_autoscience.cli study-progress --profile "
                            + str(profile_ref.resolve())
                            + " --study-id 001-risk"
                        ),
                    }
                ],
            },
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:20999",
                "quest_session_api_url": "http://127.0.0.1:20999/api/quests/quest-001/session",
                "active_run_id": "run-001",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {
                "task_intent": "优先发现卡住、无进度和 figure 质量回退，再决定是否继续自动推进。",
                "journal_target": "JAMA Network Open",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        },
    )

    payload = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        entry_mode="full_research",
    )

    assert payload["study_id"] == "001-risk"
    assert payload["runtime_status"]["decision"] == "resume"
    assert payload["progress"]["supervision"]["browser_url"] == "http://127.0.0.1:20999"
    assert payload["progress"]["task_intake"]["journal_target"] == "JAMA Network Open"
    assert payload["progress"]["progress_freshness"]["status"] == "fresh"
    assert payload["progress"]["recovery_contract"]["action_mode"] == "inspect_progress"
    assert payload["commands"]["progress"].endswith("--study-id 001-risk")
    assert "workspace-cockpit" in payload["commands"]["cockpit"]

    markdown = module.render_launch_study_markdown(payload)
    assert "http://127.0.0.1:20999" in markdown
    assert "论文叙事或方法/结果书写面仍有硬阻塞。" in markdown
    assert "优先发现卡住、无进度和 figure 质量回退" in markdown
    assert "最近 12 小时内仍有明确研究推进记录" in markdown
    assert "恢复合同" in markdown


def test_submit_study_task_writes_durable_intake_and_updates_startup_brief_block(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    startup_brief_path = profile.workspace_root / "ops" / "med-deepscientist" / "startup_briefs" / "001-risk.md"
    write_text(startup_brief_path, "# Startup brief\n\n已有人工上下文。\n")

    payload = module.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="把当前研究收口到 SCI-ready 投稿标准，并持续自检卡点与质量退化。",
        journal_target="The Lancet Digital Health",
        constraints=("始终中文汇报", "不得跳过 publication gate"),
        evidence_boundary=("必须补齐外部验证",),
        trusted_inputs=("study.yaml", "数据字典"),
        reference_papers=("PMID:12345678",),
        first_cycle_outputs=("study-progress", "runtime_watch", "publication_eval/latest.json"),
    )

    latest_json = Path(payload["artifacts"]["latest_json"])
    latest_markdown = Path(payload["artifacts"]["latest_markdown"])
    written_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    startup_brief_text = startup_brief_path.read_text(encoding="utf-8")

    assert latest_json.is_file()
    assert latest_markdown.is_file()
    assert written_payload["task_intent"].startswith("把当前研究收口到 SCI-ready 投稿标准")
    assert written_payload["journal_target"] == "The Lancet Digital Health"
    assert written_payload["constraints"] == ["始终中文汇报", "不得跳过 publication gate"]
    assert "MAS_TASK_INTAKE:BEGIN" in startup_brief_text
    assert "已有人工上下文。" in startup_brief_text
    assert "The Lancet Digital Health" in latest_markdown.read_text(encoding="utf-8")
    assert payload["study_root"] == str(study_root)


def test_build_product_entry_reuses_latest_task_intake_and_shared_handoff_envelope(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    study_root = write_study(profile.workspace_root, "001-risk")

    task_payload = module.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="把当前研究推进到可投稿的 SCI-ready 稳态。",
        entry_mode="full_research",
        journal_target="JAMA Network Open",
        evidence_boundary=("必须保留 publication gate",),
        first_cycle_outputs=("study-progress", "runtime_watch"),
    )

    payload = module.build_product_entry(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        direct_entry_mode="opl-handoff",
    )

    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["task_intent"] == task_payload["task_intent"]
    assert payload["entry_mode"] == "opl-handoff"
    assert payload["workspace_locator"]["study_id"] == "001-risk"
    assert payload["workspace_locator"]["study_root"] == str(study_root)
    assert payload["runtime_session_contract"]["managed_entry_mode"] == "full_research"
    assert payload["runtime_session_contract"]["managed_runtime_backend_id"] == profile.managed_runtime_backend_id
    assert payload["domain_payload"]["journal_target"] == "JAMA Network Open"
    assert payload["domain_payload"]["evidence_boundary"] == ["必须保留 publication gate"]
    assert payload["return_surface_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["return_surface_contract"]["default_formal_entry"] == "CLI"
    assert payload["return_surface_contract"]["supported_entry_modes"] == ["direct", "opl-handoff"]
    assert payload["return_surface_contract"]["domain_entry_contract"]["service_safe_surface_kind"] == (
        "med_autoscience_service_safe_domain_entry"
    )
    assert payload["return_surface_contract"]["domain_entry_contract"]["supported_commands"] == [
        "workspace-cockpit",
        "product-frontdesk",
        "product-preflight",
        "product-start",
        "product-entry-manifest",
        "study-progress",
        "study-runtime-status",
        "launch-study",
        "submit-study-task",
        "build-product-entry",
    ]
    assert payload["return_surface_contract"]["gateway_interaction_contract"] == {
        "surface_kind": "gateway_interaction_contract",
        "frontdoor_owner": "opl_gateway_or_domain_gui",
        "user_interaction_mode": "natural_language_frontdoor",
        "user_commands_required": False,
        "command_surfaces_for_agent_consumption_only": True,
        "shared_downstream_entry": "MedAutoScienceDomainEntry",
        "shared_handoff_envelope": [
            "target_domain_id",
            "task_intent",
            "entry_mode",
            "workspace_locator",
            "runtime_session_contract",
            "return_surface_contract",
        ],
    }
    assert payload["return_surface_contract"]["progress_command"].endswith(
        "--study-id 001-risk --format json"
    )
    assert payload["commands"]["workspace_cockpit"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["commands"]["launch_study"].endswith("--study-id 001-risk")


def test_build_product_entry_manifest_projects_repo_shell_and_shared_handoff_templates(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

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
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {
                "id": "f4_blocker_closeout",
                "status": "in_progress",
                "summary": "继续收口 blocker 并把用户入口壳压实。",
            },
            "current_program_phase": {
                "id": "phase_2_user_product_loop",
                "status": "in_progress",
                "summary": "把用户 inbox 与持续进度回路收成稳定壳。",
            },
            "next_focus": [
                "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
            ],
            "remaining_gaps": [
                "mature standalone medical product entry is still not landed",
            ],
        },
    )

    payload = module.build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
    )

    assert payload["surface_kind"] == "product_entry_manifest"
    assert payload["manifest_version"] == 2
    assert payload["manifest_kind"] == "med_autoscience_product_entry_manifest"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["formal_entry"]["default"] == "CLI"
    assert payload["formal_entry"]["supported_protocols"] == ["MCP"]
    assert payload["runtime"]["runtime_owner"] == "upstream_hermes_agent"
    assert payload["runtime"]["domain_owner"] == "med-autoscience"
    assert payload["runtime"]["executor_owner"] == "med_deepscientist"
    assert payload["runtime"]["runtime_substrate"] == "external_hermes_agent_target"
    assert payload["managed_runtime_contract"] == {
        "shared_contract_ref": "contracts/opl-gateway/managed-runtime-three-layer-contract.json",
        "runtime_owner": "upstream_hermes_agent",
        "domain_owner": "med-autoscience",
        "executor_owner": "med_deepscientist",
        "supervision_status_surface": {
            "surface_kind": "study_progress",
            "owner": "med-autoscience",
        },
        "attention_queue_surface": {
            "surface_kind": "workspace_cockpit",
            "owner": "med-autoscience",
        },
        "recovery_contract_surface": {
            "surface_kind": "study_runtime_status",
            "owner": "med-autoscience",
        },
        "fail_closed_rules": [
            "domain_supervision_cannot_bypass_runtime",
            "executor_cannot_declare_global_gate_clear",
            "runtime_cannot_invent_domain_publishability_truth",
        ],
    }
    assert payload["runtime_inventory"]["surface_kind"] == "runtime_inventory"
    assert payload["runtime_inventory"]["runtime_owner"] == "upstream_hermes_agent"
    assert payload["runtime_inventory"]["domain_owner"] == "med-autoscience"
    assert payload["runtime_inventory"]["executor_owner"] == "med_deepscientist"
    assert payload["runtime_inventory"]["substrate"] == "external_hermes_agent_target"
    assert payload["runtime_inventory"]["availability"] == "ready"
    assert payload["runtime_inventory"]["health_status"] == "healthy"
    assert payload["runtime_inventory"]["status_surface"]["ref_kind"] == "workspace_locator"
    assert payload["runtime_inventory"]["status_surface"]["ref"] == "studies/<study_id>/artifacts/runtime_watch/latest.json"
    assert payload["runtime_inventory"]["attention_surface"]["ref_kind"] == "json_pointer"
    assert payload["runtime_inventory"]["attention_surface"]["ref"] == "/operator_loop_surface"
    assert payload["runtime_inventory"]["recovery_surface"]["ref_kind"] == "json_pointer"
    assert payload["runtime_inventory"]["recovery_surface"]["ref"] == "/managed_runtime_contract/recovery_contract_surface"
    assert payload["runtime_inventory"]["workspace_binding"]["workspace_root"] == str(profile.workspace_root)
    assert payload["runtime_inventory"]["workspace_binding"]["profile_name"] == profile.name
    assert payload["runtime_inventory"]["domain_projection"]["managed_runtime_backend_id"] == profile.managed_runtime_backend_id
    assert payload["executor_defaults"]["default_executor"] == "codex_cli_autonomous"
    assert payload["executor_defaults"]["default_model"] == "inherit_local_codex_default"
    assert payload["executor_defaults"]["default_reasoning_effort"] == "inherit_local_codex_default"
    assert payload["executor_defaults"]["chat_completion_only_executor_forbidden"] is True
    assert payload["executor_defaults"]["hermes_native_requires_full_agent_loop"] is True
    assert payload["executor_defaults"]["current_backend_chain"][1].endswith(
        "codex exec autonomous agent loop"
    )
    assert payload["executor_defaults"]["optional_executor_proofs"] == [
        {
            "executor_kind": "hermes_native_proof",
            "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
            "requires_full_agent_loop": True,
            "default_model": "inherit_local_hermes_default",
            "default_reasoning_effort": "inherit_local_hermes_default",
        }
    ]
    assert payload["workspace_locator"]["profile_name"] == profile.name
    assert payload["recommended_shell"] == "workspace_cockpit"
    assert payload["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["schema_ref"] == "contracts/schemas/v1/product-entry-manifest.schema.json"
    assert payload["domain_entry_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["domain_entry_contract"]["product_entry_builder_command"] == "build-product-entry"
    assert payload["gateway_interaction_contract"]["frontdoor_owner"] == "opl_gateway_or_domain_gui"
    assert payload["gateway_interaction_contract"]["user_interaction_mode"] == "natural_language_frontdoor"
    assert payload["gateway_interaction_contract"]["command_surfaces_for_agent_consumption_only"] is True
    assert payload["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["frontdesk_surface"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["frontdesk_surface"]["surface_kind"] == "product_frontdesk"
    assert "research product frontdesk" in payload["frontdesk_surface"]["summary"]
    assert payload["operator_loop_surface"]["shell_key"] == "workspace_cockpit"
    assert payload["operator_loop_surface"]["command"] == payload["recommended_command"]
    assert payload["operator_loop_surface"]["surface_kind"] == "workspace_cockpit"
    assert "workspace 级用户 inbox" in payload["operator_loop_surface"]["summary"]
    assert payload["operator_loop_actions"]["open_loop"]["command"] == payload["recommended_command"]
    assert payload["operator_loop_actions"]["open_loop"]["surface_kind"] == "workspace_cockpit"
    assert payload["operator_loop_actions"]["submit_task"]["requires"] == ["study_id", "task_intent"]
    assert payload["operator_loop_actions"]["continue_study"]["requires"] == ["study_id"]
    assert payload["operator_loop_actions"]["inspect_progress"]["command"].endswith(
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert payload["product_entry_quickstart"]["surface_kind"] == "product_entry_quickstart"
    assert payload["product_entry_quickstart"]["recommended_step_id"] == "open_frontdesk"
    assert [step["step_id"] for step in payload["product_entry_quickstart"]["steps"]] == [
        "open_frontdesk",
        "submit_task",
        "continue_study",
        "inspect_progress",
    ]
    assert payload["product_entry_quickstart"]["steps"][0]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_quickstart"]["steps"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_quickstart"]["steps"][2]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_quickstart"]["steps"][3]["surface_kind"] == "study_progress"
    assert payload["repo_mainline"]["program_id"] == "research-foundry-medical-mainline"
    assert payload["repo_mainline"]["current_program_phase_id"] == "phase_2_user_product_loop"
    assert payload["repo_mainline"]["current_stage_summary"] == "继续收口 blocker 并把用户入口壳压实。"
    assert payload["repo_mainline"]["current_program_phase_summary"] == "把用户 inbox 与持续进度回路收成稳定壳。"
    assert payload["repo_mainline"]["next_focus"] == [
        "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
    ]
    assert payload["product_entry_status"]["summary"] == "继续收口 blocker 并把用户入口壳压实。"
    assert payload["product_entry_status"]["remaining_gaps_count"] == 1
    assert payload["product_entry_status"]["next_focus"] == [
        "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
    ]
    assert payload["task_lifecycle"]["surface_kind"] == "task_lifecycle"
    assert payload["task_lifecycle"]["task_kind"] == "mas_product_entry_mainline"
    assert payload["task_lifecycle"]["task_id"] == "research-foundry-medical-mainline:f4_blocker_closeout"
    assert payload["task_lifecycle"]["status"] == "in_progress"
    assert payload["task_lifecycle"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["task_lifecycle"]["progress_surface"]["surface_kind"] == "workspace_cockpit"
    assert payload["task_lifecycle"]["progress_surface"]["step_id"] == "inspect_workspace_inbox"
    assert payload["task_lifecycle"]["progress_surface"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["task_lifecycle"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["task_lifecycle"]["resume_surface"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["task_lifecycle"]["checkpoint_summary"]["surface_kind"] == "checkpoint_summary"
    assert payload["task_lifecycle"]["checkpoint_summary"]["status"] == "monitoring_required"
    assert payload["task_lifecycle"]["checkpoint_summary"]["lineage_ref"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        "label": "controller checkpoint lineage companion",
    }
    assert payload["task_lifecycle"]["checkpoint_summary"]["verification_ref"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
        "label": "runtime watch event companion",
    }
    assert payload["task_lifecycle"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["task_lifecycle"]["domain_projection"]["current_program_phase_id"] == "phase_2_user_product_loop"
    assert payload["task_lifecycle"]["domain_projection"]["recommended_loop_surface"] == "workspace_cockpit"
    assert payload["task_lifecycle"]["domain_projection"]["recommended_loop_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["skill_catalog"]["surface_kind"] == "skill_catalog"
    assert payload["skill_catalog"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["skill_catalog"]["supported_commands"] == payload["domain_entry_contract"]["supported_commands"]
    assert payload["skill_catalog"]["command_contracts"] == payload["domain_entry_contract"]["command_contracts"]
    assert [item["skill_id"] for item in payload["skill_catalog"]["skills"]] == [
        "mas_product_frontdesk",
        "mas_workspace_cockpit",
        "mas_submit_study_task",
        "mas_launch_study",
        "mas_study_progress",
    ]
    assert payload["skill_catalog"]["skills"][0]["target_surface_kind"] == "product_frontdesk"
    assert payload["skill_catalog"]["skills"][1]["target_surface_kind"] == "workspace_cockpit"
    assert payload["skill_catalog"]["skills"][2]["target_surface_kind"] == "study_task_intake"
    assert payload["skill_catalog"]["skills"][2]["command"].endswith(
        "--study-id <study_id> --task-intent '<task_intent>'"
    )
    assert payload["skill_catalog"]["skills"][4]["target_surface_kind"] == "study_progress"
    assert payload["automation"]["surface_kind"] == "automation"
    assert payload["automation"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["automation"]["readiness_summary"].startswith("Automation-ready rule:")
    assert payload["automation"]["automations"] == [
        {
            "surface_kind": "automation_descriptor",
            "automation_id": "mas_runtime_supervision_loop",
            "title": "MAS runtime supervision loop",
            "owner": "med-autoscience",
            "trigger_kind": "interval",
            "target_surface_kind": "runtime_watch_refresh",
            "summary": "按监督节拍刷新 study runtime，保持恢复建议和 attention queue 为最新状态。",
            "readiness_status": "automation_ready",
            "gate_policy": "publication_gated",
            "output_expectation": [
                "refresh runtime watch",
                "update workspace attention queue",
                "preserve controller decision lineage",
            ],
            "target_command": (
                "uv run python -m med_autoscience.cli watch --runtime-root "
                + str(profile.runtime_root)
                + " --profile "
                + str(profile_ref.resolve())
                + " --ensure-study-runtimes --apply"
            ),
            "domain_projection": {
                "service_status_command": str(
                    profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
                ),
                "recommended_entry_surface": "workspace_cockpit",
            },
        }
    ]
    assert payload["product_entry_overview"]["surface_kind"] == "product_entry_overview"
    assert payload["product_entry_overview"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["product_entry_overview"]["frontdesk_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_overview"]["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_overview"]["progress_surface"] == {
        "surface_kind": "study_progress",
        "command": (
            "uv run python -m med_autoscience.cli study-progress --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --format json"
        ),
        "step_id": "inspect_progress",
    }
    assert payload["product_entry_overview"]["resume_surface"] == {
        "surface_kind": "launch_study",
        "command": (
            "uv run python -m med_autoscience.cli launch-study --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id>"
        ),
        "session_locator_field": "study_id",
        "checkpoint_locator_field": "controller_decision_path",
    }
    assert payload["product_entry_overview"]["recommended_step_id"] == "open_frontdesk"
    assert payload["product_entry_overview"]["next_focus"] == [
        "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
    ]
    assert payload["product_entry_overview"]["remaining_gaps_count"] == 1
    assert payload["product_entry_overview"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["product_entry_readiness"] == {
        "surface_kind": "product_entry_readiness",
        "verdict": "runtime_ready_not_standalone_product",
        "usable_now": True,
        "good_to_use_now": False,
        "fully_automatic": False,
        "summary": (
            "当前可以作为 research frontdesk / CLI 主线使用，并通过稳定的 runtime 回路持续推进研究；"
            "但还不是成熟的独立医学产品前台。"
        ),
        "recommended_start_surface": "product_frontdesk",
        "recommended_start_command": (
            "uv run python -m med_autoscience.cli product-frontdesk --profile "
            + str(profile_ref.resolve())
        ),
        "recommended_loop_surface": "workspace_cockpit",
        "recommended_loop_command": (
            "uv run python -m med_autoscience.cli workspace-cockpit --profile "
            + str(profile_ref.resolve())
            + " --format json"
        ),
        "blocking_gaps": [
            "独立医学前台 / hosted product entry 仍未 landed。",
            "更多 workspace / host 的真实 clearance 与 study-local blocker 收口仍在继续。",
        ],
    }
    assert payload["phase2_user_product_loop"] == {
        "surface_kind": "phase2_user_product_loop_lane",
        "summary": "把启动 MAS、给 study 下任务、续跑、持续看进度、处理恢复建议和人工 gate 收成同一条用户回路。",
        "recommended_step_id": "open_frontdesk",
        "recommended_command": (
            "uv run python -m med_autoscience.cli product-frontdesk --profile "
            + str(profile_ref.resolve())
        ),
        "single_path": [
            {
                "step_id": "open_frontdesk",
                "title": "先打开 MAS 前台",
                "surface_kind": "product_frontdesk",
                "command": (
                    "uv run python -m med_autoscience.cli product-frontdesk --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "inspect_workspace_inbox",
                "title": "确认当前 workspace inbox / attention queue",
                "surface_kind": "workspace_cockpit",
                "command": (
                    "uv run python -m med_autoscience.cli workspace-cockpit --profile "
                    + str(profile_ref.resolve())
                    + " --format json"
                ),
            },
            {
                "step_id": "submit_task",
                "title": "给目标 study 写 durable task intake",
                "surface_kind": "study_task_intake",
                "command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑当前 study",
                "surface_kind": "launch_study",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看进度、阻塞和恢复建议",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            {
                "step_id": "handle_human_gate",
                "title": "遇到人工 gate 时回到 progress / cockpit 做决策",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
        ],
        "operator_questions": [
            {
                "question": "用户现在怎么启动 MAS？",
                "answer_surface_kind": "product_frontdesk",
                "command": (
                    "uv run python -m med_autoscience.cli product-frontdesk --profile "
                    + str(profile_ref.resolve())
                ),
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
        ],
        "proof_surfaces": [
            {
                "surface_kind": "product_frontdesk",
                "command": (
                    "uv run python -m med_autoscience.cli product-frontdesk --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "surface_kind": "workspace_cockpit",
                "command": (
                    "uv run python -m med_autoscience.cli workspace-cockpit --profile "
                    + str(profile_ref.resolve())
                    + " --format json"
                ),
            },
            {
                "surface_kind": "study_progress.operator_verdict",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            {
                "surface_kind": "study_progress.recovery_contract",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            },
        ],
    }
    assert payload["product_entry_preflight"] == {
        "surface_kind": "product_entry_preflight",
        "summary": "当前 product-entry 前置检查已通过，可以先复核 doctor 输出，再进入 research frontdesk。",
        "ready_to_try_now": True,
        "recommended_check_command": (
            "uv run python -m med_autoscience.cli doctor --profile "
            + str(profile_ref.resolve())
        ),
        "recommended_start_command": (
            "uv run python -m med_autoscience.cli product-frontdesk --profile "
            + str(profile_ref.resolve())
        ),
        "blocking_check_ids": [],
        "checks": [
            {
                "check_id": "workspace_root_exists",
                "title": "Workspace Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "workspace 根目录已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "runtime_root_exists",
                "title": "Runtime Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "runtime root 已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "studies_root_exists",
                "title": "Studies Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "studies 根目录已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "portfolio_root_exists",
                "title": "Portfolio Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "portfolio 根目录已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "research_backend_runtime_ready",
                "title": "Research Backend Runtime Ready",
                "status": "pass",
                "blocking": True,
                "summary": "受控 research backend runtime 已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "medical_overlay_ready",
                "title": "Medical Overlay Ready",
                "status": "pass",
                "blocking": True,
                "summary": "medical overlay 已 ready。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "external_runtime_contract_ready",
                "title": "External Runtime Contract Ready",
                "status": "pass",
                "blocking": True,
                "summary": "external Hermes runtime contract 已 ready。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "workspace_supervision_contract_ready",
                "title": "Workspace Supervision Contract Ready",
                "status": "pass",
                "blocking": True,
                "summary": "workspace supervision owner 已收敛到 canonical Hermes supervision。",
                "command": (
                    "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                    + str(profile_ref.resolve())
                ),
            },
        ],
    }
    assert payload["product_entry_guardrails"] == {
        "surface_kind": "product_entry_guardrails",
        "summary": (
            "把卡住、没进度、监管掉线、需要人工决策和质量阻塞显式投影成可执行恢复回路，"
            "避免研究主线失去监管。"
        ),
        "guardrail_classes": [
            {
                "guardrail_id": "workspace_supervision_gap",
                "trigger": "workspace-cockpit attention queue / study-progress supervisor freshness",
                    "symptom": "Hermes-hosted supervision 未在线、supervisor tick stale/missing、托管恢复真相不再新鲜。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply"
                ),
            },
            {
                "guardrail_id": "study_progress_gap",
                "trigger": "study-progress progress_freshness / workspace-cockpit attention queue",
                "symptom": "当前 study 进度 stale 或 missing，疑似卡住、空转或没有新的明确推进证据。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "guardrail_id": "human_decision_gate",
                "trigger": "study-progress needs_physician_decision / controller decision gate",
                "symptom": "当前已前移到医生、PI 或 publication release 的人工判断节点。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "guardrail_id": "runtime_recovery_required",
                "trigger": "study-progress intervention_lane / runtime_supervision health_status / workspace-cockpit attention queue",
                "symptom": "托管运行恢复失败、健康降级或长期停在恢复态，当前必须优先处理 runtime recovery。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "guardrail_id": "quality_floor_blocker",
                "trigger": "study-progress intervention_lane / runtime watch figure-loop alerts / publication gate",
                "symptom": "研究输出质量、figure/reference floor 或 publication gate 出现硬阻塞，不能继续盲目长跑。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
        ],
        "recovery_loop": [
            {
                "step_id": "inspect_workspace_inbox",
                "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile " + str(profile_ref.resolve()),
                "surface_kind": "workspace_cockpit",
            },
            {
                "step_id": "refresh_supervision",
                "command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply"
                ),
                "surface_kind": "runtime_watch_refresh",
            },
            {
                "step_id": "inspect_study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
                "surface_kind": "study_progress",
            },
            {
                "step_id": "continue_or_relaunch",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
                "surface_kind": "launch_study",
            },
        ],
    }
    assert payload["phase3_clearance_lane"] == {
        "surface_kind": "phase3_host_clearance_lane",
        "summary": "Phase 3 把 external runtime、Hermes-hosted workspace supervision 和 study recovery proof 扩到更多 workspace/host，并保持 fail-closed。",
        "recommended_step_id": "external_runtime_contract",
        "recommended_command": (
            "uv run python -m med_autoscience.cli doctor --profile "
            + str(profile_ref.resolve())
        ),
        "clearance_targets": [
            {
                "target_id": "external_runtime_contract",
                "title": "Check external Hermes runtime contract",
                "commands": [
                    "uv run python -m med_autoscience.cli doctor --profile " + str(profile_ref.resolve()),
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile " + str(profile_ref.resolve()),
                ],
            },
            {
                "target_id": "supervisor_service",
                "title": "Keep Hermes-hosted workspace supervision online",
                "commands": [
                    (
                        "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                        + str(profile_ref.resolve())
                    ),
                    (
                        "uv run python -m med_autoscience.cli watch --runtime-root "
                        + str(profile.runtime_root)
                        + " --profile "
                        + str(profile_ref.resolve())
                        + " --ensure-study-runtimes --apply"
                    ),
                ],
            },
            {
                "target_id": "study_recovery_proof",
                "title": "Prove live study recovery and supervision",
                "commands": [
                    (
                        "uv run python -m med_autoscience.cli launch-study --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                    (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                ],
            },
        ],
        "clearance_loop": [
            {
                "step_id": "external_runtime_contract",
                "title": "先确认 external Hermes runtime contract ready",
                "surface_kind": "doctor_runtime_contract",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "hermes_runtime_check",
                "title": "确认 Hermes runtime 绑定证据",
                "surface_kind": "hermes_runtime_check",
                "command": (
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "supervisor_service",
                "title": "确认 workspace 常驻监管在线",
                "surface_kind": "workspace_supervisor_service",
                "command": (
                    "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                    + str(profile_ref.resolve())
                ),
            },
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
            },
            {
                "step_id": "study_recovery_proof",
                "title": "证明 live study recovery / progress supervision 成立",
                "surface_kind": "launch_study",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "step_id": "inspect_study_progress",
                "title": "读取 study-progress proof",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "doctor.external_runtime_contract",
                "command": "uv run python -m med_autoscience.cli doctor --profile " + str(profile_ref.resolve()),
            },
            {
                "surface_kind": "study_runtime_status.autonomous_runtime_notice",
                "command": (
                    "uv run python -m med_autoscience.cli study-runtime-status --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "surface_kind": "runtime_watch",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_watch" / "latest.json"),
            },
            {
                "surface_kind": "runtime_supervision",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_supervision" / "latest.json"),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            },
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    }
    assert payload["phase4_backend_deconstruction"] == {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": "Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时诚实保留 controlled backend executor。",
        "substrate_targets": [
            {
                "capability_id": "session_run_watch_recovery",
                "owner": "upstream Hermes-Agent",
                "summary": "session / run / watch / recovery / scheduling / interruption 继续收归 outer runtime substrate。",
            },
            {
                "capability_id": "backend_generic_runtime_contract",
                "owner": "MedAutoScience controller boundary",
                "summary": "controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            },
        ],
        "backend_retained_now": [
            "MedDeepScientist CodexRunner autonomous executor chain",
            "backend-local agent/tool routing and Codex skills",
            "quest-local research execution, paper worktree, and daemon side effects",
        ],
        "current_backend_chain": [
            "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
            "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
        ],
        "optional_executor_proofs": [
            {
                "executor_kind": "hermes_native_proof",
                "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        "promotion_rules": [
            "no claim of backend retirement without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "no physical monorepo absorb before the external gate is cleared",
        ],
        "deconstruction_map_doc": "docs/program/med_deepscientist_deconstruction_map.md",
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    }
    assert payload["phase5_platform_target"] == {
        "surface_kind": "phase5_platform_target",
        "summary": (
            "Phase 5 的目标是把 MAS 继续收敛到 federation/platform-ready 形态，"
            "包括 monorepo、runtime core ingest 和更成熟的 direct product entry；"
            "但这些都必须建立在前四阶段真实成立之后。"
        ),
        "sequence_scope": "monorepo_landing_readiness",
        "current_readiness_summary": (
            "monorepo 长线已经完成 gateway/runtime truth 冻结，当前正在推进 user product loop hardening；"
            "physical absorb 仍然严格属于 post-gate 工作。"
        ),
        "north_star_topology": {
            "domain_gateway": "Med Auto Science",
            "outer_runtime_substrate_owner": "upstream Hermes-Agent",
            "controlled_research_backend": "MedDeepScientist",
            "monorepo_status": "post_gate_target",
        },
        "target_internal_modules": [
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        "landing_sequence": [
            {
                "step_id": "freeze_gateway_runtime_truth",
                "title": "Freeze gateway/runtime truth",
                "status": "completed",
                "phase_id": "phase_1_mainline_established",
                "summary": "mainline topology、product-entry companions 与 post-gate platform wording 已冻结成 repo-tracked truth。",
            },
            {
                "step_id": "stabilize_user_product_loop",
                "title": "Stabilize user product loop",
                "status": "in_progress",
                "phase_id": "phase_2_user_product_loop",
                "summary": "当前活跃步骤：继续收口 F4 blocker，并把启动 / 下任务 / 看进度 / 看恢复建议收成稳定前台回路。",
            },
            {
                "step_id": "clear_multi_workspace_host_gate",
                "title": "Clear multi-workspace / host gate",
                "status": "pending",
                "phase_id": "phase_3_multi_workspace_host_clearance",
                "summary": "把 runtime/service/recovery proof 扩到更多 workspace / host 后，才具备更大 cutover 资格。",
            },
            {
                "step_id": "freeze_backend_deconstruction_boundary",
                "title": "Freeze backend deconstruction boundary",
                "status": "pending",
                "phase_id": "phase_4_backend_deconstruction",
                "summary": "先把 substrate 与 backend retained-now 的边界继续收紧，再谈 executor 迁移或 ingest。",
            },
            {
                "step_id": "physical_monorepo_absorb",
                "title": "Physical monorepo absorb",
                "status": "blocked_post_gate",
                "phase_id": "phase_5_federation_platform_maturation",
                "summary": "只有在前面几步都稳定通过后，controller_charter / runtime / eval_hygiene 才能进入物理 monorepo absorb。",
            },
        ],
        "current_step_id": "stabilize_user_product_loop",
        "completed_step_ids": [
            "freeze_gateway_runtime_truth",
        ],
        "remaining_step_ids": [
            "clear_multi_workspace_host_gate",
            "freeze_backend_deconstruction_boundary",
            "physical_monorepo_absorb",
        ],
        "promotion_gates": [
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        "land_now": [
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
        ],
        "not_yet": [
            "physical monorepo absorb",
            "runtime core ingest across repos",
            "mature hosted standalone medical frontend",
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_federation_platform_maturation"
        ),
    }
    assert payload["product_entry_shell"]["workspace_cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_shell"]["product_frontdesk"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_shell"]["submit_study_task"]["command"].endswith(
        "submit-study-task --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --task-intent '<task_intent>'"
    )
    assert payload["product_entry_shell"]["launch_study"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_shell"]["study_progress"]["command"].endswith(
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert payload["shared_handoff"]["direct_entry_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode direct"
    )
    assert payload["shared_handoff"]["opl_handoff_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode opl-handoff"
    )
    assert payload["family_orchestration"]["human_gates"] == [
        {
            "gate_id": "study_physician_decision_gate",
            "title": "Study physician decision gate",
        },
        {
            "gate_id": "publication_release_gate",
            "title": "Publication release gate",
        },
    ]
    assert payload["family_orchestration"]["action_graph_ref"] == {
        "ref_kind": "json_pointer",
        "ref": "/family_orchestration/action_graph",
        "label": "mas family action graph",
    }
    assert payload["family_orchestration"]["action_graph"]["graph_id"] == (
        "mas_workspace_frontdoor_study_runtime_graph"
    )
    assert payload["family_orchestration"]["action_graph"]["target_domain_id"] == "med-autoscience"
    assert [node["node_id"] for node in payload["family_orchestration"]["action_graph"]["nodes"]] == [
        "step:open_frontdesk",
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert payload["family_orchestration"]["action_graph"]["edges"] == [
        {
            "from": "step:open_frontdesk",
            "to": "step:submit_task",
            "on": "new_task",
        },
        {
            "from": "step:open_frontdesk",
            "to": "step:continue_study",
            "on": "resume_study",
        },
        {
            "from": "step:open_frontdesk",
            "to": "step:inspect_progress",
            "on": "inspect_status",
        },
        {
            "from": "step:submit_task",
            "to": "step:continue_study",
            "on": "task_written",
        },
        {
            "from": "step:continue_study",
            "to": "step:inspect_progress",
            "on": "progress_refresh",
        },
    ]
    assert payload["family_orchestration"]["action_graph"]["entry_nodes"] == [
        "step:open_frontdesk",
    ]
    assert payload["family_orchestration"]["action_graph"]["exit_nodes"] == [
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert payload["family_orchestration"]["action_graph"]["human_gates"] == [
        {
            "gate_id": "study_physician_decision_gate",
            "trigger_nodes": ["step:continue_study"],
            "blocking": True,
        },
        {
            "gate_id": "publication_release_gate",
            "trigger_nodes": ["step:inspect_progress"],
            "blocking": True,
        },
    ]
    assert payload["family_orchestration"]["action_graph"]["checkpoint_policy"] == {
        "mode": "explicit_nodes",
        "checkpoint_nodes": [
            "step:submit_task",
            "step:continue_study",
            "step:inspect_progress",
        ],
    }
    assert payload["family_orchestration"]["resume_contract"] == {
        "surface_kind": "launch_study",
        "session_locator_field": "study_id",
        "checkpoint_locator_field": "controller_decision_path",
    }
    assert payload["family_orchestration"]["event_envelope_surface"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
        "label": "runtime watch event companion",
    }
    assert payload["family_orchestration"]["checkpoint_lineage_surface"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        "label": "controller checkpoint lineage companion",
    }
    assert payload["product_entry_quickstart"]["resume_contract"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_quickstart"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["product_entry_start"]["surface_kind"] == "product_entry_start"
    assert payload["product_entry_start"]["recommended_mode_id"] == "open_frontdesk"
    assert [mode["mode_id"] for mode in payload["product_entry_start"]["modes"]] == [
        "open_frontdesk",
        "submit_task",
        "continue_study",
    ]
    assert payload["product_entry_start"]["modes"][0]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_start"]["modes"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_start"]["modes"][2]["surface_kind"] == "launch_study"
    assert payload["product_entry_start"]["resume_surface"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_start"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert "standalone medical product entry" in payload["remaining_gaps"][0]


def test_build_product_frontdesk_projects_frontdoor_over_current_workspace_loop(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    profile = make_profile(tmp_path)

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
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "ready_for_task",
                "summary": "当前 workspace 已 ready，下一步先给目标 study 写 durable task intake。",
                "should_intervene_now": False,
                "focus_scope": "workspace",
                "focus_study_id": None,
                "recommended_step_id": "submit_task",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            "attention_queue": [],
        },
    )

    payload = module.build_product_frontdesk(
        profile=profile,
        profile_ref=profile_ref,
    )

    assert payload["surface_kind"] == "product_frontdesk"
    assert payload["recommended_action"] == "inspect_or_prepare_research_loop"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["schema_ref"] == "contracts/schemas/v1/product-frontdesk.schema.json"
    assert payload["domain_entry_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["gateway_interaction_contract"]["frontdoor_owner"] == "opl_gateway_or_domain_gui"
    assert payload["gateway_interaction_contract"]["user_interaction_mode"] == "natural_language_frontdoor"
    assert payload["gateway_interaction_contract"]["user_commands_required"] is False
    assert payload["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["frontdesk_surface"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["operator_loop_surface"]["shell_key"] == "workspace_cockpit"
    assert payload["operator_loop_actions"]["open_loop"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["entry_surfaces"]["frontdesk"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["entry_surfaces"]["cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["entry_surfaces"]["direct_entry_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode direct"
    )
    assert payload["summary"]["frontdesk_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["summary"]["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_overview"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["product_entry_overview"]["progress_surface"]["surface_kind"] == "study_progress"
    assert payload["product_entry_overview"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["product_entry_overview"]["resume_surface"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_readiness"]["surface_kind"] == "product_entry_readiness"
    assert payload["product_entry_readiness"]["verdict"] == "runtime_ready_not_standalone_product"
    assert payload["product_entry_readiness"]["usable_now"] is True
    assert payload["product_entry_readiness"]["good_to_use_now"] is False
    assert payload["product_entry_preflight"]["surface_kind"] == "product_entry_preflight"
    assert payload["product_entry_preflight"]["ready_to_try_now"] is True
    assert payload["product_entry_preflight"]["recommended_check_command"].endswith(
        "doctor --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_preflight"]["recommended_start_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_preflight"]["blocking_check_ids"] == []
    assert [check["check_id"] for check in payload["product_entry_preflight"]["checks"]] == [
        "workspace_root_exists",
        "runtime_root_exists",
        "studies_root_exists",
        "portfolio_root_exists",
        "research_backend_runtime_ready",
        "medical_overlay_ready",
        "external_runtime_contract_ready",
        "workspace_supervision_contract_ready",
    ]
    assert payload["product_entry_readiness"]["recommended_start_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["phase2_user_product_loop"]["recommended_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["phase2_user_product_loop"]["single_path"][2]["surface_kind"] == "study_task_intake"
    assert payload["phase2_user_product_loop"]["proof_surfaces"][1]["surface_kind"] == "workspace_cockpit"
    assert payload["operator_brief"] == {
        "surface_kind": "product_frontdesk_operator_brief",
        "verdict": "ready_for_task",
        "summary": "当前 workspace 已 ready，下一步先给目标 study 下任务，再启动研究。",
        "should_intervene_now": False,
        "focus_scope": "workspace",
        "focus_study_id": None,
        "recommended_step_id": "submit_task",
        "recommended_command": (
            "uv run python -m med_autoscience.cli submit-study-task --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --task-intent '<task_intent>'"
        ),
    }
    assert payload["workspace_operator_brief"]["verdict"] == "ready_for_task"
    assert payload["workspace_attention_queue_preview"] == []
    assert payload["product_entry_guardrails"]["surface_kind"] == "product_entry_guardrails"
    assert payload["product_entry_guardrails"]["guardrail_classes"][0]["guardrail_id"] == "workspace_supervision_gap"
    assert payload["product_entry_guardrails"]["guardrail_classes"][3]["guardrail_id"] == "runtime_recovery_required"
    assert payload["product_entry_guardrails"]["guardrail_classes"][4]["guardrail_id"] == "quality_floor_blocker"
    assert payload["product_entry_guardrails"]["recovery_loop"][1]["step_id"] == "refresh_supervision"
    assert payload["phase3_clearance_lane"]["surface_kind"] == "phase3_host_clearance_lane"
    assert payload["phase3_clearance_lane"]["recommended_step_id"] == "external_runtime_contract"
    assert payload["phase3_clearance_lane"]["clearance_targets"][1]["target_id"] == "supervisor_service"
    assert payload["phase3_clearance_lane"]["clearance_loop"][2]["step_id"] == "supervisor_service"
    assert payload["phase4_backend_deconstruction"]["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert payload["phase4_backend_deconstruction"]["current_backend_chain"][1].endswith(
        "codex exec autonomous agent loop"
    )
    assert payload["phase5_platform_target"]["surface_kind"] == "phase5_platform_target"
    assert payload["phase5_platform_target"]["current_step_id"] == "stabilize_user_product_loop"
    assert payload["phase5_platform_target"]["north_star_topology"]["monorepo_status"] == "post_gate_target"
    assert payload["product_entry_quickstart"]["recommended_step_id"] == "open_frontdesk"
    assert payload["product_entry_quickstart"]["steps"][2]["step_id"] == "continue_study"
    assert payload["product_entry_quickstart"]["steps"][2]["requires"] == ["study_id"]
    assert payload["product_entry_start"]["surface_kind"] == "product_entry_start"


def test_workspace_cockpit_flags_supervision_owner_drift_even_when_study_progress_is_fresh(
    monkeypatch, tmp_path: Path
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
                "status": "legacy_only",
                "loaded": False,
                "summary": "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。",
                "drift_reasons": ["legacy_service_loaded"],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "legacy_only",
            "loaded": False,
            "summary": "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。",
            "drift_reasons": ["legacy_service_loaded"],
            "legacy_service": {"loaded": True, "service_exists": True},
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
            "next_focus": ["keep runtime truth visible"],
            "explicitly_not_now": [],
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": [],
            "next_system_action": "继续当前主线。",
            "intervention_lane": {
                "lane_id": "monitor_only",
                "title": "继续监督当前 study",
                "severity": "info",
                "summary": "当前继续监督即可。",
                "recommended_action_id": "inspect_progress",
            },
            "operator_verdict": {
                "surface_kind": "study_operator_verdict",
                "verdict_id": "study_operator_verdict::001-risk::monitor_only",
                "study_id": "001-risk",
                "lane_id": "monitor_only",
                "severity": "info",
                "decision_mode": "monitor_only",
                "needs_intervention": False,
                "focus_scope": "study",
                "summary": "当前继续监督即可。",
                "reason_summary": "当前继续监督即可。",
                "primary_step_id": "inspect_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "monitor_only",
                "action_mode": "inspect_progress",
                "summary": "当前继续监督即可。",
                "recommended_step_id": "inspect_progress",
                "steps": [],
            },
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:21001",
                "quest_session_api_url": None,
                "active_run_id": "run-001",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert payload["workspace_status"] == "blocked"
    assert payload["workspace_supervision"]["service"]["status"] == "legacy_only"
    assert payload["attention_queue"][0]["code"] == "workspace_supervisor_service_not_loaded"
    assert payload["attention_queue"][0]["recommended_command"].endswith(
        "runtime-supervision-status --profile " + str(profile_ref.resolve())
    )


def test_build_product_frontdesk_preflight_blocks_on_workspace_supervision_owner_drift(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    profile = make_profile(tmp_path)

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
                "status": "legacy_only",
                "loaded": False,
                "summary": "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。",
                "drift_reasons": ["legacy_service_loaded"],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "ready_for_task",
                "summary": "当前 workspace 已 ready，下一步先给目标 study 写 durable task intake。",
                "should_intervene_now": False,
                "focus_scope": "workspace",
                "focus_study_id": None,
                "recommended_step_id": "submit_task",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            "attention_queue": [],
        },
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["product_entry_preflight"]["ready_to_try_now"] is False
    assert "workspace_supervision_contract_ready" in payload["product_entry_preflight"]["blocking_check_ids"]
    assert payload["operator_brief"]["verdict"] == "preflight_blocked"
    assert "legacy workspace-local runtime supervision service" in payload["product_entry_preflight"]["summary"]
    assert payload["product_entry_start"]["recommended_mode_id"] == "open_frontdesk"
    assert payload["product_entry_start"]["modes"][1]["mode_id"] == "submit_task"
    assert payload["product_entry_start"]["modes"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_start"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["product_entry_start"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["family_orchestration"]["action_graph_ref"]["ref"] == "/family_orchestration/action_graph"
    assert payload["family_orchestration"]["action_graph"]["graph_id"] == (
        "mas_workspace_frontdoor_study_runtime_graph"
    )
    assert len(payload["family_orchestration"]["action_graph"]["nodes"]) == 4
    assert len(payload["family_orchestration"]["action_graph"]["edges"]) == 5
    assert payload["family_orchestration"]["resume_contract"]["surface_kind"] == "launch_study"
    assert payload["family_orchestration"]["human_gates"][0]["gate_id"] == "study_physician_decision_gate"
    assert payload["product_entry_manifest"]["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["product_entry_manifest"]["manifest_version"] == 2
    assert payload["product_entry_manifest"]["product_entry_readiness"] == payload["product_entry_readiness"]
    assert payload["product_entry_manifest"]["product_entry_preflight"] == payload["product_entry_preflight"]
    assert payload["product_entry_manifest"]["product_entry_start"] == payload["product_entry_start"]
    assert payload["product_entry_manifest"]["product_entry_guardrails"] == payload["product_entry_guardrails"]
    assert payload["product_entry_manifest"]["phase3_clearance_lane"] == payload["phase3_clearance_lane"]
    assert payload["product_entry_manifest"]["phase4_backend_deconstruction"] == payload["phase4_backend_deconstruction"]
    assert payload["product_entry_manifest"]["phase5_platform_target"] == payload["phase5_platform_target"]
    assert payload["product_entry_manifest"]["runtime_inventory"] == payload["runtime_inventory"]
    assert payload["product_entry_manifest"]["task_lifecycle"] == payload["task_lifecycle"]
    assert payload["product_entry_manifest"]["skill_catalog"] == payload["skill_catalog"]
    assert payload["product_entry_manifest"]["automation"] == payload["automation"]

    markdown = module.render_product_frontdesk_markdown(payload)
    assert "Now" in markdown
    assert "Single Path" in markdown
    assert "Workspace Preview" in markdown
    assert "Phase 2 User Loop" in markdown
    assert "Guardrails" in markdown
    assert "workspace_supervision_gap" in markdown
    assert "Phase 3 Clearance" in markdown
    assert "recommended_step_id" in markdown
    assert "clearance_step `refresh_supervision`" in markdown
    assert "external_runtime_contract" in markdown
    assert "Phase 4 Deconstruction" in markdown
    assert "session_run_watch_recovery" in markdown
    assert "Platform Target" in markdown
    assert "Monorepo Sequence" in markdown
    assert "stabilize_user_product_loop" in markdown
    assert "post_gate_target" in markdown


def test_product_entry_manifest_fails_closed_on_invalid_gateway_interaction_contract_shape(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

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
        "_build_gateway_interaction_contract",
        lambda: {
            "surface_kind": "gateway_interaction_contract",
            "frontdoor_owner": "",
        },
    )

    with pytest.raises(ValueError, match="gateway_interaction_contract"):
        module.build_product_entry_manifest(
            profile=profile,
            profile_ref=profile_ref,
        )


def test_startup_contract_appends_latest_task_intake_context(monkeypatch, tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    startup_module = importlib.import_module("med_autoscience.controllers.study_runtime_startup")
    resolution_module = importlib.import_module("med_autoscience.controllers.study_runtime_resolution")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先发现并修复卡住、无进度、figure 质量坏循环等系统性问题。",
        constraints=("先保 runtime supervision truth",),
    )

    monkeypatch.setattr(
        startup_module.startup_boundary_gate_controller,
        "evaluate_startup_boundary",
        lambda **kwargs: {
            "allow_compute_stage": False,
            "required_first_anchor": "scout",
            "effective_custom_profile": "startup_boundary_blocked",
            "legacy_code_execution_allowed": False,
            "missing_requirements": ["paper_framing"],
        },
    )
    monkeypatch.setattr(
        startup_module.runtime_reentry_gate_controller,
        "evaluate_runtime_reentry",
        lambda **kwargs: {"allow_runtime_entry": True},
    )
    monkeypatch.setattr(
        startup_module.journal_shortlist_controller,
        "resolve_journal_shortlist",
        lambda **kwargs: {"status": "not_started", "shortlist": [], "candidate_count": 0, "uncovered_shortlist_entries": []},
    )
    monkeypatch.setattr(
        startup_module.medical_analysis_contract_controller,
        "resolve_medical_analysis_contract_for_study",
        lambda **kwargs: {"status": "resolved"},
    )
    monkeypatch.setattr(
        startup_module.medical_reporting_contract_controller,
        "resolve_medical_reporting_contract_for_study",
        lambda **kwargs: {"status": "resolved", "reporting_guideline_family": "TRIPOD"},
    )

    payload = startup_module._build_startup_contract(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        study_payload=resolution_module._load_yaml_dict(study_root / "study.yaml"),
        execution={"startup_contract_profile": "paper_required_autonomous", "launch_profile": "continue_existing_state"},
    )

    assert payload["task_intake_ref"]["study_id"] == "001-risk"
    assert "figure 质量坏循环" in payload["custom_brief"]
