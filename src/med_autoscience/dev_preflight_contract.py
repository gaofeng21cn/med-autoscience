from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PreflightCategorySpec:
    category_id: str
    exact_paths: tuple[str, ...]
    prefix_paths: tuple[str, ...]
    commands: tuple[str, ...]


@dataclass(frozen=True)
class ClassificationResult:
    matched_categories: tuple[str, ...]
    unclassified_changes: tuple[str, ...]


_CATEGORY_SPECS: tuple[PreflightCategorySpec, ...] = (
    PreflightCategorySpec(
        category_id="workflow_surface",
        exact_paths=(
            ".github/workflows/ci.yml",
            ".github/workflows/release.yml",
            ".github/release-notes.md",
            "pyproject.toml",
            "scripts/install-macos.sh",
            "tests/test_release_installer.py",
            "tests/test_release_workflow.py",
        ),
        prefix_paths=(),
        commands=(
            "uv run pytest tests/test_release_workflow.py -q",
            "uv run pytest tests/test_release_installer.py -q",
            "uv run python -m build --sdist --wheel",
        ),
    ),
    PreflightCategorySpec(
        category_id="public_doc_surface",
        exact_paths=(
            "README.md",
            "README.zh-CN.md",
            "docs/README.md",
            "docs/README.zh-CN.md",
            "docs/architecture.md",
            "docs/decisions.md",
            "docs/project.md",
            "docs/status.md",
        ),
        prefix_paths=(),
        commands=(
            "uv run pytest tests/test_dev_preflight_contract.py -q",
            "uv run pytest tests/test_dev_preflight.py -q",
            "make test-meta",
        ),
    ),
    PreflightCategorySpec(
        category_id="codex_plugin_docs_surface",
        exact_paths=(
            "docs/references/codex_plugin.md",
            "docs/references/codex_plugin_release.md",
            "scripts/install-codex-plugin.sh",
            "src/med_autoscience/codex_plugin_installer.py",
            "tests/test_codex_plugin.py",
            "tests/test_codex_plugin_installer.py",
            "tests/test_codex_plugin_installer_script.py",
        ),
        prefix_paths=(),
        commands=(
            "uv run pytest tests/test_codex_plugin.py -q",
            "uv run pytest tests/test_codex_plugin_installer.py -q",
            "uv run pytest tests/test_codex_plugin_installer_script.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="display_publication_surface",
        exact_paths=(
            "docs/capabilities/medical-display/medical_display_audit_guide.md",
            "docs/capabilities/medical-display/medical_display_template_catalog.md",
            "src/med_autoscience/display_registry.py",
            "src/med_autoscience/display_schema_contract.py",
            "src/med_autoscience/display_template_catalog.py",
            "src/med_autoscience/controllers/medical_publication_surface.py",
            "src/med_autoscience/controllers/publication_gate.py",
            "tests/test_display_layout_qc.py",
            "tests/test_display_schema_contract.py",
            "tests/test_display_surface_materialization.py",
            "tests/test_medical_publication_surface.py",
            "tests/test_publication_gate.py",
        ),
        prefix_paths=(
            "src/med_autoscience/display_layout_qc/",
            "src/med_autoscience/controllers/display_surface_materialization/",
        ),
        commands=(
            "uv run pytest tests/test_display_schema_contract.py -q",
            "uv run pytest tests/test_display_surface_materialization.py -q",
            "uv run pytest tests/test_display_layout_qc.py -q",
            "uv run pytest tests/test_publication_gate.py -q",
            "uv run pytest tests/test_medical_publication_surface.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="runtime_contract_surface",
        exact_paths=(
            "docs/references/domain-harness-os-positioning.md",
            "docs/runtime/runtime_backend_interface_contract.md",
            "docs/runtime/runtime_core_convergence_and_controlled_cutover.md",
            "docs/runtime/runtime_core_convergence_and_controlled_cutover_implementation_plan.md",
            "docs/runtime/runtime_handle_and_durable_surface_contract.md",
            "src/med_autoscience/controllers/study_outer_loop.py",
            "src/med_autoscience/controllers/study_runtime_execution.py",
            "src/med_autoscience/runtime_backend.py",
            "src/med_autoscience/controllers/runtime_watch.py",
            "src/med_autoscience/controllers/study_runtime_decision.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/study_runtime_router.py",
            "src/med_autoscience/controllers/study_runtime_startup.py",
            "src/med_autoscience/controllers/study_runtime_status.py",
            "src/med_autoscience/profiles.py",
            "src/med_autoscience/runtime_transport/hermes.py",
            "src/med_autoscience/runtime_transport/med_deepscientist.py",
            "tests/test_profiles.py",
            "tests/test_runtime_backend.py",
            "tests/test_runtime_contract_docs.py",
            "tests/test_runtime_protocol_layout.py",
            "tests/test_runtime_protocol_runtime_watch.py",
            "tests/test_runtime_protocol_study_runtime.py",
            "tests/test_runtime_transport_hermes.py",
            "tests/test_runtime_transport_med_deepscientist.py",
            "tests/test_runtime_watch.py",
            "tests/test_study_runtime_router.py",
        ),
        prefix_paths=(
            "src/med_autoscience/runtime_protocol/",
        ),
        commands=(
            "uv run pytest tests/test_runtime_backend.py -q",
            "uv run pytest tests/test_profiles.py -q",
            "uv run pytest tests/test_runtime_contract_docs.py -q",
            "uv run pytest tests/test_runtime_protocol_layout.py -q",
            "uv run pytest tests/test_runtime_watch.py -q",
            "uv run pytest tests/test_study_runtime_router.py -q",
            "uv run pytest tests/test_runtime_transport_hermes.py -q",
            "uv run pytest tests/test_runtime_transport_med_deepscientist.py -q",
            "uv run pytest tests/test_runtime_protocol_study_runtime.py -q",
            "uv run pytest tests/test_runtime_protocol_runtime_watch.py -q",
            "make test-meta",
        ),
    ),
    PreflightCategorySpec(
        category_id="external_runtime_dependency_surface",
        exact_paths=(
            "docs/references/disease_workspace_quickstart.md",
            "docs/references/workspace_architecture.md",
            "docs/runtime/agent_runtime_interface.md",
            "docs/program/external_runtime_dependency_gate.md",
            "docs/program/merge_and_cutover_gates.md",
            "docs/runtime/runtime_boundary.md",
            "docs/program/upstream_intake.md",
            "src/med_autoscience/controllers/med_deepscientist_upgrade_check.py",
            "src/med_autoscience/controllers/hermes_runtime_check.py",
            "src/med_autoscience/doctor.py",
            "src/med_autoscience/hermes_runtime_contract.py",
            "src/med_autoscience/med_deepscientist_repo_manifest.py",
            "src/med_autoscience/workspace_contracts.py",
            "tests/test_deepscientist_upgrade_check.py",
            "tests/test_external_runtime_dependency_gate.py",
            "tests/test_hermes_runtime_check.py",
            "tests/test_hermes_runtime_contract.py",
            "tests/test_med_deepscientist_repo_manifest.py",
            "tests/test_workspace_contracts.py",
        ),
        prefix_paths=(),
        commands=(
            "uv run pytest tests/test_med_deepscientist_repo_manifest.py -q",
            "uv run pytest tests/test_workspace_contracts.py -q",
            "uv run pytest tests/test_deepscientist_upgrade_check.py -q",
            "uv run pytest tests/test_hermes_runtime_contract.py -q",
            "uv run pytest tests/test_hermes_runtime_check.py -q",
            "uv run pytest tests/test_external_runtime_dependency_gate.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="integration_harness_surface",
        exact_paths=(
            "docs/runtime/agent_runtime_interface.md",
            "docs/program/hermes_backend_activation_package.md",
            "docs/program/hermes_backend_continuation_board.md",
            "docs/program/integration_harness_activation_package.md",
            "docs/program/med_deepscientist_deconstruction_map.md",
            "docs/program/merge_and_cutover_gates.md",
            "docs/program/repository_ci_preflight.md",
            "docs/program/research_foundry_medical_execution_map.md",
            "docs/program/research_foundry_medical_mainline.md",
            "docs/references/research_foundry_medical_phase_ladder.md",
            "src/med_autoscience/controllers/workspace_init.py",
            "src/med_autoscience/dev_preflight_contract.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/test_integration_harness_activation_package.py",
            "tests/test_workspace_init.py",
        ),
        prefix_paths=(),
        commands=(
            "uv run pytest tests/test_dev_preflight_contract.py -q",
            "uv run pytest tests/test_dev_preflight.py -q",
            "uv run pytest tests/test_integration_harness_activation_package.py -q",
            "uv run pytest tests/test_workspace_init.py -q",
            "make test-meta",
        ),
    ),
    PreflightCategorySpec(
        category_id="family_shared_surface",
        exact_paths=(
            "Makefile",
            "pyproject.toml",
            "scripts/verify.sh",
            "src/med_autoscience/editable_shared_bootstrap.py",
            "src/med_autoscience/dev_preflight.py",
            "src/med_autoscience/dev_preflight_contract.py",
            "src/med_autoscience/family_shared_release.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/test_editable_shared_bootstrap.py",
            "tests/test_family_shared_release.py",
            "uv.lock",
        ),
        prefix_paths=(),
        commands=(
            "make test-family",
        ),
    ),
)


def _normalize_changed_file(path: str) -> str:
    return path.strip().replace("\\", "/").removeprefix("./")


def _matches_spec(*, normalized_path: str, spec: PreflightCategorySpec) -> bool:
    if normalized_path in spec.exact_paths:
        return True
    return any(normalized_path.startswith(prefix) for prefix in spec.prefix_paths)


def classify_changed_files(changed_files: Sequence[str]) -> ClassificationResult:
    matched_categories: list[str] = []
    unclassified_changes: list[str] = []

    for changed_file in changed_files:
        normalized_path = _normalize_changed_file(str(changed_file))
        if not normalized_path:
            continue
        matched_here = False
        for spec in _CATEGORY_SPECS:
            if not _matches_spec(normalized_path=normalized_path, spec=spec):
                continue
            matched_here = True
            if spec.category_id not in matched_categories:
                matched_categories.append(spec.category_id)
        if not matched_here and normalized_path not in unclassified_changes:
            unclassified_changes.append(normalized_path)

    return ClassificationResult(
        matched_categories=tuple(matched_categories),
        unclassified_changes=tuple(unclassified_changes),
    )


def plan_commands_for_categories(categories: Iterable[str]) -> list[str]:
    selected_categories: list[str] = []
    for category in categories:
        if category not in selected_categories:
            selected_categories.append(category)

    planned_commands: list[str] = []
    for spec in _CATEGORY_SPECS:
        if spec.category_id not in selected_categories:
            continue
        for command in spec.commands:
            if command not in planned_commands:
                planned_commands.append(command)
    return planned_commands
