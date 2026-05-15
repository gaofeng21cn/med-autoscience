# Inspection Package 产品契约

Owner: `MedAutoScience`
Purpose: `human_inspection_only_delivery_surface`
State: `active_support`
Machine boundary: 人读产品契约。机器真相继续归 MAS controller、runtime、publication gate、AI reviewer、submission package contracts 与 generated artifact receipts。

`inspection_package` 面向医生、PI、编辑前审阅者和操作者，用于在论文尚未被 gate 放行时查看“当前稿件和 canonical evidence 到底是什么”。它不是投稿包，也不是质量裁决。

## 产品定位

`inspection_package` 解决的是 blocked state 下的人读可见性问题：

- `publishability_gate` blocked 时，人工可以查看当前 draft、canonical manuscript source、figures、tables、evidence ledger、review ledger、study charter 与 blocked context。
- bundle gate blocked 时，人工可以查看当前 bundle-stage inputs、已有 generated artifacts、缺口清单与 source inventory。
- 当前 `submission_minimal` 或 `current_package` stale / missing 时，人工仍能看到 canonical paper snapshot，避免把 stale handoff mirror 误认为当前研究真相。

它必须清楚标记：

- `human_inspection_only`
- `not_for_submission`
- `gate_blocked_snapshot`
- `source_inventory_present`
- `authority = human_inspection_only`

## 产品入口

当前可见性入口是 read-only 或 human-inspection-only export：

- CLI：`medautosci publication delivery-inspect --profile <profile> --study-id <study_id> --format json`
- CLI：`medautosci publication export-inspection-package --profile <profile> --study-id <study_id>`
- study progress：`delivery_inspection`
- workspace cockpit：`delivery_inspection_state`
- product-entry status：`workspace_delivery_inspection`
- product-entry action：`export_inspection_package`

`export_inspection_package` 挂在同一产品语义下，但 action effect 是 inspection export，不是 submission export、bundle apply 或 gate closeout。

## 用户可做与不可做

允许：

- 打开 inspection package 中的 manuscript、PDF preview、figures、tables、audit inventory 和 blocked-context summary。
- 对照 source inventory 判断当前显示内容来自哪个 canonical paper surface。
- 把人工意见转成 durable study task intake、reviewer revision intake 或 canonical paper repair input。

不允许：

- 将 `inspection_package` 当作 journal submission package。
- 在 inspection package 内直接修改稿件后声明完成。
- 把 inspection receipt 当成 `publication_eval/latest.json`、`controller_decisions/latest.json`、`submission_minimal` freshness proof 或 `current_package` freshness proof。
- 用 inspection export 触发投稿、bundle handoff、AI reviewer verdict 或 controller decision refresh。

## Product-entry 展示规则

Product-entry / cockpit 只展示 inspection package 的 read model：

- status：`available`、`blocked_export_available`、`missing_sources`、`stale_snapshot` 或 `not_available`
- source labels：`canonical_paper_snapshot`、`existing_projection_snapshot`、`blocked_gate_context`
- authority：`human_inspection_only`
- forbidden actions：`authorize_submission`、`clear_publishability_gate`、`dispatch_delivery_sync`、`write_current_package`、`write_submission_minimal`

如果用户需要正式投稿包，产品入口应引导回 MAS owner chain：publication gate / AI reviewer / controller decision / `submission_minimal` / `study_delivery_sync`，而不是把 inspection export 升格。
