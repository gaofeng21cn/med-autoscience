from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_text


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
    assert workspace["workspace_alerts"] == [
        "live worker 已超过 meaningful artifact delta 活动窗口，必须先恢复产物增量或写出平台修复终态。"
    ]
    assert workspace["diagnostics"]["suppressed_alerts"] == [
        "Hermes-hosted runtime supervision 尚未注册。",
        "状态需要检查。",
        "用户暂停或手动停驻，需显式恢复或新方案。",
    ]
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
    assert "Hermes-hosted runtime supervision 尚未注册。" not in html


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
    assert "generated_at" in html
    assert "freshness" in html
    assert "source refs" in html
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
    assert "source refs (4/46)" in html


def test_materialize_progress_portal_writes_only_read_model_and_static_html(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    write_text(profile.workspace_root / "studies" / "001-risk" / "study.yaml", "study_id: 001-risk\n")

    result = module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    payload_path = Path(result["payload_path"])
    html_path = Path(result["html_path"])
    hosted_package_path = Path(result["hosted_package_path"])
    assert payload_path == profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    assert html_path == profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    assert hosted_package_path == profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
    assert payload_path.exists()
    assert html_path.exists()
    assert hosted_package_path.exists()
    written_payload = json.loads(payload_path.read_text(encoding="utf-8"))
    hosted_package = json.loads(hosted_package_path.read_text(encoding="utf-8"))
    assert written_payload["study"]["study_id"] == "001-risk"
    assert written_payload["opl_handoff"]["deep_link"] == "ops/mas/progress/index.html"
    assert hosted_package["surface_kind"] == "mas_progress_portal_hosted_package"
    assert hosted_package["owner"] == "MedAutoScience"
    assert hosted_package["packaging_owner"] == "MedAutoScience"
    assert hosted_package["read_only"] is True
    assert hosted_package["default_operation_requires_external_mds"] is False
    assert hosted_package["default_diagnostic_requires_external_mds"] is False
    assert hosted_package["mds_webui_dependency_allowed"] is False
    assert hosted_package["default_webui"] == "mas_progress_portal"
    assert hosted_package["package_refs"]["hosted_package_ref"] == "artifacts/runtime/progress_portal/hosted_package.json"
    assert hosted_package["package_refs"]["progress_payload_ref"] == "artifacts/runtime/progress_portal/latest.json"
    assert hosted_package["package_refs"]["html_ref"] == "ops/mas/progress/index.html"
    assert hosted_package["package_refs"]["workspace_relative"] == {
        "hosted_package": "artifacts/runtime/progress_portal/hosted_package.json",
        "progress_payload": "artifacts/runtime/progress_portal/latest.json",
        "html": "ops/mas/progress/index.html",
    }
    assert hosted_package["entrypoints"]["workspace_helper"] == "ops/mas/bin/start-web"
    assert hosted_package["entrypoints"]["optional_local_read_only_service"] == (
        "medautosci workspace progress-portal --profile <profile> --serve"
    )
    assert "MDS WebUI state" in hosted_package["hosted_runtime_carrier_contract"]["must_not_consume"]
    assert "publication_eval/latest.json" in hosted_package["hosted_runtime_carrier_contract"]["must_not_write"]
    assert result["opl_handoff"]["payload_ref"] == str(payload_path)
    assert result["opl_handoff"]["deep_link"] == str(html_path)
    assert result["hosted_package"]["package_refs"]["hosted_package"] == str(hosted_package_path)
    assert html_path.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "controller_decisions").exists()
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "publication_eval").exists()


def test_materialize_progress_portal_can_open_static_entry(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    opened: list[str] = []
    monkeypatch.setattr(module.webbrowser, "open", lambda url: opened.append(url) or True)

    result = module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
        open_browser=True,
    )

    assert opened == [Path(result["html_path"]).as_uri()]


def test_serve_progress_portal_materializes_and_reports_read_only_local_url(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    served: dict[str, object] = {}

    class FakeServer:
        server_address = ("127.0.0.1", 4301)

        def __init__(self, address, handler):
            served["address"] = address
            served["handler"] = handler

        def serve_forever(self) -> None:
            served["served"] = True

        def server_close(self) -> None:
            served["closed"] = True

    monkeypatch.setattr(module.socketserver, "TCPServer", FakeServer)

    result = module.serve_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
        host="127.0.0.1",
        port=4301,
        interval_seconds=20,
        once=True,
    )

    assert result["status"] == "serving"
    assert result["url"] == "http://127.0.0.1:4301/"
    assert result["read_only"] is True
    assert result["interval_seconds"] == 20
    assert Path(result["html_path"]).exists()
    assert result["hosted_package_path"].endswith("artifacts/runtime/progress_portal/hosted_package.json")
    assert result["hosted_package"]["mds_webui_dependency_allowed"] is False
    assert result["opl_handoff"]["deep_link"] == result["html_path"]
    assert result["opl_handoff"]["payload_ref"] == result["payload_path"]
    assert served["address"] == ("127.0.0.1", 4301)
    assert served["closed"] is True
