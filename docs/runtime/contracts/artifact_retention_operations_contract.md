# Artifact Retention Operations Contract

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime contract and stage-surface boundaries for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable runtime contract support only; enforceable runtime truth remains in machine-readable contracts, source, tests, CLI/read-model output, runtime ledgers, and owner receipts.

## 目标

Artifact retention 只管理文件生命周期，不持有研究、发表或论文质量真相。它的职责是把可安全清理、可重建投影、运行态历史和终局止损线的文件保留策略投影成机器可读计划，并在真正物理操作前提供校验门。

通用 retention / restore / locator / lifecycle shell 归 OPL / shared family layer；MAS 在本合同中只定义医学 artifact authority refs、candidate plan、typed blocker、restore-contract gap 和 no-forbidden-write 证据。OPL lifecycle receipt 可以证明 transport、索引、checksum、restore proof 或 operator review item 存在；它不能替代 MAS artifact mutation authorization、publication quality verdict、source readiness verdict、memory accept/reject 或 `current_package` freshness proof。

## 普通 Retention Plan

普通 surface 是 `artifact_retention_operations_plan`。它只生成 read-only 计划与候选动作；当前 public CLI、domain entry、product-entry command contract 和 MCP public surface 都不得暴露 `control-plane-cleanup-apply` 或 `control-plane-safe-cache-cleanup-apply`。计划中唯一可标记为物理 apply candidate 的动作是：

- `delete-safe-cache`

其他类型只做计划或阻断：

- `canonical_source`、`data_release`、`audit_log`、`human_handoff_mirror` 保持在线。
- `derived_projection` 只能标记 `regenerate_projection_then_remove_stale`，物理移除前必须先由 canonical source 重建。
- `runtime_ephemeral` 默认 keep/audit-only；archive-compress 只是 candidate，当前不自动 apply。
- `cold_archive` 必须有 restore contract 后才能进入后续清理。

`delete-safe-cache` 候选必须携带目标当前 `target_sha256`，并由 `storage_governance_policy_projection` 以 `read_only=true`、`physical_apply_performed=false` 投影成 operator review item。真正物理清理属于 OPL cleanup / restore / retention shell 的后续 owner surface；在该 owner surface 出现前，MAS 只能输出候选、blocker、restore-contract gap 和 artifact authority refs，不能执行 cleanup apply。

2026-06-19 起，MAS repo-local runtime storage maintenance 的物理 apply 也按同一 owner 边界执行：workspace apply、direct quest backend/slimming、restore-proof compaction、archive/report retention apply、semantic raw migration、git temp cleanup、workspace-root git reinitialize/retire 和 delete-safe-cache apply 都必须消费 `opl_runtime_storage_maintenance_authorization` proof。该 proof 只授权 OPL-owned storage maintenance shell 调用 MAS adapter 完成 scoped physical maintenance；它不授权 MAS 生成 command/event/outbox/StageRun，不证明 runtime currentness、paper progress、publication readiness、artifact mutation authority 或 provider admission。dry-run、source-retained restore-proof canary、refs-only state-index-only 和 planned retention/capsule projection 保持无授权、无物理 mutation、无 progress claim。

如果一次 reviewer / writer sprint 或 gate replay 产出 artifact movement / cleanup / rebuild 相关 refs，retention plan 只能把它们记录为 artifact lineage / reproducibility refs。缺 research evidence pack refs、negative / failed-path ledger refs、decision trace refs 或 artifact lineage / reproducibility refs 时，正确结果是 stable typed blocker，而不是基于 cleanup plan 推断 paper progress、publication readiness 或 artifact authority。

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

lifecycle refs SQLite store 只作为 refs index/read model/receipt 查询层。它可以索引 retention plan、archive ref、checksum、restore proof 和 owner route receipt；论文真相、用户干预记忆、artifact mutation authorization 和可交付文件仍保留在 MAS authority surface 与文件形态中。

这套设计吸收四类成熟工程原则：[controller reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)、[幂等请求 token](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)、[SQLite application file format](https://www.sqlite.org/appfileformat.html)、[BagIt 风格 manifest/checksum preservation](https://www.rfc-editor.org/rfc/rfc8493)。它们是工程依据，不是新的 runtime 依赖。
