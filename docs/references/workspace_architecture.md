# Workspace Architecture

这份文档定义 `MedAutoScience` 体系下医学研究 workspace 的标准形态，以及从历史遗留的 inline-DeepScientist workspace 迁移到由 `MedDeepScientist` 支撑的标准形态的约束。

在顶层定位上，应始终按下面这条理解：

- `MedAutoScience` = `Research Ops` 的 `domain gateway + Domain Harness OS`
- `MedDeepScientist` = 当前由 `MedAutoScience` harness OS 控制的底层研究执行 runtime substrate
- 如果存在 `OPL Gateway`，它位于 `MedAutoScience` 之上，而不是替代 `MedAutoScience`

也就是说，当前 monorepo / runtime / controller 的任何后续演化，都应被理解为在收紧 `MedAutoScience` 内部 harness OS，而不是削弱它作为独立 domain gateway 的角色。

它面向两类对象：

- 未来要新建疾病项目 workspace 的 Agent / 技术同事
- 当前已经运行中的 legacy workspace，例如最早直接内嵌过 `DeepScientist` 程序与重依赖、如今准备迁到 `med-deepscientist` 的项目

## 目标

标准 workspace 架构应同时满足下面几件事：

- 疾病 workspace 本身轻巧、可读、可长期维护
- 项目专属状态保留在 workspace 内
- 程序本体与重依赖不在每个疾病 workspace 内重复存放
- 新疾病项目可以快速复制同一套目录骨架与启动方式
- `MedAutoScience` 继续作为 `Research Ops` 的 domain gateway 与 harness OS，`MedDeepScientist`（仓库名 `med-deepscientist`）继续作为当前底层执行 runtime substrate

这也意味着：正式研究入口必须是 `MedAutoScience`，而不是直接面向 `MedDeepScientist`、`DeepScientist upstream`，也不是被 `OPL` 顶层语义直接吞并。

## 默认心智模型

`MedAutoScience` 的默认对象不是“单篇论文目录”，而是“病种级 workspace”。

一个标准 workspace 默认表示：

- 一个病种，或一个稳定的专病研究主题
- 一批持续维护的私有/公开数据资产与数据版本
- 多个围绕同一数据底座推进的 `study`
- 多个由 `study` 收敛出来的稿件、补充材料和投稿交付物

推荐按下面的层级理解：

- `workspace`
  - 病种级长期资产层
- `dataset family / version`
  - workspace 级数据版本层，例如主分析数据、补充随访版本、多中心增补版本
- `study`
  - 单条研究线，通常对应一篇主稿或一组强关联投稿产物
- `quest`
  - `MedDeepScientist` 在某个 study 下的运行状态与过程性产物
- `paper bundle / submission package`
  - 面向投稿的 study-local 交付结果

关键点是：

- 数据资产属于 workspace 级，不属于某个单独 study
- study 消费已登记的数据版本，而不是自己成为真相源
- 同一私有版本或公开数据扩展线索可以被多个 study 复用

## 非目标

这份文档不要求：

- 立即重写 `MedDeepScientist` 或 `DeepScientist upstream` core
- 立即删除所有 legacy runtime 痕迹
- 把当前工作中的旧 quest 强行迁移到新目录后再继续研究

迁移应当是分阶段、可回退、保持现有项目可工作的。

## 设计原则

### 1. 项目专属状态留在 workspace

以下内容属于项目状态，应留在疾病 workspace 内：

- 原始数据、清洗数据、数据字典、终点定义、纳排标准
- `studies/`、`portfolio/`、`refs/`
- startup brief、startup payload、研究策略文档
- `MedDeepScientist` quest 仓库、日志、记忆、配置等运行状态
- workspace-scope overlay 与 quest-scope overlay 写入的本地 `.codex/skills/`

### 2. 程序本体与重依赖不进入疾病 workspace

以下内容不应在每个疾病 workspace 内重复存放：

- `MedAutoScience` 程序源码仓库
- `MedDeepScientist` 程序源码仓库
- `Codex`、`~/.codex`
- Python、`uv`、Node、npm、pandoc、TinyTeX 等系统级或共享级依赖
- `MedDeepScientist` 的受管 Python 环境、bundle、uv cache、runtime tools

