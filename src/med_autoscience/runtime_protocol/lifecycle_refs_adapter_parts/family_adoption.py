from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience import stage_knowledge_contract
from med_autoscience import stage_quality_contract
from med_autoscience import stage_skill_surface_projection
from med_autoscience.ars_learning_projection import build_ars_learning_projection
from med_autoscience.stage_route_contract import STAGE_ROUTE_CONTRACT_REF, load_stage_route_contract_payload
from med_autoscience.stage_surface_contract import build_stage_surface_contract

from .agent_pack_refs import (
    AGENT_KNOWLEDGE_REFS,
    AGENT_PROMPT_REFS,
    AGENT_QUALITY_GATE_REFS,
    AGENT_SKILL_REFS,
    AGENT_STAGE_POLICY_REFS,
    stage_knowledge_refs,
    stage_policy_ref,
    stage_prompt_ref,
)
from .family_adoption_ref_payload import empty_payload, payload_from_lifecycle_refs
from ..runtime_lifecycle_contract import OPL_FAMILY_ADAPTER_SOURCE_TABLES

ADOPTION_SURFACE_KIND = "mas_opl_family_persistence_lifecycle_owner_route_adoption"
FAMILY_STAGE_CONTROL_PLANE_DESCRIPTOR_KIND = "family_stage_control_plane_descriptor"
FAMILY_STAGE_CONTROL_PLANE_KIND = "family_stage_control_plane"
DOMAIN_MEMORY_DESCRIPTOR_KIND = "family_domain_memory_ref"
SOURCE_CONTRACT_REF = "contracts/opl-framework/family-contract-adoption.json"
RUNTIME_LIFECYCLE_CONTRACT_REF = (
    "med_autoscience.runtime_protocol.runtime_lifecycle_contract.runtime_lifecycle_contract"
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
    "med_autoscience.stage_knowledge_contract.stage_knowledge_plane_contract"
)
STAGE_QUALITY_PACK_CONTRACT_REF = stage_quality_contract.CONTRACT_REF
STAGE_SKILL_SURFACE_PROJECTION_REF = stage_skill_surface_projection.CONTRACT_REF
STAGE_DELIVERABLE_INDEX_CONTRACT_REF = "med_autoscience.stage_surface_contract.build_stage_surface_contract"

FORBIDDEN_OPL_AUTHORITY_SURFACES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "AI reviewer workflow",
    "paper/manuscript/current_package",
    "current_package.zip",
)

