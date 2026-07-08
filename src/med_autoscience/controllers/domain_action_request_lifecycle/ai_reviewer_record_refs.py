from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.ai_reviewer_record_contract import (
    ai_reviewer_record_has_valid_evaluation_scope,
)
from med_autoscience.controllers.domain_action_request_lifecycle.ai_reviewer_input_contract import (
    AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES,
)
from med_autoscience.controllers.domain_action_request_lifecycle.ai_reviewer_record_production_consumption import (
    currentness_check_mappings,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
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


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        parsed = json.loads(payload)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _resolved_text_ref(*, study_root: Path, value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if not candidate.is_absolute():
        candidate = study_root / candidate
    return str(candidate.resolve())


def _ai_reviewer_publication_eval_record_candidate(payload: Mapping[str, Any]) -> bool:
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


def _ai_reviewer_publication_eval_record_valid(payload: Mapping[str, Any]) -> bool:
    if not _ai_reviewer_publication_eval_record_candidate(payload):
        return False
    reviewer_os = _mapping(payload.get("reviewer_operating_system"))
    return not validate_ai_reviewer_operating_system_trace(dict(reviewer_os))


def _ai_reviewer_publication_eval_record_contract_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    if not _ai_reviewer_publication_eval_record_candidate(payload):
        return ["ai_reviewer publication eval record must satisfy the owner record contract"]
    reviewer_os = payload.get("reviewer_operating_system")
    if not isinstance(reviewer_os, Mapping):
        return ["reviewer_operating_system must be an object"]
    return validate_ai_reviewer_operating_system_trace(dict(reviewer_os))


def _sha256_file(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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


def _ref_timestamp(path: Path) -> datetime | None:
    payload = _read_json_object(path)
    timestamp = _payload_timestamp(payload or {})
    if timestamp is not None:
        return timestamp
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


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
    response_root = (
        study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    ).resolve()
    try:
        existing_path.relative_to(response_root)
        latest_path.relative_to(response_root)
    except ValueError:
        return True
    return latest_path.name > existing_path.name


def _latest_ai_reviewer_publication_eval_record(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], Path] | None:
    request_production_context = _ai_reviewer_request_production_context(
        study_root=study_root,
        request_packet=request_packet,
    )
    candidates = sorted(
        (
            path
            for path in study_root.glob(AI_REVIEWER_PUBLICATION_EVAL_RECORD_GLOB)
            if path.is_file()
        ),
        key=lambda path: path.name,
        reverse=True,
    )
    for path in candidates:
        payload = _read_json_object(path)
        if (
            payload is not None
            and _ai_reviewer_publication_eval_record_valid(payload)
            and _ai_reviewer_record_matches_request_production_context(
                record=payload,
                request_production_context=request_production_context,
            )
        ):
            return payload, path.resolve()
    return None


def _latest_ai_reviewer_publication_eval_record_candidate(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], Path] | None:
    request_production_context = _ai_reviewer_request_production_context(
        study_root=study_root,
        request_packet=request_packet,
    )
    candidates = sorted(
        (
            path
            for path in study_root.glob(AI_REVIEWER_PUBLICATION_EVAL_RECORD_GLOB)
            if path.is_file()
        ),
        key=lambda path: path.name,
        reverse=True,
    )
    for path in candidates:
        payload = _read_json_object(path)
        if (
            payload is not None
            and _ai_reviewer_publication_eval_record_candidate(payload)
            and _ai_reviewer_record_matches_request_production_context(
                record=payload,
                request_production_context=request_production_context,
            )
        ):
            return payload, path.resolve()
    return None


def _ai_reviewer_request_production_currentness_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
    record: Mapping[str, Any],
) -> list[str]:
    record_context = _ai_reviewer_record_production_context(record)
    if not record_context["work_unit_ids"] and not record_context["work_unit_fingerprints"]:
        return []
    refs: list[str] = []
    for authoring_payload in _matching_record_production_authoring_payloads(
        study_root=study_root,
        request_packet=request_packet,
    ):
        authoring_context = _ai_reviewer_record_production_context(authoring_payload)
        record_payload = _mapping(authoring_payload.get("record_payload"))
        payload_context = _ai_reviewer_record_production_context(record_payload)
        if not _production_contexts_match(
            record_context,
            authoring_context,
        ) and not _production_contexts_match(record_context, payload_context):
            continue
        for source in (record_payload, _mapping(record_payload.get("assessment_provenance"))):
            for item in _string_items(source.get("source_refs")):
                resolved = _resolved_text_ref(study_root=study_root, value=item)
                if resolved:
                    refs.append(resolved)
        reviewer_trace = _mapping(record_payload.get("reviewer_operating_system"))
        currentness_checks = _mapping(reviewer_trace.get("currentness_checks"))
        for check in currentness_check_mappings(currentness_checks):
            for key in (
                "manuscript_ref",
                "ref",
                "path",
                "source_ref",
                "evidence_ref",
                "result_ref",
            ):
                resolved = _resolved_text_ref(study_root=study_root, value=check.get(key))
                if resolved:
                    refs.append(resolved)
    source_refs = _record_source_refs(study_root=study_root, record=record)
    return list(dict.fromkeys(ref for ref in refs if ref in source_refs))


