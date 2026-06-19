#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import argparse
import hashlib
import html
import importlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import (
    TemplateRecord,
    ai_adaptation_policy,
    canonical_category_ontology,
    canonical_family_ontology,
    canonical_family_wording,
    canonical_records,
    family_categories,
    figure_family_policy,
    gallery_template_family_ontology,
    read_template_records,
)
from med_autoscience.display_pack_gallery_reference import build_gallery_reference_markdown
from med_autoscience.publication_display_contract import (
    load_publication_style_profile,
    resolve_style_roles,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"
PACK_SRC_ROOT = PACK_ROOT / "src"
TEMPLATE_ROOT = PACK_ROOT / "templates"
EXAMPLES_ROOT = REPO_ROOT / "docs" / "delivery" / "medical-display" / "examples"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "display-pack-gallery"
DOCS_PDF_PATH = EXAMPLES_ROOT / "ggplot2_template_gallery.pdf"
DOCS_REFERENCE_PATH = EXAMPLES_ROOT / "ggplot2_template_reference.md"
ASSET_ROOT = DEFAULT_OUTPUT_ROOT / "ggplot2_template_reference_assets"
PYTHON_CURRENT_ROOT = ASSET_ROOT / "python_current"
PYTHON_BASELINE_ROOT = ASSET_ROOT / "python_baseline"
HTML_PATH = DEFAULT_OUTPUT_ROOT / "ggplot2_template_gallery.html"
PDF_PATH = DEFAULT_OUTPUT_ROOT / "ggplot2_template_gallery.pdf"
REFERENCE_PATH = DEFAULT_OUTPUT_ROOT / "ggplot2_template_reference.md"
MANIFEST_PATH = ASSET_ROOT / "gallery_manifest.json"
NATURE_SKILLS_HEAD = "54eadc65d1c0535e90d792a87ab718d848ccbb7a"

if str(PACK_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_SRC_ROOT))

