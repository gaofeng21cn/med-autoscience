# OPL Temporal MAS Runtime Retirement Program

Status: `production_residency_proof_landed; mas_proof_ingestion_landed; watchdog_kernel_migrated; live_paper_apply_pending; content-level owner doc`
Date: `2026-05-13`
Owner: `MedAutoScience Runtime OS + OPL Runtime Manager integration boundary`
Purpose: 定义当前 P2 框架对齐线路：MAS 与 OPL stage-led、以 Agent executor 为最小执行单位 runtime framework 之间的边界、优先级和退役门槛。
Machine boundary: 本文是人读 program owner。机器真相继续归 MAS controller/runtime surfaces、OPL provider contracts、sidecar receipts、attempt ledgers、durable schemas、CLI/API behavior 和 live workspace evidence。
Full historical record: [2026-05-11 OPL Temporal MAS Runtime Retirement full record](../history/program/opl_temporal_mas_runtime_retirement_program_2026_05_11_full_record.md).

## 当前角色

本文是 MAS program portfolio 的 P2，也是当前执行顺序的第一优先级。P2 不是针对每个 scheduler、Hermes、MDS、Portal 或 SQLite 相关 surface 的整包退役清单。它持有内容级 framework transition：

- MAS 暴露 domain-agent descriptor、stage/control-plane metadata、sidecar export/dispatch、owner receipt、projection、artifact locator 和 authority refs。
- OPL 提供 stage-led、以 Agent executor 为最小执行单位的 framework 层：generic executor adapter、durable stage attempt、queue、wakeup、retry/dead-letter、approval/human gate transport、provider receipt、projection、shared lifecycle/index primitives。
- MAS 保留 study truth、paper quality、publication verdict、owner route、runtime owner decision 和 artifact authority。
- MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt；MAS 本地 `codex_cli_default` 只保留 standalone diagnostics，不扩展成 Hermes/Claude 执行器。

详细 module matrix 和旧 phase checklist 已归档在 full record。当前执行应选择下面的内容 lane，而不是把旧文档当成一个大计划整体执行。

## 当前状态

当前状态是 `agent_executor_adapter_boundary_landed_opl_temporal_production_proof_landed_mas_provider_proof_ingestion_landed_watchdog_kernel_migrated_live_paper_apply_pending`。

2026-05-12 文档收口口径：P2 已经具备 OPL-hosted MAS 的 descriptor、sidecar、guarded apply receipt、DM002 route-memory receipt chain、OPL Temporal production residency proof，以及 MAS 对该 proof 的 product-entry / sidecar ingestion。MAS 读取 `--opl-production-proof` 后，可把 provider availability 从 typed blocker 切到 `available`，但 authority boundary 仍保持 `can_write_domain_truth=false`、`provider_completion_is_paper_closure=false`、`paper_closure_requires_mas_owner_receipt=true`。P2 仍未具备真实 paper-line provider-hosted guarded apply success 证据。真实完成需要在 MAS owner gate 允许时逐条 paper line 产出 owner receipt、artifact/gate/reviewer/route/human-gate/stop-loss evidence，或由 live owner guard / authorization / publication gate 返回 typed blocker。

2026-05-13 functional closure 口径：真实 paper-line long-running apply 仍是 production evidence gate；在此之外，P2 的工程功能闭环不应继续等待真实论文运行。MAS 侧工作应作为 OPL `production-functional-closure-plan.zh-CN.md` 的并行 implementation lane 执行，而不是形成另一份平行大计划。MAS 已把 provider proof 中的 managed Temporal service / worker state 投影成 read-only consistency surface，并新增旧 Hermes / MDS / workspace-local scheduler 的 no-active-default-caller tombstone proof；OPL family-runtime status 和 runtime snapshot 已能消费该 read model，而不把它升级为 MAS paper closure。MAS watchdog 的功能性职责已收敛为 domain health / reconcile / MAS-controller owner repair kernel；repo-source skeleton physical anchors 与 workspace/runtime body-free evidence receipt 已落地，legacy active-path tombstone contract 也已落地。剩余 memory receipt 泛化、真实 provider-hosted owner receipt 和可删代码 cleanup 继续按 OPL umbrella lane 承接。每项结果要么进入 MAS-owned receipt / locator / typed blocker surface，要么明确返回 owner guard、live gate、authorization 或 contract gap。

