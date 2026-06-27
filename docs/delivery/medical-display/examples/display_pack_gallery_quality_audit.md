# MAS 医学论文配图 Gallery 质量审计

Owner: `MedAutoScience`
Purpose: `human_readable_quality_audit_for_display_pack_gallery`
State: `active_support`
Machine boundary: 人读质量审计。机器真相继续归 Gallery manifest、template descriptor、renderer source、layout sidecar、display lock、publication manifest、真实论文 artifact 和 owner receipt。

## 结论

当前画册定位为 `lower_bound_reference_templates_only`：它提供统一风格、图型结构和程序化出图起点。真实论文 publication-ready 结论由 paper-local visual audit、证据引用检查和 owner receipt 签认；AI 被授权按论文具体主张自由修改结构、排版、标签、配色和组合方式来拔高上限。

- overall_status: `not_publication_ready`
- publication_ready_claim_authorized: `false`
- visual template count: `34`
- reporting flow visual template count: `1`
- design visual template count: `1`
- table preview visual template count: `1`
- total Gallery visual template count: `37`
- non-visual inventory count: `3`
- lower-bound review required: `34`
- blocked evidence templates: `0`
- blocked gallery visual templates: `0`
- publication polish policy: `mas_publication_polish_policy.v1`
- figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`
- composition recipe policy: `mas_medical_figure_composition_recipes.v1`
- composition recipes: `6`
- composition storyboard gallery pages: `6`

## Paper-use 前置检查

- `core_conclusion_and_evidence_chain_locked`
- `paper_local_data_and_statistics_refs_present`
- `semantic_palette_roles_resolved_from_article_style_profile`
- `guide_legend_colorbar_overlap_checked_after_render`
- `final_physical_size_readability_checked`
- `multipanel_hierarchy_and_shared_guides_checked`
- `vector_or_high_resolution_export_recorded`
- `visual_audit_receipt_or_residual_item_recorded`

## 图件工作流前置检查

- `core_conclusion_and_evidence_chain_locked`
- `storyboard_panel_hierarchy_declared`
- `paper_local_data_and_statistics_refs_present`
- `semantic_palette_roles_resolved_from_article_style_profile`
- `rendered_artifact_inspected_at_final_size`
- `guide_legend_colorbar_overlap_checked_after_render`
- `revision_delta_or_residual_item_recorded`
- `visual_audit_receipt_or_residual_item_recorded`
- `owner_or_publication_gate_receipt_present_for_claim_bearing_figures`

## 页面级图页方案前置检查

- `composition_recipe_selected_or_explicitly_declined`
- `hero_panel_role_declared`
- `shared_legend_or_direct_label_strategy_declared`
- `programmatic_evidence_primitives_preserve_data_statistics_refs`

## 通用科研做图 Quality Floor

- policy: `mas_scientific_figure_quality_floor.v1`
- scope: `all_gallery_and_paper_candidate_figures`
- graphical abstract strategy: `brief_first_reference_guided_ai_candidate_not_single_template_reuse`
- AI executor freedom: `ai_may_choose_figure_type_layout_panel_hierarchy_backend_and_candidate_count_from_paper_local_claims`
- template library role: `quality_floor_and_reviewable_starting_point_not_ceiling_or_publication_ready_authority`
- publication ready claim authorized: `false`

Learned patterns:

- `discoverable_skill_pack_with_provenance`
- `figure_brief_before_plotting`
- `reference_selection_and_style_brief`
- `reference_target_preserve_list`
- `candidate_generation_before_owner_gate`
- `critic_review_or_route_back`
- `final_size_readability_inspection`
- `vector_export_when_possible`
- `semantic_palette_and_color_vision_check`
- `source_data_statistics_and_claim_refs_preserved`

Required refs before Gallery or paper use:

- `core_claim_and_evidence_chain_ref`
- `figure_brief_ref`
- `reference_selection_ref`
- `style_brief_ref`
- `preserve_list_ref`
- `candidate_artifact_ref`
- `critic_review_ref`
- `final_size_inspection_ref`
- `source_preservation_ref`
- `owner_gate_ref`

Rebuild boundary:

- `design_shell_graphical_abstract_reporting_flow`: may_be_rebuilt_into_stronger_visual_systems_when_the_figure_brief_and_owner_gate_require_it
- `r_ggplot2_evidence_figures`: raise_quality_through_theme_size_qc_critic_gate_references_and_source_preservation_not_wholesale_manual_redraw

Template-library refactor decision:

- `submission_graphical_abstract`: rebuilt as a single-canvas medical GA preview (`cohort -> risk signal -> care action`) with large online-readable labels, soft semantic colors, SVG source, and layout-QC sidecar. It is still a refs-only lower-bound example, not paper-specific publication authority.
- `r_ggplot2_evidence_figures`: no wholesale visual redraw in this Gallery pass. Current R templates already share the publication theme/palette system; broad redraw would risk visual regression. Reuse work should continue through shared theme, legend, payload-normalization, and QC helpers with before/after screenshots.
- `cohort_flow_figure` and `table1_baseline_characteristics`: remain reporting/table previews with their own authority boundaries; do not force them into the GA visual system.

External learning sources:

- `K-Dense-AI/scientific-agent-skills`
- `Yuan1z0825/nature-skills`
- `google-research/papervizagent`
- `dwzhu-pku/PaperBanana`
- `VILA-Lab/FigMirror`
- `dazhiyang/scientific-plotting-skill`
- `keros68/abstract-fig`
- `kpoduska/GraphicalAbstractTemplate`
- `Figpad/awesome-research-figure-prompts`
- `IyatomiLab/SciGA`

Reference learning lessons:

- [nature_final_submission_artwork](https://www.nature.com/nature/for-authors/final-submission): Use consistent figure lettering, readable reduced-size labels, vector line art when possible, RGB color, and production-quality figure files.
- [ggplot2_theme_system](https://ggplot2.tidyverse.org/reference/theme.html): Use a single theme system for titles, labels, fonts, backgrounds, gridlines, and legends so all evidence figures share one article-level visual grammar.
- [ggsci_npg_palette](https://nanx.me/ggsci/reference/scale_npg.html): Nature Publishing Group inspired discrete palettes are mature ggplot2-compatible references for publication-style categorical roles.
- [colorspace_hcl_palettes](https://colorspace.r-forge.r-project.org/): HCL-based qualitative, sequential and diverging palettes are a stable basis for article-level semantic color roles.
- [viridis_perceptual_palette](https://sjmgarnier.github.io/viridis/): Perceptually uniform and color-vision-friendly sequential palettes are preferred for continuous matrix and density-like encodings.
- [complexheatmap_color_mapping](https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html): Matrix heatmaps need fixed value-to-color mapping rather than per-plot drift; shared sequential and diverging mappings preserve cross-figure comparability.
- [nature_skills_figure_contract](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure): Figure work should start from core conclusion, evidence chain, panel hierarchy, backend-exclusive export, and final visual QA; MAS adapts this into a nonblocking R-first agent contract.
- [scientific_agent_skills_provenance](https://github.com/K-Dense-AI/scientific-agent-skills): Scientific figure skills should be discoverable, task-scoped, and provenance-carrying instead of hidden inside a generic plotting prompt.
- [papervizagent_reference_pipeline](https://github.com/google-research/papervizagent): Reference-driven figure agents separate retrieval, planning, styling, visualization, and critique; MAS adapts this as refs-only quality-floor evidence.
- [paperbanana_candidate_critic_loop](https://github.com/dwzhu-pku/PaperBanana): Academic illustration generation benefits from multiple candidates and critic rounds before owner review rather than single-shot template reuse.
- [figmirror_reference_preserve_list](https://github.com/VILA-Lab/FigMirror): Reference matching needs an explicit preserve list so style transfer does not drift away from claim, evidence, labels, or source constraints.
- [scientific_plotting_skill_hard_rules](https://github.com/dazhiyang/scientific-plotting-skill): Small hard rules for vector export, dimensions, color, typography, and parameter blocks raise the plotting floor without constraining the figure concept.
- [abstract_fig_editable_source](https://github.com/keros68/abstract-fig): Graphical abstract skills are easier to review and revise when the visual source remains editable instead of only producing a flattened image.
- [graphical_abstract_template_three_panel](https://github.com/kpoduska/GraphicalAbstractTemplate): A simple three-panel flow remains useful as a low-risk default only when it is treated as a brief-driven composition skeleton, not a fixed final visual system.
- [figpad_research_prompt_patterns](https://github.com/Figpad/awesome-research-figure-prompts): Prompt collections are most useful when converted into explicit brief, preserve-list, candidate, and critic gates rather than copied as prose prompts.
- [sciga_graphical_abstract_dataset](https://github.com/IyatomiLab/SciGA): Graphical abstracts vary by field and paper intent; a renderer should preserve AI choice of composition while enforcing readable layout and evidence constraints.

## 页面级图页方案

| Recipe | Title | Hero panel | Supporting | Primitive families | Programmatic evidence | Design shell |
| --- | --- | --- | ---: | ---: | --- | --- |
| `clinical_triptych_prediction` | Clinical Prediction Triptych | primary_model_performance_summary | 3 | 5 | `true` | `false` |
| `model_validation_dashboard` | Model Validation Dashboard | validation_summary_or_generalizability | 3 | 7 | `true` | `false` |
| `schematic_led_composite` | Schematic-led Composite | schematic_or_process_hero | 3 | 6 | `true` | `true` |
| `image_plate_plus_quantification` | Image Plate plus Quantification | representative_image_plate | 3 | 5 | `true` | `true` |
| `asymmetric_genomics_figure` | Asymmetric Genomics Figure | dominant_molecular_pattern | 3 | 6 | `true` | `false` |
| `single_cell_atlas_storyboard` | Single-cell or Spatial Atlas Storyboard | cell_state_geometry_or_spatial_context | 3 | 7 | `true` | `false` |

## 数据驱动报告流程图起点

| Template | Category | Renderer | Status | Warnings |
| --- | --- | --- | --- | --- |
| `cohort_flow_figure` | Publication Shells and Tables | r_ggplot2 | `lower_bound_review_required` | `composition_density_risk`, `illustration_shell_style_review_required` |

## 非数据设计图起点

| Template | Category | Renderer | Status | Warnings |
| --- | --- | --- | --- | --- |
| `submission_graphical_abstract` | Publication Shells and Tables | python | `lower_bound_review_required` | `composition_density_risk`, `illustration_shell_style_review_required`, `python_renderer_style_alignment_required` |

## 表格预览图起点

| Template | Category | Renderer | Status | Warnings |
| --- | --- | --- | --- | --- |
| `table1_baseline_characteristics` | Publication Shells and Tables | n/a | `lower_bound_review_required` | `composition_density_risk`, `table_shell_preview_not_table_authority` |

## 高风险图族复核项

| Family | Checks |
| --- | --- |
| `kaplan_meier_with_risk_table` | `risk_table`, `censor_marks`, `time_scale`, `event_definition`, `strata_order` |
| `genomic_landscape_or_oncoprint` | `sample_order`, `annotation_tracks`, `alteration_semantics`, `shared_heatmap_palette` |
| `matrix_heatmap` | `fixed_scale_mapping`, `sequential_vs_diverging_semantics`, `colorbar_tick_density` |
| `shap_and_model_explanation` | `feature_order`, `direction_encoding`, `legend_density`, `panel_claim_mapping` |
| `coefficient_path_or_high_density_lines` | `label_strategy`, `direct_label_or_shared_legend`, `line_density`, `semantic_fit` |
| `multipanel_storyboard` | `hero_panel`, `panel_labels`, `shared_guides`, `remove_non_claim_panels` |

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
| none | 0 |

## 主要风险项

| Warning | Templates |
| --- | ---: |
| `coefficient_path_semantic_fit_review` | 1 |
| `composition_density_risk` | 4 |
| `illustration_shell_style_review_required` | 2 |
| `km_risk_table_and_censor_mark_review` | 1 |
| `legend_or_colorbar_overlap_risk` | 5 |
| `multi_panel_readability_review` | 2 |
| `oncoprint_annotation_track_review` | 1 |
| `python_renderer_style_alignment_required` | 1 |
| `table_shell_preview_not_table_authority` | 1 |

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
| `alluvial_transition` | Longitudinal and Patient Trajectory | r_ggplot2 | `lower_bound_review_required` | none |
| `calibration_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `celltype_marker_dotplot_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `cnv_recurrence_summary_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `coefficient_path_panel` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `composition_stacked_bar` | Population and Baseline | r_ggplot2 | `lower_bound_review_required` | none |
| `confusion_matrix_heatmap_binary` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `correlation_scatter` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `cumulative_incidence_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `decision_curve_binary` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `distribution_violin_box` | Population and Baseline | r_ggplot2 | `lower_bound_review_required` | none |
| `forest_effect_main` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `generalizability_subgroup_composite_panel` | Generalizability | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_consequence_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_landscape_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `heatmap_group_comparison` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `kaplan_meier_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `model_complexity_audit_panel` | Model Audit | r_ggplot2 | `lower_bound_review_required` | none |
| `omics_volcano_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `pathway_enrichment_dotplot_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `pca_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `pr_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `radar_profile` | Population and Baseline | r_ggplot2 | `lower_bound_review_required` | none |
| `risk_layering_monotonic_bars` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `roc_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_dependence_panel` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_summary_beeswarm` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_waterfall_local_explanation_panel` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `time_dependent_roc_horizon` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `time_to_event_decision_curve` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `time_to_event_multihorizon_calibration_panel` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `tsne_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `umap_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `waterfall_response` | Clinical Trial Response and Safety | r_ggplot2 | `lower_bound_review_required` | none |

