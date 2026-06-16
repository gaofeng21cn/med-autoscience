from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import quality_repair_batch
from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    has_opl_transition_readback,
)
from med_autoscience.controllers.medical_prose_story_surface_parts.eval_bound_currentness import (
    EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER,
)
from med_autoscience.controllers.opl_execution_boundary import (
    typed_blocker as opl_execution_authorization_typed_blocker,
)
from med_autoscience.profiles import WorkspaceProfile

TASK_KIND = "domain_owner/default-executor-dispatch"
AI_REVIEWER_CURRENT_MANUSCRIPT_RECORD_WORK_UNIT = (
    "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
)
AI_REVIEWER_CURRENT_MANUSCRIPT_RECORD_REASON = "ai_reviewer_record_stale_after_current_manuscript"


def execute_quality_repair_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any],
    quest_root: Path | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "quest_root": str(quest_root),
        }
    if _dispatch_consumes_quality_repair_writer_handoff(dispatch):
        return _writer_stage_attempt_handoff_execution(dispatch=dispatch, quest_root=quest_root)
    try:
        owner_result = quality_repair_batch.run_quality_repair_batch(
            profile=profile,
            study_id=study_id,
            study_root=profile.studies_root / study_id,
            quest_id=quest_root.name,
            source="domain_owner_action_dispatch",
            authority_route_context=_authority_route_context(dispatch),
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": str(exc) or "quality_repair_batch_failed",
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "quest_root": str(quest_root),
        }
    result_payload = dict(owner_result) if isinstance(owner_result, Mapping) else {}
    handoff_ready = (
        result_payload.get("status") == "handoff_ready"
        and isinstance(result_payload.get("writer_worker_handoff"), Mapping)
    )
    if handoff_ready and _dispatch_consumes_quality_repair_writer_handoff(dispatch):
        blocker = _quality_repair_handoff_blocker(result_payload)
        return {
            "execution_status": "blocked",
            "blocked_reason": blocker,
            "typed_blocker": blocker,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": result_payload,
            "consumed_writer_handoff_empty_spin_blocked": True,
            "required_next_owner": "write",
            "required_output_surface": _text(dispatch.get("required_output_surface"))
            or _text(_mapping(dispatch.get("prompt_contract")).get("required_output_surface")),
            "quest_root": str(quest_root),
        }
    executed = bool(result_payload.get("ok"))
    blocked_reason = (
        None
        if executed or handoff_ready
        else _text(result_payload.get("blocked_reason"))
        or _text(result_payload.get("status"))
        or "quality_repair_batch_not_applied"
    )
    progress_first_route = _progress_first_currentness_routeback(
        dispatch=dispatch,
        owner_result=result_payload,
        blocked_reason=blocked_reason,
    )
    evidence_payload = (
        _blocked_owner_result_evidence_payload(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            owner_result=result_payload,
            blocked_reason=blocked_reason,
        )
        if blocked_reason is not None
        else {}
    )
    provider_handoff_fields = (
        _provider_stage_attempt_handoff_fields(
            dispatch=dispatch,
            required_output_surface=_text(dispatch.get("required_output_surface"))
            or _text(_mapping(dispatch.get("prompt_contract")).get("required_output_surface")),
        )
        if handoff_ready
        else {}
    )
    return {
        "execution_status": "handoff_ready" if handoff_ready else ("executed" if executed else "blocked"),
        "blocked_reason": blocked_reason,
        "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
        "owner_result": result_payload if result_payload else owner_result,
        **({"writer_worker_handoff": dict(result_payload["writer_worker_handoff"])} if handoff_ready else {}),
        **provider_handoff_fields,
        **progress_first_route,
        **evidence_payload,
        "quest_root": str(quest_root),
    }


