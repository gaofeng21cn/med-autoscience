<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science Logo" width="132" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh-CN.md"><strong>中文</strong></a>
</p>

<h1 align="center">Med Auto Science 医学自动科研平台</h1>

<p align="center"><strong>面向医学研究的专病工作台，用来把数据、课题和证据持续推进到论文交付</strong></p>
<p align="center">专病研究 · 证据组织 · 论文交付</p>

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
  <img src="assets/branding/medautoscience-hero.png" alt="Med Auto Science 主示意图" width="100%" />
</p>

> `Med Auto Science` 面向已经进入真实研究阶段的团队。它把选题、数据整理、证据推进、进度反馈和论文相关文件放在同一条主线上，便于持续推进和审阅。

## 一句话快速启动

你可以直接这样说：

- “帮我用这批结直肠癌数据找一个值得投稿的题目，先判断最有价值的问题是什么，还缺哪些证据。”
- “我已经做过初步分析了，帮我把结果收成一条论文主线，并告诉我下一步先补什么验证。”
- “围绕这个专病课题继续往前推，目标是形成一篇能投稿的论文，过程里的进度和文件都帮我整理好。”

## 适合处理的工作

- 从一批专病数据、注册库或队列里筛出值得继续推进的研究问题。
- 把已有分析结果和早期发现收成一条更完整的论文主线，并明确下一步证据。
- 在同一个工作区里持续推进多个相关课题，减少文件、图表、草稿和决策记录的分散。
- 把验证、亚组、校准、临床效用等补充证据放在同一条研究线上管理。
- 让论文相关结果、图表、草稿和交付文件持续绑定到对应课题。

## 工作方式

- 研究者提供临床问题、数据、约束条件和最终判断。
- AI 助手推进数据整理、分析执行、证据组织和进度反馈。
- 工作区持续保存任务、文件、进度和交付物，方便回看和审阅。

## 当前边界

- `Med Auto Science` 是更大 `OPL` 工作区里的医学研究工作线。
- 它负责课题接收、工作区语境、证据推进、进度投影和面向论文的交付。
- 临床问题界定、结论采用和投稿决策由研究者与课题负责人把关。
- 期刊投稿和外部系统交互由人工监督完成。

## 这个仓库应该怎么读

1. 潜在用户、医生和医学专家先看当前首页，再继续看 [文档索引](./docs/README.zh-CN.md)。
2. 技术规划、架构判断和方向同步，继续读 [项目概览](./docs/project.md)、[当前状态](./docs/status.md)、[架构](./docs/architecture.md)、[不可变约束](./docs/invariants.md)、[关键决策](./docs/decisions.md)。
3. 开发者和维护者再进入 `docs/runtime/`、`docs/program/`、`docs/capabilities/`、`docs/references/` 与 `docs/policies/`。

## 给维护者的技术入口

首页会故意保持成用户入口。
运行时合同、持久句柄、桥接表面和历史阶段记录都放在下面这些技术文档里：

- [文档索引](./docs/README.zh-CN.md)
- [当前状态](./docs/status.md)
- [项目概览](./docs/project.md)
- [运行时合同](./docs/runtime/)
- [阶段记录](./docs/program/)

## 开发验证

- `make test-fast`
- `make test-meta`
- `make test-display`
- `make test-full`
- GitHub `macOS CI` 会刻意把 `quick-checks` 保持为轻量告警；它保留 submission-facing DOCX/PDF 覆盖所需的 `pandoc` 与 `BasicTeX`，完整 study runtime analysis bundle 以及 `graphviz` / `R` 继续放在 `display-heavy` 和 `release/full` lane。
- `display-heavy` 在 push 上保持 advisory 告警，所以外部 analysis bundle bootstrap 抖动会继续出现在 GitHub Actions 里，同时不会把整个 workflow 判红；`release/full` 继续保持严格。

## Codex 接入说明

如果你主要通过 Codex 接入，先看 `docs/references/codex_plugin.md` 这份接入说明。
`docs/references/codex_plugin_release.md` 是配套的发布说明。

## 延伸阅读

- [文档索引](./docs/README.zh-CN.md)
- [项目概览](./docs/project.md)
- [当前状态](./docs/status.md)
- [架构](./docs/architecture.md)
- [不可变约束](./docs/invariants.md)
- [关键决策](./docs/decisions.md)
