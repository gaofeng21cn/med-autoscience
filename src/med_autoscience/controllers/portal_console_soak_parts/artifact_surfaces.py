from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .shared import dedupe_text, mapping, mapping_list, read_json_object, read_text, source_ref_objects, text


def materialized_study_page_refs(
    *,
    portal_result: Mapping[str, Any],
    portal_html_path: Path,
    studies: list[dict[str, Any]],
) -> list[str]:
    refs: list[str] = []
    for page in mapping(portal_result.get("study_pages")).values():
        if isinstance(page, Mapping):
            refs.extend([text(page.get("html_path")), text(page.get("html_ref"))])
    base = portal_html_path.parent
    for item in studies:
        study_id = text(item.get("study_id"))
        if not study_id:
            continue
        candidate = base / "studies" / study_id / "index.html"
        if candidate.is_file():
            refs.append(str(candidate))
    return [ref for ref in dedupe_text(refs) if ref]


def portal_route_trails(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    trails: list[dict[str, Any]] = []
    workbench = mapping(portal_payload.get("study_workbench"))
    trail = mapping(workbench.get("route_decision_trail"))
    if trail:
        trails.append(trail)
    for page in mapping(portal_result.get("study_pages")).values():
        if not isinstance(page, Mapping):
            continue
        payload_path = Path(str(page.get("payload_path") or ""))
        page_payload = read_json_object(payload_path)
        page_trail = mapping(mapping(page_payload.get("study_workbench")).get("route_decision_trail"))
        if page_trail:
            trails.append(page_trail)
    return trails


def portal_route_maps(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    maps: list[dict[str, Any]] = []
    workbench = mapping(portal_payload.get("study_workbench"))
    route_map = mapping(workbench.get("route_map"))
    if route_map:
        maps.append(route_map)
    for page in mapping(portal_result.get("study_pages")).values():
        if not isinstance(page, Mapping):
            continue
        payload_path = Path(str(page.get("payload_path") or ""))
        page_payload = read_json_object(payload_path)
        page_map = mapping(mapping(page_payload.get("study_workbench")).get("route_map"))
        if page_map:
            maps.append(page_map)
    return maps


def portal_conversation_panels(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    panels: list[dict[str, Any]] = []
    panel = mapping(mapping(portal_payload.get("study_workbench")).get("conversation"))
    if panel:
        panels.append(panel)
    for page in mapping(portal_result.get("study_pages")).values():
        if not isinstance(page, Mapping):
            continue
        payload_path = Path(str(page.get("payload_path") or ""))
        page_payload = read_json_object(payload_path)
        page_panel = mapping(mapping(page_payload.get("study_workbench")).get("conversation"))
        if page_panel:
            panels.append(page_panel)
    return panels


def conversation_panel_html_refs(
    *,
    portal_result: Mapping[str, Any],
    portal_html_path: Path,
) -> list[str]:
    refs: list[str] = []
    for path in [portal_html_path, *[
        Path(str(page.get("html_path") or ""))
        for page in mapping(portal_result.get("study_pages")).values()
        if isinstance(page, Mapping)
    ]]:
        html = read_text(path)
        if "执行器对话" in html and "对话来源" in html and "conversation-timeline" in html:
            refs.append(str(path))
    return refs


def route_map_html_refs(
    *,
    portal_result: Mapping[str, Any],
    portal_html_path: Path,
) -> list[str]:
    refs: list[str] = []
    for path in [portal_html_path, *[
        Path(str(page.get("html_path") or ""))
        for page in mapping(portal_result.get("study_pages")).values()
        if isinstance(page, Mapping)
    ]]:
        html = read_text(path)
        if "研究路线地图" in html and "route-map-svg" in html and "data-route-kind=\"route\"" in html:
            refs.append(str(path))
    return refs


def conversation_source_refs(payload: Mapping[str, Any]) -> list[str]:
    refs = source_ref_objects(payload.get("source_refs"))
    for item in mapping_list(payload.get("timeline")):
        refs.extend(
            [
                text(item.get("source_ref")),
                text(item.get("receipt_ref")),
                text(item.get("payload_ref")),
            ]
        )
    return dedupe_text(refs)


def terminal_log_refs(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sources = [
        dict(item)
        for item in snapshot.get("stream_sources") or []
        if isinstance(item, Mapping) and item.get("topic") in {"terminal.tail", "log.tail"}
    ]
    if not sources:
        for study in snapshot.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            for key, topic in (("terminal_sources", "terminal.tail"), ("log_sources", "log.tail")):
                for source in study.get(key) or []:
                    if isinstance(source, Mapping):
                        item = dict(source)
                        item["topic"] = topic
                        item["study_id"] = study.get("study_id")
                        sources.append(item)
    readable = [
        source
        for source in sources
        if text(source.get("source_ref")) and source.get("status", source.get("source_status")) == "available"
    ]
    return {
        "status": "passed" if readable and len(readable) == len(sources) else "blocked",
        "refs": [
            {
                "topic": text(source.get("topic")),
                "study_id": text(source.get("study_id")),
                "source_ref": text(source.get("source_ref")),
                "status": text(source.get("status")) or text(source.get("source_status")),
            }
            for source in sources
        ],
    }
