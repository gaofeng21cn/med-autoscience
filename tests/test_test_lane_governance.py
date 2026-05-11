from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _test_lane_manifest() -> dict[str, object]:
    return json.loads(_read("contracts/test-lane-manifest.json"))


def test_meta_lane_does_not_rerun_family_or_architecture_owner_tests() -> None:
    makefile = _read("Makefile")
    conftest = _read("tests/conftest.py")

    meta_block = makefile.split("test-meta:", maxsplit=1)[1].split("\ntest-display:", maxsplit=1)[0]
    assert "uv run pytest -q -m meta" in meta_block
    assert "ARCH_OWNER_BOUNDARY_TEST" not in meta_block
    meta_files_block = conftest.split("META_FILES = {", maxsplit=1)[1].split("\n}", maxsplit=1)[0]
    assert "tests/test_dev_preflight.py" not in meta_files_block
    assert "tests/test_dev_preflight_contract.py" not in meta_files_block


def test_test_lane_manifest_paths_exist_and_are_used_by_makefile() -> None:
    manifest = _test_lane_manifest()
    makefile = _read("Makefile")

    for lane in manifest["lanes"].values():
        for path in lane.get("paths", []):
            assert (REPO_ROOT / path).exists(), path
    assert " ".join(manifest["lanes"]["smoke"]["paths"]) in makefile


def test_smoke_lane_files_do_not_perform_subprocess_or_repo_root_writes() -> None:
    manifest = _test_lane_manifest()

    for path in manifest["lanes"]["smoke"]["paths"]:
        tree = ast.parse(_read(path), filename=path)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert "subprocess" not in imported_modules | imported_from_modules
        assert ".sentrux" not in _read(path)


def test_mas_entry_boundary_lane_freezes_sidecar_skill_mcp_and_docs_contract() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-entry-boundary"]

    assert lane["kind"] == "focused_mas_entry_docs_contract_gate"
    assert lane["overlap_policy"] == "allowed_with_regression"
    assert lane["authority_boundary"] == "entry_projection_and_controlled_sidecar_bridge_no_study_truth_authority"
    assert lane["implementation_status"] == "landed_docs_contract"
    assert lane["machine_truth_surface"] == "contracts/test-lane-manifest.json"

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path

    assert lane["docs"] == [
        "docs/status.md",
        "docs/architecture.md",
        "docs/runtime/control/controllers.md",
    ]
    assert lane["docs_boundary"] == {
        "markdown_prose_as_machine_truth_allowed": False,
        "docs_role": "human_navigation_and_boundary_explanation_only",
        "contract_lane": "focused_lanes.mas-entry-boundary",
    }

    framework = lane["family_runtime_framework"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert framework["legacy_optional_providers"] == ["Hermes-Agent"]
    assert framework["role"] == "stage_attempt_queue_wakeup_retry_dead_letter_human_gate_receipt_projection_transport"
    assert set(framework["not_authority_for"]) == {
        "study_truth",
        "publication_quality",
        "quality_gate",
        "artifact_authority",
        "paper_package",
    }

    sidecar = lane["sidecar_bridge"]
    assert sidecar["export_command"] == "medautosci sidecar export --profile <profile> --format json"
    assert sidecar["dispatch_command"] == "medautosci sidecar dispatch --task <task.json> --format json"
    assert sidecar["export_surface_kind"] == "mas_family_sidecar_export"
    assert sidecar["dispatch_receipt_surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert sidecar["bridge_policy"] == "controlled_bridge_to_mas_owner_surface"
    assert sidecar["allowed_bridge_writes"] == [
        "artifacts/runtime/opl_family_sidecar/dispatch_receipts/*.json",
    ]
    assert "runtime_supervisor/reconcile-apply" in sidecar["allowed_task_kinds"]
    assert "notification/receipt" in sidecar["allowed_task_kinds"]

    projections = lane["entry_projection_surfaces"]
    assert projections["action_catalog"] == "med_autoscience.action_catalog family_action_catalog"
    assert projections["mcp"] == "med_autoscience.mcp_server build_tool_manifest action_catalog_projection"
    assert projections["skill"] == "plugins/mas/skills/mas/SKILL.md"
    assert projections["plugin_manifest"] == "plugins/mas/.codex-plugin/plugin.json"
    assert (REPO_ROOT / projections["skill"]).exists()
    assert (REPO_ROOT / projections["plugin_manifest"]).exists()
    assert lane["projection_only_surfaces"] == [
        "MCP tool descriptors",
        "action_catalog projections",
        "single MAS app skill command projection",
        "product-entry manifest action metadata",
    ]
    assert lane["truth_owner"] == "MedAutoScience"
    assert set(lane["forbidden_authority_writes"]) >= {
        "study_truth",
        "study_runtime_status",
        "runtime_watch",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "paper/current_package",
        "manuscript/current_package",
        "quality_ready",
        "publication_ready",
        "submission_ready",
        "artifact_gate_override",
    }
