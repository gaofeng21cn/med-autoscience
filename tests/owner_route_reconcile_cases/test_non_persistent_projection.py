from __future__ import annotations

import importlib
import json
from pathlib import Path
import os

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _supervisor_decision(decision: str, *, study_id: str, fingerprint: str) -> dict:
    return {
        "surface_kind": "paper_autonomy_supervisor_decision",
        "decision": decision,
        "identity_match": True,
        "paper_autonomy_obligation": {
            "surface_kind": "paper_autonomy_obligation",
            "study_id": study_id,
            "quest_id": study_id,
            "stage_id": "publication_supervision",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
            "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        },
        "evidence_refs": [
            f"provider-admission::{study_id}::{fingerprint}",
            f"stage-run-identity::{study_id}::{fingerprint}",
        ],
        "missing_evidence_refs": [],
    }


def _current_owner_action(*, fingerprint: str) -> dict:
    return {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "owner_route_currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
        },
    }


def _current_work_unit(*, study_id: str, fingerprint: str) -> dict:
    return {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
        },
    }


def _write_ready_repair_dispatch(study_root: Path, *, study_id: str, fingerprint: str) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_quality_repair_batch"
        / "stage-packet.json"
    )
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "dispatch_status": "ready",
        "action_type": "run_quality_repair_batch",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "dispatch_authority": "consumer_default_executor_dispatch",
        "refs": {
            "dispatch_path": str(dispatch_path),
            "stage_packet_path": str(stage_packet_path),
        },
        "study_id": study_id,
        "quest_id": study_id,
        "owner_route": {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": study_id,
            "next_owner": "write",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "allowed_actions": ["run_quality_repair_batch"],
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
                "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
                "owner_route_currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
            },
            "truth_epoch": "truth::current",
            "route_epoch": f"route::{fingerprint}",
            "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
            "runtime_health_epoch": "runtime::current",
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
        },
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": {
                "surface": "domain_route_owner_route",
                "schema_version": 2,
                "study_id": study_id,
                "quest_id": study_id,
                "current_owner": "mas_controller",
                "next_owner": "write",
                "owner_reason": "manuscript_story_surface_delta_missing",
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
                "truth_epoch": "truth::current",
                "route_epoch": f"route::{fingerprint}",
                "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
                "runtime_health_epoch": "runtime::current",
                "work_unit_fingerprint": fingerprint,
                "source_fingerprint": fingerprint,
            },
            "allowed_write_surfaces": ["artifacts/controller/repair_execution_evidence/latest.json"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
        },
    }
    _write_json(dispatch_path, dispatch)
    _write_json(stage_packet_path, {**dispatch, "immutable_packet_ref": "existing"})


def test_domain_handler_export_suppresses_current_action_under_supervisor_materialize_decision() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"

    action = module._export_current_owner_action(
        study={},
        current_progress={
            "study_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision(
                    "materialize_recovery_action",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_work_unit": _current_work_unit(study_id=study_id, fingerprint=fingerprint),
            "current_execution_envelope": {"state_kind": "executable_owner_action"},
            "current_executable_owner_action": _current_owner_action(fingerprint=fingerprint),
        },
    )

    assert action == {}


def test_domain_handler_export_allows_current_action_under_supervisor_execute_decision() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"

    action = module._export_current_owner_action(
        study={},
        current_progress={
            "study_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision(
                    "execute_current_owner_delta",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_work_unit": _current_work_unit(study_id=study_id, fingerprint=fingerprint),
            "current_execution_envelope": {"state_kind": "executable_owner_action"},
            "current_executable_owner_action": _current_owner_action(fingerprint=fingerprint),
        },
    )

    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_fingerprint"] == fingerprint


def test_default_executor_dispatch_tasks_block_ready_dispatch_under_supervisor_materialize_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.default_executor_dispatch_tasks"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.toml"
    profile_ref.write_text("[profile]\n", encoding="utf-8")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    tasks = module.default_executor_dispatch_tasks(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        current_owner_action=_current_owner_action(fingerprint=fingerprint),
        current_work_unit=_current_work_unit(study_id=study_id, fingerprint=fingerprint),
        current_execution_envelope={"state_kind": "executable_owner_action"},
        paper_recovery_state={
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "supervisor_decision": _supervisor_decision(
                "materialize_recovery_action",
                study_id=study_id,
                fingerprint=fingerprint,
            ),
        },
        persist_identity=False,
    )

    assert tasks == []


def test_default_executor_dispatch_tasks_execute_decision_allows_ready_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.default_executor_dispatch_tasks"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.toml"
    profile_ref.write_text("[profile]\n", encoding="utf-8")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    tasks = module.default_executor_dispatch_tasks(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        current_owner_action=_current_owner_action(fingerprint=fingerprint),
        current_work_unit=_current_work_unit(study_id=study_id, fingerprint=fingerprint),
        current_execution_envelope={"state_kind": "executable_owner_action"},
        paper_recovery_state={
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "supervisor_decision": _supervisor_decision(
                "execute_current_owner_delta",
                study_id=study_id,
                fingerprint=fingerprint,
            ),
        },
        persist_identity=False,
    )

    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_fingerprint"] == fingerprint


