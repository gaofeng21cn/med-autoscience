from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from .rendering import list_html, status_chip
from .source_refs import source_ref_allowed, source_refs
from .status_display import display_text


SURFACE_KIND = "mas_progress_portal_route_decision_trail"


def build_route_decision_trail_payload(
    progress: Mapping[str, Any] | None,
    runtime: Mapping[str, Any] | None,
    package: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any]:
    resolved_progress = _mapping(progress)
    resolved_runtime = _mapping(runtime)
    resolved_package = _mapping(package)
    resolved_study_id = _non_empty_text(study_id) or _non_empty_text(resolved_progress.get("study_id")) or "unknown-study"
    explicit = _explicit_trail(resolved_progress, resolved_runtime, resolved_package)
    controller = _controller_decision(resolved_progress)
    intervention_lane = _mapping(resolved_progress.get("intervention_lane"))
    graph = _candidate_path_graph(resolved_progress, controller)
    active_path = _active_path(explicit, controller, intervention_lane, graph)
    winning_path = _winning_path(explicit, controller, intervention_lane, graph, active_path)
    progress_refs = _mapping(resolved_progress.get("refs"))
    explicit_refs = _payload_source_refs(explicit)
    controller_refs = _payload_source_refs(controller)
    intervention_refs = _payload_source_refs(intervention_lane)
    graph_refs = _payload_source_refs(graph)
    refs = _dedupe_refs(
        explicit_refs
        + controller_refs
        + intervention_refs
        + graph_refs
        + _route_source_refs(progress_refs)
    )
    node_fallback_refs = controller_refs or explicit_refs or intervention_refs or graph_refs
    nodes = _route_nodes(
        explicit,
        controller,
        intervention_lane,
        graph,
        active_path=active_path,
        winning_path=winning_path,
        fallback_refs=node_fallback_refs,
    )
    edge_fallback_refs = explicit_refs + controller_refs + intervention_refs
    edges = _route_edges(nodes, edge_fallback_refs)
    blockers = _route_blockers(nodes, node_fallback_refs)
    paths = _route_paths(nodes=nodes, active_path=active_path, winning_path=winning_path)
    missing = _missing_route_conditions(
        explicit=explicit,
        controller=controller,
        intervention_lane=intervention_lane,
        graph=graph,
        nodes=nodes,
        active_path=active_path,
        winning_path=winning_path,
        refs=refs,
    )
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "authority": {
            "kind": "read_model_helper",
            "writes_authority_surface": False,
            "authority_note": (
                "Consumes explicit route/decision trail surfaces only; it does not infer medical quality, "
                "publication readiness, or controller decisions."
            ),
            "forbidden_authority": [
                "study_truth",
                "publication_judgment",
                "quality_verdict",
                "runtime_authority",
                "artifact_authority",
                "controller_decision_authority",
            ],
        },
        "study_id": resolved_study_id,
        "status": "available" if nodes and not missing else "missing",
        "active_path": active_path,
        "winning_path": winning_path,
        "next_owner": _next_owner(nodes=nodes, active_path=active_path, winning_path=winning_path),
        "paths": paths,
        "nodes": nodes,
        "edges": edges,
        "blockers": blockers,
        "source_refs": refs,
        "conditions": {"missing": missing, "stale": [], "conflict": []},
    }


def _missing_route_conditions(
    *,
    explicit: Mapping[str, Any],
    controller: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
    graph: Mapping[str, Any],
    nodes: list[dict[str, Any]],
    active_path: str | None,
    winning_path: str | None,
    refs: Iterable[str],
) -> list[str]:
    missing = []
    if not explicit and not controller and not intervention_lane and not graph:
        missing.append("route_decision_trail")
    if not nodes:
        missing.append("route_nodes")
    if nodes and not active_path:
        missing.append("active_path")
    if nodes and not winning_path:
        missing.append("winning_path")
    if (explicit or controller or intervention_lane or graph) and not list(refs):
        missing.append("route_source_refs")
    return missing


