from __future__ import annotations

from pathlib import Path

from med_autoscience.display_pack_canonical_catalog import load_canonical_template_catalog
from med_autoscience.display_pack_loader import load_enabled_local_display_template_records


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"


def test_canonical_template_catalog_maps_full_template_inventory() -> None:
    catalog = load_canonical_template_catalog(PACK_ROOT)
    assert catalog is not None
    records = load_enabled_local_display_template_records(REPO_ROOT, inventory_scope="all")
    template_ids = {record.template_manifest.template_id for record in records}

    assert set(catalog.canonical_template_ids).issubset(template_ids)
    assert set(catalog.alias_template_ids).issubset(template_ids)
    assert len(catalog.canonical_template_ids) >= 20
    assert len(catalog.alias_template_ids) >= 50
    assert len(catalog.entries_by_template_id) == len(template_ids)

    roc_alias = catalog.entries_by_template_id["time_dependent_roc_horizon"]
    assert roc_alias.migration_status == "migrated_alias"
    assert roc_alias.canonical_template_id == "roc_curve_binary"
    assert roc_alias.default_visible is False

    roc_canonical = catalog.entries_by_template_id["roc_curve_binary"]
    assert roc_canonical.migration_status == "canonical"
    assert roc_canonical.default_visible is True
    assert "time_dependent_roc_horizon" in roc_canonical.aliases
