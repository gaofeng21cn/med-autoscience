# Controller-First And Automation-Ready Design

Date: `2026-03-30`

## Context

当前 `MedAutoScience` 已经具备：

- workspace 初始化
- managed runtime 路由
- startup boundary gate
- submission target 解析
- reference paper 合同解析
- public data asset registry / impact / startup readiness

但在实际使用中仍暴露出两个稳定性问题：

1. 负责交互的 Agent 可能绕开已有成熟 controller / CLI / overlay skill，直接凭会话上下文自行完成文献调研、期刊判断或公开数据引入。
2. 当一个 study 的边界已经明确时，系统虽然具备 `create_and_start` / `resume` DeepScientist runtime 的能力，但还没有把“进入持续自动推进状态”做成默认而稳定的行为 contract，导致交互容易停留在碎片化人工问答。

## User-Level Requirements

当前用户对 `MedAutoScience workspace` 的要求可以压缩为两条：

1. 不要发明创造。优先使用成熟模块和稳定调用方式，Agent 不应在已有平台能力覆盖的任务上自由发挥。
2. 当项目边界已经明确、且满足自动推进条件时，应默认切换到 `DeepScientist runtime` 的自动持续执行，而不是继续反复人工交互；直到产出可供人类选择的内容，再回到人类决策。

## Problem Statement

当前平台已经有很多“控制面”能力，但缺少统一、显式、跨入口生效的两类框架级策略：

- `controller-first policy`
- `automation-ready policy`

这导致系统在“可做”与“默认会做”之间还有缝隙。

## Design Goals

### G1. Controller-first by default

对于平台已覆盖的高频研究动作，Agent 必须先读平台状态、调用平台 controller 或 skill，再决定是否需要外部执行器。

### G2. Controlled fallback, not freeform improvisation

只有当平台缺少成熟模块时，才允许使用 `agent-browser`、`web`、`mineru` 等外部工具直接执行。
即便执行成功，也必须回写到平台 durable state。

### G3. Automation-ready by default once boundaries are explicit

当 study 满足自动推进条件时，平台应默认让 managed runtime 进入自动持续执行，而不是把大量“普通 route 选择”留给人工交互。

### G4. New workspace inherits this automatically

新的 workspace 不需要靠额外人工规则补丁，初始化后默认具备上述约束。

## Non-Goals

- 不在本次设计中新增新的外部检索引擎或数据下载器。
- 不尝试把所有自由任务都强行映射为 controller。
- 不修改 `DeepScientist` 上游源代码。

## Current State Assessment

### What already exists

- `submission_targets` / `journal-resolution`
- `reference_papers`
- `data-assets-status`
- `tooluniverse-status`
- `apply-data-asset-update`
- `startup-data-readiness`
- `study_runtime_router.ensure_study_runtime`

### What is missing

1. 还没有统一 policy 告诉 Agent：
   - 哪些任务必须先查哪些成熟模块
   - 何时允许 fallback
   - fallback 后必须回写哪里

2. 还没有统一 policy 告诉 runtime：
   - 何时一个 study 已经“自动推进就绪”
   - 在这种状态下应该减少人工交互、偏向 autonomous managed execution

3. workspace 初始化模板虽然会写入 startup boundary 规则，但不会把上述两条策略做成默认 contract。

## Considered Approaches

### Option A. Documentation-only

只改 README、workspace rules、entry prompt。

结论：

- 不足。
- 这只能改善提示，不会稳定约束 Agent 行为。

### Option B. Prompt-heavy

把 controller-first checklist 只注入 overlay skill 和 startup brief。

结论：

- 比文档更强，但仍然不是统一的框架 contract。
- 不足以满足“稳定可控”。

### Option C. Framework-level policy plus template propagation

新增统一 policy 源，并把它注入：

- workspace init 模板
- runtime startup contract / brief
- overlay skill 文本
- 必要的 gate / status output

结论：

- 这是本次采用方案。

## Chosen Design

### 1. Introduce `controller_first_policy`

在 `MedAutoScience` 中新增统一的 policy/rendering 模块，定义：

- 平台已成熟覆盖的任务类型
- 每类任务对应的优先 controller / CLI / skill
- fallback 何时允许
- fallback 后的回写要求

