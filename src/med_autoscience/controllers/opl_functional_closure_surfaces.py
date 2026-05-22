from __future__ import annotations

from typing import Any, Iterable, Mapping


TARGET_DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "med-autoscience"
OPL_OWNER = "one-person-lab"
MAS_EVIDENCE_LANE_REF = "contracts/evidence/mas-evidence-lane.json"
STABLE_BLOCKER_EVIDENCE_REFS = (
    MAS_EVIDENCE_LANE_REF,
    "tests/test_real_paper_readiness_owner_blocker.py::test_readiness_owner_blocker_projection_unblocks_guarded_apply_as_stable_blocker",
    "tests/test_cli_cases/owner_route_handoff_guarded_apply_cases.py::test_sidecar_dispatch_guarded_apply_records_mas_owner_receipt_present",
    "tests/test_cli_cases/owner_route_handoff_guarded_apply_cases.py::test_sidecar_dispatch_guarded_apply_records_provider_unavailable_typed_blocker",
)


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


def build_functional_closure_status_projection(
    *,
    provider_residency_read_model: Mapping[str, Any],
    provider_guarded_soak_read_model: Mapping[str, Any],
    managed_temporal_state_consistency: Mapping[str, Any],
    owner_receipt_contract: Mapping[str, Any],
    lifecycle_guarded_apply_proof: Mapping[str, Any],
    workspace_runtime_evidence_receipt: Mapping[str, Any],
    legacy_retirement_tombstone_proof: Mapping[str, Any],
    standard_domain_agent_skeleton: Mapping[str, Any],
    domain_memory_descriptor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    provider_ready = _status_is(provider_residency_read_model, "ready")
    managed_consistent = _status_is(managed_temporal_state_consistency, "consistent")
    workspace_owner_refs = _string_list(workspace_runtime_evidence_receipt.get("owner_receipt_refs"))
    observed_refs = [
        ref
        for ref in workspace_runtime_evidence_receipt.get("observed_refs") or []
        if isinstance(ref, Mapping) and ref.get("exists") is True
    ]
    memory_refs = [
        ref
        for ref in observed_refs
        if str(ref.get("role") or "").startswith("publication_route_memory")
    ]
    lines = [
        _line(
            line_id="p2_provider_residency_and_activity_soak",
            gate_class="production_evidence_gate",
            owner_surface_refs=[
                "/product_entry_manifest/provider_residency_read_model",
                "/product_entry_manifest/managed_temporal_state_consistency",
                "/sidecar_export/managed_temporal_state_consistency",
            ],
            status=(
                "provider_residency_projected_domain_activity_soak_pending"
                if provider_ready and managed_consistent
                else "typed_blocker"
            ),
            typed_blockers=[
                _typed_blocker(
                    "mas_domain_activity_long_soak_pending",
                    owner=OPL_OWNER,
                    required_surface="OPL domain activity long soak receipt + MAS sidecar receipt",
                    reason=(
                        "Provider residency can be projected, but MAS still needs a real domain "
                        "activity long soak receipt tied to a MAS sidecar receipt."
                    ),
                )
            ],
            evidence_refs=_status_refs(
                provider_residency_read_model,
                managed_temporal_state_consistency,
            ),
        ),
        _line(
            line_id="p2_mas_framework_migration",
            gate_class="landed_foundation_with_live_apply_gate",
            owner_surface_refs=[
                "/product_entry_manifest/owner_receipt_contract",
                "/sidecar_export/owner_receipt_contract",
            ],
            status="owner_receipt_envelope_landed_live_apply_chain_pending",
            typed_blockers=[
                _typed_blocker(
                    "mas_live_owner_receipt_chain_pending",
                    owner=DOMAIN_OWNER,
                    required_surface="MAS owner guarded apply receipt",
                    reason=(
                        "Direct MAS path and OPL-hosted path share the owner receipt envelope; "
                        "live paper progress still requires MAS owner receipt refs."
                    ),
                )
            ],
            evidence_refs=_status_refs(owner_receipt_contract),
        ),
        _line(
            line_id="publication_route_memory_management",
            gate_class="functional_follow_through_gate",
            owner_surface_refs=[
                "/product_entry_manifest/domain_memory_descriptor",
                "/product_entry_manifest/workspace_runtime_evidence_receipt",
            ],
            status=(
                "workspace_memory_receipt_refs_observed_scaleout_pending"
                if memory_refs
                else "body_free_descriptor_landed_receipt_scaleout_pending"
            ),
            typed_blockers=[
                _typed_blocker(
                    "publication_route_memory_multi_workspace_receipt_scaleout_pending",
                    owner=DOMAIN_OWNER,
                    required_surface="multi paper-line memory writeback router receipts",
                    reason=(
                        "The body-free memory descriptor and inventory contract are available; "
                        "more accepted/rejected workspace receipts must come from real paper lines."
                    ),
                )
            ],
            evidence_refs=[
                *(_status_refs(domain_memory_descriptor) if domain_memory_descriptor else []),
                *[str(ref.get("ref")) for ref in memory_refs if str(ref.get("ref") or "").strip()],
            ],
        ),
        _line(
            line_id="stage_surface_standardization",
            gate_class="landed_foundation_with_live_apply_gate",
            owner_surface_refs=[
                "/product_entry_manifest/standard_domain_agent_skeleton",
                "/product_entry_manifest/stage_quality_pack_contract",
                "/product_entry_manifest/stage_skill_surface_projection",
            ],
            status="stage_surfaces_landed_live_apply_followthrough_pending",
            typed_blockers=[
                _typed_blocker(
                    "stage_closeout_live_provider_owner_chain_pending",
                    owner=DOMAIN_OWNER,
                    required_surface="live provider attempt -> MAS owner stage closeout receipt",
                    reason=(
                        "Stage surfaces, skill guards, and skeleton slots are projected; live "
                        "provider-hosted paper apply must still produce MAS owner closeout refs."
                    ),
                )
            ],
            evidence_refs=_status_refs(standard_domain_agent_skeleton),
        ),
        _line(
            line_id="p1_app_runtime_workbench",
            gate_class="functional_follow_through_gate",
            owner_surface_refs=[
                "/progress_portal/mas_opl_runtime_workbench_projection",
                "/product_entry_manifest/workspace_runtime_evidence_receipt",
            ],
            status="mas_reference_projection_available_opl_app_drilldown_pending",
            typed_blockers=[
                _typed_blocker(
                    "opl_app_drilldown_product_polish_pending",
                    owner=OPL_OWNER,
                    required_surface="OPL App read-only workbench drilldown",
                    reason=(
                        "MAS can expose refs, freshness, blockers, and safe receipt refs; the "
                        "human-facing App drilldown remains an OPL product surface."
                    ),
                )
            ],
            evidence_refs=_status_refs(workspace_runtime_evidence_receipt),
        ),
        _line(
            line_id="p0_live_paper_autonomy_acceptance",
            gate_class="production_evidence_gate",
            owner_surface_refs=[
                "/product_entry_manifest/provider_guarded_soak_read_model",
                "/sidecar_dispatch/paper_autonomy/guarded-apply",
                "/product_entry_manifest/workspace_runtime_evidence_receipt",
            ],
            status=(
                "workspace_owner_receipt_refs_observed_provider_live_apply_still_evidence_gated"
                if workspace_owner_refs
                else "stable_typed_blocker_fixture_landed_live_provider_apply_scaleout_pending"
            ),
            typed_blockers=[
                _typed_blocker(
                    "provider_hosted_live_paper_apply_pending",
                    owner=DOMAIN_OWNER,
                    required_surface=(
                        "provider attempt id + typed closeout + MAS owner receipt + "
                        "artifact/gate/reviewer/route/human-gate evidence"
                    ),
                    reason=(
                        "Repo projections and dispatch receipts cannot substitute for a real "
                        "provider-hosted paper-line guarded apply owner chain. The stable "
                        "typed blocker fixture is landed, but live multi-line scaleout remains pending."
                    ),
                )
            ],
            evidence_refs=[
                *_status_refs(provider_guarded_soak_read_model),
                *STABLE_BLOCKER_EVIDENCE_REFS,
                *workspace_owner_refs,
            ],
        ),
        _line(
            line_id="legacy_residue_retirement",
            gate_class="functional_follow_through_gate",
            owner_surface_refs=[
                "/product_entry_manifest/legacy_retirement_tombstone_proof",
                "/product_entry_manifest/functional_consumer_boundary/retired_legacy_residue_tombstones",
            ],
            status=_legacy_status(legacy_retirement_tombstone_proof=legacy_retirement_tombstone_proof),
            typed_blockers=[],
            evidence_refs=_status_refs(
                legacy_retirement_tombstone_proof,
            ),
        ),
        _line(
            line_id="standard_skeleton_physicalization",
            gate_class="functional_follow_through_gate",
            owner_surface_refs=[
                "/product_entry_manifest/standard_domain_agent_skeleton",
                "/product_entry_manifest/workspace_runtime_artifact_root_locator",
            ],
            status=(
                "repo_source_anchors_landed_ongoing_slot_discipline"
                if _repo_source_anchors_landed(standard_domain_agent_skeleton)
                else "typed_blocker"
            ),
            typed_blockers=(
                []
                if _repo_source_anchors_landed(standard_domain_agent_skeleton)
                else [
                    _typed_blocker(
                        "standard_skeleton_repo_source_anchor_missing",
                        owner=DOMAIN_OWNER,
                        required_surface="standard_domain_agent_skeleton.repo_source_anchor_status",
                        reason="New repo-source surfaces need standard skeleton anchors before follow-through.",
                    )
                ]
            ),
            evidence_refs=_status_refs(standard_domain_agent_skeleton),
        ),
        _line(
            line_id="p3_foundation_guard",
            gate_class="landed_foundation",
            owner_surface_refs=[
                "/product_entry_manifest/legacy_retirement_tombstone_proof",
                "/product_entry_manifest/functional_consumer_boundary/retired_legacy_residue_tombstones",
            ],
            status="maintenance_only_no_default_mds_dependency",
            typed_blockers=[],
            evidence_refs=_status_refs(legacy_retirement_tombstone_proof),
        ),
    ]
    return {
        "surface_kind": "mas_functional_closure_status_projection",
        "version": "mas-functional-closure-status.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "owner": DOMAIN_OWNER,
        "planning_ref": "docs/active/current-development-lines.md",
        "status": "functional_surfaces_projected_production_evidence_gated",
        "summary": _functional_closure_summary(lines),
        "lines": lines,
        "open_typed_blockers": [
            blocker
            for line in lines
            for blocker in line["typed_blockers"]
            if line["gate_class"] != "landed_foundation"
        ],
        "authority_boundary": {
            "projection_owner": DOMAIN_OWNER,
            "domain_truth_owner": DOMAIN_OWNER,
            "opl_role": "projection_consumer_and_transport_only",
            "read_only": True,
            "can_write_domain_truth": False,
            "can_write_artifact_body": False,
            "can_write_memory_body": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "provider_completion_is_paper_closure": False,
            "publication_closure_claimed": False,
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


def _line(
    *,
    line_id: str,
    gate_class: str,
    owner_surface_refs: Iterable[str],
    status: str,
    typed_blockers: Iterable[Mapping[str, Any]],
    evidence_refs: Iterable[str],
) -> dict[str, Any]:
    production_gate = gate_class == "production_evidence_gate"
    blockers = [dict(item) for item in typed_blockers]
    return {
        "line_id": line_id,
        "gate_class": gate_class,
        "status": status,
        "mas_repo_functional_surface_complete": status != "typed_blocker",
        "production_evidence_complete": False if production_gate else None,
        "publication_closure_claimed": False,
        "owner_surface_refs": list(dict.fromkeys(owner_surface_refs)),
        "evidence_refs": list(dict.fromkeys(str(ref) for ref in evidence_refs if str(ref or "").strip())),
        "typed_blockers": blockers,
    }


def _typed_blocker(
    blocker_id: str,
    *,
    owner: str,
    required_surface: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_functional_closure_typed_blocker",
        "blocker_id": blocker_id,
        "owner": owner,
        "required_owner_surface": required_surface,
        "reason": reason,
        "write_permitted": False,
    }


def _status_is(surface: Mapping[str, Any], status: str) -> bool:
    return str(surface.get("status") or "").strip() == status


def _status_refs(*surfaces: Mapping[str, Any] | None) -> list[str]:
    refs: list[str] = []
    for surface in surfaces:
        if not surface:
            continue
        for key in ("proof_ref", "locator_ref", "workspace_runtime_artifact_root_locator_ref"):
            text = str(surface.get(key) or "").strip()
            if text:
                refs.append(text)
        for ref in surface.get("physical_tombstone_refs") or []:
            text = str(ref or "").strip()
            if text:
                refs.append(text)
        repo_status = surface.get("repo_source_anchor_status")
        if isinstance(repo_status, Mapping):
            for anchor in repo_status.get("anchors") or []:
                if isinstance(anchor, Mapping):
                    text = str(anchor.get("ref") or anchor.get("repo_path") or "").strip()
                    if text:
                        refs.append(text)
    return list(dict.fromkeys(refs))


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _repo_source_anchors_landed(skeleton: Mapping[str, Any]) -> bool:
    anchors = skeleton.get("repo_source_anchor_status")
    return (
        isinstance(anchors, Mapping)
        and anchors.get("status") == "landed"
        and anchors.get("missing_anchor_ids") == []
    )


def _legacy_status(
    *,
    legacy_retirement_tombstone_proof: Mapping[str, Any],
) -> str:
    active_default_callers = legacy_retirement_tombstone_proof.get("active_default_callers")
    retired_surfaces = legacy_retirement_tombstone_proof.get("retired_or_tombstoned_surfaces")
    if active_default_callers == [] and isinstance(retired_surfaces, list):
        return "no_active_default_caller_proven_cleanup_policy_satisfied"
    if active_default_callers == []:
        return "no_active_default_caller_proven_cleanup_review_pending"
    return "typed_blocker"


def _functional_closure_summary(lines: list[dict[str, Any]]) -> dict[str, Any]:
    production_lines = [line for line in lines if line["gate_class"] == "production_evidence_gate"]
    functional_lines = [
        line
        for line in lines
        if line["gate_class"] in {"functional_follow_through_gate", "landed_foundation_with_live_apply_gate"}
    ]
    landed_lines = [line for line in lines if line["gate_class"] == "landed_foundation"]
    return {
        "line_count": len(lines),
        "functional_surface_complete_count": sum(
            1 for line in lines if line["mas_repo_functional_surface_complete"] is True
        ),
        "functional_follow_through_gate_count": len(functional_lines),
        "production_evidence_gate_count": len(production_lines),
        "production_evidence_pending_count": sum(
            1 for line in production_lines if line["production_evidence_complete"] is False
        ),
        "landed_foundation_count": len(landed_lines),
        "publication_closure_claimed": False,
        "provider_completion_is_paper_closure": False,
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
    "build_functional_closure_status_projection",
    "build_lifecycle_apply_requests_surface",
    "build_lifecycle_guarded_apply_proof_surface",
    "build_owner_receipt_contract_surface",
]
