from __future__ import annotations

from html import escape
import json
import math
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any


def render_submission_graphical_abstract_gallery_preview(
    *,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
) -> None:
    width = 1800
    height = 1800
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    colors = _submission_colors(palette=palette, style_roles=style_roles)
    panels = [dict(item) for item in list(shell_payload.get("panels") or [])[:3]]
    footer_pills = [dict(item) for item in list(shell_payload.get("footer_pills") or [])]
    title = str(shell_payload.get("title") or "Submission graphical abstract").strip()

    panel_boxes = _panel_boxes(width=width, height=height, count=max(1, len(panels)))
    layout_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    svg_parts = [_svg_header(width=width, height=height)]
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="{colors["background"]}"/>')
    _append_text(
        svg_parts,
        layout_boxes,
        text=title,
        x=width * 0.06,
        y=height * 0.085,
        max_width=width * 0.88,
        font_size=44,
        font_weight="700",
        color=colors["text"],
        box_id="title",
        box_type="title",
        width=width,
        height=height,
    )

    for index, panel in enumerate(panels):
        panel_box = panel_boxes[index]
        accent = _role_color(panel.get("visual_role") or panel.get("panel_id"), index=index, colors=colors)
        panel_id = str(panel.get("panel_id") or f"panel_{index + 1}").strip() or f"panel_{index + 1}"
        panel_boxes[index]["box_id"] = f"panel_{panel_id}"
        panel_boxes[index]["box_type"] = "panel"
        _append_rect(
            svg_parts,
            panel_box,
            fill=colors["panel_fill"],
            stroke=accent,
            stroke_width=3,
            radius=26,
        )
        _append_badge(
            svg_parts,
            layout_boxes,
            label=str(panel.get("panel_label") or chr(65 + index)),
            box=_relative_box(panel_box, 0.055, 0.055, 0.155, 0.135),
            fill=accent,
            text_color="#FFFFFF",
            width=width,
            height=height,
            box_id=f"panel_label_{panel_id}",
            box_type="panel_label",
        )
        glyph_box = _relative_box(panel_box, 0.20, 0.13, 0.80, 0.43)
        _append_glyph(
            svg_parts,
            glyph_box,
            role=str(panel.get("visual_role") or ""),
            accent=accent,
            colors=colors,
        )
        layout_boxes.append(_normalized_box(glyph_box, width=width, height=height, box_id=f"visual_glyph_{panel_id}", box_type="visual_glyph"))
        _append_text(
            svg_parts,
            layout_boxes,
            text=str(panel.get("title") or ""),
            x=panel_box["x0"] + panel_box["w"] * 0.12,
            y=panel_box["y0"] + panel_box["h"] * 0.51,
            max_width=panel_box["w"] * 0.76,
            font_size=30,
            font_weight="700",
            color=colors["text"],
            box_id=f"panel_title_{panel_id}",
            box_type="panel_title",
            width=width,
            height=height,
        )
        _append_text(
            svg_parts,
            layout_boxes,
            text=str(panel.get("subtitle") or ""),
            x=panel_box["x0"] + panel_box["w"] * 0.12,
            y=panel_box["y0"] + panel_box["h"] * 0.595,
            max_width=panel_box["w"] * 0.76,
            font_size=21,
            font_weight="400",
            color=colors["muted"],
            box_id=f"panel_subtitle_{panel_id}",
            box_type="panel_subtitle",
            width=width,
            height=height,
            max_lines=2,
        )
        card = _first_card(panel)
        card_box = _relative_box(panel_box, 0.12, 0.74, 0.88, 0.92)
        _append_rect(svg_parts, card_box, fill=colors["card_fill"], stroke=colors["grid"], stroke_width=2, radius=22)
        layout_boxes.append(_normalized_box(card_box, width=width, height=height, box_id=f"card_{panel_id}", box_type="card_box"))
        _append_text(
            svg_parts,
            layout_boxes,
            text=str(card.get("title") or ""),
            x=card_box["x0"] + card_box["w"] * 0.08,
            y=card_box["y0"] + card_box["h"] * 0.27,
            max_width=card_box["w"] * 0.42,
            font_size=20,
            font_weight="400",
            color=colors["muted"],
            box_id=f"card_title_{panel_id}",
            box_type="card_title",
            width=width,
            height=height,
            max_lines=2,
        )
        _append_text(
            svg_parts,
            layout_boxes,
            text=str(card.get("value") or ""),
            x=card_box["x0"] + card_box["w"] * 0.52,
            y=card_box["y0"] + card_box["h"] * 0.36,
            max_width=card_box["w"] * 0.40,
            font_size=38,
            font_weight="700",
            color=accent,
            box_id=f"card_value_{panel_id}",
            box_type="card_value",
            width=width,
            height=height,
            max_lines=1,
        )
        _append_text(
            svg_parts,
            layout_boxes,
            text=str(card.get("detail") or ""),
            x=card_box["x0"] + card_box["w"] * 0.52,
            y=card_box["y0"] + card_box["h"] * 0.66,
            max_width=card_box["w"] * 0.40,
            font_size=18,
            font_weight="400",
            color=colors["muted"],
            box_id=f"card_detail_{panel_id}",
            box_type="card_detail",
            width=width,
            height=height,
            max_lines=1,
        )

    for index, (left, right) in enumerate(zip(panel_boxes, panel_boxes[1:], strict=False)):
        arrow_box = {
            "x0": left["x0"] + left["w"] + width * 0.012,
            "y0": left["y0"] + left["h"] * 0.345,
            "w": right["x0"] - (left["x0"] + left["w"]) - width * 0.024,
            "h": height * 0.035,
        }
        _append_arrow(svg_parts, arrow_box, color=colors["neutral"])
        guide_boxes.append(
            _normalized_box(
                arrow_box,
                width=width,
                height=height,
                box_id=f"arrow_connector_{index + 1}",
                box_type="arrow_connector",
            )
        )

    footer_boxes = _footer_boxes(width=width, height=height, pills=footer_pills)
    for pill, pill_box in zip(footer_pills, footer_boxes, strict=False):
        pill_id = str(pill.get("pill_id") or "").strip() or f"pill_{len(layout_boxes) + 1}"
        style_role = str(pill.get("style_role") or "neutral").strip().lower()
        fill = colors.get(f"{style_role}_soft", colors["light"])
        stroke = colors.get(style_role, colors["neutral"])
        _append_rect(svg_parts, pill_box, fill=fill, stroke=stroke, stroke_width=2, radius=22)
        layout_boxes.append(_normalized_box(pill_box, width=width, height=height, box_id=f"footer_pill_{pill_id}", box_type="footer_pill"))
        _append_text(
            svg_parts,
            layout_boxes,
            text=str(pill.get("label") or ""),
            x=pill_box["x0"] + pill_box["w"] * 0.08,
            y=pill_box["y0"] + pill_box["h"] * 0.58,
            max_width=pill_box["w"] * 0.84,
            font_size=19,
            font_weight="400",
            color=colors["text"],
            box_id=f"footer_pill_text_{pill_id}",
            box_type="footer_pill_text",
            width=width,
            height=height,
            max_lines=1,
        )

    svg_parts.append("</svg>\n")
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    output_svg_path.write_text("".join(svg_parts), encoding="utf-8")
    _render_svg_to_png(output_svg_path=output_svg_path, output_png_path=output_png_path, width=width, height=height)
    _write_layout(
        output_layout_path=output_layout_path,
        shell_payload=shell_payload,
        render_context=render_context,
        layout_boxes=layout_boxes,
        panel_boxes=[_normalized_box(item, width=width, height=height, box_id=item["box_id"], box_type="panel") for item in panel_boxes],
        guide_boxes=guide_boxes,
    )


