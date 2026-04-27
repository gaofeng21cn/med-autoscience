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

## Current Paper-Proven Baseline (001/003)

The current audited inventory is broader than the subset already proven against real papers.

- Paper families: `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event`, `H. Cohort and Study Design Evidence`
- Audit families: `Clinical Utility`, `Time-to-Event`, `Generalizability`, `Publication Shells and Tables`
- Template instances: `fenggaolab.org.medical-display-core::binary_calibration_decision_curve_panel`, `fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel`, `fenggaolab.org.medical-display-core::time_to_event_risk_group_summary`, `fenggaolab.org.medical-display-core::time_to_event_decision_curve`, `fenggaolab.org.medical-display-core::multicenter_generalizability_overview`, `fenggaolab.org.medical-display-core::submission_graphical_abstract`
- Cross-paper golden regression priority: title policy, annotation placement, panel-label/header-band anchoring, grouped-separation readability, landmark/time-slice semantics, graphical-abstract arrow lanes, calibration axis-window fit, and multicenter legend title/label + tick-label readability

## Template Classes

### Prediction Performance

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::roc_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | ROC Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::pr_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Precision-Recall Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::calibration_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Calibration Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |

### Clinical Utility

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::decision_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Decision Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::clinical_impact_curve_binary` | `evidence_figure` | `A. Predictive Performance and Decision` | Clinical Impact Curve (Binary Outcome) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::binary_calibration_decision_curve_panel` | `evidence_figure` | `A. Predictive Performance and Decision` | Binary Calibration and Decision Curve Panel | `python` | `binary_calibration_decision_curve_panel_inputs_v1` | `publication_binary_calibration_decision_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_threshold_governance_panel` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Time-to-Event Threshold Governance Panel | `python` | `time_to_event_threshold_governance_inputs_v1` | `publication_time_to_event_threshold_governance_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_decision_curve` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Decision Curve (Time-to-Event Horizon) | `python` | `time_to_event_decision_curve_inputs_v1` | `publication_decision_curve` | `png`, `pdf` |

### Time-to-Event

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::risk_layering_monotonic_bars` | `evidence_figure` | `B. Survival and Time-to-Event` | Monotonic Risk Layering Bars | `python` | `risk_layering_monotonic_inputs_v1` | `publication_risk_layering_bars` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_dependent_roc_horizon` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Time-Dependent ROC (Horizon) | `r_ggplot2` | `binary_prediction_curve_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_dependent_roc_comparison_panel` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Time-Dependent ROC Comparison Panel | `python` | `time_dependent_roc_comparison_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_landmark_performance_panel` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Landmark Performance Summary Panel (Time-to-Event) | `python` | `time_to_event_landmark_performance_inputs_v1` | `publication_landmark_performance_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_multihorizon_calibration_panel` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Multi-Horizon Grouped Calibration Panel (Time-to-Event) | `python` | `time_to_event_multihorizon_calibration_inputs_v1` | `publication_time_to_event_multihorizon_calibration_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::kaplan_meier_grouped` | `evidence_figure` | `B. Survival and Time-to-Event` | Kaplan-Meier Curve (Grouped) | `r_ggplot2` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::cumulative_incidence_grouped` | `evidence_figure` | `B. Survival and Time-to-Event` | Cumulative Incidence Curve (Grouped) | `r_ggplot2` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_stratified_cumulative_incidence_panel` | `evidence_figure` | `B. Survival and Time-to-Event` | Stratified Cumulative Incidence Panel | `python` | `time_to_event_stratified_cumulative_incidence_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel` | `evidence_figure` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Validation Discrimination and Grouped Calibration (Time-to-Event) | `python` | `time_to_event_discrimination_calibration_inputs_v1` | `publication_evidence_curve` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::time_to_event_risk_group_summary` | `evidence_figure` | `B. Survival and Time-to-Event` | Risk-Group Summary (Time-to-Event) | `python` | `time_to_event_grouped_inputs_v1` | `publication_survival_curve` | `png`, `pdf` |

### Data Geometry

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::umap_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | UMAP Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::pca_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | PCA Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::phate_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | PHATE Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::tsne_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | t-SNE Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::diffusion_map_scatter_grouped` | `evidence_figure` | `D. Representation Structure and Data Geometry` | Diffusion Map Scatter (Grouped) | `r_ggplot2` | `embedding_grouped_inputs_v1` | `publication_embedding_scatter` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::celltype_signature_heatmap` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Cell-Type Embedding and Signature Heatmap | `python` | `celltype_signature_heatmap_inputs_v1` | `publication_celltype_signature_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::single_cell_atlas_overview_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Single-Cell Atlas Overview Panel | `python` | `single_cell_atlas_overview_inputs_v1` | `publication_single_cell_atlas_overview_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::atlas_spatial_bridge_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Atlas-Spatial Bridge Panel | `python` | `atlas_spatial_bridge_panel_inputs_v1` | `publication_atlas_spatial_bridge_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::spatial_niche_map_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Spatial Niche Map Panel | `python` | `spatial_niche_map_inputs_v1` | `publication_spatial_niche_map_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::trajectory_progression_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Trajectory Progression Panel | `python` | `trajectory_progression_inputs_v1` | `publication_trajectory_progression_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_storyboard_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Atlas-Spatial Trajectory Storyboard Panel | `python` | `atlas_spatial_trajectory_storyboard_inputs_v1` | `publication_atlas_spatial_trajectory_storyboard_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_density_coverage_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Atlas-Spatial Trajectory Density Coverage Panel | `python` | `atlas_spatial_trajectory_density_coverage_panel_inputs_v1` | `publication_atlas_spatial_trajectory_density_coverage_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_context_support_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Atlas-Spatial Trajectory Context Support Panel | `python` | `atlas_spatial_trajectory_context_support_panel_inputs_v1` | `publication_atlas_spatial_trajectory_context_support_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_multimanifold_context_support_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Atlas-Spatial Trajectory Multimanifold Context Support Panel | `python` | `atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1` | `publication_atlas_spatial_trajectory_multimanifold_context_support_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::omics_volcano_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Omics Volcano Panel | `python` | `omics_volcano_panel_inputs_v1` | `publication_omics_volcano_panel` | `png`, `pdf` |

### Matrix Pattern

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::heatmap_group_comparison` | `evidence_figure` | `E. Feature Pattern and Matrix` | Heatmap (Group Comparison) | `r_ggplot2` | `heatmap_group_comparison_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::performance_heatmap` | `evidence_figure` | `B. Survival and Time-to-Event`, `E. Feature Pattern and Matrix` | Performance Heatmap | `r_ggplot2` | `performance_heatmap_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::confusion_matrix_heatmap_binary` | `evidence_figure` | `A. Predictive Performance and Decision`, `E. Feature Pattern and Matrix` | Binary Confusion Matrix Heatmap | `r_ggplot2` | `confusion_matrix_heatmap_binary_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::correlation_heatmap` | `evidence_figure` | `E. Feature Pattern and Matrix` | Correlation Heatmap | `r_ggplot2` | `correlation_heatmap_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::clustered_heatmap` | `evidence_figure` | `E. Feature Pattern and Matrix` | Clustered Heatmap (Precomputed Ordering) | `r_ggplot2` | `clustered_heatmap_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::gsva_ssgsea_heatmap` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | GSVA/ssGSEA Heatmap | `r_ggplot2` | `gsva_ssgsea_heatmap_inputs_v1` | `publication_heatmap` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::pathway_enrichment_dotplot_panel` | `evidence_figure` | `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Pathway Enrichment Dotplot Panel | `python` | `pathway_enrichment_dotplot_panel_inputs_v1` | `publication_pathway_enrichment_dotplot_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::celltype_marker_dotplot_panel` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `E. Feature Pattern and Matrix`, `G. Bioinformatics and Omics Evidence` | Cell-Type Marker Dotplot Panel | `python` | `celltype_marker_dotplot_panel_inputs_v1` | `publication_celltype_marker_dotplot_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::oncoplot_mutation_landscape_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Oncoplot Mutation Landscape Panel | `python` | `oncoplot_mutation_landscape_panel_inputs_v1` | `publication_oncoplot_mutation_landscape_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::cnv_recurrence_summary_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | CNV Recurrence Summary Panel | `python` | `cnv_recurrence_summary_panel_inputs_v1` | `publication_cnv_recurrence_summary_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::genomic_alteration_landscape_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Alteration Landscape Panel | `python` | `genomic_alteration_landscape_panel_inputs_v1` | `publication_genomic_alteration_landscape_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::genomic_alteration_consequence_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Alteration Consequence Panel | `python` | `genomic_alteration_consequence_panel_inputs_v1` | `publication_genomic_alteration_consequence_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::genomic_alteration_multiomic_consequence_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Alteration Multiomic Consequence Panel | `python` | `genomic_alteration_multiomic_consequence_panel_inputs_v1` | `publication_genomic_alteration_multiomic_consequence_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::genomic_alteration_pathway_integrated_composite_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Alteration Pathway-Integrated Composite Panel | `python` | `genomic_alteration_pathway_integrated_composite_panel_inputs_v1` | `publication_genomic_alteration_pathway_integrated_composite_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::genomic_program_governance_summary_panel` | `evidence_figure` | `G. Bioinformatics and Omics Evidence` | Genomic Program Governance Summary Panel | `python` | `genomic_program_governance_summary_panel_inputs_v1` | `publication_genomic_program_governance_summary_panel` | `png`, `pdf` |

### Effect Estimate

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::forest_effect_main` | `evidence_figure` | `C. Effect Size and Heterogeneity` | Forest Plot (Main Effects) | `r_ggplot2` | `forest_effect_inputs_v1` | `publication_forest_plot` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::subgroup_forest` | `evidence_figure` | `C. Effect Size and Heterogeneity` | Forest Plot (Subgroup Effects) | `r_ggplot2` | `forest_effect_inputs_v1` | `publication_forest_plot` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::multivariable_forest` | `evidence_figure` | `C. Effect Size and Heterogeneity` | Forest Plot (Multivariable Model) | `r_ggplot2` | `forest_effect_inputs_v1` | `publication_forest_plot` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::compact_effect_estimate_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Compact Effect Estimate Panel | `python` | `compact_effect_estimate_panel_inputs_v1` | `publication_compact_effect_estimate_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::coefficient_path_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Coefficient Path Panel | `python` | `coefficient_path_panel_inputs_v1` | `publication_coefficient_path_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::broader_heterogeneity_summary_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Broader Heterogeneity Summary Panel | `python` | `broader_heterogeneity_summary_panel_inputs_v1` | `publication_broader_heterogeneity_summary_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::interaction_effect_summary_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Interaction Effect Summary Panel | `python` | `interaction_effect_summary_panel_inputs_v1` | `publication_interaction_effect_summary_panel` | `png`, `pdf` |

### Model Explanation

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::shap_summary_beeswarm` | `evidence_figure` | `F. Model Explanation` | SHAP Summary Beeswarm | `python` | `shap_summary_inputs_v1` | `publication_shap_summary` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_bar_importance` | `evidence_figure` | `F. Model Explanation` | SHAP Bar Importance Panel | `python` | `shap_bar_importance_inputs_v1` | `publication_shap_bar_importance` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_signed_importance_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Signed Importance Panel | `python` | `shap_signed_importance_panel_inputs_v1` | `publication_shap_signed_importance_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_multicohort_importance_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Multicohort Importance Panel | `python` | `shap_multicohort_importance_panel_inputs_v1` | `publication_shap_multicohort_importance_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_dependence_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Dependence Panel | `python` | `shap_dependence_panel_inputs_v1` | `publication_shap_dependence_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_waterfall_local_explanation_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Waterfall Local Explanation Panel | `python` | `shap_waterfall_local_explanation_panel_inputs_v1` | `publication_shap_waterfall_local_explanation_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_force_like_summary_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Force-like Summary Panel | `python` | `shap_force_like_summary_panel_inputs_v1` | `publication_shap_force_like_summary_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_grouped_local_explanation_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Grouped Local Explanation Panel | `python` | `shap_grouped_local_explanation_panel_inputs_v1` | `publication_shap_grouped_local_explanation_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_grouped_decision_path_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Grouped Decision Path Panel | `python` | `shap_grouped_decision_path_panel_inputs_v1` | `publication_shap_grouped_decision_path_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_multigroup_decision_path_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Multigroup Decision Path Panel | `python` | `shap_multigroup_decision_path_panel_inputs_v1` | `publication_shap_multigroup_decision_path_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::partial_dependence_ice_panel` | `evidence_figure` | `F. Model Explanation` | Partial Dependence and ICE Panel | `python` | `partial_dependence_ice_panel_inputs_v1` | `publication_partial_dependence_ice_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::partial_dependence_interaction_contour_panel` | `evidence_figure` | `F. Model Explanation` | Partial Dependence Interaction Contour Panel | `python` | `partial_dependence_interaction_contour_panel_inputs_v1` | `publication_partial_dependence_interaction_contour_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::partial_dependence_interaction_slice_panel` | `evidence_figure` | `F. Model Explanation` | Partial Dependence Interaction Slice Panel | `python` | `partial_dependence_interaction_slice_panel_inputs_v1` | `publication_partial_dependence_interaction_slice_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::partial_dependence_subgroup_comparison_panel` | `evidence_figure` | `F. Model Explanation` | Partial Dependence Subgroup Comparison Panel | `python` | `partial_dependence_subgroup_comparison_panel_inputs_v1` | `publication_partial_dependence_subgroup_comparison_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::accumulated_local_effects_panel` | `evidence_figure` | `F. Model Explanation` | Accumulated Local Effects Panel | `python` | `accumulated_local_effects_panel_inputs_v1` | `publication_accumulated_local_effects_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::feature_response_support_domain_panel` | `evidence_figure` | `F. Model Explanation` | Feature Response Support Domain Panel | `python` | `feature_response_support_domain_panel_inputs_v1` | `publication_feature_response_support_domain_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_grouped_local_support_domain_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Grouped Local Support-Domain Panel | `python` | `shap_grouped_local_support_domain_panel_inputs_v1` | `publication_shap_grouped_local_support_domain_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_multigroup_decision_path_support_domain_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Multigroup Decision Path Support-Domain Panel | `python` | `shap_multigroup_decision_path_support_domain_panel_inputs_v1` | `publication_shap_multigroup_decision_path_support_domain_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::shap_signed_importance_local_support_domain_panel` | `evidence_figure` | `F. Model Explanation` | SHAP Signed Importance Local Support-Domain Panel | `python` | `shap_signed_importance_local_support_domain_panel_inputs_v1` | `publication_shap_signed_importance_local_support_domain_panel` | `png`, `pdf` |

