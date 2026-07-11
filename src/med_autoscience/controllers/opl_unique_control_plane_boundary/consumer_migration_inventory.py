from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .functional_followthrough_gaps import (
    PHYSICAL_RETIREMENT_DECISION_REF,
    PRIVATE_SURFACE_PHYSICAL_RETIREMENT_DECISION,
    build_private_surface_physical_retirement_decision_readback,
    physical_retirement_authorized,
)


PRIVATE_GENERIC_TOKEN_RESIDUE_SPECS = (
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "path": "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
        "forbidden_tokens": (
            "def build_artifact_lifecycle_inventory(",
            "def build_artifact_registry(",
            "def build_archive_cleanup_readiness(",
            "os.walk(",
        ),
    },
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "path": "src/med_autoscience/controllers/artifact_lifecycle_operations_report",
        "forbidden_tokens": (
            "os.walk(",
            "def _scan_workspace(",
            "def build_artifact_retention_operations_plan(",
            "def build_storage_governance_policy_projection(",
        ),
    },
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "path": "src/med_autoscience/controllers/workspace_authority_migration_audit.py",
        "forbidden_tokens": (
            "def _iter_candidate_paths(",
            "def _generated_delivery_paths(",
            "def run_migration_audit(",
            ".rglob(",
        ),
    },
    {
        "module_id": "workspace_source_intake_shell",
        "path": "src/med_autoscience/controllers/workspace_literature.py",
        "forbidden_tokens": (
            "def render_workspace_literature_files(",
            '"registry.jsonl"',
            '"references.bib"',
            "def _write_text(",
        ),
    },
    {
        "module_id": "publication_route_memory_locator_transport_shell",
        "path": (
            "src/med_autoscience/controllers/stage_knowledge_plane/"
            "publication_route_memory_inventory.py"
        ),
        "forbidden_tokens": (
            '"opl_aion_receipt_inventory"',
            "def _writeback_receipt_inventory(",
            '"body_free_evidence_packets"',
            "maintenance_workbench",
        ),
    },
    {
        "module_id": "paper_mission_owner_surface_materialize_dispatch_shell",
        "path": "src/med_autoscience/controllers/domain_action_request_materializer",
        "status": "retired_absence_guard",
        "forbidden_tokens": (
            "resolve_developer_supervisor_mode",
            "github_gate",
            "MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN",
            "developer_apply_safe",
        ),
    },
    {
        "module_id": "workbench_portal_generic_shell",
        "path": "src/med_autoscience/controllers/product_entry",
        "forbidden_tokens": (
            "def read_workspace_cockpit(",
            "def build_product_entry_status(",
            "def render_workspace_cockpit_markdown(",
            "def _attention_queue(",
            "workspace_attention_queue_preview",
        ),
    },
)

RETIRED_PRIVATE_GENERIC_PATHS = (
    (
        "artifact_lifecycle_storage_audit_shell",
        "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        "src/med_autoscience/controllers/artifact_lifecycle_authority_kernel.py",
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        "src/med_autoscience/controllers/artifact_lifecycle_operations_report/__init__.py",
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        "src/med_autoscience/controllers/workspace_authority_migration_audit.py",
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        "src/med_autoscience/controllers/continuous_soak_summary.py",
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        "src/med_autoscience/runtime_protocol/artifact_authority.py",
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        (
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report/"
            "scan_policy.py"
        ),
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        (
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report/"
            "operational_summary.py"
        ),
    ),
    (
        "artifact_lifecycle_storage_audit_shell",
        (
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report/"
            "study_projection.py"
        ),
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/manifest_status_surface.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/attention_projection.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_attention.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/attention_hub.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_ai.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_common.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_header.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_medical.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_queue.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_sections.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/cockpit_markdown_studies.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/command_assembly.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/health_cards.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/progress_projection.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/readiness_and_delivery.py",
    ),
    (
        "workbench_portal_generic_shell",
        "src/med_autoscience/controllers/product_entry/workspace_cockpit/state_and_study_items.py",
    ),
)


def build_source_morphology(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or Path(__file__).resolve().parents[4]).resolve()
    source_truth_available = (root / "src" / "med_autoscience").is_dir()
    residues: list[dict[str, str]] = []
    read_errors: list[dict[str, str]] = []
    scanned_paths: set[str] = set()

    if source_truth_available:
        for spec in PRIVATE_GENERIC_TOKEN_RESIDUE_SPECS:
            relative_path = str(spec["path"])
            source_path = root / relative_path
            for candidate in _python_source_files(source_path):
                candidate_ref = candidate.relative_to(root).as_posix()
                scanned_paths.add(candidate_ref)
                try:
                    source = candidate.read_text(encoding="utf-8")
                except OSError as exc:
                    read_errors.append(
                        {
                            "module_id": str(spec["module_id"]),
                            "path": candidate_ref,
                            "reason": type(exc).__name__,
                        }
                    )
                    continue
                for token in spec["forbidden_tokens"]:
                    if str(token) in source:
                        residues.append(
                            {
                                "module_id": str(spec["module_id"]),
                                "path": candidate_ref,
                                "reason": "forbidden_private_generic_token_present",
                                "token": str(token),
                            }
                        )

        for module_id, relative_path in RETIRED_PRIVATE_GENERIC_PATHS:
            if (root / relative_path).exists():
                residues.append(
                    {
                        "module_id": module_id,
                        "path": relative_path,
                        "reason": "retired_private_generic_path_present",
                        "token": "",
                    }
                )

    residue_module_ids = sorted({item["module_id"] for item in residues})
    source_purity_gap_count = (
        len(residues) + len(read_errors) + (0 if source_truth_available else 1)
    )
    return {
        "surface_kind": "mas_standard_agent_source_morphology",
        "status": "clean" if source_purity_gap_count == 0 else "residue_or_scan_gap",
        "source_truth_available": source_truth_available,
        "scanned_source_paths": sorted(scanned_paths),
        "retired_private_generic_paths": [path for _, path in RETIRED_PRIVATE_GENERIC_PATHS],
        "active_private_generic_residue_count": len(residues),
        "active_private_generic_residue_module_ids": residue_module_ids,
        "active_private_generic_residues": residues,
        "source_read_error_count": len(read_errors),
        "source_read_errors": read_errors,
        "source_purity_gap_count": source_purity_gap_count,
    }


