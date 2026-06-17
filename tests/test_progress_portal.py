from __future__ import annotations

import importlib

from tests.progress_portal_cases.helpers import _progress_payload, _runtime_continuity_payload


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
    assert "domain_route_tick" not in payload["conditions"]["missing"]
    assert payload["conditions"]["conflict"] == ["cockpit_study_id_mismatch", "package_study_id_mismatch"]
    assert "studies/001-risk/artifacts/publication_eval/latest.json" in payload["source_refs"]
    assert payload["quality"]["summary"] == "证据链仍需补强。"
    assert payload["delivery"]["summary"] == "current package 尚未生成。"
    assert "live_console" not in payload


def test_progress_portal_projects_decision_trace_refs_without_ledger_body() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = _progress_payload()
    progress["user_visible_projection"] = {
        **progress["user_visible_projection"],
        "decision_trace": {
            "summary": "Prior route narrowed the claim after a negative sensitivity result.",
            "refs": [
                "studies/001-risk/artifacts/controller_decisions/decision-trace-negative-route.json"
            ],
            "body": "private decision body must not be rendered",
        },
        "decision_trace_refs": [
            "studies/001-risk/artifacts/controller_decisions/decision-trace-negative-route.json"
        ],
        "failed_path_ledger": {
            "summary": "Transport-model route failed provenance checks.",
            "refs": [
                "studies/001-risk/artifacts/evidence/failed_paths/transport-model-route.json"
            ],
            "body": "private failed-path body must not be rendered",
        },
        "failed_path_refs": [
            "studies/001-risk/artifacts/evidence/failed_paths/transport-model-route.json"
        ],
    }

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        generated_at="2026-05-08T01:05:00+00:00",
    )
    html = module.render_progress_portal_html(payload)

    trace = payload["study"]["decision_trace"]
    failed = payload["study"]["failed_path_ledger"]
    assert trace["summary"] == "Prior route narrowed the claim after a negative sensitivity result."
    assert trace["refs"] == [
        "studies/001-risk/artifacts/controller_decisions/decision-trace-negative-route.json"
    ]
    assert trace["body_included"] is False
    assert failed["summary"] == "Transport-model route failed provenance checks."
    assert failed["refs"] == [
        "studies/001-risk/artifacts/evidence/failed_paths/transport-model-route.json"
    ]
    assert failed["body_included"] is False
    assert "body" not in trace
    assert "body" not in failed
    assert "Prior route narrowed the claim" in html
    assert "Transport-model route failed provenance checks" in html
    assert "private decision body" not in html
    assert "private failed-path body" not in html


def test_progress_portal_payload_has_no_private_live_console_link() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )
    html = module.render_progress_portal_html(payload)

    assert "live_console" not in payload
    assert "运行控制台" not in html
    assert "live-console" not in html
    assert "terminal/log stream" not in html


def test_progress_portal_human_gate_uses_needs_user_decision_not_legacy_physician_alias() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    stale_alias_payload = _progress_payload()
    stale_alias_payload["user_visible_projection"] = {
        **_progress_payload()["user_visible_projection"],
        "needs_physician_decision": True,
        "needs_user_decision": False,
    }
    stale_alias = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=stale_alias_payload,
        generated_at="2026-05-08T01:05:00+00:00",
    )
    stale_alias_html = module.render_progress_portal_html(stale_alias)

    canonical_payload = _progress_payload()
    canonical_payload["user_visible_projection"] = {
        **_progress_payload()["user_visible_projection"],
        "needs_physician_decision": False,
        "needs_user_decision": True,
    }
    canonical = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=canonical_payload,
        generated_at="2026-05-08T01:05:00+00:00",
    )
    canonical_html = module.render_progress_portal_html(canonical)

    assert stale_alias["study"]["needs_user_decision"] is False
    assert "当前没有投影出的用户决策 gate。" in stale_alias_html
    assert "需要用户确认后继续。" not in stale_alias_html
    assert canonical["study"]["needs_user_decision"] is True
    assert "需要用户确认后继续。" in canonical_html


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
                "OPL provider/runtime manager workspace supervision 尚未注册。",
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
        "OPL provider/runtime manager workspace supervision 尚未注册。",
        "用户暂停或手动停驻，需显式恢复或新方案。",
    ]
    assert workspace["diagnostics"]["suppressed_alert_items"][0]["source"] == "workspace_supervision.service.summary"
    assert workspace["diagnostics"]["suppressed_alert_items"][0]["recommended_command"] is None
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
            "workspace_alerts": ["OPL provider/runtime manager workspace supervision 尚未注册。"],
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
    assert "OPL provider/runtime manager workspace supervision 尚未注册。" in html
    assert "Hermes-hosted runtime supervision 尚未注册。" not in html
    assert "runtime-supervision-status" not in html
    assert "--manager local" not in html
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
                "MAS local scheduler 已物理退役；仅保留 tombstone/provenance refs。"
            ],
            "studies": [],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    item = payload["workspace"]["workspace_alert_items"][0]
    assert item["source"] == "workspace_supervision.service.summary"
    assert item["current_output"] == "MAS local scheduler 已物理退役；仅保留 tombstone/provenance refs。"
    assert item["recommended_command"] is None
    html = module.render_progress_portal_html(payload)
    assert "MAS local scheduler 已物理退役；仅保留 tombstone/provenance refs。" in html
    assert "workspace_supervision.service.summary" in html
    assert "--manager local" not in html


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
    assert handoff["payload_refs"]["progress_portal"] == "runtime/artifacts/progress_portal/latest.json"
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


