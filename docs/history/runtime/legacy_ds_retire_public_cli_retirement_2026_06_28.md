# Legacy `.ds` public CLI retirement 2026-06-28

Status: `retired_history`
Owner: `MedAutoScience runtime storage governance`
Purpose: `legacy_ds_public_cli_tombstone`
State: `history_only`
Machine boundary: 本文只保存历史 provenance。当前机器真相归 `src/med_autoscience/cli_public_surface.py`、CLI parser、runtime storage maintenance commands、OPL storage maintenance authority、canonical runtime state 和已有 restore/cold refs receipts。

`medautosci runtime legacy-ds-retire` 曾作为一次性迁移入口，用于把旧 `.ds` 目录归档为 source manifest、`legacy_ds.tar.gz`、restore proof、retirement receipt 和 cold ref，然后删除 legacy directory。该入口在 Yang workspace 完成物理迁移和 cold-store retention 后不再是当前 public CLI / parser / controller surface。

自 2026-06-28 起，MAS 不再暴露 `.ds` public retirement command，也不保留 alias 或 compatibility command。历史 `legacy_ds_retirement/**` receipts、manifest、restore proof、cold refs 和 archive refs 只作为 provenance / restore evidence 读取；当前目标态是 canonical `artifacts/runtime/state/runtime_state.json`、OPL storage maintenance、`runtime maintain-storage` / `storage-audit`、historical body/directory/detail retention、runtime lifecycle payload retention 和 semantic cold-store retention。

后续若发现新的 `.ds` 残留，先按 drift 处理：fresh inventory、确认 owner/live window、把有效 runtime state 或 refs 迁入 canonical surfaces，再通过当前 storage maintenance 或 owner route 形成可审计处理计划。不得重新新增 public `.ds` retirement parser、controller、alias、compat test 或长期 `.ds` read layer。
