# Third-Party Agent Entry Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

## 背景

`MedAutoScience` 当前已经明确采用：

- `Agent-first, human-auditable` 的运行层定位
- `policy -> controller -> overlay -> adapter` 的稳定扩展链路
- `DeepScientist` 作为主 runtime
- `controller / CLI` 作为正式机器接口
- `scout / idea / experiment / write / finalize` 作为主运行阶段
- `decision` 作为跨阶段治理与门控能力

现有体系已经足以让 `Codex` 等 Agent 接管一个医学研究 workspace 并推进正式研究，但对第三方 Agent 的接入仍然存在一个缺口：

- README 面向医学用户
- `AGENTS.md` 主要表达仓库定位与硬约束
- `guides/agent_runtime_interface.md` 已经是技术入口，但仍偏底层接口导向

这导致外部 Agent 即使“足够聪明”，也仍要自己猜：

- 当前任务到底属于哪种入口
- 是否需要正式 workspace / profile
- 应该优先调哪些 skill 或 controller
- 什么时候必须从轻量任务升级为正式项目纳管

如果继续把这些判断全部留给不同 Agent 自行推断，就很难保证：

- `Codex`、`OpenClaw`、`Claude Code` 三者的行为一致
- 入口判断可审计、可复现
- 文档、skill、prompt 不发生长期漂移

## 问题

当前第三方 Agent 接入存在四个结构性问题：

1. 缺少一份显式的“任务入口 -> 运行模式 -> 能力路由”统一契约。
2. `AGENTS.md` 本身不足以承载完整接入说明，只能表达原则和边界。
3. 现有 overlay skill 更像内部运行时行为注入，而不是第三方公共 API。
4. 如果直接做一个“大总 Skill”承接所有能力，会破坏现有分层，并把正式接口重新折叠回 prompt 逻辑。

## 目标

建立一套对第三方 Agent 清晰、稳定、可扩展的接入方案，使得：

- 外部可以明确看到五类公开入口，而不是自行猜测
- 只有 `全自动科研推进` 默认进入正式纳管主链
- 其余四类入口默认允许轻量专项启动，但在必要时能明确升级为正式纳管
- `Codex` 与 `OpenClaw` 成为一等兼容目标
- `Claude Code` 默认复用同一接入层，不单独维护专有规则
- 正式机器接口仍然保持在 `profile / bootstrap / controller / overlay`
- 文档、skill、prompt 共用一套单一事实源，不发生规则分叉

## 非目标

- 不把 `AGENTS.md` 扩展成完整接入手册
- 不把某个单一 Skill 设计成新的总接口
- 不修改 `DeepScientist core`
- 不让第三方 Agent 直接依赖内部 overlay 文件路径作为正式契约
- 不把五类入口重新压缩回一个模糊的“自动理解一切”的自然语言入口

## 设计结论

### 1. 公开暴露五类入口

对外直接暴露以下五类入口，不隐藏在内部：

1. `全自动科研推进`
2. `文献调研 / 证据侦察`
3. `思路启发 / 研究设计`
4. `项目优化 / 补实验 / 继续推进`
5. `稿件生成 / 投稿包导出`

这样设计的原因是，真实用户手里的项目进度差异很大：

- 有些用户只有原始数据，确实要从零进入正式项目
- 有些用户只需要调研与方向收敛
- 有些用户已经做到中后期，只需要补证据、补实验、补交付

因此，入口必须面向“项目所处阶段”而不是只面向“平台内部 skill 名称”。

### 2. 两种运行模式

五类入口共享两种运行模式：

- `正式纳管模式`
  - 进入 `workspace / profile / bootstrap`
  - 纳入 `DeepScientist` 主运行链
  - 有 quest / study / portfolio 审计面
  - 支持持续推进、正式 mutation、正式交付

- `轻量专项模式`
  - 允许在没有完整正式项目接入的情况下启动
  - 适合一次性调研、思路发散、局部优化建议、初步稿件整理
  - 默认不承担长期状态管理

两种模式的关系不是能力包含关系，而是运行形态关系：

- `全自动科研推进` 默认直接进入 `正式纳管模式`
- 其余四类入口默认从 `轻量专项模式` 启动
- 其余四类入口一旦满足升级条件，必须切换到 `正式纳管模式`

### 3. 五类入口与能力路由

| 入口 | 默认运行模式 | 轻量起步范围 | 升级后的接入动作 | 正式接口面 | 升级后的主运行链 / 辅助路由 |
| --- | --- | --- | --- | --- | --- |
| `全自动科研推进` | `正式纳管模式` | 不适用 | `doctor -> bootstrap -> overlay-status` | `profile / bootstrap / controller / overlay` | 主运行链：`scout -> idea -> experiment -> write -> finalize`；`decision` 作为继续 / 停止 / 改题门控 |
| `文献调研 / 证据侦察` | `轻量专项模式` | 文献检索、证据整理、候选切入点归纳 | 当调研结果被正式采纳进研究主线时，执行 `doctor -> bootstrap -> overlay-status` | 升级后同上 | 轻量入口默认调用 `scout`；升级后可接 `idea -> experiment -> write -> finalize` |
| `思路启发 / 研究设计` | `轻量专项模式` | 候选路线生成、比较、收敛 | 当某条路线被选中并要正式推进时，执行 `doctor -> bootstrap -> overlay-status` | 升级后同上 | 轻量入口默认调用 `idea`，必要时配合 `scout`；升级后接 `experiment -> write -> finalize`，`decision` 作为门控 |
| `项目优化 / 补实验 / 继续推进` | `轻量专项模式` | 项目诊断、缺口识别、补实验建议 | 一旦开始持续执行补实验、更新研究主线或保留正式继续 / 停止判断，执行 `doctor -> bootstrap -> overlay-status` | 升级后同上 | 轻量入口默认先做 `decision + idea` 诊断；升级后主运行链进入 `experiment`，必要时再接 `write`，`decision` 继续负责门控 |
| `稿件生成 / 投稿包导出` | `轻量专项模式` | 初稿整理、章节改写、现有材料重组 | 一旦进入目标期刊约束、submission bundle 或 final delivery，执行 `doctor -> bootstrap -> overlay-status` | 升级后同上 | 轻量入口默认调用 `write`；升级后主运行链为 `write -> finalize`，`journal-resolution` 为目标期刊解析附加路由 |

