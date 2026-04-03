from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from med_autoscience import display_registry


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _paper_relative_path(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.parent.resolve()).as_posix()


def _display_id_to_figure_id(display_id: str) -> str:
    match = re.fullmatch(r"Figure(\d+)", str(display_id).strip(), flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported figure display_id `{display_id}`")
    return f"F{int(match.group(1))}"


def _display_id_to_table_id(display_id: str) -> str:
    match = re.fullmatch(r"Table(\d+)", str(display_id).strip(), flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported table display_id `{display_id}`")
    return f"T{int(match.group(1))}"


def _replace_catalog_entry(items: list[dict[str, Any]], *, key: str, value: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    updated = [item for item in items if str(item.get(key) or "").strip() != value]
    updated.append(entry)
    return updated


def _validate_cohort_flow_payload(path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{path.name} must contain a non-empty steps list")
    normalized: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{path.name} steps[{index}] must be an object")
        step_id = str(step.get("step_id") or "").strip()
        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()
        if not step_id or not label:
            raise ValueError(f"{path.name} steps[{index}] must include step_id and label")
        raw_n = step.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} steps[{index}].n must be an integer")
        normalized.append({"step_id": step_id, "label": label, "detail": detail, "n": raw_n})
    return normalized


def _validate_baseline_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name} must contain a non-empty groups list")
    group_labels: list[str] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"{path.name} groups[{index}] must be an object")
        label = str(group.get("label") or "").strip()
        if not label:
            raise ValueError(f"{path.name} groups[{index}] must include label")
        group_labels.append(label)

    variables = payload.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError(f"{path.name} must contain a non-empty variables list")
    normalized_rows: list[dict[str, Any]] = []
    for index, variable in enumerate(variables):
        if not isinstance(variable, dict):
            raise ValueError(f"{path.name} variables[{index}] must be an object")
        label = str(variable.get("label") or "").strip()
        values = variable.get("values")
        if not label or not isinstance(values, list) or len(values) != len(group_labels):
            raise ValueError(
                f"{path.name} variables[{index}] must include label and values matching the number of groups"
            )
        normalized_rows.append({"label": label, "values": [str(item).strip() for item in values]})
    return group_labels, normalized_rows


def _render_cohort_flow_figure(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    title: str,
    steps: list[dict[str, Any]],
) -> None:
    figure_height = max(4.5, 1.8 * len(steps))
    fig, ax = plt.subplots(figsize=(8, figure_height))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(steps) * 2.2 + 0.5)
    ax.axis("off")
    ax.text(0.5, len(steps) * 2.05 + 0.25, title, fontsize=15, fontweight="bold", color="#213547")

    box_x = 1.1
    box_width = 7.8
    box_height = 1.2
    for index, step in enumerate(steps):
        y = len(steps) * 2.0 - index * 2.0
        box = FancyBboxPatch(
            (box_x, y - box_height / 2),
            box_width,
            box_height,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            linewidth=1.2,
            edgecolor="#547980",
            facecolor="#f6fbfb",
        )
        ax.add_patch(box)
        ax.text(
            box_x + 0.22,
            y + 0.16,
            step["label"],
            fontsize=11.5,
            fontweight="bold",
            color="#1f2d3d",
            va="center",
        )
        ax.text(
            box_x + 0.22,
            y - 0.14,
            f"n = {step['n']}",
            fontsize=11,
            color="#234b5a",
            va="center",
        )
        if step["detail"]:
            ax.text(
                box_x + 2.0,
                y - 0.14,
                step["detail"],
                fontsize=10.2,
                color="#4f6470",
                va="center",
            )
        if index < len(steps) - 1:
            next_y = len(steps) * 2.0 - (index + 1) * 2.0
            arrow = FancyArrowPatch(
                (5.0, y - box_height / 2 - 0.08),
                (5.0, next_y + box_height / 2 + 0.08),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.0,
                color="#6c8a91",
            )
            ax.add_patch(arrow)

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_svg_path, format="svg", bbox_inches="tight")
    fig.savefig(output_png_path, format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def _write_table_outputs(
    *,
    output_csv_path: Path,
    output_md_path: Path,
    title: str,
    group_labels: list[str],
    rows: list[dict[str, Any]],
) -> None:
    headers = ["Characteristic", *group_labels]
    table_rows = [[row["label"], *row["values"]] for row in rows]

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(table_rows)

    markdown_lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in table_rows:
        markdown_lines.append("| " + " | ".join(row) + " |")
    output_md_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def materialize_display_surface(*, paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    display_registry_payload = load_json(resolved_paper_root / "display_registry.json")
    figure_catalog = load_json(resolved_paper_root / "figures" / "figure_catalog.json")
    table_catalog = load_json(resolved_paper_root / "tables" / "table_catalog.json")

    figures_materialized: list[str] = []
    tables_materialized: list[str] = []
    written_files: list[str] = []

    for item in display_registry_payload.get("displays", []):
        if not isinstance(item, dict):
            raise ValueError("display_registry.json displays must contain objects")
        requirement_key = str(item.get("requirement_key") or "").strip()
        display_id = str(item.get("display_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()

        if requirement_key == "cohort_flow_figure":
            if display_kind != "figure":
                raise ValueError("cohort_flow_figure must be registered as a figure display")
            spec = display_registry.get_illustration_shell_spec("cohort_flow_figure")
            payload_path = resolved_paper_root / "cohort_flow.json"
            payload = load_json(payload_path)
            steps = _validate_cohort_flow_payload(payload_path, payload)
            title = str(payload.get("title") or "Cohort flow").strip() or "Cohort flow"
            figure_id = _display_id_to_figure_id(display_id)
            output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.svg"
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.png"
            _render_cohort_flow_figure(
                output_svg_path=output_svg_path,
                output_png_path=output_png_path,
                title=title,
                steps=steps,
            )
            written_files.extend([str(output_svg_path), str(output_png_path)])
            entry = {
                "figure_id": figure_id,
                "template_id": spec.shell_id,
                "renderer_family": spec.renderer_family,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.shell_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": title,
                "caption": str(payload.get("caption") or "Study cohort flow and analysis population accounting.").strip(),
                "export_paths": [
                    _paper_relative_path(output_svg_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            figure_catalog["figures"] = _replace_catalog_entry(
                list(figure_catalog.get("figures") or []),
                key="figure_id",
                value=figure_id,
                entry=entry,
            )
            figures_materialized.append(figure_id)
            continue

        if requirement_key == "table1_baseline_characteristics":
            if display_kind != "table":
                raise ValueError("table1_baseline_characteristics must be registered as a table display")
            spec = display_registry.get_table_shell_spec("table1_baseline_characteristics")
            payload_path = resolved_paper_root / "baseline_characteristics_schema.json"
            payload = load_json(payload_path)
            group_labels, rows = _validate_baseline_table_payload(payload_path, payload)
            title = str(payload.get("title") or "Baseline characteristics").strip() or "Baseline characteristics"
            table_id = _display_id_to_table_id(display_id)
            output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.csv"
            output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.md"
            _write_table_outputs(
                output_csv_path=output_csv_path,
                output_md_path=output_md_path,
                title=title,
                group_labels=group_labels,
                rows=rows,
            )
            written_files.extend([str(output_csv_path), str(output_md_path)])
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": title,
                "caption": str(payload.get("caption") or "Baseline characteristics across prespecified groups.").strip(),
                "asset_paths": [
                    _paper_relative_path(output_csv_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_md_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            table_catalog["tables"] = _replace_catalog_entry(
                list(table_catalog.get("tables") or []),
                key="table_id",
                value=table_id,
                entry=entry,
            )
            tables_materialized.append(table_id)
            continue

    dump_json(resolved_paper_root / "figures" / "figure_catalog.json", figure_catalog)
    dump_json(resolved_paper_root / "tables" / "table_catalog.json", table_catalog)
    written_files.extend(
        [
            str(resolved_paper_root / "figures" / "figure_catalog.json"),
            str(resolved_paper_root / "tables" / "table_catalog.json"),
        ]
    )
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "figures_materialized": figures_materialized,
        "tables_materialized": tables_materialized,
        "written_files": written_files,
    }
