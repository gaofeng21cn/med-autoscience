# Runtime Boundary

Owner: `MedAutoScience`
Purpose: `runtime_owner_boundary`
State: `active_contract`
Machine boundary: 本文是人读 runtime owner 边界。机器真相继续归 contracts、schema、CLI/MCP/API payload、product-entry manifest、domain-handler receipt、OPL current-control-state / provider attempt ledger、MAS runtime/controller durable surfaces、owner receipts、typed blockers 和真实 workspace artifact。

## 一句话版本

`MedAutoScience` 是唯一医学研究入口；默认 generic runtime owner 是 OPL provider-backed stage runtime；MAS 只承担 domain authority refs、DomainIntent / owner route、owner receipt、typed blocker、artifact/source/quality refs、guarded apply receipt、diagnostic explanation 和研究治理边界。

历史 MAS-local scheduler、Hermes/MDS、runtime lifecycle/SQLite、workspace-local wrapper 与旧 alias 仅作为 `docs/history/**` provenance、explicit archive/import reference 或 parity oracle 读取；当前默认面是 OPL/Temporal hosted runtime + MAS domain authority refs、owner receipts、typed blockers 和 minimal authority functions。

display / paper-facing asset packaging 独立线明确排除在这条 runtime 主线之外。

## 标准 Agent Runtime 三层边界

当前 runtime 讨论必须先按三层拆开：

| layer | 回答的问题 | 当前 owner |
| --- | --- | --- |
| Generic runtime core | attempt、queue、wakeup、worker residency、retry/dead-letter、transition runner、human gate transport 与 provider transport 谁持有。 | `OPL provider-backed stage runtime` |
| Domain authority adapter | MAS domain refs、receipt、typed blocker、guarded apply 与 diagnostic explanation 怎么交还 owner chain。 | MAS domain authority functions + `domain_authority_refs_index` |
| Product projection | 用户、PI、开发者怎么看进度、日志、阻塞和下一步。 | `Progress Portal` / `study-progress` / cockpit / OPL App workbench，只读消费 OPL current-control-state 与 MAS domain authority refs。 |

这三层不得相互升格：runtime core 不裁决 publication readiness；projection 不执行 runtime action；domain authority refs 不持有 queue、attempt、retry/dead-letter、worker residency、transition runner、generic lifecycle/index 或 workbench owner。

## 角色划分

- `MedAutoScience`
  - 负责 workspace / study 治理、startup boundary、数据准备度、overlay、研究路线、投稿约束和医学 owner chain。
  - 通过单一 MAS app skill 对外承接 CLI、workspace commands / scripts、durable surfaces 与 repo-tracked contracts。
  - 持有 study truth、publication quality、AI reviewer judgment、artifact authority、publication-route memory body decision、owner receipt 和 typed blocker。
- `OPL current control state / provider attempt ledger`
  - 负责 stage attempt、queue hydration、wakeup、provider start/query、typed closeout、retry/dead-letter、human gate transport、operator status projection 和 generic lifecycle/index。
  - 只消费 MAS domain-handler task、typed blocker、owner receipt 和 artifact/source locator refs，不写 MAS study truth、paper/package body、publication eval、controller decision、memory body 或 current package。
- MAS domain authority functions
  - 负责 DomainIntent / owner route、owner receipt、typed blocker、artifact/source/quality refs、guarded apply receipt 与 diagnostic explanation。
  - 负责 MAS domain durable metadata 与 `domain_authority_refs_index`。
  - 不持有 generic runtime、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine、runtime lifecycle read model 或 workbench owner。
- `MedDeepScientist`
  - 只负责 source provenance、historical behavior fixture、explicit backend audit / explicit archive import reference。
  - 不承担医学研究治理真相，也不承担默认 runtime truth。

## 允许的入口

正式研究流程只允许从这些入口进入：

- `med_autoscience.cli`
- `medautosci-mcp`
- workspace 下的 `ops/medautoscience/bin/*`
- 由这些入口进一步调用的 controller

