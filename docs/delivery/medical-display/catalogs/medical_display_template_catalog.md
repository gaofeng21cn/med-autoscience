# Medical Display Template Catalog

Generated from `med_autoscience.display_registry` and `med_autoscience.display_schema_contract`.

Paper-family labels follow the roadmap in [medical_display_family_roadmap.md](./medical_display_family_roadmap.md).

For the stable human-auditable overview, completion counts, and change protocol, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

## Publication Style and Override Governance

- `paper/publication_style_profile.json` is the article-level visual truth source for publication-facing figures.
- `paper/display_overrides.json` is the figure-level structured adjustment surface for manuscript-specific layout and readability decisions.
- Templates preserve a stable lower bound; article-level style and figure-level overrides may refine expression without bypassing the audited renderer path.
- Final manuscript-facing polish is **AI-first above that lower bound**: use the generated image as the truth surface, let visual review identify concrete defects, then harden the audited renderer/QC path instead of paper-local patching.
- Canonical paper-owned packaging surface remains `paper/submission_minimal/`; `manuscript/` is the human-facing mirror, while `artifacts/` is auxiliary evidence only and should not replace that fixed lookup path.
- Canonical rendered assets live under `paper/figures/generated/` and `paper/tables/generated/`; legacy top-level `paper/figures/Figure*.png|pdf|svg` / `paper/tables/Table*.csv|md` mirrors should be removed once they are no longer referenced by the active catalogs.
- `analysis_responsibility` is loaded from the canonical Display Pack catalog: raw analysis inputs may only enter templates marked `computed_in_template`; `validated_summary_required` templates require upstream validated analysis payloads.

## Current Paper-Proven Baseline (001/003)

The current audited inventory is broader than the subset already proven against real papers.

- Paper families: `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event`, `H. Cohort and Study Design Evidence`
- Audit families: `Clinical Utility`, `Time-to-Event`, `Generalizability`, `Publication Shells and Tables`
- Template instances: `fenggaolab.org.medical-display-core::calibration_curve_binary`, `fenggaolab.org.medical-display-core::time_dependent_roc_horizon`, `fenggaolab.org.medical-display-core::risk_layering_monotonic_bars`, `fenggaolab.org.medical-display-core::time_to_event_decision_curve`, `fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel`, `fenggaolab.org.medical-display-core::submission_graphical_abstract`
- Cross-paper golden regression priority: title policy, annotation placement, panel-label/header-band anchoring, grouped-separation readability, landmark/time-slice semantics, graphical-abstract arrow lanes, calibration axis-window fit, and generalizability interval readability

## Template Classes

