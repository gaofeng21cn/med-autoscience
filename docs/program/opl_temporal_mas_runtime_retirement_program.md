# OPL Temporal MAS Runtime Retirement Program

Status: `active framework enabler`
Date: `2026-05-11`
Owner: `MedAutoScience Runtime OS + OPL Runtime Manager integration boundary`
Purpose: `development_plan`
Machine boundary: this is a human-readable program plan. Machine truth must remain in MAS controller/runtime surfaces, OPL provider contracts, sidecar receipts, attempt ledgers, durable schemas, CLI/API behavior, and live workspace evidence.
Content lifecycle role: P2 framework enabler. This document owns MAS-side alignment with the OPL Codex-first, stage-led framework and provider-backed runtime; MAS paper quality, study truth, and artifact authority remain in MAS owner surfaces.

Master entry: OPL family framework 的总开发入口是 `/Users/gaofeng/workspace/one-person-lab/docs/references/runtime-substrate/opl-stage-led-agent-framework-roadmap.zh-CN.md`。OPL 在这里指 Codex-first、stage-led 的完整智能体运行框架，可作为 MAS 外部依赖；`Stage` 是大型任务步骤，`Codex CLI` 是 stage 内默认 concrete executor 和最小执行单元。本文是 MAS domain-side runtime retirement 子计划，负责把 MAS 内部 scheduler / watchdog / MDS / Hermes / Portal/Console 等 runtime-adjacent surface 按 OPL master plan 迁移、降级或退役。

## 结论

本文是 P2。P2 的任务是把 P0 论文自治目标依托到 OPL Codex-first、stage-led framework：MAS 作为医学研究 domain agent 暴露 stage descriptor、sidecar export/dispatch、receipt schema、projection builder、artifact locator 和 authority refs；OPL 提供 durable stage attempt、queue、wakeup、retry/dead-letter、approval/human gate transport、provider receipt、projection、shared lifecycle/index primitives。

当 OPL framework 和 Temporal-backed provider 通过真实 MAS paper-line soak 后，MAS 内部一批“在线底座 / watchdog / scheduler / daemon 兼容”能力进入退役或降级。目标形态是 MAS 专注医学研究 domain agent 职责：研究真相、质量判断、owner route、artifact authority 和受控 domain action；OPL/Temporal 持有长期在线、stage attempt、wakeup、retry、signal/query、approval、dead-letter、operator projection 和跨 domain runtime。

按 OPL 新定位，MAS 已验证的 SQLite 持久化、file lifecycle、artifact index、retention、restore proof、migration ledger 和 workspace lifecycle 经验，应拆成两层：`framework_generic` 能力上收到 OPL framework，`mas_domain_specific` truth 留在 MAS。MAS 不应长期独自维护其他 domain 也需要的智能体运行外围能力。

当前确定状态：

- OPL Temporal provider code 已落地，包含 Temporal TypeScript SDK、`StageAttemptWorkflow`、activity、signal/query、CLI start/query/signal 和 provider receipt。
- 真实 Temporal server/worker deployment、真实 Codex long-running activity runner、MAS paper-line soak 与 cutover 仍是 P2 当前工作。
- MAS 的 `local` supervision scheduler、one-shot `runtime-supervisor-reconcile`、workspace-local Portal / Live Console 在过渡期作为 local diagnostics、fallback 和 evidence surface 保留。
- P2 的完成证据是 direct MAS skill path 与 OPL-hosted path 共享 MAS owner receipts，并且真实 provider soak 证明 OPL 只持有 framework receipt/ref/projection，不写 MAS forbidden truth surfaces。

目标 owner split 固定为：

- `OPL Runtime Manager / Temporal provider`：durable stage attempt、queue、wakeup、retry/dead-letter、human gate signal、query/projection、provider receipt、attempt history、notification / approval transport。
- `MAS`：study truth、RuntimeHealth / StudyTruth reducer、paper progress SLO、owner-route reconcile、AI reviewer、publication gate、evidence/review ledger、canonical manuscript/package authority、sidecar export/dispatch owner receipt。
- `OPL framework lifecycle primitives`：lifecycle ledger、artifact locator/index、retention policy、restore proof、migration ledger、workspace lifecycle metadata、attempt receipt 和 provider cache cleanup；这些只保存 refs/proof/receipt，不保存医学 truth。
- `Codex CLI`：默认 concrete executor，作为 Temporal Activity 或 MAS direct path 内的执行器；不持有 domain truth。
- `Hermes`：迁移期 `hermes_legacy` provider、optional executor/proof lane 或 compatibility diagnostic。
- `MDS / DeepScientist`：historical fixture、explicit archive import、backend audit、parity oracle；不作为默认 runtime 或第二 owner。

