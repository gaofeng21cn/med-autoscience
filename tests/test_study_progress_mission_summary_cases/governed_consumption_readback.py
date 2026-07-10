from __future__ import annotations

import importlib
import json
import os

import pytest

from med_autoscience.paper_mission_run import PaperMissionRun
from med_autoscience.paper_mission_transaction import PaperMissionTransaction
from tests.paper_mission_test_helpers import (
    _write_matching_domain_gate_closeout,
    _paper_mission_transaction_payload,
    _paper_mission_forbidden_write_guard,
    _write_submission_milestone_package,
)
from tests.profile_test_helpers import write_profile

def test_typed_blocker_resolution_successor_supersedes_stale_wakeup_top_level(
    tmp_path,
) -> None:
    from types import SimpleNamespace

    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    packet_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
        / study_id
    )
    packet_root.mkdir(parents=True)
    typed_ref = "/tmp/obesity/stage_closure_decision.json"
    (packet_root / "typed_blocker_resolution.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_typed_blocker_resolution",
                "schema_version": 1,
                "status": "human_gate_resolution_packet_materialized",
                "study_id": study_id,
                "resolution_packet_materialized": True,
                "authority_materialized": False,
                "writes_authority": False,
                "submission_ready_claim_authorized": False,
                "authority_boundary": {
                    "projection_only": True,
                    "writes_owner_receipt": False,
                    "writes_typed_blocker": False,
                    "writes_human_gate": False,
                    "writes_current_package": False,
                    "writes_publication_eval": False,
                    "writes_controller_decision": False,
                    "writes_runtime_queue_or_provider_attempt": False,
                },
                "typed_blocker": {
                    "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                    "typed_blocker_evidence_ref": typed_ref,
                },
                "next_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "study_id": study_id,
                    "next_owner": "mas_authority_kernel",
                    "owner": "mas_authority_kernel",
                    "action_type": (
                        "await_human_or_mas_authority_decision_for_submission_blocker"
                    ),
                    "allowed_actions": [
                        "await_human_or_mas_authority_decision_for_submission_blocker"
                    ],
                    "work_unit_id": "submission_blocker_human_gate",
                    "work_unit_fingerprint": "665aca9bc8dce75bc5d41f9a",
                    "acceptance_refs": [typed_ref, "typed_blocker_resolution_packet_ref"],
                    "paper_facing_delta": {
                        "can_submit": False,
                        "delta_kind": "human_gate_decision",
                        "expected_delta": (
                            "paper_mission_stage_route_domain_gate_pending"
                        ),
                        "known_blockers": [],
                        "package_kind": None,
                        "paper_surface": "manuscript/current_package",
                    },
                    "accepted_answer_shape": {
                        "shape_kind": "human_gate_or_degraded_handoff",
                        "accepted_statuses": ["human_gate", "route_back", "typed_blocker"],
                        "required_refs": [
                            "human_gate_question_ref",
                            "known_blockers",
                            "resume_condition",
                        ],
                    },
                    "route_back": {
                        "required": True,
                        "route_back_to": "paper-mission inspect",
                        "route_back_evidence_ref": typed_ref,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    newer_consumption_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "paper_mission_drive"
        / study_id
        / "opl_route_handoff.json"
    )
    newer_consumption_ref.parent.mkdir(parents=True)
    newer_consumption_ref.write_text("{}", encoding="utf-8")

    payload = module._attach_typed_blocker_resolution_successor_projection(
        payload={
            "study_id": study_id,
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "runtime.opl_route",
                "action_type": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "work_unit_id": "old-runtime-route",
            },
            "artifact_first_mission_summary": {
                "read_model_source": {
                    "source_kind": "paper_mission_consumption_ledger",
                    "consumption_ledger_ref": str(newer_consumption_ref),
                }
            },
            "current_stage": "queued",
            "current_stage_summary": "旧 queued/wakeup 投影",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_user_paused_requires_explicit_wakeup",
            "current_blockers": [
                "OPL current_control_state handoff 已陈旧，当前不能确认 stage/runtime owner 仍在接管。",
                "quest user paused requires explicit wakeup",
                "claim_evidence_consistency_failed",
            ],
            "next_system_action": "需要先刷新 OPL current_control_state handoff。",
            "stage_closure_decision": {
                "stage_id": "submission_milestone_candidate",
                "outcome": {
                    "kind": "typed_blocker",
                    "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                },
            },
            "study_macro_state": {"details": {}},
            "user_visible_projection": {
                "current_stage": "queued",
                "next_owner": "one-person-lab",
            },
            "status_narration_contract": {"stage": {}, "readiness": {}},
        },
        profile=SimpleNamespace(workspace_root=workspace_root),
        study_id=study_id,
    )

    assert payload["current_stage"] == "owner_action_ready"
    assert payload["runtime_decision"] == "owner_action_required"
    assert payload["runtime_reason"] == "typed_blocker_resolution_owner_action_ready"
    assert payload["next_action"]["owner"] == "mas_authority_kernel"
    assert payload["current_executable_owner_action"]["next_owner"] == (
        "mas_authority_kernel"
    )
    assert payload["paper_facing_action"]["status"] == "owner_action_ready"
    assert payload["paper_facing_action"]["source_surface"] == "paper_mission.next_action"
    assert payload["user_visible_projection"]["current_stage"] == "owner_action_ready"
    assert payload["user_visible_projection"]["next_owner"] == "mas_authority_kernel"
    assert payload["current_blockers"][0] == (
        "paper_mission_stage_route_domain_gate_pending"
    )
    assert not any(
        "wakeup" in blocker or "OPL current_control_state handoff" in blocker
        for blocker in payload["current_blockers"]
    )
