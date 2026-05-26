# One Person Lab Blueprint Design

Date: `2026-04-02`
Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

## Context

`MedAutoScience` 已经形成了清晰的子项目定位：

- 对外是医学自动科研平台
- 对内是 `Agent-first, human-auditable` 的医学自动科研运行层
- 当前主线是收紧 `MedAutoScience -> MedDeepScientist` 的 runtime protocol、compatibility contract 与 adapter 退出路径

这说明它已经不是一个临时性的论文流水线，而是一个有明确边界、有治理层、有运行层的正式子系统。

但从 GitHub 外部视角看，当前叙事仍然容易让人把它理解为“一个医学自动科研产品”，而不是“一个更大的一人课题组体系里的首个成熟子项目”。

如果后续还会扩展：

- 自动写基金申请
- 自动写学位论文
- 自动审稿 / 评审基金申请
- 自动制作讲课 / 答辩 PPT

那么需要一个上位总纲来回答三件事：

1. 这些不是彼此孤立的产品，而是一人课题组的不同任务面。
2. 这些任务会共享同一套资产、记忆、门控、交付和 Agent 协作底座。
3. `MedAutoScience` 是这个总纲下已经成形的第一个子项目，而不是全部。

## Problem Statement

当前缺的不是再做一个子产品，而是一个能被 `PI / 课题组负责人 / 医学研究者` 直接理解的总蓝图。

这个总蓝图需要解决两个认知问题：

### 1. 避免外界把 `MedAutoScience` 误解成单点工具

如果没有顶层总集，外界会默认理解为：

- 你在做“一个自动写论文的平台”
- 后续做基金、学位论文、PPT、评审，只是零散延伸功能

这会掩盖真正的设计方向：你在建设的是“`One Person Lab` 一人课题组”的任务操作系统。

### 2. 避免总纲停留在口号

如果顶层 repo 只有一句理念宣言，也会失真。

需要明确展示：

- 一人课题组承担哪些正式任务
- 这些任务的共享底座是什么
- 当前已经落地到什么程度
- 哪些子项目已经成形，哪些仍在路线图中

## User-Level Requirements

新的 `OPL / One Person Lab` 顶层 repo 必须满足：

1. 面向 `PI / 课题组负责人 / 医学研究者`，先讲清楚总蓝图，而不是先讲工程实现。
2. 让读者优先形成的判断是：`这是一整套一人课题组体系`。
3. `MedAutoScience` 必须被清楚表述为其中一个子项目，而且是当前最成熟的子项目。
4. 顶层 repo 不能伪装成已经做完所有模块的产品中心；必须明确哪些已落地，哪些仍在规划。
5. 顶层 repo 不能退化为纯口号页；必须给出任务版图、共享底座和子项目矩阵。
6. 顶层 repo 的信息组织要允许后续自然加入：
   - grant ops
   - thesis ops
   - review ops
   - presentation ops

## Scope

本轮只定义顶层总集的公开叙事与信息架构，不做这些事：

- 不在当前仓库内实现新的 grant / thesis / review / presentation 子系统
- 不把 `MedAutoScience` README 改写成 OPL 总入口
- 不提前承诺尚未定义清楚的底层通用 runtime
- 不创建“空模块”占位代码仓库

本轮只输出：

- `OPL / One Person Lab` 的顶层定位
- 推荐的 GitHub 承载方式
- 顶层 repo 信息架构
- 首页叙事顺序
- 子项目矩阵表达方式
- 命名建议
- 一版 README 草稿

## Considered Approaches

### Option A. Blueprint Repo

做法：

- 单独创建一个顶层 repo，作为 `One Person Lab` 总蓝图
- 首页先解释一人课题组的任务版图和共享底座
- 再列出现有和未来子项目

优点：

- 最能体现你不是在做单点产品，而是在做体系
- `MedAutoScience` 的边界最清楚，不会被总纲叙事污染
- 后续可以稳定扩展更多子项目

缺点：

