from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
from typing import Iterable, Sequence

from .category_specs import build_category_specs


PYTEST_CLEAN_RUNNER = "scripts/run-pytest-clean.sh"
PYTHON_CLEAN_RUNNER = "scripts/run-python-clean.sh"
BUILD_CLEAN_RUNNER = "scripts/run-build-clean.sh"


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


@dataclass(frozen=True)
class PreflightCoveragePathFamily:
    family_id: str
    exact_paths: tuple[str, ...]
    prefix_paths: tuple[str, ...]


@dataclass(frozen=True)
class PreflightCoverageFamilyAudit:
    family_id: str
    explicit_categories: tuple[str, ...]
    explicit_classified_paths: tuple[str, ...]
    generic_python_regression_paths: tuple[str, ...]
    fail_closed_paths: tuple[str, ...]


@dataclass(frozen=True)
class PreflightCoverageAudit:
    family_audits: tuple[PreflightCoverageFamilyAudit, ...]
    explicit_classified_paths: tuple[str, ...]
    generic_python_regression_paths: tuple[str, ...]
    fail_closed_paths: tuple[str, ...]
    generic_python_regression_families: tuple[str, ...]
    fail_closed_families: tuple[str, ...]


GENERIC_PYTHON_SMOKE_CATEGORY = "generic_python_smoke_surface"
GENERIC_PYTHON_REGRESSION_CATEGORY = GENERIC_PYTHON_SMOKE_CATEGORY
DOCUMENTATION_REVIEW_CATEGORY = "documentation_review_only"

_DOC_ONLY_PREFIX_PATHS = ("docs/", "bootstrap/", "assets/branding/")
_DOC_ONLY_ROOT_FILE_PATTERNS = ("README*.md",)


_CATEGORY_SPECS = build_category_specs(
    PreflightCategorySpec,
    pytest_clean_runner=PYTEST_CLEAN_RUNNER,
    build_clean_runner=BUILD_CLEAN_RUNNER,
)


_GENERIC_PYTHON_PREFIXES = (
    "src/med_autoscience/",
    "tests/",
)

_GENERIC_PYTHON_SMOKE_COMMANDS = (
    "make test-smoke",
)
_GENERIC_PYTHON_REGRESSION_COMMANDS = _GENERIC_PYTHON_SMOKE_COMMANDS

_MATCHED_CATEGORY_FAIL_POLICY = "matched_paths_run_planned_commands"
_GENERIC_PYTHON_SMOKE_FAIL_POLICY = "unknown_python_and_test_paths_route_to_smoke"
_GENERIC_PYTHON_FAIL_POLICY = _GENERIC_PYTHON_SMOKE_FAIL_POLICY
_UNKNOWN_PATH_POLICY = {
    "python_and_test_paths": "smoke",
    "documentation_paths": "review-only",
    "workflow_config_paths": "fail-closed",
}
_UNKNOWN_DOCUMENTATION_SUGGESTION = (
    "Review documentation manually; no pytest command is planned for doc prose."
)
_UNKNOWN_WORKFLOW_CONFIG_SUGGESTION = (
    "Add workflow/config paths to a reviewed owner surface before preflight can run commands."
)

_DEFAULT_COVERAGE_PATH_FAMILIES: tuple[PreflightCoveragePathFamily, ...] = (
    PreflightCoveragePathFamily(
        family_id="source_root",
        exact_paths=(),
        prefix_paths=("src/med_autoscience/",),
    ),
    PreflightCoveragePathFamily(
        family_id="test_root",
        exact_paths=(),
        prefix_paths=("tests/",),
    ),
    PreflightCoveragePathFamily(
        family_id="runtime_docs",
        exact_paths=(),
        prefix_paths=("docs/runtime/",),
    ),
    PreflightCoveragePathFamily(
        family_id="program_docs",
        exact_paths=(),
        prefix_paths=("docs/active/",),
    ),
    PreflightCoveragePathFamily(
        family_id="policy_docs",
        exact_paths=(),
        prefix_paths=("docs/policies/",),
    ),
    PreflightCoveragePathFamily(
        family_id="reference_docs",
        exact_paths=(),
        prefix_paths=("docs/references/",),
    ),
    PreflightCoveragePathFamily(
        family_id="history_docs",
        exact_paths=(),
        prefix_paths=("docs/history/",),
    ),
    PreflightCoveragePathFamily(
        family_id="capability_docs",
        exact_paths=(),
        prefix_paths=("docs/delivery/",),
    ),
    PreflightCoveragePathFamily(
        family_id="agent_root",
        exact_paths=(),
        prefix_paths=("agent/",),
    ),
    PreflightCoveragePathFamily(
        family_id="contract_root",
        exact_paths=("contracts/README.md",),
        prefix_paths=(
            "contracts/modules/",
            "contracts/opl-framework/",
            "contracts/runtime/",
            "contracts/schemas/",
        ),
    ),
    PreflightCoveragePathFamily(
        family_id="runtime_artifact_locator_root",
        exact_paths=(),
        prefix_paths=("runtime/artifact_locator/",),
    ),
    PreflightCoveragePathFamily(
        family_id="workflow_config",
        exact_paths=(
            ".sentrux/baseline.json",
            ".sentrux/rules.toml",
            "Makefile",
            "pyproject.toml",
            "uv.lock",
        ),
        prefix_paths=(
            ".github/workflows/",
            "scripts/",
        ),
    ),
)


