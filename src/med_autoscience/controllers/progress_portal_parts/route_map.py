from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from .rendering import status_chip
from .source_refs import source_ref_allowed
from .status_display import display_text


SURFACE_KIND = "mas_progress_portal_route_map"


def build_route_map_payload(
    *,
    route_decision_trail: Mapping[str, Any],
    path_stage: Mapping[str, Any],
    artifact_groups: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    route_trail = _mapping(route_decision_trail)
    route_nodes = _mapping_list(route_trail.get("nodes"))
    route_refs = _string_list(route_trail.get("source_refs"))
    receipt_policy = _safe_action_receipt_policy()
    if _non_empty_text(route_trail.get("status")) != "available" or not route_nodes or not route_refs:
        return {
            "schema_version": 1,
            "surface_kind": SURFACE_KIND,
            "status": "missing",
            "study_id": study_id,
            "active_path": _non_empty_text(route_trail.get("active_path")),
            "winning_path": _non_empty_text(route_trail.get("winning_path")),
            "superseded_paths": [],
            "blockers": [],
            "nodes": [],
            "edges": [],
            "source_refs": _dedupe_strings(ref for ref in route_refs if source_ref_allowed(ref)),
            "conditions": {"missing": ["route_lineage"], "stale": [], "conflict": []},
            "safe_action_receipt_policy": receipt_policy,
            "authority": _authority(),
        }

    active_path = _non_empty_text(route_trail.get("active_path"))
    winning_path = _non_empty_text(route_trail.get("winning_path"))
    superseded_paths = _string_list(_mapping(route_trail.get("paths")).get("superseded"))
    blockers = _mapping_list(route_trail.get("blockers"))
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    source_refs = _dedupe_strings(ref for ref in route_refs if source_ref_allowed(ref))
    conversation_refs: list[str] = []

    stage_node = _stage_node(path_stage=path_stage, source_refs=source_refs, conversation_refs=conversation_refs)
    if stage_node:
        nodes.append(stage_node)

    previous_route_id: str | None = stage_node.get("id") if stage_node else None
    superseded_edges: list[tuple[str, str, list[str]]] = []
    for index, route in enumerate(route_nodes, start=1):
        route_node = _route_node(
            route,
            index=index,
            active_path=active_path,
            winning_path=winning_path,
            source_refs=source_refs,
            conversation_refs=conversation_refs,
        )
        nodes.append(route_node)
        if previous_route_id:
            edges.append(_edge(previous_route_id, route_node["id"], kind="advance", label="推进", source_refs=source_refs))
        previous_route_id = route_node["id"]
        superseded_by = _non_empty_text(route.get("superseded_by"))
        if superseded_by:
            superseded_edges.append((route_node["id"], superseded_by, _route_source_refs(route, fallback_refs=source_refs)))

        decision_node = _decision_node(
            route,
            route_node=route_node,
            source_refs=source_refs,
            conversation_refs=conversation_refs,
        )
        if decision_node:
            nodes.append(decision_node)
            edges.append(_edge(route_node["id"], decision_node["id"], kind="advance", label="决策", source_refs=source_refs))

        blocked = _non_empty_text(route.get("blocked_reason"))
        if blocked and decision_node:
            blocker_node = _blocker_node(
                route,
                decision_node=decision_node,
                source_refs=source_refs,
                conversation_refs=conversation_refs,
            )
            nodes.append(blocker_node)
            edges.append(_edge(decision_node["id"], blocker_node["id"], kind="blocked", label="阻塞", source_refs=source_refs))

    route_node_ids = {
        _non_empty_text(node.get("route_id")): _non_empty_text(node.get("id"))
        for node in nodes
        if node.get("kind") == "route" and _non_empty_text(node.get("route_id")) and _non_empty_text(node.get("id"))
    }
    for from_id, target_route_id, edge_refs in superseded_edges:
        target_id = route_node_ids.get(target_route_id)
        if target_id:
            edges.append(_edge(from_id, target_id, kind="superseded_by", label="被替代", source_refs=edge_refs))

    artifact_nodes = _artifact_nodes(artifact_groups)
    if artifact_nodes and nodes:
        anchor_id = nodes[-1]["id"]
        for artifact_node in artifact_nodes[:4]:
            nodes.append(artifact_node)
            edges.append(
                _edge(
                    anchor_id,
                    artifact_node["id"],
                    kind="artifact_generated",
                    label="产物生成",
                    source_refs=artifact_node["source_refs"],
                )
            )

    nodes = _dedupe_nodes(nodes)
    edges = _dedupe_edges(edges)
    missing: list[str] = []
    if not nodes:
        missing.append("route_map_nodes")
    if not edges:
        missing.append("route_map_edges")
    if not source_refs:
        missing.append("route_map_source_refs")
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": "available" if nodes and edges and source_refs else "missing",
        "study_id": study_id,
        "active_path": active_path,
        "winning_path": winning_path,
        "superseded_paths": superseded_paths,
        "blockers": blockers,
        "nodes": nodes,
        "edges": edges,
        "source_refs": source_refs,
        "conditions": {"missing": missing, "stale": [], "conflict": []},
        "safe_action_receipt_policy": receipt_policy,
        "authority": _authority(),
    }


