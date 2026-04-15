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

- Evidence figure templates: `52`
- Illustration shells: `5`
- Table shells: `5`
- Total audited templates: `62`

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

当前真正还可以继续扩容、且仍停留在 backlog 而未进入当前 active round 的候选，主要是：

- `H / broader QC / batch-effect / transportability shell follow-on beyond the first baseline-missingness-QC composite shell`
- `C/H / coefficient-path or broader heterogeneity-summary follow-on beyond the compact effect-estimate lower bound`

其中：

- `D/E/G / larger atlas-spatial-trajectory multi-view follow-on beyond the current storyboard lower bound` 已在本轮 reroute 后转入 [medical_display_active_board.md](./medical_display_active_board.md) 作为当前 active round，不再留在 backlog 候选池。
- `C/H / compact estimate panel follow-on` 已在本轮正式 absorb 为 `compact_effect_estimate_panel`，不再保留在 backlog 候选池。
- `C/H / coefficient-path follow-on` 本轮不再作为当前 active 候选保留：
  - 原因：它更接近模型审计或自由 path scene，和现有 `model_complexity_audit_panel` 的 coefficient-stability 语义部分重叠，也更容易越过当前 active board 的 bounded 边界。
- `C/H / broader heterogeneity summary follow-on` 本轮也不作为当前 active 候选保留：
  - 原因：在 `compact_effect_estimate_panel` 这一层 lower bound 已刚刚入库的前提下，是否继续扩到更宽的 heterogeneous summary 仍需后续显式 reroute，而不应立刻并入当前 active round。
- `F / support-domain explanation panel follow-on beyond the current higher-order partial-dependence lower bound` 已在本轮正式收口为 `feature_response_support_domain_panel`，并已 absorb 入当前 `main` 且通过 fresh verify，不再留在 backlog 候选池。
- `F / multi-group grouped-local follow-on` 本轮不作为当前 active 候选保留：
  - 原因：当前真实 gap 先落在 feature-response support-domain / legend / annotation contract；直接扩到 `3+` group grouped-local scene 会同步放大 panel 数、shared-feature-order 与 row-alignment 治理负担，超出本轮 bounded 边界。
- `F / multi-group decision-path follow-on` 本轮不作为当前 active 候选保留：
  - 原因：现有 `shap_grouped_decision_path_panel` 的 two-group shared-baseline lower bound 还没有被真实论文 demand 证明不足，直接扩容会把当前 round 从 support-domain contract 滑回更大的 path scene。
- `F / annotation-only readability hardening` 本轮也不作为当前 active 候选保留：
  - 原因：当前需要的是把 support-domain、subgroup-legend 与 annotation 语义一起收进正式模板契约，而不是拆成 paper-local 标注微调或独立 readability patch。
- `D/E/G / atlas_spatial_trajectory_storyboard_panel` 已在本轮正式提升为 audited five-panel storyboard baseline，不再保留为当前候选。
- `F / higher-order partial-dependence follow-on` 已在本轮正式收口为 `partial_dependence_interaction_slice_panel`、`partial_dependence_subgroup_comparison_panel` 与 `accumulated_local_effects_panel`，不再保留为当前候选。
- `H / workflow_fact_sheet_panel` 已在本轮正式提升为 audited illustration shell，不再保留为当前候选。
- `H / design_evidence_composite_shell` 已在本轮正式提升为 audited illustration shell，不再保留为当前候选。
- `H / baseline-balance / missingness / QC-shell follow-on` 已在本轮正式收口为 `baseline_missingness_qc_panel`，不再保留为当前候选。
- `D/E/G / atlas_spatial_bridge_panel` 已在本轮正式提升为 audited four-block bridge baseline，不再保留为当前候选。
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
4. 对 `C/H` 而言，`compact_effect_estimate_panel` 已完成 absorb；后续是否继续做 `coefficient-path` 或更宽的 heterogeneity summary，默认排在当前 `D/E/G` 与 `H` reroute 之后重新评估。
5. 对 `F` 而言，`feature_response_support_domain_panel` 已经收口；后续只有在新的真实论文 demand 明确证明价值时，才重新评估 `multi-group grouped-local`、`multi-group decision-path` 或更高阶 explanation scene。

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
- `coefficient_path_panel`
- `broader_heterogeneity_summary_panel`
- `confusion_matrix_heatmap_binary`
- `temporal_external_validation_overview`
- `multi_group_grouped_local_explanation_panel`
- `multi_group_decision_path_panel`
- `annotation_governance_follow_on`
- `higher_order_explanation_scene_beyond_current_pd_ale_lower_bound`

它们只有在新的真实研究交付或新的 exemplar 明确证明价值时，才应重新激活。
