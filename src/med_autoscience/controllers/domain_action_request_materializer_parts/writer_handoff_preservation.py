from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_owner_action_dispatch_parts import (
    dispatch_contract,
    persisted_dispatches,
)
from med_autoscience.controllers.default_executor_action_policy import default_executor_search_discipline
from med_autoscience.controllers.quality_repair_batch_parts import writer_handoff
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


def preserved_quality_repair_writer_handoff_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    action: Mapping[str, Any],
    dispatch_path: Path,
    owner_route: Mapping[str, Any],
    apply: bool,
    forbidden_surfaces: list[str],
) -> dict[str, Any] | None:
    if not apply:
        return None
    if action_type != "run_quality_repair_batch":
        return None
    payload = _writer_handoff_dispatch_payload(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        action=action,
        dispatch_path=dispatch_path,
        owner_route=owner_route,
    )
    if not payload:
        return None
    if _text(payload.get("surface")) != "default_executor_dispatch_request":
        return None
    if _text(payload.get("dispatch_status")) != "ready":
        return None
    if _text(payload.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if _text(payload.get("action_type")) != action_type:
        return None
    if _text(payload.get("next_executable_owner")) != "write":
        return None
    if payload.get("medical_claim_authoring_allowed") is not True:
        return None
    source_action = _mapping(payload.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return None
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return None
    if not owner_route_part.owner_route_matches(dispatch=payload, current_route=owner_route):
        request = persisted_dispatches.owner_request_payload(profile, study_id, action_type)
        request_route = owner_route_part.ensure_owner_route_v2(_mapping(request.get("owner_route")) if request else {})
        handoff_route = _mapping(payload.get("owner_route"))
        if not (
            _writer_handoff_request_bridges_current_route(
                handoff_route=handoff_route,
                request_route=request_route,
                current_route=owner_route,
            )
            or _writer_handoff_route_bridges_current_route(
                handoff_route=handoff_route,
                current_route=owner_route,
            )
        ):
            return None
    if not owner_route_part.route_allows_action(action=payload, owner_route=owner_route):
        return None
    if not persisted_dispatches.owner_request_matches_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=payload,
    ) and not _current_action_matches_writer_handoff(
        action=action,
        action_type=action_type,
        payload=payload,
        owner_route=owner_route,
    ):
        return None
    prompt_contract = _mapping(payload.get("prompt_contract"))
    if not prompt_contract:
        return None
    if dispatch_contract.prompt_contract_error(
        prompt_contract,
        forbidden_surfaces=forbidden_surfaces,
    ) is not None:
        return None
    current_work_unit_id = _work_unit_id(action.get("next_work_unit"))
    handoff_work_unit_id = _work_unit_id(source_action.get("next_work_unit"))
    if current_work_unit_id is not None and handoff_work_unit_id is not None and current_work_unit_id != handoff_work_unit_id:
        return None
    return {
        **_upgrade_writer_handoff_dispatch(payload),
        "refs": {
            "dispatch_path": str(dispatch_path),
            **_mapping(payload.get("refs")),
        },
    }


def _upgrade_writer_handoff_dispatch(payload: Mapping[str, Any]) -> dict[str, Any]:
    upgraded = dict(payload)
    prompt_contract = dict(_mapping(payload.get("prompt_contract")))
    search_discipline = default_executor_search_discipline()
    prompt_contract.setdefault("tool_discipline", search_discipline)
    prompt_contract.setdefault("search_boundaries", search_discipline)
    upgraded["prompt_contract"] = prompt_contract
    return upgraded


def _writer_handoff_dispatch_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    action: Mapping[str, Any],
    dispatch_path: Path,
    owner_route: Mapping[str, Any],
) -> dict[str, Any] | None:
    for candidate_path in _writer_handoff_dispatch_candidate_paths(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch_path=dispatch_path,
    ):
        payload = _read_json_object(candidate_path)
        if _text(_mapping(payload).get("dispatch_authority")) == "quality_repair_batch_writer_handoff":
            refs = {"dispatch_path": str(candidate_path), **_mapping(payload.get("refs"))}
            payload["refs"] = refs
            return payload
    payload = _writer_handoff_dispatch_from_current_batch_action(
        study_id=study_id,
        action_type=action_type,
        action=action,
    )
    if payload is not None:
        return payload
    payload = _writer_handoff_dispatch_from_owner_request(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        owner_route=owner_route,
    )
    if payload is not None:
        return payload
    return _writer_handoff_dispatch_from_current_action(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        action=action,
        owner_route=owner_route,
    )


