from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing required CSV file: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV headers: {path}")
        return [dict(row) for row in reader]


def _parse_float(raw_value: object, *, label: str) -> float:
    try:
        return float(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric value for {label}: {raw_value!r}") from exc


def _parse_int(raw_value: object, *, label: str) -> int:
    try:
        return int(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer value for {label}: {raw_value!r}") from exc


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    normalized = normalized.strip("_")
    return normalized or "item"


def _load_markdown_table(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"missing required markdown table: {path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 3:
        raise ValueError(f"markdown table not found in {path}")

    def parse_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip("|").split("|")]

    header = parse_row(table_lines[0])
    rows = [parse_row(line) for line in table_lines[2:]]
    return header, rows


def _row_map_from_markdown_table(*, header: list[str], rows: list[list[str]], label_column: str) -> dict[str, dict[str, str]]:
    normalized_header = {value.strip().casefold(): index for index, value in enumerate(header)}
    if label_column.casefold() not in normalized_header:
        raise ValueError(f"missing required markdown table column `{label_column}`")
    label_index = normalized_header[label_column.casefold()]
    row_map: dict[str, dict[str, str]] = {}
    for row_index, row in enumerate(rows):
        if len(row) != len(header):
            raise ValueError(f"markdown table row length mismatch at row {row_index + 1}")
        key = row[label_index].strip()
        if not key:
            raise ValueError(f"markdown table row {row_index + 1} missing `{label_column}` value")
        row_map[key] = {header[column_index].strip(): value.strip() for column_index, value in enumerate(row)}
    return row_map


def _extract_regex_group(*, text: str, pattern: str, label: str) -> tuple[str, ...]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f"unable to parse `{label}` from markdown row: {text}")
    return tuple(group.strip() for group in match.groups())
