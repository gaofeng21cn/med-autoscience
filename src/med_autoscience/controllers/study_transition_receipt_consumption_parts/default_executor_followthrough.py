from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)


_DEFAULT_EXECUTOR_EXECUTED_STATUSES = frozenset({"executed"})
_DEFAULT_EXECUTOR_CONSUMABLE_OWNER_RESULT_STATUSES = frozenset({"executed", "applied", "ok"})
_DEFAULT_EXECUTOR_CONSUMABLE_REPAIR_EVIDENCE_STATUSES = frozenset(
    {
        "progress_delta_candidate",
        "executed",
        "applied",
    }
)


def default_executor_execution_followthrough_receipt_consumption(
    *,
    study_root: Path,
    owner_route: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    current_action_types = _current_owner_route_action_types(owner_route=owner_route, actions=actions)
    if current_action_types != {"current_package_freshness_required"}:
        return {}
    for execution, receipt_ref in default_executor_execution_candidates(study_root=study_root):
        action_type = _text(execution.get("action_type"))
        owner_result = _mapping(execution.get("owner_result"))
        repair_evidence = _mapping(owner_result.get("repair_execution_evidence"))
        if action_type in current_action_types and _direct_execution_consumes_current_owner_route(
            execution=execution,
            owner_route=owner_route,
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        ):
            return {}
        if action_type not in {"publication_gate_specificity_required", "run_gate_clearing_batch"}:
            continue
        if _text(execution.get("execution_status")) not in _DEFAULT_EXECUTOR_EXECUTED_STATUSES:
            continue
        if _text(execution.get("owner_route_currentness_source")) == "stage_packet_ref_recovered":
            continue
        if not _execution_matches_to_package_freshness_followthrough(
            execution=execution,
            owner_route=owner_route,
            action_type=action_type,
        ):
            continue
        if _default_executor_dispatch_zero_execution_blocker(owner_result):
            continue
        if action_type == "publication_gate_specificity_required" and not _publication_gate_specificity_owner_result_satisfies_route_output(
            owner_result=owner_result
        ):
            continue
        if action_type == "run_gate_clearing_batch" and not _gate_clearing_batch_owner_result_satisfies_route_output(
            owner_result=owner_result
        ):
            continue
        blocked_reason = _default_executor_consumed_blocked_reason(
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        )
        return {
            "status": "consumed",
            "receipt_kind": "default_executor_execution",
            "receipt_ref": str(receipt_ref),
            "execution_id": _text(execution.get("execution_id")),
            "action_type": action_type,
            "execution_status": _text(execution.get("execution_status")),
            "owner_result_status": _text(owner_result.get("status")),
            "repair_execution_evidence_status": _text(repair_evidence.get("status")),
            **({"blocked_reason": blocked_reason} if blocked_reason else {}),
            "consumption_mode": "followthrough_action_transition",
            "followthrough_from_action_type": action_type,
            "followthrough_to_action_type": "current_package_freshness_required",
            "consumed_owner_route_idempotency_key": _text(execution.get("idempotency_key")),
            "followthrough_owner_route_idempotency_key": _text(owner_route.get("idempotency_key")),
            "consumed_owner_route_epoch": _text(owner_route.get("route_epoch")),
            "consumed_owner_route_source_fingerprint": _text(owner_route.get("source_fingerprint")),
            "changed_artifact_ref_count": len(_mapping_list(repair_evidence.get("changed_artifact_refs"))),
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
            "next_action": "honor_followthrough_current_owner_route",
        }
    return {}


def _current_owner_route_action_types(
    *,
    owner_route: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
) -> set[str]:
    allowed_actions = {_text(item) for item in owner_route.get("allowed_actions") or []}
    allowed_actions.discard("")
    action_types = {_text(action.get("action_type")) for action in actions}
    action_types.discard("")
    return allowed_actions & action_types


def _execution_matches_to_package_freshness_followthrough(
    *,
    execution: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    action_type: str,
) -> bool:
    prompt_contract = _mapping(execution.get("prompt_contract"))
    for execution_route in (
        _mapping(execution.get("current_owner_route")),
        _mapping(execution.get("owner_route")),
        _mapping(prompt_contract.get("owner_route")),
    ):
        if _to_package_freshness_currentness_matches(
            execution_route=execution_route,
            owner_route=owner_route,
            from_action_type=action_type,
        ):
            return True
    return False


def _direct_execution_consumes_current_owner_route(
    *,
    execution: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> bool:
    if _text(execution.get("execution_status")) not in _DEFAULT_EXECUTOR_EXECUTED_STATUSES:
        return False
    if _text(execution.get("owner_route_currentness_source")) == "stage_packet_ref_recovered":
        return False
    if not _execution_matches_owner_route(execution=execution, owner_route=owner_route):
        return False
    if _default_executor_dispatch_zero_execution_blocker(owner_result):
        return False
    return _default_executor_owner_result_consumable(
        owner_result=owner_result,
        repair_evidence=repair_evidence,
    )


def _execution_matches_owner_route(
    *,
    execution: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    prompt_contract = _mapping(execution.get("prompt_contract"))
    for execution_route in (
        _mapping(execution.get("current_owner_route")),
        _mapping(execution.get("owner_route")),
        _mapping(prompt_contract.get("owner_route")),
    ):
        if _owner_route_currentness_matches(execution_route=execution_route, owner_route=owner_route):
            return True
    return False


def _owner_route_currentness_matches(
    *,
    execution_route: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    if not execution_route:
        return False
    comparisons = ("route_epoch", "next_owner")
    for key in comparisons:
        current_value = _text(owner_route.get(key))
        execution_value = _text(execution_route.get(key))
        if current_value and execution_value and current_value != execution_value:
            return False
        if current_value and not execution_value:
            return False
    if not _owner_route_work_unit_currentness_matches(execution_route=execution_route, owner_route=owner_route):
        return False
    current_allowed = {_text(item) for item in owner_route.get("allowed_actions") or []}
    execution_allowed = {_text(item) for item in execution_route.get("allowed_actions") or []}
    current_allowed.discard("")
    execution_allowed.discard("")
    return bool(current_allowed) and current_allowed == execution_allowed


def _owner_route_work_unit_currentness_matches(
    *,
    execution_route: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    current_basis = _owner_route_currentness_basis(owner_route)
    execution_basis = _owner_route_currentness_basis(execution_route)
    for key in ("truth_epoch", "work_unit_fingerprint", "work_unit_id"):
        current_value = _text(current_basis.get(key))
        execution_value = _text(execution_basis.get(key))
        if current_value and not execution_value:
            return False
        if current_value and execution_value and current_value != execution_value:
            return False
    return bool(_text(current_basis.get("work_unit_fingerprint")) or _text(current_basis.get("work_unit_id")))


def _to_package_freshness_currentness_matches(
    *,
    execution_route: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    from_action_type: str,
) -> bool:
    if not execution_route:
        return False
    expected_owner_reason = {
        "publication_gate_specificity_required": "publication_gate_specificity_required",
        "run_gate_clearing_batch": "owner_authorized_publication_gate_replay",
    }.get(from_action_type)
    if expected_owner_reason is None:
        return False
    if _text(execution_route.get("owner_reason")) != expected_owner_reason:
        return False
    if _text(owner_route.get("owner_reason")) != "current_package_freshness_required":
        return False
    execution_allowed = {_text(item) for item in execution_route.get("allowed_actions") or []}
    current_allowed = {_text(item) for item in owner_route.get("allowed_actions") or []}
    execution_allowed.discard("")
    current_allowed.discard("")
    if execution_allowed != {from_action_type}:
        return False
    if current_allowed != {"current_package_freshness_required"}:
        return False
    execution_basis = _owner_route_currentness_basis(execution_route)
    current_basis = _owner_route_currentness_basis(owner_route)
    if from_action_type == "run_gate_clearing_batch":
        return _gate_replay_to_package_freshness_currentness_matches(
            execution_route=execution_route,
            owner_route=owner_route,
            execution_basis=execution_basis,
            current_basis=current_basis,
        )
    for key in ("truth_epoch", "work_unit_fingerprint", "work_unit_id"):
        current_value = _text(current_basis.get(key))
        execution_value = _text(execution_basis.get(key))
        if current_value and not execution_value:
            return False
        if current_value and execution_value and current_value != execution_value:
            return False
    return bool(_text(current_basis.get("work_unit_fingerprint")) and _text(current_basis.get("work_unit_id")))


def _gate_replay_to_package_freshness_currentness_matches(
    *,
    execution_route: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    execution_basis: Mapping[str, Any],
    current_basis: Mapping[str, Any],
) -> bool:
    if _text(execution_basis.get("work_unit_id")) != "owner_authorized_publication_gate_replay":
        return False
    if _text(current_basis.get("work_unit_id")) != "submission_minimal_refresh":
        return False
    if not _same_non_empty_text(
        _text(execution_basis.get("truth_epoch")),
        _text(current_basis.get("truth_epoch")),
    ):
        return False
    if not _same_non_empty_text(
        _source_eval_id(execution_route),
        _source_eval_id(owner_route),
    ):
        return False
    return _text(current_basis.get("work_unit_fingerprint")) is not None


def _owner_route_currentness_basis(route: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = _mapping(route.get("source_refs"))
    nested_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return {
        "truth_epoch": (
            _text(nested_basis.get("truth_epoch"))
            or _text(source_refs.get("study_truth_epoch"))
            or _text(route.get("truth_epoch"))
            or _text(route.get("route_epoch"))
        ),
        "work_unit_fingerprint": (
            _text(nested_basis.get("work_unit_fingerprint"))
            or _text(source_refs.get("work_unit_fingerprint"))
            or _text(route.get("work_unit_fingerprint"))
        ),
        "work_unit_id": _text(nested_basis.get("work_unit_id")) or _text(source_refs.get("work_unit_id")),
        "owner_reason": (
            _text(nested_basis.get("owner_reason"))
            or _text(source_refs.get("blocked_reason"))
            or _text(route.get("owner_reason"))
            or _text(route.get("failure_signature"))
        ),
    }


def _source_eval_id(route: Mapping[str, Any]) -> str:
    source_refs = _mapping(route.get("source_refs"))
    return _text(source_refs.get("source_eval_id")) or _text(route.get("source_eval_id"))


def _same_non_empty_text(left: str, right: str) -> bool:
    return bool(left and right and left == right)


def _publication_gate_specificity_owner_result_satisfies_route_output(*, owner_result: Mapping[str, Any]) -> bool:
    if not _text(owner_result.get("report_json")):
        return False
    publication_eval = _mapping(owner_result.get("publication_eval"))
    if not _text(publication_eval.get("eval_id")):
        return False
    return _is_publication_eval_latest_path(_text(publication_eval.get("artifact_path")))


def _gate_clearing_batch_owner_result_satisfies_route_output(*, owner_result: Mapping[str, Any]) -> bool:
    gate_replay = _mapping(owner_result.get("gate_replay"))
    return _text(owner_result.get("status")) == "executed" and _text(gate_replay.get("status")) == "blocked"


def _default_executor_owner_result_consumable(
    *,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> bool:
    if owner_result.get("ok") is True:
        return True
    if _text(owner_result.get("status")) in _DEFAULT_EXECUTOR_CONSUMABLE_OWNER_RESULT_STATUSES:
        return True
    if _text(repair_evidence.get("status")) in _DEFAULT_EXECUTOR_CONSUMABLE_REPAIR_EVIDENCE_STATUSES:
        return True
    return bool(_mapping_list(repair_evidence.get("changed_artifact_refs")))


def _default_executor_dispatch_zero_execution_blocker(owner_result: Mapping[str, Any]) -> bool:
    dispatcher_result = _mapping(owner_result.get("dispatcher_result"))
    if not dispatcher_result:
        return False
    execution_count = dispatcher_result.get("execution_count")
    if execution_count not in {0, "0"}:
        return False
    blocked_reason = _text(owner_result.get("blocked_reason"))
    blocked_reasons = _string_set(owner_result.get("blocked_reasons"))
    dispatch_reason = _text(dispatcher_result.get("reason"))
    return (
        blocked_reason == "domain_owner_action_dispatch_execution_count_zero"
        or "domain_owner_action_dispatch_execution_count_zero" in blocked_reasons
        or "run_quality_repair_batch_not_visible_in_current_opl_control_state" in blocked_reasons
        or "no current executable" in dispatch_reason
    )


def _default_executor_consumed_blocked_reason(
    *,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> str:
    return _text(owner_result.get("blocked_reason")) or _text(repair_evidence.get("blocked_reason"))


def _is_publication_eval_latest_path(path_text: str) -> bool:
    if not path_text:
        return False
    path = Path(path_text).expanduser()
    return path.parts[-3:] == ("artifacts", "publication_eval", "latest.json")


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        text = _text(value)
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _text(item))}


__all__ = ["default_executor_execution_followthrough_receipt_consumption"]
