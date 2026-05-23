# OPL Temporal MAS Runtime Retirement Program

Status: `production_residency_proof_landed; mas_proof_ingestion_landed; watchdog_kernel_migrated; live_paper_apply_pending; content-level owner doc`
Date: `2026-05-14`
Owner: `MedAutoScience domain owner receipts + OPL Runtime Manager integration boundary`
Purpose: 定义当前 P2 框架对齐线路：MAS 与 OPL stage-led、以 Agent executor 为最小执行单位 runtime framework 之间的边界、优先级和退役门槛。
State: `active_support`
Machine boundary: 本文是人读 program owner。机器真相继续归 MAS controller/runtime surfaces、OPL provider contracts、sidecar receipts、attempt ledgers、durable schemas、CLI/API behavior 和 live workspace evidence。
完整历史记录：[2026-05-11 OPL Temporal MAS Runtime Retirement full record](../history/program/opl_temporal_mas_runtime_retirement_program_2026_05_11_full_record.md)。

## 当前角色

本文是 MAS program portfolio 的 P2，也是当前执行顺序的第一优先级。P2 不是针对每个 scheduler、Hermes、MDS、Portal 或 SQLite 相关 surface 的整包退役清单。它持有内容级 framework transition：

- MAS 暴露 domain-agent descriptor、stage/control-plane metadata、sidecar export/dispatch、owner receipt、projection、artifact locator 和 authority refs。
- OPL 提供 stage-led、以 Agent executor 为最小执行单位的 framework 层：generic executor adapter、durable stage attempt、queue、wakeup、retry/dead-letter、approval/human gate transport、provider receipt、projection、shared lifecycle/index primitives。
- MAS 保留 study truth、paper quality、publication verdict、owner route、runtime owner decision 和 artifact authority。
- MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt；MAS 的默认 concrete executor requirement 仍是 `codex_cli_default`，本地 direct path 可独立诊断和执行，但不扩展成 Hermes/Claude 执行器，也不成为 generic executor platform。

详细 module matrix 和旧 phase checklist 已归档在 full record。当前执行应选择下面的内容 lane，而不是把旧文档当成一个大计划整体执行。

## 当前状态

当前状态是 `agent_executor_adapter_boundary_landed_opl_temporal_production_proof_landed_mas_provider_proof_ingestion_landed_watchdog_kernel_migrated_live_paper_apply_pending`。

P2 的当前口径是：OPL-hosted MAS 的 descriptor、sidecar、guarded apply receipt、publication-route memory receipt chain、OPL Temporal production residency proof ingestion、managed Temporal state projection 和 legacy no-default-caller tombstone proof 已形成可维护基础面；这些只证明 framework transition 可承载 MAS refs 和 blockers，不证明 paper closure、publication quality 或 submission readiness。

当前默认运行口径已机器化：MAS hosted path 在任务启动后默认启用 OPL/Temporal hosted autonomous runtime。`runtime_backend_default_operation_contract.default_autonomous_runtime`、product-entry `provider_topology.default_autonomous_runtime`、sidecar / product-entry `managed_temporal_state_consistency.default_autonomous_runtime` 和 `runtime_transport_handoff_projection.default_caller_policy` 都声明 OPL/Temporal 持有持久在线调度、唤醒、retry、resume、attempt ledger 和 worker residency；`codex_app_outer_driver_required=false`，`mas_daemon_scheduler_attempt_loop_allowed=false`。`Codex CLI` 仍是 stage 内默认 concrete executor，不是 MAS 私有 daemon 或 scheduler。

真实 paper-line long-running apply 仍是 production evidence gate。P2 后续只保留 framework/runtime owner 边界和 MAS-owned receipt 输出要求；具体工程收口回到 OPL production closure matrix 与 MAS 当前 development lines。每项结果要么进入 MAS-owned receipt / locator / typed blocker surface，要么明确返回 owner guard、live gate、authorization 或 contract gap。

