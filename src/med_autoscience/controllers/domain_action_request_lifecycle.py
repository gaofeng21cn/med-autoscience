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
    "medical_manuscript_blueprint",
    "claim_evidence_map",
    "medical_prose_review",
    "publication_gate_projection",
)
AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES = (
    Path("paper/draft.md"),
    Path("paper/manuscript.md"),
    Path("paper/build/review_manuscript.md"),
)
AI_REVIEWER_MEDICAL_PROSE_REVIEW_REF_CANDIDATES = (
    Path("artifacts/publication_eval/medical_prose_review.json"),
    Path("paper/medical_prose_review.json"),
    Path("paper/review/medical_prose_review.json"),
)
AI_REVIEWER_PUBLICATION_EVAL_RECORD_GLOB = (
    "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
)
AI_REVIEWER_REQUIRED_QUALITY_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
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


def _first_existing_relative_path(*, study_root: Path, candidates: tuple[Path, ...]) -> Path:
    for candidate in candidates:
        if (study_root / candidate).exists():
            return candidate
    return candidates[0]


def _ref_has_target(ref: Mapping[str, Any]) -> bool:
    return bool(_text(ref.get("path")) or _text(ref.get("relative_path")) or _text(ref.get("ref")))


def _candidate_ref_paths(*, study_root: Path, ref: Mapping[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for key in ("path", "relative_path", "ref"):
        target = _text(ref.get(key))
        if not target:
            continue
        candidate = Path(target).expanduser()
        if not candidate.is_absolute():
            candidate = study_root / candidate
        paths.append(candidate.resolve())
    return paths


def _existing_medical_prose_review_ref_payload(*, study_root: Path) -> dict[str, Any] | None:
    for relative_path in AI_REVIEWER_MEDICAL_PROSE_REVIEW_REF_CANDIDATES:
        if (study_root / relative_path).exists():
            return _ref_payload(
                study_root=study_root,
                surface="medical_prose_review",
                relative_path=relative_path,
            )
    return None


def _normalize_medical_prose_review_ref(
    *,
    study_root: Path,
    ref: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(ref)
    existing_targets = [path for path in _candidate_ref_paths(study_root=study_root, ref=payload) if path.exists()]
    if existing_targets:
        path = existing_targets[0]
        try:
            relative_path = path.relative_to(study_root).as_posix()
        except ValueError:
            relative_path = _text(payload.get("relative_path"))
        payload.update(
            {
                "surface": "medical_prose_review",
                "path": str(path),
                "present": True,
                "valid": True,
            }
        )
        if relative_path:
            payload["relative_path"] = relative_path
        return payload

    existing_payload = _existing_medical_prose_review_ref_payload(study_root=study_root)
    if existing_payload is not None:
        return existing_payload
    return payload


def default_ai_reviewer_request_input_refs(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    manuscript_relative_path = _first_existing_relative_path(
        study_root=resolved_study_root,
        candidates=AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES,
    )
    medical_prose_review_relative_path = _first_existing_relative_path(
        study_root=resolved_study_root,
        candidates=AI_REVIEWER_MEDICAL_PROSE_REVIEW_REF_CANDIDATES,
    )
    return {
        "manuscript": _ref_payload(
            study_root=resolved_study_root,
            surface="manuscript",
            relative_path=manuscript_relative_path,
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
        "medical_manuscript_blueprint": _ref_payload(
            study_root=resolved_study_root,
            surface="medical_manuscript_blueprint",
            relative_path=Path("paper/medical_manuscript_blueprint.json"),
        ),
        "claim_evidence_map": _ref_payload(
            study_root=resolved_study_root,
            surface="claim_evidence_map",
            relative_path=Path("paper/claim_evidence_map.json"),
        ),
        "medical_prose_review": _ref_payload(
            study_root=resolved_study_root,
            surface="medical_prose_review",
            relative_path=medical_prose_review_relative_path,
        ),
        "publication_gate_projection": _ref_payload(
            study_root=resolved_study_root,
            surface="publication_gate_projection",
            relative_path=Path("artifacts/publication_eval/latest.json"),
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


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _ai_reviewer_publication_eval_record_valid(payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return False
    if _text(provenance.get("source_kind")) != "publication_eval_ai_reviewer":
        return False
    if provenance.get("ai_reviewer_required") is not False:
        return False
    if not _text(payload.get("eval_id")):
        return False
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, Mapping):
        return False
    for dimension in AI_REVIEWER_REQUIRED_QUALITY_DIMENSIONS:
        if not isinstance(quality_assessment.get(dimension), Mapping):
            return False
    future_plan = payload.get("future_facing_limitations_plan")
    return isinstance(future_plan, list) and bool(future_plan)


def _latest_ai_reviewer_publication_eval_record(
    *,
    study_root: Path,
) -> tuple[dict[str, Any], Path] | None:
    candidates = sorted(
        (path for path in study_root.glob(AI_REVIEWER_PUBLICATION_EVAL_RECORD_GLOB) if path.is_file()),
        key=lambda path: path.name,
        reverse=True,
    )
    for path in candidates:
        payload = _read_json_object(path)
        if payload is not None and _ai_reviewer_publication_eval_record_valid(payload):
            return payload, path.resolve()
    return None


def _packet_with_latest_ai_reviewer_record(*, study_root: Path, packet: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(packet)
    if payload.get("ai_reviewer_record") or payload.get("publication_eval_record") or payload.get("record"):
        return payload
    latest = _latest_ai_reviewer_publication_eval_record(study_root=study_root)
    if latest is None:
        return payload
    record, record_path = latest
    payload["ai_reviewer_record"] = record
    payload["publication_eval_record_ref"] = str(record_path)
    lifecycle = dict(_mapping(payload.get("request_lifecycle")))
    lifecycle["assessment_ref"] = str(record_path)
    payload["request_lifecycle"] = lifecycle
    return payload


def materialize_ai_reviewer_request(
    *,
    study_root: str | Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    path = stable_ai_reviewer_request_path(study_root=resolved_study_root)
    payload = _packet_with_latest_ai_reviewer_record(study_root=resolved_study_root, packet=packet)
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


def _normalized_required_inputs(
    packet: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, dict[str, Any]]:
    refs = _required_inputs(packet)
    normalized: dict[str, dict[str, Any]] = {}
    for surface in AI_REVIEWER_REQUIRED_INPUT_SURFACES:
        ref = dict(_mapping(refs.get(surface)))
        if surface == "medical_prose_review":
            ref = _normalize_medical_prose_review_ref(study_root=study_root, ref=ref)
        normalized[surface] = ref
    return normalized


def _input_contract_with_normalized_refs(
    packet: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    contract = dict(_input_contract(packet))
    refs = _normalized_required_inputs(packet, study_root=study_root)
    missing = [
        surface
        for surface, ref in refs.items()
        if not _ref_has_target(ref) or ref.get("present") is False or ref.get("valid") is False
    ]
    contract["required_refs"] = refs
    contract["required_surfaces"] = list(AI_REVIEWER_REQUIRED_INPUT_SURFACES)
    contract["all_required_refs_present"] = not missing
    contract["missing_or_invalid_refs"] = missing
    return contract


def _input_blockers(packet: Mapping[str, Any], *, study_root: Path) -> list[str]:
    blockers: list[str] = []
    refs = _normalized_required_inputs(packet, study_root=study_root)
    for surface in AI_REVIEWER_REQUIRED_INPUT_SURFACES:
        ref = _mapping(refs.get(surface))
        if not ref:
            blockers.append(f"{surface}_ref_missing")
            continue
        if not _ref_has_target(ref):
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
    resolved_study_root = Path(study_root).expanduser().resolve()
    packet = read_ai_reviewer_request(study_root=resolved_study_root)
    if packet is None:
        return None

    requested_state = _text(_mapping(packet.get("request_lifecycle")).get("state")) or "requested"
    if requested_state not in AI_REVIEWER_REQUEST_STATES:
        requested_state = "requested"
    input_blockers = _input_blockers(packet, study_root=resolved_study_root)
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
        "input_contract": _input_contract_with_normalized_refs(packet, study_root=resolved_study_root),
        "required_output": dict(_mapping(packet.get("required_output") or packet.get("requested_artifact"))),
        "blockers": input_blockers or list(packet.get("blockers") if isinstance(packet.get("blockers"), list) else []),
        "assessment_written": output_written,
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "refs": {
            "request_path": str(stable_ai_reviewer_request_path(study_root=resolved_study_root)),
        },
    }
