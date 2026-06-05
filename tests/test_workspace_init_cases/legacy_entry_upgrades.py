from __future__ import annotations

import importlib
from pathlib import Path


def _assert_progress_projection_forces_json(progress_projection_text: str) -> None:
    assert 'json_args=()' in progress_projection_text
    assert 'if [[ "${arg}" == "--format" ]]; then' in progress_projection_text
    assert 'if [[ "${arg}" == --format=* ]]; then' in progress_projection_text
    assert (
        'run_medautosci study-progress --profile "${PROFILE_PATH}" --format json --study-id "${study_id}" ${json_args[@]+"${json_args[@]}"}'
        in progress_projection_text
    )
    assert (
        'run_medautosci study-progress --profile "${PROFILE_PATH}" --format json ${json_args[@]+"${json_args[@]}"}'
        in progress_projection_text
    )


def test_init_workspace_removes_legacy_runtime_entry_scripts_without_force(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy",
        dry_run=False,
        force=False,
    )

    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    progress_projection = workspace_root / "ops" / "medautoscience" / "bin" / "progress-projection"
    study_state_matrix = workspace_root / "ops" / "medautoscience" / "bin" / "study-state-matrix"
    domain_health_diagnostic = workspace_root / "ops" / "medautoscience" / "bin" / "domain-health-diagnostic"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"

    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE:-${DEFAULT_PROFILE}}"\n'
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        "run_medautosci() {\n"
        '  PYTHONPATH="${MED_AUTOSCIENCE_REPO_RESOLVED}/src${PYTHONPATH:+:${PYTHONPATH}}" \\\n'
        '    python3 -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )
    watch_runtime.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci watch \\\n'
        '  --runtime-root "/private/var/folders/example/tmp.ws/ops/med-deepscientist/runtime/quests" \\\n'
        '  "$@"\n',
        encoding="utf-8",
    )
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'LAUNCHD_LABEL="ai.medautoscience.legacy.watch-runtime"\n'
        'SYSTEMD_SERVICE_NAME="medautoscience-watch-runtime-legacy"\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        'LOG_DIR="${WORKSPACE_ROOT}/ops/medautoscience/logs"\n'
        'STDOUT_LOG="${LOG_DIR}/watch-runtime.stdout.log"\n'
        'STDERR_LOG="${LOG_DIR}/watch-runtime.stderr.log"\n\n'
        'mkdir -p "${LOG_DIR}"\n\n'
        'case "$(uname -s)" in\n'
        "  Darwin)\n"
        '    launchctl bootstrap "gui/${UID}" "${HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"\n'
        "    ;;\n"
        "  Linux)\n"
        '    systemctl --user enable --now "${SYSTEMD_SERVICE_NAME}.service"\n'
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(watch_runtime) in result["removed_files"]
    assert str(install_service) in result["removed_files"]
    assert not watch_runtime.exists()
    assert not install_service.exists()
    assert progress_projection.is_file()
    assert study_state_matrix.is_file()
    assert domain_health_diagnostic.is_file()

    shared_text = shared.read_text(encoding="utf-8")
    progress_projection_text = progress_projection.read_text(encoding="utf-8")
    study_state_matrix_text = study_state_matrix.read_text(encoding="utf-8")
    domain_health_diagnostic_text = domain_health_diagnostic.read_text(encoding="utf-8")
    assert 'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python3"' in shared_text
    assert '"${WORKSPACE_PYTHON}" -m med_autoscience.cli "$@"' in shared_text
    assert "command -v uv" not in shared_text
    assert 'python3 -m med_autoscience.cli' not in shared_text
    _assert_progress_projection_forces_json(progress_projection_text)
    assert 'run_medautosci study-state-matrix --profile "${PROFILE_PATH}" "$@"' in study_state_matrix_text
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/runtime/quests"' in domain_health_diagnostic_text
    assert 'run_medautosci runtime domain-health-diagnostic \\' in domain_health_diagnostic_text
    assert 'apply_args=(--request-opl-stage-attempts --request-opl-owner-route-reconcile --apply)' in domain_health_diagnostic_text
    assert '[[ "${arg}" == "--apply" || "${arg}" == "--dry-run" || "${arg}" == "--request-opl-stage-attempts" || "${arg}" == "--request-opl-owner-route-reconcile" ]]' in domain_health_diagnostic_text
    assert '${apply_args[@]+"${apply_args[@]}"}' in domain_health_diagnostic_text
    assert '--loop' not in domain_health_diagnostic_text


