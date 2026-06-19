# Medical Display Audit Guide

Owner: `MedAutoScience`
Purpose: `current_medical_display_audit_boundary`
State: `active_support`
Machine boundary: Human-readable delivery contract support only. Enforceable truth remains in source, template descriptors, machine-readable contracts, generated artifacts, layout sidecars, tests, audit receipts, and owner receipts.

This guide defines the current deterministic lower-bound audit surface for MAS medical display work. It is narrower than the long-term roadmap and narrower than final publication judgment.

## What Counts As Current

A display counts as current implemented inventory only when it is present in the active pack descriptors and can be reached through the current registry/schema/materialization/QC path.

Current `fenggaolab.org.medical-display-core` inventory:

- `55` evidence figures, all `r_ggplot2` subprocess renderers;
- `0` Python evidence figures;
- `4` Python illustration shells for design / flow / graphical-abstract composition;
- `7` table shells;
- `32` retired Python evidence IDs retained only in `renderer_migration_ledger.json` / `canonical_template_catalog.json` as provenance.

Retired Python evidence IDs are not hidden defaults, explicit-request inventory, Gallery comparison cards, or runtime fallback templates.

## Source Of Truth

- `display-packs/fenggaolab.org.medical-display-core/templates/*/template.toml`
- `display-packs/fenggaolab.org.medical-display-core/canonical_template_catalog.json`
- `display-packs/fenggaolab.org.medical-display-core/renderer_migration_ledger.json`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization/`
- `src/med_autoscience/display_layout_qc/`
- generated Gallery manifest under `outputs/display-pack-gallery/ggplot2_template_reference_assets/gallery_manifest.json`

The generated catalog is [medical_display_template_catalog.md](../catalogs/medical_display_template_catalog.md). The human Gallery is [ggplot2_template_reference.md](../examples/ggplot2_template_reference.md) and `ggplot2_template_gallery.pdf`.

## Renderer Policy

| Surface | Renderer policy | Authority boundary |
| --- | --- | --- |
| Evidence figures | R/ggplot2 first; current pack has no Python evidence | May display data/statistical evidence only from structured payloads and renderer/QC contracts |
| Illustration shells | Python/SVG/composition allowed | May express workflow, cohort flow, graphical abstract, or design context; cannot carry statistical evidence authority |
| Table shells | Structured table renderer | May materialize tabular display artifacts; cannot sign publication readiness |

Future Python evidence may re-enter only after documented advantage over the R/ggplot2 baseline, checked-in current descriptors, layout/QC/audit evidence, and explicit user-visible current-pack status.

## Current Audit Families

| Family | Current templates |
| --- | --- |
| Prediction performance | `roc_curve_binary`, `pr_curve_binary`, `calibration_curve_binary` |
| Clinical utility | `decision_curve_binary`, `clinical_impact_curve_binary`, `binary_calibration_decision_curve_panel`, `time_to_event_threshold_governance_panel`, `time_to_event_decision_curve` |
| Time-to-event | `risk_layering_monotonic_bars`, `kaplan_meier_grouped`, `cumulative_incidence_grouped`, `time_dependent_roc_horizon`, `time_dependent_roc_comparison_panel`, `time_to_event_landmark_performance_panel`, `time_to_event_multihorizon_calibration_panel`, `time_to_event_stratified_cumulative_incidence_panel`, `time_to_event_discrimination_calibration_panel`, `time_to_event_risk_group_summary` |
| Data geometry | `umap_scatter_grouped`, `pca_scatter_grouped`, `tsne_scatter_grouped`, `phate_scatter_grouped`, `diffusion_map_scatter_grouped`, `celltype_signature_heatmap`, `omics_volcano_panel` |
| Matrix pattern | `heatmap_group_comparison`, `performance_heatmap`, `confusion_matrix_heatmap_binary`, `correlation_heatmap`, `clustered_heatmap`, `gsva_ssgsea_heatmap`, `pathway_enrichment_dotplot_panel`, `celltype_marker_dotplot_panel`, `oncoplot_mutation_landscape_panel`, `cnv_recurrence_summary_panel`, `genomic_alteration_landscape_panel`, `genomic_alteration_consequence_panel`, `genomic_alteration_multiomic_consequence_panel`, `genomic_alteration_pathway_integrated_composite_panel`, `genomic_program_governance_summary_panel` |
| Effect estimate | `forest_effect_main`, `subgroup_forest`, `multivariable_forest`, `compact_effect_estimate_panel`, `coefficient_path_panel`, `broader_heterogeneity_summary_panel`, `interaction_effect_summary_panel` |
| Model explanation | `shap_summary_beeswarm`, `shap_bar_importance`, `shap_multicohort_importance_panel`, `shap_dependence_panel`, `shap_waterfall_local_explanation_panel`, `shap_force_like_summary_panel` |
| Model audit | `model_complexity_audit_panel` |
| Generalizability | `generalizability_subgroup_composite_panel` |
| Illustration shells | `cohort_flow_figure`, `submission_graphical_abstract`, `workflow_fact_sheet_panel`, `design_evidence_composite_shell` |
| Table shells | `table1_baseline_characteristics`, `table2_phenotype_gap_summary`, `table3_transition_site_support_summary`, `table2_time_to_event_performance_summary`, `table3_clinical_interpretation_summary`, `performance_summary_table_generic`, `grouped_risk_event_summary_table` |

## Visual QA Boundary

Renderer contracts, schema contracts, layout QC and Gallery generation prove only a minimum quality floor. A final manuscript figure still needs:

1. real paper payload and data refs;
2. render artifacts plus layout sidecar;
3. visual audit on the actual image;
4. concrete renderer/QC/style hardening when defects are found;
5. MAS owner / publication gate receipt for any readiness claim.

Green tests, Gallery generation, style-profile hash, visual-audit clear, display lock, or OPL smoke receipt cannot authorize publication readiness by themselves.

## External Exemplar Intake

External galleries, blogs, packages, and paper examples are read-only learning sources. They can justify a template gap, style rule, or audit check. They do not become current MAS display capabilities until the change lands through descriptor, schema, renderer, QC, catalog, Gallery/readback, and tests.
