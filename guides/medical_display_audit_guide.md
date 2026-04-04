# Medical Display Audit Guide

This guide is the stable, human-auditable view of the medical display system in `med-autoscience`.

Use this file when the goal is to answer:

- Which display classes are officially supported?
- Which figure and table templates are already materialized end to end?
- Which input schema contracts are enforced?
- Which renderer and layout-QC path is authoritative for each template?
- What must change together when a new display template is added?

For the exhaustive generated matrix, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).

## Scope

This guide covers the audited display surface only. A display counts as "implemented" here only when all of the following are true:

1. It is registered in `src/med_autoscience/display_registry.py`.
2. It is covered by `src/med_autoscience/display_schema_contract.py`.
3. `src/med_autoscience/controllers/display_surface_materialization.py` can materialize it from the registered input schema.
4. Its output is checked by the registered QC profile in `src/med_autoscience/display_layout_qc.py`, or by the registered table/shell contract.
5. The resulting catalog entry survives publication-surface and submission-minimal validation.

This definition is intentionally stricter than "present in a catalog" or "listed in a planning document".

## Source Of Truth

The audited source files are:

- `src/med_autoscience/display_registry.py`
  - Official registry of evidence figures, illustration shells, and table shells.
- `src/med_autoscience/display_schema_contract.py`
  - Official schema classes and input-schema field contracts.
- `src/med_autoscience/controllers/display_surface_materialization.py`
  - Official materialization path from payload to exported surface.
- `src/med_autoscience/display_layout_qc.py`
  - Official layout QC engine for publication-facing figures.
- `src/med_autoscience/controllers/medical_publication_surface.py`
  - Official manuscript-safety scan and catalog contract enforcement layer.
- `src/med_autoscience/controllers/submission_minimal.py`
  - Official submission packaging consumer for figure/table metadata.

## Current Audited Coverage

Current implemented display inventory:

- Evidence figure classes: `8`
- Implemented evidence figure templates: `20`
- Illustration shells: `1`
- Table shells: `3`
- Total implemented display templates: `24`

### Evidence Classes

| Class | Implemented Templates | Input Schemas | Primary QC Profiles |
| --- | ---: | --- | --- |
| Prediction Performance | 3 | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` |
| Clinical Utility | 2 | `binary_prediction_curve_inputs_v1`, `time_to_event_decision_curve_inputs_v1` | `publication_evidence_curve`, `publication_decision_curve` |
| Time-to-Event | 5 | `binary_prediction_curve_inputs_v1`, `time_to_event_grouped_inputs_v1`, `time_to_event_discrimination_calibration_inputs_v1` | `publication_survival_curve`, `publication_evidence_curve` |
| Data Geometry | 3 | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` |
| Matrix Pattern | 3 | `heatmap_group_comparison_inputs_v1`, `correlation_heatmap_inputs_v1`, `clustered_heatmap_inputs_v1` | `publication_heatmap` |
| Effect Estimate | 2 | `forest_effect_inputs_v1` | `publication_forest_plot` |
| Model Explanation | 1 | `shap_summary_inputs_v1` | `publication_shap_summary` |
| Generalizability | 1 | `multicenter_generalizability_inputs_v1` | `publication_multicenter_overview` |

### Publication Shell Layer

| Kind | Implemented Templates | Input Schemas | Contract Gate |
| --- | ---: | --- | --- |
| Illustration Shell | 1 | `cohort_flow_shell_inputs_v1` | shell profile + catalog contract |
| Table Shell | 3 | `baseline_characteristics_schema_v1`, `time_to_event_performance_summary_v1`, `clinical_interpretation_summary_v1` | table profile + catalog contract |

## Eight-Class Audit Map

### 1. Prediction Performance

Templates:

- `roc_curve_binary`
- `pr_curve_binary`
- `calibration_curve_binary`

Audit purpose:

- Binary-outcome discrimination and calibration evidence.
- Curve payloads remain on the audited numeric surface rather than free-text captions or ad hoc plotting code.

Authoritative contract:

- Input schema: `binary_prediction_curve_inputs_v1`
- Renderer family: `r_ggplot2`
- QC: `publication_evidence_curve`

### 2. Clinical Utility

Templates:

- `decision_curve_binary`
- `time_to_event_decision_curve`

Audit purpose:

- Clinical decision-threshold evidence for binary and time-to-event settings.

Authoritative contract:

- Input schemas: `binary_prediction_curve_inputs_v1`, `time_to_event_decision_curve_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC: `publication_evidence_curve`, `publication_decision_curve`

### 3. Time-to-Event

Templates:

- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`
- `time_dependent_roc_horizon`
- `time_to_event_discrimination_calibration_panel`
- `time_to_event_risk_group_summary`

Audit purpose:

- Grouped survival separation, event accumulation, fixed-horizon discrimination, grouped calibration, and risk-group summary views.

Authoritative contract:

- Input schemas: `binary_prediction_curve_inputs_v1`, `time_to_event_grouped_inputs_v1`, `time_to_event_discrimination_calibration_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC: `publication_survival_curve`, `publication_evidence_curve`

### 4. Data Geometry

Templates:

- `umap_scatter_grouped`
- `pca_scatter_grouped`
- `tsne_scatter_grouped`

Audit purpose:

- Structured latent-space or embedding evidence under grouped labeling.

Authoritative contract:

- Input schema: `embedding_grouped_inputs_v1`
- Renderer family: `r_ggplot2`
- QC: `publication_embedding_scatter`

### 5. Matrix Pattern

Templates:

- `heatmap_group_comparison`
- `correlation_heatmap`
- `clustered_heatmap`

Audit purpose:

- Group contrast matrices, symmetric correlation structure, and externally fixed clustered ordering.

Authoritative contract:

- Input schemas: `heatmap_group_comparison_inputs_v1`, `correlation_heatmap_inputs_v1`, `clustered_heatmap_inputs_v1`
- Renderer family: `r_ggplot2`
- QC: `publication_heatmap`

### 6. Effect Estimate

Templates:

- `forest_effect_main`
- `subgroup_forest`

Audit purpose:

- Publication-facing interval estimate display for prespecified predictors or subgroups.

Authoritative contract:

- Input schema: `forest_effect_inputs_v1`
- Renderer family: `r_ggplot2`
- QC: `publication_forest_plot`

### 7. Model Explanation

Templates:

- `shap_summary_beeswarm`

Audit purpose:

- Ranked feature-attribution summary under controlled row and point geometry.

Authoritative contract:

- Input schema: `shap_summary_inputs_v1`
- Renderer family: `python`
- QC: `publication_shap_summary`

### 8. Generalizability

Templates:

- `multicenter_generalizability_overview`

Audit purpose:

- Center-level transportability and interval alignment under audited sample-size and estimate panels.

Authoritative contract:

- Input schema: `multicenter_generalizability_inputs_v1`
- Renderer family: `python`
- QC: `publication_multicenter_overview`

## Publication Shell And Table Audit Map

### Illustration Shell

- `cohort_flow_figure`
  - Input schema: `cohort_flow_shell_inputs_v1`
  - Required exports: `png`, `svg`
  - Role: trial-style or cohort-entry audit figure

### Table Shells

- `table1_baseline_characteristics`
  - Input schema: `baseline_characteristics_schema_v1`
  - Required exports: `csv`, `md`
- `table2_time_to_event_performance_summary`
  - Input schema: `time_to_event_performance_summary_v1`
  - Required exports: `md`
- `table3_clinical_interpretation_summary`
  - Input schema: `clinical_interpretation_summary_v1`
  - Required exports: `md`
  - Additional publication-surface rule: the markdown table body is scanned for forbidden engineering or tooling language, because interpretation text must be manuscript-safe even when the catalog title/caption is clean.

## Input Schema Contract Rules

All audited schemas share the same enforcement philosophy:

1. The top-level schema identifier must match the registered template family.
2. Required display fields must be explicit and non-empty.
3. Required collections must be non-empty when the schema defines them.
4. Length-matched numeric arrays must remain length-matched after validation.
5. Interval-based templates must satisfy `lower <= estimate <= upper`.
6. Registered renderers and QC profiles must match the registry entry exactly.
7. Required export formats must be present in the catalog entry that reaches publication or submission packaging.

The exhaustive per-schema field matrix is maintained in [medical_display_template_catalog.md](./medical_display_template_catalog.md).

## Renderer And QC Boundary

The system does not treat plotting as unconstrained "free generation".

Every audited template is bound to:

- one registered renderer family
- one registered input schema
- one registered QC profile or shell/table contract
- one registered export set

This means the plotting path is constrained before, during, and after rendering:

1. Before rendering:
   - the payload must pass the registered schema validator
2. During rendering:
   - the template can only go through its registered renderer family
3. After rendering:
   - the figure must emit a layout sidecar that satisfies the registered QC profile
   - tables and shells must satisfy the registered catalog/export contract

## Publication Style Governance

Publication-facing figure appearance is no longer treated as a private template concern.

- `paper/publication_style_profile.json` is the article-level visual source of truth.
- `paper/display_overrides.json` is the structured figure-level adjustment layer.
- Templates remain the audited lower bound, but they do not cap manuscript-facing expression when the formal style and override contracts require a clearer presentation.

This keeps visual consistency at the paper level while preserving a formal route for figure-specific correction.

## Readability Audit

Layout integrity alone is not sufficient for publication release.

A figure fails readability audit when it technically renders but does not communicate the intended manuscript-facing signal, such as:

- risk-group separation that remains visually compressed
- threshold-region utility that is not meaningfully distinguishable
- grouped or panelized evidence that is present but not interpretable at publication surface

Readability failure is a blocking audit outcome. The required correction path is:

1. adjust `display_overrides.json`
2. adjust `publication_style_profile.json`
3. update the registered renderer or schema contract if the audited inputs are still insufficient

The gate does not silently repair a failed figure after export.

## Change Protocol

When adding a new display template, the minimum audited change set is:

1. Register the template in `display_registry.py`
2. Add or extend the corresponding input schema contract in `display_schema_contract.py`
3. Materialize it in `display_surface_materialization.py`
4. Attach the correct layout-QC or shell/table contract
5. Add tests for:
   - registry/schema coverage
   - materialization
   - QC
   - CLI
   - publication-surface policy if wording or export behavior changes
   - submission-minimal metadata preservation if catalog semantics change
6. Refresh the generated catalog guide
7. Update this audit guide when the class map, completion count, or audit boundary changes

## Audit Use

Use this guide as the stable human-facing entry point. Use the generated catalog for exhaustive field-by-field lookup. If the two ever disagree, the source-of-truth Python files win and both guides must be updated in the same change.
