from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DOMAIN_OWNER = "MedAutoScience"
HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF = (
    "agent/knowledge/hypothesis_portfolio_evidence_pack.md"
)
HYPOTHESIS_PORTFOLIO_VALIDATOR_REF = (
    "src/med_autoscience/opl_domain_pack/hypothesis_portfolio_pack.py::"
    "validate_hypothesis_portfolio_candidate_refs"
)
HYPOTHESIS_PORTFOLIO_REQUIRED_REFS = [
    "hypothesis_candidate_ref",
    "assumption_ref",
    "sub_assumption_ref",
    "supporting_evidence_ref",
    "contradicting_evidence_ref",
    "novelty_ref",
    "source_provenance_ref",
    "testability_ref",
    "safety_risk_ref",
    "negative_failed_path_ref",
    "independent_reviewer_or_auditor_receipt_ref",
    "human_gate_receipt_ref",
    "owner_receipt_or_typed_blocker_ref",
]
HYPOTHESIS_PORTFOLIO_ADVISORY_REFS = [
    "ranking_ref",
    "proximity_ref",
    "debate_ref",
    "tournament_ref",
    "evolution_ref",
]
HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS = [
    "next_delta_tournament_ref",
    "micro_candidate_board_ref",
    "critique_repair_hint_ref",
    "memory_lesson_ref",
    "strategy_retrospective_ref",
    "opportunistic_prefetch_ref",
]
HYPOTHESIS_PORTFOLIO_FORBIDDEN_FAMILY_ACTIONS = [
    "promote_hypothesis_to_route_authority",
    "treat_ranking_or_proximity_as_authority",
    "close_hypothesis_independent_review_gate",
]
HYPOTHESIS_PORTFOLIO_AUTHORITY_FLAGS = {
    "can_authorize_route_by_ranking": False,
    "can_close_hypothesis_independent_review_gate": False,
}
PROMOTION_AUTHORITY_BOUNDARY = {
    "ranking_or_proximity_can_authorize_promotion": False,
    "mas_owner_receipt_or_typed_blocker_required": True,
    "independent_reviewer_or_auditor_receipt_required": True,
    "human_gate_receipt_required": True,
}
PROGRESS_ENHANCEMENT_AUTHORITY_BOUNDARY = {
    "missing_progress_enhancement_ref_blocks_route": False,
    "next_delta_tournament_authorizes_next_attempt_only": True,
    "micro_candidates_can_block_selected_owner_action": False,
    "critique_hint_can_close_quality_gate": False,
    "memory_lesson_body_required": False,
    "strategy_retrospective_runs_every_attempt": False,
    "opportunistic_prefetch_blocks_mainline": False,
}


def _present_ref(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_present_ref(item) for item in value)
    return True