def _writer_handoff_dispatch_candidate_paths(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch_path: Path,
) -> tuple[Path, ...]:
    legacy_owner_callable_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / f"{action_type}.json"
    )
    if legacy_owner_callable_path == dispatch_path:
        return (dispatch_path,)
    return (dispatch_path, legacy_owner_callable_path)


def _writer_handoff_dispatch_from_current_batch_action(
    *,
    study_id: str,
    action_type: str,
    action: Mapping[str, Any],
) -> dict[str, Any] | None:
    if action_type != "run_quality_repair_batch":
        return None
    handoff = _mapping(action.get("writer_worker_handoff"))
    if _text(handoff.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return None
    if _text(handoff.get("dispatch_status")) != "ready":
        return None
    if _text(handoff.get("study_id")) != study_id:
        return None
    if _text(handoff.get("action_type")) != action_type:
        return None
    if _text(handoff.get("next_executable_owner")) != "write":
        return None
    return handoff


def _writer_handoff_dispatch_from_current_action(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any] | None:
    if action_type != "run_quality_repair_batch":
        return None
    route = owner_route_part.ensure_owner_route_v2(_mapping(owner_route))
    if not route:
        return None
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if _text(route.get("next_owner")) != "write":
        return None
    action_reason = _text(action.get("reason")) or _text(_mapping(action.get("handoff_packet")).get("reason"))
    required_output_surface = _required_output_surface(action)
    story_surface_route = (
        route_reason == "manuscript_story_surface_delta_missing"
        and action_reason == "manuscript_story_surface_delta_missing"
    )
    runtime_owner_story_surface_route = (
        route_reason == "quest_waiting_opl_runtime_owner_route"
        and action_reason == "quest_waiting_opl_runtime_owner_route"
        and _requires_manuscript_story_surface_delta(required_output_surface)
    )
    if not (story_surface_route or runtime_owner_story_surface_route):
        return None
    if not owner_route_part.route_allows_action(
        action={**dict(action), "action_type": action_type, "next_executable_owner": "write"},
        owner_route=route,
    ):
        return None
    study_root = profile.studies_root / study_id
    repair_execution_evidence_path = (
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    )
    if not repair_execution_evidence_path.exists():
        return None
    source_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    source_summary_path = _quality_summary_path(study_root)
    source_eval_id = _source_eval_id(
        action=action,
        owner_route=route,
        source_eval_path=source_eval_path,
    )
    return writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=_text(action.get("quest_id")) or _text(route.get("quest_id")) or study_id,
        schema_version=1,
        source_eval_id=source_eval_id,
        source_eval_artifact_path=str(source_eval_path) if source_eval_path.exists() else None,
        source_summary_artifact_path=str(source_summary_path) if source_summary_path.exists() else None,
        repair_execution_evidence_path=repair_execution_evidence_path,
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": dict(route),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": action_type,
                "work_unit_id": _current_work_unit_id(action=action, owner_route=route),
                "work_unit_fingerprint": _current_work_unit_fingerprint(action=action, owner_route=route),
                "source_eval_id": source_eval_id,
                "required_output_surface": required_output_surface,
                "requires_human_confirmation": False,
            },
        },
    )


