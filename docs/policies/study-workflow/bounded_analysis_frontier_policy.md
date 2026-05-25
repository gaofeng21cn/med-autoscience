# Bounded Analysis Frontier Policy

Owner: `MedAutoScience`
Purpose: `bounded_analysis_frontier_policy`
State: `active_policy`
Machine boundary: Human-readable study-workflow policy only; study truth remains in workspace artifacts, source contracts, runtime/controller outputs, generated artifacts, and owner receipts.

这份 policy 学习 `DeepScientist` optimize skill 中的 frontier、plateau、fusion、debug、stop 思路，并把它翻译为医学补充分析和 revision repair 的候选板规则。候选板是 stage execution / audit trace，不是 route scorer、controller decision、publication quality verdict 或 source readiness verdict。

## 目标

`bounded_analysis` 不能变成无限分析扩张。每次补充分析都必须服务明确 claim、reviewer concern、publication gate blocker 或 route-back reason。

每轮 bounded analysis 必须先回指当前 study charter、claim/evidence map、source refs、reviewer concern 或 controller route-back reason。`candidate board` 是 stage 内的比较和审计面，可以记录 explore / exploit / fusion / debug / stop 候选、证据收益、成本风险和决策理由；它不能单独授权 publication quality、claim expansion、source readiness、artifact mutation、submission readiness 或 `current_package` 更新。新增分析若会扩大 primary claim、重定义人群/endpoint、引入新数据权限边界或改变 artifact authority，必须回到 `decision` / human gate，而不是在 candidate board 内自行放行。

## Candidate board

每轮 bounded analysis 至少维护一个 candidate board：

- `candidate_id`
- `route_meaning`: `explore` / `exploit` / `fusion` / `debug` / `stop`
- `target_claim_or_concern`
- `expected_evidence_gain`
- `cost_and_risk`
- `clinical_interpretability`
- `decision`
- `decision_reason`

## Route meanings

- `explore`：当前缺少足够候选解释，需要有限扩展。
- `exploit`：当前最强路线已经明确，需要补强证据或稳定展示。
- `fusion`：多条已成功或互补路线需要合并成更强 claim。
- `debug`：已有路线被具体错误、数据问题或 reviewer concern 阻断。
- `stop`：继续分析不会显著提高论文质量或会制造不诚实 claim。

## Plateau 规则

出现以下情况必须考虑 `stop` 或 route-back：

- 新分析只重复已有结论
- 结果改善不能转化为临床解释或 reviewer concern closure
- 分析需要突破 study charter 或数据权限边界
- claim 需要靠 post-hoc 叙事维持

## 输出要求

bounded analysis 结束时，必须留下：

- accepted / rejected candidates
- selected path or stop reason
- failed paths
- evidence refs
- reviewer concern closure status
- next route：`write`、`finalize`、`decision` 或继续同一 bounded route
- source fingerprint、claim boundary、controller / reviewer / human-gate refs 或 typed blocker，确保后续写作和交付不能只凭 candidate board 过线

这些输出只能作为 controller、AI reviewer、publication gate 和后续 stage 的输入。它们不能单独声明科学成功、publication ready、submission ready、artifact mutation authorization 或 `current_package` freshness。