## 执行语言结论

从智能体框架本身出发，OPL family runtime 的框架层执行语言应统一到 `TypeScript`，domain agent 内部执行语言不强制统一。

统一范围：

- OPL provider、stage attempt workflow、queue、signal/query、approval、dead-letter、attempt ledger、App/API bridge、family action catalog 和跨仓 adapter 应以 `TypeScript` 为主。
- MAS / MAG / RCA 暴露给 OPL 的 contract、sidecar export/dispatch、stage descriptor、receipt schema / refs、projection builder / refs 和 artifact locator contract 必须 machine-readable，并能被 OPL `TypeScript` 层直接校验和索引。
- `Codex CLI` 仍是 stage 内默认 concrete executor；在 OPL/Temporal 路线里，它应表现为 Activity 或 domain sidecar dispatch 的执行对象，不持有 truth。

不统一范围：

- MAS 医学统计、数据分析、文献/引用、figure/table、稿件产物、Python scientific stack 继续留在 `Python` domain package。
- RCA 的 Office/PPT native helper 可以继续用 `Python`，但 route、contract、review/export gate 与服务边界归 `TypeScript`。
- MAG 若主要是 authoring / contract / product-entry，可逐步向 OPL `TypeScript` contract 层对齐，但 grant truth 和写作执行不因语言迁移改变 owner。
- `Go` / `Rust` 只适合极少数 native helper、indexer、packaging 或 performance-critical tool，不作为 OPL stage orchestration 主语言。

理由：

- Temporal 的 Workflow / Activity / Signal / Query 模型天然对应 OPL 的 `stage_attempt / Codex activity / human gate signal / progress query`，而 OPL App、CLI、MCP/HTTP bridge 和 package/runtime manager 已经更贴近 Node/TypeScript 生态。
- 医学研究 domain 的真实计算生态仍在 Python；把 MAS 内部强迁到 TypeScript 会降低统计、数据分析、文献处理和 scientific package 的可维护性。
- OPL 是框架，不是领域大脑。统一语言的目的应是统一 durable orchestration、typed contracts、adapter 和 visibility，而不是把 domain truth 重写成同一种语言。

外部工程参考：

- Temporal TypeScript SDK 把长任务拆成 Workflow、Activity、Signal、Query 和 retry/replay 边界；这支持 OPL 把 stage attempt 编排留在 TypeScript 层，而把 MAS sidecar dispatch 当作 Activity。
- LangGraph 的 persistence / checkpoint / thread 模型说明 agent state 应持久化、可恢复、可从 checkpoint 继续；这对应 OPL attempt ledger / provider history，而不是 MAS paper truth。
- OpenAI background-mode / async execution 模式强调长任务应可轮询、可继续、可返回 durable status；这支持 OPL provider 做 pollable execution，不要求 MAS 内部重写为在线 daemon。
- Pydantic AI durable execution 与 Temporal integration 说明 typed state / durable task 边界比自由文本日志更可靠；这支持 MAS/OPL 用 JSON schema、typed receipt 和 idempotency key 连接。

开发纪律：

- 新增 OPL/framework-level runtime 能力默认先做 `TypeScript` contract / provider / adapter。
- 新增 MAS research / publication / statistical / evidence 能力默认留在 MAS `Python` owner surface。
- 跨语言边界只能通过 JSON schema、typed receipt、CLI/API/MCP command 或 sidecar export/dispatch；不得通过 Markdown、日志文本、路径惯例或隐式 import 当机器接口。
- 任何语言迁移都必须证明 owner 不变、truth surface 不变、direct skill path 与 OPL-hosted path 等价。

## Boundary

本 program 的边界按 owner 固定：