def render_route_map_section(payload: Mapping[str, Any]) -> str:
    status = _non_empty_text(payload.get("status")) or "missing"
    if status != "available":
        return (
            '<section class="panel wide route-map-panel">'
            "<h2>研究路线地图 "
            + status_chip(status)
            + "</h2>"
            "<p>缺少研究路线来源。本页面不从阶段文案、文件名或产物路径猜测路线。</p>"
            + _source_ref_list(_string_list(payload.get("source_refs")))
            + "</section>"
        )
    nodes = _mapping_list(payload.get("nodes"))
    edges = _mapping_list(payload.get("edges"))
    width = max(760, 210 * max(len(nodes), 1))
    height = 270
    coordinates = _node_coordinates(nodes)
    svg_parts = [
        '<svg class="route-map-svg" role="img" aria-label="研究路线地图" viewBox="0 0 '
        + str(width)
        + " "
        + str(height)
        + '" preserveAspectRatio="xMinYMin meet">',
        '<defs><marker id="route-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs>',
    ]
    for edge in edges:
        svg_parts.extend(_edge_svg(edge, coordinates))
    for node in nodes:
        svg_parts.append(_node_svg(node, coordinates.get(_non_empty_text(node.get("id")) or "")))
    svg_parts.append("</svg>")
    return "\n".join(
        [
            '<section class="panel wide route-map-panel">',
            "<h2>研究路线地图 " + status_chip(status) + "</h2>",
            '<div class="route-map-shell" data-active-path="'
            + escape(_non_empty_text(payload.get("active_path")) or "", quote=True)
            + '" data-winning-path="'
            + escape(_non_empty_text(payload.get("winning_path")) or "", quote=True)
            + '">',
            *svg_parts,
            "</div>",
            _route_map_legend(nodes),
            _route_map_details(nodes),
            _source_ref_list(_string_list(payload.get("source_refs"))[:12]),
            "</section>",
        ]
    )


def _authority() -> dict[str, Any]:
    return {
        "kind": "read_only_route_map_projection",
        "writes_authority_surface": False,
        "can_execute_controller_actions": False,
        "forbidden_authority": [
            "study_truth",
            "publication_judgment",
            "quality_verdict",
            "runtime_authority",
            "artifact_authority",
            "controller_decision_authority",
        ],
    }


def _safe_action_receipt_policy() -> dict[str, Any]:
    return {
        "policy": "route_only_to_owner_no_direct_execution",
        "required_receipt_surface": "mas_progress_portal_action_receipt",
        "allowed_receipt_owners": [
            "mas_runtime_owner",
            "mas_controller",
            "MedAutoScience",
            "OPL provider transport",
        ],
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_mutation": False,
        "missing_behavior": "display_missing_do_not_infer",
    }


def _stage_node(
    *,
    path_stage: Mapping[str, Any],
    source_refs: list[str],
    conversation_refs: list[str],
) -> dict[str, Any]:
    stage = _first_text(path_stage.get("current_stage"), path_stage.get("paper_stage"))
    if stage is None:
        return {}
    summary = _first_text(path_stage.get("current_stage_summary"), path_stage.get("paper_stage_summary"))
    return _node(
        node_id="stage-current",
        kind="stage",
        label=f"当前阶段：{display_text(stage, empty_text='阶段未提供', preserve_known_token=False)}",
        status="current",
        summary=summary or "当前阶段摘要未提供。",
        source_refs=source_refs,
        conversation_refs=conversation_refs,
    )


