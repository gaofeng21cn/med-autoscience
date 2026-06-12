from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any


REQUIRED_KEYS = {
    "surface_kind",
    "schema_version",
    "status",
    "study_id",
    "quest_id",
    "stage_id",
    "owner",
    "action_type",
    "work_unit_id",
    "work_unit_fingerprint",
    "action_fingerprint",
    "input_refs",
    "required_output_contract",
    "acceptance_refs",
    "state",
    "currentness_basis",
    "authority_boundary",
}


def _module():
    return importlib.import_module("med_autoscience.controllers.current_work_unit")


def _assert_contract_shape(work_unit: Mapping[str, Any]) -> None:
    assert set(work_unit) == REQUIRED_KEYS
    assert work_unit["surface_kind"] == "current_work_unit"
    assert work_unit["schema_version"] == 1
    assert work_unit["status"] in {
        "executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "blocked_current_work_unit",
    }
    assert work_unit["authority_boundary"]["top_level_truth"] == "status"
    assert work_unit["authority_boundary"]["mas_owner_authority_preserved"] is True
    assert work_unit["authority_boundary"]["stage_transition_authority"] == "OPL Stage Transition Authority"
    assert work_unit["authority_boundary"]["stage_authority_role"] == (
        "non_authoritative_observation_and_intent_producer"
    )
    assert work_unit["authority_boundary"]["can_write_stage_current_pointer"] is False
    assert work_unit["authority_boundary"]["can_write_current_owner_delta"] is False
    assert work_unit["authority_boundary"]["can_write_stage_terminal_state"] is False
