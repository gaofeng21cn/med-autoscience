from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience import external_learning_adoption_closure
from med_autoscience.profiles import WorkspaceProfile


REQUEST_RELATIVE_PATH = external_learning_adoption_closure.REQUEST_RELATIVE_PATH


def execute(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = profile.studies_root / study_id
    request_path = study_root / REQUEST_RELATIVE_PATH
    request = _request(study_id=study_id, dispatch=dispatch or {})
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": external_learning_adoption_closure.SIDECAR_CALLABLE_SURFACE,
            "request_path": str(request_path),
            "result_path": None,
            "next_owner": external_learning_adoption_closure.SIDECAR_OWNER,
            "status": "opl_capability_request_preview",
            "request_only": True,
            "mas_local_capability_actuator": False,
            "mas_can_invoke_capability_sidecar": False,
            "opl_capability_runtime_required": True,
            "opl_capability_invocation_request": _opl_capability_invocation_request(
                study_root=study_root,
                request_path=request_path,
                request=request,
                dispatch=dispatch or {},
            ),
        }
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request["path"] = str(request_path)
    request_path.write_text(
        json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "execution_status": "blocked",
        "blocked_reason": "opl_capability_runtime_required",
        "typed_blocker": {
            "blocker_type": "opl_capability_runtime_required",
            "owner": "one-person-lab",
            "target_runtime_kind": "CapabilityRegistry",
            "target_runtime_owner": "one-person-lab",
            "reason": "external_learning_sidecar_owner_action_requires_opl_capability_runtime",
            "request_ref": str(request_path),
        },
        "owner_callable_surface": external_learning_adoption_closure.SIDECAR_CALLABLE_SURFACE,
        "next_owner": external_learning_adoption_closure.SIDECAR_OWNER,
        "status": "opl_capability_request_pending",
        "request_only": True,
        "mas_local_capability_actuator": False,
        "mas_can_invoke_capability_sidecar": False,
        "opl_capability_runtime_required": True,
        "opl_capability_invocation_request": _opl_capability_invocation_request(
            study_root=study_root,
            request_path=request_path,
            request=request,
            dispatch=dispatch or {},
        ),
        "request_path": str(request_path),
        "result_path": None,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
    }


def _request(*, study_id: str, dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_action = _mapping(dispatch.get("source_action"))
    required_output_surface = _text(dispatch.get("required_output_surface")) or _text(
        prompt_contract.get("required_output_surface")
    )
    return {
        "surface": "domain_action_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
        "request_kind": external_learning_adoption_closure.SIDECAR_ACTION_TYPE,
        "request_owner": external_learning_adoption_closure.SIDECAR_OWNER,
        "assigned_to": external_learning_adoption_closure.SIDECAR_OWNER,
        "status": "requested",
        "blocked_reason": None,
        "next_owner": external_learning_adoption_closure.SIDECAR_OWNER,
        "next_work_unit": external_learning_adoption_closure.SIDECAR_ACTION_TYPE,
        "required_output_surface": required_output_surface
        or external_learning_adoption_closure.SIDECAR_RESULT_RELATIVE_PATH.as_posix(),
        "owner_route": owner_route,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(dispatch.get("repeat_suppression_key"))
        or _text(prompt_contract.get("repeat_suppression_key")),
        "source_action_ref": {
            "action_type": _text(dispatch.get("action_type")) or _text(source_action.get("action_type")),
            "action_id": _text(dispatch.get("action_id")) or _text(source_action.get("action_id")),
            "dispatch_authority": _text(dispatch.get("dispatch_authority")),
            "dispatch_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
        },
        "input_contract": {
            "required_refs": {
                "current_owner_action": {"source": "dispatch_or_owner_route"},
                "external_learning_adoption_closure": {
                    "builder_ref": (
                        "med_autoscience.external_learning_adoption_closure."
                        "build_external_learning_adoption_closure"
                    )
                },
            },
            "sidecar_requirements": [
                "emit refs-only advisory candidates",
                "surface contract-only learning gaps without blocking the current owner",
                "preserve owner policy and forbidden authority boundaries",
            ],
        },
        "required_output": {
            "accepted_evidence": external_learning_adoption_closure.SIDECAR_RESULT_RELATIVE_PATH.as_posix(),
            "accepted_typed_blocker": None,
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "mainline_waits_for_sidecar": False,
        "forbidden_writes": list(external_learning_adoption_closure.FORBIDDEN_WRITES),
        "request_only": True,
        "mas_local_capability_actuator": False,
        "mas_can_invoke_capability_sidecar": False,
        "opl_capability_runtime_required": True,
        "target_runtime_owner": "one-person-lab",
        "target_runtime_kind": "CapabilityRegistry",
    }


def _opl_capability_invocation_request(
    *,
    study_root: Path,
    request_path: Path,
    request: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_capability_invocation_request",
        "schema_version": 1,
        "target_runtime_owner": "one-person-lab",
        "target_runtime_kind": "CapabilityRegistry",
        "capability_family": "external_learning_sidecar",
        "capability_id": "external_learning_owner_action_advisory",
        "request_ref": str(request_path),
        "study_root_ref": str(study_root),
        "action_type": _text(dispatch.get("action_type"))
        or _text(_mapping(request.get("source_action_ref")).get("action_type"))
        or external_learning_adoption_closure.SIDECAR_ACTION_TYPE,
        "work_unit_fingerprint": _text(request.get("work_unit_fingerprint")),
        "output_refs": [external_learning_adoption_closure.SIDECAR_RESULT_RELATIVE_PATH.as_posix()],
        "mas_can_run_capability_actuator": False,
        "mas_local_capability_actuator": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["REQUEST_RELATIVE_PATH", "execute"]
