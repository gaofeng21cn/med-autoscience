from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess


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
    assert str(workspace_root / "runtime" / "quests") in result["created_directories"]
    assert str(workspace_root / "runtime" / "archives") in result["created_directories"]
    assert str(workspace_root / "runtime" / "restore_index") in result["created_directories"]
    assert str(workspace_root / "artifacts" / "runtime") in result["created_directories"]
    assert str(workspace_root / "artifacts" / "runtime" / "progress_portal") in result["created_directories"]
    assert str(workspace_root / "ops" / "mas" / "bin") in result["created_directories"]
    assert str(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests") not in result["created_directories"]
    assert str(workspace_root / "ops" / "med-deepscientist" / "config.env") not in result["created_files"]
    assert str(workspace_root / "AGENTS.md") in result["created_files"]
    assert str(workspace_root / "ops" / "mas" / "progress" / "index.html") not in result["created_files"]
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
    assert (workspace_root / "ops" / "mas" / "bin").is_dir()
    assert (workspace_root / "runtime" / "quests").is_dir()
    assert (workspace_root / "runtime" / "archives").is_dir()
    assert (workspace_root / "runtime" / "restore_index").is_dir()
    assert (workspace_root / "artifacts" / "runtime").is_dir()
    assert (workspace_root / "artifacts" / "runtime" / "progress_portal").is_dir()
    assert not (workspace_root / "ops" / "mas" / "progress").exists()
    assert not (workspace_root / "ops" / "med-deepscientist").exists()

    behavior_gate = workspace_root / "ops" / "mas" / "behavior_equivalence_gate.yaml"
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
    assert f'runtime_root = "{workspace_root / "runtime" / "quests"}"' in profile_text
    assert f'managed_runtime_home = "{workspace_root / "runtime"}"' in profile_text
    assert "med_deepscientist_runtime_root" not in profile_text
    assert "med_deepscientist_repo_root" not in profile_text
    assert 'default_startup_anchor_policy = "scout_first_for_continue_existing_state"' in profile_text
    assert 'legacy_code_execution_policy = "forbid_without_user_approval"' in profile_text
    assert 'public_data_discovery_policy = "required_for_scout_route_selection"' in profile_text
    assert 'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]' in profile_text
    assert '"analysis-campaign", "figure-polish", "write"' in profile_text
    assert "enable_autofigure_edit" not in profile_text
    assert "autofigure_edit_bootstrap_mode" not in profile_text
    assert "autofigure_edit_service_url" not in profile_text

    med_config = workspace_root / "ops" / "medautoscience" / "config.env"
    runtime_bridge_config = workspace_root / "ops" / "mas" / "config.env"
    med_shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    runtime_bridge_shared = workspace_root / "ops" / "mas" / "bin" / "_shared.sh"
    assert med_config.is_file()
    assert runtime_bridge_config.is_file()
    assert med_shared.is_file()
    assert runtime_bridge_shared.is_file()
    med_shared_text = med_shared.read_text(encoding="utf-8")
    runtime_bridge_shared_text = runtime_bridge_shared.read_text(encoding="utf-8")
    runtime_bridge_config_text = runtime_bridge_config.read_text(encoding="utf-8")
    assert 'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"' in med_shared_text
    assert 'MED_AUTOSCIENCE_NODE_BIN="${MED_AUTOSCIENCE_NODE_BIN:-$(command -v node || true)}"' in med_shared_text
    assert 'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python3"' in med_shared_text
    assert '"${WORKSPACE_PYTHON}" -m med_autoscience.cli "$@"' in med_shared_text
    assert 'run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli' not in med_shared_text
    assert (
        'PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" - "${PROFILE_PATH}"'
        in runtime_bridge_shared_text
    )
    assert (
        'CONTRACT_JSON="${payload_json}" PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" - <<'
        in runtime_bridge_shared_text
    )
    assert 'PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" - <<' in runtime_bridge_shared_text
    assert "MED_DEEPSCIENTIST_LAUNCHER" not in runtime_bridge_config_text
    assert "MED_DEEPSCIENTIST_LAUNCHER" not in runtime_bridge_shared_text
    assert "run_med_deepscientist_launcher" not in runtime_bridge_shared_text
    assert ' uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}"' not in runtime_bridge_shared_text

    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    bootstrap = workspace_root / "ops" / "medautoscience" / "bin" / "bootstrap"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    progress_projection = workspace_root / "ops" / "medautoscience" / "bin" / "progress-projection"
    study_progress = workspace_root / "ops" / "medautoscience" / "bin" / "study-progress"
    study_state_matrix = workspace_root / "ops" / "medautoscience" / "bin" / "study-state-matrix"
    domain_health_diagnostic = workspace_root / "ops" / "medautoscience" / "bin" / "domain-health-diagnostic"
    legacy_control_surface_clean_migration = (
        workspace_root / "ops" / "medautoscience" / "bin" / "legacy-control-surface-clean-migration"
    )
    study_runtime_status = workspace_root / "ops" / "medautoscience" / "bin" / "study-runtime-status"
    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    maintain_runtime_storage = workspace_root / "ops" / "medautoscience" / "bin" / "maintain-runtime-storage"
    storage_audit = workspace_root / "ops" / "medautoscience" / "bin" / "storage-audit"
    install_watch_runtime_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    watch_runtime_service_status = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
    uninstall_watch_runtime_service = workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service"
    resolve_journal_shortlist = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist"
    init_portfolio_memory = workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory"
    portfolio_memory_status = workspace_root / "ops" / "medautoscience" / "bin" / "portfolio-memory-status"
    init_workspace_literature = workspace_root / "ops" / "medautoscience" / "bin" / "init-workspace-literature"
    workspace_literature_status = workspace_root / "ops" / "medautoscience" / "bin" / "workspace-literature-status"
    prepare_external_research = workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research"
    external_research_status = workspace_root / "ops" / "medautoscience" / "bin" / "external-research-status"
    runtime_bridge_doctor = workspace_root / "ops" / "mas" / "bin" / "doctor"
    runtime_bridge_status = workspace_root / "ops" / "mas" / "bin" / "status"
    runtime_bridge_stop = workspace_root / "ops" / "mas" / "bin" / "stop"
    assert bootstrap.is_file()
    assert show_profile.is_file()
    assert enter_study.is_file()
    assert study_progress.is_file()
    assert progress_projection.is_file()
    assert study_state_matrix.is_file()
    assert domain_health_diagnostic.is_file()
    assert legacy_control_surface_clean_migration.is_file()
    assert not study_runtime_status.exists()
    assert not watch_runtime.exists()
    assert maintain_runtime_storage.is_file()
    assert storage_audit.is_file()
    assert not (workspace_root / "ops" / "medautoscience" / "bin" / "progress-portal").exists()
    assert not install_watch_runtime_service.exists()
    assert not watch_runtime_service_status.exists()
    assert not uninstall_watch_runtime_service.exists()
    assert resolve_journal_shortlist.is_file()
    assert init_portfolio_memory.is_file()
    assert portfolio_memory_status.is_file()
    assert init_workspace_literature.is_file()
    assert workspace_literature_status.is_file()
    assert prepare_external_research.is_file()
    assert external_research_status.is_file()
    assert runtime_bridge_doctor.is_file()
    assert runtime_bridge_status.is_file()
    assert runtime_bridge_stop.is_file()
    assert not (workspace_root / "ops" / "mas" / "bin" / "start-web").exists()
    assert not (workspace_root / "ops" / "mas" / "bin" / "live-console").exists()
    assert os.access(bootstrap, os.X_OK)
    assert os.access(show_profile, os.X_OK)
    assert os.access(enter_study, os.X_OK)
    assert os.access(progress_projection, os.X_OK)
    assert os.access(study_state_matrix, os.X_OK)
    assert os.access(domain_health_diagnostic, os.X_OK)
    assert os.access(legacy_control_surface_clean_migration, os.X_OK)
    assert os.access(maintain_runtime_storage, os.X_OK)
    assert os.access(storage_audit, os.X_OK)
    assert os.access(resolve_journal_shortlist, os.X_OK)
    assert os.access(init_portfolio_memory, os.X_OK)
    assert os.access(portfolio_memory_status, os.X_OK)
    assert os.access(init_workspace_literature, os.X_OK)
    assert os.access(workspace_literature_status, os.X_OK)
    assert os.access(prepare_external_research, os.X_OK)
    assert os.access(external_research_status, os.X_OK)
    assert os.access(runtime_bridge_doctor, os.X_OK)
    assert os.access(runtime_bridge_status, os.X_OK)
    assert os.access(runtime_bridge_stop, os.X_OK)
    progress_projection_text = progress_projection.read_text(encoding="utf-8")
    study_state_matrix_text = study_state_matrix.read_text(encoding="utf-8")
    domain_health_diagnostic_text = domain_health_diagnostic.read_text(encoding="utf-8")
    legacy_control_surface_clean_migration_text = legacy_control_surface_clean_migration.read_text(encoding="utf-8")
    maintain_runtime_storage_text = maintain_runtime_storage.read_text(encoding="utf-8")
    storage_audit_text = storage_audit.read_text(encoding="utf-8")
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
    runtime_bridge_doctor_text = runtime_bridge_doctor.read_text(encoding="utf-8")
    runtime_bridge_status_text = runtime_bridge_status.read_text(encoding="utf-8")
    runtime_bridge_stop_text = runtime_bridge_stop.read_text(encoding="utf-8")
    shared_text = (workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh").read_text(encoding="utf-8")
    assert "PYTHONDONTWRITEBYTECODE=1" in shared_text
    assert 'run_medautosci workspace bootstrap --profile "${PROFILE_PATH}" "$@"' in bootstrap_text
    assert 'workspace_python_has_medautosci_cli() {' in bootstrap_text
    assert '"${WORKSPACE_PYTHON}" -c "import med_autoscience.cli"' in bootstrap_text
    assert 'if ! workspace_python_has_medautosci_cli; then' in bootstrap_text
    assert 'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"' in bootstrap_text
    assert 'run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli workspace bootstrap' in bootstrap_text
    assert 'run_medautosci doctor profile --profile "${PROFILE_PATH}" "$@"' in show_profile_text
    assert 'run_medautosci launch-study --profile "${PROFILE_PATH}" "$@"' in enter_study_text
    assert 'run_medautosci study-progress --profile "${PROFILE_PATH}" --format json ${json_args[@]+"${json_args[@]}"}' in progress_projection_text
    study_progress_text = study_progress.read_text(encoding="utf-8")
    assert 'run_medautosci study-progress --profile "${PROFILE_PATH}" ${args[@]+"${args[@]}"}' in study_progress_text
    assert '--study-id "${study_id}"' in study_progress_text
    assert '--study-id "${study_id}"' in progress_projection_text
    assert 'run_medautosci study-state-matrix --profile "${PROFILE_PATH}" "$@"' in study_state_matrix_text
    assert '--profile "${PROFILE_PATH}"' in domain_health_diagnostic_text
    assert 'run_medautosci runtime maintain-storage --profile "${PROFILE_PATH}" "$@"' in maintain_runtime_storage_text
    assert 'apply_args=(--request-opl-stage-attempts --request-opl-owner-route-reconcile --apply)' in domain_health_diagnostic_text
    assert '[[ "${arg}" == "--apply" || "${arg}" == "--dry-run" || "${arg}" == "--request-opl-stage-attempts" || "${arg}" == "--request-opl-owner-route-reconcile" ]]' in domain_health_diagnostic_text
    assert '${apply_args[@]+"${apply_args[@]}"}' in domain_health_diagnostic_text
    assert "--loop" not in domain_health_diagnostic_text
    assert (
        'run_medautosci runtime legacy-control-surface-clean-migration \\'
        in legacy_control_surface_clean_migration_text
    )
    assert '--profile "${PROFILE_PATH}"' in legacy_control_surface_clean_migration_text
    assert 'run_medautosci runtime storage-audit --profile "${PROFILE_PATH}" "$@"' in storage_audit_text
    assert 'run_medautosci publication resolve-journal-shortlist "$@"' in resolve_journal_shortlist_text
    assert 'run_medautosci data init-memory "$@"' in init_portfolio_memory_text
    assert 'run_medautosci data memory-status "$@"' in portfolio_memory_status_text
    assert 'run_medautosci data init-literature "$@"' in init_workspace_literature_text
    assert 'run_medautosci data literature-status "$@"' in workspace_literature_status_text
    assert 'run_medautosci data prepare-external-research "$@"' in prepare_external_research_text
    assert 'run_medautosci data external-research-status "$@"' in external_research_status_text
    assert 'run_medautosci doctor report --profile "${PROFILE_PATH}" "$@"' in runtime_bridge_doctor_text
    assert 'run_medautosci workspace cockpit --profile "${PROFILE_PATH}" --format json "$@"' in runtime_bridge_status_text
    assert "MAS pause-runtime is retired; use OPL current_control_state / human gate tooling." in runtime_bridge_stop_text
    assert "run_medautosci study pause-runtime" not in runtime_bridge_stop_text
    assert "run_med_deepscientist_launcher" not in runtime_bridge_doctor_text
    assert "run_med_deepscientist_launcher" not in runtime_bridge_status_text
    assert "run_med_deepscientist_launcher" not in runtime_bridge_stop_text
    med_readme_text = (workspace_root / "ops" / "medautoscience" / "README.md").read_text(encoding="utf-8")
    agents_text = (workspace_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "bin/study-state-matrix" in med_readme_text
    assert "bin/progress-projection <study_id> --format json" in med_readme_text
    assert "bin/study-progress <study_id>" in med_readme_text
    assert "ops/medautoscience/bin/study-progress <study_id>" in agents_text
    assert "ops/medautoscience/bin/study-state-matrix --format json" in agents_text

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
    assert "ops/medautoscience/bin/show-profile" in root_readme_text
    assert "ops/medautoscience/bin/progress-portal" not in root_readme_text
    assert "install-watch-runtime-service" not in root_readme_text
    assert "watch-runtime-service-status" not in root_readme_text
    assert "uninstall-watch-runtime-service" not in root_readme_text
    assert "ops/mas/progress/index.html" not in root_readme_text
    assert "ops/mas/" in root_readme_text
    assert "ops/med-deepscientist" not in root_readme_text
    assert "portfolio/research_memory/" in root_readme_text

    ops_readme = workspace_root / "ops" / "medautoscience" / "README.md"
    assert ops_readme.is_file()
    ops_readme_text = ops_readme.read_text(encoding="utf-8")
    assert "OPL current_control_state refs-only handoff" in ops_readme_text
    assert "domain-health-diagnostic" in ops_readme_text
    assert "medautosci runtime ensure-supervision --profile <profile>" not in ops_readme_text
    assert "medautosci runtime supervision-status --profile <profile>" not in ops_readme_text
    assert "medautosci runtime remove-supervision --profile <profile>" not in ops_readme_text
    assert "install-watch-runtime-service" not in ops_readme_text
    assert "watch-runtime-service-status" not in ops_readme_text
    assert "uninstall-watch-runtime-service" not in ops_readme_text

    root_agents = workspace_root / "AGENTS.md"
    assert root_agents.is_file()
    root_agents_text = root_agents.read_text(encoding="utf-8")
    assert "# glioma Workspace Rules" in root_agents_text
    assert "[`WORKSPACE_AUTOSCIENCE_RULES.md`](WORKSPACE_AUTOSCIENCE_RULES.md)" in root_agents_text
    assert "`developer_supervisor_mode`、`github_username` 与 `mas_developer_github_usernames`" in root_agents_text
    assert "PR route" in root_agents_text
    assert "如果登录账号是 `gaofeng21cn`" not in root_agents_text
    assert "优先使用 `rtk` 前缀运行 shell 命令。" not in root_agents_text
    assert "优先读取 `MINERU_TOKEN`" not in root_agents_text

    runtime_bridge_readme = workspace_root / "ops" / "mas" / "README.md"
    assert runtime_bridge_readme.is_file()
    runtime_bridge_readme_text = runtime_bridge_readme.read_text(encoding="utf-8")
    assert "MAS domain refs 运维薄入口脚本" in runtime_bridge_readme_text
    assert "OPL current-control-state" in runtime_bridge_readme_text
    assert "只调用 MAS domain refs / diagnostic surface" in runtime_bridge_readme_text
    assert "ops/med-deepscientist" not in runtime_bridge_readme_text
    assert "ensure-study-runtime" not in runtime_bridge_readme_text
    assert "MAS-first runtime 运维面" not in runtime_bridge_readme_text

    assert not (workspace_root / "ops" / "mas" / "progress" / "index.html").exists()
    assert not (workspace_root / "ops" / "mas" / "live-console").exists()

    workspace_pyproject = workspace_root / "pyproject.toml"
    assert workspace_pyproject.is_file()
    workspace_pyproject_text = workspace_pyproject.read_text(encoding="utf-8")
    expected_repo_relpath = Path(os.path.relpath(Path(module.__file__).resolve().parents[3], workspace_root)).as_posix()
    assert 'name = "glioma-workspace"' in workspace_pyproject_text
    assert 'description = "Managed Python environment for the glioma workspace."' in workspace_pyproject_text
    assert '"med-autoscience[analysis]"' in workspace_pyproject_text
    assert "[tool.uv.sources]" in workspace_pyproject_text
    assert f'med-autoscience = {{ path = "{expected_repo_relpath}", editable = true }}' in workspace_pyproject_text

    workspace_rules = workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"
    assert workspace_rules.is_file()
    workspace_rules_text = workspace_rules.read_text(encoding="utf-8")
    assert "优先复用 MedAutoScience 已覆盖的成熟 controller / CLI / overlay skill" in workspace_rules_text
    assert "边界明确且 startup-ready 后，默认切入 MAS-owned managed runtime 的自动持续推进" in workspace_rules_text
    assert "默认 cadence / wakeup / provider SLO 由 OPL provider/runtime manager 承载" in workspace_rules_text
    assert "`local` 已物理退役为 tombstone/provenance-only" in workspace_rules_text
    assert "默认由 `local` scheduler adapter 托管" not in workspace_rules_text
    assert "必须显式通知用户自动驾驶已启动或已被检测到，并提供监督入口" in workspace_rules_text
    assert "前台必须立即进入 supervisor-only 监管态" in workspace_rules_text
    assert "不得直接写入 runtime-owned 的 study / quest / paper surface" in workspace_rules_text
    assert "portfolio-memory-status" in workspace_rules_text
    assert "prepare-external-research" in workspace_rules_text

    domain_health_diagnostic_text = domain_health_diagnostic.read_text(encoding="utf-8")
    assert 'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"' in domain_health_diagnostic_text
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/runtime/quests"' in domain_health_diagnostic_text
    assert 'run_medautosci runtime domain-health-diagnostic \\' in domain_health_diagnostic_text
    assert "ops/med-deepscientist" not in domain_health_diagnostic_text


def test_generated_progress_projection_accepts_study_id_without_extra_args(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "progress-wrapper-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="progress-wrapper",
        dry_run=False,
        force=False,
    )

    progress_projection = workspace_root / "ops" / "medautoscience" / "bin" / "progress-projection"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "progress-wrapper.local.toml"
    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'PROFILE_PATH="{profile_path}"\n'
        "run_medautosci() {\n"
        "  printf '%s\\n' \"$@\"\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["/bin/bash", str(progress_projection), "002-dm-china-us-mortality-attribution"],
        check=True,
        cwd=workspace_root,
        text=True,
        capture_output=True,
    )

    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "study-progress",
        "--profile",
        str(profile_path),
        "--format",
        "json",
        "--study-id",
        "002-dm-china-us-mortality-attribution",
    ]


def test_generated_progress_projection_forces_json_format(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "progress-wrapper-format-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="progress-wrapper-format",
        dry_run=False,
        force=False,
    )

    progress_projection = workspace_root / "ops" / "medautoscience" / "bin" / "progress-projection"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "progress-wrapper-format.local.toml"
    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'PROFILE_PATH="{profile_path}"\n'
        "run_medautosci() {\n"
        "  printf '%s\\n' \"$@\"\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "/bin/bash",
            str(progress_projection),
            "002-dm-china-us-mortality-attribution",
            "--format",
            "markdown",
            "--format=json",
        ],
        check=True,
        cwd=workspace_root,
        text=True,
        capture_output=True,
    )

    output = result.stdout.splitlines()
    assert result.stderr == ""
    assert "--format=json" not in output
    assert "markdown" not in output
    assert output == [
        "study-progress",
        "--profile",
        str(profile_path),
        "--format",
        "json",
        "--study-id",
        "002-dm-china-us-mortality-attribution",
    ]


