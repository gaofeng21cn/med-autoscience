from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers import default_executor_dispatch_packets
from med_autoscience.controllers import progress_first_closeout
from med_autoscience.controllers.runtime_ai_repair_policy import (
    default_executor_policy,
    two_layer_ai_repair_policy_payload,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    current_action_selection,
    publication_owner_materialization,
    supervisor_request_packets,
    writer_handoff_preservation,
)
from med_autoscience.controllers.domain_owner_action_dispatch_parts import output_readiness
from med_autoscience.controllers.default_executor_action_policy import (
    ALLOWED_WRITE_SURFACES,
    FORBIDDEN_SURFACES,
    RETIRED_ABSENT_SURFACES,
    SOURCE_ACTION_REF_FIELDS,
    SOURCE_HANDOFF_REF_FIELDS,
    SUPPORTED_ACTION_TYPES as SUPPORTED_REQUEST_ACTION_TYPES,
    default_executor_search_discipline,
    request_output_surface_for_action_type,
    request_output_target_surface_for_action_type,
    request_owner_for_action_type,
    request_packet_ref_for_action_type,
    request_packet_ref_for_dispatch,
)
from med_autoscience.controllers.owner_route_reconcile import SUPERVISION_LATEST_RELATIVE_PATH
from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import repeat_suppression
from med_autoscience.runtime_protocol import domain_authority_refs_index


SCHEMA_VERSION = 1
CONSUMER_LATEST_RELATIVE_PATH = Path("artifacts/supervision/consumer/latest.json")
CONSUMER_HISTORY_RELATIVE_PATH = Path("artifacts/supervision/consumer/history.jsonl")
DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT = Path(
    "artifacts/supervision/consumer/default_executor_dispatches"
)
SUPPORTED_MODE = "developer_apply_safe"
RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS = frozenset(
    {
        "provider_completion",
        "running_worker",
        "queue_status",
        "retry_budget_remaining",
        "domain_completion",
        "stage_state",
        "provider_completion_is_domain_completion",
        "provider_completion_is_stage_state",
        "queue_succeeded_is_domain_completion",
        "retry_budget_is_domain_completion",
        "running_worker_is_stage_state",
    }
)
MERGE_CLEANUP_CHECKLIST = [
    "focused pytest green",
    "git diff --check green",
    "review diff touches only owned files",
    "merge branch into main after parallel worker coordination",
    "remove worktree after absorb",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _request_packet_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    if action_type not in SUPPORTED_REQUEST_ACTION_TYPES:
        raise ValueError(f"unsupported supervisor request action_type: {action_type}")
    return _study_root(profile, study_id) / _request_packet_ref_for_action_type(action_type)


def _default_executor_dispatch_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    return _study_root(profile, study_id) / DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT / f"{action_type}.json"


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def _consumer_history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_HISTORY_RELATIVE_PATH


def _current_scan_study(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any] | None:
    for study in scan_payload.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return None


def _progress_first_closeout_admission(
    *,
    scan_payload: Mapping[str, Any],
    study_id: str,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    study = _current_scan_study(scan_payload, study_id) or {}
    source_refs = _mapping(owner_route.get("source_refs"))
    running_attempt = _mapping(study.get("running_attempt")) or _mapping(study.get("current_running_attempt"))
    packet = (
        _mapping(running_attempt.get("immutable_dispatch_packet"))
        or _mapping(running_attempt.get("stage_packet"))
        or _mapping(study.get("immutable_dispatch_packet"))
    )
    identity = {
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(study.get("quest_id")),
        "work_unit_id": _text(source_refs.get("work_unit_id")) or _text(owner_route.get("work_unit_id")),
        "stage_attempt_id": _text(running_attempt.get("stage_attempt_id"))
        or _text(study.get("active_stage_attempt_id")),
    }
    return progress_first_closeout.closeout_first_admission(
        identity=identity,
        immutable_dispatch_packet=packet,
        running_attempt=running_attempt,
        owner_receipt=_mapping(study.get("owner_receipt")),
        stage_closeout=_mapping(study.get("stage_closeout")) or _mapping(study.get("latest_stage_closeout")),
        stable_typed_blocker=_mapping(study.get("stable_typed_blocker")),
    )


def _required_output_pending(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    current_study: Mapping[str, Any] | None,
) -> bool:
    return output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        current_study=current_study,
    )


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _request_owner_for_action_type(action_type: str) -> str:
    return request_owner_for_action_type(action_type)


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _request_owner_for_action_type(action_type)
    )


