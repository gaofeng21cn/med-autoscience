from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.current_work_unit.opl_profile import (
    PROFILE_REF as DOMAIN_PROJECTION_PROFILE_REF,
    build_domain_current_work_unit_projection,
)
from med_autoscience.domain_route_profile import DOMAIN_ID


OPL_HOSTED_OPERATOR_PROJECTION_REF = (
    "one-person-lab:src/modules/console/runtime-tray-app-operator-drilldown.ts"
)
OPL_CURRENT_OWNER_DELTA_REF = (
    "one-person-lab:src/modules/ledger/current-owner-delta-parts/projection.ts"
)


def build_workspace_domain_projection(
    *,
    study_progress_payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Expose MAS-owned refs; OPL Console owns aggregation and operator UX."""
    domain_display = [_study_refs(payload) for payload in study_progress_payloads]
    current_work_units = []
    for payload, display in zip(study_progress_payloads, domain_display, strict=True):
        current_work_unit = _mapping(payload.get("current_work_unit"))
        if current_work_unit:
            current_work_units.append(
                build_domain_current_work_unit_projection(
                    current_work_unit,
                    domain_display=display,
                )
            )
    return {
        "surface_kind": "opl_domain_projection",
        "schema_version": 1,
        "domain_id": DOMAIN_ID,
        "projection_profile_ref": DOMAIN_PROJECTION_PROFILE_REF,
        "projection_role": "registry_driven_domain_current_work_units",
        "current_work_units": current_work_units,
        "domain_display": {
            "surface_kind": "mas_workspace_domain_display",
            "opaque_to_opl": True,
            "studies": domain_display,
        },
        "opl_hosted_projection": {
            "owner": "one-person-lab",
            "operator_projection_ref": OPL_HOSTED_OPERATOR_PROJECTION_REF,
            "current_owner_delta_ref": OPL_CURRENT_OWNER_DELTA_REF,
            "mas_materializes_workspace_cockpit": False,
            "mas_aggregates_operator_attention": False,
            "mas_generates_operator_commands": False,
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "operator_projection_owner": "one-person-lab",
            "projection_can_execute_action": False,
            "projection_can_create_owner_receipt": False,
            "projection_can_create_typed_blocker": False,
            "projection_can_claim_publication_ready": False,
        },
    }


def _study_refs(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = {
        "study_id": _text(payload.get("study_id")),
        "quest_id": _text(payload.get("quest_id")),
        "current_owner_delta": _mapping(payload.get("current_owner_delta")) or None,
        "next_action_envelope": _mapping(payload.get("next_action_envelope")) or None,
        "study_truth_snapshot": _mapping(payload.get("study_truth_snapshot")) or None,
        "runtime_health_snapshot": _mapping(payload.get("runtime_health_snapshot")) or None,
        "authority_snapshot": _mapping(payload.get("authority_snapshot")) or None,
        "publication_eval": _mapping(payload.get("publication_eval")) or None,
        "medical_paper_readiness": _mapping(payload.get("medical_paper_readiness")) or None,
        "artifact_runtime_proof": _mapping(payload.get("artifact_runtime_proof")) or None,
        "current_blockers": _text_list(payload.get("current_blockers")),
        "owner_receipt_ref": _text(payload.get("owner_receipt_ref")),
        "typed_blocker_ref": _text(payload.get("typed_blocker_ref")),
        "human_gate": _mapping(payload.get("human_gate")) or None,
    }
    return {key: value for key, value in refs.items() if value not in (None, [], {})}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [text for item in value if (text := _text(item)) is not None]


__all__ = [
    "OPL_CURRENT_OWNER_DELTA_REF",
    "OPL_HOSTED_OPERATOR_PROJECTION_REF",
    "build_workspace_domain_projection",
]
