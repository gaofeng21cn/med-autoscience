from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REASON = "study_completion_contract_not_ready"
OWNER = "completion_evidence"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    contract = _mapping(status.get("study_completion_contract")) or _mapping(progress.get("study_completion_contract"))
    if _text(status.get("reason")) != REASON:
        return False
    return _text(contract.get("status")) == "incomplete" or contract.get("ready") is False


def block_state(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any] | None:
    if not required(status, progress):
        return None
    return {
        "blocked_reason": REASON,
        "next_owner": OWNER,
        "external_supervisor_required": False,
    }


def completed_current_truth(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("decision")) == "completed":
        return True
    if _text(status.get("quest_status")) != "completed":
        return False
    contract = _mapping(status.get("study_completion_contract")) or _mapping(progress.get("study_completion_contract"))
    return contract.get("ready") is True and _text(contract.get("status")) == "resolved"
