from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def test_init_workspace_dry_run_reports_plan_without_writing_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "diabetes-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="diabetes",
        dry_run=True,
        force=False,
    )

    assert result["dry_run"] is True
    assert result["workspace_root"] == str(workspace_root)
    assert result["workspace_name"] == "diabetes"
    assert result["created_directories"]
    assert result["created_files"]
    assert str(workspace_root / "AGENTS.md") in result["created_files"]
    assert not workspace_root.exists()


def test_init_workspace_creates_minimal_workspace_and_entry_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "glioma-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="glioma",
        dry_run=False,
        force=False,
    )

    assert result["dry_run"] is False
    assert workspace_root.exists()
    assert (workspace_root / "datasets").is_dir()
    assert (workspace_root / "contracts").is_dir()
    assert (workspace_root / "studies").is_dir()
    assert (workspace_root / "portfolio" / "data_assets").is_dir()
    assert (workspace_root / "portfolio" / "research_memory").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "literature").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "literature" / "coverage").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "prompts").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "external_reports").is_dir()
    assert (workspace_root / "ops" / "medautoscience" / "bin").is_dir()
    assert (workspace_root / "ops" / "med-deepscientist" / "bin").is_dir()
    assert (workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests").is_dir()

    behavior_gate = workspace_root / "ops" / "med-deepscientist" / "behavior_equivalence_gate.yaml"
    assert behavior_gate.is_file()
    behavior_gate_text = behavior_gate.read_text(encoding="utf-8")
    assert "schema_version: v1" in behavior_gate_text
    assert "phase_25_ready: true" in behavior_gate_text
    assert "critical_overrides: []" in behavior_gate_text

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "glioma.local.toml"
    assert profile_path.is_file()
    profile_text = profile_path.read_text(encoding="utf-8")
    assert 'name = "glioma"' in profile_text
    assert f'workspace_root = "{workspace_root}"' in profile_text
    assert 'default_startup_anchor_policy = "scout_first_for_continue_existing_state"' in profile_text
    assert 'legacy_code_execution_policy = "forbid_without_user_approval"' in profile_text
    assert 'public_data_discovery_policy = "required_for_scout_route_selection"' in profile_text
    assert 'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]' in profile_text
    assert '"analysis-campaign", "figure-polish", "write"' in profile_text
    assert "enable_autofigure_edit" not in profile_text
    assert "autofigure_edit_bootstrap_mode" not in profile_text
    assert "autofigure_edit_service_url" not in profile_text

    med_config = workspace_root / "ops" / "medautoscience" / "config.env"
    deep_config = workspace_root / "ops" / "med-deepscientist" / "config.env"
    med_shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    ds_shared = workspace_root / "ops" / "med-deepscientist" / "bin" / "_shared.sh"
    assert med_config.is_file()
    assert deep_config.is_file()
    assert med_shared.is_file()
    assert ds_shared.is_file()
    med_shared_text = med_shared.read_text(encoding="utf-8")
    ds_shared_text = ds_shared.read_text(encoding="utf-8")
    assert 'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"' in med_shared_text
    assert 'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"' in med_shared_text
    assert 'MED_AUTOSCIENCE_NODE_BIN="${MED_AUTOSCIENCE_NODE_BIN:-$(command -v node || true)}"' in med_shared_text
    assert '"${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in med_shared_text
    assert 'uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - "${PROFILE_PATH}"' in ds_shared_text
    assert 'CONTRACT_JSON="${payload_json}" uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - <<' in ds_shared_text

    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    bootstrap = workspace_root / "ops" / "medautoscience" / "bin" / "bootstrap"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    maintain_runtime_storage = workspace_root / "ops" / "medautoscience" / "bin" / "maintain-runtime-storage"
    resolve_journal_shortlist = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist"
    init_portfolio_memory = workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory"
    portfolio_memory_status = workspace_root / "ops" / "medautoscience" / "bin" / "portfolio-memory-status"
    init_workspace_literature = workspace_root / "ops" / "medautoscience" / "bin" / "init-workspace-literature"
    workspace_literature_status = workspace_root / "ops" / "medautoscience" / "bin" / "workspace-literature-status"
    prepare_external_research = workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research"
    external_research_status = workspace_root / "ops" / "medautoscience" / "bin" / "external-research-status"
    ds_doctor = workspace_root / "ops" / "med-deepscientist" / "bin" / "doctor"
    assert bootstrap.is_file()
    assert show_profile.is_file()
    assert enter_study.is_file()
    assert watch_runtime.is_file()
    assert maintain_runtime_storage.is_file()
    assert resolve_journal_shortlist.is_file()
    assert init_portfolio_memory.is_file()
    assert portfolio_memory_status.is_file()
    assert init_workspace_literature.is_file()
    assert workspace_literature_status.is_file()
    assert prepare_external_research.is_file()
    assert external_research_status.is_file()
    assert ds_doctor.is_file()
    assert os.access(bootstrap, os.X_OK)
    assert os.access(show_profile, os.X_OK)
    assert os.access(enter_study, os.X_OK)
    assert os.access(watch_runtime, os.X_OK)
    assert os.access(maintain_runtime_storage, os.X_OK)
    assert os.access(resolve_journal_shortlist, os.X_OK)
    assert os.access(init_portfolio_memory, os.X_OK)
    assert os.access(portfolio_memory_status, os.X_OK)
    assert os.access(init_workspace_literature, os.X_OK)
    assert os.access(workspace_literature_status, os.X_OK)
    assert os.access(prepare_external_research, os.X_OK)
    assert os.access(external_research_status, os.X_OK)
    assert os.access(ds_doctor, os.X_OK)
    watch_runtime_text = watch_runtime.read_text(encoding="utf-8")
    maintain_runtime_storage_text = maintain_runtime_storage.read_text(encoding="utf-8")
    bootstrap_text = bootstrap.read_text(encoding="utf-8")
    show_profile_text = show_profile.read_text(encoding="utf-8")
    enter_study_text = enter_study.read_text(encoding="utf-8")
    resolve_journal_shortlist_text = resolve_journal_shortlist.read_text(encoding="utf-8")
    init_portfolio_memory_text = init_portfolio_memory.read_text(encoding="utf-8")
    portfolio_memory_status_text = portfolio_memory_status.read_text(encoding="utf-8")
    init_workspace_literature_text = init_workspace_literature.read_text(encoding="utf-8")
    workspace_literature_status_text = workspace_literature_status.read_text(encoding="utf-8")
    prepare_external_research_text = prepare_external_research.read_text(encoding="utf-8")
    external_research_status_text = external_research_status.read_text(encoding="utf-8")
    assert 'run_medautosci workspace bootstrap --profile "${PROFILE_PATH}" "$@"' in bootstrap_text
    assert 'run_medautosci doctor profile --profile "${PROFILE_PATH}" "$@"' in show_profile_text
    assert 'run_medautosci study ensure-runtime --profile "${PROFILE_PATH}" "$@"' in enter_study_text
    assert '--profile "${PROFILE_PATH}"' in watch_runtime_text
    assert 'run_medautosci runtime maintain-storage --profile "${PROFILE_PATH}" "$@"' in maintain_runtime_storage_text
    assert "--ensure-study-runtimes" in watch_runtime_text
    assert "--apply" in watch_runtime_text
    assert "--loop" in watch_runtime_text
    assert 'run_medautosci publication resolve-journal-shortlist "$@"' in resolve_journal_shortlist_text
    assert 'run_medautosci data init-memory "$@"' in init_portfolio_memory_text
    assert 'run_medautosci data memory-status "$@"' in portfolio_memory_status_text
    assert 'run_medautosci data init-literature "$@"' in init_workspace_literature_text
    assert 'run_medautosci data literature-status "$@"' in workspace_literature_status_text
    assert 'run_medautosci data prepare-external-research "$@"' in prepare_external_research_text
    assert 'run_medautosci data external-research-status "$@"' in external_research_status_text

    portfolio_memory_readme = workspace_root / "portfolio" / "research_memory" / "README.md"
    portfolio_memory_registry = workspace_root / "portfolio" / "research_memory" / "registry.yaml"
    workspace_literature_registry = workspace_root / "portfolio" / "research_memory" / "literature" / "registry.jsonl"
    assert portfolio_memory_readme.is_file()
    assert portfolio_memory_registry.is_file()
    assert workspace_literature_registry.is_file()
    assert "Portfolio Research Memory" in portfolio_memory_readme.read_text(encoding="utf-8")

    root_readme = workspace_root / "README.md"
    assert root_readme.is_file()
    root_readme_text = root_readme.read_text(encoding="utf-8")
    assert "workspace" in root_readme_text.lower()
    assert "ops/medautoscience/bin/show-profile" in root_readme_text
    assert "不要直接通过 `med-deepscientist` UI、CLI 或 daemon HTTP API 发起研究 quest" in root_readme_text
    assert "portfolio/research_memory/" in root_readme_text

    root_agents = workspace_root / "AGENTS.md"
    assert root_agents.is_file()
    root_agents_text = root_agents.read_text(encoding="utf-8")
    assert "# glioma Workspace Rules" in root_agents_text
    assert "适用范围：当前 workspace 根目录及所有子目录。" in root_agents_text
    assert "[`WORKSPACE_AUTOSCIENCE_RULES.md`](WORKSPACE_AUTOSCIENCE_RULES.md)" in root_agents_text
    assert "先给结论，再补必要上下文" in root_agents_text
    assert "复杂任务先拆清边界、依赖和验收口径" in root_agents_text
    assert "优先使用 subagent 提高效率" in root_agents_text
    assert "确认真实生效位置、调用链路和约束" in root_agents_text
    assert "优先使用 `rtk` 前缀运行 shell 命令。" not in root_agents_text
    assert "浏览网页优先使用 `agent-browser`。" in root_agents_text
    assert "优先使用官方 `mineru-document-extractor`" in root_agents_text
    assert "优先读取 `MINERU_TOKEN`" not in root_agents_text
    assert "## 本地执行约束" in root_agents_text
    assert "不改无关文件，不覆盖用户已有本地修改" in root_agents_text
    assert "优先做直接、可验证、可维护的根因解法" in root_agents_text
    assert "避免采用降级处理、兜底方案、临时补丁" in root_agents_text
    assert "能复用既有 controller、contract、schema 和 workspace pattern" in root_agents_text
    assert "病种/课题级 research workspace" in root_agents_text
    assert "`study` 是论文交付单元" in root_agents_text
    assert "## Workspace 边界" in root_agents_text
    assert "只约束 Codex 进入本目录后的工作方式、MAS 入口选择和本地文件边界" in root_agents_text
    assert "研究设计、统计方法、投稿判断、publication gate 与 study 质量判断归属 MAS / MDS" in root_agents_text
    assert "优先在 `med-autoscience` 与 `med-deepscientist` repo 中完成基座层修复" in root_agents_text
    assert "开独立 worktree 实施和验证" in root_agents_text
    assert "如果登录账号是 `gaofeng21cn`，可以直接提交并推送到对应 repo；否则只能向对应 GitHub repo 提交 PR" in root_agents_text

    deepscientist_readme = workspace_root / "ops" / "med-deepscientist" / "README.md"
    assert deepscientist_readme.is_file()
    deepscientist_readme_text = deepscientist_readme.read_text(encoding="utf-8")
    assert "runtime 运维面" in deepscientist_readme_text
    assert "不是研究入口" in deepscientist_readme_text
    assert "ops/medautoscience/bin/enter-study" in deepscientist_readme_text

    workspace_pyproject = workspace_root / "pyproject.toml"
    assert workspace_pyproject.is_file()
    workspace_pyproject_text = workspace_pyproject.read_text(encoding="utf-8")
    expected_repo_relpath = Path(os.path.relpath(Path(module.__file__).resolve().parents[3], workspace_root)).as_posix()
    assert 'name = "glioma-workspace"' in workspace_pyproject_text
    assert 'description = "Managed Python environment for the glioma workspace."' in workspace_pyproject_text
    assert '"med-autoscience"' in workspace_pyproject_text
    assert "[tool.uv.sources]" in workspace_pyproject_text
    assert f'med-autoscience = {{ path = "{expected_repo_relpath}", editable = true }}' in workspace_pyproject_text

    workspace_rules = workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"
    assert workspace_rules.is_file()
    workspace_rules_text = workspace_rules.read_text(encoding="utf-8")
    assert "优先复用 MedAutoScience 已覆盖的成熟 controller / CLI / overlay skill" in workspace_rules_text
    assert "边界明确且 startup-ready 后，默认切入 `Hermes-backed` managed runtime 的自动持续推进" in workspace_rules_text
    assert "必须显式通知用户自动驾驶已启动或已被检测到，并提供监督入口" in workspace_rules_text
    assert "前台必须立即进入 supervisor-only 监管态" in workspace_rules_text
    assert "不得直接写入 runtime-owned 的 study / quest / paper surface" in workspace_rules_text
    assert "portfolio-memory-status" in workspace_rules_text
    assert "prepare-external-research" in workspace_rules_text

    watch_runtime_text = watch_runtime.read_text(encoding="utf-8")
    assert 'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"' in watch_runtime_text
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"' in watch_runtime_text
    assert 'run_medautosci runtime watch \\' in watch_runtime_text
    assert str(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests") not in watch_runtime_text


def test_init_workspace_is_idempotent_and_force_overwrites_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "pituitary-workspace"

    first = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert first["created_files"]

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "pituitary.local.toml"
    profile_path.write_text("# local edit\n", encoding="utf-8")
    agents_path = workspace_root / "AGENTS.md"
    agents_path.write_text("# custom local rules\n", encoding="utf-8")

    second = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert str(profile_path) in second["skipped_files"]
    assert profile_path.read_text(encoding="utf-8") == "# local edit\n"
    assert str(agents_path) in second["skipped_files"]
    assert agents_path.read_text(encoding="utf-8") == "# custom local rules\n"

    third = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=True,
    )
    assert str(profile_path) in third["overwritten_files"]
    assert 'name = "pituitary"' in profile_path.read_text(encoding="utf-8")
    assert str(agents_path) in third["overwritten_files"]
    assert "# pituitary Workspace Rules" in agents_path.read_text(encoding="utf-8")


def test_init_workspace_creates_watch_runtime_service_scripts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "lung-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="lung",
        dry_run=False,
        force=False,
    )

    runner = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    service_status = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
    uninstall_service = workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service"

    for path in (runner, install_service, service_status, uninstall_service):
        assert path.is_file()
        assert os.access(path, os.X_OK)

    runner_text = runner.read_text(encoding="utf-8")
    assert 'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"' in runner_text
    assert 'WATCH_RUNTIME_SCRIPT="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime"' in runner_text
    assert 'exec "${WATCH_RUNTIME_SCRIPT}" --interval-seconds "${WATCH_RUNTIME_INTERVAL_SECONDS}" "$@"' in runner_text

    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text

    status_text = service_status.read_text(encoding="utf-8")
    assert 'run_medautosci runtime supervision-status --profile "${PROFILE_PATH}" "$@"' in status_text

    uninstall_text = uninstall_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime remove-supervision --profile "${PROFILE_PATH}" "$@"' in uninstall_text


