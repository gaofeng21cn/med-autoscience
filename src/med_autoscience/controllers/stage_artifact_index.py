from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.stage_surface_contract import (
    MAIN_STAGE_ROUTE_IDS,
    build_stage_surface_contract,
)

ALLOWED_ARTIFACT_STATUSES = (
    "missing",
    "partial",
    "artifact_delta_present",
    "ready_for_review",
    "blocked_by_required_artifact",
    "terminal_delivered",
)

_STATUS_MISSING = "missing"
_STATUS_PARTIAL = "partial"
_STATUS_DELTA = "artifact_delta_present"

_STAGE_OUTPUT_SURFACES: dict[str, tuple[tuple[str, str], ...]] = {
    "scout": (
        ("scout_note", "artifacts/stage_outputs/scout/scout_note.md"),
        ("literature_scout_os", "artifacts/stage_outputs/scout/literature_scout_os.json"),
        ("route_recommendation", "artifacts/stage_outputs/scout/route_recommendation.json"),
        ("open_questions", "artifacts/stage_outputs/scout/open_questions.json"),
    ),
    "idea": (
        ("line_selection_note", "artifacts/stage_outputs/idea/line_selection_note.md"),
        ("study_line_scorecard", "artifacts/stage_outputs/idea/study_line_scorecard.json"),
        ("next_route_recommendation", "artifacts/stage_outputs/idea/next_route_recommendation.json"),
        ("claim_sketch", "artifacts/stage_outputs/idea/claim_sketch.md"),
    ),
    "baseline": (
        ("baseline_artifact_set", "artifacts/stage_outputs/baseline/baseline_artifact_set.json"),
        ("baseline_summary", "artifacts/stage_outputs/baseline/baseline_summary.md"),
        (
            "next_route_recommendation",
            "artifacts/stage_outputs/baseline/next_route_recommendation.json",
        ),
    ),
    "experiment": (
        ("primary_result_artifact_set", "artifacts/stage_outputs/experiment/primary_result.json"),
        ("experiment_summary", "artifacts/stage_outputs/experiment/experiment_summary.md"),
        (
            "next_route_recommendation",
            "artifacts/stage_outputs/experiment/next_route_recommendation.json",
        ),
    ),
    "analysis-campaign": (
        (
            "analysis_campaign_summary",
            "artifacts/stage_outputs/analysis-campaign/analysis_campaign_summary.md",
        ),
        (
            "bounded_analysis_candidate_board",
            "artifacts/stage_outputs/analysis-campaign/bounded_analysis_candidate_board.json",
        ),
        ("evidence_refs", "paper/evidence_ledger.json"),
        ("remaining_gaps", "artifacts/stage_outputs/analysis-campaign/remaining_gaps.json"),
    ),
    "write": (
        ("manuscript_draft", "artifacts/stage_outputs/write/manuscript_draft.json"),
        ("canonical_draft", "paper/draft.md"),
        ("claim_evidence_map", "paper/claim_evidence_map.json"),
        ("reviewer_first_pass_note", "paper/review/reviewer_first_pass.md"),
        ("first_draft_quality_note", "artifacts/stage_outputs/write/first_draft_quality_note.md"),
    ),
    "review": (
        ("reviewer_action_matrix", "artifacts/stage_outputs/review/reviewer_action_matrix.json"),
        ("review_record", "paper/review/review_ledger.json"),
        ("publication_eval", "artifacts/publication_eval/latest.json"),
    ),
    "finalize": (
        ("publication_eval", "artifacts/publication_eval/latest.json"),
        ("controller_decision", "artifacts/controller_decisions/latest.json"),
        ("package_freshness_proof", "artifacts/stage_outputs/finalize/package_freshness_proof.json"),
        ("declarations", "artifacts/stage_outputs/finalize/declarations.json"),
    ),
    "decision": (
        ("decision_memo", "artifacts/stage_outputs/decision/decision_memo.md"),
        ("stop_loss_or_go_record", "artifacts/stage_outputs/decision/stop_loss_or_go_record.json"),
    ),
    "journal-resolution": (
        (
            "journal_resolution_record",
            "artifacts/stage_outputs/journal-resolution/journal_resolution_record.json",
        ),
        ("journal_guideline_refs", "artifacts/stage_outputs/journal-resolution/guideline_refs.json"),
    ),
}


def build_stage_artifact_index(*, study_id: str, study_root: Path) -> dict[str, Any]:
    resolved_study_root = study_root.expanduser().resolve()
    stage_contract = build_stage_surface_contract()
    cards_by_stage = {
        str(card["route_id"]): card
        for card in stage_contract["stage_cards"]
        if isinstance(card, Mapping)
    }
    stages = [
        _build_stage_artifact_state(
            stage_id=stage_id,
            stage_card=cards_by_stage[stage_id],
            study_root=resolved_study_root,
        )
        for stage_id in MAIN_STAGE_ROUTE_IDS
    ]
    current_stage = _current_stage(stages)
    stale_platform_repairs = _stale_platform_repairs(study_root=resolved_study_root, stages=stages)
    return {
        "schema_version": 1,
        "surface_kind": "stage_artifact_index",
        "study_id": str(study_id),
        "study_root": str(resolved_study_root),
        "allowed_artifact_statuses": list(ALLOWED_ARTIFACT_STATUSES),
        "authority_boundary": _authority_boundary(),
        "current_stage": _current_stage_projection(current_stage),
        "next_owner_action": _next_owner_action(current_stage),
        "provider_liveness": _provider_liveness(study_root=resolved_study_root),
        "stale_platform_repairs": stale_platform_repairs,
        "stages": stages,
    }


