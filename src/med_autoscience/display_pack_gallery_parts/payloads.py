from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import tempfile

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.publication_display_contract import (
    load_publication_style_profile,
    resolve_style_roles,
)
from med_autoscience.display_pack_gallery_parts.publication_payloads import (
    PUBLICATION_R_DISPLAY_PAYLOADS,
)
from med_autoscience.display_pack_gallery_parts.core_payloads import (
    CORE_R_DISPLAY_PAYLOADS,
)
from med_autoscience.display_pack_gallery_parts.lidocaineq_payloads import (
    LIDOCAINEQ_R_DISPLAY_PAYLOADS,
)


LIDOCAINEQ_REFERENCE_DEVICE_SIZES: dict[str, tuple[float, float]] = {
    "alluvial_transition": (5.3, 3.5),
    "calibration_curve_binary": (4.8, 4.8),
    "celltype_marker_dotplot_panel": (5.4, 3.7),
    "cnv_recurrence_summary_panel": (5.3, 3.4),
    "coefficient_path_panel": (4.8, 4.8),
    "composition_stacked_bar": (5.2, 3.4),
    "confusion_matrix_heatmap_binary": (4.8, 4.8),
    "correlation_scatter": (4.8, 4.8),
    "cumulative_incidence_grouped": (4.8, 4.8),
    "decision_curve_binary": (4.8, 4.8),
    "distribution_violin_box": (4.8, 4.8),
    "forest_effect_main": (4.8, 4.8),
    "generalizability_subgroup_composite_panel": (4.8, 4.8),
    "genomic_alteration_consequence_panel": (5.3, 3.5),
    "genomic_alteration_landscape_panel": (7.0, 4.8),
    "heatmap_group_comparison": (5.2, 3.7),
    "kaplan_meier_grouped": (4.8, 4.8),
    "model_complexity_audit_panel": (4.8, 4.8),
    "omics_volcano_panel": (4.8, 4.8),
    "pathway_enrichment_dotplot_panel": (5.3, 3.7),
    "pr_curve_binary": (4.8, 4.8),
    "radar_profile": (4.8, 4.8),
    "risk_layering_monotonic_bars": (5.2, 3.4),
    "roc_curve_binary": (4.8, 4.8),
    "shap_dependence_panel": (4.8, 4.8),
    "shap_summary_beeswarm": (4.8, 4.8),
    "shap_waterfall_local_explanation_panel": (5.3, 3.5),
    "table1_baseline_characteristics": (5.7, 3.2),
    "time_dependent_roc_horizon": (4.8, 4.8),
    "time_to_event_decision_curve": (4.8, 4.8),
    "time_to_event_multihorizon_calibration_panel": (4.8, 4.8),
    "waterfall_response": (5.3, 3.4),
}


