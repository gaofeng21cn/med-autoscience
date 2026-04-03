# Medical Display QC and Schema Contract Design

## Goal

在现有 `MedAutoScience` display surface 主链上，补齐两个缺口：

1. 把 12 个 evidence template 的 `qc_result` 从“占位 pass”升级为“真实执行过的 layout/QC 结果”。
2. 把“八大类模板清单 + 输入 schema 约束”从代码内隐式知识，升级成正式、可审计、可引用的 schema contract。

本设计不改动当前主线：

- `display_registry` 仍然是真相源
- `display_surface_materialization` 仍然是唯一官方物化入口
- `figure_catalog.json` / `table_catalog.json` 仍然是实例记录面
- `medical_publication_surface` 仍然是 gate，而不是 mutation/execution 入口

## Current Gap

当前已经完成了两步：

- 14 个官方展示项都已注册
- 14 个官方展示项都已可执行物化

但仍有两个关键缺口：

### 1. QC 结果不是真正执行出来的

当前 `display_surface_materialization` 在写 catalog 时直接写入：

- `qc_result.status = pass`
- `qc_result.issues = []`

这只能说明“代码决定相信自己”，不能说明“版式确实被检查过”。

### 2. 输入 schema 只存在于 registry 和测试夹具里

现在每个 template 已经有：

- `template_id`
- `renderer_family`
- `input_schema_id`
- `layout_qc_profile`

但 `input_schema_id` 具体对应哪些字段、字段的列表结构、数值约束、模板边界，并没有一份正式文档可以审计和引用。

## Scope

这次设计覆盖两部分：

### A. Evidence Figure Unified QC

覆盖全部 12 个 evidence template：

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

### B. Auditable Template + Schema Spec

把当前展示面分成八个顶层类别，并显式记录：

- 类别 -> template 列表
- template -> `input_schema_id`
- schema -> 顶层字段
- schema -> 嵌套列表项结构
- schema -> 数值/形状约束
- template -> `renderer_family`
- template -> `required_exports`
- template -> `qc_profile`

## Explicit Non-Goals

这次不做：

- 新增第 15 个以上的新模板
- journal-specific style branching
- supplementary 全覆盖的新目录结构
- OCR、像素级启发式撞文本检测
- 通过“失败后自动重排一次”做静默兜底

## Decision Summary

### 1. QC 执行放在 `display_surface_materialization`

不新建第二套主入口，也不把 mutation 塞进 gate。

执行链保持为：

1. 读取 registry
2. 读取结构化输入
3. renderer 生成导出物
4. renderer 生成 layout sidecar
5. QC engine 基于 sidecar 执行规则
6. catalog 写入 `qc_result`
7. publication gate 只验证 catalog 中的 QC 结果是否存在且合规

### 2. QC 依赖 renderer sidecar，而不是像素后处理

为了避免启发式后处理，QC 不做：

- OCR 识别文本后猜测是否重叠
- 图像腐蚀/膨胀后猜 legend 是否压住 panel
- 失败后自动缩字或自动挪图例

改为要求 renderer 在导出时同时生成结构化 layout sidecar。

sidecar 至少记录：

- device/canvas 大小
- panel 区域
- title / subtitle / caption 的边界框
- x/y axis title 与 tick label 的边界框
- legend box 边界框
- colorbar 边界框
- forest row label / CI / marker 的边界框
- SHAP feature rows / zero line / colorbar 的边界框

这样 QC 是“基于绘图库内部几何结果做判定”，而不是“看图猜测”。

## Eight-Class Template Catalog

当前 display surface 顶层分成八类：

### 1. Prediction Performance

- `roc_curve_binary`
- `pr_curve_binary`
- `calibration_curve_binary`

### 2. Clinical Utility

- `decision_curve_binary`

### 3. Time-to-Event

- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`

### 4. Data Geometry

- `umap_scatter_grouped`
- `pca_scatter_grouped`

### 5. Matrix Pattern

- `heatmap_group_comparison`
- `correlation_heatmap`

### 6. Effect Estimate

- `forest_effect_main`

### 7. Model Explanation

- `shap_summary_beeswarm`

### 8. Publication Shells and Tables

- `cohort_flow_figure`
- `table1_baseline_characteristics`

这次实现重点是前 7 个 evidence 类别的 QC；第 8 类只在 spec 中保留位置，不在本轮新增 shell/table QC engine。

## Schema Contract Surface

### Common Display Envelope

所有 evidence display payload 在各自 schema 下都共享一层公共 envelope：

- `display_id`
- `template_id`
- `title`
- `caption`
- `paper_role`（可选，默认使用 registry allowed role 的第一个）

### Schema A: `binary_prediction_curve_inputs_v1`

适用模板：

- `roc_curve_binary`
- `pr_curve_binary`
- `calibration_curve_binary`
- `decision_curve_binary`

顶层字段：

- `schema_version`
- `input_schema_id`
- `displays`

`displays[]` 必填字段：

- `display_id`
- `template_id`
- `title`
- `caption`
- `x_label`
- `y_label`
- `series`

`reference_line` 可选字段：

- `x`
- `y`
- `label`

`series[]` 必填字段：

- `label`
- `x`
- `y`

`series[]` 可选字段：

- `annotation`

硬约束：

- `x` 与 `y` 长度必须相等
- `x` / `y` 必须是有限数值
- `series` 至少一条
- `reference_line` 若存在，其 `x` / `y` 长度必须相等

### Schema B: `time_to_event_grouped_inputs_v1`

适用模板：

- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`

`displays[]` 必填字段：

- `display_id`
- `template_id`
- `title`
- `caption`
- `x_label`
- `y_label`
- `groups`

`groups[]` 必填字段：

- `label`
- `times`
- `values`

`annotation` 可选字段：

- 用于记录 `log-rank P` / `Gray test P` 等文本

硬约束：

- `times` 与 `values` 长度必须相等
- `groups` 至少一组
- 所有数值必须有限

### Schema C: `embedding_grouped_inputs_v1`

适用模板：

- `umap_scatter_grouped`
- `pca_scatter_grouped`

`displays[]` 必填字段：

- `display_id`
- `template_id`
- `title`
- `caption`
- `x_label`
- `y_label`
- `points`

`points[]` 必填字段：

- `x`
- `y`
- `group`

硬约束：

- `points` 至少一个
- `x` / `y` 必须是有限数值
- `group` 必须非空

### Schema D: `heatmap_group_comparison_inputs_v1`

适用模板：

- `heatmap_group_comparison`

`displays[]` 必填字段：

- `display_id`
- `template_id`
- `title`
- `caption`
- `x_label`
- `y_label`
- `cells`

`cells[]` 必填字段：

- `x`
- `y`
- `value`

硬约束：

- `cells` 至少一个
- `x` / `y` 必须非空
- `value` 必须是有限数值

### Schema E: `correlation_heatmap_inputs_v1`

适用模板：

- `correlation_heatmap`

字段结构与 `heatmap_group_comparison_inputs_v1` 相同，但增加专用约束：

- 变量集合必须形成方阵
- 对角线必须存在
- 若 `(a, b)` 与 `(b, a)` 同时存在，其值必须一致

### Schema F: `forest_effect_inputs_v1`

适用模板：

- `forest_effect_main`

`displays[]` 必填字段：

- `display_id`
- `template_id`
- `title`
- `caption`
- `x_label`
- `reference_value`
- `rows`

`rows[]` 必填字段：

- `label`
- `estimate`
- `lower`
- `upper`

硬约束：

- `rows` 至少一条
- 每行必须满足 `lower <= estimate <= upper`
- 所有数值必须有限

### Schema G: `shap_summary_inputs_v1`

适用模板：

