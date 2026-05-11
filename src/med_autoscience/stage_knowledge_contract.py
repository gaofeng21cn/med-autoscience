from __future__ import annotations

from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
CONTRACT_SURFACE = "stage_knowledge_plane_contract"
KNOWLEDGE_PACKET_SURFACE = "stage_knowledge_packet"
MEMORY_CLOSEOUT_SURFACE = "stage_memory_closeout_packet"
MEMORY_ROUTER_SURFACE = "memory_write_router_receipt"
RECALL_INDEX_SURFACE = "stage_recall_index"
PUBLICATION_ROUTE_MEMORY_PACK_SURFACE = "publication_route_memory_pack"
PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE = "publication_route_memory_apply_receipt"
PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE = "paper_soak_memory_apply_proof"

EXPLORATORY_STAGES = ("scout", "idea", "analysis-campaign", "review")
PUBLICATION_ROUTE_MEMORY_STAGES = ("scout", "idea", "decision", "analysis-campaign", "review")
STAGE_KNOWLEDGE_ROOT = Path("artifacts/stage_knowledge")

TYPED_CLOSEOUT_CATEGORIES = (
    "reusable_lessons",
    "citation_gaps",
    "failed_paths",
    "reference_role_updates",
    "evidence_ledger_updates",
    "review_ledger_updates",
    "controller_decision_requests",
    "human_gate_requests",
    "claim_boundary_decisions",
)

COMMON_PACKET_FIELDS = (
    "schema_version",
    "study_id",
    "stage",
    "input_refs",
    "source_fingerprint",
    "authority_boundary",
    "idempotency_key",
)

STAGE_OBLIGATIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "scout": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "portfolio_memory.topic_landscape",
            "portfolio_memory.dataset_question_map",
            "portfolio_memory.venue_intelligence",
            "workspace_literature.coverage",
            "literature_provider_runtime.readiness",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "clinical_question_framing",
            "literature_gap",
            "anchor_paper_role",
            "route_recommendation",
        ),
    },
    "idea": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "portfolio_memory.study_recall_index",
            "study_reference_context",
            "prior_candidate_or_failed_lines",
            "journal_neighbor_refs",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "selected_line",
            "rejected_alternatives",
            "selection_rationale",
            "stop_rule",
            "memory_reuse_note",
        ),
    },
    "analysis-campaign": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "failed_path_history",
            "evidence_ledger",
            "citation_gaps",
            "bounded_frontier",
            "reviewer_concerns",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "slice_ledger",
            "negative_or_weak_result_interpretation",
            "route_impact",
            "failed_path_lesson",
        ),
    },
    "review": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "manuscript",
            "claim_evidence_map",
            "display_to_claim_map",
            "study_reference_context",
            "citation_ledger_refs",
            "ai_reviewer_calibration_memory",
            "prior_reviewer_findings",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "reviewer_action_matrix",
            "evidence_or_citation_repair_request",
            "reusable_critique_lesson",
        ),
    },
    "decision": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "publication_route_memory_refs",
            "controller_decision_inputs",
            "failed_path_history",
            "stop_loss_context",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "stop_or_pivot_lesson",
            "route_impact",
            "rejected_alternatives",
        ),
    },
}


def stage_knowledge_plane_contract() -> dict[str, Any]:
    return {
        "surface": CONTRACT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "packet_contracts": {
            KNOWLEDGE_PACKET_SURFACE: _packet_contract(KNOWLEDGE_PACKET_SURFACE),
            MEMORY_CLOSEOUT_SURFACE: _packet_contract(MEMORY_CLOSEOUT_SURFACE),
            MEMORY_ROUTER_SURFACE: _packet_contract(MEMORY_ROUTER_SURFACE),
            RECALL_INDEX_SURFACE: _packet_contract(RECALL_INDEX_SURFACE),
            PUBLICATION_ROUTE_MEMORY_PACK_SURFACE: _packet_contract(PUBLICATION_ROUTE_MEMORY_PACK_SURFACE),
            PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE: _packet_contract(
                PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE
            ),
            PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE: _packet_contract(PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE),
        },
        "exploratory_stages": list(EXPLORATORY_STAGES),
        "publication_route_memory_stages": list(PUBLICATION_ROUTE_MEMORY_STAGES),
        "stage_obligations": {
            stage: {key: list(values) for key, values in obligations.items()}
            for stage, obligations in STAGE_OBLIGATIONS.items()
        },
        "authority_boundary": authority_boundary(),
    }


def packet_contract(surface: str) -> dict[str, Any]:
    return _packet_contract(surface)


def authority_boundary() -> dict[str, Any]:
    return {
        "role": "stage_context_or_router_contract",
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_replace_controller_decision": False,
        "can_replace_evidence_ledger": False,
        "can_promote_quest_local_literature_to_workspace_authority": False,
        "can_use_chat_as_authority": False,
    }


def _packet_contract(surface: str) -> dict[str, Any]:
    return {
        "surface": surface,
        "required_fields": list(COMMON_PACKET_FIELDS),
        "authority_boundary": authority_boundary(),
    }


__all__ = [
    "COMMON_PACKET_FIELDS",
    "CONTRACT_SURFACE",
    "EXPLORATORY_STAGES",
    "KNOWLEDGE_PACKET_SURFACE",
    "MEMORY_CLOSEOUT_SURFACE",
    "MEMORY_ROUTER_SURFACE",
    "PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE",
    "PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE",
    "PUBLICATION_ROUTE_MEMORY_PACK_SURFACE",
    "PUBLICATION_ROUTE_MEMORY_STAGES",
    "RECALL_INDEX_SURFACE",
    "SCHEMA_VERSION",
    "STAGE_KNOWLEDGE_ROOT",
    "STAGE_OBLIGATIONS",
    "TYPED_CLOSEOUT_CATEGORIES",
    "authority_boundary",
    "packet_contract",
    "stage_knowledge_plane_contract",
]
