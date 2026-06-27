from __future__ import annotations

from html import escape
from pathlib import Path
import shutil
import subprocess
import textwrap
from typing import Any


def relative_box(parent: dict[str, float], x0: float, y0: float, x1: float, y1: float) -> dict[str, float]:
    return {
        "x0": parent["x0"] + parent["w"] * x0,
        "y0": parent["y0"] + parent["h"] * y0,
        "w": parent["w"] * (x1 - x0),
        "h": parent["h"] * (y1 - y0),
    }


def normalized_box(
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


def svg_header(*, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        "<defs>\n"
        '<marker id="arrowhead" markerWidth="12" markerHeight="9" refX="10" refY="4.5" orient="auto">'
        '<path d="M0,0 L12,4.5 L0,9 Z" fill="#13293D"/></marker>\n'
        "</defs>\n"
    )


def append_rect(parts: list[str], box: dict[str, float], *, fill: str, stroke: str, stroke_width: float, radius: float) -> None:
    parts.append(
        f'<rect x="{box["x0"]:.2f}" y="{box["y0"]:.2f}" width="{box["w"]:.2f}" height="{box["h"]:.2f}" '
        f'rx="{radius:.2f}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="{stroke_width:.2f}"/>\n'
    )


def append_badge(
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
    append_rect(parts, box, fill=fill, stroke=fill, stroke_width=0, radius=box["h"] / 2.0)
    parts.append(
        f'<text x="{box["x0"] + box["w"] / 2.0:.2f}" y="{box["y0"] + box["h"] * 0.66:.2f}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{box["h"] * 0.48:.2f}" font-weight="700" '
        f'fill="{escape(text_color)}" text-anchor="middle">{escape(label)}</text>\n'
    )
    layout_boxes.append(normalized_box(box, width=width, height=height, box_id=box_id, box_type=box_type))


def append_text(
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
    lines = wrap_text(text, max_width=max_width, font_size=font_size, max_lines=max_lines)
    line_height = font_size * 1.24
    for line_index, line in enumerate(lines):
        parts.append(
            f'<text x="{x:.2f}" y="{y + line_height * line_index:.2f}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.2f}" '
            f'font-weight="{escape(font_weight)}" fill="{escape(color)}">{escape(line)}</text>\n'
        )
    box_height = max(line_height * len(lines), font_size)
    layout_boxes.append(
        normalized_box(
            {"x0": x, "y0": y - font_size, "w": max_width, "h": box_height + font_size * 0.2},
            width=width,
            height=height,
            box_id=box_id,
            box_type=box_type,
        )
    )


def append_arrow(parts: list[str], box: dict[str, float], *, color: str) -> None:
    y = box["y0"] + box["h"] / 2.0
    parts.append(
        f'<line x1="{box["x0"]:.2f}" y1="{y:.2f}" x2="{box["x0"] + box["w"]:.2f}" y2="{y:.2f}" '
        f'stroke="{escape(color)}" stroke-width="4.5" stroke-linecap="round" marker-end="url(#arrowhead)"/>\n'
    )


def wrap_text(text: str, *, max_width: float, font_size: float, max_lines: int) -> list[str]:
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


def render_svg_to_png(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    width: int,
    height: int,
) -> None:
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("Chrome/Chromium is required to rasterize SVG preview")
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--window-size={width},{height}",
            f"--screenshot={output_png_path}",
            output_svg_path.resolve().as_uri(),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not output_png_path.is_file():
        raise RuntimeError(
            "Chrome/Chromium failed to rasterize SVG preview; "
            f"exit={result.returncode}; stderr={result.stderr.strip()}"
        )


def find_chrome() -> str:
    chrome_candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    )
    path = next((str(candidate) for candidate in chrome_candidates if candidate.exists()), "")
    return path or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser") or ""
