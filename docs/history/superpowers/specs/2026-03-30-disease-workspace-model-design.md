# Disease Workspace Model Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

## 背景

当前 `MedAutoScience` 已经把程序外置、profile 驱动、workspace 保留项目状态这套运行架构基本讲清楚，但默认入口叙事仍偏向“围绕一个课题推进到一篇稿件”的感觉。

这会带来两个问题：

- 新用户容易把 workspace 误解为单论文目录，而不是病种级长期研究资产层。
- 新病种项目难以一眼看懂私有数据、公开数据、study、quest、paper bundle 之间的关系。

而当前 `NF-PitNET` workspace 的根 README，反而更直接地表达了“共享数据底座 + 多课题 study 工作区”的设计思想。

## 目标

把 `MedAutoScience` 的公开模板和入口文档，明确调整为以下默认模型：

- 一个 workspace 对应一个病种或一个稳定专病研究主题。
- 一个 workspace 维护一批私有数据与公开数据资产及其版本。
- 一个 workspace 可以并行孵化多个 `study`。
- 一个 `study` 通常对应一条具体研究线，并服务一篇主稿或一组强关联投稿产物。
- `MedAutoScience` 的默认目标是让这批数据持续产生多篇可投稿论文，而不是只跑完某一条单次流程。

## 非目标

- 不改控制器逻辑、CLI 行为、数据资产 schema 或 runtime contract。
- 不把现有 legacy workspace 直接包装成模板母版。
- 不新增复杂生成器或脚手架命令。

## 设计决定

### 1. 首页先定义病种级 workspace

在根 `README.md` 中，先明确：

- `MedAutoScience` 面向的默认单位是病种级 workspace。
- workspace 的角色是共享数据底座、研究组合面和投稿交付面。
- `study` 是 workspace 内的单条研究线，而不是整个 workspace 本身。

### 2. 术语和层级前移

公开文档要显式区分以下层级：

- `workspace`
- `dataset family / version`
- `study`
- `quest`
- `paper bundle / submission package`

要让新用户不用读源码，也能知道“谁管理资产、谁消费数据、谁产出论文”。

### 3. 私有/公开数据与 study 的关系讲清楚

文档中明确：

- 私有与公开数据登记在 workspace 级资产层。
- `study` 消费这些已登记的数据版本，而不是自己成为真相源。
- 同一私有版本或公开数据线索可以被多个 `study` 复用。

### 4. 新项目启动顺序要直给

补一份面向新病种项目的简明指南，至少包含：

- 需要的最小目录骨架
- profile 要填什么
- 首次运行顺序
- 不该做什么

重点强调：

- 不复制旧 workspace
- 不在每个病种目录里 clone `DeepScientist`
- 不把单篇论文和病种 workspace 混为一层

### 5. 模板命名去单-study化

`workspace.profile.template.toml` 里的示例命名从 `my-study` 调整为病种或项目级命名，并增加注释，避免继续强化“一个 profile = 一个单篇研究目录”的误读。

## 预期修改面

- `README.md`
- `bootstrap/README.md`
- `guides/workspace_architecture.md`
- `profiles/workspace.profile.template.toml`
- 新增 `guides/disease_workspace_quickstart.md`

## 成功标准

- 新读者在首页就能看出默认单位是病种级 workspace，而不是单论文目录。
- 新病种项目的技术执行者能直接按文档建立最小骨架并接入外部 `MedAutoScience` / `DeepScientist`。
- 私有数据、公开数据、study 和投稿交付之间的关系不再需要靠猜。
