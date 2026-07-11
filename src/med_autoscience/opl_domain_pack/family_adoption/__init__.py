from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience import research_memory_contract
from med_autoscience import stage_quality_contract
from med_autoscience import stage_skill_surface_projection
from med_autoscience.ars_learning_projection import build_ars_learning_projection
from med_autoscience.autosci_learning_projection import build_autosci_learning_projection
from med_autoscience.evo_scientist_learning_projection import (
    build_evo_scientist_learning_projection,
)
from med_autoscience.external_learning_adoption_closure import (
    build_external_learning_adoption_closure,
)
from med_autoscience.stage_route_contract import (
    PROGRESS_FIRST_SPRINT_CONTRACT_FIELD,
    STAGE_ROUTE_CONTRACT_REF,
    late_stage_progress_sprint_contract_from_payload,
    load_stage_route_contract_payload,
    route_obligations_descriptor_from_payload,
)
from med_autoscience.stage_surface_contract import build_stage_surface_contract

from ..agent_pack_refs import (
    AGENT_PROMPT_REFS,
    AGENT_QUALITY_GATE_REFS,
    AGENT_SKILL_REFS,
    AGENT_STAGE_NATIVE_SEMANTIC_PACK_REF,
    AGENT_STAGE_POLICY_REFS,
)
from .. import hypothesis_portfolio_pack
from med_autoscience.opl_domain_pack import state_index_source_refs
from med_autoscience.workspace_paths import PUBLICATION_ROUTE_MEMORY_RELPATH

ADOPTION_SURFACE_KIND = "mas_opl_family_domain_authority_refs_adoption"
FAMILY_STAGE_CONTROL_PLANE_DESCRIPTOR_KIND = "family_stage_control_plane_descriptor"
DOMAIN_MEMORY_DESCRIPTOR_KIND = "family_domain_memory_ref"
SOURCE_CONTRACT_REF = "contracts/opl-framework/family-contract-adoption.json"
DOMAIN_AUTHORITY_REFS_CONTRACT_REF = (
    "med_autoscience.opl_domain_pack.state_index_source_refs.source_adapter_contract"
)
STAGE_LED_AUTONOMY_INVENTORY_REF = "docs/references/integration/stage_led_autonomy_family_inventory.md"
STAGE_LED_AUTONOMY_POLICY_REF = "docs/policies/study-workflow/stage_led_research_autonomy.md"
PUBLICATION_ROUTE_MEMORY_POLICY_REF = "docs/policies/study-workflow/publication_route_memory_policy.md"
PUBLICATION_ROUTE_MEMORY_LIBRARY_REF = "docs/policies/study-workflow/publication_route_memory_library.md"
PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF = (
    "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
)
STUDY_ARCHETYPES_REF = "docs/policies/study-workflow/study_archetypes.md"
STAGE_KNOWLEDGE_PLANE_CONTRACT_REF = (
    "med_autoscience.research_memory_contract.research_memory_contract"
)
STAGE_QUALITY_PACK_CONTRACT_REF = stage_quality_contract.CONTRACT_REF
STAGE_SKILL_SURFACE_PROJECTION_REF = stage_skill_surface_projection.CONTRACT_REF
STAGE_DELIVERABLE_INDEX_CONTRACT_REF = "med_autoscience.stage_surface_contract.build_stage_surface_contract"
PUBLICATION_ROUTE_MEMORY_LOCATOR = PUBLICATION_ROUTE_MEMORY_RELPATH.as_posix()
STAGE_ROUTE_OBLIGATIONS_DESCRIPTOR_REF = (
    "med_autoscience.stage_route_contract.route_obligations_descriptor"
)

FORBIDDEN_OPL_AUTHORITY_SURFACES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "AI reviewer workflow",
    "paper/manuscript/current_package",
    "current_package.zip",
)


def _stage_deliverable_index_projection(stage_surface: Mapping[str, Any]) -> dict[str, Any]:
    index = _mapping(stage_surface.get("stage_deliverable_index"))
    return {
        "surface_kind": index.get("surface_kind"),
        "version": index.get("version"),
        "role": index.get("role"),
        "stage_count": index.get("stage_count"),
        "locator_ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
        "stage_refs": list(index.get("stage_refs") or []),
        "human_review_page_refs": list(index.get("human_review_page_refs") or []),
        "source_refs": list(index.get("source_refs") or []),
        "human_review_policy": _mapping(index.get("human_review_policy")),
        "review_page_policy": _mapping(index.get("review_page_policy")),
        "authority_boundary": _mapping(index.get("authority_boundary")),
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "auto_advance_boundary": {
            "default_blocks_auto_advance": False,
            "blocking_only_when": "mas_human_gate_boundary_triggered",
            "opl_can_block_auto_advance": False,
            "opl_can_mark_publication_ready": False,
        },
    }