def test_init_workspace_upgrades_generated_workspace_wrappers_when_templates_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "old-wrapper-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="old-wrapper",
        dry_run=False,
        force=False,
    )

    progress_projection = workspace_root / "ops" / "medautoscience" / "bin" / "progress-projection"
    resolve_targets = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-submission-targets"
    progress_projection.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'args=("$@")\n'
        'if [[ "${#args[@]}" -gt 0 && "${args[0]}" != -* ]]; then\n'
        '  study_id="${args[0]}"\n'
        '  args=("${args[@]:1}")\n'
        '  run_medautosci progress-projection --profile "${PROFILE_PATH}" --study-id "${study_id}" "${args[@]}"\n'
        "else\n"
        '  run_medautosci progress-projection --profile "${PROFILE_PATH}" "${args[@]}"\n'
        "fi\n",
        encoding="utf-8",
    )
    resolve_targets.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'args=("$@")\n'
        "has_profile=0\n"
        'for arg in "${args[@]}"; do\n'
        '  if [[ "${arg}" == "--profile" ]]; then\n'
        "    has_profile=1\n"
        "    break\n"
        "  fi\n"
        "done\n\n"
        'if [[ "${has_profile}" -eq 1 ]]; then\n'
        '  run_medautosci publication resolve-targets "${args[@]}"\n'
        "else\n"
        '  run_medautosci publication resolve-targets --profile "${PROFILE_PATH}" "${args[@]}"\n'
        "fi\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="old-wrapper",
        dry_run=False,
        force=False,
    )

    progress_projection_text = progress_projection.read_text(encoding="utf-8")
    resolve_targets_text = resolve_targets.read_text(encoding="utf-8")
    assert str(progress_projection) in result["upgraded_files"]
    assert str(resolve_targets) in result["upgraded_files"]
    _assert_progress_projection_forces_json(progress_projection_text)
    assert 'for arg in ${args[@]+"${args[@]}"}; do' in resolve_targets_text


def test_init_workspace_removes_flat_watch_runtime_entry_even_when_current_flags_are_present(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-watch-runtime"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-watch",
        dry_run=False,
        force=False,
    )

    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    domain_health_diagnostic = workspace_root / "ops" / "medautoscience" / "bin" / "domain-health-diagnostic"
    watch_runtime.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"\n\n'
        'run_medautosci watch \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  --runtime-root "${WORKSPACE_RUNTIME_ROOT}" \\\n'
        ''
        '  --apply \\\n'
        '  --loop \\\n'
        '  "$@"\n',
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-watch",
        dry_run=False,
        force=False,
    )

    assert str(watch_runtime) in result["removed_files"]
    assert not watch_runtime.exists()
    assert domain_health_diagnostic.is_file()
    domain_health_diagnostic_text = domain_health_diagnostic.read_text(encoding="utf-8")
    assert 'run_medautosci runtime domain-health-diagnostic \\' in domain_health_diagnostic_text
    assert 'apply_args=(--request-opl-stage-attempts --request-opl-owner-route-reconcile --apply)' in domain_health_diagnostic_text
    assert '--loop' not in domain_health_diagnostic_text


