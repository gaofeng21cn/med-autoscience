from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import pytest


def test_execution_evidence_parts_remain_domain_authority_surfaces() -> None:
    for module_name in (
        "med_autoscience.controllers.study_runtime_execution.controller_authorization",
        "med_autoscience.controllers.study_runtime_execution.controller_authorization_receipts",
        "med_autoscience.controllers.study_runtime_execution.work_unit_evidence_adoption",
    ):
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_retired_execution_and_transport_aggregates_do_not_return_as_aliases() -> None:
    retired_dispatch_parts = (
        "managed_runtime" + "_authorization",
        "managed_runtime" + "_dispatches",
    )
    retired_runtime_module = "_".join(_legacy_runtime_repair_marker().split("_")[-2:])
    for module_name in (
        "med_autoscience.runtime_control.owner_callable_registry",
        "med_autoscience.controllers.study_runtime_transport",
        f"med_autoscience.controllers.paper_mission_owner_surface.{retired_runtime_module}",
        *(f"med_autoscience.controllers.stage_outcome_authority.{part}" for part in retired_dispatch_parts),
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_tombstoned_runtime_actions_are_not_mas_owner_callables_or_dispatch_actions() -> None:
    owner_route = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_policy")
    attempt_protocol = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy")
    registry = importlib.import_module("med_autoscience.controllers.owner_callable_registry")
    dispatcher = importlib.import_module("med_autoscience.controllers.stage_outcome_authority")
    router = importlib.import_module("med_autoscience.controllers.stage_outcome_authority.action_router")
    retired_action = _legacy_runtime_repair_marker()

    assert retired_action not in owner_route.ALLOWED_ACTION_TYPES
    assert retired_action not in owner_route.ROUTED_ACTION_TYPES
    for reason in (
        "abnormal_stopped_runtime_resume_required",
        "failed_quest_runtime_relaunch_required",
    ):
        contract = attempt_protocol.owner_reason_contract(reason=reason, owner="one-person-lab")
        assert contract["registered"] is True
        assert contract["owner"] == "one-person-lab"
        assert contract["allowed_actions"] == []
    retired_action_contract = attempt_protocol.owner_reason_contract(
        reason=retired_action,
        owner="one-person-lab",
    )
    assert retired_action_contract["registered"] is False
    assert retired_action_contract["allowed_actions"] == []
    assert registry.owner_callable_for_action(retired_action) is None
    assert not hasattr(dispatcher, "SUPPORTED_ACTION_TYPES")
    unsupported_execution = router.execute_owner_dispatch_action(
        profile=None,
        study_id="DM-RETIRE",
        action_type=retired_action,
        dispatch={},
        apply=False,
        execute_publication_gate_specificity=lambda **_: {},
        execute_ai_reviewer_workflow=lambda **_: {},
        quest_root_resolver=lambda *_: None,
    )
    assert unsupported_execution == {
        "execution_status": "blocked",
        "blocked_reason": "unsupported_action_type",
        "owner_callable_surface": None,
    }
    assert retired_action not in inspect.getsource(router.execute_owner_dispatch_action)


def test_paper_mission_owner_surface_no_longer_accepts_tombstoned_runtime_apply_flags() -> None:
    paper_mission_owner_surface = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
    signature = inspect.signature(paper_mission_owner_surface.scan_domain_routes)
    retired_apply_flag = f"apply_{_legacy_runtime_repair_marker()}"

    assert retired_apply_flag not in signature.parameters


def test_retired_worker_transport_aliases_do_not_return() -> None:
    domain_status_projection = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    figure_loop_guard = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    medical_publication_surface = importlib.import_module("med_autoscience.controllers.medical_publication_surface")

    retired_transport_attr = "managed_runtime" + "_transport"
    assert not hasattr(domain_status_projection, retired_transport_attr)
    assert not hasattr(figure_loop_guard, retired_transport_attr)
    assert not hasattr(medical_publication_surface, retired_transport_attr)


def _legacy_runtime_repair_marker() -> str:
    contract_path = Path(__file__).resolve().parents[2] / "contracts" / "runtime" / "legacy-active-path-tombstones.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    markers = contract["legacy_control_receipt_exclusion_policy"]["legacy_markers"]
    matches = [marker for marker in markers if marker.startswith("runtime_") and marker.endswith("_repair")]
    assert len(matches) == 1
    boundary = contract["legacy_control_receipt_exclusion_policy"]["authority_boundary"]
    assert boundary == {
        "read_only": True,
        "history_provenance_only": True,
        "can_create_runtime_entrypoint": False,
        "can_claim_generic_runtime_owner": False,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
    }
    return matches[0]
