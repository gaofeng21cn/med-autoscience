# Journal Package Builtins Design

Owner: `MedAutoScience`
Purpose: `Record landed MAS runtime design support for journal requirement and target-specific package evolution.`
State: `active_runtime_support_landed`
Machine boundary: Human-readable design support only; implementation truth remains in source, tests, contracts, generated artifacts, and verification receipts.

## 当前读法

本文记录 `journal_requirements` 与 `journal_package` 内置化的设计边界。对应 implementation 已经进入当前 source、CLI、controller、publication gate 与 focused tests；本文不再承担 active implementation plan，也不作为投稿质量、最终期刊 ready 或 publication-ready 证明。

当前机器真相入口：

- `src/med_autoscience/journal_requirements.py`
- `src/med_autoscience/controllers/journal_requirements.py`
- `src/med_autoscience/controllers/journal_package.py`
- `src/med_autoscience/controllers/publication_gate_parts/state_resolvers.py`
- `src/med_autoscience/controllers/publication_gate_parts/report_builders.py`
- `src/med_autoscience/controllers/publication_gate_parts/supervisor_and_cli.py`
- `tests/test_journal_requirements_controller.py`
- `tests/test_journal_package_controller.py`
- `tests/test_publication_gate_cases/*`

历史实现计划归 [Journal Package Builtins Implementation Plan](../../history/program/journal_package_builtins_upgrade_plan.md)。后续差距只按 active gap plan 和 live receipt/evidence 判断，不能从本文的早期设计措辞重新打开已落地 implementation checklist。

## 背景

当前 `med-autoscience` 在 publication 侧已经具备以下能力：

1. `resolve-journal-shortlist`
   提供证据化的选刊 shortlist，已经进入 CLI 和 controller-first contract。
2. `submission_minimal` / `resolve-submission-targets`
   提供通用投稿包导出，以及少数 `publication_profile` 的期刊家族化导出。
3. `resolve-journal-requirements`
   将官方 author instructions / guideline URL 与结构化字段固化到 study-local durable requirement manifest。
4. `materialize-journal-package`
   将 target-specific journal package 物化到浅层 `submission_packages/<journal_slug>/`，并写入 manifest、requirements snapshot、formatting boundary 和 zip。
5. `publication_gate`
   感知 primary journal target、requirements 与 journal package 状态；requirements 已 resolved 但 package missing / stale 时可触发 materialization sync。

当前缺口不再是缺少 repo 级 controller-owned journal-facing workflow。剩余边界是：真实投稿期刊需要用户/作者显式确认，official requirement 内容仍需可审计来源，journal package 只能作为 `journal_targeted_projection`，除非 manifest 记录 confirmed target、requirements/QC current 和 publication gate / quality authority 允许的证据链。

## 目标

本设计目标已经作为 MAS 内置能力落地：

1. 查找合适期刊
2. 将论文整理成符合该期刊格式的 target-specific package

当前链路覆盖从 journal shortlist 到 target-specific package materialization。正式投稿和 publication-ready 仍必须由 MAS publication gate、AI reviewer / auditor quality gate、artifact authority、target confirmation 和 owner receipt 共同授权。

## 非目标

- 不在本轮引入任意网页抓取器或浏览器自动化作为默认强依赖。
- 不把所有期刊都硬编码成一组 `publication_profile`。
- 不重写现有 `submission_minimal` 的 generic package contract。
- 不改变 study runtime、OPL / Temporal hosted runtime owner split 或 publication gate 的基础拓扑。

## 设计原则

### 1. controller-owned

选刊、官方要求固化、期刊包物化都必须有明确 controller 和 CLI surface，不能只停留在 prompt/skill 层。

### 2. official-source-backed

期刊格式要求必须来自官方 author instructions、submission guideline 或官方 template。系统保存结构化 contract，同时保留来源 URL 与提取时间。

### 3. generic 与 target-specific 分层

`submission_minimal` 继续作为 canonical generic package。

