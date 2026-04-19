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
  - 证据型模板：`66`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`78`
- 最近一次已吸收完成的 capability cluster：
  - `G / cnv_recurrence_summary_panel`
  - `cnv_recurrence_summary_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / next-cluster routing and owner-round open`
- Family cluster：`G`
- Capability cluster：`richer mutation-landscape or broader genomic composite beyond the first CNV-summary lower bound`
- Owner worktree：`unassigned`
- 状态：`routing_open`

### Fresh Absorb Result

- `cnv_recurrence_summary_panel` 已 absorb 到当前 `main`；
- `G/E` 当前 omics-native lower bound 已正式扩到五基线：
  - `gsva_ssgsea_heatmap`
  - `pathway_enrichment_dotplot_panel`
  - `omics_volcano_panel`
  - `oncoplot_mutation_landscape_panel`
  - `cnv_recurrence_summary_panel`
- 当前下一轮还没有 owner worktree，接下来先做 candidate 固定与 owner brief 收口。

### 本轮核心问题

当前这一轮要回答的是：

> 在 `gsva_ssgsea_heatmap`、`pathway_enrichment_dotplot_panel`、`omics_volcano_panel`、`oncoplot_mutation_landscape_panel` 与 `cnv_recurrence_summary_panel` 已经形成当前 `G/E` 五基线的前提下，下一条 `G` 家族 capability cluster 应该优先把哪一种更高阶正文图式收成单一 bounded follow-on，使论文能够进一步回答“更宽的 mutation-landscape 叙事是否值得正式模板化”或“更完整的 genomic composite 是否已经具备稳定的 schema / renderer / QC / regression 收口条件”。

### Fresh Route 收敛

当前 reroute 已明确：

1. `cnv_recurrence_summary_panel` 已经 absorb 到当前 `main`，`G/E` 当前最小五基线已经成立。
2. 当前下一轮仍优先留在 `G` 家族，先从 richer mutation-landscape 与 broader genomic composite 两个方向里收成一个单一 bounded candidate。
3. 只有在 paper question、最小 panel 结构、最小数据前提、继承关系与最小 schema / renderer / QC / regression 写集全部清楚后，才开新的 owner worktree。
4. `D/E/G` 更高阶 multi-view atlas follow-on 与 `F` 更高阶 explanation scene 继续留在后继 reroute 池。

### 本轮边界

本轮只做下面三块：

1. 在 `G` 家族里把下一条 follow-on 收成单一 bounded candidate；
2. 明确它相对当前五基线的继承关系，避免把下一轮扩成无边界的“更大组学拼图”；
3. 在 owner round 真正打开前，就把 paper question、最小 panel 结构、最小数据前提、最小写集与退出条件写清楚。

## 预期写集

当前 routing round 预计只触碰下面这组最小写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- 必要时补充新的 bounded candidate brief
- 只有 candidate fixed 后，才为下一个 `G` owner round 打开新的独立 worktree

## 最低退出条件

只有同时满足下面条件，当前 routing round 才算完成：

1. 下一个 `G` follow-on 已固定为单一 bounded capability cluster；
2. owner brief 已明确 paper question、最小 panel 结构、最小数据前提、继承关系与最小写集；
3. 新 owner worktree 已从最新干净 `main` 打开；
4. secondary / tertiary 候选顺序已明确，不再让旧的 `cnv` round 状态持续污染路由判断。

## 当前轮次结束后的候选

当前轮次结束后，secondary 候选按下面顺序继续：

1. `G / richer mutation-landscape or broader genomic composite beyond the first CNV summary lower bound`
2. `D/E/G / richer manifold or higher-order multi-view atlas follow-on only if new real-paper demand proves the current context-support lower bound insufficient`
3. `F / higher-order explanation scene only if new real-paper demand proves the current grouped-local + support-domain lower bound insufficient`

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
