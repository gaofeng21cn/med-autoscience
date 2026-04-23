# 项目概览

`Med Auto Science` 是可被通用 agent 直接调用的独立 medical research domain agent。它把研究问题、工作区语境、证据推进、人话进度和论文相关文件放在同一条研究线上，帮助团队把真实研究持续推进到可交付状态。

## 三层结构

- 用户层：研究问题、工作区、进度反馈、交付文件都统一由 `Med Auto Science` 这条 domain agent 主线承载；MAS 是唯一研究入口与 owner。
- 操作与集成层：`CLI`、`MCP`、`controller`，以及 repo-tracked 的 workspace commands / scripts / contracts，共同构成 MAS 对外稳定 capability surface；`OPL` 与机器可读产品接入接口只做 family-level session/runtime/projection 编排和 shared modules/contracts/indexes，不接管研究 owner 身份。
- 运行时层：`Med Auto Science` 持有课题与工作区权威语义以及发表判断；默认执行继续继承本机 `Codex` 配置；`Hermes-Agent` 只作为可选 hosted runtime target / reference-layer 运行载体；`MedDeepScientist` 只保留为受控后端、behavior oracle 与 upstream intake buffer，不是用户入口，也不是第二 owner。

## 当前目标

- 把医学研究的关键判断和运行状态沉到可审计的仓库跟踪合同与持久表面。
- 让研究问题、工作区语境、进度反馈和文件交付始终围绕同一条课题线组织。
- 把 CLI、本地程序/脚本、durable surface 与 repo-tracked contract 收口成稳定 capability surface，方便 `Codex` / `OPL` skill activation 直接调用。
- 让方向锁定后的自治推进、论文质量合同和投稿前审计沿同一条 controller 主线收口。
- 维护稳定的运行时合同、进度表面和交付表面，确保研究推进可验证、可回看、可迭代。

## 当前边界

- `Med Auto Science` 负责医学研究工作线本身，并作为唯一研究入口与 owner。
- `Med Auto Science` 的 `direct entry` 与 `OPL handoff` 共享同一套研究语义与 durable truth surfaces。
- `OPL` 是更高层的整合入口；它不会改写 MAS 的领域真相，也不把 MAS 定义为内部模块。
- `Hermes-Agent` 继续只出现在可选 hosted runtime target 或 reference-layer 语境，不改写 MAS 的稳定 capability surface 或研究 owner 语义。
- `MedDeepScientist` 继续承载当前仍保留在受控后端中的研究执行能力，同时保留 behavior oracle 与 upstream intake buffer 职责；它不作为用户入口，也不承担第二 owner 身份。

## 当前非目标

- 不把迁移期命名、旧产品前门术语或历史交接叙事继续抬成默认用户入口。
- 不把展示能力、交付打包或其他能力线混入当前医学研究主线定位。
- 不把临时本地状态、对话记忆或 prompt-only intent 写成权威真相。