- 短期内“能立刻点进去使用什么”没有产品型首页那么直接

结论：

- 这是本次选定方案。

### Option B. Product Hub In MedAutoScience

做法：

- 直接在 `MedAutoScience` 首页上升到 OPL 总叙事
- 把未来模块作为路线图写进当前 README

优点：

- 复用已有流量和仓库关注度

缺点：

- 医学自动科研子项目和顶层总纲会混在一起
- 外界仍容易把 OPL 理解成 `MedAutoScience` 的 marketing 包装
- 会削弱当前仓库已经很清楚的医学运行层边界

结论：

- 不选。

### Option C. Organization Profile First

做法：

- 直接用 GitHub organization profile 作为总入口
- 不单独创建总集 repo

优点：

- 生态感更强

缺点：

- 现在阶段过早
- 总纲内容、项目矩阵和演化路线缺少一个稳定载体

结论：

- 暂不选。

## Chosen Design

采用 `Option A: Blueprint Repo`。

推荐创建一个单独的顶层 repo，建议名为：

- 首选：`one-person-lab`
- 备选：`opl`
- 不推荐：`med-opl`、`medautoscience-hub` 这类过早把总纲绑定到医学子项目上的名字

这个 repo 的职责不是运行代码，而是做三件事：

1. 定义 `One Person Lab` 的总目标和边界。
2. 展示一人课题组任务版图与共享底座。
3. 维护当前子项目矩阵与路线图。

## Design

### A. Positioning

推荐的一句话定位：

> `One Person Lab` 是一个面向研究型个人与小型课题组的 Agent-first 任务体系，目标是把数据、研究、写作、评审与教学等实验室正式工作，组织成可审计、可复用、可持续推进的模块化系统。

这句话有三个关键点：

- 不是只讲自动写论文
- 不是只讲 AI Agent
- 不是只讲效率工具

它强调的是“实验室正式工作”的系统化。

### B. Audience

首页主受众：

- `PI`
- 课题组负责人
- 医学研究者
- 兼具研究与写作任务的个人研究者

首页不应默认面向：

- 纯工程开发者
- 单纯想看 API 的技术用户

技术细节可以有，但应该放到次级文档或子项目里。

### C. Reader Takeaway

首页看完后，用户应当形成的第一判断是：

> 这不是一个单点产品，而是一套“一人课题组”的总蓝图；其中 `MedAutoScience` 是已经成熟的第一个子项目。

第二判断是：

> 这套体系的核心不是把任务堆给 Agent，而是让不同任务共享同一套实验室级底座。

### D. Shared Foundation

OPL 顶层 repo 里，建议把共享底座明确定义为五层。

#### 1. Asset Layer

共享对象：

- 数据资产
- 文献与证据资产
- 模板与交付资产
- 任务上下文与约束

#### 2. Memory Layer

共享对象：

- 选题记忆
- 数据问题映射
- 期刊与基金方偏好
- 评审标准与常见反馈
- 教学素材与讲解框架

#### 3. Governance Layer

共享对象：

- 何时允许进入正式执行
- 何时需要停损 / 改题 / 补证据
- 哪些任务属于轻量探索，哪些必须纳管

#### 4. Delivery Layer

共享对象：

- 正式交付物目录
- 打包与同步规则
- 人类审核面

#### 5. Agent Execution Layer

共享对象：

- Agent 入口模式
- 稳定 controller 接口
- 运行监控与审计回写

这五层表达了“为什么不同任务可以共享一套底座”，而不是看起来只是功能相邻。

### E. Task Map

顶层 repo 应明确把“一人课题组”的正式任务，表达为并列模块，而不是未来功能列表。

建议先画成下面这张任务地图：

- Research Ops
  - 数据到论文
  - 研究路线推进
  - 证据组织与投稿交付
- Grant Ops
  - 基金选题与可行性
  - 申请书生成与迭代
  - 基金评审模拟
- Thesis Ops
  - 学位论文结构化写作
  - 图表与章节同步
  - 答辩准备