def test_init_workspace_upgrades_legacy_runtime_entry_scripts_without_force(tmp_path: Path) -> None:
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
    assert str(watch_runtime) in result["upgraded_files"]
    assert str(install_service) in result["upgraded_files"]

    shared_text = shared.read_text(encoding="utf-8")
    watch_runtime_text = watch_runtime.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_UV_BIN" in shared_text
    assert "command -v uv" in shared_text
    assert 'python3 -m med_autoscience.cli' not in shared_text
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"' in watch_runtime_text
    assert 'run_medautosci runtime watch \\' in watch_runtime_text
    assert '--ensure-study-runtimes' in watch_runtime_text
    assert '--apply' in watch_runtime_text
    assert '--loop' in watch_runtime_text
    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text


def test_init_workspace_upgrades_flat_watch_runtime_entry_even_when_current_flags_are_present(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-watch-runtime"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-watch",
        dry_run=False,
        force=False,
    )

    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    watch_runtime.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"\n\n'
        'run_medautosci watch \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  --runtime-root "${WORKSPACE_RUNTIME_ROOT}" \\\n'
        '  --ensure-study-runtimes \\\n'
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

    assert str(watch_runtime) in result["upgraded_files"]
    assert 'run_medautosci runtime watch \\' in watch_runtime.read_text(encoding="utf-8")


