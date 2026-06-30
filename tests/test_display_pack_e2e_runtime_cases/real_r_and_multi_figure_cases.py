from __future__ import annotations

import json
from pathlib import Path
import shutil

from tests.test_display_pack_e2e_runtime import (
    _build_workspace,
    _install_fake_ggconsort_package,
    _visual_audit_review,
    _write_cohort_flow_paper_inputs,
    _write_fake_dependency_run_context,
    _write_json,
    _write_real_core_r_paper_inputs,
    _write_subprocess_renderable_template,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_materialize_display_pack_publication_manifest_runs_real_core_r_subprocess_renderer(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    assert shutil.which("Rscript") is not None
    repo_root = REPO_ROOT
    paper_root = tmp_path / "workspace" / "paper"
    _write_real_core_r_paper_inputs(paper_root)

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
        figure_ids=["F1"],
    )

    figure = result["figures"][0]
    render_result = figure["render_result"]
    assert figure["template_id"] == "fenggaolab.org.medical-display-core::roc_curve_binary"
    assert figure["renderer_family"] == "r_ggplot2"
    assert figure["execution_mode"] == "subprocess"
    assert render_result["execution_mode"] == "subprocess"
    assert render_result["entrypoint"] == "Rscript render.R --request {request_json}"
    assert render_result["argv"][0] == "Rscript"
    assert render_result["argv"][1] == "render.R"
    assert render_result["argv"][2] == "--request"
    assert Path(render_result["cwd"]).name == "roc_curve_binary"
    assert Path(render_result["request_path"]).exists()
    assert Path(render_result["stdout_path"]).exists()
    assert Path(render_result["stderr_path"]).exists()
    assert Path(figure["rendered_artifacts"]["png_path"]).exists()
    assert Path(figure["rendered_artifacts"]["pdf_path"]).exists()
    assert Path(figure["rendered_artifacts"]["layout_sidecar_path"]).exists()
    request_payload = json.loads(Path(render_result["request_path"]).read_text(encoding="utf-8"))
    layout_sidecar = json.loads(Path(figure["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    request_context = request_payload["display_payload"]["render_context"]
    assert request_context["style_profile_sha256"] == figure["publication_style_profile"]["sha256"]
    assert request_context["palette"]["primary"] == "#245A6B"
    assert request_context["style_roles"]["model_curve"] == "#245A6B"
    assert request_context["typography"]["font_family"] == "sans"
    assert request_context["grid"]["color"] == "#D9E2EC"
    assert layout_sidecar["render_context"]["style_profile_sha256"] == request_context["style_profile_sha256"]
    assert layout_sidecar["style_profile"]["style_profile_sha256"] == request_context["style_profile_sha256"]
    assert layout_sidecar["style_profile"]["grid"]["color"] == "#D9E2EC"
    assert layout_sidecar["style_profile"]["typography"]["font_family"] == "sans"
    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    assert lock_payload["publication_style_profile"]["sha256"] == request_context["style_profile_sha256"]
    locked_template = next(
        item
        for pack in lock_payload["enabled_packs"]
        for item in pack["templates"]
        if item["full_template_id"] == "fenggaolab.org.medical-display-core::roc_curve_binary"
    )
    assert locked_template["execution_mode"] == "subprocess"
    assert locked_template["entrypoint"] == "Rscript render.R --request {request_json}"
    assert locked_template["render_script_path"].endswith("templates/roc_curve_binary/render.R")
    assert len(locked_template["render_script_sha256"]) == 64


def test_materialize_display_pack_publication_manifest_runs_cohort_flow_ggconsort_exact_path(
    tmp_path: Path,
) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    assert shutil.which("Rscript") is not None
    repo_root = REPO_ROOT
    paper_root = tmp_path / "workspace" / "paper"
    r_library_root = _install_fake_ggconsort_package(tmp_path)
    dependency_environment = _write_fake_dependency_run_context(
        paper_root,
        r_library_root=r_library_root,
    )
    _write_cohort_flow_paper_inputs(paper_root)
    _write_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F_cohort",
                    "template_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
                    "paper_role": "main_text",
                    "export_paths": [
                        "paper/figures/generated/F_cohort_legacy.png",
                        "paper/figures/generated/F_cohort_legacy.pdf",
                    ],
                    "qc_result": {
                        "status": "pass",
                        "layout_sidecar_path": "paper/figures/generated/F_cohort_legacy.layout.json",
                    },
                }
            ],
        },
    )

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
        figure_ids=["F_cohort"],
        dependency_environment=dependency_environment,
    )

    figure = result["figures"][0]
    render_result = figure["render_result"]
    assert result["dependency_environment"] == dependency_environment
    assert result["figure_render_receipt"]["dependency_environment"] == dependency_environment
    assert result["figure_catalog_sync"]["status"] == "synced"
    assert result["figure_catalog_sync"]["updated_figure_ids"] == ["F_cohort"]
    assert figure["template_id"] == "fenggaolab.org.medical-display-core::cohort_flow_figure"
    assert figure["short_template_id"] == "cohort_flow_figure"
    assert figure["figure_kind"] == "illustration_shell"
    assert figure["renderer_family"] == "r_ggplot2"
    assert figure["execution_mode"] == "subprocess"
    assert figure["required_exports"] == ["png", "pdf"]
    assert figure["dependency_environment"] == dependency_environment
    assert render_result["execution_mode"] == "subprocess"
    assert render_result["renderer_family"] == "r_ggplot2"
    assert render_result["entrypoint"] == "Rscript render.R --request {request_json}"
    assert render_result["argv"][0] == "Rscript"
    assert render_result["argv"][1] == "render.R"
    assert render_result["argv"][2] == "--request"
    assert Path(render_result["cwd"]).name == "cohort_flow_figure"
    assert render_result["returncode"] == 0
    assert render_result["dependency_environment"] == dependency_environment
    assert render_result["dependency_run_context"] == {
        "run_context_ref": "paper/build/dependency_run_context.json",
        "execution_fingerprint": "sha256:test-ggconsort-run-context",
    }
    for path_key in ("png_path", "pdf_path", "layout_sidecar_path"):
        assert Path(figure["rendered_artifacts"][path_key]).exists()

    request_payload = json.loads(Path(render_result["request_path"]).read_text(encoding="utf-8"))
    assert request_payload["short_template_id"] == "cohort_flow_figure"
    assert request_payload["renderer_family"] == "r_ggplot2"
    assert request_payload["dependency_environment"] == dependency_environment
    assert request_payload["display_payload"]["data_payload"]["steps"][0]["step_id"] == "screened"

    layout_sidecar = json.loads(Path(figure["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    metrics = layout_sidecar["metrics"]
    assert layout_sidecar["template_id"] == "cohort_flow_figure"
    assert figure["deterministic_qc"]["status"] == "pass"
    assert metrics["uses_ggconsort"] is True
    assert metrics["ggconsort_capable_prepared_environment_required"] is True
    assert metrics["dependency_profile_ref"] == "r_ggplot2_ggconsort_reporting_flow_v1"
    assert metrics["mature_dependency_intent"] == "ggconsort_capable_reporting_flow"
    assert metrics["renderer_family"] == "r_ggplot2"
    assert metrics["renderer_role"] == "default"
    assert metrics["opl_dependency_run_context_ref"] == "paper/build/dependency_run_context.json"
    assert metrics["opl_dependency_run_context_fingerprint"] == "sha256:test-ggconsort-run-context"
    assert [step["step_id"] for step in metrics["steps"]] == ["screened", "eligible", "analysis"]
    assert [item["exclusion_id"] for item in metrics["exclusions"]] == [
        "missing_baseline",
        "lost_followup",
    ]
    assert any(item["box_type"] == "main_step" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "exclusion_box" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "flow_connector" for item in layout_sidecar["guide_boxes"])
    assert any(item["box_type"] == "flow_branch_connector" for item in layout_sidecar["guide_boxes"])

    render_receipt = json.loads((paper_root / "figure_render_receipt.json").read_text(encoding="utf-8"))
    assert render_receipt["dependency_environment"] == dependency_environment
    assert render_receipt["figures"][0]["dependency_environment"] == dependency_environment
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    catalog_entry = figure_catalog["figures"][0]
    assert catalog_entry["export_paths"] == [
        "paper/figures/generated/F_cohort.png",
        "paper/figures/generated/F_cohort.pdf",
    ]
    assert catalog_entry["qc_result"]["layout_sidecar_path"] == "paper/figures/generated/F_cohort.layout.json"
    assert catalog_entry["rendered_artifact_refs"] == [
        "paper/figures/generated/F_cohort.png",
        "paper/figures/generated/F_cohort.pdf",
        "paper/figures/generated/F_cohort.layout.json",
    ]
    assert catalog_entry["visual_audit"]["status"] == "clear"
    assert catalog_entry["display_artifact_manifest_ref"] == "paper/build/display_artifact_manifest.F_cohort.json"
    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    locked_template = next(
        item
        for pack in lock_payload["enabled_packs"]
        for item in pack["templates"]
        if item["full_template_id"] == "fenggaolab.org.medical-display-core::cohort_flow_figure"
    )
    assert locked_template["execution_mode"] == "subprocess"
    assert locked_template["entrypoint"] == "Rscript render.R --request {request_json}"
    assert locked_template["render_script_path"].endswith("templates/cohort_flow_figure/render.R")
    assert len(locked_template["render_script_sha256"]) == 64


def test_materialize_display_pack_publication_manifest_runs_multi_figure_batch(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle
    from med_autoscience.publication_figure_quality_contract import collect_publication_figure_quality_refs

    repo_root, paper_root = _build_workspace(tmp_path)
    _write_subprocess_renderable_template(repo_root)
    _write_json(
        paper_root / "data" / "frozen" / "secondary_curve.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-secondary",
            "series": [{"x": [0.0, 0.2, 1.0], "y": [0.0, 0.76, 1.0]}],
        },
    )
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "claim_ref": "claim:primary-discrimination",
                    "data_ref": "paper/data/frozen/primary_curve.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": ["analysis/statistics/auc_primary"],
                },
                {
                    "figure_id": "F2",
                    "claim_ref": "claim:secondary-discrimination",
                    "data_ref": "paper/data/frozen/secondary_curve.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": ["analysis/statistics/auc_secondary"],
                },
            ],
        },
    )
    _write_json(
        paper_root / "figure_specs.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "schema_version": 1,
                    "figure_id": "F1",
                    "intent_ref": "paper/figure_intent.json#/figures/F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": "study/cohorts/derivation",
                        "endpoint_ref": "endpoint:mace",
                        "model_ref": "model:cox-primary",
                        "risk_horizon": "5y",
                        "effect_estimate_ref": "analysis/statistics/auc_primary",
                        "claim_role": "primary_evidence",
                    },
                    "panels": [{"panel_id": "A", "data_role": "discrimination", "mark_role": "roc_curve"}],
                },
                {
                    "schema_version": 1,
                    "figure_id": "F2",
                    "intent_ref": "paper/figure_intent.json#/figures/F2",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": "study/cohorts/validation",
                        "endpoint_ref": "endpoint:mace",
                        "model_ref": "model:cox-secondary",
                        "risk_horizon": "5y",
                        "effect_estimate_ref": "analysis/statistics/auc_secondary",
                        "claim_role": "secondary_evidence",
                    },
                    "panels": [{"panel_id": "A", "data_role": "discrimination", "mark_role": "roc_curve"}],
                },
            ],
        },
    )

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
    )

    assert [figure["figure_id"] for figure in result["figures"]] == ["F1", "F2"]
    style_hashes = {figure["publication_style_profile"]["sha256"] for figure in result["figures"]}
    assert style_hashes == {result["publication_style_profile"]["sha256"]}
    assert {figure["render_result"]["execution_mode"] for figure in result["figures"]} == {
        "subprocess",
    }
    assert {figure["renderer_family"] for figure in result["figures"]} == {"r_ggplot2"}
    assert (paper_root / "build" / "display_artifact_manifest.F1.json").exists()
    assert (paper_root / "build" / "display_artifact_manifest.F2.json").exists()
    assert [item["figure_id"] for item in json.loads((paper_root / "figure_visual_audit_receipt.json").read_text())["inspected_artifacts"]] == [
        "F1",
        "F2",
    ]
    lifecycle = load_figure_polish_lifecycle(paper_root / "figure_polish_lifecycle.json")
    assert len(lifecycle["events"]) == 12
    assert [event["state"] for event in lifecycle["events"][:6]] == [
        "draft_rendered",
        "deterministic_qc_clear",
        "visual_audit_findings",
        "revised",
        "audit_clear",
        "publication_manifested",
    ]
    assert [event["figure_id"] for event in lifecycle["events"][6:]] == ["F2"] * 6
    refs = collect_publication_figure_quality_refs(paper_root=paper_root)
    assert refs["medical_figure_spec"]["status"] == "present"
    assert refs["medical_figure_specs"]["status"] == "present"
