# MAS / OPL 进度运行时理想蓝图

Owner: `MedAutoScience / OPL Framework`
Purpose: `ideal_progress_runtime_blueprint_after_mas_opl_failure_research`
State: `active_target_design`
Machine boundary: 本文是人读顶层目标设计和迁移门。机器真相继续归 `agent/` pack、`contracts/`、源码、CLI/MCP/API 行为、OPL `DomainProgressTransitionRuntime` / StageRun / current-control readback、MAS runtime/controller durable surfaces、owner receipt、typed blocker、human gate、route-back evidence、fresh `study_progress` / domain diagnostic readback 和真实 workspace artifact。
Date: `2026-06-17`
当前完成度读法：`2026-06-20` 起，以 `contracts/paper_progress_transition_runtime_completion_audit.json#/blueprint_l0_l7_functional_acceptance` 为准；只有 `repo/source/control-plane` L0-L7 切片可读为 `done` / `100%`，整体蓝图仍是 `partial`，live acceptance 仍是 `deferred_not_run`。

## 目标结论

这两轮调研共同指向同一个设计判断：MAS/OPL 的理想形态不是“MAS 再补一个更聪明的监督器”，也不是“domain diagnostic、read-model、queue、Workbench 各自继续加优先级”。理想形态必须把论文推进压成一条 OPL-owned durable transition spine：

```text
DomainIntent -> OPL Command -> OPL Event -> OPL Transactional Outbox
  -> StageRun / ToolInvocation -> MAS OwnerAnswer -> Derived Projection
```

其中：

- `DomainIntent`：MAS 声明当前医学研究目标、stage semantics、owner action、policy result、required refs、forbidden authority。
- `OPL Command`：OPL 把 MAS intent 规范化为带 aggregate identity、expected version、idempotency key 和 precondition 的运行时命令。
- `OPL Event`：OPL 只把已提交事实写成 append-only event；event 是推进真相，不是读面文案。
- `OPL Transactional Outbox`：需要外发 side effect 时，command/event/outbox 在同一事务边界落账。
- `StageRun / ToolInvocation`：OPL 负责 provider attempt、tool invocation、lease、retry/dead-letter、human gate transport、terminal closeout。
- `MAS OwnerAnswer`：MAS 消费 terminal closeout / tool output / human answer 后，签 owner receipt、typed blocker、quality gate receipt、route-back evidence、artifact/paper delta 或 stable stop。
- `Derived Projection`：domain diagnostic、study progress、current work unit、Portal、Workbench、trace、lineage 都只是从 OPL event 和 MAS owner answer 派生。

用户可见“推进”只允许来自同一 current identity 下的 fresh runnable evidence：strict running proof、provider admission accepted、owner receipt、stable typed blocker、human gate、route-back evidence、quality gate receipt、canonical paper/gate/artifact semantic delta 或 terminal stop-loss。docs、合同、测试绿、queue empty、projection fresh、provider pending count、trace visible、read-model refresh 和 refs-only ledger 都不能替代推进证据。

## 根因判断

旧 MAS + MDS 能把论文从零推进完，根本原因不是旧架构更正确，而是它的推进闭环更短：同一个系统同时决定下一步、执行、记录结果和继续循环。质量可能粗糙，但控制权没有被拆散。

OPL-based MAS 卡住几百小时的根因是控制环拆分后没有形成新的唯一推进者：

| 症状 | 直接表现 | 根因 |
| --- | --- | --- |
| 多轮修复后仍回到同类 blocker | `current_work_unit`、`paper_recovery_state`、domain diagnostic、domain-handler export、OPL current-control、Workbench 看到不同下一步。 | transition authority 分裂；派生面都在解释“下一步”。 |
| owner receipt 已记录但不消费成下一 owner | receipt、successor action、provider admission 和旧 readiness residue 互相覆盖。 | 缺少同 identity 的 command/event/outbox transaction。 |
| provider admission pending / count=0 被反复误读 | pending、empty、observe-only、dry-run 被当成 idle、恢复或进度。 | read model 没有 `authority=false` 和 `derived_from_event_id` 约束；projection 被升格。 |
| old dispatch / queue residue 复活 | 旧 ready dispatch、old closeout、stage packet residue 抢当前 work unit。 | StageRun identity 和 selected packet/currentness identity 不统一。 |
| typed blocker 不能稳定停止或恢复 | stop-loss 后同一 work unit 被 redrive，或 blocker 只停在投影层。 | fixed-point loop 没有 exactly-one outcome / `NonAdvancingApply` 终止事件。 |

