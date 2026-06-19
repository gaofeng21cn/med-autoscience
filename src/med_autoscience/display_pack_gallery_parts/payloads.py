from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import importlib
import inspect
import json
import tempfile

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.display_pack_gallery_parts.taxonomy import LEGACY_PYTHON_BASELINE_EXCLUDED
from med_autoscience.publication_display_contract import (
    load_publication_style_profile,
    resolve_style_roles,
)

PYTHON_PAYLOAD_FIXTURE_MODULES = (
    "tests.display_surface_materialization_cases.genomic_payload_fixtures",
    "tests.display_surface_materialization_cases.illustration_payload_fixtures",
    "tests.display_surface_materialization_cases.atlas_payload_fixtures",
    "tests.display_surface_materialization_cases.response_payload_fixtures",
    "tests.display_surface_materialization_cases.transportability_payload_fixtures",
)
ILLUSTRATION_PAYLOAD_BUILDERS = {
    "workflow_fact_sheet_panel": "_make_workflow_fact_sheet_panel_payload",
    "design_evidence_composite_shell": "_make_design_evidence_composite_shell_payload",
    "baseline_missingness_qc_panel": "_make_baseline_missingness_qc_panel_payload",
    "center_coverage_batch_transportability_panel": "_make_center_coverage_batch_transportability_panel_payload",
    "transportability_recalibration_governance_panel": "_make_transportability_recalibration_governance_panel_payload",
}
MANUAL_PYTHON_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "cohort_flow_figure": {
        "schema_version": 1,
        "shell_id": "cohort_flow_figure",
        "display_id": "Figure1",
        "title": "Study cohort flow",
        "caption": "Synthetic cohort flow preview for the Display Pack Gallery.",
        "steps": [
            {"step_id": "screened", "label": "Patients screened", "n": 186, "detail": "Consecutive eligible records"},
            {"step_id": "eligible", "label": "Eligible after criteria review", "n": 142, "detail": "Complete baseline variables"},
            {"step_id": "included", "label": "Included in analysis", "n": 128, "detail": "Primary analytic cohort"},
        ],
        "exclusions": [
            {
                "exclusion_id": "missing_followup",
                "from_step_id": "eligible",
                "label": "Missing follow-up",
                "detail": "Excluded before model evaluation",
                "n": 14,
            }
        ],
        "endpoint_inventory": [
            {"endpoint_id": "primary", "label": "Primary endpoint", "detail": "Cardiovascular event", "n": 31},
            {"endpoint_id": "secondary", "label": "Secondary endpoint", "detail": "Hospitalization", "n": 44},
        ],
        "design_panels": [
            {
                "panel_id": "split",
                "layout_role": "wide_top",
                "style_role": "primary",
                "title": "Analysis split",
                "lines": [
                    {"label": "Training", "detail": "70% temporal derivation"},
                    {"label": "Validation", "detail": "30% locked holdout"},
                ],
            },
            {
                "panel_id": "review",
                "layout_role": "wide_bottom",
                "style_role": "context",
                "title": "Review boundary",
                "lines": [
                    {"label": "Outcome adjudication", "detail": "Source ledger required"},
                    {"label": "Publication surface", "detail": "Figure catalog controlled"},
                ],
            },
        ],
        "comparison_summary": {"title": "Gallery note", "body": "Synthetic counts are for renderer preview only."},
    },
    "submission_graphical_abstract": {
        "schema_version": 1,
        "shell_id": "submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "paper_role": "submission_companion",
        "title": "Submission companion overview",
        "caption": "Synthetic graphical abstract preview for the Display Pack Gallery.",
        "panels": [
            {
                "panel_id": "cohort_split",
                "panel_label": "A",
                "title": "Cohort and split",
                "subtitle": "Locked analysis cohort",
                "rows": [{"cards": [{"card_id": "analytic", "title": "Analytic cohort", "value": "15,787", "detail": "eligible patients", "accent_role": "primary"}]}],
            },
            {
                "panel_id": "primary_endpoint",
                "panel_label": "B",
                "title": "Primary endpoint",
                "subtitle": "Cardiovascular mortality",
                "rows": [{"cards": [{"card_id": "c_index", "title": "Validation C-index", "value": "0.857", "detail": "locked split", "accent_role": "secondary"}]}],
            },
        ],
        "footer_pills": [
            {"pill_id": "p1", "panel_id": "cohort_split", "label": "Internal validation", "style_role": "primary"},
            {"pill_id": "p2", "panel_id": "primary_endpoint", "label": "Supportive endpoint", "style_role": "secondary"},
        ],
    },
    "multicenter_generalizability_overview": {
        "display_id": "Figure17",
        "template_id": "multicenter_generalizability_overview",
        "title": "Multicenter generalizability overview",
        "caption": "Center-level event support with coverage context under the frozen split.",
        "center_event_y_label": "5-year CVD events",
        "coverage_y_label": "Patient count",
        "center_event_counts": [
            {"center_label": "Center 1", "split_bucket": "train", "event_count": 7},
            {"center_label": "Center 2", "split_bucket": "validation", "event_count": 5},
            {"center_label": "Center 3", "split_bucket": "train", "event_count": 3},
        ],
        "coverage_panels": [
            {"panel_id": "region", "title": "Region coverage", "layout_role": "wide_left", "bars": [{"label": "Central", "count": 72}, {"label": "East", "count": 54}, {"label": "South", "count": 43}]},
            {"panel_id": "north_south", "title": "North vs South", "layout_role": "top_right", "bars": [{"label": "North", "count": 84}, {"label": "South", "count": 114}]},
            {"panel_id": "urban_rural", "title": "Urban/rural", "layout_role": "bottom_right", "bars": [{"label": "Urban", "count": 101}, {"label": "Rural", "count": 63}, {"label": "Missing", "count": 34}]},
        ],
    },
    "phenotype_gap_structure_figure": {
        "display_id": "Figure2",
        "template_id": "phenotype_gap_structure_figure",
        "title": "Phenotype composition and treatment-gap profiles across the index cohort.",
        "rows": [
            {"phenotype_label": "Phenotype A", "share_of_index_patients": 0.42, "severe_glycemia_low_intensity_gap_rate": 0.18, "uncontrolled_glycemia_no_drug_gap_rate": 0.24, "hypertension_no_antihypertensive_gap_rate": 0.16, "dyslipidemia_no_lipid_lowering_gap_rate": 0.21},
            {"phenotype_label": "Phenotype B", "share_of_index_patients": 0.58, "severe_glycemia_low_intensity_gap_rate": 0.07, "uncontrolled_glycemia_no_drug_gap_rate": 0.11, "hypertension_no_antihypertensive_gap_rate": None, "dyslipidemia_no_lipid_lowering_gap_rate": 0.14},
        ],
    },
    "site_held_out_stability_figure": {
        "display_id": "Figure3",
        "template_id": "site_held_out_stability_figure",
        "title": "Transition stability and site-held-out support for phenotype assignment.",
        "transition_rows": [
            {"source_phenotype_label": "Phenotype A", "target_phenotype_label": "Phenotype A", "patient_count": 84, "share_of_transition_patients": 0.62},
            {"source_phenotype_label": "Phenotype A", "target_phenotype_label": "Phenotype B", "patient_count": 51, "share_of_transition_patients": 0.38},
            {"source_phenotype_label": "Phenotype B", "target_phenotype_label": "Phenotype B", "patient_count": 93, "share_of_transition_patients": 0.67},
            {"source_phenotype_label": "Phenotype B", "target_phenotype_label": "Phenotype A", "patient_count": 45, "share_of_transition_patients": 0.33},
        ],
        "site_fold_rows": [
            {"fold_id": "fold_1", "index_patients": 120, "share_of_index_patients": 0.34},
            {"fold_id": "fold_2", "index_patients": 111, "share_of_index_patients": 0.31},
            {"fold_id": "pooled_small_site", "index_patients": 121, "share_of_index_patients": 0.35},
        ],
        "eligible_site_count": 6,
        "visit_coverage": 0.83,
    },
    "treatment_gap_alignment_figure": {
        "display_id": "Figure4",
        "template_id": "treatment_gap_alignment_figure",
        "title": "Guideline-linked treatment gaps aligned to phenotypes.",
        "rows": [
            {"phenotype_label": "Phenotype A", "index_patients": 320, "severe_glycemia_low_intensity_gap_patients": 44, "uncontrolled_glycemia_no_drug_gap_patients": 61, "hypertension_no_antihypertensive_gap_patients": 37, "dyslipidemia_no_lipid_lowering_gap_patients": 72},
            {"phenotype_label": "Phenotype B", "index_patients": 280, "severe_glycemia_low_intensity_gap_patients": 29, "uncontrolled_glycemia_no_drug_gap_patients": 41, "hypertension_no_antihypertensive_gap_patients": 18, "dyslipidemia_no_lipid_lowering_gap_patients": 56},
        ],
    },
    "treatment_shift_alignment_figure": {
        "display_id": "Figure5",
        "template_id": "treatment_shift_alignment_figure",
        "title": "Treatment shift alignment summary",
        "caption": "Synthetic descriptive display preview.",
        "panels": [
            {
                "panel_id": "phenotype_shift",
                "title": "Treatment shift by phenotype",
                "x_label": "Share of patients",
                "y_label": "Phenotype",
                "marks": [
                    {"label": "Phenotype A", "value": 0.48, "comparison_value": 0.34, "annotation": "recommended"},
                    {"label": "Phenotype B", "value": 0.36, "comparison_value": 0.41},
                    {"label": "Phenotype C", "value": 0.16, "comparison_value": 0.25},
                ],
            }
        ],
    },
    "practical_factor_dot_figure": {
        "display_id": "Figure6",
        "template_id": "practical_factor_dot_figure",
        "title": "Practical factor dot summary",
        "caption": "Synthetic descriptive display preview.",
        "panels": [
            {
                "panel_id": "factor_effects",
                "title": "Practical factors",
                "x_label": "Standardized effect",
                "y_label": "Factor",
                "marks": [
                    {"label": "HbA1c above target", "value": 0.42, "annotation": "n=318"},
                    {"label": "Albuminuria", "value": 0.31, "annotation": "n=204"},
                    {"label": "Systolic BP above target", "value": 0.27, "annotation": "n=286"},
                ],
            }
        ],
    },
    "preferred_class_sensitivity_figure": {
        "display_id": "Figure7",
        "template_id": "preferred_class_sensitivity_figure",
        "title": "Preferred class sensitivity analysis",
        "caption": "Synthetic descriptive display preview.",
        "panels": [
            {
                "panel_id": "class_share",
                "title": "Preferred class share",
                "x_label": "Share",
                "y_label": "Class",
                "marks": [
                    {"label": "GLP-1RA preferred", "value": 0.42, "comparison_value": 0.35},
                    {"label": "SGLT2i preferred", "value": 0.36, "comparison_value": 0.29},
                    {"label": "Insulin intensification", "value": 0.22, "comparison_value": 0.16},
                ],
            }
        ],
    },
    "binary_calibration_decision_curve_panel": {
        "display_id": "Figure3",
        "template_id": "binary_calibration_decision_curve_panel",
        "title": "Calibration and decision curve comparison",
        "caption": "Synthetic calibration and decision curve preview for legacy Python comparison.",
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
        "caption": "Synthetic monotonic risk layering preview for legacy Python comparison.",
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
        "caption": "Synthetic feature-level SHAP distribution preview for legacy Python comparison.",
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
    "shap_grouped_local_support_domain_panel": {
        "display_id": "Figure50",
        "template_id": "shap_grouped_local_support_domain_panel",
        "title": "Grouped local explanation with support-domain follow-on.",
        "caption": "Synthetic grouped local explanation preview.",
        "grouped_local_x_label": "Local SHAP contribution",
        "support_y_label": "Predicted response probability",
        "support_legend_title": "Support domain",
        "local_panels": [
            {"panel_id": "high_risk", "panel_label": "A", "title": "High-risk phenotype", "group_label": "Phenotype 1", "baseline_value": 0.22, "predicted_value": 0.34, "contributions": [{"rank": 1, "feature": "Age", "shap_value": 0.14}, {"rank": 2, "feature": "Albumin", "shap_value": -0.05}, {"rank": 3, "feature": "Tumor size", "shap_value": 0.03}]},
            {"panel_id": "low_risk", "panel_label": "B", "title": "Lower-risk phenotype", "group_label": "Phenotype 2", "baseline_value": 0.18, "predicted_value": 0.12, "contributions": [{"rank": 1, "feature": "Age", "shap_value": -0.07}, {"rank": 2, "feature": "Albumin", "shap_value": 0.02}, {"rank": 3, "feature": "Tumor size", "shap_value": -0.01}]},
        ],
        "support_panels": [
            {
                "panel_id": "age_support",
                "panel_label": "C",
                "title": "Age response support",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "response_curve": {"x": [40.0, 50.0, 60.0, 70.0, 80.0], "y": [0.18, 0.22, 0.29, 0.35, 0.41]},
                "support_segments": [
                    {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 40.0, "domain_end": 50.0},
                    {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 50.0, "domain_end": 62.0},
                    {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 62.0, "domain_end": 72.0},
                    {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 72.0, "domain_end": 80.0},
                ],
            },
            {
                "panel_id": "albumin_support",
                "panel_label": "D",
                "title": "Albumin response support",
                "x_label": "Albumin (g/dL)",
                "feature": "Albumin",
                "reference_value": 3.8,
                "reference_label": "Median albumin",
                "response_curve": {"x": [2.8, 3.4, 4.0, 4.6], "y": [0.39, 0.31, 0.25, 0.20]},
                "support_segments": [
                    {"segment_id": "albumin_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 2.8, "domain_end": 3.4},
                    {"segment_id": "albumin_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 3.4, "domain_end": 4.2},
                    {"segment_id": "albumin_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 4.2, "domain_end": 4.6},
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
        "title": "Binary confusion matrix on the held-out cohort",
        "caption": "Row-normalized confusion matrix summarizing false-positive and false-negative error modes.",
        "x_label": "Predicted class",
        "y_label": "Observed class",
        "metric_name": "Observed proportion",
        "normalization": "row_fraction",
        "row_order": [{"label": "Observed negative"}, {"label": "Observed positive"}],
        "column_order": [{"label": "Predicted negative"}, {"label": "Predicted positive"}],
        "cells": [
            {"x": "Predicted negative", "y": "Observed negative", "value": 0.88},
            {"x": "Predicted positive", "y": "Observed negative", "value": 0.12},
            {"x": "Predicted negative", "y": "Observed positive", "value": 0.19},
            {"x": "Predicted positive", "y": "Observed positive", "value": 0.81},
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
            "output_width_in": 5.0,
            "output_height_in": 5.0,
            "show_figure_title": False,
        },
        "readability_override": {},
    }
def _workspace_fixture_display_payloads() -> dict[str, dict[str, Any]]:
    from tests.display_surface_materialization_cases.workspace_surface_fixtures import (
        build_display_surface_workspace,
    )

    with tempfile.TemporaryDirectory(prefix="mas-gallery-workspace-") as tmp_dir:
        paper_root = build_display_surface_workspace(
            Path(tmp_dir),
            include_extended_evidence=True,
        )
        payloads: dict[str, dict[str, Any]] = {}
        for path in paper_root.glob("*_inputs.json"):
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(envelope, dict):
                continue
            for display in envelope.get("displays", []):
                if not isinstance(display, dict):
                    continue
                template_id = str(display.get("template_id") or "").strip()
                if "::" in template_id:
                    template_id = template_id.split("::")[-1]
                if template_id:
                    payloads.setdefault(template_id, display)
        return payloads


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


def _load_seed_r_payloads(records: list[TemplateRecord]) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {
        key: json.loads(json.dumps(value))
        for key, value in MANUAL_PYTHON_DISPLAY_PAYLOADS.items()
    }
    payloads.update({
        key: json.loads(json.dumps(value))
        for key, value in GALLERY_R_DISPLAY_PAYLOADS.items()
    })
    payloads.update(
        {
            key: json.loads(json.dumps(value))
            for key, value in _workspace_fixture_display_payloads().items()
            if key not in payloads
        }
    )
    for record in records:
        if record.renderer_family != "r_ggplot2":
            continue
        if record.template_id not in payloads:
            payloads[record.template_id] = _generic_r_gallery_payload(record)
    return payloads


def _load_r_gallery_payload(template_id: str, seed_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        payload = json.loads(json.dumps(seed_payloads[template_id]))
    except KeyError as exc:
        raise FileNotFoundError(f"missing seed payload for {template_id}") from exc
    payload["render_context"] = _style_context_for(template_id)
    return payload
def _load_python_payload_fixtures() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for module_name in PYTHON_PAYLOAD_FIXTURE_MODULES:
        module = importlib.import_module(module_name)
        for name, value in vars(module).items():
            if not callable(value) or not name.startswith("_make_"):
                continue
            try:
                signature = inspect.signature(value)
            except (TypeError, ValueError):
                continue
            if any(parameter.default is inspect._empty for parameter in signature.parameters.values()):
                continue
            try:
                payload = value()
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            template_id = str(payload.get("template_id") or payload.get("shell_id") or "").strip()
            if "::" in template_id:
                template_id = template_id.split("::")[-1]
            if template_id:
                payloads.setdefault(template_id, payload)
        for template_id, builder_name in ILLUSTRATION_PAYLOAD_BUILDERS.items():
            builder = getattr(module, builder_name, None)
            if callable(builder):
                try:
                    payload = builder()
                except Exception:
                    continue
                if isinstance(payload, dict):
                    payloads.setdefault(template_id, payload)
    payloads.update(MANUAL_PYTHON_DISPLAY_PAYLOADS)
    return payloads


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
