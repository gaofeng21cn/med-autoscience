from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


TARGET_DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "med-autoscience"
OPL_OWNER = "one-person-lab"
DEFAULT_PROVIDER_GUARDED_SOAK_TARGETS = ("DM002", "DM003", "Obesity")
PROVIDER_HOSTED_PROOF_SURFACE = "real_paper_autonomy_provider_hosted_paper_proof"
GUARDED_APPLY_PROOF_SURFACE = "real_paper_autonomy_guarded_apply_proof"
PROVIDER_RESIDENCY_SURFACE = "provider_runtime_residency_read_model"
PAPER_LINE_GUARDED_APPLY_EVIDENCE_SURFACE = "mas_paper_line_guarded_apply_evidence_scaleout"
PRODUCTION_RESIDENCY_CHECKS = (
    "temporal_production_residency",
    "worker_restart_requery",
    "retry_dead_letter",
    "long_soak_receipt",
)
PAPER_LINE_GUARDED_APPLY_REQUIRED_REFS = (
    "owner_receipt_ref",
    "progress_delta_ref",
    "ai_reviewer_gate_ref",
    "artifact_movement_ref",
    "human_gate_ref",
    "stop_loss_ref",
    "stable_typed_blocker_ref",
    "no_forbidden_write_proof_ref",
)
PAPER_LINE_GUARDED_APPLY_ACCEPTED_RESULTS = (
    "artifact_delta",
    "gate_replay",
    "ai_reviewer_re_eval",
    "route_decision",
    "human_gate",
    "stop_loss",
    "stable_blocker",
)
PAPER_LINE_GUARDED_APPLY_FORBIDDEN_BODIES = (
    "publication_eval_body",
    "controller_decision_body",
    "artifact_gate_body",
    "memory_body",
    "final_verdict_body",
)
PAPER_LINE_GUARDED_APPLY_OPL_REF_ROLES = (
    "owner_receipt_ref",
    "progress_delta_ref",
    "ai_reviewer_gate_receipt_ref",
    "artifact_movement_ref",
    "human_gate_or_resume_ref",
    "stable_typed_blocker_ref",
    "no_forbidden_write_proof_ref",
)
REAL_PAPER_LINE_PROVIDER_CANARY_GATE = "real_paper_line_provider_canary"

