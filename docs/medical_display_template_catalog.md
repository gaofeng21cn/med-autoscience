# Medical Display Template Catalog

Generated from `med_autoscience.display_registry` and `med_autoscience.display_schema_contract`.

For the stable human-auditable overview, completion counts, and change protocol, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

## Publication Style and Override Governance

- `paper/publication_style_profile.json` is the article-level visual truth source for publication-facing figures.
- `paper/display_overrides.json` is the figure-level structured adjustment surface for manuscript-specific layout and readability decisions.
- Templates preserve a stable lower bound; article-level style and figure-level overrides may refine expression without bypassing the audited renderer path.
- Final manuscript-facing polish is **AI-first above that lower bound**: use the generated image as the truth surface, let visual review identify concrete defects, then harden the audited renderer/QC path instead of paper-local patching.
- Canonical paper-owned packaging surface remains `paper/submission_minimal/`; `manuscript/final/` is the human-facing mirror, while `artifacts/` is auxiliary evidence only and should not replace that fixed lookup path.
- Canonical rendered assets live under `paper/figures/generated/` and `paper/tables/generated/`; legacy top-level `paper/figures/Figure*.png|pdf|svg` / `paper/tables/Table*.csv|md` mirrors should be removed once they are no longer referenced by the active catalogs.

## Template Classes

### Prediction Performance

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `roc_curve_binary` | `evidence_figure` | ROC Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `pr_curve_binary` | `evidence_figure` | Precision-Recall Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `calibration_curve_binary` | `evidence_figure` | Calibration Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |

### Clinical Utility

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `decision_curve_binary` | `evidence_figure` | Decision Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `binary_calibration_decision_curve_panel` | `evidence_figure` | Binary Calibration and Decision Curve Panel | `python` | `binary_calibration_decision_curve_panel_inputs_v1` | `publication_binary_calibration_decision_curve` | `png`, `pdf` |
| `time_to_event_decision_curve` | `evidence_figure` | Decision Curve (Time-to-Event Horizon) | `python` | `time_to_event_decision_curve_inputs_v1` | `publication_decision_curve` | `png`, `pdf` |

