# OPL Temporal MAS Runtime Retirement Program

Status: `production_residency_proof_landed; mas_proof_ingestion_landed; watchdog_kernel_migrated; live_paper_apply_pending; content-level owner doc`
Date: `2026-05-14`
Owner: `MedAutoScience domain owner receipts + OPL Runtime Manager integration boundary`
Purpose: 定义当前 P2 框架对齐线路：MAS 与 OPL stage-led、以 Agent executor 为最小执行单位 runtime framework 之间的边界、优先级和退役门槛。
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

真实 paper-line long-running apply 仍是 production evidence gate。P2 后续只保留 framework/runtime owner 边界和 MAS-owned receipt 输出要求；具体工程收口回到 OPL production closure matrix 与 MAS 当前 development lines。每项结果要么进入 MAS-owned receipt / locator / typed blocker surface，要么明确返回 owner guard、live gate、authorization 或 contract gap。

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
- `medautosci sidecar export` 已为 DM002、DM003、Obesity 分别生成 provider-hosted guarded-apply pending task，每条 task 都带 target-scoped MAS owner controller decision refs、guarded-apply owner receipt contract 和独立 source fingerprint；`medautosci sidecar dispatch` 已支持 `paper_autonomy/guarded-apply`，只写 MAS sidecar dispatch receipt 和 `real_paper_autonomy_provider_hosted_guarded_apply_receipt` 嵌套结果；OPL/provider 仍不能写 publication eval、controller decisions、current package、paper package、artifact gate、memory body、evidence ledger 或 review ledger；
- `runtime_watch` 已从旧 watchdog 角色收敛为 MAS domain health / reconcile / owner repair kernel：`execution_owner_guard.supervisor_only=true` 下只允许同一 study/quest/run 的 MAS controller-owned live work-unit repair 或 controller-authorized runtime recovery；authorization mismatch、terminal lifecycle、provider/platform/OPL repair、缺 MAS controller authorization 均 fail closed。AI reviewer `publication_eval/latest.json` 只作为质量读面，不再被当作 guarded apply owner receipt；
- MAS runtime core turn runner 现在会在进入下一轮 Codex turn 前清理已闭合 publication work-unit 的 stale controller authorization，并从 prompt 中去重旧授权消息；study progress / domain route scan 同步把 runtime turn closeout 中的 paper-facing artifact delta 纳入 freshness，并在 supervisor-only live delta 且无更高优先级 action 时投影 `supervisor_only/live_quality_repair`。这些是 MAS owner repair kernel 的功能性收口，不授权 provider 或 OPL 写 paper truth；
- `publication-route-memory-inventory` 已补齐 OPL/Aion 可消费的 body-free `operator_grouping` 与 stale/deprecated `review_summary`，使 domain memory receipt refs 可以按 workspace、stage、route family 和 status 展示；memory body、writeback acceptance 和 publication route authority 仍留在 MAS owner surface；
- `standard_domain_agent_skeleton` 现在包含 `physical_skeleton_layout_audit` 和 repo-source anchor status；`agent/standard-domain-agent-anchor.json`、`contracts/runtime/standard-domain-agent-anchor.json`、`runtime/artifact_locator/workspace-runtime-artifact-root.locator.json` 与 `docs/runtime/contracts/standard_domain_agent_skeleton.md` 已作为 physical anchors，同时把 workspace artifacts 固定为 locator-only；
- MAS local scheduler path 已物理退役为 tombstone/provenance-only：默认 scheduler owner 已迁到 OPL `opl_provider_runtime_manager`，`local` 不再作为 active CLI manager、diagnostic bridge 或 cleanup command 暴露；Portal、Live Console、`study-progress` 和 cockpit 只读展示 MAS domain receipt、paper-progress blocker、quality/source refs、safe action refs 和明确 owner 的 repair hint，不再表述为 MAS 自有 generic runtime / scheduler / workbench owner。
- 默认 caller 已从 Hermes scheduler / hosted runtime 路径移走；Hermes 相关 surface 当前只作为 OPL explicit opt-in executor/proof reference、history/provenance 读取或 legacy scheduler cleanup；`ensure --manager hermes` 不再生成/刷新/触发 cron job。Hosted/runtime default path 已固定为 `retired_no_default_caller`。非默认 executor adapter 只需要证明显式接入、receipt 与 fail-closed 边界，不进入 MAS 默认 production soak。
- OPL 统一 Agent Executor Adapter 对 MAS 的边界已经落地：MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt；`codex_cli_default` 是 MAS 默认 concrete executor requirement 和 direct path 诊断入口，`Hermes-Agent` / `Claude Code` 不扩展成 MAS-owned executor kind，也不被写成 MAS runtime truth。
- `legacy_retirement_tombstone_proof` 已把 Hermes executor adapter、Hermes hosted scheduler/runtime、MDS/DeepScientist backend 和 workspace-local scheduler 分类成 explicit legacy diagnostic cleanup、retired no-default-caller history reference、fixture/provenance 或 tombstone-only refs；active default caller 为空，legacy active-path tombstone contract 已落到 `contracts/runtime/legacy-active-path-tombstones.json`，后续可删代码只按无 active reference、无 fixture/provenance dependency 与 replacement proof 执行。旧 workspace-local `install/watch/uninstall-watch-runtime-service` wrapper 已满足该删除口径：canonical scheduler 生命周期由 OPL provider/runtime manager 管理，新 scaffold 不再生成 wrapper，legacy init 只负责删除旧生成物。