def _route_node(
    route: Mapping[str, Any],
    *,
    index: int,
    active_path: str | None,
    winning_path: str | None,
    source_refs: list[str],
    conversation_refs: list[str],
) -> dict[str, Any]:
    route_id = _non_empty_text(route.get("route_id")) or f"route-{index}"
    blocked = bool(_non_empty_text(route.get("blocked_reason")))
    superseded = _non_empty_text(route.get("superseded_by"))
    status = "blocked" if blocked else "superseded" if superseded else "available"
    if route_id == active_path:
        status = "active"
    if route_id == winning_path:
        status = "winning" if status == "available" else status
    path_status = _non_empty_text(route.get("path_status")) or status
    if route_id == active_path and route_id == winning_path:
        path_status = "active_winning"
    summary = _first_text(route.get("evidence_point"), route.get("pivot_rationale"), route.get("decision"))
    return _node(
        node_id=f"route-{_slug(route_id)}",
        kind="route",
        label=_first_text(route.get("label"), route.get("route_id")) or route_id,
        status=status,
        summary=summary or "路线摘要未提供。",
        source_refs=_route_source_refs(route, fallback_refs=source_refs),
        conversation_refs=conversation_refs,
        route_id=route_id,
        path_status=path_status,
        blocker_reason=_first_text(route.get("blocker_reason"), route.get("blocked_reason")),
        next_owner=_non_empty_text(route.get("next_owner")),
    )


def _decision_node(
    route: Mapping[str, Any],
    *,
    route_node: Mapping[str, Any],
    source_refs: list[str],
    conversation_refs: list[str],
) -> dict[str, Any]:
    decision = _non_empty_text(route.get("decision"))
    pivot = _non_empty_text(route.get("pivot_rationale"))
    evidence = _non_empty_text(route.get("evidence_point"))
    if not decision and not pivot and not evidence:
        return {}
    route_id = _non_empty_text(route_node.get("route_id")) or _non_empty_text(route_node.get("id")) or "route"
    summary_parts = []
    if decision:
        summary_parts.append(f"决策：{decision}")
    if evidence:
        summary_parts.append(f"依据：{evidence}")
    if pivot:
        summary_parts.append(f"切换理由：{pivot}")
    return _node(
        node_id=f"decision-{_slug(route_id)}",
        kind="decision",
        label="路线决策",
        status=_non_empty_text(route_node.get("status")) or "available",
        summary="；".join(summary_parts),
        source_refs=source_refs,
        conversation_refs=conversation_refs,
    )


def _blocker_node(
    route: Mapping[str, Any],
    *,
    decision_node: Mapping[str, Any],
    source_refs: list[str],
    conversation_refs: list[str],
) -> dict[str, Any]:
    route_id = _non_empty_text(decision_node.get("id")) or "route"
    return _node(
        node_id=f"blocker-{_slug(route_id)}",
        kind="blocker",
        label="阻塞",
        status="blocked",
        summary=_non_empty_text(route.get("blocked_reason")) or "阻塞原因未提供。",
        source_refs=source_refs,
        conversation_refs=conversation_refs,
    )