def _python_source_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.py"))
    return []


FUNCTIONAL_SURFACE_CLASSIFICATION = {
    "declarative_pack_generated_surface": [
        "workspace_source_intake_shell", "workbench_portal_generic_shell", "paper_mission_owner_surface_materialize_dispatch_shell",
        "generic_cli_mcp_product_wrappers", "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter", "generic_transition_runner",
    ],
    "domain_authority_refs": [
        "opl_state_index_source_adapter", "paper_progress_transition_refs", "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell", "artifact_lifecycle_storage_audit_shell",
    ],
    "minimal_authority_function": [
        "study_truth",
        "progress_projection",
        "domain_diagnostic_report",
        "publication_quality_verdict",
        "ai_reviewer_workflow",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "domain_transition_table",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "typed_blocker",
        "safe_action_refs",
    ],
}
DEFAULT_CALLER_DELETION_BRIDGE_MODULE_IDS = {
    "generic_cli_mcp_product_wrappers",
    "paper_mission_owner_surface_materialize_dispatch_shell",
    "workbench_portal_generic_shell",
}
DOMAIN_AUTHORITY_REFS_RETIREMENT_GATE_BY_MODULE = {
    "opl_state_index_source_adapter": {
        "domain_ref_consumer_refs": [
            "owner-route handoff records owner-receipt refs",
            "domain-handler/product-entry projections consume domain authority refs only",
            "workspace maintenance records archive/source/artifact locator refs only",
        ],
        "retirement_gate_status": "local_index_retired_body_free_source_adapter_active",
        "delete_or_tombstone_after": [
            "source_adapter_replaced_by_opl_generated_ref_intake",
            "owner_receipt_ref_parity_proven",
            "no_forbidden_write_proof_recorded",
            "focused_domain_authority_refs_tests_green",
        ],
        "must_not_emit": [
            "generic_runtime_verdict",
            "generic_persistence_engine_owner",
            "generic_runtime_lifecycle_owner",
            "paper_closure_verdict",
        ],
    },
    "paper_progress_transition_refs": {
        "domain_ref_consumer_refs": [
            "paper progress policy adapter keeps paper work-unit identity refs",
            "domain-handler dispatch consumes OPL transition request refs",
        ],
        "retirement_gate_status": "transition_request_refs_until_opl_runtime_readback_parity",
        "delete_or_tombstone_after": [
            "opl_domain_progress_transition_runtime_consumes_policy_refs",
            "opl_transition_runtime_readback_parity_proven",
            "paper_work_unit_identity_refs_projected_by_opl",
            "focused_transition_runtime_tests_green",
        ],
        "must_not_emit": [
            "generic_queue_owner",
            "generic_outbox_owner",
            "attempt_lifecycle_owner",
            "attempt_completion_is_publication_ready",
            "paper_closure_verdict",
        ],
    },
    "runtime_storage_maintenance": {
        "migration_class": "opl_storage_substrate_mas_refs_projection",
        "domain_ref_consumer_refs": [
            "runtime grouped storage audit commands read workspace storage refs",
            "workspace storage reports expose sizes and cleanup receipts only",
        ],
        "retirement_gate_status": "mas_refs_projection_until_opl_storage_substrate_readback",
        "delete_or_tombstone_after": [
            "opl_cleanup_policy_consumes_storage_refs",
            "opl_artifact_lifecycle_storage_audit_shell_parity_proven",
            "artifact_authority_receipt_parity_proven",
            "focused_storage_maintenance_tests_green",
        ],
        "must_not_emit": [
            "generic_cleanup_policy",
            "restore_ready_verdict",
            "paper_closure_verdict",
        ],
    },
    "publication_route_memory_locator_transport_shell": {
        "domain_ref_consumer_refs": [
            "publication-route memory CLI reads locator refs",
            "stage knowledge packet consumes body-free memory refs",
            "typed closeout memory writeback records receipt refs",
        ],
        "retirement_gate_status": "domain_memory_refs_until_opl_memory_locator_parity",
        "delete_or_tombstone_after": [
            "opl_memory_locator_consumes_body_free_refs",
            "opl_generic_memory_locator_parity_proven",
            "publication_route_memory_body_stays_domain_owned",
            "focused_memory_writeback_chain_tests_green",
        ],
        "must_not_emit": [
            "memory_body_write",
            "memory_accept_reject_verdict_without_ai_first_record",
            "paper_closure_verdict",
        ],
    },
    "artifact_lifecycle_storage_audit_shell": {
        "domain_ref_consumer_refs": [
            "artifact lifecycle CLI/MCP consumes artifact refs",
            "product-entry artifact projection consumes mutation-authority refs",
        ],
        "retirement_gate_status": "domain_artifact_refs_until_opl_artifact_lifecycle_parity",
        "delete_or_tombstone_after": [
            "opl_artifact_lifecycle_consumes_artifact_refs",
            "opl_generic_artifact_lifecycle_parity_proven",
            "artifact_mutation_authority_receipt_parity_proven",
            "focused_artifact_lifecycle_tests_green",
        ],
        "must_not_emit": [
            "generic_artifact_lifecycle_owner",
            "artifact_mutation_authorized_without_mas_receipt",
            "paper_closure_verdict",
        ],
    },
}
def _domain_authority_refs_retirement_gate(module_id: str, current_ref_status: str) -> dict[str, object]:
    gate = DOMAIN_AUTHORITY_REFS_RETIREMENT_GATE_BY_MODULE[module_id]
    return {
        "module_id": module_id,
        "classification": "domain_authority_refs",
        "migration_class": str(gate.get("migration_class") or "refs_only_domain_adapter"),
        "current_ref_status": current_ref_status,
        "domain_ref_consumer_count": len(gate["domain_ref_consumer_refs"]),
        "domain_ref_consumer_refs": list(gate["domain_ref_consumer_refs"]),
        "retirement_gate_status": gate["retirement_gate_status"],
        "delete_or_tombstone_after": list(gate["delete_or_tombstone_after"]),
        "generic_owner_claim_allowed": False,
        "can_emit_paper_closure_verdict": False,
        "can_emit_generic_owner_verdict": False,
        "must_not_emit": list(gate["must_not_emit"]),
    }