首批纳入的任务域：

- literature_and_reference_anchors
- submission_targets_and_journal_resolution
- public_dataset_discovery_and_registration
- startup_and_publication_gates

### 2. Introduce `automation_ready_policy`

新增统一规则，明确：

- 边界何时算“已明确到足以自动推进”
- 哪些条件满足后应默认偏向自动创建 / 自动恢复 runtime
- 哪些情形仍然需要停留在人工澄清阶段

建议首批自动推进就绪信号：

- startup boundary 已通过
- execution engine = `deepscientist`
- auto_entry = `on_managed_research_intent`
- default entry mode 命中 managed route
- decision_policy = `autonomous`
- auto_resume = true

并且在 runtime brief 中明确：

- ordinary route ambiguity is not a reason to ask the user
- continue until durable outputs requiring human selection are produced

### 3. Propagate both policies through workspace initialization

`init-workspace` 生成的新 workspace 默认包含：

- controller-first rules
- automation-ready rules
- 对 fallback 的受控边界说明

这意味着新的 workspace 不需要事后再打补丁才知道如何约束 Agent。

### 4. Inject policies into runtime-facing surfaces

在这些位置自动注入渲染后的 policy 摘要：

- startup brief / custom brief
- workspace-generated rules file
- relevant overlay skills
- optional status payload fields for auditability

### 5. Tighten managed execution contract

不是简单追求“更自动”，而是让“边界明确后自动推进”成为默认行为。

因此：

- 在满足自动推进条件时，`ensure-study-runtime` 的默认结果应继续保持 `create_and_start` / `resume`
- 同时在 startup contract 中加强文案，明确普通 route 选择不应回退到人工交互
- 只在真正需要外部凭证、用户价值判断或安全边界确认时才升级为人工等待

## Proposed File/Module Changes

### New modules

- `src/med_autoscience/policies/controller_first.py`
- `src/med_autoscience/policies/automation_ready.py`

### Updated modules

- `src/med_autoscience/controllers/workspace_init.py`
- `src/med_autoscience/controllers/study_runtime_router.py`
- `src/med_autoscience/controllers/startup_boundary_gate.py`
- `src/med_autoscience/overlay/installer.py`

### Updated templates

- relevant overlay templates for `scout`, `decision`, `write`, `journal-resolution`
- workspace-generated rules/readme templates
- agent entry resources if needed

## Expected Behavioral Changes

### Controller-first examples

When the task is:

- journal shortlist / target journal resolution
  - first use `resolve-submission-targets`
  - then use `journal-resolution` when unresolved

- literature anchor setup
  - first inspect / resolve `reference_papers`

- public external dataset work
  - first use `data-assets-status`, `startup-data-readiness`, `tooluniverse-status`
  - after acquisition, require `apply-data-asset-update`

### Automation-ready examples

When a study is already bounded and ready:

- do not keep the system in repeated human clarification loops
- create or resume the managed DeepScientist quest
- let it continue until it produces durable options, reports, or decision artifacts for human selection

## Testing Plan

### Unit tests

- policy rendering tests
- workspace init output includes new rules
- startup contract contains automation-ready and controller-first guidance
- overlay rendering includes the new policy blocks

### Behavioral tests

- managed runtime status prefers `create_and_start` / `resume` when automation-ready conditions hold
- blocked startup still stays in scout/intake/decision
- controller-first guidance appears for new workspace outputs

### Regression tests

- existing startup boundary behavior remains intact
- existing submission target / reference paper controllers keep working
- workspace init remains backward compatible for existing profiles

## Rollout Notes

- This change should be framework-first.
- Workspace-local patches remain useful, but should no longer be required for new projects.
- Existing workspaces can adopt the stronger behavior by re-running generated assets or manually syncing updated templates/rules.

## Success Criteria

The design is successful if:

1. A newly initialized workspace explicitly inherits controller-first and automation-ready rules.
2. An Agent using MedAutoScience defaults to mature platform modules before freeform execution.
3. Once a study is bounded and startup-ready, managed runtime defaults to autonomous continuation instead of repeated manual prompting.
4. Fallback execution remains possible only when the platform truly lacks coverage, and always requires durable write-back.
