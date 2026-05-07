from __future__ import annotations

from .shared_parts.common import (
    _format_percent_1dp,
    _read_bool_override,
    _require_namespaced_registry_id,
    _require_non_empty_string,
    _require_non_negative_int,
    _require_numeric_value,
    dump_json,
    load_json,
)
from .shared_parts.layout import (
    _FlowNodeSpec,
    _FlowTextLine,
    _GraphvizLayout,
    _GraphvizNodeBox,
    _build_python_shap_layout_sidecar,
    _build_submission_graphical_abstract_arrow_lane_spec,
    _choose_shared_submission_graphical_abstract_arrow_lane,
    _flow_box_to_normalized,
    _flow_font_path,
    _flow_font_properties,
    _flow_html_label_for_node,
    _flow_union_box,
    _measure_flow_text_width_pt,
    _run_graphviz_layout,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
)
from .shared_parts.geometry import (
    _bbox_to_layout_box,
    _clip_line_segment_to_axes_window,
    _clip_reference_line_to_axes_window,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _normalize_reference_line_collection_to_device_space,
    _normalize_reference_line_to_device_space,
)
from .shared_parts.rendering import (
    _apply_publication_axes_style,
    _centered_offsets,
    _prepare_python_illustration_output_paths,
    _prepare_python_render_output_paths,
)
