# Medical Display Template Backlog

## Purpose

这个文档定义 display surface 的内部扩容目标，用来回答两个问题：

1. 当前 audited display surface 已经做到多少。
2. `v1` 计划把总模板数收敛到多少，以及每个大类准备扩到哪里为止。

它是内部 backlog，不是当前完成态真相源。

当前完成态仍以：

- `docs/medical_display_audit_guide.md`
- `docs/medical_display_template_catalog.md`

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

## Anchor-Paper Priority Queue

当前优先级不再只按“通用高频图型”抽象排序，而是先由两篇真实锚点论文驱动：

- `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk`
- `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup`

更细的资产映射见：

- `docs/medical_display_anchor_paper_audit.md`

当前固定执行顺序已经从“继续补模板”切到“真实课题 QC tighten”：

1. `003` reporting / publication gate tighten
2. `001` submission companion / graphical abstract contract tighten
3. `002` real-study `Phase C / Phase D` promotion
4. 完成以上真实课题 tighten 之后，再回到通用扩模板队列

已进入正式主线、因此不再属于当前未完成 backlog 的 `003` 驱动项：

- `risk_layering_monotonic_bars`
- `binary_calibration_decision_curve_panel`
- `model_complexity_audit_panel`
- `performance_summary_table_generic`
- `grouped_risk_event_summary_table`

当前 backlog 重点已经不是“再补一轮 catalog 名义数量”，而是让真实课题沿正式 controller / contract 链路完成清关。

### 1. `003` Reporting / Publication Gate Tighten

`003` 的正式 display surface 已经通过，当前 blocker 已转移到 reporting / publication 合同面。优先要清的不是 renderer，而是下面这些正式文件与语义检查：

- `reporting_guideline_checklist.json`
- `methods_implementation_manifest.json`
- `results_narrative_map.json`
- `figure_semantics_manifest.json`
- `derived_analysis_manifest.json`
- `manuscript_safe_reproducibility_supplement.json`
- `endpoint_provenance_note.md`
- manuscript-facing forbidden terms 清理

这一步的重点是把“可自动化吸收的结构化 blocker”和“必须回到真实 paper truth 才能闭合的 manuscript blocker”分开，而不是再把问题误判成 display template 缺口。

### 2. `001` Submission Companion / Graphical Abstract Contract Tighten

`001` 当前 publication surface 的主要缺口不再是主文 Figure / Table template，而是：

- `submission_graphical_abstract` 未正式注册
- `submission_companion` renderer semantics 尚未进入正式 contract

这说明 submission companion 仍未完全进入当前 publication-facing renderer / validator 主线。该项应作为下一条 tightening 目标单独处理，而不是与 `003` gate 问题混在一起。

### 3. `002` Real-Study `Phase C / Phase D` Promotion

`002` 目前仍停留在 Figure 1 主线化，尚未把 `Phase C / Phase D` 的 evidence figure 与 table shell 升级进真实课题 controller 主线。下一步应补齐：

- `medical_analysis_contract.json`
- `medical_reporting_contract.json`
- `publication_style_profile.json`
- `display_overrides.json`
- 对真实 `study_design_cohort_flow.json` / `clinical_metadata_packet.md` 的正式 consumer 路径

目标不是继续做一次性 paper patch，而是让 `002` 真正沿正式 controller / hydration / publication gate 链路推进。

### 4. Return To General Expansion

只有当 `003` / `001` / `002` 这三条真实课题 tighten 线都闭合后，才应重新把资源投入到更泛化的 catalog 扩容队列。

## General Expansion Queue

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