所以这不是单点 bug，而是设计缺陷：MAS 私有控制面、OPL runtime substrate、read-model projection 和 operator surfaces 之间缺少一条唯一、可回放、幂等、可恢复的 domain progress transition spine。

## 外部成熟经验的转译

本蓝图只吸收工程模式，不引入外部 runtime 或 authority。

| 来源 | 关键经验 | 本地转译 | 禁止误用 |
| --- | --- | --- | --- |
| Kubernetes controller | controller 是持续 control loop，把 current state 推近 desired state。 | OPL 持有 desired/current/status reconcile；MAS 只声明 domain desired 和 policy verdict。 | domain diagnostic / Workbench 不能自己变成第二 controller。 |
| Kubebuilder / controller-runtime | reconcile 必须幂等；一个 controller 管太多 Kind 会破坏封装和维护性。 | `DomainProgressTransitionRuntime` 必须按 aggregate identity 幂等；MAS policy adapter 不承担多个通用 runtime Kind。 | 不靠局部 if/priority 处理每种历史残留。 |
| Temporal durable execution | event history 支撑 crash recovery、resume 和持续推进。 | StageRun / provider attempt / closeout 必须有 OPL event history 和 replay/readback。 | provider completion 不等于 MAS owner answer。 |
| CQRS / Event Sourcing | write event 与 read projection 分离；append-only log 是 system of record，projection 可重建且 eventually consistent。 | OPL event log 是推进真相；study progress / domain diagnostic / Workbench 都是 derived projection。 | projection fresh 不能声明 progress。 |
| Transactional Outbox | 状态变化和外发消息在同一事务边界持久化，避免半成功。 | OPL command/event/outbox 同 transaction；provider start、owner callable、human gate 都从 outbox side effect 发出。 | MAS 不创建 OPL outbox record。 |
| OpenTelemetry | trace/span/log/metric 用于观测和诊断。 | OPL Observability Plane 暴露 trace、failure class、SLO drift、latency。 | trace visible 不能关闭 receipt、quality gate 或 blocker。 |
| OpenLineage | run/job/dataset facets 给跨系统 lineage 元数据。 | StageRun、artifact、dataset、claim/evidence 用 refs-only lineage envelope。 | lineage 只证明来源关系，不授权 paper/artifact authority。 |
| Argo Workflows | workflow artifacts 是跨 step 传递和归档的显式对象。 | OPL 运输 artifact refs；MAS 判断 artifact mutation / publication package authority。 | artifact exists / archived 不等于 publication-ready。 |
| MLflow Tracking | run、metrics、parameters、artifacts 可追踪实验过程。 | analysis campaign / model run / display candidate 进入 evidence plane。 | metric better / run complete 不等于 scientific conclusion。 |

外部证据来源：

- Kubernetes Controllers: <https://kubernetes.io/docs/concepts/architecture/controller/>
- Kubebuilder good practices: <https://book.kubebuilder.io/reference/good-practices.html>
- Temporal Events and Event History: <https://docs.temporal.io/workflow-execution/event>
- Azure CQRS pattern: <https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs>
- Azure Event Sourcing pattern: <https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing>
- Azure Transactional Outbox pattern: <https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos>
- OpenTelemetry traces: <https://opentelemetry.io/docs/concepts/signals/traces/>
- OpenLineage facets: <https://openlineage.io/docs/spec/facets/>
- Argo Workflows artifacts: <https://argo-workflows.readthedocs.io/en/latest/walk-through/artifacts/>
- MLflow Tracking: <https://mlflow.org/docs/latest/ml/tracking/>

## 理想模块分层

### 1. MAS Declarative Medical Research Pack

MAS 的长期主要源码形态应是声明式 pack，而不是私有 runtime：

- stage goal、inputs、outputs、handoff、quality gates；
- current owner action、required refs、accepted answer shape；
- source/data/artifact/publication/memory authority boundary；
- paper progress / recovery / accounting policy adapter；
- tool/capability refs、Scientific Capability Registry consumption policy；
- forbidden authority 和 fail-open / fail-closed 条件。