def _request_output_surface_for_action_type(action_type: str) -> str:
    return request_output_surface_for_action_type(action_type)


def _request_output_target_surface_for_action_type(action_type: str) -> dict[str, object] | None:
    return request_output_target_surface_for_action_type(action_type)


def _request_packet_ref_for_action_type(action_type: str) -> str:
    return request_packet_ref_for_action_type(action_type)


def _request_packet_ref_for_dispatch(action_type: str) -> str | None:
    return request_packet_ref_for_dispatch(action_type)


def _source_action_ref(action: Mapping[str, Any]) -> dict[str, Any]:
    source_ref = {key: action[key] for key in SOURCE_ACTION_REF_FIELDS if key in action}
    handoff = _mapping(action.get("handoff_packet"))
    handoff_ref = {key: handoff[key] for key in SOURCE_HANDOFF_REF_FIELDS if key in handoff}
    if handoff_ref:
        source_ref["handoff_packet"] = handoff_ref
    return source_ref


def _required_output_surface(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("required_output_surface"))
        or _text(handoff_packet.get("required_output_surface"))
        or _request_output_surface_for_action_type(action_type)
    )


def _default_executor_forbidden_surfaces(owner_route: Mapping[str, Any]) -> list[str]:
    forbidden = list(FORBIDDEN_SURFACES)
    for item in _mapping(owner_route.get("owner_reason_contract")).get("forbidden_surfaces") or []:
        if (surface := _text(item)) is not None and surface not in forbidden:
            forbidden.append(surface)
    return forbidden


def _executor_prompt(
    *,
    action_type: str,
    study_id: str,
    next_executable_owner: str,
    required_output_surface: str,
) -> str:
    typed_closeout_contract = default_executor_typed_closeout_contract(action_type=action_type)
    return (
        "Use Codex CLI as the default MAS repair executor. "
        f"Handle action `{action_type}` for study `{study_id}` as owner `{next_executable_owner}`. "
        f"Read the referenced MAS durable truth surfaces and write only the owner-authorized output `{required_output_surface}` "
        "or the supervision handoff surfaces listed in this dispatch. Do not patch paper/current_package, "
        "manuscript/current_package, publication gates, or medical conclusions outside the owner workflow. "
        f"{typed_closeout_contract['terminal_output_instruction']}"
    )


