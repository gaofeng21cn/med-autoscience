# MAS 医学论文配图 Gallery 生成状态

Owner: `MedAutoScience`
Purpose: `generated_display_pack_gallery_status`
State: `generated_active_support`
Machine boundary: 本文由 `scripts/build-display-pack-gallery.py --publish-docs` 从 Gallery manifest / canonical catalog 生成。机器真相继续归 template descriptor、canonical catalog、Gallery manifest、layout sidecar、renderer source、tests、真实论文 artifact、visual-audit receipt、owner receipt 和 publication gate。

## 当前数量口径

| 指标 | 数量 |
| --- | ---: |
| Gallery evidence figures | 35 |
| Gallery reporting flow figures | 1 |
| Gallery design figures | 1 |
| Gallery table preview figures | 1 |
| Gallery visual templates | 38 |
| Current canonical templates | 38 |
| Current non-visual canonical inventory | 3 |
| Retired alias / duplicate ids | 42 |
| Migration index entries | 80 |
| Current Python evidence templates | 0 |
| Page-level composition recipes | 6 |
| Composition storyboard gallery pages | 6 |
| LidocaineQ reference coverage audit | 33/33 |
| LidocaineQ visual parity audit | /Users/gaofeng/workspace/med-autoscience/.worktrees/dm002-display-pdf-repair-20260630/outputs/display-pack-gallery/lidocaineq_visual_parity_audit.md |
| LidocaineQ parity contact sheet | /Users/gaofeng/workspace/med-autoscience/.worktrees/dm002-display-pdf-repair-20260630/outputs/display-pack-gallery/lidocaineq_visual_parity_contact_sheet.png |
| Render cache hit | 0 |
| Render cache miss | 0 |
| Package-only reused assets | 38 |
| Render cache untracked | 0 |

`Gallery evidence figures` 是 PDF 画册中展示的 R/ggplot2 数据证据图数量。`Gallery reporting flow figures` 是结构化人数和排除原因驱动的 cohort/participant flow 起点；其 checked-in renderer 是 R/ggplot2 + `ggconsort`，必须消费 OPL prepared dependency receipt / run-context 后才允许渲染。缺 receipt 或缺 `ggconsort` 时，Gallery 只记录 `not_rendered` typed reason，不回退到 Python generated participant flow，也不宣称已执行 `ggconsort`。`Gallery design figures` 是 graphical abstract 等非统计证据设计图起点。`Composition storyboard gallery pages` 是 PDF/HTML 前段展示的图页级方案数量。`Page-level composition recipes` 是组织多个数据证据面板的图页方案，不是更多单图模板。`Current canonical templates` 是当前可推荐 canonical surface。`Retired alias / duplicate ids` 只用于显式旧 ID 迁移，不是 current template，也不是画册卡片。

Package-only 打包复用状态：`target_already_complete`；复制资产数：`0`；更新资产数：`0`。代码、payload、style profile 或 dependency receipt 未变化时，Gallery 可从既有 assets 重打包 HTML/PDF/docs；真正的渲染 freshness 仍由 render cache key、layout sidecar、dependency run-context 和真实论文 artifact 审计证明。

## 渲染器与质量口径

