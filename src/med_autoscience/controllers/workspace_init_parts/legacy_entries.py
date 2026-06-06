from __future__ import annotations

from pathlib import Path


def legacy_managed_runtime_entry_reason(*, path: Path, existing_content: str) -> str | None:
    suffix = path.parts[-4:]
    for detector in (
        legacy_generated_workspace_guidance_reason,
        legacy_mas_bridge_entry_reason,
        legacy_medautoscience_shared_entry_reason,
        legacy_supervisor_entry_reason,
        legacy_workspace_command_entry_reason,
    ):
        reason = detector(path=path, suffix=suffix, existing_content=existing_content)
        if reason is not None:
            return reason
    return None


def legacy_generated_workspace_guidance_reason(
    *,
    path: Path,
    suffix: tuple[str, ...],
    existing_content: str,
) -> str | None:
    _ = suffix
    if path.name == "AGENTS.md" and "这个文件由 `medautosci init-workspace` 自动生成" in existing_content:
        current_required_tokens = (
            "ops/medautoscience/bin/progress-projection",
            "ops/medautoscience/bin/domain-health-diagnostic",
            "OPL current-control-state refs",
        )
        if any(token not in existing_content for token in current_required_tokens):
            return "legacy_generated_workspace_agents_guidance"
        return None
    if path.name == "WORKSPACE_AUTOSCIENCE_RULES.md" and (
        "这个文件由 `medautosci init-workspace` 自动生成" in existing_content
    ):
        current_required_tokens = (
            "默认 cadence / wakeup / provider SLO 由 OPL provider/runtime manager 承载",
            "`local` 已物理退役为 tombstone/provenance-only",
        )
        legacy_tokens = (
            "Hermes-backed",
            "Hermes-hosted supervision tick",
            "MAS supervisor loop",
            "watch-runtime",
        )
        if any(token not in existing_content for token in current_required_tokens) or any(
            token in existing_content for token in legacy_tokens
        ):
            return "legacy_generated_workspace_autoscience_rules"
        return None
    if path.name == "README.md" and "这个 workspace 由 `medautosci init-workspace` 初始化" in existing_content:
        current_required_tokens = (
            "OPL stage 控制面",
            "ops/medautoscience/bin/progress-projection",
            "MAS 不提供私有 scheduler、runner、attempt 或 runtime console 入口",
        )
        legacy_tokens = (
            "ensure-study-runtime",
            "progress-portal",
            "start-web",
            "install-watch-runtime-service",
            "watch-runtime-service-status",
            "med-deepscientist repo",
            "MDS launcher",
            "med-deepscientist/bin",
        )
        if any(token not in existing_content for token in current_required_tokens) or any(
            token in existing_content for token in legacy_tokens
        ):
            return "legacy_generated_workspace_readme"
        return None
    if len(path.parts) >= 3 and path.parts[-3:] == ("ops", "medautoscience", "README.md"):
        if "这个目录是当前 workspace 面向用户和 Agent 的本地入口层" not in existing_content:
            return None
        current_required_tokens = (
            "bin/domain-health-diagnostic",
            "bin/progress-projection",
            "OPL current_control_state refs-only handoff",
        )
        legacy_tokens = (
            "bin/watch-runtime",
            "bin/supervisor-reconcile",
            "bin/supervisor-consume",
            "bin/supervisor-execute-dispatch",
            "runtime ensure-supervision",
            "runtime supervision-status",
            "runtime remove-supervision",
        )
        if any(token not in existing_content for token in current_required_tokens) or any(
            token in existing_content for token in legacy_tokens
        ):
            return "legacy_generated_medautoscience_readme"
        return None
    if len(path.parts) >= 3 and path.parts[-3:] == ("ops", "mas", "README.md"):
        if "MAS" not in existing_content or "运维薄入口脚本" not in existing_content:
            return None
        current_required_tokens = (
            "MAS domain refs 运维薄入口脚本",
            "OPL current-control-state",
            "只调用 MAS domain refs / diagnostic surface",
        )
        legacy_tokens = (
            "MAS-first runtime 运维面",
            "ensure-study-runtime",
            "start-web",
            "MAS CLI / read-model / controlled pause surface",
            "外部 MDS launcher",
            "daemon 或 WebUI",
        )
        if any(token not in existing_content for token in current_required_tokens) or any(
            token in existing_content for token in legacy_tokens
        ):
            return "legacy_generated_mas_bridge_readme"
    return None


def legacy_mas_bridge_entry_reason(*, path: Path, suffix: tuple[str, ...], existing_content: str) -> str | None:
    if len(path.parts) >= 3 and path.parts[-3:] == ("ops", "mas", "config.env"):
        if "MED_DEEPSCIENTIST_LAUNCHER" in existing_content:
            return "legacy_mds_launcher_bridge_config"
        return None
    if suffix == ("ops", "mas", "bin", "_shared.sh"):
        if "MED_DEEPSCIENTIST_LAUNCHER" in existing_content or "run_med_deepscientist_launcher" in existing_content:
            return "legacy_mds_launcher_bridge_shared"
        return None
    if len(suffix) == 4 and suffix[:3] == ("ops", "mas", "bin"):
        if "run_med_deepscientist_launcher" in existing_content:
            return "legacy_mds_launcher_bridge_forward"
        return None
    return None


