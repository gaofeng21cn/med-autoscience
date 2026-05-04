from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def operation_field_status(
    *,
    value_present: bool,
    nominal_primary_evidence: bool,
    waiver_reason: str,
    waiver_allowed: bool,
    waiver_incomplete: bool,
) -> str:
    if waiver_incomplete:
        return "blocked"
    if value_present and not nominal_primary_evidence:
        return "waived" if waiver_reason and waiver_allowed else "present"
    if waiver_reason and waiver_allowed:
        return "waived"
    return "blocked"


def operation_field_blockers(
    *,
    field: str,
    value_present: bool,
    nominal_primary_evidence: bool,
    waiver_reason: str,
    waiver_allowed: bool,
    waiver_incomplete: bool,
) -> list[str]:
    blockers = []
    if not value_present and (not waiver_reason or not waiver_allowed):
        blockers.append(f"missing_{field}")
    if waiver_incomplete and waiver_allowed:
        blockers.append(f"incomplete_{field}_waiver")
    if nominal_primary_evidence:
        blockers.append("nominal_p_value_primary_evidence")
    if waiver_reason and not waiver_allowed:
        blockers.append(f"{field}_waiver_not_allowed")
    return blockers


def reviewer_template_field_projection(
    *,
    field: str,
    template: dict[str, Any],
    waiver_reason: str,
    waiver_incomplete: bool,
    waiver_allowed: bool,
    value_present: bool,
    nominal_primary_evidence: bool,
) -> tuple[list[str], dict[str, object]]:
    status = operation_field_status(
        value_present=value_present,
        nominal_primary_evidence=nominal_primary_evidence,
        waiver_reason=waiver_reason,
        waiver_allowed=waiver_allowed,
        waiver_incomplete=waiver_incomplete,
    )
    field_blockers = operation_field_blockers(
        field=field,
        value_present=value_present,
        nominal_primary_evidence=nominal_primary_evidence,
        waiver_reason=waiver_reason,
        waiver_allowed=waiver_allowed,
        waiver_incomplete=waiver_incomplete,
    )
    updated_template = dict(template)
    updated_template["status"] = status
    updated_template["required_for_ready"] = status == "blocked"
    updated_template["blockers"] = field_blockers
    updated_template["waiver_reason"] = waiver_reason if waiver_reason and waiver_allowed else ""
    return field_blockers, updated_template


def waiver_allowed_from_template(template: Mapping[str, Any]) -> bool:
    waiver_requirements = template.get("waiver_reason_requirements")
    return isinstance(waiver_requirements, Mapping) and waiver_requirements.get("waiver_allowed") is True