FAMILY_STAGE_PACK: tuple[dict[str, Any], ...] = (
    {
        "stage_id": "direction_and_route_selection",
        "stage_kind": "planning",
        "title": "Direction and route selection",
        "domain_stage_refs": ["scout", "idea", "decision"],
        "allowed_action_refs": ["product_entry_status", "workspace_cockpit", "study_progress"],
        "requires": ["study_direction_request_received"],
        "ensures": ["direction_route_selected"],
        "next_stage_refs": ["baseline_and_evidence_setup"],
        "trust_lane": "ai_decision",
        "independent_gate_receipt_required": True,
        "runtime_event_refs": [
            "runtime_event:domain_route_owner_route.direction_route_selected",
            "runtime_event:controller_decisions.direction_route_selected",
        ],
    },
    {
        "stage_id": "baseline_and_evidence_setup",
        "stage_kind": "source_preparation",
        "title": "Baseline and evidence setup",
        "domain_stage_refs": ["baseline", "experiment"],
        "allowed_action_refs": ["submit_study_task", "launch_study", "study_progress"],
        "requires": ["direction_route_selected"],
        "ensures": ["baseline_evidence_ready"],
        "next_stage_refs": ["bounded_analysis_campaign"],
        "trust_lane": "domain_agent",
        "runtime_event_refs": [
            "runtime_event:controller_decisions.baseline_evidence_ready",
            "runtime_event:evidence_ledger.baseline_evidence_ready",
        ],
    },
    {
        "stage_id": "bounded_analysis_campaign",
        "stage_kind": "creation",
        "title": "Bounded analysis campaign",
        "domain_stage_refs": ["analysis-campaign"],
        "allowed_action_refs": ["launch_study", "study_progress", "sidecar_export", "sidecar_dispatch"],
        "requires": ["baseline_evidence_ready"],
        "ensures": ["bounded_analysis_evidence_ready"],
        "next_stage_refs": ["manuscript_authoring"],
        "trust_lane": "codex_executor",
        "runtime_event_refs": [
            "runtime_event:domain_health_diagnostic.bounded_analysis_evidence_ready",
            "runtime_event:evidence_ledger.bounded_analysis_evidence_ready",
        ],
    },
    {
        "stage_id": "manuscript_authoring",
        "stage_kind": "creation",
        "title": "Manuscript authoring",
        "domain_stage_refs": ["write"],
        "allowed_action_refs": ["launch_study", "study_progress", "sidecar_export", "sidecar_dispatch"],
        "requires": ["bounded_analysis_evidence_ready"],
        "ensures": ["manuscript_draft_reviewable"],
        "next_stage_refs": ["review_and_quality_gate"],
        "trust_lane": "codex_executor",
        "runtime_event_refs": [
            "runtime_event:controller_decisions.manuscript_draft_reviewable",
            "runtime_event:canonical_manuscript.manuscript_draft_reviewable",
        ],
    },
    {
        "stage_id": "review_and_quality_gate",
        "stage_kind": "review",
        "title": "Review and quality gate",
        "domain_stage_refs": ["review", "decision"],
        "allowed_action_refs": ["study_progress", "product_entry", "sidecar_export", "sidecar_dispatch"],
        "requires": ["manuscript_draft_reviewable"],
        "ensures": ["ai_reviewer_gate_receipt_recorded"],
        "next_stage_refs": ["finalize_and_publication_handoff"],
        "trust_lane": "ai_decision",
        "independent_gate_receipt_required": True,
        "runtime_event_refs": [
            "runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded",
            "runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded",
        ],
    },
    {
        "stage_id": "finalize_and_publication_handoff",
        "stage_kind": "packaging",
        "title": "Finalize and publication handoff",
        "domain_stage_refs": ["finalize", "journal-resolution", "decision"],
        "allowed_action_refs": ["study_progress", "product_entry", "sidecar_export"],
        "requires": ["ai_reviewer_gate_receipt_recorded"],
        "ensures": ["publication_handoff_ready_or_route_back_recorded"],
        "next_stage_refs": [],
        "trust_lane": "domain_agent",
        "runtime_event_refs": [
            "runtime_event:controller_decisions.publication_handoff_ready_or_route_back_recorded",
            "runtime_event:artifact_authority.publication_handoff_ready_or_route_back_recorded",
        ],
    },
)


