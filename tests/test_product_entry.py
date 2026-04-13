from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

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
        ),
    )

    monkeypatch.setattr(
        module,
        "_inspect_watch_runtime_service",
        lambda profile: {
            "manager": "launchd",
            "status": "not_loaded",
            "loaded": False,
            "service_file_exists": True,
            "summary": "MAS supervisor service 未常驻在线；如果要持续监管，请先安装或拉起 watch-runtime service。",
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

    def fake_progress(*, profile, study_id: str | None = None, study_root: Path | None = None, entry_mode=None) -> dict:
        resolved_study_id = study_id or Path(study_root).name
        if resolved_study_id == "001-risk":
            return {
                "study_id": resolved_study_id,
                "current_stage": "managed_runtime_supervision_gap",
                "current_stage_summary": "MAS 外环监管存在缺口。",
                "current_blockers": ["MAS 外环监管存在缺口。"],
                "next_system_action": "先恢复 supervisor loop，再继续托管推进。",
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
    assert "MAS 外环监管存在缺口。" in payload["workspace_alerts"]
    assert "图表推进陷入重复打磨循环，当前 run 应被拉回主线。" in payload["workspace_alerts"]
    assert any("距离上一次明确研究推进已经超过 12 小时" in item for item in payload["workspace_alerts"])
    assert payload["workspace_supervision"]["service"]["status"] == "not_loaded"
    assert payload["workspace_supervision"]["study_counts"]["progress_stale"] == 1
    assert payload["attention_queue"][0]["code"] == "workspace_supervisor_service_not_loaded"
    assert payload["attention_queue"][0]["recommended_command"].endswith("watch-runtime-service-status")
    assert any(item["study_id"] == "001-risk" and item["code"] == "study_supervision_gap" for item in payload["attention_queue"])
    assert any(item["study_id"] == "002-risk" and item["code"] == "study_blocked" for item in payload["attention_queue"])
    assert [item["study_id"] for item in payload["studies"]] == ["001-risk", "002-risk"]
    assert payload["studies"][0]["commands"]["launch"].endswith("--study-id 001-risk")
    assert payload["studies"][0]["task_intake"]["journal_target"] == "BMC Medicine"
    assert payload["studies"][1]["monitoring"]["browser_url"] == "http://127.0.0.1:20999"
    assert "mainline-phase --phase current" in payload["user_loop"]["phase_status_current"]
    assert "submit-study-task" in payload["user_loop"]["submit_task_template"]
    assert "study-progress" in payload["user_loop"]["watch_progress_template"]

    markdown = module.render_workspace_cockpit_markdown(payload)
    assert "001-risk" in markdown
    assert "002-risk" in markdown
    assert "Mainline Snapshot" in markdown
    assert "current_program_phase" in markdown
    assert "Attention Queue" in markdown
    assert "User Loop" in markdown
    assert "图表推进陷入重复打磨循环" in markdown
    assert "The Lancet Digital Health" in markdown
    assert "MAS supervisor service 未常驻在线" in markdown
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
    assert payload["commands"]["progress"].endswith("--study-id 001-risk")
    assert "workspace-cockpit" in payload["commands"]["cockpit"]

    markdown = module.render_launch_study_markdown(payload)
    assert "http://127.0.0.1:20999" in markdown
    assert "论文叙事或方法/结果书写面仍有硬阻塞。" in markdown
    assert "优先发现卡住、无进度和 figure 质量回退" in markdown
    assert "最近 12 小时内仍有明确研究推进记录" in markdown


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
    assert payload["return_surface_contract"]["progress_command"].endswith("--study-id 001-risk")
    assert payload["commands"]["workspace_cockpit"].endswith("workspace-cockpit --profile " + str(profile_ref.resolve()))
    assert payload["commands"]["launch_study"].endswith("--study-id 001-risk")


def test_build_product_entry_manifest_projects_repo_shell_and_shared_handoff_templates(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

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
    assert payload["runtime"]["runtime_owner"] == "med_autoscience_gateway"
    assert payload["runtime"]["runtime_substrate"] == "external_hermes_agent_target"
    assert payload["executor_defaults"]["default_executor"] == "codex_cli_autonomous"
    assert payload["executor_defaults"]["default_model"] == "inherit_local_codex_default"
    assert payload["executor_defaults"]["default_reasoning_effort"] == "inherit_local_codex_default"
    assert payload["executor_defaults"]["chat_completion_only_executor_forbidden"] is True
    assert payload["executor_defaults"]["hermes_native_requires_full_agent_loop"] is True
    assert payload["executor_defaults"]["current_backend_chain"][1].endswith(
        "codex exec autonomous agent loop"
    )
    assert payload["workspace_locator"]["profile_name"] == profile.name
    assert payload["recommended_shell"] == "workspace_cockpit"
    assert payload["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve())
    )
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
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
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
    assert payload["product_entry_shell"]["workspace_cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve())
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
    assert "standalone medical product entry" in payload["remaining_gaps"][0]


def test_build_product_frontdesk_projects_frontdoor_over_current_workspace_loop(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    profile = make_profile(tmp_path)

    payload = module.build_product_frontdesk(
        profile=profile,
        profile_ref=profile_ref,
    )

    assert payload["surface_kind"] == "product_frontdesk"
    assert payload["recommended_action"] == "inspect_or_prepare_research_loop"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["frontdesk_surface"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["operator_loop_surface"]["shell_key"] == "workspace_cockpit"
    assert payload["operator_loop_actions"]["open_loop"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve())
    )
    assert payload["entry_surfaces"]["frontdesk"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["entry_surfaces"]["cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve())
    )
    assert payload["entry_surfaces"]["direct_entry_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode direct"
    )
    assert payload["summary"]["frontdesk_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["summary"]["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve())
    )
    assert payload["family_orchestration"]["resume_contract"]["surface_kind"] == "launch_study"
    assert payload["family_orchestration"]["human_gates"][0]["gate_id"] == "study_physician_decision_gate"
    assert payload["product_entry_manifest"]["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["product_entry_manifest"]["manifest_version"] == 2


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
