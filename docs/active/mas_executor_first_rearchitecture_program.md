# MAS Executor-First 重构计划

Owner: `MedAutoScience`
Purpose: `executor_first_boundary`
State: `landed_reference`
Machine boundary: 本文说明当前 executor/owner split；机器事实归 pack、action catalog、domain route contracts 与 OPL runtime readback。

## 结论

Executor-first 已收敛为 OPL StageRun 内的执行策略，不再要求 MAS 维护 executor platform。

- `Codex CLI` 是 stage 内第一公民 executor。
- OPL 持有 scheduling、attempt、retry/dead-letter、resume、transport 与 executor adapter lifecycle。
- MAS pack 为 executor 提供 goal、context、authority boundary、tool affordances、knowledge refs 与 quality gate。
- MAS owner surface 只消费 stage outcome，并返回 receipt、typed blocker、human gate、route-back 或 domain refs。

## 当前执行链

```text
OPL StageRun
  -> executor reads MAS stage pack
  -> executor produces stage artifacts/evidence
  -> independent reviewer/auditor when required
  -> MAS owner validates domain authority result
  -> Codex CLI selected stage -> nonbinding route context
  -> OPL transports the next attempt or gate
```

Executor 可以在 stage 内选择读取顺序、工具、并行方式与候选比较；这些策略不应被硬编码成 MAS-local workflow engine。

## 不再维护

- repo-local executor scheduler/runner/session store；
- CLI/MCP executor transport；
- provider admission/current work unit/PaperRecovery next-action control plane；
- repo-local workbench、queue、attempt ledger 与 lifecycle shell；
- 同一 executor 自审并关闭 AI-first quality gate。

## Quality gate

需要质量裁决时，executor 与 reviewer/auditor 必须是独立 invocation、context/task record 与 receipt。OPL 可以运输这些 refs；MAS quality/publication owner 才能解释 verdict。

## Live evidence

结构链已落地。Provider running、真实 stage outcome、paper/artifact delta 与 quality/publication ready 仍需 fresh live evidence，当前不由本文声明。

## 相关入口

- [Architecture](../architecture.md)
- [Stage outcome runbook](../runtime/control/progress_first_stage_outcome.md)
- [Active truth plan](./mas-ideal-state-gap-plan.md)
