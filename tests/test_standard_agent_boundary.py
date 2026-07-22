from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_MAS_SOURCE_REF_PREFIXES = (
    "src/med_autoscience/authority_handlers/",
    "src/med_autoscience/styles/",
)
ALLOWED_MAS_MODULE_REF_PREFIXES = (
    "med_autoscience.authority_handlers.candidate_admission",
    "med_autoscience.authority_handlers.build_dependency_currentness",
    "med_autoscience.authority_handlers.paper_mission",
    "med_autoscience.authority_handlers.self_evolution_closeout",
    "med_autoscience.authority_handlers.study_lifecycle_reactivation",
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

def test_action_catalog_exposes_six_hosted_stages_and_four_internal_handlers() -> None:
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
    assert all(
        action["execution_scope"]
        == {"kind": "work_item", "alias_fields": ["study_id"]}
        for action in stage_actions
    )
    assert [action["action_id"] for action in authority_actions] == [
        "study_lifecycle_reactivation_authority_evaluate",
        "candidate_admission_authority_evaluate",
        "build_dependency_currentness_authority_evaluate",
        "paper_mission_authority_evaluate"
    ]
    assert {
        action["action_id"]: action["execution_binding"]["handler_ref"]
        for action in authority_actions
    } == {
        "study_lifecycle_reactivation_authority_evaluate": (
            "handler:mas.study-lifecycle-reactivation-authority-evaluate"
        ),
        "candidate_admission_authority_evaluate": (
            "handler:mas.candidate-admission-authority-evaluate"
        ),
        "build_dependency_currentness_authority_evaluate": (
            "handler:mas.build-dependency-currentness-authority-evaluate"
        ),
        "paper_mission_authority_evaluate": "handler:mas.paper-mission-authority-evaluate",
    }
    assert {item["handler_id"] for item in registry["handlers"]}.issuperset(
        {
            "mas.study-lifecycle-reactivation-authority-evaluate",
            "mas.candidate-admission-authority-evaluate",
            "mas.build-dependency-currentness-authority-evaluate",
            "mas.paper-mission-authority-evaluate",
        }
    )
    assert {
        action["action_id"]: action["execution_scope"]
        for action in authority_actions
    } == {
        "study_lifecycle_reactivation_authority_evaluate": {
            "kind": "work_item",
            "alias_fields": ["study_id"],
        },
        "candidate_admission_authority_evaluate": {
            "kind": "work_item",
            "alias_fields": ["mission.study_id"],
        },
        "build_dependency_currentness_authority_evaluate": {"kind": "none"},
        "paper_mission_authority_evaluate": {
            "kind": "work_item",
            "alias_fields": ["mission.study_id"],
        },
    }


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
    assert len(audit["modules"]) == 5
    assert all(
        module["classification"] == "minimal_authority_function"
        for module in audit["modules"]
    )
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
    assert (
        ROOT / "src/med_autoscience/authority_handlers/candidate_admission.py"
    ).is_file()
    assert (
        ROOT
        / "src/med_autoscience/authority_handlers/self_evolution_closeout.py"
    ).is_file()
    assert (
        ROOT
        / "src/med_autoscience/authority_handlers/study_lifecycle_reactivation.py"
    ).is_file()


def test_direct_skill_and_plugin_carrier_are_byte_identical() -> None:
    primary = ROOT / "agent/primary_skill/SKILL.md"
    carrier = (
        ROOT
        / "plugins/med-autoscience/skills/med-autoscience/SKILL.md"
    )
    assert primary.read_bytes() == carrier.read_bytes()


def test_primary_skill_routes_research_intent_before_lifecycle_and_excludes_clinical_care() -> None:
    skill = (ROOT / "agent/primary_skill/SKILL.md").read_text(encoding="utf-8")

    assert "name: med-autoscience" in skill
    assert "description: Use when Codex needs MedAutoScience (MAS) to plan, conduct, review, or publish medical research" in skill
    assert "Do not use for patient-specific diagnosis, treatment, triage, or emergency advice" in skill
    for heading in (
        "Admission",
        "Action Routing",
        "Default Workflow",
        "Quality And Hard Stops",
        "Output Expectations",
        "References",
    ):
        assert f"## {heading}\n" in skill

    public_actions = [
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    for action_id in public_actions:
        assert f"`{action_id}`" in skill
    assert "Choose the earliest unresolved owning Stage action" in skill
    assert "Do not route patient-specific clinical-care requests to MAS" in skill
    assert "Route funding-call strategy and grant application authoring to MAG" in skill
    assert "do not begin with package lifecycle or environment commands" in skill
    assert "`study_lifecycle_reactivation_authority_evaluate`, `candidate_admission_authority_evaluate`, `build_dependency_currentness_authority_evaluate`, and `paper_mission_authority_evaluate` are internal" in skill
    assert "runtime activity alone never reactivates MAS business truth" in skill
    assert "Retry, review, and repair limits are quality budgets" in skill
    assert "provider completion into MAS authority" in skill


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