`journal package` 作为 target-specific projection，建立在 generic / manuscript artifact 之上，但拥有独立 manifest、输出目录和验证规则。

当目标期刊只来自 shortlist、study 配置或 controller 候选，而没有用户/作者显式确认时，`journal package` 必须标注为 journal-targeted projection，不得表述成最终 journal-ready formatting。默认人读入口仍然是 `manuscript/current_package/`。

### 4. stable shallow handoff

用户侧浅层交付面输出到：

`studies/<study-id>/submission_packages/<journal_slug>/`

这条路径属于稳定浅层交付面，不再落到容易被 controller 刷新的 `manuscript/` 子树中。

该路径不是第二个真相源。它必须在 manifest 中记录 source authority、target confirmation 和 formatting boundary；未确认期刊时只能作为 derived preview / review surface。

## 方案比较

### 方案 A：只增强 shortlist，格式化继续外层手工处理

优点：
- 改动小
- 对现有流程扰动低

代价：
- 最关键的期刊格式化仍然缺少 repo 级能力
- 继续依赖人工补包
- 无法形成稳定交付面

### 方案 B：引入 journal requirement contract + journal package materializer

优点：
- 能覆盖用户真正关心的两项能力
- 与现有 `submission_minimal`、`study_delivery_sync` 自然衔接
- 可以逐步增加支持的期刊家族与单刊模板

代价：
- 需要新增 contract、controller、manifest 和测试

### 方案 C：把所有目标期刊都强行收敛成统一 `publication_profile`

优点：
- 表面结构简单

代价：
- 单刊差异会被压扁
- 官方要求无法准确落地
- 很快变成大量例外逻辑

已采用方案 B。方案 A 只保留为历史取舍；方案 C 继续作为禁止方向。

## 架构设计

### A. Journal Shortlist Surface

保留 `publication resolve-journal-shortlist` 作为 shortlist controller。

已落地能力：

- 在 shortlist 结果中明确 `recommended_primary_candidate`
- 输出可直接供下游 target 解析复用的 `journal_slug`
- 补齐 shortlist summary 到 durable artifact，便于 study 侧和 portfolio memory 复用

### B. Journal Requirement Resolution Surface

已落地 controller 与 CLI：

- `publication resolve-journal-requirements`

输入：

- `--study-root`
- `--journal-name` 或 `--journal-slug`
- `--official-guidelines-url`
- 可选 `--publication-profile`

输出：

- study 侧 durable contract 文件
- 结构化 requirement manifest
- 人类可读 markdown 摘要

durable 文件：

- `paper/journal_requirements/<journal_slug>/requirements.json`
- `paper/journal_requirements/<journal_slug>/requirements.md`

结构化字段包括：

- `journal_name`
- `journal_slug`
- `official_guidelines_url`
- `retrieved_at`
- `publication_profile`
- `abstract_word_cap`
- `title_word_cap`
- `keyword_limit`
- `main_text_word_cap`
- `main_display_budget`
- `table_budget`
- `figure_budget`
- `supplementary_allowed`
- `title_page_required`
- `blinded_main_document`
- `reference_style_family`
- `template_assets`
- `required_sections`
- `declaration_requirements`
- `submission_checklist_items`

### C. Journal Package Materialization Surface

已落地 controller 与 CLI：

- `publication materialize-journal-package`

输入：

- `--paper-root`
- `--study-root`
- `--journal-slug`

行为：

1. 读取 primary submission target
2. 读取已固化的 journal requirements
3. 从 generic manuscript artifacts 和 journal-specific surface 生成 target-specific package
4. 输出到 shallow package root
5. 写回 manifest 供 publication gate / human audit 使用

输出根目录：

- `studies/<study-id>/submission_packages/<journal_slug>/`

当前内容：

- `main_manuscript.docx`
- `main_manuscript.pdf`
- `title_page.md`（当 requirements 要求 title page）
- `declarations.md`
- `tables/`
- `figures/`
- `supplementary/`
- `SUBMISSION_TODO.md`
- `audit/journal_requirements_snapshot.json`
- `audit/submission_manifest.json`
- `<journal_slug>_submission_package.zip`

