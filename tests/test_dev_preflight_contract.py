from __future__ import annotations

import importlib
import json
from pathlib import Path
import shlex

import pytest

pytestmark = pytest.mark.family


def _planned_pytest_paths(command: str) -> tuple[str, ...]:
    parts = shlex.split(command)
    if parts[:1] == ["scripts/run-pytest-clean.sh"]:
        return tuple(part for part in parts[1:] if part.startswith("tests/"))
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


def test_stale_compatibility_terms_do_not_reenter_active_surfaces() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    search_roots = [
        repo_root / "src",
        repo_root / "tests",
        repo_root / "contracts",
        repo_root / "profiles",
    ]
    blocked_terms = (
        "backend-" + "upgrade",
        "backend-" + "upgrade-check",
        "med_deepscientist_" + "upgrade_check.py",
        "codex_cli_" + "autonomous",
        "legacy_oracle_" + "backend_audit",
    )
    violations: list[str] = []

    for root in search_roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for term in blocked_terms:
                if term in text:
                    violations.append(f"{path.relative_to(repo_root)}: {term}")

    assert violations == []


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
        module.DOCUMENTATION_REVIEW_CATEGORY,
    }
    doc_review = categories[module.DOCUMENTATION_REVIEW_CATEGORY]
    assert doc_review["category"] == module.DOCUMENTATION_REVIEW_CATEGORY
    assert doc_review["exact_paths"] == []
    assert doc_review["prefix_paths"] == ["docs/", "bootstrap/", "assets/branding/"]
    assert doc_review["root_file_patterns"] == ["README*.md"]
    assert doc_review["owner_surface"] == {
        "exact_paths": doc_review["exact_paths"],
        "prefix_paths": doc_review["prefix_paths"],
    }
    assert doc_review["fail_policy"] == "documentation_review_only_no_pytest"
    assert doc_review["commands"] == []
    assert doc_review["planned_commands"] == []
    assert doc_review["pytest_path_existence"] == []
    assert doc_review["planned_pytest_path_existence"] == []
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
        "documentation_paths": "review-only",
        "workflow_config_paths": "fail-closed",
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
    assert hygiene["unknown_documentation_paths"] == {
        "planned_commands": [],
        "fail_policy": "review-only",
        "suggestion": "Review documentation manually; no pytest command is planned for doc prose.",
    }
    assert hygiene["unknown_workflow_config_paths"] == {
        "planned_commands": [],
        "fail_policy": "fail-closed",
        "suggestion": "Add workflow/config paths to a reviewed owner surface before preflight can run commands.",
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
        "scripts/run-pytest-clean.sh tests/test_dev_preflight.py -q" in category["planned_commands"]
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
            "docs/references/example-runtime-note.md",
            "docs/runtime/example-runtime-contract.md",
            "src/med_autoscience/profiles.py",
            "profiles/workspace.profile.template.toml",
            "src/med_autoscience/controllers/study_outer_loop.py",
            "src/med_autoscience/controllers/study_runtime_decision.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/domain_status_projection.py",
            "src/med_autoscience/controllers/domain_health_diagnostic.py",
            "tests/test_profiles.py",
            "tests/test_opl_runtime_contract.py",
            "tests/test_runtime_protocol_layout.py",
            "tests/test_runtime_protocol_study_runtime.py",
            "tests/test_domain_health_diagnostic.py",
        ]
    )

    assert result.matched_categories == ("documentation_review_only", "runtime_contract_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_display_docs_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/delivery/example-capability-guide.md",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_branding_assets_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "assets/branding/medautoscience-overview.png",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_publication_route_memory_fixture_to_owner_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/policies/study-workflow/publication_route_memory_policy.md",
            "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_cards.py",
            "tests/test_stage_knowledge_plane.py",
        ]
    )

    assert result.matched_categories == (
        "documentation_review_only",
        "publication_route_memory_surface",
    )
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_stage_knowledge_plane.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_family_contract_adoption.py -q",
    ]


