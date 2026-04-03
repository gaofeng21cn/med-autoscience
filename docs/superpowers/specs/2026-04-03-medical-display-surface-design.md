# Medical Display Surface Design

## Goal

把 `MedAutoScience` 当前零散的论文图/表/说明图约束，收敛成一个统一、可审计、可扩展的“论文展示面”平台能力。

Phase 1 不追求一次性覆盖所有医学论文图型，而是先把以下对象纳入正式 contract：

- 证据图模板
- 说明图 shell
- 统计表 shell
- 统一导出与统一版式质控

核心目标不是“图更多”，而是：

- 新课题的主图不再主要依赖 agent 临时写脚本
- `Figure 1` 与 `Table 1` 从“要求存在”升级为“有官方模板约束”
- 排版低级错误从人工发现改成机器拦截
- `MedAutoScience` 成为 contract truth，而不是把真相散落在 skill 文本、quest-local script 和导出器里

## Current State

当前仓库里，最成熟的是图/表的语义约束与 manuscript gate，而不是统一模板引擎。

现状拆解如下：

1. `MedDeepScientist` 侧只有少量轻量图生成能力，主要是 connector summary chart 与 quest graph。
2. `MedAutoScience` 已经有比较强的论文面 contract：
   - `figure_renderer_contract`
   - `medical_reporting_contract`
   - `medical_analysis_contract`
   - `medical_publication_surface`
   - `figure_loop_guard`
3. 现有系统已区分：
   - 证据图 vs 说明图
   - figure shell vs table shell requirement
   - figure/table catalog vs manuscript gate
4. 但仓库内仍缺失：
   - 官方模板注册表
   - 官方 shell 注册表
   - 统一 QC profile
   - 图型唯一化机制
   - `Figure 1` / `Table 1` 的正式模板 contract

## Problem Statement

当前最主要的问题不是配色不统一，而是缺乏“模板真相面”和“版式硬约束”：

- 同一类证据图没有唯一官方实现
- 低级排版错误只在 render-inspect-revise 的人工环节暴露
- 说明图与统计表虽然被要求存在，但没有被收口为正式 shell contract
- `figure_catalog.json` / `table_catalog.json` / `figure_semantics_manifest.json` 的角色边界不够清晰
- quest-local script 与 manuscript gate 之间缺少中间层

这会导致以下后果：

- 图型实现分叉
- 导出形态不稳定
- 不同课题之间复用困难
- 旧脚本质量无法通过 contract 自动筛选
- Figure 1 / Table 1 等高度模板化对象仍然容易依赖 agent 即兴生成

## Design Principles

### 1. Platform truth over prompt suggestion

展示面 contract 必须在平台层落盘、校验、导出，而不是只存在于 skill 提示语里。

### 2. Unique official implementation per display item

每一种展示项只能命中一个官方模板。

这里的“唯一”指：

- 一个 `template_id`
- 一个 `renderer_family`
- 一个 `input_schema_id`
- 一个 `qc_profile`

不允许同一类对象长期存在“R 也行 / Python 也行 / 手工也行”的并行官方真相。

### 3. Structured input first

所有正式展示项优先由结构化输入驱动，而不是自由文本。

示例：

- `Figure 1` 使用 `paper/cohort_flow.json`
- `Table 1` 使用 `paper/baseline_characteristics_schema.json`
- 证据图使用模板定义过的统计输入 schema

### 4. Machine-checkable layout quality

重要展示面必须有统一 QC，而不是只靠“画完自己看一眼”。

### 5. New work strict, legacy work migratable

新图/新表立即强制走新体系。
旧 quest 通过显式迁移入口重生成，不做静默兼容。

## Object Model

平台对象从“画图”扩展为“论文展示面”，分为三类：

### A. Evidence Figures

承载结果证据、统计结论或数据结构证据的图。

首批总分类：

- 预测性能与决策
- 生存与时间事件
- 表征结构与数据几何
- 特征模式与矩阵
- 生物信息与组学证据
- 解释类扩展

### B. Illustration Shells

不直接承载结果统计证据，但属于论文核心展示面的说明图。

首批最重要对象：

- `cohort_flow_figure`

后续可扩：

- `study_workflow_figure`
- `model_overview_figure`
- `graphical_abstract_shell`

### C. Table Shells

高度模板化、统计规则稳定、但不属于“图”的论文展示项。

首批对象：

- `table1_baseline_characteristics`

后续可扩：

- `table2_primary_performance`
- `table_subgroup_summary`
- `table_missing_data_summary`

## Four-Layer Architecture

### 1. Reporting Contract

回答“这篇稿子必须有哪些展示项”。

继续由现有 `medical_reporting_contract` 决定，例如：

- `cohort_flow_figure`
- `table1_baseline_characteristics`
- `decision_curve_figure`

这一层只负责 requirement，不负责实现。

### 2. Registry

回答“某个展示项的官方模板是什么、谁来渲染、输入输出是什么”。

新增三本注册表：

- `evidence_figure_registry`
- `illustration_shell_registry`
- `table_shell_registry`

### 3. Catalog

回答“当前 quest 实际生成了哪些正式展示项及其产物”。

继续使用：

- `paper/figures/figure_catalog.json`
- `paper/tables/table_catalog.json`

但字段形态必须统一，并由 registry 约束。

### 4. Publication Gate

回答“当前展示项是否符合论文面 contract，可以进入 bundle / submission”。

继续由 `medical_publication_surface` 作为总 gate。

## Registry Contracts

