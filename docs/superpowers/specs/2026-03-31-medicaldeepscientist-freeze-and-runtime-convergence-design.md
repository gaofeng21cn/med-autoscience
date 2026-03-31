# MedicalDeepScientist Freeze And Runtime Convergence Design

Date: `2026-03-31`

## Context

当前我们已经有两层比较清楚的事实：

1. `MedAutoScience` 已经是医学研究治理入口。
2. 真正推动 quest 长时间自动运行的执行内核，仍然是 `DeepScientist`。

过去这套关系的默认前提是：

- 上游 `DeepScientist` 可以继续作为可约束的 generic runtime
- `MedAutoScience` 通过 `profile -> controller -> overlay -> adapter` 驯化其行为

但最近暴露出来的问题说明，这个前提已经不再稳定：

- 上游 prompt / skill 可以引入不属于医学运行层的产品导向内容
- `MedAutoScience` 需要持续清洗 prompt 污染
- 真正的执行真相仍深度依赖 `DeepScientist` 的 daemon API、`.ds` 状态和 worktree/paper/result 布局

因此，问题已经不是“要不要继续依赖 runtime”，而是“要不要继续把执行真相寄托在一个不受我们控制的上游仓库上”。

## Problem Statement

当前系统存在一个危险的不对称：

- 医学治理权已经在 `MedAutoScience`
- 执行真相和若干关键布局契约仍在 `DeepScientist`

这会带来三个直接风险：

### 1. Runtime authority split

`MedAutoScience` 负责 contract、hydration、runtime watch、publication gate，但 quest 的创建、turn 调度、mailbox、document asset、worktree 布局和运行状态真相仍由 `DeepScientist` 决定。

### 2. Upgrade risk is now product risk

当上游 prompt、skill precedence、runner 行为或 UI/asset 解析发生变化时，受损的不只是“兼容性”，而是医学论文写作面和研究交付面。

### 3. Adapter cannot retire while protocol is implicit

只要 `MedAutoScience` 还在直接依赖：

- `daemon_api`
- `.ds/runtime_state.json`
- `.ds/worktrees/*/paper/...`
- `.ds/runs/*/stdout.jsonl`
- `experiments/main/*/RESULT.json`

那 `deepscientist adapter` 就还不是可替换 shim，而是系统关键路径的一部分。

## User-Level Requirements

本次启动阶段必须满足：

1. 先得到一个可控、稳定的 `MedicalDeepScientist` 冻结基线。
2. 不把医学运行层立刻粗暴内吸进 `MedAutoScience`。
3. 允许直接带入小而确定、测试闭合的 runtime bugfix。
4. 不接受降级处理、事后补丁式兜底或启发式补救。
5. 之后的协议收口必须让 `adapter` 逐步退化为兼容层，而不是继续膨胀。

## Current System Facts

### A. `DeepScientist` 不是 LangGraph 风格框架

当前 `DeepScientist` 是一套自写 Python daemon + 文件/Git 持久态 + prompt/skill 驱动 + 薄 turn loop 的 runtime，不是 `LangGraph`、`langchain`、`temporal` 这类外部状态机框架。

这意味着：

- 冻结它并不需要接受一套复杂第三方 runtime 语义
- 但也意味着很多关键协议现在只是“代码里的事实”，不是显式文档化协议

### B. `MedAutoScience` 已经把医学治理前推到了 runtime 入口之前

当前已经形成的上层协议面包括：

- `startup_contract`
- `create_only -> hydrate -> validate -> start_or_resume`
- `runtime_watch`
- `publication_gate`
- medical overlay authority / audit
- literature hydration 与 reporting / analysis contract

这些都说明，医学运行层的权威入口已经在 `MedAutoScience`。

### C. 执行真相仍然强依赖 `DeepScientist` 布局

目前至少还有这些直接耦合：

- [daemon_api.py](/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/adapters/deepscientist/daemon_api.py)
- [runtime.py](/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/adapters/deepscientist/runtime.py)
- [study_runtime_router.py](/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_runtime_router.py)
- [study_delivery_sync.py](/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_delivery_sync.py)

这决定了：现在还不能直接删 adapter。

## Considered Approaches

