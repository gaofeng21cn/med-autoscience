<p align="center">
  <img src="assets/branding/medautoscience-logo.png" alt="Med Auto Science Logo" width="132" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh-CN.md"><strong>中文</strong></a>
</p>

<!--
Owner: MedAutoScience
Purpose: public repository entry
State: current_public_entry
Machine boundary: Human-readable public entry only. Machine truth remains in agent/, contracts, source, CLI/MCP/API behavior, product-entry manifests, sidecar receipts, runtime/controller durable surfaces, study workspace artifacts, and owner receipts.
-->

<h1 align="center">Med Auto Science 医学自动科研平台</h1>

<p align="center"><strong>面向真实医学研究的 AI 科研助手 —— 把数据、证据和写作持续推进到论文交付</strong></p>
<p align="center">专病研究 · 证据整理 · 分析推进 · 论文交付</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>适用人群</strong><br/>
      持有专病队列、临床数据库或多模态研究数据，准备持续推进课题的医生、课题负责人与医学研究团队
    </td>
    <td width="33%" valign="top">
      <strong>适用问题</strong><br/>
      题目、数据、分析结果和草稿分散在多处，希望把研究主线、进度和交付物收在同一个工作区里
    </td>
    <td width="33%" valign="top">
      <strong>如何开始</strong><br/>
      直接说明病种、数据、目标问题和希望形成的论文结果，系统就可以开始整理研究路径
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-overview-v2.png" alt="Med Auto Science 主示意图" width="100%" />
</p>

> `Med Auto Science` 面向已经进入真实研究阶段的团队。它把选题、数据、分析、证据、草稿和交付文件收在同一条研究线上，让课题可以持续推进、回看和审阅。

## 为什么是 Med Auto Science

医学科研真正难的往往不是写一段文字，而是把一个课题从数据和想法一路推到可投稿的论文。这个过程中，经常会遇到这些问题：

- 有数据，但不知道哪个问题最值得继续做。
- 已经跑出一些结果，却很难收成一条清晰论文主线。
- 图表、草稿、分析记录和补充验证散落在不同地方。
- 审稿、补分析、修结论和交付文件反复穿插，进度很难讲清楚。
- 多个专病课题并行推进时，容易丢失关键证据和决策理由。

**Med Auto Science 正是围绕这些医学研究问题设计的。**

它把一个医学课题组织成持续推进的研究线：先判断问题价值，再整理数据和证据，推进分析与验证，形成稿件主线，最后把论文相关文件收口到可审阅、可交付的状态。

它不会把医学研究当成一条死板流程。一个课题可以先形成多个可能方向，再回到数据和证据里比较，逐步收成更清楚的论文主线。AI 负责持续推进、整理和改写；研究者负责临床问题、结论采用和最终投稿判断。

## 一句话快速启动

你可以直接这样说：

- “帮我用这批结直肠癌数据找一个值得投稿的题目，先判断最有价值的问题是什么，还缺哪些证据。”
- “我已经做过初步分析了，帮我把结果收成一条论文主线，并告诉我下一步先补什么验证。”
- “围绕这个专病课题继续往前推，目标是形成一篇能投稿的论文，过程里的进度和文件都帮我整理好。”

## 核心亮点

<table width="100%">
<tr>
<td width="50%" valign="top">

**从数据中找到值得写的题目**

围绕专病队列、注册库或真实世界数据，先判断哪些问题有临床价值、证据基础和论文潜力，而不是直接堆分析。

</td>
<td width="50%" valign="top">

**把零散结果收成论文主线**

把已有分析、早期发现、图表和草稿组织成一条更清楚的研究故事，并明确下一步最该补哪些证据。

</td>
</tr>
<tr>
<td width="50%" valign="top">

**长期保存研究进度和交付文件**

课题的任务、文件、图表、草稿、验证记录和交付物持续绑定到同一工作区，方便回看、审阅和接力。