### Model Audit

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::model_complexity_audit_panel` | `evidence_figure` | `F. Model Explanation`, `H. Cohort and Study Design Evidence` | Model Complexity Audit Panel | `python` | `model_complexity_audit_panel_inputs_v1` | `publication_model_complexity_audit` | `png`, `pdf` |

### Generalizability

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel` | `evidence_figure` | `C. Effect Size and Heterogeneity`, `H. Cohort and Study Design Evidence` | Generalizability and Subgroup Composite Panel | `python` | `generalizability_subgroup_composite_inputs_v1` | `publication_generalizability_subgroup_composite_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::center_transportability_governance_summary_panel` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Center Transportability Governance Summary Panel | `python` | `center_transportability_governance_summary_panel_inputs_v1` | `publication_center_transportability_governance_summary_panel` | `png`, `pdf` |
| `fenggaolab.org.medical-display-core::multicenter_generalizability_overview` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Multicenter Generalizability Overview | `python` | `multicenter_generalizability_inputs_v1` | `publication_multicenter_overview` | `png`, `pdf` |

### Publication Shells and Tables

| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fenggaolab.org.medical-display-core::phenotype_gap_structure_figure` | `evidence_figure` | `D. Representation Structure and Data Geometry`, `H. Cohort and Study Design Evidence` | Phenotype Gap Structure Figure | `python` | `dpcc_phenotype_gap_structure_v1` | `publication_evidence_curve` | `png`, `pdf`, `svg` |
| `fenggaolab.org.medical-display-core::site_held_out_stability_figure` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Site-Held-Out Stability Figure | `python` | `dpcc_transition_site_support_v1` | `publication_survival_curve` | `png`, `pdf`, `svg` |
| `fenggaolab.org.medical-display-core::treatment_gap_alignment_figure` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Treatment Gap Alignment Figure | `python` | `dpcc_treatment_gap_alignment_v1` | `publication_evidence_curve` | `png`, `pdf`, `svg` |
| `fenggaolab.org.medical-display-core::treatment_shift_alignment_figure` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Treatment Shift Alignment Figure | `python` | `accepted_descriptive_display_data_v1` | `publication_result_display` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::practical_factor_dot_figure` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Practical Factor Dot Figure | `python` | `accepted_descriptive_display_data_v1` | `publication_result_display` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::preferred_class_sensitivity_figure` | `evidence_figure` | `H. Cohort and Study Design Evidence` | Preferred Class Sensitivity Figure | `python` | `accepted_descriptive_display_data_v1` | `publication_result_display` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::cohort_flow_figure` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Cohort Flow Figure | `python` | `cohort_flow_shell_inputs_v1` | `publication_illustration_flow` | `png`, `svg`, `pdf` |
| `fenggaolab.org.medical-display-core::submission_graphical_abstract` | `illustration_shell` | `A. Predictive Performance and Decision`, `H. Cohort and Study Design Evidence` | Submission Graphical Abstract | `python` | `submission_graphical_abstract_inputs_v1` | `submission_graphical_abstract` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::workflow_fact_sheet_panel` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Workflow Fact Sheet Panel | `python` | `workflow_fact_sheet_panel_inputs_v1` | `publication_workflow_fact_sheet_panel` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::design_evidence_composite_shell` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Design Evidence Composite Shell | `python` | `design_evidence_composite_shell_inputs_v1` | `publication_design_evidence_composite_shell` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::baseline_missingness_qc_panel` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Baseline Missingness QC Panel | `python` | `baseline_missingness_qc_panel_inputs_v1` | `publication_baseline_missingness_qc_panel` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::center_coverage_batch_transportability_panel` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Center Coverage Batch Transportability Panel | `python` | `center_coverage_batch_transportability_panel_inputs_v1` | `publication_center_coverage_batch_transportability_panel` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::transportability_recalibration_governance_panel` | `illustration_shell` | `H. Cohort and Study Design Evidence` | Transportability Recalibration Governance Panel | `python` | `transportability_recalibration_governance_panel_inputs_v1` | `publication_transportability_recalibration_governance_panel` | `png`, `svg` |
| `fenggaolab.org.medical-display-core::table1_baseline_characteristics` | `table_shell` | `H. Cohort and Study Design Evidence` | Table 1 Baseline Characteristics | `n/a` | `baseline_characteristics_schema_v1` | `publication_table_baseline` | `csv`, `md` |
| `fenggaolab.org.medical-display-core::table2_phenotype_gap_summary` | `table_shell` | `H. Cohort and Study Design Evidence` | Table 2 Phenotype Gap Summary | `n/a` | `phenotype_gap_summary_schema_v1` | `publication_table_interpretation` | `md` |
| `fenggaolab.org.medical-display-core::table3_transition_site_support_summary` | `table_shell` | `H. Cohort and Study Design Evidence` | Table 3 Transition Site Support Summary | `n/a` | `transition_site_support_summary_schema_v1` | `publication_table_interpretation` | `md` |
| `fenggaolab.org.medical-display-core::table2_time_to_event_performance_summary` | `table_shell` | `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event` | Table 2 Time-to-Event Performance Summary | `n/a` | `time_to_event_performance_summary_v1` | `publication_table_performance` | `md` |
| `fenggaolab.org.medical-display-core::table3_clinical_interpretation_summary` | `table_shell` | `A. Predictive Performance and Decision`, `H. Cohort and Study Design Evidence` | Table 3 Clinical Interpretation Summary | `n/a` | `clinical_interpretation_summary_v1` | `publication_table_interpretation` | `md` |
| `fenggaolab.org.medical-display-core::performance_summary_table_generic` | `table_shell` | `A. Predictive Performance and Decision` | Performance Summary Table (Generic) | `n/a` | `performance_summary_table_generic_v1` | `publication_table_performance` | `csv`, `md` |
| `fenggaolab.org.medical-display-core::grouped_risk_event_summary_table` | `table_shell` | `B. Survival and Time-to-Event` | Grouped Risk Event Summary Table | `n/a` | `grouped_risk_event_summary_table_v1` | `publication_table_interpretation` | `csv`, `md` |

## Input Schemas

### `accepted_descriptive_display_data_v1`

- Display kind: `evidence_figure`
- Display name: Accepted Descriptive Display Data
- Templates: `fenggaolab.org.medical-display-core::treatment_shift_alignment_figure`, `fenggaolab.org.medical-display-core::practical_factor_dot_figure`, `fenggaolab.org.medical-display-core::preferred_class_sensitivity_figure`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panels`
- Optional display fields: `paper_role`, `x_label`, `y_label`
- Required collection fields: `panels` -> `panel_id`, `title`, `x_label`, `y_label`, `marks`
- Optional collection fields: `panels` -> `annotation`
- Required nested collection fields: `panels.marks` -> `label`, `value`
- Optional nested collection fields: `panels.marks` -> `group`, `comparison_value`, `color`, `annotation`
- Additional constraints: `descriptive_displays_must_be_non_empty`, `descriptive_display_ids_must_be_unique`, `descriptive_panels_must_be_non_empty`, `descriptive_panel_ids_must_be_unique_within_display`, `descriptive_marks_must_be_non_empty`, `descriptive_mark_labels_must_be_unique_within_panel`, `descriptive_mark_values_must_be_finite_or_null_when_not_applicable`

### `binary_prediction_curve_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Binary Prediction Curves
- Templates: `fenggaolab.org.medical-display-core::roc_curve_binary`, `fenggaolab.org.medical-display-core::pr_curve_binary`, `fenggaolab.org.medical-display-core::calibration_curve_binary`, `fenggaolab.org.medical-display-core::decision_curve_binary`, `fenggaolab.org.medical-display-core::clinical_impact_curve_binary`, `fenggaolab.org.medical-display-core::time_dependent_roc_horizon`
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

### `time_dependent_roc_comparison_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-Dependent ROC Comparison Panel
- Templates: `fenggaolab.org.medical-display-core::time_dependent_roc_comparison_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `analysis_window_label`, `series`
- Optional collection fields: `panels` -> `annotation`, `time_horizon_months`, `reference_line`
- Required nested collection fields: `panels.series` -> `label`, `x`, `y`<br>`panels.reference_line` -> `x`, `y`
- Optional nested collection fields: `panels.reference_line` -> `label`
- Additional constraints: `time_dependent_roc_comparison_panels_must_be_non_empty`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_analysis_window_labels_must_be_non_empty`, `panel_series_must_be_non_empty`, `panel_series_labels_must_be_unique_within_panel`, `panel_series_label_sets_must_match_across_panels`, `panel_series_x_y_lengths_must_match`, `panel_series_values_must_be_finite`, `panel_reference_line_x_y_lengths_must_match_when_present`, `panel_time_horizon_months_must_be_positive_when_present`

