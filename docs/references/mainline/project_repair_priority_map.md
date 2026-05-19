# 项目修补优先级图

Owner: `MedAutoScience`
Purpose: `historical_repair_priority_reference`
State: `support_reference_superseded_by_ideal_state_gap_plan`
Machine boundary: 本文是人读历史修补优先级参考，不是 current execution queue、runtime truth、generic runtime owner contract 或 monorepo cutover plan。当前 truth 以 [当前状态](../../status.md)、[MAS 理想目标态](../positioning/mas_ideal_state.md)、[MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)、runtime contracts 和 machine-readable owner receipts 为准。

## 1. 文档目的

这份文档保留早期项目修补主线的三条 tranche 读法，帮助追溯 runtime truth、workspace knowledge/literature 和 physical absorb 的先后关系：

1. `runtime native truth convergence`
2. `workspace knowledge and literature convergence`
3. `controlled cutover -> physical monorepo migration`

目标不是继续按 issue-by-issue 打补丁，而是先把 authority、durable surface 与 cutover gate 冻结出来，再按阶段实施，并且持续把“已完成”和“未完成”写诚实。

## 2. 当前读法

这份文档不再冻结当前执行优先级。当前 MAS 文档治理和实现顺序已经收敛到：

- MAS north-star 与 owner 边界读 [MAS 理想目标态](../positioning/mas_ideal_state.md)。
- 当前功能/结构差距、测试/证据差距、物理源码形态差距和完善顺序读 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)。
- P0/P1/P2/P3 内容级 program 组合读 [Program Portfolio Consolidation](../../active/program_portfolio_consolidation.md) 和 [MAS 当前开发线路](../../active/current-development-lines.md)。
- runtime owner truth 读 [Runtime boundary](../../runtime/contracts/runtime_boundary.md)、[Domain SLO scheduler projection contract](../../runtime/control/domain_slo_scheduler_projection_contract.md) 和相关 machine-readable contracts。

以下旧 tranche 只能作为历史支撑参考，不能用来重开 MAS-owned generic runtime、Hermes/default scheduler、MDS default backend、monorepo cutover 或 compatibility shim。

## 3. 当前状态

### 3.1 P0：Runtime Native Truth 历史 tranche

当前应改读为：

- OPL provider-backed stage runtime 持有默认 generic runtime owner、attempt、queue、worker residency、retry/dead-letter、provider transport 和 generic lifecycle/index。
- MAS Runtime OS / `mas_runtime_core` 只承担 MAS domain runtime adapter、owner receipt、typed blocker、runtime event refs、guarded apply 和 diagnostic surface；`runtime_backend_is_generic_owner=false`。
- `runtime_binding.yaml`、live task intake、runtime watch/status 与 progress surfaces 可指向 MAS-owned domain runtime refs，但不能被写成 MAS 持有 generic runtime platform。
- 外部 MDS daemon、repo checkout、runtime root 和 WebUI 不再是 MAS 默认运行、诊断或进度查看依赖；旧 MDS runtime event / session 资料只作为 historical fixture 或 explicit legacy diagnostic 被读取。

这条 tranche 当前要守住的是：

- 不让 controller 再覆盖 `artifacts/reports/runtime_events/latest.json`
- 不让 outer loop 重新退回 `poll + inference + synthetic event`
- 不让 historical MDS fixture/provenance 与 study-owned supervision / escalation / decision truth 再次混叠

### 3.2 P1：Workspace Knowledge / Literature 已完成

当前已完成事实：

- workspace canonical literature layer 已进入 `portfolio/research_memory/literature/*`
- study-owned `artifacts/reference_context/latest.json` 已进入主线
- quest hydration 已按 materialization-only 理解，不再把 quest-local literature surface 当 authority root

这条 tranche 当前要守住的是：

- workspace canonical literature 不回退成 quest-local cache
- study reference context 不被 startup ingress 或 quest working set 重新吞掉
- venue / literature promotion 继续沿 workspace-first contract 收敛

## 4. 正式优先级

### 第一优先级：Runtime Native Truth Convergence

这条线已经完成，且仍然是整个项目不能回退的第一优先级基础。它直接决定：

- MAS 能否在 managed runtime 上继续诚实 fail-closed；
- pause / stop / waiting_for_user / parking / stale / degraded 是否还能被稳定看见；
- outer loop 是否能真正只消费正式 runtime 输入，而不是继续靠投影推断；
- 未来 monorepo 吸收的是 runtime truth，还是一套 repo-side observation shell。

完成标志已经满足：

- runtime event plane 由 runtime core 原生输出
- MAS 只消费该 plane 与 study-owned health / decision surfaces
- runtime 状态迁移不再需要 MAS 先观察后代写才算发生

### 第二优先级：Workspace Knowledge And Literature Convergence

这条线也已完成，并且是第二优先级的已完成 tranche。

原因不是它不重要，而是：

- 它主要影响知识复用、跨 study 资产化与文献一致性；
- 它依赖 `workspace / study / quest` 三层边界先保持清楚；
- 它适合在 runtime truth 稳定后，作为 knowledge plane 的对称收敛动作。

完成标志已经满足：

- workspace 拥有 canonical research memory layer；
- workspace 同时拥有 canonical literature registry；
- study 只持有本研究线的 reference context；
- quest 只持有 runtime local materialization，而不是 literature truth。

### 第三优先级：Controlled Monorepo Cutover 历史 tranche

这不是当前 active tranche。当前 MAS 目标是标准 OPL Agent：`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。物理吸收、删除、archive 或 tombstone 只在 no-active-caller、OPL parity、MAS receipt parity、history/provenance 和 focused tests 成立后按 owner surface 逐项执行。

只有在下面条件满足后，才进入 physical cutover：

1. runtime event / outer-loop input contract 已稳定消费 runtime-native truth
2. workspace knowledge / literature contract 已稳定，不再由 quest-local surfaces 充当 authority
3. `workspace / study / quest / active_run` 四层身份边界保持清楚
4. cross-repo parity gate 已通过
5. 吸收动作不再需要依赖跨 repo projection glue

## 5. 历史阶段读法

### P0

- 已完成：`med-deepscientist` 原生 runtime truth 与 `MedAutoScience` transport/status/outer-loop 消费切换。

### P1

- 已完成：workspace canonical literature / reference-context / quest materialization-only contract。

### P2

- 旧读法是 `controlled cutover -> physical monorepo migration`。
- 当前只作为 physical retirement / archive / tombstone 的历史 gate 读取。
- 新的源码形态、功能/结构差距和 evidence gate 回到 MAS 理想目标态差距计划；不得沿本文件重启 monorepo cutover 或兼容 shim。

## 6. 当前处置

本文件保留为 `support_reference`，只用于理解旧修补顺序的来源。后续不得把本文件当作 active plan 更新，也不得继续追加 dated closeout。需要新增当前计划时，应归入：

- `docs/active/mas-ideal-state-gap-plan.md`
- `docs/active/current-development-lines.md`
- `docs/active/program_portfolio_consolidation.md`
- 对应 runtime / policy / contract owner 文档
- `docs/history/**` provenance 目录
