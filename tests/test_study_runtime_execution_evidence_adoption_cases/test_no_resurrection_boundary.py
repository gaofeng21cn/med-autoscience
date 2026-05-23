from __future__ import annotations

import importlib
import inspect

import pytest


def test_execution_evidence_parts_remain_domain_authority_surfaces() -> None:
    for module_name in (
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization",
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization_receipts",
        "med_autoscience.controllers.study_runtime_execution_parts.work_unit_evidence_adoption",
    ):
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_retired_execution_and_transport_aggregates_do_not_return_as_aliases() -> None:
    retired_dispatch_parts = (
        "managed_runtime" + "_authorization",
        "managed_runtime" + "_dispatches",
    )
    for module_name in (
        "med_autoscience.controllers.study_runtime_execution",
        "med_autoscience.controllers.study_runtime_transport",
        "med_autoscience.controllers.owner_route_reconcile_parts.platform_repair",
        *(f"med_autoscience.controllers.domain_owner_action_dispatch_parts.{part}" for part in retired_dispatch_parts),
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_runtime_platform_repair_is_not_a_mas_owner_callable_or_dispatch_action() -> None:
    owner_route = importlib.import_module("med_autoscience.runtime_control.owner_route")
    registry = importlib.import_module("med_autoscience.runtime_control.owner_callable_registry")
    dispatcher = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    router = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch_parts.action_router")

    assert "runtime_platform_repair" not in owner_route.ALLOWED_ACTION_TYPES
    assert "runtime_platform_repair" not in owner_route.ROUTED_ACTION_TYPES
    assert registry.owner_callable_for_action("runtime_platform_repair") is None
    assert "runtime_platform_repair" not in dispatcher.SUPPORTED_ACTION_TYPES
    assert "runtime_platform_repair" not in inspect.getsource(router.execute_owner_dispatch_action)


def test_owner_route_reconcile_no_longer_accepts_runtime_repair_apply_flag() -> None:
    owner_route_reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    signature = inspect.signature(owner_route_reconcile.scan_domain_routes)

    assert "apply_runtime_platform_repair" not in signature.parameters


def test_retired_worker_cli_and_transport_aliases_do_not_return() -> None:
    cli_parser = importlib.import_module("med_autoscience.cli_parts.parser")
    domain_status_projection = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    figure_loop_guard = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    medical_publication_surface = importlib.import_module("med_autoscience.controllers.medical_publication_surface")

    help_text = cli_parser.build_parser(study_cycle_profiler=None).format_help()
    retired_worker_flag = "--" + "managed-runtime" + "-worker"
    retired_transport_attr = "managed_runtime" + "_transport"
    assert retired_worker_flag not in help_text
    assert not hasattr(domain_status_projection, retired_transport_attr)
    assert not hasattr(figure_loop_guard, retired_transport_attr)
    assert not hasattr(medical_publication_surface, retired_transport_attr)
