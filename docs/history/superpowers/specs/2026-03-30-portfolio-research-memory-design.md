# Portfolio Research Memory Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

## 背景

`DeepScientist` 已有 quest/global memory，但它服务的是单个 quest 的长期连续性：

- 论文阅读笔记
- 失败模式
- 决策理由
- 可复用知识卡

这层能力不足以替代医学 disease workspace 需要的 `portfolio` 级研究资产，因为后者面向的是：

- 同一批核心数据还能做哪些课题
- 同一疾病当前高信号的研究方向是什么
- 哪些期刊是现实主投带、stretch 带、backup 带
- 这些判断如何跨多个 future study 复用，而不是只留在一个 quest 的记忆卡里

当前 `MedAutoScience` 已经有 `portfolio/data_assets`，但没有对称的 `portfolio research memory` 显式层。

## 问题定义

当前平台存在三个缺口：

1. 没有 `portfolio` 级研究记忆骨架
2. 没有 controller/CLI 来初始化和检查这层资产
3. 没有把“先读 workspace 研究记忆，再决定是否做外部调研”上升成默认流程

这会导致：

- 新 workspace 即使绑定了 `DeepScientist`，也只会拥有通用 memory，不会天然拥有疾病级研究资产骨架
- topic backlog、venue intelligence、疾病热点判断容易散落在聊天里或某一篇 study 里
- agent 会不断从空白开始思考，而不是显式继承 workspace 已积累的研究记忆

## 目标

把 `portfolio research memory` 上升为 `MedAutoScience` 的显性能力，并满足：

1. 新 workspace 初始化时自动生成最小骨架
2. 平台提供显式 controller / CLI 以便初始化和检查状态
3. scout / controller-first 默认优先读取这层资产
4. 这层资产同时支持人读和机读
5. 单篇 study 的 shortlist / framing / baseline 决策仍然保留在 study 内，不被 portfolio 层替代

## 非目标

本轮不做：

- 自动生成完整 topic landscape 的全自动 ranking 系统
- 自动联网刷新所有 disease 热点或期刊指标
- 替代 `DeepScientist` memory 本身
- 把 portfolio 级资产升级为 startup hard gate

portfolio research memory 是“优先读取的显式研究资产层”，不是新的 compute gate。

## 设计原则

### 1. 分层清晰

- `DeepScientist memory`
  - quest/global 的通用知识卡
- `study/*`
  - 单篇论文的 framing、shortlist、protocol、results
- `portfolio/research_memory/*`
  - 同一 disease workspace 跨 study 复用的研究资产

### 2. 一层骨架，两种表示

`portfolio/research_memory/` 同时包含：

- 人读 Markdown
- 机读 YAML registry

这样：

- 人类可以直接审阅、编辑、讨论
- controller / future scout 可以稳定发现并消费

### 3. 内容不是自由笔记，而是有明确职责

最小骨架固定为四个资产：

1. `README.md`
   - 说明这一层是什么，不是什么
2. `registry.yaml`
   - 机读索引，列出有哪些资产、职责、路径、状态
3. `topic_landscape.md`
   - 疾病当前高信号研究方向
4. `dataset_question_map.md`
   - 基于本 workspace 核心数据可以走出的课题地图
5. `venue_intelligence.md`
   - 期刊邻域、similar-paper 落刊、现实主投带/ stretch / backup 判断

## Registry contract

`registry.yaml` 采用稳定 schema：

```yaml
schema_version: 1
memory_layer: portfolio_research_memory
workspace_scope: disease_workspace
assets:
  - asset_id: topic_landscape
    title: Disease Topic Landscape
    path: topic_landscape.md
    status: seeded
    purpose: current high-signal directions for this disease area
  - asset_id: dataset_question_map
    title: Dataset Question Map
    path: dataset_question_map.md
    status: seeded
    purpose: what publishable studies this workspace data can support
  - asset_id: venue_intelligence
    title: Venue Intelligence
    path: venue_intelligence.md
    status: seeded
    purpose: journal neighborhood and evidence-backed venue memory
```

状态先支持：

- `stub`
- `seeded`
- `mature`

## 平台能力

新增 `med_autoscience.controllers.portfolio_memory`，至少提供：

1. `init_portfolio_memory(workspace_root=...)`
   - 初始化目录与文件
   - 若已有文件则保持幂等
2. `portfolio_memory_status(workspace_root=...)`
   - 报告 root、registry、各 asset 是否存在
   - 报告 seeded asset 数量

CLI 新增：

- `init-portfolio-memory`
- `portfolio-memory-status`

Workspace init 默认：

- 创建 `portfolio/research_memory/`
- 生成 wrapper scripts
- 在 `README.md` 与 `WORKSPACE_AUTOSCIENCE_RULES.md` 中说明这层资产要先读

## 流程顺序升级

`controller_first` 与 `scout` 要明确：

1. 先读 `portfolio/research_memory`
2. 再读 quest/global memory
3. 仍不足时才外部调研
4. 外部调研结果要写回 study 或 portfolio durable state

这不是硬 gate，但它是新的默认 discipline。

## 当前 workspace 的首轮种子内容

在 `DM-CVD-Mortality-Risk` 当前 workspace 中：

### `topic_landscape.md`

填充糖尿病当前高信号方向，但强调“只保留与本 workspace 数据和 future studies 相关的方向”，避免空泛综述。

### `dataset_question_map.md`

填充：

- 已锁定的首文
- 可以从同一批数据继续分叉出的 study 方向
- 不该在同一 study 内混做的方向

### `venue_intelligence.md`

把已经在 `study 001` 内形成的 shortlist evidence 上升为 portfolio 级期刊邻域记忆，并明确：

- 什么类型的问题适合 diabetology 主投带
- 什么情况下才能往 cardiology stretch 带走
- 哪些 venue judgement 是稳定可复用的
- 哪些 judgement 仍然必须等单篇 study baseline 结果出来后再判断

## 验收标准

1. `medautosci init-workspace` 新建 workspace 后自动带有 `portfolio/research_memory/`
2. `medautosci init-portfolio-memory --workspace-root ...` 可单独初始化这层资产
3. `medautosci portfolio-memory-status --workspace-root ...` 可返回结构化状态
4. `controller_first` 与 `scout` 文案明确要求优先读取这层资产
5. 当前糖尿病 workspace 已落地三份 seeded 资产
6. 现有测试通过，且不会破坏已有 `data_assets` / `journal_shortlist` 行为
