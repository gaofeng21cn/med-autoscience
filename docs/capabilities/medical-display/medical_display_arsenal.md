# 医学绘图军火库总览

## 文档定位

本文记录 `med-autoscience` 当前已经沉淀下来的医学绘图与表格能力总账，用于回答四个问题：

1. 现在平台已经正式会做什么图、什么表；
2. 哪些能力已经过真实论文验证；
3. 哪些能力来自外部高水平期刊图例的吸收；
4. 下一次继续扩库时，应以什么边界和口径继续。

本文不是逐项输入契约手册，也不是生成式目录的替代物。

- 具体模板、输入契约、渲染器和质控配置，以 [medical_display_template_catalog.md](./medical_display_template_catalog.md) 为准。
- 论文问题层的长期路线，以 [medical_display_family_roadmap.md](./medical_display_family_roadmap.md) 为准。
- 工程审计层的严格真相，以 [medical_display_audit_guide.md](./medical_display_audit_guide.md) 为准。
- 军火库扩充时间线，以 [medical_display_arsenal_history.md](./medical_display_arsenal_history.md) 为准。
- 模板包化与军火库独立演进架构，以 [medical_display_template_pack_architecture.md](./medical_display_template_pack_architecture.md) 为准。

## 统计口径

本文统计的是“当前已进入 strict registry / template catalog / audited guide 真相面的绘图军火库”，不是任一时刻共享 `main` 工作树上恰好已经吸收完毕的全部代码状态。

当前生效统计口径以 registry / template catalog / audited guide 的一致真相为准，现行库存是 `47`。

`2026-04-07` 的 `31` 模板冻结边界只保留为历史 provenance，用来解释这条主线是如何从首批冻结快照继续扩容到当前库存的。对应历史锚点如下：

- `63cd76a`：`F` 家族干净集成锚点
- `ce129dc`：`F` 家族视觉审计决策面收口锚点
- `474ee02`：`B` 家族最后一个包含实际绘图代码变更的 head
- `3cc2a19`：绘图主线冻结交棒 head
- `9a74154`：`G` 家族首个审计基线
- 历史冻结报告索引（legacy）：`docs/history/omx/README*`

因此，本文记录的是“这条绘图主线现在到底已经会什么”，而不是“当前共享根工作树正好展开到了哪里”。

## 当前总览

- 八大论文家族 `A-H` 已全部完成首个审计基线，当前完成度为 `8/8`。
- 历史冻结快照（仅用于 provenance）为 `31`：
  - 证据型图模板 `24`
  - 插图壳层模板 `2`
  - 表格壳层模板 `5`
- 当前 strict registry / template catalog 工程口径统一为 `47`：
  - 证据型图模板 `40`
  - 插图壳层模板 `2`
  - 表格壳层模板 `5`