def _authority_route_context(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    owner_route_source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _owner_route_currentness_basis(
        owner_route=owner_route,
        owner_route_source_refs=owner_route_source_refs,
    )
    next_work_unit_raw = source_action.get("next_work_unit") or dispatch.get("next_work_unit") or prompt_contract.get("next_work_unit")
    next_work_unit = _mapping(next_work_unit_raw)
    work_unit_id = (
        _work_unit_id(next_work_unit_raw)
        or _materialized_owner_route_work_unit_id(owner_route_source_refs)
        or _work_unit_id(owner_route_source_refs.get("work_unit_id"))
        or _work_unit_id(currentness_basis.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        _text(source_action.get("work_unit_fingerprint"))
        or _text(dispatch.get("work_unit_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(owner_route_source_refs.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )
    source_eval_id = (
        _text(source_action.get("source_eval_id"))
        or _text(owner_route_source_refs.get("source_eval_id"))
        or _text(currentness_basis.get("source_eval_id"))
    )
    flat_context = {
        "control_surface": "domain_owner_action_dispatch",
        "controller_action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": dict(next_work_unit) if next_work_unit else None,
        "route_target": _text(source_action.get("route_target")) or _text(dispatch.get("route_target")),
        "route_key_question": _text(source_action.get("route_key_question")) or _text(dispatch.get("route_key_question")),
        "route_rationale": _text(source_action.get("route_rationale")) or _text(dispatch.get("route_rationale")),
        "current_owner_route": dict(owner_route) if owner_route else None,
    }
    if work_unit_id is not None:
        flat_context["controller_route_context"] = {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        }
    return {
        **flat_context,
    }


def _blocked_owner_result_evidence_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    blocked_reason: str,
) -> dict[str, Any]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind=TASK_KIND,
        study_id=study_id,
        reason=blocked_reason,
        evidence_refs=_blocked_owner_result_evidence_refs(
            profile=profile,
            dispatch=dispatch,
            owner_result=owner_result,
            owner_route=owner_route,
            blocked_reason=blocked_reason,
        ),
        source_fingerprint=_text(owner_route.get("source_fingerprint")),
        profile_name=profile.name,
    )
    return {
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
        "opl_runtime_action_execute_payload": evidence_record_payload["opl_runtime_action_execute_payload"],
        "typed_blocker_refs": list(evidence_record_payload["typed_blocker_refs"]),
        "domain_owner_receipt_refs": list(evidence_record_payload["domain_owner_receipt_refs"]),
        "domain_receipt_refs": list(evidence_record_payload["domain_owner_receipt_refs"]),
        "owner_chain_refs": list(evidence_record_payload["owner_chain_refs"]),
        "evidence_refs": list(evidence_record_payload["evidence_refs"]),
        "no_regression_evidence_refs": list(evidence_record_payload["no_regression_evidence_refs"]),
        "no_regression_refs": list(evidence_record_payload["no_regression_refs"]),
        "body_included": False,
        "domain_ready_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_mutation_authorized": False,
    }


def _progress_first_currentness_routeback(
    *,
    dispatch: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    blocked_reason: str | None,
) -> dict[str, Any]:
    if blocked_reason != EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER:
        return {}
    next_work_unit = AI_REVIEWER_CURRENT_MANUSCRIPT_RECORD_WORK_UNIT
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    currentness_blocker = _mapping(owner_result.get("currentness_blocker"))
    if not currentness_blocker:
        currentness_blocker = _mapping(owner_result.get("typed_blocker_payload"))
    return {
        "next_owner": "ai_reviewer",
        "required_next_owner": "ai_reviewer",
        "next_action_type": "return_to_ai_reviewer_workflow",
        "next_required_actions": [
            next_work_unit,
            "rematerialize_ai_reviewer_request",
            "return_to_ai_reviewer_workflow",
        ],
        "progress_first_routeback": {
            "surface": "progress_first_currentness_routeback",
            "schema_version": 1,
            "from_action_type": "run_quality_repair_batch",
            "blocked_reason": EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER,
            "next_owner": "ai_reviewer",
            "next_action_type": "return_to_ai_reviewer_workflow",
            "next_work_unit": next_work_unit,
            "owner_reason": AI_REVIEWER_CURRENT_MANUSCRIPT_RECORD_REASON,
            "stale_write_dispatch_reuse_allowed": False,
            "repeat_write_dispatch_allowed": False,
            "reason": (
                "The writer dispatch was bound to a stale AI reviewer manuscript digest; "
                "Progress-First must refresh the AI reviewer record before redriving write."
            ),
            "source_owner_route": dict(owner_route) if owner_route else None,
            "currentness_blocker": dict(currentness_blocker) if currentness_blocker else None,
        },
    }


def _blocked_owner_result_evidence_refs(
    *,
    profile: WorkspaceProfile,
    dispatch: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    blocked_reason: str,
) -> list[str]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    dispatch_refs = _mapping(dispatch.get("refs"))
    dispatch_ref = _workspace_relative_ref(
        dispatch_refs.get("dispatch_path"),
        workspace_root=profile.workspace_root,
    )
    refs = [
        dispatch_ref,
        f"{dispatch_ref}#prompt_contract" if dispatch_ref else None,
        f"{dispatch_ref}#owner_route" if dispatch_ref else None,
        _workspace_relative_ref(owner_result.get("record_path"), workspace_root=profile.workspace_root),
        f"quality-repair-batch:blocked_reason={blocked_reason}",
        _owner_route_ref("truth_epoch", owner_route),
        _owner_route_ref("runtime_health_epoch", owner_route),
        _owner_route_ref("route_epoch", owner_route),
        _owner_route_ref("work_unit_fingerprint", owner_route),
        _owner_route_ref("source_fingerprint", owner_route),
        _owner_route_ref("idempotency_key", owner_route),
        _owner_route_ref("required_output_surface", dispatch),
        _owner_route_ref("prompt_required_output_surface", prompt_contract),
    ]
    return _unique_texts(refs)


def _owner_route_ref(key: str, payload: Mapping[str, Any]) -> str | None:
    if text := _text(payload.get(key)):
        return f"owner-route:{key}={text}"
    return None


def _workspace_relative_ref(value: object, *, workspace_root: Path) -> str | None:
    text = _text(value)
    if text is None:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        return text
    try:
        return str(path.resolve().relative_to(workspace_root.expanduser().resolve()))
    except ValueError:
        return str(path.resolve())


def _unique_texts(values: list[str | None]) -> list[str]:
    refs: list[str] = []
    for value in values:
        text = _text(value)
        if text is not None and text not in refs:
            refs.append(text)
    return refs


def _dispatch_consumes_quality_repair_writer_handoff(dispatch: Mapping[str, Any]) -> bool:
    if _text(dispatch.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(dispatch.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(dispatch.get("next_executable_owner")) != "write":
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return False
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return False
    route = _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    return _text(route.get("next_owner")) == "write" and route_reason == "manuscript_story_surface_delta_missing"


def _writer_stage_attempt_handoff_execution(*, dispatch: Mapping[str, Any], quest_root: Path) -> dict[str, Any]:
    required_output_surface = _text(dispatch.get("required_output_surface")) or _text(
        _mapping(dispatch.get("prompt_contract")).get("required_output_surface")
    )
    if not has_opl_transition_readback(dispatch):
        return {
            "execution_status": "blocked",
            "blocked_reason": "opl_execution_authorization_required",
            "typed_blocker": opl_execution_authorization_typed_blocker(),
            "owner_callable_surface": None,
            "writer_worker_handoff": dict(dispatch),
            "adapter_kind": "opl_authorized_owner_callable_adapter",
            "target_runtime_owner": "one-person-lab",
            "mas_private_attempt_loop_forbidden": True,
            "mas_dispatch_authority": False,
            "mas_creates_opl_outbox": False,
            "mas_creates_opl_event": False,
            "mas_creates_opl_stage_run": False,
            "provider_admission_pending": False,
            "provider_admission_requires_opl_runtime_result": True,
            "provider_attempt_or_lease_required": False,
            "opl_transition_runtime_required": True,
            "provider_completion_is_domain_completion": False,
            "domain_completion_authorized": False,
            "required_next_owner": "write",
            "required_output_surface": required_output_surface,
            "quest_root": str(quest_root),
        }
    return {
        "execution_status": "handoff_ready",
        "blocked_reason": None,
        "owner_callable_surface": "opl_default_executor.stage_attempt",
        "writer_worker_handoff": dict(dispatch),
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "domain_completion_authorized": False,
        "required_next_owner": "write",
        "required_output_surface": required_output_surface,
        "stage_attempt_admission": _stage_attempt_admission_payload(dispatch),
        "owner_result": {
            "status": "handoff_ready",
            "paper_work_done": [
                "Prepared writer owner handoff for a canonical manuscript story-surface delta or typed blocker."
            ],
            "writer_worker_handoff_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
        },
        "quest_root": str(quest_root),
    }


def _provider_stage_attempt_handoff_fields(
    *,
    dispatch: Mapping[str, Any],
    required_output_surface: str | None,
) -> dict[str, Any]:
    return {
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "domain_completion_authorized": False,
        "required_next_owner": "write",
        "required_output_surface": required_output_surface,
        "stage_attempt_admission": _stage_attempt_admission_payload(dispatch),
    }


def _stage_attempt_admission_payload(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": "opl_stage_attempt_admission_request",
        "schema_version": 1,
        "status": "requested",
        "owner": "one-person-lab",
        "domain": "med-autoscience",
        "action_type": "run_quality_repair_batch",
        "dispatch_authority": _text(dispatch.get("dispatch_authority")) or "quality_repair_batch_writer_handoff",
        "provider_completion_is_domain_completion": False,
        "domain_completion_authorized": False,
        "required_closeout_packet": _mapping(dispatch.get("required_closeout_packet"))
        or _mapping(_mapping(dispatch.get("prompt_contract")).get("required_closeout_packet")),
    }


def _quality_repair_handoff_blocker(result_payload: Mapping[str, Any]) -> str:
    evidence = _mapping(result_payload.get("repair_execution_evidence"))
    for candidate in (
        result_payload.get("blocked_reason"),
        _first_text(evidence.get("blockers")),
        _first_text(_mapping(evidence.get("manuscript_surface_hygiene")).get("blockers")),
        _mapping(result_payload.get("writer_worker_handoff")).get("typed_blocker_if_unresolved"),
    ):
        if text := _text(candidate):
            return text
    return "manuscript_story_surface_delta_missing"


def _first_text(value: object) -> str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if text := _text(item):
            return text
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _owner_route_currentness_basis(
    *,
    owner_route: Mapping[str, Any],
    owner_route_source_refs: Mapping[str, Any],
) -> dict[str, Any]:
    return _mapping(owner_route_source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )


def _materialized_owner_route_work_unit_id(source_refs: Mapping[str, Any]) -> str | None:
    if _text(source_refs.get("bridge_authority")) != "domain_action_request_materializer_story_surface_bridge":
        return None
    if _text(source_refs.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return None
    return _text(source_refs.get("materialized_work_unit_id"))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["execute_quality_repair_batch"]
