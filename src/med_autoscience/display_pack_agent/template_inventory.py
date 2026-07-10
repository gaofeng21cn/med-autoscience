from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_analysis_responsibility import analysis_boundary_payload
from med_autoscience.display_pack_canonical_catalog import (
    CanonicalTemplateCatalog,
    CanonicalTemplateEntry,
    canonical_catalog_entry_for_template,
    load_canonical_template_catalog,
)
from med_autoscience.display_pack_dependency_environment import dependency_requirements_for_records
from med_autoscience.display_pack_loader import LoadedDisplayTemplate
from med_autoscience.display_pack_renderer_policy import (
    renderer_policy_completion,
    renderer_policy_payload,
)


@dataclass(frozen=True)
class RendererPolicyProjection:
    kind: str
    renderer_family: str
    default_visible: bool
    canonical_family_id: str
    canonical_template_id: str
    template_id: str


def full_template_id(record: LoadedDisplayTemplate) -> str:
    return record.template_manifest.full_template_id


def catalogs_by_pack_root(records: list[LoadedDisplayTemplate]) -> dict[Path, CanonicalTemplateCatalog | None]:
    catalogs: dict[Path, CanonicalTemplateCatalog | None] = {}
    for record in records:
        if record.pack_root not in catalogs:
            catalogs[record.pack_root] = load_canonical_template_catalog(record.pack_root)
    return catalogs


def migration_index_from_catalogs(
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None],
) -> dict[str, CanonicalTemplateEntry]:
    entries: dict[str, CanonicalTemplateEntry] = {}
    for catalog in catalogs.values():
        if catalog is None:
            continue
        entries.update(catalog.entries_by_template_id)
    return entries


def canonical_entry(
    record: LoadedDisplayTemplate,
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None] | None = None,
) -> CanonicalTemplateEntry:
    manifest = record.template_manifest
    catalog = catalogs.get(record.pack_root) if catalogs is not None else load_canonical_template_catalog(record.pack_root)
    return canonical_catalog_entry_for_template(
        catalog=catalog,
        template_id=manifest.template_id,
        category=manifest.audit_family,
        title=manifest.display_name,
    )


def renderer_policy_projection(
    record: LoadedDisplayTemplate,
    canonical: CanonicalTemplateEntry,
) -> RendererPolicyProjection:
    manifest = record.template_manifest
    return RendererPolicyProjection(
        kind=manifest.kind,
        renderer_family=manifest.renderer_family,
        default_visible=canonical.default_visible,
        canonical_family_id=canonical.family_id,
        canonical_template_id=canonical.canonical_template_id,
        template_id=manifest.template_id,
    )


def template_summary(
    record: LoadedDisplayTemplate,
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None] | None = None,
    request: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    manifest = record.template_manifest
    template_root = record.template_path.parent
    canonical = canonical_entry(record, catalogs)
    request_payload = dict(request or {})
    return {
        "pack_id": record.pack_manifest.pack_id,
        "pack_version": record.pack_manifest.version,
        "template_id": manifest.template_id,
        "full_template_id": manifest.full_template_id,
        "kind": manifest.kind,
        "display_name": manifest.display_name,
        "display_class_id": manifest.display_class_id,
        "audit_family": manifest.audit_family,
        "paper_family_ids": list(manifest.paper_family_ids),
        "renderer_family": manifest.renderer_family,
        "execution_mode": manifest.execution_mode,
        "entrypoint": manifest.entrypoint,
        "input_schema_ref": manifest.input_schema_ref,
        "qc_profile_ref": manifest.qc_profile_ref,
        "required_exports": list(manifest.required_exports),
        "allowed_paper_roles": list(manifest.allowed_paper_roles),
        "paper_proven": manifest.paper_proven,
        "inventory_class": manifest.inventory_class,
        "paper_provenance_refs": list(manifest.paper_provenance_refs),
        "canonical_family_id": canonical.family_id,
        "canonical_family_title": canonical.family_title,
        "canonical_family_category": canonical.family_category,
        "canonical_template_id": canonical.canonical_template_id,
        "figure_archetype": canonical.figure_archetype,
        "analysis_responsibility": canonical.analysis_responsibility,
        "analysis_input_state": canonical.analysis_input_state,
        "medical_family_ids": list(canonical.medical_family_ids),
        "publication_quality_profile": dict(canonical.publication_quality_profile),
        "analysis_boundary": analysis_boundary_payload(
            mode=canonical.analysis_responsibility,
            input_state=canonical.analysis_input_state,
            request=request_payload,
        ),
        "migration_status": canonical.migration_status,
        "resource_class": canonical.resource_class,
        "default_visible": canonical.default_visible,
        "migrated_alias_template_ids": list(canonical.aliases) if canonical.migration_status == "canonical" else [],
        "migration_reason": canonical.migration_reason,
        "renderer_policy": renderer_policy_payload(renderer_policy_projection(record, canonical)),
        "dependency_requirements": dependency_requirements_for_records(
            repo_root=repo_root or record.pack_root,
            records=[record],
        ),
        "has_render_r": (template_root / "render.R").is_file(),
        "has_render_candidate": (template_root / "render_candidate.R").is_file(),
        "golden_case_count": len(manifest.golden_case_paths),
        "exemplar_ref_count": len(manifest.exemplar_refs),
    }


def inventory_summary(records: list[LoadedDisplayTemplate]) -> dict[str, Any]:
    kinds = Counter(record.template_manifest.kind for record in records)
    renderers = Counter(record.template_manifest.renderer_family for record in records)
    execution_modes = Counter(record.template_manifest.execution_mode for record in records)
    catalogs = catalogs_by_pack_root(records)
    canonical_entries = [canonical_entry(record, catalogs) for record in records]
    renderer_policy_records = [
        renderer_policy_projection(record, canonical)
        for record, canonical in zip(records, canonical_entries, strict=True)
    ]
    canonical_template_count = sum(1 for entry in canonical_entries if entry.migration_status == "canonical")
    legacy_alias_count = sum(1 for entry in canonical_entries if entry.migration_status == "migrated_alias")
    default_visible_count = sum(1 for entry in canonical_entries if entry.default_visible)
    paper_proven_count = sum(1 for record in records if record.template_manifest.paper_proven)
    golden_template_count = sum(1 for record in records if record.template_manifest.golden_case_paths)
    exemplar_template_count = sum(1 for record in records if record.template_manifest.exemplar_refs)
    return {
        "template_count": len(records),
        "active_template_count": len(records),
        "canonical_template_count": canonical_template_count,
        "legacy_alias_template_count": legacy_alias_count,
        "default_visible_template_count": default_visible_count,
        "canonical_family_count": len({entry.family_id for entry in canonical_entries if entry.default_visible}),
        "kind_counts": dict(sorted(kinds.items())),
        "renderer_family_counts": dict(sorted(renderers.items())),
        "execution_mode_counts": dict(sorted(execution_modes.items())),
        "paper_proven_template_count": paper_proven_count,
        "golden_template_count": golden_template_count,
        "exemplar_template_count": exemplar_template_count,
        "analysis_responsibility_counts": dict(
            sorted(Counter(entry.analysis_responsibility for entry in canonical_entries).items())
        ),
        "renderer_policy_completion": renderer_policy_completion(renderer_policy_records),
    }