### Time-to-Event

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `risk_layering_monotonic_bars` | `evidence_figure` | Monotonic Risk Layering Bars | `python` | `risk_layering_monotonic_inputs_v1` | `publication_risk_layering_bars` | `png`, `pdf` |
| `time_dependent_roc_horizon` | `evidence_figure` | Time-Dependent ROC (Horizon) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `kaplan_meier_grouped` | `evidence_figure` | Kaplan-Meier Curve (Grouped) | `r_ggplot2` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |
| `cumulative_incidence_grouped` | `evidence_figure` | Cumulative Incidence Curve (Grouped) | `r_ggplot2` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |
| `time_to_event_discrimination_calibration_panel` | `evidence_figure` | Validation Discrimination and Grouped Calibration (Time-to-Event) | `python` | `time_to_event_discrimination_calibration_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `time_to_event_risk_group_summary` | `evidence_figure` | Risk-Group Summary (Time-to-Event) | `python` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |

### Data Geometry

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `umap_scatter_grouped` | `evidence_figure` | UMAP Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `pca_scatter_grouped` | `evidence_figure` | PCA Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `tsne_scatter_grouped` | `evidence_figure` | t-SNE Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |

### Matrix Pattern

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `heatmap_group_comparison` | `evidence_figure` | Heatmap (Group Comparison) | `r_ggplot2` | `heatmap_group_comparison_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `correlation_heatmap` | `evidence_figure` | Correlation Heatmap | `r_ggplot2` | `correlation_heatmap_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `clustered_heatmap` | `evidence_figure` | Clustered Heatmap (Precomputed Ordering) | `r_ggplot2` | `clustered_heatmap_inputs_v1` | `publication_heatmap` | `png`, `pdf` |

### Effect Estimate

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `forest_effect_main` | `evidence_figure` | Forest Plot (Main Effects) | `r_ggplot2` | `forest_effect_inputs_v1` | `publication_forest_plot` | `png`, `pdf` |
| `subgroup_forest` | `evidence_figure` | Forest Plot (Subgroup Effects) | `r_ggplot2` | `forest_effect_inputs_v1` | `publication_forest_plot` | `png`, `pdf` |

### Model Explanation

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `shap_summary_beeswarm` | `evidence_figure` | SHAP Summary Beeswarm | `python` | `shap_summary_inputs_v1` | `publication_shap_summary` | `png`, `pdf` |

### Model Audit

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `model_complexity_audit_panel` | `evidence_figure` | Model Complexity Audit Panel | `python` | `model_complexity_audit_panel_inputs_v1` | `publication_model_complexity_audit` | `png`, `pdf` |

### Generalizability

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `multicenter_generalizability_overview` | `evidence_figure` | Multicenter Generalizability Overview | `python` | `multicenter_generalizability_inputs_v1` | `publication_multicenter_overview` | `png`, `pdf` |

### Publication Shells and Tables

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `cohort_flow_figure` | `illustration_shell` | Cohort Flow Figure | `python` | `cohort_flow_shell_inputs_v1` | `publication_illustration_flow` | `png`, `svg` |
| `submission_graphical_abstract` | `illustration_shell` | Submission Graphical Abstract | `python` | `submission_graphical_abstract_inputs_v1` | `submission_graphical_abstract` | `png`, `svg` |
| `table1_baseline_characteristics` | `table_shell` | Table 1 Baseline Characteristics | `n/a` | `baseline_characteristics_schema_v1` | `publication_table_baseline` | `csv`, `md` |
| `table2_time_to_event_performance_summary` | `table_shell` | Table 2 Time-to-Event Performance Summary | `n/a` | `time_to_event_performance_summary_v1` | `publication_table_performance` | `md` |
| `table3_clinical_interpretation_summary` | `table_shell` | Table 3 Clinical Interpretation Summary | `n/a` | `clinical_interpretation_summary_v1` | `publication_table_interpretation` | `md` |
| `performance_summary_table_generic` | `table_shell` | Performance Summary Table (Generic) | `n/a` | `performance_summary_table_generic_v1` | `publication_table_performance` | `csv`, `md` |
| `grouped_risk_event_summary_table` | `table_shell` | Grouped Risk Event Summary Table | `n/a` | `grouped_risk_event_summary_table_v1` | `publication_table_interpretation` | `csv`, `md` |

## Input Schemas

### `binary_prediction_curve_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Binary Prediction Curves
- Templates: `roc_curve_binary`, `pr_curve_binary`, `calibration_curve_binary`, `decision_curve_binary`, `time_dependent_roc_horizon`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `series`
- Optional display fields: `paper_role`, `reference_line`
- Required collection fields: `series` -> `label`, `x`, `y`
- Optional collection fields: `series` -> `annotation`<br>`reference_line` -> `label`
- Required nested collection fields: `reference_line` -> `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `series_must_be_non_empty`, `series_x_y_lengths_must_match`, `series_values_must_be_finite`, `reference_line_x_y_lengths_must_match_when_present`

### `risk_layering_monotonic_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Monotonic Risk Layering Bars
- Templates: `risk_layering_monotonic_bars`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `left_panel_title`, `left_x_label`, `left_bars`, `right_panel_title`, `right_x_label`, `right_bars`
- Optional display fields: `paper_role`
- Required collection fields: `left_bars` -> `label`, `cases`, `events`, `risk`<br>`right_bars` -> `label`, `cases`, `events`, `risk`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `left_bars_must_be_non_empty`, `right_bars_must_be_non_empty`, `bar_cases_must_be_positive`, `bar_events_must_not_exceed_cases`, `bar_risk_must_be_finite_probability`, `bar_risk_must_match_events_over_cases`, `left_bars_risk_must_be_monotonic_non_decreasing`, `right_bars_risk_must_be_monotonic_non_decreasing`

