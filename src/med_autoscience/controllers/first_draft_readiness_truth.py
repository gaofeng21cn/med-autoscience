from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import medical_paper_readiness
from med_autoscience.medical_manuscript_blueprint import stable_medical_manuscript_blueprint_path
from med_autoscience.medical_prose_review import stable_medical_prose_review_path

__all__ = [
    "build_first_draft_readiness_truth",
    "read_first_draft_readiness_truth",
    "stable_first_draft_readiness_truth_path",
]


_SURFACE = "first_draft_readiness_truth"
_SCHEMA_VERSION = 1
_RELATIVE_PATH = Path("artifacts/medical_paper/first_draft_readiness_truth.json")
_REVIEW_LEDGER_CANDIDATES = (
    Path("paper/review/review_ledger.json"),
    Path("paper/review_ledger.json"),
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "not_json_object"
    return payload, None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_first_draft_readiness_truth_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / _RELATIVE_PATH).resolve()


def _payload_status(payload: Mapping[str, Any] | None) -> str:
    if payload is None:
        return ""
    return _text(payload.get("status") or payload.get("overall_status") or payload.get("readiness_status"))


def _ledger_closed(payload: Mapping[str, Any] | None) -> bool:
    if payload is None:
        return False
    status = _payload_status(payload)
    if status == "closed":
        return True
    concerns = _list(payload.get("concerns"))
    if concerns:
        return all(
            isinstance(item, Mapping) and _text(item.get("status")) in {"resolved", "closed"}
            for item in concerns
        )
    closures = _list(payload.get("charter_expectation_closures") or payload.get("closures"))
    if closures:
        return all(
            isinstance(item, Mapping) and _text(item.get("status")) == "closed"
            for item in closures
        )
    return False


def _surface_ref(
    *,
    path: Path,
    payload: Mapping[str, Any] | None,
    read_error: str | None,
    ready: bool,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "ready": ready,
    }
    if read_error is not None:
        ref["read_error"] = read_error
    status = _payload_status(payload)
    if status:
        ref["status"] = status
    return ref


def _blueprint_ready(payload: Mapping[str, Any] | None) -> bool:
    if payload is None:
        return False
    provenance = _mapping(payload.get("authoring_provenance"))
    status = _payload_status(payload)
    return (
        payload.get("canonical_ready") is True
        and (not status or status == "closed")
        and _text(provenance.get("owner")) in {"ai_author", "ai_reviewer"}
        and provenance.get("ai_reviewer_required") is False
    )


def _prose_review_ready(payload: Mapping[str, Any] | None) -> bool:
    if payload is None:
        return False
    quality = _mapping(payload.get("medical_journal_prose_quality"))
    route_back = _mapping(quality.get("route_back_recommendation"))
    return _text(quality.get("status")) == "ready" and route_back.get("required") is False


def _read_review_ledger(study_root: Path) -> tuple[Path, dict[str, Any] | None, str | None]:
    for relative_path in _REVIEW_LEDGER_CANDIDATES:
        path = study_root / relative_path
        payload, error = _read_json(path)
        if error == "missing":
            continue
        return path, payload, error
    return study_root / _REVIEW_LEDGER_CANDIDATES[0], None, "missing"


def _missing_required_surfaces(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for item in _list(readiness.get("capability_surfaces")):
        if not isinstance(item, Mapping):
            continue
        if item.get("required_for_ready") and _text(item.get("status")) != "present":
            missing.append(
                {
                    "surface_key": _text(item.get("surface_key")),
                    "status": _text(item.get("status")) or "missing",
                    "missing_reason": _text(item.get("missing_reason")),
                    "artifact_path": _text(item.get("artifact_path")),
                }
            )
    return missing


def build_first_draft_readiness_truth(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()

    readiness = medical_paper_readiness.build_medical_paper_readiness_surface(
        study_root=resolved_study_root
    )
    blueprint_path = stable_medical_manuscript_blueprint_path(study_root=resolved_study_root)
    blueprint, blueprint_error = _read_json(blueprint_path)
    prose_path = stable_medical_prose_review_path(study_root=resolved_study_root)
    prose_review, prose_error = _read_json(prose_path)
    review_ledger_path, review_ledger, review_ledger_error = _read_review_ledger(resolved_study_root)

    readiness_ready = readiness.get("overall_status") == "ready"
    blueprint_ready = _blueprint_ready(blueprint)
    prose_ready = _prose_review_ready(prose_review)
    review_ledger_ready = _ledger_closed(review_ledger)

    blockers: list[str] = []
    if not readiness_ready:
        blockers.append("medical_paper_readiness_not_ready")
    if not blueprint_ready:
        blockers.append("medical_manuscript_blueprint_not_ready")
    if not prose_ready:
        blockers.append("medical_prose_review_not_ready")
    if not review_ledger_ready:
        blockers.append("review_ledger_not_closed")

    status = "first_draft_ready" if not blockers else "blocked"
    payload = {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "status": status,
        "first_draft_ready": status == "first_draft_ready",
        "single_study": True,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "blockers": blockers,
        "readiness_inputs": {
            "medical_paper_readiness": {
                "surface": readiness.get("surface"),
                "overall_status": readiness.get("overall_status"),
                "ready_count": readiness.get("ready_count"),
                "required_count": readiness.get("required_count"),
                "missing_required_surfaces": _missing_required_surfaces(readiness),
                "artifact_path": str(
                    medical_paper_readiness.stable_medical_paper_readiness_path(
                        study_root=resolved_study_root
                    )
                ),
            },
            "medical_manuscript_blueprint": _surface_ref(
                path=blueprint_path,
                payload=blueprint,
                read_error=blueprint_error,
                ready=blueprint_ready,
            ),
            "medical_prose_review": _surface_ref(
                path=prose_path,
                payload=prose_review,
                read_error=prose_error,
                ready=prose_ready,
            ),
            "review_ledger": _surface_ref(
                path=review_ledger_path,
                payload=review_ledger,
                read_error=review_ledger_error,
                ready=review_ledger_ready,
            ),
        },
        "next_action": (
            {
                "action_id": "start_first_full_draft",
                "summary": "single-study 首稿 readiness truth 已闭合，可进入 first full draft。",
            }
            if status == "first_draft_ready"
            else {
                "action_id": "complete_first_draft_readiness_inputs",
                "summary": "补齐 first draft readiness truth 的阻塞输入后再进入首稿。",
            }
        ),
    }
    _write_json(stable_first_draft_readiness_truth_path(study_root=resolved_study_root), payload)
    return payload


def read_first_draft_readiness_truth(*, study_root: str | Path) -> dict[str, Any]:
    payload, error = _read_json(
        stable_first_draft_readiness_truth_path(study_root=Path(study_root))
    )
    if error is not None or payload is None:
        raise FileNotFoundError(stable_first_draft_readiness_truth_path(study_root=Path(study_root)))
    return payload
