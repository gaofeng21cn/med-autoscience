from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience import stage_quality_contract
from med_autoscience.profiles import WorkspaceProfile


SURFACE_KIND = "mas_opl_provider_ready_contract"
VERSION = "mas-opl-provider-ready.v1"
TARGET_DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "med-autoscience"
OPL_OWNER = "one-person-lab"
DEFAULT_PROVIDER_GUARDED_SOAK_TARGETS = ("DM002", "DM003", "Obesity")
PROVIDER_HOSTED_PROOF_SURFACE = "real_paper_autonomy_provider_hosted_paper_proof"
GUARDED_APPLY_PROOF_SURFACE = "real_paper_autonomy_guarded_apply_proof"

FORBIDDEN_AUTHORITY_WRITES = (
    "study_truth_write",
    "publication_quality_verdict",
    "artifact_gate_override",
    "current_package_write",
    "evidence_ledger_write",
    "review_ledger_write",
    "study_truth",
    "publication_eval",
    "controller_decisions",
    "current_package",
    "artifact_gate",
    "memory_body_write",
    "publication_route_memory_body",
    "publication_route_memory_writeback_accept",
    "memory_write_router_accept",
)


def build_opl_provider_ready_contract(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    allowed_task_kinds: Iterable[str],
    opl_production_proof: Mapping[str, Any] | None = None,
    opl_production_proof_ref: str | Path | None = None,
) -> dict[str, Any]:
    profile_ref_text = str(profile_ref) if profile_ref is not None else "<profile>"
    provider_availability = build_provider_availability_from_opl_proof(
        opl_production_proof=opl_production_proof,
        proof_ref=opl_production_proof_ref,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "provider_ready_skeleton",
        "summary": (
            "MAS exposes a provider-ready OPL/Temporal adapter contract while MAS-owned runtime, "
            "publication, quality, and artifact truth remain in workspace artifacts."
        ),
        "provider_topology": _provider_topology(provider_availability=provider_availability),
        "executor_requirements": {
            "adapter_owner": "one-person-lab",
            "generic_executor_adapter_owner": OPL_OWNER,
            "default_executor_kind": "codex_cli_default",
            "required_adapter": "opl_executor_adapter",
            "accepted_receipts": ["opl_provider_attempt_receipt", "typed_closeout_receipt"],
            "domain_action_authority": DOMAIN_OWNER,
            "mas_builtin_executor_adapter": False,
            "mas_local_codex_cli_scope": "standalone_diagnostics_only",
            "non_default_executor_opt_in_owner": OPL_OWNER,
            "non_default_executor_opt_in_policy": "explicit_opt_in_only_receipt_to_mas",
            "mas_owned_hermes_or_claude_executor": False,
        },
        "direct_mas_path": _direct_mas_path(profile_ref_text),
        "sidecar_contract": _sidecar_contract(profile=profile, profile_ref_text=profile_ref_text),
        "forbidden_write_guard": build_forbidden_write_guard_proof(
            result="configured",
            task_id=None,
            task_kind=None,
            requested_writes=(),
        ),
        "managed_temporal_state_consistency": build_managed_temporal_state_consistency_read_model(
            provider_availability=provider_availability,
        ),
        "provider_guarded_soak_read_model": build_provider_guarded_soak_read_model(
            provider_availability=provider_availability,
        ),
        "legacy_retirement_tombstone_proof": build_legacy_retirement_tombstone_proof(),
        "workspace_runtime_artifact_root_locator": _workspace_runtime_artifact_root_locator(profile=profile),
        "lifecycle_inventory": build_opl_lifecycle_inventory_surface(),
        "domain_agent_skeleton_mapping": build_domain_agent_skeleton_mapping_surface(),
        "allowed_task_kinds": sorted(str(item) for item in allowed_task_kinds),
        "truth_source_precedence": {
            "direct_mas_skill_path": "authoritative",
            "opl_provider_attempt_history": "transport_receipt_only",
            "opl_runtime_projection": "read_only_index_only",
            "provider_completion_can_advance_paper_progress": False,
            "paper_progress_requires_mas_artifact_delta_or_gate_owner": True,
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
            "classification": "retire_after_parity",
            "default_caller": False,
            "retention_reason": "history_or_optional_provider_provenance",
            "replacement_ref": "/opl_provider_ready_contract/provider_topology",
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
        },
    ]
    return {
        "surface_kind": "mas_legacy_retirement_tombstone_proof",
        "version": "mas-legacy-retirement-tombstone-proof.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "no_active_default_caller_proven",
        "active_default_callers": [],
        "retired_or_tombstoned_surfaces": retired_surfaces,
        "removal_policy": {
            "delete_or_tombstone_when": [
                "no_default_cli_mcp_product_entry_or_skill_caller",
                "no_opl_active_reference",
                "no_fixture_or_provenance_dependency",
                "replacement_diagnostic_or_history_link_exists",
            ],
            "current_action": "safe_to_tombstone_docs_and_optional_residue",
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


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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


def build_opl_lifecycle_inventory_surface() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_lifecycle_inventory",
        "version": "mas-opl-lifecycle-inventory.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "classification_policy": "framework_generic_moves_to_opl_refs_only_mas_domain_specific_remains_mas_truth",
        "framework_generic": [
            _inventory_item(
                "provider_stage_attempt",
                "OPL provider attempt ledger, retry, dead-letter, signal, and query metadata.",
                "move_to_opl_provider",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
            _inventory_item(
                "runtime_lifecycle_sidecar_index",
                "SQLite-style lifecycle index, receipt lookup, restore proof, migration ledger, and retention receipt.",
                "lift_to_opl_framework",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
            _inventory_item(
                "artifact_locator_and_retention_projection",
                "Artifact root locator, freshness index, retention policy, cache cleanup receipt, and restore proof refs.",
                "lift_to_opl_framework",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
            _inventory_item(
                "operator_projection_cache",
                "Read-only workbench or runtime projection cache built from MAS source refs.",
                "move_to_opl_provider",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
        ],
        "mas_domain_specific": [
            _inventory_item(
                "study_truth_and_runtime_health",
                "StudyTruth, RuntimeHealth, study macro state, runtime_watch, and study_runtime_status authority.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
            _inventory_item(
                "publication_quality_and_ai_reviewer",
                "publication_eval/latest.json, AI reviewer workflow, publication gate, and quality verdicts.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
            _inventory_item(
                "paper_package_and_artifact_authority",
                "canonical manuscript, evidence/review ledgers, submission_minimal, current package, and artifact gate.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
            _inventory_item(
                "owner_route_and_domain_dispatch_receipts",
                "MAS owner-route reconcile, guarded domain dispatch receipts, gate replay, and stop-loss/human gate.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
        ],
    }


def build_domain_agent_skeleton_mapping_surface() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_domain_agent_skeleton_mapping",
        "version": "mas-opl-domain-agent-skeleton-mapping.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "mapping_mode": "contract_only_no_physical_artifact_move",
        "repo_tracks_real_workspace_artifacts": False,
        "skeleton": {
            "agent/stages": [
                "templates/agent_entry_modes.yaml",
                "med_autoscience.controllers.stage_knowledge_plane.stage_knowledge_plane_contract",
            ],
            "agent/prompts": [
                "MAS app skill command contracts",
                "stage prompt and review/repair prompt surfaces",
            ],
            "agent/skills": [
                "medautosci product skill-catalog --format json",
                "medautosci sidecar export --format json",
                "medautosci sidecar dispatch --format json",
            ],
            "agent/knowledge": [
                "artifacts/stage_knowledge/<stage>/latest.json",
                "stage_memory_closeout_packet",
                "memory_write_router_receipt",
                "stage_recall_index",
            ],
            "agent/quality_gates": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "AI reviewer workflow",
                "claim-evidence and submission package gates",
                stage_quality_contract.REPO_PATH,
            ],
            "contracts/runtime/sidecar": [
                "mas_family_sidecar_export",
                "mas_family_sidecar_dispatch_receipt",
                "mas_opl_forbidden_write_guard_proof",
            ],
            "contracts/runtime/projection_builders": [
                "mas_opl_runtime_workbench_projection",
                "progress_portal opl_handoff projection",
                "product-entry manifest provider-ready contract",
            ],
            "contracts/runtime/lifecycle_adapters": [
                "mas_opl_lifecycle_inventory",
                "workspace_runtime_artifact_root_locator",
                "runtime_lifecycle_sqlite sidecar ref",
            ],
        },
    }


def build_standard_domain_agent_skeleton_surface() -> dict[str, Any]:
    mapping = build_domain_agent_skeleton_mapping_surface()
    return {
        "surface_kind": "standard_domain_agent_skeleton",
        "version": "standard-domain-agent-skeleton.v1",
        "skeleton_id": "mas.standard_domain_agent_skeleton.v1",
        "target_domain_id": DOMAIN_OWNER,
        "mapping_mode": mapping["mapping_mode"],
        "repo_tracks_real_workspace_artifacts": mapping["repo_tracks_real_workspace_artifacts"],
        "repo_source_boundary": {
            "required_dirs": ["agent", "contracts", "runtime", "docs"],
            "forbidden_dirs": ["artifacts"],
        },
        "skeleton": mapping["skeleton"],
        "workspace_runtime_artifact_root_locator_ref": (
            "/product_entry_manifest/workspace_runtime_artifact_root_locator"
        ),
        "quality_pack_locator": stage_quality_contract.build_stage_quality_pack_locator_projection(),
        "artifact_boundary": {
            "repo_contains_real_artifacts": False,
            "artifact_roots_are_locators": True,
            "workspace_artifact_locator_refs": [
                "/product_entry_manifest/workspace_runtime_artifact_root_locator"
            ],
            "runtime_artifact_locator_refs": [
                "/product_entry_manifest/workspace_runtime_artifact_root_locator"
            ],
        },
        "physical_skeleton_layout_audit": build_physical_skeleton_layout_audit_surface(),
        "authority_boundary": {
            "opl": "framework_transport_and_projection_only",
            "domain_agent": "truth_quality_artifact_owner",
            "forbidden_opl_authority": [
                "domain_truth",
                "quality_verdict",
                "canonical_artifact_blob",
                "publication_or_export_gate",
            ],
        },
    }


def build_physical_skeleton_layout_audit_surface() -> dict[str, Any]:
    slots = [
        _physical_skeleton_slot(
            "agent/stages",
            repo_paths=[
                "docs/policies/study-workflow/stage_led_research_autonomy.md",
                "src/med_autoscience/controllers/stage_knowledge_plane.py",
            ],
        ),
        _physical_skeleton_slot(
            "agent/prompts",
            repo_paths=[
                "templates/agent_entry_modes.yaml",
                "templates/codex/medautoscience-entry.SKILL.md",
                "templates/openclaw/medautoscience-entry.prompt.md",
            ],
        ),
        _physical_skeleton_slot(
            "agent/skills",
            repo_paths=[
                "src/med_autoscience/cli.py",
                "src/med_autoscience/cli_parts/parser.py",
                "plugins/mas/bin/medautosci-mcp",
            ],
        ),
        _physical_skeleton_slot(
            "agent/knowledge",
            repo_paths=[
                "docs/policies/study-workflow/publication_route_memory_policy.md",
                "docs/policies/study-workflow/publication_route_memory_library.md",
                "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
            ],
        ),
        _physical_skeleton_slot(
            "agent/quality_gates",
            repo_paths=[
                stage_quality_contract.REPO_PATH,
                "src/med_autoscience/controllers/publication_gate.py",
                "src/med_autoscience/controllers/ai_reviewer_publication_eval.py",
                "src/med_autoscience/controllers/paper_repair_executor.py",
            ],
        ),
        _physical_skeleton_slot(
            "contracts/runtime/sidecar",
            repo_paths=[
                "src/med_autoscience/controllers/sidecar_family_adapter.py",
                "src/med_autoscience/controllers/opl_provider_ready_adapter.py",
            ],
        ),
        _physical_skeleton_slot(
            "contracts/runtime/projection_builders",
            repo_paths=[
                "src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py",
                "src/med_autoscience/controllers/real_paper_autonomy_soak_inventory.py",
            ],
        ),
        _physical_skeleton_slot(
            "runtime/artifact_locator",
            locator_refs=["/product_entry_manifest/workspace_runtime_artifact_root_locator"],
            status="locator_only_no_artifact_body",
        ),
        _physical_skeleton_slot(
            "artifacts",
            locator_refs=["/product_entry_manifest/workspace_runtime_artifact_root_locator"],
            status="forbidden_repo_artifact_body",
        ),
    ]
    return {
        "surface_kind": "standard_domain_agent_physical_skeleton_layout_audit",
        "version": "standard-domain-agent-physical-layout-audit.v1",
        "standard_layout_version": "standard-domain-agent-physical-layout.v1",
        "status": "standardized_with_locator_refs",
        "repo_source_root": "repo:med-autoscience",
        "repo_tracks_real_workspace_artifacts": False,
        "artifact_body_included": False,
        "workspace_runtime_artifact_root_locator_ref": "/product_entry_manifest/workspace_runtime_artifact_root_locator",
        "slots": slots,
        "summary": {
            "mapped_slot_count": sum(1 for slot in slots if slot["status"] == "mapped_to_existing_repo_paths"),
            "locator_only_slot_count": sum(1 for slot in slots if slot["locator_refs"] and not slot["repo_paths"]),
            "missing_required_slot_count": sum(1 for slot in slots if slot["status"] == "missing_required_repo_path"),
            "forbidden_repo_artifact_body": any(slot["status"] == "forbidden_repo_artifact_body" for slot in slots),
        },
    }


def _physical_skeleton_slot(
    slot_id: str,
    *,
    repo_paths: list[str] | None = None,
    locator_refs: list[str] | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    paths = list(repo_paths or [])
    return {
        "slot_id": slot_id,
        "status": status or ("mapped_to_existing_repo_paths" if paths else "missing_required_repo_path"),
        "repo_paths": paths,
        "locator_refs": list(locator_refs or []),
        "artifact_body_included": False,
        "repo_tracks_real_workspace_artifacts": False,
    }


def receipt_refs_for_profile(profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_sidecar_receipt_refs",
        "version": "mas-opl-sidecar-receipt-refs.v1",
        "dispatch_receipt_root": "artifacts/runtime/opl_family_sidecar/dispatch_receipts",
        "dispatch_receipt_ref_template": (
            "artifacts/runtime/opl_family_sidecar/dispatch_receipts/<sha256(task_id)[:20]>.json"
        ),
        "export_receipt_ref": "sidecar export response body",
        "workspace_root": str(profile.workspace_root),
        "repo_tracked": False,
        "receipt_authority": DOMAIN_OWNER,
    }


def requested_writes_from_task(task: Mapping[str, Any]) -> list[str]:
    payload = task.get("payload") if isinstance(task.get("payload"), Mapping) else {}
    requested: list[str] = []
    for flag in (
        "domain_truth_write",
        "artifact_gate_override",
        "study_truth_write",
        "publication_quality_verdict",
        "current_package_write",
        "memory_body_write",
        "publication_route_memory_writeback_accept",
        "memory_write_router_accept",
    ):
        if bool(payload.get(flag)):
            requested.append(flag)
    payload_writes = payload.get("requested_writes")
    if isinstance(payload_writes, list):
        requested.extend(str(item) for item in payload_writes if str(item or "").strip())
    return list(dict.fromkeys(requested))


def _provider_topology(*, provider_availability: Mapping[str, Any] | None = None) -> dict[str, Any]:
    provider_available = _mapping(provider_availability).get("provider_attempt_available") is True
    return {
        "target_provider": "temporal",
        "target_provider_owner": "one-person-lab",
        "provider_state": "production_residency_proven" if provider_available else "contract_ready_skeleton",
        "legacy_provider": "hermes_legacy",
        "legacy_provider_classification": "optional_diagnostics_or_retire_after_parity",
        "hosted_runtime_policy": "opl_explicit_opt_in_only",
        "provider_attempt_owner": OPL_OWNER,
        "domain_action_owner": DOMAIN_OWNER,
        "provider_attempt_is_truth": False,
    }


def _direct_mas_path(profile_ref_text: str) -> dict[str, Any]:
    return {
        "path_id": "direct_mas_skill_path",
        "status": "authoritative",
        "profile_ref": profile_ref_text,
        "commands": {
            "read_status": f"medautosci study-progress --profile {profile_ref_text} --format json",
            "read_runtime": f"medautosci study-runtime-status --profile {profile_ref_text} --study-id <study_id>",
            "reconcile": f"medautosci runtime-supervisor-reconcile --profile {profile_ref_text} --dry-run",
        },
        "must_converge_with_opl_hosted_path": True,
    }


def _sidecar_contract(*, profile: WorkspaceProfile, profile_ref_text: str) -> dict[str, Any]:
    return {
        "export_command": f"medautosci sidecar export --profile {profile_ref_text} --format json",
        "dispatch_command": "medautosci sidecar dispatch --task <task.json> --format json",
        "queue_hydration_source": "/pending_family_tasks",
        "dispatch_receipt_refs": receipt_refs_for_profile(profile),
        "idempotency_contract": {
            "dedupe_key_required": True,
            "source_fingerprint_required_when_available": True,
            "provider_retry_must_reuse_task_id": True,
            "provider_retry_must_not_mutate_mas_truth": True,
        },
    }


def _workspace_runtime_artifact_root_locator(*, profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "surface_kind": "workspace_runtime_artifact_root_locator",
        "version": "workspace-runtime-artifact-root-locator.v1",
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "studies_root": str(profile.studies_root),
        "repo_root_tracks_real_artifacts": False,
        "locators": {
            "study_artifact_root": "studies/<study_id>/artifacts",
            "runtime_artifact_root": "studies/<study_id>/artifacts/runtime",
            "publication_eval": "studies/<study_id>/artifacts/publication_eval/latest.json",
            "controller_decisions": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "stage_knowledge_packet": "studies/<study_id>/artifacts/stage_knowledge/<stage>/latest.json",
            "dispatch_receipts": "artifacts/runtime/opl_family_sidecar/dispatch_receipts",
            "runtime_lifecycle_sqlite": "artifacts/runtime/runtime_lifecycle.sqlite",
        },
    }


def _inventory_item(
    item_id: str,
    summary: str,
    target_class: str,
    *,
    owner: str,
    mas_exports_refs_only: bool = False,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "summary": summary,
        "target_class": target_class,
        "owner": owner,
        "mas_exports_refs_only": mas_exports_refs_only,
        "domain_truth_allowed": owner == DOMAIN_OWNER,
    }


__all__ = [
    "FORBIDDEN_AUTHORITY_WRITES",
    "SURFACE_KIND",
    "VERSION",
    "build_domain_agent_skeleton_mapping_surface",
    "build_forbidden_write_guard_proof",
    "build_legacy_retirement_tombstone_proof",
    "build_managed_temporal_state_consistency_read_model",
    "build_opl_lifecycle_inventory_surface",
    "build_opl_provider_ready_contract",
    "build_provider_availability_from_opl_proof",
    "build_physical_skeleton_layout_audit_surface",
    "build_provider_guarded_soak_read_model",
    "build_standard_domain_agent_skeleton_surface",
    "load_opl_production_proof",
    "receipt_refs_for_profile",
    "requested_writes_from_task",
]
