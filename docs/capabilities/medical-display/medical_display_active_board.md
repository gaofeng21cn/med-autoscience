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
  - 证据型模板：`45`
  - 插图壳层：`2`
  - 表格壳层：`5`
  - 总模板数：`52`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / next-cluster scouting and demand routing`
- Family cluster：`H`
- Capability cluster：`workflow_fact_sheet_panel_or_design_evidence_composite_shell`
- Owner worktree：`none`
- 状态：`owner_brief_pending`

### 本轮核心问题

当前这一轮要回答的是：

> 在 `shap_grouped_decision_path_panel` 已正式吸收进主线之后，`H` 家族下一步应该先把 `workflow_fact_sheet_panel` 还是 `design_evidence_composite_shell` 收口成更高价值但仍然 bounded 的壳层能力，并且如何在开工前先锁定 owner brief，避免重新滑回自由拼装的研究设计拼图。

### 本轮边界

本轮只做下面三块：

1. `next H-cluster demand routing from real-paper / exemplar pressure`
2. `minimal owner brief for workflow_fact_sheet_panel_or_design_evidence_composite_shell`
3. `write-set / verification-slice / stop-condition lock before opening the next owner worktree`

本轮明确不做：

- `F` 家族更高阶 partial-dependence follow-on
- `D/E/G` 更大的 atlas / spatial / trajectory 多视图复合图式
- 自由拼装式 workflow / design-evidence scene composition 系统
- 任何脱离显式 schema / shell contract 的临时论文拼图

## 预期写集

当前 round 只应触碰实现新 capability cluster 所需的最小写集，通常包括：

- `display-packs/fenggaolab.org.medical-display-core/templates/...`
- `display-packs/fenggaolab.org.medical-display-core/src/...`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/display_layout_qc.py`
- 仅在必要时触碰 pack runtime / catalog sync 相关 surface
- 反映新审计真相的定向文档
- 定向回归测试

## 最低退出条件

只有同时满足下面条件，当前 scouting round 才能进入下一个 owner implementation round：

1. 下一候选 capability cluster 已固定。
2. owner brief 已明确最小写集、最小验证面与不做事项。
3. 已确认当前没有别的 active display owner worktree 与其写集冲突。
4. 当前 round 不再依赖项目本地 `.omx/`、`.codex/` 状态。

## 最低验证要求

每一轮 scouting / routing 至少要留下：

- 下一候选的 paper question 与 exemplar 理由；
- 最小实现边界；
- 计划中的 targeted tests / golden regression slice；
- 允许开新 owner worktree 的明确条件。

## 当前轮次结束后的候选

当前轮次结束后，下一批候选按下面顺序继续：

1. `H / workflow_fact_sheet_panel` 或 `design_evidence_composite_shell`
2. `D/E/G / richer atlas-spatial-trajectory multi-view follow-on`
3. `F / higher-order partial-dependence follow-on beyond the grouped-decision-path lower bound`

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