def _default_caller_deletion_bridge_exit_gate(
    item: dict[str, object],
    *,
    physical_retirement_decision: object,
) -> dict[str, object]:
    module_id = str(item["module_id"])
    classification = str(item["classification"])
    domain_authority_refs = list(item.get("mas_domain_authority_refs", []))
    current_surface_refs = list(item.get("current_surface_refs", []))
    is_authority = classification == "minimal_authority_function"
    decision_mapping = (
        physical_retirement_decision
        if isinstance(physical_retirement_decision, Mapping)
        else {}
    )
    decision_readback = build_private_surface_physical_retirement_decision_readback(
        physical_retirement_decision
    )
    scope = decision_mapping.get("scope")
    deleted_path_scopes = (
        scope.get("deleted_path_scopes") if isinstance(scope, Mapping) else []
    )
    if not isinstance(deleted_path_scopes, Sequence) or isinstance(
        deleted_path_scopes, (str, bytes)
    ):
        deleted_path_scopes = []
    matched_deleted_path_scope_ids: list[str] = []
    for deleted_path_scope in deleted_path_scopes:
        if not isinstance(deleted_path_scope, Mapping):
            continue
        surface_ids = deleted_path_scope.get("surface_ids")
        scope_id = deleted_path_scope.get("scope_id")
        if (
            isinstance(surface_ids, Sequence)
            and not isinstance(surface_ids, (str, bytes))
            and module_id in surface_ids
            and isinstance(scope_id, str)
            and scope_id.strip()
        ):
            matched_deleted_path_scope_ids.append(scope_id.strip())
    decision_authorized = decision_readback["physical_delete_authorized"] is True
    physical_delete_authorized = (
        not is_authority
        and bool(matched_deleted_path_scope_ids)
        and decision_authorized
    )
    deleted_path_scope_ids = (
        matched_deleted_path_scope_ids if physical_delete_authorized else []
    )
    gate_evidence = decision_mapping.get("gate_evidence")
    provenance = (
        gate_evidence.get("provenance") if isinstance(gate_evidence, Mapping) else {}
    )
    provenance_refs = (
        provenance.get("refs") if isinstance(provenance, Mapping) else []
    )
    if not isinstance(provenance_refs, Sequence) or isinstance(
        provenance_refs, (str, bytes)
    ):
        provenance_refs = []
    owner_decision_refs = (
        list(decision_readback["owner_decision_refs"])
        if physical_delete_authorized
        else []
    )
    return {
        "surface_kind": "mas_default_caller_deletion_domain_ref_exit_gate",
        "gate_id": f"mas.default_caller_deletion.{module_id}.domain_ref_exit.v1",
        "domain_ref_owner": "med-autoscience",
        "replacement_owner": "one-person-lab",
        "current_status": (
            "mas_domain_authority_refs_active"
            if is_authority
            else (
                "physical_retirement_authorized_for_exact_migration_scope"
                if physical_delete_authorized
                else "physical_retirement_decision_missing_or_not_authorized"
            )
        ),
        "required_before_retire": (
            []
            if physical_delete_authorized or is_authority
            else ["valid_domain_owner_physical_retirement_decision"]
        ),
        "current_surface_refs": current_surface_refs,
        "mas_domain_authority_refs": domain_authority_refs,
        "default_caller_deletion_evidence_scope": (
            "migration_decision_exact_deleted_paths_only"
            if physical_delete_authorized
            else "missing_or_invalid_migration_decision"
        ),
        "authorized_deleted_path_scope_ids": deleted_path_scope_ids,
        "owner_decision_refs": owner_decision_refs,
        "owner_decision_result_shape": "physical_delete_authorization_ref",
        "physical_delete_authorization_refs": owner_decision_refs,
        "typed_blocker_refs": [],
        "no_forbidden_write_refs": [
            f"no-forbidden-write:mas/default-caller-deletion/{module_id}/refs-only-boundary"
        ],
        "no_forbidden_write_evidence_refs": [
            f"no-forbidden-write:mas/default-caller-deletion/{module_id}/refs-only-boundary"
        ],
        "provenance_refs": (
            [PHYSICAL_RETIREMENT_DECISION_REF, *provenance_refs]
            if physical_delete_authorized
            else []
        ),
        "domain_repo_physical_delete_authorized": physical_delete_authorized,
        "physical_delete_authorized_by_refs": physical_delete_authorized,
        "mas_can_write_generic_runtime": False,
        "mas_can_own_generated_default_caller": False,
        "opl_can_write_study_truth": False,
        "opl_can_declare_publication_quality_or_export_verdict": False,
        "opl_can_issue_mas_owner_receipt": False,
        "authority_boundary": dict(decision_readback["authority_boundary"]),
    }


