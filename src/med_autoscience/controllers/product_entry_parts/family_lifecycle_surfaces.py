from __future__ import annotations

from typing import Any, Mapping

from .shared import TARGET_DOMAIN_ID, _non_empty_text, _normalized_strings


def _ref(ref: str, *, ref_kind: str = "json_pointer", label: str | None = None) -> dict[str, str]:
    payload = {"ref_kind": ref_kind, "ref": ref}
    if label:
        payload["label"] = label
    return payload


def _persistence_surface(
    *,
    surface_id: str,
    surface_role: str,
    storage_role: str,
    owner: str,
    ref: Mapping[str, Any],
    rebuild_from_refs: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "surface_id": surface_id,
        "surface_role": surface_role,
        "storage_role": storage_role,
        "owner": owner,
        "ref": dict(ref),
        "rebuild_from_refs": [dict(item) for item in (rebuild_from_refs or [])],
    }


def _build_family_persistence_policy_surface(
    *,
    adoption: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
    artifact_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    refs = dict(adoption.get("refs") or {})
    state_index_source_adapter = dict(refs.get("state_index_source_adapter") or {})
    authority_surfaces = [
        _persistence_surface(
            surface_id="progress_projection",
            surface_role="study_runtime_progress_projection_authority",
            storage_role="file_authority",
            owner=TARGET_DOMAIN_ID,
            ref=_ref("studies/<study_id>/progress_projection.json", ref_kind="workspace_locator"),
        ),
        _persistence_surface(
            surface_id="domain_health_diagnostic_latest",
            surface_role="mas_domain_runtime_health_projection",
            storage_role="file_authority",
            owner=TARGET_DOMAIN_ID,
            ref=_ref(
                "studies/<study_id>/artifacts/domain_health_diagnostic/latest.json",
                ref_kind="workspace_locator",
                label="domain_health_diagnostic",
            ),
        ),
        _persistence_surface(
            surface_id="publication_eval_latest",
            surface_role="publication_quality_authority",
            storage_role="file_authority",
            owner=TARGET_DOMAIN_ID,
            ref=_ref("studies/<study_id>/artifacts/publication_eval/latest.json", ref_kind="workspace_locator"),
        ),
        _persistence_surface(
            surface_id="controller_decisions_latest",
            surface_role="controller_decision_authority",
            storage_role="file_authority",
            owner=TARGET_DOMAIN_ID,
            ref=_ref("studies/<study_id>/artifacts/controller_decisions/latest.json", ref_kind="workspace_locator"),
        ),
        _persistence_surface(
            surface_id="current_package",
            surface_role="paper_package_authority",
            storage_role="file_authority",
            owner=TARGET_DOMAIN_ID,
            ref=_ref("studies/<study_id>/paper/submission_minimal/current_package", ref_kind="workspace_locator"),
        ),
    ]
    lifecycle_ref_indexes: list[dict[str, Any]] = []
    state_index_ref = _non_empty_text(
        state_index_source_adapter.get("workspace_relative_path")
    )
    if state_index_ref is not None:
        lifecycle_ref_indexes.append(
            _persistence_surface(
                surface_id="opl_state_index_source_adapter",
                surface_role="opl_state_index_source_adapter",
                storage_role="opl_state_index_source_adapter_ref",
                owner="one-person-lab",
                ref=_ref(
                    state_index_ref,
                    ref_kind="workspace_locator",
                    label="OPL StateIndex source adapter manifest",
                ),
                rebuild_from_refs=[
                    _ref(
                        "/opl_family_persistence_lifecycle_owner_route_adoption/refs/state_index_source_adapter",
                        label="source adapter manifest",
                    ),
                ],
            )
        )
    return {
        "surface_kind": "family_persistence_policy",
        "version": "family-persistence-policy.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "policy_id": "mas_opl_family_persistence_policy",
        "summary": (
            "MAS exposes lifecycle refs to OPL as a domain reference adapter; MAS-owned files "
            "remain the authority for study runtime, controller, publication, AI reviewer, and paper package truth."
        ),
        "authority_surfaces": authority_surfaces,
        "lifecycle_ref_indexes": lifecycle_ref_indexes,
        "projection_caches": [
            _persistence_surface(
                surface_id="product_entry_progress_projection",
                surface_role="opl_read_model_cache",
                storage_role="projection_cache",
                owner=TARGET_DOMAIN_ID,
                ref=_ref("/progress_projection", label=str(progress_projection.get("surface_kind") or "progress_projection")),
                rebuild_from_refs=[
                    _ref("/session_continuity"),
                    _ref("/artifact_inventory", label=str(artifact_inventory.get("surface_kind") or "artifact_inventory")),
                ],
            )
        ],
        "explicit_archive_import_refs": [
            _persistence_surface(
                surface_id="quest_git_restore_import",
                surface_role="explicit_archive_import_reference",
                storage_role="explicit_archive_import_ref_only",
                owner=TARGET_DOMAIN_ID,
                ref=_ref("runtime/quests/<quest_id>/.git", ref_kind="workspace_locator"),
            )
        ],
    }


def _build_family_lifecycle_ledger_surface(
    *,
    adoption: Mapping[str, Any],
    session_continuity: Mapping[str, Any],
) -> dict[str, Any]:
    refs = dict(adoption.get("refs") or {})
    state_index_source_adapter = dict(refs.get("state_index_source_adapter") or {})
    state_index_ref = _non_empty_text(
        state_index_source_adapter.get("workspace_relative_path")
    ) or (
        "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json"
    )
    return {
        "surface_kind": "family_lifecycle_ledger",
        "version": "family-lifecycle-ledger.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "ledger_id": "mas_opl_family_lifecycle_ledger",
        "phase": "verify",
        "status": "projected",
        "summary": (
            "MAS lifecycle ledger is projected from MAS receipt refs; generic persistence, restore/retention, and "
            "lifecycle indexing are OPL-owned replacement concerns."
        ),
        "actions": [
            {
                "action_id": "verify_runtime_lifecycle_ref_projection",
                "action_kind": "verify_projection",
                "target_ref": _ref(state_index_ref, ref_kind="workspace_locator"),
                "authority_owner": "one-person-lab",
                "safety_gate": "refs_only_no_domain_truth_write",
                "result": "projected",
                "manifest_ref": _ref(
                    "/opl_family_persistence_lifecycle_owner_route_adoption/refs/state_index_source_adapter",
                    label="OPL StateIndex source adapter manifest ref",
                ),
                "sha256": "0" * 64,
                "restore_ref": _ref(
                    "/session_continuity/restore_surface",
                    label=str(dict(session_continuity.get("restore_surface") or {}).get("surface_kind") or "restore surface"),
                ),
            }
        ],
    }


def _build_family_owner_route_surface(
    *,
    adoption: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
    artifact_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(adoption.get("payload") or {})
    owner_route_projection = dict(payload.get("owner_route") or {})
    current_ticket = dict(owner_route_projection.get("current_ticket") or {})
    allowed_actions = [
        item
        for item in _normalized_strings(current_ticket.get("allowed_actions") or owner_route_projection.get("allowed_actions") or [])
        if item
    ]
    if not allowed_actions:
        allowed_actions = ["workspace-cockpit", "submit-study-task", "launch-study", "study-progress"]
    route_epoch = _non_empty_text(current_ticket.get("route_epoch")) or "manifest-projection"
    idempotency_key = _non_empty_text(current_ticket.get("idempotency_key")) or f"{TARGET_DOMAIN_ID}:product-entry-manifest:{route_epoch}"
    next_owner = _non_empty_text(current_ticket.get("next_owner")) or TARGET_DOMAIN_ID
    return {
        "surface_kind": "family_owner_route",
        "version": "family-owner-route.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "route_id": "mas_opl_family_owner_route",
        "route_epoch": route_epoch,
        "source_fingerprint": "mas_product_entry_manifest:v2",
        "next_owner": next_owner,
        "allowed_actions": allowed_actions,
        "idempotency_key": idempotency_key,
        "status": "active",
        "summary": "OPL can discover MAS next-owner routing without owning MAS study, publication, or paper package truth.",
        "handoff_refs": [
            _ref("/shared_handoff/direct_entry_builder", label="direct entry builder"),
            _ref("/shared_handoff/opl_handoff_builder", label="OPL handoff builder"),
            _ref("/family_orchestration/resume_contract", label=str(family_orchestration.get("surface_kind") or "family orchestration")),
        ],
        "projection_refs": [
            _ref("/progress_projection", label=str(progress_projection.get("surface_kind") or "progress projection")),
            _ref("/artifact_inventory", label=str(artifact_inventory.get("surface_kind") or "artifact inventory")),
            _ref("/opl_family_persistence_lifecycle_owner_route_adoption", label="MAS OPL family adoption surface"),
            _ref(
                "/product_entry_shell/workspace_cockpit",
                label=str(dict(product_entry_shell.get("workspace_cockpit") or {}).get("surface_kind") or "workspace cockpit"),
            ),
        ],
    }


__all__ = [
    "_build_family_persistence_policy_surface",
    "_build_family_lifecycle_ledger_surface",
    "_build_family_owner_route_surface",
]
