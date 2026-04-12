# Medical Display Audit Guide

This guide is the stable, human-auditable view of the medical display system in `med-autoscience`.

This file is the engineering audit surface, not the top-level product roadmap taxonomy.

Use [medical_display_family_roadmap.md](./medical_display_family_roadmap.md) when the goal is to answer:

- which paper-facing evidence families the platform should eventually cover;
- how the original `A-H` families define the long-horizon display north star;
- how real-paper-driven template expansion should be evaluated at the roadmap level.

Use this file when the goal is to answer:

- Which display classes are officially supported?
- Which figure and table templates are already materialized end to end?
- Which input schema contracts are enforced?
- Which renderer and layout-QC path is authoritative for each template?
- What must change together when a new display template is added?

This guide primarily documents the deterministic and auditable lower-bound layer.

For the exhaustive generated matrix, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).

## Scope

This guide covers the audited display surface only. A display counts as "implemented" here only when all of the following are true:

1. It is registered in `src/med_autoscience/display_registry.py`.
2. It is covered by `src/med_autoscience/display_schema_contract.py`.
3. `src/med_autoscience/controllers/display_surface_materialization.py` can materialize it from the registered input schema.
4. Its output is checked by the registered QC profile in `src/med_autoscience/display_layout_qc.py`, or by the registered table/shell contract.
5. The resulting catalog entry survives publication-surface and submission-minimal validation.

This definition is intentionally stricter than "present in a catalog" or "listed in a planning document".

It is also intentionally narrower than "publication-perfect under every visual judgment." Some paper-facing refinement work will still require an explicit AI-first visual review loop on top of the deterministic audited path.

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

## Visual QA And Canonical Surface Policy

- Renderer contracts, schema contracts, and layout QC define the **minimum audited quality floor** for publication-facing displays.
- Final visual quality is intentionally **AI-first above that floor**:
  - generate the figure from the audited pipeline;
  - review the real image, not just manifests or reports;
  - let AI/human visual audit call out concrete readability/presentation defects;
  - tighten renderer/QC/contract based on those defects.
- `publication-gate` / `submission_manifest` clear is therefore **not sufficient evidence** that a final figure is manuscript-ready.
- For anchor-paper and paper-owned delivery surfaces, keep the directory truth simple and stable:
  - `paper/` = authoritative manuscript-facing source surface;
  - `paper/figures/*.shell.json` / `paper/tables/*.shell.json` = display contracts and shells, not rendered deliverables;
  - `paper/figures/generated/` and `paper/tables/generated/` = authoritative generated display outputs;
  - `paper/submission_minimal/` = stable submission-package surface that should stay continuously refreshed;
  - `manuscript/` = the only human-facing final-delivery mirror;
  - `artifacts/` = auxiliary runtime/finalization evidence only, not duplicated figure/table lookup.
  - legacy top-level exports such as `paper/figures/Figure*.png|pdf|svg` and `paper/tables/Table*.csv|md` should be pruned once the catalog points to `generated/`.

## Current Paper-Proven Baseline (001/003)

The audited inventory is intentionally broader than the subset already proven against real papers.

Current paper-proven baseline:

- Paper families: `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event`, `H. Cohort and Study Design Evidence`
- Audit families: `Clinical Utility`, `Time-to-Event`, `Generalizability`, `Publication Shells / Tables`
- Template instances:
  - `fenggaolab.org.medical-display-core::binary_calibration_decision_curve_panel`
  - `fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel`
  - `fenggaolab.org.medical-display-core::time_to_event_risk_group_summary`
  - `fenggaolab.org.medical-display-core::time_to_event_decision_curve`
  - `fenggaolab.org.medical-display-core::multicenter_generalizability_overview`
  - `fenggaolab.org.medical-display-core::submission_graphical_abstract`

These are the first-priority cross-paper regression families because they have already exposed real paper-facing failure modes and then been reverified against `001/003` final figures.

## Current Audited Coverage

Current implemented display inventory:

- Evidence figure classes: `9`
- Implemented evidence figure templates: `40`
- Illustration shells: `2`
- Table shells: `5`
- Total implemented display templates: `47`

### Evidence Classes

