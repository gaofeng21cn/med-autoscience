# Runtime Boundary

这份文档定义 `MedAutoScience`、`MAS Runtime OS`、OPL-owned outer supervision replacement、MAS supervision SLO/read-model contract、local scheduler tombstone/provenance refs、legacy `Hermes gateway cron` diagnostic adapter 与 `MedDeepScientist` 在当前架构下的边界。

## 一句话版本

`MedAutoScience` 是唯一研究入口与 research gateway，外层由单一 MAS app skill 承接稳定 callable surface；默认 generic runtime owner 是 OPL provider-backed stage runtime；`MAS Runtime OS` / `mas_runtime_core` 只承担 MAS domain runtime adapter、owner receipt、typed blocker、runtime event refs、guarded apply 与 diagnostic surface；默认 outer supervision scheduler owner 已迁到 OPL `opl_provider_runtime_manager` / `opl_family_runtime_provider` replacement；MAS supervision contract 保留 paper-progress SLO 解释、owner receipt、typed blocker、safe action refs 和 legacy tombstone/provenance refs；`local` 已从公开 CLI manager choices 移除，macOS LaunchAgent 只作为历史 tombstone/provenance 对象；`Hermes gateway cron` 只作为显式 legacy diagnostic adapter，不是研究运行中心；`MedDeepScientist`（仓库名 `med-deepscientist`）只作为 frozen source archive、historical fixture、explicit archive import reference / backend audit reference；`DeepScientist` 只在指代其上游来源或兼容语义时单独出现。

Current reading note：这里的 `Hermes` 指显式 `--manager hermes` 的 `Hermes gateway cron` diagnostic adapter 或显式 `hermes_agent` executor/proof lane；它们必须另有 readiness proof，不能被写成默认 study truth、runtime truth、session truth、provider truth 或默认 executor。

Executor adapter note：generic executor adapter 归 `OPL`；MAS 只声明 executor requirement、接收 OPL typed closeout / domain-task receipt。MAS 本地 `codex_cli_default` 只用于 standalone diagnostics；`Hermes-Agent` / `Claude Code` 只能作为 OPL 显式非默认 executor/proof/provenance/receipt 路径出现，不能扩展成 MAS-owned `executor_kind`、MAS-owned hosted executor 或 MAS runtime truth。2026-05-14 当前状态是 adapter/receipt/fail-closed 边界已落地；旧 hosted/runtime default caller 已退役。剩余验收分为真实 production-hosted soak / provider-hosted guarded apply / human gate-resume owner-chain proof、真实 workspace/runtime memory writeback receipt 泛化，以及按 `legacy_residue_audit` 对仍无 public caller 且无 fixture/provenance 价值的旧接口做物理删除。

display / paper-facing asset packaging 独立线明确排除在这条 runtime 主线之外。

## 三层边界

当前 runtime 讨论必须先按三层拆开：

| layer | 回答的问题 | 当前 owner |
| --- | --- | --- |
| Generic Runtime Core | attempt、queue、wakeup、worker residency、retry/dead-letter、transition runner 与 provider transport 谁持有 | `OPL provider-backed stage runtime` |
| Domain Runtime Adapter | 当前 MAS run / worker / turn 的 domain refs、receipt、typed blocker、guarded apply 与 diagnostic 怎么交还 owner chain | `MAS Runtime OS` / `mas_runtime_core` / MAS-owned watchdog 与 turn lifecycle kernel |
| Supervisor Scheduler | 多久触发一次外环检查、stale / crash 后谁叫醒 MAS | 默认 owner 是 OPL `opl_provider_runtime_manager`；默认 adapter 是 `opl_family_runtime_provider`；MAS `local` adapter / LaunchAgent 已物理退役为 tombstone/provenance refs；Hermes 是显式 legacy diagnostic adapter |
| Product Projection | 用户、PI、开发者怎么看进度、日志、阻塞和下一步 | `Progress Portal` / `Live Console` / `study-progress` / cockpit，只读消费前两层 |

这三层不得相互升格：scheduler 不持有研究真相；Portal / Console 不执行 runtime action；Runtime Core 不裁决 publication readiness。

## 角色划分

- `MedAutoScience`
  - 负责 workspace / study 治理
  - 负责 startup boundary、数据准备度、overlay、研究路线和投稿约束
  - 负责决定 quest 何时可以创建、启动、恢复、暂停
  - 通过单一 MAS app skill 对外承接 CLI、workspace commands / scripts、durable surfaces 与 repo-tracked contracts
- OPL scheduler replacement
  - 负责默认 outer supervision cadence、scheduler lifecycle、provider SLO、job registry / latest-run projection 与 runtime manager 投影
  - 通过 `runtime-supervision-status`、`runtime-ensure-supervision`、`runtime-remove-supervision` 默认 `--manager opl` 暴露，不安装 MAS-owned OS scheduler
