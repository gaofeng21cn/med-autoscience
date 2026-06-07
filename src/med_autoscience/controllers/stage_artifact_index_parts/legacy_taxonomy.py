from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.stage_artifact_index_parts.authority_projection import (
    authority_boundary,
)


def legacy_taxonomy_migration(
    payload: Mapping[str, Any],
    *,
    paper_study_stage_pack_ref: str,
) -> dict[str, Any]:
    migration = payload["legacy_taxonomy_migration"]
    if not isinstance(migration, Mapping):
        raise ValueError("legacy taxonomy migration must be a mapping")
    mappings = [
        _legacy_mapping_projection(item)
        for item in _mapping_items(migration.get("mappings"))
    ]
    role_mapping: dict[str, list[dict[str, str]]] = {}
    for item in mappings:
        stage_id = str(item["target_stage_id"])
        stage_roles = role_mapping.setdefault(stage_id, [])
        for role in item["legacy_artifact_roles"]:
            stage_roles.append(
                {
                    "legacy_route_id": str(item["legacy_route_id"]),
                    "legacy_role": str(role["role"]),
                    "legacy_ref": str(role["ref"]),
                    "target_role": str(role["target_role"]),
                }
            )
    policy = migration.get("current_truth_policy")
    if not isinstance(policy, Mapping):
        policy = {}
    return {
        "surface_kind": str(migration.get("surface_kind") or "mas_paper_study_legacy_taxonomy_migration"),
        "status": str(migration.get("status") or "migration_manifest"),
        "contract_ref": f"{paper_study_stage_pack_ref}#/legacy_taxonomy_migration",
        "current_truth_policy": {
            "workbench_must_not_display_two_current_truths": bool(
                policy.get("workbench_must_not_display_two_current_truths", True)
            ),
            "legacy_route_is_current_truth": bool(policy.get("legacy_route_is_current_truth", False)),
            "current_truth_surface": str(policy.get("current_truth_surface") or "paper_study_stage_pack"),
            "legacy_semantics": str(
                policy.get("legacy_semantics") or "tombstone_backfilled_current_pointer"
            ),
        },
        "mappings": mappings,
        "role_mapping": role_mapping,
        "body_included": False,
        "authority_boundary": authority_boundary(),
    }