def legacy_medautoscience_shared_entry_reason(
    *,
    path: Path,
    suffix: tuple[str, ...],
    existing_content: str,
) -> str | None:
    _ = path
    if suffix == ("ops", "medautoscience", "bin", "_shared.sh"):
        if "python3 -m med_autoscience.cli" in existing_content:
            return "legacy_python_entry"
        looks_like_uv_entry = (
            "run_medautosci() {" in existing_content
            and 'uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in existing_content
        )
        if looks_like_uv_entry and "MED_AUTOSCIENCE_UV_BIN" not in existing_content:
            return "legacy_uv_entry"
        looks_like_managed_shared = (
            "run_medautosci() {" in existing_content
            and '"${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"'
            in existing_content
        )
        looks_like_workspace_python_runner = (
            "run_medautosci() {" in existing_content
            and '"${WORKSPACE_PYTHON}" -m med_autoscience.cli "$@"' in existing_content
        )
        workspace_python_gate_is_in_runner = (
            'run_medautosci() {\n'
            '  if [[ ! -x "${WORKSPACE_PYTHON}" ]]; then\n' in existing_content
        )
        if looks_like_workspace_python_runner and not workspace_python_gate_is_in_runner:
            return "legacy_workspace_python_gate"
        if looks_like_managed_shared and "MED_AUTOSCIENCE_RSCRIPT_BIN" not in existing_content:
            return "legacy_rscript_entry"
        if looks_like_managed_shared and "MED_AUTOSCIENCE_NODE_BIN" not in existing_content:
            return "legacy_node_entry"
        if looks_like_uv_entry or looks_like_managed_shared:
            return "legacy_workspace_python_entry"
        return None
    return None


def legacy_supervisor_entry_reason(
    *,
    path: Path,
    suffix: tuple[str, ...],
    existing_content: str,
) -> str | None:
    _ = path
    supervisor_specs = (
        (
            ("ops", "medautoscience", "bin", "owner-route-reconcile"),
            ("run_medautosci owner-route-reconcile",),
            "legacy_scan_domain_routes_entry",
        ),
        (
            ("ops", "medautoscience", "bin", "domain-action-request-materialize"),
            ("runtime domain-action-request-materialize", "--mode developer_apply_safe"),
            "legacy_materialize_domain_action_requests_entry",
        ),
        (
            ("ops", "medautoscience", "bin", "domain-owner-action-dispatch"),
            ("runtime domain-owner-action-dispatch", "--mode developer_apply_safe"),
            "legacy_supervisor_execute_dispatch_entry",
        ),
    )
    return legacy_entry_reason_from_required_tokens(
        suffix=suffix,
        existing_content=existing_content,
        specs=supervisor_specs,
    )


def legacy_workspace_command_entry_reason(
    *,
    path: Path,
    suffix: tuple[str, ...],
    existing_content: str,
) -> str | None:
    _ = path
    command_specs = (
        ("bootstrap", "workspace bootstrap", "run_medautosci bootstrap", "legacy_workspace_bootstrap_entry"),
        ("show-profile", "doctor profile", "run_medautosci show-profile", "legacy_show_profile_entry"),
        ("enter-study", "launch-study", "run_medautosci ensure-study-runtime", "legacy_enter_study_entry"),
        ("enter-study", "launch-study", "run_medautosci study ensure-runtime", "legacy_enter_study_entry"),
        ("publication-gate", "publication gate", "run_medautosci publication-gate", "legacy_publication_gate_entry"),
        (
            "medical-surface",
            "publication surface",
            "run_medautosci medical-publication-surface",
            "legacy_publication_surface_entry",
        ),
        (
            "figure-loop-guard",
            "publication figure-loop-guard",
            "run_medautosci figure-loop-guard",
            "legacy_figure_loop_guard_entry",
        ),
        (
            "resolve-submission-targets",
            "publication resolve-targets",
            "run_medautosci resolve-submission-targets",
            "legacy_resolve_submission_targets_entry",
        ),
        (
            "resolve-journal-shortlist",
            "publication resolve-journal-shortlist",
            "run_medautosci resolve-journal-shortlist",
            "legacy_resolve_journal_shortlist_entry",
        ),
        (
            "init-portfolio-memory",
            "data init-memory",
            "run_medautosci init-portfolio-memory",
            "legacy_init_portfolio_memory_entry",
        ),
        (
            "portfolio-memory-status",
            "data memory-status",
            "run_medautosci portfolio-memory-status",
            "legacy_portfolio_memory_status_entry",
        ),
        (
            "init-workspace-literature",
            "data init-literature",
            "run_medautosci init-workspace-literature",
            "legacy_init_workspace_literature_entry",
        ),
        (
            "workspace-literature-status",
            "data literature-status",
            "run_medautosci workspace-literature-status",
            "legacy_workspace_literature_status_entry",
        ),
        (
            "prepare-external-research",
            "data prepare-external-research",
            "run_medautosci prepare-external-research",
            "legacy_prepare_external_research_entry",
        ),
        (
            "external-research-status",
            "data external-research-status",
            "run_medautosci external-research-status",
            "legacy_external_research_status_entry",
        ),
        (
            "export-submission",
            "publication export-targets",
            "run_medautosci export-submission-targets",
            "legacy_export_submission_targets_entry",
        ),
        ("sync-delivery", "study delivery-sync", "run_medautosci sync-study-delivery", "legacy_sync_study_delivery_entry"),
    )
    for command_name, required_token, legacy_token, reason in command_specs:
        command_suffix = ("ops", "medautoscience", "bin", command_name)
        if suffix == command_suffix and required_token not in existing_content and legacy_token in existing_content:
            return reason
    return None


def legacy_entry_reason_from_required_tokens(
    *,
    suffix: tuple[str, ...],
    existing_content: str,
    specs: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...],
) -> str | None:
    for expected_suffix, required_tokens, reason in specs:
        if suffix == expected_suffix and any(token not in existing_content for token in required_tokens):
            return reason
    return None
