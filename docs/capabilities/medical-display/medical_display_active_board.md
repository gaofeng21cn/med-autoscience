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
  - 证据型模板：`42`
  - 插图壳层：`2`
  - 表格壳层：`5`
  - 总模板数：`49`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 5 / integration / merge-back / monitor`
- Family cluster：`F`
- Capability cluster：`shap_multicohort_importance_panel`
- Owner worktree：当前专用 display worktree
- 状态：`merge_back_ready`

### 本轮核心问题

本轮要回答的是：

> 如何把 manuscript-facing 的跨 cohort 全局特征重要性对照稳定表达成多 panel、共享 feature 顺序、共享 x 语义、可审计、可复用的 bounded contract，并把 cohort identity、rank strict order、cross-panel feature-order governance、panel label anchoring 与 value-label containment 一起固化进正式模板路径。

### 本轮边界

本轮只做下面三块：

1. `bounded multi-panel SHAP multicohort importance overview`
2. `strict panel-id / cohort-identity / bar-rank / shared-feature-order contract`
3. `parallel horizontal bar geometry + panel-label / feature-label / value-label QC governance`

本轮明确不做：

- workflow / design-evidence shells
- 自由拼装式 explanation scene composition 系统
- grouped-local-explanation follow-on
- 自由拼装的 explanation scene composition

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

只有同时满足下面条件，当前 round 才能算 merge-back ready：

1. 新的 bounded template contract 已端到端落地。
2. deterministic QC 已能拦住本 cluster 已知的 lower-bound failure。
3. 新模板已完成 registry / catalog / pack 对齐。
4. focused regression 通过。
5. publication-facing display contract 仍然一致。
6. owner worktree clean，结果可吸收回 `main`。

## 最低验证要求

每一轮 active round 至少要留下：

- 新 capability 的 targeted template/runtime tests；
- 对应 family cluster 的 relevant golden regression；
- `scripts/verify.sh` 或经说明的更窄 display verification slice；
- 提交信息或定向文档中的简短 merge-back 说明。

## 当前轮次结束后的候选

只有在 `shap_multicohort_importance_panel` 被 absorb 之后，才允许 reroute 到下一批候选：

1. `F / grouped-local-explanation follow-on`
2. `H / workflow_fact_sheet_panel` 或 `design_evidence_composite_shell`
3. `D/E/G / richer atlas-spatial-trajectory multi-view follow-on`

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
