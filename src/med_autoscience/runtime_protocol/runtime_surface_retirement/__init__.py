from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .authority_flags import truthy_authority_flags


SURFACE_KIND = "mas_runtime_surface_retirement_no_authority_audit"
INVENTORY_KIND = "mas_runtime_surface_retirement_inventory"
INVENTORY_VERSION = "mas-runtime-surface-retirement-inventory.v2"
GENERIC_RUNTIME_OWNER = "one-person-lab"
ALLOWED_DISPOSITIONS = frozenset(
    {
        "physically_retired",
        "retained_domain_authority_adapter",
        "retained_read_only_projection",
        "retained_opl_authorized_adapter",
    }
)
ALLOWED_SURFACE_KEYS = frozenset(
    {
        "surface_id",
        "disposition",
        "replacement_ref",
        "tombstone_ref",
        "retained_mas_role",
        "mas_runtime_authority",
    }
)
FORBIDDEN_RESURRECTED_SURFACE_IDS = frozenset(
    {
        "domain_diagnostic_obligation_actuator",
        "mas_generic_runtime_lifecycle_contract",
        "mas_generic_runtime_lifecycle_read_model",
        "mas_generic_runtime_session_read_model",
        "mas_generic_quest_materializer",
    }
)


def audit_runtime_surface_retirement_inventory(
    inventory: Mapping[str, Any],
) -> dict[str, Any]:
    violations = validate_runtime_surface_retirement_inventory(inventory)
    surfaces = _surfaces(inventory)
    retired = [item["surface_id"] for item in surfaces if item.get("disposition") == "physically_retired"]
    retained = [item["surface_id"] for item in surfaces if item.get("disposition") != "physically_retired"]
    return {
        "surface_kind": SURFACE_KIND,
        "version": INVENTORY_VERSION,
        "status": "passed" if not violations else "failed",
        "generic_runtime_owner": GENERIC_RUNTIME_OWNER,
        "inventory_contract_valid": not violations,
        "repo_no_authority_guard_satisfied": not violations,
        "retired_surface_ids": retired,
        "retained_tail_surface_ids": retained,
        "retired_surface_count": len(retired),
        "retained_tail_count": len(retained),
        "physical_delete_allowed": False,
        "live_runtime_readiness_claim_allowed": False,
        "completion_claim_allowed": False,
        "replacement_readback_owner": GENERIC_RUNTIME_OWNER,
        "violations": violations,
        "forbidden_completion_interpretations": [
            "static_inventory_as_live_runtime_readiness",
            "repo_no_authority_guard_as_owner_receipt",
            "replacement_ref_as_live_replacement_readback",
            "retained_tail_as_physical_delete_authorization",
        ],
    }


def validate_runtime_surface_retirement_inventory(
    inventory: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if inventory.get("surface_kind") != INVENTORY_KIND:
        violations.append(_violation("<inventory>", "surface_kind_mismatch"))
    if inventory.get("version") != INVENTORY_VERSION:
        violations.append(_violation("<inventory>", "version_mismatch"))
    if inventory.get("schema_ref") != "contracts/runtime/mas-runtime-surface-retirement.schema.json":
        violations.append(_violation("<inventory>", "schema_ref_mismatch"))
    if inventory.get("generic_runtime_owner") != GENERIC_RUNTIME_OWNER:
        violations.append(_violation("<inventory>", "generic_runtime_owner_mismatch"))

    raw_surfaces = inventory.get("surfaces")
    if not isinstance(raw_surfaces, list):
        return [*violations, _violation("<inventory>", "surfaces_not_list")]

    seen: set[str] = set()
    for index, raw_surface in enumerate(raw_surfaces):
        if not isinstance(raw_surface, Mapping):
            violations.append(_violation(f"<surface:{index}>", "surface_not_object"))
            continue
        surface_id = _text(raw_surface.get("surface_id")) or f"<surface:{index}>"
        if surface_id in seen:
            violations.append(_violation(surface_id, "duplicate_surface_id"))
        seen.add(surface_id)
        if surface_id in FORBIDDEN_RESURRECTED_SURFACE_IDS:
            violations.append(_violation(surface_id, "forbidden_surface_resurrected"))
        unknown_keys = sorted(set(raw_surface) - ALLOWED_SURFACE_KEYS)
        if unknown_keys:
            violations.append(
                _violation(surface_id, f"unsupported_surface_fields:{','.join(unknown_keys)}")
            )
        disposition = _text(raw_surface.get("disposition"))
        if disposition not in ALLOWED_DISPOSITIONS:
            violations.append(_violation(surface_id, "invalid_disposition"))
        if raw_surface.get("mas_runtime_authority") is not False:
            violations.append(_violation(surface_id, "mas_runtime_authority_not_false"))
        retained_role = _text(raw_surface.get("retained_mas_role"))
        if retained_role is None:
            violations.append(_violation(surface_id, "missing_retained_mas_role"))
        replacement_ref = raw_surface.get("replacement_ref")
        tombstone_ref = raw_surface.get("tombstone_ref")
        if replacement_ref is not None and _text(replacement_ref) is None:
            violations.append(_violation(surface_id, "invalid_replacement_ref"))
        if tombstone_ref is not None and _text(tombstone_ref) is None:
            violations.append(_violation(surface_id, "invalid_tombstone_ref"))
        if disposition == "physically_retired":
            if retained_role != "none":
                violations.append(_violation(surface_id, "retired_surface_retains_mas_role"))
            if _text(tombstone_ref) is None:
                violations.append(_violation(surface_id, "retired_surface_missing_tombstone"))
        elif disposition in ALLOWED_DISPOSITIONS:
            if retained_role == "none":
                violations.append(_violation(surface_id, "retained_surface_missing_role"))
            if _text(replacement_ref) is None:
                violations.append(_violation(surface_id, "retained_surface_missing_replacement"))
        for path in truthy_authority_flags(raw_surface):
            violations.append(_violation(surface_id, f"forbidden_authority_flag:{path}"))
    return violations


def _surfaces(inventory: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    value = inventory.get("surfaces")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "ALLOWED_DISPOSITIONS",
    "FORBIDDEN_RESURRECTED_SURFACE_IDS",
    "audit_runtime_surface_retirement_inventory",
    "validate_runtime_surface_retirement_inventory",
]