### `time_to_event_landmark_performance_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Landmark Performance Summary Panel (Time-to-Event)
- Templates: `fenggaolab.org.medical-display-core::time_to_event_landmark_performance_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `discrimination_panel_title`, `discrimination_x_label`, `error_panel_title`, `error_x_label`, `calibration_panel_title`, `calibration_x_label`, `landmark_summaries`
- Optional display fields: `paper_role`
- Required collection fields: `landmark_summaries` -> `window_label`, `analysis_window_label`, `landmark_months`, `prediction_months`, `c_index`, `brier_score`, `calibration_slope`
- Optional collection fields: `landmark_summaries` -> `annotation`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `landmark_summaries_must_be_non_empty`, `window_labels_must_be_unique`, `analysis_window_labels_must_be_unique`, `landmark_months_must_be_positive`, `prediction_months_must_be_positive`, `prediction_months_must_exceed_landmark_months`, `c_index_values_must_be_finite_probability`, `brier_score_values_must_be_finite_probability`, `calibration_slope_values_must_be_finite`

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

### `time_to_event_threshold_governance_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Threshold Governance Panel
- Templates: `fenggaolab.org.medical-display-core::time_to_event_threshold_governance_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `threshold_panel_title`, `calibration_panel_title`, `calibration_x_label`, `threshold_summaries`, `risk_group_summaries`
- Optional display fields: `paper_role`
- Required collection fields: `threshold_summaries` -> `threshold_label`, `threshold`, `sensitivity`, `specificity`, `net_benefit`<br>`risk_group_summaries` -> `group_label`, `group_order`, `n`, `events`, `predicted_risk`, `observed_risk`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `threshold_summaries_must_be_non_empty`, `threshold_labels_must_be_unique`, `threshold_values_must_be_strictly_increasing_probability`, `threshold_metrics_must_be_finite`, `risk_group_summaries_must_be_non_empty`, `risk_group_order_must_be_strictly_increasing`, `risk_group_risks_must_be_finite_probability`, `risk_group_events_must_not_exceed_group_size`

### `binary_calibration_decision_curve_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Binary Calibration and Decision Curve Panel
- Templates: `fenggaolab.org.medical-display-core::binary_calibration_decision_curve_panel`
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
- Templates: `fenggaolab.org.medical-display-core::kaplan_meier_grouped`, `fenggaolab.org.medical-display-core::cumulative_incidence_grouped`, `fenggaolab.org.medical-display-core::time_to_event_risk_group_summary`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`
- Optional display fields: `paper_role`, `annotation`, `groups`, `panel_a_title`, `panel_b_title`, `event_count_y_label`
- Required collection fields: `groups` -> `label`, `times`, `values`
- Optional collection fields: `risk_group_summaries` -> `label`, `sample_size`, `events_5y`, `mean_predicted_risk_5y`, `observed_km_risk_5y`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `kaplan_meier_grouped_and_cumulative_incidence_grouped_require_non_empty_groups`, `group_times_values_lengths_must_match_when_groups_present`, `group_values_must_be_finite_when_groups_present`, `time_to_event_risk_group_summary_requires_non_empty_risk_group_summaries_when_selected`, `risk_group_summary_events_must_not_exceed_sample_size`

### `time_to_event_stratified_cumulative_incidence_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Stratified Cumulative Incidence Panel
- Templates: `fenggaolab.org.medical-display-core::time_to_event_stratified_cumulative_incidence_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `groups`
- Optional collection fields: `panels` -> `annotation`
- Required nested collection fields: `panels.groups` -> `label`, `times`, `values`
- Optional nested collection fields: None
- Additional constraints: `stratified_cumulative_incidence_panels_must_be_non_empty`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_group_labels_must_be_unique_within_panel`, `panel_group_times_values_lengths_must_match`, `panel_group_times_must_be_strictly_increasing`, `panel_group_values_must_be_finite_probability`, `panel_group_values_must_be_monotonic_non_decreasing`

### `time_to_event_discrimination_calibration_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Time-to-Event Discrimination and Calibration Panel
- Templates: `fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panel_a_title`, `panel_b_title`, `discrimination_x_label`, `calibration_x_label`, `calibration_y_label`, `discrimination_points`, `calibration_summary`
- Optional display fields: `paper_role`, `calibration_callout`
- Required collection fields: `discrimination_points` -> `label`, `c_index`<br>`calibration_summary` -> `group_label`, `group_order`, `n`, `events_5y`, `predicted_risk_5y`, `observed_risk_5y`
- Optional collection fields: `discrimination_points` -> `annotation`
- Required nested collection fields: `calibration_callout` -> `group_label`, `predicted_risk_5y`, `observed_risk_5y`
- Optional nested collection fields: `calibration_callout` -> `events_5y`, `n`
- Additional constraints: `discrimination_points_must_be_non_empty`, `discrimination_points_must_be_finite_c_index`, `calibration_summary_must_be_non_empty`, `calibration_group_order_must_be_strictly_increasing`, `calibration_summary_risks_must_be_finite_probability`, `calibration_summary_events_must_not_exceed_group_size`, `calibration_callout_must_reference_group_label_when_present`, `calibration_callout_must_match_referenced_group_when_present`

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

### `embedding_grouped_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Grouped Embedding Scatter
- Templates: `fenggaolab.org.medical-display-core::umap_scatter_grouped`, `fenggaolab.org.medical-display-core::pca_scatter_grouped`, `fenggaolab.org.medical-display-core::phate_scatter_grouped`, `fenggaolab.org.medical-display-core::tsne_scatter_grouped`, `fenggaolab.org.medical-display-core::diffusion_map_scatter_grouped`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `points`
- Optional display fields: `paper_role`
- Required collection fields: `points` -> `x`, `y`, `group`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `points_must_be_non_empty`, `point_coordinates_must_be_finite`, `point_group_must_be_non_empty`

### `celltype_signature_heatmap_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Cell-Type Embedding and Signature Heatmap
- Templates: `fenggaolab.org.medical-display-core::celltype_signature_heatmap`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `embedding_panel_title`, `embedding_x_label`, `embedding_y_label`, `embedding_points`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`, `embedding_annotation`, `heatmap_annotation`
- Required collection fields: `embedding_points` -> `x`, `y`, `group`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `embedding_points_must_be_non_empty`, `embedding_point_coordinates_must_be_finite`, `embedding_point_group_must_be_non_empty`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_embedding_groups`, `declared_heatmap_grid_must_be_complete_and_unique`

### `single_cell_atlas_overview_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Single-Cell Atlas Overview Panel
- Templates: `fenggaolab.org.medical-display-core::single_cell_atlas_overview_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `embedding_panel_title`, `embedding_x_label`, `embedding_y_label`, `embedding_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `composition_groups`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`, `embedding_annotation`, `composition_annotation`, `heatmap_annotation`
- Required collection fields: `embedding_points` -> `x`, `y`, `state_label`<br>`composition_groups` -> `group_label`, `group_order`, `state_proportions`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: `embedding_points` -> `group_label`
- Required nested collection fields: `composition_groups.state_proportions` -> `state_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `embedding_points_must_be_non_empty`, `embedding_point_coordinates_must_be_finite`, `embedding_point_state_label_must_be_non_empty`, `composition_groups_must_be_non_empty`, `composition_group_labels_must_be_unique`, `composition_group_order_must_be_strictly_increasing`, `composition_group_state_proportions_must_be_non_empty`, `composition_group_state_labels_must_match_declared_columns`, `composition_group_proportions_must_be_finite_probability`, `composition_group_proportions_must_sum_to_one`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_embedding_states`, `declared_heatmap_grid_must_be_complete_and_unique`

### `atlas_spatial_bridge_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Atlas-Spatial Bridge Panel
- Templates: `fenggaolab.org.medical-display-core::atlas_spatial_bridge_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `atlas_panel_title`, `atlas_x_label`, `atlas_y_label`, `atlas_points`, `spatial_panel_title`, `spatial_x_label`, `spatial_y_label`, `spatial_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `composition_groups`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`, `atlas_annotation`, `spatial_annotation`, `composition_annotation`, `heatmap_annotation`
- Required collection fields: `atlas_points` -> `x`, `y`, `state_label`<br>`spatial_points` -> `x`, `y`, `state_label`<br>`composition_groups` -> `group_label`, `group_order`, `state_proportions`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: `atlas_points` -> `group_label`<br>`spatial_points` -> `region_label`
- Required nested collection fields: `composition_groups.state_proportions` -> `state_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `atlas_points_must_be_non_empty`, `atlas_point_coordinates_must_be_finite`, `atlas_point_state_label_must_be_non_empty`, `spatial_points_must_be_non_empty`, `spatial_point_coordinates_must_be_finite`, `spatial_point_state_label_must_be_non_empty`, `composition_groups_must_be_non_empty`, `composition_group_labels_must_be_unique`, `composition_group_order_must_be_strictly_increasing`, `composition_group_state_proportions_must_be_non_empty`, `composition_group_state_labels_must_match_declared_columns`, `composition_group_proportions_must_be_finite_probability`, `composition_group_proportions_must_sum_to_one`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_atlas_states`, `declared_column_labels_must_match_spatial_states`, `declared_heatmap_grid_must_be_complete_and_unique`

### `spatial_niche_map_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Spatial Niche Map Panel
- Templates: `fenggaolab.org.medical-display-core::spatial_niche_map_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `spatial_panel_title`, `spatial_x_label`, `spatial_y_label`, `spatial_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `composition_groups`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`, `spatial_annotation`, `composition_annotation`, `heatmap_annotation`
- Required collection fields: `spatial_points` -> `x`, `y`, `niche_label`<br>`composition_groups` -> `group_label`, `group_order`, `niche_proportions`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: `spatial_points` -> `region_label`
- Required nested collection fields: `composition_groups.niche_proportions` -> `niche_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `spatial_points_must_be_non_empty`, `spatial_point_coordinates_must_be_finite`, `spatial_point_niche_label_must_be_non_empty`, `composition_groups_must_be_non_empty`, `composition_group_labels_must_be_unique`, `composition_group_order_must_be_strictly_increasing`, `composition_group_niche_proportions_must_be_non_empty`, `composition_group_niche_labels_must_match_declared_columns`, `composition_group_proportions_must_be_finite_probability`, `composition_group_proportions_must_sum_to_one`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_spatial_niches`, `declared_heatmap_grid_must_be_complete_and_unique`

### `trajectory_progression_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Trajectory Progression Panel
- Templates: `fenggaolab.org.medical-display-core::trajectory_progression_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `trajectory_panel_title`, `trajectory_x_label`, `trajectory_y_label`, `trajectory_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `branch_order`, `progression_bins`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`, `trajectory_annotation`, `composition_annotation`, `heatmap_annotation`
- Required collection fields: `trajectory_points` -> `x`, `y`, `branch_label`, `state_label`, `pseudotime`<br>`branch_order` -> `label`<br>`progression_bins` -> `bin_label`, `bin_order`, `pseudotime_start`, `pseudotime_end`, `branch_weights`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: `progression_bins.branch_weights` -> `branch_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `trajectory_points_must_be_non_empty`, `trajectory_point_coordinates_must_be_finite`, `trajectory_point_branch_label_must_be_non_empty`, `trajectory_point_state_label_must_be_non_empty`, `trajectory_point_pseudotime_must_be_finite_probability`, `branch_order_labels_must_be_unique`, `branch_order_labels_must_match_trajectory_branches`, `progression_bins_must_be_non_empty`, `progression_bin_labels_must_be_unique`, `progression_bin_order_must_be_strictly_increasing`, `progression_bin_intervals_must_be_strictly_increasing`, `progression_bin_branch_weights_must_be_non_empty`, `progression_bin_branch_labels_must_match_declared_branch_order`, `progression_bin_branch_weights_must_be_finite_probability`, `progression_bin_branch_weights_must_sum_to_one`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_progression_bins`, `declared_heatmap_grid_must_be_complete_and_unique`

### `atlas_spatial_trajectory_storyboard_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Atlas-Spatial Trajectory Storyboard Panel
- Templates: `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_storyboard_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `atlas_panel_title`, `atlas_x_label`, `atlas_y_label`, `atlas_points`, `spatial_panel_title`, `spatial_x_label`, `spatial_y_label`, `spatial_points`, `trajectory_panel_title`, `trajectory_x_label`, `trajectory_y_label`, `trajectory_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `composition_groups`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `state_order`, `branch_order`, `progression_bins`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`, `atlas_annotation`, `spatial_annotation`, `trajectory_annotation`, `composition_annotation`, `heatmap_annotation`
- Required collection fields: `atlas_points` -> `x`, `y`, `state_label`<br>`spatial_points` -> `x`, `y`, `state_label`<br>`trajectory_points` -> `x`, `y`, `branch_label`, `state_label`, `pseudotime`<br>`composition_groups` -> `group_label`, `group_order`, `state_proportions`<br>`state_order` -> `label`<br>`branch_order` -> `label`<br>`progression_bins` -> `bin_label`, `bin_order`, `pseudotime_start`, `pseudotime_end`, `branch_weights`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: `spatial_points` -> `region_label`
- Required nested collection fields: `composition_groups.state_proportions` -> `state_label`, `proportion`<br>`progression_bins.branch_weights` -> `branch_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `atlas_points_must_be_non_empty`, `atlas_point_coordinates_must_be_finite`, `atlas_point_state_label_must_be_non_empty`, `spatial_points_must_be_non_empty`, `spatial_point_coordinates_must_be_finite`, `spatial_point_state_label_must_be_non_empty`, `trajectory_points_must_be_non_empty`, `trajectory_point_coordinates_must_be_finite`, `trajectory_point_state_label_must_be_non_empty`, `trajectory_point_pseudotime_must_be_probability`, `trajectory_point_branch_label_must_be_non_empty`, `composition_groups_must_be_non_empty`, `composition_group_labels_must_be_unique`, `composition_group_order_must_be_strictly_increasing`, `composition_group_state_proportions_must_be_non_empty`, `composition_group_state_labels_must_match_declared_states`, `composition_group_proportions_must_be_finite_probability`, `composition_group_proportions_must_sum_to_one`, `state_order_labels_must_be_unique`, `branch_order_labels_must_be_unique`, `progression_bins_must_be_non_empty`, `progression_bin_labels_must_be_unique`, `progression_bin_order_must_be_strictly_increasing`, `progression_bin_intervals_must_be_strictly_increasing`, `progression_bin_branch_weights_must_be_non_empty`, `progression_bin_branch_labels_must_match_declared_branches`, `progression_bin_branch_weights_must_sum_to_one`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_state_labels_must_match_atlas_states`, `declared_state_labels_must_match_spatial_states`, `declared_state_labels_must_match_trajectory_states`, `declared_branch_labels_must_match_trajectory_branches`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_progression_bins`, `declared_heatmap_grid_must_be_complete_and_unique`