MAS 侧当前已落地的 P2 基线按能力类别读取：

- OPL admission：MAS 可被 OPL 发现为 aligned domain-agent skeleton 和 stage control plane；OPL 统一 Agent Executor Adapter 对 MAS 只接收 executor requirement、typed closeout 和 domain-task receipt，`Codex CLI` 是默认 concrete executor requirement，非默认 executor 只作为显式 adapter / proof lane。
- provider/read-model：OPL Temporal production residency proof 已可证明 managed Temporal service、worker、task queue、attempt query、signal、typed closeout、missing closeout blocker、retry/dead-letter 和 domain truth boundary；MAS product-entry manifest、sidecar export、OPL family-runtime status 与 runtime snapshot 同源消费这些 read-only refs。
- sidecar / owner receipt：MAS sidecar export/dispatch 可暴露 typed paper-autonomy task、owner receipt contract、lifecycle apply request 和 guarded apply proof；OPL/provider 只能保存 refs、blocker 或 receipt locator，不写 publication eval、controller decision、current package、paper package、artifact gate、memory body、evidence ledger 或 review ledger。
- paper autonomy / memory：多条真实 paper line 已具备 read-only closeout projection、guarded apply proof surface、publication-route memory consumed/writeback refs 和 no-forbidden-write boundary；真实 closeout 仍要求 MAS owner receipt、typed blocker、artifact delta、gate replay、reviewer judgment、human gate 或 stop-loss。
- domain repair / aftercare：`domain_health_diagnostic` 已收敛为 MAS domain health / reconcile / owner repair kernel；runtime turn、study progress、domain route scan 和 publication aftercare 只投影 MAS owner refs、quality/source refs、safe action refs、typed blocker 和明确 owner 的 repair hint，不授权 provider 或 OPL 写 paper truth。
- standard skeleton / locator：`standard_domain_agent_skeleton`、repo-source anchor、runtime artifact locator、body-free memory inventory、Stage Review / Index 和 workspace artifacts 均按 locator-only / refs-only 边界读取；memory body、writeback acceptance、publication route authority 和 artifact mutation authority 仍留在 MAS owner surface。
- legacy retirement：local scheduler、Hermes hosted scheduler/runtime、MDS/DeepScientist backend、workspace-local service wrapper、旧 manager/UI wording 和旧 default caller 已进入 tombstone/provenance 或 explicit diagnostic cleanup；新 scaffold 不再生成旧 wrapper，后续可删代码只按无 active reference、无 fixture/provenance dependency 与 replacement proof 执行。

cutover 或物理退役前仍未完成：

- OPL stage attempt 下真实长时 domain activity soak；OPL Codex runner 的 repo/test harness 已具备 `dry_run`、`live_dry_run` 与 `codex_cli` process supervision，但 MAS paper-line provider-hosted 连续运行证据仍未完成；
- 至少一条真实 MAS paper-line provider-hosted guarded apply soak 仍要在 live workspace gate 允许时闭合：链路为 OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer judgment / human gate / stop-loss / typed blocker；
- human gate / user modification / resume token 从 OPL signal 进入 MAS revision 或 gate owner chain 的 proof；
- provider parity 证明之后，旧 scheduler/Hermes/MDS/legacy alias 的物理删除或 history/tombstone 归档仍需按 no-active-reference 证据逐项执行；已满足删除口径的 wrapper / alias 不再保留旧入口或可调用测试。

这些剩余项现在按 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md) 的一步到位 physical/source morphology closure 路线执行，不再拆成另一份 P2 大计划，也不再沿旧 phase checklist 漂移。P2 只持有 framework/runtime owner 边界；`runtime_transport`、SQLite lifecycle、workbench、sidecar 和 status projection 这类仍存在的文件只能写成 retained adapter / diagnostic / direct handler target with deletion gate，不能写成已物理清零或 MAS generic runtime owner：

