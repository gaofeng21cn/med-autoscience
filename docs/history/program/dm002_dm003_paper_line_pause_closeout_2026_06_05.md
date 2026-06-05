# DM002 / DM003 paper-line pause closeout 2026-06-05

Owner: `MedAutoScience`
Purpose: `paper_line_pause_closeout`
State: `history_provenance`
Machine boundary: 本文是人读暂停收尾记录。当前 truth 继续归 MAS/OPL live runtime surfaces、study workspace artifacts、publication eval、publication gate、controller decisions、OPL queue / attempt ledger、owner receipts 和 typed blockers。

## Scope

本次只执行 paper-line 暂停、live truth 冻结和收尾记录。未继续 tick、redrive、dispatch 或推进论文写作；未直接修改 Yang workspace 的论文正文、`publication_eval/latest.json`、`controller_decisions/latest.json`、OPL sqlite/runtime state 或 paper/package truth。

## Live Pause Result

暂停原因：`manual_pause_for_mas_opl_platform_optimization`。

| Study | Queue hold | Held attempt | Attempt status | Provider status | Queue task status |
| --- | --- | --- | --- | --- | --- |
| `002-dm-china-us-mortality-attribution` | `queue_hold_b8a0e9a4fb8281fd493d2fdf` | `sat_187bca513e83d3bd30ffd208` | `human_gate` | `operator_hold_requested` | `waiting_approval` |
| `003-dpcc-primary-care-phenotype-treatment-gap` | `queue_hold_8654173cd77c53e78e082aa8` | `sat_91d93d3eb7f6de1cad182e8a` | `human_gate` | `operator_hold_requested` | `waiting_approval` |

Follow-up live check：

```text
opl family-runtime attempt list --status running --json
filtered_total = 0
running = []
```

因此当前没有 live running provider attempt。两条线如需恢复，必须先走 hold release / human approval，再由当前 owner route 或下一代 StageRun controller 重新生成可执行 work unit；不能直接运行全局 tick 把论文线重新推入循环。

## State Before Pause

暂停前两篇均已从旧 `opl_execution_authorization_required` typed blocker 推进到 write-owner repair：

| Study | Action | Work unit | Dispatch ref |
| --- | --- | --- | --- |
| DM002 | `run_quality_repair_batch` | `manuscript_story_repair` | `studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/c8d6ba3192e1b684c49f88fd.json` |
| DM003 | `run_quality_repair_batch` | `medical_prose_write_repair` | `studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/0ecf4193a462962753d734c6.json` |

这表示 MAS owner route 已看见下一步写作修复，不表示论文已经在产出有效 manuscript delta，也不表示 publication-ready。

## Publication Truth

Fresh read of authoritative publication surfaces：

| Study | `publication_eval/latest.json` | `publishability_gate/latest.json` |
| --- | --- | --- |
| DM002 | `overall_verdict=blocked`, `primary_claim_status=partial`, route-back target `write` | `status=blocked`; blockers include stale authority mirrors, unresolved reviewer concerns, claim-evidence failure, submission hardening gaps and forbidden manuscript terminology |
| DM003 | `overall_verdict=blocked`, `primary_claim_status=partial`, route-back target `write` | `status=blocked`; blockers include stale authority mirrors, unresolved reviewer concerns, submission hardening gaps and forbidden manuscript terminology |

结论：两篇当前都不是 publication-ready、submission-ready、paper closure 或 current-package-ready。暂停的是 write repair stage，不是最终交付阶段。

## Platform Diagnosis

近 9 小时的主要真实进展属于 MAS/OPL control-plane repair：AI reviewer record currentness、gate-clearing replay routing、owner-route consumption、default-executor dispatch authorization、provider attempt liveness / hold projection。它们改善了“下一 owner 能否被看见并被 OPL 接走”，但在暂停前尚未形成新的 paper/manuscript/package delta、independent reviewer/auditor closeout、human gate receipt 或 stable domain typed blocker。

本轮应按 `platform_repair` 归类，不计入 paper progress。后续平台优化的优先方向：

1. OPL StageRun controller：用 `StageRun.spec/status/observed_generation` 统一运行状态，避免 `latest.json`、owner-route reconcile、materialize、dispatch、attempt ledger 多面互相解释。
2. MAS receipt / blocker transition authority：Stage 完成只由 MAS `OwnerReceipt` 或 `TypedBlocker` 授权，provider completion 和 file presence 只做 evidence。
3. Currentness / dispatch arbitration：旧 request、旧 closeout、旧 provider attempt 必须按 generation / source eval / work unit fingerprint 自动 supersede，不再消耗当前预算。
4. Pause / hold visibility：study-wide hold、attempt hold、waiting approval 和 provider liveness 必须在 operator read model 中同屏可见。
5. Progress accounting：platform repair、paper delta、human gate、stable blocker 分账，防止控制面修复被误报为论文推进。

## Do Not Resume By Accident

- 不运行全局 `opl family-runtime tick` 或 MAS domain-health apply 来重新启动两条论文线，除非用户明确要求恢复。
- 不直接写 study workspace truth、paper body、publication eval、controller decision、current package 或 OPL sqlite state。
- 恢复前必须先 fresh read `study_progress`、publication eval、gate、queue hold 和 StageRun / owner-route surface。

## Evidence Commands

本记录基于以下 fresh commands 的结果：

```bash
opl family-runtime queue hold --study 002-dm-china-us-mortality-attribution --reason manual_pause_for_mas_opl_platform_optimization --json
opl family-runtime queue hold --study 003-dpcc-primary-care-phenotype-treatment-gap --reason manual_pause_for_mas_opl_platform_optimization --json
opl family-runtime attempt list --status running --json
opl family-runtime attempt list --study 002-dm-china-us-mortality-attribution --json
opl family-runtime attempt list --study 003-dpcc-primary-care-phenotype-treatment-gap --json
opl family-runtime queue list --study 002-dm-china-us-mortality-attribution --json
opl family-runtime queue list --study 003-dpcc-primary-care-phenotype-treatment-gap --json
jq ... studies/002-dm-china-us-mortality-attribution/artifacts/publication_eval/latest.json
jq ... studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/publication_eval/latest.json
jq ... studies/002-dm-china-us-mortality-attribution/artifacts/reports/publishability_gate/latest.json
jq ... studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/reports/publishability_gate/latest.json
```
