# DeepScientist Compatibility Shield Design

Date: `2026-03-31`

## Context

当前 `MedAutoScience` 作为 `DeepScientist` 的下游运行层，已经承担了：

- workspace profile 与 runtime contract
- medical overlay 与 manuscript surface 控制
- startup boundary / runtime reentry 管理
- paper-facing manuscript 与 figure/table 审核入口

但这次真实运行暴露出一个更严重的问题：`DeepScientist` 最新版本的行为变化，已经可以穿透 `MedAutoScience` 现有约束，直接污染医学论文写作与主文图面。

本次污染不是抽象担忧，而是已经发生的事实：

1. 运行环境里缺少 `matplotlib` / `pandas` 时，系统没有被阻断，反而继续走了标准库手拼 SVG 的降级路径。
2. 运行时实际读取的是上游 `DeepScientist` 的 `write` / `figure-polish` skill，而不是 workspace 的 `MedAutoScience` overlay。
3. `MedAutoScience` 目前没有覆盖 `figure-polish`，因此 figure 生成与打磨阶段仍可能落回上游默认叙事。
4. 图内出现了不属于医学 SCI 主文图的长段 narrative、summary card、工具宣介和工程化术语。

这意味着：如果不补上更强的兼容防护层，`DeepScientist` 的上游升级会持续破坏医学写作面，而这会直接影响 study 结果的可信性。

## Problem Statement

当前问题不是单点 bug，而是下游运行层缺少一层足够硬的 compatibility shield。

更具体地说，系统现在缺三类保证：

1. `runtime dependency guarantee`
   - 论文 figure 所需最小 Python 面并没有被视为受管 contract。
   - 缺关键依赖时没有强制安装，也没有强制失败。

2. `skill source guarantee`
   - `MedAutoScience` 没有稳定保证运行时实际使用的是自己的 overlay skill。
   - 上游 quest skill 副本可以在启动前反向覆盖 workspace overlay。

3. `medical figure surface guarantee`
   - figure 生成与 polish 阶段没有被稳定约束为医学 SCI 图面。
   - 即使 caption 被清理，图内可见文字仍可能被上游 prompt 或自由脚本污染。

## User-Level Requirements

当前需求可以压缩为四条：

1. 在仍然使用原版 `DeepScientist` 的前提下，最大化降低上游行为漂移对医学 study 的破坏。
2. 关键绘图依赖缺失时，不允许降级到手拼 SVG 或其他非受管路径。
3. `MedAutoScience` 必须稳定接管医学写作与 figure polish 的 manuscript-facing 规则。
4. 如果原版 `DeepScientist` 已经无法被稳定约束，则必须有清晰的升级路径切换到自维护分叉。

## Design Goals

### G1. Keep upstream DeepScientist when controllable

优先继续使用原版 `DeepScientist`，但只在其行为可以被 `MedAutoScience` 稳定约束、验证和审计时成立。

### G2. No silent degradation

关键绘图依赖缺失时，允许的路径只有：

- 受管安装成功后继续
- 安装或验证失败后直接阻断

不允许继续进入手拼 SVG、自由文本拼图或其他降级路线。

### G3. Workspace overlay must be authoritative

对于被 `MedAutoScience` 接管的医学 route，workspace overlay 必须是运行时权威源，而不是“尽量覆盖”。

### G4. Figure surface must be manuscript-hard-gated

医学主文图面不能只靠提示词约束，必须有运行时与审计面的双重硬 gate。

### G5. Fork only when shield is insufficient

不要过早维护重量级分叉；只有当 compatibility shield 已被证明不足时，才切换到 `MedAutoScience-managed DeepScientist fork`。

## Non-Goals

- 不在本次设计中重写 `DeepScientist` 的全部 runtime。
- 不试图把所有 figure 生成逻辑都迁移到 `MedAutoScience` 自己实现。
- 不在本次设计中直接重做已污染论文的全部写作与 figure 资产；本次先修系统护栏。

## Current Root Causes

### 1. Managed Python contract is too weak

`med-autoscience` 当前自己的依赖面没有把 `matplotlib` / `pandas` 当成受管 runtime contract，因此：

- `doctor` 无法报告 figure runtime 是否完整
- `bootstrap` 无法安装 figure runtime 缺口
- `ensure-study-runtime` 无法在 study 进入前阻断缺包状态

### 2. Codex home assembly lets quest skills overwrite workspace overlay

当前 `DeepScientist` runner 会在准备 project-local `CODEX_HOME` 时，把 `quest/.codex/skills` 整体复制到 `workspace/.codex/skills`。这意味着 quest skill 可以覆盖同名 workspace skill，直接导致医学 overlay 失效。

### 3. Figure-polish route is not covered by MedAutoScience overlay

当前 `MedAutoScience` overlay 已覆盖 `write`、`finalize` 等 skill，但没有覆盖 `figure-polish`。这导致 figure bundle 在关键的 render-inspect-revise 阶段仍可能沿用上游 prompt。

### 4. Figure surface gate is incomplete

