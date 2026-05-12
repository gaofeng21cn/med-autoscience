# OPL Temporal MAS Runtime Retirement Program

Status: `adapter/boundary landed; production soak pending; content-level owner doc`
Date: `2026-05-11`
Owner: `MedAutoScience Runtime OS + OPL Runtime Manager integration boundary`
Purpose: 定义当前 P2 框架对齐线路：MAS 与 OPL Codex-first、stage-led runtime framework 之间的边界、优先级和退役门槛。
Machine boundary: 本文是人读 program owner。机器真相继续归 MAS controller/runtime surfaces、OPL provider contracts、sidecar receipts、attempt ledgers、durable schemas、CLI/API behavior 和 live workspace evidence。
Full historical record: [2026-05-11 OPL Temporal MAS Runtime Retirement full record](../history/program/opl_temporal_mas_runtime_retirement_program_2026_05_11_full_record.md).

## 当前角色

本文是 MAS program portfolio 的 P2，也是当前执行顺序的第一优先级。P2 不是针对每个 scheduler、Hermes、MDS、Portal 或 SQLite 相关 surface 的整包退役清单。它持有内容级 framework transition：

- MAS 暴露 domain-agent descriptor、stage/control-plane metadata、sidecar export/dispatch、owner receipt、projection、artifact locator 和 authority refs。
- OPL 提供 Codex-first、stage-led framework 层：generic executor adapter、durable stage attempt、queue、wakeup、retry/dead-letter、approval/human gate transport、provider receipt、projection、shared lifecycle/index primitives。
- MAS 保留 study truth、paper quality、publication verdict、owner route、runtime owner decision 和 artifact authority。
- MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt；MAS 本地 `codex_cli_default` 只保留 standalone diagnostics，不扩展成 Hermes/Claude 执行器。

详细 module matrix 和旧 phase checklist 已归档在 full record。当前执行应选择下面的内容 lane，而不是把旧文档当成一个大计划整体执行。

## 当前状态

当前状态是 `agent_executor_adapter_boundary_landed_provider_ready_domain_adapter_landed_mas_guarded_apply_proof_surface_landed_live_apply_pending`。

MAS 侧已经落地：

- MAS 可被 OPL 发现为 aligned domain-agent skeleton 和 stage control plane；
- MAS sidecar export/dispatch 可暴露并消费 typed paper-autonomy task；
- MAS publication-route memory 已有 policy、seed fixtures、workspace apply closure、locator refs、typed writeback proposal 和 router receipt boundary；
- 三篇真实 paper line 已完成 read-only closeout projection：DM002 -> `ai_reviewer_re_eval`，DM003 -> `artifact_delta`，Obesity -> `artifact_delta`，且 `writes_performed=false`；
- DM002 read-only proof 已显示 publication-route memory consumed ref 和 MAS workspace/runtime writeback receipt refs，OPL/Aion 只能显示 refs；
- `real-paper-autonomy-guarded-apply-proof` 已把 read-only proof 推进为 MAS-owned guarded apply proof surface：已有 MAS owner apply receipt 时可承认真实 workspace mutation；没有 owner receipt 或 human/live gate 不允许时输出 typed blocker / receipt，并保持 no-forbidden-write proof；
- `standard_domain_agent_skeleton` 现在包含 `physical_skeleton_layout_audit`，把 repo-source physical skeleton slot 映射到现有 `docs/`、`templates/`、`src/`、`plugins/` 路径，同时把 workspace artifacts 固定为 locator-only；
- MAS local scheduler、one-shot reconcile、Portal 和 Live Console 仍是有效 local diagnostics 与 evidence surface。
- 默认 caller 已从 Hermes scheduler / hosted runtime 路径移走；Hermes 相关 surface 当前只作为 explicit optional diagnostics、proof/provenance 或 `retire_after_parity` 读法保留。本轮不要求真实 Hermes/Claude production soak，adapter smoke 与 receipt/fail-closed proof 足以关闭接入能力验收。
- OPL 统一 Agent Executor Adapter 对 MAS 的边界已经落地：MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt，本地 `codex_cli_default` 仅作 standalone diagnostics；`Hermes-Agent` / `Claude Code` 不扩展成 MAS-owned executor kind，也不被写成 MAS runtime truth。

cutover 或物理退役前仍未完成：

- OPL provider 的真实 Temporal server/worker residency；Temporal 是 OPL production online runtime 的必需依赖，未安装、未配置或 worker 未 ready 时应作为 install/repair blocker 处理，而不是退回 local provider 宣称 Full online 可用；
- OPL stage attempt 下真实长时 domain activity soak；OPL Codex runner 的 repo/test harness 已具备 `dry_run`、`live_dry_run` 与 `codex_cli` process supervision，但 MAS paper-line provider-hosted 连续运行证据仍未完成；
- 至少一条真实 MAS paper-line provider-hosted guarded apply soak 仍要在 live workspace gate 允许时闭合：链路为 OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer judgment / human gate / stop-loss / typed blocker；
- human gate / user modification / resume token 从 OPL signal 进入 MAS revision 或 gate owner chain 的 proof；
- provider parity 证明之后，清理 scheduler/Hermes/MDS/legacy compatibility 的 active-path residue。