MAS 侧已经落地：

- MAS 可被 OPL 发现为 aligned domain-agent skeleton 和 stage control plane；
- MAS sidecar export/dispatch 可暴露并消费 typed paper-autonomy task；
- MAS publication-route memory 已有 policy、Markdown canonical library、seed index、workspace apply closure、locator refs、typed writeback proposal 和 router receipt boundary；
- 三篇真实 paper line 已完成 read-only closeout projection：DM002 -> `ai_reviewer_re_eval`，DM003 -> `artifact_delta`，Obesity -> `artifact_delta`，且 `writes_performed=false`；
- DM002 read-only proof 已显示 publication-route memory consumed ref 和 MAS workspace/runtime writeback receipt refs，OPL/Aion 只能显示 refs；
- `real-paper-autonomy-guarded-apply-proof` 已把 read-only proof 推进为 MAS-owned guarded apply proof surface：已有 MAS owner apply receipt 时可承认真实 workspace mutation；没有 owner receipt 或 human/live gate 不允许时输出 typed blocker / receipt，并保持 no-forbidden-write proof；
- OPL Temporal production residency proof 已可证明 managed Temporal service + worker 的 start/query/signal、typed closeout、missing closeout blocker、retry/dead-letter boundary 和 domain truth boundary；MAS product-entry manifest 与 sidecar export 已能消费该 proof 并暴露 provider available read model；
- MAS product-entry manifest 与 sidecar export 已暴露 `managed_temporal_state_consistency`，把 provider proof 的 managed service state、worker state、task queue、attempt query readiness 和 retry/dead-letter visibility 投影给 OPL status/workbench，且仍是 read-only projection；
- OPL family-runtime status 与 runtime snapshot 已消费 MAS `managed_temporal_state_consistency` / `legacy_retirement_tombstone_proof` read model；当 MAS projection 显示 service/worker ready 时，OPL provider readiness 可按同一口径显示，但 authority boundary 保持 `status_projection_only`，不生成 paper progress、quality verdict、submission readiness 或 publication closure；
- MAS product-entry manifest 与 sidecar export 也暴露 OPL production closeout gate 可直接消费的 `owner_receipt_contract` / `domain_owner_receipt_contract`、`lifecycle_apply_requests` 和 `lifecycle_guarded_apply_proof`。这些字段只声明 MAS owner receipt envelope、OPL-owned ledger/locator apply 与 MAS-owned artifact cleanup/restore/retention receipt requirement；OPL 只能保存 refs / blocker / receipt locator，不写 MAS truth、artifact gate、memory body 或 publication verdict；
- `medautosci sidecar dispatch` 已支持 `paper_autonomy/guarded-apply`，只写 MAS sidecar dispatch receipt 和 `real_paper_autonomy_provider_hosted_guarded_apply_receipt` 嵌套结果；OPL/provider 仍不能写 publication eval、controller decisions、current package、paper package、artifact gate、memory body、evidence ledger 或 review ledger；
- `runtime_watch` 已从旧 watchdog 角色收敛为 MAS domain health / reconcile / owner repair kernel：`execution_owner_guard.supervisor_only=true` 下只允许同一 study/quest/run 的 MAS controller-owned live work-unit repair 或 controller-authorized runtime recovery；authorization mismatch、terminal lifecycle、provider/platform/OPL repair、缺 MAS controller authorization 均 fail closed。AI reviewer `publication_eval/latest.json` 只作为质量读面和 closeout evidence，不再被当作 guarded apply owner receipt；
- `standard_domain_agent_skeleton` 现在包含 `physical_skeleton_layout_audit` 和 repo-source anchor status；`agent/standard-domain-agent-anchor.json`、`contracts/runtime/standard-domain-agent-anchor.json`、`runtime/artifact_locator/workspace-runtime-artifact-root.locator.json` 与 `docs/runtime/contracts/standard_domain_agent_skeleton.md` 已作为 physical anchors，同时把 workspace artifacts 固定为 locator-only；
- MAS local scheduler、one-shot reconcile、Portal 和 Live Console 仍是有效 local diagnostics 与 evidence surface。
- 默认 caller 已从 Hermes scheduler / hosted runtime 路径移走；Hermes 相关 surface 当前只作为 explicit optional diagnostics、proof/provenance 或 `retire_after_parity` 读法保留。本轮不要求真实 Hermes/Claude production soak，adapter smoke 与 receipt/fail-closed proof 足以关闭接入能力验收。
- OPL 统一 Agent Executor Adapter 对 MAS 的边界已经落地：MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt，本地 `codex_cli_default` 仅作 standalone diagnostics；`Hermes-Agent` / `Claude Code` 不扩展成 MAS-owned executor kind，也不被写成 MAS runtime truth。
- `legacy_retirement_tombstone_proof` 已把 Hermes executor adapter、Hermes hosted scheduler/runtime、MDS/DeepScientist backend 和 workspace-local scheduler 分类成 optional adapter、retire-after-parity、fixture/provenance 或 standalone diagnostics；active default caller 为空，legacy active-path tombstone contract 已落到 `contracts/runtime/legacy-active-path-tombstones.json`，后续可删代码只按无 active reference、无 fixture/provenance dependency 与 replacement proof 执行。

