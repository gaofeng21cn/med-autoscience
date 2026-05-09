# Bounded Analysis Frontier Policy

这份 policy 学习 `DeepScientist` optimize skill 中的 frontier、plateau、fusion、debug、stop 思路，并把它翻译为医学补充分析和 revision repair 的候选板规则。

## 目标

`bounded_analysis` 不能变成无限分析扩张。每次补充分析都必须服务明确 claim、reviewer concern、publication gate blocker 或 route-back reason。

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
- winning path
- failed paths
- evidence refs
- reviewer concern closure status
- next route：`write`、`finalize`、`decision` 或继续同一 bounded route