def _writer_handoff_dispatch_from_owner_request(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    owner_route: Mapping[str, Any],
) -> dict[str, Any] | None:
    request = persisted_dispatches.owner_request_payload(profile, study_id, action_type)
    if not request:
        return None
    if _text(request.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return None
    request_route = owner_route_part.ensure_owner_route_v2(_mapping(request.get("owner_route")))
    if not _writer_handoff_request_bridges_current_route(
        handoff_route=request_route,
        request_route=request_route,
        current_route=owner_route,
    ):
        return None
    source_action = _mapping(request.get("source_action"))
    refs = _mapping(request.get("refs"))
    repair_execution_evidence_path = _text(refs.get("repair_execution_evidence_path")) or _text(
        source_action.get("repair_execution_evidence_ref")
    )
    if repair_execution_evidence_path is None:
        return None
    source_eval_id = _text(source_action.get("source_eval_id")) or _text(
        _mapping(request_route.get("source_refs")).get("source_eval_id")
    )
    current_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(current_refs.get("owner_route_currentness_basis"))
    work_unit_id = _text(current_refs.get("work_unit_id")) or _text(currentness_basis.get("work_unit_id"))
    work_unit_fingerprint = _text(owner_route.get("work_unit_fingerprint")) or _text(
        currentness_basis.get("work_unit_fingerprint")
    )
    return writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=_text(request.get("quest_id")) or study_id,
        schema_version=1,
        source_eval_id=source_eval_id,
        source_eval_artifact_path=_text(refs.get("source_eval_path")),
        source_summary_artifact_path=_text(refs.get("source_summary_path")),
        repair_execution_evidence_path=Path(repair_execution_evidence_path),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": dict(request_route),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_eval_id": source_eval_id,
                "requires_human_confirmation": False,
            },
        },
    )


def _writer_handoff_request_bridges_current_route(
    *,
    handoff_route: Mapping[str, Any],
    request_route: Mapping[str, Any],
    current_route: Mapping[str, Any],
) -> bool:
    normalized_handoff = owner_route_part.ensure_owner_route_v2(_mapping(handoff_route))
    normalized_request = owner_route_part.ensure_owner_route_v2(_mapping(request_route))
    normalized_current = owner_route_part.ensure_owner_route_v2(_mapping(current_route))
    if not (
        normalized_handoff
        and normalized_request
        and normalized_current
        and owner_route_part.owner_route_matches(
            dispatch={"owner_route": normalized_handoff},
            current_route=normalized_request,
        )
    ):
        return False
    if _text(normalized_handoff.get("owner_reason")) != "manuscript_story_surface_delta_missing":
        return False
    current_reason = _text(normalized_current.get("owner_reason"))
    if current_reason not in {"quest_waiting_opl_runtime_owner_route", "manuscript_story_surface_delta_missing"}:
        return False
    if _text(normalized_handoff.get("next_owner")) != _text(normalized_current.get("next_owner")):
        return False
    for key in (
        "study_id",
        "quest_id",
        "truth_epoch",
        "runtime_health_epoch",
        "work_unit_fingerprint",
        "source_fingerprint",
    ):
        if not _same_required_currentness_value(normalized_handoff, normalized_current, key):
            return False
    handoff_refs = _mapping(normalized_handoff.get("source_refs"))
    current_refs = _mapping(normalized_current.get("source_refs"))
    for key in ("source_eval_id", "work_unit_id"):
        if not _same_required_currentness_value(handoff_refs, current_refs, key):
            return False
    if current_reason == "manuscript_story_surface_delta_missing":
        return True
    return _text(handoff_refs.get("bridged_from_idempotency_key")) == _text(
        normalized_current.get("idempotency_key")
    )