### `atlas_spatial_trajectory_density_coverage_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Atlas-Spatial Trajectory Density Coverage Panel
- Templates: `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_density_coverage_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `atlas_panel_title`, `atlas_x_label`, `atlas_y_label`, `atlas_points`, `spatial_panel_title`, `spatial_x_label`, `spatial_y_label`, `spatial_points`, `trajectory_panel_title`, `trajectory_x_label`, `trajectory_y_label`, `trajectory_points`, `support_panel_title`, `support_x_label`, `support_y_label`, `support_scale_label`, `state_order`, `context_order`, `support_cells`
- Optional display fields: `paper_role`, `atlas_annotation`, `spatial_annotation`, `trajectory_annotation`, `support_annotation`
- Required collection fields: `atlas_points` -> `x`, `y`, `state_label`<br>`spatial_points` -> `x`, `y`, `state_label`, `region_label`<br>`trajectory_points` -> `x`, `y`, `branch_label`, `state_label`, `pseudotime`<br>`state_order` -> `label`<br>`context_order` -> `label`, `context_kind`<br>`support_cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `atlas_points_must_be_non_empty`, `atlas_point_coordinates_must_be_finite`, `atlas_point_state_label_must_be_non_empty`, `spatial_points_must_be_non_empty`, `spatial_point_coordinates_must_be_finite`, `spatial_point_state_label_must_be_non_empty`, `spatial_point_region_label_must_be_non_empty`, `trajectory_points_must_be_non_empty`, `trajectory_point_coordinates_must_be_finite`, `trajectory_point_branch_label_must_be_non_empty`, `trajectory_point_state_label_must_be_non_empty`, `trajectory_point_pseudotime_must_be_finite_probability`, `support_scale_label_must_be_non_empty`, `state_order_labels_must_be_unique`, `context_order_labels_must_be_unique`, `context_order_kinds_must_be_supported_and_unique`, `context_order_kinds_must_cover_all_required_contexts`, `support_cells_must_be_non_empty`, `support_cell_coordinates_must_be_non_empty`, `support_cell_values_must_be_finite_probability`, `declared_state_labels_must_match_atlas_states`, `declared_state_labels_must_match_spatial_states`, `declared_state_labels_must_match_trajectory_states`, `declared_state_labels_must_match_support_rows`, `declared_context_labels_must_match_support_columns`, `declared_support_grid_must_be_complete_and_unique`

### `atlas_spatial_trajectory_context_support_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Atlas-Spatial Trajectory Context Support Panel
- Templates: `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_context_support_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `atlas_panel_title`, `atlas_x_label`, `atlas_y_label`, `atlas_points`, `spatial_panel_title`, `spatial_x_label`, `spatial_y_label`, `spatial_points`, `trajectory_panel_title`, `trajectory_x_label`, `trajectory_y_label`, `trajectory_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `composition_groups`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `state_order`, `branch_order`, `progression_bins`, `row_order`, `column_order`, `cells`, `support_panel_title`, `support_x_label`, `support_y_label`, `support_scale_label`, `context_order`, `support_cells`
- Optional display fields: `paper_role`, `atlas_annotation`, `spatial_annotation`, `trajectory_annotation`, `composition_annotation`, `heatmap_annotation`, `support_annotation`
- Required collection fields: `atlas_points` -> `x`, `y`, `state_label`<br>`spatial_points` -> `x`, `y`, `state_label`, `region_label`<br>`trajectory_points` -> `x`, `y`, `branch_label`, `state_label`, `pseudotime`<br>`composition_groups` -> `group_label`, `group_order`, `state_proportions`<br>`state_order` -> `label`<br>`branch_order` -> `label`<br>`progression_bins` -> `bin_label`, `bin_order`, `pseudotime_start`, `pseudotime_end`, `branch_weights`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`<br>`context_order` -> `label`, `context_kind`<br>`support_cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: `composition_groups.state_proportions` -> `state_label`, `proportion`<br>`progression_bins.branch_weights` -> `branch_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `atlas_points_must_be_non_empty`, `atlas_point_coordinates_must_be_finite`, `atlas_point_state_label_must_be_non_empty`, `spatial_points_must_be_non_empty`, `spatial_point_coordinates_must_be_finite`, `spatial_point_state_label_must_be_non_empty`, `spatial_point_region_label_must_be_non_empty`, `trajectory_points_must_be_non_empty`, `trajectory_point_coordinates_must_be_finite`, `trajectory_point_state_label_must_be_non_empty`, `trajectory_point_pseudotime_must_be_probability`, `trajectory_point_branch_label_must_be_non_empty`, `composition_groups_must_be_non_empty`, `composition_group_labels_must_be_unique`, `composition_group_order_must_be_strictly_increasing`, `composition_group_state_proportions_must_be_non_empty`, `composition_group_state_labels_must_match_declared_states`, `composition_group_proportions_must_be_finite_probability`, `composition_group_proportions_must_sum_to_one`, `state_order_labels_must_be_unique`, `branch_order_labels_must_be_unique`, `progression_bins_must_be_non_empty`, `progression_bin_labels_must_be_unique`, `progression_bin_order_must_be_strictly_increasing`, `progression_bin_intervals_must_be_strictly_increasing`, `progression_bin_branch_weights_must_be_non_empty`, `progression_bin_branch_labels_must_match_declared_branches`, `progression_bin_branch_weights_must_sum_to_one`, `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_column_labels_must_match_progression_bins`, `declared_heatmap_grid_must_be_complete_and_unique`, `support_scale_label_must_be_non_empty`, `context_order_labels_must_be_unique`, `context_order_kinds_must_be_supported_and_unique`, `context_order_kinds_must_cover_all_required_contexts`, `support_cells_must_be_non_empty`, `support_cell_coordinates_must_be_non_empty`, `support_cell_values_must_be_finite_probability`, `declared_state_labels_must_match_atlas_states`, `declared_state_labels_must_match_spatial_states`, `declared_state_labels_must_match_trajectory_states`, `declared_state_labels_must_match_support_rows`, `declared_context_labels_must_match_support_columns`, `declared_support_grid_must_be_complete_and_unique`

### `atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Atlas-Spatial Trajectory Multimanifold Context Support Panel
- Templates: `fenggaolab.org.medical-display-core::atlas_spatial_trajectory_multimanifold_context_support_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `atlas_manifold_panels`, `spatial_panel_title`, `spatial_x_label`, `spatial_y_label`, `spatial_points`, `trajectory_panel_title`, `trajectory_x_label`, `trajectory_y_label`, `trajectory_points`, `composition_panel_title`, `composition_x_label`, `composition_y_label`, `composition_groups`, `heatmap_panel_title`, `heatmap_x_label`, `heatmap_y_label`, `score_method`, `state_order`, `branch_order`, `progression_bins`, `row_order`, `column_order`, `cells`, `support_panel_title`, `support_x_label`, `support_y_label`, `support_scale_label`, `context_order`, `support_cells`
- Optional display fields: `paper_role`, `spatial_annotation`, `trajectory_annotation`, `composition_annotation`, `heatmap_annotation`, `support_annotation`
- Required collection fields: `atlas_manifold_panels` -> `panel_id`, `panel_label`, `panel_title`, `manifold_method`, `x_label`, `y_label`, `points`<br>`spatial_points` -> `x`, `y`, `state_label`, `region_label`<br>`trajectory_points` -> `x`, `y`, `branch_label`, `state_label`, `pseudotime`<br>`composition_groups` -> `group_label`, `group_order`, `state_proportions`<br>`state_order` -> `label`<br>`branch_order` -> `label`<br>`progression_bins` -> `bin_label`, `bin_order`, `pseudotime_start`, `pseudotime_end`, `branch_weights`<br>`row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`<br>`context_order` -> `label`, `context_kind`<br>`support_cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: `atlas_manifold_panels.points` -> `x`, `y`, `state_label`<br>`composition_groups.state_proportions` -> `state_label`, `proportion`<br>`progression_bins.branch_weights` -> `branch_label`, `proportion`
- Optional nested collection fields: None
- Additional constraints: `atlas_manifold_panels_must_contain_exactly_two_panels`, `atlas_manifold_panel_ids_must_be_unique`, `atlas_manifold_panel_labels_must_be_unique`, `atlas_manifold_methods_must_be_supported_and_unique`, `atlas_manifold_panel_titles_must_be_non_empty`, `atlas_manifold_axis_labels_must_be_non_empty`, `atlas_manifold_points_must_be_non_empty`, `atlas_manifold_point_coordinates_must_be_finite`, `atlas_manifold_point_state_label_must_be_non_empty`, `spatial_points_must_be_non_empty`, `spatial_point_coordinates_must_be_finite`, `spatial_point_state_label_must_be_non_empty`, `spatial_point_region_label_must_be_non_empty`, `trajectory_points_must_be_non_empty`, `trajectory_point_coordinates_must_be_finite`, `trajectory_point_state_label_must_be_non_empty`, `trajectory_point_pseudotime_must_be_probability`, `trajectory_point_branch_label_must_be_non_empty`, `composition_groups_must_be_non_empty`, `composition_group_labels_must_be_unique`, `composition_group_order_must_be_strictly_increasing`, `composition_group_state_proportions_must_be_non_empty`, `composition_group_state_labels_must_match_declared_states`, `composition_group_proportions_must_be_finite_probability`, `composition_group_proportions_must_sum_to_one`, `branch_order_labels_must_be_unique`, `progression_bins_must_be_non_empty`, `progression_bin_labels_must_be_unique`, `progression_bin_order_must_be_strictly_increasing`, `progression_bin_intervals_must_be_strictly_increasing`, `progression_bin_branch_weights_must_be_non_empty`, `progression_bin_branch_labels_must_match_declared_branches`, `progression_bin_branch_weights_must_be_finite_probability`, `progression_bin_branch_weights_must_sum_to_one`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `matrix_cells_must_be_non_empty`, `matrix_cell_coordinates_must_be_non_empty`, `matrix_cell_values_must_be_finite`, `declared_row_labels_must_match_matrix_rows`, `declared_column_labels_must_match_matrix_columns`, `declared_matrix_grid_must_be_complete_and_unique`, `state_order_labels_must_be_unique`, `context_order_labels_must_be_unique`, `context_order_kinds_must_be_supported_and_unique`, `context_order_kinds_must_cover_all_required_contexts`, `support_cells_must_be_non_empty`, `support_cell_coordinates_must_be_non_empty`, `support_cell_values_must_be_finite_probability`, `declared_state_labels_must_match_all_atlas_manifold_states`, `declared_state_labels_must_match_spatial_states`, `declared_state_labels_must_match_trajectory_states`, `declared_state_labels_must_match_support_rows`, `declared_context_labels_must_match_support_columns`, `declared_support_grid_must_be_complete_and_unique`, `declared_column_labels_must_match_progression_bins`

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