def test_domain_handler_export_does_not_persist_dispatch_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.default_executor_dispatch_tasks"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.toml"
    profile_ref.write_text("[profile]\n", encoding="utf-8")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_quality_repair_batch"
        / "stage-packet.json"
    )
    base_dispatch = {
        "surface": "default_executor_dispatch_request",
        "dispatch_status": "ready",
        "action_type": "run_quality_repair_batch",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "dispatch_authority": "consumer_default_executor_dispatch",
        "refs": {
            "dispatch_path": str(dispatch_path),
            "stage_packet_path": str(stage_packet_path),
        },
        "study_id": study_id,
        "quest_id": study_id,
        "owner_route": {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": study_id,
            "current_owner": "mas_controller",
            "next_owner": "write",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "allowed_actions": ["run_quality_repair_batch"],
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "stale-fp",
                "owner_route_currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "stale-fp",
                    "truth_epoch": "truth::old",
                    "runtime_health_epoch": "runtime::old",
                },
            },
            "truth_epoch": "truth::old",
            "runtime_health_epoch": "runtime::old",
            "work_unit_fingerprint": "stale-fp",
            "source_fingerprint": "stale-fp",
        },
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": {
                "surface": "domain_route_owner_route",
                "schema_version": 2,
                "study_id": study_id,
                "quest_id": study_id,
                "current_owner": "mas_controller",
                "next_owner": "write",
                "owner_reason": "manuscript_story_surface_delta_missing",
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "stale-fp",
                    "owner_route_currentness_basis": {
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "stale-fp",
                    },
                },
                "truth_epoch": "truth::old",
                "runtime_health_epoch": "runtime::old",
                "work_unit_fingerprint": "stale-fp",
                "source_fingerprint": "stale-fp",
            },
            "allowed_write_surfaces": ["paper/draft.md"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }
    _write_json(dispatch_path, base_dispatch)
    _write_json(stage_packet_path, {**base_dispatch, "immutable_packet_ref": "existing"})
    os.utime(dispatch_path, (1_000, 1_000))
    os.utime(stage_packet_path, (1_000, 1_000))
    before_dispatch = dispatch_path.read_text(encoding="utf-8")
    before_stage_packet = stage_packet_path.read_text(encoding="utf-8")
    before_dispatch_mtime = dispatch_path.stat().st_mtime_ns
    before_stage_packet_mtime = stage_packet_path.stat().st_mtime_ns

    current_work_unit = {
        "status": "executable_owner_action",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::current",
        "currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::current",
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
        },
    }
    current_owner_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::current",
        "action_fingerprint": "publication-blockers::current",
        "owner_route_currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::current",
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
        },
    }

    tasks = module.default_executor_dispatch_tasks(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        current_owner_action=current_owner_action,
        current_work_unit=current_work_unit,
        current_execution_envelope={"state_kind": "executable_owner_action"},
        persist_identity=False,
    )

    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_fingerprint"] == "publication-blockers::current"
    assert dispatch_path.read_text(encoding="utf-8") == before_dispatch
    assert stage_packet_path.read_text(encoding="utf-8") == before_stage_packet
    assert dispatch_path.stat().st_mtime_ns == before_dispatch_mtime
    assert stage_packet_path.stat().st_mtime_ns == before_stage_packet_mtime