### D. Delivery Sync Integration

`submission_packages/<journal_slug>/` 是已落地的稳定浅层交付面。

现有 `manuscript/current_package` 保留为当前主审阅入口。

用户如果已经选定主投期刊，journal package 可以记录 confirmed target。未确认时，package manifest 必须保持 `journal_targeted_projection` / `target_confirmation_status=unconfirmed`，不得写成最终 journal-ready formatting。

### E. Publication Gate Integration

publication gate 已接入 journal package 维度检查：

- primary target 是否明确
- official requirements 是否已固化
- shallow journal package 是否存在
- journal package manifest 是否新鲜
- required TODO 是否存在
- 关键主文件是否齐全

generic package 完整性与 journal package 完整性分别报告。

## 受影响模块

### 已接入

- `src/med_autoscience/cli.py`
- `src/med_autoscience/controllers/submission_targets.py`
- `src/med_autoscience/controllers/study_delivery_sync.py`
- `src/med_autoscience/controllers/publication_gate.py`
- `src/med_autoscience/policies/controller_first.py`

### 已新增

- `src/med_autoscience/controllers/journal_requirements.py`
- `src/med_autoscience/controllers/journal_package.py`
- `src/med_autoscience/journal_requirements.py`
- `tests/...` 对应 controller / CLI / gate / delivery sync 覆盖

## 数据流

1. shortlist
   `resolve-journal-shortlist` 生成证据化候选
2. target
   `resolve-submission-targets` 锁定 primary target
3. requirements
   `resolve-journal-requirements` 固化官方投稿要求
4. package
   `materialize-journal-package` 物化 target-specific package
5. sync
   `study_delivery_sync` 投影到 shallow `submission_packages/<journal_slug>/`
6. gate
   `publication_gate` 检查 generic + journal-specific 交付完整性

## 验证设计

### 测试

- controller 单测
- CLI 集成测试
- delivery sync 测试
- publication gate 测试

### 关键断言

- shortlist 结果可生成稳定 `journal_slug`
- journal requirements manifest 能被结构化解析
- journal package 能输出到 `submission_packages/<journal_slug>/`
- `manuscript/` 被刷新时，`submission_packages/` 不受影响
- gate 能准确识别 journal package 缺件

## 风险

### 1. 官方要求来源异构

当前实现允许通过 study-local resolved artifact / payload 输入官方 requirement 内容；durable contract、schema、controller 和 output surface 已稳定。风险仍在来源可审计性和真实期刊要求更新，而不是 repo 内置能力缺失。

### 2. 单刊差异多

先用“通用 schema + 单刊 requirement snapshot + 少量 family adapter”模式推进，避免一开始就写死大量模板分支。

### 3. 现有 `publication_profile` 边界

`publication_profile` 继续承担家族级排版基底；单刊要求通过 `journal_requirements` 叠加，不挤占 profile 的职责。

## 当前验收读法

以下条件已由当前 source / CLI / focused tests 覆盖为内置能力边界：

1. `publication resolve-journal-shortlist` 继续可用，且结果能稳定支撑后续 target / package 链路。
2. `publication resolve-journal-requirements` 可保存官方要求快照和结构化 contract。
3. `publication materialize-journal-package` 能生成稳定浅层投稿包。
4. `study_delivery_sync` 能把 journal package 同步到 `submission_packages/<journal_slug>/`。
5. `publication_gate` 能感知 journal package 完整性与缺件。
6. 覆盖对应测试，并通过 repo 验证入口。

这组验收只表示 MAS 具备 target-specific package projection 能力。它不等于具体论文线已经 publication-ready、submission-ready、quality-approved、artifact mutation authorized 或 target confirmed。真实 paper-line 仍需走 active gap plan 中的 owner receipt、publication gate、AI reviewer / auditor record、human gate 和 no-forbidden-write proof。
