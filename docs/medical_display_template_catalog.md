# Medical Display Template Catalog

Generated from `med_autoscience.display_registry` and `med_autoscience.display_schema_contract`.

For the stable human-auditable overview, completion counts, and change protocol, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

## Publication Style and Override Governance

- `paper/publication_style_profile.json` is the article-level visual truth source for publication-facing figures.
- `paper/display_overrides.json` is the figure-level structured adjustment surface for manuscript-specific layout and readability decisions.
- Templates preserve a stable lower bound; article-level style and figure-level overrides may refine expression without bypassing the audited renderer path.

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
| `time_to_event_decision_curve` | `evidence_figure` | Decision Curve (Time-to-Event Horizon) | `python` | `time_to_event_decision_curve_inputs_v1` | `publication_decision_curve` | `png`, `pdf` |

### Time-to-Event

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
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

### Generalizability

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `multicenter_generalizability_overview` | `evidence_figure` | Multicenter Generalizability Overview | `python` | `multicenter_generalizability_inputs_v1` | `publication_multicenter_overview` | `png`, `pdf` |

### Publication Shells and Tables

| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- |
| `cohort_flow_figure` | `illustration_shell` | Cohort Flow Figure | `python` | `cohort_flow_shell_inputs_v1` | `publication_illustration_flow` | `png`, `svg` |
| `table1_baseline_characteristics` | `table_shell` | Table 1 Baseline Characteristics | `n/a` | `baseline_characteristics_schema_v1` | `publication_table_baseline` | `csv`, `md` |
| `table2_time_to_event_performance_summary` | `table_shell` | Table 2 Time-to-Event Performance Summary | `n/a` | `time_to_event_performance_summary_v1` | `publication_table_performance` | `md` |
| `table3_clinical_interpretation_summary` | `table_shell` | Table 3 Clinical Interpretation Summary | `n/a` | `clinical_interpretation_summary_v1` | `publication_table_interpretation` | `md` |

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

### `time_to_event_grouped_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Grouped Curves
- Templates: `kaplan_meier_grouped`, `cumulative_incidence_grouped`, `time_to_event_risk_group_summary`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `groups`
- Optional display fields: `paper_role`, `annotation`
- Required collection fields: `groups` -> `label`, `times`, `values`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `groups_must_be_non_empty`, `group_times_values_lengths_must_match`, `group_values_must_be_finite`

### `time_to_event_discrimination_calibration_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Discrimination and Calibration Panel
- Templates: `time_to_event_discrimination_calibration_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `discrimination_x_label`, `discrimination_y_label`, `calibration_x_label`, `calibration_y_label`, `discrimination_series`, `calibration_groups`
- Optional display fields: `paper_role`, `discrimination_reference_line`, `calibration_reference_line`
- Required collection fields: `discrimination_series` -> `label`, `x`, `y`<br>`calibration_groups` -> `label`, `times`, `values`
- Optional collection fields: `discrimination_series` -> `annotation`<br>`discrimination_reference_line` -> `label`<br>`calibration_reference_line` -> `label`
- Required nested collection fields: `discrimination_reference_line` -> `x`, `y`<br>`calibration_reference_line` -> `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `discrimination_series_must_be_non_empty`, `discrimination_series_x_y_lengths_must_match`, `calibration_groups_must_be_non_empty`, `calibration_group_times_values_lengths_must_match`, `calibration_values_must_be_finite`

### `time_to_event_decision_curve_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Decision Curves
- Templates: `time_to_event_decision_curve`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `series`
- Optional display fields: `paper_role`, `reference_line`
- Required collection fields: `series` -> `label`, `x`, `y`
- Optional collection fields: `series` -> `annotation`<br>`reference_line` -> `label`
- Required nested collection fields: `reference_line` -> `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `series_must_be_non_empty`, `series_x_y_lengths_must_match`, `series_values_must_be_finite`, `reference_line_x_y_lengths_must_match_when_present`, `publication_style_profile_required_at_materialization`, `display_override_contract_may_adjust_layout_without_changing_data`

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
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `centers`
- Optional display fields: `paper_role`, `reference_line`
- Required collection fields: `centers` -> `center_label`, `sample_size`, `estimate`, `lower`, `upper`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `centers_must_be_non_empty`, `center_labels_must_be_unique`, `sample_size_must_be_positive`, `effect_interval_must_bound_estimate`

### `cohort_flow_shell_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Cohort Flow Figure
- Templates: `cohort_flow_figure`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `steps`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `steps` -> `step_id`, `label`, `n`
- Optional collection fields: `steps` -> `detail`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `steps_must_be_non_empty`, `step_label_must_be_non_empty`, `step_n_must_be_integer`

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
