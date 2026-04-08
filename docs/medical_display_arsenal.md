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

本文统计的是“已经验证过的绘图主线军火库”，不是任一时刻共享 `main` 工作树上恰好已经吸收完毕的全部代码状态。

当前统计边界以 `2026-04-07` 的绘图主线冻结边界为准，核心锚点如下：

- `63cd76a`：`F` 家族干净集成锚点
- `ce129dc`：`F` 家族视觉审计决策面收口锚点
- `474ee02`：`B` 家族最后一个包含实际绘图代码变更的 head
- `3cc2a19`：绘图主线冻结交棒 head
- `9a74154`：`G` 家族首个审计基线
- `.omx/reports/medical-display-mainline/*`：绘图主线冻结报告面

因此，本文记录的是“这条绘图主线到底已经会什么”，而不是“当前共享根工作树正好展开到了哪里”。

## 当前总览

- 八大论文家族 `A-H` 已全部完成首个审计基线，当前完成度为 `8/8`。
- `2026-04-07` 冻结审计基线为 `31`：
  - 证据型图模板 `24`
  - 插图壳层模板 `2`
  - 表格壳层模板 `5`
- 当前 strict registry / template catalog 工程口径统一为 `39`：
  - 证据型图模板 `32`
  - 插图壳层模板 `2`
  - 表格壳层模板 `5`
- `2026-04-08` 的 rolling expansion 已在冻结基线上正式收口五个 evidence capability cluster：
  - `celltype_signature_heatmap`：把 `D/E/G` 从“仅候选复合图式”推进到第一个 pack 化 `embedding + signature heatmap` 复合模板；
  - `time_to_event_landmark_performance_panel`：把 `A/B` 从“已有 horizon ROC / grouped calibration 组件”推进到正式的 landmark/time-slice discrimination + Brier error + calibration slope 治理模板；
  - `shap_dependence_panel`：把 `F` 从“只会 SHAP summary”推进到正式多 panel dependence + shared colorbar + zero-line governance 的本地解释模板；
  - `time_to_event_threshold_governance_panel`：把 `A/B` 从“已有 decision curve / grouped calibration 组件”推进到正式的 threshold summary cards + grouped survival calibration governance 组合模板；
  - `time_to_event_multihorizon_calibration_panel`：把 `A/B` 从“已有单 horizon grouped calibration / threshold-governance 内嵌校准 panel”推进到正式的 `3/5-year` multi-horizon grouped calibration governance 模板。
- 此前文档里沿用过的 `34` 只是 freeze-baseline 之后早期 rolling headline，不再代表当前严格工程库存；从本轮起统一以 registry / template catalog 真相口径为准。
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
| `C. 效应量与异质性` | 主效应与亚组效应的区间估计表达 | `forest_effect_main`、`subgroup_forest` | 已具备首个审计基线，但尚未经历更强的真实论文驱动扩展 | 既有森林图契约沉淀 |
| `D. 表征结构与数据几何` | 嵌入空间、分群结构与低维投影表达 | `umap_scatter_grouped`、`pca_scatter_grouped`、`tsne_scatter_grouped`、`celltype_signature_heatmap` | 已具备首个审计基线，并正式吸收 atlas 风格 `embedding + signature heatmap` 复合能力 | 既有散点与嵌入契约 + `Nature Medicine` `2025` 炎症图谱图 1 + `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 |
| `E. 特征模式与矩阵` | 热图、矩阵对比、相关性与有序性能矩阵 | `heatmap_group_comparison`、`correlation_heatmap`、`clustered_heatmap`、`performance_heatmap`、`celltype_signature_heatmap` | 已具备首个审计基线，并开始从独立矩阵扩到带 celltype/program 结构耦合的复合热图 | 通用热图能力 + `Nature Medicine` 风险论文图 4c + atlas exemplar 学习 |
| `F. 模型解释` | 特征归因、解释性摘要与复杂度审计 | `shap_summary_beeswarm`、`shap_dependence_panel`、`model_complexity_audit_panel` | 已具备首个审计基线，并把 dependence family 提升为正式 pack 资产；但 waterfall / patient-level local explanation 仍待继续扩展 | `001/003` 锚点论文 + `npj Digital Medicine` `2025` SHAP dependence exemplar + `F` 家族视觉审计决策线 |
| `G. 生物信息与组学证据` | 组学打分、程序活性与组学原生热图表达 | `gsva_ssgsea_heatmap`、`celltype_signature_heatmap` | 已建立首个专用审计基线，并开始支持 celltype/program 组合式组学证据面 | 组学原生证据需求 + `Nature Medicine` `2025` / `npj Digital Medicine` `2025` 复合图谱 exemplar |
| `H. 队列与研究设计证据` | 队列构成、泛化性、研究流程与投稿壳层 | `multicenter_generalizability_overview`、`cohort_flow_figure`、`submission_graphical_abstract`、`table1_baseline_characteristics`、`table3_clinical_interpretation_summary` | 已形成真实论文证明的核心能力 | `001/003` 锚点论文 + 投稿包装需求沉淀 |

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
| `npj Digital Medicine` `2025` 前列腺 XAI SHAP dependence 图面 | 把论文现场局部 dependence explanation 提升为正式多 panel SHAP dependence 契约，并把 shared colorbar、panel label 与 zero-line 变成可审计下限 | `F` / `shap_dependence_panel` |

### 已观察、仍在候选池中的高价值素材

以下素材已经进入绘图主线视野，但当前仍不计入“已正式落地的新增军火库能力”。其中 `Nature Medicine` `2025` 炎症图谱图 1 与 `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 暴露出的 `embedding + signature heatmap` 子能力，已在 `2026-04-08` 正式入库为 `celltype_signature_heatmap`；更大 atlas / spatial / trajectory 变体仍留在候选池中：

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

- `F` 家族虽已从 `shap_summary_beeswarm` 扩到 `shap_dependence_panel`，但 waterfall / patient-level local explanation / force-like family 仍较薄，需要继续滚动 hardening；
- `D/E/G` 更大 atlas / spatial / trajectory 复合图谱结构；`celltype_signature_heatmap` 已正式入库，但不应被误写成整套 atlas 平台已经完成；
- 仅在外部范例中观察到、但还没形成正式模板与回归套件的高级图式。

## 后续维护规则

后续每次军火库扩充，至少要同步更新两份文档：

1. 本文：更新当前总览、家族全貌与已吸收能力；
2. [medical_display_arsenal_history.md](./medical_display_arsenal_history.md)：追加时间、来源、学到的结构、提升到的家族或模板。

这样做的目的，是让“现在会什么”和“怎么学会的”始终保持分离但一致。