- `local` scheduler tombstone
  - 已从公开 CLI manager choices 移除；不再提供 active status/remove/ensure command
  - macOS LaunchAgent backend 只作为 history/tombstone/provenance refs 保留，不注册、启停、清理或执行 MAS 生成的 supervision tick script
- `Hermes gateway cron`
  - 作为显式 legacy diagnostic adapter 注册、启停和执行 MAS 生成的 supervision tick script
  - 负责提供 Hermes adapter 的 job registry、schedule state、latest cron session record 与 gateway service liveness
  - 不持有 study governance、runtime authority、publication judgment 或外部 runtime workspace truth
- `MAS Runtime OS`
  - 负责 MAS domain runtime adapter、owner receipt、typed blocker、runtime event refs、guarded apply 与 diagnostic surface
  - 负责 backend registry、backend selection、runtime binding 与 MAS domain durable metadata
  - 不持有 generic runtime、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 或 workbench owner
- `MedDeepScientist`
  - 只负责 source provenance、historical behavior fixture、explicit backend audit / explicit archive import reference
  - 不承担医学研究治理真相，也不承担默认 runtime truth

## Hermes 当前实际状态

截至 `2026-05-16` 的 repo 实现，默认 scheduler owner 已迁到 OPL replacement；`local` 是显式 legacy diagnostic / cleanup adapter，Hermes 只作为显式 legacy proof / diagnostic adapter 保留：

- `runtime-ensure-supervision --manager hermes` 由 `src/med_autoscience/controllers/hermes_supervision.py` 实现；它会在 `~/.hermes/scripts/med-autoscience/<workspace-key>/watch_runtime_tick.py` 写入 MAS-owned tick script，并通过 external Hermes CLI 调用 `cron create` / `cron edit` / `cron resume` / `cron run` / `cron remove`。
- `runtime-supervision-status` 读取 `~/.hermes/cron/jobs.json`、`~/.hermes/sessions/session_cron_*.json`、Hermes gateway service 状态和 MAS 生成脚本状态，投影 `loaded` / `not_loaded` / `execution_failed` / `retired_legacy_service_present` 等 workspace supervision 状态。
- 当前 desired tick script 不是研究执行器；它只调用 MAS workspace entry，并把结果交还给 MAS durable surface。当前 legacy local / Hermes diagnostic desired command sequence 是 `watch-runtime --max-ticks 1`、`supervisor-scan`、`supervisor-consume`、`supervisor-execute-dispatch`。较早注册的真实 workspace job 可能仍是单步 `watch-runtime` script，必须通过显式 legacy diagnostic manager 路径刷新到当前脚本形态。
- `med_autoscience.runtime_transport.hermes` 当前是 explicit external Hermes-Agent diagnostics / provenance / binding contract。默认 `create_quest`、`resume_quest`、`pause_quest`、`stop_quest`、`get_quest_session`、`inspect_quest_live_runtime` 仍 fail-closed，并提示使用 `mas_runtime_core`；它没有成为默认 hosted executor、MAS-owned executor adapter 或 runtime truth。
- `systemd|cron|launchd|docker` workspace-local service managers 已从公开 CLI manager choices 和 controller direct-call payload 中移除；它们不安装旧 OS service / cron template，也不写旧 install proof。旧 service 文件或 loaded state 只作为 legacy diagnostic 的 `retired_cleanup_evidence` 暴露。MAS local LaunchAgent backend 已物理退役为 tombstone/provenance refs；公开 CLI 不再暴露 `--manager local` status/remove/ensure path。

因此，当前 Hermes 依赖的实际含义是“外层 scheduler adapter 依赖”，不是“MAS 依赖 Hermes 才能做研究执行、会话管理、论文判断或 runtime truth”。

## Scheduler 优化方向

最优方向不是新增一个 MDS 式 resident daemon，也不是继续把 `Hermes` 或本机 LaunchAgent 写成架构中心。当前 canonical 语义已经收敛为 OPL-owned scheduler replacement + MAS-owned supervision SLO/read-model contract：

- OPL 定义默认 scheduler lifecycle、cadence owner、provider SLO、job registry/latest-run projection 和 runtime manager 投影。
- MAS 定义 domain tick payload、运行顺序、幂等性、并发 / 去重、paper-progress SLO 解释、失败投影和 owner receipt。
- `local` 是显式 legacy diagnostic / cleanup adapter；`Hermes gateway cron` 是 explicit legacy diagnostic adapter。
- Hermes 和本机 LaunchAgent 对本地运行的必要依赖均已从默认路径移除；继续保留 `local` adapter 时必须服务 no-active-caller proof、cleanup proof 和同构诊断，而不是复活旧 workspace-local host service。
- Hermes 后续只能作为 OPL 显式 opt-in executor/proof/provenance 来源或历史引用出现；已无 default caller 的 hosted/runtime 命名按 `retired_no_default_caller` 处理，不能作为 MAS 默认 executor adapter、研究运行 owner 或 hidden hosted runtime。
- 在仍显式选择 Hermes 的 workspace 中，Hermes cron 可以继续投影 job / session / latest run 状态；但文档和 UI 不得把 `Hermes-hosted` 泛化成 MAS 的研究运行 owner。

