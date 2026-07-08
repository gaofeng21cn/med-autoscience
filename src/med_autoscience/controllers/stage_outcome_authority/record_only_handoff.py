from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_action_request_lifecycle import stable_ai_reviewer_request_path
from med_autoscience.profiles import WorkspaceProfile

from .action_execution.ai_reviewer_record_production import (
    build_ai_reviewer_record_worker_handoff,
)


def canonical_record_only_handoff_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    if _text(dispatch.get("dispatch_authority")) != "ai_reviewer_record_production_handoff":
        return dict(dispatch)
    if _record_only_prompt_contract_is_canonical(_mapping(dispatch.get("prompt_contract"))):
        return dict(dispatch)
    production_request = _mapping(dispatch.get("ai_reviewer_record_production_request")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("ai_reviewer_record_production_request")
    )
    if not production_request:
        return dict(dispatch)
    request_path = stable_ai_reviewer_request_path(study_root=profile.studies_root / study_id)
    request = _read_json_object(request_path) or {
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or study_id,
    }
    return build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request,
        dispatch=dispatch,
        production_request=production_request,
    )


def _record_only_prompt_contract_is_canonical(prompt_contract: Mapping[str, Any]) -> bool:
    if _text(prompt_contract.get("owner_callable_payload_ref")) is None:
        return False
    command = _text(prompt_contract.get("owner_callable_command"))
    if command is None:
        return False
    if "python3 -m med_autoscience.cli publication materialize-ai-reviewer-record" not in command:
        return False
    request = _mapping(prompt_contract.get("ai_reviewer_record_production_request"))
    if _text(request.get("owner_callable_runtime")) != "repo_local_python_module":
        return False
    allowed = {
        text
        for item in prompt_contract.get("allowed_write_surfaces") or []
        if (text := _text(item)) is not None
    }
    return {
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json",
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    }.issubset(allowed)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["canonical_record_only_handoff_dispatch"]