</td>
<td width="50%" valign="top">

**让 AI 做推进，研究者做关键判断**

AI 可以协助整理数据、执行分析、组织证据和汇报进度；临床问题界定、结论采用和投稿决策仍由研究者与课题负责人把关。

**能反复比较、修订和审阅**

医学论文不是一次生成就结束。系统可以把多个研究主张、证据缺口、分析路线和审阅意见放在同一条研究线上反复比较，持续形成下一版更可审阅的稿件和证据包。

</td>
</tr>
</table>

## 适合处理的工作

- 从一批专病数据、注册库或队列里筛出值得继续推进的研究问题。
- 把已有分析结果和早期发现收成一条更完整的论文主线。
- 管理验证、亚组、校准、临床效用等补充证据。
- 在同一个工作区里持续推进多个相关课题。
- 把论文相关结果、图表、草稿和交付文件持续绑定到对应课题。

## 当前定位与边界

- `Med Auto Science` 是医学研究 Foundry Agent，负责把专病数据、研究问题、证据和论文工作收在同一条可治理研究线上。
- 它可以作为 One Person Lab 里的研究工坊使用，也可以由 Codex 或其他 Agent 直接调用稳定能力入口。
- MAS 负责医学研究本身：研究问题、证据整理、论文主线、稿件质量和交付材料。One Person Lab 负责托管运行、进度展示、恢复重试和跨 Agent 的入口体验。
- 论文质量由研究计划、证据账本、审阅记录、AI reviewer、publication gate 和控制面记录共同约束；状态面板和脚本检查只提供辅助证据。
- 临床问题界定、结论采用和最终投稿决策由研究者与课题负责人把关。
- 期刊投稿和外部系统交互由人工监督完成。

<details>
  <summary><strong>给技术操作者看的边界说明</strong></summary>

- `Med Auto Science` 是医学研究领域智能体和 Foundry Agent，可以由 Codex 直接调用，也可以作为 OPL-compatible package 被 `OPL Framework` 发现和托管。
- MAS 负责医学研究本身：课题进入、工作区语境、证据推进、进度说明、论文质量判断、runtime-facing owner receipt/projection、artifact authority 和稿件交付。
- `OPL Framework` 是上层 stage-led 框架：负责通用运行平台，包括任务阶段、队列、唤醒、恢复、审批、记录、状态机执行和跨领域状态展示；医学结论、论文质量、domain transition 语义、artifact authority 和投稿判断由 MAS 的医学研究面继续持有。
- 在 OPL 框架里，`Stage` 表示一次较大的研究步骤，例如选题、分析、写作、审稿修复或交付；Agent executor 是 stage 内最小执行单位，`Codex CLI` 是当前第一公民 executor。
- MAS stage pack 给 executor 提供目标、上下文、authority boundary、可用 affordance、knowledge refs 和 quality gate；executor 在 attempt 内自主决定先读什么、调用哪些工具、是否并行、是否生成多个候选、是否 route back 或请求 reviewer，不由 OPL route 编排预先写死。
- MAS 工具声明遵循 Tool Affordance Boundary：声明能力、权限、凭据边界、可写范围、side effect、forbidden authority 和证据入口；不把 executor 的文献阅读、统计检查、候选生成、路线比较或追问顺序固化成 prompt 外的流程脚本。
- MAS 已完成单仓收敛。`MedDeepScientist` / `DeepScientist` 现在作为历史来源、显式归档导入、后端审计、上游学习和能力对照材料保留。
- OPL 托管的长期在线生产能力按 Temporal-backed runtime 推进。Temporal 是 OPL durable stage attempt、signal/query、retry/dead-letter 和 workflow history 的生产必需 provider；`Hermes-Agent` 不再是目标 session/wakeup substrate，但可作为显式 Agent executor adapter / proof lane 保留。当前只保证能接入、能回执、可审计，不保证行为或质量效果与 `Codex CLI` 等价。

