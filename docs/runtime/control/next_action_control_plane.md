# Codex Route Context 与旧 Next Action 控制面退役

Owner: `MedAutoScience`
Purpose: 说明 Codex CLI 唯一 stage 语义路由权，以及旧 `NextActionEnvelope` 的非绑定 transport 角色。
State: `active_retirement_boundary`
Machine boundary: 机器真相归 `agent/stages/manifest.json`、`agent/stages/stage_route_contract.yaml`、`contracts/next_action_envelope_contract.json`、源码、StageRun readback 与 owner receipts。本文不授权 runtime、domain truth、paper/package、quality 或 submission 写入。

## 结论

Codex CLI 是唯一 stage 语义控制面。上一个 stage 的任何 raw、free-text、partial、negative、failed、corrupt/unreadable 或 no-output diagnostic 都能成为下一 declared stage 的输入。Codex 可以 advance、skip、repeat、reverse 或 route-back 到任一 declared stage。

旧 `NextActionEnvelope` 不再是默认 next-action authority。其物理名暂作 legacy readback locator，但机器语义已经收薄为非绑定 `Codex route context`；默认且唯一的语义根是 `Codex CLI selected declared stage`：

- `next_action_authority=false`
- `route_selection_owner=codex_cli`
- `binding=false`
- `action_family_authority=false`
- `next_stage_may_start=true`

它只能运输 Codex 已明确选择的 stage/action、currentness refs、raw/typed artifact refs、quality debt 和 diagnostic。它不能从 work-unit 文本、reason registry、priority lattice、transition table、`allowed_actions` / `blocked_actions` 或 read model 猜测下一步，也不能因为缺字段拒绝 another declared stage。

## Progress-First

retry、review、repair、redrive 与 schema/validator 修正次数只代表质量预算。预算耗尽或输出不完整时：

1. 保留最佳 artifact、负结果和 failed-path lineage；
2. 必要时物化 no-output/failure diagnostic；
3. 标记 `completed_with_quality_debt`；
4. 关闭 quality/publication/export/submission/ready claim；
5. 把全部材料交给 Codex 选择下一 declared stage。

只有 executor unavailable、wrong-target identity/currentness、真实权限/凭据/安全/authority、不可逆动作授权或显式 human decision 可以 hard-stop。

## Transport Boundary

OPL `StageRun` / `StageAttemptReceipt` 持有 attempt、provider、retry/resume、currentness 与 refs transport，不选择医学 successor。MAS owner surfaces 持有医学 truth、quality/publication verdict、artifact/package authority、owner receipt 与真实硬边界 blocker。Receipt、provider completion、queue、read model、schema、tests 与 file presence 都不是 stage transition authority。

旧 `current_work_unit`、`current_executable_owner_action`、PaperRecovery、transition matrix、provider-admission candidate 和 `control/next_action.json` 只保留 diagnostic/provenance/no-resurrection 角色；它们不能重新生成默认 action、阻止 stage 启动或覆盖 Codex route。
