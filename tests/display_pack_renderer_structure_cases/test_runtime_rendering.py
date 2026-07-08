from __future__ import annotations

from tests.display_pack_renderer_structure_cases.common import (
    CORE_PACK_MODULE_ROOT,
    CORE_PACK_ROOT,
    CORE_PACK_SRC_ROOT,
    REPO_ROOT,
    SimpleNamespace,
    _candidate_request,
    importlib,
    json,
    os,
    subprocess,
    sys,
    tempfile,
    tomllib,
    Path,
)


def test_core_pack_representative_lidocaineq_default_renderers_render_with_r_subprocess() -> None:
    source_renderers_by_template = {
        "risk_layering_monotonic_bars": "LidocaineQ/Figure_Template::risk_layering_monotonic_bars",
        "omics_volcano_panel": "LidocaineQ/Figure_Template::volcano_deg",
        "shap_summary_beeswarm": "LidocaineQ/Figure_Template::shap_summary_beeswarm",
    }
    default_payloads: dict[str, dict[str, object]] = {
        "risk_layering_monotonic_bars": {
            "title": "Risk group summary",
            "x_label": "Risk group",
            "y_label": "Five-year risk",
            "risk_group_summaries": [
                {"label": "Low", "mean_predicted_risk_5y": 0.08, "observed_km_risk_5y": 0.07, "events_5y": 12},
                {"label": "High", "mean_predicted_risk_5y": 0.26, "observed_km_risk_5y": 0.29, "events_5y": 44},
            ],
        },
        "omics_volcano_panel": {
            "title": "Volcano candidate",
            "x_label": "log2 fold change",
            "y_label": "-log10 FDR",
            "effect_threshold": 1.0,
            "significance_threshold": 1.3,
            "points": [
                {
                    "panel_id": "A",
                    "feature_label": "IFNG",
                    "effect_value": 1.4,
                    "significance_value": 3.2,
                    "regulation_class": "upregulated",
                },
                {
                    "panel_id": "A",
                    "feature_label": "MKI67",
                    "effect_value": -1.2,
                    "significance_value": 2.7,
                    "regulation_class": "downregulated",
                },
            ],
        },
        "shap_summary_beeswarm": {
            "title": "SHAP candidate",
            "x_label": "SHAP value",
            "rows": [
                {
                    "feature": "Age",
                    "points": [
                        {"shap_value": -0.12, "feature_value": 0.20},
                        {"shap_value": 0.23, "feature_value": 0.85},
                    ],
                },
                {
                    "feature": "Ki-67",
                    "points": [
                        {"shap_value": -0.08, "feature_value": 0.35},
                        {"shap_value": 0.18, "feature_value": 0.72},
                    ],
                },
            ],
        },
    }
    with tempfile.TemporaryDirectory(prefix="mas-display-lidocaineq-r-") as tmpdir:
        output_dir = Path(tmpdir)
        for template_id, payload in default_payloads.items():
            request_path = _candidate_request(template_id=template_id, payload=payload, output_dir=output_dir)
            completed = subprocess.run(
                ["Rscript", "render.R", "--request", str(request_path)],
                cwd=CORE_PACK_ROOT / "templates" / template_id,
                capture_output=True,
                text=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr
            assert (output_dir / f"{template_id}.png").is_file()
            assert (output_dir / f"{template_id}.pdf").is_file()
            sidecar = json.loads((output_dir / f"{template_id}.layout.json").read_text(encoding="utf-8"))
            assert sidecar["template_id"] == template_id
            assert sidecar["metrics"]["renderer"] == "r_ggplot2_evidence_subprocess_v1"
            assert sidecar["metrics"]["renderer_role"] == "default"
            assert sidecar["metrics"]["source_renderer"] == source_renderers_by_template[template_id]


def test_cli_display_pack_render_candidate_runs_legacy_comparison_surface(tmp_path: Path, capsys) -> None:
    from med_autoscience import cli

    payload_path = tmp_path / "payload.json"
    output_dir = tmp_path / "candidate-output"
    payload_path.write_text(
        json.dumps(
            {
                "title": "Risk group summary",
                "x_label": "Risk group",
                "y_label": "Five-year risk",
                "risk_group_summaries": [
                    {"label": "Low", "mean_predicted_risk_5y": 0.08, "observed_km_risk_5y": 0.07, "events_5y": 12},
                    {"label": "High", "mean_predicted_risk_5y": 0.26, "observed_km_risk_5y": 0.29, "events_5y": 44},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "display-pack-render-candidate",
            "--repo-root",
            str(REPO_ROOT),
            "--template-id",
            "risk_layering_monotonic_bars",
            "--display-payload-file",
            str(payload_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["status"] == "rendered"
    assert result["candidate_only"] is True
    assert result["comparison_only"] is True
    assert result["publication_readiness_verdict"] is False
    assert result["template_id"] == "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars"
    assert result["candidate_entrypoint"] == "Rscript render_candidate.R --request {request_json}"
    assert result["authority_boundary"]["candidate_can_authorize_publication_readiness"] is False
    assert result["authority_boundary"]["candidate_can_mutate_data_or_statistics"] is False
    assert result["authority_boundary"]["candidate_can_replace_default_renderer"] is False
    assert result["authority_boundary"]["comparison_receipt_can_replace_default_renderer"] is False
    assert result["authority_boundary"]["default_renderer_promotion_already_landed"] is True
    assert result["default_renderer"]["renderer_family"] == "r_ggplot2"
    assert result["default_renderer"]["execution_mode"] == "subprocess"
    assert result["default_renderer"]["entrypoint"] == "Rscript render.R --request {request_json}"
    assert result["render_result"]["status"] == "rendered"
    assert Path(result["rendered_artifacts"]["png_path"]).is_file()
    assert Path(result["rendered_artifacts"]["pdf_path"]).is_file()
    assert Path(result["rendered_artifacts"]["layout_sidecar_path"]).is_file()
    assert Path(result["render_result"]["request_path"]).is_file()
    assert Path(result["render_result"]["stdout_path"]).is_file()
    assert Path(result["render_result"]["stderr_path"]).is_file()
    render_request = json.loads(Path(result["render_result"]["request_path"]).read_text(encoding="utf-8"))
    assert render_request["candidate_only"] is True
    assert render_request["comparison_only"] is True
    sidecar = json.loads(Path(result["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    assert sidecar["metrics"]["renderer"] == "r_ggplot2_comparison_subprocess_v1"
    assert sidecar["metrics"]["renderer_role"] == "comparison"