def validate_hypothesis_portfolio_candidate_refs(
    candidate: Mapping[str, Any],
    *,
    route_back_owner: str = "decision",
) -> dict[str, object]:
    missing_ref_families = [
        ref_family
        for ref_family in HYPOTHESIS_PORTFOLIO_REQUIRED_REFS
        if not _present_ref(candidate.get(ref_family))
    ]
    present_advisory_ref_families = [
        ref_family
        for ref_family in HYPOTHESIS_PORTFOLIO_ADVISORY_REFS
        if _present_ref(candidate.get(ref_family))
    ]
    present_progress_enhancement_ref_families = [
        ref_family
        for ref_family in HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS
        if _present_ref(candidate.get(ref_family))
    ]
    forbidden_authority_claims = _forbidden_progress_enhancement_authority_claims(candidate)
    if missing_ref_families or forbidden_authority_claims:
        status = "completed_with_quality_debt"
    else:
        status = "validated"
    result: dict[str, object] = {
        "surface_kind": "mas_hypothesis_portfolio_candidate_validation",
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_id": candidate.get("candidate_id"),
        "status": status,
        "can_promote_candidate": not missing_ref_families and not forbidden_authority_claims,
        "required_ref_families": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_ref_families": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
        "progress_enhancement_ref_families": list(HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS),
        "present_advisory_ref_families": present_advisory_ref_families,
        "present_progress_enhancement_ref_families": present_progress_enhancement_ref_families,
        "missing_ref_families": missing_ref_families,
        "missing_progress_enhancement_ref_families": [
            ref_family
            for ref_family in HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS
            if ref_family not in present_progress_enhancement_ref_families
        ],
        "progress_enhancement_refs_block_route": False,
        "advisory_refs_are_authority": False,
        "promotion_authority_boundary": dict(PROMOTION_AUTHORITY_BOUNDARY),
        "progress_enhancement_authority_boundary": dict(PROGRESS_ENHANCEMENT_AUTHORITY_BOUNDARY),
        "forbidden_authority_claims": forbidden_authority_claims,
    }
    if missing_ref_families or forbidden_authority_claims:
        result["quality_debt"] = {
            "status": "open",
            "debt_code": (
                "progress_enhancement_authority_leak"
                if forbidden_authority_claims
                else "missing_hypothesis_portfolio_ref_family"
            ),
            "missing_ref_families": missing_ref_families,
            "forbidden_authority_claims": forbidden_authority_claims,
            "blocks_stage_transition": False,
            "blocks_candidate_promotion_or_ready_claims": True,
            "route_back_owner": route_back_owner,
            "negative_or_empty_candidate_is_consumable_diagnostic_progress": True,
        }
        result["route_back_recommendation"] = {
            "selection_owner": "codex_cli",
            "suggested_stage": route_back_owner,
            "may_target_any_declared_stage": True,
            "must_carry_negative_failed_path_refs": True,
            "blocks_stage_transition": False,
        }
    return result


def _forbidden_progress_enhancement_authority_claims(candidate: Mapping[str, Any]) -> list[str]:
    authority_flags = _mapping(candidate.get("progress_enhancement_authority"))
    forbidden: list[str] = []
    for key in (
        "blocks_route_when_missing",
        "closes_quality_gate",
        "authorizes_publication_readiness",
        "authorizes_artifact_mutation",
        "counts_prefetch_as_paper_progress",
        "runs_strategy_retrospective_every_attempt",
    ):
        if authority_flags.get(key) is True:
            forbidden.append(key)
    if candidate.get("advisory_refs_are_authority") is True:
        forbidden.append("advisory_refs_are_authority")
    return forbidden


def build_hypothesis_portfolio_evidence_pack_descriptor() -> dict[str, object]:
    return {
        "surface_kind": "mas_hypothesis_portfolio_evidence_pack_descriptor",
        "schema_version": 1,
        "owner": DOMAIN_OWNER,
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "portfolio_role": "mas_owned_refs_first_hypothesis_candidate_portfolio",
        "candidate_required_refs": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_only_refs": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
        "progress_enhancement_refs": list(HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS),
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_promotion_requires_validator": True,
        "advisory_refs_are_authority": False,
        "progress_enhancement_refs_block_route": False,
        "progress_policy": (
            "missing_refs_empty_candidate_or_forbidden_claims_record_quality_debt_and_ai_route_back"
        ),
        "authority_boundary": {
            "hypothesis_truth_owner": DOMAIN_OWNER,
            "evidence_interpretation_owner": DOMAIN_OWNER,
            "quality_publication_artifact_authority_owner": DOMAIN_OWNER,
            "ranking_and_proximity_authority": "advisory_only",
            "progress_enhancement_authority": "advisory_progress_accelerator_only",
            "opl_role": "refs_projection_transport_and_display_only",
            "opl_can_write_hypothesis_truth": False,
            "opl_can_promote_evidence": False,
            "opl_can_authorize_route_by_ranking": False,
            "opl_can_close_independent_review_gate": False,
            "opl_can_authorize_publication_quality": False,
            "opl_can_authorize_artifact_mutation": False,
        },
    }