### `performance_heatmap_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Performance Heatmap
- Templates: `fenggaolab.org.medical-display-core::performance_heatmap`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `metric_name`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `metric_name_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `performance_values_must_be_finite_probability`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_heatmap_grid_must_be_complete_and_unique`

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

### `correlation_heatmap_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Correlation Heatmap
- Templates: `fenggaolab.org.medical-display-core::correlation_heatmap`
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
- Templates: `fenggaolab.org.medical-display-core::clustered_heatmap`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_heatmap_grid_must_be_complete_and_unique`

### `gsva_ssgsea_heatmap_inputs_v1`

- Display kind: `evidence_figure`
- Display name: GSVA/ssGSEA Heatmap
- Templates: `fenggaolab.org.medical-display-core::gsva_ssgsea_heatmap`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `y_label`, `score_method`, `row_order`, `column_order`, `cells`
- Optional display fields: `paper_role`
- Required collection fields: `row_order` -> `label`<br>`column_order` -> `label`<br>`cells` -> `x`, `y`, `value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `score_method_must_be_non_empty`, `cells_must_be_non_empty`, `cell_coordinates_must_be_non_empty`, `cell_values_must_be_finite`, `row_order_labels_must_be_unique`, `column_order_labels_must_be_unique`, `declared_row_labels_must_match_cell_rows`, `declared_column_labels_must_match_cell_columns`, `declared_heatmap_grid_must_be_complete_and_unique`

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

### `oncoplot_mutation_landscape_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Oncoplot Mutation Landscape Panel
- Templates: `fenggaolab.org.medical-display-core::oncoplot_mutation_landscape_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `burden_axis_label`, `frequency_axis_label`, `mutation_legend_title`, `gene_order`, `sample_order`, `annotation_tracks`, `mutation_records`
- Optional display fields: `paper_role`
- Required collection fields: `gene_order` -> `label`<br>`sample_order` -> `sample_id`<br>`annotation_tracks` -> `track_id`, `track_label`, `values`<br>`mutation_records` -> `sample_id`, `gene_label`, `alteration_class`
- Optional collection fields: None
- Required nested collection fields: `annotation_tracks.values` -> `sample_id`, `category_label`
- Optional nested collection fields: None
- Additional constraints: `y_label_must_be_non_empty`, `burden_axis_label_must_be_non_empty`, `frequency_axis_label_must_be_non_empty`, `mutation_legend_title_must_be_non_empty`, `gene_order_must_be_non_empty`, `gene_order_labels_must_be_unique`, `sample_order_must_be_non_empty`, `sample_ids_must_be_unique`, `annotation_tracks_must_be_non_empty`, `annotation_track_count_must_be_at_most_three`, `annotation_track_ids_must_be_unique`, `annotation_track_labels_must_be_non_empty`, `annotation_track_sample_coverage_must_match_declared_sample_order`, `annotation_track_category_labels_must_be_non_empty`, `mutation_records_must_be_non_empty`, `mutation_sample_ids_must_match_declared_sample_order`, `mutation_gene_labels_must_match_declared_gene_order`, `mutation_sample_gene_coordinates_must_be_unique`, `alteration_class_must_be_supported`

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

### `genomic_alteration_multiomic_consequence_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Genomic Alteration Multiomic Consequence Panel
- Templates: `fenggaolab.org.medical-display-core::genomic_alteration_multiomic_consequence_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `burden_axis_label`, `frequency_axis_label`, `alteration_legend_title`, `gene_order`, `sample_order`, `annotation_tracks`, `alteration_records`, `consequence_x_label`, `consequence_y_label`, `consequence_legend_title`, `effect_threshold`, `significance_threshold`, `driver_gene_order`, `consequence_panel_order`, `consequence_points`
- Optional display fields: `paper_role`
- Required collection fields: `gene_order` -> `label`<br>`sample_order` -> `sample_id`<br>`annotation_tracks` -> `track_id`, `track_label`, `values`<br>`alteration_records` -> `sample_id`, `gene_label`<br>`driver_gene_order` -> `label`<br>`consequence_panel_order` -> `panel_id`, `panel_title`<br>`consequence_points` -> `panel_id`, `gene_label`, `effect_value`, `significance_value`, `regulation_class`
- Optional collection fields: None
- Required nested collection fields: `annotation_tracks.values` -> `sample_id`, `category_label`
- Optional nested collection fields: None
- Additional constraints: `y_label_must_be_non_empty`, `burden_axis_label_must_be_non_empty`, `frequency_axis_label_must_be_non_empty`, `alteration_legend_title_must_be_non_empty`, `gene_order_must_be_non_empty`, `gene_order_labels_must_be_unique`, `sample_order_must_be_non_empty`, `sample_ids_must_be_unique`, `annotation_tracks_must_be_non_empty`, `annotation_track_count_must_be_at_most_three`, `annotation_track_ids_must_be_unique`, `annotation_track_labels_must_be_non_empty`, `annotation_track_sample_coverage_must_match_declared_sample_order`, `annotation_track_category_labels_must_be_non_empty`, `alteration_records_must_be_non_empty`, `alteration_sample_ids_must_match_declared_sample_order`, `alteration_gene_labels_must_match_declared_gene_order`, `alteration_sample_gene_coordinates_must_be_unique`, `alteration_record_must_define_mutation_or_cnv`, `mutation_class_must_be_supported_when_present`, `cnv_state_must_be_supported_when_present`, `consequence_x_label_must_be_non_empty`, `consequence_y_label_must_be_non_empty`, `consequence_legend_title_must_be_non_empty`, `effect_threshold_must_be_positive`, `significance_threshold_must_be_positive`, `driver_gene_order_must_be_non_empty`, `driver_gene_labels_must_be_unique`, `driver_gene_labels_must_be_subset_of_gene_order`, `consequence_panel_order_must_be_non_empty`, `consequence_panel_order_count_must_equal_three`, `consequence_panel_ids_must_match_multiomic_layers`, `consequence_panel_titles_must_be_non_empty`, `consequence_points_must_be_non_empty`, `consequence_point_panel_ids_must_match_declared_panels`, `consequence_point_gene_labels_must_match_declared_driver_genes`, `consequence_point_coordinates_must_be_complete_and_unique`, `consequence_point_effect_values_must_be_finite`, `consequence_point_significance_values_must_be_non_negative`, `consequence_point_regulation_classes_must_use_supported_vocabulary`

### `genomic_alteration_pathway_integrated_composite_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Genomic Alteration Pathway-Integrated Composite Panel
- Templates: `fenggaolab.org.medical-display-core::genomic_alteration_pathway_integrated_composite_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `burden_axis_label`, `frequency_axis_label`, `alteration_legend_title`, `gene_order`, `sample_order`, `annotation_tracks`, `alteration_records`, `consequence_x_label`, `consequence_y_label`, `consequence_legend_title`, `effect_threshold`, `significance_threshold`, `driver_gene_order`, `consequence_panel_order`, `consequence_points`, `pathway_x_label`, `pathway_y_label`, `pathway_effect_scale_label`, `pathway_size_scale_label`, `pathway_order`, `pathway_panel_order`, `pathway_points`
- Optional display fields: `paper_role`
- Required collection fields: `gene_order` -> `label`<br>`sample_order` -> `sample_id`<br>`annotation_tracks` -> `track_id`, `track_label`, `values`<br>`alteration_records` -> `sample_id`, `gene_label`<br>`driver_gene_order` -> `label`<br>`consequence_panel_order` -> `panel_id`, `panel_title`<br>`consequence_points` -> `panel_id`, `gene_label`, `effect_value`, `significance_value`, `regulation_class`<br>`pathway_order` -> `label`<br>`pathway_panel_order` -> `panel_id`, `panel_title`<br>`pathway_points` -> `panel_id`, `pathway_label`, `x_value`, `effect_value`, `size_value`
- Optional collection fields: None
- Required nested collection fields: `annotation_tracks.values` -> `sample_id`, `category_label`
- Optional nested collection fields: None
- Additional constraints: `y_label_must_be_non_empty`, `burden_axis_label_must_be_non_empty`, `frequency_axis_label_must_be_non_empty`, `alteration_legend_title_must_be_non_empty`, `gene_order_must_be_non_empty`, `gene_order_labels_must_be_unique`, `sample_order_must_be_non_empty`, `sample_ids_must_be_unique`, `annotation_tracks_must_be_non_empty`, `annotation_track_count_must_be_at_most_three`, `annotation_track_ids_must_be_unique`, `annotation_track_labels_must_be_non_empty`, `annotation_track_sample_coverage_must_match_declared_sample_order`, `annotation_track_category_labels_must_be_non_empty`, `alteration_records_must_be_non_empty`, `alteration_sample_ids_must_match_declared_sample_order`, `alteration_gene_labels_must_match_declared_gene_order`, `alteration_sample_gene_coordinates_must_be_unique`, `alteration_record_must_define_mutation_or_cnv`, `mutation_class_must_be_supported_when_present`, `cnv_state_must_be_supported_when_present`, `consequence_x_label_must_be_non_empty`, `consequence_y_label_must_be_non_empty`, `consequence_legend_title_must_be_non_empty`, `effect_threshold_must_be_positive`, `significance_threshold_must_be_positive`, `driver_gene_order_must_be_non_empty`, `driver_gene_labels_must_be_unique`, `driver_gene_labels_must_be_subset_of_gene_order`, `consequence_panel_order_must_be_non_empty`, `consequence_panel_order_count_must_equal_three`, `consequence_panel_ids_must_match_multiomic_layers`, `consequence_panel_titles_must_be_non_empty`, `consequence_points_must_be_non_empty`, `consequence_point_panel_ids_must_match_declared_panels`, `consequence_point_gene_labels_must_match_declared_driver_genes`, `consequence_point_coordinates_must_be_complete_and_unique`, `consequence_point_effect_values_must_be_finite`, `consequence_point_significance_values_must_be_non_negative`, `consequence_point_regulation_classes_must_use_supported_vocabulary`, `pathway_x_label_must_be_non_empty`, `pathway_y_label_must_be_non_empty`, `pathway_effect_scale_label_must_be_non_empty`, `pathway_size_scale_label_must_be_non_empty`, `pathway_order_must_be_non_empty`, `pathway_order_labels_must_be_unique`, `pathway_panel_order_must_be_non_empty`, `pathway_panel_order_count_must_equal_three`, `pathway_panel_ids_must_match_multiomic_layers`, `pathway_panel_titles_must_be_non_empty`, `pathway_points_must_be_non_empty`, `pathway_point_panel_ids_must_match_declared_panels`, `pathway_point_labels_must_match_declared_pathways`, `pathway_point_coordinates_must_be_complete_and_unique`, `pathway_point_x_values_must_be_finite`, `pathway_point_effect_values_must_be_finite`, `pathway_point_size_values_must_be_non_negative`

### `genomic_program_governance_summary_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Genomic Program Governance Summary Panel
- Templates: `fenggaolab.org.medical-display-core::genomic_program_governance_summary_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `evidence_panel_title`, `summary_panel_title`, `effect_scale_label`, `support_scale_label`, `layer_order`, `programs`
- Optional display fields: `paper_role`
- Required collection fields: `layer_order` -> `layer_id`, `layer_label`<br>`programs` -> `program_id`, `program_label`, `lead_driver_label`, `dominant_pathway_label`, `pathway_hit_count`, `priority_rank`, `priority_band`, `verdict`, `action`, `layer_supports`
- Optional collection fields: `programs` -> `detail`
- Required nested collection fields: `programs.layer_supports` -> `layer_id`, `effect_value`, `support_fraction`
- Optional nested collection fields: None
- Additional constraints: `evidence_panel_title_must_be_non_empty`, `summary_panel_title_must_be_non_empty`, `effect_scale_label_must_be_non_empty`, `support_scale_label_must_be_non_empty`, `layer_order_must_be_non_empty`, `layer_order_count_must_equal_five`, `layer_ids_must_match_supported_vocabulary`, `layer_labels_must_be_non_empty`, `programs_must_be_non_empty`, `program_ids_must_be_unique`, `program_labels_must_be_unique`, `lead_driver_labels_must_be_non_empty`, `dominant_pathway_labels_must_be_non_empty`, `pathway_hit_counts_must_be_positive_integers`, `priority_ranks_must_be_strictly_increasing`, `priority_bands_must_be_supported`, `verdicts_must_be_supported`, `actions_must_be_non_empty`, `program_detail_must_be_non_empty_when_present`, `layer_supports_must_be_non_empty`, `layer_supports_must_cover_declared_layers_exactly_once`, `layer_support_effect_values_must_be_finite`, `layer_support_fractions_must_be_probability`

### `forest_effect_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Forest Effect Plot
- Templates: `fenggaolab.org.medical-display-core::forest_effect_main`, `fenggaolab.org.medical-display-core::subgroup_forest`, `fenggaolab.org.medical-display-core::multivariable_forest`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `reference_value`, `rows`
- Optional display fields: `paper_role`
- Required collection fields: `rows` -> `label`, `estimate`, `lower`, `upper`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `rows_must_be_non_empty`, `effect_interval_must_bound_estimate`, `effect_values_must_be_finite`

