from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.profiles import WorkspaceProfile


SURFACE_KIND = "mas_opl_provider_ready_contract"
VERSION = "mas-opl-provider-ready.v1"
TARGET_DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "med-autoscience"
OPL_OWNER = "one-person-lab"

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
    "build_standard_domain_agent_skeleton_surface",
    "receipt_refs_for_profile",
    "requested_writes_from_task",
]
