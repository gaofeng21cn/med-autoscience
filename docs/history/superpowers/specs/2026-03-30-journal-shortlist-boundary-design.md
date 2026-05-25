# Journal Shortlist Boundary Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

## 背景

当前 MedAutoScience 已有两类和期刊相关的能力：

- `resolve-submission-targets`
- `journal-resolution`

它们服务的都是“投稿格式解析与导出”问题，而不是“选目标期刊”问题。

这导致一个错误边界：

- agent 在研究尚处于 framing / scout 阶段时，提前调用 submission target / journal resolution 流程
- 并把“投稿前格式解析”误当成“目标期刊选择”流程

这次要修复的不是某个 workspace 的临时误用，而是平台级边界缺失。

## 问题定义

平台当前缺一层 `venue selection` 能力。

所以现在的错误不是单纯“agent 用错工具”，而是：

1. 平台只有 `submission target` contract，没有 `journal shortlist evidence` contract
2. startup boundary gate 只要求 shortlist 存在，不要求 shortlist 有证据
3. controller-first policy 把 `resolve-submission-targets -> journal-resolution` 写成了通用链路
4. 这会把“投稿格式流程”错误前置到“选刊阶段”

## 目标

把“选刊”和“投稿格式解析”拆成两个明确阶段：

1. 先做 `journal shortlist resolution`
2. 再做 `journal decision`
3. 最后才允许 `submission target resolution / journal-resolution`

同时把 startup gate 升级成硬门：

- 没有 evidence-backed shortlist，就不算 `journal_shortlist_ready`

## 非目标

- 不做完整自动化 venue ranking 系统
- 不做基于网络实时抓取的全自动期刊评分引擎
- 不在当前阶段自动决定最终主投刊

## 新边界

### 1. Journal shortlist stage

这是 `scout / framing` 阶段的一部分。

它回答：

- 理想情况下这篇文章能打到什么档次
- 最像我们的文章通常发到哪类刊
- 哪些期刊是现实主投带，哪些是 stretch，哪些只是 backup

它不回答投稿模板或引用格式。

### 2. Submission target stage

只有当 shortlist 已形成，且已经明确 primary target 或至少 primary candidate 时，才允许进入这一层。

它回答：

- 该期刊的 author instructions 是什么
- 是否映射到已有 publication profile
- citation style / template / package export 怎么做

### 3. Journal resolution stage

它是 submission target stage 的一部分，只负责 unresolved journal target 的官方要求解析。

它不再承担任何 venue discovery 责任。

## 新 contract

新增 `study.yaml -> journal_shortlist_evidence`。

每个候选刊至少包含：

- `journal_name`
- `selection_band`
  - `primary_fit`
  - `strong_alternative`
  - `stretch`
  - `backup`
- `fit_summary`
- `risk_summary`
- `official_scope_sources`
- `similar_paper_examples`
- `tier_snapshot`
- `confidence`

### `similar_paper_examples`

至少 1 条，字段至少包括：

- `title`
- `journal`
- `year`
- `source_url` 或 `pmid`
- `similarity_rationale`

### `tier_snapshot`

至少包含：

- `source`
- `retrieved_on`

并且至少包含以下字段之一：

- `quartile`
- `journal_impact_factor`
- `citescore`
- `category_rank`
- `acceptance_rate`

## 新 controller

新增：

- `resolve-journal-shortlist`

职责：

- 读取 `study.yaml`
- 解析并验证 `journal_shortlist_evidence`
- 检查 evidence 是否覆盖 `journal_shortlist`
- 输出 machine-readable resolved payload

它不负责联网抓取或自动补全缺失字段，只负责解析和校验 durable state。

## Gate 语义变更

现有 `startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]` 保持不变。

但 `journal_shortlist` 的语义升级为：

- 不再只是“有 shortlist 名单”
- 而是“有 evidence-backed shortlist，且 evidence 覆盖 shortlist”

## Controller-first policy 变更

期刊相关顺序改为：

1. `resolve-journal-shortlist`
2. shortlist / primary target decision
3. `resolve-submission-targets`
4. `journal-resolution`

明确禁止：

- 用 `resolve-submission-targets` 做 venue discovery
- 用 `journal-resolution` 做 shortlist generation

## 需要修改的表面

- `src/med_autoscience/journal_shortlist.py`
- `src/med_autoscience/controllers/journal_shortlist.py`
- `src/med_autoscience/controllers/startup_boundary_gate.py`
- `src/med_autoscience/controllers/study_runtime_router.py`
- `src/med_autoscience/policies/controller_first.py`
- `src/med_autoscience/submission_targets.py`
- `src/med_autoscience/overlay/templates/deepscientist-journal-resolution.SKILL.md`
- `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- `src/med_autoscience/cli.py`
- `src/med_autoscience/controllers/workspace_init.py`

## 验证标准

### 正向

- study 只有 shortlist 名单但没有 evidence 时，`journal_shortlist_ready = false`
- study 同时有名单和完整 evidence 时，`journal_shortlist_ready = true`
- `resolve-journal-shortlist` 能输出结构化结果
- `resolve-submission-targets` 与 `journal-resolution` 仍可在后续阶段正常工作

### 反向

- controller-first summary 不再把 `resolve-submission-targets -> journal-resolution` 表述成选刊链路
- journal-resolution skill 明确声明“不是选刊流程”
- scout skill 明确声明选刊应先走 `resolve-journal-shortlist`

## 兼容性处理

这是一次有意的 hardening，不做静默向后兼容。

结果是：

- 旧 study 若只有 `journal_shortlist` 名单而无 evidence，会重新变成 not ready
- 这是预期行为，因为旧状态本来就不足以支撑稳定选刊
