"""Generic fail-closed contract binding validation for shared OPL capability packages."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


REQUIRED_NON_USABLE_OBSERVATIONS = frozenset(
    {
        "missing",
        "incompatible",
        "disabled",
        "unmaterialized",
        "unobserved",
    }
)


class CapabilityBindingError(ValueError):
    """Raised when a capability binding contract or invocation envelope violates boundaries."""


def validate_required_capability_binding_contract(
    payload: Any,
    *,
    expected_surface_kind: str,
    expected_version: str,
    expected_consumer_agent_id: str,
    expected_provider_package_id: str,
    expected_consumer_profile_id: str,
    provider_completion_field: str,
    required_block_fields: Iterable[str],
    non_usable_action: str,
    identity_error: str = "Capability binding contract identity is invalid.",
    boundary_error: str = "Capability binding contract boundary is invalid.",
) -> dict[str, Any]:
    """Validate identity, handoff mode, fail-closed block flags, and authority boundaries."""

    if (
        not isinstance(payload, Mapping)
        or payload.get("surface_kind") != expected_surface_kind
        or payload.get("version") != expected_version
        or payload.get("consumer_agent_id") != expected_consumer_agent_id
        or payload.get("provider_package_id") != expected_provider_package_id
        or payload.get("consumer_profile_id") != expected_consumer_profile_id
    ):
        raise CapabilityBindingError(identity_error)

    eligible_export_ids = payload.get("eligible_export_ids")
    direct_route_bindings = payload.get("direct_route_bindings")
    invocation_policy = payload.get("invocation_policy")
    availability_policy = payload.get("availability_policy")
    authority_boundary = payload.get("authority_boundary")
    known_non_usable_observations = (
        availability_policy.get("known_non_usable_observations")
        if isinstance(availability_policy, Mapping)
        else None
    )

    if (
        payload.get("enhancement_kind") != "required_dependency"
        or payload.get("handoff_mode") != "refs_only"
        or payload.get("provider_required") is not True
        or not isinstance(eligible_export_ids, list)
        or not eligible_export_ids
        or not all(isinstance(item, str) and item for item in eligible_export_ids)
        or not isinstance(direct_route_bindings, Mapping)
        or not isinstance(invocation_policy, Mapping)
        or invocation_policy.get(provider_completion_field) is not False
        or invocation_policy.get("provider_gap_is_hard_stop") is not True
        or invocation_policy.get("provider_gap_can_create_typed_blocker") is not False
        or invocation_policy.get("provider_gap_can_select_stage_route") is not False
        or not isinstance(availability_policy, Mapping)
        or availability_policy.get("usable_observation") != "available_compatible"
        or not isinstance(known_non_usable_observations, list)
        or not all(isinstance(item, str) and item for item in known_non_usable_observations)
        or not REQUIRED_NON_USABLE_OBSERVATIONS.issubset(set(known_non_usable_observations))
        or "available_compatible" in known_non_usable_observations
        or availability_policy.get("available_compatible_action") != "select_required_declared_skills"
        or availability_policy.get("other_observation_action") != non_usable_action
        or availability_policy.get("accepted_gap_outputs") != ["diagnostic", "typed_blocker_ref"]
        or availability_policy.get("quality_hint_is_advisory") is not False
        or availability_policy.get("creates_typed_blocker") is not False
        or any(availability_policy.get(field) is not True for field in required_block_fields)
        or not isinstance(authority_boundary, Mapping)
        or not authority_boundary
        or any(value is not False for value in authority_boundary.values())
    ):
        raise CapabilityBindingError(boundary_error)
    return dict(payload)


def select_direct_route_exports(
    contract: Mapping[str, Any],
    route_id: str,
    *,
    route_bindings_key: str = "direct_route_bindings",
    eligible_exports_key: str = "eligible_export_ids",
    missing_route_error: str | None = None,
    undeclared_export_error_prefix: str = "Direct route references undeclared capability exports: ",
) -> list[str]:
    """Return validated export IDs bound to `route_id` within `eligible_export_ids`."""

    bindings = contract.get(route_bindings_key)
    selected = bindings.get(route_id) if isinstance(bindings, Mapping) else None
    if (
        not isinstance(selected, list)
        or not selected
        or not all(isinstance(item, str) and item for item in selected)
    ):
        raise CapabilityBindingError(
            missing_route_error or f"Direct route missing capability binding: {route_id}"
        )
    eligible_export_ids = set(contract.get(eligible_exports_key, []))
    undeclared = [skill_id for skill_id in selected if skill_id not in eligible_export_ids]
    if undeclared:
        raise CapabilityBindingError(
            f"{undeclared_export_error_prefix}{', '.join(undeclared)}"
        )
    return list(selected)


def validate_refs_only_skill_invocation_envelope(
    payload: Mapping[str, Any],
    *,
    field: str,
    expected_surface_kind: str,
    expected_provider_package_id: str,
    allowed_skill_ids: set[str] | frozenset[str],
    forbidden_false_flags: Sequence[str] = ("authority",),
) -> tuple[str, list[str]]:
    """Validate common refs-only skill invocation headers and return `(skill_id, consumed_rule_refs)`."""

    if payload.get("surface_kind") != expected_surface_kind:
        raise CapabilityBindingError(
            f"{field}.surface_kind must be {expected_surface_kind}"
        )
    raw_skill_id = payload.get("skill_id")
    if not isinstance(raw_skill_id, str) or not raw_skill_id.strip():
        raise CapabilityBindingError(f"{field}.skill_id must be a non-empty string")
    skill_id = raw_skill_id.strip()
    if skill_id not in allowed_skill_ids:
        raise CapabilityBindingError(
            f"{field}.skill_id must be one of: {', '.join(sorted(allowed_skill_ids))}"
        )
    if payload.get("package_id") != expected_provider_package_id:
        raise CapabilityBindingError(
            f"{field}.package_id must be {expected_provider_package_id}"
        )
    if payload.get("status") != "completed":
        raise CapabilityBindingError(f"{field}.status must be completed")
    if payload.get("refs_only") is not True:
        raise CapabilityBindingError(f"{field}.refs_only must be true")
    for flag in forbidden_false_flags:
        if payload.get(flag) is not False:
            raise CapabilityBindingError(f"{field}.{flag} must be false")

    raw_rules = payload.get("consumed_rule_refs")
    if isinstance(raw_rules, (str, bytes, bytearray)) or not isinstance(raw_rules, Sequence):
        raise CapabilityBindingError(f"{field}.consumed_rule_refs must be an array")
    consumed_rule_refs: list[str] = []
    for index, item in enumerate(raw_rules):
        if not isinstance(item, str) or not item.strip():
            raise CapabilityBindingError(
                f"{field}.consumed_rule_refs[{index}] must be a non-empty string"
            )
        consumed_rule_refs.append(item.strip())
    if len(consumed_rule_refs) != len(set(consumed_rule_refs)):
        raise CapabilityBindingError(f"{field}.consumed_rule_refs contains duplicates")
    if not consumed_rule_refs:
        raise CapabilityBindingError(f"{field}.consumed_rule_refs must not be empty")
    return skill_id, consumed_rule_refs


__all__ = [
    "CapabilityBindingError",
    "REQUIRED_NON_USABLE_OBSERVATIONS",
    "select_direct_route_exports",
    "validate_refs_only_skill_invocation_envelope",
    "validate_required_capability_binding_contract",
]
