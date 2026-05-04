from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

AI_REVIEWER_REQUEST_STATES = ("requested", "assigned", "assessment_written", "blocked", "stale")
AI_REVIEWER_REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/ai_reviewer/latest.json")
AI_REVIEWER_REQUIRED_INPUT_SURFACES = (
    "manuscript",
    "evidence_ledger",
    "review_ledger",
    "study_charter",
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _ref_payload(*, study_root: Path, surface: str, relative_path: Path) -> dict[str, Any]:
    path = (study_root / relative_path).resolve()
    return {
        "surface": surface,
        "relative_path": relative_path.as_posix(),
        "path": str(path),
        "required": True,
        "present": path.exists(),
        "valid": path.exists(),
    }


def default_ai_reviewer_request_input_refs(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    return {
        "manuscript": _ref_payload(
            study_root=resolved_study_root,
            surface="manuscript",
            relative_path=Path("paper/manuscript.md"),
        ),
        "evidence_ledger": _ref_payload(
            study_root=resolved_study_root,
            surface="evidence_ledger",
            relative_path=Path("paper/evidence_ledger.json"),
        ),
        "review_ledger": _ref_payload(
            study_root=resolved_study_root,
            surface="review_ledger",
            relative_path=Path("paper/review/review_ledger.json"),
        ),
        "study_charter": _ref_payload(
            study_root=resolved_study_root,
            surface="study_charter",
            relative_path=Path("artifacts/controller/study_charter.json"),
        ),
    }


def stable_ai_reviewer_request_path(*, study_root: str | Path) -> Path:
    return Path(study_root).expanduser().resolve() / AI_REVIEWER_REQUEST_RELATIVE_PATH


def read_ai_reviewer_request(*, study_root: str | Path) -> dict[str, Any] | None:
    path = stable_ai_reviewer_request_path(study_root=study_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def materialize_ai_reviewer_request(
    *,
    study_root: str | Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    path = stable_ai_reviewer_request_path(study_root=study_root)
    payload = dict(packet)
    payload["path"] = str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _publication_eval_ai_reviewer_owned(publication_eval_payload: Mapping[str, Any] | None) -> bool:
    provenance = _mapping((publication_eval_payload or {}).get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "ai_reviewer"
        and _text(provenance.get("source_kind")) == "publication_eval_ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
    )


def _input_contract(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(packet.get("input_contract"))


def _required_inputs(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_input_contract(packet).get("required_refs"))


def _input_blockers(packet: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    refs = _required_inputs(packet)
    for surface in AI_REVIEWER_REQUIRED_INPUT_SURFACES:
        ref = _mapping(refs.get(surface))
        if not ref:
            blockers.append(f"{surface}_ref_missing")
            continue
        has_ref_target = bool(_text(ref.get("path")) or _text(ref.get("relative_path")) or _text(ref.get("ref")))
        if not has_ref_target:
            blockers.append(f"{surface}_ref_missing")
        elif ref.get("present") is False:
            blockers.append(f"{surface}_missing")
        elif ref.get("valid") is False:
            blockers.append(f"{surface}_invalid")
    return blockers


def project_ai_reviewer_request_lifecycle(
    *,
    study_root: str | Path,
    publication_eval_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    packet = read_ai_reviewer_request(study_root=study_root)
    if packet is None:
        return None

    requested_state = _text(_mapping(packet.get("request_lifecycle")).get("state")) or "requested"
    if requested_state not in AI_REVIEWER_REQUEST_STATES:
        requested_state = "requested"
    input_blockers = _input_blockers(packet)
    output_written = _publication_eval_ai_reviewer_owned(publication_eval_payload)

    if output_written:
        state = "assessment_written"
    elif input_blockers:
        state = "blocked"
    elif requested_state in {"assigned", "stale"}:
        state = requested_state
    else:
        state = "requested"

    return {
        "surface": "ai_reviewer_request_lifecycle",
        "schema_version": 1,
        "authority": "observability_only",
        "request_id": packet.get("request_id"),
        "request_kind": packet.get("request_kind"),
        "state": state,
        "requested_state": requested_state,
        "allowed_states": list(AI_REVIEWER_REQUEST_STATES),
        "request_owner": packet.get("request_owner"),
        "assigned_to": _mapping(packet.get("request_lifecycle")).get("assigned_to"),
        "input_contract": dict(_input_contract(packet)),
        "required_output": dict(_mapping(packet.get("required_output") or packet.get("requested_artifact"))),
        "blockers": input_blockers or list(packet.get("blockers") if isinstance(packet.get("blockers"), list) else []),
        "assessment_written": output_written,
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "refs": {
            "request_path": str(stable_ai_reviewer_request_path(study_root=study_root)),
        },
    }
