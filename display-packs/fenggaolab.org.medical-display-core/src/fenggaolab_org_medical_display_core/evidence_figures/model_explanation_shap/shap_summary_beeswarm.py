from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _build_python_shap_layout_sidecar,
    _centered_offsets,
    _prepare_python_render_output_paths,
    _read_bool_override,
    dump_json,
)

def _render_python_shap_summary_beeswarm(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    rows = list(display_payload.get("rows") or [])
    if not rows:
        raise RuntimeError("shap_summary_beeswarm requires non-empty rows")
    render_context = dict(display_payload.get("render_context") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_height = max(4.8, 0.85 * len(rows) + 1.4)
    fig, ax = plt.subplots(figsize=(7.2, figure_height))
    fig.patch.set_facecolor("white")

    feature_values = [point["feature_value"] for row in rows for point in row["points"]]
    min_value = min(feature_values)
    max_value = max(feature_values)
    if max_value == min_value:
        max_value = min_value + 1.0
    norm = matplotlib.colors.Normalize(vmin=min_value, vmax=max_value)
    cmap = plt.get_cmap("coolwarm")
    point_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        ordered_points = sorted(row["points"], key=lambda item: float(item["shap_value"]))
        offsets = _centered_offsets(len(ordered_points))
        for point_index, point in enumerate(ordered_points):
            row_position = row_index + offsets[point_index]
            ax.scatter(
                point["shap_value"],
                row_position,
                s=42,
                c=[cmap(norm(point["feature_value"]))],
                edgecolors="white",
                linewidths=0.35,
                alpha=0.95,
            )
            point_rows.append(
                {
                    "feature": str(row["feature"]),
                    "row_position": row_position,
                    "shap_value": float(point["shap_value"]),
                }
            )

    ax.axvline(0.0, color="#6b7280", linewidth=0.8, linestyle="--")
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels([str(row["feature"]) for row in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_ylabel("")
    if show_figure_title:
        ax.set_title(str(display_payload.get("title") or "").strip(), fontsize=12.5, fontweight="bold", color="#13293d")
    _apply_publication_axes_style(ax)

    scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(scalar_mappable, ax=ax, pad=0.02)
    colorbar.set_label("Feature value", fontsize=10, color="#13293d")

    fig.tight_layout()
    fig.canvas.draw()
    dump_json(
        layout_sidecar_path,
        _build_python_shap_layout_sidecar(
            figure=fig,
            axes=ax,
            colorbar=colorbar,
            rows=rows,
            point_rows=point_rows,
            template_id=template_id,
        ),
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