def build_family_stage_control_plane_descriptor() -> dict[str, Any]:
    route_contract_payload = load_stage_route_contract_payload()
    route_contracts = _mapping(route_contract_payload.get("route_contracts"))
    route_ids = list(route_contracts)
    late_stage_progress_sprint_contract = late_stage_progress_sprint_contract_from_payload(route_contract_payload)
    route_obligations_descriptor = route_obligations_descriptor_from_payload(route_contract_payload)
    knowledge_contract = research_memory_contract.research_memory_contract()
    packet_contracts = _mapping(knowledge_contract.get("packet_contracts"))
    packet_surfaces = list(packet_contracts)
    exploratory_stages = list(knowledge_contract.get("exploratory_stages") or [])
    stage_surface = build_stage_surface_contract()
    stage_deliverable_index = _stage_deliverable_index_projection(stage_surface)
    ars_learning_projection = build_ars_learning_projection()
    autosci_learning_projection = build_autosci_learning_projection()
    evo_scientist_learning_projection = build_evo_scientist_learning_projection()
    external_learning_adoption_closure = build_external_learning_adoption_closure()
    hypothesis_portfolio_evidence_pack = (
        hypothesis_portfolio_pack.build_hypothesis_portfolio_evidence_pack_descriptor()
    )
    return {
        "surface_kind": FAMILY_STAGE_CONTROL_PLANE_DESCRIPTOR_KIND,
        "schema_version": 1,
        "domain_id": "med-autoscience",
        "capability_id": "stage_led_autonomy",
        "descriptor_id": "mas_stage_led_autonomy_family_stage_control_plane",
        "authority_owner": "MedAutoScience",
        "source_refs": {
            "inventory": STAGE_LED_AUTONOMY_INVENTORY_REF,
            "policy": STAGE_LED_AUTONOMY_POLICY_REF,
            "route_contract_source": STAGE_ROUTE_CONTRACT_REF,
            "stage_native_semantic_pack_source": AGENT_STAGE_NATIVE_SEMANTIC_PACK_REF,
            "late_stage_progress_sprint_contract_source": (
                f"{STAGE_ROUTE_CONTRACT_REF}#/{PROGRESS_FIRST_SPRINT_CONTRACT_FIELD}"
            ),
            "stage_route_obligations_descriptor_source": STAGE_ROUTE_OBLIGATIONS_DESCRIPTOR_REF,
            "canonical_agent_pack_root": "agent/",
            "agent_prompt_sources": AGENT_PROMPT_REFS,
            "agent_stage_policy_sources": AGENT_STAGE_POLICY_REFS,
            "agent_skill_sources": list(AGENT_SKILL_REFS),
            "agent_quality_gate_sources": list(AGENT_QUALITY_GATE_REFS),
            "knowledge_plane_contract_source": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF,
            "quality_pack_contract_source": STAGE_QUALITY_PACK_CONTRACT_REF,
            "life_science_source_discovery_pack_source": STAGE_QUALITY_PACK_CONTRACT_REF,
            "autosci_learning_projection_source": (
                "med_autoscience.autosci_learning_projection.build_autosci_learning_projection"
            ),
            "evo_scientist_learning_projection_source": (
                "med_autoscience.evo_scientist_learning_projection.build_evo_scientist_learning_projection"
            ),
            "external_learning_adoption_closure_source": (
                "med_autoscience.external_learning_adoption_closure.build_external_learning_adoption_closure"
            ),
            "stage_skill_surface_projection_source": STAGE_SKILL_SURFACE_PROJECTION_REF,
            "stage_deliverable_index_contract_source": STAGE_DELIVERABLE_INDEX_CONTRACT_REF,
            "packet_contract_surfaces": packet_surfaces,
            "quality_pack_contract_surfaces": list(stage_quality_contract.QUALITY_PACK_CONTRACT_SURFACES),
            "stage_state_owner_surface": state_index_source_refs.REPLACEMENT_OWNER_SURFACE,
            "test_evidence": [
                "tests/test_stage_route_contract.py",
                "tests/test_stage_route_assets.py",
                "tests/test_research_memory.py",
                "tests/test_stage_knowledge_entry_injection.py",
                "tests/test_stage_knowledge_visibility.py",
                "tests/test_stage_quality_contract.py",
            ],
        },
        "route_contract_snapshot": {
            "source": STAGE_ROUTE_CONTRACT_REF,
            "route_ids": route_ids,
            "route_count": len(route_ids),
            "entry_mode_count": len(list(route_contract_payload.get("modes") or [])),
            "descriptor_derives_routes": False,
            "late_stage_progress_sprint_id": late_stage_progress_sprint_contract["sprint_id"],
            "late_stage_progress_sprint_work_units": list(
                late_stage_progress_sprint_contract["covered_work_units"]
            ),
        },
        "late_stage_progress_sprint_contract": late_stage_progress_sprint_contract,
        "route_obligations_descriptor": route_obligations_descriptor,
        "research_memory": {
            "contract_ref": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF,
            "contract_surface": knowledge_contract.get("surface"),
            "schema_version": knowledge_contract.get("schema_version"),
            "exploratory_stages": exploratory_stages,
            "packet_surfaces": packet_surfaces,
        },
        "stage_packets": {
            "stage_refs": research_memory_contract.OPL_STAGE_REFS_SURFACE,
            "memory_closeout": research_memory_contract.PUBLICATION_ROUTE_MEMORY_CLOSEOUT_SURFACE,
            "memory_acceptance_receipt": (
                research_memory_contract.PUBLICATION_ROUTE_MEMORY_ACCEPTANCE_RECEIPT_SURFACE
            ),
        },
        "hypothesis_portfolio_evidence_pack": hypothesis_portfolio_evidence_pack,
        "memory_control": {
            "closeout_categories": list(research_memory_contract.TYPED_CLOSEOUT_CATEGORIES),
            "state_index_owner_surface": state_index_source_refs.REPLACEMENT_OWNER_SURFACE,
            "acceptance_receipt_surface": (
                research_memory_contract.PUBLICATION_ROUTE_MEMORY_ACCEPTANCE_RECEIPT_SURFACE
            ),
            "publication_route_memory_pack_surface": research_memory_contract.PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
            "publication_route_memory_apply_receipt_surface": (
                research_memory_contract.PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE
            ),
            "can_promote_memory_to_evidence": False,
        },
        "stage_deliverable_index": stage_deliverable_index,
        "quality_pack_contract": stage_quality_contract.build_stage_quality_pack_projection(),
        "stage_skill_surface_projection": (
            stage_skill_surface_projection.build_stage_skill_surface_projection()
        ),
        "ars_learning_projection": ars_learning_projection,
        "autosci_learning_projection": autosci_learning_projection,
        "evo_scientist_learning_projection": evo_scientist_learning_projection,
        "external_learning_adoption_closure": external_learning_adoption_closure,
        "quality_and_publication_surfaces": {
            "evidence_ledger": "paper/evidence/evidence_ledger.json",
            "review_ledger": "paper/review/review_ledger.json",
            "controller_decisions": "artifacts/controller_decisions/latest.json",
            "publication_eval": "artifacts/publication_eval/latest.json",
            "publication_gate": "MAS publication gate",
            "ars_claim_support_audit": (
                "/product_entry_manifest/family_stage_control_plane_descriptor/ars_learning_projection"
            ),
            "autosci_research_lifecycle_contract": (
                "/product_entry_manifest/family_stage_control_plane_descriptor/autosci_learning_projection"
            ),
            "evo_scientist_progress_accelerator_contract": (
                "/product_entry_manifest/family_stage_control_plane_descriptor/evo_scientist_learning_projection"
            ),
            "external_learning_adoption_closure": (
                "/product_entry_manifest/family_stage_control_plane_descriptor/external_learning_adoption_closure"
            ),
        },
        "allowed_family_actions": [
            "index",
            "display",
            "freshness_check",
            "dispatch_mas_exported_task",
        ],
        "forbidden_family_actions": [
            "write_study_truth",
            "replace_route_contract",
            "authorize_publication_quality",
            "authorize_submission_readiness",
            "promote_memory_to_evidence",
            *hypothesis_portfolio_pack.HYPOTHESIS_PORTFOLIO_FORBIDDEN_FAMILY_ACTIONS,
            "infer_medical_route_from_projection",
        ],
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "hypothesis_truth_owner": "MedAutoScience",
            "route_contract_owner": "MedAutoScience",
            "research_memory_owner": "MedAutoScience",
            "evidence_ledger_owner": "MedAutoScience",
            "review_ledger_owner": "MedAutoScience",
            "controller_decision_owner": "MedAutoScience",
            "publication_eval_owner": "MedAutoScience",
            "publication_gate_owner": "MedAutoScience",
            "opl_role": "read_only_descriptor_consumer",
            "opl_authority": "index_display_freshness_only",
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            **hypothesis_portfolio_pack.HYPOTHESIS_PORTFOLIO_AUTHORITY_FLAGS,
        },
    }


