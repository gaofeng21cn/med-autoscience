from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from med_autoscience import stage_route_contract as stage_route_contract_module
from med_autoscience.stage_route_contract import (
    PROGRESS_FIRST_SPRINT_CONTRACT_FIELD,
    PROGRESS_FIRST_SPRINT_ID,
    PROGRESS_FIRST_SPRINT_WORK_UNIT,
    ROUTE_OBLIGATION_FIELDS,
    STAGE_ROUTE_CONTRACT_REF,
    late_stage_progress_sprint_contract_from_payload,
    load_stage_route_contract,
    load_stage_route_contract_payload,
    route_obligations_descriptor_from_payload,
    stage_entry_modes_from_payload,
)


def test_stage_route_contract_source_uses_standard_agent_stage_slot() -> None:
    payload = load_stage_route_contract_payload()

    assert STAGE_ROUTE_CONTRACT_REF == "agent/stages/stage_route_contract.yaml"
    assert set(payload) >= {
        "compatible_agents",
        PROGRESS_FIRST_SPRINT_CONTRACT_FIELD,
        "route_contracts",
        "modes",
        "evidence_review_contract",
    }
    assert load_stage_route_contract() == stage_entry_modes_from_payload(payload)


def test_route_obligations_descriptor_projects_all_canonical_routes_for_handoff() -> None:
    payload = load_stage_route_contract_payload()

    descriptor = route_obligations_descriptor_from_payload(payload)

    assert descriptor["surface_kind"] == "stage_route_obligations_descriptor"
    assert descriptor["contract_ref"] == STAGE_ROUTE_CONTRACT_REF
    assert descriptor["route_count"] == len(payload["route_contracts"])
    assert descriptor["status"] == "present"
    assert descriptor["missing_route_fields"] == {}
    assert descriptor["blockers"] == []
    assert list(descriptor["routes"]) == list(payload["route_contracts"])
    assert descriptor["authority_boundary"]["descriptor_only"] is True
    assert descriptor["authority_boundary"]["can_write_domain_truth"] is False
    for route_id, route_payload in payload["route_contracts"].items():
        route_descriptor = descriptor["routes"][route_id]
        assert route_descriptor["route_id"] == route_id
        assert route_descriptor["status"] == "present"
        assert route_descriptor["source_ref"] == f"{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}"
        assert route_descriptor["handoff_readiness"] == {
            "status": "present",
            "missing_fields": [],
            "blocker": None,
        }
        for field in ROUTE_OBLIGATION_FIELDS:
            obligation_projection = route_descriptor[field]
            assert obligation_projection["status"] == "present"
            assert obligation_projection["items"] == route_payload[field]
            assert obligation_projection["source_ref"] == (
                f"{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}/{field}"
            )
            assert all(item["status"] == "present" for item in obligation_projection["item_descriptors"])


def test_route_obligations_descriptor_reports_missing_handoff_obligations() -> None:
    payload = load_stage_route_contract_payload()
    del payload["route_contracts"]["baseline"]["knowledge_input_obligations"]
    del payload["route_contracts"]["decision"]["memory_closeout_obligations"]

    descriptor = route_obligations_descriptor_from_payload(payload)

    assert descriptor["status"] == "missing"
    assert descriptor["missing_route_fields"] == {
        "baseline": ["knowledge_input_obligations"],
        "decision": ["memory_closeout_obligations"],
    }
    assert descriptor["routes"]["baseline"]["status"] == "missing"
    assert descriptor["routes"]["baseline"]["knowledge_input_obligations"] == {
        "status": "missing",
        "items": [],
        "item_descriptors": [],
        "source_ref": f"{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/baseline/knowledge_input_obligations",
        "blocker": None,
    }
    assert descriptor["routes"]["decision"]["handoff_readiness"] == {
        "status": "missing",
        "missing_fields": ["memory_closeout_obligations"],
        "blocker": None,
    }


