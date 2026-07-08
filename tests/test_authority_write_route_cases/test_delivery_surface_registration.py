from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

WRITE_ROUTE_SURFACES = (
    (
        REPO_ROOT / "src/med_autoscience/controllers/submission_minimal/package_builder.py",
        "create_submission_minimal_package",
        "submission_materialize",
    ),
    (
        REPO_ROOT / "src/med_autoscience/controllers/study_delivery_sync/sync_orchestration.py",
        "sync_study_delivery",
        "delivery_sync",
    ),
    (
        REPO_ROOT / "src/med_autoscience/controllers/study_delivery_sync/submission_delivery_descriptions.py",
        "materialize_submission_delivery_stale_notice",
        "submission_notice_materialize",
    ),
    (
        REPO_ROOT / "src/med_autoscience/controllers/journal_package.py",
        "materialize_journal_package",
        "bundle_build",
    ),
)

ROUTE_CONTEXT_REPLAY_SURFACES = (
    (
        REPO_ROOT / "src/med_autoscience/controllers/submission_minimal/post_materialization_sync.py",
        "replay_post_submission_minimal_sync",
    ),
)

LOWER_LEVEL_DELIVERY_HELPERS = {
    "sync_draft_handoff_delivery",
    "sync_general_delivery",
    "sync_journal_specific_delivery",
    "sync_promoted_journal_delivery",
}
LOWER_LEVEL_DELIVERY_HELPER_SURFACES = (
    REPO_ROOT / "src/med_autoscience/controllers/study_delivery_sync/delivery_stage_sync.py",
    REPO_ROOT / "src/med_autoscience/controllers/study_delivery_sync/promoted_journal_delivery.py",
)

MUTATING_ENTRY_PREFIXES = ("create_", "materialize_", "replay_", "sync_")


def _function_node(path: Path, name: str) -> ast.FunctionDef:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} not found in {path}")


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        function = child.func
        if isinstance(function, ast.Name):
            names.add(function.id)
        elif isinstance(function, ast.Attribute):
            names.add(function.attr)
    return names


def _literal_keyword_values(node: ast.AST, *, function_name: str, keyword_name: str) -> set[str]:
    values: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        function = child.func
        called = (
            function.id
            if isinstance(function, ast.Name)
            else function.attr
            if isinstance(function, ast.Attribute)
            else ""
        )
        if called != function_name:
            continue
        for keyword in child.keywords:
            if (
                keyword.arg == keyword_name
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                values.add(keyword.value.value)
    return values


def _function_parameters(node: ast.FunctionDef) -> set[str]:
    return {
        argument.arg
        for argument in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
    }


def _public_mutating_entry_names(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and not node.name.startswith("_")
        and node.name.startswith(MUTATING_ENTRY_PREFIXES)
    }


def test_mutating_delivery_write_surfaces_are_registered_behind_authority_write_route() -> None:
    for path, function_name, route_action in WRITE_ROUTE_SURFACES:
        node = _function_node(path, function_name)
        called_names = _called_names(node)

        assert "authority_route_context" in _function_parameters(node)
        assert "route_context" in _function_parameters(node)
        assert "resolve_authority_write_route_context" in called_names
        assert "blocked_authority_write_payload" in called_names
        assert route_action in _literal_keyword_values(
            node,
            function_name="resolve_authority_write_route_context",
            keyword_name="action",
        )


def test_new_public_mutating_delivery_entries_must_be_explicitly_registered() -> None:
    registered_route_entries = {function_name for _path, function_name, _route_action in WRITE_ROUTE_SURFACES}
    registered_route_replays = {function_name for _path, function_name in ROUTE_CONTEXT_REPLAY_SURFACES}
    expected_public_entries = registered_route_entries | registered_route_replays | LOWER_LEVEL_DELIVERY_HELPERS
    actual_public_entries: set[str] = set()
    for path in {
        *(path for path, _function_name, _route_action in WRITE_ROUTE_SURFACES),
        *(path for path, _function_name in ROUTE_CONTEXT_REPLAY_SURFACES),
        *LOWER_LEVEL_DELIVERY_HELPER_SURFACES,
    }:
        actual_public_entries.update(_public_mutating_entry_names(path))

    assert actual_public_entries == expected_public_entries


def test_open_auto_research_projection_exposes_no_public_write_or_replay_authority() -> None:
    path = REPO_ROOT / "src/med_autoscience/controllers/open_auto_research_projection.py"

    assert _public_mutating_entry_names(path) == set()


def test_submission_minimal_post_materialization_replays_preserve_route_context() -> None:
    for path, function_name in ROUTE_CONTEXT_REPLAY_SURFACES:
        node = _function_node(path, function_name)

        assert "authority_route_context" in _function_parameters(node)
        assert "route_context" in _function_parameters(node)

        route_context_keywords = [
            keyword.value.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            for keyword in child.keywords
            if keyword.arg == "authority_route_context" and isinstance(keyword.value, ast.Name)
        ]
        assert route_context_keywords
        assert set(route_context_keywords) == {"resolved_route_context"}
