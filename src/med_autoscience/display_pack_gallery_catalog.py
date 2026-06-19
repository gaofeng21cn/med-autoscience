from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import tomllib

from med_autoscience.display_pack_canonical_catalog import (
    canonical_catalog_entry_for_template,
    load_canonical_template_catalog,
)


@dataclass(frozen=True)
class TemplateRecord:
    template_id: str
    full_template_id: str
    display_name: str
    kind: str
    audit_family: str
    renderer_family: str
    execution_mode: str
    entrypoint: str
    previous_renderer_family: str
    previous_entrypoint: str
    paper_proven: bool
    required_exports: tuple[str, ...]
    template_dir: Path
    canonical_family_id: str
    canonical_family_title: str
    canonical_family_category: str
    canonical_template_id: str
    figure_archetype: str
    migration_status: str
    default_visible: bool
    migrated_alias_template_ids: tuple[str, ...]
    migration_reason: str


def read_template_records(pack_root: Path, template_root: Path) -> list[TemplateRecord]:
    records: list[TemplateRecord] = []
    catalog = load_canonical_template_catalog(pack_root)
    catalog_ids = set(catalog.entries_by_template_id) if catalog is not None else set()
    for template_path in sorted(template_root.glob("*/template.toml")):
        payload = tomllib.loads(template_path.read_text(encoding="utf-8"))
        canonical = canonical_catalog_entry_for_template(
            catalog=catalog,
            template_id=str(payload["template_id"]),
            category=str(payload["audit_family"]),
            title=str(payload["display_name"]),
        )
        records.append(
            TemplateRecord(
                template_id=str(payload["template_id"]),
                full_template_id=str(payload["full_template_id"]),
                display_name=str(payload["display_name"]),
                kind=str(payload["kind"]),
                audit_family=str(payload["audit_family"]),
                renderer_family=str(payload["renderer_family"]),
                execution_mode=str(payload["execution_mode"]),
                entrypoint=str(payload.get("entrypoint") or ""),
                previous_renderer_family=str(payload.get("previous_renderer_family") or ""),
                previous_entrypoint=str(payload.get("previous_entrypoint") or ""),
                paper_proven=bool(payload.get("paper_proven", False)),
                required_exports=tuple(str(item) for item in payload.get("required_exports", ())),
                template_dir=template_path.parent,
                canonical_family_id=canonical.family_id,
                canonical_family_title=canonical.family_title,
                canonical_family_category=canonical.family_category,
                canonical_template_id=canonical.canonical_template_id,
                figure_archetype=canonical.figure_archetype,
                migration_status=canonical.migration_status,
                default_visible=canonical.default_visible,
                migrated_alias_template_ids=canonical.aliases if canonical.migration_status == "canonical" else (),
                migration_reason=canonical.migration_reason,
            )
        )
    if catalog is not None:
        template_ids = {record.template_id for record in records}
        missing = sorted(catalog_ids - template_ids)
        if missing:
            raise ValueError(f"canonical template catalog references missing template ids: {missing}")
    return records


def canonical_records(records: list[TemplateRecord]) -> list[TemplateRecord]:
    return [record for record in records if record.default_visible]


def family_categories(records: list[TemplateRecord]) -> dict[str, list[TemplateRecord]]:
    categories: dict[str, list[TemplateRecord]] = defaultdict(list)
    for record in canonical_records(records):
        categories[record.canonical_family_category].append(record)
    return categories