def test_classify_changed_files_flags_unclassified_paths() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/active/untracked_runtime_contract.md",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


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

    result = module.classify_changed_files(["docs/active/new_runtime_contract.md"])

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_audit_preflight_contract_coverage_identifies_explicit_classification() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        ["src/med_autoscience/controllers/domain_status_projection.py"],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="controller_sources",
                exact_paths=(),
                prefix_paths=("src/med_autoscience/controllers/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == (
        "src/med_autoscience/controllers/domain_status_projection.py",
    )
    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == ()
    assert audit.family_audits[0].explicit_categories == ("runtime_contract_surface",)
    assert audit.family_audits[0].explicit_classified_paths == (
        "src/med_autoscience/controllers/domain_status_projection.py",
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


def test_audit_preflight_contract_coverage_keeps_docs_review_only_and_workflow_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        [
            "docs/active/new_runtime_contract.md",
            ".github/workflows/new-release.yml",
            "tox.ini",
        ],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="program_docs",
                exact_paths=(),
                prefix_paths=("docs/active/",),
            ),
            module.PreflightCoveragePathFamily(
                family_id="workflow_config",
                exact_paths=("tox.ini",),
                prefix_paths=(".github/workflows/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == ("docs/active/new_runtime_contract.md",)
    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == (
        ".github/workflows/new-release.yml",
        "tox.ini",
    )
    assert audit.fail_closed_families == ("workflow_config",)


def test_classify_changed_files_matches_control_plane_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/stage_control_plane.json",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "src/med_autoscience/controllers/domain_authority_snapshot.py",
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/opl_provider_ready_adapter.py",
            "src/med_autoscience/controllers/owner_route_handoff.py",
            "src/med_autoscience/controllers/control_intent.py",
            "src/med_autoscience/controllers/control_identity.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/dataset_retention.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/control_plane_gate.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/managed_wakeup.py",
            "src/med_autoscience/controllers/study_progress_parts/projection.py",
            "src/med_autoscience/controllers/study_progress_parts/projection_quality_surfaces.py",
            "src/med_autoscience/controllers/study_progress_parts/projection_runtime_surfaces.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_orchestration.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_cli.py",
            "tests/test_autonomy_state_surface.py",
            "tests/test_artifact_lifecycle_inventory.py",
            "tests/test_artifact_lifecycle_operations_report.py",
            "tests/test_workspace_authority_migration_audit.py",
            "tests/test_cli_cases/owner_route_handoff_command.py",
        ]
    )

    assert result.matched_categories == (
        "control_plane_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_optional_provider_archive_audit_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/active/example-runtime-gate.md",
            "docs/references/example-workspace-note.md",
            "src/med_autoscience/workspace_contracts.py",
        ]
    )

    assert result.matched_categories == ("documentation_review_only", "optional_provider_archive_audit_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_public_docs_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "README.md",
            "README.zh-CN.md",
            "bootstrap/README.md",
            "docs/example.md",
            "docs/references/example-reference.md",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
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


def test_classify_changed_files_matches_packaging_workflow_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "MANIFEST.in",
            "setup.py",
            "tests/test_release_workflow.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_integration_harness_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/history/program/example-history-board.md",
            "docs/active/example-backend-map.md",
            "docs/references/example-phase-ladder.md",
            "scripts/prepare-sentrux-gitstats-clone.sh",
            "scripts/run-parallel-test-lanes.sh",
            "src/med_autoscience/controllers/workspace_init.py",
            "tests/test_workspace_init.py",
            "tests/test_sentrux_gitstats_helper.py",
        ]
    )

    assert result.matched_categories == ("documentation_review_only", "integration_harness_surface")
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
            "tests/fixtures/opl_agent_lab_longline.json",
            "tests/test_family_shared_release.py",
            "tests/test_opl_agent_lab_longline_migration.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface", "family_shared_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_root_governance_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "AGENTS.md",
            "agent/standard-domain-agent-anchor.json",
            "contracts/README.md",
            "contracts/test-lane-manifest.json",
            "contracts/runtime/legacy-active-path-tombstones.json",
            "contracts/runtime/standard-domain-agent-anchor.json",
            "contracts/modules/runtime/module_contract.yaml",
            "contracts/opl-framework/family-contract-adoption.json",
            "contracts/schemas/v1/product-entry-manifest.schema.json",
            "runtime/artifact_locator/workspace-runtime-artifact-root.locator.json",
            "tests/runtime/test_runtime_module_contract.py",
            "tests/test_opl_family_contract_adoption.py",
            "tests/test_opl_family_persistence_adapter.py",
            "tests/test_test_command_surfaces.py",
        ]
    )

    assert result.matched_categories == ("root_governance_contract_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_standard_agent_pack_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "agent/knowledge/medical_research_truth.md",
            "agent/knowledge/publication_route_memory.md",
            "agent/knowledge/source_readiness_and_artifact_authority.md",
            "agent/prompts/baseline_and_evidence_setup.md",
            "agent/prompts/bounded_analysis_campaign.md",
            "agent/prompts/direction_and_route_selection.md",
            "agent/prompts/finalize_and_publication_handoff.md",
            "agent/prompts/manuscript_authoring.md",
            "agent/prompts/review_and_quality_gate.md",
            "agent/quality_gates/ai_reviewer_auditor_gate.md",
            "agent/quality_gates/artifact_source_authority_gate.md",
            "agent/skills/medical_research_execution.md",
            "agent/skills/owner_receipt_and_route_control.md",
            "agent/stages/baseline_and_evidence_setup.policy.md",
            "agent/stages/bounded_analysis_campaign.policy.md",
            "agent/stages/direction_and_route_selection.policy.md",
            "agent/stages/finalize_and_publication_handoff.policy.md",
            "agent/stages/manuscript_authoring.policy.md",
            "agent/stages/review_and_quality_gate.policy.md",
            "contracts/action_catalog.json",
            "contracts/functional_privatization_audit.json",
            "contracts/generated_surface_handoff.json",
            "contracts/pack_compiler_input.json",
            "src/med_autoscience/overlay/templates/medical-research-baseline.SKILL.md",
            "src/med_autoscience/overlay/templates/medical-research-experiment.SKILL.md",
        ]
    )

    assert result.matched_categories == ("standard_agent_pack_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        (
            "scripts/run-pytest-clean.sh "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_test_lane_governance.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_product_entry.py -q",
    ]


