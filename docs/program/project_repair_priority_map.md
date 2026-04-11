# 项目修补优先级图

## 1. 文档目的

这份文档把项目修补主线收敛成三条正式 tranche，并明确它们的优先级、依赖关系、完成状态与当前剩余工作：

1. `runtime native truth convergence`
2. `workspace knowledge and literature convergence`
3. `controlled cutover -> physical monorepo migration`

目标不是继续按 issue-by-issue 打补丁，而是先把 authority、durable surface 与 cutover gate 冻结出来，再按阶段实施，并且持续把“已完成”和“未完成”写诚实。

## 2. 一句话结论

优先级顺序已经冻结，不再摇摆：

1. 先完成 `runtime native truth convergence`
2. 再完成 `workspace knowledge and literature convergence`
3. 最后进入 `controlled cutover -> physical monorepo migration`

原因很直接：

- `runtime native truth` 直接决定 `MedAutoScience` 是否还能诚实监管、暂停、恢复、停车、接管；
- `workspace knowledge / literature` 决定的是跨 study 复用、选题效率、文献去重与知识沉淀；
- 前者是控制面安全问题，后者是知识面与资产面收敛问题；
- monorepo 不是与前两者并列的第一优先级动作，而是前两条 contract 收紧后的物理吸收动作。

## 3. 当前状态

### 3.1 P0：Runtime Native Truth 已完成

当前已完成事实：

- `med-deepscientist` runtime core 已原生写出 quest-owned native runtime event durable surface
- `GET /api/quests/{quest_id}/session` 已暴露 `runtime_event_ref` 与 `runtime_event`
- `MedAutoScience` 已把 managed runtime 的 `status.runtime_event_ref` 改成消费 session-native ref，而不是再主写 quest-owned truth

这条 tranche 当前要守住的是：

- 不让 controller 再覆盖 `artifacts/reports/runtime_events/latest.json`
- 不让 outer loop 重新退回 `poll + inference + synthetic event`
- 不让 runtime native truth 与 study-owned supervision / escalation / decision truth 再次混叠

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

### 第三优先级：Controlled Monorepo Cutover

这是当前剩余的 active tranche。

只有在下面条件满足后，才进入 physical cutover：

1. runtime event / outer-loop input contract 已稳定消费 runtime-native truth
2. workspace knowledge / literature contract 已稳定，不再由 quest-local surfaces 充当 authority
3. `workspace / study / quest / active_run` 四层身份边界保持清楚
4. cross-repo parity gate 已通过
5. 吸收动作不再需要依赖跨 repo projection glue

## 5. 推荐的阶段顺序

### P0

- 已完成：`med-deepscientist` 原生 runtime truth 与 `MedAutoScience` transport/status/outer-loop 消费切换。

### P1

- 已完成：workspace canonical literature / reference-context / quest materialization-only contract。

### P2

- 进行 `controlled cutover -> physical monorepo migration`
- 关闭 cross-repo parity gate
- 吸收稳定模块边界与 authority contract，而不是把当前双仓临时 glue 直接搬进 monorepo

## 6. 立即执行建议

从当前起，项目修补顺序的执行口径固定为：

1. 守住已经完成的 `P0 runtime native truth`
2. 守住已经完成的 `P1 workspace knowledge / literature canonical contract`
3. 把剩余工作集中到 `P2 controlled cutover -> physical monorepo migration`

对应正式文档：

- `../runtime/runtime_core_convergence_and_controlled_cutover.md`
- `../runtime/runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- `../runtime/workspace_knowledge_and_literature_contract.md`
- `../runtime/workspace_knowledge_and_literature_implementation_plan.md`