Pack 可以被 OPL 编译和托管，但医学语义仍由 MAS 持有。

### 2. MAS Medical Authority Kernel

MAS 只保留不能声明化的最小 authority functions：

- study truth 和 source/data binding；
- source readiness verdict；
- AI reviewer / auditor / publication quality verdict materialization；
- artifact mutation authorization 和 package freshness interpretation；
- publication-route memory accept / reject / blocker；
- owner receipt signer、typed blocker materializer、human gate / route-back consumer；
- no-forbidden-write proof 和医学 helper implementation。

这些函数只能输出 owner receipt、typed blocker、quality gate receipt、domain authority ref、human gate、route-back evidence、safe action ref 或 diagnostic ref；不能扩展成 scheduler、queue、outbox、event log、workbench、state index body store 或 generic lifecycle engine。

### 3. OPL DomainProgressTransitionRuntime

OPL 基座必须把以下能力做成一等 primitive：

| Primitive | Owner | 职责 |
| --- | --- | --- |
| `CommandNormalizer` | OPL | 消费 MAS `opl_domain_progress_transition_request`，生成 OPL command。 |
| `TransitionEventLog` | OPL | append-only event log、aggregate version、schema evolution、replay。 |
| `TransactionalOutbox` | OPL | provider start、owner callable、human gate、tool invocation side effect。 |
| `FixedPointReconciler` | OPL | 每轮 exactly-one transition；无推进写 `NonAdvancingApply`。 |
| `StageRunKernel` | OPL | attempt identity、lease、retry/dead-letter、heartbeat、terminal closeout。 |
| `HumanGateTransport` | OPL | resume token、approval interrupt、timeout、requery。 |
| `RecoveryObligationStore` | OPL | 同 identity obligation lifecycle、stop-loss、route-back readback。 |
| `StateIndexKernel` | OPL | refs-only projection、lag、rebuild、current pointer drilldown。 |
| `Tool Arsenal / Capability Runtime` | OPL + MAS pack | current-owner-bound tool card、invocation plan、result envelope。 |
| `Observability / Lineage Plane` | OPL | trace、metric、log、lineage、SLO drift、failure class。 |
| `Workbench Shell` | OPL | operator default cockpit 和 drilldown；不持有 domain truth。 |

每个 primitive 的 readback 必须带：

- `identity`：study / quest / work unit / action / fingerprint / selected packet / attempt key；
- `causality`：command id、event id、outbox id、causal event id、source generation；
- `authority_boundary`：谁能写什么，谁不能解释什么；
- `exactly_one_outcome`：accepted / running / owner answer / stable blocker / human gate / route-back / non-advancing；
- `projection_metadata`：derived_from_event_id、observed_generation、lag_status、authority=false。

缺任一字段族时，该 readback 只能作为 diagnostic，不能进入 provider admission、domain diagnostic apply success、ordinary owner route、Workbench next action 或 paper progress accounting。

### 4. Derived Projection Plane

所有 read model 和 UI 都必须降级为 projection：

| Surface | 理想角色 | 不得承担 |
| --- | --- | --- |
| `study_progress` | 用户默认状态投影。 | 生成下一步或签 owner answer。 |
| domain diagnostic dry-run | 诊断当前 transition possibility。 | 声明恢复、progress 或 ready。 |
| domain diagnostic apply | OPL fixed-point runtime consumer / readback wrapper。 | MAS 内部自建 fixed-point apply。 |
| `NextActionEnvelope` | StageOutcome 后唯一 default next action envelope。 | 由 queue、attempt、delivery mirror 或旧 work-unit residue 反推。 |
| `current_work_unit` | legacy aggregate diagnostic / provenance projection。 | 选择默认下一步、覆盖 NextActionEnvelope / event log / outbox truth。 |
| `paper_recovery_state` | MAS paper policy result projection。 | 从旧 queue/dispatch residue 选下一步。 |
| `domain-handler export` | OPL runtime intake projection。 | 直接 transport 成 domain completion。 |
| Portal / Workbench | cockpit + drilldown。 | 以 UI visible / queue empty 声明 progress。 |
| trace / lineage | 观测和 provenance。 | 关闭 quality / artifact / publication authority。 |

## 理想运行协议

每个推进循环必须遵守：