MANUAL_GALLERY_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "cohort_flow_figure": {
        "schema_version": 1,
        "shell_id": "cohort_flow_figure",
        "display_id": "Figure1",
        "title": "Cohort derivation and analysis sets",
        "caption": "Synthetic CONSORT/STROBE-style cohort disposition preview for the Display Pack Gallery.",
        "layout_mode": "participant_flow",
        "steps": [
            {"step_id": "source", "label": "Source records", "n": 18642, "detail": "Consecutive registry records"},
            {"step_id": "eligible", "label": "Met eligibility criteria", "n": 15787, "detail": "Index admission and complete baseline window"},
            {"step_id": "analysis", "label": "Primary analytic cohort", "n": 15120, "detail": "Outcome status and model inputs available"},
            {"step_id": "validation", "label": "Locked validation set", "n": 4536, "detail": "Temporal holdout for primary estimate"},
        ],
        "exclusions": [
            {
                "exclusion_id": "incomplete_baseline",
                "from_step_id": "source",
                "label": "Incomplete baseline window",
                "detail": "Missing exposure or covariate source",
                "n": 2855,
            },
            {
                "exclusion_id": "missing_outcome",
                "from_step_id": "eligible",
                "label": "Outcome not auditable",
                "detail": "No linked follow-up record before lock",
                "n": 667,
            }
        ],
        "endpoint_inventory": [
            {"endpoint_id": "primary", "label": "Primary endpoint", "detail": "Cardiovascular mortality", "n": 812},
            {"endpoint_id": "secondary", "label": "Secondary endpoint", "detail": "Heart-failure hospitalization", "n": 1468},
        ],
        "design_panels": [
            {
                "panel_id": "split",
                "layout_role": "wide_top",
                "style_role": "primary",
                "title": "Analysis split",
                "lines": [
                    {"label": "Derivation", "detail": "70% temporal training set"},
                    {"label": "Validation", "detail": "30% locked temporal holdout"},
                ],
            },
            {
                "panel_id": "review",
                "layout_role": "wide_bottom",
                "style_role": "context",
                "title": "Audit boundary",
                "lines": [
                    {"label": "Counts", "detail": "Participant accounting table required"},
                    {"label": "Outcomes", "detail": "Endpoint definition and source ledger required"},
                ],
            },
        ],
        "comparison_summary": {"title": "Reporting note", "body": "Synthetic counts illustrate structured reporting only."},
    },
    "submission_graphical_abstract": {
        "schema_version": 1,
        "shell_id": "submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "paper_role": "submission_companion",
        "layout_style": "square_storyline",
        "title": "Cohort to risk-stratified care",
        "caption": "Synthetic graphical abstract preview for the Display Pack Gallery.",
        "panels": [
            {
                "panel_id": "population",
                "panel_label": "A",
                "visual_role": "population",
                "evidence_token": "n=15,120",
                "title": "Population",
                "subtitle": "Cohort locked before modeling",
                "rows": [{"cards": [{"card_id": "cohort", "title": "Analytic cohort", "value": "15,120", "evidence_token": "n=15,120", "detail": "auditable outcomes", "accent_role": "primary"}]}],
            },
            {
                "panel_id": "model_signal",
                "panel_label": "B",
                "visual_role": "model_signal",
                "evidence_token": "C=0.86",
                "title": "Model signal",
                "subtitle": "Primary endpoint risk ranking",
                "rows": [{"cards": [{"card_id": "c_index", "title": "Validation C-index", "value": "0.86", "evidence_token": "C=0.86", "detail": "temporal holdout", "accent_role": "contrast"}]}],
            },
            {
                "panel_id": "clinical_use",
                "panel_label": "C",
                "visual_role": "clinical_use",
                "evidence_token": "3.4x",
                "title": "Clinical use",
                "subtitle": "Risk-stratified follow-up",
                "rows": [{"cards": [{"card_id": "risk_group", "title": "High-risk group", "value": "3.4x", "evidence_token": "3.4x", "detail": "event enrichment", "accent_role": "secondary"}]}],
            },
        ],
        "footer_pills": [
            {"pill_id": "p1", "panel_id": "population", "label": "Cohort lock", "style_role": "primary"},
            {"pill_id": "p2", "panel_id": "model_signal", "label": "Model evidence", "style_role": "contrast"},
            {"pill_id": "p3", "panel_id": "clinical_use", "label": "Clinical message", "style_role": "secondary"},
        ],
    },
    "binary_calibration_decision_curve_panel": {
        "display_id": "Figure3",
        "template_id": "binary_calibration_decision_curve_panel",
        "title": "Calibration and decision curve comparison",
        "caption": "Synthetic calibration and decision curve preview for the R/ggplot2 gallery.",
        "calibration_x_label": "Mean predicted probability",
        "calibration_y_label": "Observed probability",
        "decision_x_label": "Threshold probability",
        "decision_y_label": "Net benefit",
        "calibration_axis_window": {"xmin": 0.0, "xmax": 0.5, "ymin": 0.0, "ymax": 0.35},
        "calibration_reference_line": {"label": "Ideal", "x": [0.0, 1.0], "y": [0.0, 1.0]},
        "calibration_series": [
            {"label": "Comparator model", "x": [0.15, 0.25, 0.35, 0.45], "y": [0.04, 0.08, 0.16, 0.32]},
            {"label": "Clinical model", "x": [0.05, 0.10, 0.18, 0.30], "y": [0.03, 0.05, 0.14, 0.31]},
        ],
        "decision_series": [
            {"label": "Comparator model", "x": [0.15, 0.20, 0.25, 0.30, 0.35], "y": [0.01, 0.0, -0.01, -0.005, -0.002]},
            {"label": "Clinical model", "x": [0.15, 0.20, 0.25, 0.30, 0.35], "y": [0.06, 0.05, 0.04, 0.03, 0.02]},
        ],
        "decision_reference_lines": [
            {"label": "Treat none", "x": [0.15, 0.20, 0.25, 0.30, 0.35], "y": [0.0, 0.0, 0.0, 0.0, 0.0]},
            {"label": "Treat all", "x": [0.15, 0.20, 0.25, 0.30, 0.35], "y": [0.01, -0.03, -0.08, -0.14, -0.22]},
        ],
        "decision_focus_window": {"xmin": 0.15, "xmax": 0.35},
    },
    "risk_layering_monotonic_bars": {
        "display_id": "Figure22",
        "template_id": "risk_layering_monotonic_bars",
        "title": "Risk layering by score band",
        "caption": "Synthetic monotonic risk layering preview for the R/ggplot2 gallery.",
        "y_label": "Outcome risk (%)",
        "left_panel_title": "Comparator score",
        "left_x_label": "Risk tertile",
        "left_bars": [
            {"label": "Low", "cases": 118, "events": 5, "risk": 0.04},
            {"label": "Intermediate", "cases": 118, "events": 9, "risk": 0.08},
            {"label": "High", "cases": 118, "events": 37, "risk": 0.31},
        ],
        "right_panel_title": "Clinical score",
        "right_x_label": "Risk tertile",
        "right_bars": [
            {"label": "Low", "cases": 118, "events": 4, "risk": 0.03},
            {"label": "Intermediate", "cases": 118, "events": 10, "risk": 0.08},
            {"label": "High", "cases": 118, "events": 43, "risk": 0.36},
        ],
    },
    "shap_summary_beeswarm": {
        "display_id": "Figure13",
        "template_id": "shap_summary_beeswarm",
        "title": "SHAP summary beeswarm",
        "caption": "Synthetic feature-level SHAP distribution preview for the R/ggplot2 gallery.",
        "x_label": "SHAP value",
        "rows": [
            {
                "feature": "Tumor size",
                "points": [
                    {"shap_value": -0.42, "feature_value": 0.15},
                    {"shap_value": -0.16, "feature_value": 0.32},
                    {"shap_value": 0.18, "feature_value": 0.70},
                    {"shap_value": 0.31, "feature_value": 0.83},
                ],
            },
            {
                "feature": "Age",
                "points": [
                    {"shap_value": -0.18, "feature_value": 0.28},
                    {"shap_value": -0.05, "feature_value": 0.39},
                    {"shap_value": 0.11, "feature_value": 0.61},
                    {"shap_value": 0.22, "feature_value": 0.74},
                ],
            },
            {
                "feature": "Albumin",
                "points": [
                    {"shap_value": -0.24, "feature_value": 0.18},
                    {"shap_value": -0.12, "feature_value": 0.34},
                    {"shap_value": 0.04, "feature_value": 0.57},
                    {"shap_value": 0.16, "feature_value": 0.79},
                ],
            },
        ],
    },
}
GALLERY_R_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "celltype_signature_heatmap": {
        "display_id": "Figure26",
        "template_id": "celltype_signature_heatmap",
        "title": "Cell-type embedding and signature activity atlas",
        "caption": "Cell-type clusters and pathway-signature activity remain aligned across the circulating immune atlas.",
        "embedding_panel_title": "Embedding by cell type",
        "embedding_x_label": "UMAP 1",
        "embedding_y_label": "UMAP 2",
        "embedding_points": [
            {"x": -2.1, "y": 1.0, "group": "T cells"},
            {"x": -1.8, "y": 0.8, "group": "T cells"},
            {"x": 1.4, "y": -0.6, "group": "Myeloid"},
            {"x": 1.8, "y": -0.9, "group": "Myeloid"},
        ],
        "heatmap_panel_title": "Signature activity",
        "heatmap_x_label": "Cell type",
        "heatmap_y_label": "Program",
        "score_method": "AUCell",
        "row_order": [{"label": "IFN response"}, {"label": "TGF-beta signaling"}],
        "column_order": [{"label": "T cells"}, {"label": "Myeloid"}],
        "cells": [
            {"x": "T cells", "y": "IFN response", "value": 0.78},
            {"x": "Myeloid", "y": "IFN response", "value": -0.22},
            {"x": "T cells", "y": "TGF-beta signaling", "value": -0.18},
            {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.61},
        ],
    },
    "confusion_matrix_heatmap_binary": {
        "display_id": "Figure26",
        "template_id": "confusion_matrix_heatmap_binary",
        "title": "Binary confusion matrix",
        "caption": "Fixed-threshold classification errors.",
        "x_label": "Predicted label",
        "y_label": "True label",
        "metric_name": "N",
        "row_order": [{"label": "Negative"}, {"label": "Positive"}],
        "column_order": [{"label": "Negative"}, {"label": "Positive"}],
        "cells": [
            {"x": "Negative", "y": "Negative", "value": 132},
            {"x": "Positive", "y": "Negative", "value": 18},
            {"x": "Negative", "y": "Positive", "value": 24},
            {"x": "Positive", "y": "Positive", "value": 96},
        ],
    },
    "gsva_ssgsea_heatmap": {
        "display_id": "Figure23",
        "template_id": "gsva_ssgsea_heatmap",
        "title": "GSVA heatmap for immune and stromal programs",
        "caption": "Precomputed GSVA pathway scores across the analytic cohort highlight the dominant immune-stromal contrast.",
        "x_label": "Samples",
        "y_label": "Gene-set programs",
        "score_method": "GSVA",
        "row_order": [{"label": "IFN-gamma response"}, {"label": "TGF-beta signaling"}],
        "column_order": [{"label": "Sample-01"}, {"label": "Sample-02"}],
        "cells": [
            {"x": "Sample-01", "y": "IFN-gamma response", "value": 0.72},
            {"x": "Sample-02", "y": "IFN-gamma response", "value": -0.24},
            {"x": "Sample-01", "y": "TGF-beta signaling", "value": -0.11},
            {"x": "Sample-02", "y": "TGF-beta signaling", "value": 0.58},
        ],
    },
    "model_complexity_audit_panel": {
        "display_id": "model_audit",
        "template_id": "model_complexity_audit_panel",
        "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
        "caption": "Discrimination, calibration, and bounded complexity audit across candidate packages.",
        "metric_panels": [
            {
                "panel_id": "auroc_panel",
                "panel_label": "A",
                "title": "Discrimination",
                "x_label": "AUROC",
                "rows": [
                    {"label": "Core preoperative model", "value": 0.80},
                    {"label": "Clinically informed preoperative model", "value": 0.81},
                    {"label": "Random forest comparison model", "value": 0.84},
                ],
            },
            {
                "panel_id": "brier_panel",
                "panel_label": "B",
                "title": "Overall error",
                "x_label": "Brier score",
                "rows": [
                    {"label": "Core preoperative model", "value": 0.14},
                    {"label": "Clinically informed preoperative model", "value": 0.11},
                    {"label": "Random forest comparison model", "value": 0.10},
                ],
            },
        ],
        "audit_panels": [
            {
                "panel_id": "coefficient_panel",
                "panel_label": "C",
                "title": "Coefficient stability",
                "x_label": "Mean odds ratio",
                "reference_value": 1.0,
                "rows": [
                    {"label": "Age", "value": 0.91},
                    {"label": "Tumor diameter", "value": 1.44},
                    {"label": "Knosp grade", "value": 1.13},
                ],
            }
        ],
    },
    "performance_heatmap": {
        "display_id": "Figure25",
        "template_id": "performance_heatmap",
        "title": "AUC heatmap across APOE4 subgroups and predictor sets",
        "caption": "Random-forest discrimination remains strongest for the integrated model across APOE4-stratified analyses.",
        "x_label": "Analytic subgroup",
        "y_label": "Predictor set",
        "metric_name": "AUC",
        "row_order": [{"label": "Clinical baseline"}, {"label": "Integrated model"}],
        "column_order": [{"label": "All participants"}, {"label": "APOE4 carriers"}],
        "cells": [
            {"x": "All participants", "y": "Clinical baseline", "value": 0.71},
            {"x": "APOE4 carriers", "y": "Clinical baseline", "value": 0.68},
            {"x": "All participants", "y": "Integrated model", "value": 0.83},
            {"x": "APOE4 carriers", "y": "Integrated model", "value": 0.79},
        ],
    },
}
def _style_context_for(template_id: str) -> dict[str, Any]:
    payload = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.TemporaryDirectory(prefix="mas-gallery-style-") as tmp_dir:
        style_path = Path(tmp_dir) / "publication_style_profile.json"
        style_path.write_text(serialized, encoding="utf-8")
        style_profile = load_publication_style_profile(style_path)
    style_roles = resolve_style_roles(style_profile=style_profile, template_id=template_id)
    output_width, output_height = LIDOCAINEQ_REFERENCE_DEVICE_SIZES.get(template_id, (5.0, 5.0))
    return {
        "style_profile_id": style_profile.style_profile_id,
        "style_profile_ref": "human_reference_default_publication_style_profile",
        "style_profile_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "journal_palette_ref": style_profile.journal_palette_ref,
        "palette": dict(style_profile.palette),
        "semantic_roles": dict(style_profile.semantic_roles),
        "style_roles": style_roles,
        "typography": dict(style_profile.typography),
        "stroke": dict(style_profile.stroke),
        "grid": dict(style_profile.grid),
        "layout_override": {
            "output_width_in": output_width,
            "output_height_in": output_height,
            "show_figure_title": False,
        },
        "readability_override": {},
    }