def test_init_workspace_upgrades_generated_guidance_and_removes_private_control_wrappers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-private-control"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-private",
        dry_run=False,
        force=False,
    )

    agents_path = workspace_root / "AGENTS.md"
    readme_path = workspace_root / "README.md"
    rules_path = workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"
    ops_readme_path = workspace_root / "ops" / "medautoscience" / "README.md"
    mas_readme_path = workspace_root / "ops" / "mas" / "README.md"
    bin_root = workspace_root / "ops" / "medautoscience" / "bin"
    supervisor_root = workspace_root / "ops" / "medautoscience" / "supervisor"
    legacy_wrappers = [
        bin_root / "ensure-study-runtime",
        bin_root / "domain-route-scan",
        bin_root / "domain-route-reconcile",
        bin_root / "supervisor-scan",
        bin_root / "supervisor-reconcile",
        bin_root / "supervisor-consume",
        bin_root / "supervisor-execute-dispatch",
        supervisor_root / "cron" / "supervisor-scan.cron",
        supervisor_root / "launchd" / "README.md",
        supervisor_root / "systemd" / "medautoscience-supervisor-scan.service",
        supervisor_root / "systemd" / "medautoscience-supervisor-scan.timer",
    ]

    agents_path.write_text(
        "# legacy-private Workspace Rules\n\n"
        "这个文件由 `medautosci init-workspace` 自动生成，用于声明当前 workspace 的本地约束、MAS 入口语义与基座回灌要求。\n\n"
        "默认通过 `ops/medautoscience/bin/show-profile`、`ops/medautoscience/bin/bootstrap`、"
        "`ops/medautoscience/bin/enter-study` 与 `ops/medautoscience/bin/watch-runtime` 调用 MAS 工作流。\n\n"
        "动手前必须查询对应 study 的 `study-runtime-status`。\n",
        encoding="utf-8",
    )
    readme_path.write_text(
        "# legacy-private Research Workspace\n\n"
        "这个 workspace 由 `medautosci init-workspace` 初始化。\n\n"
        "通过 `ops/medautoscience/bin/enter-study` 或 `ensure-study-runtime` 进入正式研究流程。\n\n"
        "运行 `ops/medautoscience/bin/install-watch-runtime-service` 管理 Hermes-hosted supervision job。\n",
        encoding="utf-8",
    )
    rules_path.write_text(
        "# Workspace Autoscience Rules\n\n"
        "这个文件由 `medautosci init-workspace` 自动生成，用于声明新 workspace 默认继承的运行约束。\n\n"
        "- 边界明确且 startup-ready 后，默认切入 `Hermes-backed` managed runtime 的自动持续推进。\n"
        "- live managed runtime 需要持续在线的 Hermes-hosted supervision tick；默认由 Hermes gateway cron 托管 "
        "`ops/medautoscience/bin/watch-runtime` 的单次 tick。\n",
        encoding="utf-8",
    )
    ops_readme_path.write_text(
        "# MedAutoScience Workspace Entry\n\n"
        "这个目录是当前 workspace 面向用户和 Agent 的本地入口层。\n\n"
        "推荐的长时监管入口：\n\n"
        "- `bin/watch-runtime`\n"
        "- `bin/supervisor-reconcile`\n"
        "- `bin/supervisor-consume`\n"
        "- `bin/supervisor-execute-dispatch`\n\n"
        "MAS scheduler supervision job 由 canonical CLI 管理："
        "`medautosci runtime ensure-supervision --profile <profile>`、"
        "`medautosci runtime supervision-status --profile <profile>` 与 "
        "`medautosci runtime remove-supervision --profile <profile>`。\n",
        encoding="utf-8",
    )
    mas_readme_path.write_text(
        "# MAS Runtime Bridge\n\n"
        "这个目录保留当前 workspace 的 MAS-native 运维薄入口脚本。\n\n"
        "它是 MAS-first runtime 运维面，不是研究入口。\n\n"
        "请遵守下面的边界：\n\n"
        "- 研究 quest 的创建、恢复、门禁判断统一走 `MedAutoScience`。\n"
        "- 需要进入 study 时，使用 `ops/medautoscience/bin/enter-study`、"
        "`ops/medautoscience/bin/bootstrap`、`ensure-study-runtime` 等受管入口。\n"
        "- 如果需要查看或维护 runtime，本目录下脚本只调用 MAS CLI / read-model / controlled pause surface，"
        "不调用外部 MDS launcher、daemon 或 WebUI。\n",
        encoding="utf-8",
    )
    for path in legacy_wrappers:
        path.parent.mkdir(parents=True, exist_ok=True)
    (bin_root / "ensure-study-runtime").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci ensure-study-runtime --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    (bin_root / "domain-route-scan").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci runtime domain-route-scan --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    (bin_root / "domain-route-reconcile").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci runtime domain-route-reconcile --profile "${PROFILE_PATH}" --mode developer_apply_safe --apply "$@"\n',
        encoding="utf-8",
    )
    (bin_root / "supervisor-scan").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci runtime supervisor-scan --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    (bin_root / "supervisor-reconcile").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci runtime supervisor-reconcile --profile "${PROFILE_PATH}" --mode developer_apply_safe --apply "$@"\n',
        encoding="utf-8",
    )
    (bin_root / "supervisor-consume").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci runtime supervisor-consume --profile "${PROFILE_PATH}" --mode developer_apply_safe --apply "$@"\n',
        encoding="utf-8",
    )
    (bin_root / "supervisor-execute-dispatch").write_text(
        "#!/usr/bin/env bash\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        'run_medautosci runtime supervisor-execute-dispatch --profile "${PROFILE_PATH}" --mode developer_apply_safe --apply "$@"\n',
        encoding="utf-8",
    )
    (supervisor_root / "cron" / "supervisor-scan.cron").write_text(
        "* * * * * ops/medautoscience/bin/supervisor-scan\n",
        encoding="utf-8",
    )
    (supervisor_root / "launchd" / "README.md").write_text(
        "ops/medautoscience/bin/install-watch-runtime-service --manager launchd\n",
        encoding="utf-8",
    )
    (supervisor_root / "systemd" / "medautoscience-supervisor-scan.service").write_text(
        "ExecStart=ops/medautoscience/bin/supervisor-scan\n",
        encoding="utf-8",
    )
    (supervisor_root / "systemd" / "medautoscience-supervisor-scan.timer").write_text(
        "Description=Run MedAutoScience portable supervisor scan hourly\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-private",
        dry_run=False,
        force=False,
    )

    for path in legacy_wrappers:
        assert str(path) in result["removed_files"]
        assert not path.exists()
    for path in (agents_path, readme_path, rules_path, ops_readme_path, mas_readme_path):
        assert str(path) in result["upgraded_files"]
    agents_text = agents_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")
    rules_text = rules_path.read_text(encoding="utf-8")
    ops_readme_text = ops_readme_path.read_text(encoding="utf-8")
    mas_readme_text = mas_readme_path.read_text(encoding="utf-8")
    for text in (agents_text, readme_text, rules_text, ops_readme_text, mas_readme_text):
        assert "watch-runtime" not in text
        assert "study-runtime-status" not in text
        assert "ensure-study-runtime" not in text
        assert "install-watch-runtime-service" not in text
        assert "supervisor-reconcile" not in text
        assert "supervisor-consume" not in text
        assert "supervisor-execute-dispatch" not in text
    assert "ops/medautoscience/bin/study-progress" in agents_text
    assert "ops/medautoscience/bin/progress-projection" in agents_text
    assert "ops/medautoscience/bin/domain-health-diagnostic" in agents_text
    assert "OPL current-control-state refs" in agents_text
    assert "OPL stage 控制面" in readme_text
    assert "MAS 不提供私有 scheduler、runner、attempt 或 runtime console 入口" in readme_text
    assert "默认 cadence / wakeup / provider SLO 由 OPL provider/runtime manager 承载" in rules_text
    assert "OPL current_control_state refs-only handoff" in ops_readme_text
    assert "MAS domain refs 运维薄入口脚本" in mas_readme_text
    assert "OPL current-control-state" in mas_readme_text
    assert "只调用 MAS domain refs / diagnostic surface" in mas_readme_text
    assert "MAS-first runtime 运维面" not in mas_readme_text