| remaining gate | gate class | P2 responsibility | completion evidence |
| --- | --- | --- | --- |
| `provider_residency_status_and_activity_soak` | `production_evidence_gate` | 消费 OPL provider proof，向 MAS product-entry / sidecar / workbench 投影 provider readiness、attempt query、retry/dead-letter、typed blocker 和 no-forbidden-write boundary。 | OPL attempt refs + MAS sidecar receipt + domain activity closeout；缺真实 provider 或 live gate 时返回 typed blocker。 |
| `provider_guarded_apply_soak` | `production_evidence_gate` | 保持 provider-hosted request 只能进入 MAS sidecar dispatch / guarded apply receipt，不写 MAS truth。 | MAS owner receipt 显示 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 stable blocker。 |
| `human_gate_resume_owner_chain` | `production_evidence_gate` | 只承载 OPL approval/signal/transport refs；MAS 决定 human gate 是否阻塞、恢复或 route back。 | MAS controller / runtime owner surface 记录 human gate reason、resume receipt、next owner 或 typed blocker。 |
| `legacy_physical_cleanup` | `functional_follow_through_gate` | `workspace-legacy-physical-cleanup-audit` 与 `workspace-legacy-physical-cleanup-apply` 已完成 5 个真实 profile 的旧 active-path archive/tombstone 和 provenance ref rewrite；workspace-local service wrapper 不再生成，旧 root 不再作为 active runtime / controller / delivery path。后续只做 drift guard 和新增 legacy ref cleanup。 | targeted no-active-reference proof、replacement proof、无 current truth/delivery/provenance dependency、focused cleanup tests。 |
| `skeleton_and_lifecycle_followthrough` | `functional_follow_through_gate` | 把 repo-source anchors、artifact locator、cleanup/restore/retention receipt requirement 投影给 OPL。 | 新 surface 按 standard skeleton slot 落位；domain artifact mutation 返回 MAS receipt requirement 或 typed blocker。 |

## 活跃内容 Lane

| priority | lane | 当前范围 | output |
| --- | --- | --- | --- |
| `P2.1` | `opl_framework_foundation` | OPL 已具备 Temporal production residency proof，可证明 stage attempt、Temporal-backed runtime、queue/wakeup、retry/dead-letter、approval/human gate transport、receipt/projection 与 domain truth boundary；MAS 已提供 managed lifecycle state consistency projection，OPL family-runtime status / runtime snapshot 已消费该 projection，剩余是更长时 domain activity soak 和 App 级展示 polish。 | OPL framework/provider readiness evidence |
| `P2.2` | `mas_framework_migration` | MAS 作为 OPL-admitted domain agent 暴露 domain skeleton、stage descriptor、sidecar export/dispatch、owner receipts、projection builder、artifact locator 和 authority refs。 | MAS direct path / OPL-hosted path receipt equivalence |
| `P2.3` | `framework_generic_lifecycle_lift` | 把 MAS runtime lifecycle、artifact locator、retention、restore-proof、migration-ledger 经验分类为 OPL framework-generic primitive 与 MAS-domain truth。 | OPL primitive candidates plus MAS retained-domain list |
| `P2.4` | `legacy_retirement_after_replacement` | MAS 已提供 no-active-default-caller tombstone proof、physical tombstone contract、workspace legacy physical cleanup audit/apply 和 5 个真实 profile 的 no-active-reference proof；旧 scheduler/Hermes/MDS/legacy manager/UI wording 与代码继续按 replacement proof 逐项退役，只有 archive/provenance/parity 必需 reader 保留。 | retired path evidence、targeted cleanup audit、tombstone contract、删除旧入口后的 scaffold/init tests 和更新后的 explicit diagnostic docs |
| `P2.5` | `final_paper_line_guarded_soak` | read-only proof 已覆盖多条真实 paper line；MAS-owned guarded apply proof 与 sidecar dispatch receipt closure surface 已能承认 MAS owner receipt 或返回 typed blocker；sidecar pending task projection 已按独立 source fingerprint 与 target-scoped owner refs 生成。下一步是在 provider-hosted live apply 中证明真实 paper line 可经 OPL attempt + MAS owner chain 前进或明确阻塞。 | MAS truth surface 中的 attempt query、owner receipt、progress delta、gate replay、reviewer update、human gate、stop-loss 或 typed blocker |

