# 架构概览

Owner: `MedAutoScience`
Purpose: `architecture_current_truth`
State: `active_current_truth`
Machine boundary: 本文解释 owner split。机器边界以 `contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`、`contracts/generated_surface_handoff.json`、`contracts/action_catalog.json` 与源码为准。

## 目标形态

MAS 是标准 OPL domain agent，不是第二套平台：

```text
MAS declarative pack
  stages / prompts / knowledge / quality gates
  action catalog / schemas / environment requirements
                    |
                    v
OPL generated and hosted surfaces
  CLI / MCP / Skill / product entry / status / workbench
  runtime / StageRun / StateIndex / lifecycle / observability
                    |
                    v
MAS domain-handler targets and minimal authority functions
  medical truth / quality / publication / artifact / memory
  owner receipt / typed blocker / human gate / domain refs
```

canonical id 固定为 `mas`。`med-autoscience` 仅是 repo/package/plugin locator。

## Declarative Medical Research Pack

`agent/` 与机器 contracts 描述：

- 22 个 action 及其 input/output schema；
- stage manifest、prompt、knowledge refs 和 quality gate；
- domain route/profile、projection 与 forbidden-write boundary；
- `analysis-display` 环境需求，包括 R/Bioconductor 依赖声明；
- primary skill 与 Codex plugin carrier 的受控镜像关系。

Pack 只声明需求和能力，不实现通用 transport、installer、workspace bootstrap、runtime shell 或 workbench。

Foundry 系列 policy 只由唯一 OPL Framework 持有。MAS 的 `contracts/foundry_agent_series.json` 是 refs-only consumer contract，只记录 canonical contract refs、policy fingerprint、MAS domain delta 与 false-authority envelope；MAS 不复制 OPL policy body，也不声明本地 Framework 依赖。

Framework Python helper 同样由 OPL 持有。OPL module workflow 在 MAS checkout 维护 `src/opl_framework` carrier；MAS 通过该 namespace 消费，不在 `pyproject.toml` 或 `uv.lock` 声明、安装或锁定 OPL implementation。

## OPL 平台职责

OPL 是 generated/default owner：

- 从 action catalog 生成 CLI、MCP、Skill、product-entry 与 harness；
- 托管 status、workbench、runtime lifecycle、queue、attempt ledger、retry/dead-letter 与 observability；
- 提供 StageRun、StateIndex、storage/lifecycle 与环境准备；
- 传输 human gate、owner answer、receipt/blocker refs；
- 不写 MAS study truth、quality verdict、publication authority、artifact body 或 memory body。

`Codex CLI` 是 stage 内第一公民 executor；其他 executor adapter 必须显式接入，且不承诺质量等价。Temporal 是 hosted durable runtime 的 substrate，属于 OPL 平台边界。

## MAS 保留职责

MAS 只保留不能声明化或上收的 domain authority：

- study/source readiness 与医学研究语义；
- AI reviewer/auditor 质量记录与 publication gate；
- canonical paper、evidence、artifact mutation 与 memory accept/reject；
- owner receipt、typed blocker、human gate 与 route-back decision；
- domain-native validators/materializers，且不得获得通用 runtime authority。

Retained surface 的机器 inventory 是 `contracts/authority_kernel_inventory.json`。inventory presence 只证明分类存在，不证明 live ready。

## Progress control

默认 next-action authority 只有：

`StageOutcome -> NextActionEnvelope`

OPL 可以承载 command/event/outbox/StageRun 和 projection；MAS owner consumption 解释医学结果。旧 provider admission、current work unit、PaperRecovery、domain-action request 和 repo-local controller shell 只能是 tombstone/provenance 或受限 diagnostic，不得重新成为 authority。

## Generated surface handoff

`contracts/generated_surface_handoff.json` 固定以下 ownership：

| Generated/hosted surface | Owner |
| --- | --- |
| CLI / MCP / Skill / product-entry manifest | OPL |
| status read model / workbench drilldown | OPL |
| runtime environment prepare/run | OPL |
| domain handler target / medical authority result | MAS |

MAS 不再维护 repo-local wrapper parity。新增 ordinary action 时，更新 catalog/schema/handler target，由 OPL 重新生成 surface；不新增 parser、JSON-RPC transport、installer 或 workbench renderer。

## Live evidence 边界

结构完成与 live acceptance 分账。contracts、tests、descriptor ready、projection clean、queue empty 与 docs 只能证明 repo/source/control-plane。Runtime ready、paper progress、publication ready、provider running 与 production ready 必须有 fresh live/readback/artifact/receipt evidence。

## 相关入口

- [项目概览](./project.md)
- [不可变约束](./invariants.md)
- [Runtime boundary](./runtime/contracts/runtime_boundary.md)
- [Stage outcome runbook](./runtime/control/progress_first_stage_outcome.md)
- [理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
