from __future__ import annotations

from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
LEARNING_SURFACE = "ai_reviewer_calibration_learning_read_model"
OUTCOME_REGRESSION_SURFACE = "ai_reviewer_outcome_learning_regression"
SUPPORTED_OUTCOME_TYPES = (
    "major_revision",
    "reject",
    "accept",
    "editorial_desk_reject",
    "post_review_repair",
)
SOURCE_OUTCOME_ALIASES = {
    "rejection": "reject",
    "reviewer_revision": "post_review_repair",
}
REQUIRED_LEARNING_FAILURE_MODES = (
    "claim_overreach",
    "missing_reviewer_trace",
    "coverage_as_quality",
    "weak_external_validation",
    "statistical_discipline_waiver_misuse",
)
FAILURE_MODE_CALIBRATION_REFS = {
    "claim_overreach": "ai_reviewer_calibration_corpus#claim_overreach",
    "coverage_as_quality": "ai_reviewer_calibration_corpus#coverage_as_quality",
    "mechanical_gate_misuse": "ai_reviewer_calibration_corpus#mechanical_gate_as_quality",
    "missing_reviewer_trace": "ai_reviewer_calibration_corpus#missing_reviewer_trace",
    "weak_external_validation": "ai_reviewer_calibration_corpus#weak_external_validation",
    "statistical_discipline_waiver_misuse": (
        "ai_reviewer_calibration_corpus#statistical_discipline_waiver_misuse"
    ),
}
AI_REVIEWER_PROVENANCE_REQUIREMENTS = {
    "assessment_provenance.owner": "ai_reviewer",
    "assessment_provenance.ai_reviewer_required": False,
    "assessment_provenance.policy_id": "medical_publication_critique_v1",
    "reviewer_operating_system.required": True,
}
MECHANICAL_INPUT_CONTRACT = {
    "role": "evidence_only",
    "can_authorize_readiness": False,
    "can_close_quality_gate": False,
    "can_replace_ai_reviewer_provenance": False,
}
REAL_STUDY_SOAK_STAGES = (
    "literature_scout",
    "line_selection",
    "main_analysis",
    "bounded_analysis",
    "route_back",
    "stop_loss",
    "revision_reopen",
    "runtime_recovery",
    "finalize_rebuild",
    "final_pre_submission_audit",
)

CALIBRATION_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "mechanical_ready_without_ai_provenance",
        "failure_mode": "ready wording appeared from gate or coverage without AI reviewer ownership",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "reject ready state until publication_eval carries AI reviewer provenance and trace",
    },
    {
        "case_id": "thin_first_draft_despite_richer_data_asset",
        "failure_mode": "draft uses already-verified data only descriptively when stronger bounded analysis is supported",
        "expected_route": "return_to_analysis_campaign",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "route back for limited supplemental analysis before full manuscript drafting",
    },
    {
        "case_id": "coverage_complete_but_quality_unreviewed",
        "failure_mode": "coverage or paper contract health is treated as medical manuscript quality ready",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "preserve coverage as mechanical oracle and require MAS AI preflight",
    },
    {
        "case_id": "medical_prose_review_route_back",
        "failure_mode": "work-report prose or controller language remains in a manuscript-like draft",
        "expected_route": "return_to_write",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "AI prose review identifies section-level rewrite targets before finalize",
    },
    {
        "case_id": "claim_strength_exceeds_evidence",
        "failure_mode": "clinical or novelty claims exceed evidence ledger support",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "AI reviewer narrows claim or routes to bounded evidence repair",
    },
    {
        "case_id": "reviewer_trace_missing",
        "failure_mode": "AI reviewer gives a conclusion without structured rubric, provenance, or route-back trace",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "fail closed until reviewer_operating_system trace is complete",
    },
    {
        "case_id": "thin_first_draft",
        "failure_mode": "first draft stays descriptive when the target journal layer requires stronger section planning and claim placement",
        "expected_route": "return_to_write",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "require target journal family, section plan, and claim-to-paragraph trace before draft readiness",
    },
    {
        "case_id": "overstrong_claim",
        "failure_mode": "target-journal style examples or near-neighbor framing produce claims stronger than the evidence ledger supports",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "route back to restrained language strategy and claim-evidence alignment",
    },
    {
        "case_id": "claim_overreach",
        "failure_mode": "claim scope, causal language, or novelty framing overreaches the accepted evidence ledger",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "require claim-level restraint before drafting, revision response, or final audit",
    },
    {
        "case_id": "missing_reviewer_trace",
        "failure_mode": "publication critique lacks reviewer operating system trace across route-back and final audit stages",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "fail closed until AI reviewer provenance and route-back trace are present",
    },
    {
        "case_id": "coverage_as_quality",
        "failure_mode": "section, display, or checklist coverage is treated as publication quality",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "preserve coverage as mechanical evidence and require subjective AI reviewer quality judgment",
    },
    {
        "case_id": "mechanical_gate_as_quality",
        "failure_mode": "a passing controller or mechanical gate is projected as manuscript quality readiness",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "block readiness until AI reviewer artifact owns the quality decision",
    },
    {
        "case_id": "weak_external_validation",
        "failure_mode": "external validation, generalizability, or holdout evidence is too weak for the target claim",
        "expected_route": "return_to_analysis_campaign",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "route to bounded validation repair or narrow the claim before quality acceptance",
    },
    {
        "case_id": "statistical_discipline_waiver_misuse",
        "failure_mode": "statistical discipline waiver is used to bypass required model, subgroup, or sensitivity rigor",
        "expected_route": "return_to_analysis_campaign",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "require reviewer-traceable statistical rationale before waiving analysis repair",
    },
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for raw in value if (item := _text(raw))]


