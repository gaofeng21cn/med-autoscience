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
  - 证据型模板：`58`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`70`
- 最近一次已吸收完成的 capability cluster：
  - `F / multi-group decision-path follow-on beyond the current two-group shared-baseline lower bound`
  - `shap_multigroup_decision_path_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / next-cluster reroute / owner brief needed`
- Family cluster：`F`
- Capability cluster：`multi-group grouped-local follow-on beyond the current multigroup decision-path lower bound`
- Owner worktree：`未开启`
- 状态：`brief_needed`

### 本轮核心问题

当前这一轮要回答的是：

> 在 `shap_grouped_local_explanation_panel`、`shap_grouped_decision_path_panel`、`shap_multigroup_decision_path_panel`、`feature_response_support_domain_panel`、`partial_dependence_interaction_slice_panel`、`partial_dependence_subgroup_comparison_panel` 与 `accumulated_local_effects_panel` 已经入库的前提下，如何把更宽的 multi-group grouped-local manuscript-facing explanation evidence 收束成新的 bounded template，使论文能够稳定回答“多组之间的局部解释差异是否清楚、共享特征顺序与基线是否仍可读、support-domain 下限之外是否还需要更强的 explanation scene”，并继续保持投稿面可审计、可回归、可复用。

### Fresh Route 收敛

当前 reroute 已明确：

1. `F` 家族 multi-group decision-path follow-on 已经用 `shap_multigroup_decision_path_panel` 正式收口。
2. 下一轮继续留在 `F` 家族 explanation follow-on，继续坚持 bounded manuscript-facing template 路线，直接服务 multi-group grouped-local 的进一步合同化。
3. 下一轮先收口 owner brief，再开唯一 owner worktree 进入实现。

### 本轮边界

本轮只做下面三块：

1. 固定 `F` 家族当前 owner 候选为 `multi-group grouped-local follow-on`；
2. 在 `F` 家族当前 round 里，继续复用现有 grouped-local / multigroup decision-path / support-domain vocabulary、shared feature-order discipline 与 bounded explanation contract；
3. 用新的 owner brief 明确最终单一候选后，再落正式 schema / renderer / QC / regression 写集。

## 预期写集

下一轮 owner implementation 预计触碰下面这组最小写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/display_source_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/display_layout_qc.py`
- 对应 explanation renderer 文件
- 对应 grouped-local regression tests
- 仅在 template inventory 真相变化后触碰 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`

## 最低退出条件

只有同时满足下面条件，当前 `F` owner round 才算完成：

1. `multi-group grouped-local follow-on` 已正式入库为单一 bounded explanation template；
2. input schema、source contract、materialization、renderer、layout QC 与 regression 已一起闭环；
3. fresh verify 至少覆盖该 `F` lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 当前轮次结束后的候选

当前轮次结束后，secondary 候选按下面顺序继续：

1. `D/E/G / richer multi-view atlas-spatial-trajectory composite follow-on beyond the current density / coverage support baseline`
2. `C/H / broader heterogeneity summary follow-on only if new real-paper demand proves the current compact + coefficient-path lower bound insufficient`
3. `H / broader transportability and center-coverage follow-on only if new real-paper demand proves the current recalibration-governance lower bound insufficient`

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