| owner | authority |
| --- | --- |
| `MAS` | 独立医学研究 domain agent；持有 study truth、publication quality、current package、evidence/review ledgers、artifact gate、controller decisions 和 runtime owner receipt。 |
| `OPL` | framework runtime owner；持有 provider receipt、attempt ledger、queue/wakeup/retry/dead-letter、approval/human gate transport、projection 和 lifecycle/index primitives。 |
| `Temporal-backed provider` | P2 目标生产 substrate；承载 durable workflow、activity retry/timeout、signal/query、history replay 和 recovery proof。 |
| `Hermes / MDS / old local services` | archive、provenance、compatibility、legacy/optional proof 或 diagnostic 语境；默认 MAS 运行路径和目标在线 substrate 都回到 MAS + OPL provider 边界。 |

MAS 的 SQLite runtime authority 只按 `framework_generic` / `mas_domain_specific` 分类上收经验；OPL 上收 lifecycle metadata、artifact locator、retention receipt、restore proof 和 migration ledger 等 framework primitives。Temporal provider 通过真实 soak 前，MAS 本地诊断和 fail-safe 入口保留。

## 退役原则

每个 MAS runtime-adjacent 模块都按四类处理：

| class | meaning | closeout rule |
| --- | --- | --- |
| `retain_in_mas` | MAS domain authority 或 owner surface | 保留，必要时改名/收口，不能迁到 OPL。 |
| `move_to_opl_provider` | 通用长期在线 / queue / attempt / signal 能力 | 迁到 OPL provider abstraction，Temporal 落地后由 workflow/activity/signal/query 表达。 |
| `degrade_to_local_diagnostics` | 过渡期本地诊断、one-shot、fallback | 保留显式命令，不作为 Full online readiness 或默认产品 runtime。 |
| `retire_after_parity` | 旧兼容、legacy vocabulary、重复 UI/manager | 满足无默认调用、无 public surface 引用、无 fixture 必需、已有替代证据后删除或归档。 |
| `lift_to_opl_framework` | MAS 已验证且可跨 domain 复用的运行外围能力 | 先归类为 `framework_generic`，再迁到 OPL shared schema/provider/helper；MAS 只保留 domain truth refs。 |

退役必须有 evidence gate：

- OPL provider 已能创建、查询、恢复、重试、dead-letter MAS stage attempt。
- MAS direct skill path 与 OPL-hosted path 对同一 study owner route 结果等价。
- MAS sidecar export 生成的 `pending_family_tasks[]` 能被 OPL queue hydration 幂等消费。
- MAS sidecar dispatch 能回到 MAS owner chain 写 receipt，并证明未写 forbidden truth surfaces。
- 至少一条真实 MAS paper line 完成 read-only 或 guarded apply soak，能看到 provider attempt、Codex/domain sidecar、typed closeout、MAS owner receipt、progress delta / human gate / stop-loss；artifact delta / gate replay 仍只能由 MAS owner surface 授权。
- 本地 scheduler 退役不会降低 direct MAS diagnostics、offline development、explicit one-shot recovery 和 workspace evidence 可读性。
- MAS SQLite/file lifecycle 经验已经完成 `framework_generic` / `mas_domain_specific` 分类，并有 OPL shared primitive 或明确保留理由。
- MAS skeleton mapping 能把现有 stage、prompt/skill、knowledge、quality gate、contract、sidecar、receipt schema、projection builder 和 artifact locator contract 映射到 OPL standard domain-agent skeleton。

## 模块处理矩阵

### 1. Scheduler / watchdog / online substrate

