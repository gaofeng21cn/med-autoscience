# Medical Display Template Backlog

## Purpose

这个文档定义 display surface 的内部扩容目标，用来回答两个问题：

1. 当前 audited display surface 已经做到多少。
2. `v1` 计划把总模板数收敛到多少，以及每个大类准备扩到哪里为止。

它是内部 backlog，不是当前完成态真相源。

当前完成态仍以：

- `guides/medical_display_audit_guide.md`
- `guides/medical_display_template_catalog.md`

为准。

## Current Audited Inventory

截至当前工作树：

- Evidence figure templates: `20`
- Illustration shells: `1`
- Table shells: `3`
- Total audited templates: `24`

## V1 Target

`v1` 先把 audited template 总数定为 `40`，不再继续停留在“几十种”的口头目标。

拆分为：

- Evidence figure templates: `36`
- Illustration + table shells: `4`
- Total audited templates: `40`

这个数刻意不是越大越好。

边界是：

- 优先覆盖临床医学 AI 论文的高频、可结构化、可审计展示项
- 不追求一次性覆盖所有低频、病种专有、期刊专有、机制专有图型
- 不为了追求数量引入需要启发式后处理或 renderer 内自由发挥的模板

## Class-Level Target

### 1. Prediction Performance

- Current: `3`
- Target: `4`
- Delta: `+1`

Planned additions:

- `confusion_matrix_heatmap_binary`

### 2. Clinical Utility

- Current: `2`
- Target: `4`
- Delta: `+2`

Planned additions:

- `clinical_impact_curve_binary`
- `net_intervention_avoided_curve_binary`

### 3. Time-to-Event

- Current: `5`
- Target: `6`
- Delta: `+1`

Planned additions:

- `landmark_kaplan_meier_grouped`

### 4. Data Geometry

- Current: `3`
- Target: `5`
- Delta: `+2`

Planned additions:

- `density_contour_grouped`
- `trajectory_scatter_grouped`

### 5. Matrix Pattern

- Current: `3`
- Target: `6`
- Delta: `+3`

Planned additions:

- `annotated_signature_heatmap`
- `mutation_oncoprint`
- `response_pattern_heatmap`

### 6. Effect Estimate

- Current: `2`
- Target: `5`
- Delta: `+3`

Planned additions:

- `multivariable_forest`
- `interaction_forest`
- `sensitivity_forest`

### 7. Model Explanation

- Current: `1`
- Target: `4`
- Delta: `+3`

Planned additions:

- `shap_bar_importance`
- `shap_dependence_scatter`
- `partial_dependence_curve`

### 8. Generalizability

- Current: `1`
- Target: `2`
- Delta: `+1`

Planned additions:

- `temporal_external_validation_overview`

## Promotion Rules

只有同时满足下面条件的候选模板，才允许进入 audited surface：

1. 能写成显式输入 schema，而不是靠自由文本指挥 renderer。
2. 统计输入边界稳定，不依赖渲染阶段临时推断。
3. 物化导出能稳定生成 `png/pdf` 与可审计 sidecar。
4. 能复用现有 `qc_profile`，或值得新增一个明确的 profile。
5. 不允许把聚类、重排、避让、文字修正放到 renderer 内做启发式补救。

## Immediate Priority Queue

如果继续按“高频 + 强约束 + 可复用”推进，下一批优先顺序建议是：

1. `clinical_impact_curve_binary`
2. `multivariable_forest`
3. `shap_bar_importance`
4. `confusion_matrix_heatmap_binary`

原因：

- 这几类在临床 AI 论文中都高频
- 语义边界相对稳定
- 前三者都能较多复用现有 schema / renderer / QC
- `confusion_matrix_heatmap_binary` 虽然高频，但需要单独收紧离散矩阵语义，优先级略低于前 3 个
