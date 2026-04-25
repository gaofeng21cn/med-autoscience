# MedDeepScientist Continuous Learning Plan

这份文档定义 `MAS` 针对 `MedDeepScientist` / `DeepScientist` 方法论的当前吸收计划、后续学习重点和长期维护方式。

它处理的是 program 级问题：

1. 当前最值得吸收什么
2. 为什么这些主题值得排在前面
3. 这些主题分别落到 `MAS` 的哪个 owner 面
4. 即使未来 `MDS` 进一步被吸收，这条学习主线还要持续关注什么

## 0. 长期政策入口

持续学习上游 `DeepScientist` 的长期规则固定在 [DeepScientist Continuous Learning Policy](./deepscientist_continuous_learning_policy.md)。本计划负责当前阶段排序；政策文档负责说明即使 `MDS` 被 `MAS` 完全吸收后，学习主线如何继续。

维护者触发“学习一下 `DeepScientist` 的最新更新”这类周期性学习任务时，执行入口固定为 [DeepScientist Latest-Update Learning Protocol](./deepscientist_latest_update_learning_protocol.md)。它把这句话解释为 fresh upstream audit、decision matrix、并行 worktree 落地、验证、吸收回 `main` 和清理的完整流程。

## 1. 当前判断

当前阶段最值得持续学习的对象，是 `DeepScientist` 体系里已经证明有效的研究行为组织方式，而不是 repo 名称、交互外观或局部实现细节。

`MAS` 当前需要优先吸收四类 lesson：

1. 研究合同如何前置冻结
2. 研究全过程如何用 ledger 和 durable surface 持续解释
3. 长时间自治如何把 interrupt / resume / replan / decision record 组织成正式治理链
4. 持续学习本身如何受 oracle、intake、parity proof 约束

## 2. 为什么这四类主题排在最前

### 2.1 它们直接决定 MAS 的主线成色

`MAS` 当前的核心目标已经从“接通一个研究 backend”升级到“作为医学研究主线 owner，持续把研究收口到高质量论文与长期自治”。这要求主线先稳住研究合同、研究账本、外环治理和可审计决策。

### 2.2 它们最适合做 repo-tracked truth

这些主题都能被翻译成明确的文档、contract、测试和 durable surface。对 `MAS` 来说，这类内容一旦吸收，就能长期降低 owner 漂移与语义漂移。

### 2.3 它们能让后续物理吸收更轻

先把方法论变成 `MAS` 自己的 owner truth，后续再处理 runtime core、adapter、parity harness、controlled cutover，会有更稳定的验收面。

## 3. 当前吸收计划

### Phase A：先把 lesson 收成 repo-tracked owner truth

目标：

- 把“持续学习 `DeepScientist` 方法论”收成 `MAS` program 文档主线。
- 把 lesson 映射到 `controller_charter`、`runtime`、`eval_hygiene` 三块 owner。
- 把 `MDS` 的 oracle / intake / parity 角色写成长期可持续解释面。

当前入口：

- [MAS Single-Project Quality And Autonomy Mainline](./mas_single_project_quality_and_autonomy_mainline.md)
- [MedDeepScientist Deconstruction Map](./med_deepscientist_deconstruction_map.md)
- [MedDeepScientist Method Learning Disciplines](./med_deepscientist_method_learning_disciplines.md)

### Phase B：优先吸收论文质量主线的方法论

重点主题：

1. `study charter` 作为质量总合同
2. `paper evidence ledger` 作为 claim-evidence 主账本
3. `review ledger` 作为 novelty、clinical relevance、reviewer concern、submission risk 主账本
4. `bounded_analysis` 的自动推进、自动收口和自动回写

这些主题排在前面，是因为它们直接决定 `MAS` 能否把“高质量医学论文”解释成一条有合同、有执行、有审阅的主线。

### Phase C：优先吸收长时间自治主线的方法论

重点主题：

