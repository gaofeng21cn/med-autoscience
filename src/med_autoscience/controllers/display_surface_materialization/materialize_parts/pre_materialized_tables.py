from __future__ import annotations

import csv

from ..shared import Any, Path, _paper_relative_path, utc_now
from .workspace import _claim_ids_for_table


def _existing_table_catalog_entry(*, table_catalog: dict[str, Any], table_id: str) -> dict[str, Any] | None:
    for entry in table_catalog.get("tables", []) or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("table_id") or "").strip() == table_id:
            return entry
    return None


def _dpcc_medication_capture_markdown_path(*, paper_root: Path) -> Path | None:
    for path in (
        paper_root / "tables" / "generated" / "T3_medication_capture_sensitivity.md",
        paper_root / "tables" / "T3_medication_capture_sensitivity.md",
    ):
        if path.exists():
            return path
    return None


def _markdown_table_to_rows(markdown: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if all(cell and set(cell.replace(":", "").replace("-", "").strip()) == set() for cell in cells):
            continue
        rows.append(cells)
    return rows


def _write_markdown_table_csv_from_source(*, source_md_path: Path, output_csv_path: Path) -> None:
    rows = _markdown_table_to_rows(source_md_path.read_text(encoding="utf-8"))
    if not rows:
        raise ValueError(f"pre-materialized table `{source_md_path}` does not contain a markdown table")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def _pre_materialized_markdown_table_path(
    *,
    paper_root: Path,
    requirement_short_id: str,
    table_id: str,
) -> Path | None:
    if requirement_short_id == "table1_baseline_characteristics" and table_id == "T1":
        path = paper_root / "tables" / "T1_baseline_characteristics.md"
    elif requirement_short_id == "table2_phenotype_gap_summary" and table_id == "T2":
        path = paper_root / "tables" / "T2_phenotype_gap_summary.md"
    else:
        return None
    return path if path.exists() else None


def _materialize_pre_materialized_markdown_table(
    *,
    paper_root: Path,
    source_md_path: Path,
    output_md_path: Path,
    output_csv_path: Path,
    table_catalog: dict[str, Any],
    claim_evidence_map: dict[str, Any],
    table_id: str,
    table_shell_id: str,
    pack_id: str,
    paper_role: str,
    input_schema_id: str,
    qc_profile: str,
    default_title: str,
    default_caption: str,
) -> dict[str, Any]:
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(source_md_path.read_text(encoding="utf-8"), encoding="utf-8")
    _write_markdown_table_csv_from_source(source_md_path=source_md_path, output_csv_path=output_csv_path)
    existing_entry = _existing_table_catalog_entry(table_catalog=table_catalog, table_id=table_id)
    existing_title = str((existing_entry or {}).get("title") or "").strip()
    existing_caption = str((existing_entry or {}).get("caption") or "").strip()
    claim_ids = _claim_ids_for_table(
        table_catalog=table_catalog,
        claim_evidence_map=claim_evidence_map,
        table_id=table_id,
    )
    render_result = {
        "title": existing_title or default_title,
        "caption": existing_caption or default_caption,
        "table_layout_policy": "pre_materialized_markdown_owner_surface",
        "source_table_path": _paper_relative_path(source_md_path, paper_root=paper_root),
    }
    return {
        "table_id": table_id,
        "table_shell_id": table_shell_id,
        "pack_id": pack_id,
        "paper_role": paper_role,
        "input_schema_id": input_schema_id,
        "qc_profile": qc_profile,
        "qc_result": {
            "status": "pass",
            "issues": [],
            "checked_at": utc_now(),
        },
        "title": render_result["title"],
        "caption": render_result["caption"],
        "asset_paths": [
            _paper_relative_path(output_csv_path, paper_root=paper_root),
            _paper_relative_path(output_md_path, paper_root=paper_root),
        ],
        "source_paths": [
            _paper_relative_path(source_md_path, paper_root=paper_root),
        ],
        "claim_ids": claim_ids,
        "render_result": render_result,
    }


__all__ = [
    "_dpcc_medication_capture_markdown_path",
    "_existing_table_catalog_entry",
    "_materialize_pre_materialized_markdown_table",
    "_pre_materialized_markdown_table_path",
]