### `binary_calibration_decision_curve_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Binary Calibration and Decision Curve Panel
- Templates: `binary_calibration_decision_curve_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `calibration_x_label`, `calibration_y_label`, `decision_x_label`, `decision_y_label`, `calibration_axis_window`, `calibration_series`, `decision_series`, `decision_reference_lines`, `decision_focus_window`
- Optional display fields: `paper_role`, `calibration_reference_line`
- Required collection fields: `calibration_series` -> `label`, `x`, `y`<br>`decision_series` -> `label`, `x`, `y`<br>`decision_reference_lines` -> `label`, `x`, `y`
- Optional collection fields: `calibration_reference_line` -> `label`
- Required nested collection fields: `calibration_reference_line` -> `x`, `y`<br>`calibration_axis_window` -> `xmin`, `xmax`, `ymin`, `ymax`<br>`decision_focus_window` -> `xmin`, `xmax`
- Optional nested collection fields: None
- Additional constraints: `calibration_series_must_be_non_empty`, `calibration_series_x_y_lengths_must_match`, `decision_series_must_be_non_empty`, `decision_series_x_y_lengths_must_match`, `decision_reference_lines_must_be_non_empty`, `decision_reference_lines_x_y_lengths_must_match`, `calibration_axis_window_must_be_strictly_increasing`, `decision_focus_window_must_be_strictly_increasing`

### `model_complexity_audit_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Model Complexity Audit Panel
- Templates: `model_complexity_audit_panel`
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
- Templates: `kaplan_meier_grouped`, `cumulative_incidence_grouped`, `time_to_event_risk_group_summary`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`
- Optional display fields: `paper_role`, `annotation`, `groups`, `panel_a_title`, `panel_b_title`, `event_count_y_label`
- Required collection fields: `groups` -> `label`, `times`, `values`
- Optional collection fields: `risk_group_summaries` -> `label`, `sample_size`, `events_5y`, `mean_predicted_risk_5y`, `observed_km_risk_5y`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `kaplan_meier_grouped_and_cumulative_incidence_grouped_require_non_empty_groups`, `group_times_values_lengths_must_match_when_groups_present`, `group_values_must_be_finite_when_groups_present`, `time_to_event_risk_group_summary_requires_non_empty_risk_group_summaries_when_selected`

### `time_to_event_discrimination_calibration_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Discrimination and Calibration Panel
- Templates: `time_to_event_discrimination_calibration_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panel_a_title`, `panel_b_title`, `discrimination_x_label`, `calibration_x_label`, `calibration_y_label`, `discrimination_points`, `calibration_summary`
- Optional display fields: `paper_role`, `calibration_callout`
- Required collection fields: `discrimination_points` -> `label`, `c_index`<br>`calibration_summary` -> `group_label`, `group_order`, `n`, `events_5y`, `predicted_risk_5y`, `observed_risk_5y`
- Optional collection fields: `discrimination_points` -> `annotation`
- Required nested collection fields: `calibration_callout` -> `group_label`, `predicted_risk_5y`, `observed_risk_5y`
- Optional nested collection fields: `calibration_callout` -> `events_5y`, `n`
- Additional constraints: `discrimination_points_must_be_non_empty`, `discrimination_points_must_be_finite_c_index`, `calibration_summary_must_be_non_empty`, `calibration_group_order_must_be_strictly_increasing`, `calibration_summary_risks_must_be_finite_probability`, `calibration_callout_must_reference_group_label_when_present`

### `time_to_event_decision_curve_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Decision Curves
- Templates: `time_to_event_decision_curve`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panel_a_title`, `panel_b_title`, `x_label`, `y_label`, `treated_fraction_y_label`, `series`, `treated_fraction_series`
- Optional display fields: `paper_role`, `reference_line`
- Required collection fields: `series` -> `label`, `x`, `y`<br>`treated_fraction_series` -> `label`, `x`, `y`
- Optional collection fields: `series` -> `annotation`<br>`reference_line` -> `label`
- Required nested collection fields: `reference_line` -> `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `series_must_be_non_empty`, `series_x_y_lengths_must_match`, `series_values_must_be_finite`, `reference_line_x_y_lengths_must_match_when_present`, `treated_fraction_series_x_y_lengths_must_match`, `treated_fraction_values_must_be_finite`, `publication_style_profile_required_at_materialization`, `display_override_contract_may_adjust_layout_without_changing_data`

### `embedding_grouped_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Grouped Embedding Scatter
- Templates: `umap_scatter_grouped`, `pca_scatter_grouped`, `tsne_scatter_grouped`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `points`
- Optional display fields: `paper_role`
- Required collection fields: `points` -> `x`, `y`, `group`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `points_must_be_non_empty`, `point_coordinates_must_be_finite`, `point_group_must_be_non_empty`

### `heatmap_group_comparison_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Heatmap Group Comparison
- Templates: `heatmap_group_comparison`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`

### `correlation_heatmap_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Correlation Heatmap
- Templates: `correlation_heatmap`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `matrix_must_be_square`, `matrix_must_include_diagonal`, `matrix_must_be_symmetric`

### `clustered_heatmap_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Clustered Heatmap
- Templates: `clustered_heatmap`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_heatmap_grid_must_be_complete_and_unique`

### `forest_effect_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Forest Effect Plot
- Templates: `forest_effect_main`, `subgroup_forest`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `reference_value`, `rows`
- Optional display fields: `paper_role`
- Required collection fields: `rows` -> `label`, `estimate`, `lower`, `upper`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `rows_must_be_non_empty`, `effect_interval_must_bound_estimate`, `effect_values_must_be_finite`

