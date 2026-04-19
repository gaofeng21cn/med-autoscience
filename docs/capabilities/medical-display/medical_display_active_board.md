# Medical Display Active Board

## 文档定位

这个文件是 medical display 主线当前唯一的 tracked active execution surface。

用它回答下面五个问题：

- 当前唯一 active round 是什么；
- 当前处于哪个 phase；
- 下一步应该实现什么；
- merge-back 前最低需要满足哪些验证条件；
- 当前 round 结束后，下一个候选 capability cluster 是什么。

这个文件取代了过去把项目本地 `.omx/`、`.codex/` 状态当作执行面的做法。

`docs/history/omx/` 下的材料只保留为历史审计面，不再参与当前路由。

## 当前主线状态

- `A-H` 首个审计基线覆盖：`8/8`
- 当前 strict audited inventory：
  - 证据型模板：`62`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`74`
- 最近一次已吸收完成的 capability cluster：
  - `H / broader transportability and center-coverage follow-on beyond the current recalibration-governance lower bound`
  - `center_transportability_governance_summary_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 5 / integration / merge-back / cleanup`
- Family cluster：`F`
- Capability cluster：`shap_grouped_local_support_domain_panel`
- Owner worktree：`/Users/gaofeng/workspace/med-autoscience/.worktrees/medical-display-f-explanation-20260419`
- 状态：`merge_back_ready`

### 本轮核心问题

当前这一轮要回答的是：

> 在 `shap_summary_beeswarm`、`shap_bar_importance`、`shap_signed_importance_panel`、`shap_multicohort_importance_panel`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`shap_force_like_summary_panel`、`shap_grouped_local_explanation_panel`、`shap_grouped_decision_path_panel`、`shap_multigroup_decision_path_panel`、`partial_dependence_ice_panel`、`partial_dependence_interaction_contour_panel`、`partial_dependence_interaction_slice_panel`、`partial_dependence_subgroup_comparison_panel`、`accumulated_local_effects_panel` 与 `feature_response_support_domain_panel` 已经入库的前提下，如何把 grouped-local comparison 与 matched support-domain context 合成一个正文可直接使用的 bounded explanation scene，使论文能够同时回答“为什么模型做出这样的判断”和“这个解释在什么支持域里站得住”，并继续保持正文主叙事可审计、可回归、可复用。

### Fresh Route 收敛

当前 reroute 已明确：

1. `H` broader transportability and center-coverage follow-on 已经用 `center_transportability_governance_summary_panel` 正式收口。
2. 当前 `F` round 已收敛为单一 bounded 模板 `shap_grouped_local_support_domain_panel`，继续坚持 manuscript-facing composite 路线。
3. `D/E/G` 更高阶 manifold / multi-view atlas follow-on 与 `C/H` calibration appendix / robustness synthesis 继续留在后继 reroute 池。
4. 当前 round 已完成 schema / renderer / QC / docs / verify 闭环，下一步进入 absorb / push / cleanup。

### 本轮边界

本轮只做下面三块：

1. 固定 `F` 家族当前 owner 模板为 `shap_grouped_local_support_domain_panel`；
2. 在 `F` 当前 round 里，复用现有 grouped-local 与 support-domain vocabulary，并显式新增 local-to-support feature-order governance；
3. 把 schema / renderer / QC / regression / tracked docs 一起闭环，不再把当前 round 停在 owner brief 阶段。

## 预期写集

下一轮 owner implementation 预计触碰下面这组最小写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/display_source_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/display_layout_qc.py`
- 对应 `F` follow-on renderer 文件
- 对应 `F` / cross-paper golden regression tests
- `tests/test_display_layout_qc.py`
- 仅在 template inventory 真相变化后触碰 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`、`medical_display_arsenal_history.md`、`medical_display_family_roadmap.md`、`medical_display_template_backlog.md`

## 最低退出条件

只有同时满足下面条件，当前 `F` owner round 才算完成：

1. `shap_grouped_local_support_domain_panel` 已正式入库为单一 bounded manuscript-facing template；
2. input schema、source contract、materialization、renderer、layout QC 与 regression 已一起闭环；
3. fresh verify 至少覆盖该 `F` lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 当前轮次结束后的候选

当前轮次结束后，secondary 候选按下面顺序继续：

1. `D/E/G / richer manifold or higher-order multi-view atlas follow-on only if new real-paper demand proves the current context-support lower bound insufficient`
2. `C/H / calibration appendix or higher-order robustness synthesis only if new real-paper demand proves the current broader-heterogeneity lower bound insufficient`
3. `H / broader transportability or higher-order center-governance synthesis only if new real-paper demand proves the current center_transportability_governance_summary_panel lower bound insufficient`

## 明确不是执行面

下面这些都不是当前 active execution surface：

- 项目本地 `.omx/` prompt / report state
- 项目本地 `.codex/` prompt / report state
- `docs/history/omx/` 下的历史材料
- 已经 absorb 完成的旧 owner worktree 便签

## 更新规则

只有在以下任一情况发生时才更新本文件：

1. active round 改变；
2. phase 改变；
3. next-candidate 顺序改变；
4. audited inventory 发生实质变化；
5. 当前 round absorb 完成并发生 reroute。
