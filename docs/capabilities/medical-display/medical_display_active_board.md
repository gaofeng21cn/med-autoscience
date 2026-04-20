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
  - 证据型模板：`75`
  - 插图壳层：`7`
  - 表格壳层：`5`
  - 总模板数：`87`
- 最近一次已吸收完成的 capability cluster：
  - `G / genomic_program_governance_summary_panel`
- 当前执行模型：
  - 任一时刻只允许一个 active owner round；
  - 每一轮 owner round 使用一个独立 display worktree；
  - 仓库根 `main` 只负责吸收、验证、清理；
  - 项目本地 `.omx/`、`.codex/` 一律不视为权威执行面。

## 当前 Active Round

- Phase：`Phase 5 / owner closeout`
- Family cluster：`F / model explanation`
- Capability cluster：`shap_multigroup_decision_path_support_domain_panel`
- Owner worktree：`.worktrees/codex/medical-display-f-explanation-scene-20260420`
- 状态：`verified_merge_back_ready`

### Fresh Owner Round Result

- 当前 owner round 已把 `shap_multigroup_decision_path_support_domain_panel` 收口为 audited inventory；
- strict audited inventory 已更新到：
  - `Model Explanation`：`18`
  - evidence figures：`75`
  - total templates：`87`
- 当前 fresh verify 已完成：
  - `uv run pytest -q tests/test_display_registry.py tests/test_display_schema_contract.py` → `93 passed`
  - `uv run pytest -q tests/test_display_layout_qc.py tests/test_display_surface_materialization.py tests/test_display_f_golden_regression.py` → `332 passed`
- 下一步是把当前 owner round 吸收到 `main`，然后按 reroute 规则固定下一个 capability cluster。

### 当前轮次目标

当前这轮已经回答清楚：

> `F` 家族是否需要一张可直接进入正文的多组 explanation scene，把三组 shared decision path 与 matched support-domain follow-on 固化为同一张 audited 复合图。

### 当前 Next Baton

当前 baton 已明确：

1. 最新的 `G / genomic_program_governance_summary_panel` owner round 已经 absorb 完成。
2. 当前 `F / shap_multigroup_decision_path_support_domain_panel` owner round 已完成实现与 fresh verify。
3. 当前 strict audited inventory 已推进到 `75 / 7 / 5 / 87`。
4. 下一步是 merge-back，然后把 `F`、`D/E/G` 与 `C/H` 的 higher-order follow-on 重新排序。

### 下一轮边界

当前 closeout 只做下面三块：

1. 先把当前 `F` owner round 吸收到 `main`；
2. 再 fresh 读取当前 audit guide / template catalog / arsenal / active board；
3. 最后比较 `F`、`D/E/G` 与 `C/H` 的真实论文 demand 哪一条最值得开启下一轮。

## 预期写集

当前 merge-back 预计先触碰下面这组写集：

- `docs/capabilities/medical-display/medical_display_active_board.md`
- `docs/capabilities/medical-display/medical_display_template_backlog.md`

只有 absorb 完成并 reroute 固定后，才允许再触碰：

- 对应新 cluster 的 registry / schema / source contract / materialization / renderer / QC / regression 文件
- 以及仅在 template inventory 真相变化后需要同步的 `medical_display_arsenal.md`、`medical_display_audit_guide.md`、`medical_display_template_catalog.md`、`medical_display_arsenal_history.md`、`medical_display_family_roadmap.md`

## 最低退出条件

只有同时满足下面条件，当前 owner round 才允许关闭并让下一轮打开：

1. 当前 owner round 的 absorb / cleanup 必须完成；
2. 新候选必须有清晰的论文问题、最小 panel 结构与最小数据前提；
3. 新候选必须明确继承当前 lower bound，而不是退回 paper-local 修图；
4. reroute 必须明确为什么当前应该优先 `F`、`D/E/G` 或 `C/H`。

## 当前轮次结束后的候选

当前本轮完成后的 reroute 候选按下面顺序继续：

1. `F / higher-order explanation scene only if new real-paper demand proves the current grouped-local + multigroup decision-scene lower bound insufficient`
2. `D/E/G / richer higher-order multi-view atlas follow-on only if new real-paper demand proves the current context-support plus PHATE-inclusive lower bound insufficient`
3. `C/H / calibration appendix or higher-order robustness synthesis only if new real-paper demand proves the current compact-estimate + coefficient-path + broader-heterogeneity lower bound insufficient`

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
