from __future__ import annotations

import importlib
import json
from pathlib import Path
import pytest

from tests.study_runtime_test_helpers import make_profile, write_text
from tests.progress_portal_cases.helpers import _progress_payload
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
    assert payload_path == profile.workspace_root / "runtime" / "artifacts" / "progress_portal" / "latest.json"
    assert html_path == profile.workspace_root / "ops" / "mas" / "progress" / "studies" / "001-risk" / "index.html"
    assert workspace_html_path == profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    assert hosted_package_path == profile.workspace_root / "runtime" / "artifacts" / "progress_portal" / "hosted_package.json"
    assert payload_path.exists()
    assert html_path.exists()
    assert workspace_html_path.exists()
    assert hosted_package_path.exists()
    written_payload = json.loads(payload_path.read_text(encoding="utf-8"))
    written_study_payload = json.loads(
        (
            profile.workspace_root
            / "runtime"
            / "artifacts"
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
    assert hosted_package["package_role"] == "read_model_projection_package"
    assert hosted_package["truth_role"] == "projection_only_no_workspace_runtime_truth"
    assert hosted_package["read_only"] is True
    assert hosted_package["default_operation_requires_external_mds"] is False
    assert hosted_package["default_diagnostic_requires_external_mds"] is False
    assert hosted_package["mds_webui_dependency_allowed"] is False
    assert hosted_package["default_webui"] == "mas_progress_portal"
    assert hosted_package["package_refs"]["hosted_package_ref"] == "runtime/artifacts/progress_portal/hosted_package.json"
    assert hosted_package["package_refs"]["progress_payload_ref"] == "runtime/artifacts/progress_portal/latest.json"
    assert hosted_package["package_refs"]["html_ref"] == "ops/mas/progress/index.html"
    assert hosted_package["package_refs"]["workspace_relative"] == {
        "hosted_package": "runtime/artifacts/progress_portal/hosted_package.json",
        "progress_payload": "runtime/artifacts/progress_portal/latest.json",
        "html": "ops/mas/progress/index.html",
    }
    assert hosted_package["package_refs"]["study_pages"]["001-risk"] == {
        "payload": "runtime/artifacts/progress_portal/studies/001-risk/latest.json",
        "html": "ops/mas/progress/studies/001-risk/index.html",
    }
    assert hosted_package["entrypoints"] == {
        "opl_hosted_workbench_consumer": "OPL App/workbench consumes MAS progress payload refs",
        "progress_payload_ref": "runtime/artifacts/progress_portal/latest.json",
    }
    assert "hosted_runtime_carrier_contract" not in hosted_package
    materializer = hosted_package["read_model_materializer_boundary"]
    assert materializer["surface_kind"] == "mas_progress_portal_read_model_materializer_boundary"
    assert materializer["status"] == "domain_owned_read_model_materializer_no_active_workspace_helper"
    assert materializer["hosted_package_role"] == "read_model_projection_package"
    assert materializer["hosted_package_truth_role"] == "projection_only_no_workspace_runtime_truth"
    assert materializer["physical_module"] == (
        "src/med_autoscience/controllers/progress_portal_parts/read_model_materializer.py"
    )
    assert materializer["materializer_scope"] == (
        "domain_owned_payload_html_and_hosted_package_projection"
    )
    assert materializer["active_callers"] == []
    assert materializer["domain_repo_physical_delete_authorized"] is False
    assert materializer["writes_only"] == [
        "runtime/artifacts/progress_portal/latest.json",
        "runtime/artifacts/progress_portal/hosted_package.json",
        "runtime/artifacts/progress_portal/studies/<study_id>/latest.json",
        "ops/mas/progress/index.html",
        "ops/mas/progress/studies/<study_id>/index.html",
    ]
    assert "runtime_control_owner" in materializer["does_not_claim"]
    assert "read-model materializer" in materializer["retention_reason"]
    assert "MDS WebUI state" in materializer["must_not_consume"]
    assert "publication_eval/latest.json" in materializer["must_not_write"]
    assert materializer["surface_kind"] == "mas_progress_portal_read_model_materializer_boundary"
    assert materializer["domain_repo_physical_delete_authorized"] is False
    assert "local_http_service_owner" in materializer["does_not_claim"]
    assert materializer["writes_only"] == [
        "runtime/artifacts/progress_portal/latest.json",
        "runtime/artifacts/progress_portal/hosted_package.json",
        "runtime/artifacts/progress_portal/studies/<study_id>/latest.json",
        "ops/mas/progress/index.html",
        "ops/mas/progress/studies/<study_id>/index.html",
    ]
    assert result["opl_handoff"]["payload_ref"].endswith("runtime/artifacts/progress_portal/studies/001-risk/latest.json")
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
        / "runtime"
        / "artifacts"
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
            / "runtime"
            / "artifacts"
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


def test_materialize_progress_portal_isolates_unselected_study_projection_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    selected_id = "002-running"
    blocked_id = "001-old-config"
    write_text(profile.studies_root / selected_id / "study.yaml", f"study_id: {selected_id}\n")
    write_text(profile.studies_root / blocked_id / "study.yaml", f"study_id: {blocked_id}\n")

    def fake_read_study_progress(**kwargs):
        assert kwargs["sync_runtime_summary"] is False
        if kwargs["study_id"] == blocked_id:
            raise ValueError("manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only")
        return _progress_payload(kwargs["study_id"])

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.materialize_progress_portal(
        profile=profile,
        study_id=selected_id,
        progress_payload=_progress_payload(selected_id),
        cockpit_payload={
            "workspace_status": "attention_required",
            "workspace_alerts": [
                f"{blocked_id} study progress projection failed: manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only"
            ],
            "studies": [
                {
                    "study_id": blocked_id,
                    "state_label": "进度投影异常",
                    "state_summary": "该 study 的进度投影失败；其他 study 仍可继续显示和监管。",
                    "current_stage": "projection_blocked",
                    "paper_stage": "projection_blocked",
                    "current_blockers": [
                        f"{blocked_id} study progress projection failed: manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only"
                    ],
                    "progress_freshness": {
                        "status": "invalid",
                        "summary": (
                            "study progress projection failed: "
                            "manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only"
                        ),
                    },
                    "monitoring": {"health_status": "blocked", "supervisor_tick_status": "unknown"},
                    "intervention_lane": {
                        "lane_id": "study_projection_error",
                        "title": "Repair study progress projection",
                    },
                },
                {"study_id": selected_id, "state_label": "自动运行中"},
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert set(result["study_pages"]) == {blocked_id, selected_id}
    selected_payload = json.loads(Path(result["study_pages"][selected_id]["payload_path"]).read_text(encoding="utf-8"))
    blocked_payload = json.loads(Path(result["study_pages"][blocked_id]["payload_path"]).read_text(encoding="utf-8"))
    blocked_html = Path(result["study_pages"][blocked_id]["html_path"]).read_text(encoding="utf-8")

    assert selected_payload["study"]["study_id"] == selected_id
    assert selected_payload["study"]["state_label"] == "质量修复/复审中"
    assert blocked_payload["study"]["study_id"] == blocked_id
    assert blocked_payload["study"]["current_stage"] == "projection_blocked"
    assert blocked_payload["freshness"]["status"] == "invalid"
    assert blocked_payload["study"]["supervision"]["health_status"] == "blocked"
    assert blocked_payload["study_workbench"]["overview"]["state_label"] == "进度投影异常"
    assert blocked_payload["source_payloads"]["progress"]["projection_error"] is True
    progress = blocked_payload["source_payloads"]["progress"]
    assert progress["projection_error_metadata"] == {
        "diagnostic_only": True,
        "authority": False,
        "can_generate_action": False,
        "can_execute": False,
    }
    assert progress["intervention_lane_metadata"] == {
        "diagnostic_only": True,
        "authority": False,
        "can_generate_action": False,
        "can_execute": False,
    }
    assert progress["user_visible_action_metadata"] == {
        "next_system_action_role": "diagnostic_projection_error_label",
        "authority": False,
        "can_generate_action": False,
        "can_execute": False,
    }
    assert "manual_finish.compatibility_guard_only" in blocked_html
    assert Path(result["workspace_html_path"]).exists()


def test_materialized_study_page_projects_real_paper_line_workspace_proof_as_read_only_locators(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "study.yaml", "study_id: 001-risk\n")
    write_text(study_root / "artifacts" / "stage_reviews" / "write" / "latest.md", "# Write Stage Review\n")
    write_text(
        study_root / "artifacts" / "stage_reviews" / "index.json",
        json.dumps(
            {
                "surface_kind": "mas_stage_deliverable_index",
                "study_id": "001-risk",
                "stage": "write",
                "review_page_ref": "artifacts/stage_reviews/write/latest.md",
                "source_refs": [
                    "studies/001-risk/artifacts/evidence/ledger.jsonl",
                    "studies/001-risk/artifacts/review/ledger.jsonl",
                    "studies/001-risk/artifacts/publication_eval/latest.json",
                    "studies/001-risk/artifacts/controller_decisions/latest.json",
                    "studies/001-risk/artifacts/package_freshness/latest.json",
                ],
                "paper_line_workspace_proof": {
                    "evidence_ledger_ref": "artifacts/evidence/ledger.jsonl",
                    "review_ledger_ref": "artifacts/review/ledger.jsonl",
                    "publication_eval_ref": "artifacts/publication_eval/latest.json",
                    "controller_decision_ref": "artifacts/controller_decisions/latest.json",
                    "artifact_freshness_ref": "artifacts/package_freshness/latest.json",
                    "package_proof_ref": "paper/current_package/proof.json",
                },
                "paper_asset_delta": {
                    "delta_types": ["manuscript", "package"],
                    "refs": ["paper/manuscript.md", "paper/current_package/current_package.zip"],
                },
                "freshness_signal": {"state": "green_current"},
                "human_review": {"state": "annotated"},
                "next_owner": {"owner": "MedAutoScience", "next_routes": ["review"]},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    for ref in (
        "artifacts/evidence/ledger.jsonl",
        "artifacts/review/ledger.jsonl",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        "artifacts/package_freshness/latest.json",
        "paper/current_package/proof.json",
    ):
        write_text(study_root / ref, "{}\n")

    result = module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    payload = json.loads(
        (
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "progress_portal"
            / "studies"
            / "001-risk"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    html = Path(result["html_path"]).read_text(encoding="utf-8")
    review = payload["study_workbench"]["stage_review_index"]
    proof = review["rows"][0]["paper_line_workspace_proof"]
    assert review["status"] == "available"
    assert proof["surface_kind"] == "mas_paper_line_workspace_locator_proof"
    assert proof["status"] == "available"
    assert proof["body_included"] is False
    assert proof["read_only"] is True
    assert proof["authority"]["writes_authority_surface"] is False
    assert proof["authority"]["can_authorize_quality_verdict"] is False
    assert proof["authority"]["can_authorize_submission_readiness"] is False
    assert proof["authority"]["can_authorize_artifact_authority"] is False
    assert proof["locators"]["publication_eval"]["ref"] == "studies/001-risk/artifacts/publication_eval/latest.json"
    assert proof["locators"]["controller_decision"]["ref"] == (
        "studies/001-risk/artifacts/controller_decisions/latest.json"
    )
    assert proof["locators"]["package_proof"]["ref"] == "studies/001-risk/paper/current_package/proof.json"
    assert all(item["body_included"] is False for item in proof["locators"].values())
    assert "studies/001-risk/artifacts/evidence/ledger.jsonl" in review["source_refs"]
    assert "studies/001-risk/artifacts/review/ledger.jsonl" in review["source_refs"]
    assert "studies/001-risk/artifacts/publication_eval/latest.json" in review["source_refs"]
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in review["source_refs"]
    assert "studies/001-risk/artifacts/package_freshness/latest.json" in review["source_refs"]
    assert "studies/001-risk/paper/current_package/proof.json" in review["source_refs"]
    assert "paper-line workspace proof" in html
    assert "studies/001-risk/artifacts/publication_eval/latest.json" in html
    assert "studies/001-risk/paper/current_package/proof.json" in html
    assert "{}" not in html


def test_materialized_study_page_fails_closed_when_paper_line_workspace_proof_refs_are_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "study.yaml", "study_id: 001-risk\n")
    write_text(study_root / "artifacts" / "stage_reviews" / "write" / "latest.md", "# Write Stage Review\n")
    write_text(
        study_root / "artifacts" / "stage_reviews" / "index.json",
        json.dumps(
            {
                "surface_kind": "mas_stage_deliverable_index",
                "study_id": "001-risk",
                "stage": "write",
                "review_page_ref": "artifacts/stage_reviews/write/latest.md",
                "source_refs": ["studies/001-risk/artifacts/publication_eval/latest.json"],
                "paper_line_workspace_proof": {
                    "evidence_ledger_ref": "artifacts/evidence/ledger.jsonl",
                    "publication_eval_ref": "artifacts/publication_eval/latest.json",
                    "controller_decision_ref": "artifacts/controller_decisions/latest.json",
                    "package_proof_ref": "paper/current_package/proof.json",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(study_root / "artifacts" / "evidence" / "ledger.jsonl", "{}\n")
    write_text(study_root / "artifacts" / "publication_eval" / "latest.json", "{}\n")
    write_text(study_root / "artifacts" / "controller_decisions" / "latest.json", "{}\n")
    write_text(study_root / "paper" / "current_package" / "proof.json", "{}\n")

    module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
    )

    payload = json.loads(
        (
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "progress_portal"
            / "studies"
            / "001-risk"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    review = payload["study_workbench"]["stage_review_index"]
    assert review["status"] == "missing"
    assert review["rows"] == []
    assert "paper_line_workspace_proof_refs" in review["conditions"]["missing"]


def test_materialize_progress_portal_can_open_static_entry(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    materializer_module = importlib.import_module(
        "med_autoscience.controllers.progress_portal_parts.read_model_materializer"
    )
    profile = make_profile(tmp_path)
    opened: list[str] = []
    monkeypatch.setattr(materializer_module.webbrowser, "open", lambda url: opened.append(url) or True)

    result = module.materialize_progress_portal(
        profile=profile,
        study_id="001-risk",
        progress_payload=_progress_payload(),
        generated_at="2026-05-08T01:05:00+00:00",
        open_browser=True,
    )

    assert opened == [Path(result["html_path"]).as_uri()]


def test_progress_portal_has_no_repo_local_http_service_entry(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    materializer_module = importlib.import_module(
        "med_autoscience.controllers.progress_portal_parts.read_model_materializer"
    )

    assert not hasattr(module, "serve_progress_portal")
    assert not hasattr(materializer_module, "serve_progress_portal")


def test_progress_portal_workspace_carrier_module_is_retired() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.controllers.progress_portal_parts.workspace_carrier")
