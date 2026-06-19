from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import tomllib

from med_autoscience.display_pack_canonical_catalog import (
    canonical_catalog_entry_for_template,
    load_canonical_template_catalog,
)
from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog

CORE_MEDICAL_FIGURE_FAMILY_CATALOG_REF = "contracts/medical-figure-family-catalog/"
FIGURE_FAMILY_POLICY_SOURCE = "medical_figure_family_catalog"
GALLERY_TEMPLATE_FAMILY_SOURCE = "display_pack_canonical_template_catalog"


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


def visual_gallery_records(records: list[TemplateRecord]) -> list[TemplateRecord]:
    return [
        record
        for record in canonical_records(records)
        if record.renderer_family != "n/a" and record.kind != "table_shell"
    ]


def non_visual_canonical_records(records: list[TemplateRecord]) -> list[TemplateRecord]:
    return [
        record
        for record in canonical_records(records)
        if record.renderer_family == "n/a" or record.kind == "table_shell"
    ]


def family_categories(records: list[TemplateRecord]) -> dict[str, list[TemplateRecord]]:
    categories: dict[str, list[TemplateRecord]] = defaultdict(list)
    for record in visual_gallery_records(records):
        categories[record.canonical_family_category].append(record)
    return categories


def figure_family_policy() -> dict[str, object]:
    return {
        "policy_version": 1,
        "current_metadata_source": FIGURE_FAMILY_POLICY_SOURCE,
        "core_catalog_ref": CORE_MEDICAL_FIGURE_FAMILY_CATALOG_REF,
        "gallery_template_metadata_source": GALLERY_TEMPLATE_FAMILY_SOURCE,
        "core_catalog_dependency": "loaded_via_medical_figure_family_catalog_loader",
        "default_gallery_surface": "visual_canonical_families_only",
        "alias_handling": "hidden_from_gallery_cards_preserved_in_migration_index",
        "non_visual_handling": "kept_in_manifest_inventory_hidden_from_image_gallery_cards",
        "machine_boundary": "core_catalog_and_gallery_metadata_only_not_source_truth_statistical_truth_or_publication_readiness_authority",
    }


def ai_adaptation_policy() -> dict[str, object]:
    return dict(load_medical_figure_family_catalog().ai_adaptation_policy)


def canonical_family_wording(record: TemplateRecord) -> str:
    return (
        f"{record.canonical_family_title} "
        f"({record.canonical_family_category}): {record.figure_archetype}"
    )


def gallery_template_family_ontology(records: list[TemplateRecord]) -> list[dict[str, object]]:
    seen: set[str] = set()
    entries: list[dict[str, object]] = []
    for record in visual_gallery_records(records):
        if record.canonical_family_id in seen:
            continue
        seen.add(record.canonical_family_id)
        entries.append(
            {
                "family_id": record.canonical_family_id,
                "title": record.canonical_family_title,
                "category": record.canonical_family_category,
                "canonical_template_id": record.canonical_template_id,
                "figure_archetype": record.figure_archetype,
                "canonical_family_wording": canonical_family_wording(record),
            }
        )
    return entries


def canonical_family_ontology() -> list[dict[str, object]]:
    catalog = load_medical_figure_family_catalog()
    return [
        {
            "family_id": family.family_id,
            "category_id": family.category_id,
            "title": family.title,
            "intent": family.intent,
            "canonical_variants": list(family.canonical_variants),
            "template_seed_ids": list(family.template_seed_ids),
            "style_tokens": list(family.style_tokens),
            "palette_tokens": list(family.palette_tokens),
            "qa_gate_ids": list(family.qa_gate_ids),
            "loose_match_terms": list(family.loose_match_terms),
            "external_refs": list(family.external_refs),
        }
        for family in catalog.families_by_id.values()
    ]


def canonical_category_ontology() -> list[dict[str, object]]:
    catalog = load_medical_figure_family_catalog()
    return [
        {
            "category_id": category.category_id,
            "title": category.title,
            "family_count": len(category.families),
            "family_ids": [family.family_id for family in category.families],
        }
        for category in catalog.categories
    ]
