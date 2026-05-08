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
    assert payload_path == profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    assert html_path == profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    assert payload_path.exists()
    assert html_path.exists()
    written_payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert written_payload["study"]["study_id"] == "001-risk"
    assert written_payload["opl_handoff"]["deep_link"] == "ops/mas/progress/index.html"
    assert result["opl_handoff"]["payload_ref"] == str(payload_path)
    assert result["opl_handoff"]["deep_link"] == str(html_path)
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
    assert result["opl_handoff"]["deep_link"] == result["html_path"]
    assert result["opl_handoff"]["payload_ref"] == result["payload_path"]
    assert served["address"] == ("127.0.0.1", 4301)
    assert served["closed"] is True