现有 `medical_publication_surface` 已能阻断 caption/catalog 中的工具宣介和工程术语，但还不够：

- 需要更明确地区分图内允许文本与禁止文本
- 需要稳定覆盖 SVG/JSON 等 figure text asset 的可见文字
- 需要把“医学 SCI 图面语义”前推到生成/打磨阶段，而不只是事后清洗

## Considered Approaches

### Option A. Stay on upstream and only add more post-hoc cleaning

做法：

- 继续使用原版 `DeepScientist`
- 只强化 `medical_publication_surface`
- 只在污染出现后再清理 caption、catalog 和 SVG 文字

结论：

- 不接受。
- 这是事后补救，不是系统性预防。
- 用户已明确不接受降级与补丁式兜底。

### Option B. Build a MedAutoScience compatibility shield on top of upstream

做法：

- 保持原版 `DeepScientist`
- 在 `MedAutoScience` 层补齐依赖 contract、skill authority、figure hard gate
- 同时引入“已验证 DeepScientist 版本”概念

结论：

- 这是本次推荐方案。
- 它能以更低维护成本解决当前问题，并保留后续切 fork 的空间。

### Option C. Immediately maintain a MedAutoScience fork of DeepScientist

做法：

- 直接把当前需要的 `DeepScientist` 修改都收进自维护分叉
- 以后由 `MedAutoScience` 负责 runtime 与 runner 语义

结论：

- 现在还不是第一选择。
- 成本高，仓库更重，升级与回归验证压力更大。
- 只有当 Option B 被证伪时才应采用。

## Chosen Design

采用 `Option B`: 在保留原版 `DeepScientist` 的前提下，为 `MedAutoScience` 增加一层更硬的 compatibility shield，并明确 fork 触发条件。

## Design

### 1. Introduce a managed figure runtime contract

新增统一的 figure runtime contract，明确：

- `matplotlib`
- `pandas`

是医学论文 figure 的强制依赖，而不是可选依赖。

该 contract 必须同时覆盖三个入口：

- `doctor`
- `bootstrap`
- `ensure-study-runtime`

行为要求：

1. `doctor`
   - 报告 figure runtime 是否完整
   - 报告当前解释器下两者是否可导入及版本号

2. `bootstrap`
   - 当依赖缺失时，使用受管 `uv` 环境安装
   - 安装后立刻做 import 验证
   - 验证失败则 bootstrap 失败

3. `ensure-study-runtime`
   - 在允许创建 / 启动 / 恢复 study runtime 之前，先确认 figure runtime contract 已通过
   - 若未通过，直接阻断 managed runtime 进入

这一层不是“绘图时再看”，而是进入 study runtime 前就必须满足的 contract。

### 2. Ban non-managed SVG fallback for paper-facing figures

新增明确规则：

- 对 manuscript-facing figure route，不允许因为缺少 `matplotlib/pandas` 而转去标准库手拼 SVG
- 不允许把“系统里有 `rsvg-convert` / `inkscape`”解释为可继续的信号
- 任何 paper figure 生成必须显式依赖通过 figure runtime contract 的受管 Python 入口

这条规则应同时体现在：

- runtime contract 文档
- overlay skill 约束
- figure surface gate 的阻断文案

### 3. Make MedAutoScience overlay authoritative for managed skills

对被 `MedAutoScience` 接管的 skill，workspace overlay 必须成为运行时权威源。

需要达到的效果：

1. 准备 `CODEX_HOME` 时：
   - 先复制 workspace `.codex`
   - 再处理 `quest/.codex/skills`
   - quest skill 只能补缺，不能覆盖同名 workspace skill

2. 对于 overlay 管辖的 skill：
   - 必须能从审计面看到最终使用的是哪一个来源
   - 如果不是 `MedAutoScience` overlay，直接视为 contract 失败

3. `doctor` / contract 输出中要增加：
   - `write` 实际来源
   - `finalize` 实际来源
   - `figure-polish` 实际来源

### 4. Add a MedAutoScience `figure-polish` overlay

当前 figure 污染最危险的缺口之一，是 `figure-polish` 不在 overlay 覆盖面内。

因此新增完整 `figure-polish` overlay，明确医学图面约束：

- 主文图是证据图，不是信息图
- 图内可见文字仅允许：
  - panel label
  - axis label
  - legend
  - necessary statistical annotation
  - minimal group/sample note
- 不允许：
  - summary card
  - narrative paragraph
  - claim banner
  - tool/vendor/service mention
  - repo / website disclosure
  - engineering route labels
  - AI system self-advertising

同时明确：

- figure polish 不得改变 claim 语义
- figure polish 不得引入 manuscript 未定义的方法学标签
- figure polish 只允许做医学论文图面的表达收敛，而不是自由创作

### 5. Strengthen medical figure surface hard gate

`medical_publication_surface` 需要升级为 figure manuscript hard gate，而不是只做 caption 清洗。

新增检查目标：

- generated SVG
- figure metadata JSON
- figure catalog entries
- caption / note / manuscript_purpose
- any text asset exported with a main-text figure

