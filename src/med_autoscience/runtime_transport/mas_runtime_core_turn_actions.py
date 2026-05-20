from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.publication_eval_specificity_targets import specificity_target_status


QUALITY_REPAIR_BATCH_WORK_UNIT_IDS = frozenset(
    {
        "analysis_claim_evidence_repair",
        "figure_results_trace_repair",
        "manuscript_story_repair",
        "treatment_gap_reporting_repair",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
        "display_reporting_contract_repair",
        "controller_owned_publication_repair",
        "local_architecture_overview_repair",
        "medical_prose_quality_analysis_source_documentation_repair",
    }
)
GATE_CLEARING_BATCH_WORK_UNIT_IDS = frozenset(
    {
        "publication_gate_replay",
        "submission_authority_sync_closure",
        "submission_delivery_sync_closure",
        "submission_minimal_refresh",
    }
)
RUNTIME_REDRIVE_ACTION_NAMES = frozenset(
    {
        "ensure_study_runtime",
        "ensure_study_runtime_relaunch_stopped",
    }
)
SUPERVISOR_DISPATCH_ACTION_NAMES = frozenset({"return_to_ai_reviewer_workflow"})
DOMAIN_OWNER_DISPATCH_ACTION_NAMES = frozenset(
    {
        "unit_harmonized_external_validation_rerun",
        "recover_transport_model_provenance",
        "methodology_reframe_route_decision",
        "provenance_limited_harmonization_audit",
    }
)
SPECIFICITY_WORK_UNIT_IDS = frozenset({"gate_needs_specificity", "needs_specificity"})
ANALYSIS_HARMONIZATION_WORK_UNIT_IDS = frozenset(
    {
        "unit_harmonized_external_validation_rerun",
        "unit_harmonized_validation_uncertainty_and_grouped_calibration",
    }
)


def controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    names = _raw_controller_action_names(authorization)
    if specificity_targets_ready_for_quality_repair(authorization):
        names = [name for name in names if name != "request_gate_specificity"]
        if "run_quality_repair_batch" not in names:
            names.append("run_quality_repair_batch")
    elif domain_owner_work_unit_present(authorization):
        names = [
            name
            for name in names
            if name not in RUNTIME_REDRIVE_ACTION_NAMES or name in DOMAIN_OWNER_DISPATCH_ACTION_NAMES
        ]
        for unit_id in primary_controller_work_unit_ids(authorization):
            if unit_id in DOMAIN_OWNER_DISPATCH_ACTION_NAMES and unit_id not in names:
                names.append(unit_id)
    elif analysis_harmonization_work_unit_present(authorization):
        names = [name for name in names if name not in RUNTIME_REDRIVE_ACTION_NAMES]
        if "unit_harmonized_external_validation_rerun" not in names:
            names.append("unit_harmonized_external_validation_rerun")
    elif (
        not controller_callable_action_present(names)
        and runtime_redrive_action_present(names)
        and gate_clearing_work_unit_present(authorization)
    ):
        names.append("run_gate_clearing_batch")
    elif "run_quality_repair_batch" not in names and quality_repair_work_unit_present(authorization):
        names.append("run_quality_repair_batch")
    elif not controller_callable_action_present(names) and gate_clearing_work_unit_present(authorization):
        names.append("run_gate_clearing_batch")
    return names


def controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    return _work_unit_ids_from_candidates(
        [
            authorization.get("work_unit_id"),
            authorization.get("next_work_unit"),
            authorization.get("blocking_work_units"),
            authorization.get("work_unit_targets"),
        ]
    )


def primary_controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    return _work_unit_ids_from_candidates(
        [
            authorization.get("work_unit_id"),
            authorization.get("next_work_unit"),
        ]
    )


def controller_action_command(*, action_name: str, quest_id: str) -> str | None:
    if action_name in SUPERVISOR_DISPATCH_ACTION_NAMES or action_name in DOMAIN_OWNER_DISPATCH_ACTION_NAMES:
        return (
            '"${MED_AUTOSCIENCE_REPO}/scripts/run-python-clean.sh" '
            "-m med_autoscience.cli domain-owner-action-dispatch "
            '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --studies <study_id> '
            f"--action-types {action_name} --mode developer_apply_safe --apply --managed-runtime-worker"
        )
    command_by_action = {
        "run_quality_repair_batch": "quality-repair-batch",
        "run_gate_clearing_batch": "gate-clearing-batch",
    }
    command_name = command_by_action.get(action_name)
    if command_name is None:
        return None
    return (
        '"${MED_AUTOSCIENCE_REPO}/scripts/run-python-clean.sh" '
        f"-m med_autoscience.cli {command_name} "
        '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --study-id <study_id> '
        f"--quest-id {quest_id}"
    )


def _raw_controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    raw_actions = authorization.get("controller_actions")
    if isinstance(raw_actions, str):
        actions: list[object] = [raw_actions]
    elif isinstance(raw_actions, (list, tuple)):
        actions = list(raw_actions)
    else:
        actions = []
    names: list[str] = []
    for item in actions:
        if isinstance(item, Mapping):
            raw_name = item.get("action_type") or item.get("action") or item.get("name")
        else:
            raw_name = item
        name = str(raw_name or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _work_unit_ids_from_candidates(candidates: list[object]) -> list[str]:
    unit_ids: list[str] = []

    def append_unit_id(value: object) -> None:
        if isinstance(value, Mapping):
            raw_value = value.get("unit_id") or value.get("work_unit_id") or value.get("id")
        else:
            raw_value = value
        unit_id = str(raw_value or "").strip()
        if unit_id and unit_id not in unit_ids:
            unit_ids.append(unit_id)

    for candidate in candidates:
        if isinstance(candidate, (list, tuple)):
            for item in candidate:
                append_unit_id(item)
        else:
            append_unit_id(candidate)
    return unit_ids


def controller_callable_action_present(action_names: list[str]) -> bool:
    return any(
        name in {"run_quality_repair_batch", "run_gate_clearing_batch"}
        or name in SUPERVISOR_DISPATCH_ACTION_NAMES
        or name in DOMAIN_OWNER_DISPATCH_ACTION_NAMES
        for name in action_names
    )


def runtime_redrive_action_present(action_names: list[str]) -> bool:
    return any(name in RUNTIME_REDRIVE_ACTION_NAMES for name in action_names)


def quality_repair_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    return any(unit_id in QUALITY_REPAIR_BATCH_WORK_UNIT_IDS for unit_id in controller_work_unit_ids(authorization))


def gate_clearing_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    return any(unit_id in GATE_CLEARING_BATCH_WORK_UNIT_IDS for unit_id in primary_controller_work_unit_ids(authorization))


def analysis_harmonization_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    return any(unit_id in ANALYSIS_HARMONIZATION_WORK_UNIT_IDS for unit_id in controller_work_unit_ids(authorization))


def domain_owner_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    return any(unit_id in DOMAIN_OWNER_DISPATCH_ACTION_NAMES for unit_id in primary_controller_work_unit_ids(authorization))


def specificity_targets_ready_for_quality_repair(authorization: Mapping[str, Any]) -> bool:
    if not any(unit_id in SPECIFICITY_WORK_UNIT_IDS for unit_id in controller_work_unit_ids(authorization)):
        return False
    return specificity_target_status(authorization.get("specificity_targets")).get("complete") is True


__all__ = [
    "controller_action_command",
    "controller_action_names",
    "controller_work_unit_ids",
    "primary_controller_work_unit_ids",
]
