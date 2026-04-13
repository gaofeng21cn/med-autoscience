# 医学绘图军火库扩充历史

## 文档定位

本文记录绘图军火库是如何一步一步扩出来的，重点回答五个问题：

1. 什么时间扩充了什么；
2. 这次扩充是从哪篇论文、哪类图面、哪条真实需求学来的；
3. 这次扩充提升了哪个论文家族；
4. 具体落成了哪个模板、契约、质控或回归能力；
5. 当前这次扩充处于什么状态。

与 [medical_display_arsenal.md](./medical_display_arsenal.md) 的分工是：

- `medical_display_arsenal.md` 记录“现在军火库里有什么”；
- 本文记录“这些能力是怎么学会的、什么时候学会的”。

## 记录口径

说明：

- 本文保留历史阶段决策与冻结事件；
- 若历史里出现“终止自动续跑”“显式重开才继续”这类治理口径，应优先按后续 `continuous mainline / rolling hardening` 文档解释；
- 也就是说，历史事件保留，但其治理口径可能已被后续主线文档 supersede。

本文按绘图主线的已验证里程碑记录，不按共享 `main` 当时是否已经完全吸收来记账。

当前历史锚点以以下边界为准：

- `acd5734`：锚点论文收口真相固化
- `f32d7f7`：锚点论文收口吸收到主线
- `6965385`：`A/B/H` 跨论文加固
- `1b5b1bd` / `9a74154`：`G` 家族首个审计基线
- `0891811`：`B` 家族分层累计发生率面板
- `9209ebc`：`B` 家族多窗口 ROC 面板
- `f8d2e0c`：复合面板 token 对齐加固
- `474ee02`：性能热图
- `3cc2a19`：冻结交棒收口

## 正式落地的扩充时间线

