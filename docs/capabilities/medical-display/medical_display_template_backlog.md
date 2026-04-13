# Medical Display Template Backlog

## Purpose

这个文档现在只负责记录 display 的候选扩容池与历史 backlog 清理结果。

它不是当前 active execution surface。

当前 active round 与当前 phase 一律以 [medical_display_active_board.md](./medical_display_active_board.md) 为准。

当前完成态真相优先看：

- `./medical_display_audit_guide.md`
- `./medical_display_template_catalog.md`
- `./medical_display_anchor_paper_audit.md`
- `./medical_display_active_board.md`

## Current Audited Inventory Snapshot

截至当前审计真相：

- Evidence figure templates: `45`
- Illustration shells: `3`
- Table shells: `5`
- Total audited templates: `53`

这些数字来自当前 audited guide / template catalog，而不是旧的锚点论文冻结快照。

## Historical Anchor-Driven Cleanup

`001` 与 `003` 曾经驱动过的历史 backlog 已经完成清理，不再作为当前 active blocker：

- `001 direct migration pack`
- `003 risk_layering_monotonic_bars`
- `003 binary_calibration_decision_curve_panel`
- `003 model_complexity_audit_panel`
- `003 performance summary`
- `003 grouped risk event summary`
- `Figure 1 unified shell upgrade`
- `H / workflow_fact_sheet_panel`
- `H / design_evidence_composite_shell`

这些条目保留在这里，只是为了说明它们已经出队，不应再持续污染当前判断。

## Current Candidate Pool

当前真正还可以继续扩容、但暂未进入当前 active round 的候选，主要是：

- `D/E/G / richer atlas-spatial-trajectory multi-view follow-on`
- `F / higher-order partial-dependence follow-on beyond the grouped-decision-path lower bound`
- `H / baseline-balance / missingness / QC-shell follow-on`

其中：

- `H / workflow_fact_sheet_panel` 已在本轮正式提升为 audited illustration shell，不再保留为当前候选。
- `H / design_evidence_composite_shell` 已在本轮正式提升为 audited illustration shell，不再保留为当前候选。
- `F / richer grouped-local-explanation variants beyond the first audited baseline` 已在本轮收口为 `shap_grouped_decision_path_panel`，不再保留为当前候选。

这些候选不等于必须立即实现。

只有当：

1. 当前 active round 已 absorb；
2. reroute 重新确认优先级；
3. 新的真实论文或高质量 exemplar 证明其价值；

它们才应进入新的 owner round。

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

## Longer-Horizon Inactive Queue

下面这些方向仍可作为更远期候选，但当前不是 active mainline：

- `clinical_impact_curve_binary`
- `multivariable_forest`
- `confusion_matrix_heatmap_binary`
- `temporal_external_validation_overview`

它们只有在新的真实研究交付或新的 exemplar 明确证明价值时，才应重新激活。