### Option A. 继续只做 upstream + shield

做法：

- 保持原版 `DeepScientist`
- 继续靠 overlay、controller、upgrade-check 和审计面去驯化

优点：

- 短期最省事

缺点：

- 已经无法解决“上游产品方向直接进入 runtime 真相”的问题
- 每次升级都要重新证明 prompt / runner / UI / asset 行为没有越界

结论：

- 不再适合作为默认路线。

### Option B. 先冻结一个薄的 `MedicalDeepScientist`，再逐步收口 protocol

做法：

- 以当前审计过的 `DeepScientist` 提交为基线创建兄弟仓库 `MedicalDeepScientist`
- 首批只带入确定性 runtime 修复，不做大规模重写
- `MedAutoScience` 先把目前隐含在 adapter 里的协议提炼出来
- 等协议面稳定后，再逐步去掉 `deepscientist adapter`

优点：

- 先拿回执行真相控制权
- 不会同时重写 runtime 和治理层
- 与当前 `controller-first` 路线兼容

缺点：

- 需要开始维护一个受控 fork
- 需要补一轮协议显式化工作

结论：

- 这是本次推荐方案，也是本次选定方案。

### Option C. 直接把 `DeepScientist` 内吸到 `MedAutoScience`

做法：

- 直接把 daemon、turn loop、quest state、runner 和 UI/asset 语义吸收到 `MedAutoScience`

优点：

- 最终分层最简单

缺点：

- 同时重做 runtime core、协议、目录布局和上层 controller 对接
- 现阶段风险最高

结论：

- 现在不选。

## Chosen Design

采用 `Option B`：

先冻结一个受控的 `MedicalDeepScientist` 兄弟仓库，先把执行真相稳定下来，再以 `runtime protocol convergence` 的方式逐步把 `MedAutoScience` 对 `DeepScientist` 的隐式耦合变成显式协议，最后再移除 `deepscientist adapter`。

## Design

### 1. Freeze a thin sibling fork, not an immediate rewrite

`MedicalDeepScientist` 的第一阶段定义如下：

- 仓库形态：兄弟仓库，不 vendor 进 `MedAutoScience`
- 冻结基线：以 `DeepScientist` 当前已审计的 `main` 提交为准
- 首批目标：稳定 runtime truth，不追求立刻改变全部 package 名称或 import 路径

第一阶段明确不做：

- 不做 Python package rename
- 不改 quest/layout 语义
- 不改 daemon API shape
- 不重写 turn loop

原因很简单：

- 这几个点正是 `MedAutoScience` 当前还在依赖的兼容面
- 如果一开始就动它们，会把“冻结 fork”和“协议迁移”两件事混成一次高风险操作

### 2. Freeze baseline and cherry-pick policy

冻结基线建议采用：

- `DeepScientist` 提交 `a7853fd`

首批直接带入的提交只包括“确定性 runtime 正确性修复”：

- `d4994db Fix worktree document asset resolution`

这条修复应直接进入首批冻结，原因是：

- 它修的是 active worktree 下文档资产解析的真实 bug
- 直接影响 Web App 中 PNG / SVG / PDF 的展示
- 已包含针对 `svg/png/pdf` 的测试覆盖

下列内容不应自动进入首批冻结：

- 与上游产品偏好、prompt 叙事、运行风格相关的近期变更
- 需要 `MedAutoScience` 同步 adoption 才有意义的新 contract 位

其中：

- `9bd736d feat: add explicit publishability gate mode`
  - 不直接进入首批冻结
  - 只有当我们决定把 `publishability_gate_mode` 升格为 `MedicalDeepScientist` 的稳定 startup contract 字段时才带入
- `pr2 external controller docs`
  - 文档方向正确
  - 可以后续带入，但不阻塞冻结

### 3. Treat `uv.lock` drift as an explicit freeze decision

当前 `DeepScientist` 工作树存在未提交的 [uv.lock](/Users/gaofeng/workspace/DeepScientist/uv.lock) 漂移。

这部分不能被“顺手带过去”，必须显式处理：

- 要么在新 fork 中重新生成并提交依赖锁
- 要么在冻结说明里明确“沿用基线提交，不带未提交 lock 漂移”

