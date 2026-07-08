from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _prepare_display_golden_workspace(
    paper_root: Path,
    *,
    display_id: str,
    requirement_key: str,
    catalog_id: str,
    template_id: str,
) -> None:
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": display_id,
                    "display_kind": "figure",
                    "requirement_key": requirement_key,
                    "catalog_id": catalog_id,
                    "shell_path": f"paper/figures/{display_id}.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": display_id,
                    "template_id": template_id,
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )


__all__ = [
    "Path",
    "importlib",
    "json",
    "_dump_json",
    "_prepare_display_golden_workspace",
]