- 截至 `2026-04-12`，post-baseline rolling expansion 已在冻结基线上正式收口十三个 evidence capability cluster：
  - `celltype_signature_heatmap`：把 `D/E/G` 从“仅候选复合图式”推进到第一个 pack 化 `embedding + signature heatmap` 复合模板；
  - `time_to_event_landmark_performance_panel`：把 `A/B` 从“已有 horizon ROC / grouped calibration 组件”推进到正式的 landmark/time-slice discrimination + Brier error + calibration slope 治理模板；
  - `shap_dependence_panel`：把 `F` 从“只会 SHAP summary”推进到正式多 panel dependence + shared colorbar + zero-line governance 的本地解释模板；
  - `time_to_event_threshold_governance_panel`：把 `A/B` 从“已有 decision curve / grouped calibration 组件”推进到正式的 threshold summary cards + grouped survival calibration governance 组合模板；
  - `time_to_event_multihorizon_calibration_panel`：把 `A/B` 从“已有单 horizon grouped calibration / threshold-governance 内嵌校准 panel”推进到正式的 `3/5-year` multi-horizon grouped calibration governance 模板；
  - `single_cell_atlas_overview_panel`：把 `D/E/G` 从“已有 embedding + signature heatmap”继续推进到正式的 atlas overview baseline，并把 `embedding occupancy + group-wise composition shift + marker/program definition` 一并固化为单一复合模板；
  - `spatial_niche_map_panel`：把 `D/E/G` 从“已有 atlas overview baseline”继续推进到正式的 tissue-coordinate niche composite，并把 `spatial topography + region-wise niche composition + marker/program definition` 一并固化为单一复合模板；
  - `trajectory_progression_panel`：把 `D/E/G` 从“已有 atlas overview + spatial niche baseline”继续推进到正式的 trajectory progression composite，并把 `trajectory embedding + pseudotime-bin branch composition + marker/module kinetics` 一并固化为单一复合模板；
  - `shap_waterfall_local_explanation_panel`：把 `F` 从“已有 summary + dependence”继续推进到正式 patient-level local explanation baseline，并把 `baseline -> ordered feature contributions -> final prediction` 的 additive path 固化为单一 bounded 模板；
  - `shap_force_like_summary_panel`：把 `F` 从“已有 summary + dependence + waterfall”继续推进到正式 representative-case force-like summary baseline，并把 `baseline marker + positive/negative contribution lanes + prediction marker` 的 bounded explanation path 固化为单一模板；
  - `partial_dependence_ice_panel`：把 `F` 从“已有 summary + dependence + waterfall + force-like”继续推进到正式 bounded `PDP mean + ICE curves` explanation baseline，并把 per-panel reference line/label、shared legend 语义与 `PDP/ICE` 几何 containment 固化为单一模板；
  - `shap_bar_importance`：把 `F` 从“已有 summary + local explanation”补齐到正式 bounded global importance overview，并把 rank strict order、feature uniqueness、non-negative importance、bar/label/value-label sidecar 关联与 panel containment 固化为单一模板；
  - `generalizability_subgroup_composite_panel`：把 `C/H` 从“forest 与 multicenter overview 分散承接子组件”推进到正式的 bounded `generalizability + subgroup interval` 复合模板，并把 cohort-level metric overview、support labels、subgroup interval block 与 outboard label containment 一并固化为单一复合契约。
- 此前文档里沿用过的早期 rolling headline，不再代表当前严格工程库存；从本轮起统一以 registry / template catalog 真相口径为准。
- 真实由锚点论文 `001/003` 证明过的核心家族是 `A`、`B`、`H`。
- 当前主线状态不应再被理解成“默认停车、显式重开才继续”。
- 更准确的理解是：
  - `A-H` 首个审计基线已完成；
  - 当前进入 rolling hardening / visual audit / paper-driven strengthening；
  - 本文只负责记录能力库存与成熟度，不再承载默认停车治理规则。
- 质量策略固定为两层：
  - 模板、输入契约、渲染器与质控负责保下限；
  - AI 优先的视觉审计负责逼近论文级上限。

## 军火库的三层结构

### 1. 论文家族层

回答的是“论文到底在呈现什么证据问题”。

这层是长期北极星，按 `A-H` 组织：

- `A` 预测性能与决策
- `B` 生存与时间事件
- `C` 效应量与异质性
- `D` 表征结构与数据几何
- `E` 特征模式与矩阵
- `F` 模型解释
- `G` 生物信息与组学证据
- `H` 队列与研究设计证据

### 2. 审计家族层

回答的是“这类图在工程上由什么契约、什么渲染结构、什么质控风险来治理”。

这层的职责是让平台能够稳定维护，而不是把所有图都混成单一目录。

### 3. 模板实例层

回答的是“具体是哪一个模板、哪个输入契约、哪个渲染器、哪个质控配置在工作”。

军火库真正可复用的最小单元，落在这一层。

## 当前军火库全貌

