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
REQUIRED_MAS_RETAINS = frozenset(
    {
        "medical_truth",
        "publication_quality",
        "artifact_mutation_authority",
        "source_readiness",
        "stage_outcome_authority",
        "owner_receipt",
        "typed_blocker",
    }
)
REQUIRED_OPL_OWNS = frozenset(
    {
        "queue",
        "attempt",
        "retry",
        "lifecycle",
        "state_index",
        "observability",
        "workbench_shell",
    }
)
REQUIRED_RETAINED_SURFACES = {
    "stage_outcome_authority": (
        "retained_domain_authority_adapter",
        "owner_callable_policy_and_typed_blocker_adapter",
        "opl:domain-progress-transition-runtime",
    ),
    "runtime_health_kernel": (
        "retained_read_only_projection",
        "body_free_diagnostic_projection",
        "opl:observability-readback",
    ),
    "progress_portal_study_workbench_overview_action_projection": (
        "retained_read_only_projection",
        "body_free_workbench_source_projection",
        "opl:hosted-workbench-shell",
    ),
    "agent_tool_arsenal_scientific_capability_registry": (
        "retained_read_only_projection",
        "declarative_capability_metadata_projection",
        "opl:capability-runtime",
    ),
    "runtime_lifecycle_payload_retention": (
        "retained_opl_authorized_adapter",
        "authorized_maintenance_callable_adapter",
        "opl:lifecycle-retention",
    ),
    "runtime_storage_maintenance": (
        "retained_opl_authorized_adapter",
        "authorized_storage_maintenance_adapter",
        "opl:storage-maintenance-and-restore",
    ),
}


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
    authority_boundary = inventory.get("authority_boundary")
    if not isinstance(authority_boundary, Mapping):
        violations.append(_violation("<inventory>", "authority_boundary_not_object"))
    else:
        if not _matches_exact_strings(
            authority_boundary.get("mas_retains"), REQUIRED_MAS_RETAINS
        ):
            violations.append(_violation("<inventory>", "mas_retains_mismatch"))
        if not _matches_exact_strings(
            authority_boundary.get("opl_owns"), REQUIRED_OPL_OWNS
        ):
            violations.append(_violation("<inventory>", "opl_owns_mismatch"))

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
    retained = {
        item["surface_id"]: item
        for item in raw_surfaces
        if isinstance(item, Mapping)
        and _text(item.get("surface_id")) is not None
        and item.get("disposition") != "physically_retired"
    }
    if set(retained) != set(REQUIRED_RETAINED_SURFACES):
        violations.append(_violation("<inventory>", "retained_surface_set_mismatch"))
    for surface_id, expected in REQUIRED_RETAINED_SURFACES.items():
        surface = retained.get(surface_id)
        if surface is None:
            continue
        actual = (
            surface.get("disposition"),
            surface.get("retained_mas_role"),
            surface.get("replacement_ref"),
        )
        if actual != expected:
            violations.append(_violation(surface_id, "retained_surface_contract_mismatch"))
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


def _matches_exact_strings(value: object, expected: frozenset[str]) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(expected)
        and all(isinstance(item, str) for item in value)
        and set(value) == expected
    )


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "ALLOWED_DISPOSITIONS",
    "FORBIDDEN_RESURRECTED_SURFACE_IDS",
    "REQUIRED_MAS_RETAINS",
    "REQUIRED_OPL_OWNS",
    "REQUIRED_RETAINED_SURFACES",
    "audit_runtime_surface_retirement_inventory",
    "validate_runtime_surface_retirement_inventory",
]