def test_init_workspace_upgrades_legacy_public_forward_scripts_without_force(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-public-forwarders"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-public",
        dry_run=False,
        force=False,
    )

    bootstrap = workspace_root / "ops" / "medautoscience" / "bin" / "bootstrap"
    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    publication_gate = workspace_root / "ops" / "medautoscience" / "bin" / "publication-gate"
    resolve_submission_targets = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-submission-targets"
    init_portfolio_memory = workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory"
    prepare_external_research = workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research"
    sync_delivery = workspace_root / "ops" / "medautoscience" / "bin" / "sync-delivery"

    bootstrap.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci bootstrap --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    show_profile.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci show-profile --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    enter_study.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci ensure-study-runtime --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    publication_gate.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci publication-gate "$@"\n',
        encoding="utf-8",
    )
    resolve_submission_targets.write_text(
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
        '  run_medautosci resolve-submission-targets "${args[@]}"\n'
        "else\n"
        '  run_medautosci resolve-submission-targets --profile "${PROFILE_PATH}" "${args[@]}"\n'
        "fi\n",
        encoding="utf-8",
    )
    init_portfolio_memory.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci init-portfolio-memory "$@"\n',
        encoding="utf-8",
    )
    prepare_external_research.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci prepare-external-research "$@"\n',
        encoding="utf-8",
    )
    sync_delivery.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci sync-study-delivery "$@"\n',
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-public",
        dry_run=False,
        force=False,
    )

    for path in (
        bootstrap,
        show_profile,
        enter_study,
        publication_gate,
        resolve_submission_targets,
        init_portfolio_memory,
        prepare_external_research,
        sync_delivery,
    ):
        assert str(path) in result["upgraded_files"]

    assert 'run_medautosci workspace bootstrap --profile "${PROFILE_PATH}" "$@"' in bootstrap.read_text(encoding="utf-8")
    assert 'run_medautosci doctor profile --profile "${PROFILE_PATH}" "$@"' in show_profile.read_text(encoding="utf-8")
    assert 'run_medautosci study ensure-runtime --profile "${PROFILE_PATH}" "$@"' in enter_study.read_text(encoding="utf-8")
    assert 'run_medautosci publication gate "$@"' in publication_gate.read_text(encoding="utf-8")
    resolve_targets_text = resolve_submission_targets.read_text(encoding="utf-8")
    assert 'run_medautosci publication resolve-targets "${args[@]}"' in resolve_targets_text
    assert 'run_medautosci publication resolve-targets --profile "${PROFILE_PATH}" "${args[@]}"' in resolve_targets_text
    assert 'run_medautosci data init-memory "$@"' in init_portfolio_memory.read_text(encoding="utf-8")
    assert 'run_medautosci data prepare-external-research "$@"' in prepare_external_research.read_text(encoding="utf-8")
    assert 'run_medautosci study delivery-sync "$@"' in sync_delivery.read_text(encoding="utf-8")