```text
1. read OPL authoritative event state
2. read MAS domain truth / policy adapter result / owner answer refs
3. read external observation with source generation
4. decide exactly one transition under aggregate identity
5. commit command/event/outbox with compare-and-set
6. execute side effect through OPL StageRun/tool/human transport or MAS owner callable
7. fresh readback
8. repeat until stable accepted outcome or NonAdvancingApply
```

稳定 outcome 只允许：

- `provider_admission_accepted`
- `strict_current_identity_running_proof`
- `terminal_closeout_consumed`
- `owner_receipt_recorded_or_consumed`
- `quality_gate_receipt_recorded`
- `stable_typed_blocker`
- `human_gate_opened`
- `route_back_evidence_recorded`
- `paper_or_artifact_semantic_delta`
- `terminal_stop_loss`
- `NonAdvancingApply`

同一 aggregate/version 如果再次读到相同状态且没有产生新 event/outbox/owner answer，必须写 `NonAdvancingApply` typed blocker，而不是返回 `ok=true`、`observe_only`、`pending_count=0` 或 refreshed projection。

## 一劳永逸的解法

“一劳永逸”不是一次性修完所有历史数据，而是关闭同类问题的再生路径。完成条件必须是架构级的：

1. OPL 是唯一 transition runtime owner：command/event/outbox/fixed-point/StageRun/human gate/state index 都在 OPL。
2. MAS 是唯一 medical authority owner：paper policy、owner answer、quality verdict、artifact/memory/source authority 都在 MAS。
3. 所有 status/projection/UI 均可重建：没有 read model 能单独写下一步、签 receipt 或授权 provider。
4. 所有 side effect 来自 transactional outbox：provider start、owner callable、tool invocation、human gate transport 都有同 transaction readback。
5. 所有历史坏轨迹进入 replay：DM002/DM003 的 owner receipt 不推进、stale dispatch 复活、pending count 误读、typed blocker redrive、closeout/StageRun identity split 都必须变成 replay fixture。
6. 所有无推进 apply 变成 typed blocker：`NonAdvancingApply` 是正式 outcome，不是失败日志。
7. 所有完成声明绑定 live evidence：测试和合同只证明实现形状，论文推进只由 fresh runtime / owner evidence 证明。

只有满足这些条件，同类问题才不会继续在 domain diagnostic、current_work_unit、domain-handler export、OPL queue、Workbench 或 sidecar 中换个名字复发。

## 迁移路线

| Lane | 目标 | 完成门 | 不能声明 |
| --- | --- | --- | --- |
| L0 理想蓝图与入口收敛 | 固定本文、核心入口、OPL/MAS owner split、forbidden interpretations。 | docs diff clean、入口可追踪。 | runtime ready / paper progress。 |
| L1 OPL runtime contract | 固定 command/event/outbox envelope、aggregate identity、idempotency、projection metadata、NonAdvancingApply。 | OPL contract + conformance tests。 | provider-backed soak。 |
| L2 MAS adapter 收薄 | MAS 只输出 clean transition request 和 policy / owner answer shape。 | focused tests 证明无 OPL runtime artifact 字段、无 outbox/event/StageRun 自签。 | MAS 可以 authorize provider admission。 |
| L3 historical replay | DM002/DM003 坏轨迹全部 replay 到 exactly-one outcome。 | replay fixtures 通过，forbidden interpretation 被拒绝。 | live paper recovered。 |
| L4 domain diagnostic / owner-route / export 消费 OPL event | 派生面 consume-only，domain diagnostic apply 走 OPL runtime。 | focused tests + dry-run/readback shape 证明 projection authority=false。 | domain diagnostic dry-run = progress。 |
| L5 transactional outbox side effect | provider start / owner callable / human gate 都从 OPL outbox 发出。 | outbox append + StageRun/tool/human gate readback 绑定同 identity。 | provider completion = MAS owner answer。 |
| L6 projection demotion / legacy retirement | old dispatch、queue residue、local scheduler、private kernel 只剩 tombstone/provenance/diagnostic。 | no active caller、replacement parity、no-forbidden-write proof、fresh owner/stable blocker gate。 | private residue 物理全删，除非有 live gate。 |
| L7 live paper-line acceptance | DM002/DM003 fresh apply/readback 给出 exactly-one live outcome。 | running proof / owner receipt / stable blocker / human gate / route-back / paper delta。 | publication-ready / submission-ready，除非质量门另证。 |

