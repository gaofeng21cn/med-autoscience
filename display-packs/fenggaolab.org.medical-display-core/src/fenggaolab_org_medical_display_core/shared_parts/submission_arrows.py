from __future__ import annotations

from typing import Any


def _expanded_arrow_lane_intervals(
    boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    *,
    shared_y0: float,
    shared_y1: float,
    expansion: float,
) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    for box in boxes:
        lower = max(shared_y0, float(box["y0"]) - expansion)
        upper = min(shared_y1, float(box["y1"]) + expansion)
        if upper > lower:
            intervals.append((lower, upper))
    intervals.sort()
    return intervals


def _merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    merged: list[list[float]] = [[intervals[0][0], intervals[0][1]]]
    for lower, upper in intervals[1:]:
        current = merged[-1]
        if lower <= current[1]:
            current[1] = max(current[1], upper)
            continue
        merged.append([lower, upper])
    return [(float(lower), float(upper)) for lower, upper in merged]


def _arrow_lane_candidate_gaps(
    *,
    merged_occupied_intervals: list[tuple[float, float]],
    shared_y0: float,
    shared_y1: float,
) -> list[tuple[float, float]]:
    candidate_gaps: list[tuple[float, float]] = []
    cursor = shared_y0
    for lower, upper in merged_occupied_intervals:
        if lower > cursor:
            candidate_gaps.append((cursor, lower))
        cursor = max(cursor, upper)
    if cursor < shared_y1:
        candidate_gaps.append((cursor, shared_y1))
    return candidate_gaps


def _arrow_lane_target_y(
    *,
    shared_y0: float,
    shared_y1: float,
    left_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    right_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
) -> float:
    target_y = (shared_y0 + shared_y1) / 2.0
    left_span_y0 = min((float(box["y0"]) for box in left_occupied_boxes), default=shared_y0)
    right_span_y0 = min((float(box["y0"]) for box in right_occupied_boxes), default=shared_y0)
    left_span_y1 = max((float(box["y1"]) for box in left_occupied_boxes), default=shared_y1)
    right_span_y1 = max((float(box["y1"]) for box in right_occupied_boxes), default=shared_y1)
    shared_content_y0 = max(shared_y0, left_span_y0, right_span_y0)
    shared_content_y1 = min(shared_y1, left_span_y1, right_span_y1)
    if shared_content_y1 > shared_content_y0:
        return (shared_content_y0 + shared_content_y1) / 2.0
    return target_y


def _usable_arrow_lane_gaps(
    *,
    candidate_gaps: list[tuple[float, float]],
    shared_y0: float,
    shared_y1: float,
    lane_margin: float,
    edge_margin: float,
) -> list[tuple[float, float]]:
    usable_gaps: list[tuple[float, float]] = []
    for lower, upper in candidate_gaps:
        usable_lower = max(lower, shared_y0 + lane_margin)
        usable_upper = min(upper, shared_y1 - lane_margin)
        if edge_margin > 0.0:
            usable_lower = max(usable_lower, shared_y0 + edge_margin)
            usable_upper = min(usable_upper, shared_y1 - edge_margin)
        if usable_upper > usable_lower:
            usable_gaps.append((usable_lower, usable_upper))
    return usable_gaps


def _fallback_arrow_lane_gap(*, shared_y0: float, shared_y1: float, lane_margin: float) -> tuple[float, float]:
    lower_bound = shared_y0 + lane_margin
    upper_bound = shared_y1 - lane_margin
    if lower_bound > upper_bound:
        midpoint = (shared_y0 + shared_y1) / 2.0
        return midpoint, midpoint
    return lower_bound, upper_bound


def _build_submission_graphical_abstract_arrow_lane_spec(
    *,
    left_panel_box: dict[str, float],
    right_panel_box: dict[str, float],
    left_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    right_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    clearance_pt: float,
    arrow_half_height_pt: float,
    edge_proximity_pt: float | None = None,
) -> dict[str, Any]:
    shared_y0 = max(float(left_panel_box["y0"]), float(right_panel_box["y0"]))
    shared_y1 = min(float(left_panel_box["y1"]), float(right_panel_box["y1"]))
    if shared_y1 <= shared_y0:
        raise ValueError("submission_graphical_abstract panels must share a vertical overlap to place arrows")

    expansion = max(clearance_pt + arrow_half_height_pt, 0.0)
    merged_occupied_intervals = _merge_intervals(
        _expanded_arrow_lane_intervals(
            left_occupied_boxes,
            shared_y0=shared_y0,
            shared_y1=shared_y1,
            expansion=expansion,
        )
        + _expanded_arrow_lane_intervals(
            right_occupied_boxes,
            shared_y0=shared_y0,
            shared_y1=shared_y1,
            expansion=expansion,
        )
    )
    candidate_gaps = _arrow_lane_candidate_gaps(
        merged_occupied_intervals=merged_occupied_intervals,
        shared_y0=shared_y0,
        shared_y1=shared_y1,
    )
    target_y = _arrow_lane_target_y(
        shared_y0=shared_y0,
        shared_y1=shared_y1,
        left_occupied_boxes=left_occupied_boxes,
        right_occupied_boxes=right_occupied_boxes,
    )

    lane_margin = max(arrow_half_height_pt, 0.0)
    edge_margin = max(edge_proximity_pt or 0.0, 0.0)
    usable_gaps = _usable_arrow_lane_gaps(
        candidate_gaps=candidate_gaps,
        shared_y0=shared_y0,
        shared_y1=shared_y1,
        lane_margin=lane_margin,
        edge_margin=edge_margin,
    )

    if not usable_gaps:
        usable_gaps = [_fallback_arrow_lane_gap(shared_y0=shared_y0, shared_y1=shared_y1, lane_margin=lane_margin)]

    return {
        "target_y": float(target_y),
        "usable_gaps": [(float(lower), float(upper)) for lower, upper in usable_gaps],
    }


def _choose_shared_submission_graphical_abstract_arrow_lane(
    lane_specs: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> float:
    normalized_specs = [dict(spec) for spec in lane_specs if isinstance(spec, dict)]
    if not normalized_specs:
        raise ValueError("submission_graphical_abstract requires at least one adjacent panel pair")

    shared_intervals = [tuple(interval) for interval in normalized_specs[0]["usable_gaps"]]
    for spec in normalized_specs[1:]:
        next_intersection: list[tuple[float, float]] = []
        for current_lower, current_upper in shared_intervals:
            for candidate_lower, candidate_upper in spec["usable_gaps"]:
                overlap_lower = max(float(current_lower), float(candidate_lower))
                overlap_upper = min(float(current_upper), float(candidate_upper))
                if overlap_upper <= overlap_lower:
                    continue
                next_intersection.append((overlap_lower, overlap_upper))
        shared_intervals = next_intersection
        if not shared_intervals:
            break

    if not shared_intervals:
        raise ValueError(
            "submission_graphical_abstract arrows require a shared blank lane across all adjacent panel pairs"
        )

    target_y = sum(float(spec["target_y"]) for spec in normalized_specs) / len(normalized_specs)
    for lower, upper in shared_intervals:
        if lower <= target_y <= upper:
            return target_y
    best_lower, best_upper = min(
        shared_intervals,
        key=lambda gap: abs(((gap[0] + gap[1]) / 2.0) - target_y),
    )
    return (best_lower + best_upper) / 2.0