CATEGORY_ORDER = (
    "Prediction Performance",
    "Clinical Utility",
    "Time-to-Event",
    "Effect Estimate",
    "Generalizability",
    "Data Geometry",
    "Matrix Pattern",
    "Model Explanation",
    "Model Audit",
    "Publication Shells and Tables",
)
LEGACY_PYTHON_BASELINE_EXCLUDED = (
    "celltype_signature_heatmap",
    "model_complexity_audit_panel",
    "time_to_event_decision_curve",
    "time_to_event_discrimination_calibration_panel",
    "time_to_event_risk_group_summary",
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


@dataclass(frozen=True)
class RenderedAsset:
    status: str
    image_ref: str = ""
    preview_image_ref: str = ""
    payload_ref: str = ""
    layout_ref: str = ""
    pdf_ref: str = ""
    svg_ref: str = ""
    reason: str = ""
    image_size_px: tuple[int, int] = (0, 0)
    preview_image_size_px: tuple[int, int] = (0, 0)

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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError:
        return (0, 0)
    with Image.open(path) as image:
        return image.size


def _square_gallery_preview(path: Path) -> tuple[Path, tuple[int, int]]:
    try:
        from PIL import Image
    except ImportError:
        return (path, _image_size(path))
    with Image.open(path) as image:
        width, height = image.size
        if width == height:
            return (path, (width, height))
        side = max(width, height)
        preview_path = path.with_name(f"{path.stem}.gallery.png")
        canvas = Image.new("RGB", (side, side), "white")
        source = image.convert("RGBA")
        paste_position = ((side - width) // 2, (side - height) // 2)
        canvas.paste(source, paste_position, source)
        canvas.save(preview_path, format="PNG")
        return (preview_path, (side, side))


def _relative_ref(path: Path) -> str:
    return str(path.relative_to(HTML_PATH.parent))


def _strip_trailing_whitespace(path: Path) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    stripped = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    if stripped != text:
        path.write_text(stripped, encoding="utf-8")


def _clean_assets() -> None:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    for path in ASSET_ROOT.iterdir():
        if path.name == "gallery_manifest.json":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        elif path.suffix in {".png", ".pdf", ".json", ".svg"}:
            path.unlink()
    PYTHON_CURRENT_ROOT.mkdir(parents=True, exist_ok=True)
    PYTHON_BASELINE_ROOT.mkdir(parents=True, exist_ok=True)


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


def _render_r_template(record: TemplateRecord, seed_payloads: dict[str, dict[str, Any]]) -> RenderedAsset:
    payload = _load_r_gallery_payload(record.template_id, seed_payloads)
    payload_path = ASSET_ROOT / f"{record.template_id}.payload.json"
    output_png = ASSET_ROOT / f"{record.template_id}.png"
    output_pdf = ASSET_ROOT / f"{record.template_id}.pdf"
    output_layout = ASSET_ROOT / f"{record.template_id}.layout.json"
    request_path = ASSET_ROOT / f"{record.template_id}.render_request.json"
    _write_json(payload_path, payload)
    request = {
        "schema_version": 1,
        "execution_mode": record.execution_mode,
        "renderer_family": record.renderer_family,
        "figure_id": record.template_id,
        "template_id": record.full_template_id,
        "short_template_id": record.template_id,
        "display_payload": payload,
        "output_png_path": str(output_png),
        "output_pdf_path": str(output_pdf),
        "layout_sidecar_path": str(output_layout),
    }
    _write_json(request_path, request)
    env = {
        **dict(**__import__("os").environ),
        "MAS_DISPLAY_OUTPUT_WIDTH_IN": "5",
        "MAS_DISPLAY_OUTPUT_HEIGHT_IN": "5",
    }
    result = subprocess.run(
        ["Rscript", "render.R", "--request", str(request_path)],
        cwd=record.template_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    request_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"{record.template_id} render failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    for path in (output_png, output_pdf, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    preview_path, preview_size = _square_gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf),
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
    )


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


def _render_python_template(
    record: TemplateRecord,
    payload: dict[str, Any],
    *,
    output_root: Path,
    suffix: str,
) -> RenderedAsset:
    output_root.mkdir(parents=True, exist_ok=True)
    output_png = output_root / f"{record.template_id}.{suffix}.png"
    output_pdf = output_root / f"{record.template_id}.{suffix}.pdf"
    output_svg = output_root / f"{record.template_id}.{suffix}.svg"
    output_layout = output_root / f"{record.template_id}.{suffix}.layout.json"
    payload_path = output_root / f"{record.template_id}.{suffix}.payload.json"
    render_payload = json.loads(json.dumps(payload))
    render_context = _style_context_for(record.template_id)
    if record.kind == "evidence_figure":
        render_payload["render_context"] = render_context
    _write_json(payload_path, render_payload)
    if record.kind == "evidence_figure":
        from fenggaolab_org_medical_display_core.evidence_figures import render_python_evidence_figure

        try:
            render_python_evidence_figure(
                template_id=record.full_template_id,
                display_payload=render_payload,
                output_png_path=output_png,
                output_pdf_path=output_pdf,
                output_svg_path=output_svg,
                layout_sidecar_path=output_layout,
            )
        except TypeError as exc:
            if "output_svg_path" not in str(exc):
                raise
            render_python_evidence_figure(
                template_id=record.full_template_id,
                display_payload=render_payload,
                output_png_path=output_png,
                output_pdf_path=output_pdf,
                layout_sidecar_path=output_layout,
            )
    elif record.kind == "illustration_shell":
        from fenggaolab_org_medical_display_core.illustration_shells import render_illustration_shell

        render_illustration_shell(
            template_id=record.full_template_id,
            shell_payload=render_payload,
            render_context=render_context,
            output_svg_path=output_svg,
            output_png_path=output_png,
            output_pdf_path=output_pdf,
            output_layout_path=output_layout,
            payload_path=payload_path,
        )
    else:
        raise RuntimeError(f"unsupported python gallery kind `{record.kind}`")
    for path in (output_png, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    _strip_trailing_whitespace(output_svg)
    preview_path, preview_size = _square_gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf) if output_pdf.is_file() else "",
        svg_ref=_relative_ref(output_svg) if output_svg.is_file() else "",
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
    )


def _legacy_python_baseline_payload(
    record: TemplateRecord,
    fixture_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    try:
        return _python_display_payload(record, fixture_payloads)
    except RuntimeError:
        return None


def _render_legacy_python_baseline(record: TemplateRecord, payload: dict[str, Any] | None) -> RenderedAsset:
    if record.template_id in LEGACY_PYTHON_BASELINE_EXCLUDED:
        return RenderedAsset(status="excluded", reason="legacy_python_baseline_failed_previous_render")
    if record.previous_renderer_family != "python" or not record.previous_entrypoint:
        return RenderedAsset(status="not_applicable")
    if payload is None:
        return RenderedAsset(status="not_available", reason="legacy_python_fixture_missing")
    previous_record = TemplateRecord(
        template_id=record.template_id,
        full_template_id=record.full_template_id,
        display_name=record.display_name,
        kind=record.kind,
        audit_family=record.audit_family,
        renderer_family="python",
        execution_mode="python_plugin",
        entrypoint=record.previous_entrypoint,
        previous_renderer_family="",
        previous_entrypoint="",
        paper_proven=record.paper_proven,
        required_exports=record.required_exports,
        template_dir=record.template_dir,
        canonical_family_id=record.canonical_family_id,
        canonical_family_title=record.canonical_family_title,
        canonical_family_category=record.canonical_family_category,
        canonical_template_id=record.canonical_template_id,
        figure_archetype=record.figure_archetype,
        migration_status=record.migration_status,
        default_visible=record.default_visible,
        migrated_alias_template_ids=record.migrated_alias_template_ids,
        migration_reason=record.migration_reason,
    )
    try:
        return _render_python_template(previous_record, payload, output_root=PYTHON_BASELINE_ROOT, suffix="python")
    except Exception as exc:
        return RenderedAsset(status="excluded", reason=f"legacy_python_baseline_render_failed: {type(exc).__name__}: {exc}")


def _html_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-")


def _asset_html(asset: RenderedAsset, *, label: str) -> str:
    if asset.status != "rendered":
        return ""
    display_image_ref = asset.preview_image_ref or asset.image_ref
    links = [f'<a href="{html.escape(asset.payload_ref)}">payload</a>', f'<a href="{html.escape(asset.layout_ref)}">layout</a>']
    if asset.preview_image_ref and asset.preview_image_ref != asset.image_ref:
        links.append(f'<a href="{html.escape(asset.image_ref)}">raw PNG</a>')
    if asset.pdf_ref:
        links.append(f'<a href="{html.escape(asset.pdf_ref)}">PDF</a>')
    if asset.svg_ref:
        links.append(f'<a href="{html.escape(asset.svg_ref)}">SVG</a>')
    return f"""
<div class="figure-pane">
  <div class="pane-label">{html.escape(label)}</div>
  <a class="image-link" href="{html.escape(display_image_ref)}">
    <img src="{html.escape(display_image_ref)}" alt="{html.escape(label)}">
  </a>
  <div class="asset-links">{' · '.join(links)}</div>
</div>"""


def _render_html(
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
) -> str:
    categories = family_categories(records)
    ordered_categories = [item for item in CATEGORY_ORDER if item in categories]
    ordered_categories.extend(sorted(set(categories) - set(ordered_categories)))

    default_style = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD
    palette = default_style["palette"]
    visible_records = canonical_records(records)
    rendered_count = sum(1 for record in visible_records if rendered[record.template_id].status == "rendered")
    baseline_count = sum(
        1
        for record in visible_records
        if baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).status == "rendered"
    )
    meta = (
        f'<span class="pill">style_profile_id: {html.escape(default_style["style_profile_id"])}</span>'
        f'<span class="pill">journal_palette_ref: {html.escape(default_style["journal_palette_ref"])}</span>'
        f'<span class="pill">gallery cards: {len(visible_records)}</span>'
        f'<span class="pill">family policy: canonical metadata only</span>'
        f'<span class="pill">R/ggplot2 canonical: {sum(1 for record in visible_records if record.renderer_family == "r_ggplot2")}</span>'
        f'<span class="pill">Python canonical: {sum(1 for record in visible_records if record.renderer_family == "python")}</span>'
        f'<span class="pill">rendered images: {rendered_count}</span>'
        f'<span class="pill">Python comparisons: {baseline_count}</span>'
    )
    swatches = "".join(
        (
            f'<span class="swatch"><span class="box" style="background:{html.escape(palette[key])}"></span>'
            f'<code>{html.escape(key)}</code></span>'
        )
        for key in ("primary", "secondary", "tertiary", "quaternary", "violet", "neutral", "heatmap_seq_high", "heatmap_high")
        if key in palette
    )
    nav = "\n".join(
        f'<a href="#family-{_html_id(category)}"><span>{html.escape(category)}</span><strong>{len(categories[category])}</strong></a>'
        for category in ordered_categories
    )
    sections: list[str] = []
    for category in ordered_categories:
        cards: list[str] = []
        for record in sorted(categories[category], key=lambda item: (item.kind, item.canonical_family_id)):
            asset = rendered[record.template_id]
            baseline = baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable"))
            tags = "".join(
                f'<span class="tag">{html.escape(tag)}</span>'
                for tag in (
                    record.canonical_family_id,
                    record.kind,
                    record.renderer_family,
                    "canonical",
                )
            )
            family_wording = canonical_family_wording(record)
            panes = _asset_html(asset, label="R / ggplot2" if record.renderer_family == "r_ggplot2" else "Python")
            if baseline.status == "rendered":
                panes += _asset_html(baseline, label="Legacy Python baseline")
            if asset.status != "rendered":
                panes = f'<div class="placeholder"><strong>{html.escape(record.canonical_family_title)}</strong><span>{html.escape(record.kind)} · {html.escape(record.renderer_family)}</span><em>{html.escape(asset.reason or "no renderer output")}</em></div>'
            cards.append(
                f"""
<article class="card" id="template-{html.escape(record.template_id)}">
  <div class="panes{' compare' if baseline.status == 'rendered' else ''}">{panes}</div>
  <div class="card-body">
    <h3>{html.escape(record.canonical_family_title)}</h3>
    <p><code>{html.escape(record.template_id)}</code></p>
    <p>{html.escape(family_wording)}</p>
    <div class="tags">{tags}</div>
  </div>
</article>"""
            )
        sections.append(
            f"""
<section class="section" id="family-{_html_id(category)}">
  <h2>{html.escape(category)} <span>{len(categories[category])}</span></h2>
  <div class="cards">{''.join(cards)}
  </div>
</section>"""
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MAS Display Pack Canonical Gallery</title>
<style>
:root{{--ink:#272727;--muted:#666;--line:#e4e7eb;--bg:#f7f8fa;--card:#fff;}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.42}}
a{{color:#0f4d92;text-decoration:none}}a:hover{{text-decoration:underline}}
header{{padding:22px 30px 16px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}}
h1{{margin:0 0 8px;font-size:25px;letter-spacing:0}}
.sub{{max-width:1080px;color:var(--muted);font-size:14px}}
.meta,.palette{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.pill,.swatch{{border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 10px;font-size:12px;color:#333}}
.swatch{{display:inline-flex;align-items:center;gap:7px}}
.box{{width:16px;height:16px;border-radius:50%;border:1px solid rgba(0,0,0,.14)}}
.layout{{display:grid;grid-template-columns:260px minmax(0,1fr);gap:20px;padding:22px 28px 40px}}
.nav{{position:sticky;top:118px;align-self:start;background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px}}
.nav h2{{font-size:13px;margin:0 0 8px;color:#555}}
.nav a{{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid #eef1f4;font-size:13px;color:#333}}
.nav a:first-of-type{{border-top:0}}
.section{{margin:0 0 28px}}
.section h2{{margin:0 0 12px;font-size:21px}}.section h2 span{{font-size:13px;color:var(--muted);font-weight:500}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;break-inside:avoid}}
.panes{{display:grid;grid-template-columns:1fr;background:#fff;border-bottom:1px solid var(--line)}}
.panes.compare{{grid-template-columns:1fr 1fr}}
.figure-pane{{min-width:0;border-right:1px solid var(--line)}}
.figure-pane:last-child{{border-right:0}}
.pane-label{{font-size:11px;color:#555;padding:7px 9px;border-bottom:1px solid #eef1f4;background:#fbfcfd}}
.image-link{{display:block;background:#fff}}
.image-link img{{display:block;width:100%;aspect-ratio:1/1;object-fit:contain;background:#fff}}
.asset-links{{font-size:11px;color:#555;padding:7px 9px;border-top:1px solid #eef1f4}}
.placeholder{{height:260px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:18px;text-align:center;background:#fff;border-bottom:1px solid var(--line);color:#555}}
.placeholder strong{{color:#333}}.placeholder span,.placeholder em{{font-size:12px}}
.card-body{{padding:11px 12px}}
.card h3{{margin:0 0 5px;font-size:15px;line-height:1.28}}
.card p{{margin:5px 0;font-size:12px;color:#555}}
.tags{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}
.tag{{font-size:11px;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:#fbfcfd;color:#555}}
@media(max-width:900px){{header{{position:static}}.layout{{display:block;padding:16px}}.nav{{position:static;margin-bottom:18px}}.cards{{grid-template-columns:1fr}}.panes.compare{{grid-template-columns:1fr}}.figure-pane{{border-right:0;border-bottom:1px solid var(--line)}}}}
@media print{{@page{{size:A4;margin:10mm}}header{{position:static}}.layout{{display:block;padding:0}}.nav{{display:none}}.cards{{grid-template-columns:repeat(2,1fr);gap:10px}}body{{background:#fff}}.card{{break-inside:avoid}}}}
</style>
</head>
<body>
<header>
  <h1>MAS Display Pack Canonical Gallery</h1>
  <div class="sub">默认用户面只展示 canonical 图型家族；旧模板 ID 已迁移为 aliases，完整迁移索引只保留在 manifest 中。</div>
  <div class="meta">{meta}</div>
  <div class="palette">{swatches}</div>
</header>
<div class="layout">
<nav class="nav"><h2>索引</h2>{nav}</nav>
<main>{''.join(sections)}</main>
</div>
</body>
</html>
"""


def _write_reference(
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
    *,
    reference_path: Path,
) -> None:
    default_style = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD
    visible_records = canonical_records(records)
    categories = Counter(record.canonical_family_category for record in visible_records)
    rendered_count = sum(1 for record in visible_records if rendered[record.template_id].status == "rendered")
    baseline_count = sum(
        1
        for record in visible_records
        if baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).status == "rendered"
    )
    category_lines = "\n".join(
        f"| {category} | {categories[category]} |"
        for category in CATEGORY_ORDER
        if category in categories
    )
    excluded = ", ".join(f"`{item}`" for item in LEGACY_PYTHON_BASELINE_EXCLUDED)
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_text(
        build_gallery_reference_markdown(
            category_lines=category_lines,
            default_style=default_style,
            renderer_inventory=Counter(record.renderer_family for record in visible_records),
            rendered_count=rendered_count,
            baseline_count=baseline_count,
            excluded_python_comparisons=excluded,
            canonical_gallery_family_count=len(visible_records),
            nature_skills_head=NATURE_SKILLS_HEAD,
        ),
        encoding="utf-8",
    )


def _export_pdf() -> None:
    chrome_candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    )
    chrome = next((str(path) for path in chrome_candidates if path.exists()), None)
    if chrome is None:
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome is None:
        raise RuntimeError("Chrome/Chromium is required to export the gallery PDF")
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={PDF_PATH}",
            f"file://{HTML_PATH}",
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )


def _configure_output_paths(output_root: Path) -> None:
    global ASSET_ROOT
    global PYTHON_CURRENT_ROOT
    global PYTHON_BASELINE_ROOT
    global HTML_PATH
    global PDF_PATH
    global REFERENCE_PATH
    global MANIFEST_PATH

    resolved = output_root.expanduser()
    if not resolved.is_absolute():
        resolved = REPO_ROOT / resolved
    resolved = resolved.resolve()
    ASSET_ROOT = resolved / "ggplot2_template_reference_assets"
    PYTHON_CURRENT_ROOT = ASSET_ROOT / "python_current"
    PYTHON_BASELINE_ROOT = ASSET_ROOT / "python_baseline"
    HTML_PATH = resolved / "ggplot2_template_gallery.html"
    PDF_PATH = resolved / "ggplot2_template_gallery.pdf"
    REFERENCE_PATH = resolved / "ggplot2_template_reference.md"
    MANIFEST_PATH = ASSET_ROOT / "gallery_manifest.json"


def _copy_docs_gallery() -> None:
    DOCS_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PDF_PATH, DOCS_PDF_PATH)
    shutil.copy2(REFERENCE_PATH, DOCS_REFERENCE_PATH)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local MAS display-pack gallery.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Ignored local gallery output root. Defaults to outputs/display-pack-gallery.",
    )
    parser.add_argument(
        "--publish-docs",
        action="store_true",
        help="Copy only ggplot2_template_gallery.pdf and ggplot2_template_reference.md into docs.",
    )
    return parser.parse_args(argv)


def _build_manifest(
    *,
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
    publish_docs: bool,
) -> dict[str, Any]:
    visible_records = canonical_records(records)
    canonical_rendered_count = sum(
        1
        for record in visible_records
        if rendered[record.template_id].status == "rendered"
    )
    internal_rendered_count = sum(
        1
        for asset in rendered.values()
        if asset.status == "rendered"
    )
    baseline_rendered_count = sum(1 for asset in baseline_rendered.values() if asset.status == "rendered")
    return {
        "schema_version": 5,
        "status": "rendered",
        "html_path": str(HTML_PATH),
        "pdf_path": str(PDF_PATH),
        "docs_pdf_path": str(DOCS_PDF_PATH) if publish_docs else "",
        "docs_reference_path": str(DOCS_REFERENCE_PATH) if publish_docs else "",
        "template_count": len(visible_records),
        "active_template_count": len(visible_records),
        "migration_inventory_template_count": len(records),
        "canonical_family_count": len(canonical_family_ontology()),
        "gallery_template_family_count": len({record.canonical_family_id for record in visible_records}),
        "canonical_template_count": sum(1 for record in records if record.migration_status == "canonical"),
        "default_visible_template_count": len(visible_records),
        "legacy_alias_template_count": sum(1 for record in records if record.migration_status == "migrated_alias"),
        "rendered_image_template_count": canonical_rendered_count,
        "internal_rendered_image_template_count": internal_rendered_count,
        "legacy_python_baseline_rendered_count": baseline_rendered_count,
        "renderer_family_counts": dict(sorted(Counter(record.renderer_family for record in records).items())),
        "style_profile_id": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["style_profile_id"],
        "journal_palette_ref": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["journal_palette_ref"],
        "preview_device": {"width_in": 5.0, "height_in": 5.0},
        "nature_skills_observed_head": NATURE_SKILLS_HEAD,
        "excluded_legacy_python_baselines": list(LEGACY_PYTHON_BASELINE_EXCLUDED),
        "categories": dict(Counter(record.canonical_family_category for record in visible_records)),
        "figure_family_policy": figure_family_policy(),
        "ai_adaptation_policy": ai_adaptation_policy(),
        "canonical_category_ontology": canonical_category_ontology(),
        "canonical_family_ontology": canonical_family_ontology(),
        "gallery_template_family_ontology": gallery_template_family_ontology(records),
        "template_surface_policy": {
            "gallery_default_surface": "canonical_families_only",
            "active_inventory_is_canonical_only": True,
            "migration_inventory_preserved_in_manifest": True,
            "migrated_alias_templates_hidden_from_default_cards": True,
            "explicit_alias_requests_migrate_to_canonical_template": True,
        },
        "templates": [
            {
                "template_id": record.template_id,
                "display_name": record.display_name,
                "audit_family": record.audit_family,
                "canonical_family_id": record.canonical_family_id,
                "canonical_family_title": record.canonical_family_title,
                "canonical_family_category": record.canonical_family_category,
                "canonical_template_id": record.canonical_template_id,
                "figure_archetype": record.figure_archetype,
                "canonical_family_wording": canonical_family_wording(record),
                "migration_status": record.migration_status,
                "default_visible": record.default_visible,
                "migrated_alias_template_ids": list(record.migrated_alias_template_ids),
                "migration_reason": record.migration_reason,
                "kind": record.kind,
                "renderer_family": record.renderer_family,
                "execution_mode": record.execution_mode,
                "paper_proven": record.paper_proven,
                "render_status": rendered[record.template_id].status,
                "render_reason": rendered[record.template_id].reason,
                "image_size_px": list(rendered[record.template_id].image_size_px),
                "image_ref": rendered[record.template_id].image_ref,
                "preview_image_size_px": list(rendered[record.template_id].preview_image_size_px),
                "preview_image_ref": rendered[record.template_id].preview_image_ref,
                "payload_ref": rendered[record.template_id].payload_ref,
                "layout_ref": rendered[record.template_id].layout_ref,
                "pdf_ref": rendered[record.template_id].pdf_ref,
                "svg_ref": rendered[record.template_id].svg_ref,
                "legacy_python_baseline": {
                    "status": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).status,
                    "reason": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).reason,
                    "image_ref": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).image_ref,
                    "preview_image_ref": baseline_rendered.get(
                        record.template_id, RenderedAsset(status="not_applicable")
                    ).preview_image_ref,
                    "payload_ref": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).payload_ref,
                    "layout_ref": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).layout_ref,
                    "pdf_ref": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).pdf_ref,
                    "svg_ref": baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).svg_ref,
                    "image_size_px": list(
                        baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).image_size_px
                    ),
                    "preview_image_size_px": list(
                        baseline_rendered.get(
                            record.template_id, RenderedAsset(status="not_applicable")
                        ).preview_image_size_px
                    ),
                },
            }
            for record in records
            if record.default_visible
        ],
        "migration_index": [
            {
                "template_id": record.template_id,
                "canonical_family_id": record.canonical_family_id,
                "canonical_template_id": record.canonical_template_id,
                "migration_status": record.migration_status,
                "default_visible": record.default_visible,
                "migration_reason": record.migration_reason,
            }
            for record in records
        ],
    }


def main() -> int:
    args = _parse_args(sys.argv[1:])
    _configure_output_paths(args.output_root)
    if shutil.which("Rscript") is None:
        raise RuntimeError("Rscript is required to rebuild the gallery")
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    seed_r_payloads = _load_seed_r_payloads(records)
    _clean_assets()
    fixture_payloads = _load_python_payload_fixtures()
    rendered: dict[str, RenderedAsset] = {}
    baseline_rendered: dict[str, RenderedAsset] = {}
    for record in records:
        if record.renderer_family == "r_ggplot2":
            rendered[record.template_id] = _render_r_template(record, seed_r_payloads)
            baseline_payload = _legacy_python_baseline_payload(record, fixture_payloads)
            baseline_rendered[record.template_id] = _render_legacy_python_baseline(record, baseline_payload)
        elif record.renderer_family == "python":
            try:
                payload = _python_display_payload(record, fixture_payloads)
                rendered[record.template_id] = _render_python_template(
                    record,
                    payload,
                    output_root=PYTHON_CURRENT_ROOT,
                    suffix="python",
                )
            except Exception as exc:
                rendered[record.template_id] = RenderedAsset(
                    status="not_rendered",
                    reason=f"{type(exc).__name__}: {exc}",
                )
        else:
            rendered[record.template_id] = RenderedAsset(status="not_visual", reason="table_shell_or_non_visual_template")

    HTML_PATH.write_text(_render_html(records, rendered, baseline_rendered), encoding="utf-8")
    _strip_trailing_whitespace(HTML_PATH)
    _write_reference(records, rendered, baseline_rendered, reference_path=REFERENCE_PATH)
    _strip_trailing_whitespace(REFERENCE_PATH)
    visible_records = canonical_records(records)
    manifest = _build_manifest(
        records=records,
        rendered=rendered,
        baseline_rendered=baseline_rendered,
        publish_docs=args.publish_docs,
    )
    _write_json(MANIFEST_PATH, manifest)
    _export_pdf()
    if args.publish_docs:
        _copy_docs_gallery()
    print(
        json.dumps(
            {
                "status": "rendered",
                "active_templates": len(visible_records),
                "migration_inventory_templates": len(records),
                "rendered_image_templates": manifest["rendered_image_template_count"],
                "internal_rendered_image_templates": manifest["internal_rendered_image_template_count"],
                "canonical_python_comparisons": sum(
                    1
                    for record in visible_records
                    if baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).status == "rendered"
                ),
                "internal_python_comparisons": manifest["legacy_python_baseline_rendered_count"],
                "html_path": str(HTML_PATH),
                "pdf_path": str(PDF_PATH),
                "docs_pdf_path": str(DOCS_PDF_PATH) if args.publish_docs else "",
                "docs_reference_path": str(DOCS_REFERENCE_PATH) if args.publish_docs else "",
                "manifest_path": str(MANIFEST_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
