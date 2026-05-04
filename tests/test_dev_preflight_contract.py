from __future__ import annotations

import importlib
import json
from pathlib import Path
import shlex

import pytest

pytestmark = pytest.mark.family


def _planned_pytest_paths(command: str) -> tuple[str, ...]:
    parts = shlex.split(command)
    if len(parts) < 3 or parts[:3] != ["uv", "run", "pytest"]:
        return ()
    return tuple(part for part in parts[3:] if part.startswith("tests/"))


def _all_category_exact_paths(module) -> tuple[str, ...]:
    return tuple(dict.fromkeys(path for spec in module._CATEGORY_SPECS for path in spec.exact_paths))


def _category_path_families(module) -> tuple:
    return tuple(
        module.PreflightCoveragePathFamily(
            family_id=spec.category_id,
            exact_paths=spec.exact_paths,
            prefix_paths=spec.prefix_paths,
        )
        for spec in module._CATEGORY_SPECS
    )


def test_preflight_category_exact_test_paths_exist() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")
    repo_root = Path(__file__).resolve().parents[1]

    missing_paths = [
        f"{spec.category_id}: {path}"
        for spec in module._CATEGORY_SPECS
        for path in spec.exact_paths
        if path.startswith("tests/") and not (repo_root / path).exists()
    ]

    assert missing_paths == []


def test_preflight_planned_pytest_paths_exist() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")
    repo_root = Path(__file__).resolve().parents[1]

    missing_paths = [
        f"{spec.category_id}: {path}"
        for spec in module._CATEGORY_SPECS
        for command in spec.commands
        for path in _planned_pytest_paths(command)
        if not (repo_root / path).exists()
    ]

    assert missing_paths == []


def test_preflight_contract_report_lists_categories_and_planned_commands() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    report = module.build_preflight_contract_report()
    categories = {category["category_id"]: category for category in report["categories"]}

    assert report["surface_kind"] == "preflight_contract_report"
    assert set(categories) == {
        *(spec.category_id for spec in module._CATEGORY_SPECS),
        module.GENERIC_PYTHON_REGRESSION_CATEGORY,
    }
    public_doc = categories["public_doc_surface"]
    assert public_doc["category"] == "public_doc_surface"
    assert "README.md" in public_doc["exact_paths"]
    assert public_doc["prefix_paths"] == []
    assert public_doc["owner_surface"] == {
        "exact_paths": public_doc["exact_paths"],
        "prefix_paths": public_doc["prefix_paths"],
    }
    assert public_doc["fail_policy"] == "matched_paths_run_planned_commands"
    assert public_doc["commands"] == public_doc["planned_commands"]
    assert "uv run pytest tests/test_dev_preflight_contract.py -q" in public_doc["planned_commands"]
    assert {
        "command": "uv run pytest tests/test_dev_preflight_contract.py -q",
        "path": "tests/test_dev_preflight_contract.py",
        "exists": True,
    } in public_doc["planned_pytest_path_existence"]
    assert public_doc["pytest_path_existence"] == public_doc["planned_pytest_path_existence"]
    assert "fail-closed" in public_doc["unknown_path_suggestion"]
    assert any("fail-closed" in suggestion for suggestion in public_doc["unknown_path_suggestions"])
    generic = categories[module.GENERIC_PYTHON_REGRESSION_CATEGORY]
    assert generic["category"] == module.GENERIC_PYTHON_REGRESSION_CATEGORY
    assert generic["exact_paths"] == []
    assert generic["prefix_paths"] == ["src/med_autoscience/", "tests/"]
    assert generic["owner_surface"] == {
        "exact_paths": [],
        "prefix_paths": ["src/med_autoscience/", "tests/"],
    }
    assert generic["fail_policy"] == "unknown_python_and_test_paths_route_to_regression"
    assert generic["planned_commands"] == ["make test-regression"]
    assert "make test-regression" in generic["unknown_path_suggestion"]
    assert any("src/med_autoscience/" in suggestion for suggestion in generic["unknown_path_suggestions"])
    assert any("tests/" in suggestion for suggestion in generic["unknown_path_suggestions"])
    assert report["unknown_path_policy"] == {
        "python_and_test_paths": "regression",
        "docs_workflow_config_paths": "fail-closed",
    }


def test_preflight_contract_report_planned_pytest_paths_exist() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")
    repo_root = Path(__file__).resolve().parents[1]
    report = module.build_preflight_contract_report()

    missing_paths = [
        f"{category['category_id']}: {path}"
        for category in report["categories"]
        for command in category["planned_commands"]
        for path in _planned_pytest_paths(str(command))
        if not (repo_root / path).exists()
    ]

    assert missing_paths == []