这些是内容线。后续变更可以只实现其中一条，不需要触碰整个 P2 surface。

### OPL Umbrella Plan 对齐

P2 对 OPL production functional closure 的职责是提供 MAS domain-owned evidence，而不是复制 OPL 的 provider/operator/workbench 总计划。对应关系如下：

| OPL lane | MAS P2 responsibility | boundary |
| --- | --- | --- |
| `provider-readiness-operator-closure` | 消费 OPL production proof，向 product-entry / sidecar / workbench projection 暴露 provider available、freshness、typed blocker 和 no-forbidden-write boundary。 | MAS 不实现 OPL provider kernel 或 operator repair action。 |
| `owner-receipt-contract-generalization` | 把 MAS sidecar dispatch、guarded apply、stage closeout、human gate、stop-loss 和 owner progress 都投影为同构 owner receipt / typed blocker refs。 | OPL attempt ledger 只持 refs，不持 paper truth。 |
| `domain-memory-apply-generalization` | 让 publication-route memory consumed/proposal/accepted/rejected/writeback receipt 泛化到更多 fixture / workspace owner surface。 | OPL/Aion 不读取 memory body，不接受或拒绝 writeback。 |
| `lifecycle-guarded-apply-generalization` | 对 MAS artifact/package/runtime mutation 保持 domain receipt requirement；只把 locator / blocker / restore refs 投影给 OPL。 | OPL metadata apply 不能删除或重写 MAS artifacts。 |
| `physical-skeleton-follow-through` | 维护 MAS repo-source skeleton physical anchors、slot 映射与低风险 follow-through。 | workspace/runtime artifact body、receipt instances、memory body 不迁入 repo skeleton。 |
| `legacy-active-path-final-retirement` | 给旧 MDS/Hermes/local scheduler/default alias surface 做 no-active-caller proof 和 tombstone/retained-provenance 分类。 | explicit archive、fixture、parity oracle 可保留，但必须标注语境；legacy active-path tombstone contract 已落地。 |
| `operator-workbench-drilldown` | 提供 MAS workbench projection 所需的 provider refs、stage review refs、memory refs、safe action receipt refs 和 typed blockers。 | OPL App 只展示和发受控 request，不写 MAS truth。 |
| `cross-repo-production-closeout-gate` | 提供 MAS 当前功能闭环状态、验证 refs、receipt coverage、legacy residue state 和 typed blocker summary。 | 缺真实 live apply 时报告 typed blocker，不把 gate 写成 paper closure。 |

## 当前分类规则

任何 MAS runtime-adjacent surface 开工前必须先分类：

| class | meaning |
| --- | --- |
| `retain_in_mas` | domain authority 或 owner surface 留在 MAS |
| `move_to_opl_provider` | 通用 long-running attempt、queue、wakeup、retry、signal/query、approval 或 dead-letter 责任进入 OPL provider |
| `lift_to_opl_framework` | 跨 domain lifecycle/index/restore/retention primitive 进入 OPL shared framework，MAS 保留 domain refs |
| `degrade_to_local_diagnostics` | MAS 保留显式 one-shot/local diagnostic/evidence command，不作为 Full online readiness |
| `retired_no_default_caller` | old alias、legacy vocabulary、duplicated UI 或 manager path 已无 default caller；无 fixture/provenance 需要时直接删除源码、命令 wrapper 和测试入口，只保留 history/reference 语境 |

该规则取代旧的文件级假设。一个文件或功能可以包含混合内容；先分类内容块，再只移动或编辑该内容块。