### 3. 显式配置优先于隐式搜索

workspace 入口脚本不得通过猜测目录结构来寻找外部程序仓库。

必须通过显式配置指定：

- `MedAutoScience` repo 路径
- `MedDeepScientist` repo 路径
- 当前 workspace 的 profile 路径

### 4. wrapper 必须 profile-driven

workspace 侧的 wrapper 只负责两件事：

- 读取 workspace profile 和显式环境配置
- 调用外部共享程序

wrapper 不应继续硬编码：

- 某个具体疾病 workspace 下的绝对 runtime 路径
- 某个固定用户机器布局下的程序路径
- 某个旧版 legacy controller 路径

同时，wrapper 的职责边界也应明确：

- `ops/medautoscience/bin/*` 是研究入口
- `ops/med-deepscientist/bin/*` 是 runtime 运维入口
- 两者不能混用
- workspace 内所有 `ops/med-deepscientist/...` 路径派生应统一走 `med_autoscience.runtime_protocol.layout`

## 标准分层

标准架构分为四层。

### A. 系统共享层

这一层放系统级工具与用户级配置：

- `Codex`
- `~/.codex`
- Python
- `uv`
- Node / npm
- pandoc
- TinyTeX

这一层按机器维护，不按疾病 workspace 维护。

### B. 外部共享程序层

这一层放共享程序源码仓库：

- `MedAutoScience` repo
- `MedDeepScientist` repo

推荐形态：

- `/path/to/med-autoscience`
- `/path/to/med-deepscientist`

这一层允许升级、PR、版本切换，但不应和某个疾病项目目录耦合。

### C. 疾病 workspace 层

这一层放项目内容与项目专属运行状态。

推荐目录骨架如下：

```text
<workspace>/
├── .codex/
│   └── skills/
├── datasets/
├── contracts/
├── studies/
├── portfolio/
├── refs/
├── ops/
│   ├── medautoscience/
│   │   ├── bin/
│   │   ├── profiles/
│   │   ├── config.env
│   │   └── README.md
│   └── deepscientist/
│       ├── bin/
│       ├── config.env
│       ├── runtime/
│       │   ├── quests/
│       │   ├── logs/
│       │   ├── memory/
│       │   └── config/
│       ├── startup_briefs/
│       ├── startup_payloads/
│       ├── templates/
│       └── project policies / notes
└── docs/ or notes/ (project-local)
```

目录职责建议理解为：

- `datasets/`
  - 冻结后的分析数据版本或稳定数据入口
- `contracts/`
  - 变量、终点、队列与语义合同
- `studies/`
  - 多条具体研究线，每个 `study-id` 独立组织自己的实验、稿件与交付
- `portfolio/`
  - workspace 级选题池、数据资产登记、公开数据扩展、跨 study 方法学积累
- `refs/`
  - 参考论文、提取稿与文献笔记
- `ops/`
  - workspace 本地入口、配置与 project-local runtime state

### D. 运行时重依赖层

这一层专门放 `MedDeepScientist` 运行所需的重依赖：

- 受管 Python 环境
- `uv` cache
- runtime bundle
- 运行工具安装目录

这部分应视为“可重建的运行支撑层”，不是项目知识本身，因此不应继续深埋在疾病 workspace 里。

对于 `MedDeepScientist` 来说，这一层最终必须通过显式路径契约或正式兼容层来接入，而不是靠人工挪目录、临时 symlink 或手改 `site-packages`。

## MedDeepScientist 的推荐形态

`MedDeepScientist` 沿用了 upstream `DeepScientist` 对两个概念的区分：

- repo root
- runtime home

上游文档已经说明：

- repo root 是程序源码仓库
- runtime home 默认仍兼容 upstream 的 `~/DeepScientist/`
- `runtime/` 下包含 `python-env`、`uv-cache`、`bundle`、`tools`

因此在 `MedAutoScience` 体系下，推荐进一步把 `MedDeepScientist` 的使用方式收敛为：

- 外部共享 repo：`med_deepscientist_repo_root`
- workspace 内项目状态 home：`med_deepscientist_runtime_root`
- 外部共享重依赖：由 `MedDeepScientist` launcher / runtime 管理，不和疾病 workspace 绑定