def _normalize_source_outcome(value: object) -> str:
    outcome = SOURCE_OUTCOME_ALIASES.get(_text(value), _text(value))
    if outcome not in SUPPORTED_OUTCOME_TYPES:
        raise ValueError(f"unsupported AI reviewer calibration source_outcome: {outcome}")
    return outcome


def _normalize_learning_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    failure_mode = _text(entry.get("failure_mode"))
    if failure_mode not in FAILURE_MODE_CALIBRATION_REFS:
        raise ValueError(f"unsupported AI reviewer calibration failure_mode: {failure_mode}")
    normalized = {
        "entry_id": _text(entry.get("entry_id")),
        "source_outcome": _normalize_source_outcome(entry.get("source_outcome")),
        "failure_mode": failure_mode,
        "source_ref": _text(entry.get("source_ref")),
        "issue_summary": _text(entry.get("issue_summary")),
        "claim_refs": _text_list(entry.get("claim_refs")),
        "evidence_refs": _text_list(entry.get("evidence_refs")),
        "reviewer_trace_refs": _text_list(entry.get("reviewer_trace_refs")),
        "calibration_ref": FAILURE_MODE_CALIBRATION_REFS[failure_mode],
    }
    missing = [
        field
        for field in ("entry_id", "source_outcome", "source_ref", "issue_summary")
        if not normalized[field]
    ]
    if missing:
        raise ValueError(f"AI reviewer calibration learning entry missing fields: {', '.join(missing)}")
    if not normalized["evidence_refs"]:
        raise ValueError("AI reviewer calibration learning entry requires evidence_refs")
    if not normalized["reviewer_trace_refs"]:
        raise ValueError("AI reviewer calibration learning entry requires reviewer_trace_refs")
    return normalized


def _learning_authority_contract() -> dict[str, Any]:
    return {
        "read_model_only": True,
        "outcome_intake_can_authorize_quality": False,
        "outcome_intake_can_authorize_drafting": False,
        "learning_can_authorize_quality": False,
        "learning_can_authorize_drafting": False,
        "learning_can_authorize_submission": False,
        "learning_can_authorize_finalize": False,
        "required_calibration_refs_can_authorize_quality": False,
    }