| current surface | target class | target owner | reason |
| --- | --- | --- | --- |
| `supervision_scheduler.py` façade | `degrade_to_local_diagnostics` | MAS | 作为 local / one-shot diagnostics 保留；Full online runtime 迁到 OPL provider。 |
| `supervision_scheduler_parts/local_adapter.py` | `degrade_to_local_diagnostics` | MAS | macOS LaunchAgent 只保留为 local fallback 和 migration proof；Temporal ready 后不作为默认 readiness。 |
| `hermes_supervision.py` / `hermes_supervision_parts/*` | `retire_after_parity` plus `hermes_legacy` | OPL legacy provider / MAS diagnostic | Hermes-first default 已 supersede；保留 compatibility 直到 Temporal soak。 |
| `runtime-supervision-status` | `degrade_to_local_diagnostics` | MAS + OPL projection | 输出应明确 local diagnostics / provider readiness split。 |
| `runtime-ensure-supervision` | `degrade_to_local_diagnostics` | MAS | 继续可修复 local scheduler；不能表示 Full online ready。 |
| old `systemd|cron|launchd|docker` managers | `retire_after_parity` | MAS cleanup evidence only | 内部 controller 只保留 direct cleanup evidence；公开 CLI / workspace help 不再暴露这些 manager 作为可选项。 |
| `runtime_watch.run_watch_loop` long loop mode | `retire_after_parity` | MAS diagnostics only | 长期 loop 应由 provider schedule/attempt 表达；MAS 只保留 one-shot tick。 |
| MAS per-run worker wrapper heartbeat | `retain_in_mas` with provider projection | MAS Runtime OS | 它证明 Codex child / artifact delta / turn completion；Temporal Activity heartbeat 可消费但不能替代 MAS runtime truth。 |

目标状态：

```text
Temporal schedule/workflow
  -> OPL stage_attempt
  -> Codex activity or MAS sidecar dispatch activity
  -> MAS owner receipt / runtime truth / artifact delta
  -> OPL query/projection reads refs only
```

### 2. Supervisor / owner-route / paper progress

| current surface | target class | target owner | reason |
| --- | --- | --- | --- |
| `runtime_supervisor_scan.py` | `retain_in_mas` | MAS controller | 读取 MAS truth 并生成 owner route，不能外移。 |
| `runtime_supervisor_consumer.py` | `retain_in_mas` | MAS controller | 传播 owner route / request packet，不能让 OPL重算 owner。 |
| `runtime_supervisor_dispatch_executor.py` | `retain_in_mas` | MAS controller | 执行 MAS owner-authorized action，写 MAS receipt。 |
| `runtime_supervisor_reconcile.py` | `retain_in_mas` | MAS controller | `scan -> consume -> execute-dispatch -> rescan` 是 domain reconcile。 |
| `paper_progress_reconciler.py` | `retain_in_mas` | MAS Paper Progress SLO | 判断 meaningful artifact delta，是 MAS 用户旅程 SLO。 |
| `paper_work_unit_outbox` / receipt SQLite sidecar | `retain_in_mas` | MAS Runtime OS / controller | 幂等和 source fingerprint 属 domain action transaction。 |
| `owner_callable_registry` / owner route | `retain_in_mas` | MAS | OPL 只能 transport，不能决定医学 next owner。 |

目标状态：OPL/Temporal 只把 `runtime_supervisor/reconcile-apply` 作为 typed activity 派发给 MAS；MAS 仍执行完整 owner-route gate，并返回 accepted/blocked/no-op/human-gate receipt。

### 3. Sidecar bridge / OPL handoff

| current surface | target class | target owner | reason |
| --- | --- | --- | --- |
| `sidecar_family_adapter.export_family_sidecar` | `retain_in_mas` and harden | MAS | MAS 显式授权 OPL queue 的唯一任务来源。 |
| `sidecar_family_adapter.dispatch_family_task` | `retain_in_mas` and harden | MAS | 接受 OPL typed task 后回到 MAS owner chain。 |
| `pending_family_tasks[]` | `move_to_opl_provider` as queue input | OPL queue / MAS source | MAS 生成，OPL 入队、去重、重试、dead-letter。 |
| `family_runtime_supervision` projection | `move_to_opl_provider` as read-only index | OPL projection | OPL 展示 provider/domain freshness，不写 MAS truth。 |
| `mas_opl_runtime_workbench_projection` | `move_to_opl_app_projection` | OPL App consumes / MAS produces | UI 工作台消费 MAS projection，不能成为 authority。 |

目标状态：MAS sidecar 是 OPL/Temporal 到 MAS 的唯一自动推进桥。OPL 不从 MAS read-only projection 自行推断新 task；只消费 MAS 显式导出的 `pending_family_tasks[]`。

### 4. Progress Portal / Live Console / terminal

