# Research Foundry Medical Execution Map

这份文档把 `Med Auto Science` 当前主线压成一张可执行地图，回答四个问题：

1. 这条主线的最终目标是什么
2. 当前已经做到哪里
3. 当前 OMX 正在覆盖哪一层
4. 后续必须按什么顺序继续推进

## 一句话结论

`Med Auto Science` 当前不是在做一组彼此分散的局部优化，而是在沿同一条主线收敛：

- 业务上：把医学研究稳定推进到发表级论文交付
- 架构上：把仓库收敛成 `Research Foundry` 的医学实现，即医学 `domain gateway + domain harness OS`

因此，当前所有执行都应被理解为：为了最终稳定地产出 paper-facing delivery，先把长期运行所需的 authority、delivery 与 real-study adoption 三层逐次收紧。

## 四层执行图

```text
第 1 层：Authority Foundation
  已完成
  - study charter artifact carrier
  - runtime escalation record
  - publication eval minimal schema
  - outer-loop wakeup and decision loop

第 2 层：Parameterized Authority Inputs
  进行中
  - charter-parameterized input contract
  - 目标：让 eval / outer-loop / delivery 通过同一套 fail-closed charter projection 拿到稳定输入

第 3 层：Delivery / Publication Plane
  待进入
  - delivery plane contract map
  - manuscript / reporting / submission / display / figure / table contract

第 4 层：Real-Study Relaunch & Verify
  待进入
  - anchor-study relaunch
  - real-study relaunch and verify
  - 目标：验证新的 contract 是否真正支撑 paper-owned truth surface

后置门：Monorepo Scaffold Gate
  禁止提前进入
  - 只有前四层收紧后，才允许考虑 scaffold / cutover
```

## 当前所在位置

当前唯一活跃子线是：

- `charter-parameterized input contract`

因此，当前 OMX 正在覆盖的是第 2 层，而不是整个主线的全部。

这意味着：

- 它现在不是在直接做真实课题重跑
- 也不是在做完整 delivery plane 收口
- 它在做的是 delivery 与 real-study 重跑之前必须先稳定下来的输入合同层

## 每一层解决什么问题

## 第 1 层：Authority Foundation

这一层解决的是“关键对象是否存在、归谁负责、以什么 durable artifact 形式存在”。

已经完成的对象包括：

- `study_charter`
- `runtime_escalation_record`
- `publication_eval_record`
- `study_decision_record`
- `study_outer_loop_tick(...)`

它们的意义是：

- 运行中的 `MedDeepScientist` 不再越权决定 study-level 走向
- `Med Auto Science` 具备 outer-loop controller 能力
- 研究推进、升级、评估、裁决都不再只停留在 prompt 层

## 第 2 层：Parameterized Authority Inputs

这一层解决的是“下游模块到底怎么从 `study_charter` 拿到稳定输入”。

当前要收紧的是：

- charter -> eval
- charter -> outer-loop
- charter -> delivery

这一层的目标不是重新定义 authority object，而是形成 compact、可复用、fail-closed 的参数化 projection。

只有这一层稳了，后面才不会在：

- `publication_eval`
- `study_outer_loop_tick(...)`
- manuscript / reporting / submission / display

之间重复散落参数逻辑、字段解释与 prompt 补丁。

## 第 3 层：Delivery / Publication Plane

这一层解决的是“论文交付面本身的正式 contract map”。

重点包括：

- manuscript surface
- reporting contract
- publication gate
- submission companion
- graphical abstract / companion artifact
- figure / table contract
- display template catalog

这里的核心不是“继续加模板”这么简单，而是把这些交付面重新写成 harness OS 下的正式 delivery plane。

## 第 4 层：Real-Study Relaunch & Verify

这一层解决的是“这些合同在真实课题里到底能不能稳定工作”。

重点不是 demo，而是：

- 真实课题重跑
- 真实论文交付重跑
- anchor paper closure / relaunch
- 验证 paper-owned truth surface 是否稳定

也就是说，这一层是对前面三层 contract 的真实世界检验。

## 固定推进顺序

从当前节点开始，推荐固定按下面顺序推进：

1. `charter-parameterized input contract`
2. `delivery plane contract map`
3. `real-study relaunch and verify`
4. `only-then monorepo scaffold gate`

当前不允许反过来做：

- 不能因为想更快看到论文表面，就跳过第 2 层
- 不能因为想做更大重构，就提前进入 monorepo scaffold
- 不能因为某条历史 worktree 里还有归档 mailbox，就回头重开旧子线

## OMX 当前应该怎么理解自己的工作

当前 OMX 不是在做“整个项目”，而是在做“整个项目当前最正确的下一层”。

更具体地说：

- OMX 当前覆盖：第 2 层
- OMX 接下来应自动推进：第 3 层
- OMX 再之后应自动推进：第 4 层

但前提是：

- 每一层都必须先完成 contract convergence
- 无 hard blocker 时再进入 clean worktree 最小实现验证
- 每层完成后更新 reports，再进入下一固定子线

## 当前正式执行口径

今后统一按下面这条口径理解：

`Med Auto Science` 的当前主线是一条四层收敛路线：

1. 先立 authority foundation
2. 再收紧 parameterized authority inputs
3. 再收紧 delivery / publication plane
4. 再用真实课题 relaunch 验证整条链是否成立

只有在这四层都稳定后，才允许讨论更大的 monorepo scaffold/cutover。
