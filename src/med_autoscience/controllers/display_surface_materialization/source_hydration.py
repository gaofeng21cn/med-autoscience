from __future__ import annotations

import filecmp
import shutil

from .shared import (
    Any,
    Path,
    _ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID,
    _paper_relative_path,
    display_registry,
    get_template_short_id,
    load_json,
)
from med_autoscience.display_source_contract import INPUT_FILENAME_BY_SCHEMA_ID, TABLE_INPUT_FILENAME_BY_SCHEMA_ID


_BODY_AUTHORITY_CURRENT_BODY_PAPER_REL = (
    "artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper"
)

_SUPPORT_SOURCE_RELS = (
    "build/dependency_environment_lock.json",
    "build/dependency_environment_receipt.json",
    "build/dependency_run_context.json",
    "figures/figure_catalog.json",
    "tables/table_catalog.json",
    "figure_semantics_manifest.json",
    "publication_style_profile.json",
    "display_overrides.json",
    "claim_evidence_map.json",
)

_TABLE_SOURCE_CSV_BY_TEMPLATE_SHORT_ID = {
    "table2_phenotype_gap_summary": "tables/T2_phenotype_gap_summary.csv",
    "table3_transition_site_support_summary": "tables/T3_transition_site_support_summary.csv",
}


def _current_body_paper_root(*, paper_root: Path) -> Path:
    return paper_root.parent / _BODY_AUTHORITY_CURRENT_BODY_PAPER_REL


def _copy_if_source_changed(
    *,
    source_root: Path,
    paper_root: Path,
    rel_path: str,
) -> Path | None:
    source_path = source_root / rel_path
    if not source_path.exists():
        return None
    target_path = paper_root / rel_path
    if target_path.exists() and filecmp.cmp(source_path, target_path, shallow=False):
        return None
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    return target_path


def _current_generated_status(path: Path) -> str:
    if not path.exists() or path.suffix != ".json":
        return ""
    try:
        payload = load_json(path)
    except (OSError, ValueError):
        return ""
    status = str(payload.get("status") or "").strip()
    if status.startswith("materialized_from_current_"):
        return status
    return ""


def _should_preserve_current_generated_target(
    *,
    source_path: Path,
    target_path: Path,
) -> bool:
    target_status = _current_generated_status(target_path)
    if not target_status:
        return False
    source_status = _current_generated_status(source_path)
    return source_status != target_status


def _copy_shell_path(
    *,
    source_root: Path,
    paper_root: Path,
    item: dict[str, Any],
    copied_files: list[Path],
) -> dict[str, Any] | None:
    shell_path = str(item.get("shell_path") or "").strip()
    if not shell_path:
        return None
    if shell_path.startswith("paper/"):
        shell_rel_path = shell_path.removeprefix("paper/")
    else:
        shell_rel_path = shell_path
    copied_path = _copy_if_source_changed(
        source_root=source_root,
        paper_root=paper_root,
        rel_path=shell_rel_path,
    )
    if copied_path is not None:
        copied_files.append(copied_path)
    resolved_shell_path = paper_root / shell_rel_path
    if not resolved_shell_path.exists():
        return None
    return load_json(resolved_shell_path)


def _resolve_requirement_key(
    *,
    item: dict[str, Any],
    shell_payload: dict[str, Any] | None,
) -> str:
    requirement_key = str(item.get("requirement_key") or "").strip()
    if (
        display_registry.is_evidence_figure_template(requirement_key)
        or display_registry.is_illustration_shell(requirement_key)
        or display_registry.is_table_shell(requirement_key)
    ):
        return requirement_key
    if shell_payload is None:
        return requirement_key
    for key in ("requirement_key", "template_id", "shell_id", "table_shell_id"):
        value = str(shell_payload.get(key) or "").strip()
        if (
            display_registry.is_evidence_figure_template(value)
            or display_registry.is_illustration_shell(value)
            or display_registry.is_table_shell(value)
        ):
            return value
    return requirement_key


def _required_input_rels_for_display(
    *,
    item: dict[str, Any],
    requirement_key: str,
) -> list[str]:
    display_kind = str(item.get("display_kind") or "").strip()
    if display_kind == "figure" and display_registry.is_illustration_shell(requirement_key):
        spec = display_registry.get_illustration_shell_spec(requirement_key)
        filename = _ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID.get(spec.input_schema_id)
        return [filename] if filename else []
    if display_kind == "figure" and display_registry.is_evidence_figure_template(requirement_key):
        spec = display_registry.get_evidence_figure_spec(requirement_key)
        filename = INPUT_FILENAME_BY_SCHEMA_ID.get(spec.input_schema_id)
        return [filename] if filename else []
    if display_kind == "table" and display_registry.is_table_shell(requirement_key):
        spec = display_registry.get_table_shell_spec(requirement_key)
        filename = TABLE_INPUT_FILENAME_BY_SCHEMA_ID.get(spec.input_schema_id)
        rels = [filename] if filename else []
        table_csv = _TABLE_SOURCE_CSV_BY_TEMPLATE_SHORT_ID.get(get_template_short_id(spec.shell_id))
        if table_csv:
            rels.append(table_csv)
        return rels
    return []


def hydrate_display_surface_sources_from_current_body(
    *,
    paper_root: Path,
    display_registry_payload: dict[str, Any],
) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    source_root = _current_body_paper_root(paper_root=resolved_paper_root)
    if not source_root.exists():
        return {
            "status": "skipped_no_body_authority_current_body",
            "source_root": str(source_root),
            "hydrated_files": [],
            "missing_required_source_files": [],
            "preserved_current_generated_sources": [],
        }

    copied_files: list[Path] = []
    missing_required_source_files: list[str] = []
    preserved_current_generated_sources: list[str] = []
    required_rels: set[str] = set()
    displays = display_registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json must contain a displays list")

    for item in displays:
        if not isinstance(item, dict):
            raise ValueError("display_registry.json displays must contain objects")
        shell_payload = _copy_shell_path(
            source_root=source_root,
            paper_root=resolved_paper_root,
            item=item,
            copied_files=copied_files,
        )
        requirement_key = _resolve_requirement_key(item=item, shell_payload=shell_payload)
        for rel_path in _required_input_rels_for_display(item=item, requirement_key=requirement_key):
            required_rels.add(rel_path)

    for rel_path in sorted(_SUPPORT_SOURCE_RELS):
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=resolved_paper_root,
            rel_path=rel_path,
        )
        if copied_path is not None:
            copied_files.append(copied_path)

    for rel_path in sorted(required_rels):
        source_path = source_root / rel_path
        target_path = resolved_paper_root / rel_path
        if not source_path.exists():
            if not target_path.exists():
                missing_required_source_files.append(rel_path)
            continue
        if _should_preserve_current_generated_target(source_path=source_path, target_path=target_path):
            preserved_current_generated_sources.append(rel_path)
            continue
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=resolved_paper_root,
            rel_path=rel_path,
        )
        if copied_path is not None:
            copied_files.append(copied_path)

    hydrated_files = [
        _paper_relative_path(path, paper_root=resolved_paper_root)
        for path in sorted(set(copied_files))
    ]
    return {
        "status": "hydrated" if hydrated_files else "current",
        "source_root": str(source_root),
        "hydrated_files": hydrated_files,
        "missing_required_source_files": missing_required_source_files,
        "preserved_current_generated_sources": [
            f"paper/{rel_path}" for rel_path in sorted(set(preserved_current_generated_sources))
        ],
    }


__all__ = [
    "hydrate_display_surface_sources_from_current_body",
]
