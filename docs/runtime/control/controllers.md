# MAS Controllers

Owner: `MedAutoScience`
Purpose: `domain_control_boundary`
State: `active_current_truth`
Machine boundary: 本文解释 MAS domain control。机器真相归 stage/action contracts、controller durable surfaces、owner receipts 与 OPL StageRun readback。

## Controller 不是平台

MAS controller 只处理医学 policy/authority，不拥有 scheduler、queue、attempt、StateIndex、lifecycle、storage、health、environment 或 workbench。

允许的职责：

- 读取 MAS-owned study/source/artifact refs；
- 验证 request identity、authority boundary 与 forbidden writes；
- 生成医学 policy result、owner receipt、typed blocker 或 human gate；
- 物化 MAS-owned publication/quality/artifact decision；
- 把 `StageOutcome` 解释为 nonbinding Codex route context。

禁止的职责：

- 从 queue/attempt/provider/UI 状态选 current owner；
- 维护 repo-local runner、dispatch ledger、retry/dead-letter 或 resume token；
- 重建 OPL StateIndex、runtime health 或 storage maintenance；
- 充当 CLI/MCP/workbench facade；
- 用 mechanical score/validator 关闭 AI-first quality gate。

## Current control chain

```text
OPL StageRun output
  -> MAS domain policy/authority evaluation
  -> StageOutcome
  -> nonbinding Codex route context
  -> OPL transport/readback
  -> same-identity MAS owner consumption
```

`StageOutcome` 可以是：

- owner receipt；
- stable typed blocker；
- human gate；
- route-back；
- artifact/evidence delta refs；
- independent reviewer/auditor receipt。

缺 route context 时保留 StageOutcome、artifact 或 no-output/failure diagnostic，Codex 仍可启动任一 declared stage；不从 legacy current work unit、provider admission、PaperRecovery 或旧 domain-action request 补推 owner/action。只有真实 authority/safety/permission/identity/currentness、不可逆动作或显式 human decision 才 fail closed。

## Quality independence

程序负责 schema、identity、evidence refs 与 forbidden writes。医学质量结论必须来自独立 AI reviewer/auditor invocation，publication gate 由 MAS owner解释；OPL 只运输 receipt refs。

## Platform repair

Currentness、projection、transport、StateIndex、storage、health 或 workbench 问题若没有同步产生 domain delta或 stable typed blocker，只能记为 OPL platform repair，不能写成 paper progress。

## Legacy surface

旧 provider admission、current work unit、PaperRecovery、domain-action request、owner-callable body carrier 和 repo-local runtime shell只允许 tombstone/provenance/no-resurrection guard。不得新增 compatibility adapter、alias 或专门 rollup/currentness subsystem。

## Live evidence

Controller shape/test pass 不等于 live apply。只有 fresh StageRun/readback、owner receipt、typed blocker、human gate、reviewer receipt或真实 artifact delta 能证明对应 live outcome。

## 相关入口

- [Runtime boundary](../contracts/runtime_boundary.md)
- [Stage outcome](./progress_first_stage_outcome.md)
- [Invariants](../../invariants.md)
- [Active plan](../../active/mas-ideal-state-gap-plan.md)