这里的命名已经不再保留 `deepscientist_*` 前缀。

`med_deepscientist_runtime_root` 明确表示 “project-local MedDeepScientist state root”。

也就是说，这个路径在迁移完成前，可能仍暂时包含 upstream 默认放在 home 下的 `runtime/python-env`、`runtime/uv-cache`、`runtime/bundle`、`runtime/tools`。

迁移的目的不是保留旧字段名，而是逐步把这部分重依赖从同一路径中剥离出去，并保留 project-local state 不变。

### 保留在 workspace 内的 MedDeepScientist 内容

- `quests/`
- `logs/`
- `memory/`
- `config/`
- 项目级 startup brief、payload、templates、policies

### 应逐步迁出的 MedDeepScientist 内容

- `runtime/python-env`
- `runtime/uv-cache`
- `runtime/bundle`
- `runtime/tools`

这些内容重、可重建、且不承载疾病知识。

## MedAutoScience profile 契约

未来标准 workspace profile 至少应显式声明：

- `workspace_root`
- `runtime_root`
- `studies_root`
- `portfolio_root`
- `med_deepscientist_runtime_root`
- `med_deepscientist_repo_root`

当前实现下，一个“可直接启动”的最小 profile 还应包含：

- `name`
- `default_publication_profile`
- `default_citation_style`
- `enable_medical_overlay`
- `medical_overlay_scope`
- `medical_overlay_skills`

推荐解释如下：

- `workspace_root`
  - 当前疾病 workspace 根目录
- `runtime_root`
  - 当前 workspace 中 `MedDeepScientist` quest 根目录，通常是 `ops/med-deepscientist/runtime/quests`
- `med_deepscientist_runtime_root`
  - 当前 workspace 中 `MedDeepScientist` 项目状态根目录
- `med_deepscientist_repo_root`
  - 外部共享 `MedDeepScientist` 源码仓库

这里的 `name` 也应理解为 workspace 名称，而不是单个 study 名称。

对应地，workspace 侧还应有：

- `ops/medautoscience/config.env`
  - 显式指定外部共享 `MedAutoScience` repo
- `ops/med-deepscientist/config.env`
  - 显式指定外部共享 `MedDeepScientist` repo，或其受控 launcher 入口

当前阶段 `med_deepscientist_repo_root` 主要为 `med-deepscientist-upgrade-check` 等审计流程服务，让 Controller 能确定目标 repo 是否存在、是否为 Git 仓库、工作树是否干净等状态；它并不天然意味着 workspace 正在直接从这个 repo 运行，真正的执行真相仍可能在 workspace 内部 `site-packages` 级 overlay 或 legacy controller 补丁里。Phase 1 新增的变化是：当 repo 根目录存在 `MEDICAL_FORK_MANIFEST.json` 时，`MedAutoScience` 会把它识别为受控的 `med-deepscientist` fork，并在 `repo_check` / `workspace_contracts` 中暴露 manifest 元数据。但这仍然只说明 repo 身份已受控，不说明 adapter 已可退出。为了不在 Phase 1 过早把运行源切走，workspace 必须在 `ops/med-deepscientist/behavior_equivalence_gate.yaml` 保留一个稳定的 artifact，`med_autoscience.workspace_contracts.inspect_behavior_equivalence_gate` 会读取其中的 `schema_version`、`phase_25_ready` 和 `critical_overrides`，只有当 `phase_25_ready` 被显式置为 `true` 且 `critical_overrides` 里列出的 site-packages 补丁都被迁出或替换后，才可以考虑把 `med_deepscientist_repo_root` 当作真实执行来源。只要 `phase_25_ready=false`，就不能宣称已经完成外部执行切换，`med-deepscientist-upgrade-check` 也会返回 `blocked_behavior_equivalence_gate`，提醒我们继续固化 audit-level 合约。
## 当前实现下的最小可运行 workspace 契约

这份文档描述的是目标架构，但在当前实现里，新 workspace 还不是“只靠 6 个路径字段就能直接启动”的完全抽象状态。

当前最小可运行契约应至少同时满足：

