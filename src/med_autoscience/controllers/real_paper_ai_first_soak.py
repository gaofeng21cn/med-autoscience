from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "real_paper_ai_first_soak"
OBSERVATION_SURFACE = "real_paper_ai_first_soak_observation"

CANONICAL_ARTIFACT_REBUILD_SOURCE = "canonical_sources_and_ai_reviewer_quality_decision"
QUALITY_AUTHORIZATION_SOURCE = "ai_reviewer_backed_publication_eval_or_manual_gate"
STRUCTURED_ROUTE_BACK_TAXONOMY = "structured_rework_taxonomy"
AI_REVIEWER_TRACE_SOURCE = "reviewer_operating_system_trace"
MANUAL_GATE_SOURCE = "explicit_human_decision"

PAPER_LINES: tuple[dict[str, Any], ...] = (
    {
        "paper_id": "nf-pitnet-003",
        "soak_role": "manual-finishing-to-ai-first-regression",
        "expected_evidence": "route_back_and_artifact_rebuild_trace",
    },
    {
        "paper_id": "dpcc-003",
        "soak_role": "large-real-world-primary-care-paper",
        "expected_evidence": "pre_draft_ai_reviewer_intervention_trace",
    },
    {
        "paper_id": "dpcc-004",
        "soak_role": "parallel-real-paper-generalization",
        "expected_evidence": "quality_authorization_and_manual_gate_trace",
    },
)

EVIDENCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "paper_id",
    "quality_authorization_source",
    "artifact_rebuild_source",
    "route_back_count",
    "route_back_reasons",
    "ai_reviewer_intervention_points",
    "mechanical_ready_overreach_detected",
    "final_blockers",
    "manual_gate",
)

DERIVED_ARTIFACT_AUTHORITY_MARKERS: tuple[str, ...] = (
    "current_package",
    "submission_minimal",
    "artifacts/final",
    "manuscript/current_package",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _contains_derived_artifact_marker(value: object) -> bool:
    text = _text(value)
    return any(marker in text for marker in DERIVED_ARTIFACT_AUTHORITY_MARKERS)


def build_real_paper_ai_first_soak_contract() -> dict[str, Any]:
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "purpose": "measure_ai_first_flow_rework_and_quality",
        "manual_study_artifact_patch_allowed": False,
        "canonical_flow_only": True,
        "observational_evidence_only": True,
        "quality_gate_relaxation_allowed": False,
        "mechanical_ready_can_authorize_quality": False,
        "artifact_patch_targets": [],
        "paper_lines": [dict(line) for line in PAPER_LINES],
        "evidence_schema": {
            "required_fields": list(EVIDENCE_REQUIRED_FIELDS),
            "field_contracts": {
                "paper_id": "stable_real_paper_line_id",
                "quality_authorization_source": QUALITY_AUTHORIZATION_SOURCE,
                "artifact_rebuild_source": CANONICAL_ARTIFACT_REBUILD_SOURCE,
                "route_back_count": "count_of_quality_os_route_backs",
                "route_back_reasons": STRUCTURED_ROUTE_BACK_TAXONOMY,
                "ai_reviewer_intervention_points": AI_REVIEWER_TRACE_SOURCE,
                "mechanical_ready_overreach_detected": "boolean_quality_authority_overreach_flag",
                "final_blockers": "remaining_blockers_without_relaxing_gates",
                "manual_gate": MANUAL_GATE_SOURCE,
            },
        },
        "authority_requirements": {
            "quality_authorization_source": QUALITY_AUTHORIZATION_SOURCE,
            "artifact_rebuild_source": CANONICAL_ARTIFACT_REBUILD_SOURCE,
            "route_back_reasons": STRUCTURED_ROUTE_BACK_TAXONOMY,
            "ai_reviewer_intervention_points": AI_REVIEWER_TRACE_SOURCE,
            "manual_gate": MANUAL_GATE_SOURCE,
        },
        "forbidden_modes": [
            "manual_artifact_patch",
            "derived_artifact_as_quality_authority",
            "derived_artifact_as_rebuild_source",
            "mechanical_ready_as_quality_authority",
            "quality_gate_relaxation",
            "study_workspace_patch",
        ],
    }


def build_real_paper_ai_first_soak_observation(
    *,
    paper_id: str,
    quality_authorization_source: str,
    artifact_rebuild_source: str,
    route_back_reasons: list[str],
    ai_reviewer_intervention_points: list[str],
    mechanical_ready_overreach_detected: bool,
    final_blockers: list[str],
    manual_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface": OBSERVATION_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "paper_id": paper_id,
        "quality_authorization_source": quality_authorization_source,
        "artifact_rebuild_source": artifact_rebuild_source,
        "route_back_count": len(route_back_reasons),
        "route_back_reasons": list(route_back_reasons),
        "ai_reviewer_intervention_points": list(ai_reviewer_intervention_points),
        "mechanical_ready_overreach_detected": bool(mechanical_ready_overreach_detected),
        "final_blockers": list(final_blockers),
        "manual_gate": dict(manual_gate),
        "manual_study_artifact_patch_allowed": False,
        "canonical_flow_only": True,
        "observational_evidence_only": True,
        "artifact_write_paths": [],
    }


def validate_real_paper_ai_first_soak_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    allowed_paper_ids = {_text(line["paper_id"]) for line in PAPER_LINES}

    if observation.get("surface") != OBSERVATION_SURFACE:
        issues.append({"code": "observation_surface_invalid"})
    if observation.get("schema_version") != SCHEMA_VERSION:
        issues.append({"code": "schema_version_invalid"})

    for field in EVIDENCE_REQUIRED_FIELDS:
        if field not in observation:
            issues.append({"code": "required_field_missing", "field": field})

    paper_id = _text(observation.get("paper_id"))
    if paper_id not in allowed_paper_ids:
        issues.append({"code": "paper_id_not_in_soak_contract", "paper_id": paper_id})

    if observation.get("manual_study_artifact_patch_allowed") is not False:
        issues.append({"code": "manual_artifact_patching_enabled"})
    if observation.get("canonical_flow_only") is not True:
        issues.append({"code": "canonical_flow_not_required"})
    if observation.get("observational_evidence_only") is not True:
        issues.append({"code": "observational_evidence_not_enforced"})
    if _list(observation.get("artifact_write_paths")):
        issues.append({"code": "artifact_write_path_present"})

    if _contains_derived_artifact_marker(observation.get("quality_authorization_source")):
        issues.append({"code": "quality_authority_uses_derived_artifact"})
    if _text(observation.get("artifact_rebuild_source")) != CANONICAL_ARTIFACT_REBUILD_SOURCE:
        issues.append({"code": "artifact_rebuild_source_not_canonical"})

    route_back_reasons = _list(observation.get("route_back_reasons"))
    if not route_back_reasons:
        issues.append({"code": "route_back_reasons_missing"})
    elif observation.get("route_back_count") != len(route_back_reasons):
        issues.append({"code": "route_back_count_mismatch"})

    if not _list(observation.get("ai_reviewer_intervention_points")):
        issues.append({"code": "ai_reviewer_intervention_points_missing"})
    if not _mapping(observation.get("manual_gate")):
        issues.append({"code": "manual_gate_missing"})

    return {
        "surface": "real_paper_ai_first_soak_observation_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
