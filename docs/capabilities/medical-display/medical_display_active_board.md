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
- Capability cluster：`genomic_alteration_landscape_panel`
- Owner worktree：`/Users/gaofeng/workspace/med-autoscience/.worktrees/medical-display-g-genomic-alteration-20260419T045941Z`
- 状态：`owner_round_open`

### Fresh Absorb Result

- `cnv_recurrence_summary_panel` 已 absorb 到当前 `main`；
- `G/E` 当前 omics-native lower bound 已正式扩到五基线：
  - `gsva_ssgsea_heatmap`
  - `pathway_enrichment_dotplot_panel`
  - `omics_volcano_panel`
  - `oncoplot_mutation_landscape_panel`
  - `cnv_recurrence_summary_panel`
- 当前下一轮已经固定为一个更高阶但仍 bounded 的 `G` 家族模板，接下来直接进入 owner round。

### 本轮核心问题

当前这一轮要回答的是：

> 在 `gsva_ssgsea_heatmap`、`pathway_enrichment_dotplot_panel`、`omics_volcano_panel`、`oncoplot_mutation_landscape_panel` 与 `cnv_recurrence_summary_panel` 已经形成当前 `G/E` 五基线的前提下，如何把 top journal 常见的基因级 mutation + CNV alteration landscape 正式沉淀成一个正文可直接使用的 bounded 模板，使论文能够稳定回答“哪些基因在 cohort 内反复发生 mutation 或 copy-number alteration、这些 alteration 是否共享同一 sample order 与 cohort 注释语义、样本级 alteration burden 与基因级 alteration frequency 能否在同一图面里保持全程可审计、可回归、可复用”。

### Fresh Route 收敛

当前 reroute 已明确：

1. `cnv_recurrence_summary_panel` 已经 absorb 到当前 `main`，`G/E` 当前最小五基线已经成立。
2. 当前下一轮固定为 `genomic_alteration_landscape_panel`，优先做 richer mutation-landscape，而不是先扩成更宽的 genomic composite。
3. 这条 follow-on 直接承接高水平组学论文里高频出现的 mutation + CNV alteration landscape 结构，并把 `oncoplot + cnv` 从相邻模板推进到更统一的 gene-level manuscript-facing lower bound。
4. `D/E/G` 更高阶 multi-view atlas follow-on 与 `F` 更高阶 explanation scene 继续留在后继 reroute 池。

### 本轮边界

本轮只做下面三块：

1. 固定 `G` 家族当前 owner 模板为 `genomic_alteration_landscape_panel`；
2. 在当前 round 里，显式固定 shared `gene_order`、shared `sample_order`、alteration-state vocabulary、top burden bar、right-side gene-level alteration frequency 与 up-to-three annotation tracks 治理；
3. 把 schema / renderer / QC / regression / tracked docs 一起闭环，并让 `G` 家族从“相邻 oncoplot + CNV lower bound”推进到更统一的 gene-level genomic landscape lower bound。

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

1. `genomic_alteration_landscape_panel` 已正式入库为单一 bounded manuscript-facing template；
2. input schema、source contract、materialization、renderer、layout QC 与 regression 已一起闭环；
3. fresh verify 至少覆盖该 `G` lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 当前轮次结束后的候选

当前轮次结束后，secondary 候选按下面顺序继续：

1. `G / broader genomic composite beyond the first gene-level mutation-plus-CNV landscape lower bound`
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
