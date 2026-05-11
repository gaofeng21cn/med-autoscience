# 项目概览

`Med Auto Science` 是可被通用 agent 直接调用的独立 medical research domain agent，外层由单一 MAS app skill 承接稳定 callable surface。它也可以作为 OPL Codex-first、stage-led family agent framework 上的 admitted domain agent 被托管、唤醒和投影，但医学研究 stage、质量判断、study truth 和论文交付 authority 始终由 MAS 持有。它把研究问题、工作区语境、证据推进、人话进度和论文相关文件放在同一条研究线上，帮助团队把真实研究持续推进到可交付状态。

## 当前结构

- 用户层：研究问题、工作区、进度反馈、交付文件都统一由 `Med Auto Science` 这条 domain agent 主线承载；对外第一主语是独立 domain agent，其后是单一 MAS app skill。
- 操作与集成层：`CLI`、`MCP`、`controller`，以及 repo-tracked 的 workspace commands / scripts / contracts，共同构成 MAS 对外稳定 capability surface；`product-entry manifest`、`OPL handoff` 与其他机器可读桥接只做 family-level session/runtime/projection 编排和 shared modules/contracts/indexes，不接管研究 owner 身份。
- Stage-led family framework 层：OPL 可以读取 MAS stage/action/projection descriptor，负责任务唤醒、队列、handoff、receipt、human gate transport、retry/dead-letter 和跨域可见性；MAS 继续负责 `scout`、`idea`、`analysis-campaign`、`review`、`decision` 等医学研究 stage 语义、prompt/skill、AI reviewer、publication gate、study truth reducer 和 artifact authority。
- OPL 运行管理层：目标形态中，`OPL Runtime Manager` 位于 OPL product entry / family orchestration 与 family runtime provider 之间，只负责 provider profile/provisioning、task registration hydration、runtime status projection、doctor/repair/resume、native helper catalog 与高频状态索引；Temporal 是目标生产 provider，Hermes 是迁移期 legacy/optional provider 或 executor/proof lane。它不成为 MAS 的研究 truth、scheduler kernel、session store、memory store 或 concrete executor。
- 运行时层：`Med Auto Science` 已完成 monolith closeout，持有课题与工作区权威语义、默认运行、默认诊断、进度入口以及发表判断；默认执行继续继承本机 `Codex` 配置；`Hermes-Agent` 只作为可选 hosted runtime target / reference-layer 运行载体或 legacy provider/proof lane，并可由 OPL Runtime Manager 管理其 family-level adapter/projection；`MedDeepScientist` 不再是默认 operation / diagnostic / runtime root / WebUI 依赖，只保留为显式 backend audit、source provenance、historical fixture、explicit archive import reference、behavior parity oracle 与 upstream intake source。

## 当前目标

- 把医学研究的关键判断和运行状态沉到可审计的仓库跟踪合同与持久表面。
- 让研究问题、工作区语境、进度反馈和文件交付始终围绕同一条课题线组织。
- 把 CLI、本地程序/脚本、durable surface 与 repo-tracked contract 收口成稳定 capability surface，方便 `Codex` / `OPL` skill activation 直接调用。
- 让方向锁定后的自治推进、pre-draft 质量运行、AI reviewer workflow、投稿前审计和产物重建证明沿同一条 controller 主线收口。
- 让用户可见状态、owner routing、运行健康、dispatch 执行与文件生命周期治理都围绕同一组 durable truth surface 收敛；SQLite 用作索引和 receipt，不替代文件 authority。
- 维护稳定的运行时合同、进度表面和交付表面，确保研究推进可验证、可回看、可迭代。
- 文档负责人工可读地说明当前可用系统、运行方向和证据缺口；不通过新增测试或 preflight wording gate 约束文档措辞。

## 当前边界

- `Med Auto Science` 负责医学研究工作线本身，并作为唯一研究入口与 owner。
- `Med Auto Science` 的 direct path 与任何经过 OPL 的 integration handoff 共享同一套研究语义与 durable truth surfaces。
- `OPL` 是更高层的整合入口；它不会改写 MAS 的领域真相，也不把 MAS 定义为内部模块。
- `OPL` 的 stage-led framework 支撑不改变 MAS direct skill path；Codex App 可继续直接调用 MAS app skill，OPL 只消费同一套 MAS-owned skill/action/stage metadata。
- `OPL Runtime Manager` 可以读取 MAS 的 task registration、runtime_control projection、artifact/progress locator 与 wakeup/approval 边界，用于上层状态索引和托管入口编排；这些 projection 只能回指 MAS durable truth surface，不能复制或替代研究判断。
- `Hermes-Agent` 继续只出现在可选 hosted runtime target、reference-layer、legacy provider 或 executor/proof lane 语境，不改写 MAS 的稳定 capability surface 或研究 owner 语义；Temporal/provider 也不得写 MAS truth。
- `MedDeepScientist` 不再承载默认运行、默认诊断、runtime root、WebUI 依赖或第二 owner 语义；保留价值只通过 MAS 显式声明的 backend audit、source provenance、historical fixture、explicit archive import reference、upstream intake 和 parity oracle surface 出现。
- `MAS AI-first Research OS` 是长线目标架构。当前可用落点是 pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 与真实论文 soak 的逐步闭合；真实论文 soak 仍是证据缺口。
- `Stage-Led Autonomy` 已有 MAS-owned operating surface：stage entry 通过 `stage_knowledge_packet` 读取 memory/literature/evidence/review/claim boundary，stage closeout 通过 `stage_memory_closeout_packet` 和 `memory_write_router_receipt` 做受控写回，`stage_recall_index` 只作为 read model。Publication-route 经验以 natural-language-first memory card 形式进入 stage knowledge plane，帮助 Codex CLI 探索，不作为程序化 recipe engine。`study_line_decision_engine` 与 `route_decision_orchestrator` 当前只承担 audit comparator、route router、stop-loss 和 executable task materializer 角色；它们不得绕过 stage output 生成研究路线或授权论文质量。
- 旧程序/脚本控制的退役口径按默认权威判断，而不是按文件是否存在判断：默认运行、诊断、进度、publication/package、stage-led paper loop 已迁到 MAS-owned surface；explicit archive import、historical fixture、restore diagnostic、compat import facade 和 parity oracle 可保留到对应替代面验证后再删除。保留期间它们必须 fail-closed 到非 authority。

## 当前非目标

- 不把迁移期命名、旧产品前门术语或历史交接叙事继续抬成默认用户入口。
- 不把展示能力、交付打包或其他能力线混入当前医学研究主线定位。
- 不把临时本地状态、对话记忆或 prompt-only intent 写成权威真相。
- 不新增文档 wording gate，不把文档措辞交给测试程序、preflight contract 或机械后处理约束。
