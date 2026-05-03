from __future__ import annotations

import inspect
from pathlib import Path
import fnmatch
from typing import Any, Callable

import pytest

from tests.control_plane_route_helpers import writable_route_context


REPO_ROOT = Path(__file__).resolve().parents[1]

NESTED_CASE_COLLECTION_IGNORE_GLOBS = (
    "product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_*.py",
    "test_runtime_watch_cases/*_cases_cases/test_*.py",
)

collect_ignore_glob = list(NESTED_CASE_COLLECTION_IGNORE_GLOBS)

META_FILES = {
    "tests/controller_charter/test_controller_charter_module_contract.py",
    "tests/eval_hygiene/test_eval_hygiene_module_contract.py",
    "tests/integration/test_monorepo_scaffold_boundaries.py",
    "tests/runtime/test_runtime_module_contract.py",
    "tests/test_agent_entry_assets.py",
    "tests/test_codex_plugin.py",
    "tests/test_codex_plugin_installer.py",
    "tests/test_codex_plugin_installer_script.py",
    "tests/test_codex_plugin_scaffold.py",
    "tests/test_dev_preflight.py",
    "tests/test_dev_preflight_contract.py",
    "tests/test_med_deepscientist_repo_manifest.py",
    "tests/test_python_environment_contract.py",
    "tests/test_release_installer.py",
    "tests/test_release_metadata.py",
    "tests/test_release_workflow.py",
    "tests/test_workspace_contracts.py",
}

DISPLAY_HEAVY_FILES = {
    "tests/test_display_ab_golden_regression.py",
    "tests/test_display_abh_golden_regression.py",
    "tests/test_display_ch_golden_regression.py",
    "tests/test_display_deg_golden_regression.py",
    "tests/test_display_f_golden_regression.py",
    "tests/test_display_layout_qc.py",
    "tests/test_display_surface_materialization.py",
    "tests/test_display_surface_materialization_cli.py",
    "tests/test_medical_startup_contract_support.py",
    "tests/test_submission_minimal_display_surface.py",
}

FAMILY_FILES = {
    "tests/test_editable_shared_bootstrap.py",
    "tests/test_family_shared_release.py",
}

WRITE_ROUTE_LEGACY_DEFAULT_FILES = {
    "tests/test_submission_minimal.py",
    "tests/test_study_delivery_sync.py",
    "tests/test_journal_package_controller.py",
    "tests/test_publication_gate.py",
    "tests/test_quality_repair_batch.py",
    "tests/test_gate_clearing_batch.py",
    "tests/test_fast_lane_executor.py",
    "tests/test_artifact_lifecycle_inventory.py",
}

WRITE_ROUTE_LEGACY_DEFAULT_PREFIXES = (
    "tests/submission_minimal_cases/",
    "tests/test_study_delivery_sync_cases/",
    "tests/test_publication_gate_cases/",
    "tests/test_gate_clearing_batch_cases/",
)


def _relative_test_path(item: pytest.Item) -> str:
    path = Path(str(item.fspath)).resolve()
    return path.relative_to(REPO_ROOT).as_posix()


def _is_nested_case_collection_path(relative_test_path: str) -> bool:
    relative_to_tests = relative_test_path.removeprefix("tests/")
    return any(fnmatch.fnmatch(relative_to_tests, pattern) for pattern in NESTED_CASE_COLLECTION_IGNORE_GLOBS)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "write_route_legacy_default: legacy focused write tests that inject explicit control-plane route authority",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    nested_case_items = [item for item in items if _is_nested_case_collection_path(_relative_test_path(item))]
    if nested_case_items:
        items[:] = [item for item in items if item not in nested_case_items]
    for item in items:
        relative_path = _relative_test_path(item)
        if relative_path in META_FILES:
            item.add_marker(pytest.mark.meta)
        if relative_path in DISPLAY_HEAVY_FILES:
            item.add_marker(pytest.mark.display_heavy)
        if relative_path in FAMILY_FILES:
            item.add_marker(pytest.mark.family)
        if relative_path in WRITE_ROUTE_LEGACY_DEFAULT_FILES or relative_path.startswith(
            WRITE_ROUTE_LEGACY_DEFAULT_PREFIXES
        ):
            item.add_marker(pytest.mark.write_route_legacy_default)


@pytest.fixture
def writable_control_plane_route_context() -> dict[str, object]:
    return writable_route_context()


@pytest.fixture(autouse=True)
def _inject_legacy_write_route_context(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if request.node.get_closest_marker("write_route_legacy_default") is None:
        return
    if "test_control_plane_write_route_authority.py" in _relative_test_path(request.node):
        return
    route_context = writable_route_context()

    def _wrap(function: Callable[..., Any]) -> Callable[..., Any]:
        signature = inspect.signature(function)

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if kwargs.get("control_plane_route_context") is None and kwargs.get("route_context") is None:
                if "control_plane_route_context" in signature.parameters:
                    kwargs["control_plane_route_context"] = route_context
                elif "route_context" in signature.parameters:
                    kwargs["route_context"] = route_context
            return function(*args, **kwargs)

        return wrapped

    for module_name, function_names in {
        "med_autoscience.controllers.submission_minimal": ("create_submission_minimal_package",),
        "med_autoscience.controllers.study_delivery_sync": ("sync_study_delivery",),
        "med_autoscience.controllers.journal_package": ("materialize_journal_package",),
        "med_autoscience.controllers.publication_gate": ("run_controller",),
        "med_autoscience.controllers.publication_gate_parts.supervisor_and_cli": ("run_controller",),
        "med_autoscience.controllers.quality_repair_batch": ("run_quality_repair_batch",),
        "med_autoscience.controllers.gate_clearing_batch": ("run_gate_clearing_batch",),
        "med_autoscience.controllers.fast_lane_executor": ("build_fast_lane_execution_manifest",),
    }.items():
        try:
            module = __import__(module_name, fromlist=["_"])
        except ImportError:
            continue
        for function_name in function_names:
            function = getattr(module, function_name, None)
            if callable(function):
                monkeypatch.setattr(module, function_name, _wrap(function))