- gallery default surface: `canonical_current_visual_gallery_templates`
- evidence gallery default surface: `canonical_current_r_ggplot2_evidence_templates`
- reporting flow gallery default surface: `canonical_current_validated_reporting_flow_shells`
- reporting flow dependency profile: `r_ggplot2_ggconsort_reporting_flow_v1`
- reporting flow generated fallback claims ggconsort: `false`
- design gallery default surface: `canonical_current_non_statistical_illustration_shell_templates`
- table preview gallery default surface: `canonical_current_table_shell_preview_templates`
- evidence figures default to R/ggplot2: `true`
- Python illustration shells visible as design cards: `true`
- Python evidence retained without advantage proof: `false`
- style profile: `student_curated_clinical_publication_v1`
- journal palette: `lidocaineq_figure_template_palette_20260621`
- quality overall status: `not_publication_ready`
- publication-ready claim authorized: `false`
- force render: `false`
- package only: `true`
- blocked evidence templates after current render: `0`
- blocked gallery visual templates after current render: `0`
- lower-bound review required: `35`
- gallery lower-bound admission: `gallery_lower_bound_passed_requires_paper_audit`
- publication quality profile coverage: `38/38` (100%)
- publication polish policy: `mas_publication_polish_policy.v1`
- figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`
- composition recipe policy: `mas_medical_figure_composition_recipes.v1`
- LidocaineQ 33 项参考覆盖完整: `true`
- LidocaineQ 33 项逐图视觉审计: `/Users/gaofeng/workspace/med-autoscience/.worktrees/dm002-display-pdf-repair-20260630/outputs/display-pack-gallery/lidocaineq_visual_parity_audit.md`

## LidocaineQ 质量审计面

LidocaineQ 33 项是学习和质量审计输入，不作为 Gallery 永久章节。Gallery 只展示 MAS current canonical templates；逐图视觉对比、差距和修复状态写入独立审计文件与 contact sheet。

| Reference template | MAS current template | Mapping relation | Status |
| --- | --- | --- | --- |
| `survival_km` | `kaplan_meier_grouped` | `renamed_current_template` | `covered` |
| `cumulative_incidence_grouped` | `cumulative_incidence_grouped` | `direct_current_template` | `covered` |
| `roc_auc` | `roc_curve_binary` | `renamed_current_template` | `covered` |
| `time_dependent_roc_horizon` | `time_dependent_roc_horizon` | `direct_current_template` | `covered` |
| `calibration_curve_binary` | `calibration_curve_binary` | `direct_current_template` | `covered` |
| `pr_curve_binary` | `pr_curve_binary` | `direct_current_template` | `covered` |
| `decision_curve_binary` | `decision_curve_binary` | `direct_current_template` | `covered` |
| `time_to_event_decision_curve` | `time_to_event_decision_curve` | `direct_current_template` | `covered` |
| `time_to_event_multihorizon_calibration_panel` | `time_to_event_multihorizon_calibration_panel` | `direct_current_template` | `covered` |
| `forest_cox` | `forest_effect_main` | `renamed_current_template` | `covered` |
| `coefficient_path_panel` | `coefficient_path_panel` | `direct_current_template` | `covered` |
| `generalizability_subgroup_composite_panel` | `generalizability_subgroup_composite_panel` | `direct_current_template` | `covered` |
| `violin_box` | `distribution_violin_box` | `retired_alias_to_current_template` | `covered` |
| `bar_stacked` | `composition_stacked_bar` | `retired_alias_to_current_template` | `covered` |
| `risk_layering_monotonic_bars` | `risk_layering_monotonic_bars` | `direct_current_template` | `covered` |
| `scatter_correlation` | `correlation_scatter` | `retired_alias_to_current_template` | `covered` |
| `embedding_umap_tsne` | `pca_scatter_grouped`, `tsne_scatter_grouped`, `umap_scatter_grouped` | `renamed_current_template` | `covered` |
| `heatmap` | `heatmap_group_comparison` | `renamed_current_template` | `covered` |
| `confusion_matrix_heatmap_binary` | `confusion_matrix_heatmap_binary` | `direct_current_template` | `covered` |
| `volcano_deg` | `omics_volcano_panel` | `renamed_current_template` | `covered` |
| `gsea_enrichment` | `pathway_enrichment_dotplot_panel` | `renamed_current_template` | `covered` |
| `oncoplot_mutation` | `genomic_alteration_landscape_panel` | `renamed_current_template` | `covered` |
| `genomic_alteration_consequence_panel` | `genomic_alteration_consequence_panel` | `direct_current_template` | `covered` |
| `cnv_recurrence_summary_panel` | `cnv_recurrence_summary_panel` | `direct_current_template` | `covered` |
| `waterfall` | `waterfall_response` | `retired_alias_to_current_template` | `covered` |
| `shap_dependence_panel` | `shap_dependence_panel` | `direct_current_template` | `covered` |
| `shap_summary_beeswarm` | `shap_summary_beeswarm` | `direct_current_template` | `covered` |
| `shap_waterfall_local_explanation_panel` | `shap_waterfall_local_explanation_panel` | `direct_current_template` | `covered` |
| `model_complexity_audit_panel` | `model_complexity_audit_panel` | `direct_current_template` | `covered` |
| `celltype_marker_dotplot_panel` | `celltype_marker_dotplot_panel` | `direct_current_template` | `covered` |
| `sankey_alluvial` | `alluvial_transition` | `retired_alias_to_current_template` | `covered` |
| `radar` | `radar_profile` | `retired_alias_to_current_template` | `covered` |
| `baseline_table` | `table1_baseline_characteristics` | `renamed_current_template` | `covered` |

## 数据处理责任

| Responsibility | Current templates |
| --- | ---: |
| `computed_in_template` | 3 |
| `illustration_shell` | 1 |
| `table_shell` | 1 |
| `validated_summary_required` | 33 |

- raw analysis requests fail closed unless the selected template declares `computed_in_template`
- `validated_summary_required` templates render upstream analysis outputs; they do not fit models, recompute curves, run differential testing, infer SHAP values, or call variants

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

## 页面级图页方案

| Recipe | Title | Hero panel | Supporting | Primitive families | Default layout |
| --- | --- | --- | ---: | ---: | --- |
| `clinical_triptych_prediction` | Clinical Prediction Triptych | primary_model_performance_summary | 3 | 5 | one_large_left_panel_with_two_or_three_right_support_panels |
| `model_validation_dashboard` | Model Validation Dashboard | validation_summary_or_generalizability | 3 | 7 | performance_or_generalizability_hero_with_explanation_and_governance_support |
| `schematic_led_composite` | Schematic-led Composite | schematic_or_process_hero | 3 | 6 | schematic_hero_above_or_left_with_small_programmatic_evidence_panels |
| `image_plate_plus_quantification` | Image Plate plus Quantification | representative_image_plate | 3 | 5 | dark_or_neutral_image_plate_with_adjacent_white_background_quantification |
| `asymmetric_genomics_figure` | Asymmetric Genomics Figure | dominant_molecular_pattern | 3 | 6 | wide_pattern_hero_with_narrow_right_or_bottom_consequence_panels |
| `single_cell_atlas_storyboard` | Single-cell or Spatial Atlas Storyboard | cell_state_geometry_or_spatial_context | 3 | 7 | atlas_embedding_or_spatial_hero_with_marker_composition_and_trajectory_support |

## 数据驱动报告流程图 Gallery

| Template | Display name | Renderer | Render status |
| --- | --- | --- | --- |
| `cohort_flow_figure` | Cohort Flow Figure | r_ggplot2 | rendered |

## 非数据设计图 Gallery

| Template | Display name | Renderer | Render status |
| --- | --- | --- | --- |
| `submission_graphical_abstract` | Submission Graphical Abstract | python | rendered |

## 表格预览图 Gallery

| Template | Display name | Renderer | Render status |
| --- | --- | --- | --- |
| `table1_baseline_characteristics` | Table 1 Baseline Characteristics | n/a | rendered |

## 画册分类

| Category | Gallery evidence figures |
| --- | ---: |
| Clinical Trial Response and Safety | 1 |
| Clinical Utility | 2 |
| Data Geometry | 3 |
| Effect Estimate | 3 |
| Generalizability | 2 |
| Genomic and Omics | 6 |
| Longitudinal and Patient Trajectory | 1 |
| Matrix Pattern | 2 |
| Model Audit | 1 |
| Model Explanation | 3 |
| Population and Baseline | 3 |
| Prediction Performance | 3 |
| Time-to-Event | 5 |

## 表格/非图像库存

| Template | Category | Kind |
| --- | --- | --- |
| `cohort_flow_figure` | Publication Shells and Tables | illustration_shell |
| `submission_graphical_abstract` | Publication Shells and Tables | illustration_shell |
| `table1_baseline_characteristics` | Publication Shells and Tables | table_shell |