def legacy_mappings_by_stage(
    legacy_taxonomy_migration: Mapping[str, Any],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    by_stage: dict[str, list[Mapping[str, Any]]] = {}
    for item in _mapping_items(legacy_taxonomy_migration.get("mappings")):
        stage_id = _text(item.get("target_stage_id"))
        if stage_id is None:
            continue
        by_stage.setdefault(stage_id, []).append(item)
    return {stage_id: tuple(items) for stage_id, items in by_stage.items()}


def legacy_role_refs_for_stage(
    legacy_stage_mappings: tuple[Mapping[str, Any], ...],
) -> tuple[dict[str, str], ...]:
    refs: list[dict[str, str]] = []
    for mapping in legacy_stage_mappings:
        legacy_route_id = _required_text(mapping.get("legacy_route_id"), "legacy_route_id")
        for role in _mapping_items(mapping.get("legacy_artifact_roles")):
            refs.append(
                {
                    "legacy_route_id": legacy_route_id,
                    "role": _required_text(role.get("role"), "role"),
                    "target_role": _required_text(role.get("target_role"), "target_role"),
                    "ref": _required_text(role.get("ref"), "ref"),
                }
            )
    return tuple(refs)


def legacy_taxonomy_migration_stage_read_model(
    *,
    stage_id: str,
    legacy_stage_mappings: tuple[Mapping[str, Any], ...],
    current_pointer: Mapping[str, Any],
    next_owner_action: Mapping[str, Any],
    paper_study_stage_pack_ref: str,
) -> dict[str, Any]:
    legacy_route_ids = [
        _required_text(mapping.get("legacy_route_id"), "legacy_route_id")
        for mapping in legacy_stage_mappings
    ]
    current_pointer_ref = _required_text(current_pointer.get("pointer_ref"), "pointer_ref")
    promotion_state = _required_text(current_pointer.get("promotion_state"), "promotion_state")
    pointer_present = promotion_state == "current_pointer_promoted"
    tombstone_refs = [
        f"{paper_study_stage_pack_ref}#/legacy_taxonomy_migration/mappings/{legacy_route_id}"
        for legacy_route_id in legacy_route_ids
    ]
    tombstone_present = bool(tombstone_refs)
    fail_closed_reason = _legacy_taxonomy_fail_closed_reason(
        pointer_present=pointer_present,
        tombstone_present=tombstone_present,
    )
    migration_status = (
        "backfilled_current_pointer_present"
        if fail_closed_reason is None
        else fail_closed_reason
    )
    return {
        "surface_kind": "legacy_stage_taxonomy_migration_stage_read_model",
        "schema_version": 1,
        "contract_ref": f"{paper_study_stage_pack_ref}#/legacy_taxonomy_migration",
        "stage_native_stage_id": stage_id,
        "legacy_route_ids": legacy_route_ids,
        "legacy_stage_mappings": [
            {
                "legacy_route_id": legacy_route_id,
                "stage_native_stage_id": stage_id,
                "migration_status": migration_status,
                "current_pointer_ref": current_pointer_ref,
                "tombstone_or_provenance_ref": tombstone_ref,
                "legacy_route_is_current_truth": False,
            }
            for legacy_route_id, tombstone_ref in zip(legacy_route_ids, tombstone_refs, strict=True)
        ],
        "migration_status": migration_status,
        "backfill_status": migration_status,
        "backfilled_current_pointer": {
            "status": "present" if pointer_present else "missing",
            "pointer_ref": current_pointer_ref,
            "promotion_state": promotion_state,
        },
        "tombstone_or_provenance_required": True,
        "tombstone_or_provenance_present": tombstone_present,
        "tombstone_or_provenance_ref": tombstone_refs[0] if len(tombstone_refs) == 1 else None,
        "tombstone_or_provenance_refs": tombstone_refs,
        "workbench_dual_truth_forbidden": True,
        "workbench_display_current_truth": "paper_study_stage_pack",
        "legacy_route_is_current_truth": False,
        "current_truth_surface": "paper_study_stage_pack",
        "fail_closed": fail_closed_reason is not None,
        "fail_closed_reason": fail_closed_reason,
        "next_owner_action": dict(next_owner_action) if fail_closed_reason is not None else {},
        "authority": {
            **authority_boundary(),
            "derived_projection": True,
            "writes_mas_truth": False,
            "writes_study_truth": False,
            "writes_current_pointer": False,
            "claims_publication_ready": False,
        },
        "body_included": False,
    }


def _legacy_mapping_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    legacy_route_id = _required_text(value.get("legacy_route_id"), "legacy_route_id")
    target_stage_id = _required_text(value.get("target_stage_id"), "target_stage_id")
    return {
        "legacy_route_id": legacy_route_id,
        "target_stage_id": target_stage_id,
        "migration_semantics": "tombstone_backfilled_current_pointer",
        "workbench_display_current_truth": "paper_study_stage_pack",
        "legacy_route_is_current_truth": False,
        "legacy_artifact_roles": [
            {
                "role": _required_text(role.get("role"), "role"),
                "ref": _required_text(role.get("ref"), "ref"),
                "target_role": _required_text(role.get("target_role"), "target_role"),
            }
            for role in _mapping_items(value.get("legacy_artifact_roles"))
        ],
    }


def _legacy_taxonomy_fail_closed_reason(
    *,
    pointer_present: bool,
    tombstone_present: bool,
) -> str | None:
    if not tombstone_present:
        return "tombstone_or_provenance_required"
    if not pointer_present:
        return "current_pointer_backfill_required"
    return None


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _required_text(value: object, field: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"missing required text field: {field}")
    return text


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


__all__ = [
    "legacy_mappings_by_stage",
    "legacy_role_refs_for_stage",
    "legacy_taxonomy_migration",
    "legacy_taxonomy_migration_stage_read_model",
]