def build_family_stage_control_plane_descriptor() -> dict[str, Any]:
    route_contract_payload = load_stage_route_contract_payload()
    route_contracts = _mapping(route_contract_payload.get("route_contracts"))
    route_ids = list(route_contracts)
    knowledge_contract = stage_knowledge_contract.stage_knowledge_plane_contract()
    packet_contracts = _mapping(knowledge_contract.get("packet_contracts"))
    packet_surfaces = list(packet_contracts)
    exploratory_stages = list(knowledge_contract.get("exploratory_stages") or [])
    stage_surface = build_stage_surface_contract()
    stage_deliverable_index = _stage_deliverable_index_projection(stage_surface)
    ars_learning_projection = build_ars_learning_projection()
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
            "canonical_agent_pack_root": "agent/",
            "agent_prompt_sources": AGENT_PROMPT_REFS,
            "agent_stage_policy_sources": AGENT_STAGE_POLICY_REFS,
            "agent_skill_sources": list(AGENT_SKILL_REFS),
            "agent_quality_gate_sources": list(AGENT_QUALITY_GATE_REFS),
            "agent_knowledge_sources": list(AGENT_KNOWLEDGE_REFS),
            "knowledge_plane_contract_source": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF,
            "quality_pack_contract_source": STAGE_QUALITY_PACK_CONTRACT_REF,
            "stage_skill_surface_projection_source": STAGE_SKILL_SURFACE_PROJECTION_REF,
            "stage_deliverable_index_contract_source": STAGE_DELIVERABLE_INDEX_CONTRACT_REF,
            "packet_contract_surfaces": packet_surfaces,
            "quality_pack_contract_surfaces": list(stage_quality_contract.QUALITY_PACK_CONTRACT_SURFACES),
            "stage_knowledge_root": str(stage_knowledge_contract.STAGE_KNOWLEDGE_ROOT),
            "test_evidence": [
                "tests/test_stage_route_contract.py",
                "tests/test_stage_route_assets.py",
                "tests/test_stage_knowledge_plane.py",
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
        },
        "stage_knowledge_plane": {
            "contract_ref": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF,
            "contract_surface": knowledge_contract.get("surface"),
            "schema_version": knowledge_contract.get("schema_version"),
            "exploratory_stages": exploratory_stages,
            "packet_surfaces": packet_surfaces,
        },
        "stage_packets": {
            "knowledge_packet": stage_knowledge_contract.KNOWLEDGE_PACKET_SURFACE,
            "memory_closeout_packet": stage_knowledge_contract.MEMORY_CLOSEOUT_SURFACE,
            "memory_write_router_receipt": stage_knowledge_contract.MEMORY_ROUTER_SURFACE,
            "stage_recall_index": stage_knowledge_contract.RECALL_INDEX_SURFACE,
        },
        "memory_control": {
            "closeout_categories": list(stage_knowledge_contract.TYPED_CLOSEOUT_CATEGORIES),
            "router_receipt_surface": stage_knowledge_contract.MEMORY_ROUTER_SURFACE,
            "recall_index_surface": stage_knowledge_contract.RECALL_INDEX_SURFACE,
            "publication_route_memory_pack_surface": stage_knowledge_contract.PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
            "publication_route_memory_apply_receipt_surface": (
                stage_knowledge_contract.PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE
            ),
            "can_promote_memory_to_evidence": False,
        },
        "stage_deliverable_index": stage_deliverable_index,
        "quality_pack_contract": stage_quality_contract.build_stage_quality_pack_projection(),
        "stage_skill_surface_projection": (
            stage_skill_surface_projection.build_stage_skill_surface_projection()
        ),
        "ars_learning_projection": ars_learning_projection,
        "quality_and_publication_surfaces": {
            "evidence_ledger": "paper/evidence/evidence_ledger.json",
            "review_ledger": "paper/review/review_ledger.json",
            "controller_decisions": "artifacts/controller_decisions/latest.json",
            "publication_eval": "artifacts/publication_eval/latest.json",
            "publication_gate": "MAS publication gate",
            "ars_claim_support_audit": (
                "/product_entry_manifest/family_stage_control_plane_descriptor/ars_learning_projection"
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
            "infer_medical_route_from_projection",
        ],
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "route_contract_owner": "MedAutoScience",
            "stage_knowledge_plane_owner": "MedAutoScience",
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
        },
    }


