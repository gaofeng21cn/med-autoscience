# 项目修补优先级图

## 1. 文档目的

这份文档把当前项目修补主线收敛成两条正式 tranche，并明确它们的优先级、依赖关系与停车条件：

1. `runtime native truth convergence`
2. `workspace knowledge and literature convergence`

目标不是继续按 issue-by-issue 打补丁，而是先把 authority、durable surface 与 cutover gate 冻结出来，再按阶段实施。

## 2. 一句话结论

两个方向都要做，但优先级不能平均分配。

当前推荐顺序是：

1. 先完成 `runtime native truth convergence`
2. 再完成 `workspace knowledge and literature convergence`
3. 最后进入 `controlled monorepo cutover`

原因很直接：

- `runtime native truth` 直接决定 `MedAutoScience` 是否还能诚实监管、暂停、恢复、停车、接管；
- `workspace knowledge / literature` 决定的是跨 study 复用、选题效率、文献去重与知识沉淀；
- 前者是控制面安全问题，后者是知识面与资产面收敛问题；
- monorepo 不是与两者并列的第一优先级动作，而是这两条 contract 收紧后的物理吸收动作。

## 3. 当前两个缺口分别是什么

### 3.1 Runtime 主线缺口

虽然当前仓内已经有：

- `runtime_event`
- `runtime_event_ref`
- `outer_loop_input`

但这条事件面仍然主要由 repo-side controller 物化，而不是 `med-deepscientist` runtime core 原生输出。

这会留下三个结构性风险：

1. MAS 仍需要依赖 controller tick 才能观察到部分 runtime 状态迁移。
2. 事件 plane 的 owner 仍偏向 `MedAutoScience`，而不是 quest-native runtime。
3. physical monorepo 现在做，只会把 repo-side projection 带进 monorepo，而不是把 runtime truth 本身带进去。

### 3.2 Workspace 知识/文献主线缺口

虽然当前仓内已经有：

- `portfolio/research_memory/*`
- `topic_landscape.md`
- `dataset_question_map.md`
- `venue_intelligence.md`

但文献 materialization 仍主要沿着：

- `startup_contract.paper_urls`
- `reference_papers`
- `quest_hydration`
- `quest_root/literature/*`

这条 quest-local 路径落盘。

这会留下三个结构性风险：

1. 同一 disease workspace 的文献资产会在多个 quest 中重复物化和重复清洗。
2. workspace memory 已经上提，但 workspace canonical literature registry 还没有对称上提。
3. study 与 quest 的引用集边界不够清楚，导致 startup anchor、study framing、runtime local working set 混在一起。

## 4. 正式优先级

### 第一优先级：Runtime Native Truth Convergence

先做这条线，因为它直接决定：

- MAS 能否在 managed runtime 上继续诚实 fail-closed；
- pause / stop / waiting_for_user / parking / stale / degraded 是否还能被稳定看见；
- outer loop 是否能真正只消费正式 runtime 输入，而不是继续靠投影推断；
- 未来 monorepo 吸收的是 runtime truth，还是一套 repo-side observation shell。

本 tranche 的完成标志不是“又多了几个 controller 补丁”，而是：

- runtime event plane 由 runtime core 原生输出；
- MAS 只消费该 plane 与 study-owned health / decision surfaces；
- runtime 状态迁移不再需要 MAS 先观察后代写才算发生。

### 第二优先级：Workspace Knowledge And Literature Convergence

这条线排第二，但要紧跟着做。

原因不是它不重要，而是：

- 它主要影响知识复用、跨 study 资产化与文献一致性；
- 它依赖 `workspace / study / quest` 三层边界先保持清楚；
- 它适合在 runtime truth 稳定后，作为 knowledge plane 的对称收敛动作。

本 tranche 的完成标志不是“多了一些 memory 文档”，而是：

- workspace 拥有 canonical research memory layer；
- workspace 同时拥有 canonical literature registry；
- study 只持有本研究线的 reference context；
- quest 只持有 runtime local materialization，而不是 literature truth。

### 第三优先级：Controlled Monorepo Cutover

monorepo 仍要做，但它必须排在前两条 tranche 之后。

只有在下面条件满足后，才进入 physical cutover：

1. runtime event / outer-loop input contract 已变成 runtime-native truth；
2. workspace knowledge / literature contract 已经稳定，不再由 quest-local surfaces 充当 authority；
3. `workspace / study / quest / active_run` 四层身份边界保持清楚；
4. 吸收动作不再需要依赖跨 repo projection glue。

## 5. 推荐的阶段顺序

### P0

- 冻结并实现 `runtime native truth` 的正式 contract 与 cutover gate。
- 冻结并实现 `workspace knowledge / literature` 的正式 contract 与 authority boundary。

### P1

- 让 runtime repo 原生输出事件面，并让 MAS 改为纯消费者。
- 让 workspace 拥有 canonical literature registry，并让 study / quest 改为受控 materialization。

### P2

- 在双侧 contract 都稳定后，做 `controlled monorepo cutover`。
- 吸收的是稳定模块边界与 authority contract，不是把当前双仓临时 glue 直接搬进 monorepo。

## 6. 立即执行建议

从今天起，项目修补顺序固定为：

1. 先继续压实 runtime native truth 与 cutover gate；
2. 随后压实 workspace knowledge / literature canonical contract；
3. 两条线都通过后，再进入 monorepo physical migration。

对应正式文档：

- `docs/runtime_core_convergence_and_controlled_cutover.md`
- `docs/runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- `docs/workspace_knowledge_and_literature_contract.md`
- `docs/workspace_knowledge_and_literature_implementation_plan.md`