### `compact_effect_estimate_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Compact Effect Estimate Panel
- Templates: `fenggaolab.org.medical-display-core::compact_effect_estimate_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `reference_value`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `rows`
- Optional collection fields: None
- Required nested collection fields: `panels.rows` -> `row_id`, `row_label`, `estimate`, `lower`, `upper`
- Optional nested collection fields: `panels.rows` -> `support_n`
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_be_between_two_and_four`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `reference_value_must_be_finite`, `panel_rows_must_be_non_empty`, `panel_row_ids_must_be_unique_within_panel`, `panel_row_labels_must_be_unique_within_panel`, `panel_row_values_must_be_finite`, `panel_row_intervals_must_wrap_estimate`, `panel_row_support_n_must_be_positive_when_present`, `panel_row_orders_must_match_across_panels`

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

### `broader_heterogeneity_summary_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Broader Heterogeneity Summary Panel
- Templates: `fenggaolab.org.medical-display-core::broader_heterogeneity_summary_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `matrix_panel_title`, `x_label`, `reference_value`, `slice_legend_title`, `slices`, `effect_rows`, `summary_panel_title`
- Optional display fields: `paper_role`
- Required collection fields: `slices` -> `slice_id`, `slice_label`, `slice_kind`, `slice_order`<br>`effect_rows` -> `row_id`, `row_label`, `verdict`, `slice_estimates`
- Optional collection fields: `effect_rows` -> `detail`
- Required nested collection fields: `effect_rows.slice_estimates` -> `slice_id`, `estimate`, `lower`, `upper`
- Optional nested collection fields: `effect_rows.slice_estimates` -> `support_n`
- Additional constraints: `slices_must_be_non_empty`, `slice_count_must_be_between_two_and_five`, `slice_ids_must_be_unique`, `slice_labels_must_be_unique`, `slice_orders_must_be_strictly_increasing`, `slice_kinds_must_be_supported`, `reference_value_must_be_finite`, `effect_rows_must_be_non_empty`, `effect_row_ids_must_be_unique`, `effect_row_labels_must_be_unique`, `effect_row_verdicts_must_be_supported`, `effect_row_slice_estimates_must_be_non_empty`, `effect_row_slice_estimates_must_cover_declared_slices_exactly_once`, `effect_row_values_must_be_finite`, `effect_row_intervals_must_wrap_estimate`, `effect_row_support_n_must_be_positive_when_present`, `effect_row_detail_must_be_non_empty_when_present`

### `interaction_effect_summary_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Interaction Effect Summary Panel
- Templates: `fenggaolab.org.medical-display-core::interaction_effect_summary_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `estimate_panel_title`, `x_label`, `reference_value`, `summary_panel_title`, `modifiers`
- Optional display fields: `paper_role`
- Required collection fields: `modifiers` -> `modifier_id`, `modifier_label`, `interaction_estimate`, `lower`, `upper`, `support_n`, `favored_group_label`, `interaction_p_value`, `verdict`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `modifiers_must_be_non_empty`, `modifier_count_must_be_between_two_and_six`, `modifier_ids_must_be_unique`, `modifier_labels_must_be_unique`, `reference_value_must_be_finite`, `interaction_estimates_must_be_finite`, `interaction_intervals_must_wrap_estimate`, `modifier_support_n_must_be_positive`, `interaction_p_values_must_be_between_zero_and_one`, `favored_group_labels_must_be_non_empty`, `modifier_verdicts_must_use_controlled_vocabulary`

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

### `shap_bar_importance_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Bar Importance Panel
- Templates: `fenggaolab.org.medical-display-core::shap_bar_importance`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `bars`
- Optional display fields: `paper_role`
- Required collection fields: `bars` -> `rank`, `feature`, `importance_value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `bars_must_be_non_empty`, `bar_features_must_be_unique`, `bar_ranks_must_be_strictly_increasing`, `bar_importance_values_must_be_non_negative_finite`, `bar_importance_values_must_be_sorted_descending_by_rank`

### `shap_signed_importance_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Signed Importance Panel
- Templates: `fenggaolab.org.medical-display-core::shap_signed_importance_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `negative_label`, `positive_label`, `bars`
- Optional display fields: `paper_role`
- Required collection fields: `bars` -> `rank`, `feature`, `signed_importance_value`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `bars_must_be_non_empty`, `bar_features_must_be_unique`, `bar_ranks_must_be_strictly_increasing`, `bar_signed_importance_values_must_be_finite_and_non_zero`, `bar_signed_importance_values_must_be_sorted_by_absolute_magnitude_descending`

### `shap_multicohort_importance_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Multicohort Importance Panel
- Templates: `fenggaolab.org.medical-display-core::shap_multicohort_importance_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `cohort_label`, `bars`
- Optional collection fields: None
- Required nested collection fields: `panels.bars` -> `rank`, `feature`, `importance_value`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_cohort_labels_must_be_unique`, `panel_bars_must_be_non_empty`, `panel_bar_features_must_be_unique_within_panel`, `panel_bar_ranks_must_be_strictly_increasing`, `panel_bar_importance_values_must_be_non_negative_finite`, `panel_bar_importance_values_must_be_sorted_descending_by_rank`, `panel_feature_orders_must_match_across_panels`

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

### `shap_force_like_summary_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Force-like Summary Panel
- Templates: `fenggaolab.org.medical-display-core::shap_force_like_summary_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `case_label`, `baseline_value`, `predicted_value`, `contributions`
- Optional collection fields: None
- Required nested collection fields: `panels.contributions` -> `feature`, `shap_value`
- Optional nested collection fields: `panels.contributions` -> `feature_value_text`
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_case_labels_must_be_unique`, `panel_values_must_be_finite`, `panel_contributions_must_be_non_empty`, `panel_contribution_features_must_be_unique_within_panel`, `panel_contribution_values_must_be_finite_and_non_zero`, `panel_prediction_value_must_equal_baseline_plus_contributions`, `panel_contributions_must_be_sorted_by_absolute_magnitude_descending`

### `shap_grouped_local_explanation_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Grouped Local Explanation Panel
- Templates: `fenggaolab.org.medical-display-core::shap_grouped_local_explanation_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `x_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `group_label`, `baseline_value`, `predicted_value`, `contributions`
- Optional collection fields: None
- Required nested collection fields: `panels.contributions` -> `rank`, `feature`, `shap_value`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_group_labels_must_be_unique`, `panel_values_must_be_finite`, `panel_contributions_must_be_non_empty`, `panel_contribution_ranks_must_be_strictly_increasing`, `panel_contribution_features_must_be_unique_within_panel`, `panel_contribution_values_must_be_finite_and_non_zero`, `panel_prediction_value_must_equal_baseline_plus_contributions`, `panel_feature_orders_must_match_across_panels`

### `shap_grouped_decision_path_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Grouped Decision Path Panel
- Templates: `fenggaolab.org.medical-display-core::shap_grouped_decision_path_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panel_title`, `x_label`, `y_label`, `legend_title`, `baseline_value`, `groups`
- Optional display fields: `paper_role`
- Required collection fields: `groups` -> `group_id`, `group_label`, `predicted_value`, `contributions`
- Optional collection fields: None
- Required nested collection fields: `groups.contributions` -> `rank`, `feature`, `shap_value`
- Optional nested collection fields: None
- Additional constraints: `group_count_must_equal_two`, `group_ids_must_be_unique`, `group_labels_must_be_unique`, `baseline_value_must_be_finite`, `group_prediction_value_must_equal_baseline_plus_contributions`, `group_contribution_ranks_must_be_strictly_increasing`, `group_contribution_values_must_be_finite_and_non_zero`, `group_feature_orders_must_match`

### `shap_multigroup_decision_path_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Multigroup Decision Path Panel
- Templates: `fenggaolab.org.medical-display-core::shap_multigroup_decision_path_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `panel_title`, `x_label`, `y_label`, `legend_title`, `baseline_value`, `groups`
- Optional display fields: `paper_role`
- Required collection fields: `groups` -> `group_id`, `group_label`, `predicted_value`, `contributions`
- Optional collection fields: None
- Required nested collection fields: `groups.contributions` -> `rank`, `feature`, `shap_value`
- Optional nested collection fields: None
- Additional constraints: `group_count_must_equal_three`, `group_ids_must_be_unique`, `group_labels_must_be_unique`, `baseline_value_must_be_finite`, `group_prediction_value_must_equal_baseline_plus_contributions`, `group_contribution_ranks_must_be_strictly_increasing`, `group_contribution_values_must_be_finite_and_non_zero`, `group_feature_orders_must_match`

### `partial_dependence_ice_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Partial Dependence and ICE Panel
- Templates: `fenggaolab.org.medical-display-core::partial_dependence_ice_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `pdp_curve`, `ice_curves`
- Optional collection fields: None
- Required nested collection fields: `panels.pdp_curve` -> `x`, `y`<br>`panels.ice_curves` -> `curve_id`, `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_features_must_be_unique`, `panel_reference_labels_must_be_non_empty`, `panel_reference_values_must_be_finite`, `panel_pdp_curve_must_have_matching_x_y_lengths`, `panel_pdp_curve_x_must_be_strictly_increasing`, `panel_pdp_curve_values_must_be_finite`, `panel_ice_curves_must_be_non_empty`, `panel_ice_curve_ids_must_be_unique_within_panel`, `ice_curve_x_y_lengths_must_match`, `ice_curve_x_grids_must_match_pdp_curve_x`, `ice_curve_values_must_be_finite`, `panel_reference_values_must_fall_within_pdp_curve_range`

### `partial_dependence_interaction_contour_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Partial Dependence Interaction Contour Panel
- Templates: `fenggaolab.org.medical-display-core::partial_dependence_interaction_contour_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `colorbar_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `y_label`, `x_feature`, `y_feature`, `reference_x_value`, `reference_y_value`, `reference_label`, `x_grid`, `y_grid`, `response_grid`, `observed_points`
- Optional collection fields: None
- Required nested collection fields: `panels.observed_points` -> `point_id`, `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_two`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_feature_pairs_must_be_unique`, `panel_reference_labels_must_be_non_empty`, `panel_x_grids_must_be_strictly_increasing`, `panel_y_grids_must_be_strictly_increasing`, `panel_response_grids_must_match_declared_axes`, `panel_response_values_must_be_finite`, `panel_observed_points_must_be_non_empty`, `panel_observed_point_ids_must_be_unique_within_panel`, `panel_observed_points_must_be_finite`, `panel_observed_points_must_fall_within_declared_grid_range`, `panel_reference_point_must_fall_within_declared_grid_range`

### `partial_dependence_interaction_slice_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Partial Dependence Interaction Slice Panel
- Templates: `fenggaolab.org.medical-display-core::partial_dependence_interaction_slice_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `legend_title`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `x_feature`, `slice_feature`, `reference_value`, `reference_label`, `slice_curves`
- Optional collection fields: None
- Required nested collection fields: `panels.slice_curves` -> `slice_id`, `slice_label`, `conditioning_value`, `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_two`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_feature_pairs_must_be_unique`, `panel_reference_labels_must_be_non_empty`, `panel_reference_values_must_be_finite`, `panel_slice_curves_must_have_at_least_two_entries`, `panel_slice_curve_ids_must_be_unique_within_panel`, `panel_slice_curve_labels_must_be_unique_within_panel`, `panel_slice_curve_x_y_lengths_must_match`, `panel_slice_curve_x_must_be_strictly_increasing`, `panel_slice_curve_values_must_be_finite`, `panel_slice_curve_x_grids_must_match_within_panel`, `panel_reference_values_must_fall_within_slice_curve_range`, `panel_slice_label_sets_must_match_across_panels`