def test_preflight_contract_report_planned_pytest_path_statuses_exist() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")
    report = module.build_preflight_contract_report()

    missing_statuses = [
        f"{category['category_id']}: {status['path']}"
        for category in report["categories"]
        for status in category["planned_pytest_path_existence"]
        if status["exists"] is not True
    ]

    assert missing_statuses == []
    for category in report["categories"]:
        planned_statuses = {
            (status["command"], status["path"])
            for status in category["planned_pytest_path_existence"]
        }
        planned_paths = {
            (command, path)
            for command in category["planned_commands"]
            for path in _planned_pytest_paths(str(command))
        }
        assert planned_statuses == planned_paths


def test_preflight_contract_report_hygiene_documents_review_policies() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")
    report = module.build_preflight_contract_report()

    hygiene = report["contract_hygiene"]

    assert hygiene["planned_pytest_paths_exist"] is True
    assert hygiene["missing_planned_pytest_paths"] == []
    assert hygiene["unknown_python_and_test_paths"] == {
        "category": module.GENERIC_PYTHON_REGRESSION_CATEGORY,
        "planned_commands": ["make test-regression"],
        "fail_policy": "unknown_python_and_test_paths_route_to_regression",
    }
    assert hygiene["unknown_docs_workflow_config_paths"] == {
        "planned_commands": [],
        "fail_policy": "fail-closed",
        "suggestion": "Add the path to a reviewed owner surface before preflight can run commands.",
    }


def test_preflight_contract_report_cli_is_read_only_json(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor", "preflight-contract-report", "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 0
    assert report["surface_kind"] == "preflight_contract_report"
    assert report["contract_hygiene"]["planned_pytest_paths_exist"] is True
    assert any(category["category_id"] == "workflow_surface" for category in report["categories"])
    workflow = next(category for category in report["categories"] if category["category_id"] == "workflow_surface")
    assert workflow["category"] == "workflow_surface"
    assert workflow["pytest_path_existence"] == workflow["planned_pytest_path_existence"]
    assert isinstance(workflow["unknown_path_suggestion"], str)
    assert any(
        "uv run pytest tests/test_dev_preflight.py -q" in category["planned_commands"]
        for category in report["categories"]
    )


def test_preflight_category_audit_keeps_spec_paths_explicit() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        _all_category_exact_paths(module),
        path_families=_category_path_families(module),
    )

    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == ()
    assert all(
        family_audit.family_id in family_audit.explicit_categories
        for family_audit in audit.family_audits
        if family_audit.explicit_classified_paths
    )


def test_classify_changed_files_matches_runtime_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/references/domain-harness-os-positioning.md",
            "docs/runtime/runtime_backend_interface_contract.md",
            "docs/runtime/runtime_handle_and_durable_surface_contract.md",
            "docs/runtime/runtime_supervision_loop.md",
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
            "tests/test_work_unit_runtime_contract.py",
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
            "docs/program/untracked_runtime_contract.md",
        ]
    )

    assert result.matched_categories == ()
    assert result.unclassified_changes == ("docs/program/untracked_runtime_contract.md",)


