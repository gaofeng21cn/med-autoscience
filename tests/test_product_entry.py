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
    assert "submit-study-task" in payload["user_loop"]["submit_task_template"]
    assert "study-progress" in payload["user_loop"]["watch_progress_template"]

    markdown = module.render_workspace_cockpit_markdown(payload)
    assert "001-risk" in markdown
    assert "002-risk" in markdown
    assert "Mainline Snapshot" in markdown
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