def test_default_executor_dispatch_tasks_overlay_current_action_identity_on_stale_same_action_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.default_executor_dispatch_tasks"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.toml"
    profile_ref.write_text("[profile]\n", encoding="utf-8")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_quality_repair_batch"
        / "stage-packet.json"
    )
    stale_dispatch = {
        "surface": "default_executor_dispatch_request",
        "dispatch_status": "ready",
        "action_type": "run_quality_repair_batch",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "dispatch_authority": "consumer_default_executor_dispatch",
        "refs": {
            "dispatch_path": str(dispatch_path),
            "stage_packet_path": str(stage_packet_path),
        },
        "study_id": study_id,
        "quest_id": study_id,
        "owner_route": {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": study_id,
            "current_owner": "mas_controller",
            "next_owner": "write",
            "owner_reason": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "source_refs": {
                "work_unit_id": "run_quality_repair_batch",
                "work_unit_fingerprint": "stage-native-next-action::old-fp",
                "owner_route_currentness_basis": {
                    "work_unit_id": "run_quality_repair_batch",
                    "work_unit_fingerprint": "stage-native-next-action::old-fp",
                    "truth_epoch": "stage-native-next-action::old",
                    "runtime_health_epoch": "stage-native-next-action::old",
                },
            },
            "truth_epoch": "stage-native-next-action::old",
            "runtime_health_epoch": "stage-native-next-action::old",
            "work_unit_fingerprint": "stage-native-next-action::old-fp",
            "source_fingerprint": "stage-native-next-action::old-fp",
        },
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": {
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "run_quality_repair_batch",
                    "work_unit_fingerprint": "stage-native-next-action::old-fp",
                },
            },
            "allowed_write_surfaces": ["artifacts/controller/repair_execution_evidence/latest.json"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
        },
    }
    _write_json(dispatch_path, stale_dispatch)
    _write_json(stage_packet_path, {**stale_dispatch, "immutable_packet_ref": "existing"})
    before_dispatch = dispatch_path.read_text(encoding="utf-8")
    before_stage_packet = stage_packet_path.read_text(encoding="utf-8")

    current_owner_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
        "owner_route_currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "source_eval_id": "publication-eval::current",
        },
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "source_eval_id": "publication-eval::current",
        },
    }

    tasks = module.default_executor_dispatch_tasks(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        current_owner_action=current_owner_action,
        current_work_unit=current_work_unit,
        current_execution_envelope={"state_kind": "executable_owner_action"},
        persist_identity=False,
    )

    assert len(tasks) == 1
    assert tasks[0]["task_kind"] == "domain_owner/default-executor-dispatch"
    assert tasks[0]["work_unit_id"] == "medical_prose_write_repair"
    assert tasks[0]["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert tasks[0]["payload"]["work_unit_id"] == "medical_prose_write_repair"
    owner_route_basis = tasks[0]["payload"]["owner_route_currentness_basis"]
    assert {
        key: owner_route_basis.get(key)
        for key in (
            "work_unit_id",
            "work_unit_fingerprint",
            "truth_epoch",
            "runtime_health_epoch",
            "source_eval_id",
        )
    } == {
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
        "source_eval_id": "publication-eval::current",
    }
    assert owner_route_basis["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert dispatch_path.read_text(encoding="utf-8") == before_dispatch
    assert stage_packet_path.read_text(encoding="utf-8") == before_stage_packet


def test_default_executor_dispatch_tasks_require_existing_dispatch_packet_for_current_action_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.default_executor_dispatch_tasks"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.toml"
    profile_ref.write_text("[profile]\n", encoding="utf-8")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_root = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    current_owner_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
        "source_eval_id": (
            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
            "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
        ),
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
            ),
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006815-adef9d6c0803e64e",
        },
        "target_surface": {
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
            ),
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006815-adef9d6c0803e64e",
        },
    }

    tasks = module.default_executor_dispatch_tasks(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        current_owner_action=current_owner_action,
        current_work_unit=current_work_unit,
        current_execution_envelope={
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "medical_prose_write_repair",
        },
        persist_identity=False,
    )

    assert not dispatch_root.exists()
    assert tasks == []


def test_default_executor_dispatch_tasks_suppress_residual_action_when_current_work_unit_is_typed_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.default_executor_dispatch_tasks"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.toml"
    profile_ref.write_text("[profile]\n", encoding="utf-8")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    stage_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_gate_clearing_batch"
        / "stage-packet.json"
    )
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "dispatch_status": "ready",
        "action_type": "run_gate_clearing_batch",
        "next_executable_owner": "gate_clearing_batch",
        "executor_kind": "codex_cli_default",
        "dispatch_authority": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "refs": {
            "dispatch_path": str(dispatch_path),
            "stage_packet_path": str(stage_packet_path),
        },
        "study_id": study_id,
        "quest_id": study_id,
        "owner_route": {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": study_id,
            "next_owner": "gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "source_refs": {
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-current",
                "owner_route_currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-current",
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
            },
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
            "work_unit_fingerprint": "sha256:gate-replay-current",
            "source_fingerprint": "sha256:gate-replay-current",
        },
    }
    _write_json(dispatch_path, dispatch)
    _write_json(stage_packet_path, {**dispatch, "immutable_packet_ref": "existing"})

    tasks = module.default_executor_dispatch_tasks(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay-current",
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay-current",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                },
            },
        },
        current_execution_envelope={"state_kind": "typed_blocker"},
        persist_identity=False,
    )

    assert tasks == []


def test_scan_domain_routes_rejects_unknown_study_id_before_reading_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm001")
    write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution", quest_id="quest-dm002")

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("unknown study ids must be rejected before runtime status is read")

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", fail_if_called)
    monkeypatch.setattr(module.study_progress, "read_study_progress", fail_if_called)

    with pytest.raises(ValueError, match="Unknown supervisor study_id: DM002"):
        module.scan_domain_routes(
            profile=profile,
            study_ids=("DM002",),
            apply_safe_actions=True,
            persist_surfaces=False,
        )