| 论文家族 | 主要回答的问题 | 当前代表模板 | 当前成熟度 | 主要来路 |
| --- | --- | --- | --- | --- |
| `A. 预测性能与决策` | 模型效果、校准、决策阈值与临床可用性 | `roc_curve_binary`、`pr_curve_binary`、`calibration_curve_binary`、`decision_curve_binary`、`binary_calibration_decision_curve_panel`、`time_to_event_decision_curve`、`time_to_event_landmark_performance_panel`、`time_to_event_threshold_governance_panel`、`time_to_event_multihorizon_calibration_panel` | 已形成真实论文证明的核心能力，并已把 `Brier/error-oriented` landmark 治理、threshold summary + grouped survival calibration governance，以及 multi-horizon grouped calibration governance 一并提升为正式模板资产 | `001/003` 锚点论文 + `A/B/H` 回归加固 + `Nature Communications` `2021` 动态复发风险 exemplar + `Nature Medicine` / `npj Digital Medicine` `2025` 阈值与校准 exemplar |
| `B. 生存与时间事件` | 随时间推移的风险分层、累计发生、固定时间点表现与多窗口对比 | `kaplan_meier_grouped`、`cumulative_incidence_grouped`、`time_to_event_discrimination_calibration_panel`、`time_to_event_risk_group_summary`、`time_to_event_stratified_cumulative_incidence_panel`、`time_dependent_roc_comparison_panel`、`time_to_event_landmark_performance_panel`、`time_to_event_threshold_governance_panel`、`time_to_event_multihorizon_calibration_panel` | 当前工程加固最充分、结构最完整的家族之一，并已具备正式 landmark/time-slice performance governance、grouped survival calibration governance 与 multi-horizon grouped calibration governance | `001/003` 锚点论文 + `HTN-AI` 图 3 + `Nature Medicine` 风险论文图 4a/4c + `Nature Communications` `2021` 动态复发风险 exemplar + `Nature Medicine` / `npj Digital Medicine` `2025` 阈值与校准 exemplar |
| `C. 效应量与异质性` | 主效应与亚组效应的区间估计表达 | `forest_effect_main`、`subgroup_forest`、`generalizability_subgroup_composite_panel` | 已具备首个审计基线，并把 subgroup interval evidence 从单一 forest 扩到带 cohort/generalizability overview 的 bounded composite baseline | 既有森林图契约沉淀 + `JAMA Surgery` `2025` / `npj Digital Medicine` `2026` / `World Psychiatry` `2024` subgroup-generalizability exemplar |
| `D. 表征结构与数据几何` | 嵌入空间、分群结构、tissue-coordinate 空间拓扑、trajectory / manifold 演进与低维投影表达 | `umap_scatter_grouped`、`pca_scatter_grouped`、`tsne_scatter_grouped`、`celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel` | 已具备首个审计基线，并把 D/E/G baseline 从 `embedding + signature heatmap` 扩到 `atlas overview`、`spatial niche topography + composition + marker/program` 与 `trajectory progression + branch composition + kinetics` 三级复合图式 | 既有散点与嵌入契约 + `Nature Medicine` `2025` 炎症图谱图 1 + `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 + `Genome Research` `2021` / `Nature Communications` `2023` atlas overview exemplar + `Nature Medicine` `2024` / `Nature Communications` `2025` / `npj Digital Medicine` `2025` spatial niche exemplar + `Nature Biotechnology` `2023` trajectory exemplar |
| `E. 特征模式与矩阵` | 热图、矩阵对比、相关性、有序性能矩阵与带 marker/program / kinetics 解释的复合图 | `heatmap_group_comparison`、`correlation_heatmap`、`clustered_heatmap`、`performance_heatmap`、`celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel` | 已具备首个审计基线，并开始从独立矩阵扩到带 celltype/program、spatial niche 与 trajectory kinetics 叙事耦合的复合热图 | 通用热图能力 + `Nature Medicine` 风险论文图 4c + atlas/spatial/trajectory exemplar 学习 |
| `F. 模型解释` | 特征归因、解释性摘要与复杂度审计 | `shap_summary_beeswarm`、`shap_bar_importance`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`shap_force_like_summary_panel`、`partial_dependence_ice_panel`、`model_complexity_audit_panel` | 已具备首个审计基线，并把 global bar-importance overview、dependence、patient-level waterfall、representative-case force-like summary 与 bounded PDP+ICE baseline 一并提升为正式 pack 资产；当前剩余主缺口转向 richer partial-dependence variants、signed / multi-cohort feature-importance 与 grouped-local-explanation follow-on | `001/003` 锚点论文 + `npj Digital Medicine` `2025` SHAP dependence exemplar + `npj Digital Medicine` `2025` UMORSS 图 6 + `JBJS Open Access` `2025` PARITY 图 6A/B + SHAP force plot / bar importance / PDP-ICE 经典解释图式 + `F` 家族视觉审计决策线 |
| `G. 生物信息与组学证据` | 组学打分、程序活性与组学原生热图表达 | `gsva_ssgsea_heatmap`、`celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel` | 已建立首个专用审计基线，并把组学/程序证据从单独热图推进到带 atlas occupancy、spatial niche composition 与 trajectory kinetics channel 的复合证据面 | 组学原生证据需求 + `Nature Medicine` `2025` / `npj Digital Medicine` `2025` 复合图谱 exemplar + atlas/spatial/trajectory partial-fit 学习 |
| `H. 队列与研究设计证据` | 队列构成、泛化性、研究流程与投稿壳层 | `multicenter_generalizability_overview`、`generalizability_subgroup_composite_panel`、`cohort_flow_figure`、`submission_graphical_abstract`、`table1_baseline_characteristics`、`table3_clinical_interpretation_summary` | 已形成真实论文证明的核心能力，并把 multicenter generalizability 继续扩到 cohort-level overview + subgroup robustness 的 bounded composite baseline | `001/003` 锚点论文 + 投稿包装需求沉淀 + `JAMA Surgery` `2025` / `npj Digital Medicine` `2026` / `World Psychiatry` `2024` generalizability exemplar |

## 已被真实论文证明的核心能力

当前真正经过真实论文交付、而不只是“目录里存在”的核心能力，主要集中在 `001/003` 锚点论文暴露过的失败模式上。

已经被正式吸收进军火库下限保护的关键能力包括：

- 默认不把 `figure title` 直接画进图面，而是让标题策略服从稿件表达面；
- 注释文本需要落在预期空白区域内，而不是只要画出来就算通过；
- `panel label` 与 `header band` 必须稳定锚定，不能漂移；
- 有顺序含义的风险分层摘要，必须同时满足顺序、单调性与可读性；
- 时间窗、多窗口、多时间片证据需要显式写入结构，而不是靠图例或自由拼接暗示；
- 图形摘要的箭头通道、泛化性图的图例标题与标签、坐标窗与有效数据域之间的关系，都已经进入正式下限治理。

这意味着军火库的价值不只是“会画”，而是“知道哪些地方最容易把论文图画坏，并且已经把一部分坏法做成了确定性的下限防线”。

## 外部高水平期刊图例吸收情况

### 已经正式吸收进军火库的外部锚点

| 来源 | 吸收的结构能力 | 提升到的论文家族 / 模板 |
| --- | --- | --- |
| `HTN-AI` 图 3 | 把单一累计发生曲线提升为显式多分层、多面板累计发生率契约 | `B` / `time_to_event_stratified_cumulative_incidence_panel` |
| `Nature Medicine` 风险论文图 4a | 把单时间窗 ROC 提升为显式多窗口、多面板 ROC 契约 | `A/B` / `time_dependent_roc_comparison_panel` |
| `Nature Medicine` 风险论文图 4c | 把泛化热图提升为有顺序、有指标语义、有数值边界的性能热图契约 | `B/E` / `performance_heatmap` |
| `Nature Communications` `2021` ctDNA 动态复发风险研究 | 把 forward landmark windows 的 discrimination、Brier error 与 calibration slope 从自由拼图提升为统一治理的三联 summary 契约 | `A/B` / `time_to_event_landmark_performance_panel` |
| `Nature Medicine` `2025` 结直肠手术 AI 决策支持论文图 4a-d + `npj Digital Medicine` `2025` RCC / 胃癌预后论文图 2/5 | 把 threshold summary cards、grouped survival calibration governance、risk-group operating review 从论文现场组合图提升为正式 pack 模板契约 | `A/B` / `time_to_event_threshold_governance_panel` |
| `Nature Medicine` `2025` 结直肠手术 AI 决策支持论文图 4a-d 与 `npj Digital Medicine` `2025` RCC / 胃癌预后论文图 2/5 所体现的多 horizon 校准叙事 | 把 `3/5-year` 并列 grouped calibration governance 从单 horizon dumbbell / 组合图内嵌局部能力提升为正式 multi-horizon 校准模板，并把 horizon strict order、panel identity 与 calibration point fail-closed 一并固定 | `A/B` / `time_to_event_multihorizon_calibration_panel` |
| `Nature Medicine` `2025` 炎症图谱图 1 + `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 | 把单独的 embedding scatter 与矩阵热图提升为显式耦合的 `celltype/program` 复合图式，并把 `score_method`、行列完备性、legend/colorbar 锚定做成确定性约束 | `D/E/G` / `celltype_signature_heatmap` |
| `Genome Research` `2021` tumor immune atlas 图 2 + `Nature Communications` `2023` integrated TME mapping 图 3 | 把 repeated atlas partial-fit 学到的 `embedding occupancy + group-wise composition shift + marker/signature definition` 固化为单一 atlas overview composite，并把 composition 完整性、state vocabulary 对齐、heatmap 网格完备性与 panel-level readability 做成正式契约 | `D/E/G` / `single_cell_atlas_overview_panel` |
| `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `npj Digital Medicine` `2025` tissue-organization exemplar + `Nature Communications` `2023` TME mapping 图 3 | 把 tissue-coordinate niche localization、region-wise niche composition 与 marker/program definition 从多篇论文里的现场复合图提升为统一的 spatial niche composite，并把 niche vocabulary 对齐、composition 完整性、heatmap 网格完备性与 panel-label anchoring 做成正式契约 | `D/E/G` / `spatial_niche_map_panel` |
| `Nature Biotechnology` `2023` trajectory exemplar | 把 trajectory / manifold 里的 branch progression、pseudotime-bin composition 与 marker/module kinetics 从论文现场多块拼图提升为统一的 trajectory progression composite，并把 branch vocabulary、pseudotime bins、branch-weight completeness 与 kinetics heatmap 网格做成正式契约 | `D/E/G` / `trajectory_progression_panel` |
| `npj Digital Medicine` `2025` 前列腺 XAI SHAP dependence 图面 | 把论文现场局部 dependence explanation 提升为正式多 panel SHAP dependence 契约，并把 shared colorbar、panel label 与 zero-line 变成可审计下限 | `F` / `shap_dependence_panel` |
| `npj Digital Medicine` `2025` UMORSS ovarian workflow 图 6 + `JBJS Open Access` `2025` PARITY bone tumor explanation 图 6A/B | 把 patient-level SHAP explanation 从“单篇论文现场插图”提升为正式 waterfall 模板；固定 `baseline -> ordered contributions -> final prediction` additive path、case/panel 唯一性、贡献方向一致性与预测值守恒约束 | `F` / `shap_waterfall_local_explanation_panel` |
| `真实解释型论文交付需求 + SHAP force plot 经典解释图式` | 把代表性病例的局部解释从 waterfall 再推进到 bounded force-like summary；固定 `baseline marker -> positive/negative directional lanes -> prediction marker` 的 panel 内表达，并把标签 containment、方向一致性与排序守恒做成正式契约 | `F` / `shap_force_like_summary_panel` |
| `真实解释型论文交付需求 + PDP / ICE 经典解释图式` | 把按特征展开的 marginal response 与 individual trajectory explanation 从候选概念提升为正式 bounded multi-panel 模板；固定 `PDP mean + ICE curves`、per-panel reference line/label、shared legend 语义以及 panel 内几何 containment 契约 | `F` / `partial_dependence_ice_panel` |
| `真实解释型论文交付需求 + SHAP bar importance 经典解释图式` | 把全局特征重要性总览从“解释章节常见但未正式入库的补位图式”提升为正式 bounded 单 panel 模板；固定 feature unique、rank strict order、importance non-negative finite、bar/value-label 关联与 panel containment 契约 | `F` / `shap_bar_importance` |
| `JAMA Surgery` `2025` multicenter surgical transfusion risk 图 2A/B + `npj Digital Medicine` `2026` postcranioplasty multicenter cohort 图 3/4/5 + `World Psychiatry` `2024` UHR 1000+ 图 2 | 把 subgroup interval 与 generalizability overview 从“forest + multicenter panels 各自独立”提升为固定两块式 composite；同时把 cohort/support completeness、subgroup interval fail-closed、legend 语义与 outboard label containment 做成正式契约 | `C/H` / `generalizability_subgroup_composite_panel` |

### 已观察、仍在候选池中的高价值素材

以下素材已经进入绘图主线视野，但当前仍不计入“已正式落地的新增军火库能力”。其中 atlas exemplar 暴露出的 `embedding + signature heatmap`、`embedding + composition + marker/program overview`，spatial exemplar 暴露出的 `tissue-coordinate niche topography + region-wise niche composition + marker/program definition`，以及 trajectory exemplar 暴露出的 `trajectory progression + pseudotime-bin branch composition + marker/module kinetics`，已分别正式入库为 `celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`spatial_niche_map_panel` 与 `trajectory_progression_panel`；更大 atlas / spatial / trajectory 多视图变体仍留在候选池中：

