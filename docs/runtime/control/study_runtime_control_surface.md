# Study Runtime Read Surface

Owner: `MedAutoScience`
Purpose: `Explain the passive MAS study/runtime read boundary.`
State: `active_runtime_support`
Machine boundary: Human-readable support only; OPL owns runtime transport and Codex CLI owns semantic stage routing.

MAS 不再维护 `study_outer_loop_tick`、transition table、controller decision refresh 或私有 stage dispatcher。正式普通入口只有 V2 六个 OPL-hosted Stage actions；状态、进度、attempt 与 owner-route readback 由 OPL StageRun/current-control/hosted workbench 投影，MAS 只提供 study truth、authority refs 与 owner outputs。旧 `study_progress`、`study_state_matrix`、`paper_mission` 和 domain-handler export/dispatch 是 internal diagnostic/provenance residue，不是 generated public actions。

这些入口可以读取 study truth、artifact refs、阴性结果、失败尝试、publication/quality observation、owner receipt、human gate 和 authority evidence，但不能：

- 选择、接受、拒绝、排序或重写 semantic stage route；
- 因 schema、packet、receipt、review 或质量分数缺口阻止 Codex 启动其他 declared stage；
- 把 retry/review/repair 预算耗尽写成 execution blocker；
- 直接写 OPL queue、attempt、provider 或 StageRun 状态。

Codex CLI 可以携带任意可读 artifact 前进、重复、跳过或 route-back。普通质量缺口记录为 quality debt，只关闭 accepted/ready/publication/export/submission claim。仅零可读输出、损坏不可读、identity/currentness、权限/安全、不可逆操作或明确 human authority 可以硬停。
