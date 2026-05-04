from __future__ import annotations

from typing import Any, Mapping, Sequence

from med_autoscience.controllers.ai_reviewer_calibration import (
    build_ai_reviewer_calibration_corpus,
    build_ai_reviewer_calibration_learning_read_model,
)
from med_autoscience.publication_eval_reviewer_os import validate_ai_reviewer_operating_system_trace


SCHEMA_VERSION = 1
SURFACE = "ai_reviewer_journal_writing_authorization"
FULL_DRAFTING_MODE = "full_manuscript_drafting"
PRE_DRAFT_MODE = "pre_draft_planning_only"
REQUIRED_POLICY_ID = "medical_publication_critique_v1"
CRITIQUE_LINK_FIELDS = ("claim_id", "display_id", "evidence_ref", "reviewer_concern_ref")

__all__ = [
    "build_ai_reviewer_journal_writing_authorization",
    "build_authoring_runtime_authorization",
]


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


def _validate_writing_layer_inputs(
    *,
    target_journal_writing_layer: Mapping[str, Any],
    claim_to_paragraph_map: Mapping[str, Any],
    display_to_claim_map: Mapping[str, Any],
    restrained_language_strategy: Mapping[str, Any],
    blockers: list[str],
) -> None:
    if _mapping_or_none(target_journal_writing_layer) is None:
        _add_blocker(blockers, "target_journal_writing_layer_missing")
    _validate_non_empty_mapping_shape(
        payload=claim_to_paragraph_map,
        missing_blocker="claim_to_paragraph_map_missing",
        empty_blocker="claim_to_paragraph_map_empty",
        blockers=blockers,
    )
    _validate_non_empty_mapping_shape(
        payload=display_to_claim_map,
        missing_blocker="display_to_claim_map_missing",
        empty_blocker="display_to_claim_map_empty",
        blockers=blockers,
    )
    if _mapping_or_none(restrained_language_strategy) is None:
        _add_blocker(blockers, "restrained_language_strategy_missing")


def _validate_non_empty_mapping_shape(
    *,
    payload: Mapping[str, Any],
    missing_blocker: str,
    empty_blocker: str,
    blockers: list[str],
) -> None:
    normalized = _mapping_or_none(payload)
    if normalized is None:
        _add_blocker(blockers, missing_blocker)
    elif not any(_has_non_empty_shape(value) for value in normalized.values()):
        _add_blocker(blockers, empty_blocker)


def _mapping_entries(payload: Mapping[str, Any], field_name: str) -> list[dict[str, Any]]:
    items = payload.get(field_name)
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return []
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _normalized_text_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [text for item in value if (text := _non_empty_ref(item))]


def _claim_entry_id(entry: Mapping[str, Any], index: int) -> str:
    return _non_empty_ref(entry.get("claim_id")) or f"claim[{index}]"


def _display_entry_id(entry: Mapping[str, Any], index: int) -> str:
    return _non_empty_ref(entry.get("display_id")) or f"display[{index}]"


def _validate_claim_to_paragraph_trace(
    claim_to_paragraph_map: Mapping[str, Any],
    blockers: list[str],
) -> None:
    normalized = _mapping_or_none(claim_to_paragraph_map)
    if normalized is None:
        return
    for index, entry in enumerate(_mapping_entries(normalized, "claims")):
        claim_id = _claim_entry_id(entry, index)
        if _non_empty_ref(entry.get("paragraph_id")) is None:
            _add_blocker(blockers, f"claim_to_paragraph_map_paragraph_missing:{claim_id}")
        if not _normalized_text_list(entry.get("evidence_refs")):
            _add_blocker(blockers, f"claim_to_paragraph_map_evidence_trace_missing:{claim_id}")
        if not _normalized_text_list(entry.get("reviewer_concern_refs")):
            _add_blocker(blockers, f"claim_to_paragraph_map_review_trace_missing:{claim_id}")


def _validate_display_to_claim_trace(
    display_to_claim_map: Mapping[str, Any],
    blockers: list[str],
) -> None:
    normalized = _mapping_or_none(display_to_claim_map)
    if normalized is None:
        return
    for index, entry in enumerate(_mapping_entries(normalized, "links")):
        display_id = _display_entry_id(entry, index)
        if not _normalized_text_list(entry.get("claim_ids")):
            _add_blocker(blockers, f"display_to_claim_map_claim_trace_missing:{display_id}")
        if not _normalized_text_list(entry.get("evidence_refs")):
            _add_blocker(blockers, f"display_to_claim_map_evidence_trace_missing:{display_id}")