- `Cancer Cell` `2022` 肾脏图谱类图面：
  - 价值：总体嵌入 + 主要细胞类型热图 + 空间上下文；
  - 可能提升：`D/E/G`；
  - 当前状态：已作为外部范例候选归档。
- `Lancet Digital Health` 多癌种风险图 2：
  - 价值：风险表达与泛化表达的稿件级组合方式；
  - 可能提升：`A/H`；
  - 当前状态：保留为低优先级候选。

## 当前军火库的边界

### 1. 军火库不是模板数量竞赛

军火库的目标是提升论文交付能力，而不是机械堆模板数量。

一个模板只有在以下条件同时满足时，才算真正进入军火库：

- 已注册；
- 有正式输入契约；
- 有渲染路径；
- 有质控路径；
- 能通过稿件包装与投稿输出验证；
- 最好还能被真实论文图面验证过。

### 2. 下限与上限必须分开治理

模板与质控负责保下限，但它们不应该假装自己已经覆盖了全部视觉判断。

真正的论文级上限，仍然依赖 AI 优先的视觉审计与再修订闭环：

1. 先按审计路径出图；
2. 再看真实图像；
3. 明确指出具体问题；
4. 再把可复用的问题沉淀回模板、契约、渲染器或质控。

### 3. 当前仍不计入“已成熟完成”的部分