def test_stage_route_contract_loader_falls_back_to_packaged_resource(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packaged_resource = tmp_path / "stage_route_contract.yaml"
    packaged_resource.write_text(
        Path(STAGE_ROUTE_CONTRACT_REF).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(stage_route_contract_module, "find_stage_route_contract_path", lambda: None)
    monkeypatch.setattr(stage_route_contract_module, "files", lambda package: tmp_path)

    payload = load_stage_route_contract_payload()

    assert payload["compatible_agents"] == ["Codex", "Claude Code", "OpenClaw"]


def test_load_stage_route_contract_returns_canonical_modes() -> None:
    modes = load_stage_route_contract()

    assert len(modes) == 6
    assert tuple(mode.mode_id for mode in modes) == (
        "full_research",
        "literature_scout",
        "idea_exploration",
        "project_optimization",
        "writing_delivery",
        "manuscript_fast_lane",
    )
    assert all("Claude Code" in mode.compatible_agents for mode in modes)


def test_load_stage_route_contract_keeps_formal_chain_and_writing_constraints() -> None:
    modes = {mode.mode_id: mode for mode in load_stage_route_contract()}
    full_research = modes["full_research"]
    writing_delivery = modes["writing_delivery"]
    manuscript_fast_lane = modes["manuscript_fast_lane"]

    assert full_research.default_runtime_mode == "managed"
    assert full_research.preconditions == ("workspace/profile available",)
    assert full_research.managed_entry_actions == (
        "doctor",
        "bootstrap",
        "overlay-status",
        "request-opl-stage-attempt",
    )
    assert full_research.managed_routes == (
        "scout",
        "idea",
        "write",
        "finalize",
    )
    assert full_research.startup_boundary_gated_routes == (
        "baseline",
        "experiment",
        "analysis-campaign",
    )
    assert full_research.governance_routes == ("decision",)
    assert writing_delivery.lightweight_routes == ("write",)
    assert writing_delivery.startup_boundary_gated_routes == ()
    assert writing_delivery.auxiliary_routes == ("journal-resolution",)
    assert "submission bundle or final delivery requested" in writing_delivery.upgrade_triggers
    assert manuscript_fast_lane.default_runtime_mode == "lightweight"
    assert manuscript_fast_lane.lightweight_routes == ("write", "finalize")
    assert manuscript_fast_lane.startup_boundary_gated_routes == ()
    assert any("new analysis" in trigger for trigger in manuscript_fast_lane.upgrade_triggers)


def test_load_stage_route_contract_payload_reads_canonical_agents_and_mode_count() -> None:
    payload = load_stage_route_contract_payload()

    assert payload["compatible_agents"] == ["Codex", "Claude Code", "OpenClaw"]
    assert len(payload["modes"]) == 6


def test_late_stage_progress_sprint_contract_covers_dm002_gate_replay_work_unit() -> None:
    payload = load_stage_route_contract_payload()

    contract = late_stage_progress_sprint_contract_from_payload(payload)

    assert contract["sprint_id"] == PROGRESS_FIRST_SPRINT_ID
    assert PROGRESS_FIRST_SPRINT_WORK_UNIT in contract["covered_work_units"]
    assert set(contract["covered_routes"]) >= {"write", "review", "finalize"}
    assert contract["control_plane_outputs"] == [
        "progress_delta",
        "single_next_owner_blocker",
        "human_gate",
        "stop_loss",
    ]
    assert "record_only_reviewer_loop" in contract["forbidden_control_plane_outputs"]
    assert "provider_completed_without_typed_closeout" in contract["forbidden_control_plane_outputs"]
    assert contract["currentness_followthrough_policy"] == [
        (
            "consumed AI reviewer record production must advance to the current controller write/gate owner "
            "with owner_output_consumption preserved"
        ),
        (
            "stale manuscript-digest write dispatch must route to AI reviewer current-manuscript record production, "
            "not repeat the same write dispatch"
        ),
        (
            "receipt/read-model reconcile is a platform step and cannot consume the sprint budget unless it yields "
            "a concrete next owner, typed blocker, human gate, or stop-loss"
        ),
    ]


def test_stage_entry_modes_from_payload_preserves_mode_level_managed_entry_actions() -> None:
    payload = load_stage_route_contract_payload()
    payload["modes"] = [
        {
            "mode_id": "full_research",
            "display_name": "Full Research",
            "default_runtime_mode": "managed",
            "preconditions": ["workspace/profile available"],
            "lightweight_scope": "none",
            "managed_entry_actions": ["doctor", "bootstrap", "request-opl-stage-attempt"],
            "lightweight_routes": [],
            "managed_routes": [
                "scout",
                "idea",
                "write",
                "finalize",
            ],
            "startup_boundary_gated_routes": ["baseline", "experiment", "analysis-campaign"],
            "governance_routes": ["decision"],
            "auxiliary_routes": [],
            "upgrade_triggers": [],
        },
        {
            "mode_id": "writing_delivery",
            "display_name": "Writing Delivery",
            "default_runtime_mode": "lightweight",
            "preconditions": ["workspace/profile available"],
            "lightweight_scope": "manuscript and delivery packaging",
            "managed_entry_actions": ["doctor", "overlay-status", "request-opl-stage-attempt"],
            "lightweight_routes": ["write"],
            "managed_routes": ["write", "finalize"],
            "startup_boundary_gated_routes": [],
            "governance_routes": [],
            "auxiliary_routes": ["journal-resolution"],
            "upgrade_triggers": ["submission bundle or final delivery requested"],
        },
    ]

    modes = {mode.mode_id: mode for mode in stage_entry_modes_from_payload(payload)}

    assert modes["full_research"].managed_entry_actions == ("doctor", "bootstrap", "request-opl-stage-attempt")
    assert modes["writing_delivery"].managed_entry_actions == (
        "doctor",
        "overlay-status",
        "request-opl-stage-attempt",
    )


def test_payload_and_typed_loader_use_top_level_compatible_agents() -> None:
    payload = load_stage_route_contract_payload()
    modes_payload = payload["modes"]
    assert isinstance(modes_payload, list)
    for mode in modes_payload:
        assert isinstance(mode, dict)
        assert "compatible_agents" not in mode

    canonical_agents = tuple(payload["compatible_agents"])
    modes = load_stage_route_contract()
    assert all(mode.compatible_agents == canonical_agents for mode in modes)


def test_load_stage_route_contract_payload_rejects_missing_required_list_field(tmp_path: Path) -> None:
    path = tmp_path / "invalid_stage_route_contract.yaml"
    payload = load_stage_route_contract_payload()
    payload["modes"] = [
        {
            "mode_id": "broken_mode",
            "display_name": "Broken Mode",
            "default_runtime_mode": "lightweight",
            "preconditions": ["workspace/profile available"],
            "lightweight_scope": "demo",
            "managed_entry_actions": ["doctor", "bootstrap", "overlay-status"],
            "lightweight_routes": ["write"],
            "startup_boundary_gated_routes": [],
            "governance_routes": [],
            "auxiliary_routes": [],
            "upgrade_triggers": [],
        }
    ]
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="managed_routes"):
        load_stage_route_contract_payload(path=path)


def test_stage_entry_modes_reject_mode_level_compatible_agents_override() -> None:
    payload = load_stage_route_contract_payload()
    payload["modes"] = [
        {
            "mode_id": "full_research",
            "display_name": "Full Research",
            "default_runtime_mode": "managed",
            "compatible_agents": ["Codex"],
            "preconditions": ["workspace/profile available"],
            "lightweight_scope": "none",
            "managed_entry_actions": ["doctor", "bootstrap", "overlay-status", "request-opl-stage-attempt"],
            "lightweight_routes": [],
            "managed_routes": [
                "scout",
                "idea",
                "write",
                "finalize",
            ],
            "startup_boundary_gated_routes": ["baseline", "experiment", "analysis-campaign"],
            "governance_routes": ["decision"],
            "auxiliary_routes": [],
            "upgrade_triggers": [],
        }
    ]

    with pytest.raises(ValueError, match="compatible_agents"):
        stage_entry_modes_from_payload(payload)


def test_stage_route_contract_parser_preserves_distinct_entry_actions() -> None:
    payload = load_stage_route_contract_payload()
    payload["modes"][0]["managed_entry_actions"] = ["doctor", "bootstrap"]

    assert stage_entry_modes_from_payload(payload)[0].managed_entry_actions == ("doctor", "bootstrap")