- Review Ops
  - 审稿意见生成
  - 基金申请评审
  - rebuttal 与 revision 组织
- Presentation Ops
  - 讲课 PPT
  - 汇报 PPT
  - 答辩 PPT

这里的重点不是一次性承诺全部实现，而是把任务版图讲清楚。

### F. Project Matrix

任务地图下面，建议紧接一个“子项目矩阵”。

推荐用三列：

| 项目 | 负责什么 | 当前状态 |
| --- | --- | --- |
| `MedAutoScience` | 医学自动科研主线，从数据到论文交付 | Active, most mature |
| `Grant Ops` | 基金申请与基金评审工作流 | Planned |
| `Thesis Ops` | 学位论文与答辩工作流 | Planned |
| `Review Ops` | 审稿、评审与回复工作流 | Planned |
| `Presentation Ops` | 课程、汇报与答辩材料工作流 | Planned |

其中：

- `MedAutoScience` 要有独立链接
- 其他项即使尚未建仓，也可以先写 `Planned`

### G. Recommended Repo Structure

顶层 repo 初版不需要复杂目录，建议只保留：

```text
one-person-lab/
├── README.md
├── docs/
│   ├── operating-model.md
│   ├── task-map.md
│   ├── shared-foundation.md
│   └── roadmap.md
└── assets/
    └── opl-map.png
```

职责建议：

- `README.md`
  - 对外总入口
- `docs/operating-model.md`
  - 解释 OPL 的操作模型
- `docs/task-map.md`
  - 解释各任务模块
- `docs/shared-foundation.md`
  - 解释共享底座
- `docs/roadmap.md`
  - 解释当前和未来子项目

如果要更轻，也可以先只有一个 `README.md`，但至少要预留这些概念结构。

### H. Recommended README Flow

首页建议按这个顺序组织。

#### 1. Hero

一屏回答三个问题：

- `OPL 是什么`
- `它面向谁`
- `它不是单点产品`

推荐标题：

`One Person Lab`

推荐副标题：

`A blueprint for an agent-first, human-auditable one-person research lab.`

如果你希望更贴近中文语境，也可以在副标题里补一句：

`面向一人课题组的任务体系蓝图`

#### 2. Why This Exists

这里不要先讲 AI，很容易把叙事做浅。

应先讲：

- 一个研究型个人或小课题组，真实承担的不只是写论文
- 同一批数据、文献、思路和交付物，会反复服务论文、基金、学位论文、评审和教学
- 这些工作不应该拆成彼此孤立的工具链

#### 3. What A One Person Lab Needs To Do

这里放任务版图。

#### 4. What These Tasks Share

这里放共享底座五层。

#### 5. Current Projects

这里明确写：

- `MedAutoScience` 是当前最成熟的项目
- 它负责医学自动科研主线，从数据到论文交付

#### 6. Roadmap

这里写未来方向，但措辞要克制：

- 不是“即将发布一切”
- 而是“下一步计划扩展到这些任务面”

#### 7. Collaboration

这里说明：

- 欢迎合作
- 欢迎共建
- 欢迎围绕具体子项目展开讨论

### I. Naming Recommendation

推荐命名采用双层：

- 顶层理念名：`One Person Lab`
- 内部简称：`OPL`

子项目命名建议保持 “明确任务 + ops/system” 的风格，例如：

- `MedAutoScience`
- `Grant Ops`
- `Thesis Ops`
- `Review Ops`
- `Presentation Ops`

不建议一开始就给所有未来项目起过于品牌化的新名字，因为：

- 当前最重要的是讲清任务版图
- 不是先制造一堆品牌壳

### J. Non-Goals

顶层 repo 建议明确写出：

- OPL 不是“一个 Agent 帮你自动完成一切”的口号
- OPL 不是单篇论文自动生成器
- OPL 不是把实验室任务退化成若干 prompt
- OPL 不是今天就已经完成的全家桶产品

这能避免外界误解。

## Draft README

下面是一版可直接作为顶层 repo 首页起稿的草案。

