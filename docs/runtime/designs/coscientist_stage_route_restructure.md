# Co-Scientist Stage / Route 重构设计与执行规格

Owner: `MedAutoScience`
Purpose: `stage_route_runtime_design_and_execution_specification`
State: `active_runtime_design`
Machine boundary: 本文是 runtime-facing Stage / Route 重构设计和下一轮 `/goal` 的执行规格。它不声明任何能力已经落地，不替代 `docs/active/mas-ideal-state-gap-plan.md` 的 single Active Truth owner，不作为机器真相。实际完成必须落到 `agent/` semantic pack、`contracts/`、源码、测试、runtime/controller durable surfaces、owner receipts、typed blockers、真实 workspace artifact 或 repo-native verification。
Date: `2026-06-04`

## 读法

本文先把 Co-Scientist 论文启发转译成 MAS-native Stage / Route 重构目标，再把目标拆成可并行落地的工程线。完成本文本身只表示“执行规格已冻结”；下一步必须把本文 `执行目标` 和 `落地线` 作为 `/goal` 的 source of truth，逐项推进到 contract、code、test、runtime projection 和文档入口。

本文与现有 active owner 的关系：

- [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 继续持有 single Active Truth、当前差距、证据尾项和禁止误写口径。
- [MAS Stage Surface Standardization Program](../../active/stage_surface_standardization_program.md) 继续持有 stage surface 形态和 machine-boundary guard。
- 本文只持有这次“一步到位重构”的执行规格、并行工作线、完成门和吸收策略。
- 完成本文后，若下一轮实际执行改变 contract/source/runtime 语义，必须同步回 gap plan、stage surface program、runtime contracts、source/docs/tests 中的对应 owner。

## 外部启发的 MAS-native 结论

Co-Scientist 的可学习点不是复制外部 runtime，也不是让 Elo、ranking、proximity 决定科学真相。可吸收的核心是：

1. 科研任务由专职 agent 角色持续协作，而不是单个大 prompt 一次性产出。
2. 研究 goal 先被解析成可执行 plan configuration，评价标准、约束和偏好进入每轮生成、评审、排序与演化。
3. Generation、Reflection、Ranking、Proximity、Evolution、Meta-review 形成长期反馈循环。
4. context memory 让后续轮次吸收失败路径、共同 reviewer 批评、候选聚类和专家反馈。
5. tool use 是 stage-specific 的：文献检索、私有资料索引、开放数据库、专业 AI 模型和实验/分析工具必须受目标约束。
6. human/expert-in-the-loop 是质量与方向边界，不是 UI 附属功能。

MAS 的目标转译为：

```text
Stage-native scientific work system
  -> Stage 是真实科研工作包
  -> Route 是资源与 owner 编排策略
  -> Portfolio 是跨 Stage 的候选 / 证据 / 失败路径记忆
  -> Quality gate 是独立 reviewer / auditor authority
  -> OPL 只持有 runtime substrate 和 refs-only projection
```

## Progress-first Co-Scientist affordance 落地口径

2026-06-10 起，Co-Scientist 剩余可学习点在 MAS 中只落为 `current_owner_native_jit_affordance`：affordance 默认可供 current owner 使用，但 ordinary path 默认不运行额外探索、tournament、meta-review、prefetch 或 memory scan；只有当前 owner action、owner route、route-back、typed blocker、reviewer gate 或 stop-loss 判断显式声明，或 current delta / gate 形态本身隐含需要 ref family、repair context、briefing 或 arbitration 时，才即时调用对应 affordance。它服务当前 owner 的 route selection、独立 reviewer/auditor briefing 和 publication-route memory 复用，不能改变 stage admission、route authority、quality closure、publication readiness、artifact authority 或 owner receipt / typed blocker 边界。

这层增益只回答三个问题：

- 帮助 route 更快选出下一次真实科研 delta。
- 帮助 reviewer / auditor 更快发现 claim、evidence、artifact 或 source 缺口。
- 帮助 memory 复用失败路径、negative result、rejected candidate 和 reviewer concern，减少同义空转。

六项机制固定为 current-owner-native JIT affordance 形态：

| 机制 | Progress-first 用法 | 禁止升级 |
| --- | --- | --- |
| `next-delta tournament` | 只在当前 owner / route-back / stop-loss 显式要求或由 current delta 形态隐含需要 route arbitration 时，对候选下一 delta 做 bounded 比较，输出 route advisory：哪个 paper、artifact、reviewer、memory、human-gate 或 typed-blocker delta 最值得下一次 attempt 追。 | 不成为默认 route scan、admission gate、route blocking layer、quality closure、publication readiness、artifact authority 或 owner receipt。 |
| `bounded micro-candidate generation` | 只在当前 owner 显式要求或由 current delta 形态隐含需要候选时，在当前 stage / work unit 内生成少量可执行候选，例如 claim repair、analysis check、display fix、review question 或 memory lookup target；候选必须绑定 target surface、预算和停止条件。 | 不成为默认 brainstorm、后台研究队列、hard preflight、route 前置阻塞或替代 executor 直接推进。 |
| `critique-as-repair-hint` | 把 reviewer / auditor 批评转成下一 owner 可消费的 repair hint、target surface、missing evidence ref 和 route-back reason。 | 批评本身不关闭 quality gate，不声明 paper ready，不替代独立 reviewer/auditor record 或 MAS owner receipt。 |
| `reusable lesson extraction` | 只在当前 owner 显式要求或由 current delta 形态隐含需要 failure recall / reviewer concern 时，召回失败路径、negative result、曾拒候选、route-back、human decision 和 reviewer concern，作为当前 attempt 的 context refs；最多产出一个 refs-only reusable lesson。 | memory recall / writeback score 不等于 memory accept/reject verdict、paper progress、artifact authority 或 publication-route closure。 |
| `triggered meta-review` | 只在 route 停滞、重复同一 work unit、reviewer 输出冲突、高风险 promotion 或 stop-loss 候选出现时触发，用来给 decision / route owner 生成 arbitration brief。 | 不作为每轮必经 gate，不阻断正常 admission，不替代 publication gate、human gate、owner receipt 或 stable typed blocker。 |
| `opportunistic knowledge prefetch` | 只在下一 owner 已明确、当前 owner 显式要求或 current delta 形态隐含需要、且不会拖慢 admission 时，准备文献、source、journal constraint、prior failed path 和 reviewer concern refs，供 executor/reviewer 快速 hydrate context。 | 缺失、陈旧或低分 prefetch 只能记为 observability / platform repair；不得计为 paper progress、route blocker、quality score 或 readiness proof。 |

因此，Progress-first controller 读到这些 signal 时只能把它们当作 next-owner selection、reviewer briefing、memory reuse 或 no-loop suppression 的输入。真正推进仍必须落到 paper/artifact/reviewer/memory/human-gate delta、MAS owner receipt、stable typed blocker、route-back、stop-loss 或可消费 next owner handoff。

## 执行目标

下一轮 `/goal` 的目标应写成：

> 以 `docs/runtime/designs/coscientist_stage_route_restructure.md` 为 source of truth，把 MAS 重构为 Co-Scientist 启发的 Stage-native scientific work system：每个 Stage 都有明确 skill、tool、knowledge、portfolio、quality gate、closeout 和 owner receipt/blocker 合同；Route controller 以 Progress-first 方式选择下一真实科研 delta；hypothesis / claim / analysis portfolio 进入 MAS-owned refs-first contract；相关 `agent/` pack、machine-readable contracts、source projections、focused tests、runtime/docs 入口全部落地并验证，完成后吸收回 `main`、清理临时 worktree/分支。

该目标的完成条件不是本文存在，而是下文所有 `验收门` 通过或产出 stable typed blocker / human gate / stop-loss，并且没有把 platform repair、projection freshness、ranking score、provider completion 或 tests pass 写成医学质量、publication readiness、artifact authority 或 paper closure。

## 理想 Stage 合同

每个主 Stage 必须变成同构、可发现、可执行、可审计的工作包。统一字段如下：

| 字段 | 必须表达的内容 | 机器落点 |
| --- | --- | --- |
| `stage_objective` | 本 Stage 要产生的真实科研增量 | `agent/stages/stage_route_contract.yaml` 或派生 descriptor |
| `entry_contract` | 进入 Stage 前必须读到的 study truth、source、evidence、memory、artifact refs | stage knowledge packet / controller read model |
| `skill_pack` | Stage 内 executor 的人读 skill、prompt、工作规则 | `agent/skills/`、`agent/prompts/`、generated stage surfaces |
| `tool_policy` | 可用工具、数据库、模型、脚本和 forbidden writes | action catalog / product-entry / domain-handler allowlist |
| `knowledge_packet` | 文献、source、failed-path、portfolio、reviewer concerns、journal constraints | `stage_knowledge_packet`、memory descriptor |
| `portfolio_input` | 候选假设、claim、analysis option、失败路径、ranking/proximity advisory | hypothesis / research portfolio contract |
| `quality_gate` | 独立 reviewer/auditor、rubric、currentness、route-back/blocker | `agent/quality_gates/`、publication eval / review ledger |
| `closeout` | owner receipt、typed blocker、human gate、route-back、stop-loss 或 progress delta | owner receipt / typed blocker contract |
| `memory_writeback` | 可复用经验、失败路径、route memory accept/reject/blocker | publication-route memory writeback receipt |
| `opl_projection` | OPL 只能 index/display/dispatch refs 的边界 | generated descriptor / refs-only projection |

统一禁止项：

- Stage completion 不能由 provider completion、queue done、read-model refreshed、page generated、ranking top score 或 executor 自审证明。
- Stage closeout 不能只有状态刷新；必须产生 domain delta、owner receipt、typed blocker、human gate、route-back、stop-loss 或明确 no-op currentness proof。
- Quality gate 不能由同一 executor invocation 自审关闭。
- OPL/App/workbench 不能写 MAS study truth、memory body、artifact body、publication verdict 或 `current_package`。

## 理想 Route 编排

Route 应从静态阶段链升级为 Progress-first route supervisor：

1. 每个 Stage closeout 输出候选下一步：继续、route back、review、repair、human gate、stop-loss、finalize 或 typed blocker。
2. Route supervisor 以 `evidence gain / claim impact / risk / cost / blocked refs / human gate / quality pressure` 为排序因素选择下一 owner。
3. 选择结果只授权“下一次 attempt”，不授权医学质量、publication readiness 或 artifact mutation。
4. 每次 attempt 必须更新 portfolio、failed-path ledger、review memory、next owner 和 owner receipt/blocker。
5. 重复 receipt consumption、read-model reconcile、provider liveness repair 只能记为 platform repair；没有同步 domain delta 时不能计入 paper progress。

Route controller 的稳定输出形状：

```text
current_owner_ticket
  owner
  allowed_action
  work_unit
  required_input_refs
  target_surface
  acceptance_criteria
  forbidden_writes
  expected_receipt_or_blocker
  no_loop_budget
```

## Portfolio OS

MAS 需要把 hypothesis、claim、analysis candidate、review finding、failed path 和 route option 统一成 refs-first portfolio object。Co-Scientist 的 tournament / proximity / evolution 信号进入 advisory field，不进入 authority field。

每个 portfolio candidate 至少包含：

- `candidate_id`、`study_id`、`quest_id`、`route_stage`、`currentness_basis`。
- 研究目标和 active claim boundary。
- assumption / sub-assumption decomposition。
- supporting evidence refs 与 contradicting evidence refs。
- novelty / prior-art / source provenance refs。
- testability / feasibility / safety refs。
- negative / failed-path refs。
- ranking、pairwise debate、proximity、evolution、meta-review refs，并明确 `advisory=true`。
- promotion / rejection / route-back / human gate / owner receipt / typed blocker refs。

Promotion 规则：

- 缺 source refs、contradiction refs、failed-path refs、testability refs 或 required reviewer/human gate refs 时，必须 fail closed。
- ranking/proximity 只能影响探索顺序、reviewer workload 和候选聚类。
- 进入 write/review/finalize 的候选必须绑定 claim-evidence map、AI reviewer/auditor record、publication gate 或 typed blocker。

## Stage-by-Stage 落地目标

| Stage | 需要落地的 skill/tool/knowledge/QC 目标 |
| --- | --- |
| `scout` | 强化 literature/source discovery skill；工具绑定文献检索、source locator、guideline/journal-neighbor refs；知识包必须含 topic landscape、workspace literature coverage、prior-art boundary；QC 检查 question/population/evidence boundary、novelty 和 source readiness。 |
| `idea` | 引入 portfolio generation / proximity / advisory ranking；工具绑定 candidate board、prior failed-line recall；知识包含 prior candidate、journal fit、study reference context；QC 检查 novelty、clinical relevance、data fit、testability、stop rule。 |
| `baseline` | 强化 cohort/endpoint/comparator readiness；工具绑定 data contract、baseline runner、reproducibility refs；知识包含 cohort lock、endpoint window、comparator history；QC 检查 reproducibility、source readiness、failed comparator lessons。 |
| `experiment` | 明确 primary-result execution contract；工具绑定 analysis pipeline、stat plan、run lineage；知识包含 approved protocol、endpoint/comparator lock；QC 检查 result answers question、negative result preservation、deviation refs。 |
| `analysis-campaign` | 加入 bounded exploration / evolution loop；工具绑定 sensitivity、subgroup、fusion/debug/stop candidate board；知识包含 evidence gap、reviewer concerns、failed-path history；QC 检查 evidence gain、multiplicity、claim boundary、route impact。 |
| `write` | 把 portfolio candidate 转为 claim narrative；工具绑定 manuscript builder、claim-evidence map、citation/display tools；知识包含 evidence pack、journal neighbors、reporting guideline；QC 检查 claim restraint、citation support、reader risk、display-to-claim consistency。 |
| `review` | 对齐 Reflection / deep verification / observation review；工具绑定 full literature/source-grounded reader/stat reporting/citation checks；知识包含 manuscript、claim map、prior reviewer findings；QC 必须由独立 AI reviewer/auditor record 关闭。 |
| `finalize` | 明确 package authority 和 artifact freshness；工具绑定 rebuild/export/proof/declarations；知识包含 publication eval、controller decision、package freshness、human gate status；QC 检查 artifact lineage、submission readiness boundary、human gate。 |
| `decision` | 作为 Meta-review / route arbitration owner；工具绑定 stop-loss memo、route matrix、decision trace；知识包含 all receipts/blockers/reviews；QC 检查 go/stop/reroute/human gate 是否引用 current evidence。 |
| `journal-resolution` | 作为 outlet/package route resolver；工具绑定 journal guidelines、export profile、response/data/citation/figure packs；知识包含 target outlet constraints；QC 检查 journal fit 不改变 claim boundary。 |

## 并行落地线

下一轮实际执行可以拆成四条并行 worktree / subagent lane。每条 lane 必须拥有 disjoint write set，主会话负责最终 diff、验证、吸收和清理。

### Lane A: Semantic Pack / Stage Contract

Write scope:

- `agent/stages/stage_route_contract.yaml`
- `agent/stages/*.policy.md`
- `agent/prompts/*.md`
- `agent/skills/*.md`
- `agent/knowledge/*.md`
- `agent/quality_gates/*.md`

目标：

- 把 `portfolio_input`、`tool_policy`、`quality_gate`、`closeout` 和 `opl_projection` 明确进入每个 Stage 的声明面。
- 将 Co-Scientist-inspired Generation / Reflection / Ranking / Proximity / Evolution / Meta-review 转译为 MAS stage role，不使用外部 runtime 名称作为 authority。
- 更新 hypothesis portfolio / evidence pack、AI reviewer / auditor gate、medical research execution skill policy。

验收：

- 每个 route 有 portfolio/knowledge/QC/closeout obligation 或明确 `not_applicable`。
- advisory ranking/proximity 不出现在 authority 字段。
- executor/reviewer 独立性在 quality gate 中 fail closed。

### Lane B: Machine Contracts / Generated Projection

Write scope:

- `contracts/pack_compiler_input.json`
- `contracts/stage_control_plane.json`
- `contracts/action_catalog.json`
- `contracts/foundry_agent_series.json`
- `contracts/generated_surface_handoff.json`
- 相关生成器源码和 fixture，仅在必要时触及。

目标：

- 让 pack compiler 和 stage control plane 投影 Stage-native scientific work system 的字段。
- 确保 OPL generated/hosted surfaces 只能消费 refs、task、receipt、blocker、projection，不能获得 authority。
- 把 portfolio refs、advisory signal refs、quality gate refs、closeout refs 投影到可验证 machine-readable surface。

验收：

- 生成合同与源码构建结果一致。
- `generated_surface_owner=one-person-lab`、MAS authority invariant 不被放宽。
- 修改 machine-readable contract 时跑 `make test-meta`。

### Lane C: Controller / Route Supervisor / Read Model

Write scope:

- `src/med_autoscience/**` 中 stage_route、opl_domain_pack、runtime_protocol、controller/read-model 相关最小必要文件。
- 对应 focused tests。

目标：

- Route supervisor 输出稳定 `current_owner_ticket` 或等价 projection。
- no-loop budget、platform repair / domain delta 分账、owner receipt/blocker selection 更直接地围绕 Stage-native contract。
- 如果当前源码已有等价字段，则优先收薄和重命名；不新增 MAS-private scheduler、queue、attempt loop。

验收：

- 当前 owner/action/work unit/target surface 可由 machine contract 推导。
- 重复 receipt/read-model reconcile 不计 paper progress。
- OPL/provider completion 不授权 MAS closure。

### Lane D: Runtime Docs / Active Plan / Operator Runbook

Write scope:

- `docs/active/mas-ideal-state-gap-plan.md`
- `docs/active/current-development-lines.md`
- `docs/active/stage_surface_standardization_program.md`
- `docs/runtime/**`
- `docs/project.md`、`docs/invariants.md`、`docs/status.md` 中必要 compact 更新。

目标：

- 把完成后的实际落点回写到唯一 active truth、stage surface owner、runtime contracts 和 operator runbook。
- 删除或归档被新 contract 取代的平行叙述，不制造第二 backlog。
- 明确哪些仍是 production evidence tail：真实 paper-line apply、reviewer/auditor scaleout、human gate/resume、artifact/memory lifecycle receipt、provider long soak。

验收：

- active docs 只保留当前 owner、open gates、执行顺序和禁止误写。
- dated proof / receipt id / worklist 数字不进入 active docs。
- 文档变更通过 docs-only verification。

## 吸收与清理规则

实际执行阶段若使用多个 worktree：

1. 每个 lane 从当前 `main` 或指定 base 建立独立 worktree。
2. 每个 lane 的 prompt 第一行必须写清 `任务、cwd、读写权限、source of truth、停止条件`。
3. lane 间写集必须 disjoint；若冲突，主会话决定取舍，不让 subagent 自行扩大 scope。
4. 每个 lane 完成后主会话必须检查 diff、运行必要 focused verification、确认没有 forbidden writes。
5. 吸收回 main 时只吸收本轮文件；不覆盖并发脏改动。
6. 合并后运行总验证，清理本轮 worktree 和临时分支。
7. 无法完成的 lane 必须产出 stable typed blocker / human gate / stop-loss 式记录，不能在最终回复中包装为完成。

## 总体验收门

下一轮 `/goal` 只有在以下条件满足时才能关闭：

- `agent/` stage semantic pack 已表达 Stage-native scientific work system。
- machine-readable contracts / generated projections 与 `agent/` source 一致。
- Route supervisor / read model 不再把 platform repair 误记为 paper progress。
- Portfolio object 和 advisory ranking/proximity 边界进入 contract/test。
- 独立 reviewer/auditor quality gate 和 executor self-review ban 有 focused test 或明确 fail-closed proof。
- OPL boundary 保持 refs-only：不能写 study truth、memory body、artifact body、publication verdict、source readiness verdict 或 `current_package`。
- 文档入口已同步，且 single Active Truth 仍归 `mas-ideal-state-gap-plan.md`。
- 至少运行：
  - `rtk git diff --check`
  - `rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs agent contracts src tests README.md README.zh-CN.md`
  - `rtk scripts/verify.sh`，若触及 machine-readable contract / runtime semantics，追加 `rtk make test-meta`
  - 根据触及面追加 focused pytest 或 contract generation check。

若执行阶段只完成文档和 contract，但未完成 source/read-model/runtime 行为，不能关闭总目标；必须保留 open lane、typed blocker 或后续 owner。

## 当前禁止误写

- 不能把本文写成 MAS 已经实现 Co-Scientist-like runtime。
- 不能把 progress-first Co-Scientist affordance 写成默认前置流程、真实 paper-line 已关闭、production-ready、domain-ready、publication-ready、submission-ready 或 `current_package` fresh。
- 不能引入外部 Co-Scientist runtime、外部 authority、不可审计 provider body 或 ranking owner。
- 不能把 Elo、pairwise debate、novelty score、proximity representative、meta-review summary 写成 source readiness、quality verdict、publication gate、human gate、artifact authority、owner receipt 或 typed blocker。
- 不能把 `next-delta tournament`、`bounded micro-candidate generation`、`critique-as-repair-hint`、`reusable lesson extraction`、`triggered meta-review` 或 `opportunistic knowledge prefetch` 写成 admission gate、quality closure、publication readiness、artifact authority、route blocking layer，或把 platform repair / prefetch / review score 计为 paper progress。
- 不能把 active docs 中的执行规格当成 machine interface；机器 truth 必须进入 contracts/source/tests/runtime surfaces。
- 不能把 specs landing、suite pass、contract generated、provider completion 或 OPL worklist 清零写成 paper closure、publication-ready、domain-ready、submission-ready 或 `current_package` 更新。
