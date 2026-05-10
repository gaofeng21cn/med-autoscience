from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _runtime_continuity_payload() -> dict[str, object]:
    return {
        "runtime_session": {
            "worker_state": "stale",
            "worker_running": False,
            "active_run_id": None,
            "last_known_run_id": "run-stale-001",
            "runtime_liveness_status": "stale",
            "last_seen_at": "2026-05-08T00:40:00+00:00",
            "monitor_kind": "mas_per_run_worker_wrapper",
            "monitor_state": "stale",
            "heartbeat_age_seconds": 420,
            "last_output_at": "2026-05-08T00:38:00+00:00",
            "stale_reason": "heartbeat_ttl_exceeded",
            "will_start_llm": False,
            "freshness_state": "stale",
            "freshness_age_seconds": 1500,
            "evidence_refs": ["studies/001-risk/artifacts/runtime/session/latest.json"],
        },
        "recovery_intent": {
            "current_action": "safe_reconcile_ready",
            "reason": "worker_stale",
            "next_owner": "mas_controller",
            "next_eligible_tick": "2026-05-08T01:10:00+00:00",
            "dedupe_fingerprint": "runtime-continuity-001",
            "authority": {
                "quality_ready_authorized": False,
                "publication_ready_authorized": False,
                "submission_ready_authorized": False,
            },
            "evidence_refs": ["studies/001-risk/artifacts/runtime/recovery_intent/latest.json"],
        },
        "runtime_reconcile_trigger": {
            "safe_to_request": True,
            "recommended_command": (
                "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
                "--profile /workspace/profile.toml --studies 001-risk --dry-run"
            ),
            "dedupe_fingerprint": "runtime-continuity-001",
            "will_start_llm": False,
            "source_refs": ["studies/001-risk/artifacts/runtime/owner_route/latest.json"],
        },
        "owner_route": {
            "next_owner": "mas_controller",
            "owner_reason": "runtime_stale",
            "source_fingerprint": "runtime-continuity-001",
            "work_unit_fingerprint": "runtime-continuity-001",
            "source_refs": {
                "runtime_health_epoch": "runtime-health-001",
                "publication_eval_path": "studies/001-risk/artifacts/publication_eval/latest.json",
            },
        },
        "paper_progress_stall": {
            "why_not_running": "worker heartbeat is stale; no new manuscript artifact delta",
            "same_fingerprint_or_handoff": "same_fingerprint",
            "source_refs": ["studies/001-risk/artifacts/autonomy/slo_status/latest.json"],
        },
    }


def _progress_payload(study_id: str = "001-risk") -> dict[str, object]:
    return {
        "study_id": study_id,
        "generated_at": "2026-05-08T01:00:00+00:00",
        "user_visible_projection": {
            "schema_version": 2,
            "writer_state": "live",
            "user_next": "wait",
            "reason": "quality_repair",
            "state_label": "质量修复/复审中",
            "state_summary": "正在补齐统计和证据账本，当前无需医生操作。",
            "current_stage": "quality_repair",
            "current_stage_summary": "AI reviewer 要求补充 subgroup sensitivity analysis。",
            "paper_stage": "revision",
            "paper_stage_summary": "论文主线处于返修强化阶段。",
            "current_blockers": ["subgroup sensitivity table 尚未刷新"],
            "next_system_action": "补充 subgroup 分析并更新 review ledger。",
            "needs_physician_decision": False,
            "evidence": {
                "latest_events": [
                    {
                        "timestamp": "2026-05-08T00:58:00+00:00",
                        "summary": "完成 reviewer gap triage。",
                    }
                ],
                "refs": [
                    "studies/001-risk/artifacts/runtime/runtime_supervision/latest.json",
                ],
            },
            "evidence_refs": [
                "studies/001-risk/artifacts/controller_decisions/latest.json",
            ],
        },
        "progress_freshness": {
            "status": "stale",
            "summary": "最近 90 分钟没有新的可见写作推进。",
            "latest_event_at": "2026-05-08T00:58:00+00:00",
        },
        "publication_eval": {
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "证据链仍需补强。",
            },
            "quality_assessment": {
                "statistics": {
                    "status": "blocked",
                    "summary": "缺少 subgroup sensitivity table。",
                }
            },
        },
        "delivery_inspection": {
            "current_package": {
                "status": "missing",
                "summary": "current package 尚未生成。",
            }
        },
        "supervision": {
            "active_run_id": "run-001",
            "supervisor_tick_status": "fresh",
        },
        "outer_supervision_slo": {
            "surface_kind": "outer_supervision_slo",
            "state": "fresh",
            "latest_outer_supervision_at": "2026-05-08T00:59:00+00:00",
        },
        "refs": {
            "study_runtime_status": "studies/001-risk/artifacts/runtime/status.json",
            "runtime_watch": "studies/001-risk/artifacts/runtime_watch/latest.json",
            "publication_eval": "studies/001-risk/artifacts/publication_eval/latest.json",
        },
    }