def build_hypothesis_portfolio_evidence_pack_contract() -> dict[str, object]:
    descriptor = build_hypothesis_portfolio_evidence_pack_descriptor()
    authority = dict(descriptor["authority_boundary"])  # type: ignore[index]
    authority.update(
        {
            "novelty_source_provenance_owner": DOMAIN_OWNER,
            "testability_safety_owner": DOMAIN_OWNER,
            "negative_failed_path_owner": DOMAIN_OWNER,
            "opl_can_accept_novelty": False,
            "opl_can_declare_testability_or_safety": False,
        }
    )
    return {
        "surface_kind": "mas_hypothesis_portfolio_evidence_pack_contract",
        "schema_version": 1,
        "owner": DOMAIN_OWNER,
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "portfolio_role": "mas_owned_hypothesis_candidate_and_evidence_ref_pack",
        "candidate_required_ref_families": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_ref_families": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
        "progress_enhancement_ref_families": list(HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS),
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_promotion_requires_validator": True,
        "advisory_refs_are_authority": False,
        "progress_enhancement_refs_block_route": False,
        "candidate_validation_output_contract": {
            "success_status": "validated",
            "consumable_candidate_missing_refs_status": "completed_with_quality_debt",
            "degraded_status": "completed_with_quality_debt",
            "can_promote_candidate_requires": "all_required_ref_families_present",
            "quality_debt_blocks_stage_transition": False,
            "quality_debt_blocks_candidate_promotion_or_ready_claims": True,
            "route_back_selection_owner": "codex_cli",
            "route_back_may_target_any_declared_stage": True,
        },
        "progress_enhancement_contract": {
            "role": "advisory_progress_accelerator",
            "missing_progress_enhancement_ref_blocks_route": False,
            "max_reusable_memory_lesson_refs_per_attempt": 1,
            "strategy_retrospective_triggered_only_by": [
                "stop_loss_candidate",
                "repeated_failure",
                "human_gate_pressure",
                "claim_boundary_drift",
                "no_loop_budget_exhausted",
            ],
            "opportunistic_prefetch_blocks_mainline": False,
        },
        "advisory_only_fields": [
            "ranking",
            "proximity",
            "elo_like_score",
            "debate_winner",
            "candidate_evolution_order",
        ],
        "missing_ref_policy": {
            "consumable_candidate": "completed_with_quality_debt_and_continue",
            "zero_consumable_candidate": "completed_with_quality_debt_and_ai_selected_route_back",
            "quality_debt_blocks_stage_transition": False,
            "quality_debt_blocks_candidate_promotion_or_ready_claims": True,
        },
        "authority_boundary": authority,
    }


def stage_hypothesis_portfolio_evidence_pack_contract() -> dict[str, object]:
    descriptor = build_hypothesis_portfolio_evidence_pack_descriptor()
    return {
        "descriptor_ref": (
            "/product_entry_manifest/family_stage_control_plane_descriptor/"
            "hypothesis_portfolio_evidence_pack"
        ),
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "consumption_boundary": "refs_only_no_body_no_authority_transfer",
        "ranking_and_proximity_authority": "advisory_only",
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_promotion_requires_validator": True,
        "advisory_refs_are_authority": False,
        "required_ref_families": list(descriptor["candidate_required_refs"]),
        "advisory_ref_families": list(descriptor["advisory_only_refs"]),
        "progress_enhancement_ref_families": list(descriptor["progress_enhancement_refs"]),
        "progress_enhancement_refs_block_route": False,
        "candidate_output_shapes": {
            "validated": {"status": "validated"},
            "consumable_with_missing_refs": {
                "status": "completed_with_quality_debt",
                "blocks_stage_transition": False,
                "blocks_candidate_promotion_or_ready_claims": True,
            },
            "zero_consumable_candidate": {
                "status": "completed_with_quality_debt",
                "blocks_stage_transition": False,
                "blocks_candidate_promotion_or_ready_claims": True,
                "route_back_selection_owner": "codex_cli",
            },
        },
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
