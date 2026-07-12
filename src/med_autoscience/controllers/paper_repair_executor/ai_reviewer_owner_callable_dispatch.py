from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_callable_action_policy import FORBIDDEN_SURFACES
from med_autoscience.controllers.runtime_ai_repair_policy import owner_callable_policy


def build(
    *,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    action_type: str,
    owner_route: Mapping[str, Any],
    dispatch_path: Path,
    request: Mapping[str, Any],
    surface: str,
    schema_version: int,
    callable_surface: str,
    opl_execution_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    work_unit_fingerprint = _text(owner_route.get("work_unit_fingerprint"))
    has_opl_authorization = bool(opl_execution_authorization)
    dispatch_status = "ready"
    prompt_contract = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": dict(owner_route),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
        "request_packet_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
        "source": surface,
        "opl_execution_authorization": dict(opl_execution_authorization or {}),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": ["artifacts/supervision/**"],
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "opl_execution_authorization_required": False,
        "opl_execution_authorization_present": has_opl_authorization,
        "owner_callable_requires_opl_authorization": False,
    }
    return {
        "surface": "mas_ai_route_context_projection",
        "schema_version": schema_version,
        **owner_callable_policy(),
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-repair::{study_id}::{action_type}::{_work_unit_id(work_unit)}",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "dispatch_status": dispatch_status,
        "dispatch_authority": "paper_repair_executor_inline_owner_dispatch",
        "owner_route": dict(owner_route),
        "opl_execution_authorization": dict(opl_execution_authorization or {}),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "action_fingerprint": work_unit_fingerprint,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "prompt_contract": prompt_contract,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "opl_execution_authorization_required": False,
        "opl_execution_authorization_present": has_opl_authorization,
        "provider_admission_pending": False,
        "owner_callable_requires_opl_authorization": False,
        "mas_private_attempt_loop_forbidden": True,
        "source_action": {
            "surface": surface,
            "work_unit_id": _work_unit_id(work_unit),
            "work_unit_type": _text(work_unit.get("work_unit_type")),
            "callable_surface": callable_surface,
            "request_path": _text(request.get("path")),
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "request_packet_path": _text(request.get("path")),
        },
    }


def _work_unit_id(work_unit: Mapping[str, Any]) -> str:
    return _text(work_unit.get("work_unit_id")) or _text(work_unit.get("id")) or "unknown-work-unit"


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