cutover 或物理退役前仍未完成：

- OPL stage attempt 下真实长时 domain activity soak；OPL Codex runner 的 repo/test harness 已具备 `dry_run`、`live_dry_run` 与 `codex_cli` process supervision，但 MAS paper-line provider-hosted 连续运行证据仍未完成；
- 至少一条真实 MAS paper-line provider-hosted guarded apply soak 仍要在 live workspace gate 允许时闭合：链路为 OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer judgment / human gate / stop-loss / typed blocker；
- human gate / user modification / resume token 从 OPL signal 进入 MAS revision 或 gate owner chain 的 proof；
- provider parity 证明之后，旧 scheduler/Hermes/MDS/legacy compatibility 的物理删除或 history/tombstone 归档仍需按 no-active-reference 证据逐项执行。

这些剩余项现在按 [MAS Current Development Lines](./current_development_lines.md) 的全线规划闭环表执行，不再拆成另一份 P2 大计划。P2 只持有 framework/runtime owner 边界：

| remaining gate | gate class | P2 responsibility | completion evidence |
| --- | --- | --- | --- |
| `provider_residency_status_and_activity_soak` | `production_evidence_gate` | 消费 OPL provider proof，向 MAS product-entry / sidecar / workbench 投影 provider readiness、attempt query、retry/dead-letter、typed blocker 和 no-forbidden-write boundary。 | OPL attempt refs + MAS sidecar receipt + domain activity closeout；缺真实 provider 或 live gate 时返回 typed blocker。 |
| `provider_guarded_apply_soak` | `production_evidence_gate` | 保持 provider-hosted request 只能进入 MAS sidecar dispatch / guarded apply receipt，不写 MAS truth。 | MAS owner receipt 显示 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 stable blocker。 |
| `human_gate_resume_owner_chain` | `production_evidence_gate` | 只承载 OPL approval/signal/transport refs；MAS 决定 human gate 是否阻塞、恢复或 route back。 | MAS controller / runtime owner surface 记录 human gate reason、resume receipt、next owner 或 typed blocker。 |
| `legacy_physical_cleanup` | `functional_follow_through_gate` | 用 legacy audit 和 tombstone contract 指导旧 active-path 删除或归档。 | stale scan、no default caller proof、replacement proof、无 fixture/provenance dependency、focused compatibility tests。 |
| `skeleton_and_lifecycle_followthrough` | `functional_follow_through_gate` | 把 repo-source anchors、artifact locator、cleanup/restore/retention receipt requirement 投影给 OPL。 | 新 surface 按 standard skeleton slot 落位；domain artifact mutation 返回 MAS receipt requirement 或 typed blocker。 |