def test_generated_profile_optional_wrapper_accepts_no_args_under_bash_nounset(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "profile-wrapper-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="profile-wrapper",
        dry_run=False,
        force=False,
    )

    resolve_targets = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-submission-targets"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "profile-wrapper.local.toml"
    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'PROFILE_PATH="{profile_path}"\n'
        "run_medautosci() {\n"
        "  printf '%s\\n' \"$@\"\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["/bin/bash", str(resolve_targets)],
        check=True,
        cwd=workspace_root,
        text=True,
        capture_output=True,
    )

    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "publication",
        "resolve-targets",
        "--profile",
        str(profile_path),
    ]


def test_init_workspace_records_detected_github_username_in_profile(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "detected-user-workspace"

    monkeypatch.setattr(module.shutil, "which", lambda command: "/usr/bin/gh" if command == "gh" else None)

    class Completed:
        returncode = 0
        stdout = "someone-else\n"

    monkeypatch.setattr(module.subprocess, "run", lambda *_, **__: Completed())

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="detected-user",
        dry_run=False,
        force=False,
    )

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "detected-user.local.toml"
    profile_text = profile_path.read_text(encoding="utf-8")

    assert 'developer_supervisor_mode = "external_observe"' in profile_text
    assert 'github_username = "someone-else"' in profile_text
    assert 'mas_developer_github_usernames = ["gaofeng21cn"]' in profile_text