def _submission_colors(*, palette: dict[str, Any], style_roles: dict[str, Any]) -> dict[str, str]:
    def color(key: str, fallback: str) -> str:
        return str(style_roles.get(key) or palette.get(key) or fallback).strip() or fallback

    return {
        "background": color("background", "#FFFFFF"),
        "text": color("text", "#13293D"),
        "muted": color("muted", "#64748B"),
        "grid": color("grid", "#E6EDF2"),
        "neutral": color("neutral", "#13293D"),
        "panel_fill": color("light", "#EEF4F7"),
        "card_fill": "#FFFFFF",
        "light": color("light", "#EEF4F7"),
        "primary": color("primary", "#245A6B"),
        "secondary": color("secondary", "#8B3A3A"),
        "contrast": color("contrast", "#2166AC"),
        "primary_soft": color("primary_soft", "#DCEBF0"),
        "secondary_soft": color("secondary_soft", "#F1DADA"),
        "contrast_soft": color("contrast_soft", "#DCE8F4"),
        "neutral_soft": color("light", "#EEF4F7"),
    }


def _panel_boxes(*, width: int, height: int, count: int) -> list[dict[str, float]]:
    margin_x = width * 0.055
    gap = width * 0.045
    top = height * 0.20
    panel_height = height * 0.585
    panel_width = (width - margin_x * 2.0 - gap * float(max(0, count - 1))) / float(count)
    return [
        {
            "x0": margin_x + index * (panel_width + gap),
            "y0": top,
            "w": panel_width,
            "h": panel_height,
        }
        for index in range(count)
    ]


