from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CanonicalTemplateFamily:
    family_id: str
    category: str
    title: str
    figure_archetype: str
    canonical_template_id: str
    aliases: tuple[str, ...]
    default_visible: bool
    migration_reason: str


@dataclass(frozen=True)
class CanonicalTemplateEntry:
    family_id: str
    family_title: str
    family_category: str
    figure_archetype: str
    canonical_template_id: str
    template_id: str
    migration_status: str
    default_visible: bool
    aliases: tuple[str, ...]
    migration_reason: str


@dataclass(frozen=True)
class CanonicalTemplateCatalog:
    schema_version: int
    catalog_id: str
    pack_id: str
    purpose: str
    default_surface_policy: dict[str, Any]
    external_learning_refs: dict[str, Any]
    families: tuple[CanonicalTemplateFamily, ...]
    entries_by_template_id: dict[str, CanonicalTemplateEntry]
    canonical_template_ids: tuple[str, ...]
    alias_template_ids: tuple[str, ...]


def _expect_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"canonical template catalog `{key}` must be a non-empty string")
    return value.strip()


def _expect_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"canonical template catalog `{key}` must be a bool")
    return value


def _expect_str_tuple(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"canonical template catalog `{key}` must be a list")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"canonical template catalog `{key}`[{index}] must be a non-empty string")
        normalized.append(item.strip())
    return tuple(normalized)


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _parse_family(raw_family: dict[str, Any]) -> CanonicalTemplateFamily:
    aliases = _expect_str_tuple(raw_family, "aliases")
    canonical_template_id = _expect_str(raw_family, "canonical_template_id")
    if canonical_template_id in aliases:
        raise ValueError(f"canonical template `{canonical_template_id}` must not also be listed as an alias")
    return CanonicalTemplateFamily(
        family_id=_expect_str(raw_family, "family_id"),
        category=_expect_str(raw_family, "category"),
        title=_expect_str(raw_family, "title"),
        figure_archetype=_expect_str(raw_family, "figure_archetype"),
        canonical_template_id=canonical_template_id,
        aliases=aliases,
        default_visible=_expect_bool(raw_family, "default_visible"),
        migration_reason=_expect_str(raw_family, "migration_reason"),
    )


def load_canonical_template_catalog(pack_root: Path) -> CanonicalTemplateCatalog | None:
    path = pack_root / "canonical_template_catalog.json"
    if not path.is_file():
        return None
    payload = _read_json_object(path)
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != 1:
        raise ValueError("canonical template catalog schema_version must equal 1")
    raw_families = payload.get("families")
    if not isinstance(raw_families, list) or not raw_families:
        raise ValueError("canonical template catalog families must be a non-empty list")

    families: list[CanonicalTemplateFamily] = []
    entries_by_template_id: dict[str, CanonicalTemplateEntry] = {}
    canonical_template_ids: list[str] = []
    alias_template_ids: list[str] = []
    for index, raw_family in enumerate(raw_families):
        if not isinstance(raw_family, dict):
            raise ValueError(f"canonical template catalog families[{index}] must be an object")
        family = _parse_family(raw_family)
        if family.family_id in {item.family_id for item in families}:
            raise ValueError(f"duplicate canonical family_id `{family.family_id}`")
        families.append(family)
        canonical_entry = CanonicalTemplateEntry(
            family_id=family.family_id,
            family_title=family.title,
            family_category=family.category,
            figure_archetype=family.figure_archetype,
            canonical_template_id=family.canonical_template_id,
            template_id=family.canonical_template_id,
            migration_status="canonical",
            default_visible=family.default_visible,
            aliases=family.aliases,
            migration_reason=family.migration_reason,
        )
        if family.canonical_template_id in entries_by_template_id:
            raise ValueError(f"duplicate canonical template id `{family.canonical_template_id}`")
        entries_by_template_id[family.canonical_template_id] = canonical_entry
        canonical_template_ids.append(family.canonical_template_id)
        for alias in family.aliases:
            if alias in entries_by_template_id:
                raise ValueError(f"duplicate canonical alias template id `{alias}`")
            entries_by_template_id[alias] = CanonicalTemplateEntry(
                family_id=family.family_id,
                family_title=family.title,
                family_category=family.category,
                figure_archetype=family.figure_archetype,
                canonical_template_id=family.canonical_template_id,
                template_id=alias,
                migration_status="migrated_alias",
                default_visible=False,
                aliases=family.aliases,
                migration_reason=family.migration_reason,
            )
            alias_template_ids.append(alias)

    return CanonicalTemplateCatalog(
        schema_version=schema_version,
        catalog_id=_expect_str(payload, "catalog_id"),
        pack_id=_expect_str(payload, "pack_id"),
        purpose=_expect_str(payload, "purpose"),
        default_surface_policy=dict(payload.get("default_surface_policy") or {}),
        external_learning_refs=dict(payload.get("external_learning_refs") or {}),
        families=tuple(families),
        entries_by_template_id=entries_by_template_id,
        canonical_template_ids=tuple(canonical_template_ids),
        alias_template_ids=tuple(alias_template_ids),
    )


def default_canonical_entry(template_id: str, *, category: str, title: str) -> CanonicalTemplateEntry:
    return CanonicalTemplateEntry(
        family_id=template_id,
        family_title=title or template_id,
        family_category=category,
        figure_archetype="unclassified_template",
        canonical_template_id=template_id,
        template_id=template_id,
        migration_status="canonical_unclassified",
        default_visible=True,
        aliases=(),
        migration_reason="No pack-local canonical catalog entry was found for this template.",
    )


def canonical_catalog_entry_for_template(
    *,
    catalog: CanonicalTemplateCatalog | None,
    template_id: str,
    category: str,
    title: str,
) -> CanonicalTemplateEntry:
    if catalog is None:
        return default_canonical_entry(template_id, category=category, title=title)
    return catalog.entries_by_template_id.get(
        template_id,
        default_canonical_entry(template_id, category=category, title=title),
    )