| 日期 | 里程碑 | 来源 | 学到并固化了什么 | 提升到的家族 / 模板 | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| `2026-04-05` | 锚点论文收口真相固化 | 内部锚点论文 `001` 与 `003` | 明确 `paper/` 为长期 authority surface；回填 `figure_catalog`、`table_catalog`、`submission_minimal`；补齐 `003` 的两类表格壳层能力；把真实论文已经证明的图表面正式提升为审计真相 | `A/B/H` 论文实战基线；`binary_calibration_decision_curve_panel`、`time_to_event_discrimination_calibration_panel`、`time_to_event_risk_group_summary`、`time_to_event_decision_curve`、`multicenter_generalizability_overview`、`submission_graphical_abstract`、`performance_summary_table_generic`、`grouped_risk_event_summary_table` | 已成为锚点论文收口真相 |
| `2026-04-06` | 锚点论文收口吸收到主线 | `medical-display-anchor-paper-closure` 收口成果 | 把锚点论文收口成果从独立工作线吸收到主线，为后续跨论文加固提供公共起点 | `A/B/H` 主线共同基座 | 已并入主线 |
| `2026-04-06` | `A/B/H` 跨论文确定性加固 | `001/003` 真实论文暴露的失败模式 | 把标题策略、注释落位、`panel label` / `header band` 锚定、图形摘要箭头通道、坐标窗拟合、多中心图例可读性等问题从“论文现场修图经验”提升为可复用回归真相 | `A/B/H`；跨论文 golden regression 基线 | 已落成 `6965385` |
| `2026-04-06` | `G` 家族首个专用审计基线 | 组学原生证据需求，不再允许隐式借用 `E` 家族热图 | 新增 `gsva_ssgsea_heatmap` 与专用输入契约，要求 `score_method`，把 `G` 从“被邻近热图顺带覆盖”升级为独立可审计能力 | `G` / `gsva_ssgsea_heatmap` | 已落成 `1b5b1bd`，clean baseline 锚点为 `9a74154` |
| `2026-04-06` | `B` 家族分层累计发生率面板 | `HTN-AI` 图 3 | 把单一累计发生曲线提升为显式多面板、多分层累计发生率契约，并补齐 panel 级 schema、layout QC、readability 检查 | `B` / `time_to_event_stratified_cumulative_incidence_panel` | 已落成 `0891811` |
| `2026-04-07` | `B` 家族多窗口 ROC 面板 | `Nature Medicine` 风险论文图 4a | 把单时间窗 ROC 升级为显式多窗口、多面板 ROC 契约，让时间窗语义从输入到渲染和质控全程可审计 | `A/B` / `time_dependent_roc_comparison_panel` | 已落成 `9209ebc` |
| `2026-04-07` | 复合面板 token 对齐加固 | 前一轮多窗口 ROC 落地后的工程收口 | 统一 renderer 与 QC 对 `panel_label` 的 token 规则，防止空格或标点导致 sidecar、box id 与质控错配 | `B` 复合面板体系；`time_dependent_roc_comparison_panel`、`time_to_event_stratified_cumulative_incidence_panel` | 已落成 `f8d2e0c` |
| `2026-04-07` | 性能热图正式入库 | `Nature Medicine` 风险论文图 4c | 把普通矩阵热图提升为有固定行列顺序、有指标语义、有数值边界的性能热图契约 | `B/E` / `performance_heatmap` | 已落成 `474ee02` |
| `2026-04-07` | 主线冻结收口 | 绘图主线治理决策 | 同步 `F` 家族延期重开决策、固定冻结交棒边界、终止自动续跑，为未来显式重开保留干净入口 | 主线治理；不新增模板 | 已落成 `3cc2a19` |
| `2026-04-08` | `D/E/G` 细胞类型-签名复合热图正式入库 | 真实论文复合图谱交付需求 + `Nature Medicine` `2025` 炎症图谱图 1 + `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 | 把单独的 embedding scatter 与程序/签名热图组合，提升为正式 `celltype/program` 复合模板；固定 `score_method`、embedding group ↔ heatmap column 对齐、完整行列网格、legend/colorbar 锚定，并补齐 python renderer、layout QC 与 golden regression | `D/E/G` / `celltype_signature_heatmap` | 已正式入库，作为 post-baseline rolling expansion 的首个复合图谱切片 |
| `2026-04-08` | `A/B` landmark performance + Brier/error 三联治理正式入库 | 真实时间事件论文交付需求 + `Nature Communications` `2021` ctDNA 动态复发风险研究 | 把 forward landmark windows 的 discrimination、Brier score 与 calibration slope 从稿件现场自由拼图提升为统一的三联 summary 模板；同时补齐输入契约、python renderer、layout QC 与 A/B golden regression 锁定 | `A/B` / `time_to_event_landmark_performance_panel` | 已正式入库，作为 post-baseline rolling expansion 的第二个 capability cluster |
| `2026-04-08` | `F` 家族 SHAP dependence 面板正式入库 | 真实解释型论文交付需求 + `npj Digital Medicine` `2025` SHAP dependence exemplar | 把单一 summary beeswarm 之外的局部 dependence explanation 提升为正式多 panel 模板；固定 panel feature 唯一性、point finite contract、shared colorbar label、zero-line guide 与 F 家族 golden regression 锁定 | `F` / `shap_dependence_panel` | 已正式入库，作为 post-baseline rolling expansion 的第三个 capability cluster |
| `2026-04-08` | `A/B` threshold summary + grouped survival calibration governance 正式入库 | 真实 deployment-facing 生存论文交付需求 + `Nature Medicine` `2025` 结直肠手术 AI 决策支持论文图 4a-d + `npj Digital Medicine` `2025` RCC / 胃癌预后论文图 2/5 | 把 threshold summary cards 与 grouped survival calibration governance 从稿件现场组合图提升为统一的 pack 模板；固定 threshold label 唯一性、threshold strict order、risk-group finite probability、card/panel anchoring、calibration point fail-closed，并补齐 python renderer、layout QC 与 A/B golden regression 锁定 | `A/B` / `time_to_event_threshold_governance_panel` | 已正式入库，作为 post-baseline rolling expansion 的第四个 capability cluster |
| `2026-04-08` | `A/B` multi-horizon grouped calibration governance 正式入库 | 真实 deployment-facing 生存论文交付需求 + `Nature Medicine` `2025` 结直肠手术 AI 决策支持论文图 4a-d + `npj Digital Medicine` `2025` RCC / 胃癌预后论文图 2/5 | 把 `3/5-year` 并列 grouped calibration governance 从单 horizon dumbbell / 阈值组合图内嵌能力提升为正式多 panel 模板；固定 horizon strict order、panel label/id 唯一性、panel 内 group_order 递增、risk finite probability 与 calibration point fail-closed，并补齐 python renderer、layout QC 与 A/B golden regression 锁定 | `A/B` / `time_to_event_multihorizon_calibration_panel` | 已正式入库，作为 post-baseline rolling expansion 的第五个 capability cluster |
| `2026-04-08` | `D/E/G` atlas overview composite 正式入库 | repeated atlas partial-fit + `Genome Research` `2021` tumor immune atlas 图 2 + `Nature Communications` `2023` integrated TME mapping 图 3 | 把 atlas 论文里反复暴露的 `embedding occupancy + group-wise composition shift + marker/signature definition` 从局部拼图提升为正式 3-panel overview 模板；新增 `single_cell_atlas_overview_inputs_v1`、python renderer、layout QC，以及 `D/E/G` golden regression 锁定，并把 composition 完整性、state vocabulary 对齐与 heatmap 网格完备性做成 fail-closed contract | `D/E/G` / `single_cell_atlas_overview_panel` | 已正式入库，作为 post-baseline rolling expansion 的第六个 capability cluster |
| `2026-04-09` | `F` 家族 SHAP patient-level waterfall 正式入库 | 真实解释型论文交付需求 + `npj Digital Medicine` `2025` UMORSS ovarian workflow 图 6 + `JBJS Open Access` `2025` PARITY bone tumor explanation 图 6A/B | 把 patient-level SHAP explanation 从论文现场病例图提升为正式 waterfall 模板；新增 `shap_waterfall_local_explanation_panel_inputs_v1`、python renderer、layout QC 与 F 家族 golden regression 锁定，并把 `baseline -> ordered contributions -> final prediction` additive path、case/panel 唯一性、贡献值有限且非零、方向一致性与 prediction 守恒做成 fail-closed contract | `F` / `shap_waterfall_local_explanation_panel` | 已正式入库，作为 post-baseline rolling expansion 的第七个 capability cluster |
| `2026-04-09` | `C/H` subgroup + generalizability composite 正式入库 | `JAMA Surgery` `2025` multicenter surgical transfusion risk 图 2A/B + `npj Digital Medicine` `2026` postcranioplasty multicenter cohort 图 3/4/5 + `World Psychiatry` `2024` UHR 1000+ 图 2 | 把 subgroup interval 与 multicenter generalizability overview 从两个相邻组件提升为固定两块式 composite；新增 `generalizability_subgroup_composite_inputs_v1`、python renderer、layout QC 与 `C/H` golden regression 锁定，并把 cohort/support completeness、subgroup interval fail-closed、legend 语义、panel label anchoring 与 outboard label containment 做成正式契约 | `C/H` / `generalizability_subgroup_composite_panel` | 已正式入库，作为 post-baseline rolling expansion 的第八个 capability cluster |
| `2026-04-11` | `D/E/G` spatial niche composite 正式入库 | `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `npj Digital Medicine` `2025` tissue-organization exemplar + `Nature Communications` `2023` TME mapping 图 3 | 把 tissue-coordinate niche localization、region-wise niche composition 与 marker/program definition 从多篇论文里的现场复合图提升为统一的 spatial niche 3-panel 模板；新增 `spatial_niche_map_inputs_v1`、python renderer、layout QC 与 `D/E/G` golden regression 锁定，并把 niche vocabulary 对齐、composition 完整性、heatmap 网格完备性与 panel-label anchoring 做成 fail-closed contract | `D/E/G` / `spatial_niche_map_panel` | 已正式入库，作为 post-baseline rolling expansion 的第九个 capability cluster |
| `2026-04-11` | `D/E/G` trajectory progression composite 正式入库 | `Nature Biotechnology` `2023` trajectory exemplar | 把 trajectory / manifold 里的 branch progression、pseudotime-bin composition 与 marker/module kinetics 从论文现场多块拼图提升为统一的 trajectory progression 3-panel 模板；新增 `trajectory_progression_inputs_v1`、python renderer、layout QC 与 `D/E/G` golden regression 锁定，并把 branch vocabulary 对齐、pseudotime-bin completeness、branch-weight sum 与 kinetics heatmap 网格完备性做成 fail-closed contract | `D/E/G` / `trajectory_progression_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十个 capability cluster |
| `2026-04-11` | `F` 家族 SHAP force-like summary 正式入库 | 真实解释型论文交付需求 + SHAP force plot 经典解释图式 | 把代表性病例的局部解释从 waterfall 再推进到 bounded force-like summary；新增 `shap_force_like_summary_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 `baseline marker -> positive/negative directional lanes -> prediction marker`、panel/case 唯一性、标签 containment、方向一致性、贡献排序与预测值守恒做成正式契约 | `F` / `shap_force_like_summary_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十一个 capability cluster |
| `2026-04-12` | `F` 家族 PDP+ICE explanation baseline 正式入库 | 真实解释型论文交付需求 + PDP / ICE 经典解释图式 | 把按特征展开的 marginal response 与 individual trajectory explanation 从候选 follow-on 提升为正式 bounded multi-panel 模板；新增 `partial_dependence_ice_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 `PDP mean + ICE curves`、per-panel reference line/label、shared legend 语义与 panel 内几何 containment 做成正式契约 | `F` / `partial_dependence_ice_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十二个 capability cluster |
| `2026-04-12` | `F` 家族 SHAP bar importance 正式入库 | 真实解释型论文交付需求 + SHAP bar importance 经典解释图式 | 把全局特征重要性总览从“解释章节常见但未正式入库的补位图式”提升为正式 bounded 单 panel 模板；新增 `shap_bar_importance_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 feature unique、rank strict order、importance non-negative finite、bar/value-label sidecar 关联与 panel containment 做成正式契约 | `F` / `shap_bar_importance` | 已正式入库，作为 post-baseline rolling expansion 的第十三个 capability cluster |
| `2026-04-12` | `F` 家族 SHAP signed importance 正式入库 | 真实解释型论文交付需求 + SHAP signed importance / divergent bar 经典解释图式 | 把方向性全局特征重要性总览从“已有全局 importance，但仍缺 polarity 治理”的阶段提升为正式 zero-centered 单 panel 模板；新增 `shap_signed_importance_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 signed polarity、absolute-magnitude strict order、negative/positive direction labels、zero-line side governance 与 polarity-aware value-label containment 做成正式契约 | `F` / `shap_signed_importance_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十四个 capability cluster |
| `2026-04-12` | `F` 家族 SHAP multicohort importance 正式入库 | 真实解释型论文交付需求 + multi-cohort global importance comparison 经典解释图式 | 把跨 cohort 的全局特征重要性对照从“single-cohort global importance 的 follow-on 候选”提升为正式 bounded multi-panel 模板；新增 `shap_multicohort_importance_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 panel/cohort identity、shared feature-order governance、per-panel rank strict order、bar/value-label sidecar 关联与 panel-label anchoring 做成正式契约 | `F` / `shap_multicohort_importance_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十五个 capability cluster |
| `2026-04-12` | `F` 家族 SHAP grouped local explanation 正式入库 | 真实解释型论文交付需求 + grouped local explanation comparison 经典解释图式 | 把 grouped local explanation comparison 从“已有 waterfall / force-like 局部解释，但仍缺共享 feature 顺序的多 panel 对照”的 follow-on 候选提升为正式 bounded multi-panel 模板；新增 `shap_grouped_local_explanation_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 panel/group identity、shared feature-order governance、baseline-plus-contribution conservation、zero-centered signed contribution lanes 与 row-aligned feature/value labels 做成正式契约 | `F` / `shap_grouped_local_explanation_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十六个 capability cluster |
| `2026-04-13` | `F` 家族 pairwise partial-dependence interaction contour 正式入库 | `npj Digital Medicine` `2026` pairwise partial-dependence interaction exemplar + `Nature Communications` `2020` pairwise PDP / interaction reasoning exemplar | 把 pairwise partial-dependence interaction 从论文现场的 3D / pairwise scene 收敛成更适合投稿审计的二维 contour lower bound；新增 `partial_dependence_interaction_contour_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把显式 `x_grid/y_grid`、`response_grid` 维度一致性、shared colorbar、reference crosshair 与 observed-support containment 做成正式契约 | `F` / `partial_dependence_interaction_contour_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十七个 capability cluster |
| `2026-04-13` | `F` 家族 SHAP grouped decision path 正式入库 | 真实解释型论文交付需求 + SHAP decision plot / grouped decision-path 经典解释图式 | 把 grouped decision-path comparison 从“已有 grouped-local comparison，但仍缺共享 baseline 的 cumulative decision path 对照”的 follow-on 候选提升为正式 bounded 单 panel 模板；新增 `shap_grouped_decision_path_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 shared feature-order、baseline reference line、ordered cumulative segments、prediction marker / label 与两组守恒关系做成正式契约 | `F` / `shap_grouped_decision_path_panel` | 已正式入库，作为 post-baseline rolling expansion 的第十八个 capability cluster |
| `2026-04-13` | `F` 家族 higher-order interaction slice 正式入库 | 真实解释型论文交付需求 + higher-order partial-dependence slice 经典解释图式 | 把 higher-order partial-dependence interaction 从“已有 PDP/ICE 与 pairwise contour lower bound，但仍缺固定切片条件下的条件响应图式”的 follow-on 候选提升为正式 bounded multi-panel 模板；新增 `partial_dependence_interaction_slice_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把切片条件、panel feature/slice identity、slice-point finite contract、shared legend 语义与 slice-point containment 做成正式契约 | `F` / `partial_dependence_interaction_slice_panel` | 已正式入库，作为 post-baseline rolling expansion 的第二十一个 capability cluster |
| `2026-04-13` | `F` 家族 subgroup-conditioned PDP comparison 正式入库 | 真实解释型论文交付需求 + subgroup-conditioned partial-dependence 经典解释图式 | 把 subgroup-conditioned partial-dependence comparison 从“已有总体层面的 PDP lower bound，但仍缺分组对照解释图式”的 follow-on 候选提升为正式 bounded multi-panel 模板；新增 `partial_dependence_subgroup_comparison_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 subgroup identity、shared x-domain、estimate/ribbon finite contract、panel-label anchoring 与 subgroup estimate-marker containment 做成正式契约 | `F` / `partial_dependence_subgroup_comparison_panel` | 已正式入库，作为 post-baseline rolling expansion 的第二十二个 capability cluster |
| `2026-04-13` | `F` 家族 accumulated local effects 正式入库 | 真实解释型论文交付需求 + ALE 经典解释图式 | 把 accumulated local effects 从“已有 PDP 系列 lower bound，但仍缺对相关特征更稳健的局部效应表达”的 follow-on 候选提升为正式 bounded 单 panel 模板；新增 `accumulated_local_effects_panel_inputs_v1`、python renderer、layout QC 与 `F` 家族 golden regression 锁定，并把 bin order、bin width、local-effect finite contract、zero/reference guide 与 bin containment 做成正式契约 | `F` / `accumulated_local_effects_panel` | 已正式入库，作为 post-baseline rolling expansion 的第二十三个 capability cluster |
| `2026-04-13` | `H` 家族 workflow fact sheet shell 正式入库 | 真实 manuscript-facing 研究设计摘要需求 + bounded shell hardening 决策 | 把 workflow / study-design summary 从“候选设计证据 shell”收敛成固定 `2x2` section grid 的 manuscript-facing fact sheet；新增 `workflow_fact_sheet_panel_inputs_v1`、python renderer、layout QC 与 shell-catalog materialization 路径，并把 panel-label anchoring、section-title containment、fact label/value containment 做成 fail-closed contract | `H` / `workflow_fact_sheet_panel` | 已正式入库，作为 post-baseline rolling expansion 的首个 bounded illustration-shell follow-on |
| `2026-04-13` | `H` 家族 design-evidence composite shell 正式入库 | 真实 manuscript-facing 研究设计骨架需求 + bounded shell hardening 决策 | 把研究设计摘要从“固定 `2x2` fact sheet”继续推进到带 `workflow ribbon + three summary panels` 的 manuscript-facing bounded composite shell；新增 `design_evidence_composite_shell_inputs_v1`、python renderer、layout QC 与 shell-catalog materialization 路径，并把 workflow-stage containment、panel-label anchoring、summary-title containment 与 card label/value containment 做成 fail-closed contract | `H` / `design_evidence_composite_shell` | 已正式入库，作为 post-baseline rolling expansion 的第二个 bounded illustration-shell follow-on |
| `2026-04-13` | `D/E/G` atlas-spatial bridge composite 正式入库 | `Nature Medicine` `2024` spatial niche exemplar + `Nature Medicine` `2025` atlas-state bridge exemplar + `Nature Communications` `2025` spatial atlas exemplar | 把 atlas 里的状态结构、组织空间里的状态定位、region-wise state composition 与 marker/program definition 从多篇论文里的分块复合图提升为统一的四块式 bridge 模板；新增 `atlas_spatial_bridge_panel_inputs_v1`、python renderer、layout QC 与 `D/E/G` golden regression 锁定，并把 atlas/spatial state vocabulary 对齐、atlas/spatial point 域约束、region composition 完整性、heatmap 网格完备性与四个 panel-label anchor 做成 fail-closed contract | `D/E/G` / `atlas_spatial_bridge_panel` | 已正式入库，作为 post-baseline rolling expansion 的第二十个 capability cluster |
| `2026-04-13` | `D/E/G` atlas-spatial-trajectory storyboard composite 正式入库 | `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `Nature Biotechnology` `2023` trajectory exemplar | 把 atlas、空间与轨迹三条已经分开审计的证据链继续上提为统一的五块式 storyboard 模板；新增 `atlas_spatial_trajectory_storyboard_inputs_v1`、python renderer、layout QC 与 `D/E/G` golden regression 锁定，并把共享 state vocabulary、trajectory branch/bin 治理、region composition 完整性、kinetics heatmap 网格与五个 panel-label anchor 做成 fail-closed contract | `D/E/G` / `atlas_spatial_trajectory_storyboard_panel` | 已正式入库，作为 post-baseline rolling expansion 的第二十四个 capability cluster |

