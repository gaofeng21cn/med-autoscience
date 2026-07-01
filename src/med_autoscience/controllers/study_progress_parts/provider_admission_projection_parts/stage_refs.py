from __future__ import annotations

from typing import Any, Mapping

from ..shared import _mapping_copy, _non_empty_text


def retain_stage_packet_refs_for_provider_readback(candidate: dict[str, Any]) -> None:
    stage_family = stage_packet_ref_family(candidate)
    stage_packet_ref = _non_empty_text(stage_family.get("stage_packet_ref"))
    stage_packet_refs = text_list(stage_family.get("stage_packet_refs"))
    checkpoint_refs = text_list(stage_family.get("checkpoint_refs"))
    source_refs = _mapping_copy(candidate.get("source_refs"))
    if stage_packet_ref is not None:
        candidate["stage_packet_ref"] = stage_packet_ref
        source_refs["stage_packet_ref"] = stage_packet_ref
    if stage_packet_refs:
        candidate["stage_packet_refs"] = stage_packet_refs
        source_refs["stage_packet_refs"] = stage_packet_refs
    if checkpoint_refs:
        candidate["checkpoint_refs"] = checkpoint_refs
        source_refs["checkpoint_refs"] = checkpoint_refs
    if source_refs:
        candidate["source_refs"] = source_refs


def merge_stage_packet_ref_family(
    target: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    merged = stage_packet_ref_family({**dict(source), **dict(target)})
    source_family = stage_packet_ref_family(source)
    stage_packet_ref = _non_empty_text(merged.get("stage_packet_ref")) or _non_empty_text(
        source_family.get("stage_packet_ref")
    )
    stage_packet_refs = dedupe_text_items(
        merged.get("stage_packet_refs"),
        source_family.get("stage_packet_refs"),
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = dedupe_text_items(
        merged.get("checkpoint_refs"),
        source_family.get("checkpoint_refs"),
    ) or list(stage_packet_refs)
    source_refs = {
        **_mapping_copy(source.get("source_refs")),
        **_mapping_copy(target.get("source_refs")),
    }
    if stage_packet_ref is not None:
        target["stage_packet_ref"] = stage_packet_ref
        source_refs["stage_packet_ref"] = stage_packet_ref
    if stage_packet_refs:
        target["stage_packet_refs"] = stage_packet_refs
        source_refs["stage_packet_refs"] = stage_packet_refs
    if checkpoint_refs:
        target["checkpoint_refs"] = checkpoint_refs
        source_refs["checkpoint_refs"] = checkpoint_refs
    if source_refs:
        target["source_refs"] = source_refs


def stage_packet_ref_family(payload: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = _mapping_copy(payload.get("source_refs"))
    owner_route_refs = _mapping_copy(_mapping_copy(payload.get("owner_route")).get("source_refs"))
    currentness_basis = _mapping_copy(payload.get("currentness_basis"))
    provider_identity = _mapping_copy(payload.get("provider_admission_identity"))
    stage_packet_ref = first_non_empty_text(
        payload.get("stage_packet_ref"),
        source_refs.get("stage_packet_ref"),
        owner_route_refs.get("stage_packet_ref"),
        currentness_basis.get("stage_packet_ref"),
        provider_identity.get("stage_packet_ref"),
    )
    stage_packet_refs = dedupe_text_items(
        payload.get("stage_packet_refs"),
        source_refs.get("stage_packet_refs"),
        owner_route_refs.get("stage_packet_refs"),
        currentness_basis.get("stage_packet_refs"),
        provider_identity.get("stage_packet_refs"),
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = dedupe_text_items(
        payload.get("checkpoint_refs"),
        source_refs.get("checkpoint_refs"),
        owner_route_refs.get("checkpoint_refs"),
        currentness_basis.get("checkpoint_refs"),
        provider_identity.get("checkpoint_refs"),
    ) or list(stage_packet_refs)
    return {
        key: value
        for key, value in {
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs,
            "checkpoint_refs": checkpoint_refs,
        }.items()
        if value not in (None, "", [], {})
    }


def first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def dedupe_text_items(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        for item in text_list(value):
            if item not in refs:
                refs.append(item)
    return refs


def text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    items: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in items:
            items.append(text)
    return items
