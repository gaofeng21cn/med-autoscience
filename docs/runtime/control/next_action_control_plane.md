# Stage Route Decision 与 Transition Materialization

Owner: `MedAutoScience`
Purpose: 说明 decisive Attempt 的语义路由权与 OPL StageRun controller 的 transition 物化边界。
State: `active_current_boundary`
Machine boundary: 机器真相归 `agent/stages/manifest.json`、`agent/stages/stage_route_contract.yaml`、StageRun readback 与 owner receipts。本文不授权 runtime、domain truth、paper/package、quality 或 submission 写入。

## 结论

语义 route decision 只能由当前 StageRun 的 decisive Codex Attempt 给出：primary-only StageRun 是 producer；formal Review StageRun 是终局 reviewer 或 re-reviewer。上一个 Stage 的 consumable artifact、partial/negative result 或已物化的 failure diagnostic 都能成为下一 declared Stage 的输入；decisive Attempt 可以建议 advance、skip、repeat、reverse 或 route-back 到任一 declared Stage。

旧 `NextActionEnvelope` 已从 active machine contract 退役，只保留 Git 与 history provenance。当前双 owner ABI 是：

- `semantic_route_decision_owner=decisive_codex_attempt`
- `stage_transition_materialization_owner=opl_stage_run_controller`
- Attempt 只输出 route recommendation / route impact
- controller 只校验 decisive role、declared target 与合法 shape，然后物化 transition

OPL transport 只能运输 decisive Attempt 已明确给出的 target、currentness refs、artifact refs、quality debt 和 diagnostic。它不能从 work-unit 文本、reason registry、priority lattice、transition table、`allowed_actions` / `blocked_actions` 或 read model 猜测下一步，也不能改写医学路由语义。

## Progress-First

retry、review、repair、redrive 与 schema/validator 修正次数只代表质量预算。预算耗尽或输出不完整时：

1. 保留最佳 artifact、负结果和 failed-path lineage；
2. 必要时物化 no-output/failure diagnostic；
3. 标记 `completed_with_quality_debt`；
4. 关闭 quality/publication/export/submission/ready claim；
5. 由 decisive Attempt 给出语义 route recommendation，controller 物化合法 target。

只有 executor unavailable、wrong-target identity/currentness、真实权限/凭据/安全/authority、不可逆动作授权或显式 human decision 可以 hard-stop。

## Transport Boundary

OPL `StageRun` / `StageAttemptReceipt` 持有 attempt、provider、retry/resume、currentness 与 refs transport；controller 持有 transition materialization，但不选择医学 successor。MAS owner surfaces 持有医学 truth、quality/publication verdict、artifact/package authority、owner receipt 与真实硬边界 blocker。Receipt、provider completion、queue、read model、schema、tests 与 file presence 都不是语义 route decision authority。

旧 `current_work_unit`、`current_executable_owner_action`、PaperRecovery、transition matrix、provider-admission candidate 和 `control/next_action.json` 只保留 diagnostic/provenance/no-resurrection 角色；它们不能重新生成默认 action、阻止 stage 启动或覆盖 Codex route。