def test_init_workspace_upgrades_shared_script_that_still_invokes_bare_uv(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-uv-workspace"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    shared.parent.mkdir(parents=True, exist_ok=True)
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
        '  uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-uv",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    shared_text = shared.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_UV_BIN" in shared_text
    assert '"${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in shared_text


def test_init_workspace_upgrades_current_managed_scripts_when_rscript_binding_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-rscript-workspace"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    shared.parent.mkdir(parents=True, exist_ok=True)
    install_service.parent.mkdir(parents=True, exist_ok=True)

    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy-rscript.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -n "${MED_AUTOSCIENCE_PROFILE:-}" ]]; then\n'
        '  PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE}"\n'
        "else\n"
        '  PROFILE_PATH="${DEFAULT_PROFILE}"\n'
        "fi\n\n"
        'if [[ -z "${MED_AUTOSCIENCE_REPO:-}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO is not configured. Set it in ${CONFIG_ENV_PATH} or export it explicitly." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        'if [[ ! -f "${PROFILE_PATH}" ]]; then\n'
        '  echo "Profile file not found: ${PROFILE_PATH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ${CONFIG_ENV_PATH} or install uv on PATH." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "run_medautosci() {\n"
        '  "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'LAUNCHD_LABEL="ai.medautoscience.legacy-rscript.watch-runtime"\n'
        'SYSTEMD_SERVICE_NAME="medautoscience-watch-runtime-legacy-rscript"\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        'LOG_DIR="${WORKSPACE_ROOT}/ops/medautoscience/logs"\n'
        'STDOUT_LOG="${LOG_DIR}/watch-runtime.stdout.log"\n'
        'STDERR_LOG="${LOG_DIR}/watch-runtime.stderr.log"\n\n'
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ops/medautoscience/config.env or install uv on PATH before installing the service." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'mkdir -p "${LOG_DIR}"\n\n'
        'case "$(uname -s)" in\n'
        "  Darwin)\n"
        '    LAUNCHD_LABEL="${LAUNCHD_LABEL}" \\\n'
        '    WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS}" \\\n'
        '    MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN}" \\\n'
        "    python3 - <<'PY'\n"
        "import os\n"
        "payload = {\n"
        '    "EnvironmentVariables": {\n'
        '        "WATCH_RUNTIME_INTERVAL_SECONDS": os.environ["WATCH_RUNTIME_INTERVAL_SECONDS"],\n'
        '        "MED_AUTOSCIENCE_UV_BIN": os.environ["MED_AUTOSCIENCE_UV_BIN"],\n'
        "    },\n"
        "}\n"
            "print(payload)\n"
            "PY\n"
            '    launchctl bootstrap "gui/${UID}" "${HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"\n'
            "    ;;\n"
            "  Linux)\n"
            '    cat > /tmp/watch-runtime.service <<EOF\n'
            'Environment=WATCH_RUNTIME_INTERVAL_SECONDS=${WATCH_RUNTIME_INTERVAL_SECONDS}\n'
            'Environment=MED_AUTOSCIENCE_UV_BIN=${MED_AUTOSCIENCE_UV_BIN}\n'
            "EOF\n"
            '    systemctl --user enable --now "${SYSTEMD_SERVICE_NAME}.service"\n'
            "    ;;\n"
            "esac\n",
            encoding="utf-8",
        )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-rscript",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(install_service) in result["upgraded_files"]
    assert "MED_AUTOSCIENCE_RSCRIPT_BIN" in shared.read_text(encoding="utf-8")
    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text


