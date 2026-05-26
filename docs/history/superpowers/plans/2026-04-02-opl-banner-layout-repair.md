# OPL Banner Layout Repair Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `one-person-lab` 顶部 banner 中左侧 `Shared Foundation` 图标难以理解且与文字重叠、右侧底部状态卡片文字溢出的布局问题。

**Architecture:** 保持整张 banner 的总体尺寸、配色和信息层级不变，只重排左侧图标内部节点结构与底部状态卡片宽度分配。用 SVG 原生几何与文本坐标修复，不引入额外图片依赖。修复后通过本地渲染 PNG 做视觉核验。

**Tech Stack:** SVG, Git, `rsvg-convert`

---

## File Responsibilities

- `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner.svg`
  顶部 banner 的唯一真相源，负责左侧图标、标题区和底部状态卡片布局。
- `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner-check.png`
  本地渲染检查图，仅用于人工核验，不提交。

### Task 1: 先写出失败条件并用渲染图确认问题

**Files:**
- Modify: `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner.svg`
- Create: `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner-check.png`

- [ ] **Step 1: 记录当前失败条件**

失败条件：

```text
1. 左侧绿色节点下压到文字区，破坏图标区与文字区边界。
2. 左侧图标语义不清，无法稳定表达 Shared Foundation 的结构含义。
3. 右侧最末卡片 Presentation Ops 文本超出卡片边界。
```

- [ ] **Step 2: 渲染当前 SVG 作为基线检查**

Run:

```bash
rsvg-convert /Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner.svg -o /Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner-check.png
```

Expected: 生成 PNG，并能肉眼看到左侧重叠和右下角文字溢出。

### Task 2: 以最小改动修复左侧图标和底部状态卡片

**Files:**
- Modify: `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner.svg`

- [ ] **Step 1: 重排左侧 Shared Foundation 图标**

目标布局：

```text
- 左侧保留深色底卡
- 一个左主节点
- 右上四个浅色基础节点
- 一个右下绿色强调节点，但完全留在图标区内
- SHARED FOUNDATION 文本独立放在底部居中，不与任何节点重叠
```

- [ ] **Step 2: 底部卡片改成不等宽布局**

目标宽度分配：

```text
Research Ops: x=560 width=190
Grant Ops: x=770 width=150
Thesis Ops: x=940 width=150
Review Ops: x=1110 width=165
Presentation Ops: x=1295 width=205
```

- [ ] **Step 3: 降低最长标签的风险**

修正要求：

```text
- Presentation Ops 标题字号从 22 微降到 20
- 各卡片文字采用更一致的左内边距，而不是继续靠经验值硬顶边界
```

### Task 3: 重新渲染并验证结果

**Files:**
- Modify: `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner.svg`
- Create: `/Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner-check.png`

- [ ] **Step 1: 重新渲染检查图**

Run:

```bash
rsvg-convert /Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner.svg -o /Users/gaofeng/workspace/one-person-lab/assets/branding/opl-banner-check.png
```

Expected: 成功生成新 PNG。

- [ ] **Step 2: 检查修复结果**

检查标准：

```text
1. 左侧绿色节点不再压到文字区
2. SHARED FOUNDATION 文本与图标完全分层
3. Presentation Ops 不再溢出
4. 整张 banner 的视觉风格与现有 README 保持一致
```

- [ ] **Step 3: 清理并提交**

Run:

```bash
git -C /Users/gaofeng/workspace/one-person-lab status --short
```

Expected: 只出现预期中的 banner 资产改动；检查图不纳入提交。