## 优先级调整

旧 P2 标题里有 `Temporal` 和 `retirement`，但当前优先级应按 framework-first 执行：

1. 先完成 OPL 作为完整智能体框架的基础能力；
2. 再把 MAS 迁移成 OPL-admitted domain agent，并冻结 sidecar/receipt/authority/ref 边界；
3. 同步把 MAS 已验证的通用 lifecycle/index/restore pattern 上收到 OPL framework；
4. 用替代证据清理旧 local/Hermes/MDS/default alias surface，不把旧兼容性无限期保留；满足删除口径时直接删除，不新增兼容 wrapper；
5. 最后做真实 MAS paper-line guarded apply soak，验证迁移后的目标形态；当前 read-only soak 与 MAS-owned guarded apply proof surface 是进入 live apply 的前置证据，不是最终投稿级完成证据。

因此，当前优先级不是先 paper soak，也不是无证据清空历史层。清理属于迁移收口条件：删除前必须证明无 default caller、无 fixture/provenance 必需、已有 replacement diagnostic/history link；证明成立后就直接删除，不再把旧入口当作维护目标。

## 边界

OPL/Temporal 可以持有：

- generic executor adapter、Codex CLI default selection、Hermes/Claude explicit opt-in executor routing、stage attempt identity、queue state、activity status、retry/dead-letter state、approval/human-gate transport state、provider history、query/projection、framework lifecycle/index/cache metadata。Temporal production residency proof 是 OPL-hosted production path 的 provider readiness 证据；local provider 只保留 MAS direct/local diagnostics、OPL dev/CI/offline baseline 和 fixture proof。

MAS 必须持有：

- study truth、runtime health truth、paper progress SLO、owner-route decision、AI reviewer verdict、publication gate、evidence/review ledgers、canonical manuscript/package authority、terminal attach owner gate 和 MAS action receipts。

MAS sidecar/dispatcher/readiness 只能表达 OPL executor requirement 或接收 OPL receipt。`executor_kind` 的 MAS-owned 支持面保持 `codex_cli_default`，用于默认 concrete executor requirement、direct path 执行和 standalone diagnostics；Hermes scheduler / hosted runtime 文字统一按 explicit OPL opt-in reference、history/provenance 或 `retired_no_default_caller` 处理。

Provider attempt completion、queue hydration 或 worker liveness 只是支撑证据。只有 MAS owner surfaces 显示 artifact delta、gate owner progress、AI reviewer judgment update、route decision、stop-loss、human gate 或 typed blocker 时，才算 paper progress。

## 验证

P2 证据按层级判断：

1. Focused MAS sidecar/export/dispatch tests 和 forbidden-write tests；
2. OPL provider attempt/queue/signal/query tests 和 Temporal production residency proof；
3. Direct MAS skill path 与 OPL-hosted path 的 receipt equivalence，以及 MAS product-entry/sidecar 对 `--opl-production-proof` 的 proof ingestion；
4. guarded apply 前先做 real paper-line read-only soak；当前多条真实 paper line 已满足该前置条件；
5. guarded apply evidence 必须写明 OPL attempt ref、MAS owner receipt、idempotency key、source fingerprint、source refs、artifact delta / blocker 和 no-forbidden-write proof；
6. 退役验证必须证明无 default CLI/MCP/product-entry/skill caller、无 OPL active reference、无 fixture/provenance dependency，并有 replacement diagnostic/history link。

Docs-only P2 更新需要 `git diff --check` 和 link/path spot check。Contract/runtime 更新需要 focused tests 加 repo-native verification。

## 历史内容处置

上一版 P2 长文档包含完整 module matrix、TypeScript language rationale、target phases、developer checklist、open risks 和详细 cleanup candidates。它已经归档为 full record。

需要 provenance 和实施细节时读取归档。当前规划和执行应从本文的活跃内容 lane、分类规则和优先级开始。
