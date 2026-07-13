# Runtime Boundary

Owner: `MedAutoScience`
Purpose: `runtime_owner_boundary`
State: `active_current_truth`
Machine boundary: 本文解释边界；机器事实归 OPL runtime contracts/readback、MAS domain contracts、durable artifacts 与 receipts。

## 结论

MAS 不是 runtime platform。Runtime owner split 是：

| Responsibility | Owner |
| --- | --- |
| scheduler / queue / attempt ledger / retry / dead-letter / resume | OPL |
| command / event / outbox / StageRun | OPL |
| StateIndex / workspace locator / lifecycle / storage / observability | OPL |
| environment prepare/run | OPL |
| hosted status/workbench | OPL |
| medical policy / study truth / source readiness | MAS |
| AI reviewer/publication quality | MAS |
| artifact/memory authority | MAS |
| owner receipt / typed blocker / human gate | MAS |

## Runtime request/answer

OPL 可以向 MAS domain handler target 发出 schema-valid request。MAS 返回：

- domain refs；
- owner receipt；
- stable typed blocker；
- human gate；
- authority result；
- forbidden-write-safe diagnostic refs。

MAS 不返回或维护通用 queue mutation、attempt lease、retry policy、StateIndex rows、storage maintenance plan、health snapshot或 workbench action shell。

## Progress authority

默认控制链：

`Codex CLI selected stage -> nonbinding route context -> OPL transport/readback -> MAS owner consumption`

OPL receipt 证明 transport，不替代 MAS owner answer。旧 provider admission、current work unit、PaperRecovery、domain action request和 repo-local next-action materializer 已退役或 tombstone-only。

## Environment

MAS 在 `contracts/runtime_environment_requirements.json` 声明 requirement；OPL 负责 `env prepare/run`。MAS 不在 import、workspace bootstrap、plugin installer 或 domain handler 内安装/修复环境。

## Forbidden authority

OPL runtime/read model/workbench 不得：

- 写 MAS study truth、publication eval 或 controller decision；
- 授权 canonical paper/artifact mutation；
- 接受/拒绝 memory body；
- 签 MAS owner receipt；
- 把 queue/attempt/provider/UI 状态解释成 paper progress 或 quality verdict。

MAS domain code 不得：

- 建立通用 scheduler、runner、queue、attempt ledger 或 lifecycle store；
- 重建 OPL StateIndex、health/observability 或 workbench shell；
- 新增手写 CLI/MCP/runtime transport；
- 以兼容为由复活旧 runtime/control-plane producer。

## Live acceptance

Contract/schema、focused tests、descriptor ready、projection clean、queue empty 和 dry-run 只证明 repo structural behavior。Runtime ready/provider running 需要 fresh OPL readback；paper/quality/publication claim 需要 fresh MAS owner/artifact/reviewer evidence。

## 相关入口

- [Architecture](../../architecture.md)
- [Controllers](../control/controllers.md)
- [Stage outcome](../control/progress_first_stage_outcome.md)
- [Active plan](../../active/mas-ideal-state-gap-plan.md)