| current surface | target class | target owner | reason |
| --- | --- | --- | --- |
| Progress Portal static/local service | `degrade_to_local_diagnostics` | MAS Product Projection | 保留 fallback 和 evidence；主产品体验迁到 OPL App Runtime Workbench。 |
| Live Console local UI | `degrade_to_local_diagnostics` | MAS Product Projection | 保留 debug/fallback；OPL App 统一展示。 |
| terminal attach gate / token / lease / audit | `retain_in_mas` | MAS Runtime OS | terminal 输入属于 runtime owner action，不能让 OPL 直接写。 |
| terminal/log read-only tail | `move_to_opl_app_projection` | OPL App consumes | OPL 可展示 transcript/log refs。 |
| pause/resume/stop buttons | `split` | OPL transport + MAS action owner | OPL 负责 UI/confirmation，MAS 写 receipt。 |

目标状态：OPL App 是用户主工作台；MAS local HTML 是 fallback。所有 action 都走 MAS owner endpoint / receipt。

### 5. Runtime transport / MDS / legacy compatibility

| current surface | target class | target owner | reason |
| --- | --- | --- | --- |
| `runtime_transport/med_deepscientist*` | `retire_after_parity` | MAS provenance / backend audit | 保留 explicit backend audit、archive import 和 parity oracle；删除默认路径。 |
| `runtime_transport/hermes.py` | `retire_after_parity` | OPL legacy provider | Hermes 仅 compatibility/proof。 |
| `hermes_runtime_contract.py` | `retire_after_parity` | OPL provider readiness docs | 不再作为 MAS future readiness truth。 |
| legacy restore/import diagnostics | `degrade_to_local_diagnostics` | MAS archive/provenance | 只服务旧 workspace 恢复，不进入默认 runtime。 |
| old path readers / ignore / compat guards | `retire_after_parity` | MAS | 无 fixture/restore 依赖后删除。 |

目标状态：MDS/DeepScientist 留作 source provenance、historical fixture、explicit archive import、backend audit 和 parity oracle。默认 runtime/import path 统一解析到 MAS-owned surfaces。

### 6. Domain truth / quality / artifact authority

MAS authority surfaces:

- `StudyTruthKernel`
- `RuntimeHealthKernel`
- `study_macro_state`
- `study_runtime_status`
- `runtime_watch` truth output
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `evidence_ledger`
- `review_ledger`
- AI reviewer workflow
- publication gate
- canonical manuscript/package loop
- submission package / current package authority
- artifact rebuild proof
- route decision / stop-loss / human gate owner

OPL/Temporal 可以保存 refs、attempt receipt、activity result summary 和 provider history；它不能保存或生成这些 truth。

### 7. SQLite / file lifecycle / restore proof

| current surface | target class | target owner | reason |
| --- | --- | --- | --- |
| runtime lifecycle SQLite schema patterns | `lift_to_opl_framework` | OPL framework primitive | lifecycle ledger、attempt metadata、restore proof、migration ledger 是跨 domain 外围能力。 |
| artifact locator / freshness / retention projection | `lift_to_opl_framework` | OPL artifact/lifecycle layer | MAG/RCA 也需要 artifact index、retention 和 cleanup receipt；不应由 MAS 私有实现重复演化。 |
| restore proof archive and migration ledger pattern | `lift_to_opl_framework` | OPL lifecycle layer plus domain source refs | restore/provenance 是框架级安全能力；domain artifact 内容和 truth refs 仍在 MAS。 |
| study-specific paper artifacts and ledgers | `retain_in_mas` | MAS Artifact OS / Quality OS | manuscript、package、evidence/review ledger、publication/controller truth 不得迁出。 |
| current workspace legacy compatibility readers | `retire_after_parity` or `degrade_to_local_diagnostics` | MAS provenance / OPL skeleton migration audit | 有 restore/provenance replacement 后继续删除或归档。 |

目标状态：OPL 提供 lifecycle / artifact / retention / restore primitive；MAS 通过 sidecar/projection 暴露 study-owned refs 和 action receipt。OPL cleanup 只能清理 framework-owned cache/index/receipt/provider state；domain artifact 删除、压缩或重建必须走 MAS owner receipt。