def _normalize_changed_file(path: str) -> str:
    return path.strip().replace("\\", "/").removeprefix("./")


def _matches_spec(*, normalized_path: str, spec: PreflightCategorySpec) -> bool:
    if normalized_path in spec.exact_paths:
        return True
    return any(normalized_path.startswith(prefix) for prefix in spec.prefix_paths)


def _matches_path_family(*, normalized_path: str, family: PreflightCoveragePathFamily) -> bool:
    if normalized_path in family.exact_paths:
        return True
    return any(normalized_path.startswith(prefix) for prefix in family.prefix_paths)


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
        if not matched_here and is_generic_python_change(normalized_path):
            matched_here = True
            if GENERIC_PYTHON_REGRESSION_CATEGORY not in matched_categories:
                matched_categories.append(GENERIC_PYTHON_REGRESSION_CATEGORY)
        if not matched_here and is_documentation_review_only_change(normalized_path):
            matched_here = True
            if DOCUMENTATION_REVIEW_CATEGORY not in matched_categories:
                matched_categories.append(DOCUMENTATION_REVIEW_CATEGORY)
        if not matched_here and normalized_path not in unclassified_changes:
            unclassified_changes.append(normalized_path)

    return ClassificationResult(
        matched_categories=tuple(matched_categories),
        unclassified_changes=tuple(unclassified_changes),
    )


def is_generic_python_change(path: str) -> bool:
    normalized_path = _normalize_changed_file(path)
    return normalized_path.endswith(".py") and normalized_path.startswith(_GENERIC_PYTHON_PREFIXES)


def is_documentation_review_only_change(path: str) -> bool:
    normalized_path = _normalize_changed_file(path)
    if "/" not in normalized_path and normalized_path.startswith("README") and normalized_path.endswith(".md"):
        return True
    if normalized_path.startswith("assets/branding/"):
        return True
    return normalized_path.startswith(_DOC_ONLY_PREFIX_PATHS) and normalized_path.endswith(".md")


def _explicit_categories_for_path(normalized_path: str) -> tuple[str, ...]:
    categories = [
        spec.category_id
        for spec in _CATEGORY_SPECS
        if _matches_spec(normalized_path=normalized_path, spec=spec)
    ]
    if not categories and is_documentation_review_only_change(normalized_path):
        categories.append(DOCUMENTATION_REVIEW_CATEGORY)
    return tuple(categories)


def _append_unique(values: list[str], candidates: Iterable[str]) -> None:
    for candidate in candidates:
        if candidate not in values:
            values.append(candidate)


