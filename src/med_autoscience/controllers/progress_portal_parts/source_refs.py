from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def source_refs(*payloads: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        refs.extend(_refs_from(payload))
    return sorted(dict.fromkeys(ref for ref in refs if source_ref_allowed(ref)))


def source_ref_allowed(ref: str) -> bool:
    blocked_tokens = (
        "/ops/med-deepscientist/",
        "med-deepscientist",
        ".ds/worktrees",
    )
    return not any(token in ref for token in blocked_tokens)


def display_source_refs(value: object) -> list[str]:
    refs = _string_list(value)
    priority_tokens = (
        "/artifacts/runtime/health/",
        "/artifacts/supervision/opl_runtime_owner_handoff/",
        "/artifacts/controller_decisions/",
        "/artifacts/publication_eval/",
        "/artifacts/truth/",
        "/artifacts/runtime/progress_portal/",
        "/artifacts/supervision/hourly/",
        "/runtime/quests/",
    )
    blocked_tokens = (
        "/ops/med-deepscientist/",
        "med-deepscientist",
        ".ds/worktrees",
    )
    selected: list[str] = []
    for ref in refs:
        if any(token in ref for token in blocked_tokens):
            continue
        if any(token in ref for token in priority_tokens):
            selected.append(ref)
        if len(selected) >= 24:
            break
    return selected


def _refs_from(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        if _looks_like_ref(value):
            refs.append(value)
        return refs
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).endswith("refs") or str(key) in {"refs", "evidence_refs", "source_refs"}:
                refs.extend(_refs_from_ref_field(item))
            elif str(key).endswith("ref") or str(key).endswith("path"):
                refs.extend(_refs_from_ref_field(item))
            elif isinstance(item, Mapping | list | tuple):
                refs.extend(_refs_from(item))
        return refs
    if isinstance(value, list | tuple):
        for item in value:
            refs.extend(_refs_from(item))
    return refs


def _refs_from_ref_field(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_refs_from_ref_field(item))
        return result
    if isinstance(value, list | tuple):
        result: list[str] = []
        for item in value:
            result.extend(_refs_from_ref_field(item))
        return result
    return []


def _looks_like_ref(value: str) -> bool:
    return "/" in value or value.endswith(".json") or value.endswith(".yaml")


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


__all__ = ["display_source_refs", "source_ref_allowed", "source_refs"]