### `partial_dependence_subgroup_comparison_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Partial Dependence Subgroup Comparison Panel
- Templates: `fenggaolab.org.medical-display-core::partial_dependence_subgroup_comparison_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `subgroup_panel_label`, `subgroup_panel_title`, `subgroup_x_label`, `panels`, `subgroup_rows`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `subgroup_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `pdp_curve`, `ice_curves`<br>`subgroup_rows` -> `row_id`, `panel_id`, `row_label`, `estimate`, `lower`, `upper`, `support_n`
- Optional collection fields: None
- Required nested collection fields: `panels.pdp_curve` -> `x`, `y`<br>`panels.ice_curves` -> `curve_id`, `x`, `y`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_subgroup_labels_must_be_unique`, `panel_reference_labels_must_be_non_empty`, `panel_reference_values_must_be_finite`, `panel_pdp_curve_must_have_matching_x_y_lengths`, `panel_pdp_curve_x_must_be_strictly_increasing`, `panel_pdp_curve_values_must_be_finite`, `panel_ice_curves_must_be_non_empty`, `panel_ice_curve_ids_must_be_unique_within_panel`, `panel_ice_curve_x_y_lengths_must_match`, `panel_ice_curve_x_grids_must_match_pdp_curve_x`, `panel_ice_curve_values_must_be_finite`, `panel_reference_values_must_fall_within_pdp_curve_range`, `subgroup_rows_must_be_non_empty`, `subgroup_panel_label_must_be_distinct_from_top_panel_labels`, `subgroup_rows_must_match_panels_by_panel_id`, `subgroup_row_ids_must_be_unique`, `subgroup_row_labels_must_be_unique`, `subgroup_row_intervals_must_wrap_estimate`, `subgroup_row_support_n_must_be_positive`

### `accumulated_local_effects_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Accumulated Local Effects Panel
- Templates: `fenggaolab.org.medical-display-core::accumulated_local_effects_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `ale_curve`, `local_effect_bins`
- Optional collection fields: None
- Required nested collection fields: `panels.ale_curve` -> `x`, `y`<br>`panels.local_effect_bins` -> `bin_id`, `bin_left`, `bin_right`, `bin_center`, `local_effect`, `support_count`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_not_exceed_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_features_must_be_unique`, `panel_reference_labels_must_be_non_empty`, `panel_reference_values_must_be_finite`, `panel_ale_curve_must_have_matching_x_y_lengths`, `panel_ale_curve_x_must_be_strictly_increasing`, `panel_ale_curve_values_must_be_finite`, `panel_local_effect_bins_must_be_non_empty`, `panel_local_effect_bin_ids_must_be_unique_within_panel`, `panel_local_effect_bins_must_be_strictly_ordered_and_non_overlapping`, `panel_local_effect_values_must_be_finite`, `panel_local_effect_support_counts_must_be_positive`, `panel_ale_curve_x_must_match_bin_centers`, `panel_ale_curve_must_match_cumulative_local_effects`, `panel_reference_values_must_fall_within_declared_bin_range`

### `feature_response_support_domain_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Feature Response Support Domain Panel
- Templates: `fenggaolab.org.medical-display-core::feature_response_support_domain_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `y_label`, `panels`
- Optional display fields: `paper_role`
- Required collection fields: `panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `response_curve`, `support_segments`
- Optional collection fields: None
- Required nested collection fields: `panels.response_curve` -> `x`, `y`<br>`panels.support_segments` -> `segment_id`, `segment_label`, `support_kind`, `domain_start`, `domain_end`
- Optional nested collection fields: None
- Additional constraints: `panels_must_be_non_empty`, `panel_count_must_be_between_two_and_three`, `panel_ids_must_be_unique`, `panel_labels_must_be_unique`, `panel_features_must_be_unique`, `panel_reference_labels_must_be_non_empty`, `panel_reference_values_must_be_finite`, `panel_response_curve_must_have_matching_x_y_lengths`, `panel_response_curve_x_must_be_strictly_increasing`, `panel_response_curve_values_must_be_finite`, `panel_support_segments_must_be_non_empty`, `panel_support_segment_ids_must_be_unique_within_panel`, `panel_support_segment_labels_must_be_non_empty`, `panel_support_segment_kinds_must_be_supported`, `panel_support_segments_must_be_strictly_ordered_and_non_overlapping`, `panel_support_segments_must_cover_curve_range`, `panel_reference_values_must_fall_within_response_curve_range`

### `shap_grouped_local_support_domain_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Grouped Local Support-Domain Panel
- Templates: `fenggaolab.org.medical-display-core::shap_grouped_local_support_domain_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `grouped_local_x_label`, `support_y_label`, `support_legend_title`, `local_panels`, `support_panels`
- Optional display fields: `paper_role`
- Required collection fields: `local_panels` -> `panel_id`, `panel_label`, `title`, `group_label`, `baseline_value`, `predicted_value`, `contributions`<br>`support_panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `response_curve`, `support_segments`
- Optional collection fields: None
- Required nested collection fields: `local_panels.contributions` -> `rank`, `feature`, `shap_value`<br>`support_panels.response_curve` -> `x`, `y`<br>`support_panels.support_segments` -> `segment_id`, `segment_label`, `support_kind`, `domain_start`, `domain_end`
- Optional nested collection fields: None
- Additional constraints: `local_panels_must_be_non_empty`, `local_panel_count_must_be_between_two_and_three`, `local_panel_ids_must_be_unique`, `local_panel_labels_must_be_unique`, `local_panel_group_labels_must_be_unique`, `local_panel_values_must_be_finite`, `local_panel_contributions_must_be_non_empty`, `local_panel_contribution_ranks_must_be_strictly_increasing`, `local_panel_contribution_features_must_be_unique_within_panel`, `local_panel_contribution_values_must_be_finite_and_non_zero`, `local_panel_prediction_value_must_equal_baseline_plus_contributions`, `local_panel_feature_orders_must_match_across_panels`, `support_panels_must_be_non_empty`, `support_panel_count_must_equal_two`, `support_panel_ids_must_be_unique`, `support_panel_labels_must_be_unique_and_distinct_from_local_panel_labels`, `support_panel_labels_must_be_distinct_from_local_panel_labels`, `support_panel_features_must_be_unique`, `support_panel_reference_labels_must_be_non_empty`, `support_panel_reference_values_must_be_finite`, `support_panel_response_curve_must_have_matching_x_y_lengths`, `support_panel_response_curve_x_must_be_strictly_increasing`, `support_panel_response_curve_values_must_be_finite`, `support_panel_support_segments_must_be_non_empty`, `support_panel_support_segment_ids_must_be_unique_within_panel`, `support_panel_support_segment_kinds_must_be_supported`, `support_panel_support_segments_must_be_strictly_ordered_and_non_overlapping`, `support_panel_support_segments_must_cover_curve_range`, `support_panel_reference_values_must_fall_within_response_curve_range`, `support_panel_features_must_be_subset_of_local_feature_order`

### `shap_multigroup_decision_path_support_domain_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Multigroup Decision Path Support-Domain Panel
- Templates: `fenggaolab.org.medical-display-core::shap_multigroup_decision_path_support_domain_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `decision_panel_title`, `decision_x_label`, `decision_y_label`, `decision_legend_title`, `support_y_label`, `support_legend_title`, `baseline_value`, `groups`, `support_panels`
- Optional display fields: `paper_role`
- Required collection fields: `groups` -> `group_id`, `group_label`, `predicted_value`, `contributions`<br>`support_panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `response_curve`, `support_segments`
- Optional collection fields: None
- Required nested collection fields: `groups.contributions` -> `rank`, `feature`, `shap_value`<br>`support_panels.response_curve` -> `x`, `y`<br>`support_panels.support_segments` -> `segment_id`, `segment_label`, `support_kind`, `domain_start`, `domain_end`
- Optional nested collection fields: None
- Additional constraints: `group_count_must_equal_three`, `group_ids_must_be_unique`, `group_labels_must_be_unique`, `baseline_value_must_be_finite`, `group_prediction_value_must_equal_baseline_plus_contributions`, `group_contribution_ranks_must_be_strictly_increasing`, `group_contribution_values_must_be_finite_and_non_zero`, `group_feature_orders_must_match`, `support_panel_count_must_equal_two`, `support_panel_ids_must_be_unique`, `support_panel_labels_must_be_unique`, `support_panel_features_must_be_unique`, `support_panel_reference_labels_must_be_non_empty`, `support_panel_reference_values_must_be_finite`, `support_panel_response_curve_must_have_matching_x_y_lengths`, `support_panel_response_curve_x_must_be_strictly_increasing`, `support_panel_response_curve_values_must_be_finite`, `support_panel_support_segments_must_be_non_empty`, `support_panel_support_segment_ids_must_be_unique_within_panel`, `support_panel_support_segment_labels_must_be_non_empty`, `support_panel_support_segment_kinds_must_be_supported`, `support_panel_support_segments_must_be_strictly_ordered_and_non_overlapping`, `support_panel_support_segments_must_cover_curve_range`, `support_panel_reference_values_must_fall_within_response_curve_range`, `support_panel_features_must_be_subset_of_group_feature_order`, `support_panel_feature_order_must_follow_group_feature_order`

### `shap_signed_importance_local_support_domain_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: SHAP Signed Importance Local Support-Domain Panel
- Templates: `fenggaolab.org.medical-display-core::shap_signed_importance_local_support_domain_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `support_y_label`, `support_legend_title`, `importance_panel`, `local_panel`, `support_panels`
- Optional display fields: `paper_role`
- Required collection fields: `importance_panel.bars` -> `rank`, `feature`, `signed_importance_value`<br>`local_panel.contributions` -> `feature`, `shap_value`<br>`support_panels` -> `panel_id`, `panel_label`, `title`, `x_label`, `feature`, `reference_value`, `reference_label`, `response_curve`, `support_segments`
- Optional collection fields: None
- Required nested collection fields: `support_panels.response_curve` -> `x`, `y`<br>`support_panels.support_segments` -> `segment_id`, `segment_label`, `support_kind`, `domain_start`, `domain_end`
- Optional nested collection fields: None
- Additional constraints: `importance_panel_requires_panel_id_panel_label_title_x_label_and_direction_labels`, `importance_bars_must_be_non_empty`, `importance_bar_ranks_must_be_strictly_increasing`, `importance_bar_features_must_be_unique`, `importance_bar_values_must_be_finite_non_zero_and_sorted_by_descending_absolute_magnitude`, `local_panel_requires_panel_id_panel_label_title_case_label_x_label_baseline_and_prediction`, `local_panel_values_must_be_finite`, `local_panel_contributions_must_be_non_empty`, `local_panel_contribution_features_must_be_unique`, `local_panel_prediction_value_must_equal_baseline_plus_contributions`, `support_panel_count_must_equal_two`, `support_panel_ids_must_be_unique`, `support_panel_labels_must_be_unique_and_distinct_from_importance_and_local_labels`, `support_panel_features_must_be_unique`, `support_panel_reference_labels_must_be_non_empty`, `support_panel_reference_values_must_be_finite`, `support_panel_response_curve_must_have_matching_x_y_lengths`, `support_panel_response_curve_x_must_be_strictly_increasing`, `support_panel_response_curve_values_must_be_finite`, `support_panel_support_segments_must_be_non_empty`, `support_panel_support_segment_ids_must_be_unique_within_panel`, `support_panel_support_segment_labels_must_be_non_empty`, `support_panel_support_segment_kinds_must_be_supported`, `support_panel_support_segments_must_be_strictly_ordered_and_non_overlapping`, `support_panel_support_segments_must_cover_curve_range`, `support_panel_reference_values_must_fall_within_response_curve_range`, `local_panel_features_must_be_subset_of_global_feature_order`, `local_panel_feature_order_must_follow_global_feature_order`, `support_panel_features_must_be_subset_of_global_feature_order`, `support_panel_feature_order_must_follow_global_feature_order`

### `multicenter_generalizability_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Multicenter Generalizability Overview
- Templates: `fenggaolab.org.medical-display-core::multicenter_generalizability_overview`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `overview_mode`, `center_event_y_label`, `coverage_y_label`, `center_event_counts`, `coverage_panels`
- Optional display fields: `paper_role`
- Required collection fields: `center_event_counts` -> `center_label`, `split_bucket`, `event_count`<br>`coverage_panels` -> `panel_id`, `title`, `layout_role`, `bars`
- Optional collection fields: None
- Required nested collection fields: `coverage_panels.bars` -> `label`, `count`
- Optional nested collection fields: None
- Additional constraints: `overview_mode_must_be_center_support_counts`, `center_event_counts_must_be_non_empty`, `center_event_counts_labels_must_be_unique`, `center_event_counts_must_be_non_negative`, `coverage_panels_must_be_non_empty`, `coverage_panel_ids_must_be_unique`, `coverage_panel_layout_roles_must_cover_wide_left_top_right_bottom_right`, `coverage_panel_bars_must_be_non_empty`, `coverage_panel_bars_must_be_non_negative`

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

