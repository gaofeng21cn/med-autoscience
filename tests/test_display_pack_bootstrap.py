from __future__ import annotations

from pathlib import Path
import tomllib

from med_autoscience import display_registry
from med_autoscience.display_pack_bootstrap import (
    CORE_PACK_ID,
    export_core_pack_template_manifests,
)


def _short_id(full_template_id: str) -> str:
    return full_template_id.split("::", 1)[1]


def test_export_core_pack_template_manifests_covers_all_current_specs(tmp_path: Path) -> None:
    export_core_pack_template_manifests(tmp_path)
    manifest_paths = sorted(tmp_path.glob("templates/*/template.toml"))

    expected_full_ids = {
        *(spec.template_id for spec in display_registry.list_evidence_figure_specs()),
        *(spec.shell_id for spec in display_registry.list_illustration_shell_specs()),
        *(spec.shell_id for spec in display_registry.list_table_shell_specs()),
    }
    expected_short_ids = {_short_id(item) for item in expected_full_ids}

    assert CORE_PACK_ID == "fenggaolab.org.medical-display-core"
    assert {path.parent.name for path in manifest_paths} == expected_short_ids


def test_export_core_pack_template_manifests_writes_registry_aligned_payloads(tmp_path: Path) -> None:
    export_core_pack_template_manifests(tmp_path)

    for spec in display_registry.list_evidence_figure_specs():
        short_id = _short_id(spec.template_id)
        payload = tomllib.loads((tmp_path / "templates" / short_id / "template.toml").read_text(encoding="utf-8"))
        assert payload["template_id"] == short_id
        assert payload["full_template_id"] == spec.template_id
        assert payload["kind"] == "evidence_figure"
        assert payload["display_name"] == spec.display_name
        assert payload["paper_family_ids"] == list(spec.paper_family_ids)
        assert payload["renderer_family"] == spec.renderer_family
        assert payload["input_schema_ref"] == spec.input_schema_id
        assert payload["qc_profile_ref"] == spec.layout_qc_profile
        assert payload["required_exports"] == list(spec.required_exports)

    for spec in display_registry.list_illustration_shell_specs():
        short_id = _short_id(spec.shell_id)
        payload = tomllib.loads((tmp_path / "templates" / short_id / "template.toml").read_text(encoding="utf-8"))
        assert payload["template_id"] == short_id
        assert payload["full_template_id"] == spec.shell_id
        assert payload["kind"] == "illustration_shell"
        assert payload["display_name"] == spec.display_name
        assert payload["paper_family_ids"] == list(spec.paper_family_ids)
        assert payload["renderer_family"] == spec.renderer_family
        assert payload["input_schema_ref"] == spec.input_schema_id
        assert payload["qc_profile_ref"] == spec.shell_qc_profile
        assert payload["required_exports"] == list(spec.required_exports)

    for spec in display_registry.list_table_shell_specs():
        short_id = _short_id(spec.shell_id)
        payload = tomllib.loads((tmp_path / "templates" / short_id / "template.toml").read_text(encoding="utf-8"))
        assert payload["template_id"] == short_id
        assert payload["full_template_id"] == spec.shell_id
        assert payload["kind"] == "table_shell"
        assert payload["display_name"] == spec.display_name
        assert payload["paper_family_ids"] == list(spec.paper_family_ids)
        assert payload["renderer_family"] == "n/a"
        assert payload["input_schema_ref"] == spec.input_schema_id
        assert payload["qc_profile_ref"] == spec.table_qc_profile
        assert payload["required_exports"] == list(spec.required_exports)