def _generic_r_gallery_payload(record: TemplateRecord) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_data_digest": "gallery-synthetic-preview",
        "display_id": record.template_id,
        "template_id": record.template_id,
        "title": record.display_name,
        "caption": "Synthetic gallery preview payload for local visual inspection only.",
        "x_label": "X axis",
        "y_label": "Y axis",
        "series": [
            {
                "label": "Model",
                "x": [0, 0.05, 0.14, 0.28, 0.48, 0.72, 1],
                "y": [0, 0.36, 0.58, 0.74, 0.86, 0.95, 1],
                "panel_label": "A",
                "panel_id": "A",
            },
            {
                "label": "Comparator",
                "x": [0, 0.10, 0.25, 0.45, 0.66, 0.84, 1],
                "y": [0, 0.30, 0.49, 0.66, 0.79, 0.90, 1],
                "panel_label": "A",
                "panel_id": "A",
            },
        ],
        "decision_series": [
            {
                "label": "Model",
                "x": [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60],
                "y": [0.22, 0.20, 0.17, 0.13, 0.09, 0.05, 0.02],
                "panel_label": "A",
            },
            {
                "label": "Treat all",
                "x": [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60],
                "y": [0.18, 0.15, 0.10, 0.05, 0.00, -0.05, -0.10],
                "panel_label": "A",
            },
        ],
        "bars": [
            {"label": "Low", "value": 0.18, "panel_label": "B"},
            {"label": "Intermediate", "value": 0.36, "panel_label": "B"},
            {"label": "High", "value": 0.62, "panel_label": "B"},
        ],
        "points": [
            {"x": -1.2, "y": 0.8, "group": "Group A"},
            {"x": -0.8, "y": 0.5, "group": "Group A"},
            {"x": 0.9, "y": -0.4, "group": "Group B"},
            {"x": 1.3, "y": -0.7, "group": "Group B"},
        ],
        "rows": [
            {"label": "Feature A", "estimate": 1.4, "lower": 1.1, "upper": 1.8, "value": 0.42},
            {"label": "Feature B", "estimate": 0.8, "lower": 0.6, "upper": 1.0, "value": 0.25},
            {"label": "Feature C", "estimate": 1.2, "lower": 0.9, "upper": 1.6, "value": 0.31},
        ],
        "row_order": [{"label": "Feature A"}, {"label": "Feature B"}, {"label": "Feature C"}],
        "column_order": [{"label": "Group A"}, {"label": "Group B"}],
        "cells": [
            {"x": "Group A", "y": "Feature A", "value": 0.72},
            {"x": "Group B", "y": "Feature A", "value": -0.24},
            {"x": "Group A", "y": "Feature B", "value": -0.11},
            {"x": "Group B", "y": "Feature B", "value": 0.58},
            {"x": "Group A", "y": "Feature C", "value": 0.33},
            {"x": "Group B", "y": "Feature C", "value": -0.45},
        ],
        "reference_line": {"label": "Reference", "x": [0, 1], "y": [0, 1]},
        "reference_value": 1.0,
    }