def _required_ref_status(
    *,
    evidence_ledger_ref: str,
    review_ledger_ref: str,
    blockers: list[str],
) -> tuple[str | None, str | None]:
    normalized_evidence_ref = _non_empty_ref(evidence_ledger_ref)
    normalized_review_ref = _non_empty_ref(review_ledger_ref)
    if normalized_evidence_ref is None:
        _add_blocker(blockers, "evidence_ledger_ref_missing")
    if normalized_review_ref is None:
        _add_blocker(blockers, "review_ledger_ref_missing")
    return normalized_evidence_ref, normalized_review_ref


def _calibration_cases_status(
    *,
    calibration_case_refs: Sequence[str],
    calibration_learning_projection: Mapping[str, Any] | None,
    blockers: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    normalized_calibration_refs = _non_empty_sequence(calibration_case_refs)
    if normalized_calibration_refs is None:
        _add_blocker(blockers, "calibration_refs_missing")
        normalized_ref_texts: list[str] = []
    else:
        normalized_ref_texts = [str(ref) for ref in normalized_calibration_refs]
    applied_cases = _applied_calibration_cases(
        calibration_case_refs=normalized_ref_texts,
        blockers=blockers,
    )
    if not applied_cases:
        _add_blocker(blockers, "calibration_refs_missing")
    required_refs = _required_calibration_refs(
        explicit_refs=normalized_ref_texts,
        calibration_learning_projection=calibration_learning_projection,
    )
    supplied_case_ids = {_calibration_case_id(ref) for ref in normalized_ref_texts if _non_empty_ref(ref)}
    for ref in required_refs:
        case_id = _calibration_case_id(ref)
        if case_id not in supplied_case_ids:
            _add_blocker(blockers, f"required_calibration_ref_missing:{case_id}")
    return applied_cases, required_refs


def _required_calibration_refs(
    *,
    explicit_refs: Sequence[str],
    calibration_learning_projection: Mapping[str, Any] | None,
) -> list[str]:
    required_refs: list[str] = []
    learning_refs = []
    if calibration_learning_projection is not None:
        learning_model = build_ai_reviewer_calibration_learning_read_model(calibration_learning_projection)
        learning_refs = learning_model["required_calibration_refs"]
    source_refs = learning_refs or list(explicit_refs)
    for raw_ref in source_refs:
        ref = _non_empty_ref(raw_ref)
        if ref is not None and ref not in required_refs:
            required_refs.append(ref)
    return required_refs


def _concern_id(concern: Mapping[str, Any], index: int) -> str:
    explicit_id = _non_empty_ref(concern.get("concern_id"))
    return explicit_id if explicit_id is not None else f"concern[{index}]"


def _publication_critique_concerns(publication_eval: Mapping[str, Any]) -> list[Any] | None:
    critique_payload = (
        publication_eval.get("publication_critique")
        or publication_eval.get("critique_trace")
        or publication_eval.get("publication_critique_trace")
    )
    if isinstance(critique_payload, Mapping):
        concerns = (
            critique_payload.get("concerns")
            or critique_payload.get("critique_concerns")
            or critique_payload.get("concern_linkage")
        )
    else:
        concerns = critique_payload
    return _non_empty_sequence(concerns)


def _critique_concern_linkage(
    publication_eval: Mapping[str, Any] | None,
    blockers: list[str],
) -> list[dict[str, Any]]:
    if publication_eval is None:
        return []
    concerns = _publication_critique_concerns(publication_eval)
    if concerns is None:
        _add_blocker(blockers, "publication_critique_trace_missing")
        return []

    concern_linkage: list[dict[str, Any]] = []
    for index, raw_concern in enumerate(concerns):
        if not isinstance(raw_concern, Mapping):
            _add_blocker(blockers, f"critique_concern_invalid[{index}]")
            continue
        concern = dict(raw_concern)
        linked_values = {
            field: _non_empty_ref(concern.get(field))
            for field in CRITIQUE_LINK_FIELDS
        }
        concern_identifier = _concern_id(concern, index)
        if not any(linked_values.values()):
            _add_blocker(blockers, f"critique_concern_unlinked:{concern_identifier}")
        concern_linkage.append(
            {
                "concern_id": concern_identifier,
                "claim_id": linked_values["claim_id"],
                "display_id": linked_values["display_id"],
                "evidence_ref": linked_values["evidence_ref"],
                "reviewer_concern_ref": linked_values["reviewer_concern_ref"],
            }
        )
    return concern_linkage


def _calibration_judgment_trace(
    *,
    publication_eval: Mapping[str, Any] | None,
    required_calibration_refs: Sequence[str],
    blockers: list[str],
) -> dict[str, Any]:
    reviewer_os = _mapping_or_none((publication_eval or {}).get("reviewer_operating_system")) or {}
    route_back_decision = _mapping_or_none(reviewer_os.get("route_back_decision")) or {}
    calibration_judgment = _mapping_or_none(route_back_decision.get("calibration_judgment")) or {}
    applied_refs = []
    for raw_ref in [
        *_normalized_text_list(route_back_decision.get("calibration_refs_applied")),
        *_normalized_text_list(calibration_judgment.get("refs")),
    ]:
        if raw_ref not in applied_refs:
            applied_refs.append(raw_ref)
    missing_refs = [ref for ref in required_calibration_refs if ref not in applied_refs]
    for ref in missing_refs:
        _add_blocker(
            blockers,
            f"calibration_ref_not_used_in_ai_reviewer_judgment:{_calibration_case_id(ref)}",
        )
    return {
        "required_refs": list(required_calibration_refs),
        "applied_refs": applied_refs,
        "missing_refs": missing_refs,
        "status": "blocked" if missing_refs else "ready",
    }


def _required_input_status(blockers: Sequence[str], *prefixes: str) -> str:
    return "blocked" if any(blocker.startswith(prefix) for blocker in blockers for prefix in prefixes) else "ready"


def _authorization_contract(blockers: Sequence[str]) -> dict[str, Any]:
    return {
        "required_inputs": {
            "target_journal_writing_layer": _required_input_status(
                blockers,
                "target_journal_writing_layer",
            ),
            "claim_to_paragraph_map": _required_input_status(
                blockers,
                "claim_to_paragraph_map",
            ),
            "display_to_claim_map": _required_input_status(
                blockers,
                "display_to_claim_map",
            ),
            "restrained_language_strategy": _required_input_status(
                blockers,
                "restrained_language_strategy",
            ),
            "evidence_ledger_ref": _required_input_status(blockers, "evidence_ledger_ref"),
            "review_ledger_ref": _required_input_status(blockers, "review_ledger_ref"),
            "publication_eval_ai_reviewer_provenance": _required_input_status(
                blockers,
                "publication_eval",
                "reviewer_operating_system",
                "quality_claim",
                "mechanical_projection",
            ),
            "calibration_refs": _required_input_status(
                blockers,
                "calibration_",
                "required_calibration_",
            ),
            "critique_trace": _required_input_status(
                blockers,
                "publication_critique_trace",
                "critique_concern",
            ),
        },
        "authority_limits": {
            "authorization_can_authorize_quality": False,
            "authorization_can_authorize_submission": False,
            "authorization_can_authorize_finalize": False,
        },
        "status": "blocked" if blockers else "authorized",
        "blockers": list(blockers),
    }


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
    calibration_learning_projection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    _validate_writing_layer_inputs(
        target_journal_writing_layer=target_journal_writing_layer,
        claim_to_paragraph_map=claim_to_paragraph_map,
        display_to_claim_map=display_to_claim_map,
        restrained_language_strategy=restrained_language_strategy,
        blockers=blockers,
    )
    _validate_claim_to_paragraph_trace(claim_to_paragraph_map, blockers)
    _validate_display_to_claim_trace(display_to_claim_map, blockers)
    normalized_evidence_ref, normalized_review_ref = _required_ref_status(
        evidence_ledger_ref=evidence_ledger_ref,
        review_ledger_ref=review_ledger_ref,
        blockers=blockers,
    )
    applied_cases, required_calibration_refs = _calibration_cases_status(
        calibration_case_refs=calibration_case_refs,
        calibration_learning_projection=calibration_learning_projection,
        blockers=blockers,
    )

    ai_reviewer_authorized, quality_claim_authorized = _publication_eval_authority(
        normalized_publication_eval := _mapping_or_none(publication_eval),
        blockers,
    )
    concern_linkage = _critique_concern_linkage(normalized_publication_eval, blockers)
    calibration_judgment_trace = _calibration_judgment_trace(
        publication_eval=normalized_publication_eval,
        required_calibration_refs=required_calibration_refs,
        blockers=blockers,
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
        "required_calibration_refs": required_calibration_refs,
        "calibration_judgment_trace": calibration_judgment_trace,
        "concern_linkage": concern_linkage,
        "authorization_contract": _authorization_contract(blockers),
    }


def build_authoring_runtime_authorization(**kwargs: Any) -> dict[str, Any]:
    return build_ai_reviewer_journal_writing_authorization(**kwargs)
