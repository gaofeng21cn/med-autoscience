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
  - 证据型模板：`73`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`85`
- 当前正在收口的 capability cluster：
  - `A / clinical_impact_curve_binary`
  - `C / multivariable_forest`
  - `D / phate_scatter_grouped`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 4 / concrete backlog sweep`
- Family cluster：`A/C/D concrete absorb`
- Capability cluster：`clinical_impact_curve_binary + multivariable_forest + phate_scatter_grouped`
- Owner worktree：`medical-display-concrete-backlog-sweep-20260419T231949Z`
- 状态：`merge_back_ready`

### Fresh Worktree Result

- 当前 owner worktree 已把 `clinical_impact_curve_binary`、`multivariable_forest` 与 `phate_scatter_grouped` 吸收到 tracked docs 真相；
- strict audited inventory 已更新到：
  - `Clinical Utility`：`5`
  - `Effect Estimate`：`6`
  - `Data Geometry`：`13`
  - evidence figures：`73`
  - total templates：`85`
- `phate_scatter_grouped` 已从 concrete backlog 候选转为本轮已吸收成果；
- 当前 fresh verify 已完成：
  - `uv run pytest -q tests/test_display_registry.py tests/test_display_schema_contract.py tests/test_display_surface_materialization.py`
  - `scripts/verify.sh`
  - `make test-meta`
- 下一步是执行 absorb-back、清理 owner worktree，并回到下一轮 reroute。

### 当前轮次目标

当前这一轮要回答：

> 在现有 registry 已 materialize `clinical_impact_curve_binary`、`multivariable_forest` 与 `phate_scatter_grouped` 的前提下，如何把 `A/C/D` 三条 concrete backlog 吸收到同一套 audited inventory、docs truth 与 pack changelog，并在不扩 scope 的条件下完成 absorb-back 前收口。

### 当前 Next Baton

当前 baton 已明确：

1. `clinical_impact_curve_binary` 已进入 `Clinical Utility` 审计真相。
2. `multivariable_forest` 已进入 `Effect Estimate` 审计真相。
3. `phate_scatter_grouped` 已进入 `Data Geometry` 审计真相，并作为本轮 concrete backlog sweep 的显式吸收成果。
4. 下一棒是完成主 lane verify、absorb、cleanup，然后再回到 `G` / `D/E/G` / `F` 的 reroute 候选池。

### 下一轮边界

本轮只做下面三块：

1. 先把 `clinical_impact_curve_binary`、`multivariable_forest`、`phate_scatter_grouped` 的 contract / catalog / docs truth 收齐；
2. 再完成对应代码、测试与 verify 收口；
3. absorb-back 完成后，再恢复下一轮 reroute。

## 预期写集

当前 owner implementation 预计触碰下面这组最小写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/display_source_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/display_layout_qc.py`
- 对应 `A/C/D` renderer 文件
- 对应 `A/C/D` / cross-paper golden regression tests
- `tests/test_display_layout_qc.py`
- 仅在 template inventory 真相变化后触碰 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`、`medical_display_arsenal_history.md`、`medical_display_family_roadmap.md`、`medical_display_template_backlog.md`

## 最低退出条件

只有同时满足下面条件，本轮 `A/C/D` owner round 才算完成：

1. 三个模板的 registry、schema/materialization、renderer、layout QC 与 regression 仍需一起闭环；
2. docs / changelog / audited inventory 口径全部统一到 `73 / 7 / 5 / 85`；
3. fresh verify 至少覆盖对应 lane、`scripts/verify.sh` 与 `make test-meta`；
4. 本轮 worktree 仍需 absorb / cleanup，且不与其他 owner write set 冲突。

## 当前轮次结束后的候选

当前本轮完成后的 reroute 候选按下面顺序继续：

1. `G / higher-order genomic-governance synthesis only if new real-paper demand proves the current pathway-integrated lower bound insufficient`
2. `D/E/G / richer higher-order multi-view atlas follow-on only if new real-paper demand proves the current context-support plus PHATE-inclusive lower bound insufficient`
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