### Prediction Performance

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::roc_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | ROC Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::pr_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Precision-Recall Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::calibration_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Calibration Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Clinical Utility

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::decision_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Decision Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::time_to_event_decision_curve` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Decision Curve (Time-to-Event Horizon) | `r_ggplot2` | `time_to_event_decision_curve_inputs_v1` | `publication_decision_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::waterfall_response` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Waterfall Response | `r_ggplot2` | `waterfall_response_inputs_v1` | `publication_result_display` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Time-to-Event

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::kaplan_meier_grouped` | `evidence_figure` | `B. Survival and Time-to-Event` | Kaplan-Meier Curve (Grouped) | `r_ggplot2` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::cumulative_incidence_grouped` | `evidence_figure` | `B. Survival and Time-to-Event` | Cumulative Incidence Curve (Grouped) | `r_ggplot2` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::time_dependent_roc_horizon` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Time-Dependent ROC (Horizon) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::time_to_event_multihorizon_calibration_panel` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Multi-Horizon Grouped Calibration Panel (Time-to-Event) | `r_ggplot2` | `time_to_event_multihorizon_calibration_inputs_v1` | `publication_time_to_event_multihorizon_calibration_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::risk_layering_monotonic_bars` | `evidence_figure` | `B. Survival and Time-to-Event` | Monotonic Risk Layering Bars | `r_ggplot2` | `risk_layering_monotonic_inputs_v1` | `publication_risk_layering_bars` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Data Geometry

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::alluvial_transition` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Alluvial Transition | `r_ggplot2` | `alluvial_transition_inputs_v1` | `publication_result_display` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::pca_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | PCA Scatter (Grouped) | `r_ggplot2` | `dimensionality_reduction_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` | `computed_in_template` / `raw_feature_matrix` |
| `fenggaolab.org.medical-display-core::tsne_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | t-SNE Scatter (Grouped) | `r_ggplot2` | `dimensionality_reduction_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` | `computed_in_template` / `raw_feature_matrix` |
| `fenggaolab.org.medical-display-core::umap_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | UMAP Scatter (Grouped) | `r_ggplot2` | `dimensionality_reduction_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` | `computed_in_template` / `raw_feature_matrix` |
| `fenggaolab.org.medical-display-core::omics_volcano_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Omics Volcano Panel | `r_ggplot2` | `omics_volcano_panel_inputs_v1` | `publication_omics_volcano_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Matrix Pattern

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::composition_stacked_bar` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Composition Stacked Bar | `r_ggplot2` | `composition_stacked_bar_inputs_v1` | `publication_result_display` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::heatmap_group_comparison` | `evidence_figure` | `E. Feature Pattern and Matrix` | Heatmap (Group Comparison) | `r_ggplot2` | `heatmap_group_comparison_inputs_v1` | `publication_heatmap` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::confusion_matrix_heatmap_binary` | `evidence_figure` | `A. Predictive Performance and Decision`, `E. Feature Pattern and Matrix` | Binary Confusion Matrix Heatmap | `r_ggplot2` | `confusion_matrix_heatmap_binary_inputs_v1` | `publication_heatmap` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::genomic_alteration_landscape_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Alteration Landscape Panel | `r_ggplot2` | `genomic_alteration_landscape_panel_inputs_v1` | `publication_genomic_alteration_landscape_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::cnv_recurrence_summary_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | CNV Recurrence Summary Panel | `r_ggplot2` | `cnv_recurrence_summary_panel_inputs_v1` | `publication_cnv_recurrence_summary_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::genomic_alteration_consequence_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Alteration Consequence Panel | `r_ggplot2` | `genomic_alteration_consequence_panel_inputs_v1` | `publication_genomic_alteration_consequence_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::pathway_enrichment_dotplot_panel` | `evidence_figure` | `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Pathway Enrichment Dotplot Panel | `r_ggplot2` | `pathway_enrichment_dotplot_panel_inputs_v1` | `publication_pathway_enrichment_dotplot_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::celltype_marker_dotplot_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Cell-Type Marker Dotplot Panel | `r_ggplot2` | `celltype_marker_dotplot_panel_inputs_v1` | `publication_celltype_marker_dotplot_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Effect Estimate

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::forest_effect_main` | `evidence_figure` | `C. Effect Size and Heterogeneity` | Forest Plot (Main Effects) | `r_ggplot2` | `forest_effect_inputs_v1` | `publication_forest_plot` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::coefficient_path_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Coefficient Path Panel | `r_ggplot2` | `coefficient_path_panel_inputs_v1` | `publication_coefficient_path_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::distribution_violin_box` | `evidence_figure` | `A. Predictive Performance and Decision`, `H. Cohort and Study Design Evidence` | Distribution Violin-Box Plot | `r_ggplot2` | `distribution_violin_box_inputs_v1` | `publication_result_display` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::correlation_scatter` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Correlation Scatter | `r_ggplot2` | `correlation_scatter_inputs_v1` | `publication_result_display` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Model Explanation

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::shap_summary_beeswarm` | `evidence_figure` | `F. Model Explanation` | SHAP Summary Beeswarm | `r_ggplot2` | `shap_summary_inputs_v1` | `publication_shap_summary` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::shap_dependence_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Dependence Panel | `r_ggplot2` | `shap_dependence_panel_inputs_v1` | `publication_shap_dependence_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::shap_waterfall_local_explanation_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Waterfall Local Explanation Panel | `r_ggplot2` | `shap_waterfall_local_explanation_panel_inputs_v1` | `publication_shap_waterfall_local_explanation_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Model Audit

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::radar_profile` | `evidence_figure` | `H. Cohort and Study Design Evidence`, `G. Bioinformatics and Omics Evidence` | Radar Profile | `r_ggplot2` | `radar_profile_inputs_v1` | `publication_result_display` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |
| `fenggaolab.org.medical-display-core::model_complexity_audit_panel` | `evidence_figure` | `F. Model Explanation`, `H. Cohort and Study Design Evidence` | Model Complexity Audit Panel | `r_ggplot2` | `model_complexity_audit_panel_inputs_v1` | `publication_model_complexity_audit` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Generalizability

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Generalizability and Subgroup Composite Panel | `r_ggplot2` | `generalizability_subgroup_composite_inputs_v1` | `publication_generalizability_subgroup_composite_panel` | `png`, `pdf` | `validated_summary_required` / `validated_display_payload` |

