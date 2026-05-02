from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
from typing import Any

import matplotlib
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

from med_autoscience.display_pack_resolver import get_pack_id, get_template_short_id


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _require_namespaced_registry_id(identifier: str, *, label: str) -> tuple[str, str]:
    try:
        pack_id = get_pack_id(identifier)
        short_id = get_template_short_id(identifier)
    except ValueError as exc:
        raise ValueError(f"{label} must be namespaced as '<pack_id>::<template_id>'") from exc
    return pack_id, short_id


def _read_bool_override(mapping: dict[str, Any], key: str, default: bool) -> bool:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    return default


def _require_non_empty_string(value: object, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    return normalized


def _require_numeric_value(value: object, *, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _require_non_negative_int(value: object, *, label: str, allow_zero: bool = True) -> int:
    numeric_value = _require_numeric_value(value, label=label)
    if not float(numeric_value).is_integer():
        raise ValueError(f"{label} must be an integer")
    normalized = int(numeric_value)
    if normalized < 0 or (normalized == 0 and not allow_zero):
        comparator = ">= 1" if not allow_zero else ">= 0"
        raise ValueError(f"{label} must be {comparator}")
    return normalized


def _format_percent_1dp(*, numerator: int, denominator: int) -> str:
    percent = (Decimal(numerator) * Decimal("100")) / Decimal(denominator)
    return f"{percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"


@dataclass(frozen=True)
class _FlowTextLine:
    text: str
    font_size: float
    font_weight: str
    color: str
    gap_before: float = 0.0


@dataclass(frozen=True)
class _FlowNodeSpec:
    node_id: str
    box_id: str
    box_type: str
    panel_role: str
    fill_color: str
    edge_color: str
    linewidth: float
    lines: tuple[_FlowTextLine, ...]
    width_pt: float
    padding_pt: float


@dataclass(frozen=True)
class _GraphvizNodeBox:
    node_id: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class _GraphvizLayout:
    width_pt: float
    height_pt: float
    nodes: dict[str, _GraphvizNodeBox]


@lru_cache(maxsize=4)
def _flow_font_path(font_weight: str) -> str:
    normalized_weight = str(font_weight or "normal").strip().lower()
    filename = "DejaVuSans-Bold.ttf" if "bold" in normalized_weight else "DejaVuSans.ttf"
    font_path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / filename
    if not font_path.exists():
        raise FileNotFoundError(f"matplotlib bundled flow font is missing: {font_path}")
    return str(font_path)


def _flow_font_properties(*, font_weight: str) -> FontProperties:
    return FontProperties(fname=_flow_font_path(font_weight), weight=font_weight)


def _measure_flow_text_width_pt(text: str, *, font_size: float, font_weight: str) -> float:
    if not text:
        return 0.0
    path = TextPath((0.0, 0.0), text, size=font_size, prop=_flow_font_properties(font_weight=font_weight))
    return float(path.get_extents().width)


def _wrap_flow_text_to_width(
    value: str,
    *,
    max_width_pt: float,
    font_size: float,
    font_weight: str,
    max_chars: int | None = None,
) -> tuple[str, ...]:
    normalized = " ".join(str(value or "").split())
    if not normalized:
        return tuple()
    words = normalized.split(" ")
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate_words = [*current, word]
        candidate = " ".join(candidate_words)
        if current and _measure_flow_text_width_pt(candidate, font_size=font_size, font_weight=font_weight) > max_width_pt:
            lines.append(" ".join(current))
            current = [word]
            continue
        current = candidate_words
    if current:
        lines.append(" ".join(current))
    if max_chars is None or max_chars <= 0:
        return tuple(lines)
    normalized_lines: list[str] = []
    for line in lines:
        if len(line) <= max_chars:
            normalized_lines.append(line)
            continue
        normalized_lines.extend(
            textwrap.wrap(
                line,
                width=max_chars,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    return tuple(normalized_lines)


def _wrap_figure_title_to_width(
    title: str,
    *,
    max_width_pt: float,
    font_size: float,
    font_weight: str = "bold",
) -> tuple[str, int]:
    lines = _wrap_flow_text_to_width(
        title,
        max_width_pt=max_width_pt,
        font_size=font_size,
        font_weight=font_weight,
    )
    if not lines:
        return "", 0
    return "\n".join(lines), len(lines)


def _flow_html_label_for_node(spec: _FlowNodeSpec) -> str:
    parts = [
        (
            f'<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="{int(round(spec.padding_pt))}" '
            f'COLOR="{spec.edge_color}" BGCOLOR="{spec.fill_color}" STYLE="ROUNDED" '
            f'WIDTH="{int(round(spec.width_pt))}">'
        )
    ]
    for line in spec.lines:
        if line.gap_before > 0:
            parts.append(f'<TR><TD HEIGHT="{int(round(line.gap_before))}"></TD></TR>')
        escaped_text = html.escape(line.text)
        font_attrs = [f'POINT-SIZE="{line.font_size:.2f}"', f'COLOR="{line.color}"']
        font_open = "<FONT " + " ".join(font_attrs) + ">"
        if line.font_weight == "bold":
            font_payload = f"{font_open}<B>{escaped_text}</B></FONT>"
        else:
            font_payload = f"{font_open}{escaped_text}</FONT>"
        parts.append(f'<TR><TD ALIGN="LEFT">{font_payload}</TD></TR>')
    parts.append("</TABLE>")
    return "<" + "".join(parts) + ">"


def _run_graphviz_layout(*, graph_name: str, dot_source: str) -> _GraphvizLayout:
    dot_binary = shutil.which("dot")
    if dot_binary is None:
        raise RuntimeError(f"dot not found on PATH; required for `{graph_name}` graph layout")
    with tempfile.TemporaryDirectory(prefix=f"medautosci-{graph_name}-") as tmpdir:
        dot_path = Path(tmpdir) / f"{graph_name}.dot"
        json_path = Path(tmpdir) / f"{graph_name}.json"
        dot_path.write_text(dot_source, encoding="utf-8")
        completed = subprocess.run(
            [dot_binary, "-Tjson", str(dot_path), "-o", str(json_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"dot layout failed for `{graph_name}`: {stderr or 'unknown graphviz error'}")
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    bb_text = str(payload.get("bb") or "").strip()
    try:
        bb_left, bb_bottom, bb_right, bb_top = [float(item) for item in bb_text.split(",")]
    except ValueError as exc:
        raise RuntimeError(f"dot layout for `{graph_name}` returned invalid bounding box: {bb_text}") from exc
    nodes: dict[str, _GraphvizNodeBox] = {}
    for item in payload.get("objects") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        pos_text = str(item.get("pos") or "").strip()
        width_text = str(item.get("width") or "").strip()
        height_text = str(item.get("height") or "").strip()
        if not name or not pos_text or not width_text or not height_text:
            continue
        try:
            center_x, center_y = [float(part) for part in pos_text.split(",", 1)]
            width_pt = float(width_text) * 72.0
            height_pt = float(height_text) * 72.0
        except ValueError:
            continue
        nodes[name] = _GraphvizNodeBox(
            node_id=name,
            x0=center_x - width_pt / 2.0,
            y0=center_y - height_pt / 2.0,
            x1=center_x + width_pt / 2.0,
            y1=center_y + height_pt / 2.0,
        )
    return _GraphvizLayout(width_pt=bb_right - bb_left, height_pt=bb_top - bb_bottom, nodes=nodes)


def _flow_box_to_normalized(
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    canvas_width_pt: float,
    canvas_height_pt: float,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": float(min(x0, x1) / canvas_width_pt),
        "y0": float(min(y0, y1) / canvas_height_pt),
        "x1": float(max(x0, x1) / canvas_width_pt),
        "y1": float(max(y0, y1) / canvas_height_pt),
    }


def _flow_union_box(*, boxes: list[dict[str, float]], box_id: str, box_type: str) -> dict[str, float]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": min(item["x0"] for item in boxes),
        "y0": min(item["y0"] for item in boxes),
        "x1": max(item["x1"] for item in boxes),
        "y1": max(item["y1"] for item in boxes),
    }


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
    def _collect_expanded_intervals(boxes: list[dict[str, float]] | tuple[dict[str, float], ...]) -> list[tuple[float, float]]:
        intervals: list[tuple[float, float]] = []
        expansion = max(clearance_pt + arrow_half_height_pt, 0.0)
        for box in boxes:
            lower = max(shared_y0, float(box["y0"]) - expansion)
            upper = min(shared_y1, float(box["y1"]) + expansion)
            if upper <= lower:
                continue
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

    shared_y0 = max(float(left_panel_box["y0"]), float(right_panel_box["y0"]))
    shared_y1 = min(float(left_panel_box["y1"]), float(right_panel_box["y1"]))
    if shared_y1 <= shared_y0:
        raise ValueError("submission_graphical_abstract panels must share a vertical overlap to place arrows")

    merged_occupied_intervals = _merge_intervals(
        _collect_expanded_intervals(left_occupied_boxes) + _collect_expanded_intervals(right_occupied_boxes)
    )
    candidate_gaps: list[tuple[float, float]] = []
    cursor = shared_y0
    for lower, upper in merged_occupied_intervals:
        if lower > cursor:
            candidate_gaps.append((cursor, lower))
        cursor = max(cursor, upper)
    if cursor < shared_y1:
        candidate_gaps.append((cursor, shared_y1))

    target_y = (shared_y0 + shared_y1) / 2.0
    left_span_y0 = min((float(box["y0"]) for box in left_occupied_boxes), default=shared_y0)
    right_span_y0 = min((float(box["y0"]) for box in right_occupied_boxes), default=shared_y0)
    left_span_y1 = max((float(box["y1"]) for box in left_occupied_boxes), default=shared_y1)
    right_span_y1 = max((float(box["y1"]) for box in right_occupied_boxes), default=shared_y1)
    shared_content_y0 = max(shared_y0, left_span_y0, right_span_y0)
    shared_content_y1 = min(shared_y1, left_span_y1, right_span_y1)
    if shared_content_y1 > shared_content_y0:
        target_y = (shared_content_y0 + shared_content_y1) / 2.0

    lane_margin = max(arrow_half_height_pt, 0.0)
    edge_margin = max(edge_proximity_pt or 0.0, 0.0)
    usable_gaps: list[tuple[float, float]] = []
    for lower, upper in candidate_gaps:
        usable_lower = max(lower, shared_y0 + lane_margin)
        usable_upper = min(upper, shared_y1 - lane_margin)
        if edge_margin > 0.0:
            usable_lower = max(usable_lower, shared_y0 + edge_margin)
            usable_upper = min(usable_upper, shared_y1 - edge_margin)
        if usable_upper <= usable_lower:
            continue
        usable_gaps.append((usable_lower, usable_upper))

    if not usable_gaps:
        lower_bound = shared_y0 + lane_margin
        upper_bound = shared_y1 - lane_margin
        if lower_bound > upper_bound:
            lower_bound = upper_bound = (shared_y0 + shared_y1) / 2.0
        usable_gaps = [(lower_bound, upper_bound)]

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


def _bbox_to_layout_box(
    *,
    figure,
    bbox,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    x0, y0 = figure.transFigure.inverted().transform((bbox.x0, bbox.y0))
    x1, y1 = figure.transFigure.inverted().transform((bbox.x1, bbox.y1))
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": float(min(x0, x1)),
        "y0": float(min(y0, y1)),
        "x1": float(max(x0, x1)),
        "y1": float(max(y0, y1)),
    }


def _data_box_to_layout_box(
    *,
    axes,
    figure,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    left_bottom = axes.transData.transform((x0, y0))
    right_top = axes.transData.transform((x1, y1))
    bbox = matplotlib.transforms.Bbox.from_extents(left_bottom[0], left_bottom[1], right_top[0], right_top[1])
    return _bbox_to_layout_box(figure=figure, bbox=bbox, box_id=box_id, box_type=box_type)


def _data_point_to_figure_xy(*, axes, figure, x: float, y: float) -> tuple[float, float]:
    display_x, display_y = axes.transData.transform((x, y))
    figure_x, figure_y = figure.transFigure.inverted().transform((display_x, display_y))
    return float(figure_x), float(figure_y)


def _clip_line_segment_to_axes_window(
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> tuple[float, float, float, float] | None:
    dx = x1 - x0
    dy = y1 - y0
    t0 = 0.0
    t1 = 1.0
    for p, q in (
        (-dx, x0 - xmin),
        (dx, xmax - x0),
        (-dy, y0 - ymin),
        (dy, ymax - y0),
    ):
        if p == 0.0:
            if q < 0.0:
                return None
            continue
        t = q / p
        if p < 0.0:
            if t > t1:
                return None
            if t > t0:
                t0 = t
        else:
            if t < t0:
                return None
            if t < t1:
                t1 = t
    return (
        x0 + t0 * dx,
        y0 + t0 * dy,
        x0 + t1 * dx,
        y0 + t1 * dy,
    )


def _clip_reference_line_to_axes_window(
    *,
    reference_line: dict[str, Any] | None,
    axes,
) -> dict[str, Any] | None:
    if not isinstance(reference_line, dict):
        return None
    x_values = [float(value) for value in reference_line.get("x") or []]
    y_values = [float(value) for value in reference_line.get("y") or []]
    if len(x_values) != len(y_values):
        raise ValueError("reference_line.x and reference_line.y must have the same length")
    xmin, xmax = sorted(float(value) for value in axes.get_xlim())
    ymin, ymax = sorted(float(value) for value in axes.get_ylim())
    if len(x_values) == 1:
        x_value = x_values[0]
        y_value = y_values[0]
        if xmin <= x_value <= xmax and ymin <= y_value <= ymax:
            return {
                "x": [x_value],
                "y": [y_value],
                "label": str(reference_line.get("label") or "").strip(),
            }
        return None

    clipped_points: list[tuple[float, float]] = []
    for index in range(len(x_values) - 1):
        clipped_segment = _clip_line_segment_to_axes_window(
            x0=x_values[index],
            y0=y_values[index],
            x1=x_values[index + 1],
            y1=y_values[index + 1],
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
        )
        if clipped_segment is None:
            continue
        clipped_start = (clipped_segment[0], clipped_segment[1])
        clipped_end = (clipped_segment[2], clipped_segment[3])
        if not clipped_points or clipped_points[-1] != clipped_start:
            clipped_points.append(clipped_start)
        if clipped_points[-1] != clipped_end:
            clipped_points.append(clipped_end)
    if not clipped_points:
        return None
    return {
        "x": [point[0] for point in clipped_points],
        "y": [point[1] for point in clipped_points],
        "label": str(reference_line.get("label") or "").strip(),
    }


def _normalize_reference_line_to_device_space(
    *,
    reference_line: dict[str, Any] | None,
    axes,
    figure,
    clip_to_axes_window: bool = False,
) -> dict[str, Any] | None:
    if clip_to_axes_window:
        reference_line = _clip_reference_line_to_axes_window(reference_line=reference_line, axes=axes)
    if not isinstance(reference_line, dict):
        return None
    x_values = list(reference_line.get("x") or [])
    y_values = list(reference_line.get("y") or [])
    if len(x_values) != len(y_values):
        raise ValueError("reference_line.x and reference_line.y must have the same length")
    normalized_x: list[float] = []
    normalized_y: list[float] = []
    for x_value, y_value in zip(x_values, y_values, strict=True):
        figure_x, figure_y = _data_point_to_figure_xy(
            axes=axes,
            figure=figure,
            x=float(x_value),
            y=float(y_value),
        )
        normalized_x.append(figure_x)
        normalized_y.append(figure_y)
    return {
        "x": normalized_x,
        "y": normalized_y,
        "label": str(reference_line.get("label") or "").strip(),
    }


def _normalize_reference_line_collection_to_device_space(
    *,
    reference_lines: list[dict[str, Any]] | None,
    axes,
    figure,
) -> list[dict[str, Any]]:
    normalized_lines: list[dict[str, Any]] = []
    for item in reference_lines or []:
        normalized_line = _normalize_reference_line_to_device_space(
            reference_line=item,
            axes=axes,
            figure=figure,
        )
        if normalized_line is not None:
            normalized_lines.append(normalized_line)
    return normalized_lines


def _build_python_shap_layout_sidecar(
    *,
    figure,
    axes,
    colorbar,
    rows: list[dict[str, Any]],
    point_rows: list[dict[str, Any]],
    template_id: str,
) -> dict[str, Any]:
    renderer = figure.canvas.get_renderer()
    layout_boxes = []
    if str(axes.title.get_text() or "").strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=axes.title.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        )
    )
    panel_box = _bbox_to_layout_box(
        figure=figure,
        bbox=axes.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )
    x_min, x_max = axes.get_xlim()
    for row_index, row in enumerate(rows):
        row_box = _data_box_to_layout_box(
            axes=axes,
            figure=figure,
            x0=x_min,
            y0=row_index - 0.42,
            x1=x_max,
            y1=row_index + 0.42,
            box_id=f"feature_row_{row['feature']}",
            box_type="feature_row",
        )
        row_box["y0"] = max(float(row_box["y0"]), float(panel_box["y0"]))
        row_box["y1"] = min(float(row_box["y1"]), float(panel_box["y1"]))
        layout_boxes.append(row_box)
    zero_line_x, _ = _data_point_to_figure_xy(
        axes=axes,
        figure=figure,
        x=0.0,
        y=0.0,
    )
    guide_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        ),
        {
            "box_id": "zero_line",
            "box_type": "zero_line",
            "x0": zero_line_x,
            "y0": float(panel_box["y0"]),
            "x1": zero_line_x,
            "y1": float(panel_box["y1"]),
        },
    ]
    row_box_id_by_feature = {f"{row['feature']}": f"feature_row_{row['feature']}" for row in rows}
    feature_label_metrics: list[dict[str, Any]] = []
    for row, label_artist in zip(rows, axes.get_yticklabels()):
        label_box_id = f"feature_label_{row['feature']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="feature_label",
            )
        )
        feature_label_metrics.append(
            {
                "feature": str(row["feature"]),
                "row_box_id": row_box_id_by_feature[str(row["feature"])],
                "label_box_id": label_box_id,
            }
        )
    point_metrics: list[dict[str, Any]] = []
    for item in point_rows:
        figure_x, figure_y = _data_point_to_figure_xy(
            axes=axes,
            figure=figure,
            x=float(item["shap_value"]),
            y=float(item["row_position"]),
        )
        point_metrics.append(
            {
                "feature": str(item["feature"]),
                "row_box_id": row_box_id_by_feature[str(item["feature"])],
                "x": figure_x,
                "y": figure_y,
            }
        )
    return {
        "template_id": template_id,
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": layout_boxes,
        "panel_boxes": [panel_box],
        "guide_boxes": guide_boxes,
        "metrics": {
            "figure_height_inches": float(figure.get_figheight()),
            "figure_width_inches": float(figure.get_figwidth()),
            "feature_labels": feature_label_metrics,
            "points": point_metrics,
        },
    }


def _centered_offsets(count: int, *, half_span: float = 0.28) -> list[float]:
    if count <= 1:
        return [0.0]
    step = (half_span * 2.0) / float(count - 1)
    return [(-half_span + step * float(index)) for index in range(count)]


def _prepare_python_render_output_paths(*, output_png_path: Path, output_pdf_path: Path, layout_sidecar_path: Path) -> None:
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    layout_sidecar_path.parent.mkdir(parents=True, exist_ok=True)


def _prepare_python_illustration_output_paths(
    *,
    output_png_path: Path,
    output_svg_path: Path,
    layout_sidecar_path: Path,
) -> None:
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    layout_sidecar_path.parent.mkdir(parents=True, exist_ok=True)


def _apply_publication_axes_style(axes) -> None:
    axes.grid(axis="x", color="#e6edf2", linewidth=0.4)
    axes.grid(axis="y", visible=False)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
