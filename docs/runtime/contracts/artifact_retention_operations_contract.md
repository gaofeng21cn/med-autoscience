# Artifact Retention Operations Contract

## 目标

Artifact retention 只管理文件生命周期，不持有研究、发表或论文质量真相。它的职责是把可安全清理、可重建投影、运行态历史和终局止损线的文件保留策略投影成机器可读计划，并在真正物理操作前提供校验门。

## 普通 Retention Plan

普通 surface 是 `artifact_retention_operations_plan`。它只能执行一个物理动作：

- `delete-safe-cache`

其他类型只做计划或阻断：

- `canonical_source`、`data_release`、`audit_log`、`human_handoff_mirror` 保持在线。
- `derived_projection` 只能标记 `regenerate_projection_then_remove_stale`，物理移除前必须先由 canonical source 重建。
- `runtime_ephemeral` 默认 keep/audit-only；archive-compress 只是 candidate，当前不自动 apply。
- `cold_archive` 必须有 restore contract 后才能进入后续清理。

`delete-safe-cache` 候选必须携带目标当前 `target_sha256`。`control-plane-cleanup-apply` 消费 retention report 时，执行前会重新计算目标 sha256；如果报告里的 safe-cache 候选与当前目标不一致，直接 blocked 为 `retention_report_target_drifted_from_safe_cache`。

## 终局止损生命周期

终局 study file lifecycle 的 surface 是 `terminal_study_file_lifecycle_plan`，只在以下 macro state 同时成立时 eligible：

- `writer_state=parked`
- `user_next=none`
- `reason=stop_loss`
- `details.reopen_allowed=false`

这表示用户/owner 已明确关闭该路线，不只是早期止损建议、人工暂停或等待新方案。

即使 eligible，当前仍只生成 `mode=dry_run`：

- 必须保留 canonical source、data release、audit log 和 human handoff mirror。
- runtime ephemeral 只能标记为 `terminal_archive_compact_after_manifest`。
- 物理 archive/compact 仍要求 manifest、sha256、restore index、summary 和 restore proof。
- 没有 restore proof 的情况下不得删除或压缩 authority surface。

## SQLite 与文件 Authority

lifecycle refs SQLite store 只作为 refs index/read model/receipt 查询层。它可以索引 retention plan、archive ref、checksum、restore proof 和 owner route receipt；论文真相、用户干预记忆和可交付文件仍保留文件形态。

这套设计吸收四类成熟工程原则：[controller reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)、[幂等请求 token](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)、[SQLite application file format](https://www.sqlite.org/appfileformat.html)、[BagIt 风格 manifest/checksum preservation](https://www.rfc-editor.org/rfc/rfc8493)。它们是工程依据，不是新的 runtime 依赖。