def build_domain_memory_descriptor() -> dict[str, Any]:
    knowledge_contract = stage_knowledge_contract.stage_knowledge_plane_contract()
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
            "workspace_locator": "portfolio/research_memory/publication_route_memory",
        },
        "stage_applicability": stage_applicability,
        "retrieval_contract_ref": {
            "ref_kind": "surface_kind",
            "ref": stage_knowledge_contract.KNOWLEDGE_PACKET_SURFACE,
            "role": "stage_entry_retrieval_packet",
        },
        "writeback_contract_ref": {
            "ref_kind": "surface_kind",
            "ref": stage_knowledge_contract.MEMORY_CLOSEOUT_SURFACE,
            "role": "typed_stage_closeout_proposal",
        },
        "receipt_contract_ref": {
            "ref_kind": "surface_kind",
            "ref": stage_knowledge_contract.MEMORY_ROUTER_SURFACE,
            "role": "domain_router_receipt",
        },
        "recall_projection_ref": {
            "ref_kind": "surface_kind",
            "ref": stage_knowledge_contract.RECALL_INDEX_SURFACE,
            "role": "stage_recall_projection",
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
            "ref": "portfolio/research_memory/publication_route_memory/writeback_receipts",
            "role": "domain_owned_router_receipts",
        },
        "workspace_apply_surface": {
            "seed_apply_receipt_surface": stage_knowledge_contract.PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE,
            "memory_pack_surface": stage_knowledge_contract.PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
            "memory_pack_locator": "portfolio/research_memory/publication_route_memory/memory_pack.json",
            "migration_receipt_locator": "portfolio/research_memory/publication_route_memory/migration_receipts",
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
            "stage_knowledge_contract_schema_version": knowledge_contract.get("schema_version"),
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


def build_family_stage_control_plane(*, family_action_catalog: Mapping[str, Any]) -> dict[str, Any]:
    descriptor = build_family_stage_control_plane_descriptor()
    action_ids = {
        str(action.get("action_id"))
        for action in family_action_catalog.get("actions", [])
        if isinstance(action, Mapping) and str(action.get("action_id") or "").strip()
    }
    stages = [_build_stage_descriptor(stage, descriptor=descriptor) for stage in FAMILY_STAGE_PACK]
    missing_refs = sorted(
        {
            action_ref
            for stage in stages
            for action_ref in stage["allowed_action_refs"]
            if action_ref not in action_ids
        }
    )
    if missing_refs:
        raise ValueError(f"MAS stage control plane allowed_action_refs missing from family_action_catalog: {missing_refs}")

    return {
        "surface_kind": FAMILY_STAGE_CONTROL_PLANE_KIND,
        "version": "family-stage-control-plane.v1",
        "plane_id": "med_autoscience_stage_control_plane",
        "target_domain_id": "med-autoscience",
        "owner": "MedAutoScience",
        "source_refs": _plane_source_refs(descriptor),
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "source_observed_at_ref": "/product_entry_manifest/family_stage_control_plane_descriptor/route_contract_snapshot",
            "refresh_policy": "rebuild_product_entry_manifest_before_opl_discovery",
            "stale_if_source_refs_missing": True,
        },
        "stage_action_parity": {
            "surface_kind": "family_stage_action_parity",
            "status": "aligned",
            "family_action_catalog_ref": "/product_entry_manifest/family_action_catalog",
            "missing_action_refs": [],
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "route_contract_owner": "MedAutoScience",
            "stage_knowledge_plane_owner": "MedAutoScience",
            "publication_gate_owner": "MedAutoScience",
            "opl_role": "projection_consumer_only",
            "write_policy": "no_study_truth_writes",
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
        "stages": stages,
        "notes": [
            "Descriptor-only projection over existing MAS Stage-Led Autonomy routes.",
            "OPL may index, inspect, display and dispatch MAS-exported guarded tasks only.",
            "MAS keeps route contracts, controller runtime, evidence/review ledgers, publication gate and execution kernel.",
        ],
    }


def _plane_source_refs(descriptor: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_action_catalog",
            "role": "action_catalog",
        },
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_stage_control_plane_descriptor",
            "role": "deep_descriptor",
        },
        {
            "ref_kind": "repo_path",
            "ref": str(_mapping(descriptor.get("source_refs")).get("route_contract_source") or STAGE_ROUTE_CONTRACT_REF),
            "role": "route_contract_source",
        },
        {
            "ref_kind": "python_symbol",
            "ref": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF,
            "role": "stage_knowledge_plane_contract",
        },
        {
            "ref_kind": "python_symbol",
            "ref": STAGE_QUALITY_PACK_CONTRACT_REF,
            "role": "quality_pack_contract",
        },
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
            "role": "stage_deliverable_index",
        },
        {
            "ref_kind": "repo_path",
            "ref": STAGE_LED_AUTONOMY_INVENTORY_REF,
            "role": "inventory_reference",
        },
        {
            "ref_kind": "repo_path",
            "ref": "agent/",
            "role": "canonical_semantic_pack_root",
        },
    ]


