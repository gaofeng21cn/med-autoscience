from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.domain_route_profile import AGENT_ID, DOMAIN_ID, LEGACY_DOMAIN_IDS


PROFILE_ID = "medautoscience.next_action.profile.v1"
PROFILE_REF = "contracts/domain_projection_profile.json"
PROJECTION_SURFACE_KIND = "opl_domain_next_action_profile_projection"

_AUTHORITY_BOUNDARY = {
    "projection_is_authority": False,
    "can_write_domain_truth": False,
    "can_write_current_owner_delta": False,
    "can_write_stage_current_pointer": False,
    "can_write_stage_terminal_state": False,
    "can_create_owner_receipt": False,
    "can_create_typed_blocker": False,
    "can_create_human_gate": False,
    "can_mutate_artifact_body": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_ready": False,
    "provider_completion_is_domain_progress": False,
}


def build_domain_projection_profile() -> dict[str, Any]:
    return {
        "surface_kind": "opl_domain_next_action_profile",
        "schema_version": 1,
        "profile_id": PROFILE_ID,
        "agent_id": AGENT_ID,
        "domain_id": DOMAIN_ID,
        "legacy_domain_ids": list(LEGACY_DOMAIN_IDS),
        "projection_surface_kind": PROJECTION_SURFACE_KIND,
        "projection_owner": "MedAutoScience",
        "host_owner": "one-person-lab",
        "source_paths": [
            "src/med_autoscience/controllers/next_action_envelope.py",
            "src/med_autoscience/domain_projection_profile.py",
            "src/med_autoscience/controllers/study_launch_projection.py",
            "src/med_autoscience/controllers/study_task_submission.py",
        ],
        "surface_kinds": {
            "domain_projection": "opl_domain_projection",
            "next_action": PROJECTION_SURFACE_KIND,
            "domain_display": "mas_workspace_domain_display",
        },
        "field_mapping": {
            "work_unit_id": "next_action.work_unit_id",
            "work_unit_fingerprint": "next_action.work_unit_fingerprint",
            "status": "next_action.action_kind",
            "current_owner": "next_action.owner",
            "stage_id": "next_action.stage_id",
            "action_type": "next_action.action_type",
            "currentness_basis": "next_action.diagnostic_refs",
            "source_refs": [
                "next_action.required_input_refs",
                "next_action.diagnostic_refs",
            ],
        },
        "authority_refs": [
            "src/med_autoscience/controllers/next_action_envelope.py#compile_next_action_envelope",
            "contracts/domain_descriptor.json#/authority_boundary",
            "contracts/owner_receipt_contract.json",
        ],
        "generic_fields": [
            "domain_id",
            "work_unit_id",
            "work_unit_fingerprint",
            "status",
            "current_owner",
            "stage_id",
            "action_type",
            "currentness_basis",
            "source_refs",
            "authority_boundary",
        ],
        "domain_display_extension": {
            "field": "domain_display",
            "interpretation": "opaque_domain_owned_display_payload",
            "opl_may_probe_fields": False,
        },
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }


def build_domain_next_action_projection(
    next_action: Mapping[str, Any],
    *,
    domain_display: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    currentness_basis = {"diagnostic_refs": list(next_action.get("diagnostic_refs") or [])}
    source_refs = _text_list(next_action.get("required_input_refs"))
    source_refs.extend(
        ref
        for ref in _text_list(next_action.get("diagnostic_refs"))
        if ref not in source_refs
    )
    payload = {
        "surface_kind": PROJECTION_SURFACE_KIND,
        "schema_version": 1,
        "profile_ref": PROFILE_REF,
        "domain_id": DOMAIN_ID,
        "work_unit_id": _text(next_action.get("work_unit_id")),
        "work_unit_fingerprint": _text(next_action.get("work_unit_fingerprint")),
        "status": _text(next_action.get("action_kind")) or "unknown",
        "current_owner": _text(next_action.get("owner")),
        "stage_id": _text(next_action.get("stage_id")),
        "action_type": _text(next_action.get("action_type")),
        "currentness_basis": currentness_basis,
        "source_refs": source_refs,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    if domain_display:
        payload["domain_display"] = dict(domain_display)
    return payload


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


__all__ = [
    "PROFILE_ID",
    "PROFILE_REF",
    "PROJECTION_SURFACE_KIND",
    "build_domain_next_action_projection",
    "build_domain_projection_profile",
]
