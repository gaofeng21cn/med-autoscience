# MedAutoScience Repository Contract

适用范围：仓库根目录及其子目录；如果具体 workspace 或子目录存在更近的 `AGENTS.md`，则以更近者为准。

这些规则与 OMX 顶层编排契约同时生效：OMX 负责通用执行/协调机制，以下条目定义 `MedAutoScience` 在本仓库中的领域定位、架构优先级与硬约束。

## 项目定位

- 这个仓库的默认定位是 `Agent-first, human-auditable` 的医学自动科研运行层，不是给医学用户手工操作的底层工具箱。
- 人类主要负责提出研究目标、提供数据、审核结果、做继续/停止决策。
- Agent 主要负责读取状态、调用平台接口、推进研究执行、组织论文交付。
- 平台本身负责提供稳定、可验证、可审计的运行入口，而不是要求人直接维护底层状态文件。
- 在这个仓库中工作时，优先通过稳定的 `workspace / profile / controller / overlay / adapter` 契约推进任务，不要把仓库重新退化成临时脚本集合。

## 设计与实现优先级

- 优先保持这个 repo 作为 `MedAutoScience` 顶层入口；不要把主要工作流重新设计成“用户手工敲 CLI”。
- 优先通过 `policy -> controller -> overlay -> adapter` 这条链路表达能力，而不是散落脚本或临时旁路。
- 优先通过 profile、overlay、controller 影响 `MedDeepScientist` / `DeepScientist` runtime，避免直接修改 runtime core。
- 公开 README 面向医学用户，重点解释项目目的、适用场景和产出；底层接口细节应放到技术文档或控制器说明，而不是让首页退化成命令手册。
- 当前更高优先级是收紧 `MedAutoScience -> MedDeepScientist` 的 runtime protocol、compatibility contract 与 adapter 退出路径，而不是持续研究上游每一个新 commit。
- `upstream intake` 是周期性、按价值触发的维护动作；不要因为 upstream 多了一个 commit，就默认把它升级成当前主线工作。
- 只有当某个上游变更对 runtime 稳定性、兼容性或真实迁移成本有明确价值时，才应启动独立的 intake 审计与吸收流程。
- 涉及第三方 Agent 接入时，优先遵循已经文档化的入口模式与稳定接口面，而不是新增一套私有、不可审计的入口规则。

## 主线稳定性与 Worktree 规则

- 这个 repo 可能被其他 runtime、workspace 或本机其他工作直接依赖；默认应把共享 checkout 视为稳定依赖面，而不是随手切分支做大改动的个人沙盒。
- `main` 是默认稳定分支。能够直接、安全落在主线的小改动，可以直接在 `main` 上完成。
- 任何不能直接在 `main` 上做的较大改动、长链路重构、实验性功能或多文件迁移，必须使用独立 `worktree` 隔离执行；不要通过把这个共享 checkout 切到功能分支的方式隔离。
- 具体来说：允许“功能分支存在”，但该分支应挂在独立 worktree 上工作；不允许让当前这个共享仓库目录长期停在非 `main` 分支上，从而影响外部依赖与其他并行任务。
- 项目内优先使用已忽略的 `.worktree/` 目录管理这些隔离工作树；完成后再把经过验证的提交收回 `main`。

## 文档分层

- `guides/` 放可随仓库发布的稳定技术指南，面向 Agent 与技术协作者。
- `docs/` 放内部设计稿、spec、plan 和 agent 工作过程产物，默认不作为公开发布面的一部分。
- 不要把需要公开引用的稳定指南继续放回 `docs/`；优先放到 `guides/`。

## 数据与状态变更

- 读状态优先于做变更。
- 如果是数据资产层变更，优先走统一 controller / mutation 入口，而不是直接编辑 `registry.json`、中间状态文件或临时落盘结果。
- 所有重要 mutation 都应具备可审计落盘结果，不能只停留在对话上下文。
- 不要用静默纠偏掩盖输入错误；如果 payload、契约或状态不合法，应明确报错并留下可追踪痕迹。

## 研究推进偏置

- 默认优先高可塑性、易形成阳性证据包的医学研究路线：
  - 临床风险分层 / 分类器
  - 数据驱动亚型重构
  - 外部验证 / 模型更新
  - 灰区分诊
  - 公开数据或机制扩展 sidecar
  - 临床窄任务智能体
- 不要默认把一个固定临床假设钉死后一路做到底。
- 如果结果偏弱、发表风险明显高，应优先止损、改题、补 sidecar 或切回 `decision`，而不是继续在弱结果上空转。

## 人类审核面

- 人类主要审核 `portfolio/`、`studies/`、`runtime/quests/` 下的 summary、report、draft、final delivery 等正式落盘结果。
- Agent 应尽量把关键判断、数据变化、交付状态写入这些可审计表面，而不是留在瞬时会话里。

## 冲突处理

- 用户显式指令高于本文件。
- 更近目录下的 `AGENTS.md` 高于本文件。
- 当 OMX 通用执行规则与仓库特定规则同时适用时：前者负责如何编排执行，后者负责这个仓库内什么目标、边界与约束是优先的。
