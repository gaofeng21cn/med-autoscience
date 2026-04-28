from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience import study_task_intake
from med_autoscience.evaluation_summary import (
    read_evaluation_summary,
    resolve_evaluation_summary_ref,
)
from med_autoscience.publication_eval_latest import (
    read_publication_eval_latest,
    resolve_publication_eval_latest_ref,
)
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.study_decision_record import (
    StudyDecisionCharterRef,
    StudyDecisionPublicationEvalRef,
)


def _resolve_charter_ref(
    *,
    study_root: Path,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
) -> StudyDecisionCharterRef:
    normalized_ref = (
        charter_ref
        if isinstance(charter_ref, StudyDecisionCharterRef)
        else StudyDecisionCharterRef.from_payload(charter_ref)
    )
    charter_path = resolve_study_charter_ref(study_root=study_root, ref=normalized_ref.artifact_path)
    charter_payload = read_study_charter(study_root=study_root, ref=charter_path)
    charter_id = str(charter_payload.get("charter_id") or "").strip()
    if charter_id != normalized_ref.charter_id:
        raise ValueError("study_outer_loop_tick charter_id mismatch against stable study charter artifact")
    return StudyDecisionCharterRef(charter_id=charter_id, artifact_path=str(charter_path))


def _resolve_publication_eval_ref(
    *,
    study_root: Path,
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
) -> StudyDecisionPublicationEvalRef:
    normalized_ref = (
        publication_eval_ref
        if isinstance(publication_eval_ref, StudyDecisionPublicationEvalRef)
        else StudyDecisionPublicationEvalRef.from_payload(publication_eval_ref)
    )
    publication_eval_path = resolve_publication_eval_latest_ref(
        study_root=study_root,
        ref=normalized_ref.artifact_path,
    )
    publication_eval_payload = read_publication_eval_latest(study_root=study_root, ref=publication_eval_path)
    eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    return StudyDecisionPublicationEvalRef(eval_id=eval_id, artifact_path=str(publication_eval_path))


def _read_evaluation_summary_payload(*, study_root: Path) -> dict[str, Any] | None:
    summary_path = resolve_evaluation_summary_ref(study_root=study_root)
    if not summary_path.exists():
        return None
    try:
        summary_payload = read_evaluation_summary(study_root=study_root, ref=summary_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        raw_payload = json.loads(summary_path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw_payload, dict):
            return None
        summary_payload = raw_payload
    return summary_payload


def _read_latest_publication_eval_payload(*, study_root: Path) -> tuple[Path, dict[str, Any]] | None:
    publication_eval_path = resolve_publication_eval_latest_ref(study_root=study_root)
    if not publication_eval_path.exists():
        return None
    publication_eval_payload = read_publication_eval_latest(study_root=study_root, ref=publication_eval_path)
    return publication_eval_path, publication_eval_payload


def _read_publication_eval_payload(*, study_root: Path, ref: str | Path) -> dict[str, Any]:
    return read_publication_eval_latest(study_root=study_root, ref=ref)


def _build_study_decision_charter_ref(*, study_root: Path, missing_message: str) -> StudyDecisionCharterRef:
    charter_path = resolve_study_charter_ref(study_root=study_root)
    if not charter_path.exists():
        raise ValueError(missing_message)
    charter_payload = read_study_charter(study_root=study_root, ref=charter_path)
    return StudyDecisionCharterRef(
        charter_id=str(charter_payload.get("charter_id") or "").strip(),
        artifact_path=str(charter_path),
    )


def _latest_task_intake_yields_to_fast_lane_closeout(*, study_root: Path) -> bool:
    return study_task_intake.latest_task_intake_yields_to_manuscript_fast_lane_closeout(study_root=study_root)
