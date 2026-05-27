from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.progress_portal_parts.source_refs import source_ref_allowed


def build_stage_log_summary(
    *,
    explicit: Mapping[str, Any],
    progress: Mapping[str, Any],
    row: Mapping[str, Any] | None,
    stage: str | None,
    source_refs: Iterable[object],
) -> dict[str, Any]:
    explicit_summary = _mapping(
        explicit.get("stage_log_summary")
        or explicit.get("paper_facing_stage_log_summary")
        or progress.get("stage_log_summary")
        or progress.get("paper_facing_stage_log_summary")
    )
    if explicit_summary:
        return _normalize_explicit_stage_log_summary(
            explicit_summary,
            fallback_stage=stage,
            fallback_row=row,
            fallback_source_refs=source_refs,
        )
    return _derived_stage_log_summary(
        progress=progress,
        row=row,
        stage=stage,
        source_refs=source_refs,
    )


def runtime_stage_log_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    summary = _mapping(value)
    return {
        "status": _text(summary.get("status")) or "missing",
        "stage_name": _text(summary.get("stage_name")),
        "current_owner": _text(summary.get("current_owner")),
        "problem_summary": _text(summary.get("problem_summary")),
        "stage_goal": _text(summary.get("stage_goal")),
        "paper_work_done": _string_list(summary.get("paper_work_done")),
        "changed_paper_surfaces": _string_list(summary.get("changed_paper_surfaces")),
        "outcome": _text(summary.get("outcome")),
        "remaining_blockers": _string_list(summary.get("remaining_blockers")),
        "evidence_refs": _dedupe_refs(summary.get("evidence_refs") or []),
        "language_boundary": _mapping(summary.get("language_boundary")) or _language_boundary(),
        "authority": _mapping(summary.get("authority")) or _authority(),
    }


def _normalize_explicit_stage_log_summary(
    value: Mapping[str, Any],
    *,
    fallback_stage: str | None,
    fallback_row: Mapping[str, Any] | None,
    fallback_source_refs: Iterable[object],
) -> dict[str, Any]:
    row = _mapping(fallback_row)
    next_owner = _mapping(row.get("next_owner"))
    return {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "schema_version": 1,
        "status": _text(value.get("status")) or "available",
        "stage_name": _text(value.get("stage_name")) or _text(value.get("current_stage")) or fallback_stage,
        "current_owner": _text(value.get("current_owner")) or _text(value.get("owner")) or _text(next_owner.get("owner")),
        "problem_summary": _text(value.get("problem_summary")),
        "stage_goal": _text(value.get("stage_goal")),
        "paper_work_done": _string_list(value.get("paper_work_done")),
        "changed_paper_surfaces": _string_list(value.get("changed_paper_surfaces")),
        "outcome": _text(value.get("outcome")),
        "remaining_blockers": _string_list(value.get("remaining_blockers")) or _string_list(row.get("blockers")),
        "evidence_refs": _dedupe_refs(
            [
                *_string_list(value.get("evidence_refs")),
                *_string_list(value.get("source_refs")),
                *fallback_source_refs,
            ]
        ),
        "language_boundary": _language_boundary(),
        "authority": _authority(),
    }