1. 外环 controller 如何基于 durable truth 做继续、暂停、恢复、升级、收口裁决
2. `runtime_watch -> outer-loop wakeup -> controller decision` 如何成为统一治理链
3. study 级进度、阻塞、恢复点、人工接手点如何稳定投影到前台
4. 长时间运行中的 memory、checkpoint、artifact、decision 如何保持可追溯

这些主题排在前面，是因为长期自治的价值取决于治理质量，而治理质量取决于可见性、恢复语义和 decision record。

### Phase D：保留 MDS 作为学习与对照基础设施

当前阶段继续保留 `MDS` 的三类角色：

1. behavior oracle
2. upstream intake buffer
3. parity / legacy companion

这一步的重点是让 `MAS` 的学习主线始终有对照、有缓冲、有兼容面。

## 4. 后续即使 MDS 被进一步吸收，也要持续学习的方向

## 4.1 研究方向锁定后的自主裁决能力

`MAS` 后续要持续学习的重点，是如何在方向锁定后，稳定做出高质量研究裁决：

- 当前 claim 是否已经具备足够证据
- 哪些补充分析值得推进
- 哪些 reviewer concern 已经被覆盖
- 何时继续写作
- 何时准备投稿包

这类能力属于 `MAS` 自己的长期壁垒，和 `MDS` 是否物理存在没有直接关系。

## 4.2 study 级长期记忆与恢复治理

未来即使 `MDS` 被进一步吸收，`MAS` 仍要持续学习如何把长期研究过程做成稳定的 study memory：

- 研究合同记忆
- 决策记忆
- 证据记忆
- 审阅记忆
- 恢复点记忆

这些内容构成长期自治的核心基础设施。

## 4.3 真实研究失败与回归的 lessons pipeline

后续学习不应只来自上游源码，还应持续来自：

1. 真实 study 失败案例
2. runtime 掉线、恢复失败、decision drift 这类运维事件
3. reviewer concern 与投稿返工
4. parity replay 与旧 quest 兼容问题

这类 lesson 会持续推动 `MAS` 的 contract、docs、tests 和 operator surface 变得更强。

## 4.4 上游方法论 intake

即使未来 `MDS` 被进一步吸收，上游 `DeepScientist` 线仍可能继续产生值得借鉴的方法论。届时依然应该保持：

- 先审计价值，再决定是否 intake
- 先映射 owner，再考虑是否吸收实现
- 先补 proof surface，再扩大主线表述

## 5. 持续学习的固定输入源

这条学习 program 的固定输入源应保持为四类：

1. 上游 `DeepScientist` / `MDS` 的高价值方法论演进
2. `MAS` 真实 study 的成功和失败证据
3. `MAS` 真实 runtime / controller / ledger 运维事件
4. 论文写作、审稿、投稿阶段暴露出来的系统性缺口

只有这四类输入长期进入同一条 program，`MAS` 才能把学习动作做成稳定的主线能力。

## 6. 持续学习的固定输出面

每次有效 lesson 都应优先沉到下面这些输出面之一：

- `docs/program/`：方法论、阶段计划、maintainer 入口
- `docs/runtime/`：控制语义、durable surface、治理 contract
- `docs/status.md`：当前维护重点与阅读入口
- `tests/` 与 `make test-meta`：守住 contract 的 fail-closed proof
- 真实 study evidence：证明 lesson 真正改善了质量或自治

## 7. 当前维护建议

接下来应按下面顺序持续推进这条学习主线：

1. 持续把 lesson 写成 `MAS` 自己的 owner truth。
2. 把论文质量和长时间自治两条主线分别压成可验证 contract。
3. 保持 `MDS` 作为 behavior oracle 与 intake buffer，直到关键能力完成等价 proof。
4. 让真实 study、真实运维事件、真实投稿反馈持续回流到这条 learning program。

这条 program 的目标是让 `MAS` 长期拥有独立、可验证、可持续进化的研究方法论主线。