def _apply_reference_device_sizes(payloads: dict[str, dict[str, Any]]) -> None:
    for template_id, (width, height) in LIDOCAINEQ_REFERENCE_DEVICE_SIZES.items():
        payload = payloads.get(template_id)
        if not isinstance(payload, dict):
            continue
        render_context = payload.setdefault("render_context", {})
        if not isinstance(render_context, dict):
            render_context = {}
            payload["render_context"] = render_context
        layout_override = render_context.setdefault("layout_override", {})
        if not isinstance(layout_override, dict):
            layout_override = {}
            render_context["layout_override"] = layout_override
        layout_override.setdefault("output_width_in", width)
        layout_override.setdefault("output_height_in", height)


def _load_seed_r_payloads(records: list[TemplateRecord]) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {
        key: json.loads(json.dumps(value))
        for key, value in MANUAL_GALLERY_DISPLAY_PAYLOADS.items()
    }
    payloads.update({
        key: json.loads(json.dumps(value))
        for key, value in CORE_R_DISPLAY_PAYLOADS.items()
    })
    payloads.update({
        key: json.loads(json.dumps(value))
        for key, value in GALLERY_R_DISPLAY_PAYLOADS.items()
    })
    payloads.update({
        key: json.loads(json.dumps(value))
        for key, value in PUBLICATION_R_DISPLAY_PAYLOADS.items()
    })
    payloads.update({
        key: json.loads(json.dumps(value))
        for key, value in LIDOCAINEQ_R_DISPLAY_PAYLOADS.items()
    })
    for record in records:
        if record.renderer_family != "r_ggplot2":
            continue
        if record.template_id not in payloads:
            payloads[record.template_id] = _generic_r_gallery_payload(record)
    _apply_reference_device_sizes(payloads)
    return payloads