def _artifact_nodes(artifact_groups: Mapping[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for group_name, group in artifact_groups.items():
        mapped = _mapping(group)
        items = _mapping_list(mapped.get("items"))
        if not items:
            continue
        refs = _dedupe_strings(
            _non_empty_text(item.get("ref")) for item in items if source_ref_allowed(_non_empty_text(item.get("ref")) or "")
        )
        if not refs:
            continue
        nodes.append(
            _node(
                node_id=f"artifact-{_slug(str(group_name))}",
                kind="artifact",
                label=_first_text(mapped.get("label"), str(group_name)) or str(group_name),
                status=_non_empty_text(mapped.get("status")) or "available",
                summary="；".join(_first_text(item.get("label"), item.get("ref")) or "产物" for item in items[:3]),
                source_refs=refs,
                artifact_refs=refs,
            )
        )
    return nodes


def _node(
    *,
    node_id: str,
    kind: str,
    label: str,
    status: str,
    summary: str,
    source_refs: Iterable[str],
    artifact_refs: Iterable[str] | None = None,
    conversation_refs: Iterable[str] | None = None,
    route_id: str | None = None,
    time: str | None = None,
    path_status: str | None = None,
    blocker_reason: str | None = None,
    next_owner: str | None = None,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "kind": kind,
        "label": label,
        "status": status,
        "time": time,
        "summary": summary,
        "source_refs": _dedupe_strings(ref for ref in source_refs if ref),
        "artifact_refs": _dedupe_strings(artifact_refs or []),
        "conversation_refs": _dedupe_strings(conversation_refs or []),
        **({"route_id": route_id} if route_id else {}),
        **({"path_status": path_status} if path_status else {}),
        **({"blocker_reason": blocker_reason} if blocker_reason else {}),
        **({"next_owner": next_owner} if next_owner else {}),
    }


def _edge(from_id: str, to_id: str, *, kind: str, label: str, source_refs: Iterable[str]) -> dict[str, Any]:
    return {
        "from": from_id,
        "to": to_id,
        "kind": kind,
        "label": label,
        "status": "available",
        "source_refs": _dedupe_strings(source_refs),
    }


def _node_coordinates(nodes: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    coordinates: dict[str, tuple[int, int]] = {}
    for index, node in enumerate(nodes):
        node_id = _non_empty_text(node.get("id"))
        if node_id is None:
            continue
        x = 90 + index * 190
        y = 78 if index % 2 == 0 else 170
        coordinates[node_id] = (x, y)
    return coordinates


def _edge_svg(edge: Mapping[str, Any], coordinates: Mapping[str, tuple[int, int]]) -> list[str]:
    start = coordinates.get(_non_empty_text(edge.get("from")) or "")
    end = coordinates.get(_non_empty_text(edge.get("to")) or "")
    if not start or not end:
        return []
    return [
        '<path class="route-edge route-edge--'
        + escape(_slug(_non_empty_text(edge.get("kind")) or "advance"), quote=True)
        + '" d="M'
        + str(start[0] + 58)
        + " "
        + str(start[1])
        + " C "
        + str(start[0] + 112)
        + " "
        + str(start[1])
        + ", "
        + str(end[0] - 112)
        + " "
        + str(end[1])
        + ", "
        + str(end[0] - 58)
        + " "
        + str(end[1])
        + '" marker-end="url(#route-arrow)"><title>'
        + escape(_non_empty_text(edge.get("label")) or "路线连接")
        + "</title></path>"
    ]


def _node_svg(node: Mapping[str, Any], coordinate: tuple[int, int] | None) -> str:
    if coordinate is None:
        return ""
    node_id = _non_empty_text(node.get("id")) or "node"
    kind = _non_empty_text(node.get("kind")) or "unknown"
    status = _non_empty_text(node.get("status")) or "available"
    route_id = _non_empty_text(node.get("route_id")) or node_id
    label = display_text(node.get("label"), empty_text="节点", preserve_known_token=False)
    summary = display_text(node.get("summary"), empty_text="摘要未提供", preserve_known_token=False)
    x, y = coordinate
    return (
        '<a class="route-node-link" href="#route-node-detail-'
        + escape(_slug(node_id), quote=True)
        + '" aria-label="查看路线节点：'
        + escape(label, quote=True)
        + '">'
        '<g class="route-node route-node--'
        + escape(kind, quote=True)
        + " route-node-status--"
        + escape(status, quote=True)
        + '" data-route-id="'
        + escape(route_id, quote=True)
        + '" data-route-kind="'
        + escape(kind, quote=True)
        + '" data-route-status="'
        + escape(status, quote=True)
        + '" tabindex="0">'
        + f"<title>{escape(label)} - {escape(summary)}</title>"
        + f'<rect x="{x - 58}" y="{y - 32}" width="116" height="64" rx="8"></rect>'
        + f'<text x="{x}" y="{y - 6}" text-anchor="middle">{escape(_short(label, 14))}</text>'
        + f'<text class="route-node-meta" x="{x}" y="{y + 15}" text-anchor="middle">{escape(_short(_kind_label(kind), 12))}</text>'
        + "</g></a>"
    )


def _route_map_legend(nodes: list[dict[str, Any]]) -> str:
    kinds = _dedupe_strings(_non_empty_text(node.get("kind")) for node in nodes)
    items = "".join(f"<li>{escape(_kind_label(kind))}</li>" for kind in kinds)
    return '<div class="route-map-legend"><span>图例</span><ul>' + items + "</ul></div>"


def _route_map_details(nodes: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for node in nodes:
        node_id = _non_empty_text(node.get("id")) or "node"
        label = display_text(node.get("label"), empty_text="节点", preserve_known_token=False)
        summary = display_text(node.get("summary"), empty_text="摘要未提供", preserve_known_token=False)
        kind = _kind_label(_non_empty_text(node.get("kind")) or "")
        status = display_text(node.get("status"), empty_text="状态未提供", preserve_known_token=False)
        rows.append(
            '<li id="route-node-detail-'
            + escape(_slug(node_id), quote=True)
            + '"><strong>'
            + escape(label)
            + "</strong><span>"
            + escape(kind)
            + " / "
            + escape(status)
            + "</span><p>"
            + escape(summary)
            + "</p>"
            + _node_refs_html(node)
            + "</li>"
        )
    return '<ol class="route-map-details">' + "".join(rows) + "</ol>"


def _node_refs_html(node: Mapping[str, Any]) -> str:
    refs: list[str] = []
    source_refs = _string_list(node.get("source_refs"))
    artifact_refs = _string_list(node.get("artifact_refs"))
    conversation_refs = _string_list(node.get("conversation_refs"))
    if source_refs:
        refs.append("来源：" + "；".join(escape(ref) for ref in source_refs[:4]))
    if artifact_refs:
        refs.append("产物：" + "；".join(escape(ref) for ref in artifact_refs[:4]))
    if conversation_refs:
        links = "；".join(
            '<a href="#' + escape(ref, quote=True) + '">' + escape(ref) + "</a>"
            for ref in conversation_refs[:4]
        )
        refs.append("对话：" + links)
    if not refs:
        return ""
    return '<div class="route-node-refs">' + "".join("<span>" + item + "</span>" for item in refs) + "</div>"


def _source_ref_list(refs: list[str]) -> str:
    if not refs:
        return ""
    return "<h3>地图来源</h3><ul>" + "".join(f"<li>{escape(ref)}</li>" for ref in refs) + "</ul>"


def _first_route_node_id(nodes: list[dict[str, Any]]) -> str | None:
    for node in nodes:
        if node.get("kind") == "route":
            return _non_empty_text(node.get("id"))
    return None


def _route_source_refs(route: Mapping[str, Any], *, fallback_refs: list[str]) -> list[str]:
    refs = _dedupe_strings(
        [
            *_string_list(route.get("source_refs")),
            *_string_list(route.get("evidence_refs")),
            _non_empty_text(route.get("source_ref")),
            _non_empty_text(route.get("ref")),
        ]
    )
    allowed_refs = [ref for ref in refs if source_ref_allowed(ref)]
    return _dedupe_strings([*allowed_refs, *fallback_refs])


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in nodes:
        node_id = _non_empty_text(node.get("id"))
        if node_id is None or node_id in seen:
            continue
        seen.add(node_id)
        result.append(node)
    return result


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (
            _non_empty_text(edge.get("from")) or "",
            _non_empty_text(edge.get("to")) or "",
            _non_empty_text(edge.get("kind")) or "",
        )
        if not all(key) or key in seen:
            continue
        seen.add(key)
        result.append(edge)
    return result


def _kind_label(kind: str) -> str:
    return {
        "stage": "阶段",
        "route": "路线",
        "decision": "决策",
        "blocker": "阻塞",
        "artifact": "产物",
        "run": "执行回合",
    }.get(kind, kind)


def _short(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: max(limit - 1, 1)] + "…"


def _slug(value: str) -> str:
    result = []
    for char in value.lower():
        if char.isalnum():
            result.append(char)
        elif char in {"-", "_", ".", ":"}:
            result.append("-")
    return "".join(result).strip("-") or "node"


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dedupe_strings(values: Iterable[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = ["SURFACE_KIND", "build_route_map_payload", "render_route_map_section"]