def _ai_reviewer_record_production_context(record: Mapping[str, Any]) -> dict[str, set[str]]:
    context: dict[str, set[str]] = {"work_unit_ids": set(), "work_unit_fingerprints": set()}
    provenance = _mapping(record.get("assessment_provenance"))
    reviewer_trace = _mapping(record.get("reviewer_operating_system"))
    input_bundle = _mapping(reviewer_trace.get("input_bundle"))
    for source in (record, provenance, reviewer_trace, input_bundle):
        for key in (
            "work_unit_id",
            "source_work_unit_id",
            "requested_work_unit_id",
            "request_kind",
        ):
            if text := _text(source.get(key)):
                context["work_unit_ids"].add(text)
        for key in (
            "work_unit_fingerprint",
            "source_work_unit_fingerprint",
            "requested_work_unit_fingerprint",
        ):
            if text := _text(source.get(key)):
                context["work_unit_fingerprints"].add(text)
    return context


def _production_contexts_match(
    left: Mapping[str, set[str]],
    right: Mapping[str, set[str]],
) -> bool:
    if left.get("work_unit_fingerprints", set()).intersection(
        right.get("work_unit_fingerprints", set())
    ):
        return True
    return bool(left.get("work_unit_ids", set()).intersection(right.get("work_unit_ids", set())))


def _ai_reviewer_request_production_context(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any] | None,
) -> dict[str, set[str]]:
    context: dict[str, set[str]] = {"work_unit_ids": set(), "work_unit_fingerprints": set()}
    if request_packet is None:
        return context

    def add_context(source: Mapping[str, Any]) -> None:
        for key in (
            "next_work_unit",
            "work_unit_id",
            "source_work_unit_id",
            "requested_work_unit_id",
        ):
            if text := _text(source.get(key)):
                context["work_unit_ids"].add(text)
        for key in (
            "work_unit_fingerprint",
            "source_work_unit_fingerprint",
            "requested_work_unit_fingerprint",
            "materialized_work_unit_fingerprint",
        ):
            if text := _text(source.get(key)):
                context["work_unit_fingerprints"].add(text)

    source_workflow_ref = _mapping(request_packet.get("source_workflow_ref"))
    owner_route_source_refs = _mapping(_mapping(request_packet.get("owner_route")).get("source_refs"))
    add_context(source_workflow_ref)
    add_context(owner_route_source_refs)
    for authoring_payload in _matching_record_production_authoring_payloads(
        study_root=study_root,
        request_packet=request_packet,
    ):
        add_context(authoring_payload)
        record_payload = _mapping(authoring_payload.get("record_payload"))
        add_context(record_payload)
        add_context(_mapping(record_payload.get("assessment_provenance")))
    return context


def _matching_record_production_authoring_payloads(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    request_kind = _text(request_packet.get("request_kind"))
    payload_root = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "record_production_payloads"
    )
    payloads: list[Mapping[str, Any]] = []
    for path in sorted(payload_root.glob("*_payload.json")):
        payload = _read_json_object(path)
        if payload is None:
            continue
        if request_kind and _text(payload.get("action_type")) != request_kind:
            continue
        payloads.append(payload)
    return payloads


def _ai_reviewer_record_matches_request_production_context(
    *,
    record: Mapping[str, Any],
    request_production_context: Mapping[str, set[str]],
) -> bool:
    requested_work_unit_ids = request_production_context.get("work_unit_ids") or set()
    requested_fingerprints = request_production_context.get("work_unit_fingerprints") or set()
    if not requested_work_unit_ids and not requested_fingerprints:
        return True

    provenance = _mapping(record.get("assessment_provenance"))
    reviewer_trace = _mapping(record.get("reviewer_operating_system"))
    input_bundle = _mapping(reviewer_trace.get("input_bundle"))
    record_work_unit_ids = {
        text
        for source in (record, provenance, reviewer_trace, input_bundle)
        for text in (
            _text(source.get("work_unit_id")),
            _text(source.get("source_work_unit_id")),
            _text(source.get("requested_work_unit_id")),
        )
        if text
    }
    record_fingerprints = {
        text
        for source in (record, provenance, reviewer_trace, input_bundle)
        for text in (
            _text(source.get("work_unit_fingerprint")),
            _text(source.get("source_work_unit_fingerprint")),
            _text(source.get("requested_work_unit_fingerprint")),
        )
        if text
    }
    if requested_fingerprints and record_fingerprints.intersection(requested_fingerprints):
        return True
    if requested_work_unit_ids and record_work_unit_ids.intersection(requested_work_unit_ids):
        return True
    return False


__all__ = [
    "_ai_reviewer_publication_eval_record_contract_errors",
    "_ai_reviewer_request_production_currentness_refs",
    "_current_manuscript_ref",
    "_latest_ai_reviewer_publication_eval_record",
    "_latest_ai_reviewer_publication_eval_record_candidate",
    "_latest_record_supersedes_attached_record",
    "_payload_timestamp",
    "_record_source_fingerprints",
    "_record_source_refs",
    "_ref_timestamp",
    "_reviewer_assessment_timestamp",
    "_sha256_file",
]
