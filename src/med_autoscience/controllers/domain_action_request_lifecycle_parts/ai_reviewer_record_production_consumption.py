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
    if refs:
        return refs
    if blocked_reason == stale_after_current_manuscript:
        manuscript_ref = request_input_ref(
            study_root=study_root,
            request_packet=request_packet,
            surface="manuscript",
            required_inputs=required_inputs,
            resolved_text_ref=resolved_text_ref,
        )
        return [manuscript_ref] if manuscript_ref else []
    if blocked_reason == stale_after_current_inputs:
        return record_currentness_input_refs(
            study_root=study_root,
            request_packet=request_packet,
        )
    if blocked_reason == stale_after_unit_harmonized_rerun:
        return analysis_harmonization_currentness_refs(study_root=study_root)
    return []


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


__all__ = [
    "publication_eval_matches_attached_request_record",
    "request_currentness_refs_for_blocked_reason",
    "request_packet_record_production_blocker_reason",
]