## 本轮功能面验收矩阵

本轮 goal 只关闭 repo/source/control-plane 功能面；live evidence / runtime-paper acceptance 不作为完成门，且未运行 `domain diagnostic apply`、provider start、hydrate、tick、redrive、owner-route reconcile，未写 Yang runtime/study/paper artifacts。机器读根是 `contracts/paper_progress_transition_runtime_completion_audit.json#/blueprint_l0_l7_functional_acceptance`。

后续“一步到位”完成度审计的人工读根是 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 的“一步到位落地矩阵与完成度审计”。本文只定义 progress spine 和 L0-L7 blueprint；实际验收必须把 `repo/source/control-plane` 与 `live acceptance` 分账，逐项报告 OPL `TransitionRuntime`、`Outbox`、`StageRunKernel`、`StateIndex`、`Tool Arsenal`、`Workbench`，以及 MAS `Declarative Pack`、`Medical Authority Kernel` 是否各自拥有 fresh evidence。

| Level | 功能面 | repo/source/control-plane required | already done | live-only deferred |
| --- | --- | --- | --- | --- |
| L0 | 理想蓝图与入口收敛 | `done`：蓝图、owner split、forbidden interpretations、completion audit 分栏已落盘。 | 目标设计和 false completion boundaries 已存在，本轮补 machine acceptance matrix。 | 不涉及 live acceptance。 |
| L1 | OPL runtime contract | `done`：command/event/outbox、aggregate identity、idempotency、projection metadata、`NonAdvancingApply`、complete transaction readback shape 已有 source/contract/tests。 | OPL `DomainProgressTransitionRuntime` 与 current-control NonAdvancingApply primitive 已在 OPL main。 | DM002/DM003 same-transition OPL command/event/outbox/StageRun live readback。 |
| L2 | MAS adapter 收薄 | `done`：MAS 只输出 clean transition request / policy / owner-answer shape，不自签 OPL event/outbox/StageRun/provider admission。 | `PaperProgressPolicyAdapter` 和 projection metadata demotion tests 已覆盖。 | fresh MAS owner answer after OPL runtime consumption。 |
| L3 | historical replay | `done`：DM002/DM003 坏轨迹、pending-count 误读、owner receipt 不推进、typed blocker redrive、closeout/StageRun split 进入 replay/contract tests。 | replay fixtures 与 EvidenceGap explicit-input tests 已覆盖。 | fresh DM002/DM003 live readback 取代 replay fixture evidence。 |
| L4 | domain diagnostic / owner-route / export consume-only | `done`：domain diagnostic、provider admission、owner-route/export/current projections 只消费完整 OPL-backed readback；不完整 readback fail closed / authority=false。 | MAS readback validator、provider-admission arbiter、current_work_unit/study_progress projection tests 已覆盖。 | domain diagnostic apply exactly-one live outcome 与 current DM002/DM003 provider-admission live readback。 |
| L5 | transactional outbox side effect | `done`：side-effect acceptance contract、outbox/StageRun identity、false claim boundary、live evidence work orders 已落盘；MAS 不创建 OPL outbox。 | OPL runtime source/tests 和 MAS contracts 已定义 transaction identity boundary。 | OPL outbox/StageRun live readback 与 provider/owner callable side effect readback。 |
| L6 | projection demotion / legacy retirement | `done`：legacy queue/dispatch/local scheduler/private kernel/alias/wrapper/compat carrier 已物理退役、tombstone/provenance 或 retained-minimal-adapter 分类；no-active/rebuild/source-adapter/readback surfaces 已落盘。 | runtime retirement inventory repo-source completion 为 done，EvidenceGap projection 不再从 pending count 推断 authority。 | OPL StateIndexKernel、Workbench Shell、Observability、RecoveryObligationStore、owner-callable soak 等 live tails。 |
| L7 | live paper-line acceptance harness | `done` 仅限 preflight/runbook/contract/readback acceptance harness：work orders、evidence schema、rollup、identity gate、false live-claim boundary 已落盘。 | live acceptance harness 已存在并拒绝 docs/tests/queue empty/dry-run/projection 作为 live proof。 | fresh DM002/DM003 accepted outcome、domain diagnostic apply exactly-one、same-identity OPL current-control/StageRun readback、MAS owner receipt/stable blocker/human gate/route-back/paper delta。 |

