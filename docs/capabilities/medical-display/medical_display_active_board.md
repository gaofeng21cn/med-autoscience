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
  - 证据型模板：`65`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`77`
- 最近一次已吸收完成的 capability cluster：
  - `G / omics volcano panel`
  - `omics_volcano_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 5 / integration / merge-back / cleanup`
- Family cluster：`G`
- Capability cluster：`oncoplot_mutation_landscape_panel`
- Owner worktree：`/Users/gaofeng/workspace/med-autoscience/.worktrees/medical-display-g-oncoplot-20260419T025341Z`
- 状态：`merge_back_ready`

### 本轮核心问题

当前这一轮要回答的是：

> 在 `gsva_ssgsea_heatmap`、`pathway_enrichment_dotplot_panel` 与 `omics_volcano_panel` 已经形成当前 `G/E` 三基线的前提下，如何把 top journal 常见的 oncoplot / mutation-landscape 主图正式沉淀成一个正文可直接使用的 bounded 模板，使论文能够稳定回答“哪些基因发生了什么类型的变异、样本级 mutation burden 如何分布、基因级 altered frequency 如何排序、关键临床或 cohort 注释如何和 mutation matrix 同步对齐”，并继续保持 sample order、gene order、mutation vocabulary、annotation-track completeness 与 burden/frequency 边栏语义全程可审计、可回归、可复用。

### Fresh Route 收敛

当前 reroute 已明确：

1. `pathway_enrichment_dotplot_panel` 与 `omics_volcano_panel` 已经 absorb 到当前 `main`，`G/E` 当前最小三基线已经成立。
2. 当前 `G` round 收敛为单一 bounded 模板 `oncoplot_mutation_landscape_panel`，继续坚持高频组学正文图直接 pack 化的路线。
3. richer mutation-landscape composite、`D/E/G` 更高阶 multi-view atlas follow-on 与 `F` 更高阶 explanation scene 继续留在后继 reroute 池。
4. 当前 round 已完成 schema / renderer / QC / regression / tracked-docs 闭环，并已进入 absorb / push / cleanup。

### 本轮边界

本轮只做下面三块：

1. 固定 `G` 家族当前 owner 模板为 `oncoplot_mutation_landscape_panel`；
2. 在当前 round 里，显式固定 shared `sample_order`、shared `gene_order`、mutation-class vocabulary、top burden bar、right-side altered-frequency bar 与 up-to-three annotation tracks 治理；
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
- 对应 `G` follow-on renderer 文件
- 对应 `G` / cross-paper golden regression tests
- `tests/test_display_layout_qc.py`
- 仅在 template inventory 真相变化后触碰 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`、`medical_display_arsenal_history.md`、`medical_display_family_roadmap.md`、`medical_display_template_backlog.md`

## 最低退出条件

只有同时满足下面条件，当前 `G` owner round 才算完成：

1. `oncoplot_mutation_landscape_panel` 已正式入库为单一 bounded manuscript-facing template；
2. input schema、source contract、materialization、renderer、layout QC 与 regression 已一起闭环；
3. fresh verify 至少覆盖该 `G` lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 当前轮次结束后的候选

当前轮次结束后，secondary 候选按下面顺序继续：

1. `G / richer mutation-landscape or multi-omics genomic summary beyond the first oncoplot lower bound`
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