def _footer_boxes(*, width: int, height: int, pills: list[dict[str, Any]]) -> list[dict[str, float]]:
    if not pills:
        return []
    margin_x = width * 0.12
    gap = width * 0.02
    pill_width = (width - margin_x * 2.0 - gap * float(len(pills) - 1)) / float(len(pills))
    y0 = height * 0.835
    return [
        {
            "x0": margin_x + index * (pill_width + gap),
            "y0": y0,
            "w": pill_width,
            "h": height * 0.06,
        }
        for index in range(len(pills))
    ]


def _relative_box(parent: dict[str, float], x0: float, y0: float, x1: float, y1: float) -> dict[str, float]:
    return {
        "x0": parent["x0"] + parent["w"] * x0,
        "y0": parent["y0"] + parent["h"] * y0,
        "w": parent["w"] * (x1 - x0),
        "h": parent["h"] * (y1 - y0),
    }


def _normalized_box(
    box: dict[str, float],
    *,
    width: int,
    height: int,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": float(box["x0"] / width),
        "y0": float(box["y0"] / height),
        "x1": float((box["x0"] + box["w"]) / width),
        "y1": float((box["y0"] + box["h"]) / height),
    }


def _first_card(panel: dict[str, Any]) -> dict[str, Any]:
    for row in list(panel.get("rows") or []):
        if not isinstance(row, dict):
            continue
        cards = list(row.get("cards") or [])
        if cards and isinstance(cards[0], dict):
            return dict(cards[0])
    return {"title": panel.get("title") or "", "value": "", "detail": ""}


def _role_color(role: object, *, index: int, colors: dict[str, str]) -> str:
    role_text = str(role or "").strip().lower()
    if role_text in {"population", "source_data", "cohort"}:
        return colors["primary"]
    if role_text in {"model_signal", "model", "algorithm", "mechanism"}:
        return colors["contrast"]
    if role_text in {"clinical_use", "decision", "action", "care_path"}:
        return colors["secondary"]
    return (colors["primary"], colors["contrast"], colors["secondary"])[index % 3]


def _svg_header(*, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        "<defs>\n"
        '<marker id="arrowhead" markerWidth="12" markerHeight="9" refX="10" refY="4.5" orient="auto">'
        '<path d="M0,0 L12,4.5 L0,9 Z" fill="#13293D"/></marker>\n'
        "</defs>\n"
    )


def _append_rect(parts: list[str], box: dict[str, float], *, fill: str, stroke: str, stroke_width: float, radius: float) -> None:
    parts.append(
        f'<rect x="{box["x0"]:.2f}" y="{box["y0"]:.2f}" width="{box["w"]:.2f}" height="{box["h"]:.2f}" '
        f'rx="{radius:.2f}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="{stroke_width:.2f}"/>\n'
    )


