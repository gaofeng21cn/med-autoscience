# Legacy control surface clean migration public helper retirement 2026-06-07

Owner: `MedAutoScience`
Purpose: `runtime_public_helper_retirement_closeout`
State: `history_provenance`
Machine boundary: 本文是人读 closeout。当前机器真相继续归 `src/med_autoscience/cli.py`、`src/med_autoscience/cli_parts/parser.py`、`src/med_autoscience/cli_public_surface.py`、workspace init renderer、controller 源码和 repo-native verification。

## Scope

本轮退役 MAS public/workspace helper exposure：

- public grouped CLI：`medautosci runtime legacy-control-surface-clean-migration`
- flat CLI parser/handler：`legacy-control-surface-clean-migration`
- workspace-generated wrapper：`ops/medautoscience/bin/legacy-control-surface-clean-migration`

`src/med_autoscience/controllers/legacy_control_surface_clean_migration.py` 保留为内部 tombstone / receipt migration implementation。它继续由 controller 级测试覆盖；本轮不把内部历史迁移实现升格为 public runtime action surface。

## Current Boundary

当前公共 runtime helper 入口只保留 active owner surface，例如 domain health diagnostic、owner route reconcile、domain action materialization/dispatch、runtime storage maintenance 和 storage audit。旧 legacy control surface clean migration 不再出现在 public CLI alias、flat parser、CLI handler 或 workspace bootstrap 生成脚本中。

如果后续确有迁移需求，应通过维护者显式调用内部 controller 或新的 current owner surface 重新定义，不恢复旧 alias、wrapper 或 compatibility command。

## Verification Intent

本轮测试边界：

- CLI 退役守卫确认 grouped 与 flat 命令 fail closed。
- Workspace init 测试确认新 workspace 不再生成 wrapper，且生成的 medautoscience bin scripts 不含旧 command。
- Controller 级 migration 测试继续覆盖内部 tombstone/receipt 行为。
