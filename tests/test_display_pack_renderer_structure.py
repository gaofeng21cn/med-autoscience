from __future__ import annotations

import importlib
import sys
from pathlib import Path
import json
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PACK_MODULE_ROOT = (
    REPO_ROOT
    / "display-packs"
    / "fenggaolab.org.medical-display-core"
    / "src"
    / "fenggaolab_org_medical_display_core"
)
CORE_PACK_SRC_ROOT = CORE_PACK_MODULE_ROOT.parent
CORE_PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"


def test_core_pack_evidence_renderer_is_split_into_maintainable_modules() -> None:
    legacy_single_file = CORE_PACK_MODULE_ROOT / "evidence_figures.py"
    evidence_package = CORE_PACK_MODULE_ROOT / "evidence_figures"

    assert not legacy_single_file.exists()
    assert (evidence_package / "__init__.py").exists()

    module_line_counts = {
        path.relative_to(CORE_PACK_MODULE_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in evidence_package.rglob("*.py")
    }

    assert module_line_counts
    assert module_line_counts["evidence_figures/__init__.py"] <= 220
    assert max(module_line_counts.values()) <= 1500


def test_core_pack_illustration_shells_are_split_into_maintainable_modules() -> None:
    legacy_single_file = CORE_PACK_MODULE_ROOT / "illustration_shells.py"
    illustration_package = CORE_PACK_MODULE_ROOT / "illustration_shells"

    assert not legacy_single_file.exists()
    assert (illustration_package / "__init__.py").exists()

    module_line_counts = {
        path.relative_to(CORE_PACK_MODULE_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in illustration_package.rglob("*.py")
    }

    assert module_line_counts
    assert module_line_counts["illustration_shells/__init__.py"] <= 80
    assert max(module_line_counts.values()) <= 1500


def test_core_pack_evidence_renderer_keeps_stable_python_entrypoint() -> None:
    sys.path.insert(0, str(CORE_PACK_SRC_ROOT))
    module = importlib.import_module("fenggaolab_org_medical_display_core.evidence_figures")

    assert callable(module.render_python_evidence_figure)


def test_core_pack_r_ggplot2_templates_do_not_reference_python_bridge() -> None:
    r_templates = []
    for manifest_path in sorted((CORE_PACK_ROOT / "templates").glob("*/template.toml")):
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if payload["kind"] == "evidence_figure" and payload["renderer_family"] == "r_ggplot2":
            r_templates.append(payload["template_id"])
            assert payload["execution_mode"] == "subprocess"
            assert payload["entrypoint"] == "Rscript render.R --request {request_json}"
            assert "render_r_evidence_figure" not in payload["entrypoint"]
            assert (manifest_path.parent / "render.R").is_file()

    assert len(r_templates) == 22


def test_core_pack_renderer_migration_ledger_covers_all_evidence_templates() -> None:
    ledger = json.loads((CORE_PACK_ROOT / "renderer_migration_ledger.json").read_text(encoding="utf-8"))
    records = ledger["records"]
    manifest_ids = []
    for manifest_path in sorted((CORE_PACK_ROOT / "templates").glob("*/template.toml")):
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if payload["kind"] == "evidence_figure":
            manifest_ids.append(payload["template_id"])

    records_by_template = {item["template_id"]: item for item in records}
    lane_counts = {
        lane: sum(1 for item in records if item["migration_lane"] == lane)
        for lane in ("P0", "P1", "P2")
    }

    assert sorted(records_by_template) == sorted(manifest_ids)
    assert ledger["summary"]["evidence_template_count"] == 84
    assert ledger["summary"]["p0_landed_r_ggplot2_subprocess"] == 22
    assert ledger["summary"]["p1_r_candidate_python_templates"] == 33
    assert ledger["summary"]["p2_retained_python_or_dual_stack_later"] == 29
    assert ledger["summary"]["unclassified"] == 0
    assert lane_counts == {"P0": 22, "P1": 33, "P2": 29}
    assert records_by_template["risk_layering_monotonic_bars"]["migration_lane"] == "P1"
    assert records_by_template["celltype_signature_heatmap"]["migration_lane"] == "P1"
    assert records_by_template["multicenter_generalizability_overview"]["migration_lane"] == "P2"
    assert records_by_template["center_transportability_governance_summary_panel"]["migration_lane"] == "P2"


def test_core_pack_renderer_dependency_profile_declares_r_subprocess_runtime() -> None:
    profile = json.loads((CORE_PACK_ROOT / "renderer_dependency_profile.json").read_text(encoding="utf-8"))
    r_profile = next(item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_evidence_subprocess_v1")
    package_names = {item["name"] for item in r_profile["r_packages"]}

    assert r_profile["renderer_family"] == "r_ggplot2"
    assert r_profile["execution_mode"] == "subprocess"
    assert r_profile["entrypoint_pattern"] == "Rscript render.R --request {request_json}"
    assert {"jsonlite", "ggplot2", "ggsci", "grid"} <= package_names
    assert r_profile["shared_helper_ref"] == "rlib/medicaldisplaycore/evidence_renderer.R"
    assert r_profile["template_wrapper_ref"] == "templates/<template_id>/render.R"
