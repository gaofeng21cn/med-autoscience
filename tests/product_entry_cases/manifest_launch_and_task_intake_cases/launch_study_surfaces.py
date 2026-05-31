from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study

pytestmark = pytest.mark.contract


def test_launch_study_packages_monitoring_progress_and_commands(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    launch_surface = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.launch_surface"
    )
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        launch_surface.domain_status_projection,
        "progress_projection",
        lambda **kwargs: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "typed_blocker": {
                "blocker_type": "opl_provider_admission_required",
                "reason": "mas_private_runtime_transport_retired",
            },
        },
    )
    monkeypatch.setattr(
        launch_surface.study_progress,
        "build_study_progress_projection",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": ["论文叙事或方法/结果书写面仍有硬阻塞。"],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "recommended_command": (
                "uv run python -m med_autoscience.cli study progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [
                {
                    "step_id": "inspect_study_progress",
                    "title": "读取当前研究进度",
                    "surface_kind": "study_progress",
                    "command": (
                        "uv run python -m med_autoscience.cli study progress --profile "
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
                            "uv run python -m med_autoscience.cli study progress --profile "
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
    monkeypatch.setattr(
        launch_surface.study_progress,
        "read_study_progress",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("launch_study should reuse the runtime status payload")),
    )

    payload = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        entry_mode="full_research",
    )

    assert payload["study_id"] == "001-risk"
    assert payload["runtime_status"]["decision"] == "blocked"
    assert payload["runtime_status"]["product_entry_launch_policy"]["status"] == "opl_attempt_admission_required"
    assert payload["runtime_status"]["product_entry_launch_policy"]["mas_executes_runtime_attempt"] is False
    assert payload["progress"]["supervision"]["browser_url"] == "http://127.0.0.1:20999"
    assert payload["progress"]["task_intake"]["journal_target"] == "JAMA Network Open"
    assert payload["progress"]["progress_freshness"]["status"] == "fresh"
    assert payload["progress"]["recovery_contract"]["action_mode"] == "inspect_progress"
    assert payload["commands"]["progress"].endswith("--study-id 001-risk")
    assert "workspace-cockpit" in payload["commands"]["cockpit"]

    markdown = module.render_launch_study_markdown(payload)
    assert markdown.strip()


def test_launch_study_markdown_prefers_shared_human_status_narration() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    from opl_harness_shared.status_narration import build_status_narration_contract

    payload = {
        "study_id": "001-risk",
        "runtime_status": {"decision": "resume"},
        "progress": {
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
            "supervision": {"browser_url": "http://127.0.0.1:20999", "active_run_id": "run-001"},
        },
        "commands": {},
    }

    markdown = module.render_launch_study_markdown(payload)

    assert markdown.strip()
    assert "current_stage_summary:" not in markdown
    assert "next_system_action:" not in markdown


def test_launch_study_markdown_prefers_human_facing_labels() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    payload = {
        "study_id": "001-risk",
        "runtime_status": {"decision": "resume"},
        "progress": {
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": ["论文叙事或方法/结果书写面仍有硬阻塞。"],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "supervision": {"browser_url": "http://127.0.0.1:20999", "active_run_id": "run-001"},
            "task_intake": {
                "task_intent": "优先发现卡住、无进度和 figure 质量回退，再决定是否继续自动推进。",
                "journal_target": "JAMA Network Open",
            },
            "progress_freshness": {"summary": "最近 12 小时内仍有明确研究推进记录。"},
            "recovery_contract": {"action_mode": "inspect_progress", "summary": "论文叙事仍需先修。"},
            "recommended_commands": [
                {
                    "title": "读取当前研究进度",
                    "command": "uv run python -m med_autoscience.cli study progress --profile profile.local.toml --study-id 001-risk",
                }
            ],
        },
        "commands": {
            "progress": "uv run python -m med_autoscience.cli study progress --profile profile.local.toml --study-id 001-risk",
        },
    }

    markdown = module.render_launch_study_markdown(payload)

    assert markdown.strip()
    assert "browser_url:" not in markdown
    assert "task_intent:" not in markdown
    assert "journal_target:" not in markdown
    assert "progress_signal:" not in markdown
    assert "action_mode:" not in markdown
    assert "summary:" not in markdown


__all__ = [name for name in globals() if not name.startswith("__")]