def _build_stage_descriptor(stage: Mapping[str, Any], *, descriptor: Mapping[str, Any]) -> dict[str, Any]:
    runtime_event_refs = _required_runtime_event_refs(stage)
    cohort_loop_refs = _stage_cohort_loop_refs(stage)
    stage_id = str(stage["stage_id"])
    domain_stage_refs = list(stage["domain_stage_refs"])
    allowed_action_refs = list(stage["allowed_action_refs"])
    knowledge_refs = stage_knowledge_refs(stage)
    quality_pack_refs = stage_quality_contract.quality_pack_ids_for_stages(domain_stage_refs)
    skill_refs = [
        *[
            {"ref_kind": "repo_path", "ref": ref, "role": "domain_pack_skill_policy"}
            for ref in AGENT_SKILL_REFS
        ],
        {"ref_kind": "skill_id", "ref": "med-autoscience", "role": "domain_skill"},
        {"ref_kind": "skill_id", "ref": "mas", "role": "codex_app_skill"},
    ]
    prompt_ref = {
        "ref_kind": "repo_path",
        "ref": stage_prompt_ref(stage),
        "role": "stage_prompt",
    }
    evaluation_refs = [
        {
            "ref_kind": "json_pointer",
            "ref": "/family_stage_control_plane_descriptor/authority_boundary",
            "role": "authority_boundary",
        },
        {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "progress_projection"},
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/owner_receipt_contract",
            "role": "owner_receipt_gate",
        },
        *[
            {"ref_kind": "repo_path", "ref": ref, "role": "agent_quality_gate"}
            for ref in AGENT_QUALITY_GATE_REFS
        ],
    ]
    independent_gate_receipt_required = bool(stage.get("independent_gate_receipt_required", False))
    source_refs = [
        *_plane_source_refs(descriptor),
        {
            "ref_kind": "route_stage_refs",
            "ref": domain_stage_refs,
            "role": "mas_route_projection",
        },
    ]
    stage_contract = {
        "requires": list(stage.get("requires", [])),
        "ensures": list(stage.get("ensures", [])),
        "boundary_assumptions": [
            "MAS owns study truth, route decisions, evidence/review ledgers, publication eval, and package authority.",
            "OPL admission only checks descriptor composition; it cannot authorize publication quality or submission readiness.",
        ],
    }
    trust_boundary = {
        "lane": stage.get("trust_lane", "domain_agent"),
        "static_check_eligible": False,
        "effect_boundary": stage.get("trust_lane") == "ai_decision",
        "records_runtime_events": True,
        "owner_receipt_required": True,
        "human_gate_required": False,
        "runtime_guard_required": True,
    }
    if runtime_event_refs:
        stage_contract["runtime_event_refs"] = runtime_event_refs
        trust_boundary["runtime_event_refs"] = runtime_event_refs
    stage_contract.update(cohort_loop_refs)
    return {
        "stage_id": stage["stage_id"],
        "stage_kind": stage["stage_kind"],
        "title": stage["title"],
        "summary": f"{stage['title']} projected from MAS-owned Stage-Led Autonomy routes for OPL discovery.",
        "goal": _stage_goal(stage, descriptor=descriptor),
        "owner": "MedAutoScience",
        "domain_stage_refs": domain_stage_refs,
        "inputs": [
            {"ref_kind": "json_pointer", "ref": "/family_action_catalog", "role": "allowed_action_catalog"},
            {
                "ref_kind": "json_pointer",
                "ref": "/family_stage_control_plane_descriptor/stage_knowledge_plane",
                "role": "stage_knowledge_plane",
            },
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "progress_read_model"},
        ],
        "knowledge_refs": knowledge_refs,
        "quality_pack_refs": quality_pack_refs,
        "quality_pack_projection": stage_quality_contract.build_stage_quality_pack_ref_projection(
            domain_stage_refs
        ),
        "stage_skill_surface_projection": stage_skill_surface_projection.build_stage_skill_surface_projection(
            stage_id=stage_id
        ),
        "skills": skill_refs,
        "prompt_refs": [prompt_ref],
        "policy_refs": [
            {"ref_kind": "repo_path", "ref": STAGE_ROUTE_CONTRACT_REF, "role": "route_contract"},
            {"ref_kind": "repo_path", "ref": STAGE_LED_AUTONOMY_POLICY_REF, "role": "stage_led_policy"},
            {
                "ref_kind": "repo_path",
                "ref": stage_policy_ref(stage),
                "role": "stage_domain_policy",
            },
        ],
        "allowed_action_refs": allowed_action_refs,
        "deliverable_index_ref": _stage_deliverable_index_ref(),
        "outputs": [
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "stage_status"},
            _stage_deliverable_index_ref(),
            {
                "ref_kind": "json_pointer",
                "ref": "/opl_family_persistence_lifecycle_owner_route_adoption",
                "role": "owner_route_projection",
            },
        ],
        "evaluation": evaluation_refs,
        "codex_cli_launch_packet": stage_skill_surface_projection.build_codex_cli_launch_packet(
            stage_id=stage_id,
            prompt_ref=prompt_ref,
            skill_refs=skill_refs,
            knowledge_refs=knowledge_refs,
            quality_gate_refs=evaluation_refs,
            quality_pack_refs=quality_pack_refs,
            allowed_action_refs=allowed_action_refs,
            expected_runtime_event_refs=runtime_event_refs,
            independent_gate_receipt_required=independent_gate_receipt_required,
        ),
        "handoff": {
            "next_owner": "MedAutoScience",
            "next_stage_refs": list(stage.get("next_stage_refs", [])),
            "provides": list(stage.get("ensures", [])),
            "resume_surface_ref": "/product_entry_shell/study_progress",
            "sidecar_export_ref": "/product_entry_shell/sidecar_export",
            "sidecar_dispatch_ref": "/product_entry_shell/sidecar_dispatch",
        },
        "stage_contract": stage_contract,
        "trust_boundary": trust_boundary,
        "source_refs": source_refs,
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "source_observed_at_ref": "/product_entry_manifest/family_stage_control_plane_descriptor/route_contract_snapshot",
            "refresh_policy": "rebuild_product_entry_manifest_before_opl_discovery",
            "stale_if_source_refs_missing": True,
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "route_contract_owner": "MedAutoScience",
            "stage_knowledge_plane_owner": "MedAutoScience",
            "publication_gate_owner": "MedAutoScience",
            "opl_role": "projection_consumer_only",
            "maps_existing_routes_only": True,
            "independent_gate_receipt_required": independent_gate_receipt_required,
            "can_write_domain_truth": False,
            "can_replace_route_contract": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
    }