## 活跃内容 Lane

| priority | lane | 当前范围 | output |
| --- | --- | --- | --- |
| `P2.1` | `opl_framework_foundation` | 先完成 OPL 完整智能体框架所需的 stage attempt、Temporal-backed production runtime、queue/wakeup、retry/dead-letter、approval/human gate transport、receipt/projection、shared lifecycle/index primitive。 | OPL framework/provider readiness evidence |
| `P2.2` | `mas_framework_migration` | MAS 作为 OPL-admitted domain agent 暴露 domain skeleton、stage descriptor、sidecar export/dispatch、owner receipts、projection builder、artifact locator 和 authority refs。 | MAS direct path / OPL-hosted path receipt equivalence |
| `P2.3` | `framework_generic_lifecycle_lift` | 把 MAS runtime lifecycle、artifact locator、retention、restore-proof、migration-ledger 经验分类为 OPL framework-generic primitive 与 MAS-domain truth。 | OPL primitive candidates plus MAS retained-domain list |
| `P2.4` | `legacy_retirement_after_replacement` | 有替代证据后，删除或降级 scheduler/Hermes/MDS/legacy manager/UI wording 与代码；当前 active contract 已把 Hermes 表述收窄为 explicit optional executor adapter，把旧 manager 表述保留为 retired cleanup evidence。 | retired path evidence 和更新后的 diagnostics/fallback docs |
| `P2.5` | `final_paper_line_guarded_soak` | read-only proof 已覆盖 DM002/DM003/Obesity；MAS-owned guarded apply proof surface 已能承认 MAS owner receipt 或返回 typed blocker。下一步是在 provider-hosted live apply 中证明真实 paper line 可经 OPL attempt + MAS owner chain 前进或明确阻塞。 | MAS truth surface 中的 attempt query、owner receipt、progress delta、gate replay、reviewer update、human gate、stop-loss 或 typed blocker |

这些是内容线。后续变更可以只实现其中一条，不需要触碰整个 P2 surface。

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

- generic executor adapter、Codex CLI default selection、Hermes/Claude explicit opt-in executor routing、stage attempt identity、queue state、activity status、retry/dead-letter state、approval/human-gate transport state、provider history、query/projection、framework lifecycle/index/cache metadata。Temporal readiness 是 OPL-hosted production path 的前置条件；local provider 只保留 MAS direct/local diagnostics、OPL dev/CI/offline baseline 和 fixture proof。

MAS 必须持有：

- study truth、runtime health truth、paper progress SLO、owner-route decision、AI reviewer verdict、publication gate、evidence/review ledgers、canonical manuscript/package authority、terminal attach owner gate 和 MAS action receipts。

MAS sidecar/dispatcher/readiness 只能表达 OPL executor requirement 或接收 OPL receipt。`executor_kind` 的 MAS-owned 支持面保持 `codex_cli_default`，并且仅用于 standalone diagnostics；Hermes scheduler / hosted runtime 文字统一按 optional diagnostics/provenance 或 `retire_after_parity` 处理。

Provider attempt completion、queue hydration 或 worker liveness 只是支撑证据。只有 MAS owner surfaces 显示 artifact delta、gate owner progress、AI reviewer judgment update、route decision、stop-loss、human gate 或 typed blocker 时，才算 paper progress。

## 验证

P2 证据按层级判断：

1. Focused MAS sidecar/export/dispatch tests 和 forbidden-write tests；
2. OPL provider attempt/queue/signal/query tests；
3. Direct MAS skill path 与 OPL-hosted path 的 receipt equivalence；
4. guarded apply 前先做 real paper-line read-only soak；当前 DM002/DM003/Obesity 已满足该前置条件；
5. guarded apply evidence 必须写明 attempt id、MAS owner receipt、idempotency key、source fingerprint、source refs、artifact delta / blocker 和 no-forbidden-write proof；
6. 退役验证必须证明无 default CLI/MCP/product-entry/skill caller、无 OPL active reference、无 fixture/provenance dependency，并有 replacement diagnostic/history link。

Docs-only P2 更新需要 `git diff --check` 和 link/path spot check。Contract/runtime 更新需要 focused tests 加 repo-native verification。

## 历史内容处置

上一版 P2 长文档包含完整 module matrix、TypeScript language rationale、target phases、developer checklist、open risks 和详细 cleanup candidates。它已经归档为 full record。

需要 provenance 和实施细节时读取归档。当前规划和执行应从本文的活跃内容 lane、分类规则和优先级开始。
