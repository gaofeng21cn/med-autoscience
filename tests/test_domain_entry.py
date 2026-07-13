from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_STAGE_ACTION_IDS = {
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
}
RETIRED_PRIVATE_ACTION_IDS = {
    "study_progress",
    "paper_mission",
    "mainline_status",
    "mainline_phase",
    "domain_handler_export",
    "domain_handler_dispatch",
    "display_pack_capability_discover",
    "display_pack_orchestrate",
    "display_pack_figure_plan",
    "display_pack_preflight",
    "display_pack_render",
    "research_integrity_gate_input",
    "research_integrity_reference_verification",
    "research_integrity_review_publication_gate_stage_hook",
}


def _read_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_v2_catalog_exposes_only_hosted_stage_actions_to_users() -> None:
    catalog = _read_json("contracts/action_catalog.json")
    manifest = _read_json("agent/stages/manifest.json")
    actions = {action["action_id"]: action for action in catalog["actions"]}
    public_actions = {
        action_id: action
        for action_id, action in actions.items()
        if any(surface is not None for surface in action["supported_surfaces"].values())
    }

    assert catalog["version"] == "family-action-catalog.v2"
    assert catalog["target_domain_id"] == "mas"
    assert set(public_actions) == PUBLIC_STAGE_ACTION_IDS
    assert {stage["stage_id"] for stage in manifest["stages"]} == PUBLIC_STAGE_ACTION_IDS
    assert RETIRED_PRIVATE_ACTION_IDS.isdisjoint(actions)

    for action_id, action in public_actions.items():
        assert action["effect"] == "mutating"
        assert action["execution_binding"] == {
            "kind": "stage_binding",
            "stage_manifest_ref": "agent/stages/manifest.json",
        }
        assert action["stage_route"] == {
            "entry_stage_ref": action_id,
            "required_stage_refs": [action_id],
            "optional_stage_refs": [],
            "terminal_stage_refs": [action_id],
            "route_policy": "ai_selected_progress_route",
        }
        assert action["input_schema_ref"] == (
            "contracts/schemas/v2/mas-stage-action.input.schema.json"
        )
        assert action["output_schema_ref"] == (
            "contracts/schemas/v2/mas-stage-action.output.schema.json"
        )
        assert "source_command" not in action
        assert "handler_id" not in action
        assert "handler_ref" not in action
        for surface in action["supported_surfaces"].values():
            if surface is not None:
                assert "command" not in surface


def test_internal_authority_action_is_registry_bound_and_not_a_user_surface() -> None:
    catalog = _read_json("contracts/action_catalog.json")
    registry = _read_json("contracts/domain_handler_registry.json")
    action = next(
        item
        for item in catalog["actions"]
        if item["action_id"] == "paper_mission_authority_evaluate"
    )

    assert action["execution_binding"] == {
        "kind": "handler_ref",
        "handler_ref": "handler:mas.paper-mission-authority-evaluate",
    }
    assert action["effect"] == "read_only"
    assert "stage_route" not in action
    assert all(surface is None for surface in action["supported_surfaces"].values())
    assert registry == {
        "surface_kind": "domain_handler_registry",
        "version": "domain-handler-registry.v1",
        "handlers": [
            {
                "handler_id": "mas.paper-mission-authority-evaluate",
                "binding": {
                    "kind": "python_callable",
                    "module": "med_autoscience.authority_handlers.paper_mission",
                    "callable": "evaluate_paper_mission_authority",
                },
            }
        ],
    }

    binding = registry["handlers"][0]["binding"]
    module = importlib.import_module(binding["module"])
    assert callable(getattr(module, binding["callable"]))


def test_v2_pack_sources_do_not_restore_private_command_templates() -> None:
    descriptor = _read_json("contracts/domain_descriptor.json")
    compiler_input = _read_json("contracts/pack_compiler_input.json")
    handoff = _read_json("contracts/generated_surface_handoff.json")

    workspace_binding = descriptor["standard_agent_interface"]["workspace_binding"]
    runtime = descriptor["standard_agent_interface"]["runtime"]
    assert "entry_command_template" not in workspace_binding
    assert "manifest_command_template" not in workspace_binding
    assert "dispatch_command" not in runtime
    assert compiler_input["source_refs"]["domain_handler_registry"] == (
        "contracts/domain_handler_registry.json"
    )
    assert compiler_input["source_refs"]["source_closure_audit"] == (
        "contracts/source_closure_audit.json"
    )
    assert handoff["generated_surface_policy"]["must_dispatch_to"] == (
        "OPL-hosted MAS stage actions and registry-bound MAS minimal authority functions"
    )

    v2_default_sources = json.dumps(
        [descriptor, compiler_input, handoff], ensure_ascii=True, sort_keys=True
    )
    assert "MedAutoScienceDomainEntry" not in v2_default_sources
    assert "domain_entry.py" not in v2_default_sources
    assert "source_command" not in v2_default_sources
