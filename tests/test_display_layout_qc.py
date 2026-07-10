from __future__ import annotations

import importlib

import pytest


def _box(box_id: str, box_type: str, coordinates: tuple[float, float, float, float]) -> dict[str, object]:
    x0, y0, x1, y1 = coordinates
    return {"box_id": box_id, "box_type": box_type, "x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _sidecar(
    *,
    template_id: str = "representative_layout",
    layout_boxes: list[dict[str, object]] | None = None,
    panel_boxes: list[dict[str, object]] | None = None,
    guide_boxes: list[dict[str, object]] | None = None,
    metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "template_id": template_id,
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": layout_boxes or [],
        "panel_boxes": panel_boxes or [],
        "guide_boxes": guide_boxes or [],
        "metrics": metrics or {},
    }


GEOMETRY_CASES = (
    pytest.param(
        "publication_result_display",
        _sidecar(
            layout_boxes=[
                _box("title", "title", (0.10, 0.02, 0.60, 0.08)),
                _box("x_axis_title", "x_axis_title", (0.30, 0.92, 0.62, 0.97)),
                _box("y_axis_title", "y_axis_title", (0.01, 0.24, 0.06, 0.70)),
            ],
            panel_boxes=[_box("panel", "panel", (0.10, 0.16, 0.74, 0.88))],
        ),
        None,
        id="valid-baseline",
    ),
    pytest.param(
        "publication_result_display",
        _sidecar(layout_boxes=[_box("title", "title", (0.10, 0.02, 1.08, 0.08))]),
        "box_out_of_device",
        id="device-overflow",
    ),
    pytest.param(
        "publication_result_display",
        _sidecar(
            layout_boxes=[
                _box("title", "title", (0.10, 0.02, 0.60, 0.08)),
                _box("subtitle", "subtitle", (0.20, 0.05, 0.70, 0.11)),
            ]
        ),
        "text_box_overlap",
        id="text-overlap",
    ),
    pytest.param(
        "publication_embedding_scatter",
        _sidecar(
            template_id="umap_scatter_grouped",
            layout_boxes=[
                _box("title", "title", (0.10, 0.02, 0.60, 0.08)),
                _box("x_axis_title", "x_axis_title", (0.32, 0.92, 0.62, 0.97)),
                _box("y_axis_title", "y_axis_title", (0.01, 0.25, 0.06, 0.70)),
            ],
            panel_boxes=[_box("panel", "panel", (0.10, 0.16, 0.78, 0.88))],
            guide_boxes=[_box("legend", "legend", (0.64, 0.64, 0.92, 0.86))],
            metrics={"points": [{"x": 0.22, "y": 0.32, "group": "A"}]},
        ),
        "legend_panel_overlap",
        id="legend-clearance",
    ),
)


@pytest.mark.parametrize(("qc_profile", "layout_sidecar", "expected_rule"), GEOMETRY_CASES)
def test_run_display_layout_qc_covers_representative_geometry_risks(
    qc_profile: str,
    layout_sidecar: dict[str, object],
    expected_rule: str | None,
) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(qc_profile=qc_profile, layout_sidecar=layout_sidecar)

    if expected_rule is None:
        assert result["status"] == "pass"
        assert result["issues"] == []
        return
    assert result["status"] == "fail"
    assert expected_rule in {issue["rule_id"] for issue in result["issues"]}


def test_run_display_layout_qc_keeps_readability_as_a_separate_audit_class() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")
    layout_sidecar = _sidecar(
        template_id="kaplan_meier_grouped",
        layout_boxes=[
            _box("x_axis_title", "x_axis_title", (0.30, 0.92, 0.62, 0.97)),
            _box("y_axis_title", "y_axis_title", (0.01, 0.24, 0.06, 0.70)),
        ],
        panel_boxes=[_box("panel", "panel", (0.10, 0.16, 0.74, 0.88))],
        guide_boxes=[_box("legend", "legend", (0.78, 0.28, 0.96, 0.46))],
        metrics={
            "groups": [
                {"label": "Low risk", "times": [0.0, 5.0], "values": [1.0, 0.9980]},
                {"label": "High risk", "times": [0.0, 5.0], "values": [1.0, 0.9975]},
            ]
        },
    )

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar=layout_sidecar,
    )

    assert result["status"] == "fail"
    assert result["audit_classes"] == ["readability"]
    assert {issue["rule_id"] for issue in result["readability_findings"]} == {"risk_separation_not_readable"}
