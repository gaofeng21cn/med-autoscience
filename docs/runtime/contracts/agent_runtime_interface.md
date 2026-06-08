# Agent Runtime Interface

Owner: `MedAutoScience`
Purpose: `agent_runtime_entry_and_boundary`
State: `active_runtime_support`
Machine boundary: 本文是人读 runtime contract support。可执行 runtime truth 继续归 machine-readable contracts、source、tests、CLI/read-model output、runtime ledgers、OPL current-control / provider attempt refs、MAS owner receipts 和 typed blockers。

这份文档写给 `Codex` 等 Agent、内部技术协作者，以及需要审阅 Agent 行为的人。它属于 `docs/runtime/` active support 层，不是默认公开入口；若未来提升为公开入口，先更新 `docs/public/` / `docs/product/` 的 owner 文档与核心五件套。

## 当前结论

`MedAutoScience` 是独立 medical research domain agent，也是 OPL-compatible package。Agent 通过 MAS 稳定入口推进医学研究；OPL/Temporal 持有默认 hosted runtime substrate；MAS 持有医学 truth、owner receipt、typed blocker 和最小 authority functions。

当前 repo-tracked 运行拓扑固定为：

| layer | 当前 owner | 当前职责 |
| --- | --- | --- |
| Domain entry / authority | `MedAutoScience` | study truth、stage semantics、publication route、source readiness、quality gate、artifact/package authority、publication-route memory decision、owner receipt、typed blocker、safe action refs。 |
| Generic runtime substrate | `OPL provider-backed stage runtime` / Temporal | stage attempt、queue、wakeup、retry/dead-letter、resume、human-gate transport、provider query、worker residency、generic transition runner、operator projection。 |
| Generated / hosted surfaces | OPL generated shell + MAS domain handler target | CLI/MCP/Skill/product-entry/status/workbench descriptor、allowlisted task dispatch、refs-only projection。 |
| Product projection | Progress Portal / `study-progress` / OPL App workbench | 只读展示 runtime status、owner route、blocker、freshness 和 drilldown refs；不裁决 publication readiness。 |

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能通过 OPL 显式接入，且只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。Hermes 只可指外部 runtime 项目 / 服务、显式 proof lane 或历史 provenance。它们都不是 MAS 默认 backend、runtime truth、study truth、session owner、provider truth 或 artifact authority。

## Formal Entry

当前 formal-entry matrix：

| entry | 当前读法 |
| --- | --- |
| `CLI` | 默认正式入口。 |
| `MCP` | 协议层，不改写 CLI-first 语义。 |
| `controller` | 内部控制面，不与 CLI/MCP 并列为对外 formal entry。 |
| product-entry manifest / status | generated/hosted companion surface，只暴露 guardrail、entry、projection 和 handoff refs。 |

Product-entry contract 的当前执行真相：

- MAS 自己不直接打模型。
- family 默认执行器正式名称是 `Codex CLI`，执行模式是 `autonomous`，model / reasoning 继承本机 Codex 默认。
- `chat-only executor` forbidden。
- `Hermes-Agent` 备选执行路线只有在显式 hosted/runtime target 接入时才可用，且必须满足 full agent loop guardrail。
- 默认执行路径不得把 `MedDeepScientist` 重新暴露为 public executor backend。

## Execution Handles

Agent 不应把所有运行身份混写成一个 run id。当前至少区分：

| handle | 含义 |
| --- | --- |
| `program_id` | repo / program-level control-plane 或 report-routing 指针。 |
| `study_id` | study 聚合根身份，对应 study-owned surfaces。 |
| `quest_id` | OPL/MAS handoff 下的研究运行身份；attempt lifecycle 归 OPL，MAS 只持 domain refs。 |
| `active_run_id` | 当前 live execution 的细粒度执行句柄，只在 live execution / runtime audit 场景使用。 |

Canonical durable surfaces 包括：