def test_classify_changed_files_matches_production_acceptance_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/agent_lab_handoff.json",
            "contracts/production_acceptance/mas-production-acceptance.json",
            "tests/test_mas_production_acceptance.py",
            "tests/test_opl_standard_pack.py",
        ]
    )

    assert result.matched_categories == ("production_acceptance_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_mas_production_acceptance.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_standard_pack.py -q",
    ]


def test_classify_changed_files_matches_codex_plugin_skill_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(["plugins/mas/skills/mas/SKILL.md"])

    assert result.matched_categories == ("codex_plugin_surface",)
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


def test_classify_changed_sentrux_baseline_as_structure_quality_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            ".sentrux/baseline.json",
        ]
    )

    assert result.matched_categories == ("structure_quality_surface",)
    assert result.unclassified_changes == ()


def test_plan_commands_for_categories_deduplicates_results() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(
        ("workflow_surface", "workflow_surface", "codex_plugin_surface")
    )

    assert commands.count("scripts/run-pytest-clean.sh tests/test_release_workflow.py -q") == 1
    assert "scripts/run-pytest-clean.sh tests/test_codex_plugin.py -q" in commands


def test_plan_commands_for_documentation_review_only_do_not_run_pytest() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories((module.DOCUMENTATION_REVIEW_CATEGORY,))

    assert commands == []


def test_plan_commands_for_optional_provider_archive_audit_surface_include_gate_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("optional_provider_archive_audit_surface",))

    assert "scripts/run-pytest-clean.sh tests/test_med_deepscientist_repo_manifest.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_workspace_contracts.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_backend_audit.py -q" in commands


def test_plan_commands_for_integration_harness_surface_include_runtime_eval_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("integration_harness_surface",))

    assert "scripts/run-pytest-clean.sh tests/test_dev_preflight_contract.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_dev_preflight.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_workspace_init.py -q" in commands
    assert "make test-meta" in commands
    assert "scripts/run-pytest-clean.sh tests/test_work_unit_runtime_contract.py -q" not in commands
    assert "scripts/run-pytest-clean.sh tests/test_domain_health_diagnostic.py tests/test_study_delivery_sync.py tests/test_publication_gate.py -q" not in commands


def test_plan_commands_for_runtime_contract_surface_include_mas_runtime_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("runtime_contract_surface",))

    assert "scripts/run-pytest-clean.sh tests/test_opl_runtime_contract.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_profiles.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_runtime_protocol_layout.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_runtime_transport_hermes.py -q" not in commands
    assert "scripts/run-pytest-clean.sh tests/test_work_unit_runtime_contract.py -q" not in commands
    assert "make test-meta" in commands


def test_plan_commands_for_family_shared_surface_use_focused_family_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("family_shared_surface",))

    assert commands == ["make test-family"]


def test_plan_commands_for_structure_quality_surface_use_structure_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("structure_quality_surface",))

    assert commands == ["make test-structure"]


def test_plan_commands_for_root_governance_contract_surface_use_focused_contract_lanes() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("root_governance_contract_surface",))

    assert commands == [
        (
            "scripts/run-pytest-clean.sh "
            "tests/controller_charter/test_controller_charter_module_contract.py "
            "tests/runtime/test_runtime_module_contract.py "
            "tests/eval_hygiene/test_eval_hygiene_module_contract.py "
            "tests/integration/test_monorepo_scaffold_boundaries.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_opl_family_contract_adoption.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_family_persistence_adapter.py -q",
        "scripts/run-pytest-clean.sh tests/test_test_command_surfaces.py -q",
    ]


def test_plan_commands_for_control_plane_surface_use_focused_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("control_plane_surface",))

    assert commands == ["make test-control-plane"]