def _load_r_gallery_payload(template_id: str, seed_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        payload = json.loads(json.dumps(seed_payloads[template_id]))
    except KeyError as exc:
        raise FileNotFoundError(f"missing seed payload for {template_id}") from exc
    payload_context = payload.get("render_context")
    render_context = _style_context_for(template_id)
    if isinstance(payload_context, dict):
        for key, value in payload_context.items():
            if isinstance(value, dict) and isinstance(render_context.get(key), dict):
                render_context[key] = {**render_context[key], **value}
            else:
                render_context[key] = value
    payload["render_context"] = render_context
    return payload
def _load_python_payload_fixtures() -> dict[str, dict[str, Any]]:
    return {
        key: json.loads(json.dumps(value))
        for key, value in MANUAL_GALLERY_DISPLAY_PAYLOADS.items()
    }


def _python_display_payload(record: TemplateRecord, fixture_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        payload = json.loads(json.dumps(fixture_payloads[record.template_id]))
    except KeyError as exc:
        raise RuntimeError(f"no gallery payload fixture for current python template `{record.template_id}`") from exc
    payload.setdefault("display_id", record.template_id)
    if record.kind == "evidence_figure":
        payload["template_id"] = record.full_template_id
    else:
        payload["shell_id"] = record.full_template_id
    _normalize_decision_path_payload(payload)
    return payload


def _normalize_decision_path_payload(payload: dict[str, Any]) -> None:
    groups = payload.get("groups")
    if not isinstance(groups, list):
        return
    baseline_value = payload.get("baseline_value")
    if not isinstance(baseline_value, (int, float)):
        return
    for group in groups:
        if not isinstance(group, dict):
            continue
        running_value = float(baseline_value)
        contributions = group.get("contributions")
        if not isinstance(contributions, list):
            continue
        for contribution in contributions:
            if not isinstance(contribution, dict):
                continue
            shap_value = contribution.get("shap_value")
            if not isinstance(shap_value, (int, float)):
                continue
            contribution.setdefault("start_value", running_value)
            running_value = float(contribution["start_value"]) + float(shap_value)
            contribution.setdefault("end_value", running_value)
