from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable


TextFn = Callable[[object], str | None]
MappingFn = Callable[[object], Mapping[str, Any]]
RequiredInputsFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]
ResolvedTextRefFn = Callable[..., str | None]
CurrentnessInputRefsFn = Callable[..., list[str]]
AnalysisCurrentnessRefsFn = Callable[..., list[str]]


def request_currentness_refs_for_blocked_reason(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
    blocked_reason: str,
    stale_after_current_manuscript: str,
    stale_after_current_inputs: str,
    stale_after_unit_harmonized_rerun: str,
    required_inputs: RequiredInputsFn,
    resolved_text_ref: ResolvedTextRefFn,
    required_currentness_refs: Callable[..., list[str]],
    record_currentness_input_refs: CurrentnessInputRefsFn,
    analysis_harmonization_currentness_refs: AnalysisCurrentnessRefsFn,
) -> list[str]:
    refs = required_currentness_refs(
        study_root=study_root,
        request_packet=request_packet,
    )
    if blocked_reason == stale_after_current_manuscript:
        if refs:
            return refs
        manuscript_ref = request_input_ref(
            study_root=study_root,
            request_packet=request_packet,
            surface="manuscript",
            required_inputs=required_inputs,
            resolved_text_ref=resolved_text_ref,
        )
        return [manuscript_ref] if manuscript_ref else []
    if blocked_reason == stale_after_current_inputs:
        input_refs = record_currentness_input_refs(
            study_root=study_root,
            request_packet=request_packet,
        )
        return list(dict.fromkeys([*refs, *input_refs]))
    if refs:
        return refs
    if blocked_reason == stale_after_unit_harmonized_rerun:
        return analysis_harmonization_currentness_refs(study_root=study_root)
    return []


def effective_required_currentness_refs(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
    blocked_reason: str | None,
    stale_after_current_manuscript: str,
    stale_after_current_inputs: str,
    stale_after_unit_harmonized_rerun: str,
    required_inputs: RequiredInputsFn,
    resolved_text_ref: ResolvedTextRefFn,
    required_currentness_refs: Callable[..., list[str]],
    record_currentness_input_refs: CurrentnessInputRefsFn,
    analysis_harmonization_currentness_refs: AnalysisCurrentnessRefsFn,
    string_items: Callable[[object], list[str]],
    mapping: MappingFn,
) -> list[str]:
    if blocked_reason in {
        stale_after_current_manuscript,
        stale_after_current_inputs,
        stale_after_unit_harmonized_rerun,
    }:
        return request_currentness_refs_for_blocked_reason(
            study_root=study_root,
            request_packet=request_packet,
            blocked_reason=blocked_reason,
            stale_after_current_manuscript=stale_after_current_manuscript,
            stale_after_current_inputs=stale_after_current_inputs,
            stale_after_unit_harmonized_rerun=stale_after_unit_harmonized_rerun,
            required_inputs=required_inputs,
            resolved_text_ref=resolved_text_ref,
            required_currentness_refs=required_currentness_refs,
            record_currentness_input_refs=record_currentness_input_refs,
            analysis_harmonization_currentness_refs=analysis_harmonization_currentness_refs,
        )
    return string_items(mapping(request_packet.get("request_lifecycle")).get("required_currentness_refs"))


def owner_output_consumption_ledger(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
    request_packet: Mapping[str, Any],
    output_written: bool,
    record_blocker_reason: Callable[..., str | None],
    record_production_blocker_reason: Callable[..., str | None],
    text: TextFn,
    mapping: MappingFn,
    required_inputs: RequiredInputsFn,
    resolved_text_ref: ResolvedTextRefFn,
    required_currentness_refs: Callable[..., list[str]],
    record_currentness_input_refs: CurrentnessInputRefsFn,
    analysis_harmonization_currentness_refs: AnalysisCurrentnessRefsFn,
    stale_after_current_manuscript: str,
    stale_after_current_inputs: str,
    stale_after_unit_harmonized_rerun: str,
) -> dict[str, Any] | None:
    if not output_written:
        return None
    publication_eval = mapping(publication_eval_payload)
    eval_id = text(publication_eval.get("eval_id"))
    record_ref = text(request_packet.get("publication_eval_record_ref"))
    if eval_id is None or record_ref is None:
        return None
    blocked_reason = record_blocker_reason(request_packet) or record_production_blocker_reason(request_packet)
    if blocked_reason is None:
        return None
    required_refs = request_currentness_refs_for_blocked_reason(
        study_root=study_root,
        request_packet=request_packet,
        blocked_reason=blocked_reason,
        stale_after_current_manuscript=stale_after_current_manuscript,
        stale_after_current_inputs=stale_after_current_inputs,
        stale_after_unit_harmonized_rerun=stale_after_unit_harmonized_rerun,
        required_inputs=required_inputs,
        resolved_text_ref=resolved_text_ref,
        required_currentness_refs=required_currentness_refs,
        record_currentness_input_refs=record_currentness_input_refs,
        analysis_harmonization_currentness_refs=analysis_harmonization_currentness_refs,
    )
    return {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "record_ref": str(resolve_path(study_root=study_root, value=record_ref)),
        "eval_id": eval_id,
        "consumption_mode": "refs_only_current_ai_reviewer_record",
        "required_currentness_refs": required_refs,
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }


def resolve_path(*, study_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = study_root / path
    return path.resolve()


def request_input_ref(
    *,
    study_root: Path,
    request_packet: Mapping[str, Any],
    surface: str,
    required_inputs: RequiredInputsFn,
    resolved_text_ref: ResolvedTextRefFn,
) -> str | None:
    ref = required_inputs(request_packet).get(surface)
    if not isinstance(ref, Mapping):
        return None
    return resolved_text_ref(
        study_root=study_root,
        value=ref.get("path") or ref.get("relative_path") or ref.get("ref"),
    )


def request_packet_record_production_blocker_reason(
    *,
    request_packet: Mapping[str, Any],
    work_unit_blocked_reasons: Mapping[str, str],
    text: TextFn,
    mapping: MappingFn,
) -> str | None:
    source_workflow_ref = mapping(request_packet.get("source_workflow_ref"))
    owner_route_refs = mapping(mapping(request_packet.get("owner_route")).get("source_refs"))
    for work_unit_id in (
        text(source_workflow_ref.get("next_work_unit")),
        text(source_workflow_ref.get("work_unit_id")),
        text(owner_route_refs.get("work_unit_id")),
        text(owner_route_refs.get("materialized_work_unit_id")),
    ):
        reason = work_unit_blocked_reasons.get(work_unit_id or "")
        if reason:
            return reason
    return None


def publication_eval_matches_attached_request_record(
    *,
    publication_eval_payload: Mapping[str, Any],
    request_packet: Mapping[str, Any],
    text: TextFn,
    mapping: MappingFn,
) -> bool:
    attached_record = mapping(
        request_packet.get("ai_reviewer_record")
        or request_packet.get("publication_eval_record")
        or request_packet.get("record")
    )
    if not attached_record:
        return False
    if not text(request_packet.get("publication_eval_record_ref")):
        return False
    attached_eval_id = text(attached_record.get("eval_id"))
    return attached_eval_id is not None and attached_eval_id == text(publication_eval_payload.get("eval_id"))


def currentness_checks_cover_live_ref(
    *,
    study_root: Path,
    currentness_checks: Mapping[str, Any],
    required_ref: str,
    sha256_file: Callable[[Path], str | None],
    text: TextFn,
    resolved_text_ref: ResolvedTextRefFn,
) -> bool:
    ref_path = Path(required_ref).expanduser().resolve()
    live_digest = sha256_file(ref_path)
    if live_digest is None:
        return False
    return any(
        currentness_check_matches_live_ref(
            study_root=study_root,
            check=check,
            required_ref=str(ref_path),
            live_digest=live_digest,
            text=text,
            resolved_text_ref=resolved_text_ref,
        )
        for check in currentness_check_mappings(currentness_checks)
    )


def currentness_check_mappings(value: object, *, depth: int = 0) -> list[Mapping[str, Any]]:
    if depth > 4:
        return []
    if isinstance(value, Mapping):
        mappings: list[Mapping[str, Any]] = [value]
        for nested in value.values():
            mappings.extend(currentness_check_mappings(nested, depth=depth + 1))
        return mappings
    if isinstance(value, list):
        mappings: list[Mapping[str, Any]] = []
        for item in value:
            mappings.extend(currentness_check_mappings(item, depth=depth + 1))
        return mappings
    return []


def currentness_check_matches_live_ref(
    *,
    study_root: Path,
    check: Mapping[str, Any],
    required_ref: str,
    live_digest: str,
    text: TextFn,
    resolved_text_ref: ResolvedTextRefFn,
) -> bool:
    status = text(check.get("status"))
    if status not in {"current", "ready", "fresh", "completed", "materialized"}:
        return False
    if not any(
        resolved_text_ref(study_root=study_root, value=check.get(field)) == required_ref
        for field in ("manuscript_ref", "ref", "path", "source_ref", "evidence_ref", "result_ref")
    ):
        return False
    expected_digests = {live_digest, live_digest.removeprefix("sha256:")}
    return any(
        (text(check.get(field)) or "") in expected_digests
        for field in ("manuscript_digest", "digest", "sha256", "content_sha256", "file_sha256", "file_digest")
    )


__all__ = [
    "effective_required_currentness_refs",
    "currentness_check_mappings",
    "currentness_check_matches_live_ref",
    "currentness_checks_cover_live_ref",
    "owner_output_consumption_ledger",
    "publication_eval_matches_attached_request_record",
    "request_currentness_refs_for_blocked_reason",
    "request_packet_record_production_blocker_reason",
]