def _module_with_retirement_gate(
    item: dict[str, object],
    *,
    physical_retirement_decision: object,
) -> dict[str, object]:
    module_id = str(item["module_id"])
    result = dict(item)
    if item["classification"] == "domain_authority_refs":
        result["retirement_gate"] = _domain_authority_refs_retirement_gate(
            module_id,
            str(item["current_ref_status"]),
        )
    if module_id in DEFAULT_CALLER_DELETION_BRIDGE_MODULE_IDS:
        result["bridge_exit_gate"] = _default_caller_deletion_bridge_exit_gate(
            result,
            physical_retirement_decision=physical_retirement_decision,
        )
    latest_thinning_evidence = result.get("latest_thinning_evidence")
    if isinstance(latest_thinning_evidence, Mapping):
        latest_thinning_evidence = dict(latest_thinning_evidence)
        decision_authorized = physical_retirement_authorized(
            physical_retirement_decision
        )
        if module_id == "workbench_portal_generic_shell":
            materializer_boundary = latest_thinning_evidence.get(
                "read_model_materializer_boundary"
            )
            if isinstance(materializer_boundary, Mapping):
                latest_thinning_evidence["read_model_materializer_boundary"] = {
                    **materializer_boundary,
                    "domain_repo_physical_delete_authorized": decision_authorized,
                }
        elif module_id == "paper_mission_owner_surface_materialize_dispatch_shell":
            latest_thinning_evidence["domain_repo_physical_delete_authorized"] = (
                decision_authorized
            )
        result["latest_thinning_evidence"] = latest_thinning_evidence
    return result


