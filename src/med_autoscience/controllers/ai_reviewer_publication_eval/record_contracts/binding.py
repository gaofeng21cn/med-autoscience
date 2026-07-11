from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.ai_reviewer_story_provenance_guard import (
    AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON,
    AI_REVIEWER_RECORD_STORY_LEAKAGE_NEXT_REQUIRED_ACTIONS,
    ai_reviewer_record_story_provenance_leakage,
)
from .currentness_inputs import (
    request_record_currentness_input_refs,
)
from .currentness_evidence import (
    currentness_blocker_evidence,
)
from ..input_contract import (
    AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES,
    packet_with_normalized_input_contract,
    required_inputs,
)
from .production_currentness import (
    currentness_check_mappings,
    currentness_check_matches_live_ref,
    effective_required_currentness_refs,
    request_currentness_refs_for_blocked_reason,
    request_packet_record_production_blocker_reason,
)
from .currentness import (
    record_currentness_covers_ref,
    record_currentness_mentions_ref,
    record_source_ref_is_current,
)
from .record_refs import (
    _ai_reviewer_publication_eval_record_contract_errors,
    _ai_reviewer_request_production_currentness_refs,
    _current_manuscript_ref,
    _latest_ai_reviewer_publication_eval_record,
    _latest_ai_reviewer_publication_eval_record_candidate,
    _latest_record_supersedes_attached_record,
    _record_source_refs,
    _ref_timestamp,
    _reviewer_assessment_timestamp,
    _sha256_file,
    _string_items,
)

ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH = Path("artifacts/controller/analysis_harmonization/latest.json")
AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN = (
    "ai_reviewer_record_stale_after_unit_harmonized_rerun"
)
AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT = "ai_reviewer_record_stale_after_current_manuscript"
AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS = "ai_reviewer_record_stale_after_current_inputs"
AI_REVIEWER_RECORD_PRODUCTION_BLOCKED_REASONS_BY_WORK_UNIT = {
    "produce_ai_reviewer_publication_eval_record_against_current_manuscript": (
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT
    ),
    "produce_ai_reviewer_publication_eval_record_against_current_inputs": (
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS
    ),
    "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization": (
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN
    ),
}
def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _resolved_text_ref(*, study_root: Path, value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if not candidate.is_absolute():
        candidate = study_root / candidate
    return str(candidate.resolve())


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
    production_refs = (
        _ai_reviewer_request_production_currentness_refs(
            study_root=study_root,
            request_packet=request_packet,
            record=record,
        )
        if request_packet is not None
        else []
    )
    if production_refs:
        required_refs = production_refs
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
        if record_currentness_covers_ref(
            study_root=study_root,
            record=record,
            required_ref=ref,
            mapping=_mapping,
            text=_text,
            sha256_file=_sha256_file,
            resolved_text_ref=_resolved_text_ref,
            currentness_check_mappings=currentness_check_mappings,
            currentness_check_matches_live_ref=currentness_check_matches_live_ref,
        ):
            continue
        if record_currentness_mentions_ref(
            study_root=study_root,
            record=record,
            required_ref=ref,
            mapping=_mapping,
            resolved_text_ref=_resolved_text_ref,
            currentness_check_mappings=currentness_check_mappings,
        ):
            missing_or_stale.append(ref)
            continue
        if not record_source_ref_is_current(
            study_root=study_root,
            record=record,
            required_ref=ref,
            source_refs=source_refs,
            record_timestamp=record_timestamp,
            resolved_text_ref=_resolved_text_ref,
            record_source_refs=_record_source_refs,
            reviewer_assessment_timestamp=_reviewer_assessment_timestamp,
            ref_timestamp=_ref_timestamp,
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
    lifecycle_blocked_reason = _request_packet_record_blocker_reason(request_packet or {})
    if lifecycle_blocked_reason in {
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
    }:
        return lifecycle_blocked_reason
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


def _block_ai_reviewer_record_manuscript_story_leakage(
    *,
    payload: dict[str, Any],
    record_ref: str | None,
    leakage: Mapping[str, Any],
) -> dict[str, Any]:
    lifecycle = dict(_mapping(payload.get("record_requirements")))
    lifecycle["blocked_reason"] = AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON
    if record_ref:
        lifecycle["stale_record_ref"] = record_ref
    lifecycle["leakage_reason"] = _text(leakage.get("reason"))
    lifecycle["leakage_field_path"] = _text(leakage.get("field_path"))
    lifecycle["next_required_actions"] = list(AI_REVIEWER_RECORD_STORY_LEAKAGE_NEXT_REQUIRED_ACTIONS)
    lifecycle.pop("required_currentness_refs", None)
    payload["record_requirements"] = lifecycle
    payload.pop("ai_reviewer_record", None)
    payload.pop("publication_eval_record", None)
    payload.pop("record", None)
    payload.pop("publication_eval_record_ref", None)
    return payload


def _block_ai_reviewer_record_missing_currentness(
    *,
    study_root: Path,
    payload: dict[str, Any],
    record: Mapping[str, Any],
    record_ref: str | None,
    missing_currentness_refs: list[str],
    blocked_reason: str = AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
) -> dict[str, Any]:
    lifecycle = dict(_mapping(payload.get("record_requirements")))
    lifecycle["blocked_reason"] = blocked_reason
    if record_ref:
        lifecycle["stale_record_ref"] = record_ref
    if "required_currentness_refs" not in lifecycle:
        lifecycle["required_currentness_refs"] = missing_currentness_refs
    else:
        lifecycle["missing_currentness_refs"] = missing_currentness_refs
    lifecycle["currentness_evidence"] = currentness_blocker_evidence(
        study_root=study_root,
        record=record,
        record_ref=record_ref,
        missing_currentness_refs=missing_currentness_refs,
        blocked_reason=blocked_reason,
        text=_text,
        mapping=_mapping,
        resolved_text_ref=_resolved_text_ref,
        currentness_check_mappings=currentness_check_mappings,
    )
    payload["record_requirements"] = lifecycle
    payload.pop("ai_reviewer_record", None)
    payload.pop("publication_eval_record", None)
    payload.pop("record", None)
    payload.pop("publication_eval_record_ref", None)
    return payload


def _block_ai_reviewer_record_invalid_currentness_contract(
    *,
    study_root: Path,
    payload: dict[str, Any],
    record: Mapping[str, Any],
    record_ref: str | None,
    contract_errors: list[str],
) -> dict[str, Any]:
    currentness_refs = _request_record_currentness_input_refs(
        study_root=study_root,
        request_packet=payload,
    )
    source_refs = _record_source_refs(study_root=study_root, record=record)
    required_refs = [ref for ref in currentness_refs if ref in source_refs]
    if not required_refs and currentness_refs:
        required_refs = currentness_refs
    blocked_reason = (
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS
        if required_refs
        else AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN
    )
    manuscript_ref = _current_manuscript_ref(study_root=study_root, record=record)
    if manuscript_ref:
        required_refs = [manuscript_ref]
        blocked_reason = AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT
    payload = _block_ai_reviewer_record_missing_currentness(
        study_root=study_root,
        payload=payload,
        record=record,
        record_ref=record_ref,
        missing_currentness_refs=list(dict.fromkeys(required_refs)),
        blocked_reason=blocked_reason,
    )
    lifecycle = dict(_mapping(payload.get("record_requirements")))
    lifecycle["reviewer_operating_system_errors"] = contract_errors
    payload["record_requirements"] = lifecycle
    return payload


def _clear_ai_reviewer_record_lifecycle_blockers(
    *,
    payload: dict[str, Any],
    assessment_ref: str | None = None,
) -> dict[str, Any]:
    lifecycle = dict(_mapping(payload.get("record_requirements")))
    lifecycle["blocked_reason"] = None
    if assessment_ref:
        lifecycle["assessment_ref"] = assessment_ref
    lifecycle.pop("stale_record_ref", None)
    lifecycle.pop("required_currentness_refs", None)
    lifecycle.pop("missing_currentness_refs", None)
    lifecycle.pop("currentness_evidence", None)
    lifecycle.pop("leakage_reason", None)
    lifecycle.pop("leakage_field_path", None)
    lifecycle.pop("next_required_actions", None)
    payload["record_requirements"] = lifecycle
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
            study_root=study_root,
            payload=payload,
            record=record,
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



def _packet_with_latest_ai_reviewer_record(*, study_root: Path, packet: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(packet)
    latest = _latest_ai_reviewer_publication_eval_record(study_root=study_root, request_packet=payload)
    latest_candidate = _latest_ai_reviewer_publication_eval_record_candidate(
        study_root=study_root,
        request_packet=payload,
    )
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
    if latest_candidate is not None:
        candidate_record, candidate_path = latest_candidate
        if latest is None or candidate_path != latest[1]:
            contract_errors = _ai_reviewer_publication_eval_record_contract_errors(candidate_record)
            if contract_errors and (
                not existing_record
                or _latest_record_supersedes_attached_record(
                    study_root=study_root,
                    payload=payload,
                    latest_record_path=candidate_path,
                )
            ):
                return _block_ai_reviewer_record_invalid_currentness_contract(
                    study_root=study_root,
                    payload=payload,
                    record=candidate_record,
                    record_ref=str(candidate_path),
                    contract_errors=contract_errors,
                )
    if existing_record:
        contract_errors = _ai_reviewer_publication_eval_record_contract_errors(existing_record)
        if contract_errors:
            return _block_ai_reviewer_record_invalid_currentness_contract(
                study_root=study_root,
                payload=payload,
                record=existing_record,
                record_ref=_text(payload.get("publication_eval_record_ref")),
                contract_errors=contract_errors,
            )
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
    payload = packet_with_normalized_input_contract(
        study_root=resolved_study_root,
        packet=packet,
    )
    return _packet_with_latest_ai_reviewer_record(study_root=resolved_study_root, packet=payload)


def _request_required_currentness_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    lifecycle = _mapping(request_packet.get("record_requirements"))
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
        required_inputs=required_inputs,
        resolved_text_ref=_resolved_text_ref,
    )


def _request_packet_record_blocker_reason(request_packet: Mapping[str, Any]) -> str | None:
    blocked_reason = _text(_mapping(request_packet.get("record_requirements")).get("blocked_reason"))
    if blocked_reason in {
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
        AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON,
    }:
        return blocked_reason
    return None


def _request_packet_record_production_blocker_reason(request_packet: Mapping[str, Any]) -> str | None:
    return request_packet_record_production_blocker_reason(
        request_packet=request_packet,
        work_unit_blocked_reasons=AI_REVIEWER_RECORD_PRODUCTION_BLOCKED_REASONS_BY_WORK_UNIT,
        text=_text,
        mapping=_mapping,
    )


def _effective_required_currentness_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
    blocked_reason: str | None,
) -> list[str]:
    return effective_required_currentness_refs(
        study_root=study_root,
        request_packet=request_packet,
        blocked_reason=blocked_reason,
        stale_after_current_manuscript=AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
        stale_after_current_inputs=AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_INPUTS,
        stale_after_unit_harmonized_rerun=AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
        required_inputs=required_inputs,
        resolved_text_ref=_resolved_text_ref,
        required_currentness_refs=_request_required_currentness_refs,
        record_currentness_input_refs=_request_record_currentness_input_refs,
        analysis_harmonization_currentness_refs=_analysis_harmonization_currentness_refs,
        string_items=_string_items,
        mapping=_mapping,
    )
