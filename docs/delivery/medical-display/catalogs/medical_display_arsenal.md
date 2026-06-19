# 医学绘图军火库总览

Owner: `MedAutoScience`
Purpose: `current_medical_display_arsenal_index`
State: `active_support`
Machine boundary: 本文是当前人读能力索引。机器真相继续归 `display_registry.py`、`display_schema_contract.py`、`display-packs/**/templates/*/template.toml`、`canonical_template_catalog.json`、`renderer_migration_ledger.json`、Gallery manifest、tests、runtime artifacts 和 owner receipts。

## 当前口径

当前默认出图面是 `fenggaolab.org.medical-display-core` 的 canonical Display Pack：

- 当前模板总数：`66`
- evidence figure：`55`，全部为 `renderer_family = "r_ggplot2"` 和 `execution_mode = "subprocess"`
- Python evidence：`0`
- design / flow / graphical abstract illustration shell：`4`，允许 Python composition，但不承载统计证据 authority
- table shell：`7`
- 旧 Python evidence ID 不再维护为当前 pack inventory、Gallery 对比图、agent discover、runtime materialization 或显式请求库存

完整逐项目录由 [medical_display_template_catalog.md](./medical_display_template_catalog.md) 生成；干净 Gallery 和可视示例见 [ggplot2_template_reference.md](../examples/ggplot2_template_reference.md) 与 `ggplot2_template_gallery.pdf`。

## 默认风格

当前内置默认不是 Nature 官方模板复刻，也不是 Lancet/JAMA 专用模板。默认 profile 是 `nature_informed_clinical_publication_v1`：

- 白底、细轴线、弱网格、紧凑 typography；
- 统一 semantic clinical palette；
- matrix heatmap 统一使用 shared sequential / diverging heatmap roles；
- 横向 colorbar 使用统一宽度和低字号，避免 legend / guide 与图面拥挤；
- 数据证据图统一走 R/ggplot2，设计和流程图允许更高表现力的 composition 路线。

AI 可以在模板下限之上做 paper-local 结构、标注、配色和排版改动；模板只提供最低质量地板，不限制最终上限。

## 当前图型家族

| 家族 | 代表用途 | 当前代表模板 |
| --- | --- | --- |
| `A. 预测性能与决策` | ROC/PR、校准、决策曲线、临床影响、二分类混淆矩阵 | `roc_curve_binary`、`pr_curve_binary`、`calibration_curve_binary`、`decision_curve_binary`、`clinical_impact_curve_binary`、`binary_calibration_decision_curve_panel`、`confusion_matrix_heatmap_binary` |
| `B. 生存与时间事件` | KM/累计发生、time-dependent ROC、landmark performance、多窗口校准、风险分层 | `kaplan_meier_grouped`、`cumulative_incidence_grouped`、`time_dependent_roc_horizon`、`time_dependent_roc_comparison_panel`、`time_to_event_discrimination_calibration_panel`、`time_to_event_risk_group_summary`、`time_to_event_landmark_performance_panel`、`time_to_event_multihorizon_calibration_panel` |
| `C. 效应量与异质性` | 主效应、亚组、交互、紧凑多 panel effect summary | `forest_effect_main`、`multivariable_forest`、`subgroup_forest`、`compact_effect_estimate_panel`、`coefficient_path_panel`、`broader_heterogeneity_summary_panel`、`interaction_effect_summary_panel` |
| `D. 表征结构与数据几何` | PCA/UMAP/t-SNE/PHATE/diffusion map 等 embedding 展示 | `umap_scatter_grouped`、`pca_scatter_grouped`、`tsne_scatter_grouped`、`phate_scatter_grouped`、`diffusion_map_scatter_grouped` |
| `E. 特征模式与矩阵` | group heatmap、correlation、clustered heatmap、performance matrix、marker/dotplot | `heatmap_group_comparison`、`correlation_heatmap`、`clustered_heatmap`、`performance_heatmap`、`celltype_marker_dotplot_panel` |
| `F. 模型解释` | SHAP summary/bar/dependence/waterfall/force-like 和模型复杂度审计 | `shap_summary_beeswarm`、`shap_bar_importance`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`shap_force_like_summary_panel`、`shap_multicohort_importance_panel`、`model_complexity_audit_panel` |
| `G. 生物信息与组学证据` | GSVA/ssGSEA、volcano、oncoplot、CNV、genomic landscape、multiomic consequence | `gsva_ssgsea_heatmap`、`omics_volcano_panel`、`oncoplot_mutation_landscape_panel`、`cnv_recurrence_summary_panel`、`genomic_alteration_landscape_panel`、`genomic_alteration_consequence_panel`、`genomic_alteration_multiomic_consequence_panel`、`genomic_alteration_pathway_integrated_composite_panel`、`genomic_program_governance_summary_panel` |
| `H. 队列、泛化性与研究设计` | generalizability/subgroup 复合图、cohort flow、workflow/design shell、baseline/performance tables | `generalizability_subgroup_composite_panel`、`cohort_flow_figure`、`submission_graphical_abstract`、`workflow_fact_sheet_panel`、`design_evidence_composite_shell`、`table1_baseline_characteristics`、`table2_time_to_event_performance_summary`、`table3_clinical_interpretation_summary` |

## 维护规则

- 新增 evidence template 默认必须是 R/ggplot2；Python evidence 只有在证明相对 R/ggplot2 有明确优势、通过视觉审计并作为 current audited template 进入 current pack 后，才允许出现。
- 不为历史兼容保留重复模板；旧 ID 只允许作为仍存在 current 模板的 canonical alias，不维护旧 Python evidence 清单。
- Gallery 默认只展示 canonical family 的代表模板；重复 ROC/KM/heatmap/forest 变体收敛为 alias，不作为用户默认选项。
- 任何声称 publication-ready 的图都必须来自真实 paper payload、render-inspect-revise、visual audit 和 owner/publication gate；模板/Gallery 只能证明质量下限。
