from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.policies import DEFAULT_PUBLICATION_CRITIQUE_POLICY
from med_autoscience.publication_eval_record import PublicationEvalRecord
from med_autoscience.publication_eval_reviewer_os import validate_ai_reviewer_operating_system_trace

__all__ = [
    "STABLE_PUBLICATION_EVAL_LATEST_RELATIVE_PATH",
    "materialize_ai_reviewer_publication_eval_latest",
    "materialize_publication_eval_latest",
    "read_publication_eval_latest",
    "resolve_publication_eval_latest_ref",
    "stable_publication_eval_latest_path",
]


STABLE_PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
_LEGACY_AI_REVIEWER_RECHECK_BUNDLE_STAGE_VERDICTS = frozenset(
    {
        "review_owner_clear_for_bundle_stage",
    }
)
_LEGACY_AI_REVIEWER_RECHECK_PRIMARY_CLAIM_STATUSES = {
    "supported_with_limitations": "partial",
}


def stable_publication_eval_latest_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_PUBLICATION_EVAL_LATEST_RELATIVE_PATH).resolve()


def resolve_publication_eval_latest_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_publication_eval_latest_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("publication eval latest reader only accepts the eval-owned latest artifact")
    return stable_path


def read_publication_eval_latest(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    latest_path = resolve_publication_eval_latest_ref(study_root=study_root, ref=ref)
    payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"publication eval latest payload must be a JSON object: {latest_path}")
    payload = _normalize_legacy_ai_reviewer_recheck_payload(payload)
    return PublicationEvalRecord.from_payload(payload).to_dict()


def materialize_publication_eval_latest(
    *,
    study_root: Path,
    record: PublicationEvalRecord | dict[str, Any],
) -> dict[str, str]:
    normalized_record = (
        record
        if isinstance(record, PublicationEvalRecord)
        else PublicationEvalRecord.from_payload(record)
    )
    latest_path = stable_publication_eval_latest_path(study_root=study_root)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(normalized_record.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "eval_id": normalized_record.eval_id,
        "artifact_path": str(latest_path),
    }


def _normalize_legacy_ai_reviewer_recheck_payload(payload: dict[str, Any]) -> dict[str, Any]:
    provenance = payload.get("assessment_provenance")
    verdict = payload.get("verdict")
    if not isinstance(provenance, dict) or not isinstance(verdict, dict):
        return payload
    if provenance.get("owner") != "ai_reviewer":
        return payload
    if provenance.get("source_kind") != "publication_eval_ai_reviewer_recheck":
        return payload
    if provenance.get("ai_reviewer_required") is not False:
        return payload
    overall_verdict = str(verdict.get("overall_verdict") or "").strip()
    if overall_verdict not in _LEGACY_AI_REVIEWER_RECHECK_BUNDLE_STAGE_VERDICTS:
        return payload

    normalized_payload = dict(payload)
    normalized_verdict = dict(verdict)
    normalized_verdict["overall_verdict"] = "promising"
    primary_claim_status = str(normalized_verdict.get("primary_claim_status") or "").strip()
    normalized_verdict["primary_claim_status"] = _LEGACY_AI_REVIEWER_RECHECK_PRIMARY_CLAIM_STATUSES.get(
        primary_claim_status,
        primary_claim_status,
    )
    normalized_payload["verdict"] = normalized_verdict
    if "mechanical_projection_used_as_quality_authority" not in provenance:
        normalized_provenance = dict(provenance)
        normalized_provenance["mechanical_projection_used_as_quality_authority"] = False
        normalized_payload["assessment_provenance"] = normalized_provenance
    normalized_payload["recommended_actions"] = [
        _normalize_legacy_ai_reviewer_recheck_action(action)
        for action in (payload.get("recommended_actions") or [])
        if isinstance(action, dict)
    ]
    return normalized_payload


def _normalize_legacy_ai_reviewer_recheck_action(action: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(action)
    if normalized.get("requires_controller_decision") is not True:
        normalized["requires_controller_decision"] = True
    return normalized


def materialize_ai_reviewer_publication_eval_latest(
    *,
    study_root: Path,
    record: PublicationEvalRecord | dict[str, Any],
) -> dict[str, str]:
    normalized_record = (
        record
        if isinstance(record, PublicationEvalRecord)
        else PublicationEvalRecord.from_payload(record)
    )
    payload = normalized_record.to_dict()
    provenance = payload["assessment_provenance"]
    if provenance["owner"] != "ai_reviewer":
        raise ValueError("AI reviewer publication eval must declare assessment_provenance.owner=ai_reviewer")
    if provenance["source_kind"] != "publication_eval_ai_reviewer":
        raise ValueError("AI reviewer publication eval must declare assessment_provenance.source_kind=publication_eval_ai_reviewer")
    if provenance["ai_reviewer_required"] is not False:
        raise ValueError("AI reviewer publication eval cannot still require AI reviewer judgment")
    if provenance["policy_id"] != DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]:
        raise ValueError(
            f"AI reviewer publication eval policy_id must be {DEFAULT_PUBLICATION_CRITIQUE_POLICY['policy_id']}"
        )
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, dict):
        raise ValueError("AI reviewer publication eval must include quality_assessment")
    prose_quality = quality_assessment.get("medical_journal_prose_quality")
    if not isinstance(prose_quality, dict):
        raise ValueError("AI reviewer publication eval must include quality_assessment.medical_journal_prose_quality")
    if not str(prose_quality.get("summary") or "").strip():
        raise ValueError("AI reviewer publication eval medical_journal_prose_quality.summary must be non-empty")
    reviewer_os_errors = validate_ai_reviewer_operating_system_trace(payload.get("reviewer_operating_system"))
    if reviewer_os_errors:
        raise ValueError("AI reviewer publication eval reviewer_operating_system invalid: " + "; ".join(reviewer_os_errors))
    return materialize_publication_eval_latest(study_root=study_root, record=normalized_record)