cutover 或物理退役前仍未完成：

- OPL stage attempt 下真实长时 domain activity soak；OPL Codex runner 的 repo/test harness 已具备 `dry_run`、`live_dry_run` 与 `codex_cli` process supervision，但 MAS paper-line provider-hosted 连续运行证据仍未完成；
- 至少一条真实 MAS paper-line provider-hosted guarded apply soak 仍要在 live workspace gate 允许时闭合：链路为 OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer judgment / human gate / stop-loss / typed blocker；
- human gate / user modification / resume token 从 OPL signal 进入 MAS revision 或 gate owner chain 的 proof；
- provider parity 证明之后，旧 scheduler/Hermes/MDS/legacy alias 的物理删除或 history/tombstone 归档仍需按 no-active-reference 证据逐项执行；已满足删除口径的 wrapper / alias 不再保留兼容入口或可调用测试。

这些剩余项现在按 [MAS Current Development Lines](./current-development-lines.md) 的全线规划闭环表执行，不再拆成另一份 P2 大计划。P2 只持有 framework/runtime owner 边界：

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
| `P2.5` | `final_paper_line_guarded_soak` | read-only proof 已覆盖 DM002/DM003/Obesity；MAS-owned guarded apply proof 与 sidecar dispatch receipt closure surface 已能承认 MAS owner receipt 或返回 typed blocker；sidecar pending task projection 已按 DM002/DM003/Obesity 拆成独立 source fingerprint 与 target-scoped owner refs。下一步是在 provider-hosted live apply 中证明真实 paper line 可经 OPL attempt + MAS owner chain 前进或明确阻塞。 | MAS truth surface 中的 attempt query、owner receipt、progress delta、gate replay、reviewer update、human gate、stop-loss 或 typed blocker |

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

因此，当前优先级不是先 paper soak，也不是无证据清空历史层。清理属于迁移收口条件：删除前必须证明无 default caller、无 fixture/provenance 必需、已有 replacement diagnostic/history link；证明成立后就直接删除，不再把兼容入口当作维护目标。

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
4. guarded apply 前先做 real paper-line read-only soak；当前 DM002/DM003/Obesity 已满足该前置条件；
5. guarded apply evidence 必须写明 attempt id、MAS owner receipt、idempotency key、source fingerprint、source refs、artifact delta / blocker 和 no-forbidden-write proof；
6. 退役验证必须证明无 default CLI/MCP/product-entry/skill caller、无 OPL active reference、无 fixture/provenance dependency，并有 replacement diagnostic/history link。

Docs-only P2 更新需要 `git diff --check` 和 link/path spot check。Contract/runtime 更新需要 focused tests 加 repo-native verification。

## 历史内容处置

上一版 P2 长文档包含完整 module matrix、TypeScript language rationale、target phases、developer checklist、open risks 和详细 cleanup candidates。它已经归档为 full record。

需要 provenance 和实施细节时读取归档。当前规划和执行应从本文的活跃内容 lane、分类规则和优先级开始。