def test_init_workspace_upgrades_current_managed_scripts_when_node_binding_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-node-workspace"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    shared.parent.mkdir(parents=True, exist_ok=True)
    install_service.parent.mkdir(parents=True, exist_ok=True)

    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy-node.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -n "${MED_AUTOSCIENCE_PROFILE:-}" ]]; then\n'
        '  PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE}"\n'
        "else\n"
        '  PROFILE_PATH="${DEFAULT_PROFILE}"\n'
        "fi\n\n"
        'if [[ -z "${MED_AUTOSCIENCE_REPO:-}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO is not configured. Set it in ${CONFIG_ENV_PATH} or export it explicitly." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        'if [[ ! -f "${PROFILE_PATH}" ]]; then\n'
        '  echo "Profile file not found: ${PROFILE_PATH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ${CONFIG_ENV_PATH} or install uv on PATH." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_RSCRIPT_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN must be an absolute path: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN is not executable: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'export MED_AUTOSCIENCE_RSCRIPT_BIN\n\n'
        "run_medautosci() {\n"
        '  "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'LAUNCHD_LABEL="ai.medautoscience.legacy-node.watch-runtime"\n'
        'SYSTEMD_SERVICE_NAME="medautoscience-watch-runtime-legacy-node"\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        'LOG_DIR="${WORKSPACE_ROOT}/ops/medautoscience/logs"\n'
        'STDOUT_LOG="${LOG_DIR}/watch-runtime.stdout.log"\n'
        'STDERR_LOG="${LOG_DIR}/watch-runtime.stderr.log"\n\n'
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ops/medautoscience/config.env or install uv on PATH before installing the service." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_RSCRIPT_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN must be an absolute path: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN is not executable: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'mkdir -p "${LOG_DIR}"\n\n'
        'case "$(uname -s)" in\n'
        "  Darwin)\n"
        '    LAUNCHD_LABEL="${LAUNCHD_LABEL}" \\\n'
        '    WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS}" \\\n'
        '    MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN}" \\\n'
        '    MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN}" \\\n'
        "    python3 - <<'PY'\n"
        "import os\n"
        "payload = {\n"
        '    "EnvironmentVariables": {\n'
        '        "WATCH_RUNTIME_INTERVAL_SECONDS": os.environ["WATCH_RUNTIME_INTERVAL_SECONDS"],\n'
        '        "MED_AUTOSCIENCE_UV_BIN": os.environ["MED_AUTOSCIENCE_UV_BIN"],\n'
        "    },\n"
        "}\n"
        "if os.environ.get(\"MED_AUTOSCIENCE_RSCRIPT_BIN\"):\n"
        '    payload["EnvironmentVariables"]["MED_AUTOSCIENCE_RSCRIPT_BIN"] = os.environ["MED_AUTOSCIENCE_RSCRIPT_BIN"]\n'
        "print(payload)\n"
        "PY\n"
        '    launchctl bootstrap "gui/${UID}" "${HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"\n'
        "    ;;\n"
        "  Linux)\n"
        '    cat > /tmp/watch-runtime.service <<EOF\n'
        'Environment=WATCH_RUNTIME_INTERVAL_SECONDS=${WATCH_RUNTIME_INTERVAL_SECONDS}\n'
        'Environment=MED_AUTOSCIENCE_UV_BIN=${MED_AUTOSCIENCE_UV_BIN}\n'
        'Environment=MED_AUTOSCIENCE_RSCRIPT_BIN=${MED_AUTOSCIENCE_RSCRIPT_BIN}\n'
        "EOF\n"
        '    systemctl --user enable --now "${SYSTEMD_SERVICE_NAME}.service"\n'
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-node",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(install_service) in result["upgraded_files"]
    assert "MED_AUTOSCIENCE_NODE_BIN" in shared.read_text(encoding="utf-8")
    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text