def _derived_stage_log_summary(
    *,
    progress: Mapping[str, Any],
    row: Mapping[str, Any] | None,
    stage: str | None,
    source_refs: Iterable[object],
) -> dict[str, Any]:
    normalized_row = _mapping(row)
    evidence = _first_mapping(
        progress.get("repair_execution_evidence"),
        _mapping(progress.get("quality_repair_batch_followthrough")).get("repair_execution_evidence"),
        _mapping(progress.get("quality_repair_batch")).get("repair_execution_evidence"),
        _mapping(progress.get("latest_quality_repair_batch")).get("repair_execution_evidence"),
    )
    quality_repair = _first_mapping(
        progress.get("quality_repair_batch_followthrough"),
        progress.get("quality_repair_batch"),
        progress.get("latest_quality_repair_batch"),
    )
    user_visible = _mapping(progress.get("user_visible_projection"))
    paper_asset_delta = _mapping(normalized_row.get("paper_asset_delta"))
    canonical_delta = _mapping(evidence.get("canonical_artifact_delta"))
    manuscript_hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    next_owner = _mapping(normalized_row.get("next_owner"))
    changed_surfaces = _changed_paper_surfaces(
        paper_asset_delta=paper_asset_delta,
        canonical_delta=canonical_delta,
        evidence=evidence,
    )
    blockers = _dedupe_texts(
        [
            *_string_list(normalized_row.get("blockers")),
            *_string_list(evidence.get("blockers")),
            *_string_list(manuscript_hygiene.get("blockers")),
        ]
    )
    evidence_refs = _dedupe_refs(
        [
            *source_refs,
            *_string_list(evidence.get("source_refs")),
            *_paths_from_ref_dicts(canonical_delta.get("artifact_refs")),
            _text(evidence.get("evidence_ledger_ref")),
            _text(evidence.get("review_ledger_ref")),
            _text(evidence.get("ai_reviewer_recheck_request_ref")),
            _text(quality_repair.get("latest_record_path")),
            _text(quality_repair.get("repair_execution_evidence_path")),
        ]
    )
    return {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "schema_version": 1,
        "status": "available" if evidence or normalized_row else "missing",
        "stage_name": stage,
        "current_owner": _text(next_owner.get("owner")) or _text(quality_repair.get("next_owner")),
        "problem_summary": _first_text(
            user_visible.get("current_stage_summary"),
            user_visible.get("state_summary"),
            quality_repair.get("summary"),
        ),
        "stage_goal": _first_text(
            user_visible.get("next_system_action"),
            quality_repair.get("next_confirmation_signal"),
        ),
        "paper_work_done": _paper_work_done(
            evidence=evidence,
            paper_asset_delta=paper_asset_delta,
            quality_repair=quality_repair,
        ),
        "changed_paper_surfaces": changed_surfaces,
        "outcome": _outcome(evidence=evidence, quality_repair=quality_repair),
        "remaining_blockers": blockers,
        "evidence_refs": evidence_refs,
        "language_boundary": _language_boundary(),
        "authority": _authority(),
    }


def _paper_work_done(
    *,
    evidence: Mapping[str, Any],
    paper_asset_delta: Mapping[str, Any],
    quality_repair: Mapping[str, Any],
) -> list[str]:
    explicit = _string_list(quality_repair.get("paper_work_done"))
    if explicit:
        return explicit
    result: list[str] = []
    for delta_type in _string_list(paper_asset_delta.get("delta_types")):
        result.append(f"{delta_type} surface updated")
    canonical_delta = _mapping(evidence.get("canonical_artifact_delta"))
    if canonical_delta.get("meaningful_artifact_delta") is True:
        result.append("canonical paper evidence delta recorded")
    if evidence.get("evidence_ledger_update_done") is True:
        result.append("evidence ledger updated")
    if evidence.get("review_ledger_update_done") is True:
        result.append("review ledger updated")
    if evidence.get("ai_reviewer_recheck_done") is True:
        result.append("AI reviewer recheck request recorded")
    return _dedupe_texts(result)


def _changed_paper_surfaces(
    *,
    paper_asset_delta: Mapping[str, Any],
    canonical_delta: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> list[str]:
    return _dedupe_refs(
        [
            *_string_list(paper_asset_delta.get("refs")),
            *_paths_from_ref_dicts(canonical_delta.get("artifact_refs")),
            _text(evidence.get("evidence_ledger_ref")),
            _text(evidence.get("review_ledger_ref")),
        ]
    )


def _outcome(*, evidence: Mapping[str, Any], quality_repair: Mapping[str, Any]) -> str | None:
    status = _text(evidence.get("status")) or _text(quality_repair.get("status"))
    if status == "progress_delta_candidate":
        return "paper_progress_delta_recorded"
    if status == "controller_progress_delta_candidate":
        return "controller_progress_delta_recorded"
    if status == "handoff_ready":
        return "writer_handoff_ready"
    if status == "pending":
        return "pending_required_followthrough"
    return status


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        mapped = _mapping(value)
        if mapped:
            return mapped
    return {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _paths_from_ref_dicts(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    paths: list[str] = []
    for item in value:
        mapped = _mapping(item)
        if path := _text(mapped.get("path")):
            paths.append(path)
    return paths


def _authority() -> dict[str, Any]:
    return {
        "kind": "read_only_paper_facing_stage_log_projection",
        "writes_authority_surface": False,
        "truth_owner": "MedAutoScience",
        "can_write_paper": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def _language_boundary() -> dict[str, Any]:
    return {
        "paper_body_included": False,
        "paper_body_target": False,
        "internal_review_language_allowed_in_paper_body": False,
        "summary_scope": "stage_log_read_model_only",
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _dedupe_refs(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text is None or text in seen or not source_ref_allowed(text):
            continue
        seen.add(text)
        result.append(text)
    return result


def _dedupe_texts(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "build_stage_log_summary",
    "runtime_stage_log_summary",
]