def test_progress_portal_payload_exposes_opl_runtime_workbench_projection_without_authority_transfer() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        profile_ref="/workspace/ops/medautoscience/profiles/diabetes.toml",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        runtime_payload={
            "study_id": "001-risk",
            "active_run_id": "run-runtime-001",
            "opl_current_control_state": {"active_run_id": "run-opl-001", "status": "attempt_running"},
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    projection = payload["mas_opl_runtime_workbench_projection"]
    assert projection["surface_kind"] == "mas_opl_runtime_workbench_projection"
    assert projection["schema_version"] == 1
    assert projection["workspace"] == {
        "workspace_root": "/workspace",
        "profile_ref": "/workspace/ops/medautoscience/profiles/diabetes.toml",
        "profile_name": "diabetes",
    }
    assert projection["studies"][0]["study_id"] == "001-risk"
    assert projection["studies"][0]["macro_state"] == "质量修复/复审中"
    assert projection["studies"][0]["links"]["progress_payload_ref"] == "runtime/artifacts/progress_portal/latest.json"
    assert "conversation_read_model_ref" not in projection["studies"][0]["links"]
    intents = projection["studies"][0]["operator_intent_projection"]
    assert intents["pause"]["owner"] == "one-person-lab"
    assert intents["pause"]["surface_kind"] == "workbench_operator_intent_projection_ref"
    assert intents["pause"]["command"] is None
    assert intents["pause"]["execute_authority"] is False
    assert intents["pause"]["must_route_to_opl_runtime"] is True
    assert intents["stop"]["confirmation_required"] is False
    assert intents["stop"]["external_authority_confirmation_required"] is True
    assert projection["terminal"]["mode"] == "external_control_plane_required"
    assert projection["terminal"]["active_run_id"] == "run-opl-001"
    assert projection["terminal"]["token_required"] is True
    assert projection["terminal"]["lease_required"] is True
    assert projection["authority"]["opl_role"] == "projection_consumer_and_action_transport_only"
    assert projection["authority"]["mas_truth_owner"] is True
    assert projection["authority"]["forbidden_writes"] == [
        "study_truth",
        "publication_judgment",
        "quality_verdict",
        "runtime_authority",
        "artifact_authority",
        "runtime_state",
        "runtime_sqlite",
        "terminal_commands",
        "current_package",
        "evidence_ledger",
        "review_ledger",
    ]


def test_progress_portal_runtime_workbench_boundary_is_read_only_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        profile_ref="/workspace/ops/medautoscience/profiles/diabetes.toml",
        study_id="001-risk",
        progress_payload=_progress_payload(),
        runtime_payload={
            "study_id": "001-risk",
            "opl_current_control_state": {
                "active_run_id": "run-opl-001",
                "status": "attempt_running",
            },
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    projection = payload["mas_opl_runtime_workbench_projection"]
    assert projection["projection_boundary"] == {
        "surface_kind": "mas_opl_runtime_workbench_projection_boundary",
        "projection_only": True,
        "actions_role": "operator_intent_projection_refs",
        "links_role": "read_only_drilldown_refs",
        "next_summary_role": "read_only_drilldown_summary",
        "can_execute_controller_action": False,
        "can_generate_next_action_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_worker_attempt": False,
        "can_retry_or_dead_letter": False,
        "can_authorize_publication_ready": False,
        "can_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }
    study = projection["studies"][0]
    assert study["next_action_summary_role"] == "read_only_drilldown_summary"
    assert study["next_action_summary_is_controller_action"] is False
    assert study["links_role"] == "read_only_drilldown_refs"
    assert study["links_can_execute"] is False
    assert study["actions_role"] == "operator_intent_projection_refs"
    assert study["actions_can_execute"] is False
    assert study["actions_deprecated"] is True
    assert study["actions_authority"] is False
    assert study["actions_are_operator_intent_refs"] is True
    assert all(action["allowed"] is False for action in study["actions"].values())
    assert all(action["execute_authority"] is False for action in study["actions"].values())
    assert all(action["command"] is None for action in study["operator_intent_projection"].values())
    assert all(action["confirmation_required"] is False for action in study["operator_intent_projection"].values())
    assert all(
        action["must_read_back_mas_owner_receipt"] is True
        for action in study["operator_intent_projection"].values()
    )


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
    assert "runtime_session" not in continuity
    assert "owner_receipt_handoff" not in continuity
    assert continuity["surface_kind"] == "mas_domain_authority_control_projection"
    assert continuity["opl_control_plane"]["runtime_control_owner"] == "one-person-lab"
    assert continuity["opl_control_plane"]["stage_attempt_state_owned_by_mas"] is False
    assert continuity["authority"]["quality_ready_authorized"] is False
    assert impact["surface_kind"] == "mas_production_blocker_impact_projection"
    assert impact["affects_output"] is True
    assert impact["next_owner"] == "mas_controller"
    assert impact["why_not_running"] == "worker heartbeat is stale; no new manuscript artifact delta"
    assert impact["same_fingerprint_or_handoff"] == "same_fingerprint"
    assert impact["route"]["source_fingerprint"] == "runtime-continuity-001"
    assert "studies/001-risk/artifacts/autonomy/slo_status/latest.json" in impact["source_refs"]
    assert impact["authority"]["writes_authority_surface"] is False
    assert payload["opl_handoff"]["runtime_continuity"]["opl_control_plane"]["runtime_control_owner"] == "one-person-lab"
    assert "last worker heartbeat" not in html
    assert "will start LLM" not in html
    assert "safe_reconcile_ready" not in html
    assert "是否影响产出" in html
    assert "safe reconcile command" not in html
    assert "--dry-run" not in html
    assert "run-stale-001" not in html
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
                "uv run python -m med_autoscience.cli owner-route-reconcile "
                "--profile /workspace/profile.toml --studies 001-risk "
                "--developer-supervisor-mode external_observe"
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
    assert "runtime_session" not in continuity
    assert "owner_receipt_handoff" not in continuity
    assert continuity["opl_control_plane"]["runtime_control_owner"] == "one-person-lab"
    assert continuity["opl_control_plane"]["stage_attempt_state_owned_by_mas"] is False
    assert impact["next_owner"] == "mas_controller"
    assert impact["affects_output"] is True
    assert impact["same_fingerprint_or_handoff"] == "same_fingerprint"
    assert "will_start_llm" not in impact
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
        "/workspace/studies/001-risk/artifacts/supervision/opl_runtime_owner_handoff/latest.json",
        "/workspace/studies/001-risk/artifacts/controller_decisions/latest.json",
        "/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
        "not/a/selected/source/ref",
    ] + [f"/workspace/legacy/{index:03d}.json" for index in range(40)]

    html = module.render_progress_portal_html(payload)

    assert "/workspace/studies/001-risk/artifacts/runtime/health/latest.json" in html
    assert "/workspace/studies/001-risk/artifacts/controller_decisions/latest.json" in html
    assert "/workspace/studies/001-risk/artifacts/supervision/opl_runtime_owner_handoff/latest.json" in html
    assert "/workspace/studies/001-risk/artifacts/runtime/runtime_supervision/latest.json" not in html
    assert "med-deepscientist" not in html
    assert "not/a/selected/source/ref" not in html
    assert "数据来源 (4/47)" in html


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
