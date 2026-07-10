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
    assert render_result["entrypoint"] == (
        "Rscript ../../render.R --template roc_curve_binary --mode {render_mode} --request {request_json}"
    )
    assert render_result["argv"][:7] == [
        "Rscript",
        "../../render.R",
        "--template",
        "roc_curve_binary",
        "--mode",
        "final",
        "--request",
    ]
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
    assert locked_template["entrypoint"] == render_result["entrypoint"]
    assert locked_template["render_script_path"] is None
    assert locked_template["render_script_sha256"] is None


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
    assert render_result["entrypoint"] == (
        "Rscript ../../render.R --template cohort_flow_figure --mode {render_mode} --request {request_json}"
    )
    assert render_result["argv"][:7] == [
        "Rscript",
        "../../render.R",
        "--template",
        "cohort_flow_figure",
        "--mode",
        "final",
        "--request",
    ]
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
    assert locked_template["entrypoint"] == render_result["entrypoint"]
    assert locked_template["render_script_path"] is None
    assert locked_template["render_script_sha256"] is None


def test_display_pack_publication_manifest_auto_consumes_prepared_dependency_environment_for_cohort_flow(
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
    _write_json(
        paper_root / "build" / "dependency_environment_receipt.json",
        {
            "schema_version": 1,
            "status": "prepared",
            "failure_class": "",
            "lock_ref": "paper/build/dependency_environment_lock.json",
            "environment_ref": "test-ggconsort-managed-r-library",
            "cache_key": "test-ggconsort-managed-r-library",
            "target_platform": "test-platform",
            "run_context_ref": dependency_environment["run_context_ref"],
        },
    )
    _write_cohort_flow_paper_inputs(paper_root)

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
        figure_ids=["F_cohort"],
    )

    assert result["dependency_environment"]["status"] == "prepared"
    assert result["dependency_environment"]["run_context_ref"] == "paper/build/dependency_run_context.json"
    assert result["dependency_environment"]["run_context_fingerprint"] == "sha256:test-ggconsort-run-context"
    figure = result["figures"][0]
    assert figure["dependency_environment"]["status"] == "prepared"
    assert figure["render_result"]["returncode"] == 0
    request_payload = json.loads(Path(figure["render_result"]["request_path"]).read_text(encoding="utf-8"))
    assert request_payload["dependency_environment"]["status"] == "prepared"
    layout_sidecar = json.loads(Path(figure["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["uses_ggconsort"] is True
    assert layout_sidecar["metrics"]["opl_dependency_run_context_fingerprint"] == (
        "sha256:test-ggconsort-run-context"
    )


def test_materialize_display_pack_publication_manifest_runs_cohort_source_layer_accounting_mode(
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
        paper_root / "data" / "frozen" / "cohort_flow.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-source-layer-flow",
            "title": "Cohort and source-layer accounting",
            "flow_mode": "source_layer_accounting",
            "denominator_step_id": "registry_records",
            "steps": [
                {"step_id": "registry_records", "label": "Declared analytic registry records", "n": 4189},
                {"step_id": "alliance_platform_records", "label": "Alliance platform source layer", "n": 2451},
                {"step_id": "xiangya2_management_records", "label": "Xiangya2 management clinic source layer", "n": 1204},
                {"step_id": "xiangya2_precision_records", "label": "Xiangya2 precision clinic source layer", "n": 534},
            ],
            "source_layers": [
                {
                    "layer_id": "alliance_platform_records",
                    "step_id": "alliance_platform_records",
                    "label": "Alliance platform source layer",
                    "n": 2451,
                },
                {
                    "layer_id": "xiangya2_management_records",
                    "step_id": "xiangya2_management_records",
                    "label": "Xiangya2 management clinic source layer",
                    "n": 1204,
                },
                {
                    "layer_id": "xiangya2_precision_records",
                    "step_id": "xiangya2_precision_records",
                    "label": "Xiangya2 precision clinic source layer",
                    "n": 534,
                },
            ],
            "subcohort_coverage": [
                {"coverage_id": "xiangya2_subcohort", "label": "Xiangya2 subcohort", "n": 1748, "denominator_n": 4189},
                {"coverage_id": "phq9_available", "label": "PHQ-9 available", "n": 979, "denominator_n": 1748},
                {"coverage_id": "gad7_available", "label": "GAD-7 available", "n": 993, "denominator_n": 1748},
            ],
            "exported_centers": 33,
            "exclusions": [],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F_cohort",
            "intent_ref": "paper/figure_intent.json#/figures/F_cohort",
            "template_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
            "figure_kind": "illustration_shell",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/registry",
                "claim_role": "source_layer_accounting",
            },
            "panels": [
                {"panel_id": "A", "data_role": "source_layer_accounting", "mark_role": "source_layer_boxes"},
                {"panel_id": "B", "data_role": "subcohort_coverage", "mark_role": "coverage_bars"},
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
    layout_sidecar = json.loads(Path(figure["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    metrics = layout_sidecar["metrics"]
    assert figure["deterministic_qc"]["status"] == "pass"
    assert metrics["layout_mode"] == "source_layer_accounting"
    assert metrics["reporting_flow_kind"] == "cohort_source_layer_and_subcohort_coverage"
    assert metrics["figure_purpose"] == "participant_accounting_and_strobe_source_boundary"
    assert metrics["renderer_family"] == "r_ggplot2"
    assert metrics["uses_ggconsort"] is True
    assert metrics["panel_ids"] == ["A", "B"]
    assert [item["n"] for item in metrics["source_layers"]] == [2451, 1204, 534]
    assert [item["n"] for item in metrics["subcohort_coverage"]] == [1748, 979, 993]
    assert metrics["exported_centers"] == 33
    assert not any(item["box_type"] == "flow_connector" for item in layout_sidecar["guide_boxes"])
    assert any(item["box_type"] == "source_layer_connector" for item in layout_sidecar["guide_boxes"])


def test_materialize_display_pack_publication_manifest_keeps_obesity_cohort_flow_inside_panel(
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
        paper_root / "data" / "frozen" / "cohort_flow.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-obesity-cohort-flow",
            "title": "Multicenter obesity phenotype cohort flow",
            "steps": [
                    {
                        "step_id": "xiangya1_records",
                        "label": "Xiangya Hospital source records with BMI and follow-up linkage",
                        "detail": "Derivation source before adult eligibility and duplicate cleanup",
                        "n": 472638,
                    },
                    {
                        "step_id": "xiangya1_analysis",
                        "label": "Xiangya derivation cohort after adult eligibility and duplicate cleanup",
                        "detail": "Primary phenotype atlas analysis set",
                        "n": 174522,
                    },
                    {
                        "step_id": "xiangya2_records",
                        "label": "Xiangya Second Hospital temporal validation records",
                        "detail": "External validation source before observation-window checks",
                        "n": 291604,
                    },
                    {
                        "step_id": "xiangya2_precision_records",
                        "label": "External precision analysis cohort with harmonized phenotype windows",
                        "detail": "Harmonized endpoint-window analysis set",
                        "n": 83617,
                    },
            ],
            "exclusions": [
                {
                    "exclusion_id": "missing_bmi_followup",
                    "from_step_id": "xiangya1_records",
                    "label": "Missing BMI, age, sex, or follow-up anchor",
                    "n": 298116,
                },
                {
                    "exclusion_id": "short_observation",
                    "from_step_id": "xiangya2_records",
                    "label": "Insufficient observation window for endpoint ascertainment",
                    "n": 207987,
                },
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "obesity_complication",
                    "label": "Incident obesity-related complication composite",
                    "event_n": 18429,
                    "detail": "Events counted after phenotype-index date across harmonized follow-up windows",
                }
            ],
            "design_panels": [
                {
                    "panel_id": "interpretation_boundary",
                    "title": "Interpretation boundary",
                    "lines": [
                        {
                            "label": "Multicenter EHR phenotype atlas",
                            "detail": "Descriptive association and transportability analysis, not causal treatment effect estimation",
                        },
                        {
                            "label": "Harmonized phenotype windows",
                            "detail": "BMI category and endpoint windows were aligned before site-level comparison",
                        },
                        {
                            "label": "External validation",
                            "detail": "Xiangya Second Hospital supports transportability assessment after local data-quality checks",
                        },
                        {
                            "label": "Clinical guardrail",
                            "detail": "Claims remain bounded to phenotype description and risk-stratification support",
                        },
                    ],
                }
            ],
            "comparison_summary": [],
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
    assert figure["deterministic_qc"]["status"] == "pass"
    layout_sidecar = json.loads(Path(figure["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["uses_ggconsort"] is True
    assert layout_sidecar["metrics"]["step_detail_render_policy"] == "metadata_only_not_drawn"
    assert (
        layout_sidecar["metrics"]["step_detail_truncation_policy"]
        == "no_ellipsis_truncation_complete_wrapped_text"
    )
    panel = next(item for item in layout_sidecar["panel_boxes"] if item["box_id"] == "participant_flow_main")
    main_steps = [item for item in layout_sidecar["layout_boxes"] if item["box_type"] == "main_step"]
    flow_nodes = [item for item in layout_sidecar["metrics"]["flow_nodes"] if item["box_type"] == "main_step"]
    assert len(main_steps) == 4
    assert all(item["line_count"] > 2 for item in flow_nodes)
    assert all(item["detail_truncated"] is False for item in flow_nodes)
    for box in main_steps:
        assert box["x0"] >= panel["x0"]
        assert box["x1"] <= panel["x1"]
        assert box["y0"] >= panel["y0"]
        assert box["y1"] <= panel["y1"]


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
