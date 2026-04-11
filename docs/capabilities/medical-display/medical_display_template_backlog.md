# Medical Display Template Backlog

## Purpose

这个文档定义 display surface 的扩容边界，但它不再把已经清掉的锚点论文假设继续留在 active backlog 里。

当前完成态真相优先看：

- `./medical_display_audit_guide.md`
- `./medical_display_template_catalog.md`
- `./medical_display_anchor_paper_audit.md`

## Current Audited Inventory

截至当前工作树：

- Evidence figure templates: `23`
- Illustration shells: `1`
- Table shells: `5`
- Total audited templates: `29`

新增并已进入正式 audited surface 的 anchor-driven 能力：

- `risk_layering_monotonic_bars`
- `binary_calibration_decision_curve_panel`
- `model_complexity_audit_panel`
- `performance_summary_table_generic`
- `grouped_risk_event_summary_table`

## Anchor-Driven Backlog Status

`001` 与 `003` 之前驱动过的 active backlog 现在已经重判：

- `001 direct migration pack`：已不再是 active backlog；study-owned `paper/` root 已建立并通过 cross-paper verification。
- `003 risk_layering_monotonic_bars` / `binary_calibration_decision_curve_panel` / `model_complexity_audit_panel`：已不再是 gap；已正式进入 audited repo surface。
- `003 performance summary` / `grouped risk event summary`：已不再是 table-shell gap；已正式进入 audited repo surface。
- `Figure 1 unified shell upgrade`：不再作为当前 backlog blocker；当前真实 submission surfaces 已稳定承载 `F1 cohort_flow_figure`，且 `001` legacy sidecar role 已在正式 materializer 中被兼容。

## Current Boundary

当前没有新的 anchor-paper display template gap 需要立即实现。

只有在 fresh truth 再次证明下面任一条件时，才允许开启下一轮模板扩容：

1. 新的真实 study-owned paper root 暴露出 audited contract 无法表达的论文语义。
2. 现有 template 能渲染，但 schema / QC / submission surface 不能稳定闭环。
3. 真实论文表达需要更清晰的正式 contract，而不是 renderer 层的临时补救。

## Promotion Rules

只有同时满足下面条件的候选模板，才允许进入 audited surface：

1. 能写成显式输入 schema，而不是靠自由文本指挥 renderer。
2. 统计输入边界稳定，不依赖渲染阶段临时推断。
3. 物化导出能稳定生成 `png/pdf` 与可审计 sidecar。
4. 能复用现有 `qc_profile`，或值得新增一个明确的 profile。
5. 不允许把聚类、重排、避让、文字修正放到 renderer 内做启发式补救。

## Inactive General Expansion Queue

下面这些候选仍可作为未来扩容候选，但当前不是 active mainline：

- `clinical_impact_curve_binary`
- `multivariable_forest`
- `shap_bar_importance`
- `confusion_matrix_heatmap_binary`
- `temporal_external_validation_overview`

重新激活它们的前提是：

- fresh anchor-paper truth 已经收口；
- 或者新的真实研究交付明确暴露了这些模板的稳定需求。
