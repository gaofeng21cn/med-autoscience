from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_display_pack_config(repo_root: Path) -> None:
    (repo_root / "config").mkdir(parents=True)
    (repo_root / "config" / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
version = "0.3.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_renderable_pack(repo_root: Path) -> None:
    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    template_root = pack_root / "templates" / "roc_curve_binary"
    module_root = pack_root / "src" / "demo_display_core"
    template_root.mkdir(parents=True)
    module_root.mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.3.0"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "E2E renderable test pack"',
                'maintainer = "MAS tests"',
                'license = "MIT"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "python"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'style_profile_ref = "paper_neutral_clinical_v1"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "demo_display_core.renderers:render_template"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (module_root / "__init__.py").write_text("", encoding="utf-8")
    (module_root / "renderers.py").write_text(
        """
from __future__ import annotations

import json


def render_template(*, template_id, display_payload, output_png_path, output_pdf_path, layout_sidecar_path):
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    layout_sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    output_png_path.write_text("PNG:" + template_id, encoding="utf-8")
    output_pdf_path.write_text("%PDF:" + template_id, encoding="utf-8")
    layout_sidecar_path.write_text(
        json.dumps(
            {
                "template_id": "roc_curve_binary",
                "device": {"width": 10.0, "height": 8.0},
                "layout_boxes": [
                    {"box_id": "title", "box_type": "title", "x0": 1.0, "y0": 0.1, "x1": 8.8, "y1": 0.55},
                    {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.2, "y0": 2.0, "x1": 0.7, "y1": 6.0},
                    {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 3.0, "y0": 7.2, "x1": 7.0, "y1": 7.7},
                ],
                "panel_boxes": [
                    {"box_id": "panel", "box_type": "panel", "x0": 1.2, "y0": 1.0, "x1": 8.0, "y1": 6.7}
                ],
                "guide_boxes": [
                    {"box_id": "legend", "box_type": "legend", "x0": 8.2, "y0": 1.0, "x1": 9.7, "y1": 2.0}
                ],
                "metrics": {
                    "series": [{"x": [0.0, 0.4, 1.0], "y": [0.0, 0.82, 1.0]}],
                    "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                },
                "render_context": display_payload["render_context"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\\n",
        encoding="utf-8",
    )
    return {"status": "rendered", "template_id": template_id}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_subprocess_renderable_template(repo_root: Path) -> None:
    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    template_root = pack_root / "templates" / "roc_curve_binary_ggplot2"
    template_root.mkdir(parents=True)
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary_ggplot2"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve (R/ggplot2 subprocess)"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'style_profile_ref = "paper_neutral_clinical_v1"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "subprocess"',
                f'entrypoint = "{sys.executable} render_subprocess.py --request {{request_json}}"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "render_subprocess.py").write_text(
        """
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    output_png_path = Path(request["output_png_path"])
    output_pdf_path = Path(request["output_pdf_path"])
    layout_sidecar_path = Path(request["layout_sidecar_path"])
    for path in (output_png_path, output_pdf_path, layout_sidecar_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    output_png_path.write_text("PNG:subprocess:" + request["template_id"], encoding="utf-8")
    output_pdf_path.write_text("%PDF:subprocess:" + request["template_id"], encoding="utf-8")
    layout_sidecar_path.write_text(
        json.dumps(
            {
                "template_id": "roc_curve_binary_ggplot2",
                "device": {"width": 10.0, "height": 8.0},
                "layout_boxes": [
                    {"box_id": "title", "box_type": "title", "x0": 1.0, "y0": 0.1, "x1": 8.8, "y1": 0.55},
                    {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.2, "y0": 2.0, "x1": 0.7, "y1": 6.0},
                    {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 3.0, "y0": 7.2, "x1": 7.0, "y1": 7.7},
                ],
                "panel_boxes": [
                    {"box_id": "panel", "box_type": "panel", "x0": 1.2, "y0": 1.0, "x1": 8.0, "y1": 6.7}
                ],
                "guide_boxes": [
                    {"box_id": "legend", "box_type": "legend", "x0": 8.2, "y0": 1.0, "x1": 9.7, "y1": 2.0}
                ],
                "metrics": {
                    "series": [{"x": [0.0, 0.4, 1.0], "y": [0.0, 0.82, 1.0]}],
                    "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                },
                "render_context": request["display_payload"]["render_context"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\\n",
        encoding="utf-8",
    )
    print(json.dumps({"renderer": "subprocess", "figure_id": request["figure_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_paper_inputs(paper_root: Path) -> None:
    _write_json(
        paper_root / "data" / "frozen" / "primary_curve.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-primary",
            "series": [{"x": [0.0, 0.4, 1.0], "y": [0.0, 0.82, 1.0]}],
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
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
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
            "panels": [
                {
                    "panel_id": "A",
                    "data_role": "discrimination",
                    "mark_role": "roc_curve",
                }
            ],
        },
    )
    _write_json(
        paper_root / "publication_style_profile.json",
        {
            "schema_version": 1,
            "style_profile_id": "paper_neutral_clinical_v1",
            "palette": {"primary": "#245A6B", "secondary": "#B89A6D", "neutral": "#6B7280"},
            "semantic_roles": {
                "model_curve": "primary",
                "comparator_curve": "secondary",
                "reference_line": "neutral",
            },
            "typography": {"title_size": 12.0},
            "stroke": {"primary_linewidth": 2.0},
        },
    )
    _write_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_style_reference_bundle.json",
        {
            "schema_version": 1,
            "bundle_id": "lab-display-style-v1",
            "references": [
                {
                    "reference_id": "reference-roc",
                    "source_ref": "https://example.org/reference-paper",
                    "decision": "adopt",
                    "applies_to": ["fenggaolab.org.medical-display-core::roc_curve_binary"],
                    "style_notes": ["compact legend", "print-safe neutral reference line"],
                }
            ],
        },
    )


def _write_real_core_r_paper_inputs(paper_root: Path) -> None:
    _write_paper_inputs(paper_root)
    _write_json(
        paper_root / "data" / "frozen" / "primary_curve.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-primary",
            "title": "Primary ROC",
            "x_label": "1 - Specificity",
            "y_label": "Sensitivity",
            "series": [
                {
                    "label": "Primary model",
                    "x": [0.0, 0.2, 0.6, 1.0],
                    "y": [0.0, 0.72, 0.9, 1.0],
                },
                {
                    "label": "Comparator",
                    "x": [0.0, 0.3, 0.7, 1.0],
                    "y": [0.0, 0.58, 0.82, 1.0],
                },
            ],
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
        },
    )


def _visual_audit_review() -> dict[str, object]:
    return {
        "audit_mode": "human_visual_review",
        "reviewer": {
            "provider": "mas-test-reviewer",
            "model": "fixture-human-review",
            "prompt_hash": "d" * 64,
        },
        "findings": [],
        "final_status": "clear",
    }


def _build_workspace(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    paper_root = tmp_path / "workspace" / "paper"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    _write_renderable_pack(repo_root)
    _write_paper_inputs(paper_root)
    return repo_root, paper_root


def test_materialize_display_pack_publication_manifest_runs_full_quality_loop(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle
    from med_autoscience.publication_figure_quality_contract import (
        collect_publication_figure_quality_refs,
        load_figure_visual_audit_receipt,
    )

    repo_root, paper_root = _build_workspace(tmp_path)

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
    )

    assert result["status"] == "publication_manifested"
    assert result["publication_readiness_verdict"] is False
    assert result["authority_boundary"]["mas_publication_quality_authority"] is True
    assert result["authority_boundary"]["display_pack_lock_can_authorize_publication_readiness"] is False

    figure = result["figures"][0]
    assert figure["figure_id"] == "F1"
    assert figure["deterministic_qc"]["status"] == "pass"
    assert Path(figure["rendered_artifacts"]["png_path"]).exists()
    assert Path(figure["rendered_artifacts"]["pdf_path"]).exists()
    assert Path(figure["rendered_artifacts"]["layout_sidecar_path"]).exists()

    manifest_path = paper_root / "build" / "display_pack_publication_manifest.json"
    lock_path = paper_root / "build" / "display_pack_lock.json"
    artifact_manifest_path = paper_root / "build" / "display_artifact_manifest.F1.json"
    qc_path = paper_root / "qc" / "F1.layout_qc.json"
    assert manifest_path.exists()
    assert lock_path.exists()
    assert artifact_manifest_path.exists()
    assert qc_path.exists()

    visual_receipt = load_figure_visual_audit_receipt(paper_root / "figure_visual_audit_receipt.json")
    assert visual_receipt["inspected_artifacts"][0]["artifact_sha256"] == figure["rendered_artifacts"]["png_sha256"]
    assert visual_receipt["final_status"] == "clear"

    lifecycle = load_figure_polish_lifecycle(paper_root / "figure_polish_lifecycle.json")
    assert [event["state"] for event in lifecycle["events"]] == [
        "draft_rendered",
        "deterministic_qc_clear",
        "visual_audit_findings",
        "revised",
        "audit_clear",
        "publication_manifested",
    ]

    refs = collect_publication_figure_quality_refs(paper_root=paper_root)
    assert refs["figure_intent"]["status"] == "present"
    assert refs["medical_figure_spec"]["status"] == "present"
    assert refs["figure_style_reference_bundle"]["status"] == "present"
    assert refs["figure_visual_audit_receipt"]["status"] == "present"
    assert refs["figure_polish_lifecycle"]["status"] == "present"


def test_cli_publication_display_pack_e2e_emits_manifest_json(tmp_path: Path, capsys) -> None:
    from med_autoscience import cli

    repo_root, paper_root = _build_workspace(tmp_path)

    exit_code = cli.main(
        [
            "publication",
            "display-pack-e2e",
            "--repo-root",
            str(repo_root),
            "--paper-root",
            str(paper_root),
            "--visual-audit-review-json",
            json.dumps(_visual_audit_review()),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "publication_manifested"
    assert payload["manifest_path"].endswith("paper/build/display_pack_publication_manifest.json")


def test_materialize_display_pack_publication_manifest_runs_subprocess_renderer(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    repo_root, paper_root = _build_workspace(tmp_path)
    _write_subprocess_renderable_template(repo_root)
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F2",
                    "claim_ref": "claim:secondary-discrimination",
                    "data_ref": "paper/data/frozen/primary_curve.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": ["analysis/statistics/auc_secondary"],
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
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
    )

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
    )

    figure = result["figures"][0]
    assert figure["figure_id"] == "F2"
    assert figure["render_result"]["execution_mode"] == "subprocess"
    assert figure["render_result"]["renderer_family"] == "r_ggplot2"
    assert figure["render_result"]["returncode"] == 0
    assert Path(figure["render_result"]["request_path"]).exists()
    assert Path(figure["render_result"]["stdout_path"]).read_text(encoding="utf-8").strip()
    assert Path(figure["rendered_artifacts"]["png_path"]).read_text(encoding="utf-8").startswith("PNG:subprocess:")


def test_materialize_display_pack_publication_manifest_runs_real_core_r_subprocess_renderer(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    assert shutil.which("Rscript") is not None
    repo_root = Path(__file__).resolve().parents[1]
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
    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
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
    assert {figure["render_result"]["execution_mode"] for figure in result["figures"]} == {
        "python_plugin",
        "subprocess",
    }
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
