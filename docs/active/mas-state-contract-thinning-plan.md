# MAS 状态与 Contract 收薄计划

Owner: `MedAutoScience`
Purpose: `state_contract_thinning_active_plan`
State: `active_plan`
Machine boundary: 本文是人读执行计划。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、domain-handler receipt、runtime/controller durable surfaces、真实 workspace artifact、owner receipt、typed blocker 和 generated artifact proof。
Date: `2026-05-29`

## 目标

MAS 当前控制面要从多层局部状态、长 reason enum、supersession reason 和 projection-local 判断，收敛到 AI-first / executor-first 的最小稳定 contract。

目标形态是：

`macro_state + owner_route + receipt_or_blocker + evidence_refs`

这表示：

- `study_macro_state` 只表达短宏观状态，服务用户、operator 和 read model。
- `owner_route` 是唯一执行票据，服务 consumer、dispatch executor 和 OPL handoff。
- `owner receipt / typed blocker / human gate / stop-loss / terminal success` 是执行闭环。
- `evidence_refs` 指向 AI reviewer、auditor、publication gate、artifact、memory 或 runtime evidence；开放式医学判断由 AI executor / reviewer / skill 完成。

细分 `StudyRuntimeReason`、publication supervisor phase、stale/superseded reason、workbench/operator 文案和 projection-local status 只能作为 diagnostic detail、read-model explanation 或 typed blocker payload，不得成为跨入口执行 contract。

## 不变量

- 程序只做 authority refs、forbidden-write guard、idempotency、schema/provenance validation、receipt signing、typed blocker materialization 和 read-model projection。
- 医学质量、写作质量、路线判断、修订策略和发表判断必须回到 AI-first executor / reviewer / auditor record。
- 任何可执行动作必须绑定当前 `owner_route` 的 `route_epoch`、`source_fingerprint`、`next_owner`、`allowed_actions` 和 `idempotency_key`。
- 旧 dispatch、旧 publication eval、旧 controller decision、旧 runtime state 和旧 OPL attempt 只能落 typed blocker，不得被 projection-local reason 重新激活。
- OPL 继续持有 generic runtime / queue / attempt / retry / workbench shell；MAS 不恢复私有 scheduler、state-machine runner、queue 或 worker residency owner。

## 并行落地线

| Lane | 写集 | 完成信号 |
| --- | --- | --- |
| `active_plan_and_truth_docs` | `docs/active/mas-state-contract-thinning-plan.md`、`docs/active/mas-ideal-state-gap-plan.md`、`docs/status.md`、核心五件套与 ideal-state reference | active plan 已成为当前收薄目标入口；gap/status/ideal-state 明确 compact contract 与禁止误写口径。 |
| `macro_state_control_reason` | `src/med_autoscience/controllers/study_macro_state.py` 与 focused macro-state tests | 长 runtime/status reason 只进入 `details` 或 diagnostic 字段，不扩展 macro `reason` 稳定枚举。 |
| `runtime_projection_contract_docs` | `docs/runtime/projections/study_macro_state_and_owner_route.md`、`docs/runtime/control/study_runtime_orchestration.md` 和必要 contract notes | runtime docs 明确稳定控制面只承认 macro state、owner route、receipt/blocker、evidence refs。 |
| `consumer_followthrough` | owner-route、study-progress、product-entry、domain-handler 或 default-executor focused tests | current consumer 只从 `macro_state + owner_route + receipt_or_blocker + evidence_refs` 取得执行授权；长 reason / supervisor phase / liveness prose 只能进入 diagnostic 或 blocker payload。 |

## 当前可一次落地的范围

本轮一次关闭四条 lane。文档先固定目标态，源码和 focused tests 随后把至少一个真实 consumer 授权点从长 `StudyRuntimeReason` / projection-local reason 特例迁移到 owner-route / receipt-or-blocker / evidence-ref 驱动；剩余大规模 enum 删除只在有完整 consumer 兼容迁移证据后执行。

本轮允许：

- 新增 active plan。
- 更新 ideal/gap/status/current map/invariants/architecture 的 current truth。
- 在 macro-state 代码中补充短 reason / diagnostic reason separation。
- 更新 runtime projection/control 文档。
- 补 focused tests，证明长 reason 不提升为宏观控制状态，也不作为 current consumer 的执行授权开关。

本轮不做：

- 不修改真实 study workspace artifact、paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body。
- 不把现有 verified OPL refs-only ledger receipt 写成 MAS domain ready、production ready、publication ready 或 artifact authority。
- 不大规模删除 reason enum、typed blocker reason 或 owner-route reason；本轮先关闭授权依赖，后续物理删枚举需要全 consumer 覆盖证据。
- 不恢复 retired runtime transport、compat alias、fallback、scheduler 或 MAS-local generic runner。

## 完成门

- Active docs 明确 `macro_state + owner_route + receipt_or_blocker + evidence_refs` 是状态收薄目标。
- `study_macro_state` 的稳定 reason 仍保持短枚举；细分 status/runtime reason 进入 details/diagnostic。
- Runtime docs 声明细分 reason/supersession/publication supervisor phase 不是跨入口 execution contract。
- Consumer focused test 证明 current execution authorization 由 owner route / allowed actions / receipt-or-blocker / evidence refs 驱动，不能仅凭长 `StudyRuntimeReason` 或 projection-local reason 放行。
- Focused verification 通过：docs lint / conflict marker check，macro-state focused pytest，consumer focused pytest，必要时 runtime docs diff check。
- 并行 worktree 的改动已吸收回 `main`，临时 worktree 和分支已清理；未吸收项必须明确保留原因。

## 后续 direct implementation tail

本轮关闭授权依赖后，剩余尾项只允许作为覆盖面扩展，不再改变目标 contract：

1. 将更多 `study_progress`、product-entry、domain-handler export 和 default-executor dispatch consumer 改为读取同一个 materialized/shadow macro state 与 owner route。
2. 将 supersession reason 家族折叠为少量 stable blocker class，细分原因进入 `details`、`source_refs` 和 operator explanation。
3. 将 `StudyRuntimeReason` 标注为 diagnostic/read-model enum；新增执行判断必须进入 owner route 或 typed blocker，而不是扩展 long reason。
4. 对每个 owner-route consumer 增加 focused currentness test：旧 route 不可执行、forbidden writes 不发生、AI-first quality record 必须由独立 reviewer/auditor 支撑。