以下方向已经有价值，但当前不应被误写成“军火库已经完整具备”：

- `F` 家族虽已从 `shap_summary_beeswarm` 扩到 `shap_bar_importance`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`shap_force_like_summary_panel` 与 `partial_dependence_ice_panel`，但 richer partial-dependence variants、signed / multi-cohort feature-importance 与 grouped-local-explanation follow-on 仍需继续滚动 hardening；
- `C/H` 虽已从 `subgroup_forest` / `multicenter_generalizability_overview` 扩到 `generalizability_subgroup_composite_panel`，但 workflow shell、calibration appendix、baseline-balance / missingness / QC shells 仍未成熟；
- `D/E/G` 更大 atlas / spatial / trajectory 复合图谱结构；`single_cell_atlas_overview_panel`、`spatial_niche_map_panel` 与 `trajectory_progression_panel` 虽已把 baseline 扩到 occupancy / spatial topography / progression + composition + marker-program or kinetics，但不应被误写成整套 atlas / spatial / trajectory 平台已经完成；
- 仅在外部范例中观察到、但还没形成正式模板与回归套件的高级图式。

## 后续维护规则

后续每次军火库扩充，至少要同步更新两份文档：

1. 本文：更新当前总览、家族全貌与已吸收能力；
2. [medical_display_arsenal_history.md](./medical_display_arsenal_history.md)：追加时间、来源、学到的结构、提升到的家族或模板。

这样做的目的，是让“现在会什么”和“怎么学会的”始终保持分离但一致。