## 活跃内容 Lane

| priority | lane | 当前范围 | output |
| --- | --- | --- | --- |
| `P2.1` | `opl_framework_foundation` | OPL 已具备 Temporal production residency proof，可证明 stage attempt、Temporal-backed runtime、queue/wakeup、retry/dead-letter、approval/human gate transport、receipt/projection 与 domain truth boundary；MAS 已提供 managed lifecycle state consistency projection，OPL family-runtime status / runtime snapshot 已消费该 projection，剩余是更长时 domain activity soak 和 App 级展示 polish。 | OPL framework/provider readiness evidence |
| `P2.2` | `mas_framework_migration` | MAS 作为 OPL-admitted domain agent 暴露 domain skeleton、stage descriptor、sidecar export/dispatch、owner receipts、projection builder、artifact locator 和 authority refs。 | MAS direct path / OPL-hosted path receipt equivalence |
| `P2.3` | `framework_generic_lifecycle_lift` | 把 MAS runtime lifecycle、artifact locator、retention、restore-proof、migration-ledger 经验分类为 OPL framework-generic primitive 与 MAS-domain truth。 | OPL primitive candidates plus MAS retained-domain list |
| `P2.4` | `legacy_retirement_after_replacement` | MAS 已提供 no-active-default-caller tombstone proof 和 physical tombstone contract；有替代证据后，继续删除或降级 scheduler/Hermes/MDS/legacy manager/UI wording 与代码。当前 active contract 已把 Hermes 表述收窄为 explicit optional executor adapter，把旧 manager 表述保留为 retired cleanup evidence。 | retired path evidence、tombstone contract 和更新后的 diagnostics/fallback docs |
| `P2.5` | `final_paper_line_guarded_soak` | read-only proof 已覆盖 DM002/DM003/Obesity；MAS-owned guarded apply proof 与 sidecar dispatch receipt closure surface 已能承认 MAS owner receipt 或返回 typed blocker。下一步是在 provider-hosted live apply 中证明真实 paper line 可经 OPL attempt + MAS owner chain 前进或明确阻塞。 | MAS truth surface 中的 attempt query、owner receipt、progress delta、gate replay、reviewer update、human gate、stop-loss 或 typed blocker |

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
| `legacy-active-path-final-retirement` | 给旧 MDS/Hermes/local scheduler/default compat surface 做 no-active-caller proof 和 tombstone/retained-provenance 分类。 | explicit archive、fixture、parity oracle 可保留，但必须标注语境；legacy active-path tombstone contract 已落地。 |
| `operator-workbench-drilldown` | 提供 MAS workbench projection 所需的 provider refs、stage review refs、memory refs、safe action receipt refs 和 typed blockers。 | OPL App 只展示和发受控 request，不写 MAS truth。 |
| `cross-repo-production-closeout-gate` | 提供 MAS 当前功能闭环状态、验证 refs、receipt coverage、legacy residue state 和 typed blocker summary。 | 缺真实 live apply 时报告 typed blocker，不把 gate 写成 paper closure。 |

## 当前分类规则

任何 MAS runtime-adjacent surface 开工前必须先分类：

| class | meaning |
| --- | --- |
| `retain_in_mas` | domain authority 或 owner surface 留在 MAS |
| `move_to_opl_provider` | 通用 long-running attempt、queue、wakeup、retry、signal/query、approval 或 dead-letter 责任进入 OPL provider |
| `lift_to_opl_framework` | 跨 domain lifecycle/index/restore/retention primitive 进入 OPL shared framework，MAS 保留 domain refs |
| `degrade_to_local_diagnostics` | MAS 保留显式 one-shot/local/fallback/evidence command，不作为 Full online readiness |
| `retire_after_parity` | old compatibility、legacy vocabulary、duplicated UI 或 manager path 只有在无 default caller、无 fixture need 且有替代 proof 后删除 |

