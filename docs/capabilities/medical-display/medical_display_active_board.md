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

- Phase：`Phase 4 / owner-brief locked / owner implementation ready`
- Family cluster：`D/E/G`
- Capability cluster：`atlas-spatial-trajectory density / coverage contract follow-on beyond the current storyboard lower bound`
- Owner worktree：`未开启（本轮 reroute 已在隔离 worktree 内完成并可 cleanup；下一 heartbeat 按当前 capability cluster 新开唯一 owner implementation worktree）`
- 状态：`implementation_ready`

### 本轮核心问题

当前这一轮要回答的是：

> 在 `single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel` 与 `atlas_spatial_trajectory_storyboard_panel` 已经入库的前提下，如何把 atlas / spatial / trajectory family 里仍然分散的 density / coverage semantics 提升为一个固定四块式、paper-facing、可审计的 composite contract，使论文能够稳定回答“state 在 atlas / tissue / progression contexts 里分别集中在哪里、覆盖了多少范围、这些 coverage shift 是否足以支撑图中叙事”，而不是重新滑回自由 atlas dashboard / storyboard 拼图。

### Fresh Route 收敛

当前 reroute 已明确：

1. 保留 `atlas-spatial-trajectory density / coverage contract follow-on` 作为当前唯一 owner implementation 候选：
   - 原因：它直接对应 roadmap 中 `D` 的 density / coverage gap、`E` 的复合矩阵 gap，以及 `G` 的 larger multi-view omics composite gap，同时仍能复用现有 atlas / spatial / trajectory lower bound 的受控词表与 panel 结构。
2. 不保留 `PHATE / richer manifold overlay only` 作为当前 round：
   - 原因：单独扩到替代 projection / manifold overlay 会把当前 round 收缩成偏 `D` 的 geometry 变体，更容易滑回 projection gallery，而不是 `D/E/G` 联动的 paper-facing composite contract。
3. 不保留 `legend / annotation / readability-only hardening` 作为当前 round：
   - 原因：这仍然是需要继续做的 hardening 方向，但它更像现有模板的上限加固，还不能替代下一条真正的 multi-view capability cluster。
4. 不保留 `omics-only matrix expansion` 作为当前 round：
   - 原因：如果先做更宽的 matrix / heatmap 扩容，容易脱离 atlas / spatial / trajectory 的 joint paper question，把当前 round 重新拉回孤立 matrix lane。

### 本轮边界

本轮只做下面三块：

1. 固定 `D/E/G` 家族当前 owner implementation 候选为 `atlas-spatial-trajectory density / coverage contract follow-on`，不再在 PHATE-only、readability-only、omics-only matrix expansion 与更大 atlas / spatial / trajectory gallery 之间来回摆动
2. owner implementation 只允许做一个固定四块式 composite：
   - `atlas density / manifold occupancy panel`
   - `spatial coverage topography panel`
   - `trajectory progression coverage panel`
   - `state-by-context support heatmap`
3. 新模板必须复用现有 atlas / spatial / trajectory lower bound 里的 `state_label`、`region_label`、`branch_label`、`pseudotime bin` 等受控语义，只把 density / coverage contract 提升为正式 surface，不顺手引入 histology/raw-image lane 或任意 panel 增长

本轮明确不做：

- 重开刚刚 absorb 的 `F / feature_response_support_domain_panel`
- 把当前 round 降解成 `PHATE` 替代投影、projection gallery 或 organ-specific atlas gallery
- 把当前 round 退化成 annotation-only / readability-only patch
- 顺手把 `H` 壳层 follow-on、`C/H` heterogeneity follow-on、`F` 的 multi-group grouped-local / decision-path 扩容，或更大的 omics-only matrix lane 并入当前 round

## 预期写集

下一轮 owner implementation 只应触碰下面这组最小写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/display_source_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/display_layout_qc.py`
- `tests/test_display_registry.py`
- `tests/test_display_schema_contract.py`
- `tests/test_display_surface_materialization.py`
- `tests/test_display_layout_qc.py`
- `tests/test_display_deg_golden_regression.py`
- 仅在 template inventory 真相变化后触碰 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`

## 最低退出条件

只有同时满足下面条件，当前 `D/E/G` owner implementation round 才算完成：

1. `atlas-spatial-trajectory density / coverage contract follow-on` 已正式入库为单一 bounded template，而不是仍停留在 storyboard 外的 paper-local 拼图。
2. input schema、source contract、materialization validator、renderer、layout QC 与 `D/E/G` golden regression 已一起闭环。
3. fresh verify 至少覆盖 targeted `D/E/G` lane 与仓库默认最小验证。
4. 本轮 worktree 已 absorb / push / cleanup，且未与其他 display owner write set 发生冲突。

## 最低验证要求

当前 owner implementation 至少要留下：

- 清晰的 paper question 与 exemplar 理由：
  - 为什么论文需要同时表达 atlas / spatial / trajectory contexts 里的 density / coverage shift，而现有 storyboard lower bound 还不够。
- 固定四块式 composite 的最小实现边界；
- targeted tests：
  - `tests/test_display_registry.py`
  - `tests/test_display_schema_contract.py`
  - `tests/test_display_surface_materialization.py`
  - `tests/test_display_layout_qc.py`
  - `tests/test_display_deg_golden_regression.py`
- 至少一条新的 `D/E/G` golden regression slice，锁定 density / coverage semantics；
- absorb 前的 fresh `scripts/verify.sh` 通过证据。

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