### 8. Standard domain-agent skeleton

MAS 的目标接入形态应映射到 OPL standard skeleton：

```text
agent/
  stages/
  prompts/
  skills/
  knowledge/
  quality_gates/
contracts/
  runtime/
    sidecar/
    projection_builders/
    lifecycle_adapters/
docs/
```

迁移纪律：

- 先做 skeleton mapping，不直接移动目录。
- `agent/stages` 映射现有 `agent_entry_modes.yaml`、Stage-Led Autonomy route contract、bounded-analysis policy 和 route decision surface。
- `agent/prompts` / `agent/skills` 映射 MAS app skill、stage prompt、review/repair prompt 和 Codex entry policy。
- `agent/knowledge` 映射 stage knowledge packet、memory closeout packet、memory write router、recall index、literature/reference context，以及 natural-language-first publication route memory。`publication_route_memory_pack`、`publication_route_memory_apply_receipt` 和 writeback receipts 属 MAS workspace/runtime root；repo 只保存 schema、seed fixture 和 locator contract。该层只做检索、注入、provenance、freshness 和 writeback routing；不得把论文套路做成 OPL 或 MAS 的机械 recipe engine。
- `agent/quality_gates` 映射 AI reviewer、publication gate、reporting guideline、claim-evidence/display-to-claim gates。
- `runtime/sidecar` / `runtime/projection_builders` / `runtime/lifecycle_adapters` 映射 sidecar export/dispatch、Progress Portal、Live Console、OPL workbench projection，以及 workspace/runtime artifact locator、retention 和 restore-proof adapter。
- workspace / runtime artifact root 继续保存 MAS study truth、publication eval、controller decisions、owner receipts、论文包、中间产物和最终交付物；开发仓 skeleton 只保存 schema、adapter、builder 和 locator contract。
- `artifacts` 保持 MAS-owned truth 和最终论文产物 authority。

物理重组门槛：

- direct MAS skill path 和 OPL-hosted path 语义等价。
- OPL skeleton validator 能证明 required refs 齐全。
- restore/provenance readers 不依赖旧目录名作为唯一入口。
- focused sidecar / stage / portal / publication gate / artifact tests 和 `make test-meta` 通过。
- 真实 paper-line read-only 或 guarded soak 未出现 path regressions。

## Target Development Phases

执行顺序必须跟 OPL master plan 对齐：

1. OPL master P1 已证明 Temporal provider core 可在 repo/test 面表达 workflow/activity/signal/query；后续先补真实 Temporal worker/server deployment 与 Codex long-running activity runner。
2. OPL master P2b 先把 MAS lifecycle/file-management 经验抽象为 framework primitive，MAS 侧完成 `framework_generic` / `mas_domain_specific` 清单。
3. OPL master P2c 冻结 standard domain-agent skeleton，MAS 先做 mapping/adapters，再考虑物理目录重组。
4. MAS 只在 sidecar export/dispatch、owner receipt、stage closeout 和 forbidden-write gate 已对齐后进入真实 paper-line guarded soak。
5. 真实 soak 通过后，才把 MAS local scheduler、Hermes adapter、old manager aliases、MDS runtime transport、duplicated Portal/Live Console wording 和非标准目录入口继续物理退役。
6. 任何 MAS 清理不得削弱 direct MAS skill path、offline diagnostics、restore/provenance reader 或 MAS-owned publication/quality/artifact authority。

### Phase 0: Inventory and wording freeze

目标：先阻止继续扩大 MAS 内部在线底座。

交付：

- 本 program 成为 OPL/Temporal 成熟后 MAS runtime 退役的 active plan。
- MAS docs 明确 OPL Temporal provider code 已落地，但真实 live provider cutover / MAS scheduler 替换未完成，不能把目标状态写成现实状态。
- OPL/framework-level 新 runtime 能力默认采用 TypeScript；MAS domain research 能力继续采用 Python owner surface，通过 typed contract 连接。
- `runtime_supervision_loop`、`supervision_scheduler_contract`、`status` 后续更新时必须把 local scheduler 写成 diagnostics / transitional fail-safe。
- 搜索 Hermes-first、watchdog、scheduler、daemon、LaunchAgent、local service wording，分成 active / legacy / diagnostics / retired。

