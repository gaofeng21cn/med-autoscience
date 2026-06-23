from __future__ import annotations

from pathlib import Path


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
    axes.grid(axis="x", visible=False)
    axes.grid(axis="y", color="#eceff2", linewidth=0.35, linestyle="-", zorder=0)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    for spine_name in ("left", "bottom"):
        axes.spines[spine_name].set_visible(True)
        axes.spines[spine_name].set_color("#272727")
        axes.spines[spine_name].set_linewidth(0.6)
    axes.tick_params(axis="both", colors="#272727", width=0.6)