def _append_badge(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    label: str,
    box: dict[str, float],
    fill: str,
    text_color: str,
    width: int,
    height: int,
    box_id: str,
    box_type: str,
) -> None:
    _append_rect(parts, box, fill=fill, stroke=fill, stroke_width=0, radius=box["h"] / 2.0)
    parts.append(
        f'<text x="{box["x0"] + box["w"] / 2.0:.2f}" y="{box["y0"] + box["h"] * 0.66:.2f}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{box["h"] * 0.48:.2f}" font-weight="700" '
        f'fill="{escape(text_color)}" text-anchor="middle">{escape(label)}</text>\n'
    )
    layout_boxes.append(_normalized_box(box, width=width, height=height, box_id=box_id, box_type=box_type))


def _append_text(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_size: float,
    font_weight: str,
    color: str,
    box_id: str,
    box_type: str,
    width: int,
    height: int,
    max_lines: int = 3,
) -> None:
    lines = _wrap_text(text, max_width=max_width, font_size=font_size, max_lines=max_lines)
    line_height = font_size * 1.24
    for line_index, line in enumerate(lines):
        parts.append(
            f'<text x="{x:.2f}" y="{y + line_height * line_index:.2f}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.2f}" '
            f'font-weight="{escape(font_weight)}" fill="{escape(color)}">{escape(line)}</text>\n'
        )
    box_height = max(line_height * len(lines), font_size)
    layout_boxes.append(
        _normalized_box(
            {"x0": x, "y0": y - font_size, "w": max_width, "h": box_height + font_size * 0.2},
            width=width,
            height=height,
            box_id=box_id,
            box_type=box_type,
        )
    )


def _append_arrow(parts: list[str], box: dict[str, float], *, color: str) -> None:
    y = box["y0"] + box["h"] / 2.0
    parts.append(
        f'<line x1="{box["x0"]:.2f}" y1="{y:.2f}" x2="{box["x0"] + box["w"]:.2f}" y2="{y:.2f}" '
        f'stroke="{escape(color)}" stroke-width="4.0" marker-end="url(#arrowhead)"/>\n'
    )


def _append_glyph(
    parts: list[str],
    box: dict[str, float],
    *,
    role: str,
    accent: str,
    colors: dict[str, str],
) -> None:
    role_text = str(role or "").strip().lower()
    _append_rect(parts, box, fill="#FFFFFF", stroke=accent, stroke_width=3, radius=20)
    x0 = box["x0"]
    y0 = box["y0"]
    w = box["w"]
    h = box["h"]
    if role_text in {"population", "source_data", "cohort"}:
        for index, (cx, cy) in enumerate(((0.34, 0.42), (0.50, 0.36), (0.66, 0.43), (0.42, 0.61), (0.58, 0.62))):
            parts.append(f'<circle cx="{x0 + w * cx:.2f}" cy="{y0 + h * cy:.2f}" r="{h * 0.055:.2f}" fill="{escape(accent)}"/>\n')
            parts.append(f'<line x1="{x0 + w * cx:.2f}" y1="{y0 + h * (cy + 0.065):.2f}" x2="{x0 + w * cx:.2f}" y2="{y0 + h * (cy + 0.19):.2f}" stroke="{escape(accent)}" stroke-width="4"/>\n')
    elif role_text in {"model_signal", "model", "algorithm", "mechanism"}:
        parts.append(f'<polyline points="{x0+w*0.18:.2f},{y0+h*0.72:.2f} {x0+w*0.40:.2f},{y0+h*0.55:.2f} {x0+w*0.60:.2f},{y0+h*0.39:.2f} {x0+w*0.82:.2f},{y0+h*0.24:.2f}" fill="none" stroke="{escape(accent)}" stroke-width="5"/>\n')
        for cx, label in ((0.25, "X"), (0.50, "f"), (0.75, "Y")):
            node = {"x0": x0 + w * cx - w * 0.055, "y0": y0 + h * 0.64, "w": w * 0.11, "h": h * 0.12}
            _append_rect(parts, node, fill=colors["contrast_soft"], stroke=accent, stroke_width=2, radius=8)
            parts.append(f'<text x="{x0 + w * cx:.2f}" y="{node["y0"] + node["h"] * 0.68:.2f}" font-family="Arial, Helvetica, sans-serif" font-size="{h*0.07:.2f}" font-weight="700" fill="{escape(accent)}" text-anchor="middle">{label}</text>\n')
    else:
        center = {"x0": x0 + w * 0.32, "y0": y0 + h * 0.28, "w": w * 0.36, "h": h * 0.18}
        _append_rect(parts, center, fill=colors["secondary_soft"], stroke=accent, stroke_width=2, radius=10)
        parts.append(f'<text x="{x0+w*0.50:.2f}" y="{center["y0"] + center["h"] * 0.67:.2f}" font-family="Arial, Helvetica, sans-serif" font-size="{h*0.07:.2f}" font-weight="700" fill="{escape(accent)}" text-anchor="middle">Risk</text>\n')
        for cx, label in ((0.34, "Low"), (0.66, "High")):
            target = {"x0": x0 + w * cx - w * 0.09, "y0": y0 + h * 0.60, "w": w * 0.18, "h": h * 0.15}
            _append_rect(parts, target, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=10)
            parts.append(f'<text x="{x0+w*cx:.2f}" y="{target["y0"] + target["h"] * 0.65:.2f}" font-family="Arial, Helvetica, sans-serif" font-size="{h*0.055:.2f}" fill="{escape(accent)}" text-anchor="middle">{label}</text>\n')