```md
# One Person Lab

**A blueprint for an agent-first, human-auditable one-person research lab.**

`One Person Lab (OPL)` is a blueprint for building a one-person lab: a modular system where research, writing, review, and teaching workflows are organized as auditable, reusable, agent-driven workstreams rather than isolated tools.

It is not a single product.
It is a long-term project map.

## Why this exists

A real lab does not only produce papers.

It also writes grant proposals, prepares theses, reviews papers and funding applications, builds presentation materials, and continuously reuses the same datasets, literature, methods, and delivery assets across these tasks.

Most AI tooling treats these jobs as separate one-off workflows.
OPL starts from the opposite assumption:

- these tasks belong to the same lab
- they should share the same asset base
- they should share memory, governance, and delivery surfaces
- agents should help execute them, but humans should still audit the outputs and make key decisions

## What a one-person lab needs to do

- Research Ops
  - from data to paper
  - evidence packaging
  - submission delivery
- Grant Ops
  - proposal planning
  - grant writing
  - review simulation
- Thesis Ops
  - dissertation drafting
  - chapter synchronization
  - defense preparation
- Review Ops
  - paper review
  - grant review
  - rebuttal and revision support
- Presentation Ops
  - lecture slides
  - lab presentations
  - defense slides

## What these tasks share

Across all of these workstreams, a lab still needs the same foundations:

- asset layer
  - datasets, references, templates, delivery artifacts
- memory layer
  - topic memory, venue memory, review memory, teaching memory
- governance layer
  - when to proceed, when to stop, when to reframe
- delivery layer
  - stable output packages and human review surfaces
- agent execution layer
  - stable interfaces, controller actions, runtime monitoring, audit trails

## Current projects

### MedAutoScience

`MedAutoScience` is the first mature project under the OPL umbrella.

It focuses on medical research operations:

- disease-workspace organization
- data governance
- study progression
- evidence packaging
- manuscript and submission delivery

Repository:

- [MedAutoScience](https://github.com/gaofeng21cn/med-autoscience)

## Roadmap

OPL is intended to expand beyond medical paper workflows into broader lab workstreams, including:

- grant ops
- thesis ops
- review ops
- presentation ops

These are planned workstreams, not finished products.

## Collaboration

If you are interested in building agent-first, human-auditable lab systems, or want to collaborate on specific workstreams, feel free to open an issue or reach out through the relevant project repository.
```

## Rollout Recommendation

建议按两步落地：

### Step 1

先创建 `one-person-lab` 顶层 repo，只放：

- `README.md`
- 一个简单的 `docs/roadmap.md`
- 指向 `MedAutoScience` 的明确入口

目标是先把总纲讲清楚，而不是一次写完整站点。

### Step 2

等第二个子项目轮廓稳定后，再补：

- 更正式的任务地图
- 更明确的共享底座文档
- organization profile 或 docs site

## Risks And Tradeoffs

### 1. 风险：总纲过大、落地感过弱

缓解方式：

- 在首页明确写 `MedAutoScience` 是当前最成熟项目
- 其他模块只写成 planned workstreams，不伪装成熟度

### 2. 风险：外界仍把 OPL 当成医学自动科研包装页

缓解方式：

- 首页任务地图必须覆盖基金、学位论文、评审、PPT
- 不要让 `MedAutoScience` 占据首页 80% 的篇幅

### 3. 风险：过早承诺未来子项目名称和边界

缓解方式：

- 先用任务型名称
- 先定义任务面，不急着定义完整产品边界

## Acceptance Criteria

如果这份设计被正确执行，首次访问顶层 repo 的 `PI / 医学研究者` 应能在几分钟内理解：

1. `OPL` 不是单点产品，而是总蓝图。
2. 一人课题组不止写论文，还有基金、学位论文、评审和 PPT 等任务面。
3. 这些任务共享资产、记忆、门控、交付和 Agent 执行底座。
4. `MedAutoScience` 是当前最成熟的第一个子项目。
