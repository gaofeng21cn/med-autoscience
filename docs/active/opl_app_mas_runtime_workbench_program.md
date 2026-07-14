# OPL App MAS Workbench Boundary

Owner: `MedAutoScience + OPL App`
Purpose: `opl_owned_mas_workbench_projection_boundary`
State: `active_support`
Machine boundary: 本文只定义 MAS 对 OPL App 的 refs-only input；App/runtime实现归 OPL，study/publication/artifact authority归 MAS owner surfaces。

## Owner split

OPL App/Console 可以展示：

- StageRun/Attempt/session/provider状态；
- body-free artifact/source/review/owner receipt refs；
- typed blocker、human gate、route decision 与 freshness；
- package/environment/resource currentness receipts。

App 不得写 MAS study truth、publication verdict、canonical artifact body、memory body、
owner receipt或 current package。MAS 不维护 repo-local workbench projection builder、
HTML/Markdown cockpit、IPC、history cache或 action shell。

## 操作边界

Pause/resume/stop/reconcile等 operator intent 必须进入 OPL action/runtime surface，
再由 StageRun/authority contract校验；UI可见性本身不授权执行。任何涉及 publication、
submission、artifact mutation、credential或 irreversible action的操作继续 fail closed。

## Evidence

Contract/readback只能证明 projection shape。用户可用的 workbench仍需真实 App
screenshot/interaction、stale/fresh状态、blocked/human-gate路径、操作 receipt与
no-forbidden-write evidence；这些证据归 OPL App/release lane，不在 MAS 创建替代 UI。
