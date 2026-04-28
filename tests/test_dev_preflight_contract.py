from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.family


def test_classify_changed_files_matches_runtime_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/references/domain-harness-os-positioning.md",
            "docs/runtime/runtime_backend_interface_contract.md",
            "docs/runtime/runtime_handle_and_durable_surface_contract.md",
            "src/med_autoscience/profiles.py",
            "src/med_autoscience/runtime_backend.py",
            "src/med_autoscience/controllers/study_outer_loop.py",
            "src/med_autoscience/controllers/study_runtime_execution.py",
            "src/med_autoscience/controllers/study_runtime_decision.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/study_runtime_router.py",
            "src/med_autoscience/controllers/runtime_watch.py",
            "src/med_autoscience/runtime_transport/hermes.py",
            "src/med_autoscience/runtime_transport/med_deepscientist.py",
            "tests/test_profiles.py",
            "tests/test_runtime_backend.py",
            "tests/test_runtime_contract_docs.py",
            "tests/test_runtime_protocol_layout.py",
            "tests/test_runtime_transport_hermes.py",
            "tests/test_runtime_watch.py",
        ]
    )

    assert result.matched_categories == ("runtime_contract_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_display_surface_exact_guide() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/capabilities/medical-display/medical_display_audit_guide.md",
        ]
    )

    assert result.matched_categories == ("display_publication_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_flags_unclassified_paths() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/untracked_controller.py",
        ]
    )

    assert result.matched_categories == ()
    assert result.unclassified_changes == ("src/med_autoscience/controllers/untracked_controller.py",)


def test_classify_changed_files_matches_external_runtime_dependency_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/program/external_runtime_dependency_gate.md",
            "docs/references/workspace_architecture.md",
            "docs/references/disease_workspace_quickstart.md",
            "src/med_autoscience/workspace_contracts.py",
        ]
    )

    assert result.matched_categories == ("external_runtime_dependency_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_public_doc_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "README.md",
            "README.zh-CN.md",
            "docs/README.md",
            "docs/README.zh-CN.md",
            "docs/project.md",
            "docs/architecture.md",
            "docs/status.md",
            "docs/decisions.md",
        ]
    )

    assert result.matched_categories == ("public_doc_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_integration_harness_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/program/hermes_backend_continuation_board.md",
            "docs/program/hermes_backend_activation_package.md",
            "docs/program/med_deepscientist_deconstruction_map.md",
            "docs/program/integration_harness_activation_package.md",
            "docs/program/research_foundry_medical_mainline.md",
            "docs/references/research_foundry_medical_phase_ladder.md",
            "scripts/prepare-sentrux-gitstats-clone.sh",
            "src/med_autoscience/controllers/workspace_init.py",
            "src/med_autoscience/dev_preflight_contract.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/test_workspace_init.py",
            "tests/test_integration_harness_activation_package.py",
            "tests/test_sentrux_gitstats_helper.py",
        ]
    )

    assert result.matched_categories == ("integration_harness_surface", "family_shared_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_family_shared_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "pyproject.toml",
            "uv.lock",
            "Makefile",
            "scripts/verify.sh",
            "src/med_autoscience/editable_shared_bootstrap.py",
            "src/med_autoscience/dev_preflight.py",
            "src/med_autoscience/dev_preflight_contract.py",
            "src/med_autoscience/family_shared_release.py",
            "tests/test_editable_shared_bootstrap.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/test_family_shared_release.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface", "family_shared_surface", "integration_harness_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_verify_script_as_family_shared_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "scripts/verify.sh",
        ]
    )

    assert result.matched_categories == ("family_shared_surface",)
    assert result.unclassified_changes == ()


def test_plan_commands_for_categories_deduplicates_results() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(
        ("workflow_surface", "workflow_surface", "codex_plugin_docs_surface")
    )

    assert commands.count("uv run pytest tests/test_release_workflow.py -q") == 1
    assert "uv run pytest tests/test_codex_plugin.py -q" in commands


def test_plan_commands_for_public_doc_surface_stay_lightweight() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("public_doc_surface",))

    assert commands == [
        "uv run pytest tests/test_dev_preflight_contract.py -q",
        "uv run pytest tests/test_dev_preflight.py -q",
        "make test-meta",
    ]


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
    assert "uv run pytest tests/test_dev_preflight.py -q" in commands
    assert "uv run pytest tests/test_integration_harness_activation_package.py -q" in commands
    assert "uv run pytest tests/test_workspace_init.py -q" in commands
    assert "make test-meta" in commands
    assert "uv run pytest tests/test_runtime_contract_docs.py -q" not in commands
    assert "uv run pytest tests/test_runtime_watch.py tests/test_study_delivery_sync.py tests/test_publication_gate.py -q" not in commands


def test_plan_commands_for_runtime_contract_surface_include_hermes_and_doc_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("runtime_contract_surface",))

    assert "uv run pytest tests/test_runtime_backend.py -q" in commands
    assert "uv run pytest tests/test_profiles.py -q" in commands
    assert "uv run pytest tests/test_runtime_protocol_layout.py -q" in commands
    assert "uv run pytest tests/test_runtime_transport_hermes.py -q" in commands
    assert "uv run pytest tests/test_runtime_contract_docs.py -q" in commands
    assert "make test-meta" in commands


def test_plan_commands_for_family_shared_surface_use_focused_family_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("family_shared_surface",))

    assert commands == ["make test-family"]
