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
  - 证据型模板：`69`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`81`
- 最近一次已吸收完成的 capability cluster：
  - `G / genomic_alteration_multiomic_consequence_panel`
  - `genomic_alteration_multiomic_consequence_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / next-cluster scouting`
- Family cluster：`G`
- Capability cluster：`pathway-integrated genomic composite beyond the current landscape-plus-three-omics lower bound`
- Owner worktree：`not_opened`
- 状态：`ready_for_next_owner_round`

### Fresh Mainline Result

- `genomic_alteration_multiomic_consequence_panel` 已完成 absorb / push / cleanup；
- `G/E` 当前 omics-native lower bound 已正式扩到八基线：
  - `gsva_ssgsea_heatmap`
  - `pathway_enrichment_dotplot_panel`
  - `omics_volcano_panel`
  - `oncoplot_mutation_landscape_panel`
  - `cnv_recurrence_summary_panel`
  - `genomic_alteration_landscape_panel`
  - `genomic_alteration_consequence_panel`
  - `genomic_alteration_multiomic_consequence_panel`
- display 主干当前只剩根 `main` 一个 worktree；
- 下一步是先收口更高阶 `G` 家族 owner brief，再新开唯一 owner worktree 进入实现。

### 当前轮次目标

当前下一轮要回答：

> 在 `GSVA/ssGSEA` heatmap、pathway enrichment dotplot、omics volcano、oncoplot、CNV summary、gene-level genomic landscape、driver-centric consequence follow-on 与固定三层 multiomic consequence follow-on 已经成立的前提下，如何把 pathway-integrated broader genomic composite 固化成正文可直接使用的下一条 bounded 模板，并把更强的 pathway / omics 联动叙事推进到可审计、可回归、可复用的统一 contract。

### 当前 Next Baton

当前 baton 已明确：

1. 当前主干已经吸收 `genomic_alteration_multiomic_consequence_panel`，并完成 push 与 cleanup。
2. 当前下一步是基于最新 `main` fresh intake 高价值 exemplar，收口 pathway-integrated broader genomic composite 的 owner brief。
3. 只有 owner brief 收口后，才新开唯一 owner worktree 进入实现。
4. `D/E/G` 更高阶 multi-view atlas follow-on 与 `F` 更高阶 explanation scene 继续留在后继 reroute 池。

### 下一轮边界

下一轮只做下面三块：

1. 固定 `G` 家族下一轮 owner 候选为 `pathway-integrated genomic composite beyond the current landscape-plus-three-omics lower bound`；
2. 在 owner brief 阶段显式固定 exemplar、paper question、最小 panel structure、最小数据前提、继承自现有八基线的 contract surface；
3. 进入实现后，再把 schema / renderer / QC / regression / tracked docs 一起闭环。

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

只有同时满足下面条件，下一轮 `G` owner round 才算完成：

1. 新的 broader genomic composite 已正式入库为单一 bounded manuscript-facing template；
2. input schema、source contract、materialization、renderer、layout QC 与 regression 已一起闭环；
3. fresh verify 至少覆盖该 `G` lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 当前轮次结束后的候选

当前 pathway-integrated broader genomic composite 收口后，secondary 候选按下面顺序继续：

1. `G / pathway-integrated genomic composite beyond the current landscape-plus-three-omics lower bound`
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