- `runtime_binding.yaml`
- `progress_projection`
- `domain_health_diagnostic`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `studies/<study_id>/artifacts/controller/gate_clearing_batch/latest.json`
- `studies/<study_id>/artifacts/runtime/health/latest.json`
- `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `artifacts/runtime/domain_authority_refs.sqlite`
- `artifacts/runtime/lifecycle_migration/*`
- `runtime/quests/<quest_id>/` materialization manifest
- `runtime/restore_index/*`

这些 surfaces 的读法：

- `publication_eval/latest.json` 和 `controller_decisions/latest.json` 继续是 study-owned truth surface。
- runtime health、domain health diagnostic、escalation record 和 progress projection 是 diagnostic / projection surface，不替代 current owner ticket。
- Git history、Git diff/log、workspace root Git、quest `.git`、worktree list、retired lifecycle SQLite 或 recovery-intent snapshots 不作为默认 runtime status surface。
- Agent 查状态和做 lifecycle 操作时优先读 OPL current-control、MAS file authority、macro state / owner route、domain authority refs index、migration ledger、quest manifest 和 restore index。

## Stable Runtime Entries

用户和 Agent 当前可见的启动与监督入口：

| task | entry |
| --- | --- |
| repo 主线阶段 / 缺口 | `mainline-status` |
| repo 阶段详情 | `mainline-phase --phase <current|next|phase_id>` |
| workspace cockpit | `workspace-cockpit --profile <profile>` |
| durable study task intake | `submit-study-task --profile <profile> --study-id <study_id> --task-intent "<intent>"` |
| 正式启动或续跑 | `launch-study --profile <profile> --study-id <study_id>` |
| 人话进度投影 | `study progress --profile <profile> --study-id <study_id>` |
| MAS refs 刷新 | `runtime domain-health-diagnostic --runtime-root <runtime_root> --profile <profile> --request-opl-stage-attempts --dry-run` |
| product companion | `product-entry-status --profile <profile>` / `product-entry-manifest --profile <profile>` |

Workspace-local Progress-first 监控薄入口：

- `ops/medautoscience/bin/study-progress <study_id> --format json`
- `ops/medautoscience/bin/study-state-matrix --format json`

`progress-projection` workspace wrapper 与 CLI command 已退役；文档、脚本和自动化必须使用 `study-progress --format json`。

OPL `current_control_state` / provider attempt ledger 持有 scheduler lifecycle、provider liveness、attempt、retry/dead-letter 和 operator runtime projection。MAS 不再提供 `runtime-supervision-*` compatibility CLI，不再把 workspace-local LaunchAgent / systemd / cron / docker service 写成 active runtime option。

## Agent Usage Rules

Agent 调用接口时遵守以下顺序：

1. 先读状态，再做变更。
2. 优先使用平台稳定入口，不直接改底层状态文件。
3. 不直接调用 external Hermes daemon / repo / workspace surface 发起研究流程，除非当前 profile 显式进入 hosted target 诊断。
4. 不直接调用 `MedDeepScientist` daemon HTTP API，不把 `MedDeepScientist` UI / CLI 当成研究入口。
5. 所有正式研究推进经 MAS controller / domain handler 产生 DomainIntent、owner route、owner receipt 或 typed blocker，再由 OPL hydrate stage attempt。
6. 变更数据资产时使用对应 policy / CLI mutation 入口；不把自由文本状态塞进 registry，也不绕过 release contract。

低层数据资产、workspace bootstrap 和 profile 命令不在本文重复维护。当前入口读：

- workspace 接入与部署：[bootstrap README](../../../bootstrap/README.md)
- workspace 架构：[Workspace architecture](../../references/workspace/workspace_architecture.md)
- 数据资产策略：[Data asset management](../../policies/study-workflow/data_asset_management.md)
- 默认研究场景：[Study archetypes](../../policies/study-workflow/study_archetypes.md)
- 研究路线偏置：[Research route bias policy](../../policies/study-workflow/research_route_bias_policy.md)
- controller 与内部能力：[Controllers](../control/controllers.md)
- managed study runtime：[Study runtime orchestration](../control/study_runtime_orchestration.md)
- MAS runtime owner boundary：[Runtime boundary](./runtime_boundary.md)
- runtime handle / durable surface：[Runtime handle and durable surface contract](./runtime_handle_and_durable_surface_contract.md)
- stage route contract：[MAS stage route contract](./stage_route_contract.md)
- domain-handler provider 与 figure routes：[Domain handler figure routes](../../delivery/medical-display/contracts/domain_handler_figure_routes.md)

## Third-Party Agent Assets

当前对外按兼容消费来表达的 Agent 包括 `Codex`、`Claude Code`、`OpenClaw`。如果需要把入口契约交给受控 Agent 或内部技术协作者，优先使用：

- stage route contract：[stage_route_contract.md](./stage_route_contract.md)
- 机器可读镜像：[stage_route_contract.yaml](../../../templates/stage_route_contract.yaml)
- `Codex` 入口模板：[medautoscience-entry.SKILL.md](../../../templates/codex/medautoscience-entry.SKILL.md)
- `OpenClaw` 入口模板：[medautoscience-entry.prompt.md](../../../templates/openclaw/medautoscience-entry.prompt.md)

`Claude Code` 不单独维护专有入口模板，默认复用 `Codex` 这一套入口契约。

这些资产只负责声明 entry actions、研究 routes、governance routes、auxiliary routes、轻量专项模式和正式 managed 模式的升级边界。它们不授权外部 executor 越过 MAS owner surface，也不把 OPL queue / provider completion / descriptor ready 写成 publication-ready。

## Frontend / Product Projection Contract

Product-entry、workspace cockpit、Progress Portal 和 OPL App workbench 只能做 projection / drilldown / handoff：

- `study-progress` 负责用户可读阶段摘要、当前任务摘要、progress freshness、当前阻塞、下一步、`intervention_lane`、`recommended_command(s)` 和 `recovery_contract`。
- `workspace-cockpit` / `launch-study` / `product-entry-status` 消费 `study-progress.recovery_contract`、`recommended_command` 和 `intervention_lane`，不得各自再猜恢复路径。
- 质量硬阻塞、human decision gate、runtime recovery、workspace supervision gap 和 study progress gap 必须结构化投影，不能压平成泛化 `study_blocked`。
- Product projection 不能写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper body、memory body、artifact body 或 MAS owner receipt authority。

## 不允许写成

- OPL provider proof、queue completion、descriptor ready、test pass 或 workbench 可见性等于 MAS paper closure、publication-ready、domain-ready、artifact mutation authorization 或 `current_package` 更新。
- MDS / DeepScientist / Hermes / non-default executor proof lane / workspace archive 是 MAS 默认 active runtime owner。
- workspace-local LaunchAgent / systemd / cron / docker service 是产品态常驻路径或替代 scheduler。
- `runtime_transport`、`mas_runtime_core*`、旧 lifecycle writer、旧 alias、legacy wrapper 或 compatibility facade 是 current active caller。
- Markdown 文档路径、章节或文案是机器接口。机器面必须使用 schema、JSON、CLI/API payload、manifest、durable semantic ID 或 generated artifact。

## 历史指针

以下材料只作 provenance，不能恢复为 current runtime owner 或 active backlog：

- [Runtime history archive](../../history/runtime/README.md)
- [Program history archive](../../history/program/README.md)
- [Hermes backend continuation board](../../history/program/hermes_backend_continuation_board.md)
- [Hermes backend activation package](../../history/program/hermes_backend_activation_package.md)
- [Upstream Hermes-Agent fast cutover board](../../history/program/upstream_hermes_agent_fast_cutover_board.md)
- [MedDeepScientist deconstruction map](../../references/med-deepscientist/med_deepscientist_deconstruction_map.md)
- [MedDeepScientist upstream intake](../../references/med-deepscientist/upstream_intake.md)
- [External runtime dependency gate](../../policies/runtime-governance/external_runtime_dependency_gate.md)
- [Manual runtime stabilization checklist](../../policies/runtime-governance/manual_runtime_stabilization_checklist.md)

当前 runtime truth 从 [runtime README](../README.md)、[runtime boundary](./runtime_boundary.md)、[study runtime control surface](../control/study_runtime_control_surface.md)、[study runtime orchestration](../control/study_runtime_orchestration.md)、[study progress projection](../projections/study_progress_projection.md) 和 live MAS/OPL outputs 读取。