新增阻断条件：

- 图内 prose 叙述
- 工具 / vendor / service 宣介
- 工程化术语直接进入 title/caption/in-figure text
- summary card / narrative card 进入主文图

新增指导语：

- 重新进入 `figure-polish`
- 仅重写 figure-visible text 与 figure metadata
- 不允许把图内 narrative 转移到 caption 继续保留

### 6. Introduce validated-upstream-version policy

`MedAutoScience` 不再默认把“最新版 `DeepScientist`”视为可直接使用。

新增概念：

- `validated upstream version`

含义：

- 某个 `DeepScientist` 版本只有在通过 `MedAutoScience` compatibility checks 后，才算受支持

检查面至少包括：

- skill overlay authority
- managed figure runtime contract
- figure-polish route coverage
- medical surface gate compatibility

这意味着后续升级流程应从“拉到最新”改为：

1. 检测上游新版本
2. 在 compatibility checks 下验证
3. 只有验证通过才允许进入受管 workspace

### 7. Define fork escalation criteria

保持 upstream-first 不是无条件的。若出现以下任一情况，应切换到 `MedAutoScience-managed DeepScientist fork`：

1. `DeepScientist` 不再允许稳定覆盖 skill source priority
2. 关键医学 manuscript / figure 指令被硬编码进内部 prompt，且外部 overlay 无法禁用
3. compatibility shield 已经部署，但仍无法防止上游版本持续污染 manuscript-facing surface
4. 上游发布频率与行为漂移已高到使下游兼容成本长期高于维护薄分叉

fork 的目标不是“重写 DeepScientist”，而是冻结：

- runner skill precedence
- codex home assembly
- manuscript-facing route semantics
- figure route hard gates

## Proposed File-Level Changes

### MedAutoScience

- `pyproject.toml`
- `src/med_autoscience/doctor.py`
- `src/med_autoscience/workspace_contracts.py`
- `src/med_autoscience/controllers/study_runtime_router.py`
- `src/med_autoscience/overlay/installer.py`
- `src/med_autoscience/policies/medical_publication_surface.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- new figure runtime contract module
- new `figure-polish` overlay template

### DeepScientist upstream compatibility touchpoint

- `runners/codex.py`

如果该修改最终被证明无法在 upstream 流程内稳定保留，再升级为 `MedAutoScience` 自维护分叉。

## Testing Strategy

按 TDD 执行，至少补这几组失败测试：

1. Python environment contract
   - figure runtime 缺 `matplotlib`
   - figure runtime 缺 `pandas`
   - bootstrap 可安装并验证
   - ensure-study-runtime 在依赖不完整时阻断

2. Skill authority
   - workspace overlay 与 quest skill 同名时，workspace overlay 胜出
   - `write` / `finalize` / `figure-polish` 来源可审计

3. Figure overlay coverage
   - `figure-polish` 被纳入 overlay 安装与重覆写
   - 未覆盖 `figure-polish` 时 contract 报错

4. Medical figure surface
   - SVG 内出现工具宣介时被阻断
   - SVG 内出现 summary card / 长段 narrative 时被阻断
   - caption 与图内文本同时扫描

5. Upgrade compatibility
   - 未通过 compatibility shield 的 upstream 版本被标为不可放行

## Expected Behavioral Changes

修复后，系统应表现为：

1. 进入 managed study runtime 前，figure 依赖必须已经齐全并被验证。
2. 缺 `matplotlib/pandas` 时不会再继续跑 paper figure，更不会走手拼 SVG 降级。
3. `write`、`finalize`、`figure-polish` 等医学关键 skill 的实际来源可审计且稳定指向 `MedAutoScience` overlay。
4. figure 生成与 polish 的目标从“信息图式叙事图”收敛为“医学 SCI 主文证据图”。
5. `DeepScientist` 上游升级从“默认采用”改为“兼容验证后放行”。

## Risks

### R1. Upstream touchpoint may still drift

即使只改一个优先级触点，上游后续版本也可能再次改变 runner home assembly。

应对：

- 把该行为做成兼容测试
- 一旦失效，立即触发 fork 评估

### R2. Figure runtime contract may enlarge MedAutoScience environment

`matplotlib/pandas` 会让 `med-autoscience` 的受管环境变重。

判断：

- 这是可接受成本。
- 对医学论文 figure 而言，这是必要依赖，不是可选装饰。

### R3. Existing contaminated study surfaces remain untrusted

系统护栏修好后，已经被污染的 paper/figure surface 仍然不能自动恢复可信。

后续要求：

- 对受影响 study 的 writing / figure route 进行受管重跑或重审

## Decision

当前采用的决策是：

- 先不立即维护 `DeepScientist` 自有分叉
- 先构建更强的 `MedAutoScience compatibility shield`
- 同时把 fork 触发条件写清楚并做成显式升级路径

这能在最小维护成本下先恢复可控性；如果事实证明上游已无法被稳定约束，再切换到自维护分叉。