def build_domain_memory_descriptor() -> dict[str, Any]:
    knowledge_contract = research_memory_contract.research_memory_contract()
    exploratory_stages = list(knowledge_contract.get("exploratory_stages") or [])
    stage_applicability = ["scout", "idea", "decision", "analysis-campaign", "review"]
    return {
        "surface_kind": DOMAIN_MEMORY_DESCRIPTOR_KIND,
        "version": "family-domain-memory-ref.v1",
        "memory_ref_id": "mas_publication_route_memory",
        "target_domain_id": "med-autoscience",
        "owner": "MedAutoScience",
        "memory_family": "publication_route_memory",
        "memory_pack_ref": {
            "ref_kind": "repo_policy_and_workspace_locator",
            "ref": PUBLICATION_ROUTE_MEMORY_POLICY_REF,
            "role": "publication_route_memory_policy_seed",
            "workspace_locator": PUBLICATION_ROUTE_MEMORY_LOCATOR,
        },
        "stage_applicability": stage_applicability,
        "retrieval_contract_ref": {
            "ref_kind": "surface_kind",
            "ref": research_memory_contract.OPL_STAGE_REFS_SURFACE,
            "role": "opl_stage_entry_refs",
        },
        "writeback_contract_ref": {
            "ref_kind": "surface_kind",
            "ref": research_memory_contract.PUBLICATION_ROUTE_MEMORY_CLOSEOUT_SURFACE,
            "role": "typed_publication_memory_closeout",
        },
        "receipt_contract_ref": {
            "ref_kind": "surface_kind",
            "ref": research_memory_contract.PUBLICATION_ROUTE_MEMORY_ACCEPTANCE_RECEIPT_SURFACE,
            "role": "domain_memory_acceptance_receipt",
        },
        "recall_projection_ref": {
            "ref_kind": "surface_kind",
            "ref": state_index_source_refs.REPLACEMENT_OWNER_SURFACE,
            "role": "opl_state_index_projection",
        },
        "migration_plan_ref": {
            "ref_kind": "human_doc",
            "ref": f"{PUBLICATION_ROUTE_MEMORY_POLICY_REF}#migration-plan",
            "role": "domain_owned_migration_plan",
        },
        "canonical_body_ref": {
            "ref_kind": "human_doc",
            "ref": PUBLICATION_ROUTE_MEMORY_LIBRARY_REF,
            "role": "markdown_first_memory_body",
            "opl_body_owner": False,
        },
        "seed_corpus_ref": {
            "ref_kind": "repo_path",
            "ref": PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF,
            "role": "repo_source_seed_index",
        },
        "writeback_receipt_locator_ref": {
            "ref_kind": "workspace_locator",
            "ref": f"{PUBLICATION_ROUTE_MEMORY_LOCATOR}/writeback_receipts",
            "role": "domain_owned_router_receipts",
        },
        "workspace_apply_surface": {
            "seed_apply_receipt_surface": research_memory_contract.PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE,
            "memory_pack_surface": research_memory_contract.PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
            "memory_pack_locator": f"{PUBLICATION_ROUTE_MEMORY_LOCATOR}/memory_pack.json",
            "migration_receipt_locator": f"{PUBLICATION_ROUTE_MEMORY_LOCATOR}/migration_receipts",
            "repo_tracks_real_pack_or_receipts": False,
        },
        "provenance_refs": [
            {"ref_kind": "human_doc", "ref": PUBLICATION_ROUTE_MEMORY_POLICY_REF, "role": "policy"},
            {"ref_kind": "human_doc", "ref": PUBLICATION_ROUTE_MEMORY_LIBRARY_REF, "role": "canonical_markdown_body"},
            {"ref_kind": "repo_path", "ref": PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF, "role": "seed_index"},
            {"ref_kind": "human_doc", "ref": STUDY_ARCHETYPES_REF, "role": "first_generation_memory_seed"},
            {"ref_kind": "python_symbol", "ref": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF, "role": "retrieval_writeback_contract"},
        ],
        "freshness": {
            "status": "policy_seed",
            "refresh_policy": "rebuild_product_entry_manifest_before_opl_discovery",
            "research_memory_contract_schema_version": knowledge_contract.get("schema_version"),
            "stage_knowledge_exploratory_stages": exploratory_stages,
            "stale_if_policy_or_stage_contract_missing": True,
        },
        "migration_readiness": {
            "status": "workspace_apply_closure_ready",
            "canonical_body_status": "markdown_source_available",
            "seed_index_status": "repo_source_index_available",
            "memory_body_migration": "domain_owned_workspace_apply_available",
            "writeback_receipt_locator_status": "workspace_locator_declared",
            "opl_apply_allowed": False,
        },
        "status": "active",
        "authority_boundary": {
            "opl_role": "locator_projection_owner",
            "domain_memory_owner": "MedAutoScience",
            "domain_router_owner": "MedAutoScience",
            "forbidden_opl_authority": [
                "memory_store_owner",
                "domain_truth_owner",
                "quality_verdict_owner",
                "artifact_authority",
                "publication_route_decision_owner",
                "publication_readiness_owner",
            ],
            "can_write_domain_truth": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_promote_memory_to_evidence": False,
            "can_write_artifacts": False,
        },
    }