def audit_preflight_contract_coverage(
    repo_tracked_paths: Sequence[str],
    *,
    path_families: Sequence[PreflightCoveragePathFamily] = _DEFAULT_COVERAGE_PATH_FAMILIES,
) -> PreflightCoverageAudit:
    normalized_paths = tuple(
        normalized_path
        for path in repo_tracked_paths
        if (normalized_path := _normalize_changed_file(str(path)))
    )
    family_audits: list[PreflightCoverageFamilyAudit] = []
    all_explicit_classified_paths: list[str] = []
    all_generic_python_regression_paths: list[str] = []
    all_fail_closed_paths: list[str] = []
    generic_python_regression_families: list[str] = []
    fail_closed_families: list[str] = []

    for family in path_families:
        family_paths = tuple(
            path for path in normalized_paths if _matches_path_family(normalized_path=path, family=family)
        )
        explicit_categories: list[str] = []
        explicit_classified_paths: list[str] = []
        generic_python_regression_paths: list[str] = []
        fail_closed_paths: list[str] = []

        for path in family_paths:
            categories = _explicit_categories_for_path(path)
            if categories:
                _append_unique(explicit_categories, categories)
                explicit_classified_paths.append(path)
            elif is_generic_python_change(path):
                generic_python_regression_paths.append(path)
            elif is_documentation_review_only_change(path):
                _append_unique(explicit_categories, (DOCUMENTATION_REVIEW_CATEGORY,))
                explicit_classified_paths.append(path)
            else:
                fail_closed_paths.append(path)

        if generic_python_regression_paths:
            generic_python_regression_families.append(family.family_id)
        if fail_closed_paths:
            fail_closed_families.append(family.family_id)
        _append_unique(all_explicit_classified_paths, explicit_classified_paths)
        _append_unique(all_generic_python_regression_paths, generic_python_regression_paths)
        _append_unique(all_fail_closed_paths, fail_closed_paths)
        family_audits.append(
            PreflightCoverageFamilyAudit(
                family_id=family.family_id,
                explicit_categories=tuple(explicit_categories),
                explicit_classified_paths=tuple(explicit_classified_paths),
                generic_python_regression_paths=tuple(generic_python_regression_paths),
                fail_closed_paths=tuple(fail_closed_paths),
            )
        )

    return PreflightCoverageAudit(
        family_audits=tuple(family_audits),
        explicit_classified_paths=tuple(all_explicit_classified_paths),
        generic_python_regression_paths=tuple(all_generic_python_regression_paths),
        fail_closed_paths=tuple(all_fail_closed_paths),
        generic_python_regression_families=tuple(generic_python_regression_families),
        fail_closed_families=tuple(fail_closed_families),
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
    if GENERIC_PYTHON_REGRESSION_CATEGORY in selected_categories:
        for command in _GENERIC_PYTHON_REGRESSION_COMMANDS:
            if command not in planned_commands:
                planned_commands.append(command)
    return planned_commands


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return here.parents[3]


def _planned_pytest_paths(command: str) -> tuple[str, ...]:
    parts = shlex.split(command)
    if not parts:
        return ()
    if parts[:1] == [PYTEST_CLEAN_RUNNER]:
        return tuple(part for part in parts[1:] if part.startswith("tests/"))
    if len(parts) < 3 or parts[:3] != ["uv", "run", "pytest"]:
        return ()
    return tuple(part for part in parts[3:] if part.startswith("tests/"))


def _planned_pytest_path_existence(commands: Sequence[str]) -> list[dict[str, object]]:
    repo_root = _repo_root()
    return [
        {
            "command": command,
            "path": path,
            "exists": (repo_root / path).exists(),
        }
        for command in commands
        for path in _planned_pytest_paths(command)
    ]


def _missing_planned_pytest_paths(categories: Sequence[dict[str, object]]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for category in categories:
        for status in category["planned_pytest_path_existence"]:
            if status["exists"] is True:
                continue
            missing.append(
                {
                    "category": str(category["category"]),
                    "command": str(status["command"]),
                    "path": str(status["path"]),
                }
            )
    return missing


def _owner_surface(*, exact_paths: Sequence[str], prefix_paths: Sequence[str]) -> dict[str, object]:
    return {
        "exact_paths": list(exact_paths),
        "prefix_paths": list(prefix_paths),
    }


def _unknown_path_suggestions_for_category(spec: PreflightCategorySpec) -> list[str]:
    suggestions = [
        f"Review unknown docs paths manually. {_UNKNOWN_DOCUMENTATION_SUGGESTION}",
    ]
    if any(path.startswith("tests/") for path in (*spec.exact_paths, *spec.prefix_paths)):
        suggestions.append(
            "Unknown tests/*.py paths route to generic_python_smoke_surface unless added to an owner surface."
        )
    if any(path.startswith("src/med_autoscience/") for path in (*spec.exact_paths, *spec.prefix_paths)):
        suggestions.append(
            "Unknown src/med_autoscience/*.py paths route to generic_python_smoke_surface unless added to an owner surface."
        )
    return suggestions


def _contract_hygiene(categories: Sequence[dict[str, object]]) -> dict[str, object]:
    missing_pytest_paths = _missing_planned_pytest_paths(categories)
    return {
        "planned_pytest_paths_exist": not missing_pytest_paths,
        "missing_planned_pytest_paths": missing_pytest_paths,
        "unknown_python_and_test_paths": {
            "category": GENERIC_PYTHON_REGRESSION_CATEGORY,
            "planned_commands": list(_GENERIC_PYTHON_REGRESSION_COMMANDS),
            "fail_policy": _GENERIC_PYTHON_FAIL_POLICY,
        },
        "unknown_documentation_paths": {
            "planned_commands": [],
            "fail_policy": "review-only",
            "suggestion": _UNKNOWN_DOCUMENTATION_SUGGESTION,
        },
        "unknown_workflow_config_paths": {
            "planned_commands": [],
            "fail_policy": "fail-closed",
            "suggestion": _UNKNOWN_WORKFLOW_CONFIG_SUGGESTION,
        },
    }


def build_preflight_contract_report() -> dict[str, object]:
    categories: list[dict[str, object]] = []
    for spec in _CATEGORY_SPECS:
        commands = list(spec.commands)
        owner_surface = _owner_surface(exact_paths=spec.exact_paths, prefix_paths=spec.prefix_paths)
        pytest_path_existence = _planned_pytest_path_existence(commands)
        unknown_path_suggestions = _unknown_path_suggestions_for_category(spec)
        categories.append(
            {
                "category": spec.category_id,
                "category_id": spec.category_id,
                "exact_paths": list(spec.exact_paths),
                "prefix_paths": list(spec.prefix_paths),
                "owner_surface": owner_surface,
                "fail_policy": _MATCHED_CATEGORY_FAIL_POLICY,
                "commands": commands,
                "planned_commands": commands,
                "pytest_path_existence": pytest_path_existence,
                "planned_pytest_path_existence": pytest_path_existence,
                "unknown_path_suggestion": unknown_path_suggestions[0],
                "unknown_path_suggestions": unknown_path_suggestions,
            }
        )
    generic_commands = list(_GENERIC_PYTHON_REGRESSION_COMMANDS)
    generic_unknown_path_suggestions = [
        "Unknown src/med_autoscience/*.py paths route to generic_python_smoke_surface and run make test-smoke.",
        "Unknown tests/*.py paths route to generic_python_smoke_surface and run make test-smoke.",
        f"Unknown docs paths are review-only. {_UNKNOWN_DOCUMENTATION_SUGGESTION}",
        f"Unknown workflow/config paths remain fail-closed. {_UNKNOWN_WORKFLOW_CONFIG_SUGGESTION}",
    ]
    generic_pytest_path_existence = _planned_pytest_path_existence(generic_commands)
    categories.append(
        {
            "category": GENERIC_PYTHON_REGRESSION_CATEGORY,
            "category_id": GENERIC_PYTHON_REGRESSION_CATEGORY,
            "exact_paths": [],
            "prefix_paths": list(_GENERIC_PYTHON_PREFIXES),
            "owner_surface": _owner_surface(exact_paths=(), prefix_paths=_GENERIC_PYTHON_PREFIXES),
            "fail_policy": _GENERIC_PYTHON_FAIL_POLICY,
            "commands": generic_commands,
            "planned_commands": generic_commands,
            "pytest_path_existence": generic_pytest_path_existence,
            "planned_pytest_path_existence": generic_pytest_path_existence,
            "unknown_path_suggestion": generic_unknown_path_suggestions[0],
            "unknown_path_suggestions": generic_unknown_path_suggestions,
        }
    )
    documentation_commands: list[str] = []
    categories.append(
        {
            "category": DOCUMENTATION_REVIEW_CATEGORY,
            "category_id": DOCUMENTATION_REVIEW_CATEGORY,
            "exact_paths": [],
            "prefix_paths": list(_DOC_ONLY_PREFIX_PATHS),
            "root_file_patterns": list(_DOC_ONLY_ROOT_FILE_PATTERNS),
            "owner_surface": _owner_surface(
                exact_paths=(),
                prefix_paths=_DOC_ONLY_PREFIX_PATHS,
            ),
            "fail_policy": "documentation_review_only_no_pytest",
            "commands": documentation_commands,
            "planned_commands": documentation_commands,
            "pytest_path_existence": [],
            "planned_pytest_path_existence": [],
            "unknown_path_suggestion": _UNKNOWN_DOCUMENTATION_SUGGESTION,
            "unknown_path_suggestions": [_UNKNOWN_DOCUMENTATION_SUGGESTION],
        }
    )
    return {
        "surface_kind": "preflight_contract_report",
        "unknown_path_policy": dict(_UNKNOWN_PATH_POLICY),
        "contract_hygiene": _contract_hygiene(categories),
        "categories": categories,
        "fail_closed_families": [
            {
                "family_id": family.family_id,
                "exact_paths": list(family.exact_paths),
                "prefix_paths": list(family.prefix_paths),
            }
            for family in _DEFAULT_COVERAGE_PATH_FAMILIES
        ],
    }