### `shap_summary_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Summary Beeswarm
- Templates: `shap_summary_beeswarm`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `rows`
- Optional display fields: `paper_role`
- Required collection fields: `rows` -> `feature`, `points`
- Optional collection fields: None
- Required nested collection fields: `rows.points` -> `shap_value`, `feature_value`
- Optional nested collection fields: None
- Additional constraints: `rows_must_be_non_empty`, `row_feature_must_be_non_empty`, `row_points_must_be_non_empty`, `shap_values_must_be_finite`, `feature_values_must_be_finite`

### `multicenter_generalizability_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Multicenter Generalizability Overview
- Templates: `multicenter_generalizability_overview`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `overview_mode`, `center_event_y_label`, `coverage_y_label`, `center_event_counts`, `coverage_panels`
- Optional display fields: `paper_role`
- Required collection fields: `center_event_counts` -> `center_label`, `split_bucket`, `event_count`<br>`coverage_panels` -> `panel_id`, `title`, `layout_role`, `bars`
- Optional collection fields: None
- Required nested collection fields: `coverage_panels.bars` -> `label`, `count`
- Optional nested collection fields: None
- Additional constraints: `overview_mode_must_be_center_support_counts`, `center_event_counts_must_be_non_empty`, `center_event_counts_labels_must_be_unique`, `center_event_counts_must_be_non_negative`, `coverage_panels_must_be_non_empty`, `coverage_panel_ids_must_be_unique`, `coverage_panel_layout_roles_must_cover_wide_left_top_right_bottom_right`, `coverage_panel_bars_must_be_non_empty`, `coverage_panel_bars_must_be_non_negative`

### `cohort_flow_shell_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Cohort Flow Figure
- Templates: `cohort_flow_figure`
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
- Templates: `submission_graphical_abstract`
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
- Templates: `table1_baseline_characteristics`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `groups`, `variables`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `groups` -> `group_id`, `label`<br>`variables` -> `variable_id`, `label`, `values`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `groups_must_be_non_empty`, `variables_must_be_non_empty`, `variable_values_length_must_match_groups`

### `time_to_event_performance_summary_v1`

- Display kind: `table_shell`
- Display name: Time-to-Event Performance Summary Table
- Templates: `table2_time_to_event_performance_summary`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `columns`, `rows`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `columns` -> `column_id`, `label`<br>`rows` -> `row_id`, `label`, `values`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `columns_must_be_non_empty`, `rows_must_be_non_empty`, `row_values_length_must_match_columns`

### `clinical_interpretation_summary_v1`

- Display kind: `table_shell`
- Display name: Clinical Interpretation Summary Table
- Templates: `table3_clinical_interpretation_summary`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `columns`, `rows`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `columns` -> `column_id`, `label`<br>`rows` -> `row_id`, `label`, `values`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `columns_must_be_non_empty`, `rows_must_be_non_empty`, `row_values_length_must_match_columns`

### `performance_summary_table_generic_v1`

- Display kind: `table_shell`
- Display name: Performance Summary Table (Generic)
- Templates: `performance_summary_table_generic`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `row_header_label`, `columns`, `rows`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `columns` -> `column_id`, `label`<br>`rows` -> `row_id`, `label`, `values`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `row_header_label_must_be_non_empty`, `columns_must_be_non_empty`, `rows_must_be_non_empty`, `row_values_length_must_match_columns`

### `grouped_risk_event_summary_table_v1`

- Display kind: `table_shell`
- Display name: Grouped Risk Event Summary Table
- Templates: `grouped_risk_event_summary_table`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `surface_column_label`, `stratum_column_label`, `cases_column_label`, `events_column_label`, `risk_column_label`, `rows`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `rows` -> `row_id`, `surface`, `stratum`, `cases`, `events`, `risk_display`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `surface_column_label_must_be_non_empty`, `stratum_column_label_must_be_non_empty`, `cases_column_label_must_be_non_empty`, `events_column_label_must_be_non_empty`, `risk_column_label_must_be_non_empty`, `rows_must_be_non_empty`, `row_surface_must_be_non_empty`, `row_stratum_must_be_non_empty`, `row_cases_must_be_positive_integer`, `row_events_must_be_integer_between_zero_and_cases`, `row_risk_display_must_match_events_over_cases_percent_1dp`
