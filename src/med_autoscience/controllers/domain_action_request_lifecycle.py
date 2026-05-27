from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.ai_reviewer_story_provenance_guard import (
    AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON,
    AI_REVIEWER_RECORD_STORY_LEAKAGE_NEXT_REQUIRED_ACTIONS,
    ai_reviewer_record_story_provenance_leakage,
)
from med_autoscience.controllers.ai_reviewer_record_contract import (
    ai_reviewer_record_has_valid_evaluation_scope,
)
from med_autoscience.controllers.domain_action_request_lifecycle_parts.ai_reviewer_currentness_inputs import (
    request_record_currentness_input_refs,
)

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
ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH = Path("artifacts/controller/analysis_harmonization/latest.json")
AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN = (
    "ai_reviewer_record_stale_after_unit_harmonized_rerun"
)
AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT = "ai_reviewer_record_stale_after_current_manuscript"
AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS = "ai_reviewer_record_stale_after_current_inputs"
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
    if not isinstance(payload, dict):
        return None
    if _text(payload.get("surface_kind")) == "legacy_control_surface_tombstone":
        return None
    return payload


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
    if not ai_reviewer_record_has_valid_evaluation_scope(payload):
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


def _resolved_text_ref(*, study_root: Path, value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if not candidate.is_absolute():
        candidate = study_root / candidate
    return str(candidate.resolve())


def _sha256_file(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _analysis_harmonization_currentness_refs(*, study_root: Path) -> list[str]:
    result_path = (study_root / ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH).resolve()
    result = _read_json_object(result_path)
    if not result or result.get("unit_harmonized_rerun_completed") is not True:
        return []
    refs = [str(result_path)]
    rerun_ref = _resolved_text_ref(study_root=study_root, value=result.get("rerun_evidence_ref"))
    if rerun_ref:
        refs.append(rerun_ref)
    return refs


def _current_manuscript_ref(*, study_root: Path, record: Mapping[str, Any]) -> str | None:
    source_refs = _record_source_refs(study_root=study_root, record=record)
    for relative_path in AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES:
        candidate = (study_root / relative_path).resolve()
        candidate_ref = str(candidate)
        if candidate.exists() and candidate_ref in source_refs:
            return candidate_ref
    return None


def _record_source_refs(*, study_root: Path, record: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    provenance = _mapping(record.get("assessment_provenance"))
    candidates = [
        *(_string_items(provenance.get("source_refs"))),
        *(_string_items(record.get("source_refs"))),
        *(_string_items(record.get("evidence_refs"))),
    ]
    quality_assessment = record.get("quality_assessment")
    if isinstance(quality_assessment, Mapping):
        for dimension_payload in quality_assessment.values():
            candidates.extend(
                ref
                for ref in _string_items(_mapping(dimension_payload).get("evidence_refs"))
            )
    for item in candidates:
        resolved = _resolved_text_ref(study_root=study_root, value=item)
        if resolved:
            refs.add(resolved)
    return refs


def _record_source_fingerprints(record: Mapping[str, Any]) -> set[str]:
    fingerprints: set[str] = set()

    def add(value: object) -> None:
        text = _text(value)
        if text:
            fingerprints.add(text)

    provenance = _mapping(record.get("assessment_provenance"))
    reviewer_trace = _mapping(record.get("reviewer_operating_system"))
    input_bundle = _mapping(reviewer_trace.get("input_bundle"))
    for source in (record, provenance, reviewer_trace, input_bundle):
        add(source.get("source_fingerprint"))
        add(source.get("request_source_fingerprint"))
        for item in _string_items(source.get("source_fingerprints")):
            add(item)
        for item in _string_items(source.get("request_source_fingerprints")):
            add(item)
        for item in _string_items(source.get("source_refs")):
            if item.startswith("sha256:"):
                add(item)
    return fingerprints


def _record_missing_currentness_refs(
    *,
    study_root: Path,
    record: Mapping[str, Any],
    request_packet: Mapping[str, Any] | None = None,
) -> list[str]:
    packet_refs = (
        _request_required_currentness_refs(study_root=study_root, request_packet=request_packet)
        if request_packet is not None
        else []
    )
    input_refs = (
        _request_record_currentness_input_refs(study_root=study_root, request_packet=request_packet)
        if request_packet is not None
        else []
    )
    required_refs = packet_refs or _analysis_harmonization_currentness_refs(study_root=study_root)
    source_refs = _record_source_refs(study_root=study_root, record=record)
    current_manuscript_ref = _current_manuscript_ref(study_root=study_root, record=record)
    if current_manuscript_ref and current_manuscript_ref not in set(required_refs):
        required_refs = [*required_refs, current_manuscript_ref]
    for ref in input_refs:
        if ref in source_refs and ref not in set(required_refs):
            required_refs = [*required_refs, ref]
    if not required_refs:
        return []
    record_timestamp = _reviewer_assessment_timestamp(record)
    missing_or_stale: list[str] = []
    for ref in required_refs:
        if ref not in source_refs:
            missing_or_stale.append(ref)
            continue
        ref_timestamp = _ref_timestamp(Path(ref))
        if ref_timestamp is not None and (
            record_timestamp is None or record_timestamp < ref_timestamp
        ):
            missing_or_stale.append(ref)
    return missing_or_stale


def _record_currentness_blocked_reason(
    *,
    study_root: Path,
    record: Mapping[str, Any],
    missing_currentness_refs: list[str],
    request_packet: Mapping[str, Any] | None = None,
) -> str:
    current_manuscript_ref = _current_manuscript_ref(study_root=study_root, record=record)
    if current_manuscript_ref and current_manuscript_ref in set(missing_currentness_refs):
        return AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT
    input_refs = (
        set(_request_record_currentness_input_refs(study_root=study_root, request_packet=request_packet))
        if request_packet is not None
        else set()
    )
    if input_refs and input_refs.intersection(missing_currentness_refs):
        return AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS
    return AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN


def _ref_timestamp(path: Path) -> datetime | None:
    payload = _read_json_object(path)
    timestamp = _payload_timestamp(payload or {})
    if timestamp is not None:
        return timestamp
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def _payload_timestamp(payload: Mapping[str, Any]) -> datetime | None:
    for key in (
        "emitted_at",
        "generated_at",
        "completed_at",
        "finished_at",
        "updated_at",
        "created_at",
        "recorded_at",
    ):
        timestamp = _parse_timestamp(payload.get(key))
        if timestamp is not None:
            return timestamp
    return None


def _reviewer_assessment_timestamp(payload: Mapping[str, Any]) -> datetime | None:
    for value in (
        payload.get("eval_id"),
        _mapping(payload.get("reviewer_operating_system")).get("trace_id"),
    ):
        timestamp = _parse_identifier_timestamp(value)
        if timestamp is not None:
            return timestamp
    return _payload_timestamp(payload)


def _parse_identifier_timestamp(value: object) -> datetime | None:
    text = _text(value)
    if text is None or "::" not in text:
        return None
    return _parse_timestamp(text.rsplit("::", 1)[-1])


def _parse_timestamp(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _block_ai_reviewer_record_manuscript_story_leakage(
    *,
    payload: dict[str, Any],
    record_ref: str | None,
    leakage: Mapping[str, Any],
) -> dict[str, Any]:
    lifecycle = dict(_mapping(payload.get("request_lifecycle")))
    lifecycle["blocked_reason"] = AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON
    if record_ref:
        lifecycle["stale_record_ref"] = record_ref
    lifecycle["leakage_reason"] = _text(leakage.get("reason"))
    lifecycle["leakage_field_path"] = _text(leakage.get("field_path"))
    lifecycle["next_required_actions"] = list(AI_REVIEWER_RECORD_STORY_LEAKAGE_NEXT_REQUIRED_ACTIONS)
    lifecycle.pop("required_currentness_refs", None)
    payload["request_lifecycle"] = lifecycle
    payload.pop("ai_reviewer_record", None)
    payload.pop("publication_eval_record", None)
    payload.pop("record", None)
    payload.pop("publication_eval_record_ref", None)
    return payload


def _block_ai_reviewer_record_missing_currentness(
    *,
    payload: dict[str, Any],
    record_ref: str | None,
    missing_currentness_refs: list[str],
    blocked_reason: str = AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
) -> dict[str, Any]:
    lifecycle = dict(_mapping(payload.get("request_lifecycle")))
    lifecycle["blocked_reason"] = blocked_reason
    if record_ref:
        lifecycle["stale_record_ref"] = record_ref
    lifecycle["required_currentness_refs"] = missing_currentness_refs
    payload["request_lifecycle"] = lifecycle
    payload.pop("ai_reviewer_record", None)
    payload.pop("publication_eval_record", None)
    payload.pop("record", None)
    payload.pop("publication_eval_record_ref", None)
    return payload


def _clear_ai_reviewer_record_lifecycle_blockers(
    *,
    payload: dict[str, Any],
    assessment_ref: str | None = None,
) -> dict[str, Any]:
    lifecycle = dict(_mapping(payload.get("request_lifecycle")))
    lifecycle["blocked_reason"] = None
    if assessment_ref:
        lifecycle["assessment_ref"] = assessment_ref
    lifecycle.pop("stale_record_ref", None)
    lifecycle.pop("required_currentness_refs", None)
    lifecycle.pop("leakage_reason", None)
    lifecycle.pop("leakage_field_path", None)
    lifecycle.pop("next_required_actions", None)
    payload["request_lifecycle"] = lifecycle
    return payload


def _attach_ai_reviewer_record(
    *,
    payload: dict[str, Any],
    record: Mapping[str, Any],
    record_ref: str,
) -> dict[str, Any]:
    payload["ai_reviewer_record"] = dict(record)
    payload["publication_eval_record_ref"] = record_ref
    return _clear_ai_reviewer_record_lifecycle_blockers(payload=payload, assessment_ref=record_ref)


def _validate_ai_reviewer_record_for_packet(
    *,
    study_root: Path,
    payload: dict[str, Any],
    record: Mapping[str, Any],
    record_ref: str | None,
    attach_record: bool,
) -> dict[str, Any]:
    missing_currentness_refs = _record_missing_currentness_refs(
        study_root=study_root,
        record=record,
        request_packet=payload,
    )
    if missing_currentness_refs:
        return _block_ai_reviewer_record_missing_currentness(
            payload=payload,
            record_ref=record_ref,
            missing_currentness_refs=missing_currentness_refs,
            blocked_reason=_record_currentness_blocked_reason(
                study_root=study_root,
                record=record,
                missing_currentness_refs=missing_currentness_refs,
                request_packet=payload,
            ),
        )
    leakage = ai_reviewer_record_story_provenance_leakage(record)
    if leakage is not None:
        return _block_ai_reviewer_record_manuscript_story_leakage(
            payload=payload,
            record_ref=record_ref,
            leakage=leakage,
        )
    if attach_record and record_ref:
        return _attach_ai_reviewer_record(payload=payload, record=record, record_ref=record_ref)
    return _clear_ai_reviewer_record_lifecycle_blockers(payload=payload, assessment_ref=record_ref)


def _resolved_record_ref(*, study_root: Path, payload: Mapping[str, Any]) -> Path | None:
    record_ref = _text(payload.get("publication_eval_record_ref"))
    if not record_ref:
        return None
    path = Path(record_ref).expanduser()
    if not path.is_absolute():
        path = study_root / path
    return path.resolve()


def _latest_record_supersedes_attached_record(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
    latest_record_path: Path,
) -> bool:
    existing_path = _resolved_record_ref(study_root=study_root, payload=payload)
    latest_path = latest_record_path.resolve()
    if existing_path is None:
        return True
    if existing_path == latest_path:
        return False
    response_root = (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").resolve()
    try:
        existing_path.relative_to(response_root)
        latest_path.relative_to(response_root)
    except ValueError:
        return True
    return latest_path.name > existing_path.name


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


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
    latest = _latest_ai_reviewer_publication_eval_record(study_root=study_root)
    existing_record = _mapping(payload.get("ai_reviewer_record") or payload.get("publication_eval_record") or payload.get("record"))
    if latest is not None:
        latest_record, latest_record_path = latest
        if not existing_record or _latest_record_supersedes_attached_record(
            study_root=study_root,
            payload=payload,
            latest_record_path=latest_record_path,
        ):
            return _validate_ai_reviewer_record_for_packet(
                study_root=study_root,
                payload=payload,
                record=latest_record,
                record_ref=str(latest_record_path),
                attach_record=True,
            )
    if existing_record:
        return _validate_ai_reviewer_record_for_packet(
            study_root=study_root,
            payload=payload,
            record=existing_record,
            record_ref=_text(payload.get("publication_eval_record_ref")),
            attach_record=False,
        )
    return payload


def ai_reviewer_request_with_latest_record(
    *,
    study_root: str | Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    return _packet_with_latest_ai_reviewer_record(study_root=resolved_study_root, packet=packet)


def materialize_ai_reviewer_request(
    *,
    study_root: str | Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    path = stable_ai_reviewer_request_path(study_root=resolved_study_root)
    payload = ai_reviewer_request_with_latest_record(study_root=resolved_study_root, packet=packet)
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


def _publication_eval_consumes_ai_reviewer_request(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
    request_packet: Mapping[str, Any],
    request_path: Path,
) -> bool:
    if not _publication_eval_ai_reviewer_owned(publication_eval_payload):
        return False
    record_blocker = _request_packet_record_blocker_reason(request_packet)
    if record_blocker:
        return _publication_eval_consumes_record_blocked_request(
            study_root=study_root,
            publication_eval_payload=_mapping(publication_eval_payload),
            request_packet=request_packet,
            blocked_reason=record_blocker,
        )
    publication_eval = _mapping(publication_eval_payload)
    request_ref = str(request_path.resolve())
    source_refs = set(_record_source_refs(study_root=study_root, record=publication_eval))
    request_fingerprint = _text(request_packet.get("source_fingerprint"))
    source_fingerprints = _record_source_fingerprints(publication_eval)
    if request_fingerprint and request_fingerprint in source_fingerprints:
        return True
    if request_ref in source_refs:
        if request_fingerprint is None:
            return True
    request_timestamp = _payload_timestamp(request_packet)
    if request_timestamp is None:
        try:
            request_timestamp = datetime.fromtimestamp(request_path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            request_timestamp = None
    eval_timestamp = _reviewer_assessment_timestamp(publication_eval)
    if request_timestamp is not None and eval_timestamp is not None:
        return eval_timestamp >= request_timestamp
    if request_timestamp is not None and eval_timestamp is None:
        return False
    if request_fingerprint is not None:
        return False
    return True


def _publication_eval_consumes_record_blocked_request(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    request_packet: Mapping[str, Any],
    blocked_reason: str,
) -> bool:
    if blocked_reason == AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON:
        return False
    if blocked_reason not in {
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
    }:
        return False
    required_refs = _request_required_currentness_refs(study_root=study_root, request_packet=request_packet)
    if blocked_reason == AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS and not required_refs:
        required_refs = _request_record_currentness_input_refs(
            study_root=study_root,
            request_packet=request_packet,
        )
    if not required_refs:
        return False
    reviewer_os = _mapping(publication_eval_payload.get("reviewer_operating_system"))
    currentness_checks = _mapping(reviewer_os.get("currentness_checks"))
    if not currentness_checks:
        return False
    return all(
        _currentness_checks_cover_live_ref(
            study_root=study_root,
            currentness_checks=currentness_checks,
            required_ref=required_ref,
        )
        for required_ref in required_refs
    )


def _request_required_currentness_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    lifecycle = _mapping(request_packet.get("request_lifecycle"))
    for value in _string_items(lifecycle.get("required_currentness_refs")):
        resolved = _resolved_text_ref(study_root=study_root, value=value)
        if resolved:
            refs.append(resolved)
    return list(dict.fromkeys(refs))


def _request_record_currentness_input_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
) -> list[str]:
    return request_record_currentness_input_refs(
        study_root=study_root,
        request_packet=request_packet,
        required_inputs=_required_inputs,
        resolved_text_ref=_resolved_text_ref,
    )


def _currentness_checks_cover_live_ref(
    *,
    study_root: Path,
    currentness_checks: Mapping[str, Any],
    required_ref: str,
) -> bool:
    ref_path = Path(required_ref).expanduser().resolve()
    live_digest = _sha256_file(ref_path)
    if live_digest is None:
        return False
    for check in _currentness_check_mappings(currentness_checks):
        if _currentness_check_matches_live_ref(
            study_root=study_root,
            check=check,
            required_ref=str(ref_path),
            live_digest=live_digest,
        ):
            return True
    return False


def _currentness_check_mappings(value: object, *, depth: int = 0) -> list[Mapping[str, Any]]:
    if depth > 4:
        return []
    if isinstance(value, Mapping):
        mappings: list[Mapping[str, Any]] = [value]
        for nested in value.values():
            mappings.extend(_currentness_check_mappings(nested, depth=depth + 1))
        return mappings
    if isinstance(value, list):
        mappings: list[Mapping[str, Any]] = []
        for item in value:
            mappings.extend(_currentness_check_mappings(item, depth=depth + 1))
        return mappings
    return []


def _currentness_check_matches_live_ref(
    *,
    study_root: Path,
    check: Mapping[str, Any],
    required_ref: str,
    live_digest: str,
) -> bool:
    status = _text(check.get("status"))
    if status not in {"current", "ready", "fresh", "completed", "materialized"}:
        return False
    matched_ref = False
    for field in (
        "manuscript_ref",
        "ref",
        "path",
        "source_ref",
        "evidence_ref",
        "result_ref",
    ):
        resolved = _resolved_text_ref(study_root=study_root, value=check.get(field))
        if resolved == required_ref:
            matched_ref = True
            break
    if not matched_ref:
        return False
    expected_digests = {live_digest, live_digest.removeprefix("sha256:")}
    return any(
        (_text(check.get(field)) or "") in expected_digests
        for field in (
            "manuscript_digest",
            "digest",
            "sha256",
            "content_sha256",
            "file_sha256",
            "file_digest",
        )
    )


def _request_packet_record_blocker_reason(request_packet: Mapping[str, Any]) -> str | None:
    blocked_reason = _text(_mapping(request_packet.get("request_lifecycle")).get("blocked_reason"))
    if blocked_reason in {
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
        AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON,
    }:
        return blocked_reason
    return None


def _request_packet_has_record_currentness_blocker(request_packet: Mapping[str, Any]) -> bool:
    return _request_packet_record_blocker_reason(request_packet) is not None


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
    request_path = stable_ai_reviewer_request_path(study_root=resolved_study_root)
    output_written = _publication_eval_consumes_ai_reviewer_request(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        request_packet=packet,
        request_path=request_path,
    )

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
        "blocked_reason": _text(_mapping(packet.get("request_lifecycle")).get("blocked_reason")),
        "stale_record_ref": _text(_mapping(packet.get("request_lifecycle")).get("stale_record_ref")),
        "required_currentness_refs": _string_items(
            _mapping(packet.get("request_lifecycle")).get("required_currentness_refs")
        ),
        "source_ref": _text(_mapping(packet.get("request_lifecycle")).get("source_ref")),
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "refs": {
            "request_path": str(request_path),
        },
    }