### Publication Shells and Tables

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::cohort_flow_figure` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Cohort Flow Figure | `r_ggplot2` | `cohort_flow_shell_inputs_v1` | `publication_illustration_flow` | `png`, `pdf` | `validated_summary_required` / `validated_reporting_flow_payload` |
| `fenggaolab.org.medical-display-core::submission_graphical_abstract` | `illustration_shell` | `A. Predictive Performance and Decision`, `H. Cohort and Study Design Evidence` | Submission Graphical Abstract | `python` | `submission_graphical_abstract_inputs_v1` | `submission_graphical_abstract` | `png`, `svg` | `illustration_shell` / `not_statistical_evidence` |
| `fenggaolab.org.medical-display-core::table1_baseline_characteristics` | `table_shell` | `H. Cohort and Study Design Evidence` | Table 1 Baseline Characteristics | `n/a` | `baseline_characteristics_schema_v1` | `publication_table_baseline` | `csv`, `md` | `table_shell` / `validated_table_values` |

## Input Schemas

### `binary_prediction_curve_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Binary Prediction Curves
- Templates: `fenggaolab.org.medical-display-core::roc_curve_binary`, `fenggaolab.org.medical-display-core::pr_curve_binary`, `fenggaolab.org.medical-display-core::calibration_curve_binary`, `fenggaolab.org.medical-display-core::decision_curve_binary`, `fenggaolab.org.medical-display-core::time_dependent_roc_horizon`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `series`
- Optional display fields: `paper_role`, `reference_line`, `time_horizon_months`
- Required collection fields: `series` -> `label`, `x`, `y`
- Optional collection fields: `series` -> `annotation`<br>`reference_line` -> `label`
- Required nested collection fields: `reference_line` -> `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `series_must_be_non_empty`, `series_x_y_lengths_must_match`, `series_values_must_be_finite`, `reference_line_x_y_lengths_must_match_when_present`, `time_dependent_roc_horizon_requires_positive_time_horizon_months_when_selected`

### `risk_layering_monotonic_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Monotonic Risk Layering Bars
- Templates: `fenggaolab.org.medical-display-core::risk_layering_monotonic_bars`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `left_panel_title`, `left_x_label`, `left_bars`, `right_panel_title`, `right_x_label`, `right_bars`
- Optional display fields: `paper_role`
- Required collection fields: `left_bars` -> `label`, `cases`, `events`, `risk`<br>`right_bars` -> `label`, `cases`, `events`, `risk`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `left_bars_must_be_non_empty`, `right_bars_must_be_non_empty`, `bar_cases_must_be_positive`, `bar_events_must_not_exceed_cases`, `bar_risk_must_be_finite_probability`, `bar_risk_must_match_events_over_cases`, `left_bars_risk_must_be_monotonic_non_decreasing`, `right_bars_risk_must_be_monotonic_non_decreasing`

### `time_to_event_multihorizon_calibration_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Multi-Horizon Grouped Calibration Panel (Time-to-Event)
- Templates: `fenggaolab.org.medical-display-core::time_to_event_multihorizon_calibration_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `time_horizon_months`, `calibration_summary`
- Optional collection fields: None
- Required nested collection fields: `panels.calibration_summary` -> `group_label`, `group_order`, `n`, `events`, `predicted_risk`, `observed_risk`
- Optional nested collection fields: None
- Additional constraints: `multihorizon_calibration_panels_must_be_non_empty`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_time_horizon_months_must_be_positive`, `panel_time_horizon_months_must_be_strictly_increasing`, `panel_calibration_summary_must_be_non_empty`, `panel_group_order_must_be_strictly_increasing`, `panel_group_risks_must_be_finite_probability`, `panel_group_events_must_not_exceed_group_size`

