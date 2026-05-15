from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.medical_prose_review import read_medical_prose_review
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.publication_eval_reviewer_os import validate_ai_reviewer_operating_system_trace

__all__ = ["build_ai_reviewer_runtime_workflow_state"]


_REVIEW_LEDGER_CANDIDATES = (
    Path("paper/review/review_ledger.json"),
    Path("paper/review_ledger.json"),
)
_EVIDENCE_LEDGER_RELATIVE_PATH = Path("paper/evidence_ledger.json")
_POLICY_ID = "medical_publication_critique_v1"
_AUTHORIZATION_READY_REASON = (
    "AI reviewer publication eval, medical prose review, review ledger, and evidence ledger are closed."
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _ref_payload(*, study_root: Path, relative_path: Path, present: bool, valid: bool) -> dict[str, Any]:
    path = (study_root / relative_path).resolve()
    return {
        "path": str(path),
        "relative_path": relative_path.as_posix(),
        "present": present,
        "valid": valid,
    }


def _ledger_is_closed(payload: Mapping[str, Any]) -> bool:
    status = _text(payload.get("status"))
    if status is not None and status != "closed":
        return False
    closed_signal_present = status == "closed"
    closure_items = _list(payload.get("charter_expectation_closures"))
    if closure_items:
        closed_signal_present = True
        for item in closure_items:
            if isinstance(item, Mapping) and _text(item.get("status")) != "closed":
                return False
    concerns = _list(payload.get("concerns"))
    if concerns:
        closed_signal_present = True
        for concern in concerns:
            if isinstance(concern, Mapping) and _text(concern.get("status")) not in {"resolved", "closed"}:
                return False
    return closed_signal_present


def _read_ledger(
    *,
    study_root: Path,
    relative_paths: tuple[Path, ...],
) -> tuple[Mapping[str, Any] | None, Path, str | None]:
    selected = relative_paths[0]
    for relative_path in relative_paths:
        path = study_root / relative_path
        if not path.exists():
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            return None, relative_path, f"invalid_json:{exc.__class__.__name__}"
        if not isinstance(payload, Mapping):
            return None, relative_path, "payload_not_object"
        return payload, relative_path, None
    return None, selected, "missing"


def _publication_eval_authorized(payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(payload.get("assessment_provenance"))
    quality_assessment = _mapping(payload.get("quality_assessment"))
    prose_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    reviewer_os = payload.get("reviewer_operating_system")
    return (
        provenance.get("owner") == "ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
        and provenance.get("policy_id") == _POLICY_ID
        and bool(_text(prose_quality.get("summary")))
        and _text(prose_quality.get("status")) == "ready"
        and not validate_ai_reviewer_operating_system_trace(reviewer_os)
    )


def _medical_prose_review_route_back(payload: Mapping[str, Any]) -> dict[str, Any]:
    quality = _mapping(payload.get("medical_journal_prose_quality"))
    route = _mapping(quality.get("route_back_recommendation"))
    required = route.get("required") is True
    return {
        "required": required,
        "target": _text(route.get("route_target")) if required else None,
        "reason": _text(route.get("reason")) if required else None,
        "source": "medical_prose_review" if required else None,
    }


def _authorization(*, authorized: bool, status: str) -> dict[str, Any]:
    if authorized:
        return {
            "authorized": True,
            "status": "authorized",
            "reason": _AUTHORIZATION_READY_REASON,
        }
    return {
        "authorized": False,
        "status": status,
        "reason": "AI reviewer workflow is not closed for finalize/submission authorization.",
    }


def build_ai_reviewer_runtime_workflow_state(study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    blockers: list[str] = []

    try:
        publication_eval = read_publication_eval_latest(study_root=resolved_study_root)
        publication_eval_present = True
        publication_eval_valid = True
    except FileNotFoundError:
        publication_eval = {}
        publication_eval_present = False
        publication_eval_valid = False
        blockers.append("publication_eval_missing")
    except (ValueError, TypeError, json.JSONDecodeError):
        publication_eval = {}
        publication_eval_present = True
        publication_eval_valid = False
        blockers.append("publication_eval_invalid")

    try:
        medical_prose_review = read_medical_prose_review(study_root=resolved_study_root)
        medical_prose_present = True
        medical_prose_valid = True
    except FileNotFoundError:
        medical_prose_review = {}
        medical_prose_present = False
        medical_prose_valid = False
        blockers.append("medical_prose_review_missing")
    except (ValueError, TypeError, json.JSONDecodeError):
        medical_prose_review = {}
        medical_prose_present = True
        medical_prose_valid = False
        blockers.append("medical_prose_review_invalid")

    review_ledger, review_ledger_relative_path, review_ledger_error = _read_ledger(
        study_root=resolved_study_root,
        relative_paths=_REVIEW_LEDGER_CANDIDATES,
    )
    review_ledger_present = review_ledger_error != "missing"
    review_ledger_valid = review_ledger is not None
    review_ledger_closed = bool(review_ledger and _ledger_is_closed(review_ledger))
    if review_ledger_error == "missing":
        blockers.append("review_ledger_missing")
    elif not review_ledger_valid:
        blockers.append("review_ledger_invalid")
    elif not review_ledger_closed:
        blockers.append("review_ledger_not_closed")

    evidence_ledger, evidence_ledger_relative_path, evidence_ledger_error = _read_ledger(
        study_root=resolved_study_root,
        relative_paths=(_EVIDENCE_LEDGER_RELATIVE_PATH,),
    )
    evidence_ledger_present = evidence_ledger_error != "missing"
    evidence_ledger_valid = evidence_ledger is not None
    evidence_ledger_closed = bool(evidence_ledger and _ledger_is_closed(evidence_ledger))
    if evidence_ledger_error == "missing":
        blockers.append("evidence_ledger_missing")
    elif not evidence_ledger_valid:
        blockers.append("evidence_ledger_invalid")
    elif not evidence_ledger_closed:
        blockers.append("evidence_ledger_not_closed")

    publication_eval_ai_authorized = bool(publication_eval_valid and _publication_eval_authorized(publication_eval))
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    assessment_owner = _text(provenance.get("owner")) or "mechanical_projection"
    quality_assessment = _mapping(publication_eval.get("quality_assessment"))
    prose_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    prose_quality_status = _text(prose_quality.get("status"))
    if publication_eval_valid and not publication_eval_ai_authorized:
        blockers.append("publication_eval_not_ai_reviewer_authority")
        if assessment_owner == "ai_reviewer" and prose_quality_status and prose_quality_status != "ready":
            blockers.append("medical_journal_prose_quality_not_ready")

    route_back = (
        _medical_prose_review_route_back(medical_prose_review)
        if medical_prose_valid
        else {"required": False, "target": None, "reason": None, "source": None}
    )
    if route_back["required"]:
        blockers.append("medical_prose_review_route_back_required")

    workflow_authorized = (
        publication_eval_ai_authorized
        and medical_prose_valid
        and not route_back["required"]
        and review_ledger_closed
        and evidence_ledger_closed
    )
    if assessment_owner == "mechanical_projection":
        authority_state = "projection_only"
        authorization_status = "review_required"
        if not route_back["required"]:
            route_back = {
                "required": True,
                "target": "ai_reviewer",
                "reason": "Mechanical publication eval cannot authorize finalize/submission quality closure.",
                "source": "publication_eval",
            }
    elif workflow_authorized:
        authority_state = "authorized"
        authorization_status = "authorized"
    else:
        authority_state = "review_required"
        authorization_status = "review_required"

    return {
        "surface": "ai_reviewer_runtime_workflow_state",
        "schema_version": 1,
        "quality_authority": {
            "owner": assessment_owner,
            "state": authority_state,
            "policy_id": _text(provenance.get("policy_id")),
            "ai_reviewer_required": not publication_eval_ai_authorized,
            "mechanical_projection_can_authorize_quality": False,
        },
        "finalize_authorization": _authorization(
            authorized=workflow_authorized,
            status=authorization_status,
        ),
        "submission_authorization": _authorization(
            authorized=workflow_authorized,
            status=authorization_status,
        ),
        "route_back": route_back,
        "blockers": blockers,
        "refs": {
            "publication_eval": _ref_payload(
                study_root=resolved_study_root,
                relative_path=Path("artifacts/publication_eval/latest.json"),
                present=publication_eval_present,
                valid=publication_eval_valid,
            ),
            "medical_prose_review": _ref_payload(
                study_root=resolved_study_root,
                relative_path=Path("artifacts/publication_eval/medical_prose_review.json"),
                present=medical_prose_present,
                valid=medical_prose_valid,
            ),
            "review_ledger": _ref_payload(
                study_root=resolved_study_root,
                relative_path=review_ledger_relative_path,
                present=review_ledger_present,
                valid=review_ledger_valid and review_ledger_closed,
            ),
            "evidence_ledger": _ref_payload(
                study_root=resolved_study_root,
                relative_path=evidence_ledger_relative_path,
                present=evidence_ledger_present,
                valid=evidence_ledger_valid and evidence_ledger_closed,
            ),
        },
    }