- profile 已提供上面列出的全部关键字段
- workspace 内存在这些约定目录：
  - `studies/`
  - `portfolio/`
  - `datasets/` 或等价数据入口
  - `ops/medautoscience/`
  - `ops/med-deepscientist/`
- 当前 controller 仍默认若干固定拓扑：
  - `studies/<study-id>/...`
  - `portfolio/data_assets/...`
  - `ops/med-deepscientist/runtime/...`

这也意味着当前实现默认承认下面的基数关系：

- 一个 workspace 对应多个数据版本
- 一个 workspace 对应多个 study
- 一个 study 对应一个或多个 quest
- 一个 study 对应自己的 paper bundle / submission package

因此，短期目标不是宣称“现有实现已经完全 topology-agnostic”，而是：

- 先把 workspace 骨架标准化
- 再逐步把更多 controller 从固定拓扑提升到真正由 profile 驱动

但从 Phase 2 开始，固定拓扑不再允许散落在 controller 内部重复推导，而是要通过显式 runtime protocol 管理：

- `med_autoscience.runtime_protocol.topology`
  - 管理 `paper_root -> worktree_root -> quest_root -> study_root` 的关系
  - 当前受管布局仍明确要求 `ops/med-deepscientist/runtime/quests/<quest_id>/.ds/worktrees/<worktree>/paper`
- `med_autoscience.runtime_protocol.quest_state`
  - 管理 `runtime_state.json`、quest status、active quest 枚举、main `RESULT.json`、active `stdout.jsonl`
- `med_autoscience.runtime_protocol.paper_artifacts`
  - 管理 `paper_root`、bundle manifest、artifact manifest、submission outputs 这些 paper-facing 交付拓扑
- `med_autoscience.runtime_protocol.user_message`
  - 管理 `.ds/user_message_queue.json`、interaction journal 与 pending message 计数
- `med_autoscience.runtime_transport.med_deepscientist`
  - 管理 daemon URL 解析与 quest create / pause / resume / control 这类 engine-specific transport
  - 对 controller 而言它仍是稳定 transport 调用面；若内部继续拆出更薄的 seam，也只是实现层组织方式，不改变对外 contract
- `adapters.deepscientist.*`
  - 现在只保留兼容导出与 shim 角色
  - 不再是 runtime 布局、quest state、paper artifact、user message 或 transport 的真相源

这意味着当前阶段的目标不是“假装已经摆脱具体目录形状”，而是先把这些形状提升为 `MedAutoScience` 自己明确定义、可测试、可审计的协议面。

从长期目标看，理想架构不是 `MedAutoScience -> adapter -> MedDeepScientist` 这种双重真相结构，而是：

- `policy`
  - 只表达规则
- `controller`
  - 只编排动作
- `runtime_protocol`
  - 只管理 filesystem-facing contracts
- `runtime_transport`
  - 只管理 engine-specific transport
- `med-deepscientist`
  - 只负责执行引擎本体

因此将来要继续移除的是：

- adapter 中重复维护的一层 runtime 解析
- controller 内部零散的路径猜测和文件格式判断
- 一份信息在 protocol、adapter、controller 三处各写一次的结构
- “为了兼容旧入口而保留”的多层转发链

## Workspace wrapper 契约

workspace 内的 wrapper 应满足：

- 只通过 profile 和显式环境变量解析路径
- 只调用外部共享 `MedAutoScience` / `MedDeepScientist`
- 不继续直接依赖 workspace 内 legacy 程序副本

推荐同时保留两类薄入口：

- `ops/medautoscience/bin/*`
  - 面向医学治理层和 controller
- `ops/med-deepscientist/bin/*`
  - 面向 daemon 启动、doctor、runtime 运维等 `MedDeepScientist` 原生入口

wrapper 不应继续做：

- 自动搜索某个“看起来像 repo 的目录”
- 默认假设 `MedDeepScientist` 程序本体就在当前 workspace 里
- 直接调用已经退役的 workspace 私有 controller 脚本

## 新疾病 workspace 的最快启动方式

目标不是“复制一个已经膨胀过的旧项目”，而是复制一个轻量 skeleton。

标准启动顺序应为：

