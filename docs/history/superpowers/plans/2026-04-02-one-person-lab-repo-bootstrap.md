# One Person Lab Repo Bootstrap Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `/Users/gaofeng/workspace/one-person-lab` 创建一个可直接发布到 GitHub 的 OPL 顶层蓝图仓库骨架，明确 `One Person Lab` 总纲、任务版图、共享底座和 `MedAutoScience` 子项目定位。

**Architecture:** 新仓库保持“文档型总集”而不是代码型产品仓库。根目录 `README.md` 承担对外总入口，`docs/` 下拆分为 operating model、task map、shared foundation、roadmap 四份稳定说明，所有内容围绕同一主叙事组织。

**Tech Stack:** Markdown, Git

---

## File Responsibilities

- `/Users/gaofeng/workspace/one-person-lab/README.md`
  顶层公开入口，负责定义 OPL、解释为什么需要它、展示任务版图、共享底座、当前项目矩阵和路线图。
- `/Users/gaofeng/workspace/one-person-lab/docs/operating-model.md`
  解释 OPL 的角色分工、运行原则和人机协作边界。
- `/Users/gaofeng/workspace/one-person-lab/docs/task-map.md`
  解释一人课题组的核心任务模块和模块之间的复用关系。
- `/Users/gaofeng/workspace/one-person-lab/docs/shared-foundation.md`
  解释 Asset / Memory / Governance / Delivery / Agent Execution 五层共享底座。
- `/Users/gaofeng/workspace/one-person-lab/docs/roadmap.md`
  解释当前已落地的 `MedAutoScience` 和未来的 workstreams。

### Task 1: 创建仓库骨架并初始化 git

**Files:**
- Create: `/Users/gaofeng/workspace/one-person-lab/README.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/operating-model.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/task-map.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/shared-foundation.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/roadmap.md`

- [ ] **Step 1: 创建目录骨架**

Run:

```bash
mkdir -p /Users/gaofeng/workspace/one-person-lab/docs
```

Expected: 目录 `/Users/gaofeng/workspace/one-person-lab` 和 `/Users/gaofeng/workspace/one-person-lab/docs` 存在。

- [ ] **Step 2: 初始化 git 仓库**

Run:

```bash
git -C /Users/gaofeng/workspace/one-person-lab init
```

Expected: 输出 `Initialized empty Git repository` 或等价信息。

### Task 2: 编写 README 总入口

**Files:**
- Create: `/Users/gaofeng/workspace/one-person-lab/README.md`

- [ ] **Step 1: 写入 README 主结构**

README 必须包含以下 section，并保持顺序一致：

```md
# One Person Lab

## OPL 是什么
## 为什么它不是单产品
## 一人课题组的任务版图
## 这些任务共享什么底座
## 当前项目矩阵
## 当前最成熟项目：MedAutoScience
## 路线图
## 延伸阅读
```

- [ ] **Step 2: 在 README 中明确 `MedAutoScience` 的子项目定位**

README 里必须出现这段意思等价的文字：

```md
`MedAutoScience` 是 `OPL` 体系下当前最成熟的第一个子项目。
它聚焦医学自动科研主线：从专病数据治理、研究推进、证据组织到论文与投稿交付。
```

- [ ] **Step 3: 在 README 中加入项目矩阵**

README 里必须包含这张矩阵：

```md
| 项目 | 负责什么 | 当前状态 |
| --- | --- | --- |
| `MedAutoScience` | 医学自动科研主线，从数据到论文交付 | Active |
| `Grant Ops` | 基金申请与基金评审工作流 | Planned |
| `Thesis Ops` | 学位论文与答辩工作流 | Planned |
| `Review Ops` | 审稿、评审与回复工作流 | Planned |
| `Presentation Ops` | 讲课、汇报与答辩材料工作流 | Planned |
```

### Task 3: 编写四份支撑文档

**Files:**
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/operating-model.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/task-map.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/shared-foundation.md`
- Create: `/Users/gaofeng/workspace/one-person-lab/docs/roadmap.md`

- [ ] **Step 1: 写 `operating-model.md`**

必须覆盖以下结构：

```md
# OPL Operating Model

## 核心判断
## 角色分工
## 运行原则
## 为什么这不是 prompt 集合
```

- [ ] **Step 2: 写 `task-map.md`**

必须按五类 workstreams 展开：

```md
# OPL Task Map

- Research Ops
- Grant Ops
- Thesis Ops
- Review Ops
- Presentation Ops
```

- [ ] **Step 3: 写 `shared-foundation.md`**

必须写清五层底座：

```md
# Shared Foundation

- Asset Layer
- Memory Layer
- Governance Layer
- Delivery Layer
- Agent Execution Layer
```

- [ ] **Step 4: 写 `roadmap.md`**

必须至少包含：

```md
# OPL Roadmap

## 当前阶段
## 下一阶段
## 更后续阶段
```

并且 `当前阶段` 里要明确 `MedAutoScience` 已成形，其他模块仍是 planned workstreams。

### Task 4: 做基础校验

**Files:**
- Modify: `/Users/gaofeng/workspace/one-person-lab/README.md`
- Modify: `/Users/gaofeng/workspace/one-person-lab/docs/operating-model.md`
- Modify: `/Users/gaofeng/workspace/one-person-lab/docs/task-map.md`
- Modify: `/Users/gaofeng/workspace/one-person-lab/docs/shared-foundation.md`
- Modify: `/Users/gaofeng/workspace/one-person-lab/docs/roadmap.md`

- [ ] **Step 1: 检查文件是否齐全**

Run:

```bash
find /Users/gaofeng/workspace/one-person-lab -maxdepth 2 -type f | sort
```

Expected: 至少看到 `README.md` 和 `docs/` 下四份文档。

- [ ] **Step 2: 检查 Markdown 改动有没有明显格式问题**

Run:

```bash
git -C /Users/gaofeng/workspace/one-person-lab diff --check
```

Expected: 无输出。

- [ ] **Step 3: 检查仓库状态**

Run:

```bash
git -C /Users/gaofeng/workspace/one-person-lab status --short
```

Expected: 显示新建文件，工作区内容与预期一致。