一步到位的 scheduler contract 与迁移计划见 [Supervision Scheduler Contract](../control/supervision_scheduler_contract.md)。

## 允许的入口

正式研究流程只允许从这些入口进入：

- `med_autoscience.cli`
- `medautosci-mcp`
- workspace 下的 `ops/medautoscience/bin/*`
- 由这些入口进一步调用的 controller

`OPL` handoff、product-entry manifest 和其他机器可读桥接属于集成或参考层，不是正式研究入口。

## 不允许的入口

下列路径不应作为研究入口使用：

- 直接调用 external `Hermes` daemon / repo / workspace surface
- 直接调用 `MedDeepScientist` daemon HTTP API
- 直接在 `MedDeepScientist` UI 中创建或启动 quest
- 直接用 `MedDeepScientist` CLI 发起研究流程
- 绕过 `MedAutoScience` controller 的自定义脚本

这些路径即使技术上可达，在架构上也视为旁路。

关于 runtime 发出升级信号后 MAS controller 如何消费输入并继续推进，当前正式边界见：

- [Runtime Event and Outer Loop Input Contract](./runtime_event_and_outer_loop_input_contract.md)
- [Study Runtime Control Surface](../control/study_runtime_control_surface.md)

## MAS-First Runtime Layout

新建 workspace 默认使用 MAS-first 分层布局：

- `runtime/quests/`：quest live runtime root。
- `runtime/archives/`：cold / stopped runtime archive root。
- `runtime/restore_index/`：restore proof 与 source checksum 索引。
- `artifacts/runtime/runtime_lifecycle.sqlite`：SQLite lifecycle sidecar，只保存 index / history / cursor / receipt / retention ledger。
- `ops/mas/`：受控研究后端的 launcher config、薄运维脚本和 behavior gate。

这些目录不是面向研究用户或 Agent 的正式研究入口。

`ops/mas/bin/start-web`、`status`、`doctor`、`stop` 只用于 runtime 运维，不用于研究启动决策。
所有默认 workspace runtime 路径的程序化派生应统一走 `med_autoscience.runtime_protocol.layout`，而不是在 controller、workspace scaffold 或 wrapper 中重复硬编码。

当前 repo 内还没有 external `Hermes` runtime workspace truth，因此不得在本仓文档里伪造新的 `ops/hermes/...` 正式布局。
旧 `ops/med-deepscientist/runtime/quests/` 只作为显式历史 workspace restore/provenance reader 和迁移输入保留；新 writer 不再把它作为默认写入目标。

## 为什么不需要把研究门禁下沉到 backend 内核

在当前架构里，只要 `MedAutoScience` 是唯一交互层，研究门禁就应该放在入口层，而不是 backend 内核：

- startup boundary 是研究治理规则，不是 runtime 调度规则
- 期刊约束、证据包约束、study framing 约束都属于 `MedAutoScience`
- `Hermes` 负责 substrate-level contract，不负责 study governance
- `MAS Runtime OS` 只执行被批准的动作
- `MedDeepScientist` 只作为历史对照或显式诊断 reference

因此，不把研究治理规则堆到 runtime 内核里，并不代表门禁变弱；前提是所有正式调用都经过 `MedAutoScience`。
如果讨论的是受控 fork 与其上游差异，再单独使用 `DeepScientist upstream` 这一说法。

## 工程约束

为保持这条边界成立，后续新增功能时应遵守：

- 不新增直接面向用户的 `MedDeepScientist` 或 external `Hermes` 研究入口说明
- 不新增绕过 `MedAutoScience` 的 quest 创建脚本
- Agent 入口模板、workspace 脚手架和公开文档都必须把 `MedAutoScience` 写成唯一研究入口
- 不重新引入 `adapters/deepscientist/*` 这类 legacy shim 作为 production 依赖
- 不在 controller 中重复拼接 runtime 路径；统一走 `runtime_protocol.layout`
- external runtime gate 未清除前，不得把 external `Hermes` repo / daemon / workspace truth 写成本仓既成事实
- 不把 `executor_kind` 从 `codex_cli_default` 扩展为 MAS-owned `hermes_agent`、`claude_agent` 或其他 hosted executor；非默认 executor 只能经 OPL 显式 opt-in adapter 返回 typed receipt
