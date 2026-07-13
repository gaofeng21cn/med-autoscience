from __future__ import annotations

import importlib
import json
from pathlib import Path
import shlex

import pytest

pytestmark = pytest.mark.family


def _planned_pytest_paths(command: str) -> tuple[str, ...]:
    parts = shlex.split(command)
    if parts[:2] == ["make", "test-paths"]:
        return tuple(part for part in parts[2:] if part.startswith("tests/"))
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
        "kernel_authorized_" + "provider_attempt",
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
