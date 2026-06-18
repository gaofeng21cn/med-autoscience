from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def owner_delta_read_only_summary(projection: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(projection)
    owner = _non_empty_text(payload.get("owner"))
    action_type = _non_empty_text(payload.get("action_type"))
    work_unit_id = _non_empty_text(payload.get("work_unit_id"))
    required_delta_kind = _non_empty_text(payload.get("required_delta_kind"))
    owner_receipt_ref = _non_empty_text(payload.get("owner_receipt_ref"))
    typed_blocker_ref = _non_empty_text(payload.get("typed_blocker_ref"))

    parts = []
    if owner is not None:
        parts.append(f"owner={owner}")
    if action_type is not None:
        parts.append(f"action_type={action_type}")
    if required_delta_kind is not None:
        parts.append(f"required_delta={required_delta_kind}")
    if work_unit_id is not None:
        parts.append(f"work_unit_id={work_unit_id}")
    if owner_receipt_ref is not None:
        parts.append(f"owner_receipt_ref={owner_receipt_ref}")
    if typed_blocker_ref is not None:
        parts.append(f"typed_blocker_ref={typed_blocker_ref}")

    return {
        "surface_kind": "mas_progress_portal_owner_delta_read_only_summary",
        "status": "available" if parts else "missing",
        "summary": "; ".join(parts) if parts else None,
        "source": "current_owner_delta",
        "role": "read_only_owner_delta_summary",
        "projection_only": True,
        "can_generate_action": False,
        "can_execute": False,
        "can_authorize_provider_admission": False,
        "can_authorize_worker_attempt": False,
        "requires_opl_current_control_readback": True,
        "must_not_be_used_as_next_action_authority": True,
        "must_not_be_used_as_provider_admission": True,
        "must_not_be_used_as_paper_progress": True,
        "must_not_be_used_as_publication_ready": True,
    }


def legacy_next_action_diagnostic(*values: object) -> dict[str, Any]:
    texts = []
    for value in values:
        text = _non_empty_text(value)
        if text is None or text in texts:
            continue
        texts.append(text)
    return {
        "surface_kind": "mas_progress_portal_legacy_next_action_diagnostic",
        "status": "available" if texts else "missing",
        "values": texts,
        "role": "diagnostic_legacy_projection_input",
        "projection_only": True,
        "can_generate_action": False,
        "can_execute": False,
        "can_authorize_provider_admission": False,
        "can_authorize_worker_attempt": False,
        "must_not_be_used_as_next_action_authority": True,
        "must_not_be_used_as_provider_admission": True,
        "must_not_be_used_as_paper_progress": True,
        "must_not_be_used_as_publication_ready": True,
    }


def workbench_next_action_projection(
    projection: Mapping[str, Any] | None,
    *legacy_values: object,
) -> dict[str, Any]:
    summary = owner_delta_read_only_summary(projection)
    return {
        "user_next": summary["summary"],
        "user_next_role": "read_only_owner_delta_summary",
        "owner_delta_summary": summary,
        "legacy_next_action_diagnostic": legacy_next_action_diagnostic(*legacy_values),
        "next_action_summary": summary["summary"],
        "next_action_summary_role": "read_only_drilldown_summary",
        "next_action_summary_is_controller_action": False,
        "next_action_summary_can_generate_action": False,
        "next_action_summary_requires_opl_current_control_readback": True,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().split())
    return text or None
