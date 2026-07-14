from __future__ import annotations

import json
from pathlib import Path
import re

import pytest


pytestmark = pytest.mark.meta
ROOT = Path(__file__).resolve().parents[1]
ALLOWED_MAS_SOURCE_REF_PREFIXES = (
    "src/med_autoscience/authority_handlers/",
    "src/med_autoscience/resources/",
    "src/med_autoscience/styles/",
)
ALLOWED_MAS_MODULE_REF_PREFIXES = (
    "med_autoscience.authority_handlers.paper_mission",
)
CANONICAL_RETIRED_DEFAULT_SURFACE_IDS = [
    "cli",
    "mcp",
    "skill",
    "product_entry",
    "product_status",
    "product_session",
    "domain_handler",
    "workbench",
]


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_python_source_morphology_is_exact_and_private_surfaces_are_absent() -> None:
    source_root = ROOT / "src/med_autoscience"
    relative_files = {
        path.relative_to(ROOT).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    }
    assert relative_files == {
        "src/med_autoscience/__init__.py",
        "src/med_autoscience/authority_handlers/__init__.py",
        "src/med_autoscience/authority_handlers/paper_mission.py",
        "src/med_autoscience/resources/__init__.py",
        "src/med_autoscience/resources/stage_route_contract.yaml",
        "src/med_autoscience/styles/__init__.py",
        "src/med_autoscience/styles/american-chemical-society.csl",
        "src/med_autoscience/styles/american-medical-association.csl",
        "src/med_autoscience/styles/frontiers.csl",
    }


def test_action_catalog_exposes_six_hosted_stages_and_one_internal_handler() -> None:
    catalog = _load("contracts/action_catalog.json")
    registry = _load("contracts/domain_handler_registry.json")
    actions = catalog["actions"]
    stage_actions = [
        action
        for action in actions
        if action["execution_binding"]["kind"] == "stage_binding"
    ]
    authority_actions = [
        action
        for action in actions
        if action["execution_binding"]["kind"] == "handler_ref"
    ]

    assert catalog["version"] == "family-action-catalog.v2"
    assert [action["action_id"] for action in stage_actions] == [
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert all(
        action["execution_binding"]
        == {
            "kind": "stage_binding",
            "stage_manifest_ref": "agent/stages/manifest.json",
        }
        for action in stage_actions
    )
    assert [action["action_id"] for action in authority_actions] == [
        "paper_mission_authority_evaluate"
    ]
    assert authority_actions[0]["execution_binding"]["handler_ref"] == (
        f"handler:{registry['handlers'][0]['handler_id']}"
    )


def test_generated_surfaces_are_opl_owned_and_private_surfaces_are_forbidden() -> None:
    handoff = _load("contracts/generated_surface_handoff.json")
    policy = _load("contracts/private_functional_surface_policy.json")
    audit = _load("contracts/functional_privatization_audit.json")

    assert {surface["surface_id"] for surface in handoff["generated_surfaces"]} == {
        "cli",
        "mcp",
        "skill",
        "product_entry_manifest",
        "domain_handler",
        "status_read_model",
        "workbench_drilldown",
    }
    assert all(
        surface["owner"] == "one-person-lab"
        for surface in handoff["generated_surfaces"]
    )
    assert all(
        value is False for value in policy["no_second_control_plane_gate"].values()
    )
    assert audit["status"] == (
        "standard_domain_pack_and_registry_bound_authority_function_only"
    )
    assert len(audit["modules"]) == 1
    assert audit["modules"][0]["classification"] == "minimal_authority_function"
    assert audit["retired_default_surface_ids"] == (
        CANONICAL_RETIRED_DEFAULT_SURFACE_IDS
    )
    assert audit["default_surface_boundary"] == {
        "state": "physically_absent",
        "owner": "one-person-lab",
        "domain_repo_can_own_default_surface": False,
        "verification_ref": "scripts/repo_hygiene_audit.py",
    }
    boundary_text = json.dumps(audit["default_surface_boundary"]).lower()
    assert "allowlist" not in boundary_text
    assert "whitelist" not in boundary_text
    assert (ROOT / "agent/primary_skill/SKILL.md").is_file()
    assert (
        ROOT / "src/med_autoscience/authority_handlers/paper_mission.py"
    ).is_file()


def test_direct_skill_and_plugin_carrier_are_byte_identical() -> None:
    primary = ROOT / "agent/primary_skill/SKILL.md"
    carrier = (
        ROOT
        / "plugins/med-autoscience/skills/med-autoscience/SKILL.md"
    )
    assert primary.read_bytes() == carrier.read_bytes()


def test_no_active_contract_uses_retired_callable_or_mixed_route_owner() -> None:
    active_roots = [ROOT / "agent", ROOT / "contracts", ROOT / "runtime"]
    forbidden = {
        "validator_ref",
        '"route_selection_owner"',
        "med_autoscience.controllers.",
        "med_autoscience.opl_domain_pack.",
        "med_autoscience.runtime.",
        "src/med_autoscience/controllers/",
        "src/med_autoscience/opl_domain_pack/",
    }
    matches: dict[str, list[str]] = {}
    for root in active_roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".yaml", ".yml", ".md"}:
                continue
            content = path.read_text(encoding="utf-8")
            found = sorted(token for token in forbidden if token in content)
            if found:
                matches[path.relative_to(ROOT).as_posix()] = found

    assert matches == {}


def test_active_machine_surfaces_do_not_reference_retired_mas_implementation() -> None:
    active_roots = [ROOT / "agent", ROOT / "contracts", ROOT / "runtime"]
    source_pattern = re.compile(r"src/med_autoscience/[A-Za-z0-9_.*?/-]+")
    module_pattern = re.compile(r"(?<![A-Za-z0-9_])med_autoscience\.[A-Za-z0-9_.]+")
    matches: dict[str, list[str]] = {}

    for root in active_roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".yaml", ".yml", ".md"}:
                continue
            content = path.read_text(encoding="utf-8")
            retired_refs = {
                ref
                for ref in source_pattern.findall(content)
                if not ref.startswith(ALLOWED_MAS_SOURCE_REF_PREFIXES)
            }
            retired_refs.update(
                ref
                for ref in module_pattern.findall(content)
                if not ref.startswith(ALLOWED_MAS_MODULE_REF_PREFIXES)
            )
            if retired_refs:
                matches[path.relative_to(ROOT).as_posix()] = sorted(retired_refs)

    assert matches == {}


def test_active_machine_contract_local_test_refs_exist() -> None:
    missing: dict[str, list[str]] = {}

    def visit(value: object) -> list[str]:
        if isinstance(value, dict):
            return [ref for item in value.values() for ref in visit(item)]
        if isinstance(value, list):
            return [ref for item in value for ref in visit(item)]
        if isinstance(value, str) and value.startswith("tests/"):
            return [value]
        return []

    for path in sorted((ROOT / "contracts").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for ref in visit(payload):
            local_path = ref.split("::", maxsplit=1)[0].split("#", maxsplit=1)[0]
            if local_path.endswith("/") or any(token in local_path for token in "*?["):
                continue
            if not (ROOT / local_path).exists():
                relative_path = path.relative_to(ROOT).as_posix()
                missing.setdefault(relative_path, []).append(ref)

    assert missing == {}