</details>

## 这个仓库应该怎么读

1. 潜在用户、医生和医学专家先看当前首页，再继续看 [文档索引](./docs/README.md)。
2. 技术规划、架构判断和方向同步，继续读 [项目概览](./docs/project.md)、[当前状态](./docs/status.md)、[架构](./docs/architecture.md)、[不可变约束](./docs/invariants.md)、[关键决策](./docs/decisions.md)。
3. 开发者和维护者继续从 [文档索引](./docs/README.md) 进入 `docs/active/`、`docs/runtime/`、`docs/delivery/`、`docs/references/` 与 `docs/policies/`。

## 给 Agent 和技术操作者的快速入口

<details>
  <summary><strong>如果你准备把这个仓直接交给 Codex 或其他 Agent，先看这里</strong></summary>

- 不会自动安装。单独 clone 这个仓不会把 OPL Framework 或生产运行时一起装好。要把 MAS 用到能用，先准备好当前的 `one-person-lab` checkout 或 release bundle，然后再用 `medautosci product skill-catalog --profile <profile> --format json` 看 skill，或者用 `medautosci domain-handler export --profile <profile> --format json` 把能力交给 OPL / Codex。
- 先读 [文档索引](./docs/README.md)。这里已经把当前产品边界、operator entry surface 和技术阅读顺序列清楚了。
- 如果你要接管或初始化一个专病 workspace，下一跳读 [Bootstrap](./bootstrap/README.md)。它说明了 workspace-first 心智模型，以及 `init-workspace -> doctor -> show-profile -> bootstrap` 这条最短接管路径。
- 在改 runtime、入口表述或 docs 之前，把 [项目概览](./docs/project.md)、[当前状态](./docs/status.md)、[架构](./docs/architecture.md)、[不可变约束](./docs/invariants.md) 和 [关键决策](./docs/decisions.md) 当成人工可读的 repo-tracked 真相集。
- 当前 operator entry surfaces 仍可通过 `CLI`、`MCP`、`product-entry` 和 `controller` 发现，但在 strict OPL Agent purity 口径下，它们是 migration input，不是 MAS 长期自有 wrapper。当前执行地图放在 `docs/active/`，产品入口与运行时合同主要放在 `docs/product/` 和 `docs/runtime/`，Agent 可以直接从这些文档切入，不必先通读代码；根层 `agent/` pack 是 OPL generated-interface 的语义来源，本地 CLI/MCP/product-entry/sidecar/controller 命令必须收薄成 MAS domain handler target、医学 authority function、owner receipt / typed blocker producer，或在 OPL generated/default caller parity 证明后删除。
- MAS 可以通过 Codex app skill 直接调用，也可以通过 OPL 托管调用。两条路径共同使用 MAS-owned stage、controller、durable truth 和 artifact surface；OPL/Temporal 是默认托管自治 runtime，负责持久调度、唤醒、retry、resume 和投影。
- 如果外部 agent 需要直接读取 repo-tracked 的 MAS skill surface，用 `medautosci product skill-catalog --profile <profile> --format json`；返回的是单一 MAS app skill、底层 command contracts，以及由现有 runtime/session/progress/artifact surface 投影出的 machine-readable `runtime_continuity` envelope。
- OPL Full online runtime 集成使用 `medautosci sidecar export --profile <profile> --format json` 和 `medautosci sidecar dispatch --task <task.json> --format json`。本地 CLI/status/manifest 可用于诊断 provider readiness；Temporal 暂不可用时，状态面应明确报告 OPL production required dependency blocker。

</details>

## 延伸阅读

- [文档索引](./docs/README.md)
- [项目概览](./docs/project.md)
- [当前状态](./docs/status.md)
- [架构](./docs/architecture.md)
- [不可变约束](./docs/invariants.md)
- [关键决策](./docs/decisions.md)
