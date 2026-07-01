# 医学绘图军火库总览

Owner: `MedAutoScience`
Purpose: `current_medical_display_arsenal_index`
State: `active_support`
Machine boundary: 本文是当前人读能力索引。机器真相继续归 `display_registry.py`、`display_schema_contract.py`、`display-packs/**/templates/*/template.toml`、`canonical_template_catalog.json`、`renderer_migration_ledger.json`、Gallery manifest、tests、runtime artifacts 和 owner receipts。

## 当前口径

本文只维护医学展示能力的人读索引、图型家族读法和维护规则，不手写 current template / Gallery / retired alias / analysis responsibility 数量。

动态数量和逐项 truth 按以下 owner 读取：

- current canonical template、Gallery evidence / reporting-flow / design / table-preview figure、retired alias、Python evidence、render/package 状态和 analysis responsibility 计数：生成的 ScholarSkills compact gallery review package 与 Gallery manifest；
- 完整 descriptor inventory、每个模板的 renderer family、input schema、QC profile 和 analysis responsibility：生成的 [medical_display_template_catalog.md](./medical_display_template_catalog.md)；
- Display Pack v2 current landed status、E2E path、MAS/OPL handoff 和 forbidden-authority boundary：[display_pack_v2_landing_status.md](../contracts/display_pack_v2_landing_status.md)；
- 人读 Gallery 和可视示例：生成的 ScholarSkills compact gallery review package。

默认用户路径、Gallery、agent discover 和 figure plan 只暴露 current canonical surface。旧 Python evidence ID 不维护为当前 pack inventory、Gallery 对比图、agent discover、runtime materialization 或显式请求库存。

## 默认风格

当前内置默认不是 Nature 官方模板复刻，也不是 Lancet/JAMA 专用模板。默认 profile 是 `nature_informed_clinical_publication_v1`：

- 白底、细轴线、弱网格、紧凑 typography；
- 统一 semantic clinical palette；
- matrix heatmap 统一使用 shared sequential / diverging heatmap roles；
- 横向 colorbar 使用统一宽度和低字号，避免 legend / guide 与图面拥挤；
- 数据证据图统一走 R/ggplot2，设计和流程图允许更高表现力的 composition 路线。

AI 可以在模板下限之上做 paper-local 结构、标注、配色和排版改动；模板只提供最低质量地板，不限制最终上限。

## 分析责任边界

模板不是统计 truth 的第二来源。当前 canonical catalog 给每个模板绑定 `analysis_responsibility`：

- `computed_in_template`：模板 renderer 含受限分析 workflow，可从声明的 raw input 计算展示坐标。目前只用于 `pca_scatter_grouped`、`tsne_scatter_grouped`、`umap_scatter_grouped`，输入状态为 `raw_feature_matrix`。
- `validated_summary_required`：模板只渲染上游已验证 display payload。ROC/PR/calibration/DCA/KM/time-dependent ROC/heatmap/forest/SHAP/omics/模型审计等都属于这一类。
- `illustration_shell`：设计、流程、graphical abstract shell，不承载统计证据 authority。
- `table_shell`：表格 shell，只接受已审阅表格值。

MAS agent 如果收到 `labels_and_scores`、`patient_level_records`、`raw_counts`、`time_status_records` 等 raw analysis input，但推荐模板不是 `computed_in_template`，会 fail closed 到 `analysis_summary_required_before_display_render`，下一步是先物化 validated analysis summary，而不是让画图模板临时重算模型、曲线、p 值、SHAP 或富集结果。

## 当前图型家族

| 家族 | 代表用途 | 当前代表模板 |
| --- | --- | --- |
| `A. 预测性能与决策` | ROC/PR、校准、决策曲线、二分类混淆矩阵 | `roc_curve_binary`、`pr_curve_binary`、`calibration_curve_binary`、`decision_curve_binary`、`confusion_matrix_heatmap_binary` |
| `B. 生存与时间事件` | KM/累计发生、time-dependent ROC、多窗口校准、风险分层 | `kaplan_meier_grouped`、`cumulative_incidence_grouped`、`time_dependent_roc_horizon`、`time_to_event_multihorizon_calibration_panel`、`risk_layering_monotonic_bars`、`time_to_event_decision_curve` |
| `C. 效应量与异质性` | 主效应、亚组、交互、模型路径 | `forest_effect_main`、`coefficient_path_panel` |
| `D. 表征结构与数据几何` | PCA/UMAP/t-SNE 等经典 embedding 展示 | `umap_scatter_grouped`、`pca_scatter_grouped`、`tsne_scatter_grouped` |
| `E. 特征模式与矩阵` | group heatmap、classification matrix、marker/dotplot | `heatmap_group_comparison`、`confusion_matrix_heatmap_binary`、`celltype_marker_dotplot_panel` |
| `F. 模型解释` | SHAP summary/dependence/waterfall 和模型复杂度审计 | `shap_summary_beeswarm`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`model_complexity_audit_panel` |
| `G. 生物信息与组学证据` | volcano、pathway dotplot、CNV、genomic landscape、multiomic consequence | `omics_volcano_panel`、`pathway_enrichment_dotplot_panel`、`cnv_recurrence_summary_panel`、`genomic_alteration_landscape_panel`、`genomic_alteration_consequence_panel` |
| `H. 队列、泛化性与研究设计` | generalizability/subgroup 复合图、cohort flow、graphical abstract、baseline table shell | `generalizability_subgroup_composite_panel`、`cohort_flow_figure`、`submission_graphical_abstract`、`table1_baseline_characteristics` |

## 维护规则

- 新增 evidence template 默认必须是 R/ggplot2；Python evidence 只有在证明相对 R/ggplot2 有明确优势、通过视觉审计并作为 current audited template 进入 current pack 后，才允许出现。
- 不为历史兼容保留重复模板；旧 ID 只允许作为仍存在 current 模板的 canonical alias，不维护旧 Python evidence 清单。
- Gallery 默认只展示 canonical family 的代表模板；重复 ROC/KM/heatmap/forest 变体收敛为 alias，不作为用户默认选项。
- 任何声称 publication-ready 的图都必须来自真实 paper payload、render-inspect-revise、visual audit 和 owner/publication gate；模板/Gallery 只能证明质量下限。
