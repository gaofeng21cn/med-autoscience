from __future__ import annotations

import importlib
import json
from pathlib import Path
import shlex

import pytest

from tests.dev_preflight_contract_cases.plan_commands import (
    test_plan_commands_for_categories_deduplicates_results,
    test_plan_commands_for_documentation_review_only_do_not_run_pytest,
    test_plan_commands_for_optional_provider_archive_audit_surface_include_gate_proofs,
    test_plan_commands_for_integration_harness_surface_include_runtime_eval_proofs,
    test_plan_commands_for_runtime_contract_surface_include_mas_runtime_proofs,
    test_plan_commands_for_family_shared_surface_use_focused_family_lane,
    test_plan_commands_for_structure_quality_surface_use_structure_lane,
    test_plan_commands_for_root_governance_contract_surface_use_focused_contract_lanes,
    test_plan_commands_for_control_plane_surface_use_focused_lane,
)

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
        repo_root / "profiles",
    ]
    blocked_terms = (
        "backend-" + "upgrade",
        "backend-" + "upgrade-check",
        "med_deepscientist_" + "upgrade_check.py",
        "codex_cli_" + "autonomous",
        "legacy_oracle_" + "backend_audit",
        "paper_autonomy_" + "supervisor_apply",
        "paper_progress_" + "transition_kernel",
        "single_transition_" + "authority",
        "kernel_authorized_" + "provider_admission",
        "mas_opl_paper_" + "autonomy_supervisor_apply",
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
    assert generic["fail_policy"] == "unknown_python_and_test_paths_route_to_smoke"
    assert generic["planned_commands"] == ["make test-smoke"]
    assert "make test-smoke" in generic["unknown_path_suggestion"]
    assert any("src/med_autoscience/" in suggestion for suggestion in generic["unknown_path_suggestions"])
    assert any("tests/" in suggestion for suggestion in generic["unknown_path_suggestions"])
    assert report["unknown_path_policy"] == {
        "python_and_test_paths": "smoke",
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
        "planned_commands": ["make test-smoke"],
        "fail_policy": "unknown_python_and_test_paths_route_to_smoke",
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


from tests.dev_preflight_contract_cases.classification_and_surface_cases import (
    test_preflight_category_audit_keeps_spec_paths_explicit,
    test_classify_changed_files_matches_runtime_contract_surface,
    test_classify_changed_files_routes_display_docs_to_review_only,
    test_classify_changed_files_routes_branding_assets_to_review_only,
    test_classify_changed_files_routes_publication_route_memory_fixture_to_owner_surface,
    test_classify_changed_files_routes_mcp_plugin_config_to_codex_plugin_surface,
    test_classify_changed_files_flags_unclassified_paths,
    test_classify_changed_files_routes_unknown_python_to_generic_smoke,
    test_classify_changed_files_keeps_unknown_docs_fail_closed,
    test_audit_preflight_contract_coverage_identifies_explicit_classification,
    test_audit_preflight_contract_coverage_marks_generic_python_fallback,
    test_audit_preflight_contract_coverage_keeps_docs_review_only_and_workflow_fail_closed,
    test_classify_changed_files_matches_control_plane_surface,
    test_classify_changed_files_matches_cli_parser_surface,
    test_classify_changed_files_matches_owner_answer_candidate_intake_surface,
    test_classify_changed_files_matches_study_owner_gate_decision_surface,
    test_classify_changed_files_matches_paper_progress_transition_boundary_surface,
    test_classify_changed_files_matches_optional_provider_archive_audit_surface,
    test_classify_changed_files_routes_public_docs_to_review_only,
    test_classify_changed_files_matches_ci_workflow_surface,
    test_classify_changed_files_matches_packaging_workflow_surface,
    test_classify_changed_files_matches_integration_harness_surface,
    test_classify_changed_files_matches_family_shared_surface,
    test_classify_changed_files_matches_root_governance_contract_surface,
    test_classify_changed_files_matches_standard_agent_pack_surface,
    test_classify_changed_files_matches_external_learning_sidecar_surface,
    test_classify_changed_files_matches_evo_scientist_progress_accelerator_surface,
    test_classify_changed_files_matches_data_asset_display_and_overlay_contracts,
    test_classify_changed_files_matches_stage_kernel_pack_contract_surface,
    test_classify_changed_files_matches_domain_action_materializer_surface,
    test_classify_changed_files_matches_paper_autonomy_supervisor_surface,
    test_classify_changed_files_matches_production_acceptance_surface,
    test_classify_changed_files_matches_codex_plugin_skill_surface,
    test_classify_changed_clean_runner_scripts_as_family_shared_surface,
    test_classify_changed_sentrux_baseline_as_structure_quality_surface,
)
