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
        return input_refs
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
    return string_items(mapping(request_packet.get("record_requirements")).get("required_currentness_refs"))


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
    "request_currentness_refs_for_blocked_reason",
    "request_packet_record_production_blocker_reason",
]
