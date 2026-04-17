<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science Logo" width="132" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh-CN.md"><strong>中文</strong></a>
</p>

<h1 align="center">Med Auto Science 医学自动科研平台</h1>

<p align="center"><strong>面向医学研究的主线系统，用来把专病数据持续推进到论文级研究</strong></p>
<p align="center">Clinical Research Progression · Evidence Packaging · Submission Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>面向谁</strong><br/>
      希望把专病数据、课题和证据稳定推进到正式论文交付的医学团队与研究者
    </td>
    <td width="33%" valign="top">
      <strong>能帮什么</strong><br/>
      研究组织、证据打包、进度监管与面向投稿的研究交付
    </td>
    <td width="33%" valign="top">
      <strong>公开角色</strong><br/>
      `Research Foundry` 里的医学 `Research Ops` 主线，`OPL` 继续只承担可选的顶层 federation 入口
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="Med Auto Science 主示意图" width="100%" />
</p>

> `Med Auto Science` 是 `Research Foundry` 家族里的医学科研主线。它的目标，是帮助团队把研究过程做成可治理、可审计、能持续朝论文交付推进的正式工作流。

## 它能帮你做什么

- 把专病 workspace、数据、study、证据和输出组织到同一条可审计主线上。
- 让课题从 intake、分析继续推进到验证、证据组织与稿件交付。
- 让研究叙事更贴近临床意义，而不是默认套进通用机器学习论文模板。
- 让进度、阻塞和监督状态保持可见，而不是藏在一条长对话或一串脆弱脚本里。

## 更适合什么课题

- 你已经有专病队列、注册库，或一套稳定的临床数据。
- 你希望多个课题复用同一个 workspace 和知识底座。
- 你在写作前需要外部验证、亚组分析、校准、临床效用或 sidecar 证据。
- 你的真实目标是论文级交付，而不只是跑完一次分析。

## 当前公开可走的路径

| 路径 | 状态 | 含义 |
| --- | --- | --- |
| Agent 协作研究主线 | Active | 当前最诚实、也最适合真实课题推进的使用路径 |
| 轻量 `product-entry` shell | Early | 已经能启动、下任务、看进度，但还不是成熟独立医疗前台 |
| 医学展示 / 论文配图支线 | Supporting line | 与 runtime 主线刻意分开，避免图件工作反过来改写研究 authority |
| 成熟的独立医疗用户前台 | Not landed | 仍是 runtime gate 之后的后续工作 |

## 这个仓库应该怎么读

1. 潜在用户、医生和医学专家先看当前首页，再继续看 [文档索引](./docs/README.zh-CN.md)。
2. 技术规划、架构判断和方向同步，继续读 [项目概览](./docs/project.md)、[当前状态](./docs/status.md)、[架构](./docs/architecture.md)、[不可变约束](./docs/invariants.md)、[关键决策](./docs/decisions.md)。
3. 开发者和维护者再进入 `docs/runtime/`、`docs/program/`、`docs/capabilities/`、`docs/references/` 与 `docs/policies/`。

## 用人话解释它的边界

`Med Auto Science` 不是底下所有 runtime 组件的统称。
它的职责，是对医学研究入口、study authority 和研究真相负责。

```text
User / Agent
  -> OPL Gateway（可选）
      -> Med Auto Science
          -> 受控研究后端
```

更直白地说：

- `OPL` 可选，且始终在这个仓库之上。
- `Med Auto Science` 负责医学研究 workflow 和 authority boundary。
- 当前真实研究引擎仍然在这个仓库之下，不应和公开产品入口混成一层。

## 这个仓库不是什么

- 它不是“成熟独立医疗前台已经落地”的宣传口径。
- 它不是“上游 `Hermes-Agent` 已经在这里完整接管研究执行”的结论。
- 它不是把论文配图资产化支线重新混回研究 runtime 主线的地方。

<details>
  <summary><strong>面向技术读者的运行时真相说明</strong></summary>

当前 formal-entry matrix 仍然是 `CLI`、`MCP` 和 `controller`，并继续落在 `Codex-default host-agent runtime` 基线上。
repo-tracked 产品主线仍按 `Auto-only` 理解。

当前 tranche 分层仍然明确写成：

- `P0 runtime native truth`
- `P1 workspace canonical literature / knowledge truth`
- `P2 controlled cutover -> physical monorepo migration`

当前真实 runtime ownership 仍然是分层的：

- `Med Auto Science` 负责研究入口、study/workspace authority 与 outer-loop 治理。
- `MedDeepScientist` 继续承担真实研究执行的受控后端。
- 上游 `Hermes-Agent` 仍是目标 outer runtime substrate，而不是本仓已经完整落地的终态。

当前 durable handle 继续这样理解：

- `program_id` 指向 `research-foundry-medical-mainline`。
- `study_id` 仍是 study 的持久身份。
- `quest_id` 是受控 research backend quest 正式运行句柄。
- `active_run_id` 仍是当前 live daemon run handle。
- `study-progress` 继续投影医生/PI 能读的人话进度。

repo-tracked runtime truth 与本地 operator handoff surface 继续分层维护。
当前 repo-side 外层 runtime seam 不等于上游 `Hermes-Agent` runtime 已经落地，独立上游 `Hermes-Agent` host 对 backend engine 的完整替代仍要继续穿过这道 gate。
也就是说，external runtime gate 仍然存在，并且已经诚实收口成 `P2` 的外部 blocker。

当前 repo-verified 的公开入口 wording 继续保持：

- `operator entry` 和 `agent entry`
- `product entry`：真正成熟的 direct user-facing 入口还没有落地
- 当前轻量 shell 仍然围绕 `build-product-entry` 收口

兼容目标路径继续写成：

- `User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`
- `User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

当前这层轻量 shell 已包括 `workspace-cockpit`、`submit-study-task`、`launch-study`、`product-preflight`、`product-start`、`product-frontdesk`、`product-entry-manifest` 与 `build-product-entry`。
这些表面已经把启动、下任务和看进度收口得更诚实，而且 manifest/frontdesk 现在还会直接带出 guardrail-recovery 回路、结构化 `Phase 3` host-clearance lane、`Phase 4` backend-deconstruction lane，以及 `Phase 5` 平台目标；但这依然不等于成熟独立医疗前台已经落地。

医学展示支线继续与 runtime 主线刻意分开，避免发表图件工作反过来改写研究 authority 与 gateway 真相。
</details>

## 开发验证

- `make test-fast`
- `make test-meta`
- `make test-display`
- `make test-full`
- GitHub `macOS CI` 会刻意把 `quick-checks` 保持为轻量告警；完整 study runtime analysis bundle 仍只在 `display-heavy` 和 `release/full` lane 上准备。

## Codex plugin 接入

如果你主要通过 Codex 接入，先看 `docs/references/codex_plugin.md` 这份 Codex plugin 接入说明。
`docs/references/codex_plugin_release.md` 是配套的 Codex plugin 发布说明。

## 延伸阅读

- [文档索引](./docs/README.zh-CN.md)
- [项目概览](./docs/project.md)
- [当前状态](./docs/status.md)
- [架构](./docs/architecture.md)
- [不可变约束](./docs/invariants.md)
- [关键决策](./docs/decisions.md)
