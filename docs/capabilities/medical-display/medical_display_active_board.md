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
  - 证据型模板：`68`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`80`
- 最近一次已吸收完成的 capability cluster：
  - `G / genomic_alteration_landscape_panel`
  - `genomic_alteration_landscape_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 5 / integration / merge-back ready`
- Family cluster：`G`
- Capability cluster：`genomic_alteration_consequence_panel`
- Owner worktree：`/Users/gaofeng/workspace/med-autoscience/.worktrees/medical-display-g-broader-genomic-20260419T092609Z`
- 状态：`merge_back_ready`

### Fresh Owner Result

- `genomic_alteration_consequence_panel` 已在当前 owner round 内完成 schema / source contract / materialization / renderer / layout QC / regression 闭环；
- `G/E` 当前 omics-native lower bound 已正式扩到七基线：
  - `gsva_ssgsea_heatmap`
  - `pathway_enrichment_dotplot_panel`
  - `omics_volcano_panel`
  - `oncoplot_mutation_landscape_panel`
  - `cnv_recurrence_summary_panel`
  - `genomic_alteration_landscape_panel`
  - `genomic_alteration_consequence_panel`
- 当前 owner round 已完成 fresh focused verify、`scripts/verify.sh`、`make test-meta`、`py_compile` 与 `git diff --check`；
- 当前下一步是 clean integration / merge-back lane，把这轮 owner 结果吸收到干净主干基线，再决定后继 capability cluster。

### 本轮收口结果

当前这一轮已经回答：

> 在 `GSVA/ssGSEA` heatmap、pathway enrichment dotplot、omics volcano、oncoplot、CNV summary 与 gene-level genomic landscape 已经成立的前提下，如何把 top journal 常见的 driver-centric transcriptome / proteome consequence follow-on 固化成正文可直接使用的 bounded 模板，并把 shared gene/sample governance、driver-gene subset、effect / significance threshold、consequence panel identity 与 downstream scatter semantics 一起推进到可审计、可回归、可复用的统一 contract。

### 当前 Merge-Back Baton

当前 baton 已明确：

1. 当前 owner round 的 tracked code、tracked docs 与 pack changelog 已同步到 `genomic_alteration_consequence_panel` 真相。
2. 当前需要的唯一外层动作是把这轮结果 merge-back 到干净主干 intake surface。
3. 当前 merge-back 完成后，`G` 家族的 next candidate 回到 `broader genomic composite beyond the current gene-level landscape-plus-consequence lower bound`。
4. `D/E/G` 更高阶 multi-view atlas follow-on 与 `F` 更高阶 explanation scene 继续留在后继 reroute 池。

### 本轮边界

本轮只做下面三块：

1. 固定 `G` 家族当前 owner 模板为 `genomic_alteration_consequence_panel`；
2. 在当前 round 里，显式固定 shared `gene_order`、shared `sample_order`、driver-gene subset、consequence panel order、effect / significance threshold、transcriptome / proteome consequence scatter semantics 与 up-to-three annotation tracks 治理；
3. 把 schema / renderer / QC / regression / tracked docs 一起闭环，并让 `G` 家族从“gene-level genomic landscape lower bound”推进到更完整的 driver-centric landscape-plus-consequence lower bound。

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

1. `genomic_alteration_consequence_panel` 已正式入库为单一 bounded manuscript-facing template；
2. input schema、source contract、materialization、renderer、layout QC 与 regression 已一起闭环；
3. fresh verify 至少覆盖该 `G` lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 当前轮次结束后的候选

当前 merge-back 完成后，secondary 候选按下面顺序继续：

1. `G / broader genomic composite beyond the current gene-level landscape-plus-consequence lower bound`
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
