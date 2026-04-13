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
  - 插图壳层：`4`
  - 表格壳层：`5`
  - 总模板数：`54`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 5 / integration / merge-back / reroute`
- Family cluster：`H`
- Capability cluster：`design_evidence_composite_shell`
- Owner worktree：`.worktrees/medical-display-design-evidence-composite-20260413T054244Z`
- 状态：`merge_back_ready`

### 本轮核心问题

当前这一轮要回答的是：

> 如何把 `design_evidence_composite_shell` 作为固定 `workflow ribbon + three summary panels` 的 bounded illustration shell 正式落进 registry / schema / materialization / QC / catalog truth，并在 merge-back 前锁定它不会滑回自由拼装式 design-evidence scene。

### 本轮边界

本轮只做下面三块：

1. `design_evidence_composite_shell` 的 manifest / schema / renderer / QC / materialization 闭环
2. 与新 shell 对应的 tracked docs / catalog sync
3. merge-back 前最低验证面与 reroute 入口锁定

本轮明确不做：

- 自由拼装式 workflow / design-evidence scene composition 系统
- `D/E/G` 更大的 atlas / spatial / trajectory 多视图复合图式
- `F` 家族更高阶 partial-dependence follow-on
- `H` 家族更广的 baseline-balance / missingness / QC-shell follow-on

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

1. `H / design_evidence_composite_shell`
2. `D/E/G / richer atlas-spatial-trajectory multi-view follow-on`
3. `F / higher-order partial-dependence follow-on beyond the grouped-decision-path lower bound`
4. `H / baseline-balance / missingness / QC-shell follow-on`

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