### `model_complexity_audit_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Model Complexity Audit Panel
- Templates: `fenggaolab.org.medical-display-core::model_complexity_audit_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `metric_panels`, `audit_panels`
- Optional display fields: `paper_role`
- Required collection fields: `metric_panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `rows`<br>`audit_panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `rows`
- Optional collection fields: `metric_panels` -> `reference_value`<br>`audit_panels` -> `reference_value`
- Required nested collection fields: `metric_panels.rows` -> `label`, `value`<br>`audit_panels.rows` -> `label`, `value`
- Optional nested collection fields: None
- Additional constraints: `metric_panels_must_be_non_empty`, `audit_panels_must_be_non_empty`, `panel_row_values_must_be_finite`

### `time_to_event_grouped_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Grouped Curves
- Templates: `fenggaolab.org.medical-display-core::kaplan_meier_grouped`, `fenggaolab.org.medical-display-core::cumulative_incidence_grouped`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`
- Optional display fields: `paper_role`, `annotation`, `groups`, `panel_a_title`, `panel_b_title`, `event_count_y_label`
- Required collection fields: `groups` -> `label`, `times`, `values`
- Optional collection fields: `risk_group_summaries` -> `label`, `sample_size`, `events_5y`, `mean_predicted_risk_5y`, `observed_km_risk_5y`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `kaplan_meier_grouped_and_cumulative_incidence_grouped_require_non_empty_groups`, `group_times_values_lengths_must_match_when_groups_present`, `group_values_must_be_finite_when_groups_present`, `time_to_event_risk_group_summary_requires_non_empty_risk_group_summaries_when_selected`, `risk_group_summary_events_must_not_exceed_sample_size`

### `time_to_event_decision_curve_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Decision Curves
- Templates: `fenggaolab.org.medical-display-core::time_to_event_decision_curve`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panel_a_title`, `panel_b_title`, `x_label`, `y_label`, `treated_fraction_y_label`, `series`, `treated_fraction_series`
- Optional display fields: `paper_role`, `reference_line`, `time_horizon_months`
- Required collection fields: `series` -> `label`, `x`, `y`<br>`treated_fraction_series` -> `label`, `x`, `y`
- Optional collection fields: `series` -> `annotation`<br>`reference_line` -> `label`
- Required nested collection fields: `reference_line` -> `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `series_must_be_non_empty`, `series_x_y_lengths_must_match`, `series_values_must_be_finite`, `reference_line_x_y_lengths_must_match_when_present`, `treated_fraction_series_x_y_lengths_must_match`, `treated_fraction_values_must_be_finite`, `publication_style_profile_required_at_materialization`, `display_override_contract_may_adjust_layout_without_changing_data`, `time_horizon_months_must_be_positive_when_declared`

### `dimensionality_reduction_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Dimensionality Reduction Workflow
- Templates: `fenggaolab.org.medical-display-core::pca_scatter_grouped`, `fenggaolab.org.medical-display-core::tsne_scatter_grouped`, `fenggaolab.org.medical-display-core::umap_scatter_grouped`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `embedding_input_mode`, `feature_matrix`
- Optional display fields: `paper_role`, `source_feature_matrix_digest`, `embedding_options`, `points`
- Required collection fields: `feature_matrix` -> `sample_id`, `group`, `features`
- Optional collection fields: `points` -> `sample_id`, `x`, `y`, `group`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `default_current_templates_compute_embedding_from_feature_matrix`, `feature_matrix_must_be_non_empty`, `feature_rows_must_have_same_named_numeric_features`, `sample_groups_must_be_non_empty`, `pca_uses_stats_prcomp`, `tsne_requires_Rtsne_backend`, `umap_requires_uwot_backend`, `precomputed_points_allowed_only_when_embedding_input_mode_is_precomputed`

