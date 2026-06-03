from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import current_writer_handoff
from .action_execution_parts import ai_reviewer_record_production


def persisted_handoff_supersedes_consumer_inline(
    *,
    study_id: str,
    action_type: str,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
    owner_request_current: bool,
) -> bool:
    if _persisted_quality_repair_writer_handoff_supersedes_consumer_inline(
        study_id=study_id,
        action_type=action_type,
        consumer_dispatch=consumer_dispatch,
        persisted_dispatch=persisted_dispatch,
        owner_request_current=owner_request_current,
    ):
        return True
    return _persisted_record_only_handoff_supersedes_consumer_inline(
        action_type=action_type,
        consumer_dispatch=consumer_dispatch,
        persisted_dispatch=persisted_dispatch,
        owner_request_current=owner_request_current,
    )


def _persisted_quality_repair_writer_handoff_supersedes_consumer_inline(
    *,
    study_id: str,
    action_type: str,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
    owner_request_current: bool,
) -> bool:
    if not current_writer_handoff.self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=action_type,
        dispatch=persisted_dispatch,
    ):
        return False
    if not owner_request_current:
        return False
    return not current_writer_handoff.self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=_text(consumer_dispatch.get("action_type")) or "",
        dispatch=consumer_dispatch,
    )


def _persisted_record_only_handoff_supersedes_consumer_inline(
    *,
    action_type: str,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
    owner_request_current: bool,
) -> bool:
    if action_type != ai_reviewer_record_production.ACTION_TYPE:
        return False
    if _text(persisted_dispatch.get("dispatch_authority")) != ai_reviewer_record_production.DISPATCH_AUTHORITY:
        return False
    if _text(persisted_dispatch.get("required_output_surface")) != ai_reviewer_record_production.RECORD_OUTPUT_SURFACE:
        return False
    if not owner_request_current:
        return False
    return not (
        _text(consumer_dispatch.get("dispatch_authority")) == ai_reviewer_record_production.DISPATCH_AUTHORITY
        and _text(consumer_dispatch.get("required_output_surface"))
        == ai_reviewer_record_production.RECORD_OUTPUT_SURFACE
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["persisted_handoff_supersedes_consumer_inline"]
