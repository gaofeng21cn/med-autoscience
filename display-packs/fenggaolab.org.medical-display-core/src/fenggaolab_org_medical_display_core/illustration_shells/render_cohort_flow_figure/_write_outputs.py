from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from ...shared import _FlowNodeSpec, dump_json


def _write_multi_panel_outputs(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    output_pdf_path: Path | None = None,
    step_specs: list[_FlowNodeSpec],
    exclusion_specs: dict[str, _FlowNodeSpec],
    step_boxes_by_id: dict[str, dict[str, float]],
    exclusion_boxes_by_id: dict[str, dict[str, float]],
    rendered_padding_for_spec: Callable[[_FlowNodeSpec], float],
    layout_boxes: list[dict[str, Any]],
    panel_boxes: list[dict[str, Any]],
    guide_boxes: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    endpoint_inventory: list[dict[str, Any]],
    design_panels: list[dict[str, Any]],
    render_context_payload: dict[str, Any],
    fig: Figure,
) -> None:
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    flow_nodes = []
    for spec in step_specs:
        box = step_boxes_by_id.get(spec.node_id)
        if box is None:
            continue
        flow_nodes.append(
            {
                "box_id": spec.box_id,
                "box_type": spec.box_type,
                "line_count": len(spec.lines),
                "max_line_chars": max((len(line.text) for line in spec.lines), default=0),
                "rendered_height_pt": box["y1"] - box["y0"],
                "rendered_width_pt": box["x1"] - box["x0"],
                "padding_pt": rendered_padding_for_spec(spec),
            }
        )
    for spec in exclusion_specs.values():
        box = exclusion_boxes_by_id.get(spec.node_id)
        if box is None:
            continue
        flow_nodes.append(
            {
                "box_id": spec.box_id,
                "box_type": spec.box_type,
                "line_count": len(spec.lines),
                "max_line_chars": max((len(line.text) for line in spec.lines), default=0),
                "rendered_height_pt": box["y1"] - box["y0"],
                "rendered_width_pt": box["x1"] - box["x0"],
                "padding_pt": rendered_padding_for_spec(spec),
            }
        )
    dump_json(
        output_layout_path,
        {
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "steps": steps,
                "exclusions": exclusions,
                "endpoint_inventory": endpoint_inventory,
                "design_panels": design_panels,
                "flow_nodes": flow_nodes,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(
        output_svg_path,
        format="svg",
        metadata={"Creator": "FenggaoLab medical display core"},
    )
    fig.savefig(output_png_path, format="png", dpi=220)
    if output_pdf_path is not None:
        fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