def _build_stage_artifact_state(
    *,
    stage_id: str,
    stage_card: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    required_refs = [
        {
            "role": role,
            "ref": ref,
            "source": "stage_artifact_index_declared_output",
            "body_included": False,
        }
        for role, ref in _required_output_surfaces(stage_id)
    ]
    observed_refs = [
        {
            "role": item["role"],
            "ref": item["ref"],
            "path": str(study_root / str(item["ref"])),
            "body_included": False,
        }
        for item in required_refs
        if (study_root / str(item["ref"])).exists()
    ]
    artifact_status = _artifact_status(required_refs=required_refs, observed_refs=observed_refs)
    next_missing = _next_missing_surface(required_refs=required_refs, observed_refs=observed_refs)
    return {
        "surface_kind": "stage_artifact_state",
        "stage_id": stage_id,
        "display_name": str(stage_card.get("display_name") or stage_id),
        "required_output_refs": required_refs,
        "observed_artifact_refs": observed_refs,
        "artifact_status": artifact_status,
        "freshness": _freshness(artifact_status),
        "stage_progress_status": _stage_progress_status(artifact_status),
        "next_missing_surface": next_missing,
        "next_routes": list(stage_card.get("next_routes") or ()),
        "authority_boundary": _authority_boundary(),
    }


def _required_output_surfaces(stage_id: str) -> tuple[tuple[str, str], ...]:
    return _STAGE_OUTPUT_SURFACES.get(
        stage_id,
        ((f"{stage_id}_stage_output", f"artifacts/stage_outputs/{stage_id}/latest.json"),),
    )


def _artifact_status(*, required_refs: list[dict[str, Any]], observed_refs: list[dict[str, Any]]) -> str:
    if not observed_refs:
        return _STATUS_MISSING
    if len(observed_refs) < len(required_refs):
        return _STATUS_PARTIAL
    return _STATUS_DELTA


def _stage_progress_status(artifact_status: str) -> str:
    if artifact_status == _STATUS_MISSING:
        return "artifact_required"
    if artifact_status == _STATUS_PARTIAL:
        return "artifact_partial"
    return "artifact_delta_present"


def _freshness(artifact_status: str) -> dict[str, Any]:
    if artifact_status == _STATUS_MISSING:
        return {
            "status": "red_missing",
            "meaning": "required stage artifact refs are missing",
            "blocks_auto_advance_by_default": False,
        }
    if artifact_status == _STATUS_PARTIAL:
        return {
            "status": "yellow_partial",
            "meaning": "some required stage artifact refs are present",
            "blocks_auto_advance_by_default": False,
        }
    return {
        "status": "green_artifact_delta_present",
        "meaning": "required stage artifact refs are present",
        "blocks_auto_advance_by_default": False,
    }


def _next_missing_surface(
    *,
    required_refs: list[dict[str, Any]],
    observed_refs: list[dict[str, Any]],
) -> str | None:
    observed = {str(item["ref"]) for item in observed_refs}
    for item in required_refs:
        ref = str(item["ref"])
        if ref not in observed:
            return ref
    return None


def _current_stage(stages: list[dict[str, Any]]) -> dict[str, Any]:
    furthest_observed_index = max(
        (
            index
            for index, stage in enumerate(stages)
            if stage["observed_artifact_refs"]
        ),
        default=-1,
    )
    if furthest_observed_index >= 0:
        for stage in stages[: furthest_observed_index + 1]:
            if not stage["observed_artifact_refs"]:
                return stage
        next_index = min(furthest_observed_index + 1, len(stages) - 1)
        return stages[next_index]
    for stage in stages:
        if stage["artifact_status"] != _STATUS_DELTA:
            return stage
    return stages[-1]


def _current_stage_projection(stage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage_id": stage["stage_id"],
        "artifact_status": stage["artifact_status"],
        "stage_progress_status": stage["stage_progress_status"],
        "next_missing_surface": stage["next_missing_surface"],
    }


def _next_owner_action(stage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "owner": stage["stage_id"],
        "action_type": "materialize_stage_artifact_delta",
        "required_output_surface": stage["next_missing_surface"],
        "artifact_first_authority": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
    }


def _provider_liveness(*, study_root: Path) -> dict[str, Any]:
    runtime_ref = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    return {
        "runtime_ref": str(runtime_ref),
        "runtime_ref_exists": runtime_ref.exists(),
        "provider_completion_is_paper_progress": False,
        "paper_progress_source": "stage_artifact_index",
    }


def _stale_platform_repairs(*, study_root: Path, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    has_artifact_delta = any(stage["observed_artifact_refs"] for stage in stages)
    if not has_artifact_delta:
        return []
    candidates = (
        ("controller_decisions/latest.json", study_root / "artifacts" / "controller_decisions" / "latest.json"),
        ("publication_eval/latest.json", study_root / "artifacts" / "publication_eval" / "latest.json"),
        (
            "runtime/provider_liveness",
            study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        ),
    )
    return [
        {
            "source": source,
            "ref": str(path),
            "reason": "artifact_delta_takes_precedence_over_platform_currentness",
            "counts_as_paper_progress": False,
        }
        for source, path in candidates
        if path.exists()
    ]


def _authority_boundary() -> dict[str, bool]:
    return {
        "artifact_first_can_determine_stage_progress": True,
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "provider_completion_is_paper_progress": False,
    }


__all__ = [
    "ALLOWED_ARTIFACT_STATUSES",
    "build_stage_artifact_index",
]