## OPL 基座优化要求

OPL 侧应把这次 MAS 经验提升为 Foundry Agent 的通用基座能力：

- `TransitionRuntime` 必须成为唯一 ordinary progress transition owner：command normalization、event append、fixed-point reconcile、NonAdvancingApply 和 replay/readback 都在 OPL，MAS 只提交 DomainIntent / policy result。
- `Outbox` 必须与 transition event 同事务提交：provider start、MAS owner callable、tool invocation 和 human gate side effect 都从 outbox 发出，outbox emitted 不等于 MAS owner answer。
- `StageRunKernel` 必须持有 attempt identity、lease、retry/dead-letter、resume、heartbeat 和 terminal closeout；provider completion 只能作为 MAS owner-consumption input。
- `StateIndex` 必须只做 refs-only rebuild/read/checkpoint，显式区分 observed generation、accepted transition ref、projection lag 和 authority=false。
- `Tool Arsenal` 必须从 `current_owner_delta` 生成 tool card、invocation plan 和 `ToolResultEnvelope`；capability 输出默认是 refs-only candidate，只有 MAS owner/reviewer/route-back 消费后才进入 progress。
- `Workbench` 必须默认显示 current owner、stable outcome 和 next gate；raw queue、trace、lineage、provider detail 只进入 drilldown。
- 标准 Agent 默认 ordinary route 必须从 `current_owner_delta` 进入 transition runtime，而不是从 raw worklist、queue history、sidecar refs 或 UI action 反推。
- `StageRun currentness identity` 必须包含 route identity、attempt idempotency、selected stage packet / dispatch refs、source generation 和 terminal closeout ordering。
- `domain-handler export` intake 必须优先识别 domain progress transition request；普通 owner-callable pending task 不得旁路 transition runtime。
- `StateIndexKernel` 必须显式区分 observed_generation 与 accepted_transition_ref，避免高 generation observation 抹掉低 generation accepted transition。
- App / Console / Workbench 默认只显示 current owner、stable outcome 和 next human/action gate；raw queue、trace、lineage、provider detail 进入 drilldown。
- Standard Agent conformance 必须拒绝五类伪完成：descriptor ready、generated interface ready、provider completed、refs-only ledger verified、classification zero。

## 验收口径

按风险分层：

- L1 docs/design：`git diff --check`、冲突标记扫描、入口链接 spot-check。
- L3 contract/runtime shape：focused contract tests、replay fixtures、forbidden interpretation tests、projection demotion tests。
- L4 runtime/currentness：fresh `study_progress`、domain diagnostic apply/readback、OPL current-control / StageRun readback、owner receipt / typed blocker / human gate / route-back refs。

禁止完成声明：

- `contract_landed` 不能代表 runtime landed。
- focused tests 通过不能代表 live domain diagnostic apply 前进。
- OPL event/outbox append 不能代表 MAS owner answer。
- provider completion 不能代表 paper progress。
- lineage / trace / metric / UI visible 不能代表 quality gate。
- `provider_admission_pending_count=0`、queue empty、projection fresh 不能代表 idle、done 或恢复。

## 与现有文档的关系

- [MAS / OPL Agent OS 目标运行架构参考](./mas_opl_agent_os_target_operating_architecture.md) 定义总体产品与运行分层；本文把“论文推进为什么卡住、如何一劳永逸地压成运行时 spine”单独提炼。
- [OPL Domain Progress Transition Runtime 与 MAS Paper Policy Adapter 目标设计](./paper_progress_transition_kernel_target.md) 是本文在 paper-line currentness / owner-route / provider admission 上的具体 runtime 设计。
- [Paper Autonomy Supervisor 目标设计](./paper_autonomy_supervisor_target.md) 继续定义 paper obligation / supervisor decision；本文要求通用 fixed-point 和 resume runtime 上收到 OPL。
- [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 维护执行顺序、当前证据缺口和下一轮 prompt；本文不替代 active plan。
- [当前状态](../../status.md)、[架构概览](../../architecture.md)、[不可变约束](../../invariants.md)、[关键决策记录](../../decisions.md) 只保留短入口和当前口径，不重复本文细节。
