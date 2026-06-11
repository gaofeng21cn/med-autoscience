from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts import (
    missing_refs_typed_closeout,
    nonconsumable_redrive_budget,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_result_policy import (
    default_executor_consumed_blocked_reason,
    default_executor_dispatch_zero_execution_blocker,
    default_executor_owner_result_consumable,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_followthrough import (
    default_executor_execution_followthrough_receipt_consumption,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.owner_receipts import (
    human_gate_resume_receipt_consumption,
    mas_owner_apply_receipt_consumption,
    publication_route_memory_writeback_receipt_consumption,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.owner_route_currentness import (
    execution_matches_owner_route,
    owner_route_currentness_basis as build_owner_route_currentness_basis,
)

_DEFAULT_EXECUTOR_EXECUTED_STATUSES = frozenset({"executed", "closed_with_domain_owner_refs"})


def execution_receipt_consumption(status: Mapping[str, Any]) -> dict[str, Any]:
    supersession = _mapping(status.get("blocked_turn_closeout_supersession"))
    if not supersession:
        return {}
    source_ref = relative_study_artifact_ref(_text(supersession.get("source_path")))
    return {
        "status": "superseded_stale_closeout",
        "receipt_kind": "default_executor_execution",
        "superseded_run_id": _text(supersession.get("superseded_run_id")),
        "execution_id": _text(supersession.get("execution_id")),
        "action_type": _text(supersession.get("action_type")),
        "source_ref": source_ref or _text(supersession.get("source_surface")),
        "next_action": "honor_newer_owner_execution_receipt",
    }


def default_executor_execution_receipt_consumption(
    *,
    study_root: Path,
    owner_route: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    current_action_types = _current_owner_route_action_types(owner_route=owner_route, actions=actions)
    if not current_action_types:
        return {}
    nonconsumable_matches: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    for index, (execution, receipt_ref) in enumerate(default_executor_execution_candidates(study_root=study_root)):
        action_type = _text(execution.get("action_type"))
        if action_type not in current_action_types:
            continue
        owner_result = _mapping(execution.get("owner_result"))
        repair_evidence = _mapping(owner_result.get("repair_execution_evidence"))
        blocked_typed_closeout = missing_refs_typed_closeout.is_blocked_typed_closeout(
            execution=execution,
            receipt_ref=receipt_ref,
        )
        missing_refs_typed_closeout_packet = missing_refs_typed_closeout.is_missing_refs_typed_closeout(
            execution=execution,
            receipt_ref=receipt_ref,
        )
        if (
            _text(execution.get("execution_status")) not in _DEFAULT_EXECUTOR_EXECUTED_STATUSES
            and not blocked_typed_closeout
            and not missing_refs_typed_closeout_packet
        ):
            continue
        if _text(execution.get("owner_route_currentness_source")) == "stage_packet_ref_recovered" and not (
            _recovered_stage_packet_currentness_consumable(
                action_type=action_type,
                owner_result=owner_result,
                repair_evidence=repair_evidence,
            )
        ):
            continue
        if not execution_matches_owner_route(execution=execution, owner_route=owner_route):
            continue
        dispatch_zero_execution_blocker = default_executor_dispatch_zero_execution_blocker(owner_result)
        if dispatch_zero_execution_blocker:
            match = nonconsumable_redrive_budget.match(
                execution=execution,
                receipt_ref=receipt_ref,
                action_type=action_type,
                owner_result=owner_result,
                repair_evidence=repair_evidence,
                reason=nonconsumable_redrive_budget.reason(
                    action_type=action_type,
                    owner_result=owner_result,
                    repair_evidence=repair_evidence,
                    dispatch_zero_execution_blocker=dispatch_zero_execution_blocker,
                ),
            )
            nonconsumable_matches.append(match)
            outcomes.append(
                _default_executor_execution_outcome(
                    kind="nonconsumable",
                    receipt_ref=receipt_ref,
                    sequence_index=index,
                    payload=match,
                    study_root=study_root,
                )
            )
            continue
        if missing_refs_typed_closeout_packet:
            outcomes.append(
                _default_executor_execution_outcome(
                    kind="consumed",
                    receipt_ref=receipt_ref,
                    sequence_index=index,
                    payload=missing_refs_typed_closeout.consumption(
                        execution=execution,
                        receipt_ref=receipt_ref,
                        owner_route=owner_route,
                        action_type=action_type,
                    ),
                    study_root=study_root,
                )
            )
            continue
        if not default_executor_owner_result_consumable(
            action_type=action_type,
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        ):
            match = nonconsumable_redrive_budget.match(
                execution=execution,
                receipt_ref=receipt_ref,
                action_type=action_type,
                owner_result=owner_result,
                repair_evidence=repair_evidence,
                reason=nonconsumable_redrive_budget.reason(
                    action_type=action_type,
                    owner_result=owner_result,
                    repair_evidence=repair_evidence,
                    dispatch_zero_execution_blocker=dispatch_zero_execution_blocker,
                ),
            )
            nonconsumable_matches.append(match)
            outcomes.append(
                _default_executor_execution_outcome(
                    kind="nonconsumable",
                    receipt_ref=receipt_ref,
                    sequence_index=index,
                    payload=match,
                    study_root=study_root,
                )
            )
            continue
        blocked_reason = default_executor_consumed_blocked_reason(
            action_type=action_type,
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        )
        owner_route_currentness_basis = build_owner_route_currentness_basis(owner_route)
        outcomes.append(
            _default_executor_execution_outcome(
                kind="consumed",
                receipt_ref=receipt_ref,
                sequence_index=index,
                payload={
                    "status": "consumed",
                    "receipt_kind": "default_executor_execution",
                    "receipt_ref": str(receipt_ref),
                    "execution_id": _text(execution.get("execution_id")),
                    "action_type": action_type,
                    "execution_status": _text(execution.get("execution_status")),
                    "owner_result_status": _text(owner_result.get("status")),
                    "owner_receipt_ref": _text(execution.get("owner_receipt_ref"))
                    or _text(owner_result.get("owner_receipt_ref")),
                    "repair_execution_evidence_status": _text(repair_evidence.get("status")),
                    **({"blocked_reason": blocked_reason} if blocked_reason else {}),
                    **_typed_blocker_consumption_fields(execution, blocked_reason=blocked_reason),
                    "work_unit_id": _text(owner_route_currentness_basis.get("work_unit_id")),
                    "work_unit_fingerprint": _text(owner_route_currentness_basis.get("work_unit_fingerprint")),
                    "canonical_work_unit_identity": owner_route_currentness_basis,
                    "owner_route_currentness_basis": owner_route_currentness_basis,
                    "consumed_owner_route_idempotency_key": _text(owner_route.get("idempotency_key")),
                    "consumed_owner_route_epoch": _text(owner_route.get("route_epoch")),
                    "consumed_owner_route_source_fingerprint": _text(owner_route.get("source_fingerprint")),
                    "changed_artifact_ref_count": len(_mapping_list(repair_evidence.get("changed_artifact_refs"))),
                    "quality_authorized": False,
                    "submission_authorized": False,
                    "current_package_write_authorized": False,
                    "next_action": (
                        "honor_typed_blocker_without_redrive"
                        if _text(execution.get("stage_closeout_outcome")) == "typed_blocker"
                        else "do_not_redrive_consumed_owner_route"
                    ),
                },
                study_root=study_root,
            )
        )
    latest_outcome = _latest_default_executor_execution_outcome(outcomes)
    if latest_outcome is None:
        return {}
    if latest_outcome.get("kind") == "nonconsumable":
        if not nonconsumable_redrive_budget.budget_exhausted(nonconsumable_matches):
            return {}
        return nonconsumable_redrive_budget.consumption(
            latest=_mapping(latest_outcome.get("payload")),
            owner_route=owner_route,
            repeat_count=len(nonconsumable_matches),
        )
    return dict(_mapping(latest_outcome.get("payload")))


def _typed_blocker_consumption_fields(
    execution: Mapping[str, Any],
    *,
    blocked_reason: str | None,
) -> dict[str, Any]:
    if _text(execution.get("stage_closeout_outcome")) != "typed_blocker":
        return {}
    reason = (
        _text(execution.get("typed_blocker_reason"))
        or _text(blocked_reason)
        or "default_executor_typed_blocker"
    )
    typed_blocker_ref = _text(execution.get("typed_blocker_ref"))
    owner_receipt_ref = _text(execution.get("owner_receipt_ref"))
    return {
        key: value
        for key, value in {
            "outcome": "typed_blocker",
            "typed_blocker_reason": reason,
            "typed_blocker_ref": typed_blocker_ref,
            "owner_receipt_ref": owner_receipt_ref,
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "reason": reason,
                "blocker_type": reason,
                "source_ref": typed_blocker_ref,
                "owner_receipt_ref": owner_receipt_ref,
                "next_owner": "med-autoscience",
                "write_permitted": False,
            },
        }.items()
        if value is not None
    }


def default_executor_execution_nonconsumable_closeout(
    *,
    study_root: Path,
    owner_route: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    current_action_types = _current_owner_route_action_types(owner_route=owner_route, actions=actions)
    if not current_action_types:
        return {}
    for execution, receipt_ref in default_executor_execution_candidates(study_root=study_root):
        action_type = _text(execution.get("action_type"))
        if action_type not in current_action_types:
            continue
        blocked_typed_closeout = missing_refs_typed_closeout.is_blocked_typed_closeout(
            execution=execution,
            receipt_ref=receipt_ref,
        )
        missing_refs_typed_closeout_packet = missing_refs_typed_closeout.is_missing_refs_typed_closeout(
            execution=execution,
            receipt_ref=receipt_ref,
        )
        if (
            _text(execution.get("execution_status")) not in _DEFAULT_EXECUTOR_EXECUTED_STATUSES
            and not blocked_typed_closeout
            and not missing_refs_typed_closeout_packet
        ):
            continue
        if not execution_matches_owner_route(execution=execution, owner_route=owner_route):
            continue
        owner_result = _mapping(execution.get("owner_result"))
        repair_evidence = _mapping(owner_result.get("repair_execution_evidence"))
        recovered_stage_packet_currentness = (
            _text(execution.get("owner_route_currentness_source")) == "stage_packet_ref_recovered"
            and not (
                _recovered_stage_packet_currentness_consumable(
                    action_type=action_type,
                    owner_result=owner_result,
                    repair_evidence=repair_evidence,
                )
            )
        )
        dispatch_zero_execution_blocker = default_executor_dispatch_zero_execution_blocker(owner_result)
        if missing_refs_typed_closeout_packet:
            continue
        if not recovered_stage_packet_currentness and default_executor_owner_result_consumable(
            action_type=action_type,
            owner_result=owner_result,
            repair_evidence=repair_evidence,
        ):
            continue
        return {
            "status": "non_consumable_closeout",
            "receipt_kind": "default_executor_execution",
            "receipt_ref": str(receipt_ref),
            "execution_id": _text(execution.get("execution_id")),
            "action_type": action_type,
            "execution_status": _text(execution.get("execution_status")),
            "owner_result_status": _text(owner_result.get("status")),
            "repair_execution_evidence_status": _text(repair_evidence.get("status")),
            "reason": nonconsumable_redrive_budget.reason(
                action_type=action_type,
                owner_result=owner_result,
                repair_evidence=repair_evidence,
                dispatch_zero_execution_blocker=dispatch_zero_execution_blocker,
            ),
            "changed_artifact_ref_count": len(_mapping_list(repair_evidence.get("changed_artifact_refs"))),
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
            "next_action": "redrive_owner_route_with_closeout_context",
        }
    return {}


def _default_executor_execution_outcome(
    *,
    kind: str,
    receipt_ref: str,
    sequence_index: int,
    payload: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "receipt_ref": str(receipt_ref),
        "sequence_index": sequence_index,
        "sort_key": _default_executor_execution_outcome_sort_key(
            receipt_ref=receipt_ref,
            sequence_index=sequence_index,
            study_root=study_root,
        ),
        "payload": dict(payload),
    }


def _latest_default_executor_execution_outcome(outcomes: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    if not outcomes:
        return None
    return max(outcomes, key=lambda item: _mapping(item).get("sort_key") or ("", 0))


def _default_executor_execution_outcome_sort_key(
    *,
    receipt_ref: str,
    sequence_index: int,
    study_root: Path,
) -> tuple[str, int]:
    path = _resolve_study_artifact_ref(study_root=study_root, ref=receipt_ref)
    try:
        return f"{path.stat().st_mtime_ns:020d}", -sequence_index
    except OSError:
        return "", -sequence_index


def _resolve_study_artifact_ref(*, study_root: Path, ref: str) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path
    workspace_root = _workspace_root_from_study_root(study_root)
    if workspace_root is not None and path.parts and path.parts[0] == "studies":
        return workspace_root / path
    return study_root / path


def ai_reviewer_publication_eval_receipt_consumption(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_ref: Path,
) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return {}
    if _text(provenance.get("source_kind")) != "publication_eval_ai_reviewer":
        return {}
    if provenance.get("ai_reviewer_required") is not False:
        return {}
    if not _mapping(publication_eval.get("reviewer_operating_system")):
        return {}
    eval_id = _text(publication_eval.get("eval_id"))
    if not eval_id:
        return {}
    owner_route_currentness_basis = _publication_eval_owner_route_currentness_basis(publication_eval)
    return {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": str(publication_eval_ref),
        "eval_id": eval_id,
        "reviewer_trace_ref": f"{publication_eval_ref}#reviewer_operating_system",
        "work_unit_id": _text(owner_route_currentness_basis.get("work_unit_id")),
        "work_unit_fingerprint": _text(owner_route_currentness_basis.get("work_unit_fingerprint")),
        "owner_route_currentness_basis": owner_route_currentness_basis or None,
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }


def bundle_stage_completion_receipt_consumption(
    *,
    study_root: Path,
    publication_eval: Mapping[str, Any],
    work_unit: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
) -> dict[str, Any]:
    work_unit_id = _text(work_unit.get("unit_id"))
    if not work_unit_id:
        return {}
    work_unit_fingerprint = _text(controller_decision.get("work_unit_fingerprint")) or _text(
        work_unit.get("fingerprint")
    )
    quest_root = _publication_eval_quest_root(publication_eval)
    if quest_root is None:
        return {}
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.exists():
        return {}
    for closeout_path in sorted(closeout_root.glob("*.json")):
        closeout = _read_json_object(closeout_path)
        if closeout is None or closeout.get("status") != "completed":
            continue
        if closeout.get("meaningful_artifact_delta") is not True:
            continue
        for artifact_ref in closeout.get("artifact_refs") or []:
            artifact_ref_text = _text(artifact_ref)
            artifact_path = _resolve_runtime_artifact_ref(quest_root, artifact_ref_text)
            if artifact_path is None or not _runtime_artifact_ref_is_json_payload(artifact_path):
                continue
            package_closure = _read_json_object(artifact_path)
            if not _package_closure_matches_work_unit(
                package_closure,
                study_root=study_root,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=work_unit_fingerprint,
            ):
                continue
            return {
                "status": "consumed",
                "receipt_kind": "runtime_turn_closeout_package_closure",
                "consumed_work_unit_id": work_unit_id,
                "consumed_work_unit_fingerprint": work_unit_fingerprint,
                "completion_ref": _quest_relative_ref(quest_root=quest_root, path=closeout_path),
                "artifact_ref": artifact_ref_text,
                "next_action": "do_not_redrive_completed_work_unit",
            }
    return {}


def relative_study_artifact_ref(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text).expanduser()
    parts = path.parts
    if "artifacts" not in parts:
        return path.name
    return str(Path(*parts[parts.index("artifacts") :]))


def _publication_eval_quest_root(publication_eval: Mapping[str, Any]) -> Path | None:
    runtime_context_refs = _mapping(publication_eval.get("runtime_context_refs"))
    runtime_escalation_ref = _text(runtime_context_refs.get("runtime_escalation_ref"))
    if not runtime_escalation_ref:
        return None
    path = Path(runtime_escalation_ref).expanduser()
    parts = path.parts
    if "artifacts" not in parts:
        return None
    artifacts_index = parts.index("artifacts")
    if artifacts_index <= 0:
        return None
    return Path(*parts[:artifacts_index]).resolve()


def _publication_eval_owner_route_currentness_basis(publication_eval: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    reviewer_os = _mapping(publication_eval.get("reviewer_operating_system"))
    input_bundle = _mapping(reviewer_os.get("input_bundle"))
    basis = (
        _mapping(provenance.get("owner_route_currentness_basis"))
        or _mapping(input_bundle.get("owner_route_currentness_basis"))
        or _mapping(publication_eval.get("owner_route_currentness_basis"))
    )
    work_unit_id = (
        _text(basis.get("work_unit_id"))
        or _text(provenance.get("work_unit_id"))
        or _text(input_bundle.get("work_unit_id"))
        or _publication_eval_work_unit_id(publication_eval)
    )
    work_unit_fingerprint = (
        _text(basis.get("work_unit_fingerprint"))
        or _text(provenance.get("work_unit_fingerprint"))
        or _text(input_bundle.get("work_unit_fingerprint"))
        or _publication_eval_work_unit_fingerprint(publication_eval)
    )
    source_eval_id = _text(basis.get("source_eval_id")) or _text(publication_eval.get("eval_id"))
    return {
        "truth_epoch": _text(basis.get("truth_epoch")),
        "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_id": source_eval_id,
    }


def _publication_eval_work_unit_id(publication_eval: Mapping[str, Any]) -> str:
    for action in _mapping_list(publication_eval.get("recommended_actions")):
        work_unit = _mapping(action.get("next_work_unit"))
        value = _text(work_unit.get("unit_id")) or _text(action.get("work_unit_id"))
        if value:
            return value
    return ""


def _publication_eval_work_unit_fingerprint(publication_eval: Mapping[str, Any]) -> str:
    for action in _mapping_list(publication_eval.get("recommended_actions")):
        value = _text(action.get("work_unit_fingerprint")) or _text(
            _mapping(action.get("next_work_unit")).get("fingerprint")
        )
        if value:
            return value
    return ""


def _resolve_runtime_artifact_ref(quest_root: Path, artifact_ref: str) -> Path | None:
    if not artifact_ref:
        return None
    path = Path(artifact_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (quest_root / path).resolve()


def _runtime_artifact_ref_is_json_payload(path: Path) -> bool:
    return path.suffix.lower() == ".json"


def _package_closure_matches_work_unit(
    payload: Mapping[str, Any] | None,
    *,
    study_root: Path,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> bool:
    if payload is None:
        return False
    if _text(payload.get("artifact_kind")) != work_unit_id:
        return False
    work_unit = _mapping(payload.get("work_unit"))
    if _text(work_unit.get("unit_id")) != work_unit_id:
        return False
    if work_unit_fingerprint and _text(work_unit.get("fingerprint")) != work_unit_fingerprint:
        return False
    authority_closure = _mapping(payload.get("authority_closure"))
    if _text(authority_closure.get("status")) != "closed_for_bundle_stage":
        return False
    if _text(authority_closure.get("publication_gate_status")) != "clear":
        return False
    if authority_closure.get("publication_gate_allow_write") is not True:
        return False
    if list(authority_closure.get("publication_gate_blockers") or []):
        return False
    submission_authority = _mapping(payload.get("submission_minimal_authority"))
    if _text(submission_authority.get("status")) != "current":
        return False
    human_facing_delivery = _mapping(payload.get("human_facing_delivery"))
    current_package_zip = _text(human_facing_delivery.get("current_package_zip"))
    if not current_package_zip:
        return False
    package_path = Path(current_package_zip).expanduser()
    if not package_path.is_absolute():
        package_path = study_root / package_path
    try:
        package_path.resolve().relative_to(study_root.resolve())
    except ValueError:
        return False
    return _text(human_facing_delivery.get("status")) == "current"


def _quest_relative_ref(*, quest_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(quest_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _study_relative_ref(*, study_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(study_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _read_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _writeback_receipt_refs(*, study_root: Path, receipt: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    receipt_refs = _text_list(receipt.get("receipt_refs"))
    if len(receipt_refs) >= 2:
        refs.append(receipt_refs[1])
    writeback_locator = _text(receipt.get("writeback_receipt_locator_ref"))
    idempotency_key = _text(receipt.get("idempotency_key"))
    workspace_root = _workspace_root_from_study_root(study_root)
    if workspace_root is not None and writeback_locator and idempotency_key:
        refs.append(str(workspace_root / writeback_locator / f"{idempotency_key}.json"))
    return _unique_texts(refs)


def _workspace_root_from_study_root(study_root: Path) -> Path | None:
    resolved = study_root.expanduser().resolve()
    if resolved.parent.name == "studies":
        return resolved.parent.parent
    return None


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


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _recovered_stage_packet_currentness_consumable(
    *,
    action_type: str,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> bool:
    if action_type == "run_gate_clearing_batch":
        return _text(owner_result.get("blocked_reason")) == "publication_gate_replay_blocked"
    if action_type != "run_quality_repair_batch":
        return False
    if owner_result.get("ok") is not True and _text(owner_result.get("status")) not in {"executed", "applied", "ok"}:
        return False
    return _quality_repair_story_surface_delta_present(repair_evidence)


def _quality_repair_story_surface_delta_present(repair_evidence: Mapping[str, Any]) -> bool:
    hygiene = _mapping(repair_evidence.get("manuscript_surface_hygiene"))
    return (
        hygiene.get("story_surface_delta_required") is True
        and hygiene.get("story_surface_delta_present") is True
        and _text(hygiene.get("status")) in {"clear", "ready", "passed"}
    )


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _unique_texts(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "ai_reviewer_publication_eval_receipt_consumption",
    "bundle_stage_completion_receipt_consumption",
    "default_executor_execution_nonconsumable_closeout",
    "default_executor_execution_followthrough_receipt_consumption",
    "default_executor_execution_receipt_consumption",
    "execution_receipt_consumption",
    "mas_owner_apply_receipt_consumption",
    "publication_route_memory_writeback_receipt_consumption",
    "relative_study_artifact_ref",
]