def render_route_decision_trail_section(payload: Mapping[str, Any]) -> str:
    nodes = _mapping_list(payload.get("nodes"))
    items = [_node_label(node) for node in nodes]
    refs = _string_list(payload.get("source_refs"))[:12]
    active_path = _non_empty_text(payload.get("active_path"))
    winning_path = _non_empty_text(payload.get("winning_path"))
    summary_items = []
    if active_path:
        summary_items.append(f"当前路线：{active_path}")
    if winning_path:
        summary_items.append(f"当前采用：{winning_path}")
    conditions = _mapping(payload.get("conditions"))
    missing = _string_list(conditions.get("missing"))
    if missing:
        summary_items.append("missing: " + ", ".join(missing))
    return "\n".join(
        [
            '<section class="panel wide route-decision-trail">',
            "<h2>路线 / 决策 "
            + status_chip(payload.get("status") or "missing")
            + "</h2>",
            list_html(summary_items, empty_text="当前没有路线投影。"),
            list_html(items, empty_text="缺少显式路线节点；本页面不从阶段摘要或文件名猜测研究路线。"),
            "<h3>路线来源</h3>",
            list_html(refs, empty_text="缺少路线来源；本页面不推断路线来源。"),
            "</section>",
        ]
    )


def _explicit_trail(*payloads: Mapping[str, Any]) -> dict[str, Any]:
    for payload in payloads:
        for key in ("route_decision_trail", "decision_trail", "route_trail"):
            candidate = _mapping(payload.get(key))
            if candidate:
                return candidate
    return {}


