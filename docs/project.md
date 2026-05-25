# 项目概览

Owner: `MedAutoScience`
Purpose: `project_current_truth`
State: `active_current_truth`
Machine boundary: 本文是人读项目角色与边界概览。机器真相继续归 `agent/` pack、`contracts/`、CLI/MCP/API 行为、product-entry manifest、owner receipts、runtime/controller durable surfaces、真实 workspace artifact 与 owner receipts。

`Med Auto Science` 是可被通用 agent 直接调用的独立 medical research domain agent，外层由单一 MAS app skill 承接稳定 callable surface。它也可以作为 `OPL` 完整智能体运行框架中的 admitted domain agent 被托管、唤醒和投影；OPL 是 stage-led 的外层框架，`Stage` 表示大型任务步骤，Agent executor 是 stage 内最小执行单位，`Codex CLI` 是当前第一公民 executor。医学研究 stage、质量判断、study truth 和论文交付 authority 始终由 MAS 持有。它把研究问题、工作区语境、证据推进、人话进度和论文相关文件放在同一条研究线上，帮助团队把真实研究持续推进到可交付状态。

## 当前结构

- 用户层：研究问题、工作区、进度反馈、交付文件都统一由 `Med Auto Science` 这条 domain agent 主线承载；对外第一主语是独立 domain agent，其后是单一 MAS app skill。
- 操作与集成层：`CLI`、`MCP`、`controller`，以及 repo-tracked 的 workspace commands / scripts / contracts，是当前可发现的 direct/operator 调用面；在 strict OPL Agent purity 目标下，它们只应收薄为 MAS domain handler target、医学 authority function、owner receipt / typed blocker producer 或 diagnostic refs。`product-entry manifest`、`OPL handoff` 与其他机器可读桥接负责 OPL stage-runtime session/runtime/projection 编排和 shared modules/contracts/indexes，generated/default caller owner 归 OPL，研究 owner 身份继续归 MAS。
- Stage-led family framework 层：OPL 可以读取 MAS stage/action/projection descriptor，负责任务唤醒、队列、handoff、receipt、human gate transport、retry/dead-letter 和跨域可见性；MAS 继续负责 `scout`、`idea`、`analysis-campaign`、`review`、`decision` 等医学研究 stage 语义、`agent/` 下的 prompt/skill/knowledge/quality gate pack、AI reviewer、publication gate、study truth reducer 和 artifact authority。
- OPL 运行管理层：目标形态中，`OPL Runtime Manager` 位于 OPL product entry / family orchestration 与 Temporal-backed family runtime provider 之间，负责 provider profile/provisioning、task registration hydration、runtime status projection、doctor/repair/resume、native helper catalog 与高频状态索引；Temporal 是 OPL production online runtime 的必需 substrate，并且是 MAS hosted autonomous runtime 的默认 provider。Hermes 只在显式非默认 executor/proof lane、hosted proof backend 或诊断语境中出现，local provider 只作为 dev/CI/offline baseline。MAS 研究 truth、domain transition、owner receipt、memory body、artifact/publication authority 和 domain quality owner 继续由 MAS-owned surface 持有；generic scheduler、queue、attempt ledger、state-machine runner 与 App/workbench shell 归 OPL Framework。
- 运行时接入层：`Med Auto Science` 已完成 monolith closeout，持有课题与工作区权威语义、MAS-owned controller/runtime-facing truth、进度入口以及发表判断；默认 hosted path 在任务启动后交给 OPL/Temporal 持久在线调度、唤醒、retry 和 resume，stage 内默认 concrete executor 仍是 `Codex CLI` 并继承本机 Codex 配置。`Hermes-Agent` 只作为显式非默认 Agent executor adapter / proof lane 或 reference-layer 运行载体，并可由 OPL Framework 管理其 family-level adapter/projection；`MedDeepScientist` 的当前角色是显式 backend audit、source provenance、historical fixture、explicit archive import reference、behavior parity oracle 与 upstream intake source。

## 当前目标