### Evidence Figure Registry

每个条目至少包含：

- `template_id`
- `display_name`
- `evidence_class`
- `research_question_class`
- `renderer_family`
- `implementation_ref`
- `input_schema_id`
- `output_requirements`
- `layout_qc_profile`
- `allowed_paper_roles`
- `required_stats_contract`
- `forbidden_mutations`

### Illustration Shell Registry

每个条目至少包含：

- `shell_id`
- `display_name`
- `renderer_family`
- `implementation_ref`
- `input_schema_id`
- `layout_spec`
- `visible_text_rules`
- `export_requirements`
- `shell_qc_profile`
- `allowed_paper_roles`

### Table Shell Registry

每个条目至少包含：

- `table_shell_id`
- `display_name`
- `implementation_ref`
- `input_schema_id`
- `stat_profile`
- `column_layout_profile`
- `footnote_profile`
- `export_requirements`
- `table_qc_profile`
- `allowed_paper_roles`

## Display Catalog Contracts

### Figure Catalog

`figure_catalog.json` 应从“路径清单”升级成“实例化展示项记录”。

每个 figure entry 建议至少包含：

- `figure_id`
- `template_id`
- `renderer_family`
- `paper_role`
- `input_schema_id`
- `source_paths`
- `export_paths`
- `qc_profile`
- `qc_result`
- `claim_ids`

### Table Catalog

`table_catalog.json` 同样应从弱描述升级成强实例记录。

每个 table entry 建议至少包含：

- `table_id`
- `table_shell_id`
- `paper_role`
- `input_schema_id`
- `source_paths`
- `asset_paths`
- `qc_profile`
- `qc_result`
- `claim_ids`

## Official Implementation Policy

### Renderer coexistence

平台承认 `r_ggplot2` 与 `python` 两个证据图 renderer family。

但共存规则不是“都可以”，而是：

- 每种图型只能指定一个官方 renderer
- 同一种模板不能同时有两个官方实现

### Recommended renderer allocation

Phase 1 推荐：

- `R-first`
  - ROC / PR
  - calibration
  - DCA
  - KM / CIF
  - forest
  - UMAP / PCA
  - heatmap
  - volcano / enrichment
- `Python-first`
  - SHAP family

这样既保留现实上的最优生态，又避免平台长期分叉。

## Quality Control Model

### Figure QC

Phase 1 先做机器可稳定判断的硬错误：

- text out of bounds
- text-text overlap
- legend-data overlap
- panel spacing below threshold
- font size below threshold
- required vector export missing
- preview export missing
- unsupported palette/count rule violation
- heatmap annotation overflow

### Table QC

Phase 1 先做：

- header overflow
- column width overflow
- missing abbreviation/unit notes
- invalid stat format by variable type
- missing missingness policy note
- missing overall/group count fields for Table 1

### Illustration Shell QC

Phase 1 先做：

- node text overflow
- broken connectors
- count non-conservation
- missing final analytic sample node

## Phase 1 Scope

### Phase 1A: Contracts and truth surfaces

必做：

- 新增三个 registry
- 收紧 `figure_semantics_manifest` 与 figure/table catalog
- 将 `cohort_flow_figure` 与 `table1_baseline_characteristics` 升格为正式 shell contract
- gate 开始校验模板命中、导出要求与 QC 结果

### Phase 1B: First official template set

首批 evidence figure 模板：

- `roc_curve_binary`
- `pr_curve_binary`
- `calibration_curve_binary`
- `decision_curve_binary`
- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`
- `umap_scatter_grouped`
- `pca_scatter_grouped`
- `heatmap_group_comparison`
- `correlation_heatmap`
- `forest_effect_main`
- `shap_summary_beeswarm`

首批 shells：

- `cohort_flow_figure`
- `table1_baseline_characteristics`

### Phase 1C: Unified QC layer

把 Figure / Table / Shell 的 QC 结果纳入 catalog 和 publication gate。

### Explicit non-goals for Phase 1

不在 Phase 1 内完成：

- 全量组学图谱
- 所有 subgroup / forest 变体
- 所有 embedding 变体
- supplementary 全覆盖
- 全量 journal-specific style branching

## Migration Strategy

### New work

新生成的正式展示项必须走 registry + shell/template + QC。

### Legacy work

旧 quest 只允许通过显式迁移入口进入新体系：

- 选择展示项
- 匹配官方模板
- 冻结输入
- 重生成
- 记录迁移结果

禁止静默把旧图视为“天然合规”。

## Risks

### 1. Contract inflation

如果 registry 字段设计过重，落地会变慢。

对策：
Phase 1 只保留最必要字段，把统计 profile / layout profile 控制在最小闭环。

### 2. Over-generalization

如果一开始想覆盖所有医学图，模板边界会失真。

对策：
总分类完整，首批模板克制。

### 3. R/Python boundary confusion

如果不强制图型唯一官方实现，平台会回到当前分叉状态。

对策：
模板层强制唯一 `template_id -> renderer_family -> implementation_ref`。

### 4. QC false positives

版式 QC 一开始容易误报。

对策：
Phase 1 只做最确定的硬错误，不做复杂美学评分。

## Recommended Next Step

下一步进入 implementation planning，并按以下优先级执行：

1. 收紧 registry / catalog / manifest contract
2. 让 `Figure 1` 与 `Table 1` 成为正式 shell contract
3. 落首批 12 个 evidence figure 模板
4. 上统一 QC
5. 提供 legacy migration entry
