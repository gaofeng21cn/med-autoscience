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