| Class | Implemented Templates | Input Schemas | Primary QC Profiles |
| --- | ---: | --- | --- |
| Prediction Performance | 3 | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` |
| Clinical Utility | 4 | `binary_prediction_curve_inputs_v1`, `time_to_event_decision_curve_inputs_v1`, `time_to_event_threshold_governance_inputs_v1`, `binary_calibration_decision_curve_panel_inputs_v1` | `publication_evidence_curve`, `publication_binary_calibration_decision_curve`, `publication_decision_curve`, `publication_time_to_event_threshold_governance_panel` |
| Time-to-Event | 10 | `binary_prediction_curve_inputs_v1`, `risk_layering_monotonic_inputs_v1`, `time_dependent_roc_comparison_inputs_v1`, `time_to_event_landmark_performance_inputs_v1`, `time_to_event_multihorizon_calibration_inputs_v1`, `time_to_event_grouped_inputs_v1`, `time_to_event_stratified_cumulative_incidence_inputs_v1`, `time_to_event_discrimination_calibration_inputs_v1` | `publication_risk_layering_bars`, `publication_survival_curve`, `publication_evidence_curve`, `publication_landmark_performance_panel`, `publication_time_to_event_multihorizon_calibration_panel` |
| Data Geometry | 7 | `embedding_grouped_inputs_v1`, `celltype_signature_heatmap_inputs_v1`, `single_cell_atlas_overview_inputs_v1`, `spatial_niche_map_inputs_v1`, `trajectory_progression_inputs_v1` | `publication_embedding_scatter`, `publication_celltype_signature_panel`, `publication_single_cell_atlas_overview_panel`, `publication_spatial_niche_map_panel`, `publication_trajectory_progression_panel` |
| Matrix Pattern | 5 | `heatmap_group_comparison_inputs_v1`, `performance_heatmap_inputs_v1`, `correlation_heatmap_inputs_v1`, `clustered_heatmap_inputs_v1`, `gsva_ssgsea_heatmap_inputs_v1` | `publication_heatmap` |
| Effect Estimate | 2 | `forest_effect_inputs_v1` | `publication_forest_plot` |
| Model Explanation | 6 | `shap_summary_inputs_v1`, `shap_bar_importance_inputs_v1`, `shap_dependence_panel_inputs_v1`, `shap_waterfall_local_explanation_panel_inputs_v1`, `shap_force_like_summary_panel_inputs_v1`, `partial_dependence_ice_panel_inputs_v1` | `publication_shap_summary`, `publication_shap_bar_importance`, `publication_shap_dependence_panel`, `publication_shap_waterfall_local_explanation_panel`, `publication_shap_force_like_summary_panel`, `publication_partial_dependence_ice_panel` |
| Model Audit | 1 | `model_complexity_audit_panel_inputs_v1` | `publication_model_complexity_audit` |
| Generalizability | 2 | `multicenter_generalizability_inputs_v1`, `generalizability_subgroup_composite_inputs_v1` | `publication_multicenter_overview`, `publication_generalizability_subgroup_composite_panel` |

### Publication Shell Layer

| Kind | Implemented Templates | Input Schemas | Contract Gate |
| --- | ---: | --- | --- |
| Illustration Shell | 2 | `cohort_flow_shell_inputs_v1`, `submission_graphical_abstract_inputs_v1` | shell profile + catalog contract |
| Table Shell | 5 | `baseline_characteristics_schema_v1`, `time_to_event_performance_summary_v1`, `clinical_interpretation_summary_v1`, `performance_summary_table_generic_v1`, `grouped_risk_event_summary_table_v1` | table profile + catalog contract |

## Current Audit-Family Map

The audit families below are the current engineering governance view.

They are intentionally not the same thing as the roadmap-level `A-H` paper families:

- roadmap families answer manuscript-facing evidence questions;
- audit families answer renderer, schema, QC, and materialization governance questions.

That distinction is intentional and should be preserved.

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
- `binary_calibration_decision_curve_panel`
- `time_to_event_threshold_governance_panel`
- `time_to_event_decision_curve`

Audit purpose:

- Clinical decision-threshold evidence for binary and time-to-event settings, including structured threshold cards and grouped survival-calibration governance.

Authoritative contract:

- Input schemas: `binary_prediction_curve_inputs_v1`, `binary_calibration_decision_curve_panel_inputs_v1`, `time_to_event_threshold_governance_inputs_v1`, `time_to_event_decision_curve_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC: `publication_evidence_curve`, `publication_binary_calibration_decision_curve`, `publication_decision_curve`, `publication_time_to_event_threshold_governance_panel`

### 3. Time-to-Event

Templates:

- `risk_layering_monotonic_bars`
- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`
- `time_dependent_roc_horizon`
- `time_dependent_roc_comparison_panel`
- `time_to_event_landmark_performance_panel`
- `time_to_event_multihorizon_calibration_panel`
- `time_to_event_stratified_cumulative_incidence_panel`
- `time_to_event_discrimination_calibration_panel`
- `time_to_event_risk_group_summary`

Audit purpose:

- Risk-layer stratification, grouped survival separation, event accumulation, fixed-horizon discrimination, landmark/time-slice performance governance, multi-window ROC comparison, stratified cumulative-incidence panels, grouped calibration at one or multiple horizons, and risk-group summary views.

Authoritative contract:

- Input schemas: `binary_prediction_curve_inputs_v1`, `risk_layering_monotonic_inputs_v1`, `time_dependent_roc_comparison_inputs_v1`, `time_to_event_landmark_performance_inputs_v1`, `time_to_event_multihorizon_calibration_inputs_v1`, `time_to_event_grouped_inputs_v1`, `time_to_event_stratified_cumulative_incidence_inputs_v1`, `time_to_event_discrimination_calibration_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC: `publication_risk_layering_bars`, `publication_survival_curve`, `publication_evidence_curve`, `publication_landmark_performance_panel`, `publication_time_to_event_multihorizon_calibration_panel`

### 4. Data Geometry

Templates:

- `umap_scatter_grouped`
- `pca_scatter_grouped`
- `tsne_scatter_grouped`
- `celltype_signature_heatmap`
- `single_cell_atlas_overview_panel`
- `spatial_niche_map_panel`
- `trajectory_progression_panel`

Audit purpose:

- Structured latent-space, tissue-coordinate niche, atlas, or trajectory-progression evidence under grouped labeling, including composite panels that must keep declared niche/state/branch vocabularies, composition summaries, pseudotime bins, and marker-program heatmap grids fail-closed together.

Authoritative contract:

- Input schemas: `embedding_grouped_inputs_v1`, `celltype_signature_heatmap_inputs_v1`, `single_cell_atlas_overview_inputs_v1`, `spatial_niche_map_inputs_v1`, `trajectory_progression_inputs_v1`
- Renderer families: `r_ggplot2`, `python`
- QC: `publication_embedding_scatter`, `publication_celltype_signature_panel`, `publication_single_cell_atlas_overview_panel`, `publication_spatial_niche_map_panel`, `publication_trajectory_progression_panel`

### 5. Matrix Pattern

Templates:

- `heatmap_group_comparison`
- `performance_heatmap`
- `correlation_heatmap`
- `clustered_heatmap`
- `gsva_ssgsea_heatmap`

Audit purpose:

- Group contrast matrices, audited performance grids, symmetric correlation structure, externally fixed clustered ordering, and omics-native GSVA/ssGSEA program heatmaps.

Authoritative contract:

- Input schemas: `heatmap_group_comparison_inputs_v1`, `performance_heatmap_inputs_v1`, `correlation_heatmap_inputs_v1`, `clustered_heatmap_inputs_v1`, `gsva_ssgsea_heatmap_inputs_v1`
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
- `shap_bar_importance`
- `shap_dependence_panel`
- `shap_waterfall_local_explanation_panel`
- `shap_force_like_summary_panel`
- `partial_dependence_ice_panel`

Audit purpose:

- Ranked feature-attribution summary, bounded global importance overview, multi-panel dependence explanation, patient-level additive waterfall paths, bounded force-like representative-case summaries, and bounded PDP+ICE panels under controlled point geometry, shared legend/colorbar governance, explicit zero/reference guides, directional positive/negative contribution lanes, and deterministic panel-level contract reconciliation.

Authoritative contract:

- Input schemas: `shap_summary_inputs_v1`, `shap_bar_importance_inputs_v1`, `shap_dependence_panel_inputs_v1`, `shap_waterfall_local_explanation_panel_inputs_v1`, `shap_force_like_summary_panel_inputs_v1`, `partial_dependence_ice_panel_inputs_v1`
- Renderer family: `python`
- QC: `publication_shap_summary`, `publication_shap_bar_importance`, `publication_shap_dependence_panel`, `publication_shap_waterfall_local_explanation_panel`, `publication_shap_force_like_summary_panel`, `publication_partial_dependence_ice_panel`

### 8. Model Audit

Templates:

- `model_complexity_audit_panel`

Audit purpose:

- Controlled multi-panel audit of metric coherence, bounded complexity, and coefficient/domain stability without reverting to free-form plotting.

Authoritative contract:

- Input schema: `model_complexity_audit_panel_inputs_v1`
- Renderer family: `python`
- QC: `publication_model_complexity_audit`

### 9. Generalizability

Templates:

- `multicenter_generalizability_overview`
- `generalizability_subgroup_composite_panel`

Audit purpose:

- Center-level transportability plus bounded subgroup interval robustness under audited sample-size, cohort-level metric, and interval-estimate panels.

Authoritative contract:

- Input schemas: `multicenter_generalizability_inputs_v1`, `generalizability_subgroup_composite_inputs_v1`
- Renderer family: `python`
- QC: `publication_multicenter_overview`, `publication_generalizability_subgroup_composite_panel`

## Publication Shell And Table Audit Map

### Illustration Shells

- `fenggaolab.org.medical-display-core::cohort_flow_figure`
  - Input schema: `cohort_flow_shell_inputs_v1`
  - Required exports: `png`, `svg`
  - Role: trial-style or cohort-entry audit figure
- `fenggaolab.org.medical-display-core::submission_graphical_abstract`
  - Input schema: `submission_graphical_abstract_inputs_v1`
  - Required exports: `png`, `svg`
  - Role: paper-facing graphical-abstract shell routed through the audited catalog and QC path

### Table Shells

- `fenggaolab.org.medical-display-core::table1_baseline_characteristics`
  - Input schema: `baseline_characteristics_schema_v1`
  - Required exports: `csv`, `md`
- `fenggaolab.org.medical-display-core::table2_time_to_event_performance_summary`
  - Input schema: `time_to_event_performance_summary_v1`
  - Required exports: `md`
- `fenggaolab.org.medical-display-core::table3_clinical_interpretation_summary`
  - Input schema: `clinical_interpretation_summary_v1`
  - Required exports: `md`
  - Additional publication-surface rule: the markdown table body is scanned for forbidden engineering or tooling language, because interpretation text must be manuscript-safe even when the catalog title/caption is clean.
- `fenggaolab.org.medical-display-core::performance_summary_table_generic`
  - Input schema: `performance_summary_table_generic_v1`
  - Required exports: `csv`, `md`
- `fenggaolab.org.medical-display-core::grouped_risk_event_summary_table`
  - Input schema: `grouped_risk_event_summary_table_v1`
  - Required exports: `csv`, `md`

## Cross-Paper Golden Regression Priority

Phase 1 hardening should not start from abstract template counts. The first regression lane should stay anchored on the real-paper-used families already exercised by `001/003`.

### A/B curve-panel families

- `fenggaolab.org.medical-display-core::binary_calibration_decision_curve_panel`
- `fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel`
- `fenggaolab.org.medical-display-core::time_to_event_risk_group_summary`
- `fenggaolab.org.medical-display-core::time_to_event_decision_curve`
- lower-bound focus: title policy, blank-zone annotation placement, calibration axis-window fit, grouped-separation readability, and landmark/time-slice regression semantics

### H generalizability and shell layer

- `fenggaolab.org.medical-display-core::multicenter_generalizability_overview`
- `fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel`
- `fenggaolab.org.medical-display-core::submission_graphical_abstract`
- lower-bound focus: panel-label anchoring, outboard cohort/subgroup label containment, legend title/label semantics, tick-label readability, arrow-lane placement, and catalog/package routing consistency

### D/E/G composite atlas lane

- `fenggaolab.org.medical-display-core::celltype_signature_heatmap`
- lower-bound focus: embedding-group and declared heatmap-column alignment, complete row/column coverage without duplicate coordinates, explicit score-method provenance, and stable legend/colorbar anchoring for the composite panel

### F local explanation lane

- `fenggaolab.org.medical-display-core::shap_dependence_panel`
- `fenggaolab.org.medical-display-core::shap_waterfall_local_explanation_panel`
- `fenggaolab.org.medical-display-core::shap_force_like_summary_panel`
- `fenggaolab.org.medical-display-core::partial_dependence_ice_panel`
- lower-bound focus: panel-feature uniqueness, finite point coordinates, zero-line containment, shared colorbar/legend governance, panel-label anchoring, contribution direction consistency, positive/negative lane containment, prediction-marker directionality, deterministic `baseline + contributions = prediction` reconciliation, and in-panel PDP/ICE/reference-line containment with aligned reference-label semantics for manuscript-facing local explanation panels

### AI-first visual audit lane

- deterministic QC keeps ownership of repeatable lower-bound failures;
- AI-first visual critique remains mandatory for paper-facing issues that are still too context-sensitive to encode cleanly in deterministic rules;
- `gate clear != final figure QA clear` remains the governing rule when deciding whether a family is mature enough for real-paper reuse.

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

Use this guide as the stable human-facing entry point. Use the generated catalog for exhaustive field-by-field lookup. If the two ever disagree, the source-of-truth Python files win and both documents must be updated in the same change.