def test_classify_changed_files_routes_unknown_python_to_generic_regression() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/new_controller.py",
            "tests/test_new_controller.py",
        ]
    )

    assert result.matched_categories == ("generic_python_regression_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == ["make test-regression"]


def test_classify_changed_files_keeps_unknown_docs_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(["docs/program/new_runtime_contract.md"])

    assert result.matched_categories == ()
    assert result.unclassified_changes == ("docs/program/new_runtime_contract.md",)


def test_audit_preflight_contract_coverage_identifies_explicit_classification() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        ["src/med_autoscience/controllers/study_runtime_router.py"],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="controller_sources",
                exact_paths=(),
                prefix_paths=("src/med_autoscience/controllers/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == (
        "src/med_autoscience/controllers/study_runtime_router.py",
    )
    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == ()
    assert audit.family_audits[0].explicit_categories == ("runtime_contract_surface",)
    assert audit.family_audits[0].explicit_classified_paths == (
        "src/med_autoscience/controllers/study_runtime_router.py",
    )


def test_audit_preflight_contract_coverage_marks_generic_python_fallback() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        [
            "src/med_autoscience/controllers/new_controller.py",
            "tests/test_new_controller.py",
        ],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="controller_sources",
                exact_paths=(),
                prefix_paths=("src/med_autoscience/controllers/",),
            ),
            module.PreflightCoveragePathFamily(
                family_id="test_sources",
                exact_paths=(),
                prefix_paths=("tests/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == ()
    assert audit.generic_python_regression_paths == (
        "src/med_autoscience/controllers/new_controller.py",
        "tests/test_new_controller.py",
    )
    assert audit.fail_closed_paths == ()
    assert audit.generic_python_regression_families == (
        "controller_sources",
        "test_sources",
    )


def test_audit_preflight_contract_coverage_keeps_unknown_non_python_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        [
            "docs/program/new_runtime_contract.md",
            ".github/workflows/new-release.yml",
            "tox.ini",
        ],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="program_docs",
                exact_paths=(),
                prefix_paths=("docs/program/",),
            ),
            module.PreflightCoveragePathFamily(
                family_id="workflow_config",
                exact_paths=("tox.ini",),
                prefix_paths=(".github/workflows/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == ()
    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == (
        "docs/program/new_runtime_contract.md",
        ".github/workflows/new-release.yml",
        "tox.ini",
    )
    assert audit.fail_closed_families == ("program_docs", "workflow_config")


def test_classify_changed_files_matches_control_plane_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/study_control_plane_kernel.py",
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/control_plane_migration_audit.py",
            "src/med_autoscience/controllers/control_plane_state.py",
            "src/med_autoscience/cli.py",
            "src/med_autoscience/cli_parts/parser.py",
            "src/med_autoscience/mcp_server.py",
            "src/med_autoscience/controllers/control_intent.py",
            "src/med_autoscience/controllers/control_identity.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/dataset_retention.py",
            "src/med_autoscience/controllers/runtime_watch_parts/control_plane_gate.py",
            "src/med_autoscience/controllers/runtime_watch_parts/managed_wakeup.py",
            "src/med_autoscience/controllers/study_progress_parts/projection.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_orchestration.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_cli.py",
            "src/med_autoscience/runtime_protocol/paper_artifacts.py",
            "tests/test_study_control_plane_kernel.py",
            "tests/test_artifact_lifecycle_inventory.py",
            "tests/test_artifact_lifecycle_operations_report.py",
            "tests/test_control_plane_migration_audit.py",
            "tests/test_cli_cases/public_entry_commands.py",
            "tests/test_mcp_server.py",
            "tests/control_plane_fixtures.py",
        ]
    )

    assert result.matched_categories == (
        "control_plane_surface",
        "runtime_contract_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_external_runtime_dependency_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/program/external_runtime_dependency_gate.md",
            "docs/program/manual_runtime_stabilization_checklist.md",
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
            "docs/invariants.md",
            "docs/status.md",
            "docs/decisions.md",
            "docs/references/series-doc-governance-checklist.md",
        ]
    )

    assert result.matched_categories == ("public_doc_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_ci_workflow_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            ".github/workflows/advisory.yml",
            ".github/workflows/ci.yml",
            "tests/test_release_workflow.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface",)
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
            "scripts/run-parallel-test-lanes.sh",
            "src/med_autoscience/controllers/workspace_init.py",
            "tests/test_workspace_init.py",
            "tests/test_integration_harness_activation_package.py",
            "tests/test_sentrux_gitstats_helper.py",
        ]
    )

    assert result.matched_categories == ("integration_harness_surface",)
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

    assert result.matched_categories == ("workflow_surface", "family_shared_surface")
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
    assert "uv run pytest tests/test_hermes_runtime_contract.py -q" in commands
    assert "uv run pytest tests/test_hermes_runtime_check.py -q" in commands


def test_plan_commands_for_integration_harness_surface_include_runtime_eval_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("integration_harness_surface",))

    assert "uv run pytest tests/test_dev_preflight_contract.py -q" in commands
    assert "uv run pytest tests/test_dev_preflight.py -q" in commands
    assert "uv run pytest tests/test_integration_harness_activation_package.py -q" in commands
    assert "uv run pytest tests/test_workspace_init.py -q" in commands
    assert "make test-meta" in commands
    assert "uv run pytest tests/test_work_unit_runtime_contract.py -q" not in commands
    assert "uv run pytest tests/test_runtime_watch.py tests/test_study_delivery_sync.py tests/test_publication_gate.py -q" not in commands


def test_plan_commands_for_runtime_contract_surface_include_hermes_and_doc_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("runtime_contract_surface",))

    assert "uv run pytest tests/test_runtime_backend.py -q" in commands
    assert "uv run pytest tests/test_profiles.py -q" in commands
    assert "uv run pytest tests/test_runtime_protocol_layout.py -q" in commands
    assert "uv run pytest tests/test_runtime_transport_hermes.py -q" in commands
    assert "uv run pytest tests/test_work_unit_runtime_contract.py -q" in commands
    assert "make test-meta" in commands


def test_plan_commands_for_family_shared_surface_use_focused_family_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("family_shared_surface",))

    assert commands == ["make test-family"]


def test_plan_commands_for_control_plane_surface_use_focused_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("control_plane_surface",))

    assert commands == ["make test-control-plane"]