- `shap_summary_beeswarm`

`displays[]` 必填字段：

- `display_id`
- `template_id`
- `title`
- `caption`
- `x_label`
- `rows`

`rows[]` 必填字段：

- `feature`
- `points`

`rows[].points[]` 必填字段：

- `shap_value`
- `feature_value`

硬约束：

- `rows` 至少一条
- 每条 `feature` 必须非空
- 每条 `rows[].points` 必须非空
- `shap_value` / `feature_value` 必须为有限数值

## QC Object Model

### QC Sidecar

每个 evidence figure 新增一个 sidecar：

- 路径：与主导出物同目录
- 命名：`<figure_id>_<template_id>.layout.json`

字段至少包含：

- `schema_version`
- `figure_id`
- `template_id`
- `renderer_family`
- `qc_profile`
- `device`
- `layout_boxes`
- `panel_boxes`
- `guide_boxes`
- `metrics`

其中：

- `device` 记录画布宽高、dpi、单位
- `layout_boxes` 记录标题、轴标题、caption、tick labels 等边界框
- `panel_boxes` 记录主绘图区边界
- `guide_boxes` 记录 legend / colorbar / annotation block 边界
- `metrics` 记录规则判断所需的数值，如 row count、point count、x/y range 等

### Catalog `qc_result`

`figure_catalog.json` 中的 `qc_result` 升级为：

- `status`
- `checked_at`
- `engine_id`
- `qc_profile`
- `layout_sidecar_path`
- `issues`
- `metrics`

其中：

- `status` 只能是 `pass` / `fail`
- `engine_id` 本轮固定为 `display_layout_qc_v1`
- `layout_sidecar_path` 指向 renderer 产出的 sidecar
- `issues[]` 为结构化 issue，而不是纯文本

`issues[]` 单条至少包含：

- `rule_id`
- `severity`
- `message`
- `target`

可选字段：

- `observed`
- `expected`
- `box_refs`

## QC Profiles

### `publication_evidence_curve`

适用：

- ROC / PR / Calibration / Decision Curve

规则至少包括：

- 标题框、x 轴标题框、y 轴标题框都存在
- 所有文本框都落在 device 范围内
- legend box 不与 panel box 相交
- title / axis title / caption 彼此不相交
- 所有 series 坐标长度合法
- reference line 若存在，其坐标在 device domain 内

### `publication_survival_curve`

适用：

- Kaplan-Meier / Cumulative Incidence

规则至少包括：

- 与 curve 类共用的文字和边界框规则
- annotation block 若存在，不得与 panel 或 legend 相交
- 分组曲线至少一组
- 所有时间点和概率值有限

### `publication_embedding_scatter`

适用：

- UMAP / PCA

规则至少包括：

- 标题、轴标题、legend box 存在
- legend box 不与 panel 相交
- 所有点都在 panel domain 内
- group label 唯一且非空

### `publication_heatmap`

适用：

- Group Comparison Heatmap / Correlation Heatmap

规则至少包括：

- heatmap tile 区域存在
- colorbar box 存在且不与 panel 相交
- annotation text box 若启用，不得越出对应 tile box
- x/y label 与 tick label 不得越界
- correlation heatmap 额外检查对称性与方阵完整性

### `publication_forest_plot`

适用：

- Main-effect forest

规则至少包括：

- row label box、estimate marker、CI segment 都存在
- reference line 存在
- 任一 row label box 不与 panel box 相交
- estimate marker 必须位于 `lower` 到 `upper` 区间对应的图上位置

### `publication_shap_summary`

适用：

- SHAP summary beeswarm

规则至少包括：

- zero line 存在
- colorbar box 存在
- feature row boxes 不重叠
- 任一点的 y 位置必须落在所属 feature row box 内
- title / x-axis / colorbar 不得越界或互相相交

## Renderer Responsibilities

### R Renderers