1. 创建新的疾病 workspace 骨架
2. 放入原始数据、数据说明、变量定义、终点定义、已有参考文献与研究设想
3. 配置 workspace profile
4. 显式指向外部共享的 `MedAutoScience` repo
5. 显式指向外部共享的 `MedDeepScientist` repo
6. 运行 `doctor`
7. 由 Agent 调用 `bootstrap` 初始化 workspace 级接入与数据资产状态
8. 在 `studies/` 下创建首个 `study-id`
9. 再进入 intake、scout、idea、experiment 等具体研究推进

这样新项目不需要：

- 在疾病目录里再 clone 一份 `MedDeepScientist` 或上游 `DeepScientist`
- 在疾病目录里再装一套程序级 Python 环境
- 在疾病目录里长期维护 `site-packages` 级补丁

更不应该做的是：

- 复制一个已经膨胀过的 legacy workspace 作为新病种模板
- 把单篇论文目录误当成 workspace 顶层
- 在每个 study 下面各自维护一份未经登记的数据“真相副本”

## Legacy inline-DeepScientist workspace 的定义

以下情况属于 legacy inline-DeepScientist workspace：

- 疾病 workspace 内直接放了一份 `DeepScientist` 程序副本
- 疾病 workspace 内长期保留 `python-env`、`uv-cache`、bundle 等重依赖
- 对 `site-packages/deepscientist/...` 做过项目内魔改
- wrapper 仍然依赖 workspace 私有旧脚本而不是 `MedAutoScience` 入口

当前 `NF-PitNET` workspace 属于这种过渡态：

- `MedAutoScience` 已外部共享
- `MedDeepScientist` 仍有明显 inline runtime 遗留
- 可以继续工作，但不应整体复制去做新病种模板

## NF-PitNET 迁移策略

迁移目标不是“清空旧项目再重来”，而是把当前可工作的项目逐步变成未来新项目的模板。

### Phase 0: 冻结事实面

先明确当前哪些东西是真正还在工作中的：

- 当前 quest state
- 当前 wrapper
- 当前 overlay
- 当前对 `MedDeepScientist` 的本地覆盖

这一阶段只做 inventory，不改行为。

### Phase 1: 文档先行

先把以下内容写成稳定文档：

- 标准 workspace 架构
- 当前 workspace 的 legacy 与 target 对照
- 哪些目录属于项目状态
- 哪些目录属于重依赖

这是后续迁移的审计基线。

目前 Phase 1 只完成 state contract、launcher/runtime contract 与 behavior equivalence gate 的文档梳理与校验，真实执行仍可能是 workspace 内 legacy 的 `site-packages` overlay 或本地补丁。只有当 `ops/med-deepscientist/behavior_equivalence_gate.yaml` 里的 `phase_25_ready` 显式变为 `true`，并且 `critical_overrides` 中提到的 site-packages 层补丁都被明确迁出或替换后，`med-deepscientist-upgrade-check` 才会放行 Phase 2 及以后的外部执行迁移工作；在这之前不能宣称已经完成对外执行源的切换。
### Phase 2: wrapper 全量 profile-driven

先改 workspace 入口层，而不是先动 quest。

目标：

- `ops/medautoscience/bin/*` 只从 profile 取 runtime 路径
- 不再在 wrapper 或 workspace scaffold 中散落硬编码 `ops/med-deepscientist/runtime/quests`
- 为未来新 workspace 直接复制 wrapper 打基础

### Phase 2.5: 行为等价门

在进入 Phase 3 或 Phase 4 之前，必须先确认 legacy workspace 当前可工作的“行为性补丁”已经满足下面条件之一：

- 已经通过 `MedAutoScience` overlay、startup contract、workspace policy 或正式兼容层显式迁出
- 或已经验证删除后不会改变当前项目的关键行为

这里的“行为性补丁”包括但不限于：

- `site-packages` 中改变 prompt / gate / routing 行为的本地修改
- 影响 write / finalize / publication gate 的程序级 patch
- 影响当前 quest 自动推进逻辑的 runtime 层修改

如果这个门没有通过，就不能先切到外部共享程序来源再回头补救；否则会先丢行为，再谈迁移。

