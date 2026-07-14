# MAS Executor-First 重构边界

Owner: `MedAutoScience`
Purpose: `executor_first_no_resurrection_guard`
State: `active_support`
Machine boundary: 本文解释已落地的 executor/owner split；机器事实归 Stage/action/quality contracts、OPL StageRun ledger 与 MAS authority results。

## 已落地形态

Codex Attempt 是 Stage 内最小执行单位；OPL StageRun controller 持有 invocation、
session isolation、retry、ledger 与 transition materialization。MAS 只声明 Stage goal、
专业依赖、quality rubric、route target 与 domain authority boundary。

四角色固定为 producer、reviewer、repairer、re_reviewer。正式 Review 使用独立
Attempt/session；repairer 不拥有终局 route authority。领域 route 由 decisive Codex
Attempt 决定，controller 只校验并物化。

## 禁止复活

MAS 不得新增 repo-local runner、scheduler、queue、session store、attempt ledger、
runtime lifecycle、workbench、CLI/MCP transport 或 route transition controller。
其他 executor 只通过 OPL 显式 adapter 接入，不承诺与 Codex CLI 质量等价。

## Evidence boundary

Contracts、focused tests 和 generated interface readback证明结构；真实 session isolation、
StageRun replay、provider residency 与 paper outcome 仍需 OPL runtime/owner evidence。
