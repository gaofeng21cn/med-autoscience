from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer import FORBIDDEN_SURFACES
from med_autoscience.controllers.runtime_ai_repair_policy import default_executor_policy
from med_autoscience.runtime_control import repeat_suppression


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
    repeat_key = repeat_suppression.repeat_key(owner_route)
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
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "request_packet_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
        "source": surface,
        "opl_execution_authorization": dict(opl_execution_authorization or {}),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": ["artifacts/supervision/**"],
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": schema_version,
        **default_executor_policy(),
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-repair::{study_id}::{action_type}::{_work_unit_id(work_unit)}",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "dispatch_status": "ready",
        "dispatch_authority": "paper_repair_executor_inline_owner_dispatch",
        "owner_route": dict(owner_route),
        "opl_execution_authorization": dict(opl_execution_authorization or {}),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": repeat_key,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "prompt_contract": prompt_contract,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
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
