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
  - 证据型模板：`52`
  - 插图壳层：`5`
  - 表格壳层：`5`
  - 总模板数：`62`
- 最近一次已吸收完成的 capability cluster：
  - `F / support-domain explanation panel follow-on beyond the current higher-order partial-dependence lower bound`
  - `feature_response_support_domain_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / next-cluster scouting / owner-brief routing`
- Family cluster：`D/E/G`
- Capability cluster：`larger atlas-spatial-trajectory multi-view follow-on beyond the current storyboard lower bound`
- Owner worktree：`未开启（F / feature_response_support_domain_panel 已 absorb、fresh verify 并完成 reroute；下一轮待 fresh route 后再开唯一 owner worktree）`
- 状态：`routing_ready`

### 本轮核心问题

当前这一轮要回答的是：

> 在 `single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel` 与 `atlas_spatial_trajectory_storyboard_panel` 已经入库的前提下，如何为 `D/E/G` 选定下一个仍然 bounded、可审计、真正由真实论文 demand 驱动的 larger atlas-spatial-trajectory multi-view follow-on，而不是重新滑回自由 atlas dashboard / storyboard 拼图。

### 本轮边界

本轮只做下面三块：

1. 固定 `D/E/G` 家族下一候选 capability cluster，不在更大 atlas / spatial / trajectory 多视图变体、organ-specific gallery、自由 dashboard 等多个 follow-on 之间来回摆动
2. 写清 owner brief：paper question、最小边界、最小写集、最小验证面、golden regression slice 与明确不做事项
3. 在开新 owner worktree 之前，锁定 reroute 口径与 secondary candidate 顺序

本轮明确不做：

- 重开刚刚 absorb 的 `F / feature_response_support_domain_panel`
- 没有 owner brief 就直接开新的 `D/E/G` 家族实现 worktree
- 任意数量视图的 atlas wall、free-form dashboard、caption-driven storybook 或 organ-specific gallery
- 顺手把 `H` 壳层 follow-on、`C/H` heterogeneity follow-on，或 `F` 的 multi-group grouped-local / decision-path 扩容并入当前 round

## 预期写集

当前 routing round 只应触碰 reroute 所需的最小写集，通常包括：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- 仅在 reroute 口径或 inventory 真相变化时触碰 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`
- 在 `D/E/G` 家族 owner brief 固定前，不触碰新的核心 display 实现文件

## 最低退出条件

只有同时满足下面条件，当前 routing round 才能进入下一个 owner implementation round：

1. `D/E/G` 家族下一候选 capability cluster 已固定。
2. owner brief 已明确最小写集、最小验证面与不做事项。
3. 已确认当前没有别的 active display owner worktree 与其写集冲突。
4. `F / feature_response_support_domain_panel` 这一轮已 absorb、fresh verify、push、cleanup 完成。

## 最低验证要求

每一轮 scouting / routing 至少要留下：

- 下一候选的 paper question 与 exemplar 理由；
- 最小实现边界；
- 计划中的 targeted tests / golden regression slice；
- 允许开新 owner worktree 的明确条件。

## 当前轮次结束后的候选

当前轮次结束后，secondary 候选按下面顺序继续：

1. `H / broader QC / batch-effect / transportability shell follow-on beyond the first baseline-missingness-QC composite shell`
2. `C/H / coefficient-path or broader heterogeneity-summary follow-on beyond the compact effect-estimate lower bound`
3. `F / multi-group grouped-local or decision-path follow-on only if new paper demand proves the current support-domain lower bound insufficient`

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
