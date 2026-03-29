# README Medical Homepage Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `README.md` 重写为面向医学用户的 GitHub 首页，并把 Agent/技术细节迁移到专门文档中承接。

**Architecture:** README 只保留医学用户需要的项目定位、适用场景、人机分工、当前能力和技术入口。Agent 运行接口、CLI 与 mutation payload 示例集中到新的技术文档，`bootstrap/README.md`、`controllers/README.md` 和 `policies/*.md` 继续承担部署、实现与策略说明。

**Tech Stack:** Markdown, GitHub README, repository docs

---

### Task 1: 新增 Agent 接口承接文档

**Files:**
- Create: `docs/agent_runtime_interface.md`
- Reference: `README.md`
- Reference: `bootstrap/README.md`
- Reference: `controllers/README.md`
- Reference: `policies/data_asset_management.md`
- Reference: `policies/study_archetypes.md`
- Reference: `policies/research_route_bias_policy.md`

- [ ] **Step 1: 提取 README 中必须迁移的 Agent 细节**

记录需要从首页正文移出的技术内容：

- `Agent-first, human-auditable` 的技术化解释
- 数据资产相关 CLI 入口
- `apply-data-asset-update` 的定位
- mutation payload JSON 示例
- `workspace/profile/bootstrap` 的衔接路径
- policy 文档入口
- 原“仓库文档”列表中的技术入口

- [ ] **Step 2: 写出新文档骨架**

文档至少包含以下章节：

- 运行层定位
- 人类与 Agent 的分工
- 稳定接口入口
- 数据资产 mutation 示例
- mutation payload 的使用边界
- `workspace/profile/bootstrap` 的衔接方式
- 与部署和 policy 文档的衔接

- [ ] **Step 3: 把 CLI 和 JSON 示例迁入新文档**

从 `README.md` 中迁出命令和 payload 细节，改写为 Agent 能直接理解的说明，而不是首页说明文。

必须明确写出：

- 什么情况下优先用统一 mutation 入口
- 什么情况下只读查询即可
- payload 示例是接口示例，不是给医学用户手工填写的表单

- [ ] **Step 4: 校对入口路径**

确认新文档中提供到以下文档的清晰跳转：

- `bootstrap/README.md`
- `controllers/README.md`
- `policies/data_asset_management.md`
- `policies/study_archetypes.md`
- `policies/research_route_bias_policy.md`

- [ ] **Step 5: 自查是否满足“给 Agent 用，但人类可审计”**

检查文档是否同时回答：

- Agent 调什么
- 人类审什么
- 首页为什么不再直接展示这些细节
- 如何从运行接口文档继续进入 `workspace/profile/bootstrap`

- [ ] **Step 6: 做一次迁移映射核对**

逐项标记从 README 移出的技术块的唯一落点：

- CLI 命令清单
- mutation payload 示例
- 最小部署命令与字段说明
- 平台核心组成中的内部命名说明
- 原“仓库文档”列表

### Task 2: 重写 README 首页主叙事

**Files:**
- Modify: `README.md`
- Reference: `docs/superpowers/specs/2026-03-29-readme-medical-homepage-design.md`

- [ ] **Step 1: 重排标题区和首屏摘要**

把首屏调整为：

- Logo
- 中文主标题
- 面向医学用户的副标语
- 3 条首屏摘要
- 主示意图

并移除当前 badge 与过强的工程仓库首屏信号。

- [ ] **Step 2: 重写开篇定位**

在 README 前段明确：

- 外层称呼仍可用“平台”
- 本质定义是 `Agent-first, human-auditable` 的医学自动科研运行层
- 它不是给医学用户直接操作底层命令的工具箱
- 人类负责提出任务、提供数据、审阅结果和做关键决策
- Agent 负责调用运行层接口推进研究与交付

- [ ] **Step 3: 重写医学用户核心区块**

把首页主体改写为以下顺序：

- 这个项目适合谁
- 这个项目解决什么问题
- 当前已具备的关键能力
- 你最终会得到什么
- 适合哪些数据与研究类型
- 平台如何工作
- 默认优先研究场景

其中“平台如何工作”必须包含：

