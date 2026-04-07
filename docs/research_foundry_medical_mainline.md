# Research Foundry Medical Mainline

这份文档把 `Med Auto Science` 当前真正的主线固定下来。

它回答四个问题：

1. `Med Auto Science` 现在到底在做什么
2. `Research Foundry`、`domain gateway`、`Domain Harness OS` 三者是什么关系
3. 为什么论文交付仍然是顶层业务目标，但不再主导整个架构分层
4. 在 `real-study relaunch` 已 absorbed 到 `main` 之后，接下来必须按什么顺序继续推进

如果只想快速看“最终目标、当前进度、固定顺序”的压缩版，可直接看：

- [Research Foundry Medical Execution Map](./research_foundry_medical_execution_map.md)
- [Integration Harness Activation Package](./integration_harness_activation_package.md)

## 一句话结论

`Med Auto Science` 当前应被理解为：

- `Research Foundry` 在医学场景上的首个成熟实现
- 对外承担医学 `Research Ops` 的 `domain gateway`
- 对内承担医学自动科研的 `Domain Harness OS`

而它的业务北极星始终不变：

- 把医学研究从数据资产稳定推进到可投稿论文

## 两层主线必须分开理解

### 1. 业务北极星

业务目标非常明确，而且不会改变：

- 形成值得继续投入的研究路线
- 形成完整证据链
- 形成稿件、图表、表格与投稿交付

所以：

- `display`
- `paper`
- `submission delivery`

都仍然是 `P0` 级能力。

### 2. 架构主线

为了让这些交付能力稳定存在，系统本体必须先收紧成：

- 对外稳定的 `domain gateway`
- 对内清晰的 `Domain Harness OS`
- 明确的 `controller / runtime / eval / delivery` authority boundary

因此：

- `display / paper delivery` 不是被降级
- 而是被放回 `delivery / publication plane` 的正确层级

它们依然决定平台有没有真实价值，但不再决定整个平台如何分层。

## 当前推荐的系统理解

推荐始终按下面这条链路理解：

```text
Human / Agent
  -> OPL Gateway
      -> Research Foundry
          -> Med Auto Science Domain Gateway
              -> Med Auto Science Domain Harness OS
                  -> Controller / Runtime / Eval / Delivery
```

这里的关键含义是：

- `OPL`
  - 负责顶层 federation 与 gateway language
- `Research Foundry`
  - 负责 `Research Ops` 的通用 framework 身份
- `Med Auto Science`
  - 负责医学场景的正式实现
- `Med DeepScientist`
  - 当前仍是最核心的 runtime substrate 之一
  - 但不等于整个 `Med Auto Science`

## Domain Gateway 与 Domain Harness OS 的分工

### Domain Gateway

`Med Auto Science` 作为 `domain gateway`，负责：

- 暴露正式入口
- 暴露稳定 contract
- 暴露 workspace / study / controller / adapter 的可审计控制面
- 阻止外部调用方直接绕过边界去碰内部 runtime

### Domain Harness OS

`Med Auto Science` 作为 `Domain Harness OS`，负责：

- 组织 controller、runtime、eval、delivery 为同一条长期运行链
- 持有 authority artifact、runtime artifact、verdict artifact 与 delivery artifact 的边界
- 维持研究推进、审核、停止、promotion、publication hygiene 与 submission delivery

未来 monorepo 内部的：

- `controller_charter`
- `runtime`
- `eval_hygiene`

都应被理解为这个 harness OS 的内部主模块。

与此同时，outer loop 不应被误解成第二个常驻 runtime。当前推荐形态是：

- `MedDeepScientist` 作为常驻 inner runtime
- `Med Auto Science` 作为 tick-driven outer controller

相关机制见：

- [Outer-Loop Wakeup And Decision Loop](./outer_loop_wakeup_and_decision_loop.md)

## 为什么 publication / display 仍然是主价值

这一点必须说清楚：

- `Med Auto Science` 最终不是为了“架构漂亮”
- 而是为了稳定产出医学论文

所以 publication / display 不是边缘能力，而是：

- `delivery plane`
- `publication plane`
- `paper-facing value plane`