def _writer_handoff_route_bridges_current_route(
    *,
    handoff_route: Mapping[str, Any],
    current_route: Mapping[str, Any],
) -> bool:
    normalized_handoff = owner_route_part.ensure_owner_route_v2(_mapping(handoff_route))
    normalized_current = owner_route_part.ensure_owner_route_v2(_mapping(current_route))
    if not normalized_handoff or not normalized_current:
        return False
    if _text(normalized_handoff.get("owner_reason")) != "manuscript_story_surface_delta_missing":
        return False
    current_reason = _text(normalized_current.get("owner_reason"))
    if current_reason not in {"quest_waiting_opl_runtime_owner_route", "manuscript_story_surface_delta_missing"}:
        return False
    if _text(normalized_handoff.get("next_owner")) != _text(normalized_current.get("next_owner")):
        return False
    for key in (
        "study_id",
        "quest_id",
        "truth_epoch",
        "runtime_health_epoch",
        "work_unit_fingerprint",
        "source_fingerprint",
    ):
        if not _same_required_currentness_value(normalized_handoff, normalized_current, key):
            return False
    handoff_refs = _mapping(normalized_handoff.get("source_refs"))
    current_refs = _mapping(normalized_current.get("source_refs"))
    for key in ("source_eval_id", "work_unit_id"):
        if not _same_required_currentness_value(handoff_refs, current_refs, key):
            return False
    if current_reason == "manuscript_story_surface_delta_missing":
        return True
    return _text(handoff_refs.get("bridged_from_idempotency_key")) == _text(
        normalized_current.get("idempotency_key")
    )


def _current_action_matches_writer_handoff(
    *,
    action: Mapping[str, Any],
    action_type: str,
    payload: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    if action_type != "run_quality_repair_batch":
        return False
    action_reason = _text(action.get("reason"))
    if not (
        action_reason == "manuscript_story_surface_delta_missing"
        or (
            action_reason == "quest_waiting_opl_runtime_owner_route"
            and _requires_manuscript_story_surface_delta(_required_output_surface(action))
        )
    ):
        return False
    if _text(payload.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(payload.get("next_executable_owner")) != "write":
        return False
    source_action = _mapping(payload.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return False
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return False
    route = owner_route_part.ensure_owner_route_v2(_mapping(owner_route))
    payload_route = owner_route_part.ensure_owner_route_v2(_mapping(payload.get("owner_route")))
    if not (
        owner_route_part.owner_route_matches(
            dispatch={"owner_route": payload_route},
            current_route=route,
        )
        or _writer_handoff_route_bridges_current_route(
            handoff_route=payload_route,
            current_route=route,
        )
    ):
        return False
    if not owner_route_part.route_allows_action(
        action={**dict(action), "action_type": action_type, "next_executable_owner": "write"},
        owner_route=route,
    ):
        return False
    current_work_unit_id = _work_unit_id(action.get("next_work_unit"))
    handoff_work_unit_id = _work_unit_id(source_action.get("next_work_unit"))
    return not (
        current_work_unit_id is not None
        and handoff_work_unit_id is not None
        and current_work_unit_id != handoff_work_unit_id
    )


def _same_required_currentness_value(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    key: str,
) -> bool:
    left_value = _text(left.get(key))
    right_value = _text(right.get(key))
    return left_value is not None and right_value is not None and left_value == right_value


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _current_work_unit_id(*, action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> str | None:
    refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis"))
    return (
        _work_unit_id(action.get("next_work_unit"))
        or _text(action.get("executable_work_unit"))
        or _text(action.get("controller_work_unit_id"))
        or _text(refs.get("work_unit_id"))
        or _text(basis.get("work_unit_id"))
    )


def _current_work_unit_fingerprint(*, action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> str | None:
    refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis"))
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(refs.get("work_unit_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
    )


def _source_eval_id(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    source_eval_path: Path,
) -> str | None:
    refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis"))
    return (
        _text(action.get("source_eval_id"))
        or _text(refs.get("source_eval_id"))
        or _text(basis.get("source_eval_id"))
        or _text(_mapping(_read_json_object(source_eval_path)).get("eval_id"))
    )


def _required_output_surface(action: Mapping[str, Any]) -> str | None:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return _text(action.get("required_output_surface")) or _text(handoff_packet.get("required_output_surface"))


def _requires_manuscript_story_surface_delta(value: object) -> bool:
    text = str(value or "").strip().lower()
    return (
        "canonical manuscript story-surface delta" in text
        and "typed blocker:manuscript_story_surface_delta_missing" in text
    )


def _quality_summary_path(study_root: Path) -> Path:
    canonical = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    if canonical.exists():
        return canonical
    return study_root / "artifacts" / "evaluation_summary" / "latest.json"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["preserved_quality_repair_writer_handoff_dispatch"]