def test_init_workspace_merges_profile_root_keys_before_existing_tables(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "existing-table-workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "existing-table.local.toml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "existing-table"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                "",
                "[explicit_archive_import_ref]",
                'runtime_root = "/tmp/archive"',
                "read_only = true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "_detect_github_username", lambda: "gaofeng21cn")

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="existing-table",
        dry_run=False,
        force=False,
    )

    profile_text = profile_path.read_text(encoding="utf-8")
    assert profile_text.index('github_username = "gaofeng21cn"') < profile_text.index("[explicit_archive_import_ref]")
    assert profile_text.count('developer_supervisor_mode = "external_observe"') == 1
    assert profile_text.count('mas_developer_github_usernames = ["gaofeng21cn"]') == 1


def test_bootstrap_repairs_table_misnested_developer_profile_keys(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "profile-repair-workspace"

    monkeypatch.setattr(module, "_detect_github_username", lambda: "gaofeng21cn")
    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="profile-repair",
        dry_run=False,
        force=False,
    )
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "profile-repair.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "profile-repair"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "",
                "[explicit_archive_import_ref]",
                'runtime_root = "/tmp/legacy-runtime"',
                'developer_supervisor_mode = "external_observe"',
                'mas_developer_github_usernames = ["gaofeng21cn"]',
                'github_username = "gaofeng21cn"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    first = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="profile-repair",
        dry_run=False,
        force=False,
    )
    second = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="profile-repair",
        dry_run=False,
        force=False,
    )

    profile_text = profile_path.read_text(encoding="utf-8")
    assert str(profile_path) in first["upgraded_files"]
    assert str(profile_path) in second["skipped_files"]
    assert profile_text.count('developer_supervisor_mode = "external_observe"') == 1
    assert profile_text.count('mas_developer_github_usernames = ["gaofeng21cn"]') == 1
    assert profile_text.count('github_username = "gaofeng21cn"') == 1
    assert profile_text.index('developer_supervisor_mode = "external_observe"') < profile_text.index(
        "[explicit_archive_import_ref]"
    )
    profile = profiles.load_profile(profile_path)
    assert profile.developer_supervisor_mode == "external_observe"
    assert profile.github_username == "gaofeng21cn"
    assert profile.mas_developer_github_usernames == ("gaofeng21cn",)


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


def test_init_workspace_does_not_report_current_generated_guidance_as_upgraded(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "current-guidance-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="current-guidance",
        dry_run=False,
        force=False,
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="current-guidance",
        dry_run=False,
        force=False,
    )

    current_guidance_paths = {
        str(workspace_root / "README.md"),
        str(workspace_root / "AGENTS.md"),
        str(workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"),
        str(workspace_root / "ops" / "medautoscience" / "README.md"),
        str(workspace_root / "ops" / "mas" / "README.md"),
    }
    assert current_guidance_paths.isdisjoint(result["upgraded_files"])