def build_opl_family_adoption_surface(
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    source_adapter = state_index_source_refs.source_adapter_manifest()
    return {
        "surface_kind": ADOPTION_SURFACE_KIND,
        "schema_version": 1,
        "workspace_root": str(resolved_workspace_root),
        "refs": {
            "source_contract": SOURCE_CONTRACT_REF,
            "domain_authority_refs_contract": DOMAIN_AUTHORITY_REFS_CONTRACT_REF,
            "state_index_source_adapter": _state_index_source_ref(source_adapter),
            "authority_boundary": {
                "domain_truth_owner": "MedAutoScience",
                "opl_role": "OPL stage-runtime discovery and indexing only",
                "allowed_operation": "refs_payload_projection_only",
                "forbidden_opl_authority_surfaces": list(FORBIDDEN_OPL_AUTHORITY_SURFACES),
            },
        },
        "payload": _body_free_adoption_payload(source_adapter),
    }


def build_product_entry_adoption_projection(
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    source_adapter = state_index_source_refs.source_adapter_manifest()
    stage_control_plane_descriptor = build_family_stage_control_plane_descriptor()
    payload = _body_free_adoption_payload(source_adapter)
    payload["family_stage_control_plane_descriptor"] = stage_control_plane_descriptor
    return {
        "surface_kind": ADOPTION_SURFACE_KIND,
        "schema_version": 1,
        "workspace_root": str(resolved_workspace_root),
        "refs": {
            "source_contract": SOURCE_CONTRACT_REF,
            "domain_authority_refs_contract": DOMAIN_AUTHORITY_REFS_CONTRACT_REF,
            "state_index_source_adapter": _state_index_source_ref(source_adapter),
            "authority_boundary": {
                "domain_truth_owner": "MedAutoScience",
                "opl_role": "OPL stage-runtime discovery and indexing only",
                "allowed_operation": "refs_payload_projection_only",
                "forbidden_opl_authority_surfaces": list(FORBIDDEN_OPL_AUTHORITY_SURFACES),
            },
        },
        "payload": payload,
    }


def _state_index_source_ref(source_adapter: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": source_adapter["surface_kind"],
        "manifest_ref": source_adapter["manifest_ref"],
        "workspace_relative_path": source_adapter["manifest_ref"],
        "status": source_adapter["status"],
        "replacement_owner_surface": source_adapter["replacement_owner_surface"],
        "source_families": list(source_adapter["source_families"]),
        "local_persistence": "absent",
        "body_included": False,
    }


def _body_free_adoption_payload(
    source_adapter: Mapping[str, Any],
) -> dict[str, Any]:
    source_families = list(source_adapter["source_families"])
    return {
        "persistence": {
            "maps_to_opl_contract": "opl_family_persistence_contract.v1",
            "state_index_source_adapter_ref": "/refs/state_index_source_adapter",
            "source_families": source_families,
            "local_persistence": "absent",
            "body_included": False,
        },
        "lifecycle": {
            "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
            "source_families": ["dispatch_receipts", "archive_refs"],
        },
        "owner_route": {
            "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
            "source_family": "owner_route_receipts",
            "route_ticket_shape": [
                "idempotency_key",
                "route_epoch",
                "current_owner",
                "next_owner",
                "allowed_actions",
            ],
        },
        "authority_boundary": {
            "publication_eval_owner": "MedAutoScience",
            "ai_reviewer_owner": "MedAutoScience",
            "paper_package_owner": "MedAutoScience",
            "opl_authority": "discovery_and_indexing_only",
        },
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "ADOPTION_SURFACE_KIND",
    "DOMAIN_MEMORY_DESCRIPTOR_KIND",
    "FAMILY_STAGE_CONTROL_PLANE_DESCRIPTOR_KIND",
    "build_domain_memory_descriptor",
    "build_family_stage_control_plane_descriptor",
    "build_opl_family_adoption_surface",
    "build_product_entry_adoption_projection",
]