`behavior_equivalence_gate.yaml` 是 workspace 的长期 artifact，必须放在 `ops/med-deepscientist/` 里并交给 `med_autoscience.workspace_contracts.inspect_behavior_equivalence_gate` 审核。这个文件会验证 `schema_version`、`phase_25_ready`、`critical_overrides`，其中 `critical_overrides` 正是对可能仍在 `site-packages` 或 controller 目录执行的本地补丁的清单；只有这些补丁被显式迁走、`phase_25_ready` 变为 `true` 时，才认定行为等价门通过，否则就会产生 `behavior_gate.phase_25_ready_false` 之类的阻断信息，`med-deepscientist-upgrade-check` 会把 `behavior_gate` 直接标记为阻塞，从而避免我们在还没确认等价的情况下把 `med_deepscientist_repo_root` 当作真实执行源。Phase 1 的 `MEDICAL_FORK_MANIFEST.json` 只是 repo-level 受控身份 artifact；它不能替代这道门。这道门既是 Phase 1 审计的结果，也是 Phase 2.5 对 site-packages overlay 级别补丁的最终挡板。
### Phase 3: MedDeepScientist 调用外部程序化

这一阶段的核心不是迁走项目状态，而是迁走程序本体依赖。

目标：

- 当前 workspace 不再依赖 workspace 内程序副本来“代表 MedDeepScientist”
- 统一以外部共享 `med_deepscientist_repo_root` 作为程序来源
- 项目内只保留 runtime state 和 project-local 配置

如果 Phase 1 已经切到受控的 `med-deepscientist` fork，那么这里的“外部共享 `med_deepscientist_repo_root`”可以具体落到该 fork。

进入本阶段前，必须已经通过 Phase 2.5 的行为等价门。

### Phase 4: 重依赖外置

这一阶段逐步把以下内容从 workspace 内挪出：

- 受管 Python 环境
- `uv` cache
- runtime bundle
- runtime tools

迁移后，workspace 内仍保留：

- `quests`
- `logs`
- `memory`
- `config`

这一阶段的前提条件必须先满足其一：

- `DeepScientist upstream` 已支持把 project-local home 与 shared runtime assets 分离配置
- 或 `MedAutoScience` 已提供正式的、可审计的兼容层来声明这些外部路径

不允许的做法：

- 手工创建一次性 symlink 后长期遗忘
- 直接修改 `site-packages` 来偷偷重定向路径
- 让不同疾病 workspace 共用同一个 quest / memory / logs 真相面

进入本阶段前，也必须已经通过 Phase 2.5 的行为等价门。

### Phase 5: 去 site-packages 魔改

任何程序级补丁，只要还能通过下面方式表达，就不应继续保留在 `site-packages`：

- `MedAutoScience` overlay
- startup contract / startup payload
- workspace policy 文档
- 显式 patch / compatibility 机制

这一步的目标是把升级敏感点压缩到最低。

## 迁移过程中的硬约束

### 必须保持兼容的内容

- 现有 quest 仓库与 Git 历史
- `studies/<study-id>/...` 下已有交付物
- 已经形成的 overlay skill 行为
- 现有 startup brief、payload、study 级策略文档

### 不应继续放大的内容

- workspace 内的程序副本
- workspace 内的重依赖目录
- `site-packages` 级长期魔改
- wrapper 中的疾病专属硬编码

## 完成态判定

当一个 workspace 满足下面条件时，可视为完成迁移：

- workspace 内没有 `MedDeepScientist` 程序源码副本
- workspace 内只保留项目状态，不保留程序级重依赖
- `MedAutoScience` 和 `MedDeepScientist` 都通过显式配置指向外部共享 repo
- wrapper 完全由 profile 驱动
- 新疾病项目可以通过复制 skeleton + 修改 profile 的方式启动

## 推荐后续动作

在 `MedAutoScience` 中，后续应按这个顺序继续推进：

1. 先把 workspace wrapper 改成完全 profile-driven
2. 再补一个标准新项目 skeleton
3. 再把 `NF-PitNET` 的 `MedDeepScientist` 调用方式逐步迁成“外部程序 + 本地运行状态”
4. 最后再处理遗留的程序级补丁与 runtime 重依赖外置