### `omics_volcano_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Omics Volcano Panel
- Templates: `fenggaolab.org.medical-display-core::omics_volcano_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `legend_title`, `effect_threshold`, `significance_threshold`, `panel_order`, `points`
- Optional display fields: `paper_role`
- Required collection fields: `panel_order` -> `panel_id`, `panel_title`<br>`points` -> `panel_id`, `feature_label`, `effect_value`, `significance_value`, `regulation_class`
- Optional collection fields: `points` -> `label_text`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `legend_title_must_be_non_empty`, `effect_threshold_must_be_positive`, `significance_threshold_must_be_positive`, `panel_order_must_be_non_empty`, `panel_order_count_must_be_at_most_two`, `panel_ids_must_be_unique`, `panel_titles_must_be_non_empty`, `points_must_be_non_empty`, `point_panel_ids_must_match_declared_panels`, `each_declared_panel_must_contain_points`, `point_feature_labels_must_be_unique_within_panel`, `point_effect_values_must_be_finite`, `point_significance_values_must_be_non_negative`, `point_regulation_classes_must_use_supported_vocabulary`, `point_label_text_must_be_non_empty_when_present`

### `heatmap_group_comparison_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Heatmap Group Comparison
- Templates: `fenggaolab.org.medical-display-core::heatmap_group_comparison`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`

### `confusion_matrix_heatmap_binary_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Binary Confusion Matrix Heatmap
- Templates: `fenggaolab.org.medical-display-core::confusion_matrix_heatmap_binary`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `metric_name`, `normalization`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `metric_name_must_be_non_empty`, `normalization_must_use_supported_vocabulary`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `confusion_matrix_values_must_be_finite_probability`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `binary_confusion_matrix_must_have_exactly_two_row_labels`, `binary_confusion_matrix_must_have_exactly_two_column_labels`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_heatmap_grid_must_be_complete_and_unique`, `row_fraction_confusion_rows_must_sum_to_one_when_selected`, `column_fraction_confusion_columns_must_sum_to_one_when_selected`, `overall_fraction_confusion_matrix_must_sum_to_one_when_selected`

### `pathway_enrichment_dotplot_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Pathway Enrichment Dotplot Panel
- Templates: `fenggaolab.org.medical-display-core::pathway_enrichment_dotplot_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `effect_scale_label`, `size_scale_label`, `panel_order`, `pathway_order`, `points`
- Optional display fields: `paper_role`
- Required collection fields: `panel_order` -> `panel_id`, `panel_title`<br>`pathway_order` -> `label`<br>`points` -> `panel_id`, `pathway_label`, `x_value`, `effect_value`, `size_value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `effect_scale_label_must_be_non_empty`, `size_scale_label_must_be_non_empty`, `panel_order_must_be_non_empty`, `panel_order_count_must_be_at_most_two`, `panel_ids_must_be_unique`, `panel_titles_must_be_non_empty`, `pathway_order_labels_must_be_unique`, `points_must_be_non_empty`, `point_panel_ids_must_match_declared_panels`, `point_pathway_labels_must_match_declared_pathways`, `point_x_values_must_be_finite`, `point_effect_values_must_be_finite`, `point_size_values_must_be_non_negative`, `declared_panel_pathway_grid_must_be_complete_and_unique`

### `celltype_marker_dotplot_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Cell-Type Marker Dotplot Panel
- Templates: `fenggaolab.org.medical-display-core::celltype_marker_dotplot_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `effect_scale_label`, `size_scale_label`, `panel_order`, `celltype_order`, `marker_order`, `points`
- Optional display fields: `paper_role`
- Required collection fields: `panel_order` -> `panel_id`, `panel_title`<br>`celltype_order` -> `label`<br>`marker_order` -> `label`<br>`points` -> `panel_id`, `celltype_label`, `marker_label`, `effect_value`, `size_value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `effect_scale_label_must_be_non_empty`, `size_scale_label_must_be_non_empty`, `panel_order_must_be_non_empty`, `panel_order_count_must_be_at_most_two`, `panel_ids_must_be_unique`, `panel_titles_must_be_non_empty`, `celltype_order_labels_must_be_unique`, `marker_order_labels_must_be_unique`, `points_must_be_non_empty`, `point_panel_ids_must_match_declared_panels`, `point_celltype_labels_must_match_declared_celltypes`, `point_marker_labels_must_match_declared_markers`, `point_effect_values_must_be_finite`, `point_size_values_must_be_non_negative`, `declared_panel_celltype_marker_grid_must_be_complete_and_unique`