## 已观察、已记录、但尚未正式入库的学习素材

以下素材已经进入绘图主线的视野，并且会影响未来显式重开时的优先级；但它们当前还不是正式军火库的一部分。

| 日期 | 来源 | 看到了什么 | 可能提升的家族 / 模板方向 | 当前状态 |
| --- | --- | --- | --- | --- |
| `2026-04-06` | `Nature Medicine` `2025` 炎症图谱图 1 | 复合式图谱结构、细胞群嵌入、签名热图、跨层叙事组合 | `D/E/G`，尤其是 atlas composite 一类复合图式 | 其中 `embedding + signature heatmap` 与 atlas overview baseline 子能力已于 `2026-04-08` 正式入库；更大 atlas / spatial 多视图变体仍为候选 |
| `2026-04-06` | `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2 | 单细胞嵌入、谱系热图、空间表达与解释性联动 | `D/E/F/G` | 其中 `celltype/program` 复合热图、atlas overview baseline 与 SHAP dependence 子能力已于 `2026-04-08` 正式入库；空间/更深解释联动仍为候选 |
| `2026-04-06` | `Cancer Cell` `2022` 肾脏图谱类图面 | 总体嵌入、主要细胞类型热图、空间上下文并置 | `D/E/G` | 已归档为高价值候选，未正式入库 |
| `2026-04-06` | `Lancet Digital Health` 多癌种风险图 2 | 风险表达与泛化表达的稿件级组合方式 | `A/H` | 低优先级候选，暂未进入主执行线 |

## 这份历史文档的使用方式

后续每次扩库，建议按以下顺序补记：

1. 写清楚这次扩库的日期；
2. 写清楚来源是内部真实论文、外部高水平期刊，还是工程治理决策；
3. 写清楚“学到的结构”是什么，而不是只写“新增了一个模板”；
4. 写清楚提升到了哪个论文家族、哪个模板、哪个质控或哪个回归面；
5. 写清楚当前状态是“已正式入库”“仅候选归档”还是“治理收口”。

这样，军火库扩充就不会退化为零散提交历史，而能长期保留“为什么学、从哪学、学会了什么”的可审计脉络。
