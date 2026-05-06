# AI-first Closeout / Handoff Governance

本文件定义 MAS AI-first 并行 lane 的人工/AI 接力规则。它服务 closeout 审阅、handoff 续接和非冲突计划收口；不新增 wording gate，不参与 publication gate、submission gate、runtime authority 或真实论文质量判定。

## 适用范围

本轮 governance 只覆盖 repo-tracked closeout/handoff 材料和轻量 meta 测试。

本轮不覆盖：

- live study artifact 手工修补；
- `DM002` live artifact 修改；
- `risk-*` 独立线；
- 真实论文 soak；
- 外部 worktree 清理；
- `README*`、`docs/status.md` 或主 checkout 已有外部未提交改动相关文件。

## Closeout 记录语义

每条非冲突计划完成记录必须落在 `docs/program/plan_completion_ledger.md`，并使用同一组 ledger 字段。记录只说明计划项、落地证据、验证证据、push/cleanup 状态、live surface 验收和剩余缺口；不得把 narrative closeout 升级为机械质量 gate。

`external_active_owner` 表示该项仍由本轮以外的活跃对话、worktree、branch 或上游 PR 持有。使用该状态时必须能回答：

- owner 类型；
- owner 标识；
- 本轮为什么不能吸收、清理或改写；
- 本轮允许的动作边界；
- 后续接力入口。

`external_active_owner` 不是完成态，也不是失败态。它是并行工作中的 ownership 保留状态，用于阻止当前 lane 抢占外部活跃线。

## Worktree 清理规则

closeout 只能清理本轮新建并完成吸收的 worktree/branch。任何本轮开始前已存在、由其他对话持有、名称或状态无法确认、等待上游 review、或被用户明确排除的 worktree/branch 都必须保留，并在 ledger 中标记 owner。

吸收或清理 worktree/branch 前必须先用 `ai_first_external_lane_registry` 形成 closeout cleanup safety check。若 safety check 判定 `must_preserve=true` 或 `allowed_to_cleanup=false`，当前 lane 只能记录 `external_active_owner` 或 `not_performed_by_request`，不得吸收、重写或删除该对象。

默认 external active 保护名称包括 `paper-orchestra-*`、`mas-gate-*`、`mas-progress-*` 和 `mas-runtime-*`。`ai-first-*` 只在登记为 external active 时受保护；本轮新建且未登记 external active 的 `ai-first-*` worktree 可以按本轮 closeout 权限和验证结果进入清理判定。

如果 lane 没有 merge、push 或 cleanup 权限，记录必须写明 `not_performed_by_request` 或 `external_active_owner`，不能写成已清理。

## Handoff 记录模板

| 字段 | 必填 | 允许状态或内容 |
| --- | --- | --- |
| `plan_id` | yes | 稳定计划 ID。 |
| `planned_items` | yes | 可逐项判定的验收项。 |
| `landed_commits` | yes | commit/branch，未落地写 `none`，外部活跃写 `external_active_owner`。 |
| `tests_run` | yes | 实际运行命令，未运行写 `none` 并说明原因。 |
| `pushed` | yes | `yes`、`no`、`not_performed_by_request` 或 `external_active_owner`。 |
| `worktrees_cleaned` | yes | `yes`、`no`、`not_performed_by_request` 或 `external_active_owner`；只能描述本轮 worktree。 |
| `live_surface_verified` | yes | 只读验收 surface 或 `none`。 |
| `skipped_with_user_acceptance` | yes | 用户明确接受的跳过项；没有写 `none`。 |
| `remaining_gaps` | yes | 尚未闭环的问题；没有写 `none`。 |
| `handoff_receiver` | yes | 下一接手者、外部 owner 或 `none`。 |
| `handoff_entrypoint` | yes | 下一次继续时读取的文档、surface、branch、PR 或命令。 |
| `out_of_scope_boundaries` | yes | 本轮明确不触碰的 live artifact、worktree、risk 或 soak 边界。 |

## 当前 AI-first 边界

真实论文 soak 和 `DM002` live artifact 仍不属于本轮 closeout/handoff governance lane。可以记录它们是剩余证据缺口或外部 live observation anchor，但不能把本文件、ledger narrative 或 meta 测试解释成真实论文质量改善、submission readiness 或 artifact 修复证据。
