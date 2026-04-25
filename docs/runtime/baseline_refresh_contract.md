# Baseline Refresh Contract

这份 contract 学习 `DeepScientist` 的 baseline overwrite refresh flow，但在 `MAS` 中固定为医学 comparator / baseline 的显式刷新语义。

## 目标

当 baseline、comparator、Table 1、模型对照、外部验证或 paper-facing baseline surface 需要更新时，不能静默覆盖旧结果。

所有 refresh 必须留下可审计记录，说明：

- 原 baseline / comparator 是什么
- refresh 触发原因是什么
- 哪些 paper-facing surface 被影响
- 哪些 evidence / review / publication gate refs 需要同步
- refresh 后的 accepted baseline 是什么

## 允许的 refresh 场景

- cohort definition、endpoint、time horizon 或 exclusion rule 被正式更新
- baseline implementation 修复了确定性错误
- comparator 需要从 exploratory baseline 升级为 manuscript comparator
- Table 1、calibration、DCA、subgroup 或 external-validation surface 需要和最新 study charter 对齐
- publication gate 明确要求 baseline-facing surface refresh

## 禁止的 refresh 场景

- 为了让结果更好看而覆盖 baseline
- 没有 study charter / route decision 支撑的 comparator 替换
- 只改 manuscript prose，不更新 evidence / review / publication surface
- 用 terminal log 或 memory 代替 refresh record

## Baseline refresh record

正式 refresh 至少记录：

```yaml
schema_version: 1
record_type: baseline_refresh
study_id: <study_id>
quest_id: <quest_id>
previous_baseline_ref: <ref>
refreshed_baseline_ref: <ref>
refresh_reason: <reason>
affected_surfaces:
  - study_charter
  - evidence_ledger
  - review_ledger
  - publication_eval/latest.json
  - manuscript/tables
  - display_pack
verification_refs:
  - <command-or-artifact-ref>
route_decision_ref: <controller-decision-ref>
```

## Route integration

- `baseline` route 产出 accepted comparator 前，必须检查是否存在 pending refresh record。
- `analysis-campaign` 发现 baseline mismatch 时，必须 route back 到 baseline refresh，不得直接在分析结果中补救。
- `write` 和 `finalize` 发现 paper-facing baseline stale 时，必须要求 refresh 或显式 waiver。
- `publication_eval/latest.json` 可以把 stale baseline 投影成 `return_to_baseline` 或 `return_to_analysis_campaign`，但不能吞成 prose blocker。

## 与 DeepScientist 的关系

上游的 overwrite baseline refresh flow 证明：baseline 不是一次性附件，而是长期 research workspace 的可刷新 truth surface。

`MAS` 的吸收方式是把 overwrite 约束为 medical baseline refresh record：允许更新，但每次更新都必须可解释、可验证、可回退。
