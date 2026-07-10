# External Runtime Dependency Gate

Owner: `MedAutoScience`
Purpose: `external_runtime_reference_boundary`
State: `active_policy`
Machine boundary: 本文定义 external executor/backend 的引用边界；runtime truth归 OPL provider readback、external source evidence与 MAS owner receipts。

## 结论

External runtime 不是 MAS 默认可用性的前置。MAS 当前是 OPL standard domain agent；OPL 持有 hosted runtime，MAS 持有医学 authority。

`Hermes-Agent`、MedDeepScientist/DeepScientist 与 external workspace 只允许以下角色：

- explicit non-default executor/proof lane；
- historical backend audit；
- explicit archive import；
- upstream learning/provenance；
- parity oracle。

它们不得成为 MAS 默认 runtime、默认 diagnostic、quality owner、artifact authority 或 publication gate。

## Allowed evidence

External surface 可以提供：

- repo/release/manifest identity；
- provider/executor connectivity proof；
- explicit archive provenance；
- behavior/parity audit refs；
- external workspace/artifact refs；
- independent executor attempt receipt。

MAS owner 必须按当前 contract消费这些 refs，才能影响 study truth或 owner route。

## Forbidden interpretation

- external service reachable 不等于 MAS paper progress；
- executor attempt completed 不等于 quality/publication ready；
- historical backend parity 不等于 current runtime ready；
- archive import 不等于 canonical artifact authority；
- external workspace state 不得直接覆盖 MAS study truth；
- 缺 external evidence 不得恢复 MAS-local scheduler、runner、CLI/MCP transport、installer或 workbench。

## Owner route

| 缺口 | Owner |
| --- | --- |
| OPL provider/runtime | OPL runtime owner |
| explicit executor adapter | OPL executor/provider owner |
| external archive/provenance | source/archive owner |
| medical truth/quality/publication | MAS owner |
| credentials/human approval | explicit human gate |

Repo-side contract/test只能证明引用边界和 fail-closed behavior；不能生成外部部署、credential、live provider或真实 workspace evidence。

## Historical blocker

`EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB` 只作为旧 cutover blocker provenance保留，不得作为当前 MAS 默认状态。当前状态读 [Status](../../status.md) 与 fresh owner/runtime surfaces。

## Live evidence

Explicit executor/proof、external archive、provider running与 parity claim需要对应 live/readback/artifact evidence。缺证据时保持 `evidence_required`，不包装成 ready，也不新增 MAS private platform。

## 相关入口

- [Runtime boundary](../../runtime/contracts/runtime_boundary.md)
- [Architecture](../../architecture.md)
- [Invariants](../../invariants.md)
- [Status](../../status.md)