验收：

- active docs 不再把 Hermes 或 MAS LaunchAgent 写成 Full online target。
- 公开 CLI 不再把已退役 manager 当作可选 runtime path；旧 service 只在内部 cleanup/audit surface 出现。
- 后续新增 MAS runtime 文档必须引用本 program 或 OPL provider plan。

### Phase 1: Contract freeze between OPL provider and MAS

目标：冻结跨仓机器边界，避免 OPL/Temporal 与 MAS 互相写错 truth。

交付：

- `mas_family_sidecar_export` schema 补齐 provider-ready 字段：task kind、dedupe key、source fingerprint、required MAS owner、forbidden writes、human gate boundary。
- `mas_family_sidecar_dispatch_receipt` 明确 accepted / blocked / no-op / human-gate / started-worker / artifact-delta / gate-replay result。
- OPL `stage_attempt` 与 MAS `owner_route` 建立引用关系，但不合并 truth。
- direct MAS skill path 与 OPL-hosted path 使用同一 MAS sidecar / controller receipt。

验收：

- OPL queue hydration 只能消费 MAS `pending_family_tasks[]`。
- OPL dispatch task 请求 forbidden writes 时 MAS fail-closed。
- MAS receipt 可回指 OPL attempt id，但 MAS truth 不依赖 OPL attempt history。

### Phase 2: Temporal provider pilot

目标：让 OPL provider 从已落地 code path 进入真实运行环境，真正承接 MAS stage attempt。

交付：

- 已完成：OPL `temporal` provider 具备 `StageAttemptWorkflow`、Codex / domain sidecar activity、human gate / user instruction / resume signal 和 query surface。
- 待完成：真实 Temporal server/worker deployment 能运行 MAS stage attempt。
- 待完成：Codex activity 从 stub 升级为真实 long-running runner，domain sidecar activity 调用 MAS owner dispatch。
- 待完成：human gate、user modification intake、pause/resume/stop 信号进入真实 MAS revision / gate owner chain。
- Query 返回 attempt status、freshness、blocked reason、MAS source refs。
- Provider history 写 OPL attempt ledger；MAS truth 仍由 MAS 写。

验收：

- Temporal workflow replay 不触发重复 MAS work unit。
- Activity retry 使用 MAS idempotency key / source fingerprint。
- Temporal failure 或 dead-letter 不被 MAS 误读为 publication/quality verdict。

### Phase 3: MAS paper-line guarded soak

目标：用真实 MAS paper line 证明 provider 替代本地 watchdog 后不降级。

交付：

- 选择一条真实 paper line 做 read-only then guarded apply soak。
- OPL 创建 stage attempt，Temporal Activity 调用 MAS sidecar dispatch。
- MAS 执行 owner-route reconcile 或 memory write router，产生 typed closeout receipt、progress delta、gate replay、AI reviewer recheck、human gate、stop-loss 或 typed blocker。
- `paper_soak_memory_apply_proof` 作为 read-only proof surface 连接 OPL attempt、Codex/domain sidecar、typed closeout、MAS receipt 和 progress delta / human gate / stop-loss；它不写真实论文包，不授权 quality，不替代 publication gate。
- OPL App / CLI 能展示 provider attempt、MAS source refs、receipt、next owner 和 blocker。

验收：

- 同一 source fingerprint 不重复启动 worker。
- dry-run 不启动 Codex worker。
- apply 只在 MAS owner route 允许时启动 worker。
- 论文进展以 MAS artifact delta / gate owner 前进 / AI reviewer judgment 为准，不以 provider attempt completed 为准。

### Phase 4: Default online cutover

目标：把 Full online runtime 默认交给 OPL provider。

交付：

- OPL Full readiness 以 configured family runtime provider ready 为准。
- MAS `runtime-ensure-supervision` 默认文案降级为 local diagnostics / one-shot repair。
- MAS workspace bootstrap 不再把 local scheduler install 当成 Full online readiness。
- Progress Portal / workspace cockpit 显示 provider readiness 与 local diagnostics split。
- Hermes adapter 标为 `hermes_legacy`，不作为默认 install/readiness。

验收：