### `center_transportability_governance_summary_panel_inputs_v1`

- Display kind: `evidence_figure`
- Display name: Center Transportability Governance Summary Panel
- Templates: `fenggaolab.org.medical-display-core::center_transportability_governance_summary_panel`
- Required top-level fields: `schema_version`, `input_schema_id`, `displays`
- Optional top-level fields: None
- Required display fields: `display_id`, `template_id`, `title`, `caption`, `metric_family`, `metric_panel_title`, `metric_x_label`, `metric_reference_value`, `batch_shift_threshold`, `slope_acceptance_lower`, `slope_acceptance_upper`, `oe_ratio_acceptance_lower`, `oe_ratio_acceptance_upper`, `summary_panel_title`, `centers`
- Optional display fields: `paper_role`
- Required collection fields: `centers` -> `center_id`, `center_label`, `cohort_role`, `support_count`, `event_count`, `metric_estimate`, `metric_lower`, `metric_upper`, `max_shift`, `slope`, `oe_ratio`, `verdict`, `action`
- Optional collection fields: `centers` -> `detail`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `metric_family_must_be_supported`, `metric_reference_value_must_be_finite`, `batch_shift_threshold_must_be_positive_finite`, `slope_acceptance_band_must_be_positive_finite_and_ordered`, `oe_ratio_acceptance_band_must_be_positive_finite_and_ordered`, `centers_must_be_non_empty`, `center_ids_must_be_unique`, `center_labels_must_be_unique`, `center_support_counts_must_be_positive_integers`, `center_event_counts_must_be_non_negative_integers`, `center_event_counts_must_not_exceed_support_counts`, `center_metric_values_must_be_finite`, `center_metric_intervals_must_wrap_estimate`, `center_max_shift_must_be_probability`, `center_slopes_must_be_positive_finite`, `center_oe_ratios_must_be_positive_finite`, `center_verdicts_must_be_supported`, `center_actions_must_be_non_empty`, `center_detail_must_be_non_empty_when_present`

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

### `workflow_fact_sheet_panel_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Workflow Fact Sheet Panel
- Templates: `fenggaolab.org.medical-display-core::workflow_fact_sheet_panel`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `sections`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `sections` -> `section_id`, `panel_label`, `title`, `layout_role`, `facts`
- Optional collection fields: None
- Required nested collection fields: `sections.facts` -> `fact_id`, `label`, `value`
- Optional nested collection fields: `sections.facts` -> `detail`
- Additional constraints: `sections_must_contain_exactly_four_items`, `section_ids_must_be_unique`, `section_panel_labels_must_be_unique`, `section_layout_roles_must_match_four_panel_fact_sheet_grid`, `section_facts_must_be_non_empty`, `section_fact_ids_must_be_unique_within_section`

### `design_evidence_composite_shell_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Design Evidence Composite Shell
- Templates: `fenggaolab.org.medical-display-core::design_evidence_composite_shell`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `workflow_stages`, `summary_panels`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `workflow_stages` -> `stage_id`, `title`<br>`summary_panels` -> `panel_id`, `panel_label`, `title`, `layout_role`, `cards`
- Optional collection fields: None
- Required nested collection fields: `summary_panels.cards` -> `card_id`, `label`, `value`
- Optional nested collection fields: `workflow_stages` -> `detail`<br>`summary_panels.cards` -> `detail`
- Additional constraints: `workflow_stages_must_contain_three_or_four_items`, `workflow_stage_ids_must_be_unique`, `summary_panels_must_contain_exactly_three_items`, `summary_panel_ids_must_be_unique`, `summary_panel_labels_must_be_unique`, `summary_panel_layout_roles_must_match_three_panel_composite`, `summary_panel_cards_must_be_non_empty`, `summary_panel_card_ids_must_be_unique_within_panel`

### `baseline_missingness_qc_panel_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Baseline Missingness QC Panel
- Templates: `fenggaolab.org.medical-display-core::baseline_missingness_qc_panel`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `balance_panel_title`, `balance_x_label`, `balance_threshold`, `primary_balance_label`, `balance_variables`, `missingness_panel_title`, `missingness_x_label`, `missingness_y_label`, `missingness_rows`, `missingness_columns`, `missingness_cells`, `qc_panel_title`, `qc_cards`
- Optional top-level fields: `caption`, `secondary_balance_label`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `balance_variables` -> `variable_id`, `label`, `primary_value`<br>`missingness_rows` -> `label`<br>`missingness_columns` -> `label`<br>`missingness_cells` -> `x`, `y`, `value`<br>`qc_cards` -> `card_id`, `label`, `value`
- Optional collection fields: `balance_variables` -> `secondary_value`<br>`qc_cards` -> `detail`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `balance_variables_must_be_non_empty`, `balance_variable_ids_must_be_unique`, `balance_variable_labels_must_be_unique`, `balance_primary_values_must_be_finite_non_negative`, `balance_secondary_values_require_secondary_label`, `balance_secondary_values_must_be_finite_non_negative`, `balance_threshold_must_be_positive_finite`, `missingness_rows_must_be_non_empty`, `missingness_row_labels_must_be_unique`, `missingness_columns_must_be_non_empty`, `missingness_column_labels_must_be_unique`, `missingness_cells_must_be_non_empty`, `missingness_cell_values_must_be_probability`, `declared_missingness_rows_must_match_cells`, `declared_missingness_columns_must_match_cells`, `declared_missingness_grid_must_be_complete_and_unique`, `qc_cards_must_be_non_empty`, `qc_card_ids_must_be_unique`

### `center_coverage_batch_transportability_panel_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Center Coverage Batch Transportability Panel
- Templates: `fenggaolab.org.medical-display-core::center_coverage_batch_transportability_panel`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `coverage_panel_title`, `coverage_x_label`, `center_rows`, `batch_panel_title`, `batch_x_label`, `batch_y_label`, `batch_threshold`, `batch_rows`, `batch_columns`, `batch_cells`, `transportability_panel_title`, `transportability_cards`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `center_rows` -> `center_id`, `center_label`, `cohort_role`, `support_count`, `event_count`<br>`batch_rows` -> `label`<br>`batch_columns` -> `label`<br>`batch_cells` -> `x`, `y`, `value`<br>`transportability_cards` -> `card_id`, `label`, `value`
- Optional collection fields: `transportability_cards` -> `detail`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `center_rows_must_be_non_empty`, `center_row_ids_must_be_unique`, `center_row_labels_must_be_unique`, `center_support_counts_must_be_positive_integers`, `center_event_counts_must_be_non_negative_integers`, `center_event_counts_must_not_exceed_support_counts`, `batch_threshold_must_be_positive_finite`, `batch_rows_must_be_non_empty`, `batch_row_labels_must_be_unique`, `batch_columns_must_be_non_empty`, `batch_column_labels_must_be_unique`, `batch_cells_must_be_non_empty`, `batch_cell_values_must_be_probability`, `declared_batch_rows_must_match_cells`, `declared_batch_columns_must_match_cells`, `declared_batch_grid_must_be_complete_and_unique`, `transportability_cards_must_be_non_empty`, `transportability_card_ids_must_be_unique`

### `transportability_recalibration_governance_panel_inputs_v1`

- Display kind: `illustration_shell`
- Display name: Transportability Recalibration Governance Panel
- Templates: `fenggaolab.org.medical-display-core::transportability_recalibration_governance_panel`
- Required top-level fields: `schema_version`, `shell_id`, `display_id`, `title`, `coverage_panel_title`, `coverage_x_label`, `center_rows`, `batch_panel_title`, `batch_x_label`, `batch_y_label`, `batch_threshold`, `batch_rows`, `batch_columns`, `batch_cells`, `recalibration_panel_title`, `slope_acceptance_lower`, `slope_acceptance_upper`, `oe_ratio_acceptance_lower`, `oe_ratio_acceptance_upper`, `recalibration_rows`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `center_rows` -> `center_id`, `center_label`, `cohort_role`, `support_count`, `event_count`<br>`batch_rows` -> `label`<br>`batch_columns` -> `label`<br>`batch_cells` -> `x`, `y`, `value`<br>`recalibration_rows` -> `center_id`, `slope`, `oe_ratio`, `action`
- Optional collection fields: `recalibration_rows` -> `detail`
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `center_rows_must_be_non_empty`, `center_row_ids_must_be_unique`, `center_row_labels_must_be_unique`, `center_support_counts_must_be_positive_integers`, `center_event_counts_must_be_non_negative_integers`, `center_event_counts_must_not_exceed_support_counts`, `batch_threshold_must_be_positive_finite`, `batch_rows_must_be_non_empty`, `batch_row_labels_must_be_unique`, `batch_columns_must_be_non_empty`, `batch_column_labels_must_be_unique`, `batch_cells_must_be_non_empty`, `batch_cell_values_must_be_probability`, `declared_batch_rows_must_match_cells`, `declared_batch_columns_must_match_cells`, `declared_batch_grid_must_be_complete_and_unique`, `slope_acceptance_band_must_be_positive_finite_and_ordered`, `oe_ratio_acceptance_band_must_be_positive_finite_and_ordered`, `recalibration_rows_must_be_non_empty`, `recalibration_row_center_ids_must_be_unique`, `recalibration_row_center_ids_must_reference_declared_centers`, `recalibration_rows_must_cover_declared_centers`, `recalibration_slopes_must_be_positive_finite`, `recalibration_oe_ratios_must_be_positive_finite`

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

### `time_to_event_performance_summary_v1`

- Display kind: `table_shell`
- Display name: Time-to-Event Performance Summary Table
- Templates: `fenggaolab.org.medical-display-core::table2_time_to_event_performance_summary`
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
- Templates: `fenggaolab.org.medical-display-core::table3_clinical_interpretation_summary`
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
- Templates: `fenggaolab.org.medical-display-core::performance_summary_table_generic`
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
- Templates: `fenggaolab.org.medical-display-core::grouped_risk_event_summary_table`
- Required top-level fields: `schema_version`, `table_shell_id`, `display_id`, `title`, `surface_column_label`, `stratum_column_label`, `cases_column_label`, `events_column_label`, `risk_column_label`, `rows`
- Optional top-level fields: `caption`
- Required display fields: None
- Optional display fields: None
- Required collection fields: `rows` -> `row_id`, `surface`, `stratum`, `cases`, `events`, `risk_display`
- Optional collection fields: None
- Required nested collection fields: None
- Optional nested collection fields: None
- Additional constraints: `surface_column_label_must_be_non_empty`, `stratum_column_label_must_be_non_empty`, `cases_column_label_must_be_non_empty`, `events_column_label_must_be_non_empty`, `risk_column_label_must_be_non_empty`, `rows_must_be_non_empty`, `row_surface_must_be_non_empty`, `row_stratum_must_be_non_empty`, `row_cases_must_be_positive_integer`, `row_events_must_be_integer_between_zero_and_cases`, `row_risk_display_must_match_events_over_cases_percent_1dp`
