from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import provenance_limited_harmonization_owner
from med_autoscience.profiles import WorkspaceProfile


REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/provenance_limited_harmonization/latest.json")


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
            "owner_callable_surface": (
                "provenance_limited_harmonization_owner."
                "provenance_limited_harmonization_audit_or_typed_blocker"
            ),
            "request_path": str(request_path),
            "next_owner": "provenance_limited_harmonization_owner",
        }
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request["path"] = str(request_path)
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    owner_execution = provenance_limited_harmonization_owner.provenance_limited_harmonization_audit_or_typed_blocker(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
        request=request,
        apply=True,
    )
    owner_result = _mapping(owner_execution.get("owner_result"))
    owner_result["request_path"] = str(request_path)
    owner_result["request_kind"] = "provenance_limited_harmonization_audit"
    return {**owner_execution, "owner_result": owner_result, "request_path": str(request_path)}


def _request(*, study_id: str, dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    required_output_surface = _text(dispatch.get("required_output_surface")) or _text(
        prompt_contract.get("required_output_surface")
    )
    if required_output_surface is None:
        required_output_surface = (
            "provenance-limited harmonization audit or "
            "typed blocker:provenance_limited_harmonization_audit_required"
        )
    return {
        "surface": "domain_action_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
        "request_kind": "provenance_limited_harmonization_audit",
        "request_owner": "provenance_limited_harmonization_owner",
        "assigned_to": "provenance_limited_harmonization_owner",
        "status": "requested",
        "blocked_reason": "provenance_limited_harmonization_audit_required",
        "next_owner": "provenance_limited_harmonization_owner",
        "next_work_unit": "provenance_limited_harmonization_audit",
        "required_output_surface": required_output_surface,
        "owner_route": owner_route,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(dispatch.get("repeat_suppression_key"))
        or _text(prompt_contract.get("repeat_suppression_key")),
        "source_action_ref": {
            "action_type": _text(dispatch.get("action_type")),
            "action_id": _text(dispatch.get("action_id")),
            "dispatch_authority": _text(dispatch.get("dispatch_authority")),
            "dispatch_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
            "source_ref": _text(source_action.get("source_ref")),
        },
        "input_contract": {
            "required_refs": {
                "controller_decision": {"relative_path": "artifacts/controller_decisions/latest.json"},
                "analysis_harmonization_owner_result": {
                    "relative_path": "artifacts/controller/analysis_harmonization/latest.json"
                },
                "source_provenance_owner_result": {
                    "relative_path": "artifacts/controller/source_provenance/latest.json"
                },
            },
            "audit_requirements": [
                "consume the terminal source-provenance blocker",
                "state that current raw transported-score results cannot support medical transportability conclusions",
                "choose among stop-loss, clean reproducible rebuild, or human-gate routes without editing paper surfaces",
            ],
        },
        "required_output": {
            "accepted_evidence": "provenance-limited harmonization audit",
            "accepted_typed_blocker": "provenance_limited_harmonization_audit_required",
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "REQUEST_RELATIVE_PATH",
    "execute",
]