FORBIDDEN_AUTHORITY_WRITES = (
    "study_truth_write",
    "publication_quality_verdict",
    "artifact_gate_override",
    "current_package_write",
    "evidence_ledger_write",
    "review_ledger_write",
    "study_truth",
    "publication_eval",
    "publication_eval_write",
    "controller_decisions",
    "controller_decisions_write",
    "current_package",
    "paper/current_package",
    "manuscript/current_package",
    "paper/manuscript/current_package",
    "current_package.zip",
    "artifact_gate",
    "artifact_authority",
    "publication_authority",
    "publication_authority_write",
    "evidence_ledger",
    "memory_body_write",
    "review_ledger",
    "publication_route_memory_body",
    "publication_route_memory_writeback_accept",
    "memory_write_router_accept",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def build_provider_residency_read_model(
    *,
    provider_available: bool,
    receipt_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    receipts = dict(receipt_refs or {})
    checks = [
        _provider_residency_check(
            check_id=check_id,
            provider_available=provider_available,
            receipt_ref=receipts.get(check_id),
        )
        for check_id in PRODUCTION_RESIDENCY_CHECKS
    ]
    missing = [item["check_id"] for item in checks if item["status"] != "receipt_observed"]
    status = "ready" if provider_available and not missing else "typed_blocker"
    return {
        "surface_kind": PROVIDER_RESIDENCY_SURFACE,
        "version": "provider-runtime-residency-read-model.v1",
        "mode": "opl_owned_read_model_refs_only",
        "target_provider": "temporal",
        "provider_owner": OPL_OWNER,
        "domain_owner": DOMAIN_OWNER,
        "status": status,
        "provider_available": bool(provider_available),
        "checks": checks,
        "required_evidence": list(PRODUCTION_RESIDENCY_CHECKS),
        "accepted_receipt_surfaces": [
            "opl_provider_attempt_receipt",
            "opl_provider_worker_lifecycle_receipt",
            "opl_provider_retry_dead_letter_receipt",
            "opl_provider_long_soak_receipt",
            "typed_closeout_receipt",
        ],
        "typed_blocker": (
            None
            if status == "ready"
            else {
                "surface_kind": "mas_provider_residency_typed_blocker",
                "blocker_id": "production_provider_residency_evidence_missing",
                "owner": OPL_OWNER,
                "missing_evidence": missing,
                "reason": (
                    "MAS can consume OPL provider sidecar tasks and typed receipts, but production "
                    "Temporal residency is not proven by the required OPL-owned receipts."
                ),
                "required_owner_surface": "OPL production provider residency receipt bundle",
                "write_permitted": False,
            }
        ),
        "consumer_contract": {
            "mas_consumes": ["sidecar_task", "typed_receipt", "receipt_refs"],
            "mas_owned_provider_kernel": False,
            "provider_completion_is_paper_closure": False,
            "queue_completion_is_paper_closure": False,
            "paper_progress_requires_mas_owner_receipt": True,
        },
        "authority_boundary": {
            "provider_attempt_owner": OPL_OWNER,
            "domain_truth_owner": DOMAIN_OWNER,
            "can_write_domain_truth": False,
            "can_write_current_package": False,
            "can_authorize_publication_quality": False,
            "can_write_memory_body": False,
        },
    }

def build_forbidden_write_guard_proof(
    *,
    result: str,
    task_id: str | None,
    task_kind: str | None,
    requested_writes: Iterable[str],
) -> dict[str, Any]:
    requested = [str(item) for item in requested_writes if str(item or "").strip()]
    forbidden_requested = [item for item in requested if item in FORBIDDEN_AUTHORITY_WRITES]
    return {
        "surface_kind": "mas_opl_forbidden_write_guard_proof",
        "version": "mas-opl-forbidden-write-guard.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "task_id": task_id,
        "task_kind": task_kind,
        "result": result,
        "guard_mode": "fail_closed",
        "guard_owner": DOMAIN_OWNER,
        "requested_writes": requested,
        "forbidden_requested_writes": forbidden_requested,
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_override_artifact_gate": False,
        "can_write_current_package": False,
        "proof_refs": [
            {
                "ref_kind": "python_symbol",
                "ref": "med_autoscience.controllers.sidecar_family_adapter.dispatch_family_sidecar_task",
                "role": "dispatch_guard",
            },
            {
                "ref_kind": "json_pointer",
                "ref": "/authority_boundary/forbidden_authorities",
                "role": "receipt_authority_boundary",
            },
        ],
    }

def build_provider_guarded_soak_read_model(
    *,
    provider_available: bool = False,
    provider_availability: Mapping[str, Any] | None = None,
    target_studies: Iterable[str] = DEFAULT_PROVIDER_GUARDED_SOAK_TARGETS,
) -> dict[str, Any]:
    targets = tuple(str(item) for item in target_studies if str(item or "").strip())
    availability = (
        dict(provider_availability)
        if provider_availability is not None
        else _provider_availability(provider_available=provider_available)
    )
    provider_attempt_available = availability.get("provider_attempt_available") is True
    no_forbidden_write_proof = build_forbidden_write_guard_proof(
        result=(
            "configured"
            if provider_attempt_available
            else "blocked_provider_completion_is_not_paper_closure"
        ),
        task_id="provider-guarded-soak-read-model:no-forbidden-write-proof",
        task_kind="provider_guarded_soak_read_model",
        requested_writes=("current_package_write", "publication_quality_verdict", "study_truth_write"),
    )
    no_forbidden_write_proof.update(
        {
            "provider_completion_is_paper_closure": False,
            "queue_completion_is_paper_closure": False,
            "paper_closure_requires_mas_owner_receipt": True,
            "only_mas_owner_receipt_can_prove_mutation": True,
        }
    )
    return {
        "surface_kind": "provider_guarded_soak_read_model",
        "version": "provider-guarded-soak-read-model.v1",
        "mode": "descriptor_read_model",
        "target_studies": list(targets),
        "expected_surface_shape": {
            "provider_proof_surface": PROVIDER_HOSTED_PROOF_SURFACE,
            "guarded_apply_surface": GUARDED_APPLY_PROOF_SURFACE,
            "closeout_packet_surface": "domain_stage_closeout_packet",
            "typed_blocker_surface": "mas_provider_guarded_soak_typed_blocker",
        },
        "provider_availability": availability,
        "target_coverage": [
            _provider_guarded_soak_target_coverage(
                target,
                provider_attempt_available=provider_attempt_available,
            )
            for target in targets
        ],
        "provider_completion_semantics": {
            "provider_completion_is_paper_closure": False,
            "queue_completion_is_paper_closure": False,
            "paper_closure_requires_mas_owner_receipt": True,
            "mutation_proof_surface": "MAS owner receipt",
        },
        "paper_line_guarded_apply_evidence": build_paper_line_guarded_apply_evidence_scaleout_surface(),
        "no_forbidden_write_proof": no_forbidden_write_proof,
        "authority_boundary": {
            "provider_attempt_owner": OPL_OWNER,
            "domain_truth_owner": DOMAIN_OWNER,
            "provider_completion_is_truth": False,
            "queue_completion_is_paper_closure": False,
            "can_write_domain_truth": False,
            "can_write_current_package": False,
            "can_authorize_publication_quality": False,
        },
    }

def build_paper_line_guarded_apply_evidence_scaleout_surface() -> dict[str, Any]:
    return {
        "surface_kind": PAPER_LINE_GUARDED_APPLY_EVIDENCE_SURFACE,
        "version": "mas-paper-line-guarded-apply-evidence-scaleout.v1",
        "lane_id": "lane_4a_mas_evidence_scaleout",
        "mode": "domain_owned_refs_only",
        "owner": DOMAIN_OWNER,
        "provider_attempt_owner": OPL_OWNER,
        "scaleout_status": "pending_real_paper_line_owner_receipts",
        "selected_evidence_surface": "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence",
        "real_paper_line_provider_canary_contract": {
            "gate_id": REAL_PAPER_LINE_PROVIDER_CANARY_GATE,
            "task_id": "agent-lab-task:mas/real-paper-line-provider-canary",
            "success_criterion": "mas_owner_chain_returns_owner_receipt_or_stable_typed_blocker",
            "provider_completion_is_success": False,
            "selected_opl_ingestable_ref_surface": (
                "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
            ),
            "required_closeout_surface": "mas_real_paper_line_provider_canary_closeout",
            "allowed_terminal_owner_results": [
                "owner_receipt",
                "stable_typed_blocker",
            ],
            "forbidden_authority": [
                "provider_completion_authorizes_domain_ready",
                "provider_or_opl_writes_publication_eval",
                "provider_or_opl_writes_controller_decisions",
                "provider_or_opl_writes_current_package",
                "provider_or_opl_writes_memory_or_artifact_body",
            ],
            "body_included": False,
        },
        "required_owner_outcome_refs": list(PAPER_LINE_GUARDED_APPLY_REQUIRED_REFS),
        "accepted_apply_results": list(PAPER_LINE_GUARDED_APPLY_ACCEPTED_RESULTS),
        "opl_ingestable_ref_contract": {
            "ref_packet_role": "opl_agent_lab_evidence_scaleout_input",
            "selected_surface": "existing_mas_paper_line_guarded_apply_evidence",
            "allowed_ref_roles": list(PAPER_LINE_GUARDED_APPLY_OPL_REF_ROLES),
            "closeout_requires_mas_owner_receipt_or_typed_blocker": True,
            "opl_may_persist_refs_only": True,
            "opl_may_write_domain_truth": False,
            "opl_may_write_memory_body": False,
            "opl_may_write_artifact_body": False,
            "opl_may_authorize_publication_or_quality": False,
        },
        "scaleout_ref_packets": [
            _paper_line_scaleout_ref_packet(
                packet_id="progress_delta_ref_packet",
                required_role="progress_delta_ref",
                owner_surface="artifacts/controller/repair_execution_evidence/latest.json",
                fallback_owner_surface="artifacts/runtime/turn_closeouts/<active_run_id>.json",
            ),
            _paper_line_scaleout_ref_packet(
                packet_id="ai_reviewer_gate_receipt_ref_packet",
                required_role="ai_reviewer_gate_receipt_ref",
                owner_surface="artifacts/publication_eval/latest.json",
                fallback_owner_surface="artifacts/supervision/requests/ai_reviewer/latest.json",
            ),
            _paper_line_scaleout_ref_packet(
                packet_id="artifact_movement_ref_packet",
                required_role="artifact_movement_ref",
                owner_surface="artifact_authority_receipt",
                fallback_owner_surface="artifacts/controller/gate_replay_requests/latest.json",
            ),
            _paper_line_scaleout_ref_packet(
                packet_id="human_gate_or_resume_ref_packet",
                required_role="human_gate_or_resume_ref",
                owner_surface="artifacts/controller_decisions/latest.json",
                fallback_owner_surface="human_gate_resume_receipt",
            ),
            _paper_line_scaleout_ref_packet(
                packet_id="stable_typed_blocker_ref_packet",
                required_role="stable_typed_blocker_ref",
                owner_surface="typed_blocker_receipt",
                fallback_owner_surface="artifacts/controller_decisions/latest.json",
            ),
        ],
        "domain_owned_outcome_refs": [
            _paper_line_outcome_ref(
                outcome_id="progress_delta",
                owner_surface_role="progress_delta_ref",
                source_surfaces=[
                    "artifacts/controller/repair_execution_receipts/latest.json",
                    "artifacts/controller/repair_execution_evidence/latest.json",
                ],
            ),
            _paper_line_outcome_ref(
                outcome_id="ai_reviewer_gate_movement",
                owner_surface_role="ai_reviewer_gate_ref",
                source_surfaces=[
                    "artifacts/publication_eval/latest.json",
                    "review_ledger",
                ],
            ),
            _paper_line_outcome_ref(
                outcome_id="artifact_movement",
                owner_surface_role="artifact_movement_ref",
                source_surfaces=[
                    "artifacts/controller/gate_replay_requests/latest.json",
                    "artifact_authority_receipt",
                ],
            ),
            _paper_line_outcome_ref(
                outcome_id="human_gate",
                owner_surface_role="human_gate_ref",
                source_surfaces=[
                    "artifacts/controller_decisions/latest.json",
                    "human_gate_resume_receipt",
                ],
            ),
            _paper_line_outcome_ref(
                outcome_id="stop_loss",
                owner_surface_role="stop_loss_ref",
                source_surfaces=[
                    "artifacts/controller_decisions/latest.json",
                    "stop_loss_receipt",
                ],
            ),
            _paper_line_outcome_ref(
                outcome_id="stable_typed_blocker",
                owner_surface_role="stable_typed_blocker_ref",
                source_surfaces=[
                    "artifacts/controller_decisions/latest.json",
                    "typed_blocker_receipt",
                ],
            ),
        ],
        "body_included": False,
        "artifact_body_included": False,
        "memory_body_included": False,
        "publication_eval_body_included": False,
        "controller_decision_body_included": False,
        "domain_verdict_claimed": False,
        "provider_completion_is_paper_closure": False,
        "opl_can_write_publication_eval": False,
        "opl_can_write_controller_decisions": False,
        "opl_can_write_artifact_gate": False,
        "opl_can_write_memory_body": False,
        "opl_can_write_final_verdict": False,
        "forbidden_body_surfaces": list(PAPER_LINE_GUARDED_APPLY_FORBIDDEN_BODIES),
        "source_contract_refs": [
            "contracts/owner_receipt_contract.json",
            "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
            "product_entry_manifest.provider_guarded_soak_read_model",
        ],
    }

def _paper_line_scaleout_ref_packet(
    *,
    packet_id: str,
    required_role: str,
    owner_surface: str,
    fallback_owner_surface: str,
) -> dict[str, Any]:
    return {
        "packet_id": packet_id,
        "owner": DOMAIN_OWNER,
        "required_role": required_role,
        "owner_surface": owner_surface,
        "fallback_owner_surface": fallback_owner_surface,
        "body_included": False,
        "opl_ingestable": True,
        "opl_projection_only": True,
        "write_permitted": False,
        "domain_truth_owner": DOMAIN_OWNER,
    }

def _paper_line_outcome_ref(
    *,
    outcome_id: str,
    owner_surface_role: str,
    source_surfaces: list[str],
) -> dict[str, Any]:
    return {
        "outcome_id": outcome_id,
        "owner": DOMAIN_OWNER,
        "domain_owned": True,
        "owner_surface_role": owner_surface_role,
        "source_surfaces": source_surfaces,
        "body_included": False,
        "write_permitted": False,
        "opl_projection_only": True,
    }

def build_managed_temporal_state_consistency_read_model(
    *,
    provider_availability: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    availability = dict(provider_availability or _provider_availability(provider_available=False))
    runtime_snapshot = _mapping(availability.get("runtime_snapshot"))
    provider_available = availability.get("provider_attempt_available") is True
    managed_ready = (
        runtime_snapshot.get("address_source") == "managed_local_service_state"
        and runtime_snapshot.get("lifecycle_status") == "ready"
        and runtime_snapshot.get("server_reachable") is True
        and runtime_snapshot.get("worker_ready") is True
    )
    status = "consistent" if provider_available and managed_ready else "typed_blocker"
    blocker = None
    if status != "consistent":
        blocker = {
            "surface_kind": "mas_opl_managed_temporal_state_typed_blocker",
            "blocker_id": "managed_temporal_state_not_consistent",
            "owner": OPL_OWNER,
            "reason": (
                "OPL provider status/read-model needs a proven managed service and worker state "
                "before MAS can project provider-hosted paper apply readiness."
            ),
            "required_owner_surface": "OPL family-runtime status --provider temporal",
            "write_permitted": False,
        }
    return {
        "surface_kind": "mas_opl_managed_temporal_state_consistency",
        "version": "mas-opl-managed-temporal-state-consistency.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": status,
        "provider_state": "production_residency_proven" if provider_available else "contract_ready_skeleton",
        "provider_availability_status": availability.get("status"),
        "proof_ref": availability.get("proof_ref"),
        "managed_state": {
            "address_source": runtime_snapshot.get("address_source"),
            "lifecycle_status": runtime_snapshot.get("lifecycle_status"),
            "server_reachable": runtime_snapshot.get("server_reachable") is True,
            "worker_ready": runtime_snapshot.get("worker_ready") is True,
            "task_queue": runtime_snapshot.get("task_queue"),
        },
        "opl_status_projection": {
            "provider": "temporal",
            "read_model_owner": OPL_OWNER,
            "managed_service_state": "ready" if managed_ready else "unavailable",
            "worker_state": "ready" if runtime_snapshot.get("worker_ready") is True else "unknown",
            "attempt_query_ready": provider_available and managed_ready,
            "retry_dead_letter_state_visible": provider_available,
        },
        "consistency_checks": {
            "provider_available_matches_managed_state": provider_available == managed_ready,
            "managed_state_source_is_typed": runtime_snapshot.get("address_source") == "managed_local_service_state",
            "server_reachable": runtime_snapshot.get("server_reachable") is True,
            "worker_ready": runtime_snapshot.get("worker_ready") is True,
            "task_queue_declared": bool(str(runtime_snapshot.get("task_queue") or "").strip()),
        },
        "blocker": blocker,
        "authority_boundary": {
            "projection_owner": OPL_OWNER,
            "domain_truth_owner": DOMAIN_OWNER,
            "read_only": True,
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "provider_completion_is_paper_closure": False,
        },
    }

def build_legacy_retirement_tombstone_proof() -> dict[str, Any]:
    retired_surfaces = [
        {
            "surface_id": "hermes_agent_executor_adapter",
            "classification": "explicit_optional_executor_adapter",
            "default_caller": False,
            "retention_reason": "proof_or_diagnostics_only",
            "replacement_ref": "/opl_provider_ready_contract/executor_requirements",
        },
        {
            "surface_id": "hermes_scheduler_hosted_runtime",
            "classification": "retired_no_default_caller",
            "default_caller": False,
            "retention_reason": "tombstoned_history_reference_only",
            "replacement_ref": "/opl_provider_ready_contract/provider_topology",
            "tombstone_ref": "contracts/runtime/legacy-active-path-tombstones.json",
        },
        {
            "surface_id": "mds_deepscientist_backend",
            "classification": "fixture_or_provenance_only",
            "default_caller": False,
            "retention_reason": "historical_fixture_and_parity_oracle",
            "replacement_ref": "/standard_domain_agent_skeleton",
        },
        {
            "surface_id": "workspace_local_scheduler",
            "classification": "standalone_diagnostics_only",
            "default_caller": False,
            "retention_reason": "local_diagnostics_not_opl_hosted_runtime",
            "replacement_ref": "/managed_temporal_state_consistency",
            "tombstone_ref": "contracts/runtime/legacy-active-path-tombstones.json",
        },
    ]
    return {
        "surface_kind": "mas_legacy_retirement_tombstone_proof",
        "version": "mas-legacy-retirement-tombstone-proof.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "no_active_default_caller_proven",
        "active_default_callers": [],
        "replacement_parity_refs": [
            "/opl_provider_ready_contract/provider_topology",
            "/opl_provider_ready_contract/managed_temporal_state_consistency",
            "/opl_provider_ready_contract/runtime_transport_handoff_projection",
            "/product_entry_manifest/functional_consumer_boundary",
            "contracts/runtime/legacy-active-path-tombstones.json",
        ],
        "no_regression_evidence_refs": [
            "tests/product_entry_cases/action_catalog_parity_cases/provider_cases.py::test_product_entry_manifest_exposes_provider_guarded_soak_read_model_with_typed_blockers",
            "tests/test_cli_cases/sidecar_family_adapter_command_cases/export_cases.py::test_sidecar_family_export_exposes_managed_temporal_state_consistency",
        ],
        "retired_or_tombstoned_surfaces": retired_surfaces,
        "tombstone_refs": [
            "contracts/runtime/legacy-active-path-tombstones.json",
            "docs/history/runtime/legacy_active_path_tombstones.md",
        ],
        "history_refs": [
            "docs/active/opl_temporal_mas_runtime_retirement_program.md",
            "docs/decisions.md#2026-05-16默认-domain-slo-scheduler-projection-owner-迁到-opl-replacement",
        ],
        "physical_tombstone_refs": [
            "contracts/runtime/legacy-active-path-tombstones.json",
            "docs/history/runtime/legacy_active_path_tombstones.md",
        ],
        "removal_policy": {
            "delete_or_tombstone_when": [
                "no_default_cli_mcp_product_entry_or_skill_caller",
                "no_opl_active_reference",
                "no_fixture_or_provenance_dependency",
                "replacement_diagnostic_or_history_link_exists",
            ],
            "current_action": "legacy_active_path_tombstones_landed",
        },
        "authority_boundary": {
            "proof_role": "caller_inventory_and_tombstone_read_model",
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
    }

def load_opl_production_proof(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    proof_path = Path(path).expanduser()
    try:
        payload = json.loads(proof_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "surface_kind": "opl_temporal_production_residency_proof_ref",
            "proof_ref": str(proof_path),
            "evidence_status": "unreadable",
            "error": f"{exc.__class__.__name__}: {exc}",
        }
    if not isinstance(payload, Mapping):
        return {
            "surface_kind": "opl_temporal_production_residency_proof_ref",
            "proof_ref": str(proof_path),
            "evidence_status": "invalid_shape",
        }
    return dict(payload)

def build_provider_availability_from_opl_proof(
    *,
    opl_production_proof: Mapping[str, Any] | None = None,
    proof_ref: str | Path | None = None,
) -> dict[str, Any]:
    if opl_production_proof is None:
        return _provider_availability(provider_available=False)
    wrapper = _mapping(opl_production_proof.get("family_runtime_residency_proof")) or opl_production_proof
    production = _mapping(wrapper.get("production_residency_proof")) or wrapper
    checks = _mapping(production.get("checks"))
    required_checks = (
        "external_temporal_server_reachable",
        "managed_worker_ready",
        "worker_completed_attempt",
        "worker_restart_requery",
        "signal_history_preserved",
        "typed_closeout_required_for_completed",
        "missing_closeout_blocks_completion",
        "retry_or_dead_letter_boundary_observed",
        "domain_truth_boundary_preserved",
    )
    missing_checks = [check for check in required_checks if checks.get(check) is not True]
    receipt = _mapping(production.get("proof_receipt"))
    closeout_status = str(production.get("closeout_status") or wrapper.get("closeout_status") or "")
    provider_kind = str(production.get("provider_kind") or wrapper.get("provider_kind") or "")
    proven = (
        provider_kind == "temporal"
        and closeout_status == "production_residency_proven"
        and receipt.get("receipt_status") == "proven"
        and not missing_checks
    )
    if proven:
        runtime_snapshot = _mapping(production.get("runtime_snapshot"))
        return {
            "status": "available",
            "provider_attempt_available": True,
            "provider_kind": "temporal",
            "proof_surface": str(production.get("surface_kind") or wrapper.get("surface_kind") or ""),
            "proof_ref": str(proof_ref) if proof_ref is not None else None,
            "closeout_status": closeout_status,
            "proof_receipt": {
                "receipt_kind": receipt.get("receipt_kind"),
                "receipt_status": receipt.get("receipt_status"),
                "completed_workflow_id": receipt.get("completed_workflow_id"),
                "blocked_workflow_id": receipt.get("blocked_workflow_id"),
            },
            "runtime_snapshot": {
                "address_source": runtime_snapshot.get("address_source"),
                "lifecycle_status": runtime_snapshot.get("lifecycle_status"),
                "server_reachable": runtime_snapshot.get("server_reachable"),
                "worker_ready": runtime_snapshot.get("worker_ready"),
                "task_queue": runtime_snapshot.get("task_queue"),
            },
            "checks": {check: checks.get(check) is True for check in required_checks},
            "semantics": {
                "provider_residency_proven": True,
                "provider_completion_is_paper_closure": False,
                "paper_closure_requires_mas_owner_receipt": True,
                "mas_runtime_watch_role": "domain_truth_and_local_diagnostics",
            },
        }
    return {
        "status": "typed_blocker",
        "provider_attempt_available": False,
        "proof_ref": str(proof_ref) if proof_ref is not None else None,
        "blocker": {
            "surface_kind": "mas_provider_guarded_soak_typed_blocker",
            "blocker_id": "provider_guarded_soak_production_proof_not_proven",
            "owner": OPL_OWNER,
            "reason": "OPL Temporal production proof is missing, unreadable, or not proven.",
            "required_owner_surface": "OPL production Temporal residency proof",
            "write_permitted": False,
            "observed_provider_kind": provider_kind or None,
            "observed_closeout_status": closeout_status or None,
            "missing_checks": missing_checks,
            "evidence_status": opl_production_proof.get("evidence_status"),
        },
    }

def _provider_residency_receipt_refs_from_availability(availability: Mapping[str, Any]) -> dict[str, str]:
    if availability.get("provider_attempt_available") is not True:
        return {}
    proof_ref = str(availability.get("proof_ref") or "").strip()
    receipt = _mapping(availability.get("proof_receipt"))
    completed_workflow_id = str(receipt.get("completed_workflow_id") or "").strip()
    blocked_workflow_id = str(receipt.get("blocked_workflow_id") or "").strip()
    base_ref = proof_ref or completed_workflow_id or blocked_workflow_id
    if not base_ref:
        return {}
    return {
        "temporal_production_residency": base_ref,
        "worker_restart_requery": base_ref,
        "retry_dead_letter": blocked_workflow_id or base_ref,
        "long_soak_receipt": base_ref,
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

def _provider_guarded_soak_target_coverage(
    target_study: str,
    *,
    provider_attempt_available: bool = False,
) -> dict[str, Any]:
    if provider_attempt_available:
        return {
            "surface_kind": "mas_provider_guarded_soak_target_coverage",
            "target_study": target_study,
            "status": "provider_available_guarded_apply_pending",
            "expected_provider_proof_surface": PROVIDER_HOSTED_PROOF_SURFACE,
            "expected_guarded_apply_surface": GUARDED_APPLY_PROOF_SURFACE,
            "write_permitted": False,
            "provider_completion_is_paper_closure": False,
            "paper_closure_requires_mas_owner_receipt": True,
            "required_owner_surface": "MAS owner receipt",
        }
    return {
        "surface_kind": "mas_provider_guarded_soak_typed_blocker",
        "target_study": target_study,
        "status": "typed_blocker",
        "blocker_id": f"provider_guarded_soak_evidence_unavailable:{target_study}",
        "expected_provider_proof_surface": PROVIDER_HOSTED_PROOF_SURFACE,
        "expected_guarded_apply_surface": GUARDED_APPLY_PROOF_SURFACE,
        "write_permitted": False,
        "provider_completion_is_paper_closure": False,
        "paper_closure_requires_mas_owner_receipt": True,
        "required_owner_surface": "MAS owner receipt",
    }

def _provider_residency_check(
    *,
    check_id: str,
    provider_available: bool,
    receipt_ref: object,
) -> dict[str, Any]:
    receipt_text = str(receipt_ref or "").strip()
    status = "receipt_observed" if provider_available and receipt_text else "typed_blocker"
    return {
        "check_id": check_id,
        "status": status,
        "receipt_ref": receipt_text or None,
        "owner": OPL_OWNER,
        "body_included": False,
        "write_permitted": False,
        "required_surface": _provider_residency_required_surface(check_id),
    }

def _provider_residency_required_surface(check_id: str) -> str:
    return {
        "temporal_production_residency": "OPL Temporal production residency receipt",
        "worker_restart_requery": "OPL worker restart and re-query receipt",
        "retry_dead_letter": "OPL retry policy and dead-letter receipt",
        "long_soak_receipt": "OPL long soak receipt",
    }.get(check_id, "OPL provider residency receipt")
