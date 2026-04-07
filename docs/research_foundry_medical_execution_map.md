# Research Foundry Medical Execution Map

这份文档把 `Med Auto Science` 当前主线压成一张可执行地图，回答四个问题：

1. 这条主线的最终目标是什么
2. 当前已经做到哪里
3. 当前 OMX 正在覆盖哪一层
4. 后续必须按什么顺序继续推进

## 一句话结论

`Med Auto Science` 当前不是在做一组彼此分散的局部优化，而是在沿同一条主线收敛：

- 业务上：把医学研究稳定推进到发表级论文交付
- 架构上：把仓库收敛成 `Research Foundry` 的医学实现，即医学 `domain gateway + Domain Harness OS`

因此，当前所有执行都应被理解为：在 authority / delivery / real-study 都已 absorbed 的前提下，继续把 integration harness 与 cutover readiness 收紧到真实门槛，而不是提前宣布 runtime 已稳定切换。

## 六段执行图

```text
第 1 段：Authority Foundation
  已完成并 absorbed
  - study charter artifact carrier
  - runtime escalation record
  - publication eval minimal schema
  - outer-loop wakeup and decision loop

第 2 段：Formal Runtime Control Surface
  已完成并 absorbed
  - pause / stop / rerun / human-confirmation semantics
  - fail-closed control-action surface

第 3 段：Delivery / Publication Plane
  已完成并 absorbed
  - delivery plane contract map
  - artifact-surface freeze
  - publication gate / delivery sync authority boundary

第 4 段：Real-Study Relaunch & Verify
  已完成并 absorbed
  - real-study anchor relaunch
  - runtime watch coherence closeout
  - external workspace-side blocker classification
  - repo-tracked verification note：docs/real_study_relaunch_verification.md

第 5 段：Integration Harness And Cutover Readiness
  当前 active
  - 已有 absorbed baseline：controller-runtime seam
  - 当前最小 tranche：runtime-eval / delivery-report repo-native baseline
  - 当前保持关闭：end-to-end study harness / cutover / behavior-equivalence / cross-repo write / med-deepscientist write
  - 当前 canonical bridge：docs/integration_harness_activation_package.md

第 6 段：Vocabulary And Contract Freeze / Open Research Foundry Validation
  后置 pending
  - vocabulary / schema / package freeze
  - core-candidate extraction audit
  - second-domain readiness contract
```

## 当前所在位置

当前唯一 active tranche 是：

- `Phase 6 / Integration Harness And Cutover Readiness`
- 当前最窄 write scope：`runtime-eval / delivery-report repo-native baseline`

这意味着：

- 它不是重新打开 delivery plane 主体实现
- 它不是重新打开 real-study external workspace writer
- 它也不是把 `end-to-end harness` 或 `cutover` 偷渡进 repo-side next step

## 当前 tranche 解决什么问题

当前 tranche 解决的是：

1. repo-tracked mainline docs 仍然停留在 pre-relaunch 阶段叙事的问题
2. `runtime_watch -> publication_gate -> study_delivery_sync` 这条 runtime-eval / delivery-report seam 尚未进入 repo-native preflight contract 的问题
3. 当前 integration baseline 容易被误读成“产品 runtime 成熟度”的问题

因此本轮要做的不是“加更多功能”，而是：

- 把当前 absorbed truth 与下一 phase activation package 用 canonical docs 收紧
- 把最小 runtime-eval proof surface 编进开发控制面的 preflight / regression baseline
- 明确 residual risks 与 external surfaces

## 固定推进顺序

从当前节点开始，推荐固定按下面顺序推进：

1. 冻结 `Phase 6` activation package
2. 维持 repo-native runtime-eval / delivery-report baseline 可持续复跑
3. 只有在新的 repo-tracked gate 放行后，才允许讨论 `end-to-end study harness`
4. 只有在 `Phase 6` 真正 closeout 后，才允许进入 `Phase 7 / Vocabulary And Contract Freeze`
5. 再之后才是 `Open Research Foundry Validation`

当前不允许反过来做：

- 不能因为 real-study anchor 已验证，就跳过 integration harness baseline
- 不能因为 delivery plane 已冻结，就直接宣称 cutover readiness 已完成
- 不能因为 external workspace-side blocker 存在，就把它误写成 repo-side runtime contract 未成熟

## OMX 当前应该怎么理解自己的工作

当前 OMX 不是在做“整个项目已经结束”，而是在做“已 absorbed real-study truth 之后，当前最正确的下一条 repo-side tranche”。

更具体地说：

- OMX 当前覆盖：`Phase 6` 最小 repo-native baseline
- OMX 当前不得覆盖：external workspace writer、end-to-end study harness、cutover、behavior-equivalence
- OMX 当前的收口标准：docs / tests / reports / control plane 同口径，且 targeted + broader regression fresh 通过

## 当前正式执行口径

今后统一按下面这条口径理解：

`Med Auto Science` 的当前主线已经完成 authority、control surface、delivery plane 与 real-study relaunch 四段 absorbed 收口；当前正式 active 的是 `Phase 6 / Integration Harness And Cutover Readiness`，其最小 tranche 是 repo-native runtime-eval / delivery-report baseline，而不是 `end-to-end study harness` 或 `cutover`。