它们仍然是平台对医学用户最直观、最关键的交付面。

只是它们应该建立在稳定底座上：

- `study_charter`
- `startup projection`
- `runtime escalation`
- `publication eval`
- `medical reporting contract`
- `display template contract`

## 当前 absorbed position / 2026-04-07

截至 `2026-04-07`，当前主线已经依次完成并 absorbed 到 `main`：

1. outer-loop durable decision loop
2. formal runtime control surface (`pause / stop / rerun / requires_human_confirmation`)
3. delivery plane contract map and artifact-surface freeze
4. real-study relaunch and verify

当前 authoritative real-study closeout 见：

- [Real-Study Relaunch Verification](./real_study_relaunch_verification.md)

因此，当前 repo-side 真正的下一阶段不是再回头争论 authority foundation，而是：

- `Phase 6 / Integration Harness And Cutover Readiness`

## 当前 active phase 的正式理解

当前 active phase 只应被理解为：

- 在已 absorbed 的 real-study truth 之上，继续把 `controller / runtime / eval / delivery` chain 收紧成可持续复跑的 integration baseline
- 同时明确 `merge gate` 与 `runtime cutover gate` 仍然是两道不同的门

这并不等于：

- `end-to-end study harness` 已打开
- `cutover` 已打开
- `behavior-equivalence` 已通过
- external workspace-side blocker 已经消失

当前 phase 的 repo-tracked canonical bridge 见：

- [Integration Harness Activation Package](./integration_harness_activation_package.md)

## 固定推进顺序

从当前节点开始，推荐固定按下面顺序推进：

1. `Phase 6 / Integration Harness And Cutover Readiness`
   - 先冻结 activation package
   - 再维持最小 repo-native harness baseline
   - 继续保持 `end-to-end harness / cutover / behavior-equivalence` 关闭，直到单独门控放行
2. `Phase 7 / Vocabulary And Contract Freeze`
3. `Phase 8 / Open Research Foundry Validation`

当前不允许反过来做：

- 不能因为 real-study 已有 anchor 验证，就跳过 integration harness baseline
- 不能因为要更快进入 cutover，就把 `merge gate` 与 `runtime cutover gate` 混成一个门
- 不能因为 external workspace-side blocker 存在，就回退 repo-side fail-closed contract

## 当前 immediate next step

当前最自然的 immediate next step 是：

1. 把 repo-tracked mainline docs 从 pre-relaunch 叙事同步到 post-relaunch absorbed truth
2. 把 `runtime_watch -> publication_gate -> study_delivery_sync` 这一段 proof surface 编入 repo-native preflight baseline
3. 以 targeted regression + broader regression 证明当前最小 tranche 已收口

而不是：

- 打开 `end-to-end study harness`
- 打开 `cutover`
- 直接改 external workspace truth
- 把开发控制面的 baseline 误写成产品 runtime 成熟度

## 非目标

当前主线不主张：

- 把 `Med Auto Science` 重新降级成“论文工具箱”
- 把 `display / paper` 误当成边缘能力
- 因为要 monorepo 就提前做大规模代码搬迁
- 因为要开放化就提前把医学语义抹平
- 把 `Research Foundry` 现在就做成新的物理主仓库
- 在 repo-tracked contract 未显式授权前做 `med-deepscientist` 写入或 `cross-repo write`

## 正式判断

因此，当前 `med-autoscience` 仓库的正式主线应写成：

> `Med Auto Science` is the medical implementation of `Research Foundry`, operating as a medical `domain gateway + Domain Harness OS`, with publication-grade paper delivery as the business north star.

对应中文可稳定表述为：

> `Med Auto Science` 是 `Research Foundry` 的医学实现；对外是医学 `Research Ops` 的 `domain gateway`，对内是医学自动科研的 `Domain Harness OS`；其业务北极星始终是把研究稳定推进到发表级论文交付。当前已完成 delivery-plane 与 real-study relaunch 收口，下一正式阶段是 `Phase 6 / Integration Harness And Cutover Readiness`，但仍未打开 `end-to-end harness` 与 `cutover`。