def _default_executor_dispatch(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    required_output_surface: str,
    apply: bool,
    developer_mode_payload: Mapping[str, Any],
    scan_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    dispatch_path = _default_executor_dispatch_path(profile, study_id, action_type)
    executor_policy = default_executor_policy()
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    closeout_admission = _progress_first_closeout_admission(
        scan_payload=scan_payload,
        study_id=study_id,
        action=action,
        owner_route=owner_route,
    )
    preserved_writer_handoff = writer_handoff_preservation.preserved_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        action=action,
        dispatch_path=dispatch_path,
        owner_route=owner_route,
        apply=apply,
        forbidden_surfaces=FORBIDDEN_SURFACES,
    )
    if preserved_writer_handoff is not None:
        return preserved_writer_handoff
    idempotency_key = _text(owner_route.get("idempotency_key"))
    repeat_key = repeat_suppression.repeat_key(owner_route)
    typed_closeout_contract = default_executor_typed_closeout_contract(action_type=action_type)
    forbidden_surfaces = _default_executor_forbidden_surfaces(owner_route)
    required_output_target_surface = _request_output_target_surface_for_action_type(action_type)
    prompt_contract = {
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(_mapping(action.get("handoff_packet")).get("quest_id")),
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "owner_route": owner_route or None,
        "owner_reason_contract": _mapping(owner_route.get("owner_reason_contract")) or None,
        "owner_route_attempt_protocol": _mapping(owner_route.get("owner_route_attempt_protocol")) or None,
        "owner_route_currentness_basis": _mapping(_mapping(owner_route.get("source_refs")).get("owner_route_currentness_basis")) or None,
        "idempotency_key": idempotency_key,
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "request_packet_ref": _request_packet_ref_for_dispatch(action_type),
        "paper_progress_stall": _mapping(action.get("paper_progress_stall")) or None,
        "source_scan_latest": str(_scan_latest_path(profile)),
        "required_closeout_packet": typed_closeout_contract,
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "tool_discipline": default_executor_search_discipline(),
        "search_boundaries": default_executor_search_discipline(),
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    if required_output_target_surface is not None:
        prompt_contract["required_output_target_surface"] = required_output_target_surface
    dispatch_shell = {
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "owner_route": owner_route or None,
        "prompt_contract": prompt_contract,
        "required_closeout_packet": typed_closeout_contract,
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
    }
    owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(
        dispatch=dispatch_shell
    )
    dispatch_status = (
        "ready"
        if apply
        and _text(developer_mode_payload.get("mode")) == SUPPORTED_MODE
        and developer_mode_payload.get("safe_actions_enabled") is True
        and owner_route_attempt_envelope.get("dispatchable") is True
        and owner_route_part.route_allows_action(
            action={
                **dict(action),
                "next_executable_owner": next_executable_owner,
                "action_type": action_type,
            },
            owner_route=owner_route,
        )
        else "dry_run" if not apply else "blocked"
    )
    blocked_reason = _default_executor_dispatch_blocked_reason(
        dispatch_status=dispatch_status,
        developer_mode_payload=developer_mode_payload,
        action=action,
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        owner_route=owner_route,
        owner_route_attempt_envelope=owner_route_attempt_envelope,
    )
    current_study = _current_scan_study(scan_payload, study_id)
    repeat_guard = repeat_suppression.dispatch_repeat_suppression(
        dispatch={"prompt_contract": prompt_contract, "owner_route": owner_route, "dispatch_status": dispatch_status},
        current_study=current_study,
        existing_dispatch=_read_json_object(dispatch_path),
        required_output_pending=_required_output_pending(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            current_study=current_study,
        ),
    )
    if dispatch_status == "ready" and repeat_guard["repeat_suppressed"]:
        dispatch_status = "repeat_suppressed"
        blocked_reason = repeat_suppression.REPEAT_SUPPRESSED_REASON
    if dispatch_status == "ready" and closeout_admission.get("admission_status") == "blocked":
        dispatch_status = "blocked"
        blocked_reason = _text(closeout_admission.get("blocked_reason"))
    return _default_executor_dispatch_payload(
        profile=profile,
        action=action,
        action_type=action_type,
        study_id=study_id,
        dispatch_path=dispatch_path,
        executor_policy=executor_policy,
        next_executable_owner=next_executable_owner,
        required_output_surface=required_output_surface,
        owner_route=owner_route,
        idempotency_key=idempotency_key,
        repeat_key=repeat_key,
        dispatch_status=dispatch_status,
        blocked_reason=blocked_reason,
        repeat_guard=repeat_guard,
        typed_closeout_contract=typed_closeout_contract,
        owner_route_attempt_envelope=owner_route_attempt_envelope,
        prompt_contract=prompt_contract,
        progress_first_closeout_admission=closeout_admission,
        generated_at=generated_at,
    )


def _default_executor_dispatch_payload(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    dispatch_path: Path,
    executor_policy: Mapping[str, Any],
    next_executable_owner: str,
    required_output_surface: str,
    owner_route: Mapping[str, Any],
    idempotency_key: str | None,
    repeat_key: str | None,
    dispatch_status: str,
    blocked_reason: str | None,
    repeat_guard: Mapping[str, Any],
    typed_closeout_contract: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    progress_first_closeout_admission: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": SCHEMA_VERSION,
        **dict(executor_policy),
        "study_id": study_id,
        "quest_id": prompt_contract["quest_id"],
        "generated_at": generated_at,
        "action_type": action_type,
        "action_id": _text(action.get("action_id")),
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        **(
            {"required_output_target_surface": dict(prompt_contract["required_output_target_surface"])}
            if "required_output_target_surface" in prompt_contract
            else {}
        ),
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": _text(action.get("action_fingerprint")),
        "paper_progress_stall": _mapping(action.get("paper_progress_stall")) or None,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "repeat_suppressed": bool(repeat_guard["repeat_suppressed"]),
        "why_not_applied": repeat_guard["why_not_applied"],
        "repeat_suppression": dict(repeat_guard),
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": dict(typed_closeout_contract),
        "owner_route_attempt_envelope": dict(owner_route_attempt_envelope),
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "default_executor_policy": dict(executor_policy),
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "prompt_contract": dict(prompt_contract),
        "progress_first_closeout_admission": dict(progress_first_closeout_admission),
        "executor_prompt": _executor_prompt(
            action_type=action_type,
            study_id=study_id,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
        ),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "source_action": _source_action_ref(action),
        "source_action_runtime_completion_fields_omitted": sorted(
            key for key in action if key in RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS
        ),
        "refs": {
            "scan_latest": str(_scan_latest_path(profile)),
            "dispatch_path": str(dispatch_path),
        },
    }


def _default_executor_dispatch_blocked_reason(
    *,
    dispatch_status: str,
    developer_mode_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    owner_route: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
) -> str | None:
    if dispatch_status != "blocked":
        return None
    if reason := _github_block_reason(developer_mode_payload):
        return reason
    if owner_route_attempt_envelope.get("dispatchable") is not True:
        return "owner_route_currentness_basis_missing"
    if owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": next_executable_owner,
            "action_type": action_type,
        },
        owner_route=owner_route,
    ):
        return None
    return "owner_route_next_owner_mismatch"