def test_init_workspace_upgrades_medautoscience_config_with_detected_node_binding(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "config-upgrade-workspace"
    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    detected_node = tmp_path / "bin" / "node"
    detected_node.parent.mkdir(parents=True, exist_ok=True)
    detected_node.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    detected_node.chmod(0o755)
    config_env.parent.mkdir(parents=True, exist_ok=True)
    config_env.write_text(
        "\n".join(
            [
                'MED_AUTOSCIENCE_REPO="/Users/gaofeng/workspace/med-autoscience"',
                f'MED_AUTOSCIENCE_PROFILE="{workspace_root / "ops" / "medautoscience" / "profiles" / "config-upgrade.local.toml"}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module.shutil, "which", lambda executable: str(detected_node) if executable == "node" else None)

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="config-upgrade",
        dry_run=False,
        force=False,
    )

    assert str(config_env) in result["upgraded_files"]
    config_text = config_env.read_text(encoding="utf-8")
    assert f'MED_AUTOSCIENCE_NODE_BIN="{detected_node}"' in config_text
    assert 'MED_AUTOSCIENCE_REPO="/Users/gaofeng/workspace/med-autoscience"' in config_text


def test_init_workspace_upgrades_configured_active_profile_with_explicit_hermes_binding(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "nfpitnet-workspace"
    profiles_root = workspace_root / "ops" / "medautoscience" / "profiles"
    profiles_root.mkdir(parents=True, exist_ok=True)
    active_profile = profiles_root / "nfpitnet.workspace.toml"
    active_profile.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                'med_deepscientist_repo_root = "/Users/gaofeng/workspace/med-deepscientist"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["intake-audit", "scout", "baseline", "idea", "decision", "experiment", "analysis-campaign", "write", "review", "rebuttal", "finalize"]',
                'medical_overlay_bootstrap_mode = "ensure_ready"',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "llm_agent_clinical_task"]',
                'default_startup_anchor_policy = "scout_first_for_continue_existing_state"',
                'legacy_code_execution_policy = "forbid_without_user_approval"',
                'public_data_discovery_policy = "required_for_scout_route_selection"',
                'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    config_env.parent.mkdir(parents=True, exist_ok=True)
    config_env.write_text(
        "\n".join(
            [
                'MED_AUTOSCIENCE_REPO="/Users/gaofeng/workspace/med-autoscience"',
                f'MED_AUTOSCIENCE_PROFILE="{active_profile}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    hermes_repo_root = tmp_path / "_external" / "hermes-agent"
    hermes_home_root = tmp_path / ".hermes"
    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="nfpitnet",
        dry_run=False,
        force=False,
        hermes_agent_repo_root=hermes_repo_root,
        hermes_home_root=hermes_home_root,
    )

    assert result["profile_path"] == str(active_profile)
    assert str(active_profile) in result["upgraded_files"]
    assert not (profiles_root / "nfpitnet.local.toml").exists()

    active_profile_text = active_profile.read_text(encoding="utf-8")
    assert f'hermes_agent_repo_root = "{hermes_repo_root}"' in active_profile_text
    assert f'hermes_home_root = "{hermes_home_root}"' in active_profile_text
    assert 'preferred_study_archetypes = ["clinical_classifier", "llm_agent_clinical_task"]' in active_profile_text