def test_progress_portal_payload_projects_core_status_and_fail_closed_conditions() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        cockpit_payload={
            "workspace_status": "attention_required",
            "workspace_alerts": ["workspace supervisor needs attention"],
            "studies": [{"study_id": "other-study", "state_label": "自动运行中"}],
        },
        runtime_payload={
            "study_id": "001-risk",
            "supervisor_tick_audit": {"status": "missing"},
        },
        package_payload={
            "study_id": "other-study",
            "status": "current",
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert payload["surface_kind"] == "mas_progress_portal"
    assert payload["brand"] == "Med Auto Science"
    assert payload["generated_at"] == "2026-05-08T01:05:00+00:00"
    assert payload["workspace"]["profile_name"] == "diabetes"
    assert payload["study"]["study_id"] == "001-risk"
    assert payload["study"]["state_label"] == "质量修复/复审中"
    assert payload["study"]["next_system_action"] == "补充 subgroup 分析并更新 review ledger。"
    assert payload["freshness"]["status"] == "stale"
    assert payload["conditions"]["stale"] == ["progress_freshness"]
    assert "runtime_supervisor_tick" in payload["conditions"]["missing"]
    assert payload["conditions"]["conflict"] == ["cockpit_study_id_mismatch", "package_study_id_mismatch"]
    assert "studies/001-risk/artifacts/publication_eval/latest.json" in payload["source_refs"]
    assert payload["quality"]["summary"] == "证据链仍需补强。"
    assert payload["delivery"]["summary"] == "current package 尚未生成。"
    assert payload["live_console"] == {
        "available": True,
        "label": "运行控制台",
        "html_ref": "ops/mas/live-console/index.html",
        "href": "../../../live-console/index.html?study_id=001-risk",
        "scope": "study",
        "study_id": "001-risk",
        "capability_badge": "单篇运行控制台",
        "session_read_model_ref": "artifacts/runtime/live_console/session_read_model/latest.json",
        "serve_command": "medautosci runtime live-console --profile <profile> --serve",
        "authority": "read_only_runtime_observation",
        "disabled_reason": None,
    }


def test_progress_portal_payload_can_disable_live_console_link_with_reason() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
        live_console_disabled_reason="runtime live console read model is not installed",
    )
    html = module.render_progress_portal_html(payload)

    assert payload["live_console"]["available"] is False
    assert payload["live_console"]["disabled_reason"] == "runtime live console read model is not installed"
    assert "运行控制台不可用" in html
    assert "runtime live console read model is not installed" in html
    assert "terminal/log stream" not in html


