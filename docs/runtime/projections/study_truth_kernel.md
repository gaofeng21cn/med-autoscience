# Study Truth Kernel

Owner: `MedAutoScience`
Purpose: `study_truth_projection_boundary`
State: `active_runtime_support`
Machine boundary: 本文解释 reducer/read-model 语义。机器真相归 MAS study artifacts、controller records、source、contracts 与 owner receipts。

## 定位

`StudyTruthKernel` 是 MAS 的 domain reducer，不是 runtime platform。它从 MAS-owned task intake、publication/quality decision、artifact authority、human gate与 owner receipts 派生 study truth snapshot。

它不拥有：

- OPL command/event/outbox/StageRun；
- queue、attempt、retry/dead-letter；
- StateIndex、storage/lifecycle、runtime health；
- CLI/MCP/status/workbench transport；
- 默认 next-action selection。

## Authority

Study truth snapshot 是 MAS domain projection。默认 next action 仍只来自：

`Codex CLI selected stage -> nonbinding route context`

Reducer 不从 delivery mirror、queue/attempt、provider、旧 current work unit、PaperRecovery 或 diagnostic projection补全 owner/action。

## Inputs

- study/task/reviewer-revision intake；
- MAS controller/owner decision；
- AI reviewer/publication gate record；
- canonical paper/evidence/artifact refs；
- memory/artifact authority decision；
- human gate/resume input；
- same-identity OPL StageRun/transport refs。

OPL refs 只证明 transport/currentness，不替代 MAS domain verdict。

## Outputs

Kernel 只输出可重建的 domain snapshot与 body-free refs，供 OPL generated status/workbench 和 MAS owner surfaces消费。Hosted surface 不得写回 truth、publication eval、controller decision、artifact body 或 memory body。

## Dominance

- explicit stop-loss/final-line decision 强于旧 ready/finalize projection；
- 新 task/reviewer revision 强于旧 stopped/submission projection；
- fresh human resume 强于旧 wait state；
- current AI reviewer/publication owner record 强于 stale quality projection；
- live writer/artifact lock 限制 package authority；
- current package/submission mirror 不是 study authority。

## Rebuild 与 currentness

Projection 可以重建，authority inputs不可由 projection 反推。Snapshot 缺 identity、current owner result 或 evidence refs 时 fail closed；修复 projection本身只算 platform/read-model repair，不算 paper progress。

## Evidence boundary

Reducer test、snapshot materialization、status visible 与 projection clean 不证明 live paper progress、quality ready、publication ready 或 production ready。对应 claim 需要 fresh owner receipt、reviewer/auditor receipt、human gate 或 canonical artifact semantic delta。

## 相关入口

- [Runtime boundary](../contracts/runtime_boundary.md)
- [Controllers](../control/controllers.md)
- [Stage outcome](../control/progress_first_stage_outcome.md)
