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
  - 证据型模板：`81`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`93`
- 最近一次已吸收完成的 capability cluster：
  - `A/E / confusion_matrix_heatmap_binary`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / post-absorb reroute`
- Family cluster：`A/E absorbed, reroute reopened`
- Capability cluster：`confusion_matrix_heatmap_binary closed`
- Owner worktree：`not_opened`
- 状态：`ready_for_next_owner_round`

### Fresh Mainline Result

- 当前主干已吸收的最新 capability cluster 是 `confusion_matrix_heatmap_binary`；
- strict audited inventory 已更新到：
  - `Data Geometry`：`15`
  - `Matrix Pattern`：`15`
  - evidence figures：`81`
  - total templates：`93`
- `confusion_matrix_heatmap_binary` 已把 `A/E` 的高频二分类诊断矩阵表达从“通用 heatmap 可勉强承接”推进到正式的 binary confusion-matrix lower bound，并把显式 `2x2` 网格、`row/column/overall` normalization 语义、`metric_name`、行列顺序和数值边界固化进单一契约；
- 下一步是按 reroute 规则固定下一个 capability cluster，再新开唯一 owner worktree。

### 当前轮次目标

当前下一轮要回答：

> 在 `A/E` 家族 binary confusion-matrix heatmap 已经 absorb 完成的前提下，下一条最值得继续扩容的 manuscript-facing capability cluster 应该是什么，以及它是否值得为新的真实论文 demand 开启唯一 owner round。

### 当前 Next Baton

当前 baton 已明确：

1. 最新的 `D/E/G / celltype_marker_dotplot_panel` owner round 已经 absorb 完成。
2. 最新的 `A/E / confusion_matrix_heatmap_binary` owner round 已完成 closeout，strict audited inventory 已推进到 `81 / 7 / 5 / 93`。
3. 当前没有打开中的 owner worktree，下一轮要先 reroute，再开唯一 owner round。
4. 下一轮优先继续比较 `A/H`、`F`、`D/E/G` 与 `C/H` 的真实论文 demand 与 capability-cluster 价值。

### 下一轮边界

下一轮只做下面三块：

1. 先 fresh 读取当前 audit guide / template catalog / arsenal / active board；
2. 再比较 `A/H`、`F`、`D/E/G` 与 `C/H` 的真实论文 demand 哪一条最值得开启下一轮；
3. 只有 reroute 固定后，才新开唯一 owner worktree 进入实现。

## 预期写集

下一轮 owner implementation 预计先触碰下面这组前置路由写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`

只有 reroute 固定后，才允许再触碰：

- 对应新 cluster 的 registry / schema / source contract / materialization / renderer / QC / regression 文件
- 以及仅在 template inventory 真相变化后需要同步的 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`、`medical_display_arsenal_history.md`、`medical_display_family_roadmap.md`

## 最低退出条件

只有同时满足下面条件，下一轮 owner round 才允许打开：

1. 新候选必须有清晰的论文问题、最小 panel 结构与最小数据前提；
2. 新候选必须明确继承当前 lower bound，而不是退回 paper-local 修图；
3. reroute 必须明确为什么当前应该优先 `A/H`、`F`、`D/E/G` 或 `C/H`；
4. 打开新的 owner worktree 前，当前已完成 round 的 absorb / cleanup 必须完成。

## 当前轮次结束后的候选

当前本轮完成后的 reroute 候选按下面顺序继续：

1. `A/H / temporal_external_validation_overview only if new real-paper demand proves the current ROC/PR/calibration/clinical-impact/performance/confusion lower bound insufficient`
2. `F / higher-order explanation scene or AI-first visual hardening only if new real-paper demand proves the current signed-importance + local-waterfall + support-domain scene and grouped decision-scene lower bound insufficient`
3. `D/E/G / richer higher-order multi-view atlas follow-on only if new real-paper demand proves the current multimanifold context-support lower bound insufficient`
4. `C/H / calibration appendix or higher-order robustness synthesis only if new real-paper demand proves the current compact-estimate + coefficient-path + broader-heterogeneity lower bound insufficient`

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