R evidence renderer 在导出 `png/pdf` 之外，必须额外导出 layout sidecar。

约束：

- sidecar 必须来自 `ggplotGrob` / `grid` / `gtable` 的内部几何结果
- 不允许通过导出位图后再用 OCR 推断文本位置

### Python Renderers

Python renderer 在 `matplotlib` draw 之后，从 artist bbox 中提取几何信息，生成 sidecar。

适用于：

- 当前 `cohort_flow_figure`
- 当前 `shap_summary_beeswarm`
- 后续任何 `renderer_family = python` 的 evidence template

## Publication Gate Changes

`medical_publication_surface` 不执行 QC，但应收紧校验：

- `qc_result.status` 必须存在
- `qc_result.engine_id` 必须存在
- `qc_result.layout_sidecar_path` 必须存在
- `qc_result.checked_at` 必须存在
- 若 `status = fail`，则 gate 必须阻断
- `qc_result.qc_profile` 必须与 registry/profile 对齐

## Auditable Spec Surface

为了让“八大类模板 + schema contract”成为可审计对象，而不是只存在于 spec 文本里，实施层应新增一个稳定文档导出面：

- `guides/medical_display_template_catalog.md`

这个稳定文档应由结构化真相源生成，而不是手写维护。

它至少包含：

- 八大类模板目录
- 每个 template 的 `renderer_family`
- 每个 template 的 `input_schema_id`
- 每个 template 的 `required_exports`
- 每个 template 的 `qc_profile`
- 每个 schema 的字段定义与嵌套结构

内部真相源建议新增一个单独模块承载这些 schema contract，而不是让 `display_surface_materialization.py` 和测试夹具成为事实上的 schema 文档。

## Implementation Shape

建议拆成三层：

### 1. Schema Contract Layer

新增结构化 schema contract 模块，负责：

- 八大类目录
- template -> schema 绑定
- schema 字段定义
- schema 校验规则摘要

### 2. QC Execution Layer

新增 display layout QC 模块，负责：

- 读取 renderer sidecar
- 按 `qc_profile` 执行规则
- 产出结构化 `qc_result`

### 3. Materialization Integration Layer

在 `display_surface_materialization` 中：

- 调 renderer
- 要求 renderer 同时产出 sidecar
- 调 QC engine
- 把 `qc_result` 写入 catalog

## Testing Strategy

至少覆盖：

### 1. Schema Contract Tests

- 八大类目录完整
- 12 个 template 都有 schema 绑定
- 每个 schema 的必填字段和嵌套结构可枚举

### 2. QC Engine Unit Tests

- 合法 sidecar -> `pass`
- legend/panel overlap -> `fail`
- title out of bounds -> `fail`
- correlation matrix 不对称 -> `fail`
- forest CI 区间非法 -> `fail`
- SHAP row overlap -> `fail`

### 3. Materialization Integration Tests

- 物化时生成 `layout.json`
- catalog 中写入真实 `qc_result`
- `status=fail` 的 figure 不得被 publication gate 放行

## Risks

### 1. Renderer Sidecar Drift

如果 sidecar 是手工拼接、没有稳定来源，会很快漂移。

对策：

- sidecar 只能来自绘图库内部几何对象
- 不允许额外人工修正 bbox

### 2. QC Rule Inflation

如果每个模板都单独写很多规则，系统会迅速变重。

对策：

- 先按 `qc_profile` 分层
- 让多个 template 共享 profile

### 3. Doc Drift

如果 schema 文档靠手写，会与 registry/validator 漂移。

对策：

- 最终稳定文档由结构化真相源生成
- 不把测试夹具当文档

## Recommended Next Step

下一步先做两件事：

1. 写 implementation plan，把 schema contract layer、QC engine、materialization integration 分成独立任务。
2. 先落地 evidence figure 的 QC sidecar + `qc_result`，随后再导出稳定的 `guides/medical_display_template_catalog.md`。
