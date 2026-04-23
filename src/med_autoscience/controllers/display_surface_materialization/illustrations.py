from __future__ import annotations

from .shared import Any, FontProperties, Path, TextPath, _REPO_ROOT, csv, dataclass, display_pack_runtime, display_registry, html, json, lru_cache, matplotlib, shutil, subprocess, tempfile, textwrap
from .renderers import _prepare_python_illustration_output_paths

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
        parts.append(f"<TR><TD ALIGN=\"LEFT\">{font_payload}</TD></TR>")
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

def _render_cohort_flow_figure(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    title: str,
    steps: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    endpoint_inventory: list[dict[str, Any]],
    design_panels: list[dict[str, Any]],
    render_context: dict[str, Any],
) -> None:
    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )
    template_id = display_registry.get_illustration_shell_spec("cohort_flow_figure").shell_id
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
    )
    render_callable(
        template_id=template_id,
        output_svg_path=output_svg_path,
        output_png_path=output_png_path,
        output_layout_path=output_layout_path,
        title=title,
        steps=steps,
        exclusions=exclusions,
        endpoint_inventory=endpoint_inventory,
        design_panels=design_panels,
        render_context=render_context,
    )

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

def _choose_submission_graphical_abstract_arrow_lane(
    *,
    left_panel_box: dict[str, float],
    right_panel_box: dict[str, float],
    left_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    right_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    clearance_pt: float,
    arrow_half_height_pt: float,
    edge_proximity_pt: float | None = None,
) -> float:
    lane_spec = _build_submission_graphical_abstract_arrow_lane_spec(
        left_panel_box=left_panel_box,
        right_panel_box=right_panel_box,
        left_occupied_boxes=left_occupied_boxes,
        right_occupied_boxes=right_occupied_boxes,
        clearance_pt=clearance_pt,
        arrow_half_height_pt=arrow_half_height_pt,
        edge_proximity_pt=edge_proximity_pt,
    )
    usable_gaps = list(lane_spec["usable_gaps"])
    target_y = float(lane_spec["target_y"])

    for lower, upper in usable_gaps:
        if lower <= target_y <= upper:
            return target_y
    best_lower, best_upper = min(
        usable_gaps,
        key=lambda gap: abs(((gap[0] + gap[1]) / 2.0) - target_y),
    )
    return (best_lower + best_upper) / 2.0

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

def _render_submission_graphical_abstract(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
) -> None:
    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )
    template_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
    )
    render_callable(
        template_id=template_id,
        output_svg_path=output_svg_path,
        output_png_path=output_png_path,
        output_layout_path=output_layout_path,
        shell_payload=shell_payload,
        render_context=render_context,
    )

def _write_rectangular_table_outputs(
    *,
    output_md_path: Path,
    title: str,
    headers: list[str],
    table_rows: list[list[str]],
    output_csv_path: Path | None = None,
) -> None:
    if output_csv_path is not None:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(table_rows)

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in table_rows:
        markdown_lines.append("| " + " | ".join(row) + " |")
    output_md_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

def _write_table_outputs(
    *,
    output_md_path: Path,
    title: str,
    column_labels: list[str],
    rows: list[dict[str, Any]],
    stub_header: str,
    output_csv_path: Path | None = None,
) -> None:
    headers = [stub_header, *column_labels]
    table_rows = [[row["label"], *row["values"]] for row in rows]
    _write_rectangular_table_outputs(
        output_md_path=output_md_path,
        title=title,
        headers=headers,
        table_rows=table_rows,
        output_csv_path=output_csv_path,
    )


__all__ = [
    "_FlowTextLine",
    "_FlowNodeSpec",
    "_GraphvizNodeBox",
    "_GraphvizLayout",
    "_flow_font_path",
    "_flow_font_properties",
    "_measure_flow_text_width_pt",
    "_wrap_flow_text_to_width",
    "_wrap_figure_title_to_width",
    "_flow_html_label_for_node",
    "_run_graphviz_layout",
    "_flow_box_to_normalized",
    "_flow_union_box",
    "_render_cohort_flow_figure",
    "_build_submission_graphical_abstract_arrow_lane_spec",
    "_choose_submission_graphical_abstract_arrow_lane",
    "_choose_shared_submission_graphical_abstract_arrow_lane",
    "_render_submission_graphical_abstract",
    "_write_rectangular_table_outputs",
    "_write_table_outputs",
]