def test_progress_portal_profile_without_study_selector_projects_workspace_overview() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        cockpit_payload={
            "workspace_status": "active",
            "studies": [
                {"study_id": "001-dm-cvd-mortality-risk", "current_stage": "parked"},
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "current_stage": "live",
                    "monitoring": {"active_run_id": "run-dm002"},
                },
                {"study_id": "003-dpcc-primary-care-phenotype-treatment-gap", "current_stage": "write"},
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert payload["study"]["scope"] == "workspace"
    assert payload["study"]["study_id"] == "workspace-overview"
    assert payload["study"]["state_label"] == "工作区概览"
    assert all(item["selected"] is False for item in payload["workspace"]["studies"])
    assert payload["section_explanations"][0]["source"] == "workspace_cockpit"
    assert {
        item["current_output"]
        for item in payload["section_explanations"]
    } >= {"工作区概要", "论文线概览", "工作区告警", "诊断与修复建议", "数据来源"}
    html = module.render_progress_portal_html(payload)
    assert "页面条目说明" in html
    assert "<dt>当前论文线</dt><dd>工作区总览</dd>" in html
    assert "workspace_cockpit.studies" in html
    assert "section_explanations" not in html
    assert "publication evaluation projection 缺失" not in html
    assert "current package projection 缺失" not in html
    assert "质量投影缺失" not in html
    assert "交付投影缺失" not in html


def test_progress_portal_payload_projects_distinct_workspace_studies_and_suppresses_legacy_alert_noise() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        progress_payload=_progress_payload("003-dpcc-primary-care-phenotype-treatment-gap"),
        cockpit_payload={
            "workspace_status": "blocked",
            "workspace_alerts": [
                "Hermes-hosted runtime supervision 尚未注册。",
                "状态需要检查。",
                "用户暂停或手动停驻，需显式恢复或新方案。",
                "live worker 已超过 meaningful artifact delta 活动窗口，必须先恢复产物增量或写出平台修复终态。",
            ],
            "studies": [
                {
                    "study_id": "001-dm-cvd-mortality-risk",
                    "state_label": "用户暂停/手动停驻",
                    "state_summary": "用户暂停/手动停驻；当前没有实际写入，需显式恢复或给出新方案。",
                    "current_stage": "parked",
                    "monitoring": {},
                    "progress_freshness": {"status": "stale", "summary": "用户暂停或手动停驻，需显式恢复或新方案。"},
                },
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "state_label": "自动运行中",
                    "state_summary": "自动运行中；系统有实际 writer/run 正在推进。",
                    "current_stage": "live",
                    "paper_stage": "analysis-campaign",
                    "monitoring": {
                        "active_run_id": "mas-run-002",
                        "health_status": "recovering",
                        "supervisor_tick_status": "stale",
                    },
                    "progress_freshness": {
                        "status": "stale",
                        "summary": "live worker 已超过 meaningful artifact delta 活动窗口，必须先恢复产物增量或写出平台修复终态。",
                    },
                    "intervention_lane": {"title": "优先处理 activity timeout"},
                },
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "state_label": "自动运行中",
                    "state_summary": "自动运行中；系统有实际 writer/run 正在推进。",
                    "current_stage": "live",
                    "paper_stage": "write",
                    "monitoring": {
                        "active_run_id": "mas-run-003",
                        "health_status": "recovering",
                        "supervisor_tick_status": "stale",
                    },
                    "progress_freshness": {
                        "status": "stale",
                        "summary": "最近监管可能新鲜，但 meaningful artifact delta 已过期。",
                    },
                    "next_system_action": "观察自动运行推进。",
                },
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    workspace = payload["workspace"]
    assert workspace["workspace_alerts"] == ["进度信号：有记录，但 worker 或 artifact delta 不满足继续推进证据。"]
    assert workspace["workspace_alert_items"][0]["source"] == "workspace_cockpit.progress_freshness"
    assert workspace["workspace_alert_items"][0]["purpose"]
    assert workspace["workspace_alert_items"][0]["current_output"] == "进度信号：有记录，但 worker 或 artifact delta 不满足继续推进证据。"
    assert workspace["workspace_alert_items"][0]["expected"]
    assert workspace["diagnostics"]["suppressed_alerts"] == [
        "MAS scheduler runtime supervision 尚未注册。",
        "用户暂停或手动停驻，需显式恢复或新方案。",
    ]
    assert workspace["diagnostics"]["suppressed_alert_items"][0]["source"] == "workspace_supervision.service.summary"
    assert workspace["diagnostics"]["suppressed_alert_items"][0]["recommended_command"] == (
        "uv run python -m med_autoscience.cli runtime-ensure-supervision --profile <profile>"
    )
    studies = workspace["studies"]
    assert [item["study_id"] for item in studies] == [
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    dm002 = studies[1]
    assert dm002["active_run_id"] == "mas-run-002"
    assert dm002["runtime_health_status"] == "recovering"
    assert dm002["supervisor_tick_status"] == "stale"
    assert dm002["paper_stage"] == "analysis-campaign"
    assert dm002["operator_focus"] == "优先处理 activity timeout"
    dpcc003 = studies[2]
    assert dpcc003["active_run_id"] == "mas-run-003"
    assert dpcc003["paper_stage"] == "write"


def test_progress_portal_html_deduplicates_repeated_status_copy_and_renders_workspace_studies() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    repeated = "自动运行中；系统有实际 writer/run 正在推进。"
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        progress_payload={
            **_progress_payload("003-dpcc-primary-care-phenotype-treatment-gap"),
            "user_visible_projection": {
                **_progress_payload("003-dpcc-primary-care-phenotype-treatment-gap")["user_visible_projection"],
                "state_label": "自动运行中",
                "state_summary": repeated,
                "current_stage": "live",
                "current_stage_summary": repeated,
                "paper_stage": "write",
                "paper_stage_summary": repeated,
            },
        },
        cockpit_payload={
            "workspace_alerts": ["Hermes-hosted runtime supervision 尚未注册。"],
            "studies": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "state_label": "自动运行中",
                    "current_stage": "live",
                    "paper_stage": "analysis-campaign",
                    "monitoring": {
                        "active_run_id": "mas-run-002",
                        "health_status": "recovering",
                        "supervisor_tick_status": "stale",
                    },
                    "progress_freshness": {"status": "stale", "summary": "artifact delta stale"},
                },
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "state_label": "自动运行中",
                    "current_stage": "live",
                    "paper_stage": "write",
                    "monitoring": {
                        "active_run_id": "mas-run-003",
                        "health_status": "recovering",
                        "supervisor_tick_status": "stale",
                    },
                    "progress_freshness": {"status": "stale", "summary": "artifact delta stale"},
                },
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    html = module.render_progress_portal_html(payload)

    assert html.count(f"<p>{repeated}</p>") == 1
    assert "论文线概览" in html
    assert "002-dm-china-us-mortality-attribution" in html
    assert "003-dpcc-primary-care-phenotype-treatment-gap" in html
    assert "mas-run-002" in html
    assert "mas-run-003" in html
    assert "诊断与修复建议" in html
    assert "MAS scheduler runtime supervision 尚未注册。" in html
    assert "Hermes-hosted runtime supervision 尚未注册。" not in html
    assert "runtime-ensure-supervision" in html
    assert ">none<" not in html
    assert "not_required" not in html
    assert "来源" in html
    assert "用途" in html
    assert "当前输出" in html
    assert "期望输出" in html


def test_progress_portal_projects_local_scheduler_drift_with_repair_command() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        cockpit_payload={
            "workspace_alerts": [
                "MAS local scheduler 尚未安装或存在漂移；运行 runtime-ensure-supervision 可刷新。"
            ],
            "studies": [],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    item = payload["workspace"]["workspace_alert_items"][0]
    assert item["source"] == "workspace_supervision.service.summary"
    assert item["current_output"] == "MAS local scheduler 尚未安装或存在漂移；运行 runtime-ensure-supervision 可刷新。"
    assert item["recommended_command"] == (
        "uv run python -m med_autoscience.cli runtime-ensure-supervision --profile <profile>"
    )
    html = module.render_progress_portal_html(payload)
    assert "MAS local scheduler 尚未安装或存在漂移；运行 runtime-ensure-supervision 可刷新。" in html
    assert "workspace_supervision.service.summary" in html
    assert "runtime-ensure-supervision" in html


def test_progress_portal_hides_low_information_generic_status_diagnostic_when_study_rows_exist() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        cockpit_payload={
            "workspace_alerts": ["状态需要检查。"],
            "studies": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "monitoring": {"health_status": "escalated"},
                    "progress_freshness": {"status": "not_required"},
                }
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    html = module.render_progress_portal_html(payload)

    assert payload["workspace"]["diagnostics"]["suppressed_alert_items"] == []
    assert "状态需要检查。" not in html
    assert "无需自动推进" in html
    assert "not_required" not in html
    assert "无运行编号" in html
    assert ">none<" not in html


def test_progress_portal_html_header_is_workspace_scoped_and_shows_explicit_local_time() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        progress_payload=_progress_payload("003-dpcc-primary-care-phenotype-treatment-gap"),
        generated_at="2026-05-08T01:05:00+00:00",
        local_timezone="Asia/Shanghai",
    )

    html = module.render_progress_portal_html(payload)

    assert "<h1>diabetes</h1>" in html
    assert "<h1>003-dpcc-primary-care-phenotype-treatment-gap</h1>" not in html
    assert "<dt>当前论文线</dt><dd>003-dpcc-primary-care-phenotype-treatment-gap</dd>" in html
    assert "<dt>本机时间</dt><dd>2026-05-08 09:05:00 +08:00" in html
    assert "Asia/Shanghai" in html
    assert "<dt>UTC 时间</dt><dd>2026-05-08T01:05:00+00:00</dd>" in html


def test_progress_portal_default_local_time_uses_iana_timezone_from_env(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    monkeypatch.setenv("TZ", "Asia/Shanghai")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        progress_payload=_progress_payload("003-dpcc-primary-care-phenotype-treatment-gap"),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert payload["generated_at_local"] == {
        "timezone": "Asia/Shanghai",
        "iso": "2026-05-08T09:05:00+08:00",
        "label": "2026-05-08 09:05:00 +08:00 Asia/Shanghai",
    }


def test_progress_portal_default_local_time_resolves_macos_localtime_symlink(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    local_time = importlib.import_module("med_autoscience.controllers.progress_portal_parts.local_time")
    monkeypatch.delenv("TZ", raising=False)
    monkeypatch.setattr(
        local_time,
        "localtime_symlink_target",
        lambda: "/var/db/timezone/zoneinfo/Asia/Shanghai",
    )
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        progress_payload=_progress_payload("003-dpcc-primary-care-phenotype-treatment-gap"),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert payload["generated_at_local"]["timezone"] == "Asia/Shanghai"
    assert payload["generated_at_local"]["label"] == "2026-05-08 09:05:00 +08:00 Asia/Shanghai"


def test_progress_portal_payload_exposes_family_level_opl_handoff_without_new_truth() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        package_payload={
            "study_id": "001-risk",
            "status": "current",
            "summary": "current package is ready.",
            "refs": [
                "studies/001-risk/manuscript/current_package",
                "studies/001-risk/manuscript/current_package.zip",
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    handoff = payload["opl_handoff"]
    assert handoff["handoff_kind"] == "mas_progress_portal_opl_family_projection"
    assert handoff["owner"] == "mas"
    assert handoff["role"] == "family_level_projection"
    assert handoff["authority"] == "display_artifact_only"
    assert handoff["opl_role"] == "family_level_projection_consumer_only"
    assert handoff["payload_refs"]["progress_portal"] == "artifacts/runtime/progress_portal/latest.json"
    assert handoff["payload_refs"]["source_payloads"] == payload["source_payloads"]
    assert handoff["freshness"] == payload["freshness"]
    assert handoff["source_refs"] == payload["source_refs"]
    assert handoff["artifact_locators"] == [
        "studies/001-risk/manuscript/current_package",
        "studies/001-risk/manuscript/current_package.zip",
    ]
    assert handoff["deep_link"] == "ops/mas/progress/index.html"
    assert handoff["forbidden_authority"] == [
        "study_truth",
        "publication_judgment",
        "quality_verdict",
        "runtime_authority",
        "artifact_authority",
    ]


def test_progress_portal_projects_runtime_continuity_without_new_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_progress_payload(),
        **_runtime_continuity_payload(),
    }

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        generated_at="2026-05-08T01:05:00+00:00",
    )
    html = module.render_progress_portal_html(payload)

    continuity = payload["study"]["runtime_continuity"]
    impact = payload["study"]["production_blocker_impact"]
    assert continuity["runtime_session"]["worker_state"] == "stale"
    assert continuity["runtime_session"]["last_seen_at"] == "2026-05-08T00:40:00+00:00"
    assert continuity["runtime_session"]["last_known_run_id"] == "run-stale-001"
    assert continuity["runtime_session"]["monitor_kind"] == "mas_per_run_worker_wrapper"
    assert continuity["runtime_session"]["heartbeat_age_seconds"] == 420
    assert continuity["runtime_session"]["will_start_llm"] is False
    assert continuity["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert continuity["recovery_intent"]["next_owner"] == "mas_controller"
    assert continuity["recovery_intent"]["authority"] == {
        "quality_ready_authorized": False,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
    }
    assert impact["surface_kind"] == "mas_production_blocker_impact_projection"
    assert impact["affects_output"] is True
    assert impact["next_owner"] == "mas_controller"
    assert impact["why_not_running"] == "worker heartbeat is stale; no new manuscript artifact delta"
    assert impact["same_fingerprint_or_handoff"] == "same_fingerprint"
    assert impact["will_start_llm"] is False
    assert impact["safe_reconcile_command"].endswith("--studies 001-risk --dry-run")
    assert impact["route"]["source_fingerprint"] == "runtime-continuity-001"
    assert "studies/001-risk/artifacts/runtime/owner_route/latest.json" in impact["source_refs"]
    assert impact["authority"]["writes_authority_surface"] is False
    assert payload["opl_handoff"]["runtime_continuity"]["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert payload["opl_handoff"]["production_blocker_impact"]["safe_reconcile_command"] == impact["safe_reconcile_command"]
    assert "last worker heartbeat" in html
    assert "will start LLM" in html
    assert "safe_reconcile_ready" in html
    assert "是否影响产出" in html
    assert "safe reconcile command" in html
    assert "--studies 001-risk --dry-run" in html
    assert "run-stale-001" in html
    assert "quality_ready_authorized" not in html
    assert "MDS" not in html


def test_progress_portal_projects_outer_supervision_slo_conditions() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = {
        **_progress_payload(),
        "outer_supervision_slo": {
            "surface_kind": "outer_supervision_slo",
            "state": "due",
            "recommended_command": (
                "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
                "--profile /workspace/profile.toml --studies 001-risk --mode developer_apply_safe --dry-run"
            ),
        },
    }

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert payload["study"]["outer_supervision_slo"]["state"] == "due"
    assert "outer_supervision_slo_due" in payload["conditions"]["stale"]


def test_workspace_cockpit_study_item_projects_runtime_continuity() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_payload")
    progress = {
        **_progress_payload(),
        **_runtime_continuity_payload(),
    }

    item = module._study_item(progress_payload=progress, profile_ref="/workspace/profile.toml")

    continuity = item["runtime_continuity"]
    impact = item["production_blocker_impact"]
    assert continuity["runtime_session"]["worker_state"] == "stale"
    assert continuity["runtime_session"]["last_known_run_id"] == "run-stale-001"
    assert continuity["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert continuity["recovery_intent"]["authority"]["submission_ready_authorized"] is False
    assert impact["next_owner"] == "mas_controller"
    assert impact["affects_output"] is True
    assert impact["same_fingerprint_or_handoff"] == "same_fingerprint"
    assert impact["will_start_llm"] is False
    assert item["outer_supervision_slo"]["state"] == "fresh"


def test_progress_portal_html_is_single_file_mas_view_without_default_mds_product_semantics() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    html = module.render_progress_portal_html(payload)

    assert html.startswith("<!doctype html>")
    assert "Med Auto Science" in html
    assert "UTC 时间" in html
    assert "进度新鲜度" in html
    assert "数据来源" in html
    assert "stale" in html
    assert "subgroup sensitivity table 尚未刷新" in html
    assert "<link " not in html
    assert "<script src=" not in html
    assert "MDS" not in html
    assert "DeepScientist" not in html


def test_progress_portal_html_source_refs_are_bounded_and_do_not_render_legacy_mds_paths() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )
    payload["source_refs"] = [
        "/workspace/ops/med-deepscientist/runtime/quests/001-risk/.ds/worktrees/paper",
        "/workspace/studies/001-risk/artifacts/runtime/health/latest.json",
        "/workspace/studies/001-risk/artifacts/runtime/runtime_supervision/latest.json",
        "/workspace/studies/001-risk/artifacts/controller_decisions/latest.json",
        "/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
        "not/a/selected/source/ref",
    ] + [f"/workspace/legacy/{index:03d}.json" for index in range(40)]

    html = module.render_progress_portal_html(payload)

    assert "/workspace/studies/001-risk/artifacts/runtime/health/latest.json" in html
    assert "/workspace/studies/001-risk/artifacts/controller_decisions/latest.json" in html
    assert "med-deepscientist" not in html
    assert "not/a/selected/source/ref" not in html
    assert "数据来源 (4/46)" in html


def test_progress_portal_payload_source_refs_filter_legacy_runtime_paths() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload={
            **_progress_payload(),
            "refs": {
                "legacy": "/workspace/ops/med-deepscientist/runtime/quests/001/.ds/worktrees/paper",
                "health": "/workspace/studies/001-risk/artifacts/runtime/health/latest.json",
            },
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert "/workspace/studies/001-risk/artifacts/runtime/health/latest.json" in payload["source_refs"]
    assert all("med-deepscientist" not in ref and ".ds/worktrees" not in ref for ref in payload["source_refs"])


def test_study_workbench_helper_projects_path_stage_artifacts_and_source_refs_without_filename_inference() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress={
            **_progress_payload(),
            "route_decision_trail": {
                "active_path": "analysis-route-b",
                "winning_path": "analysis-route-b",
                "nodes": [
                    {
                        "route_id": "analysis-route-a",
                        "label": "Start with broad risk model",
                        "evidence_point": "calibration audit",
                        "blocked_reason": "external validation failed",
                        "pivot_rationale": "route B has transportable subgroup evidence",
                        "superseded_by": "analysis-route-b",
                    }
                ],
                "source_refs": ["studies/001-risk/artifacts/controller_decisions/latest.json"],
            },
            "artifact_locators": [
                {
                    "group": "draft",
                    "label": "canonical manuscript draft",
                    "ref": "studies/001-risk/paper/manuscript.md",
                    "status": "fresh",
                },
                {
                    "category": "review_proof",
                    "label": "AI reviewer proof",
                    "path": "studies/001-risk/artifacts/publication_eval/latest.json",
                    "status": "blocked",
                },
                {
                    "label": "looks like a figure but has no explicit group",
                    "ref": "studies/001-risk/manuscript/current_package/figures/Figure1.png",
                },
            ],
            "delivery_refs": [
                {
                    "kind": "figures_tables",
                    "label": "Table 1",
                    "ref": "studies/001-risk/paper/tables/table1.csv",
                }
            ],
        },
        cockpit={
            "studies": [
                {
                    "study_id": "001-risk",
                    "current_stage": "cockpit-stage",
                    "paper_stage": "cockpit-paper-stage",
                    "monitoring": {"health_status": "recovering"},
                }
            ]
        },
        runtime={
            "study_id": "001-risk",
            "active_run_id": "run-001",
            "artifact_locators": [
                {
                    "group": "runtime_evidence",
                    "label": "runtime supervision",
                    "ref": "studies/001-risk/artifacts/runtime/runtime_supervision/latest.json",
                }
            ],
        },
        package={
            "study_id": "001-risk",
            "refs": [
                "studies/001-risk/manuscript/current_package",
                "studies/001-risk/manuscript/current_package.zip",
            ],
        },
        study_id="001-risk",
    )

    assert payload["surface_kind"] == "mas_progress_portal_study_workbench"
    assert payload["tabs"][1] == {"id": "route_decision_trail", "label": "路线/决策", "status": "available"}
    assert payload["route_decision_trail"]["surface_kind"] == "mas_progress_portal_route_decision_trail"
    assert payload["route_decision_trail"]["active_path"] == "analysis-route-b"
    assert payload["route_decision_trail"]["winning_path"] == "analysis-route-b"
    assert payload["route_decision_trail"]["nodes"][0] == {
        "route_id": "analysis-route-a",
        "label": "Start with broad risk model",
        "decision": None,
        "evidence_point": "calibration audit",
        "blocked_reason": "external validation failed",
        "pivot_rationale": "route B has transportable subgroup evidence",
        "superseded_by": "analysis-route-b",
        "source": "route_decision_trail.nodes",
    }
    assert payload["route_decision_trail"]["authority"]["writes_authority_surface"] is False
    assert payload["route_decision_trail"]["authority"]["forbidden_authority"] == [
        "study_truth",
        "publication_judgment",
        "quality_verdict",
        "runtime_authority",
        "artifact_authority",
        "controller_decision_authority",
    ]
    assert payload["path_stage"]["current_stage"] == "quality_repair"
    assert payload["path_stage"]["paper_stage"] == "revision"
    assert payload["runtime"]["active_run_id"] == "run-001"
    assert payload["artifact_groups"]["draft"]["items"][0]["ref"] == "studies/001-risk/paper/manuscript.md"
    assert payload["artifact_groups"]["figures_tables"]["items"][0]["ref"] == "studies/001-risk/paper/tables/table1.csv"
    assert payload["artifact_groups"]["current_package"]["items"] == [
        {
            "ref": "studies/001-risk/manuscript/current_package",
            "label": "studies/001-risk/manuscript/current_package",
            "status": "available",
            "source": "package.refs",
        },
        {
            "ref": "studies/001-risk/manuscript/current_package.zip",
            "label": "studies/001-risk/manuscript/current_package.zip",
            "status": "available",
            "source": "package.refs",
        },
    ]
    assert payload["artifact_groups"]["review_proof"]["items"][0]["status"] == "blocked"
    assert payload["artifact_groups"]["runtime_evidence"]["items"][0]["ref"].endswith(
        "runtime_supervision/latest.json"
    )
    all_refs = [
        item["ref"]
        for group in payload["artifact_groups"].values()
        for item in group["items"]
    ]
    assert "studies/001-risk/manuscript/current_package/figures/Figure1.png" not in all_refs
    assert "artifact_group:draft" not in payload["conditions"]["missing"]
    assert "artifact_group:figures_tables" not in payload["conditions"]["missing"]
    assert "artifact_group:current_package" not in payload["conditions"]["missing"]
    assert "artifact_group:review_proof" not in payload["conditions"]["missing"]
    assert "artifact_group:runtime_evidence" not in payload["conditions"]["missing"]
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in payload["source_refs"]
    assert payload["tabs"][4] == {"id": "artifacts", "label": "产物", "status": "available"}


def test_study_workbench_helper_renders_conversation_read_model_timeline() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    conversation_payload = {
        "surface_kind": "mas_runtime_conversation_read_model",
        "selected_study_id": "001-risk",
        "read_only": True,
        "timeline_summary": {
            "item_count": 3,
            "counts_by_kind": {
                "user_message": 1,
                "turn_receipt": 1,
                "runtime_control_ref": 1,
            },
        },
        "timeline": [
            {
                "sequence": 1,
                "item_kind": "user_message",
                "study_id": "001-risk",
                "message_id": "msg-pending",
                "message_status": "pending",
                "content_ref": "content_present",
                "source_ref": "runtime/quests/001/artifacts/runtime/user_message_queue.json",
            },
            {
                "sequence": 2,
                "item_kind": "turn_receipt",
                "study_id": "001-risk",
                "run_id": "run-001",
                "turn_reason": "queued_user_messages",
                "turn_status": "completed",
                "source_ref": "runtime/quests/001/artifacts/runtime/turn_receipts.jsonl",
            },
            {
                "sequence": 3,
                "item_kind": "runtime_control_ref",
                "study_id": "001-risk",
                "event_name": "blocked_waiting_for_user",
                "blocker_refs": [{"kind": "blocking_decision_request", "value": "confirm next route"}],
                "source_ref": "runtime/quests/001/.ds/runtime_state.json",
            },
            {
                "sequence": 4,
                "item_kind": "turn_receipt",
                "study_id": "other-study",
                "run_id": "run-other",
                "source_ref": "runtime/quests/other/artifacts/runtime/turn_receipts.jsonl",
            },
        ],
        "source_refs": [
            {
                "surface_kind": "user_message_queue",
                "study_id": "001-risk",
                "source_ref": "runtime/quests/001/artifacts/runtime/user_message_queue.json",
                "read_only": True,
            },
            {
                "surface_kind": "turn_receipts_jsonl",
                "study_id": "001-risk",
                "source_ref": "runtime/quests/001/artifacts/runtime/turn_receipts.jsonl",
                "read_only": True,
            },
            {
                "surface_kind": "turn_receipts_jsonl",
                "study_id": "other-study",
                "source_ref": "runtime/quests/other/artifacts/runtime/turn_receipts.jsonl",
                "read_only": True,
            },
        ],
    }

    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
        conversation_payload=conversation_payload,
    )
    html = parts.render_study_workbench_sections(payload)

    assert {"id": "conversation", "label": "Conversation", "status": "available"} in payload["tabs"]
    assert payload["conversation"]["surface_kind"] == "mas_progress_portal_conversation_panel"
    assert payload["conversation"]["status"] == "available"
    assert [item["item_kind"] for item in payload["conversation"]["timeline_items"]] == [
        "user_message",
        "turn_receipt",
        "runtime_control_ref",
    ]
    assert "runtime/quests/other/artifacts/runtime/turn_receipts.jsonl" not in json.dumps(
        payload["conversation"],
        ensure_ascii=False,
    )
    assert "Conversation" in html
    assert "user_message" in html
    assert "msg-pending" in html
    assert "turn_receipt" in html
    assert "run-001" in html
    assert "blocked_waiting_for_user" in html
    assert "confirm next route" in html
    assert "runtime/quests/001/artifacts/runtime/turn_receipts.jsonl" in html
    assert "run-other" not in html


def test_progress_portal_materialization_surfaces_selected_study_conversation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {"study_id": study_id, "quest_id": quest_id, "quest_root": str(quest_root), "active_run_id": "run-001"},
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "user_message_queue.json",
        {
            "pending": [
                {
                    "message_id": "msg-portal",
                    "content": "解释当前阻塞。",
                    "recorded_at": "2026-05-09T01:00:00+00:00",
                }
            ],
            "completed": [],
        },
    )
    _write_text(
        quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl",
        json.dumps(
            {
                "run_id": "run-001",
                "reason": "user_message",
                "status": "completed",
                "recorded_at": "2026-05-09T01:01:00+00:00",
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    result = module.materialize_progress_portal(
        profile=profile,
        study_id=study_id,
        progress_payload=_progress_payload(study_id),
        runtime_payload={"study_id": study_id, "active_run_id": "run-001"},
        package_payload={"study_id": study_id},
        generated_at="2026-05-09T01:02:00+00:00",
    )

    payload_path = Path(result["study_pages"][study_id]["payload_path"])
    html_path = Path(result["study_pages"][study_id]["html_path"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")
    assert payload["study_workbench"]["conversation"]["status"] == "available"
    assert "Conversation" in html
    assert "msg-portal" in html
    assert "run-001" in html
    assert "artifacts/runtime/conversation_read_model/latest.json" in payload["study_workbench"]["conversation"][
        "source_refs"
    ]


def test_study_workbench_helper_fail_closes_missing_inputs_and_conflicts() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress={},
        cockpit={"studies": [{"study_id": "other-study"}]},
        runtime={"study_id": "other-study"},
        package={"study_id": "other-study"},
        study_id="001-risk",
    )

    assert payload["overview"]["state_label"] is None
    assert payload["path_stage"]["current_stage"] is None
    assert payload["source_refs"] == []
    assert payload["artifact_groups"]["draft"]["status"] == "missing"
    assert payload["artifact_groups"]["current_package"]["status"] == "missing"
    assert payload["conditions"]["missing"] == [
        "study_progress",
        "user_visible_projection_v2",
        "source_refs",
        "runtime_active_run_id",
        "artifact_group:draft",
        "artifact_group:figures_tables",
        "artifact_group:current_package",
        "artifact_group:review_proof",
        "artifact_group:runtime_evidence",
        "route_decision_trail:route_decision_trail",
        "route_decision_trail:route_nodes",
    ]
    assert payload["conditions"]["conflict"] == [
        "runtime_study_id_mismatch",
        "package_study_id_mismatch",
        "cockpit_study_id_mismatch",
    ]
    assert payload["conversation"]["status"] == "missing"


def test_study_workbench_render_helper_returns_html_sections() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk", "refs": ["studies/001-risk/manuscript/current_package.zip"]},
        study_id="001-risk",
    )

    html = parts.render_study_workbench_sections(payload)

    assert "单篇论文工作台" in html
    assert "Route / Decision Trail" in html
    assert "缺少显式路线节点" in html
    assert "路径与阶段" in html
    assert "当前交付包" in html
    assert "studies/001-risk/manuscript/current_package.zip" in html
    assert "缺少 source refs。" not in html


def test_route_decision_trail_helper_projects_branch_block_pivot_and_winning_path() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_route_decision_trail_payload(
        progress={
            "study_id": "001-risk",
            "controller_decision": {
                "decision_type": "study_line_route_decision",
                "route_decision": "switch_line",
                "route_target": "route-b",
                "selected_line_id": "route-b",
                "route_rationale": "route A blocked at validation; route B preserves the claim boundary.",
                "blockers": ["route-a_external_validation_failed"],
                "candidate_path_graph": {
                    "surface": "candidate_path_graph",
                    "authority": "read_model_only",
                    "selected_candidate_id": "route-b",
                    "candidates": [
                        {
                            "candidate_id": "route-a",
                            "question": "Can broad model generalize?",
                            "decision": "stop",
                            "evidence_basis": ["external validation AUC dropped"],
                            "stop_rule": "stop if external validation fails",
                        },
                        {
                            "candidate_id": "route-b",
                            "question": "Can subgroup route preserve the claim?",
                            "decision": "pivot",
                            "evidence_basis": ["subgroup signal replicated"],
                            "expected_artifact": "artifacts/medical_paper/candidate_paths/route-b.json",
                        },
                    ],
                    "source_refs": ["studies/001-risk/artifacts/medical_paper/route_decision_orchestrator.json"],
                },
                "source_refs": ["studies/001-risk/artifacts/controller_decisions/latest.json"],
            },
        },
        runtime={},
        package={},
        study_id="001-risk",
    )

    assert payload["status"] == "available"
    assert payload["active_path"] == "route-b"
    assert payload["winning_path"] == "route-b"
    assert [node["route_id"] for node in payload["nodes"]] == ["route-a", "route-b"]
    assert payload["nodes"][0]["blocked_reason"] == "stop if external validation fails"
    assert payload["nodes"][0]["pivot_rationale"] == "route A blocked at validation; route B preserves the claim boundary."
    assert payload["nodes"][1]["decision"] == "pivot"
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in payload["source_refs"]
    html = parts.render_route_decision_trail_section(payload)
    assert "Route / Decision Trail" in html
    assert "active path: route-b" in html
    assert "winning path: route-b" in html
    assert "route-a" in html
    assert "blocked=stop if external validation fails" in html
    assert "Route Source Refs" in html
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in html


def test_route_decision_trail_helper_fail_closes_without_explicit_route_inputs() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_route_decision_trail_payload(
        progress={
            "study_id": "001-risk",
            "artifact_locators": [
                {
                    "group": "draft",
                    "ref": "studies/001-risk/manuscript/current_package/route-a-wins.txt",
                }
            ],
        },
        runtime={},
        package={},
        study_id="001-risk",
    )

    assert payload["status"] == "missing"
    assert payload["nodes"] == []
    assert payload["active_path"] is None
    assert payload["conditions"]["missing"] == ["route_decision_trail", "route_nodes"]
    assert payload["source_refs"] == []


def test_route_decision_trail_helper_blocks_incomplete_explicit_route_inputs() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_route_decision_trail_payload(
        progress={
            "study_id": "001-risk",
            "route_decision_trail": {
                "surface_kind": "mas_progress_portal_route_decision_trail",
                "nodes": [
                    {
                        "route_id": "route-a",
                        "label": "Can broad model generalize?",
                        "decision": "continue",
                    }
                ],
            },
        },
        runtime={},
        package={},
        study_id="001-risk",
    )

    assert payload["status"] == "missing"
    assert [node["route_id"] for node in payload["nodes"]] == ["route-a"]
    assert payload["conditions"]["missing"] == [
        "active_path",
        "winning_path",
        "route_source_refs",
    ]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