- 新 workspace 通过 OPL online path 可被唤醒、重试、dead-letter、human-gate。
- 没有 OPL provider 时，MAS direct path 报 degraded online readiness，但本地 status/progress 可读。
- local scheduler 不与 provider 双调度同一 workspace。

### Phase 5: Physical retirement and cleanup

目标：删除或归档不再需要的旧面。

候选清理：

- Hermes-first wording、Hermes gateway default readiness、Hermes cron install as target docs。
- MAS old manager aliases：`systemd|cron|launchd|docker` direct manager path。
- Old workspace-local service cleanup scaffolds。
- MDS daemon / runtime transport default import paths。
- Duplicated Portal/Live Console product-primary wording once OPL App workbench is primary.
- Any tests that assert legacy prose or old manager wording instead of durable contract.

删除门槛：

- 无 default CLI/MCP/product-entry/skill surface 引用。
- 无 OPL App / OPL provider active reference。
- 无 fixture/restore/provenance 必需。
- 有 history/provenance replacement 或 explicit diagnostic replacement。
- `scripts/verify.sh`、`make test-meta`、focused runtime/sidecar/provider tests green。

## Required Verification Ladders

Docs-only changes:

- `git diff --check`
- link/path spot check with `rg`
- no Markdown wording tests added

MAS contract changes:

- focused sidecar tests
- focused runtime supervisor/reconcile tests
- focused product-entry / skill catalog tests if command metadata changes
- `make test-meta`
- `scripts/verify.sh`

OPL provider changes:

- OPL provider contract tests
- family runtime queue / attempt tests
- Temporal workflow fixture tests once provider exists
- OPL App projection tests if UI consumes new fields

Real workspace cutover:

- read current `study_progress`, `study_runtime_status`, `runtime_supervision/latest.json`, `publication_eval/latest.json`, `controller_decisions/latest.json`
- run read-only soak before guarded apply
- record active_run_id, owner_route, idempotency key, source fingerprint, receipt path, artifact delta / blocker
- confirm no forbidden truth writes by OPL provider

## Developer Checklist

Before touching MAS runtime-adjacent code:

1. Identify class: `retain_in_mas`, `move_to_opl_provider`, `degrade_to_local_diagnostics`, or `retire_after_parity`.
2. Read current `docs/decisions.md`, `docs/architecture.md`, `docs/status.md`, this program, and OPL Temporal provider plan.
3. If the change affects online behavior, update or validate `sidecar export/dispatch` and OPL provider contracts first.
4. If the change affects quality/publication/artifacts, keep it in MAS owner surfaces.
5. If retiring a legacy path, prove there is no default caller and no fixture/provenance dependency.
6. If updating UI/projection, preserve read-only projection boundary and action receipt boundary.

## Open Risks

- Temporal provider may take longer than MAS cleanup appetite. Until P2/P3 evidence exists, MAS local diagnostics cannot be removed.
- OPL provider history may tempt future code to treat attempt completion as paper progress. Tests and docs must keep MAS artifact delta / gate replay as the only paper progress proof.
- Dual scheduling risk exists during cutover. A workspace must have one primary online scheduler/provider; local scheduler and provider must not both run the same apply tick.
- User-facing UI may hide source refs. OPL App should provide concise default status but always keep source/ref/debug drawer available.
- Legacy compatibility may linger because old studies need restore/provenance readers. Physical deletion should follow restore proof, not aesthetic cleanup.

## Definition Of Done

This program is complete only when:

- Temporal-backed OPL provider has passed real MAS paper-line soak.
- OPL family runtime is the default Full online runtime for MAS wakeup/retry/dead-letter/human gate.
- MAS local scheduler is explicitly diagnostics/fallback only.
- Hermes is `hermes_legacy` or optional executor/proof only.
- MDS/DeepScientist runtime transport is archive/provenance/parity only.
- OPL App is the primary user runtime workbench, while MAS local Portal/Live Console remain fallback/evidence/debug.
- MAS direct skill path and OPL-hosted path converge on the same MAS owner receipts and truth surfaces.
- No OPL/Temporal surface can write or claim authority over MAS study truth, publication judgment, quality gate, current package, evidence/review ledger, or artifact gate.