def _stage_cohort_loop_refs(stage: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    stage_id = str(stage["stage_id"])
    return {
        "source_scope_refs": [
            {
                "ref_kind": "route_stage_refs",
                "ref": list(stage["domain_stage_refs"]),
                "role": "mas_route_stage_source_scope",
            },
            {
                "ref_kind": "json_pointer",
                "ref": f"/product_entry_manifest/family_stage_control_plane/stages/{stage_id}/source_refs",
                "role": "stage_source_ref_projection",
            },
        ],
        "cohort_query_refs": [
            {
                "ref_kind": "json_pointer",
                "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/route_contract_snapshot",
                "role": "auditable_stage_cohort_query",
            },
        ],
        "trigger_refs": [
            {
                "ref_kind": "queue_ref",
                "ref": f"opl://family-stage-queue/med-autoscience/{stage_id}",
                "role": "opl_provider_stage_launch_trigger",
            },
            {
                "ref_kind": "action_ref",
                "ref": list(stage["allowed_action_refs"]),
                "role": "mas_guarded_action_trigger_candidates",
            },
        ],
        "monitor_refs": [
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "stage_progress_monitor"},
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "runtime_status_monitor"},
        ],
        "dashboard_metric_refs": [
            {
                "ref_kind": "json_pointer",
                "ref": f"/product_entry_manifest/family_stage_control_plane/stages/{stage_id}/freshness",
                "role": "operator_stage_freshness_metric",
            },
        ],
    }


def _required_runtime_event_refs(stage: Mapping[str, Any]) -> list[str]:
    stage_id = str(stage.get("stage_id") or "")
    refs = [str(ref) for ref in stage.get("runtime_event_refs") or [] if str(ref).strip()]
    if not refs:
        raise ValueError(f"runtime guard stage missing runtime_event_refs: {stage_id}")
    return refs


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


def _stage_deliverable_index_ref() -> dict[str, Any]:
    return {
        "ref_kind": "json_pointer",
        "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
        "role": "stage_deliverable_index",
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "human_review_blocks_auto_advance_by_default": False,
        "blocking_only_when": "mas_human_gate_boundary_triggered",
    }


def _stage_goal(stage: Mapping[str, Any], *, descriptor: Mapping[str, Any]) -> str:
    route_contracts = _mapping(load_stage_route_contract_payload().get("route_contracts"))
    route_goals = [
        str(_mapping(route_contracts.get(route_id)).get("goal") or "").strip()
        for route_id in stage["domain_stage_refs"]
    ]
    route_goals = [goal for goal in route_goals if goal]
    if route_goals:
        return " / ".join(route_goals[:2])
    route_count = _mapping(descriptor.get("route_contract_snapshot")).get("route_count")
    return f"Expose MAS route snapshot for {stage['title']} without changing the {route_count} MAS routes."


