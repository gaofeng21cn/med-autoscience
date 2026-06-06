# Progress projection command retirement closeout 2026-06-06

Owner: `MedAutoScience`
Purpose: `progress_projection_command_retirement_closeout`
State: `closed`
Machine boundary: 人读 closeout。机器事实以 CLI parser、workspace init renderer、retired workspace cleanup、tests 和 runtime/controller source 为准。

## 结论

`progress-projection` public CLI command、grouped `study progress-projection` alias 与 workspace-local `ops/medautoscience/bin/progress-projection` wrapper 已退役。

当前单 study Progress-first 入口统一为：

- `medautosci study progress --profile <profile> --study-id <study_id> --format json`
- `ops/medautoscience/bin/study-progress <study_id> --format json`

`progress_projection` 下划线命名继续表示 MAS 内部 runtime read-model / controller truth surface，不等同于已退役的连字符 public command。

## Scope

本次退役覆盖：

- flat CLI parser command `progress-projection`
- grouped public alias `study progress-projection`
- generated workspace wrapper `ops/medautoscience/bin/progress-projection`
- generated workspace guidance、workspace README、agent runtime contract 与 product/user-visible command strings
- tests 中对旧 command / wrapper 的正向兼容断言

## Verification

Focused verification:

- `scripts/run-pytest-clean.sh tests/test_cli_cases/study_progress_monitoring_commands.py tests/test_cli_cases/runtime_and_quality_commands.py tests/test_workspace_init_cases/workspace_creation.py tests/test_workspace_init_cases/legacy_entry_upgrades.py tests/test_cli_cases/public_entry_commands.py -q`
- `git diff --check`
- `rg -n "progress-projection" README.md docs/README.md docs/status.md docs/active docs/runtime docs/product src tests/test_cli_cases tests/test_workspace_init_cases`

剩余 `progress-projection` 命中只允许存在于退役 path/marker、negative guard、legacy fixture 或非 public internal provenance id；当前用户/Agent 可复制入口必须使用 `study-progress --format json`。
