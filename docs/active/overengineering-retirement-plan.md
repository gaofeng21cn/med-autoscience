# MAS 过度设计退役与收薄计划

Owner: `MedAutoScience`
Purpose: `overengineering_closeout_reference`
State: `landed_reference`
Machine boundary: 本文只保留 closeout 结论。逐项 current status归 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)，机器事实归 contracts/source/tests/OPL readback。

## 结论

2026-07-10 批准的 12 项过度设计结构目标已全部落地。MAS 当前形态是：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`

本文件不再维护 lane、branch、dated test output、line-count流水或旧 completion audit；这些信息由 Git provenance与 `docs/history/`追溯。

## Closeout summary

| ID | 退役目标 | 终态 |
| --- | --- | --- |
| OE-01 | dead code / empty exports | deleted |
| OE-02 | unconsumed generated/package assets | deleted |
| OE-03 | MAS-local StateIndex pilot | OPL StateIndex + body-free refs |
| OE-04 | import-time editable bootstrap | standard packaging |
| OE-05 | pytest aggregate collection | native pytest collection |
| OE-06 | local environment/installer | OPL env/plugin provisioning |
| OE-07 | retirement subsystem | minimal no-authority/tombstone guard |
| OE-08 | repo-local workbench | OPL hosted workbench |
| OE-09 | Tool Arsenal/capability runtime | OPL-generated action surface |
| OE-10 | hand-written CLI/MCP glue | OPL-generated interfaces |
| OE-11 | runtime health/lifecycle/storage | OPL observability/lifecycle/StateIndex |
| OE-12 | legacy next-action family | `StageOutcome -> NextActionEnvelope` |

Exact completion evidence与 Live evidence分账见 [Active truth plan](./mas-ideal-state-gap-plan.md)。

结构 closeout 的 L1-L4 已完成；双仓本地 full verification、吸收、push/readback 与 worktree cleanup 仍按 L5 执行。`scripts/run-build-clean.sh` 是保留的正式 build-isolation runner；退役的是旧 runtime/editable clean runner。

## No resurrection

- 不恢复已删除的 CLI/MCP/parser/JSON-RPC/workbench/installer/runtime wrapper。
- 不为已退役 surface 新建 compatibility shim、alias、facade、registry、rollup、currentness或聚合测试。
- 普通 capability通过 action catalog/schema/handler target表达，由 OPL 生成 interface。
- 通用 runtime/index/lifecycle/environment/workbench需求路由 OPL。
- MAS只新增有 active caller且无法声明化的医学 authority function，并登记 authority inventory。

## Live evidence

Live evidence保持独立 `partial_deferred`。结构 closeout不声明 provider running、paper progress、quality/publication ready、artifact mutation authorized、submission ready或 production ready。

## 相关入口

- [Active truth plan](./mas-ideal-state-gap-plan.md)
- [Status](../status.md)
- [Architecture](../architecture.md)
- [Decisions](../decisions.md)
- [Historical completion ledger](../history/program/plan_completion_ledger.md)