def _request_task(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    action_type = _text(action.get("action_type")) or "unknown_action"
    return supervisor_request_packets.request_task(
        action=action,
        schema_version=SCHEMA_VERSION,
        developer_mode_payload=developer_mode_payload,
        apply=apply,
        supported_mode=SUPPORTED_MODE,
        packet_path=_request_packet_path(profile, study_id, action_type),
        scan_latest_path=_scan_latest_path(profile),
        forbidden_surfaces=FORBIDDEN_SURFACES,
        allowed_write_surfaces=ALLOWED_WRITE_SURFACES,
    )


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def _selected_actions(
    *,
    profile: WorkspaceProfile,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    request_selected: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    allowed_studies = set(study_ids)
    actions, preignored = _current_actions_for_studies(scan_payload=scan_payload, study_ids=study_ids)
    ignored.extend(preignored)
    if not isinstance(actions, list):
        return request_selected, ignored
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        study_id = _text(action.get("study_id"))
        if study_id not in allowed_studies:
            ignored.append(_ignored_action(action, "study_not_requested"))
            continue
        selected_action = publication_owner_materialization.materialization_action(
            profile=profile,
            action=action,
        ) or dict(action)
        action_type = _text(selected_action.get("action_type"))
        if action_type in SUPPORTED_REQUEST_ACTION_TYPES:
            request_selected.append(selected_action)
            continue
        else:
            ignored.append(_ignored_action(selected_action, "unsupported_action_type"))
            continue
    return request_selected, ignored


def _current_actions_for_studies(
    *,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]:
    return current_action_selection.current_actions_for_studies(
        scan_payload=scan_payload,
        study_ids=study_ids,
    )


def _resolve_study_ids_from_scan(scan_payload: Mapping[str, Any], study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    resolved: list[str] = []
    for action in scan_payload.get("action_queue") or []:
        if isinstance(action, Mapping) and (study_id := _text(action.get("study_id"))) is not None:
            resolved.append(study_id)
    for study in scan_payload.get("studies") or []:
        if isinstance(study, Mapping) and (study_id := _text(study.get("study_id"))) is not None:
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _ai_reviewer_request_refresh(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any] | None:
    study_root = _study_root(profile, study_id)
    request_path = domain_action_request_lifecycle.stable_ai_reviewer_request_path(study_root=study_root)
    packet = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    if packet is None:
        return None
    refreshed = domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=packet,
    )
    changed = refreshed != packet
    if apply and changed:
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(
            json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "surface": "ai_reviewer_request_refresh",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "request_path": str(request_path),
        "refresh_status": "refreshed" if changed else "unchanged",
        "written": bool(apply and changed),
        "publication_eval_record_ref": _text(refreshed.get("publication_eval_record_ref")),
        "attached_eval_id": _text(_mapping(refreshed.get("ai_reviewer_record")).get("eval_id")),
        "blocked_reason": _text(_mapping(refreshed.get("request_lifecycle")).get("blocked_reason")),
    }


def _ai_reviewer_request_refreshes(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    apply: bool,
) -> list[dict[str, Any]]:
    refreshes: list[dict[str, Any]] = []
    for study_id in study_ids:
        refresh = _ai_reviewer_request_refresh(profile=profile, study_id=study_id, apply=apply)
        if refresh is not None:
            refreshes.append(refresh)
    return refreshes


def _persist_default_executor_dispatches(
    *,
    profile: WorkspaceProfile,
    dispatches: list[dict[str, Any]],
) -> list[str]:
    written_files: list[str] = []
    for dispatch in dispatches:
        if _text(dispatch.get("dispatch_status")) != "ready":
            continue
        dispatch_path = Path(_mapping(dispatch.get("refs")).get("dispatch_path"))
        packet_dispatch = default_executor_dispatch_packets.dispatch_with_immutable_packet_ref(
            dispatch=dispatch,
            dispatch_path=dispatch_path,
        )
        dispatch.clear()
        dispatch.update(packet_dispatch)
        _write_json(dispatch_path, dispatch)
        immutable_dispatch_path = default_executor_dispatch_packets.dispatch_stage_packet_path(
            dispatch,
            fallback_dispatch_path=dispatch_path,
        )
        if immutable_dispatch_path != dispatch_path:
            _write_json(immutable_dispatch_path, dispatch)
        dispatch["dispatch_id"] = f"dispatch::{_text(dispatch.get('study_id'))}::{_text(dispatch.get('action_type'))}"
        quest_root = profile.runtime_root / (_text(dispatch.get("quest_id")) or _text(dispatch.get("study_id")) or "")
        dispatch["domain_authority_ref_index"] = domain_authority_refs_index.record_dispatch_receipt(
            quest_root=quest_root,
            receipt=dispatch,
            receipt_path=dispatch_path,
            db_path=domain_authority_refs_index.workspace_authority_refs_index_path(profile.workspace_root),
        )
        _write_json(dispatch_path, dispatch)
        if immutable_dispatch_path != dispatch_path:
            _write_json(immutable_dispatch_path, dispatch)
        written_files.append(str(dispatch_path))
        if immutable_dispatch_path != dispatch_path:
            written_files.append(str(immutable_dispatch_path))
    return written_files


def _persist_request_packets(request_tasks: list[dict[str, Any]]) -> list[str]:
    written_files: list[str] = []
    for task in request_tasks:
        if _text(task.get("dispatch_status")) != "applied":
            continue
        packet_path = Path(_mapping(task.get("refs")).get("request_packet_path"))
        packet = _request_packet_for_persistence(task=task, packet_path=packet_path)
        _write_json(packet_path, packet)
        written_files.append(str(packet_path))
    return written_files


def _apply_progress_first_closeout_to_request_tasks(
    *,
    request_tasks: list[dict[str, Any]],
    default_executor_dispatches: list[dict[str, Any]],
) -> None:
    admissions_by_identity: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    for dispatch in default_executor_dispatches:
        admission = _mapping(dispatch.get("progress_first_closeout_admission"))
        if _text(admission.get("admission_status")) != "blocked":
            continue
        identity = (_text(dispatch.get("study_id")), _text(dispatch.get("action_type")))
        admissions_by_identity[identity] = admission
    if not admissions_by_identity:
        return
    for task in request_tasks:
        admission = admissions_by_identity.get((_text(task.get("study_id")), _text(task.get("action_type"))))
        if admission is None:
            continue
        task["dispatch_status"] = "blocked"
        task["blocked_reason"] = _text(admission.get("blocked_reason"))
        task["progress_first_closeout_admission"] = dict(admission)
        handoff = dict(_mapping(task.get("handoff_packet")))
        handoff["progress_first_closeout_admission"] = dict(admission)
        handoff["blocked_reason"] = _text(admission.get("blocked_reason"))
        task["handoff_packet"] = handoff


def _request_packet_for_persistence(
    *,
    task: Mapping[str, Any],
    packet_path: Path,
) -> dict[str, Any]:
    packet = _mapping(task.get("handoff_packet"))
    if _text(task.get("action_type")) != "return_to_ai_reviewer_workflow":
        return packet
    action = _mapping(task.get("source_action"))
    lifecycle = dict(_mapping(packet.get("request_lifecycle")))
    reason = _text(action.get("reason")) or _text(packet.get("reason"))
    if reason:
        lifecycle["blocked_reason"] = reason
    if stale_record_ref := _text(action.get("stale_record_ref")):
        lifecycle["stale_record_ref"] = stale_record_ref
    required_refs = [ref for ref in action.get("required_currentness_refs") or [] if _text(ref)]
    if required_refs:
        lifecycle["required_currentness_refs"] = required_refs
    if source_ref := _text(action.get("source_ref")):
        lifecycle["source_ref"] = source_ref
    if lifecycle:
        packet["request_lifecycle"] = lifecycle
    source_workflow_ref = _source_workflow_ref_for_ai_reviewer_request(
        action=action,
        packet=packet,
        existing_packet=_read_json_object(packet_path),
    )
    if source_workflow_ref:
        packet["source_workflow_ref"] = source_workflow_ref
    try:
        study_root = packet_path.parents[4]
    except IndexError:
        return packet
    return domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=packet,
    )


def _source_workflow_ref_for_ai_reviewer_request(
    *,
    action: Mapping[str, Any],
    packet: Mapping[str, Any],
    existing_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source_handoff = _mapping(action.get("handoff_packet"))
    ref = {
        **_mapping(_mapping(existing_packet).get("source_workflow_ref")),
        **_mapping(source_handoff.get("source_workflow_ref")),
        **_mapping(packet.get("source_workflow_ref")),
    }
    if next_work_unit := _text(action.get("next_work_unit")):
        ref["next_work_unit"] = next_work_unit
    if route_back_target := (
        _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(action.get("owner"))
        or _text(_mapping(action.get("owner_route")).get("next_owner"))
        or _text(packet.get("request_owner"))
    ):
        ref["route_back_target"] = route_back_target
    return ref


def _persist_consumer_payload(
    *,
    profile: WorkspaceProfile,
    payload: Mapping[str, Any],
    generated_at: str,
    study_ids: tuple[str, ...],
    request_task_count: int,
    ai_reviewer_request_refresh_count: int,
    written_files: list[str],
    effective_mode: str,
) -> None:
    written_files.append(str(_consumer_latest_path(profile)))
    _write_json(_consumer_latest_path(profile), payload)
    _append_json_line(
        _consumer_history_path(profile),
        {
            "generated_at": generated_at,
            "study_ids": list(study_ids),
            "request_task_count": request_task_count,
            "ai_reviewer_request_refresh_count": ai_reviewer_request_refresh_count,
            "written_files": list(written_files),
            "effective_mode": effective_mode,
        },
    )


def materialize_domain_action_requests(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="external_queue_consumer",
    )
    developer_mode_payload = developer_mode.to_dict()
    scan_payload = _read_json_object(_scan_latest_path(profile)) or {}
    resolved_study_ids = _resolve_study_ids_from_scan(scan_payload, study_ids)
    selected_request_actions, ignored_actions = _selected_actions(
        profile=profile,
        scan_payload=scan_payload,
        study_ids=resolved_study_ids,
    )
    request_tasks = [
        _request_task(
            profile=profile,
            action=action,
            developer_mode_payload=developer_mode_payload,
            apply=apply,
        )
        for action in selected_request_actions
    ]
    default_executor_dispatches = [
        _default_executor_dispatch(
            profile=profile,
            action=action,
            action_type=_text(action.get("action_type")) or "unknown_action",
            next_executable_owner=_owner_from_action(action, _text(action.get("action_type")) or "unknown_action"),
            required_output_surface=_required_output_surface(action, _text(action.get("action_type")) or "unknown_action"),
            apply=apply,
            developer_mode_payload=developer_mode_payload,
            scan_payload=scan_payload,
            generated_at=generated_at,
        )
        for action in selected_request_actions
    ]
    _apply_progress_first_closeout_to_request_tasks(
        request_tasks=request_tasks,
        default_executor_dispatches=default_executor_dispatches,
    )
    ai_reviewer_request_refreshes: list[dict[str, Any]] = []
    written_files: list[str] = []
    if apply and developer_mode.safe_actions_enabled:
        written_files.extend(_persist_default_executor_dispatches(profile=profile, dispatches=default_executor_dispatches))
        written_files.extend(_persist_request_packets(request_tasks))
        ai_reviewer_request_refreshes = _ai_reviewer_request_refreshes(
            profile=profile,
            study_ids=resolved_study_ids,
            apply=True,
        )
        for refresh in ai_reviewer_request_refreshes:
            if refresh.get("written") is True:
                written_files.append(str(refresh["request_path"]))
    else:
        ai_reviewer_request_refreshes = _ai_reviewer_request_refreshes(
            profile=profile,
            study_ids=resolved_study_ids,
            apply=False,
        )

    payload = {
        "surface": "domain_action_request_materializer",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "source_surface": str(_scan_latest_path(profile)),
        "dry_run": not apply,
        "requested_studies": list(resolved_study_ids),
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "github_gate": dict(developer_mode.github_user_gate),
        "developer_supervisor_mode": developer_mode_payload,
        "apply_allowed": bool(apply and developer_mode.safe_actions_enabled),
        "runtime_control_owner": "one-person-lab",
        "request_task_count": len(request_tasks),
        "request_tasks": request_tasks,
        "ai_reviewer_request_refresh_count": len(ai_reviewer_request_refreshes),
        "ai_reviewer_request_refreshes": ai_reviewer_request_refreshes,
        "default_executor_dispatch_count": len(default_executor_dispatches),
        "repeat_suppressed_count": sum(item.get("repeat_suppressed") is True for item in default_executor_dispatches),
        "default_executor_dispatches": default_executor_dispatches,
        "ignored_actions": ignored_actions,
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "merge_cleanup_checklist": list(MERGE_CLEANUP_CHECKLIST),
        "written_files": written_files,
        "refs": {
            "latest_path": str(_consumer_latest_path(profile)),
            "history_path": str(_consumer_history_path(profile)),
        },
    }
    if apply and developer_mode.safe_actions_enabled:
        payload["written_files"] = written_files
        _persist_consumer_payload(
            profile=profile,
            payload=payload,
            generated_at=generated_at,
            study_ids=resolved_study_ids,
            request_task_count=len(request_tasks),
            ai_reviewer_request_refresh_count=len(ai_reviewer_request_refreshes),
            written_files=written_files,
            effective_mode=developer_mode.mode,
        )
    return payload


__all__ = [
    "CONSUMER_LATEST_RELATIVE_PATH",
    "FORBIDDEN_SURFACES",
    "RETIRED_ABSENT_SURFACES",
    "SCHEMA_VERSION",
    "SUPPORTED_REQUEST_ACTION_TYPES",
    "materialize_domain_action_requests",
]