## 分类完成度

| Category | Status | Completion | Gallery visual | R/ggplot2 evidence | Current Python evidence |
| --- | --- | ---: | ---: | ---: | ---: |
| Clinical Trial Response and Safety | `done` | 100% | 1 | 1 | 0 |
| Clinical Utility | `done` | 100% | 2 | 2 | 0 |
| Data Geometry | `done` | 100% | 3 | 3 | 0 |
| Effect Estimate | `done` | 100% | 3 | 3 | 0 |
| Generalizability | `done` | 100% | 1 | 1 | 0 |
| Genomic and Omics | `done` | 100% | 6 | 6 | 0 |
| Longitudinal and Patient Trajectory | `done` | 100% | 1 | 1 | 0 |
| Matrix Pattern | `done` | 100% | 2 | 2 | 0 |
| Model Audit | `done` | 100% | 1 | 1 | 0 |
| Model Explanation | `done` | 100% | 3 | 3 | 0 |
| Population and Baseline | `done` | 100% | 3 | 3 | 0 |
| Prediction Performance | `done` | 100% | 3 | 3 | 0 |
| Publication Shells and Tables | `done` | 100% | 0 | 0 | 0 |
| Time-to-Event | `done` | 100% | 5 | 5 | 0 |

## 当前 Python 数据证据模板

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | evidence_figure | python | current_pack_retains_no_python_evidence_templates |

