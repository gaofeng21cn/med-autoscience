from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_text
from tests.test_progress_portal import _progress_payload
from tests.progress_portal_cases.test_stage_review_surface import _stage_review_payload


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
    workspace_html_path = Path(result["workspace_html_path"])
    hosted_package_path = Path(result["hosted_package_path"])
    assert payload_path == profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    assert html_path == profile.workspace_root / "ops" / "mas" / "progress" / "studies" / "001-risk" / "index.html"
    assert workspace_html_path == profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    assert hosted_package_path == profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
    assert payload_path.exists()
    assert html_path.exists()
    assert workspace_html_path.exists()
    assert hosted_package_path.exists()
    written_payload = json.loads(payload_path.read_text(encoding="utf-8"))
    written_study_payload = json.loads(
        (
            profile.workspace_root
            / "artifacts"
            / "runtime"
            / "progress_portal"
            / "studies"
            / "001-risk"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    hosted_package = json.loads(hosted_package_path.read_text(encoding="utf-8"))
    assert written_payload["study"]["scope"] == "workspace"
    assert written_study_payload["study"]["study_id"] == "001-risk"
    assert written_study_payload["study"]["scope"] == "study"
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
    assert hosted_package["package_refs"]["study_pages"]["001-risk"] == {
        "payload": "artifacts/runtime/progress_portal/studies/001-risk/latest.json",
        "html": "ops/mas/progress/studies/001-risk/index.html",
    }
    assert hosted_package["entrypoints"]["workspace_helper"] == "ops/mas/bin/start-web"
    assert hosted_package["entrypoints"]["optional_local_read_only_service"] == (
        "medautosci workspace progress-portal --profile <profile> --serve"
    )
    assert "MDS WebUI state" in hosted_package["hosted_runtime_carrier_contract"]["must_not_consume"]
    assert "publication_eval/latest.json" in hosted_package["hosted_runtime_carrier_contract"]["must_not_write"]
    assert result["opl_handoff"]["payload_ref"].endswith("artifacts/runtime/progress_portal/studies/001-risk/latest.json")
    assert result["opl_handoff"]["deep_link"] == str(html_path)
    assert result["hosted_package"]["package_refs"]["hosted_package"] == str(hosted_package_path)
    assert html_path.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert "路线 / 决策" in html_path.read_text(encoding="utf-8")
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "controller_decisions").exists()
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "publication_eval").exists()


def test_materialized_study_page_renders_stage_review_table_without_writing_truth(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    write_text(profile.workspace_root / "studies" / "001-risk" / "study.yaml", "study_id: 001-risk\n")

    result = module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_stage_review_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    study_payload_path = (
        profile.workspace_root
        / "artifacts"
        / "runtime"
        / "progress_portal"
        / "studies"
        / "001-risk"
        / "latest.json"
    )
    html = Path(result["html_path"]).read_text(encoding="utf-8")
    payload = json.loads(study_payload_path.read_text(encoding="utf-8"))
    assert payload["study_workbench"]["stage_review_index"]["status"] == "available"
    assert "Stage 交付审阅" in html
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in html
    assert "质量 verdict" in html
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "stage_reviews").exists()
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "controller_decisions").exists()
    assert not (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "publication_eval").exists()


def test_materialized_study_page_reads_existing_stage_review_locator_without_writing_truth(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "study.yaml", "study_id: 001-risk\n")
    write_text(
        study_root / "artifacts" / "stage_reviews" / "write" / "latest.md",
        "# Write Stage Review\n\n人工审阅页正文留在 workspace artifact。\n",
    )
    write_text(
        study_root / "artifacts" / "stage_reviews" / "index.json",
        json.dumps(
            {
                "surface_kind": "mas_stage_deliverable_index",
                "study_id": "001-risk",
                "stage": "write",
                "review_page_ref": "artifacts/stage_reviews/write/latest.md",
                "source_refs": ["studies/001-risk/artifacts/controller_decisions/latest.json"],
                "claim_trace": {"impact_state": "strengthened"},
                "freshness_signal": {"state": "green_current"},
                "human_review": {"state": "annotated"},
                "next_owner": {"owner": "MedAutoScience", "next_routes": ["review"]},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    result = module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    study_payload_path = (
        profile.workspace_root
        / "artifacts"
        / "runtime"
        / "progress_portal"
        / "studies"
        / "001-risk"
        / "latest.json"
    )
    payload = json.loads(study_payload_path.read_text(encoding="utf-8"))
    review = payload["study_workbench"]["stage_review_index"]
    assert review["status"] == "available"
    assert review["latest_review_page"]["body_included"] is False
    assert review["rows"][0]["latest_review_page_proof"]["status"] == "available"
    assert review["rows"][0]["paper_line_index_proof"]["index_surface_kind"] == "mas_stage_deliverable_index"
    assert review["rows"][0]["claim_impact"]["impact_state"] == "strengthened"
    assert "studies/001-risk/artifacts/stage_reviews/write/latest.md" in Path(result["html_path"]).read_text(
        encoding="utf-8"
    )
    assert (study_root / "artifacts" / "stage_reviews" / "index.json").exists()
    assert (study_root / "artifacts" / "stage_reviews" / "write" / "latest.md").exists()
    assert not (study_root / "artifacts" / "publication_eval").exists()


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
    assert result["actions_enabled"] is False
    assert result["opl_handoff"]["deep_link"] == result["html_path"]
    assert result["opl_handoff"]["payload_ref"].endswith("artifacts/runtime/progress_portal/studies/001-risk/latest.json")
    assert served["address"] == ("127.0.0.1", 4301)
    assert served["closed"] is True
