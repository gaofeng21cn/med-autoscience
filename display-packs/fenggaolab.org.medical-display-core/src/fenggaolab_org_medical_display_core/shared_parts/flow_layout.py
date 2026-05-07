from __future__ import annotations

from dataclasses import dataclass
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


def _run_graphviz_json_payload(*, graph_name: str, dot_binary: str, dot_source: str) -> dict[str, Any]:
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
        return json.loads(json_path.read_text(encoding="utf-8"))


def _graphviz_bounding_box(*, payload: dict[str, Any], graph_name: str) -> tuple[float, float, float, float]:
    bb_text = str(payload.get("bb") or "").strip()
    try:
        bb_left, bb_bottom, bb_right, bb_top = [float(item) for item in bb_text.split(",")]
    except ValueError as exc:
        raise RuntimeError(f"dot layout for `{graph_name}` returned invalid bounding box: {bb_text}") from exc
    return bb_left, bb_bottom, bb_right, bb_top


def _graphviz_node_box_from_payload(item: object) -> _GraphvizNodeBox | None:
    if not isinstance(item, dict):
        return None
    name = str(item.get("name") or "").strip()
    pos_text = str(item.get("pos") or "").strip()
    width_text = str(item.get("width") or "").strip()
    height_text = str(item.get("height") or "").strip()
    if not name or not pos_text or not width_text or not height_text:
        return None
    try:
        center_x, center_y = [float(part) for part in pos_text.split(",", 1)]
        width_pt = float(width_text) * 72.0
        height_pt = float(height_text) * 72.0
    except ValueError:
        return None
    return _GraphvizNodeBox(
        node_id=name,
        x0=center_x - width_pt / 2.0,
        y0=center_y - height_pt / 2.0,
        x1=center_x + width_pt / 2.0,
        y1=center_y + height_pt / 2.0,
    )


def _run_graphviz_layout(*, graph_name: str, dot_source: str) -> _GraphvizLayout:
    dot_binary = shutil.which("dot")
    if dot_binary is None:
        raise RuntimeError(f"dot not found on PATH; required for `{graph_name}` graph layout")
    payload = _run_graphviz_json_payload(graph_name=graph_name, dot_binary=dot_binary, dot_source=dot_source)
    bb_left, bb_bottom, bb_right, bb_top = _graphviz_bounding_box(payload=payload, graph_name=graph_name)
    nodes: dict[str, _GraphvizNodeBox] = {}
    for item in payload.get("objects") or []:
        node_box = _graphviz_node_box_from_payload(item)
        if node_box is not None:
            nodes[node_box.node_id] = node_box
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