### `cnv_recurrence_summary_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: CNV Recurrence Summary Panel
- Templates: `fenggaolab.org.medical-display-core::cnv_recurrence_summary_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `burden_axis_label`, `frequency_axis_label`, `cnv_legend_title`, `region_order`, `sample_order`, `annotation_tracks`, `cnv_records`
- Optional display fields: `paper_role`
- Required collection fields: `region_order` -> `label`<br>`sample_order` -> `sample_id`<br>`annotation_tracks` -> `track_id`, `track_label`, `values`<br>`cnv_records` -> `sample_id`, `region_label`, `cnv_state`
- Optional collection fields: None
- Required nested collection fields: `annotation_tracks.values` -> `sample_id`, `category_label`
- Optional nested collection fields: None
- Additional constraints: `y_label_must_be_non_empty`, `burden_axis_label_must_be_non_empty`, `frequency_axis_label_must_be_non_empty`, `cnv_legend_title_must_be_non_empty`, `region_order_must_be_non_empty`, `region_order_labels_must_be_unique`, `sample_order_must_be_non_empty`, `sample_ids_must_be_unique`, `annotation_tracks_must_be_non_empty`, `annotation_track_count_must_be_at_most_three`, `annotation_track_ids_must_be_unique`, `annotation_track_labels_must_be_non_empty`, `annotation_track_sample_coverage_must_match_declared_sample_order`, `annotation_track_category_labels_must_be_non_empty`, `cnv_records_must_be_non_empty`, `cnv_sample_ids_must_match_declared_sample_order`, `cnv_region_labels_must_match_declared_region_order`, `cnv_sample_region_coordinates_must_be_unique`, `cnv_state_must_be_supported`

### `genomic_alteration_landscape_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Genomic Alteration Landscape Panel
- Templates: `fenggaolab.org.medical-display-core::genomic_alteration_landscape_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `burden_axis_label`, `frequency_axis_label`, `alteration_legend_title`, `gene_order`, `sample_order`, `annotation_tracks`, `alteration_records`
- Optional display fields: `paper_role`
- Required collection fields: `gene_order` -> `label`<br>`sample_order` -> `sample_id`<br>`annotation_tracks` -> `track_id`, `track_label`, `values`<br>`alteration_records` -> `sample_id`, `gene_label`
- Optional collection fields: None
- Required nested collection fields: `annotation_tracks.values` -> `sample_id`, `category_label`
- Optional nested collection fields: None
- Additional constraints: `y_label_must_be_non_empty`, `burden_axis_label_must_be_non_empty`, `frequency_axis_label_must_be_non_empty`, `alteration_legend_title_must_be_non_empty`, `gene_order_must_be_non_empty`, `gene_order_labels_must_be_unique`, `sample_order_must_be_non_empty`, `sample_ids_must_be_unique`, `annotation_tracks_must_be_non_empty`, `annotation_track_count_must_be_at_most_three`, `annotation_track_ids_must_be_unique`, `annotation_track_labels_must_be_non_empty`, `annotation_track_sample_coverage_must_match_declared_sample_order`, `annotation_track_category_labels_must_be_non_empty`, `alteration_records_must_be_non_empty`, `alteration_sample_ids_must_match_declared_sample_order`, `alteration_gene_labels_must_match_declared_gene_order`, `alteration_sample_gene_coordinates_must_be_unique`, `alteration_record_must_define_mutation_or_cnv`, `mutation_class_must_be_supported_when_present`, `cnv_state_must_be_supported_when_present`

### `genomic_alteration_consequence_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Genomic Alteration Consequence Panel
- Templates: `fenggaolab.org.medical-display-core::genomic_alteration_consequence_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `burden_axis_label`, `frequency_axis_label`, `alteration_legend_title`, `gene_order`, `sample_order`, `annotation_tracks`, `alteration_records`, `consequence_x_label`, `consequence_y_label`, `consequence_legend_title`, `effect_threshold`, `significance_threshold`, `driver_gene_order`, `consequence_panel_order`, `consequence_points`
- Optional display fields: `paper_role`
- Required collection fields: `gene_order` -> `label`<br>`sample_order` -> `sample_id`<br>`annotation_tracks` -> `track_id`, `track_label`, `values`<br>`alteration_records` -> `sample_id`, `gene_label`<br>`driver_gene_order` -> `label`<br>`consequence_panel_order` -> `panel_id`, `panel_title`<br>`consequence_points` -> `panel_id`, `gene_label`, `effect_value`, `significance_value`, `regulation_class`
- Optional collection fields: None
- Required nested collection fields: `annotation_tracks.values` -> `sample_id`, `category_label`
- Optional nested collection fields: None
- Additional constraints: `y_label_must_be_non_empty`, `burden_axis_label_must_be_non_empty`, `frequency_axis_label_must_be_non_empty`, `alteration_legend_title_must_be_non_empty`, `gene_order_must_be_non_empty`, `gene_order_labels_must_be_unique`, `sample_order_must_be_non_empty`, `sample_ids_must_be_unique`, `annotation_tracks_must_be_non_empty`, `annotation_track_count_must_be_at_most_three`, `annotation_track_ids_must_be_unique`, `annotation_track_labels_must_be_non_empty`, `annotation_track_sample_coverage_must_match_declared_sample_order`, `annotation_track_category_labels_must_be_non_empty`, `alteration_records_must_be_non_empty`, `alteration_sample_ids_must_match_declared_sample_order`, `alteration_gene_labels_must_match_declared_gene_order`, `alteration_sample_gene_coordinates_must_be_unique`, `alteration_record_must_define_mutation_or_cnv`, `mutation_class_must_be_supported_when_present`, `cnv_state_must_be_supported_when_present`, `consequence_x_label_must_be_non_empty`, `consequence_y_label_must_be_non_empty`, `consequence_legend_title_must_be_non_empty`, `effect_threshold_must_be_positive`, `significance_threshold_must_be_positive`, `driver_gene_order_must_be_non_empty`, `driver_gene_labels_must_be_unique`, `driver_gene_labels_must_be_subset_of_gene_order`, `consequence_panel_order_must_be_non_empty`, `consequence_panel_order_count_must_be_at_most_two`, `consequence_panel_ids_must_be_unique`, `consequence_panel_titles_must_be_non_empty`, `consequence_points_must_be_non_empty`, `consequence_point_panel_ids_must_match_declared_panels`, `consequence_point_gene_labels_must_match_declared_driver_genes`, `consequence_point_coordinates_must_be_complete_and_unique`, `consequence_point_effect_values_must_be_finite`, `consequence_point_significance_values_must_be_non_negative`, `consequence_point_regulation_classes_must_use_supported_vocabulary`

### `forest_effect_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Forest Effect Plot
- Templates: `fenggaolab.org.medical-display-core::forest_effect_main`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `reference_value`, `rows`
- Optional display fields: `paper_role`
- Required collection fields: `rows` -> `label`, `estimate`, `lower`, `upper`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `rows_must_be_non_empty`, `effect_interval_must_bound_estimate`, `effect_values_must_be_finite`

