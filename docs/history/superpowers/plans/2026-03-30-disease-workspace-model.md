# Disease Workspace Model Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 MedAutoScience 的公开模板文档改成“病种级 workspace 管理多数据版本、多 study、多篇论文”的默认入口模型。

**Architecture:** 仅修改公开文档和模板，不改 CLI 或控制器。通过首页定义、架构文档补层级、bootstrap 讲启动顺序、profile 模板去单-study化，再补一份直给 quickstart，把默认心智模型统一起来。

**Tech Stack:** Markdown, TOML, Git

---

### Task 1: 固化首页默认模型

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 重读首页现状，定位需要替换的叙事段落**

Run: `sed -n '1,260p' /Users/gaofeng/workspace/med-autoscience/README.md`
Expected: 能看到当前首页更偏平台能力总览，尚未把 workspace 定义成病种级长期资产层。

- [ ] **Step 2: 修改首页，使 workspace / study / 论文产出面关系前移**

写入内容应覆盖：

```md
- 一个 workspace 默认对应一个病种或稳定专病主题
- workspace 维护共享数据底座、研究组合和投稿交付
- studies/ 对应多条研究线
- 平台目标是持续产出多篇论文，而不是只推进单次流程
```

- [ ] **Step 3: 自检首页是否仍保持面向医学用户、避免过度技术化**

Run: `sed -n '1,260p' /Users/gaofeng/workspace/med-autoscience/README.md`
Expected: 首页语言仍然偏医学用户可读，但默认模型已经清楚。

### Task 2: 补强 workspace 架构文档

**Files:**
- Modify: `guides/workspace_architecture.md`

- [ ] **Step 1: 在架构文档中补实体层级与基数关系**

需要明确：

```md
workspace -> dataset family/version -> study -> quest -> paper bundle
```

- [ ] **Step 2: 明确哪些是 workspace 级资产，哪些是 study 级消费面**

至少补充：

```md
- datasets/ 与 portfolio/data_assets/ 是 workspace 级
- studies/<study-id>/ 消费已登记版本
- 同一数据版本可被多个 study 复用
```

- [ ] **Step 3: 补“不该做什么”**

包括：

```md
- 不复制 legacy workspace 当模板
- 不在每个病种 workspace 内再 clone DeepScientist
- 不把单篇论文目录当成 workspace 顶层
```

### Task 3: 改 bootstrap 与 profile 模板

**Files:**
- Modify: `bootstrap/README.md`
- Modify: `profiles/workspace.profile.template.toml`

- [ ] **Step 1: 在 bootstrap 文档中加入新病种项目的最小骨架与首次启动顺序**

应覆盖：

```md
1. 建立病种级空 workspace
2. 放入 datasets/contracts/portfolio/studies/ops 最小骨架
3. 准备 profile
4. doctor
5. bootstrap
6. 再创建首个 study
```

- [ ] **Step 2: 在 profile 模板中改示例命名并补注释**

至少包含：

```toml
# 这是病种级 workspace profile，不是单篇论文配置
name = "my-disease-workspace"
```

- [ ] **Step 3: 复读模板与 bootstrap，确认命名不再强化单-study误解**

Run: `sed -n '1,240p' /Users/gaofeng/workspace/med-autoscience/profiles/workspace.profile.template.toml && sed -n '1,260p' /Users/gaofeng/workspace/med-autoscience/bootstrap/README.md`
Expected: 新病种项目的最小启动顺序与 profile 心智模型都清楚。

### Task 4: 新增直给 quickstart

**Files:**
- Create: `guides/disease_workspace_quickstart.md`

- [ ] **Step 1: 新增面向新病种项目的简明指南**

文档应包含：

```md
- workspace 是什么
- 目录骨架
- 数据资产与 study 的关系
- 首次启动顺序
- 常见误区
```

- [ ] **Step 2: 在 README 中加入该指南入口**

Run: `rg -n "disease_workspace_quickstart" /Users/gaofeng/workspace/med-autoscience/README.md /Users/gaofeng/workspace/med-autoscience/guides`
Expected: README 已能把读者导向该指南。

### Task 5: 验证与提交

**Files:**
- Modify: `README.md`
- Modify: `bootstrap/README.md`
- Modify: `guides/workspace_architecture.md`
- Modify: `profiles/workspace.profile.template.toml`
- Create: `guides/disease_workspace_quickstart.md`

- [ ] **Step 1: 逐文件检查文案是否统一**

Run: `rg -n "my-study|单篇|workspace|study|dataset family|paper bundle" /Users/gaofeng/workspace/med-autoscience/README.md /Users/gaofeng/workspace/med-autoscience/bootstrap/README.md /Users/gaofeng/workspace/med-autoscience/guides/workspace_architecture.md /Users/gaofeng/workspace/med-autoscience/guides/disease_workspace_quickstart.md /Users/gaofeng/workspace/med-autoscience/profiles/workspace.profile.template.toml`
Expected: 单-study旧叙事显著减少，病种级 workspace 叙事前移。

- [ ] **Step 2: 查看 git diff，确认只改文档与模板**

Run: `git diff -- README.md bootstrap/README.md guides/workspace_architecture.md guides/disease_workspace_quickstart.md profiles/workspace.profile.template.toml docs/superpowers/specs/2026-03-30-disease-workspace-model-design.md docs/superpowers/plans/2026-03-30-disease-workspace-model.md`
Expected: 仅包含本轮文档与模板改动。

- [ ] **Step 3: Commit**

```bash
git add README.md bootstrap/README.md guides/workspace_architecture.md guides/disease_workspace_quickstart.md profiles/workspace.profile.template.toml docs/superpowers/specs/2026-03-30-disease-workspace-model-design.md docs/superpowers/plans/2026-03-30-disease-workspace-model.md
git commit -m "docs: clarify disease workspace model"
```