def _wrap_text(text: str, *, max_width: float, font_size: float, max_lines: int) -> list[str]:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return [""]
    chars_per_line = max(8, int(max_width / max(font_size * 0.55, 1.0)))
    lines = textwrap.wrap(normalized, width=chars_per_line, break_long_words=False, break_on_hyphens=False)
    if len(lines) <= max_lines:
        return lines
    trimmed = lines[:max_lines]
    trimmed[-1] = trimmed[-1].rstrip(".") + "..."
    return trimmed


def _render_svg_to_png(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    width: int,
    height: int,
) -> None:
    chrome = _find_chrome()
    if not chrome:
        raise RuntimeError("Chrome/Chromium is required to rasterize submission_graphical_abstract SVG preview")
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--window-size={width},{height}",
            f"--screenshot={output_png_path}",
            f"file://{output_svg_path}",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not output_png_path.is_file():
        raise RuntimeError(
            "Chrome/Chromium failed to rasterize submission_graphical_abstract SVG preview; "
            f"exit={result.returncode}; stderr={result.stderr.strip()}"
        )


def _find_chrome() -> str:
    chrome_candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    )
    path = next((str(candidate) for candidate in chrome_candidates if candidate.exists()), "")
    return path or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser") or ""


def _write_layout(
    *,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    layout_boxes: list[dict[str, Any]],
    panel_boxes: list[dict[str, Any]],
    guide_boxes: list[dict[str, Any]],
) -> None:
    output_layout_path.parent.mkdir(parents=True, exist_ok=True)
    output_layout_path.write_text(
        json.dumps(
            {
                "template_id": "submission_graphical_abstract",
                "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                "layout_boxes": layout_boxes,
                "panel_boxes": panel_boxes,
                "guide_boxes": guide_boxes,
                "metrics": {
                    "layout_style": str(shell_payload.get("layout_style") or "square_storyline"),
                    "panel_count": len(shell_payload.get("panels") or []),
                    "panels": list(shell_payload.get("panels") or []),
                    "footer_pills": list(shell_payload.get("footer_pills") or []),
                    "visual_roles": [str(panel.get("visual_role") or "").strip() for panel in list(shell_payload.get("panels") or [])],
                    "source_renderer": "mas_gallery_stdlib_svg_preview",
                },
                "render_context": render_context,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
