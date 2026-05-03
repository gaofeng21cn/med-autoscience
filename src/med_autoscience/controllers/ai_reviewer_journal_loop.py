from __future__ import annotations

from typing import Any, Mapping, Sequence

from med_autoscience.controllers.ai_reviewer_calibration import build_ai_reviewer_calibration_corpus
from med_autoscience.publication_eval_reviewer_os import validate_ai_reviewer_operating_system_trace


SCHEMA_VERSION = 1
SURFACE = "ai_reviewer_journal_writing_authorization"
FULL_DRAFTING_MODE = "full_manuscript_drafting"
PRE_DRAFT_MODE = "pre_draft_planning_only"
REQUIRED_POLICY_ID = "medical_publication_critique_v1"

__all__ = ["build_ai_reviewer_journal_writing_authorization"]


def _mapping_or_none(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    normalized = dict(value)
    return normalized if normalized else None


def _non_empty_ref(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _non_empty_sequence(value: Any) -> list[Any] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    normalized = [item for item in value if item]
    return normalized if normalized else None


def _has_non_empty_shape(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(value)
    return False


def _add_blocker(blockers: list[str], blocker: str) -> None:
    if blocker not in blockers:
        blockers.append(blocker)


def _calibration_case_id(ref: str) -> str:
    return ref.rsplit("#", 1)[-1].strip()


def _applied_calibration_cases(
    *,
    calibration_case_refs: Sequence[str],
    blockers: list[str],
) -> list[dict[str, Any]]:
    corpus = build_ai_reviewer_calibration_corpus()
    cases_by_id = {str(case["case_id"]): case for case in corpus["cases"]}
    applied: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_ref in enumerate(calibration_case_refs):
        ref = _non_empty_ref(raw_ref)
        if ref is None:
            _add_blocker(blockers, f"calibration_refs_invalid[{index}]")
            continue
        case_id = _calibration_case_id(ref)
        case = cases_by_id.get(case_id)
        if case is None:
            _add_blocker(blockers, f"calibration_case_unknown:{case_id}")
            continue
        if case_id in seen:
            continue
        seen.add(case_id)
        applied.append(
            {
                "case_id": case_id,
                "expected_route": case["expected_route"],
                "mechanical_facts_role": case["mechanical_facts_role"],
                "quality_gate_relaxation_allowed": case["quality_gate_relaxation_allowed"],
            }
        )
    return applied


def _publication_eval_authority(
    publication_eval: Mapping[str, Any] | None,
    blockers: list[str],
) -> tuple[bool, bool]:
    if publication_eval is None:
        _add_blocker(blockers, "publication_eval_missing")
        return False, False

    provenance = publication_eval.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        _add_blocker(blockers, "publication_eval_provenance_missing")
        return False, False

    owner = _non_empty_ref(provenance.get("owner"))
    policy_id = _non_empty_ref(provenance.get("policy_id"))
    ai_reviewer_required = provenance.get("ai_reviewer_required")
    owner_is_ai_reviewer = (
        owner == "ai_reviewer"
        and ai_reviewer_required is False
        and policy_id == REQUIRED_POLICY_ID
    )
    if not owner_is_ai_reviewer:
        _add_blocker(blockers, "publication_eval_not_ai_reviewer_owned")

    if owner == "mechanical_projection" or publication_eval.get("mechanical_projection"):
        _add_blocker(blockers, "mechanical_projection_cannot_authorize_quality")

    reviewer_errors = validate_ai_reviewer_operating_system_trace(
        publication_eval.get("reviewer_operating_system")
    )
    if reviewer_errors:
        _add_blocker(blockers, "reviewer_operating_system_trace_missing_or_invalid")

    quality_claim_authorized = publication_eval.get("quality_claim_authorized")
    if quality_claim_authorized is not True:
        _add_blocker(blockers, "quality_claim_not_authorized_by_ai_reviewer")

    return owner_is_ai_reviewer and not reviewer_errors, quality_claim_authorized is True


def build_ai_reviewer_journal_writing_authorization(
    *,
    target_journal_writing_layer: Mapping[str, Any],
    claim_to_paragraph_map: Mapping[str, Any],
    display_to_claim_map: Mapping[str, Any],
    restrained_language_strategy: Mapping[str, Any],
    evidence_ledger_ref: str,
    review_ledger_ref: str,
    publication_eval: Mapping[str, Any],
    calibration_case_refs: Sequence[str],
) -> dict[str, Any]:
    blockers: list[str] = []

    if _mapping_or_none(target_journal_writing_layer) is None:
        _add_blocker(blockers, "target_journal_writing_layer_missing")
    if _mapping_or_none(claim_to_paragraph_map) is None:
        _add_blocker(blockers, "claim_to_paragraph_map_missing")
    elif not any(_has_non_empty_shape(value) for value in claim_to_paragraph_map.values()):
        _add_blocker(blockers, "claim_to_paragraph_map_empty")
    if _mapping_or_none(display_to_claim_map) is None:
        _add_blocker(blockers, "display_to_claim_map_missing")
    elif not any(_has_non_empty_shape(value) for value in display_to_claim_map.values()):
        _add_blocker(blockers, "display_to_claim_map_empty")
    if _mapping_or_none(restrained_language_strategy) is None:
        _add_blocker(blockers, "restrained_language_strategy_missing")

    normalized_evidence_ref = _non_empty_ref(evidence_ledger_ref)
    normalized_review_ref = _non_empty_ref(review_ledger_ref)
    if normalized_evidence_ref is None:
        _add_blocker(blockers, "evidence_ledger_ref_missing")
    if normalized_review_ref is None:
        _add_blocker(blockers, "review_ledger_ref_missing")

    normalized_calibration_refs = _non_empty_sequence(calibration_case_refs)
    if normalized_calibration_refs is None:
        _add_blocker(blockers, "calibration_refs_missing")
        applied_cases: list[dict[str, Any]] = []
    else:
        applied_cases = _applied_calibration_cases(
            calibration_case_refs=[str(ref) for ref in normalized_calibration_refs],
            blockers=blockers,
        )
        if not applied_cases:
            _add_blocker(blockers, "calibration_refs_missing")

    ai_reviewer_authorized, quality_claim_authorized = _publication_eval_authority(
        _mapping_or_none(publication_eval),
        blockers,
    )

    full_drafting_authorized = not blockers and ai_reviewer_authorized and quality_claim_authorized
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "authority": {
            "owner": "ai_reviewer",
            "publication_eval_surface": "artifacts/publication_eval/latest.json",
            "mechanical_projection_can_authorize_quality": False,
        },
        "full_drafting_authorized": full_drafting_authorized,
        "mode": FULL_DRAFTING_MODE if full_drafting_authorized else PRE_DRAFT_MODE,
        "quality_claim_authorized": quality_claim_authorized,
        "blockers": blockers,
        "required_refs": {
            "evidence_ledger_ref": normalized_evidence_ref,
            "review_ledger_ref": normalized_review_ref,
        },
        "calibration_cases_applied": applied_cases,
    }