`OPL` handoff、product-entry manifest、domain-handler payload 和其他机器可读载荷属于 generated/hosted surface、integration 或 reference 层。它们可以托管、调度、索引、展示和 dispatch allowlisted MAS task，但必须回到 MAS owner surface 签 receipt、blocker 或 authority ref。

## 不允许的入口

下列路径不应作为研究入口使用：

- 绕过 `MedAutoScience` controller 的自定义脚本；
- 直接调用外部 backend、archive、diagnostic 或 historical fixture 发起研究流程；
- 在非 MAS owner surface 中写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package、artifact gate、memory body 或 study truth；
- 把 OPL provider completion、queue pass、descriptor ready 或 test pass 写成 MAS publication readiness。

这些路径即使技术上可达，在架构上也视为旁路。

关于 runtime 发出升级信号后 MAS controller 如何消费输入并继续推进，当前正式边界见：

- [Runtime Event and Outer Loop Input Contract](./runtime_event_and_outer_loop_input_contract.md)
- [Study Runtime Control Surface](../control/study_runtime_control_surface.md)

## MAS-First Runtime Layout

新建 workspace 默认使用 MAS-first 分层布局：

- `runtime/quests/`：quest live runtime root。
- `runtime/archives/`：cold / stopped runtime archive root。
- `runtime/restore_index/`：restore proof 与 source checksum 索引。
- `artifacts/runtime/domain_authority_refs.sqlite`：domain authority refs SQLite index，只保存 owner receipt、typed blocker、locator、archive/provenance 和 no-forbidden-write refs。
- `ops/mas/`：受控研究后端的 launcher config、薄运维脚本和 behavior gate。

这些目录不是面向研究用户或 Agent 的正式研究入口。

`ops/mas/bin/start-web` 已退役；`status`、`doctor`、`stop` 这类薄入口不得作为研究启动决策面。所有默认 workspace runtime 路径的程序化派生应统一走 `med_autoscience.runtime_protocol.layout`，而不是在 controller、workspace scaffold 或 wrapper 中重复硬编码。

## 为什么研究门禁留在 MAS owner surface

在当前架构里，只要 `MedAutoScience` 是唯一交互层，研究门禁就应该放在 MAS owner surface：

- startup boundary 是研究治理规则，不是 runtime 调度规则；
- 期刊约束、证据包约束、study framing 约束都属于 `MedAutoScience`；
- OPL runtime 执行 stage/runtime 动作；MAS domain authority functions 签收、阻断或解释被批准的 domain 动作；
- external backend、archive 或 historical fixture 只能作为 reference/provenance，不持有默认 study governance。

因此，不把研究治理规则堆到 runtime core 里，并不代表门禁变弱；前提是所有正式调用都经过 `MedAutoScience`。

## 工程约束

为保持这条边界成立，后续新增功能时应遵守：

- 不新增绕过 `MedAutoScience` 的 quest 创建脚本；
- Agent 入口模板、workspace 脚手架和公开文档都必须把 `MedAutoScience` 写成唯一研究入口；
- 不新增 production 依赖式 external backend shim；
- 不在 controller 中重复拼接 runtime 路径；统一走 `runtime_protocol.layout`；
- 不把非默认 executor 扩展成 MAS-owned hosted executor 或 runtime truth；非默认 executor 只能经 OPL 显式 opt-in adapter 返回 typed receipt；
- 不把 product/status/workbench/read-model helper 扩展成 queue、attempt、retry/dead-letter、worker residency、generic lifecycle/index 或 operator current-state owner；
- 不让 Markdown 文档路径、章节或文案成为机器接口；机器面必须使用 schema、JSON、CLI/API payload、manifest、durable semantic ID 或 generated artifact。

历史 scheduler、local workspace service、runtime lifecycle、Console/WebUI parity 和 physical retirement 记录见 [runtime history archive](../../history/runtime/README.md)。这些材料只作 provenance，不能恢复为 current runtime owner。
