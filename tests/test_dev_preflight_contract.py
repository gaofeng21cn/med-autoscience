from __future__ import annotations

import importlib


def test_classify_changed_files_matches_runtime_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/study_runtime_router.py",
            "src/med_autoscience/controllers/runtime_watch.py",
            "src/med_autoscience/runtime_transport/med_deepscientist.py",
            "tests/test_runtime_watch.py",
        ]
    )

    assert result.matched_categories == ("runtime_contract_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_display_surface_exact_guide() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/medical_display_audit_guide.md",
        ]
    )

    assert result.matched_categories == ("display_publication_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_flags_unclassified_paths() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/workspace_init.py",
        ]
    )

    assert result.matched_categories == ()
    assert result.unclassified_changes == ("src/med_autoscience/controllers/workspace_init.py",)


def test_classify_changed_files_matches_external_runtime_dependency_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/external_runtime_dependency_gate.md",
            "src/med_autoscience/workspace_contracts.py",
        ]
    )

    assert result.matched_categories == ("external_runtime_dependency_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_integration_harness_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/integration_harness_activation_package.md",
            "tests/test_integration_harness_activation_package.py",
        ]
    )

    assert result.matched_categories == ("integration_harness_surface",)
    assert result.unclassified_changes == ()


def test_plan_commands_for_categories_deduplicates_results() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(
        ("workflow_surface", "workflow_surface", "codex_plugin_docs_surface")
    )

    assert commands.count("uv run pytest tests/test_release_workflow.py -q") == 1
    assert "uv run pytest tests/test_codex_plugin.py -q" in commands


def test_plan_commands_for_external_runtime_dependency_surface_include_gate_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("external_runtime_dependency_surface",))

    assert "uv run pytest tests/test_med_deepscientist_repo_manifest.py -q" in commands
    assert "uv run pytest tests/test_workspace_contracts.py -q" in commands
    assert "uv run pytest tests/test_deepscientist_upgrade_check.py -q" in commands
    assert "uv run pytest tests/test_external_runtime_dependency_gate.py -q" in commands


def test_plan_commands_for_integration_harness_surface_include_runtime_eval_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("integration_harness_surface",))

    assert "uv run pytest tests/test_dev_preflight_contract.py -q" in commands
    assert "uv run pytest tests/test_integration_harness_activation_package.py -q" in commands
    assert (
        "uv run pytest tests/test_runtime_watch.py tests/test_study_delivery_sync.py tests/test_publication_gate.py -q"
        in commands
    )
