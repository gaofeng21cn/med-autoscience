# Medical Display Audit Guide

This guide is the stable, human-auditable view of the medical display system in `med-autoscience`.

Use this file when the goal is to answer which display classes are officially supported, which templates are fully audited, and which schema/QC path each class is bound to.

For the exhaustive generated matrix, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).

## Current Audited Coverage

- Evidence figure classes: `9`
- Implemented evidence figure templates: `23`
- Illustration shells: `2`
- Table shells: `5`
- Total implemented display templates: `30`

## Evidence Class Map

| Class | Implemented Templates | Input Schemas | Primary QC Profiles |
| --- | ---: | --- | --- |
| Prediction Performance | 4 | `binary_prediction_curve_inputs_v1`, `risk_layering_monotonic_inputs_v1` | `publication_evidence_curve`, `publication_risk_layering_bars` |
| Clinical Utility | 3 | `binary_prediction_curve_inputs_v1`, `binary_calibration_decision_curve_panel_inputs_v1`, `time_to_event_decision_curve_inputs_v1` | `publication_evidence_curve`, `publication_binary_calibration_decision_curve`, `publication_decision_curve` |
| Time-to-Event | 5 | `binary_prediction_curve_inputs_v1`, `time_to_event_grouped_inputs_v1`, `time_to_event_discrimination_calibration_inputs_v1` | `publication_evidence_curve`, `publication_survival_curve` |
| Data Geometry | 3 | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` |
| Matrix Pattern | 3 | `heatmap_group_comparison_inputs_v1`, `correlation_heatmap_inputs_v1`, `clustered_heatmap_inputs_v1` | `publication_heatmap` |
| Effect Estimate | 2 | `forest_effect_inputs_v1` | `publication_forest_plot` |
| Model Explanation | 1 | `shap_summary_inputs_v1` | `publication_shap_summary` |
| Model Audit | 1 | `model_complexity_audit_panel_inputs_v1` | `publication_model_complexity_audit` |
| Generalizability | 1 | `multicenter_generalizability_inputs_v1` | `publication_multicenter_overview` |

## Evidence Class Detail

### Prediction Performance

Templates:
- `roc_curve_binary`
- `pr_curve_binary`
- `calibration_curve_binary`
- `risk_layering_monotonic_bars`

Authoritative contract:
- Input schemas: `binary_prediction_curve_inputs_v1`, `risk_layering_monotonic_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC profiles: `publication_evidence_curve`, `publication_risk_layering_bars`

### Clinical Utility

Templates:
- `decision_curve_binary`
- `binary_calibration_decision_curve_panel`
- `time_to_event_decision_curve`

Authoritative contract:
- Input schemas: `binary_prediction_curve_inputs_v1`, `binary_calibration_decision_curve_panel_inputs_v1`, `time_to_event_decision_curve_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC profiles: `publication_evidence_curve`, `publication_binary_calibration_decision_curve`, `publication_decision_curve`

### Time-to-Event

Templates:
- `time_dependent_roc_horizon`
- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`
- `time_to_event_discrimination_calibration_panel`
- `time_to_event_risk_group_summary`

Authoritative contract:
- Input schemas: `binary_prediction_curve_inputs_v1`, `time_to_event_grouped_inputs_v1`, `time_to_event_discrimination_calibration_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC profiles: `publication_evidence_curve`, `publication_survival_curve`

### Data Geometry

Templates:
- `umap_scatter_grouped`
- `pca_scatter_grouped`
- `tsne_scatter_grouped`

Authoritative contract:
- Input schemas: `embedding_grouped_inputs_v1`
- Renderer families: `r_ggplot2`
- QC profiles: `publication_embedding_scatter`

### Matrix Pattern

Templates:
- `heatmap_group_comparison`
- `correlation_heatmap`
- `clustered_heatmap`

Authoritative contract:
- Input schemas: `heatmap_group_comparison_inputs_v1`, `correlation_heatmap_inputs_v1`, `clustered_heatmap_inputs_v1`
- Renderer families: `r_ggplot2`
- QC profiles: `publication_heatmap`

### Effect Estimate

Templates:
- `forest_effect_main`
- `subgroup_forest`

Authoritative contract:
- Input schemas: `forest_effect_inputs_v1`
- Renderer families: `r_ggplot2`
- QC profiles: `publication_forest_plot`

### Model Explanation

Templates:
- `shap_summary_beeswarm`

Authoritative contract:
- Input schemas: `shap_summary_inputs_v1`
- Renderer families: `python`
- QC profiles: `publication_shap_summary`

### Model Audit

Templates:
- `model_complexity_audit_panel`

Authoritative contract:
- Input schemas: `model_complexity_audit_panel_inputs_v1`
- Renderer families: `python`
- QC profiles: `publication_model_complexity_audit`

### Generalizability

Templates:
- `multicenter_generalizability_overview`

Authoritative contract:
- Input schemas: `multicenter_generalizability_inputs_v1`
- Renderer families: `python`
- QC profiles: `publication_multicenter_overview`

## Publication Shell Layer

| Kind | Implemented Templates | Input Schemas | Contract Gate |
| --- | ---: | --- | --- |
| Illustration Shell | 2 | `cohort_flow_shell_inputs_v1`, `submission_graphical_abstract_inputs_v1` | shell profile + catalog contract |
| Table Shell | 5 | `baseline_characteristics_schema_v1`, `time_to_event_performance_summary_v1`, `clinical_interpretation_summary_v1`, `performance_summary_table_generic_v1`, `grouped_risk_event_summary_table_v1` | table profile + catalog contract |

## Change Protocol

Whenever a new audited display template is added, update `display_registry.py`, `display_schema_contract.py`, `display_surface_materialization.py`, `display_layout_qc.py`, the checked-in guides, and the program reports in the same change.