## 默认面排除的表格/非图像库存

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | none | none | none |

## 外部准则

- [nature_final_submission_artwork](https://www.nature.com/nature/for-authors/final-submission): Use consistent figure lettering, readable reduced-size labels, vector line art when possible, RGB color, and production-quality figure files.
- [ggplot2_theme_system](https://ggplot2.tidyverse.org/reference/theme.html): Use a single theme system for titles, labels, fonts, backgrounds, gridlines, and legends so all evidence figures share one article-level visual grammar.
- [ggsci_npg_palette](https://nanx.me/ggsci/reference/scale_npg.html): Nature Publishing Group inspired discrete palettes are mature ggplot2-compatible references for publication-style categorical roles.
- [colorspace_hcl_palettes](https://colorspace.r-forge.r-project.org/): HCL-based qualitative, sequential and diverging palettes are a stable basis for article-level semantic color roles.
- [viridis_perceptual_palette](https://sjmgarnier.github.io/viridis/): Perceptually uniform and color-vision-friendly sequential palettes are preferred for continuous matrix and density-like encodings.
- [complexheatmap_color_mapping](https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html): Matrix heatmaps need fixed value-to-color mapping rather than per-plot drift; shared sequential and diverging mappings preserve cross-figure comparability.
- [nature_skills_figure_contract](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure): Figure work should start from core conclusion, evidence chain, panel hierarchy, backend-exclusive export, and final visual QA; MAS adapts this into a nonblocking R-first agent contract.
- [scientific_agent_skills_provenance](https://github.com/K-Dense-AI/scientific-agent-skills): Scientific figure skills should be discoverable, task-scoped, and provenance-carrying instead of hidden inside a generic plotting prompt.
- [papervizagent_reference_pipeline](https://github.com/google-research/papervizagent): Reference-driven figure agents separate retrieval, planning, styling, visualization, and critique; MAS adapts this as refs-only quality-floor evidence.
- [paperbanana_candidate_critic_loop](https://github.com/dwzhu-pku/PaperBanana): Academic illustration generation benefits from multiple candidates and critic rounds before owner review rather than single-shot template reuse.
- [figmirror_reference_preserve_list](https://github.com/VILA-Lab/FigMirror): Reference matching needs an explicit preserve list so style transfer does not drift away from claim, evidence, labels, or source constraints.
- [scientific_plotting_skill_hard_rules](https://github.com/dazhiyang/scientific-plotting-skill): Small hard rules for vector export, dimensions, color, typography, and parameter blocks raise the plotting floor without constraining the figure concept.
- [abstract_fig_editable_source](https://github.com/keros68/abstract-fig): Graphical abstract skills are easier to review and revise when the visual source remains editable instead of only producing a flattened image.
- [graphical_abstract_template_three_panel](https://github.com/kpoduska/GraphicalAbstractTemplate): A simple three-panel flow remains useful as a low-risk default only when it is treated as a brief-driven composition skeleton, not a fixed final visual system.
- [figpad_research_prompt_patterns](https://github.com/Figpad/awesome-research-figure-prompts): Prompt collections are most useful when converted into explicit brief, preserve-list, candidate, and critic gates rather than copied as prose prompts.
- [sciga_graphical_abstract_dataset](https://github.com/IyatomiLab/SciGA): Graphical abstracts vary by field and paper intent; a renderer should preserve AI choice of composition while enforcing readable layout and evidence constraints.