### `coefficient_path_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Coefficient Path Panel
- Templates: `fenggaolab.org.medical-display-core::coefficient_path_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `path_panel_title`, `x_label`, `reference_value`, `step_legend_title`, `steps`, `coefficient_rows`, `summary_panel_title`, `summary_cards`
- Optional display fields: `paper_role`
- Required collection fields: `steps` -> `step_id`, `step_label`, `step_order`<br>`coefficient_rows` -> `row_id`, `row_label`, `points`<br>`summary_cards` -> `card_id`, `label`, `value`
- Optional collection fields: `summary_cards` -> `detail`
- Required nested collection fields: `coefficient_rows.points` -> `step_id`, `estimate`, `lower`, `upper`
- Optional nested collection fields: `coefficient_rows.points` -> `support_n`
- Additional constraints: `steps_must_contain_between_two_and_five_entries`, `step_ids_must_be_unique`, `step_orders_must_be_strictly_increasing`, `reference_value_must_be_finite`, `coefficient_rows_must_be_non_empty`, `coefficient_row_ids_must_be_unique`, `coefficient_row_labels_must_be_unique`, `coefficient_points_must_cover_all_declared_steps_once`, `coefficient_point_values_must_be_finite`, `coefficient_point_intervals_must_wrap_estimate`, `coefficient_point_support_n_must_be_positive_when_present`, `summary_cards_must_contain_between_two_and_four_entries`, `summary_card_ids_must_be_unique`

### `shap_summary_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Summary Beeswarm
- Templates: `fenggaolab.org.medical-display-core::shap_summary_beeswarm`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `rows`
- Optional display fields: `paper_role`
- Required collection fields: `rows` -> `feature`, `points`
- Optional collection fields: None
- Required nested collection fields: `rows.points` -> `shap_value`, `feature_value`
- Optional nested collection fields: None
- Additional constraints: `rows_must_be_non_empty`, `row_feature_must_be_non_empty`, `row_points_must_be_non_empty`, `shap_values_must_be_finite`, `feature_values_must_be_finite`

### `shap_dependence_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Dependence Panel
- Templates: `fenggaolab.org.medical-display-core::shap_dependence_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `colorbar_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `interaction_feature`, `points`
- Optional collection fields: None
- Required nested collection fields: `panels.points` -> `feature_value`, `shap_value`, `interaction_value`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_features_must_be_unique`, `panel_points_must_be_non_empty`, `panel_point_values_must_be_finite`

### `shap_waterfall_local_explanation_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Waterfall Local Explanation Panel
- Templates: `fenggaolab.org.medical-display-core::shap_waterfall_local_explanation_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `case_label`, `baseline_value`, `predicted_value`, `contributions`
- Optional collection fields: None
- Required nested collection fields: `panels.contributions` -> `feature`, `shap_value`
- Optional nested collection fields: `panels.contributions` -> `feature_value_text`
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_case_labels_must_be_unique`, `panel_values_must_be_finite`, `panel_contributions_must_be_non_empty`, `panel_contribution_features_must_be_unique_within_panel`, `panel_contribution_values_must_be_finite_and_non_zero`, `panel_prediction_value_must_equal_baseline_plus_contributions`

