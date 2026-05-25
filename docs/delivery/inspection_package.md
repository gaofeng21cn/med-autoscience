# Inspection Package 交付契约

Owner: `MedAutoScience`
Purpose: `human_inspection_only_delivery_export_contract`
State: `active_support`
Machine boundary: 人读交付契约。正式 delivery authority 继续归 `paper/`、`submission_minimal`、`study_delivery_sync`、publication gate、AI reviewer verdict 与 controller decisions。

`inspection_package` 是人工检查导出面。blocked gate、bundle blocked、`submission_minimal` / `current_package` stale 或 missing 时，它导出当前 draft / canonical paper surfaces 的快照；当 `delivery_inspector` 证明现有 `current_package.zip` 已是 controller-authorized current package 时，它可以只写 human-inspection-only review pointer，并返回 `authorized_current_package_available` 与 `recommended_human_review_path`。两种路径都帮助人工理解当前稿件、证据、图表、review ledger 和 delivery 状态；两种路径都不创建投稿授权。

## 允许输入

允许读取：

- `study_root/paper/` 下的 canonical manuscript source、draft、figures、tables、evidence ledger、review ledger、study charter、revision / rebuttal input。
- 已存在的 generated DOCX/PDF/figure/table projection，前提是在 manifest 中标记为 `existing_projection_snapshot`。
- `publication_gate`、`publication_supervisor_state`、`domain_health_diagnostic` 或 `study_progress` 的 blocked context，前提是仅作为 provenance。
- `delivery_inspector` 已判定为 current 的 `manuscript/current_package.zip`，仅可作为 `authorized_current_package_available` review pointer，不可作为 canonical snapshot source 或 authority root。

禁止把以下对象作为 authority 输入：

- `manuscript/current_package/`
- `manuscript/current_package.zip`
- journal package mirror
- legacy unmanaged submission surface
- inspection package 上一次导出结果

## 允许输出

blocked/stale snapshot 路径允许写入：

- `study_root/manuscript/inspection_package/`
- `study_root/manuscript/inspection_package.zip`
- `study_root/artifacts/inspection_package/manifest.json`
- `study_root/artifacts/inspection_package/source_inventory.json`
- `study_root/artifacts/inspection_package/checksums.json`
- `study_root/artifacts/inspection_package/blocked_context.json`
- `study_root/artifacts/inspection_package/export_receipt.json`
- `study_root/artifacts/inspection_package/latest.json`

输出 manifest 必须包含：

- `surface_kind = inspection_package`
- `authority = human_inspection_only`
- `not_for_submission = true`
- `gate_blocked_snapshot = true`（blocked snapshot 物化模式）或 `gate_blocked_snapshot = false`（authorized current-package pointer 模式）
- `source_inventory`
- `blocked_context_refs`
- `forbidden_writes`

当前 controller 同步写 `manuscript/inspection_package_manifest.json` 作为人读包旁路 manifest，并写 `artifacts/inspection_package/latest.json` 作为 stable owner receipt。

当 `delivery_inspector` 证明正式 `current_package.zip` 已 current 且调用方未指定 `--force-materialize` 时，controller 只写 `manuscript/inspection_package_manifest.json`、`artifacts/inspection_package/latest.json` 及 `artifacts/inspection_package/*` inspection metadata；manifest status 为 `authorized_current_package_available`，`targets.authorized_current_package_zip` 指向现有正式包。该路径不写 `manuscript/inspection_package/` 或 `manuscript/inspection_package.zip`，也不更新正式 delivery authority。

## Forbidden writes

`inspection_package` 的实现和任何 product-entry / CLI / MCP wrapper 都不得写：

- `study_root/paper/submission_minimal/`
- `study_root/manuscript/current_package/`
- `study_root/manuscript/current_package.zip`
- `study_root/paper/journal_submissions/`
- `study_root/manuscript/journal_package_mirrors/`
- `study_root/artifacts/publication_eval/latest.json`
- `study_root/artifacts/controller_decisions/latest.json`

它也不得调用会 materialize 这些 surface 的 apply path，包括 `submission_minimal` export、`study_delivery_sync`、journal package materialization、AI reviewer eval materializer 或 outer-loop decision writer。

## 导出模式与使用条件

`inspection_package` 有两种当前模式：

1. Blocked snapshot 物化：在以下状态导出 `manuscript/inspection_package/` 与 `manuscript/inspection_package.zip`：

- `publishability_gate` blocked
- bundle gate blocked
- `publication_supervisor_state.bundle_tasks_downstream_only = true` 且下游 bundle/write action 被 gate 阻止
- `submission_minimal` / `current_package` stale 或 missing，但 canonical `paper/` surface 可读

2. Authorized current-package pointer：当 `delivery_inspector` 证明现有 `current_package.zip` 已是 current controller-authorized package，且未显式 `force_materialize` 时，只写 `manuscript/inspection_package_manifest.json` 与 `artifacts/inspection_package/*.json` receipt / source inventory，返回 `status=authorized_current_package_available` 和 `recommended_human_review_path`。这条路径不重新物化 inspection zip，不写 `current_package`，不生成新的 freshness proof。

显式 `--force-materialize` 会走 blocked snapshot 物化路径，生成独立 human-inspection snapshot；它不改变投稿或 delivery authority。

导出成功只代表 inspection snapshot 或 review pointer 可读。它不改变 gate status，不关闭 blocker，不更新 `publication_eval/latest.json`，不写 `controller_decisions/latest.json`，不生成 `current_package` freshness proof。

## 测试计划

Focused tests 应覆盖以下契约：

- inspection package contract documents forbidden writes and human-inspection-only authority。
- blocked publishability / bundle gate 下允许 inspection export，但 export plan 不包含 submission / current package / eval / decision writes。
- current authorized package 下允许返回 review pointer，但不得重新写 `current_package` 或把 pointer 当作 submission authority。
- 现有 `delivery_inspector` 和 product-entry `delivery_inspection` projection 保持 read-only，不能授权 submission、publication quality 或 delivery sync dispatch。
- inspection output manifest 与 source inventory 区分 `canonical_paper_snapshot` 和 `existing_projection_snapshot`。
- 如果 source 只来自 `current_package`、journal mirror 或旧 inspection package，export 必须 fail closed。