- 人类负责什么
- Agent 负责什么
- 平台如何作为稳定、可审计的运行层承接两者
- 内部组成只能以高层业务角色出现，不能退回工程命名表

- [ ] **Step 4: 把内部 taxonomy 改写为医学场景表达**

主页中不再直接展示英文 `archetype` id 表格，改用医学问题场景描述，并把细则入口交给 `policies/study_archetypes.md`。

- [ ] **Step 5: 保留真实能力边界**

确保改写后没有新增不存在的功能承诺，并保留“当前边界”区说明一期范围。

### Task 3: 接入技术 handoff 区

**Files:**
- Modify: `README.md`
- Reference: `docs/agent_runtime_interface.md`
- Reference: `bootstrap/README.md`
- Reference: `controllers/README.md`

- [ ] **Step 1: 新增 `details` 折叠区**

标题固定为“给技术同事 / AI 执行者”。

- [ ] **Step 2: 组织任务式入口**

折叠区至少提供以下路径：

- Agent 接入与运行接口
- 工作区接入与部署
- 控制器与内部能力
- 平台规则与策略

平台规则与策略入口必须显式覆盖：

- `policies/data_asset_management.md`
- `policies/study_archetypes.md`
- `policies/research_route_bias_policy.md`

- [ ] **Step 3: 从首页正文删除技术命令清单**

移除数据资产 CLI 清单、mutation payload 示例和最小部署命令块，不在首页正文保留这些细节。

同时处理以下来源块的迁移：

- 原“平台核心组成”中的内部命名表改写为业务角色说明
- 原“仓库文档”列表并入技术折叠区，避免重复导航

- [ ] **Step 4: 校对技术入口与正文分工**

检查首页正文只服务医学用户理解，技术折叠区只负责 handoff，不与正文重复讲解。

并逐项确认所有从 README 移出的技术块都有唯一落点。

### Task 4: 验证改写结果

**Files:**
- Verify: `README.md`
- Verify: `docs/agent_runtime_interface.md`

- [ ] **Step 1: 阅读最终 README 全文**

Run: `sed -n '1,320p' README.md`

Expected:

- 首屏先出现摘要，再出现主示意图
- 首屏三条摘要分别回答“适合谁 / 解决什么问题 / 最终得到什么”
- README 正文明确写出人类与 Agent 的分工
- 没有 CLI 命令块和 JSON payload 示例残留在首页正文
- 医学用户路径和技术 handoff 路径分明

- [ ] **Step 2: 阅读 Agent 接口文档**

Run: `sed -n '1,320p' docs/agent_runtime_interface.md`

Expected:

- 保留被迁出的命令和 payload 细节
- 清楚写明人类与 Agent 的分工
- 清楚标注 mutation payload 的使用边界
- 对技术同事有明确入口价值
- 能继续跳转到 `bootstrap/README.md`、`controllers/README.md` 和 3 份 policy 文档

- [ ] **Step 3: 审核技术入口完整性**

Run: `rg -n "给技术同事|AI 执行者|bootstrap/README|controllers/README|policies/data_asset_management|policies/study_archetypes|policies/research_route_bias_policy|agent_runtime_interface" README.md docs/agent_runtime_interface.md`

Expected:

- README 折叠区包含全部任务式入口
- 没有单独残留重复的“仓库文档”导航区
- 技术入口链接与新文档中的衔接路径一致

- [ ] **Step 4: 做 source-to-destination mapping audit**

逐项核对 spec 中的迁移映射表，确认每个来源块已经：

- 保留为业务表达
- 或下沉到唯一目标文档
- 或通过首页折叠区给出唯一入口

- [ ] **Step 5: 检查改动差异**

Run: `git diff -- README.md docs/agent_runtime_interface.md docs/superpowers/specs/2026-03-29-readme-medical-homepage-design.md docs/superpowers/plans/2026-03-29-readme-medical-homepage-rewrite.md`

Expected:

- README 变成用户首页而不是命令手册
- 技术细节被迁移但没有丢失
- 新增文档路径与折叠区入口一致
- 首页不再保留重复技术导航或工程命名表主导叙事
