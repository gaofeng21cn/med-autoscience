# Research Foundry Medical Execution Map

这份文档把 `Med Auto Science` 当前主线压成一张可执行地图，回答四个问题：

1. 这条主线的最终目标是什么
2. 当前已经做到哪里
3. 当前 OMX 正在覆盖哪一层
4. 后续必须按什么顺序继续推进

如果只想快速看当前真实起点与下一棒，可同时看：

- [Real-Study Relaunch Verification](./real_study_relaunch_verification.md)
- [Integration Harness Activation Package](./integration_harness_activation_package.md)

## 一句话结论

`Med Auto Science` 当前不是在做一组彼此分散的局部优化，而是在沿同一条主线收敛：

- 业务上：把医学研究稳定推进到发表级论文交付
- 架构上：把仓库收敛成 `Research Foundry` 的医学实现，即医学 `domain gateway + Domain Harness OS`

因此，当前所有执行都应被理解为：为了最终稳定地产出 paper-facing delivery，先完成 authority / delivery / real-study 收口，再把 `controller -> runtime -> eval -> delivery` 这条链压成可持续复跑的 activation baseline。

## 五层执行图

```text
第 1 层：Authority Foundation
  已完成
  - study charter artifact carrier
  - runtime escalation record
  - publication eval minimal schema
  - outer-loop wakeup and decision loop

第 2 层：Parameterized Authority Inputs
  已完成
  - charter-parameterized input contract
  - 结果：eval / outer-loop / delivery 已通过同一套 fail-closed charter projection 拿到稳定输入

第 3 层：Delivery / Publication Plane
  已完成
  - delivery plane contract map
  - manuscript / reporting / submission / display / figure / table contract

第 4 层：Real-Study Relaunch & Verify
  已完成并 absorbed 到 main
  - anchor-study relaunch
  - real-study relaunch and verify
  - 当前 repo-tracked verification note：`docs/real_study_relaunch_verification.md`
  - 最新锚点：`001-dm-cvd-mortality-risk`
  - 已验证 managed entry / runtime watch / publication gate / study delivery sync；remaining blocker 已被收敛到 external workspace-side publication surface

第 5 层：Integration Harness Activation & Baseline
  当前 active
  - 当前 repo-tracked bridge：`docs/integration_harness_activation_package.md`
  - 目标：冻结 `controller -> runtime -> eval -> delivery` chain、cutover readiness、residual risk、external surface requirement
  - 当前最小 baseline：`runtime_watch` / `publication_gate` / `study_delivery_sync`

后置门：End-to-End Harness / Cutover Readiness
  继续关闭
  - 只有第 5 层 absorb 之后，且 external runtime surface 真正放行，才允许继续
```

## 当前所在位置

当前唯一活跃子线是：

- `Phase 6 / integration harness activation package`

因此，当前 OMX 正在覆盖的是第 5 层，而不是重新回到 authority / delivery / real-study 的旧 tranche。

这意味着：

- 它现在不是在重做 `real-study relaunch`
- 也不是在打开 `end-to-end study harness`
- 它在做的是 `real-study` absorbed 之后的最小 repo-side activation baseline

## 每一层解决什么问题

### 第 1 层：Authority Foundation

这一层解决的是“关键对象是否存在、归谁负责、以什么 durable artifact 形式存在”。

### 第 2 层：Parameterized Authority Inputs

这一层已经完成，当前不再是 active tranche。

它解决的是“下游模块到底怎么从 `study_charter` 拿到稳定输入”。

### 第 3 层：Delivery / Publication Plane

这一层解决的是“论文交付面本身的正式 contract map”。

当前与 runtime / eval / outer-loop artifact 一起冻结的 repo-tracked canonical bridge，见 `docs/delivery_plane_contract_map.md`。

### 第 4 层：Real-Study Relaunch & Verify

这一层解决的是“这些合同在真实课题里到底能不能稳定工作”。

也就是说，这一层是对前面三层 contract 的真实世界检验。

### 第 5 层：Integration Harness Activation & Baseline

这一层解决的是：

- `real-study` 已验证之后，repo 内还能合法继续冻结什么
- 当前最小 `runtime -> eval / delivery` baseline 到底是谁
- 哪些部分已经是 repo-side 可持续 proof，哪些仍然需要 external runtime / cutover surface

当前固定的 repo-tracked bridge 见：

- [Integration Harness Activation Package](./integration_harness_activation_package.md)

## 固定推进顺序

从当前 absorbed 起点开始，推荐固定按下面顺序推进：

1. authority / parameterized inputs（已完成）
2. delivery / publication plane（已完成）
3. real-study relaunch and verify（已完成）
4. integration harness activation package（当前 active）
5. only-then `end-to-end harness / cutover readiness`

## OMX 当前应该怎么理解自己的工作

当前 OMX 不是在做“整个项目”，而是在做“整个项目当前最正确的下一层”。

更具体地说：

- OMX 当前覆盖：第 5 层
- OMX 当前目标：先 absorb activation baseline
- OMX 再之后才允许看 external runtime gate 是否允许继续

## 当前正式执行口径

今后统一按下面这条口径理解：

`Med Auto Science` 的当前主线是一条五层收敛路线：

1. 先立 authority foundation
2. 再收紧 parameterized authority inputs
3. 再收紧 delivery / publication plane
4. 再用真实课题 relaunch 验证整条链是否成立
5. 再把 integration harness activation baseline 压成稳定 repo-tracked bridge

只有在这五层都稳定后，才允许讨论更大的 `end-to-end harness / cutover readiness`。