- 把医学研究的关键判断和运行状态沉到可审计的仓库跟踪合同与持久表面。
- 让研究问题、工作区语境、进度反馈和文件交付始终围绕同一条课题线组织。
- 把 CLI、本地程序/脚本、durable surface 与 repo-tracked contract 收口成可审计的 domain handler / authority refs surface，方便 direct MAS skill 与 `OPL` generated/default callers 调用，而不把 repo-local wrapper 写成长期 generic capability owner。
- 让方向锁定后的自治推进、pre-draft 质量运行、AI reviewer workflow、投稿前审计和产物重建证明沿同一条 controller 主线收口。
- 让用户可见状态、owner routing、运行健康、dispatch 执行与文件生命周期治理都围绕同一组 durable truth surface 收敛；SQLite 用作索引和 receipt，文件 authority 继续持有交付物真相。
- 维护稳定的运行时合同、进度表面和交付表面，确保研究推进可验证、可回看、可迭代。
- 文档负责人工可读地说明当前可用系统、运行方向和证据缺口；文档措辞维护走人工 review、`git diff --check` 和必要的 link spot-check。

## 当前边界

- `Med Auto Science` 负责医学研究工作线本身，并作为唯一研究入口与 owner。
- `Med Auto Science` 的 direct path 与任何经过 OPL 的 integration handoff 共享同一套研究语义与 durable truth surfaces。
- `OPL` 是更高层的整合入口；MAS 的领域真相和内部模块边界继续由 MAS 持有。
- `OPL` 的 stage-led framework 支撑 MAS direct skill path；Codex App 可直接调用 MAS app skill 作为入口，但不承担任务启动后的外围持续 driver。OPL 消费同一套 MAS-owned skill/action/stage metadata，并在 hosted path 持有 scheduling/wakeup/retry/resume。
- `OPL Framework` 可以读取 MAS 的 task registration、runtime_control projection、artifact/progress locator 与 wakeup/approval 边界，用于上层状态索引和托管入口编排；这些都是 thin adapter / projection surface，研究判断继续回到 MAS durable truth surface。
- `Hermes-Agent` 只出现在显式非默认 Agent executor adapter、reference-layer 或 proof lane 语境；MAS 的研究 owner、domain handler、authority refs 和 owner receipt 语义继续以 MAS surface 为准。当前只保证这类 executor 能接入、能产出回执并可审计，不保证行为或质量效果与 `Codex CLI` 等价。
- `MedDeepScientist` 的保留价值通过 MAS 显式声明的 backend audit、source provenance、historical fixture、explicit archive import reference、upstream intake 和 parity oracle surface 出现。
- `MAS AI-first Research OS` 是长线目标架构。当前可用落点是 pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 与真实论文 soak 的逐步闭合；真实论文 soak 仍是证据缺口。
- `Stage-Led Autonomy` 已有 MAS-owned operating surface：stage entry 通过 `stage_knowledge_packet` 读取 memory/literature/evidence/review/claim boundary，stage closeout 通过 `stage_memory_closeout_packet` 和 `memory_write_router_receipt` 做受控写回，`stage_recall_index` 作为 read model。Publication-route 经验已经可以实现为 natural-language-first memory card：它们配 minimal metadata、small-set retrieval、typed closeout writeback 和 router receipt，帮助 Codex CLI 在 stage 内自主探索；研究路线生成和论文质量授权继续以 stage output、AI reviewer 与 controller truth 为准。`study_line_decision_engine` 与 `route_decision_orchestrator` 当前承担 audit comparator、route router、stop-loss 和 executable task materializer 角色。总入口见 [Study Workflow](./policies/study-workflow/README.md)。
- 旧程序/脚本控制的退役口径按默认权威判断。默认运行、诊断、进度、publication/package、stage-led paper loop 已迁到 MAS-owned surface；explicit archive import、historical fixture、restore diagnostic、archive import provenance locator 和 parity oracle 可保留到对应替代面验证后再删除，并以 fail-closed 方式运行。

## 当前聚焦范围

- 默认用户入口以 `Med Auto Science` domain agent 和单一 MAS app skill 表达。
- 医学研究主线优先覆盖研究问题、工作区语境、证据推进、论文质量判断和文件交付。
- 权威真相来自 durable truth surface、controller 记录、质量审阅记录和 canonical artifact proof。
- 文档维护以人工可读清晰度、当前事实一致性和链接可追踪性为验收重点。