def build_opl_family_adoption_surface(
    *,
    connect: Any,
    ensure_schema: Any,
    inspect_lifecycle_store: Any,
    workspace_lifecycle_store_path: Any,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = Path(db_path or workspace_lifecycle_store_path(resolved_workspace_root)).expanduser().resolve()
    inspection = inspect_lifecycle_store(resolved_db_path)
    payload = empty_payload(inspection=inspection)
    if resolved_db_path.exists():
        with connect(resolved_db_path) as conn:
            ensure_schema(conn)
            payload = payload_from_lifecycle_refs(conn, inspection=inspection)
    return {
        "surface_kind": ADOPTION_SURFACE_KIND,
        "schema_version": 1,
        "workspace_root": str(resolved_workspace_root),
        "refs": {
            "source_contract": SOURCE_CONTRACT_REF,
            "runtime_lifecycle_contract": RUNTIME_LIFECYCLE_CONTRACT_REF,
            "sqlite_refs_index": {
                "surface_kind": "lifecycle_refs_sqlite_index",
                "workspace_relative_path": "artifacts/runtime/runtime_lifecycle.sqlite",
                "db_path": str(resolved_db_path),
                "status": inspection.get("status") or "missing",
            },
            "authority_boundary": {
                "domain_truth_owner": "MedAutoScience",
                "opl_role": "OPL stage-runtime discovery and indexing only",
                "allowed_operation": "refs_payload_projection_only",
                "forbidden_opl_authority_surfaces": list(FORBIDDEN_OPL_AUTHORITY_SURFACES),
            },
        },
        "payload": payload,
    }


def build_product_entry_adoption_projection(
    *,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = Path(db_path or (resolved_workspace_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite")).resolve()
    stage_control_plane_descriptor = build_family_stage_control_plane_descriptor()
    return {
        "surface_kind": ADOPTION_SURFACE_KIND,
        "schema_version": 1,
        "workspace_root": str(resolved_workspace_root),
        "refs": {
            "source_contract": SOURCE_CONTRACT_REF,
            "runtime_lifecycle_contract": RUNTIME_LIFECYCLE_CONTRACT_REF,
            "sqlite_refs_index": {
                "surface_kind": "lifecycle_refs_sqlite_index",
                "workspace_relative_path": "artifacts/runtime/runtime_lifecycle.sqlite",
                "db_path": str(resolved_db_path),
            },
            "authority_boundary": {
                "domain_truth_owner": "MedAutoScience",
                "opl_role": "OPL stage-runtime discovery and indexing only",
                "allowed_operation": "refs_payload_projection_only",
                "forbidden_opl_authority_surfaces": list(FORBIDDEN_OPL_AUTHORITY_SURFACES),
            },
        },
        "payload": {
            "persistence": {
                "maps_to_opl_contract": "opl_family_persistence_contract.v1",
                "sqlite_refs_index_ref": "/refs/sqlite_refs_index",
                "source_tables": list(OPL_FAMILY_ADAPTER_SOURCE_TABLES),
            },
            "lifecycle": {
                "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
                "source_tables": [
                    "runtime_snapshots",
                    "snapshot_file_refs",
                    "dispatch_receipts",
                    "turn_receipts",
                    "archive_refs",
                    "report_index",
                ],
            },
            "owner_route": {
                "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
                "source_table": "owner_route_receipts",
                "route_ticket_shape": ["idempotency_key", "route_epoch", "current_owner", "next_owner", "allowed_actions"],
            },
            "authority_boundary": {
                "publication_eval_owner": "MedAutoScience",
                "ai_reviewer_owner": "MedAutoScience",
                "paper_package_owner": "MedAutoScience",
                "opl_authority": "discovery_and_indexing_only",
            },
            "family_stage_control_plane_descriptor": stage_control_plane_descriptor,
        },
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "ADOPTION_SURFACE_KIND",
    "DOMAIN_MEMORY_DESCRIPTOR_KIND",
    "FAMILY_STAGE_CONTROL_PLANE_KIND",
    "FAMILY_STAGE_CONTROL_PLANE_DESCRIPTOR_KIND",
    "build_domain_memory_descriptor",
    "build_family_stage_control_plane",
    "build_family_stage_control_plane_descriptor",
    "build_opl_family_adoption_surface",
    "build_product_entry_adoption_projection",
]