这里的“轻量专项模式”不等于“一锤子买卖”。它表示：

- 默认先以局部任务启动
- 不要求一开始就进入正式 runtime 管理
- 但允许且必须在满足条件时升级为正式项目

其中需要特别明确两点：

- `项目优化 / 补实验 / 继续推进`
  - “项目诊断、补实验建议”可以轻量启动
  - “持续补实验并继续主线研究”一旦开始执行，就必须升级

- `稿件生成 / 投稿包导出`
  - “初稿整理、章节改写”可以轻量启动
  - “正式投稿包导出、final delivery”一旦开始，就必须升级

### 4. 从轻量专项模式升级为正式纳管模式的触发条件

只要满足以下任意一条，就必须升级：

1. 需要写入或更新正式研究状态。
2. 需要做数据资产层变更或统一 mutation。
3. 任务会跨多个阶段持续推进，而不再是单次局部响应。
4. 需要把继续 / 停止 / 改题 / 补 sidecar 的判断作为正式节点留痕。
5. 需要生成正式投稿交付物，例如 submission bundle 或 final delivery。
6. 任务需要后续可恢复、可接力、可复查，而不是停留在一次会话中。

可压缩成一句统一规则：

> 如果任务需要正式状态、正式变更、正式交付、后续接力中的任意一个，就必须从轻量专项模式升级为正式纳管模式。

### 5. 接入载体采用“单一事实源 + 双薄包装”

不采用“只靠 `AGENTS.md`”，也不采用“大一统总 Skill”。推荐做法是：

- 一个公开稳定的接入指南
  - 建议路径：`guides/agent_entry_modes.md`
  - 负责解释五类入口、两种运行模式、升级条件、正式接口边界

- 一个结构化路由清单
  - 建议路径：`templates/agent_entry_modes.yaml`
  - 作为单一事实源，保存 mode id、名称、前置条件、默认模式、路由链、升级规则

- 一个 `Codex` 薄入口 Skill
  - 负责识别五类入口、检查前置条件、分发到现有 skill / controller
  - 不承载科研能力本体，不替代正式接口

- 一个 `OpenClaw` 入口 prompt / agent card
  - 逻辑与 `Codex` 薄入口对齐
  - 不另起一套规则，只消费同一事实源

这套结构确保：

- 真正稳定的机器接口仍然是 `profile / bootstrap / controller / overlay`
- `Codex` 与 `OpenClaw` 共享同一入口事实源
- 文档和 prompt 的规则不会长期漂移

### 6. 对 `Claude Code` 的兼容表述

工程优先级上，先实现：

- `Codex` 的薄入口包装
- `OpenClaw` 的薄入口包装

`Claude Code` 不单独设计专有接入层。

但对外文档表述上，统一写为：

- 兼容 `Codex`
- 兼容 `Claude Code`
- 兼容 `OpenClaw`

实现方式是：

- 三者都消费同一套接入指南与结构化路由事实源
- 不为 `Claude Code` 增加独立规则体系
- 如果未来存在极薄兼容壳，也只能是对同一事实源的消费层，而不是新的事实源

### 7. 各类入口的用户心智模型

为了避免用户误解，公开文档里需要明确：

- `全自动科研推进`
  - 表示把任务作为一个正式研究项目纳入主运行链
  - 包含文献调研、思路启发、路线选择、实验推进、写作与交付
  - 正式主运行链采用 `scout -> idea -> experiment -> write -> finalize`
  - `decision` 负责继续 / 停止 / 改题等跨阶段门控

- 其余四类入口
  - 表示先以专项任务启动
  - 不是能力残缺版
  - 也不等于只能做一次
  - 只是默认不立即进入正式项目纳管

## 推荐后续落地顺序

1. 先补 `guides/agent_entry_modes.md`
2. 再补结构化路由清单 `templates/agent_entry_modes.yaml`
3. 再实现 `Codex` 薄入口 Skill
4. 再补 `OpenClaw` 入口 prompt / card
5. 最后在 README 与外部文档中统一加入五类入口与兼容表述

## 约束

- 五类入口必须保持公开可见，不再折回内部术语
- 正式机器接口仍以 `controller / CLI` 为中心，不得被入口 Skill 架空
- 不允许用启发式兜底代替正式升级规则
- 外部文档对兼容对象统一表述为 `Codex / Claude Code / OpenClaw`