def _controller_decision(progress: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("controller_decision", "latest_controller_decision"):
        candidate = _mapping(progress.get(key))
        if candidate:
            return candidate
    nested = _mapping(progress.get("controller_decisions"))
    latest = _mapping(nested.get("latest"))
    if latest:
        return latest
    return _mapping(_explicit_trail(progress).get("controller_decision"))


def _candidate_path_graph(progress: Mapping[str, Any], controller: Mapping[str, Any]) -> dict[str, Any]:
    for payload in (progress, controller, _mapping(controller.get("study_line_decision"))):
        candidate = _mapping(payload.get("candidate_path_graph"))
        if candidate:
            return candidate
    explicit = _explicit_trail(progress)
    return _mapping(explicit.get("candidate_path_graph"))


def _route_nodes(
    explicit: Mapping[str, Any],
    controller: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
    graph: Mapping[str, Any],
    *,
    active_path: str | None,
    winning_path: str | None,
    fallback_refs: list[str],
) -> list[dict[str, Any]]:
    explicit_nodes = _mapping_list(explicit.get("nodes")) or _mapping_list(explicit.get("route_nodes"))
    nodes = [_normalize_node(node, index=index + 1, source="route_decision_trail.nodes") for index, node in enumerate(explicit_nodes)]
    graph_candidates = _mapping_list(graph.get("candidates"))
    if graph_candidates:
        for index, candidate in enumerate(graph_candidates):
            nodes.append(_node_from_candidate(candidate, index=index + 1, controller=controller))
    if not nodes and controller:
        node = _node_from_controller(controller)
        if node:
            nodes.append(node)
    if not nodes and intervention_lane:
        node = _node_from_intervention_lane(intervention_lane)
        if node:
            nodes.append(node)
    return [
        _enrich_node(node, active_path=active_path, winning_path=winning_path, fallback_refs=fallback_refs)
        for node in _dedupe_nodes(nodes)
    ]


def _normalize_node(node: Mapping[str, Any], *, index: int, source: str) -> dict[str, Any]:
    route_id = _first_text(node.get("route_id"), node.get("candidate_id"), node.get("line_id"), node.get("id")) or f"route-{index}"
    decision = _first_text(node.get("decision"), node.get("route_decision"), node.get("status"))
    return {
        "route_id": route_id,
        "label": _first_text(node.get("label"), node.get("title"), node.get("question")) or route_id,
        "decision": decision,
        "evidence_point": _first_text(node.get("evidence_point"), node.get("evidence_basis"), node.get("expected_artifact")),
        "blocked_reason": _first_text(node.get("blocked_reason"), node.get("blocker"), node.get("stop_rule")),
        "pivot_rationale": _first_text(node.get("pivot_rationale"), node.get("route_rationale"), node.get("rationale")),
        "superseded_by": _first_text(node.get("superseded_by"), node.get("replaced_by")),
        "next_owner": _first_text(node.get("next_owner"), node.get("owner"), node.get("route_owner")),
        "source_refs": _node_source_refs(node),
        "source": source,
    }


def _node_from_candidate(candidate: Mapping[str, Any], *, index: int, controller: Mapping[str, Any]) -> dict[str, Any]:
    route_id = _first_text(candidate.get("candidate_id"), candidate.get("line_id"), candidate.get("route_id")) or f"candidate-{index}"
    evidence_basis = _string_list(candidate.get("evidence_basis"))
    blockers = _string_list(controller.get("blockers"))
    decision = _non_empty_text(candidate.get("decision"))
    return {
        "route_id": route_id,
        "label": _first_text(candidate.get("question"), candidate.get("label"), candidate.get("title")) or route_id,
        "decision": decision,
        "evidence_point": "; ".join(evidence_basis) or _non_empty_text(candidate.get("expected_artifact")),
        "blocked_reason": _non_empty_text(candidate.get("stop_rule")) or ("; ".join(blockers) if decision in {"stop", "human_gate"} else None),
        "pivot_rationale": _first_text(controller.get("route_rationale"), controller.get("reason"), controller.get("route_control_decision")),
        "superseded_by": _non_empty_text(candidate.get("superseded_by")),
        "next_owner": _first_text(candidate.get("next_owner"), controller.get("next_owner")),
        "source_refs": _node_source_refs(candidate),
        "source": "candidate_path_graph.candidates",
    }


def _node_from_controller(controller: Mapping[str, Any]) -> dict[str, Any]:
    route_id = _first_text(controller.get("route_target"), controller.get("selected_line_id"), controller.get("route_decision"))
    if route_id is None:
        return {}
    return {
        "route_id": route_id,
        "label": _first_text(controller.get("route_key_question"), controller.get("requested_action"), controller.get("decision_type")) or route_id,
        "decision": _non_empty_text(controller.get("route_decision")),
        "evidence_point": _non_empty_text(controller.get("evidence_point")),
        "blocked_reason": "; ".join(_string_list(controller.get("blockers"))) or None,
        "pivot_rationale": _first_text(controller.get("route_rationale"), controller.get("reason"), controller.get("route_control_decision")),
        "superseded_by": None,
        "next_owner": _non_empty_text(controller.get("next_owner")),
        "source_refs": _node_source_refs(controller),
        "source": "controller_decision",
    }


def _node_from_intervention_lane(intervention_lane: Mapping[str, Any]) -> dict[str, Any]:
    route_id = _first_text(
        intervention_lane.get("route_target"),
        intervention_lane.get("lane_id"),
        intervention_lane.get("recommended_action_id"),
    )
    if route_id is None:
        return {}
    return {
        "route_id": route_id,
        "label": _first_text(
            intervention_lane.get("route_target_label"),
            intervention_lane.get("title"),
            intervention_lane.get("lane_id"),
        )
        or route_id,
        "decision": _first_text(intervention_lane.get("repair_mode"), intervention_lane.get("recommended_action_id")),
        "decision_role": "display_label_from_intervention_lane",
        "authority": False,
        "can_generate_action": False,
        "can_execute": False,
        "source_recommended_action_id": _non_empty_text(intervention_lane.get("recommended_action_id")),
        "evidence_point": _first_text(intervention_lane.get("route_key_question"), intervention_lane.get("summary")),
        "blocked_reason": _first_text(intervention_lane.get("blocked_reason"), intervention_lane.get("blocker")),
        "pivot_rationale": _first_text(intervention_lane.get("route_summary"), intervention_lane.get("summary")),
        "superseded_by": _non_empty_text(intervention_lane.get("superseded_by")),
        "next_owner": _first_text(intervention_lane.get("next_owner"), intervention_lane.get("owner")),
        "source_refs": _node_source_refs(intervention_lane),
        "source": "intervention_lane",
    }


def _enrich_node(
    node: Mapping[str, Any],
    *,
    active_path: str | None,
    winning_path: str | None,
    fallback_refs: list[str],
) -> dict[str, Any]:
    enriched = dict(node)
    route_id = _non_empty_text(enriched.get("route_id"))
    blocked_reason = _first_text(enriched.get("blocked_reason"), enriched.get("blocker_reason"))
    path_status = "available"
    if blocked_reason:
        path_status = "blocked"
    if _non_empty_text(enriched.get("superseded_by")):
        path_status = "superseded"
    if route_id and route_id == active_path and route_id == winning_path:
        path_status = "active_winning"
    elif route_id and route_id == active_path:
        path_status = "active"
    elif route_id and route_id == winning_path:
        path_status = "winning"
    explicit_refs = _string_list(enriched.get("source_refs"))
    refs = _dedupe_refs(explicit_refs or fallback_refs)
    enriched["node_kind"] = _non_empty_text(enriched.get("node_kind")) or "route"
    enriched["path_status"] = path_status
    enriched["blocker_reason"] = blocked_reason
    enriched["next_owner"] = _non_empty_text(enriched.get("next_owner"))
    enriched["source_refs"] = refs
    return enriched


def _route_edges(nodes: list[dict[str, Any]], fallback_refs: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    route_ids = {
        _non_empty_text(node.get("route_id"))
        for node in nodes
        if _non_empty_text(node.get("route_id"))
    }
    for node in nodes:
        route_id = _non_empty_text(node.get("route_id"))
        superseded_by = _non_empty_text(node.get("superseded_by"))
        if route_id is None or superseded_by is None or superseded_by not in route_ids:
            continue
        result.append(
            {
                "from": route_id,
                "to": superseded_by,
                "kind": "superseded_by",
                "status": "superseded",
                "label": f"{route_id} -> {superseded_by}",
                "source_refs": _dedupe_refs(_string_list(node.get("source_refs")) + fallback_refs),
            }
        )
    return result


def _route_blockers(nodes: list[dict[str, Any]], fallback_refs: list[str]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for node in nodes:
        route_id = _non_empty_text(node.get("route_id"))
        reason = _first_text(node.get("blocked_reason"), node.get("blocker_reason"))
        if route_id is None or reason is None:
            continue
        blockers.append(
            {
                "route_id": route_id,
                "reason": reason,
                "next_owner": _non_empty_text(node.get("next_owner")),
                "source_refs": _dedupe_refs(_string_list(node.get("source_refs")) or fallback_refs),
            }
        )
    return blockers


def _route_paths(
    *,
    nodes: list[dict[str, Any]],
    active_path: str | None,
    winning_path: str | None,
) -> dict[str, Any]:
    return {
        "active": active_path,
        "winning": winning_path,
        "superseded": [
            route_id
            for route_id in (
                _non_empty_text(node.get("route_id"))
                for node in nodes
                if _non_empty_text(node.get("superseded_by"))
            )
            if route_id is not None
        ],
    }


def _next_owner(
    *,
    nodes: list[dict[str, Any]],
    active_path: str | None,
    winning_path: str | None,
) -> str | None:
    for target in (winning_path, active_path):
        if target is None:
            continue
        for node in nodes:
            if _non_empty_text(node.get("route_id")) == target:
                owner = _non_empty_text(node.get("next_owner"))
                if owner is not None:
                    return owner
    for node in nodes:
        owner = _non_empty_text(node.get("next_owner"))
        if owner is not None:
            return owner
    return None


def _node_source_refs(node: Mapping[str, Any]) -> list[str]:
    return _payload_source_refs(node)


def _payload_source_refs(payload: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("source_refs", "evidence_refs", "artifact_refs", "receipt_refs"):
        refs.extend(_refs_from_ref_field(payload.get(key)))
    for key in ("source_ref", "evidence_ref", "artifact_ref", "receipt_ref", "ref"):
        refs.extend(_refs_from_ref_field(payload.get(key)))
    return _dedupe_refs(ref for ref in refs if source_ref_allowed(ref))


def _active_path(
    explicit: Mapping[str, Any],
    controller: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
    graph: Mapping[str, Any],
) -> str | None:
    return _first_text(
        explicit.get("active_path"),
        explicit.get("active_route"),
        controller.get("route_target"),
        controller.get("selected_line_id"),
        intervention_lane.get("route_target"),
        intervention_lane.get("lane_id"),
        graph.get("selected_candidate_id"),
    )


def _winning_path(
    explicit: Mapping[str, Any],
    controller: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
    graph: Mapping[str, Any],
    active_path: str | None,
) -> str | None:
    return _first_text(
        explicit.get("winning_path"),
        explicit.get("winning_route"),
        controller.get("winning_path"),
        graph.get("winning_candidate_id"),
        intervention_lane.get("winning_path"),
        active_path,
    )


def _node_label(node: Mapping[str, Any]) -> str:
    parts = [
        display_text(node.get("route_id"), empty_text="unknown-route", preserve_known_token=False),
        display_text(node.get("label"), empty_text="问题未提供", preserve_known_token=False),
    ]
    decision = _non_empty_text(node.get("decision"))
    if decision:
        parts.append(f"决策={decision}")
    evidence = _non_empty_text(node.get("evidence_point"))
    if evidence:
        parts.append(f"依据={evidence}")
    blocked = _non_empty_text(node.get("blocked_reason"))
    if blocked:
        parts.append(f"阻塞={blocked}")
    pivot = _non_empty_text(node.get("pivot_rationale"))
    if pivot:
        parts.append(f"切换理由={pivot}")
    superseded_by = _non_empty_text(node.get("superseded_by"))
    if superseded_by:
        parts.append(f"被替代为={superseded_by}")
    return " | ".join(parts)


def _route_source_refs(progress_refs: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "controller_decision",
        "controller_decision_path",
        "controller_decisions_path",
        "route_decision_path",
        "opl_runtime_owner_handoff_path",
        "runtime_status_summary_path",
        "study_truth_snapshot_path",
    ):
        refs.extend(_refs_from_ref_field(progress_refs.get(key)))
    return [ref for ref in refs if source_ref_allowed(ref)]


def _refs_from_ref_field(value: object) -> list[str]:
    text = _non_empty_text(value)
    if text is not None:
        return [text]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_refs_from_ref_field(item))
        return result
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        result: list[str] = []
        for item in value:
            result.extend(_refs_from_ref_field(item))
        return result
    return []


def _dedupe_refs(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for node in nodes:
        route_id = _non_empty_text(node.get("route_id"))
        if route_id is None:
            continue
        key = (route_id, _non_empty_text(node.get("decision")))
        if key in seen:
            continue
        seen.add(key)
        result.append(node)
    return result


def _first_text(*values: object) -> str | None:
    for value in values:
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            text = "; ".join(_string_list(value))
        else:
            text = _non_empty_text(value)
        if text:
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
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "SURFACE_KIND",
    "build_route_decision_trail_payload",
    "render_route_decision_trail_section",
]