### `generalizability_subgroup_composite_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Generalizability and Subgroup Composite Panel
- Templates: `fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `metric_family`, `primary_label`, `overview_panel_title`, `overview_x_label`, `overview_rows`, `subgroup_panel_title`, `subgroup_x_label`, `subgroup_reference_value`, `subgroup_rows`
- Optional display fields: `paper_role`, `comparator_label`
- Required collection fields: `overview_rows` -> `cohort_id`, `cohort_label`, `support_count`, `metric_value`<br>`subgroup_rows` -> `subgroup_id`, `subgroup_label`, `estimate`, `lower`, `upper`
- Optional collection fields: `overview_rows` -> `comparator_metric_value`, `event_count`<br>`subgroup_rows` -> `group_n`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `metric_family_must_be_supported`, `primary_label_must_be_non_empty`, `overview_rows_must_be_non_empty`, `overview_cohort_ids_must_be_unique`, `overview_cohort_labels_must_be_unique`, `overview_support_counts_must_be_non_negative`, `overview_event_counts_must_be_non_negative_when_present`, `overview_metric_values_must_be_finite`, `overview_comparator_metric_values_must_be_finite_when_present`, `overview_comparator_metric_values_must_be_present_for_all_rows_when_comparator_label_is_declared`, `overview_comparator_metric_values_must_be_absent_without_comparator_label`, `subgroup_reference_value_must_be_finite`, `subgroup_rows_must_be_non_empty`, `subgroup_ids_must_be_unique`, `subgroup_labels_must_be_unique`, `subgroup_values_must_be_finite`, `subgroup_group_n_must_be_non_negative_when_present`, `subgroup_rows_must_satisfy_lower_le_estimate_le_upper`

### `cohort_flow_shell_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Cohort Flow Figure
- Templates: `fenggaolab.org.medical-display-core::cohort_flow_figure`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `steps`
- Optional top-level fields: `caption`, `exclusions`, `endpoint_inventory`, `design_panels`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `steps` -> `step_id`, `label`, `n`<br>`exclusions` -> `exclusion_id`, `from_step_id`, `label`, `n`<br>`endpoint_inventory` -> `endpoint_id`, `label`, `event_n`<br>`design_panels` -> `panel_id`, `title`, `layout_role`, `lines`
- Optional collection fields: `steps` -> `detail`<br>`exclusions` -> `detail`<br>`endpoint_inventory` -> `detail`
- Required nested collection fields: `design_panels.lines` -> `label`
- Optional nested collection fields: `design_panels.lines` -> `detail`
- Additional constraints: `steps_must_be_non_empty`, `step_ids_must_be_unique`, `step_label_must_be_non_empty`, `step_n_must_be_integer`, `exclusions_from_step_ids_must_reference_steps`, `exclusion_ids_must_be_unique`, `exclusion_n_must_be_integer`, `endpoint_inventory_ids_must_be_unique`, `endpoint_inventory_event_n_must_be_integer`, `design_panel_ids_must_be_unique`, `design_panel_layout_roles_must_be_supported_and_unique`, `design_panel_lines_must_be_non_empty`

### `submission_graphical_abstract_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Submission Graphical Abstract
- Templates: `fenggaolab.org.medical-display-core::submission_graphical_abstract`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `catalog_id`, `title`, `caption`, `panels`
- Optional top-level fields: `paper_role`, `footer_pills`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `subtitle`, `rows`
- Optional collection fields: `footer_pills` -> `pill_id`, `label`, `style_role`
- Required nested collection fields: `panels.rows` -> `cards`<br>`panels.rows.cards` -> `card_id`, `title`, `value`
- Optional nested collection fields: `panels.rows.cards` -> `detail`, `accent_role`<br>`footer_pills` -> `panel_id`
- Additional constraints: `graphical_abstract_panels_must_be_non_empty`, `graphical_abstract_panel_ids_must_be_unique`, `graphical_abstract_rows_must_be_non_empty`, `graphical_abstract_cards_must_be_non_empty`, `graphical_abstract_footer_pills_must_reference_known_panels_when_present`

### `baseline_characteristics_schema_v1`

- Display kind: `table_shell`
- Display name: Baseline Characteristics Table
- Templates: `fenggaolab.org.medical-display-core::table1_baseline_characteristics`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `groups`, `variables`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `groups` -> `group_id`, `label`<br>`variables` -> `variable_id`, `label`, `values`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `groups_must_be_non_empty`, `variables_must_be_non_empty`, `variable_values_length_must_match_groups`
