from __future__ import annotations

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
PROVIDER_RESIDENCY_SURFACE = "provider_runtime_residency_read_model"
PRODUCTION_RESIDENCY_CHECKS = (
    "temporal_production_residency",
    "worker_restart_requery",
    "retry_dead_letter",
    "long_soak_receipt",
)

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
) -> dict[str, Any]:
    profile_ref_text = str(profile_ref) if profile_ref is not None else "<profile>"
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "provider_ready_skeleton",
        "summary": (
            "MAS exposes a provider-ready OPL/Temporal adapter contract while MAS-owned runtime, "
            "publication, quality, and artifact truth remain in workspace artifacts."
        ),
        "provider_topology": _provider_topology(),
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
        "provider_guarded_soak_read_model": build_provider_guarded_soak_read_model(
            provider_available=False,
        ),
        "provider_residency_read_model": build_provider_residency_read_model(
            provider_available=False,
        ),
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
    provider_available: bool,
    target_studies: Iterable[str] = DEFAULT_PROVIDER_GUARDED_SOAK_TARGETS,
) -> dict[str, Any]:
    targets = tuple(str(item) for item in target_studies if str(item or "").strip())
    no_forbidden_write_proof = build_forbidden_write_guard_proof(
        result=(
            "configured"
            if provider_available
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
        "provider_availability": _provider_availability(provider_available=provider_available),
        "target_coverage": [
            _provider_guarded_soak_target_coverage(target) for target in targets
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


def _provider_guarded_soak_target_coverage(target_study: str) -> dict[str, Any]:
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


def _provider_topology() -> dict[str, Any]:
    return {
        "target_provider": "temporal",
        "target_provider_owner": "one-person-lab",
        "provider_state": "contract_ready_skeleton",
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
    "build_opl_lifecycle_inventory_surface",
    "build_opl_provider_ready_contract",
    "build_physical_skeleton_layout_audit_surface",
    "build_provider_guarded_soak_read_model",
    "build_provider_residency_read_model",
    "build_standard_domain_agent_skeleton_surface",
    "receipt_refs_for_profile",
    "requested_writes_from_task",
]