该规则取代旧的文件级假设。一个文件或功能可以包含混合内容；先分类内容块，再只移动或编辑该内容块。

## 优先级调整

旧 P2 标题里有 `Temporal` 和 `retirement`，但当前优先级应按 framework-first 执行：

1. 先完成 OPL 作为完整智能体框架的基础能力；
2. 再把 MAS 迁移成 OPL-admitted domain agent，并冻结 sidecar/receipt/authority/ref 边界；
3. 同步把 MAS 已验证的通用 lifecycle/index/restore pattern 上收到 OPL framework；
4. 用替代证据清理旧 local/Hermes/MDS/default-compat surface，不把旧兼容性无限期保留；
5. 最后做真实 MAS paper-line guarded apply soak，验证迁移后的目标形态；当前 read-only soak 与 MAS-owned guarded apply proof surface 是进入 live apply 的前置证据，不是最终投稿级完成证据。

因此，当前优先级不是先 paper soak，也不是先物理删除。清理属于迁移收口条件：删除前必须证明无 default caller、无 fixture/provenance 必需、已有 replacement diagnostic/history link。

## 边界

OPL/Temporal 可以持有：

- generic executor adapter、Codex CLI default selection、Hermes/Claude explicit opt-in executor routing、stage attempt identity、queue state、activity status、retry/dead-letter state、approval/human-gate transport state、provider history、query/projection、framework lifecycle/index/cache metadata。Temporal production residency proof 是 OPL-hosted production path 的 provider readiness 证据；local provider 只保留 MAS direct/local diagnostics、OPL dev/CI/offline baseline 和 fixture proof。

MAS 必须持有：

- study truth、runtime health truth、paper progress SLO、owner-route decision、AI reviewer verdict、publication gate、evidence/review ledgers、canonical manuscript/package authority、terminal attach owner gate 和 MAS action receipts。

MAS sidecar/dispatcher/readiness 只能表达 OPL executor requirement 或接收 OPL receipt。`executor_kind` 的 MAS-owned 支持面保持 `codex_cli_default`，并且仅用于 standalone diagnostics；Hermes scheduler / hosted runtime 文字统一按 optional diagnostics/provenance 或 `retire_after_parity` 处理。

Provider attempt completion、queue hydration 或 worker liveness 只是支撑证据。只有 MAS owner surfaces 显示 artifact delta、gate owner progress、AI reviewer judgment update、route decision、stop-loss、human gate 或 typed blocker 时，才算 paper progress。

## 验证

P2 证据按层级判断：

1. Focused MAS sidecar/export/dispatch tests 和 forbidden-write tests；
2. OPL provider attempt/queue/signal/query tests 和 Temporal production residency proof；
3. Direct MAS skill path 与 OPL-hosted path 的 receipt equivalence，以及 MAS product-entry/sidecar 对 `--opl-production-proof` 的 proof ingestion；
4. guarded apply 前先做 real paper-line read-only soak；当前 DM002/DM003/Obesity 已满足该前置条件；
5. guarded apply evidence 必须写明 attempt id、MAS owner receipt、idempotency key、source fingerprint、source refs、artifact delta / blocker 和 no-forbidden-write proof；
6. 退役验证必须证明无 default CLI/MCP/product-entry/skill caller、无 OPL active reference、无 fixture/provenance dependency，并有 replacement diagnostic/history link。

Docs-only P2 更新需要 `git diff --check` 和 link/path spot check。Contract/runtime 更新需要 focused tests 加 repo-native verification。

## 历史内容处置

上一版 P2 长文档包含完整 module matrix、TypeScript language rationale、target phases、developer checklist、open risks 和详细 cleanup candidates。它已经归档为 full record。

需要 provenance 和实施细节时读取归档。当前规划和执行应从本文的活跃内容 lane、分类规则和优先级开始。
