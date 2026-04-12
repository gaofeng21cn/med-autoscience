# Research Foundry Medical Phase Ladder

这份文档把 `Med Auto Science` 从“当前主线已成立”走到“更完整理想形态”的 5 个阶段固定下来。

它解决三个问题：

1. 理想形态到底是什么
2. 现在处在第几阶段
3. 后面该按什么顺序继续做，而不是把高优先级与后置长线混在一起

配套命令面：

- 总览：`uv run python -m med_autoscience.cli mainline-status`
- 分阶段：`uv run python -m med_autoscience.cli mainline-phase --phase <current|next|phase_id>`

## 理想形态

按 `OPL -> Research Foundry -> Med Auto Science` 这条定位，最终目标不是单一仓库里的一套脚本，而是一条清楚分层、长期自治、可监管的产品链：

- `OPL`：family-level federation / gateway language
- `Research Foundry`：通用 `Research Ops` framework
- `Med Auto Science`：medical domain gateway + `Domain Harness OS`
- upstream `Hermes-Agent`：长期在线 outer runtime substrate owner
- `MedDeepScientist`：先作为 controlled research backend，之后再逐步解构

面向用户时，理想形态必须至少成立下面这件事：

- 用户能稳定地启动 MAS、下达任务、持续看进度、看到卡住/掉线/质量退化告警，并在需要时做人类决策

## 五阶段梯子

### Phase 1. Mainline Established

目标：

- 先让 `MedAutoScience -> Hermes-Agent target substrate -> controlled MedDeepScientist backend` 这条主线诚实成立
- 拿到 external runtime truth、repo-side real adapter、真实 study recovery/progress proof
- 把当前 blocker 收口成真实外部 gate / study gate / human gate

完成标志：

- F1-F3 证据链成立
- F4 blocker closeout 不再主要是 repo-side seam 问题
- `mainline-status`、`workspace-cockpit`、`study-progress` 已能说清当前真相

当前状态：

- 当前就在这一阶段尾声
- 重点是继续收口 active study blocker，并把用户入口继续收成稳定产品回路

### Phase 2. User Product Loop

目标：

- 把“怎么启动、怎么下任务、怎么持续看进度”做成稳定用户回路
- 把 stuck-state、掉线、恢复建议、人工决策点、质量退化告警统一暴露给用户

完成标志：

- repo-tracked shell 已足够像真实 user inbox，而不是分散命令集合
- 用户不用自己手拼 controller surface，就能完成 start / submit / watch / supervise
- 前台能持续看到 progress freshness、attention queue 与恢复入口

这一阶段的本质：

- 不是提前宣称 standalone product frontend 已落地
- 而是把当前 agent-operated 路径收成一个真实可用的轻量 product loop

### Phase 3. Multi-Workspace / Host Clearance

目标：

- 把当前 proof 从单机、少量 workspace 扩到更广的真实环境
- 证明 service、watch、recovery、quality guard、human gate 在更多宿主和 workspace 上都成立

完成标志：

- external runtime clearance 不再只依赖当前开发宿主
- 多个 workspace / study 都能稳定通过 service、recovery、progress projection
- host/env compatibility 不再反复成为主阻塞

### Phase 4. Backend Deconstruction

目标：

- 在 outer runtime 与用户回路稳定之后，再逐步解构 `MedDeepScientist`
- 把确实属于通用 runtime substrate 的能力继续迁出

完成标志：

- 迁出的能力有明确 owner、contract、tests、proof surface
- backend 剩余职责更接近 controlled research executor，而不是 hidden runtime authority
- executor route 的替换按 contract 逐步发生，而不是一次性重写

注意：

- 这一步不要求立刻把 backend 里的 `Codex + skills` 全部替掉
- 只要 executor contract 仍成立，底层执行生态可以继续受控复用

### Phase 5. Federation And Platform Maturation

目标：

- 最后再考虑更大平台化事项，例如 federation-facing direct entry、runtime core ingest、monorepo

完成标志：

- 前四阶段已经稳定
- 更大物理结构调整不再会制造 truth drift
- `OPL` 家族级入口与 MAS domain 入口能自然衔接

注意：

- 这是严格后置长线
- 不属于当前默认实施入口

## 顺序为什么不能乱

如果跳过顺序，最常见的坏结果是：

- Phase 1 还没收干净就去做 monorepo
- Phase 2 还没成型就对外过度宣称成熟产品前台
- Phase 3 还没跑开就误以为 external gate 已经普遍清除
- Phase 4 还没准备好就强行替换 backend executor

所以固定顺序必须是：

1. 先把主线成立
2. 再把用户回路做实
3. 再把多环境 clearance 做实
4. 再做 backend 解构
5. 最后才做更大平台化

## 当前正式判断

当前 repo-tracked truth 应写成：

- 现在处在 `Phase 1` 尾声，而不是已经跨到成熟产品态
- 当前最重要的下一阶段是 `Phase 2`
- `Phase 3-5` 都已经知道要做什么，但仍是后续阶段，不应抢跑

因此当前最该继续推进的是：

- 继续收口 `F4 blocker closeout`
- 继续强化用户可见的 product-entry loop
- 继续把真实 progress / recovery / escalation / human gate 暴露清楚

而不是：

- 提前做 physical migration
- 提前做 cross-repo rewrite
- 提前写成 “Hermes 已完全替代 backend executor”