def _outcome_regression_authority_contract() -> dict[str, Any]:
    return {
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_drafting": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _failure_mode_projection(entries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    projection: list[dict[str, Any]] = []
    for failure_mode in FAILURE_MODE_CALIBRATION_REFS:
        matching_entries = [entry for entry in entries if entry["failure_mode"] == failure_mode]
        if not matching_entries:
            continue
        source_outcomes: list[str] = []
        for entry in matching_entries:
            source_outcome = str(entry["source_outcome"])
            if source_outcome not in source_outcomes:
                source_outcomes.append(source_outcome)
        projection.append(
            {
                "failure_mode": failure_mode,
                "count": len(matching_entries),
                "calibration_ref": FAILURE_MODE_CALIBRATION_REFS[failure_mode],
                "source_outcomes": source_outcomes,
            }
        )
    return projection


def _counts_by_field(entries: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = str(entry[field])
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_ai_reviewer_calibration_learning_read_model(
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = dict(payload or {})
    entries = [
        _normalize_learning_entry(entry)
        for entry in _list_of_mappings(source.get("learning_entries"))
    ]
    projected_required_refs = _text_list(source.get("required_calibration_refs"))
    counts: dict[str, int] = {}
    required_failure_modes: list[str] = []
    required_refs: list[str] = []
    for entry in entries:
        failure_mode = entry["failure_mode"]
        counts[failure_mode] = counts.get(failure_mode, 0) + 1
        if failure_mode not in required_failure_modes:
            required_failure_modes.append(failure_mode)
        calibration_ref = entry["calibration_ref"]
        if calibration_ref not in required_refs:
            required_refs.append(calibration_ref)
    for ref in projected_required_refs:
        if ref not in required_refs:
            required_refs.append(ref)
    return {
        "surface": LEARNING_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "supported_outcomes": list(SUPPORTED_OUTCOME_TYPES),
        "regression_failure_modes": list(REQUIRED_LEARNING_FAILURE_MODES),
        "regression_refs": [
            FAILURE_MODE_CALIBRATION_REFS[failure_mode]
            for failure_mode in REQUIRED_LEARNING_FAILURE_MODES
        ],
        "required_failure_modes": required_failure_modes,
        "required_calibration_refs": required_refs,
        "failure_mode_counts": counts,
        "outcome_counts": _counts_by_field(entries, "source_outcome"),
        "failure_mode_projection": _failure_mode_projection(entries),
        "outcome_learning_regression": build_outcome_learning_calibration_regression(
            {"learning_entries": entries}
        ),
        "learning_entries": entries,
        "authority_contract": _learning_authority_contract(),
    }


def append_ai_reviewer_calibration_learning_entry(
    *,
    existing_payload: Mapping[str, Any] | None,
    learning_entry: Mapping[str, Any],
) -> dict[str, Any]:
    entries = _list_of_mappings(dict(existing_payload or {}).get("learning_entries"))
    entries.append(dict(learning_entry))
    return build_ai_reviewer_calibration_learning_read_model({"learning_entries": entries})


def append_ai_reviewer_calibration_outcome_intake(
    *,
    existing_payload: Mapping[str, Any] | None,
    outcome_intake: Mapping[str, Any],
) -> dict[str, Any]:
    learning_entry = {
        "entry_id": _text(outcome_intake.get("entry_id") or outcome_intake.get("outcome_id")),
        "source_outcome": outcome_intake.get("source_outcome") or outcome_intake.get("outcome_type"),
        "failure_mode": outcome_intake.get("failure_mode"),
        "source_ref": outcome_intake.get("source_ref") or outcome_intake.get("outcome_ref"),
        "issue_summary": outcome_intake.get("issue_summary") or outcome_intake.get("outcome_summary"),
        "claim_refs": outcome_intake.get("claim_refs"),
        "evidence_refs": outcome_intake.get("evidence_refs"),
        "reviewer_trace_refs": outcome_intake.get("reviewer_trace_refs"),
    }
    return append_ai_reviewer_calibration_learning_entry(
        existing_payload=existing_payload,
        learning_entry=learning_entry,
    )


def build_outcome_learning_calibration_regression(
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    entries = [
        _normalize_learning_entry(entry)
        for entry in _list_of_mappings(dict(payload or {}).get("learning_entries"))
    ]
    refs: list[str] = []
    failure_modes: list[str] = []
    for entry in entries:
        if entry["failure_mode"] not in failure_modes:
            failure_modes.append(entry["failure_mode"])
        if entry["calibration_ref"] not in refs:
            refs.append(entry["calibration_ref"])
    missing_required_modes = [
        mode for mode in REQUIRED_LEARNING_FAILURE_MODES if mode not in set(failure_modes)
    ]
    planning_mode = "repair_planning_only" if refs else "pre_draft_planning_only"
    if not missing_required_modes and refs:
        planning_mode = "calibration_regression_ready_for_authoring_review"
    return {
        "surface": OUTCOME_REGRESSION_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if refs else "blocked",
        "planning_mode": planning_mode,
        "supported_outcomes": list(SUPPORTED_OUTCOME_TYPES),
        "required_failure_modes": list(REQUIRED_LEARNING_FAILURE_MODES),
        "observed_failure_modes": failure_modes,
        "missing_required_failure_modes": missing_required_modes,
        "required_calibration_refs": refs,
        "regression_refs": refs,
        "outcome_counts": _counts_by_field(entries, "source_outcome"),
        "failure_mode_projection": _failure_mode_projection(entries),
        "full_drafting_allowed_without_required_refs": False,
        "repair_planning_allowed": bool(refs),
        "pre_draft_planning_allowed": True,
        "authority_contract": _outcome_regression_authority_contract(),
    }


def build_ai_reviewer_calibration_corpus() -> dict[str, Any]:
    return {
        "surface": "ai_reviewer_calibration_corpus",
        "schema_version": SCHEMA_VERSION,
        "authority": {
            "owner": "MedAutoScience Quality OS",
            "mechanical_projection_can_close_case": False,
            "ai_reviewer_required_for_subjective_quality": True,
            "prompt_only_calibration_allowed": False,
            "ai_reviewer_provenance_requirements": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        },
        "cases": [dict(case) for case in CALIBRATION_CASES],
        "soak_matrix": {
            "surface": "real_study_soak_matrix",
            "role": "quality_regression_and_route_back_proof",
            "mechanical_projection_can_authorize_quality": False,
            "required_stages": list(REAL_STUDY_SOAK_STAGES),
            "stage_evidence_contract": {
                "requires_ai_reviewer_provenance_for_quality": True,
                "requires_route_back_trace": True,
                "requires_quality_regression_projection": True,
                "mechanical_gate_role": "evidence_only",
            },
        },
        "regression_axes": [
            "ai_reviewer_provenance",
            "pre_draft_quality",
            "coverage_as_mechanical_oracle",
            "medical_journal_prose",
            "claim_evidence_alignment",
            "reviewer_os_trace_completeness",
            "target_journal_writing_layer",
            "real_study_soak_matrix",
        ],
    }


def build_pre_draft_readiness_materialization_contract() -> dict[str, Any]:
    return {
        "surface": "pre_draft_readiness_materialization_contract",
        "schema_version": SCHEMA_VERSION,
        "stable_path": "paper/pre_draft_writing_readiness.json",
        "materializer_owner": "MedAutoScience Quality OS",
        "readiness_verdict_authority": {
            "required_owner": "ai_reviewer",
            "required_ai_reviewer_required": False,
            "required_policy_id": "medical_publication_critique_v1",
            "required_trace_surface": "reviewer_operating_system",
            "prompt_only_authority_allowed": False,
        },
        "ai_first_blocking_inputs": [
            "study_charter.paper_quality_contract",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "paper/medical_manuscript_blueprint.json",
            "artifacts/publication_eval/latest.json",
        ],
        "mechanical_supporting_inputs": [
            "reporting_guideline_checklist.json",
            "claim_evidence_map",
            "artifact_inventory",
            "manuscript_section_inventory",
        ],
        "mechanical_supporting_input_contract": MECHANICAL_INPUT_CONTRACT,
        "required_decisions": [
            "clinical_question_ready",
            "evidence_strength_ready",
            "reporting_guideline_ready",
            "manuscript_shape_ready",
            "route_back_not_required",
        ],
        "fail_closed_without_ai_reviewer": True,
        "fail_closed_without_ai_reviewer_provenance": True,
        "fail_closed_statuses": ["review_required", "route_back_required"],
        "mechanical_inputs_authorize_quality": False,
        "mechanical_inputs_can_only_supply": "evidence_only",
        "forbidden_materialization_modes": [
            "prompt_only_readiness",
            "mechanical_ready_verdict",
            "coverage_complete_as_quality_ready",
            "claim_only_ready",
        ],
    }


def build_quality_regression_calibration_evidence_contract() -> dict[str, Any]:
    return {
        "surface": "quality_regression_calibration_evidence_contract",
        "owner": "MAS Evaluation OS",
        "judge_scores": {
            "accepted_sources": ["autorater", "side_by_side_judge"],
            "role": "calibration_evidence_only",
            "can_authorize_publication_quality": False,
            "can_replace_ai_reviewer": False,
        },
        "required_refs": [
            "draft_eval_ref",
            "revision_eval_ref",
            "final_package_eval_ref",
            "calibration_evidence_refs",
        ],
        "fail_closed_without_refs": True,
    }
