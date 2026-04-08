from __future__ import annotations

from contextlib import contextmanager
import importlib
from pathlib import Path
import sys
import tomllib

from med_autoscience import display_registry
from med_autoscience.display_pack_bootstrap import (
    CORE_PACK_ID,
    export_core_pack_template_manifests,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def _load_entrypoint(entrypoint: str) -> object:
    module_name, function_name = entrypoint.split(":", 1)
    importlib.invalidate_caches()
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


@contextmanager
def _core_pack_src_on_sys_path():
    src_root = REPO_ROOT / "display-packs" / CORE_PACK_ID / "src"
    src_root_str = str(src_root)
    already_present = src_root_str in sys.path
    if not already_present:
        sys.path.insert(0, src_root_str)
        importlib.invalidate_caches()
    try:
        yield
    finally:
        if not already_present:
            sys.path.remove(src_root_str)


def test_exported_entrypoint_is_real_importable_callable(tmp_path: Path) -> None:
    export_core_pack_template_manifests(tmp_path)
    representative_entrypoints = {
        "roc_curve_binary": "fenggaolab_org_medical_display_core.evidence_figures:render_r_evidence_figure",
        "time_to_event_risk_group_summary": (
            "fenggaolab_org_medical_display_core.evidence_figures:render_python_evidence_figure"
        ),
        "cohort_flow_figure": "fenggaolab_org_medical_display_core.illustration_shells:render_illustration_shell",
        "table1_baseline_characteristics": "fenggaolab_org_medical_display_core.table_shells:render_table_shell",
    }

    with _core_pack_src_on_sys_path():
        for template_short_id, expected_entrypoint in representative_entrypoints.items():
            payload = tomllib.loads(
                (tmp_path / "templates" / template_short_id / "template.toml").read_text(encoding="utf-8")
            )
            entrypoint = payload["entrypoint"]
            target = _load_entrypoint(entrypoint)
            assert entrypoint == expected_entrypoint
            assert callable(target)


def test_exported_manifests_do_not_reference_host_materialization_entrypoint(tmp_path: Path) -> None:
    export_core_pack_template_manifests(tmp_path)
    manifest_paths = sorted(tmp_path.glob("templates/*/template.toml"))

    assert manifest_paths
    for manifest_path in manifest_paths:
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        assert payload["entrypoint"] != (
            "med_autoscience.controllers.display_surface_materialization:materialize_display_surface"
        )


def test_exported_manifests_move_all_figure_execution_into_pack_local_modules(tmp_path: Path) -> None:
    export_core_pack_template_manifests(tmp_path)

    for spec in (
        *display_registry.list_evidence_figure_specs(),
        *display_registry.list_illustration_shell_specs(),
        *display_registry.list_table_shell_specs(),
    ):
        short_id = _short_id(spec.template_id if hasattr(spec, "template_id") else spec.shell_id)
        payload = tomllib.loads((tmp_path / "templates" / short_id / "template.toml").read_text(encoding="utf-8"))
        assert payload["entrypoint"].startswith("fenggaolab_org_medical_display_core.")


def test_export_does_not_delete_unrelated_template_directories(tmp_path: Path) -> None:
    extra_dir = tmp_path / "templates" / "local_custom_template"
    extra_dir.mkdir(parents=True)
    marker_path = extra_dir / "keep.txt"
    marker_path.write_text("do-not-delete", encoding="utf-8")

    export_core_pack_template_manifests(tmp_path)

    assert marker_path.read_text(encoding="utf-8") == "do-not-delete"
