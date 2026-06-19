from __future__ import annotations

import json
import tomllib
from pathlib import Path

from med_autoscience import display_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"
TEMPLATE_ROOT = CORE_PACK_ROOT / "templates"
PACK_SOURCE_ROOT = CORE_PACK_ROOT / "src" / "fenggaolab_org_medical_display_core"


def _template_payloads() -> list[dict[str, object]]:
    return [
        tomllib.loads(path.read_text(encoding="utf-8"))
        for path in sorted(TEMPLATE_ROOT.glob("*/template.toml"))
    ]


def test_current_template_descriptors_have_no_python_evidence_inventory() -> None:
    evidence_templates = [
        payload for payload in _template_payloads()
        if payload["kind"] == "evidence_figure"
    ]
    python_evidence = [
        payload for payload in evidence_templates
        if payload["renderer_family"] == "python"
    ]

    assert len(evidence_templates) == 55
    assert python_evidence == []
    assert {payload["renderer_family"] for payload in evidence_templates} == {"r_ggplot2"}
    assert all(payload["execution_mode"] == "subprocess" for payload in evidence_templates)


def test_current_pack_source_tree_has_no_python_evidence_implementation_inventory() -> None:
    evidence_python_files = sorted((PACK_SOURCE_ROOT / "evidence_figures").rglob("*.py"))

    assert [path.name for path in evidence_python_files] == ["__init__.py", "r_renderer.py"]
    assert not (PACK_SOURCE_ROOT / "evidence_figures" / "python_registry.py").exists()
    assert not [
        path
        for path in evidence_python_files
        if path.name != "__init__.py" and path.name != "r_renderer.py"
    ]


def test_current_runtime_surfaces_have_no_python_evidence_inventory() -> None:
    from med_autoscience.controllers.display_surface_materialization.payload_loader import _VALIDATOR_BY_SCHEMA_ID
    from med_autoscience.display_layout_qc.router import QC_PROFILE_RUNNERS

    evidence_specs = display_registry.list_evidence_figure_specs()
    illustration_specs = display_registry.list_illustration_shell_specs()

    assert len(evidence_specs) == 55
    assert [item.template_id for item in evidence_specs if item.renderer_family == "python"] == []
    assert {item.renderer_family for item in illustration_specs} == {"python"}
    assert set(_VALIDATOR_BY_SCHEMA_ID) == {item.input_schema_id for item in evidence_specs}
    assert not [
        profile
        for profile in QC_PROFILE_RUNNERS
        if "python" in profile.lower() and profile.startswith("publication_")
    ]


def test_current_catalogs_do_not_maintain_retired_python_evidence_id_lists() -> None:
    canonical_catalog = json.loads((CORE_PACK_ROOT / "canonical_template_catalog.json").read_text(encoding="utf-8"))
    migration_ledger = json.loads((CORE_PACK_ROOT / "renderer_migration_ledger.json").read_text(encoding="utf-8"))

    assert "retired_python_evidence_template_ids" not in canonical_catalog
    assert "retired_python_evidence_template_ids" not in migration_ledger
    assert "retired_python_evidence_template_count" not in migration_ledger["summary"]
    assert migration_ledger["summary"]["python_evidence_retained_count"] == 0
    assert canonical_catalog["default_surface_policy"][
        "python_evidence_templates_not_retained_without_advantage_proof"
    ] is True
