from __future__ import annotations

import importlib
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
    assert payload["stage_native_semantic_pack_ref"] == (
        "agent/stages/stage_native_semantic_pack.yaml#/stage_native_semantic_pack"
    )
    assert set(payload) >= {
        "compatible_agents",
        "stage_native_semantic_pack_ref",
        PROGRESS_FIRST_SPRINT_CONTRACT_FIELD,
        "route_contracts",
        "modes",
        "evidence_review_contract",
    }
    assert load_stage_route_contract() == stage_entry_modes_from_payload(payload)


def test_stage_native_semantic_pack_covers_all_stage_obligation_fields() -> None:
    semantic_pack_path = Path("agent/stages/stage_native_semantic_pack.yaml")
    payload = yaml.safe_load(semantic_pack_path.read_text(encoding="utf-8"))
    pack = payload["stage_native_semantic_pack"]

    assert pack["source_design"] == "docs/runtime/designs/coscientist_stage_route_restructure.md"
    assert pack["state"] == "semantic_pack_contract_source"
    required_fields = set(pack["required_stage_fields"])
    assert required_fields == {
        "stage_objective",
        "entry_contract",
        "skill_pack",
        "tool_policy",
        "knowledge_packet",
        "portfolio_input",
        "quality_gate",
        "closeout",
        "memory_writeback",
        "opl_projection",
    }
    assert pack["advisory_signal_policy"]["forbidden_authority_uses"]
    assert "ranking" in pack["advisory_signal_policy"]["advisory_only"]
    assert "proximity" in pack["advisory_signal_policy"]["advisory_only"]
    light_source = pack["advisory_signal_policy"]["clean_room_pattern_sources"][
        "light_external_pattern_intake"
    ]
    assert light_source["source_project"] == "Light0305/Light"
    assert light_source["absorbed_as"] == (
        "mas_native_progress_first_advisory_and_skill_engineering_contract_pattern"
    )
    assert {
        "MODE_REGISTRY.md",
        "skills/light-orchestrator/references/passport.md",
        "skills/light-orchestrator/references/checkpoints.md",
        "skills/light-citation/references/locator_audit.md",
        "skills/light-literature-search/scripts/prisma_flow.py",
        "skills/light-figure-drawing/references/figure_integrity.md",
        "skills/light-figure-drawing/scripts/figure_integrity_lint.py",
        "skills/light-paper-polishing/references/argument_review.md",
        "skills/light-paper-polishing/scripts/style_fingerprint.py",
    } <= set(light_source["source_paths"])
    assert {
        "progress_passport_ref_ledger",
        "checkpoint_gate_budget",
        "progressive_disclosure_skill_bundle",
        "bounded_mode_registry",
        "citation_locator_audit",
        "prisma_flow_count_reconciliation",
        "style_fingerprint_author_voice_hint",
        "argument_review_claim_evidence_boundary",
        "figure_integrity_lint_warning_ref",
    } <= set(light_source["useful_patterns"])
    assert light_source["orchestrator_dependency"] is False
    assert light_source["copy_external_skill_inventory"] is False
    assert light_source["may_create_or_replace_stage_router"] is False
    jit_affordance_strategy = pack["progress_enhancement"]["jit_affordance_strategy"]
    assert jit_affordance_strategy["default_invocation"] == "none"
    assert jit_affordance_strategy["default_design"] == "ordinary_progress_has_no_extra_advisory_stage"
    assert jit_affordance_strategy["secondary_invocation_cap"][
        "skill_engineering_intake_limit"
    ] == "skill_engineering_affordance_gaps_do_not_preflight_block_dispatch"
    light_mechanism = pack["progress_enhancement"]["jit_affordance_strategy"]["mechanisms"][
        "light_external_pattern_intake"
    ]
    assert {
        "skill_engineering_affordance_ref",
        "progress_passport_ref",
        "citation_locator_audit_ref",
        "prisma_flow_reconciliation_ref",
        "argument_review_hint_ref",
        "figure_integrity_warning_ref",
    } <= set(light_mechanism["output_refs"])
    assert light_mechanism["skill_engineering_policy"] == {
        "passport_maps_to": "mas_stage_attempt_ledger_and_owner_receipt_refs",
        "checkpoint_maps_to": "route_back_typed_blocker_human_gate_or_known_limitation_refs",
        "mode_registry_maps_to": "bounded_skill_entrypoint_modes_not_stage_router",
        "progressive_disclosure_maps_to": "thin_mas_skill_entrypoint_plus_referenced_contract_refs",
        "argument_review_maps_to": "claim_evidence_boundary_and_hedging_hint_only",
        "figure_integrity_lint_maps_to": "display_reviewer_warning_or_route_required_ref_only",
        "missing_behavior": "skip_or_repair_hint",
    }
    assert {
        "mas_stage_owner_route",
        "mas_app_skill_entrypoint",
    } <= set(light_mechanism["cannot_replace"])
    assert pack["execution_review_independence"]["policy"] == "fail_closed"

    main_stages = pack["main_stages"]
    assert set(main_stages) >= {
        "scout",
        "idea",
        "baseline",
        "experiment",
        "analysis-campaign",
        "write",
        "review",
        "finalize",
        "decision",
        "journal-resolution",
    }
    for stage_id, stage_payload in main_stages.items():
        assert required_fields <= set(stage_payload), stage_id
        assert stage_payload["portfolio_input"]["advisory_signals"]
        assert stage_payload["quality_gate"]["independence"]["fail_closed_if_missing_or_same_invocation"] is True
        assert stage_payload["opl_projection"]["forbidden"]


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


def test_stage_route_contract_declares_machine_anti_loop_policy() -> None:
    dhd = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    payload = load_stage_route_contract_payload()

    policy = payload["anti_loop_policy"]

    assert policy["ordinary_path_root"] == "current_owner_delta"
    assert policy["same_tick_max_passes"] == 3
    assert policy["same_tick_max_passes"] == dhd.PROGRESS_FIRST_SAME_TICK_MAX_PASSES
    assert set(policy["same_tick_continue_reasons"]) == {
        "continue_same_tick_after_sync_owner_delta",
        "continue_same_tick_after_provider_admission_delta",
    }
    assert policy["repeat_identity_fields"] == [
        "study_id",
        "stage_run_id",
        "stage_id",
        "current_owner",
        "work_unit_id",
        "work_unit_fingerprint",
        "target_surface",
        "source_fingerprint",
    ]
    assert policy["allowed_reentry_signals"] == [
        "meaningful_artifact_delta",
        "new_owner_receipt",
        "new_typed_blocker",
        "human_gate_ref",
        "route_back_ref",
        "stop_loss",
        "provider_running_proof",
    ]
    assert "repeat_same_work_unit_without_new_consumed_evidence" in policy["forbidden_loop_shapes"]
    assert {
        "dispatch_materialized_but_not_selected",
        "typed_blocker_or_dispatch_blocker_observed",
        "provider_handoff_written_admission_pending",
        "provider_attempt_started",
        "max_passes_exhausted_owner_delta_required",
    } <= set(policy["terminal_diagnostics"])
    assert policy["exhausted_budget_outputs"] == [
        "TypedBlocker",
        "human_gate_ref",
        "stop_loss",
        "route_back_ref",
    ]
    assert policy["dry_run_write_policy"] == {
        "may_refresh_diagnostic_reports": True,
        "may_write_study_truth": False,
        "may_write_owner_route_reconcile": False,
        "may_dispatch_owner_action": False,
        "may_mutate_paper_or_package": False,
    }


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