禁止做法：

- 直接把当前脏工作树整体复制成 fork 基线

### 4. Promote runtime protocol to a first-class design object

从现在开始，`MedAutoScience` 不应再把下面这些事实只看成 adapter 内部细节，而应把它们视为 runtime protocol：

#### Creation and control protocol

- create quest
- pause / resume / stop quest
- daemon base URL resolution

#### Startup and hydration protocol

- `startup_contract`
- create payload
- hydration payload
- hydration validation outputs

#### Quest state protocol

- runtime status
- active run id
- pending mailbox / delivered mailbox
- stdout stream path

#### Workspace and artifact topology protocol

- active worktree root
- paper root
- main result root
- manuscript delivery root

#### Durable control report protocol

- `publication_gate`
- `runtime_watch`
- medical manuscript / literature / reporting audit outputs

这些协议位在第一阶段不要求全部 engine-neutral，但要求全部显式命名、可测试、可审计。

### 5. Reframe the current adapter as a compatibility shim

在 `MedicalDeepScientist` 创建后，`deepscientist adapter` 的职责必须收缩为：

- 协议编解码
- 路径解析
- HTTP / file-based transport

它不应继续承担：

- 新医学治理逻辑
- 新论文策略逻辑
- 新 route decision 逻辑

这些逻辑应继续留在：

- `policy`
- `controller`
- `overlay`

### 6. Remove adapter only after protocol convergence

`deepscientist adapter` 的退出条件不是“已经有了 fork”，而是下面三件事都成立：

1. `MedAutoScience` 已有显式 `runtime protocol` 帮助层或模块，能够替代当前 adapter 中散落的路径/状态假设。
2. `study_delivery_sync`、`publication_gate`、`runtime_watch`、`study_runtime_router` 等调用点都只依赖协议帮助层，而不再直接依赖 `.ds` 细节。
3. `MedicalDeepScientist` 的执行面已经被 `MedAutoScience` 当成受控 engine，而不是“碰巧兼容 DeepScientist 布局”的外部仓库。

## Phased Rollout

### Phase 1. Freeze `MedicalDeepScientist`

目标：

- 建立兄弟仓库
- 记录冻结基线
- 带入 `d4994db`
- 显式处理 `uv.lock`
- 让现有 `deepscientist_repo_root` / upgrade-check / 审计流程能指向新的受控 repo

完成标志：

- 新仓库基线可审计
- 文档说明首批 cherry-pick 范围
- 运行时 document asset 行为验证通过

### Phase 2. Runtime protocol convergence

目标：

- 从当前 adapter 和 controller 中提炼协议帮助层
- 把 `.ds`、worktree、paper/result 布局依赖集中管理
- 让 `study_delivery_sync` 等调用点停止直接假设 `DeepScientist` 目录形状

完成标志：

- 关键协议位有独立测试
- 调用点依赖协议层而非散落路径拼接

### Phase 3. Adapter retirement

目标：

- 将 `deepscientist adapter` 替换为 `MedicalDeepScientist` 兼容引擎接入层，或进一步抽象成 engine-neutral runtime layer

完成标志：

- `MedAutoScience` 不再以 `DeepScientist` 命名耦合自己的控制面
- adapter 成为薄 transport，或被更高层的 protocol client 替代

## Acceptance Criteria

本次路线被视为成功，至少要满足：

1. `MedicalDeepScientist` 冻结后，不再受上游 prompt / UI / runner 漂移直接影响。
2. `d4994db` 这类确定性修复可以稳定进入受控 fork。
3. `MedAutoScience` 新增医学能力时，不需要继续把业务语义塞进 adapter。
4. 后续任何“去掉 adapter”的工作，都能以显式 protocol 迁移来做，而不是一次性重写。

## Open Decisions

仍需在后续 implementation plan 中明确的点包括：

1. `MedicalDeepScientist` 的仓库路径、remote 命名和版本号策略。
2. `deepscientist_repo_root` 字段是否在过渡期继续沿用原名，还是新增更中性的 engine repo root 配置。
3. `publishability_gate_mode` 是否进入受控 fork 的稳定 contract。
4. 何时启动 package/import rename；该动作明确不属于第一阶段。
