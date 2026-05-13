from __future__ import annotations

from typing import Any, Mapping


TARGET_DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "med-autoscience"
OPL_OWNER = "one-person-lab"


def build_owner_receipt_contract_surface(
    *,
    provider_availability: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    availability = dict(provider_availability or _provider_availability(provider_available=False))
    provider_available = availability.get("provider_attempt_available") is True
    typed_blocker = None
    if not provider_available:
        typed_blocker = {
            "surface_kind": "mas_owner_receipt_contract_typed_blocker",
            "blocker_id": "mas_live_owner_receipt_soak_pending",
            "owner": DOMAIN_OWNER,
            "reason": (
                "MAS can declare the owner receipt envelope, but a live provider-hosted paper apply "
                "must still return MAS owner receipt refs before paper progress can advance."
            ),
            "required_owner_surface": "MAS owner guarded apply receipt",
            "write_permitted": False,
        }
    return {
        "surface_kind": "domain_owner_receipt_contract",
        "version": "mas-domain-owner-receipt-contract.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "owner": DOMAIN_OWNER,
        "status": "contract_declared_live_soak_pending",
        "accepted_return_shapes": [
            "domain_receipt",
            "typed_blocker",
            "no_regression_evidence",
        ],
        "receipt_ref_policy": {
            "opl_persists": "receipt_refs_only",
            "mas_persists": "domain_receipt_and_workspace_truth_refs",
            "memory_body_externalized": True,
            "artifact_body_externalized": True,
        },
        "required_receipt_axes": [
            "provider_attempt_ref",
            "typed_closeout_ref",
            "mas_owner_receipt_ref",
            "artifact_delta_or_typed_blocker_ref",
            "gate_replay_ref",
            "reviewer_update_ref",
            "route_decision_ref",
            "human_gate_or_stop_loss_ref",
            "no_forbidden_write_proof_ref",
        ],
        "forbidden_write_guard": _forbidden_write_guard_proof(),
        "provider_availability": availability,
        "typed_blocker": typed_blocker,
        "authority_boundary": {
            "opl_role": "attempt_transport_and_receipt_ref_projection_only",
            "domain_truth_owner": DOMAIN_OWNER,
            "quality_verdict_owner": DOMAIN_OWNER,
            "artifact_authority_owner": DOMAIN_OWNER,
            "can_write_domain_truth": False,
            "can_write_artifact_gate": False,
            "can_write_memory_body": False,
        },
    }


def build_lifecycle_apply_requests_surface() -> list[dict[str, Any]]:
    return [
        {
            "action_id": "mas-opl-stage-attempt-ledger-retention",
            "action_kind": "retention",
            "owner_scope": "opl_owned_ledger",
            "authority_owner": OPL_OWNER,
            "target_ref": "opl-ledger:medautoscience:stage-attempts",
            "domain_receipt_required": False,
        },
        {
            "action_id": "mas-workspace-artifact-cleanup-requires-domain-receipt",
            "action_kind": "cleanup",
            "owner_scope": "domain_owned_artifact",
            "authority_owner": DOMAIN_OWNER,
            "target_ref": "workspace:med-autoscience:artifacts",
            "domain_receipt_required": True,
            "required_receipt_shape": "domain_receipt",
        },
        {
            "action_id": "mas-workspace-artifact-restore-requires-domain-receipt",
            "action_kind": "restore",
            "owner_scope": "domain_owned_artifact",
            "authority_owner": DOMAIN_OWNER,
            "target_ref": "workspace:med-autoscience:artifact-restore",
            "domain_receipt_required": True,
            "required_receipt_shape": "domain_receipt",
        },
    ]


def build_lifecycle_guarded_apply_proof_surface() -> dict[str, Any]:
    requests = build_lifecycle_apply_requests_surface()
    domain_owned_requests = [
        request for request in requests if request.get("owner_scope") == "domain_owned_artifact"
    ]
    return {
        "surface_kind": "mas_lifecycle_guarded_apply_proof",
        "version": "mas-lifecycle-guarded-apply-proof.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "domain_receipt_required_for_domain_artifact_mutation",
        "apply_status": "blocked_domain_receipt_required",
        "requests": requests,
        "coverage": {
            "cleanup": any(request["action_kind"] == "cleanup" for request in requests),
            "restore": any(request["action_kind"] == "restore" for request in requests),
            "retention": any(request["action_kind"] == "retention" for request in requests),
        },
        "domain_receipt_required_count": len(domain_owned_requests),
        "domain_receipt_refs": [],
        "typed_blockers": [
            {
                "surface_kind": "mas_lifecycle_apply_typed_blocker",
                "blocker_id": "mas_domain_artifact_lifecycle_receipt_required",
                "owner": DOMAIN_OWNER,
                "reason": (
                    "OPL may retain provider ledger/locator metadata, but cleanup or restore of "
                    "MAS-owned artifacts requires a MAS lifecycle receipt."
                ),
                "required_owner_surface": "MAS lifecycle apply receipt",
                "write_permitted": False,
            }
        ],
        "authority_boundary": {
            "opl_can_apply_owned_ledger_or_locator": True,
            "opl_writes_domain_truth": False,
            "opl_writes_domain_artifact": False,
            "opl_writes_memory_body": False,
            "domain_artifact_mutation_requires_mas_receipt": True,
        },
    }


def _forbidden_write_guard_proof() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_forbidden_write_guard_proof",
        "version": "mas-opl-forbidden-write-guard.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "task_id": "owner-receipt-contract:no-forbidden-write-proof",
        "task_kind": "owner_receipt_contract",
        "result": "configured",
        "guard_mode": "fail_closed",
        "guard_owner": DOMAIN_OWNER,
        "requested_writes": [],
        "forbidden_requested_writes": [],
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_override_artifact_gate": False,
        "can_write_current_package": False,
    }


def _provider_availability(*, provider_available: bool) -> dict[str, Any]:
    if provider_available:
        return {
            "status": "available",
            "provider_attempt_available": True,
        }
    return {
        "status": "typed_blocker",
        "provider_attempt_available": False,
        "blocker": {
            "surface_kind": "mas_provider_guarded_soak_typed_blocker",
            "blocker_id": "provider_guarded_soak_provider_unavailable",
            "owner": OPL_OWNER,
            "reason": "real provider attempt surface is unavailable to MAS projection",
            "required_owner_surface": "OPL provider attempt receipt / guarded soak provider proof",
            "write_permitted": False,
        },
    }


__all__ = [
    "build_lifecycle_apply_requests_surface",
    "build_lifecycle_guarded_apply_proof_surface",
    "build_owner_receipt_contract_surface",
]