_FUNCTIONAL_MODULE_INVENTORY = (
    {
        "module_id": "opl_state_index_source_adapter",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/runtime_protocol/opl_state_index_source_adapter.py",
            "src/med_autoscience/opl_domain_pack/",
            "src/med_autoscience/controllers/owner_route_handoff/substrate_adapter.py",
        ],
        "domain_ref_consumers": [
            "owner-route handoff domain authority refs",
            "paper work-unit and dispatch owner receipt refs",
            "domain-handler/product-entry domain authority refs projections",
        ],
        "current_ref_status": "body_free_state_index_source_adapter_no_local_persistence",
        "authority_boundary": "refs_only_owner_receipt_locator_index_not_generic_runtime_owner",
        "provenance_boundary": {
            "surface_role": "body_free_domain_authority_ref_source_adapter",
            "history_role": "retired_runtime_lifecycle_sqlite_provenance",
            "body_policy": "refs_receipts_blockers_only",
            "may_emit": ["owner_receipt_ref", "typed_blocker_ref", "progress_projection_ref", "domain_authority_locator_ref"],
            "must_not_emit": [
                "generic_runtime_verdict",
                "generic_runtime_lifecycle_owner",
                "generic_restore_verdict",
                "paper_closure_verdict",
            ],
            "generic_owner_claim_allowed": False,
        },
        "migration_action": "emit_body_free_state_index_source_refs_and_consume_opl_current_control_state",
        "retention_reason": (
            "MAS can emit body-free paper-line owner receipt, typed blocker, and locator refs; "
            "generic persistence, runtime lifecycle indexing, restore/retention, queue, and receipt ledger ownership stay in OPL."
        ),
        "opl_expected_primitives": [
            "opl_current_control_state_projection",
            "opl_provider_attempt_receipt_ledger",
            "opl_restore_retention_receipt_shell",
        ],
        "forbidden_mas_roles": [
            "generic_persistence_engine",
            "generic_lifecycle_engine",
            "generic_runtime_lifecycle_owner",
            "generic_restore_retention_owner",
        ],
        "mas_domain_authority_refs": ["owner_receipt", "progress_projection"],
    },
    {
        "module_id": "paper_progress_transition_refs",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": ["src/med_autoscience/controllers/paper_progress_transition_refs.py"],
        "domain_ref_consumers": ["paper policy adapter and domain-handler dispatch transition refs"],
        "current_ref_status": "transition_request_refs_no_queue_attempt_or_outbox_owner",
        "migration_action": "declare_paper_transition_refs_and_opl_runtime_readback_requirements",
        "retention_reason": "Paper work-unit identity, publication gate context, and artifact delta obligations are MAS domain facts.",
        "opl_expected_primitives": [
            "domain_progress_transition_runtime",
            "transactional_outbox",
            "stage_run_identity",
            "non_advancing_apply",
        ],
        "mas_domain_authority_refs": ["paper_work_unit_semantics", "publication_gate", "owner_receipt"],
    },
    {
        "module_id": "runtime_storage_maintenance",
        "owner": "one-person-lab",
        "classification": "domain_authority_refs",
        "migration_class": "opl_storage_substrate_mas_refs_projection",
        "code_paths": [
            "src/med_autoscience/controllers/restore_proof_compaction_helpers.py",
        ],
        "domain_ref_consumers": ["runtime grouped storage audit commands", "workspace storage reports"],
        "current_ref_status": "opl_owned_storage_substrate_mas_refs_only_projection",
        "migration_action": "declare_storage_audit_refs_and_consume_opl_lifecycle_cleanup_policy",
        "retention_reason": (
            "OPL owns runtime storage maintenance; MAS may expose study/workspace refs, typed blockers, "
            "and artifact authority receipt refs only."
        ),
        "opl_expected_primitives": ["opl_artifact_lifecycle_storage_audit_shell", "opl_restore_retention_receipt_shell", "opl_runtime_lifecycle_cleanup_policy"],
        "mas_domain_authority_refs": ["artifact_authority", "workspace_artifact_refs"],
        "authority_boundary": "opl_storage_substrate_mas_refs_only_projection_no_generic_cleanup_policy_owner",
        "provenance_boundary": {
            "surface_role": "mas_refs_only_source_projection_for_opl_storage_substrate",
            "history_role": "storage_maintenance_provenance",
            "body_policy": "workspace_refs_sizes_receipts_blockers_only",
            "may_emit": [
                "workspace_artifact_ref",
                "cleanup_receipt_ref",
                "restore_proof_ref",
                "typed_blocker",
                "storage_size_ref",
            ],
            "must_not_emit": [
                "generic_cleanup_policy",
                "restore_ready_verdict",
                "paper_closure_verdict",
                "publication_ready_verdict",
                "artifact_mutation_authorization",
            ],
            "generic_owner_claim_allowed": False,
        },
        "latest_thinning_evidence": {
            "status": "runtime_storage_physical_modules_retired",
            "scope": "restore_and_cold_store_helpers_moved_to_neutral_controller_module",
            "extracted_paths": [
                "src/med_autoscience/controllers/restore_proof_compaction_helpers.py",
            ],
            "retired_physical_modules": ["legacy_mas_storage_maintenance_python_namespace"],
            "domain_refs_entry_shell": None,
            "domain_refs_entry_role": "retired_storage_adapter_provenance_only",
            "live_report_boundary_payload": {
                "surface_kind": "mas_runtime_storage_refs_only_adapter_boundary",
                "report_modes": [
                    "workspace_storage_audit",
                    "study_runtime_storage_maintenance",
                    "orphan_quest_runtime_storage_maintenance",
                ],
                "body_policy": "workspace_refs_sizes_receipts_blockers_only",
                "must_not_emit": [
                    "generic_cleanup_policy",
                    "restore_ready_verdict",
                    "paper_closure_verdict",
                    "publication_ready_verdict",
                    "artifact_mutation_authorization",
                ],
                "can_write_domain_truth": False,
                "can_write_publication_eval": False,
                "can_write_controller_decision": False,
                "can_write_current_package": False,
            },
            "does_not_claim_physical_delete": True,
            "does_not_claim_opl_default_caller": True,
            "does_not_claim_generic_cleanup_policy_owner": True,
            "does_not_touch_publication_or_package_authority": True,
        },
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "opl_state_index_source_adapter.source_adapter_contract"],
    },
    {
        "module_id": "workspace_source_intake_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/workspace_contracts.py",
            "src/med_autoscience/controllers/workspace_literature.py",
            "src/med_autoscience/adapters/literature/pubmed.py",
            "src/med_autoscience/adapters/literature/pmc.py",
            "src/med_autoscience/controllers/literature_provider_runtime.py",
        ],
        "domain_ref_consumers": ["workspace init/readiness CLI", "MCP workspace readiness tools", "product-entry workspace surfaces"],
        "current_ref_status": "domain_source_adapter_active",
        "migration_action": "declare_source_intake_policy_in_pack_and_keep_mas_source_readiness_verdict",
        "retention_reason": "Source quality, medical evidence readiness, and literature relevance remain MAS domain authority.",
        "opl_expected_primitives": ["workspace_source_intake_shell", "source_locator_index"],
        "mas_domain_authority_refs": ["source_readiness_verdict", "evidence_ledger_refs"],
    },
    {
        "module_id": "publication_route_memory_locator_transport_shell",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/stage_knowledge_plane/",
            "src/med_autoscience/controllers/stage_knowledge_plane/publication_route_memory_inventory.py",
            "src/med_autoscience/controllers/stage_knowledge_plane/publication_route_memory_writeback.py",
        ],
        "domain_ref_consumers": ["publication-route memory CLI", "stage knowledge packet", "typed closeout memory writeback"],
        "current_ref_status": "body_free_locator_transport_active",
        "migration_action": "declare_publication_route_memory_refs_no_memory_body_transport",
        "retention_reason": "MAS keeps publication-route memory body, recall policy, and accept/reject/blocker writeback verdict.",
        "opl_expected_primitives": ["generic_memory_locator", "memory_writeback_transport", "body_free_memory_projection"],
        "mas_domain_authority_refs": ["publication_route_memory_body", "memory_writeback_decision"],
    },
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/delivery_artifact_authority.py",
            "src/med_autoscience/controllers/delivery_authority_backfill_apply.py",
            "src/med_autoscience/controllers/study_delivery_sync/",
        ],
        "domain_ref_consumers": ["study delivery sync", "controller-gated delivery manifest backfill"],
        "current_ref_status": "generic_lifecycle_retired_domain_delivery_authority_active",
        "migration_action": "retain_domain_delivery_authority_and_consume_opl_lifecycle_projection",
        "retention_reason": "Canonical manuscript/package mutation and rebuild proof are MAS artifact authority.",
        "opl_expected_primitives": ["opl_generic_artifact_lifecycle", "opl_artifact_locator", "opl_restore_retention_receipt_shell"],
        "mas_domain_authority_refs": ["artifact_authority", "current_package_authority"],
        "authority_boundary": "opl_owns_lifecycle_shell_mas_authorizes_artifact_mutation",
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "opl_state_index_source_adapter.source_adapter_contract"],
    },
    {
        "module_id": "workbench_portal_generic_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/domain_projection_profile.py",
            "src/med_autoscience/controllers/next_action_envelope.py",
            "src/med_autoscience/controllers/study_launch_projection.py",
            "src/med_autoscience/controllers/study_task_submission.py",
        ],
        "domain_ref_consumers": [
            "opl generated console and workbench",
            "domain entry study launch handoff",
            "domain entry task intake handoff",
        ],
        "current_ref_status": "opl_generated_workbench_surface_consumes_mas_domain_projection_refs",
        "migration_action": "declare_workbench_projection_inputs_for_opl_app_generated_shell",
        "retention_reason": (
            "MAS supplies per-study route map, quality/source refs, blockers, domain-handler owner-route handoff refs, "
            "while OPL owns the hosted workbench and generated projection shell."
        ),
        "current_surface_refs": [
            "product_status",
            "status_read_model",
            "workbench",
            "workbench_drilldown",
            "portal",
            "cockpit",
            "domain_projection_profile",
            "workspace_domain_projection",
            "study_launch_handoff",
            "study_task_intake_owner_route",
        ],
        "opl_expected_primitives": ["opl_generic_workbench", "opl_operator_attention_queue", "opl_route_decision_drilldown_shell"],
        "mas_domain_authority_refs": ["study_progress_projection", "safe_action_refs"],
        "authority_boundary": "opl_hosts_workbench_shell_mas_supplies_refs_only_domain_projection",
        "latest_thinning_evidence": {
            "status": "mas_local_workspace_cockpit_materializer_physical_delete_landed",
            "retired_paths": [
                path
                for module_id, path in RETIRED_PRIVATE_GENERIC_PATHS
                if module_id == "workbench_portal_generic_shell"
            ],
            "read_model_materializer_boundary": {
                "status": "retired_local_materializer_replaced_by_opl_hosted_workbench",
                "hosted_package_role": "opl_owned_read_model_projection_package",
                "hosted_package_truth_role": "projection_only_no_workspace_runtime_truth",
                "physical_module": None,
                "materializer_scope": "opl_owned_payload_html_and_hosted_package_projection",
                "active_callers": [],
                "writes_only": [],
                "does_not_claim": [
                    "workspace_workbench_owner",
                    "status_wrapper_owner",
                    "generic_runtime_owner",
                    "local_http_service_owner",
                    "runtime_control_owner",
                ],
                "domain_repo_physical_delete_authorized": False,
                "physical_retirement_decision_ref": PHYSICAL_RETIREMENT_DECISION_REF,
                "retention_reason": (
                    "The MAS-local materializer is retired; MAS retains only domain refs consumed by OPL-hosted projection surfaces; "
                    "it is not a workspace helper, service wrapper, or runtime control owner."
                ),
                "does_not_write": [
                    "study_truth",
                    "publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "current_package",
                    "runtime_state",
                ],
            },
            "retired_combined_portal_runtime_soak_provenance": {
                "status": "physically_retired_no_alias",
                "scope": "retired_read_model_evidence_shell_provenance",
                "retired_paths": [
                    "retired_combined_portal_runtime_soak_entry_removed_no_alias",
                    "retired_combined_portal_runtime_soak_split_package_removed_no_alias",
                ],
                "domain_ref_consumer_count": 0,
                "replacement_owner": "one-person-lab",
                "replacement_surface": "opl_current_control_state_or_app_workbench_soak",
                "does_not_claim_active_entry": True,
                "does_not_touch_publication_or_package_authority": True,
            },
            "domain_projection_sources": [
                "src/med_autoscience/domain_projection_profile.py",
                "src/med_autoscience/controllers/next_action_envelope.py",
                "src/med_autoscience/controllers/study_launch_projection.py",
                "src/med_autoscience/controllers/study_task_submission.py",
            ],
            "physical_delete_landed": True,
            "does_not_claim_opl_default_caller": True,
            "does_not_touch_publication_or_package_authority": True,
        },
        "proof_refs": [
            "contracts/domain_projection_profile.json",
            "domain_handler_export.functional_consumer_boundary.generated_surface_handoff",
        ],
    },
    {
        "module_id": "paper_mission_owner_surface_materialize_dispatch_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/paper_mission_owner_surface/",
            "src/med_autoscience/controllers/next_action_envelope.py",
            "src/med_autoscience/controllers/stage_outcome_authority/__init__.py",
            "src/med_autoscience/controllers/owner_callable_action_policy.py",
            "src/med_autoscience/reviewer_revision_feedbackops_dispatch.py",
            "src/med_autoscience/reviewer_revision_oma_materialization.py",
        ],
        "retired_code_paths": ["src/med_autoscience/controllers/domain_route_reconcile.py"],
        "domain_ref_consumers": ["owner-route one-shot tick", "runtime owner-route reconcile", "domain-handler dispatch"],
        "current_ref_status": "opl_runtime_manager_loop_consumed_mas_owner_route_guard_active",
        "migration_action": "declare_owner_route_policy_and_consume_opl_runtime_manager_loop",
        "retention_reason": "MAS must keep owner-route facts, publication gate blockers, safe action refs, and no-forbidden-write evidence.",
        "current_surface_refs": [
            "domain_handler",
            "domain_handler_export",
            "domain_handler_dispatch",
        ],
        "opl_expected_primitives": ["opl_generic_runner", "opl_attempt_retry_dead_letter", "opl_repair_projection", "opl_provider_runtime_manager"],
        "mas_domain_authority_refs": ["owner_route", "publication_gate", "safe_action_refs"],
        "authority_boundary": "opl_scans_and_dispatches_generic_loop_mas_guards_domain_route_and_receipt",
        "latest_thinning_evidence": {
            "status": "owner_callable_action_policy_single_source_landed",
            "policy_module": "src/med_autoscience/controllers/owner_callable_action_policy.py",
            "thin_entrypoints": [
                "src/med_autoscience/controllers/next_action_envelope.py",
                "src/med_autoscience/controllers/stage_outcome_authority/__init__.py",
            ],
            "single_source_fields": [
                "supported_action_types",
                "forbidden_surfaces",
                "retired_absent_surfaces",
                "allowed_write_surfaces",
                "source_action_ref_fields",
                "source_handoff_ref_fields",
                "request_owner_by_action_type",
                "request_output_surface_by_action_type",
                "request_packet_ref_by_action_type",
            ],
            "domain_repo_physical_delete_authorized": False,
            "physical_retirement_decision_ref": PHYSICAL_RETIREMENT_DECISION_REF,
            "does_not_write": [
                "study_truth",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "memory_body",
                "artifact_body",
            ],
            "does_not_claim": [
                "owner_chain_closed",
                "domain_ready",
                "production_ready",
                "publication_ready",
                "artifact_mutation_authorized",
            ],
        },
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "product_entry_manifest.functional_consumer_boundary.opl_functional_harness_consumer_coverage"],
    },
    {
        "module_id": "generic_cli_mcp_product_wrappers",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/domain_entry.py",
            "src/med_autoscience/domain_projection_profile.py",
            "src/med_autoscience/controllers/owner_route_handoff/domain_handler_export.py",
            "src/med_autoscience/controllers/owner_route_handoff/dispatch_orchestration.py",
            "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
        ],
        "domain_ref_consumers": ["MAS CLI", "MCP tool handlers", "skill direct domain entry", "product-entry manifest"],
        "current_ref_status": "domain_handlers_active_opl_generated_wrapper_metadata_consumed",
        "migration_action": "derive_wrapper_metadata_from_declarative_pack_and_opl_generated_surfaces",
        "retention_reason": "MAS keeps domain command handlers, direct domain entry, and owner receipts; OPL owns CLI/MCP/Skill/product/status descriptor projection and routing shell.",
        "current_surface_refs": [
            "cli",
            "mcp",
            "skill",
            "product_entry",
            "product_entry_manifest",
            "product_session",
        ],
        "opl_expected_primitives": [
            "opl_action_catalog_projection",
            "opl_product_entry_shell",
            "opl_mcp_descriptor_projection",
            "opl_skill_descriptor_projection",
            "opl_generated_command_surface",
        ],
        "mas_domain_authority_refs": ["domain_action_handler", "owner_receipt"],
        "authority_boundary": "opl_generates_wrapper_and_skill_metadata_mas_executes_domain_authority_handlers",
        "proof_refs": [
            "declarative_pack_compiler_input.family_action_catalog",
            "generated_surface_handoff.cli",
            "generated_surface_handoff.mcp",
            "generated_surface_handoff.skill",
            "generated_surface_handoff.product_entry",
        ],
    },
    {
        "module_id": "generic_daemon_or_scheduler_lifecycle",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "migration_class": "provenance_or_fixture",
        "code_paths": [
            "src/med_autoscience/controllers/opl_unique_control_plane_boundary/consumer_migration_inventory.py",
            "src/med_autoscience/controllers/mds_capability_parity/behavior_equivalence.py",
        ],
        "domain_ref_consumers": ["opl_current_control_state owner refs"],
        "current_ref_status": "opl_replacement_default_local_tombstone_only",
        "migration_action": "declare_scheduler_requirement_in_pack_and_keep_retired_provenance_refs",
        "retention_reason": "MAS supplies paper-progress domain SLO semantics and retired scheduler provenance refs only; OPL owns lifecycle, cadence, queue, attempt, and control.",
        "opl_expected_primitives": ["scheduler_lifecycle", "cadence_slo", "provider_slo"],
        "mas_domain_authority_refs": ["paper_progress_slo_semantics", "typed_blocker"],
    },
    {
        "module_id": "generic_queue_attempt_retry_dead_letter",
        "owner": "one-person-lab",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/study_runtime_execution/controller_authorization_receipts.py",
            "src/med_autoscience/controllers/paper_mission_owner_surface/opl_provider_attempts.py",
            "src/med_autoscience/controllers/opl_provider_ready_adapter/provider_readiness.py",
            "src/med_autoscience/controllers/study_runtime_decision/publication_and_submission.py",
            "src/med_autoscience/paper_mission_opl_readback/opl_task_readback.py",
            "src/med_autoscience/runtime_control/owner_route_attempt_protocol.py",
        ],
        "domain_ref_consumers": ["OPL provider stage runtime", "MAS owner receipt / typed blocker consumers"],
        "current_ref_status": "opl_owned_runtime_control_mas_consumes_closeout_refs",
        "migration_action": "declare_queue_attempt_requirements_and_return_mas_stage_closeout_receipts",
        "retention_reason": "OPL owns queue/attempt/retry/dead-letter; MAS keeps stage closeout semantics, owner receipts, and typed blockers.",
        "opl_expected_primitives": ["opl_generic_queue", "opl_attempt_ledger", "opl_retry_dead_letter", "opl_worker_lifecycle_transport"],
        "mas_domain_authority_refs": ["stage_closeout_domain_semantics", "owner_receipt"],
        "authority_boundary": "opl_owns_queue_attempt_retry_transport_mas_signs_stage_closeout_receipts",
        "proof_refs": ["opl_functional_harness_consumer_coverage.queue_stage_attempt_typed_closeout", "opl_functional_harness_consumer_coverage.restart_dead_letter_repair_human_gate_state_chain"],
    },
    {
        "module_id": "generic_transition_runner",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/study_domain_transition_table.py",
            "src/med_autoscience/controllers/study_state_matrix.py",
            "src/med_autoscience/controllers/study_domain_transition_guard.py",
        ],
        "domain_ref_consumers": ["study-state-matrix CLI", "runtime consumer guard", "OPL transition descriptor"],
        "current_ref_status": "domain_transition_spec_active_generic_runner_owned_by_opl",
        "migration_action": "declare_domain_transition_spec_for_opl_generic_runner",
        "retention_reason": "MAS owns medical transition semantics and oracle fixtures; OPL executes the generic state-machine transport.",
        "opl_expected_primitives": ["generic_transition_runner", "transition_matrix_runner", "idempotent_tick"],
        "mas_domain_authority_refs": ["domain_transition_table", "publication_quality_verdict", "artifact_authority"],
    },
    {
        "module_id": "study_truth",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/study_truth_kernel.py",
            "src/med_autoscience/controllers/progress_projection.py",
        ],
        "domain_ref_consumers": ["MAS controller owner route", "study progress/read models"],
        "current_ref_status": "domain_authority_active",
        "migration_action": "authority_stays_in_mas",
        "cannot_absorb_reason": "Medical study truth and paper route state are domain facts, not framework runtime state.",
        "mas_domain_authority_refs": ["study_truth", "progress_projection"],
    },
    {
        "module_id": "publication_quality_verdict",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/publication_gate/__init__.py",
            "src/med_autoscience/controllers/study_progress/publication_runtime.py",
            "src/med_autoscience/controllers/ai_reviewer_runtime_workflow.py",
            "src/med_autoscience/controllers/ai_reviewer_publication_eval/__init__.py",
            "src/med_autoscience/controllers/agent_lab_medical_manuscript_quality/__init__.py",
            "src/med_autoscience/study_task_intake_revision.py",
        ],
        "domain_ref_consumers": ["AI reviewer workflow", "publication gate", "controller decision"],
        "current_ref_status": "domain_authority_active",
        "migration_action": "authority_stays_in_mas",
        "cannot_absorb_reason": "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts.",
        "mas_domain_authority_refs": ["publication_quality_verdict", "ai_reviewer_workflow", "publication_gate"],
    },
    {
        "module_id": "artifact_authority",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/canonical_artifact_contract.py",
            "src/med_autoscience/controllers/study_delivery_sync.py",
            "src/med_autoscience/controllers/submission_minimal.py",
        ],
        "domain_ref_consumers": ["delivery sync", "package freshness proof", "submission package handoff"],
        "current_ref_status": "domain_authority_active",
        "migration_action": "authority_stays_in_mas",
        "cannot_absorb_reason": "Canonical manuscript/package mutation and submission authority are MAS artifact authority.",
        "mas_domain_authority_refs": ["artifact_authority", "current_package_authority"],
    },
)

def build_functional_module_inventory(
    *,
    physical_retirement_decision: object = PRIVATE_SURFACE_PHYSICAL_RETIREMENT_DECISION,
) -> tuple[dict[str, object], ...]:
    return tuple(
        _module_with_retirement_gate(
            dict(item),
            physical_retirement_decision=physical_retirement_decision,
        )
        for item in _FUNCTIONAL_MODULE_INVENTORY
    )


FUNCTIONAL_MODULE_INVENTORY = build_functional_module_inventory()


__all__ = [
    "FUNCTIONAL_MODULE_INVENTORY",
    "FUNCTIONAL_SURFACE_CLASSIFICATION",
    "DOMAIN_AUTHORITY_REFS_RETIREMENT_GATE_BY_MODULE",
    "PRIVATE_GENERIC_TOKEN_RESIDUE_SPECS",
    "RETIRED_PRIVATE_GENERIC_PATHS",
    "build_functional_module_inventory",
    "build_source_morphology",
]
