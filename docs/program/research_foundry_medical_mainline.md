# Research Foundry Medical Mainline

这份文档把 `Med Auto Science` 当前真正的主线固定下来。

它回答五个问题：

1. `Med Auto Science` 现在到底在做什么
2. `Research Foundry`、`domain gateway`、`Domain Harness OS` 三者是什么关系
3. 为什么论文交付仍然是顶层业务目标，但不再主导整个架构分层
4. 当前 absorbed position 到了哪里
5. 这条主线接下来应按什么顺序推进

如果只想快速看“最终目标、当前进度、固定顺序”的压缩版，可直接看：

- [Research Foundry Medical Execution Map](./research_foundry_medical_execution_map.md)
- [Integration Harness Activation Package](./integration_harness_activation_package.md)
- [External Runtime Dependency Gate](./external_runtime_dependency_gate.md)

## 一句话结论

`Med Auto Science` 当前应被理解为：

- `Research Foundry` 在医学场景上的成熟实现
- 对外承担医学 `Research Ops` 的 `domain gateway`
- 对内承担医学自动科研的 `Domain Harness OS`

而它的业务北极星始终不变：

- 把医学研究从数据资产稳定推进到可投稿论文

## 长线目标与当前阶段必须分开理解

这里必须严格区分：

- 长线目标
- 当前阶段
- 当前停车终态

长线目标始终是：

- 把医学研究稳定推进到发表级证据链、稿件、图表表格与投稿交付
- 把 `Med Auto Science` 收敛成稳定、可审计、publication-grade 的医学 `Research Ops` domain gateway + `Domain Harness OS`

当前阶段只是：

- 当前 repo-tracked absorbed position 已推进到哪一层
- 当前 repo-side 还允许继续冻结什么
- 当前是 repo 内继续推进，还是已经被 external runtime readiness 阻塞

因此：

- 长线目标不等于当前 `Phase 6`
- 长线目标也不等于当前这一轮 activation package
- 当前 absorbed tranche 完成后，默认不应回到“等人工逐棒点名”
- 只有当 external runtime gate、cutover gate 或更高层产品判断阻塞时，才应诚实停车

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

outer loop 不应被误解成第二个常驻 runtime。当前推荐形态是：

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

## 2026-04-08 / 当前 absorbed position

截至 `2026-04-08`，repo-tracked truth 应按下面这条事实理解：

1. `authority / outer-loop / delivery plane` 三层 contract 已完成并 absorbed 到 `main`
2. `real-study relaunch and verify` 已在真实 anchor 上完成验证，并把 remaining blocker 收敛为 external workspace-side truth gap
3. `Phase 6 / Integration Harness And Cutover Readiness` 的最小 activation package 已完成并 absorbed 到 `main`
4. 当前 repo-side 终态不是“没有下一步”，而是：
   - `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`
5. 当前最小 repo-tracked activation artifact 仍固定为：
   - [Integration Harness Activation Package](./integration_harness_activation_package.md)

这意味着：

- repo 内已经完成了当前 truth 允许冻结的最小 `controller -> runtime -> eval -> delivery` baseline
- 当前不应回退去重做 `real-study relaunch`
- 当前也不应把 repo-side 已完成部分误写成 `end-to-end harness / cutover readiness` 已放行
- 真正阻塞继续前进的是 external runtime / cutover readiness 依赖，而不是当前 repo-side baseline 仍未 absorb

这条 activation package 负责的始终只是：

- 冻结 `controller -> runtime -> eval -> delivery` chain 的当前 baseline
- 诚实写清 `cutover readiness`、residual risks 与 external surface requirement
- 不把 `end-to-end study harness`、cutover、`med-deepscientist` 写入、cross-repo write 偷渡进来

## 当前 immediate next step

当前 repo 内已经没有新的产品级 same-repo tranche 可自动打开。

当前 repo-side 唯一仍可合法继续收紧的动作，是把 external blocker 本身冻结成可审计的 canonical package，见：

- [External Runtime Dependency Gate](./external_runtime_dependency_gate.md)

在该 package 收口完成后，当前真正的 next step 应理解为：

1. 先在 external runtime / cutover surface 上清掉真实 blocker
2. 等 external gate 放行后，再回到本仓继续推进更大的 `end-to-end harness / cutover readiness`
3. 在此之前，不重开 repo-side tranche 来伪造“继续推进”

## 固定推进顺序

从当前 absorbed 起点开始，推荐固定按下面顺序推进：

1. authority / outer-loop / delivery plane convergence（已完成）
2. real-study relaunch and verify（已完成）
3. integration harness activation baseline（已完成并 absorbed）
4. external runtime / cutover readiness blocker 清理（当前阻塞）
5. only-then `end-to-end harness / cutover readiness`

## 非目标

当前主线不主张：

- 把 `Med Auto Science` 重新降级成“论文工具箱”
- 把 `display / paper` 误当成边缘能力
- 因为要 cutover 就提前做越权写入
- 因为要自动推进就跳过 fail-closed 边界
- 把 `Research Foundry` 现在就做成新的物理主仓库

## 正式判断

因此，当前 `med-autoscience` 仓库的正式主线应写成：

- 先完成 authority / outer-loop / delivery plane convergence
- 再完成 real-study relaunch and verify
- 再把 `Phase 6 / Integration Harness And Cutover Readiness` 的最小 activation package absorb 到 `main`
- 当前停车终态应诚实写成 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`
- 只有在 external runtime surface 与 cutover gate 真正放行后，才允许继续往更大 harness / cutover 推进
