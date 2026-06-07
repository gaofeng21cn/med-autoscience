# Legacy control surface clean migration public helper retirement 2026-06-07

Owner: `MedAutoScience`
Purpose: `runtime_public_helper_retirement_closeout`
State: `history_provenance`
Machine boundary: 本文是人读 closeout。当前机器真相继续归 `src/med_autoscience/cli.py`、`src/med_autoscience/cli_parts/parser.py`、`src/med_autoscience/cli_public_surface.py`、workspace init renderer、controller 源码和 repo-native verification。

## Scope

本轮退役 MAS public/workspace helper exposure，并在后续 cleanup tranche 物理退役内部历史迁移实现：

- public grouped CLI：`medautosci runtime legacy-control-surface-clean-migration`
- flat CLI parser/handler：`legacy-control-surface-clean-migration`
- workspace-generated wrapper：`ops/medautoscience/bin/legacy-control-surface-clean-migration`
- internal controller implementation：`src/med_autoscience/controllers/legacy_control_surface_clean_migration.py`
- direct controller regression file：`tests/test_legacy_control_surface_clean_migration.py`

旧内部 controller 不再作为 retained migration implementation、public runtime action surface、workspace helper、CLI alias 或 compatibility entry 存在。当前 active source 只保留 tombstoned payload 的 reader/filter 语义，例如 `legacy_control_surface_tombstone` 被 outbox、domain request lifecycle、runtime protocol 或 readiness projection 识别为 history/provenance，不恢复旧迁移 writer。

## Current Boundary

当前公共 runtime helper 入口只保留 active owner surface，例如 domain health diagnostic、owner route reconcile、domain action materialization/dispatch、runtime storage maintenance 和 storage audit。旧 legacy control surface clean migration 不再出现在 public CLI alias、flat parser、CLI handler、workspace bootstrap 生成脚本或 internal controller source 中。

如果后续确有迁移需求，应通过新的 current owner surface 重新定义，不恢复旧 internal controller、alias、wrapper、compatibility command 或 direct controller test。

## Verification Intent

当前测试边界：

- CLI 退役守卫确认 grouped 与 flat 命令 fail closed。
- Workspace init 测试确认新 workspace 不再生成 wrapper，且生成的 medautoscience bin scripts 不含旧 command。
- Tombstone/receipt 行为由当前 readers 和 boundary tests 覆盖；旧 direct controller migration tests 已随 implementation 退役。
