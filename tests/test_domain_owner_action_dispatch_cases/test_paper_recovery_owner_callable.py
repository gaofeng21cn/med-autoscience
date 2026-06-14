from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_accepts_paper_recovery_owner_callable_route_without_scan_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    fingerprint = "current-readiness-typed-blocker::002-dm::current"
    route = _owner_route(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
    )
    route.update(
        {
            "truth_epoch": fingerprint,
            "route_epoch": fingerprint,
            "runtime_health_epoch": fingerprint,
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
            "owner_reason": "medical_paper_readiness_missing",
            "failure_signature": "medical_paper_readiness_missing",
            "source_refs": {
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": fingerprint,
                "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
                "source_surface": "paper_recovery_state",
                "owner_route_currentness_basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
        required_output_surface="artifacts/medical_paper/readiness.json",
        owner_route=route,
    )
    dispatch_payload["authority"] = "paper_recovery_state"
    dispatch_payload["source_action"] = {
        "authority": "paper_recovery_state",
        "source_surface": "paper_recovery_state",
        "action_type": "complete_medical_paper_readiness_surface",
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "work_unit_fingerprint": fingerprint,
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.action_execution,
        "execute_complete_medical_paper_readiness_surface",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "medical_paper_readiness.complete_medical_paper_readiness_surface",
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("complete_medical_paper_readiness_surface",),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "paper_recovery_owner_callable"
    assert execution["current_owner_route"]["idempotency_key"] == route["idempotency_key"]


def test_execute_dispatch_invokes_persisted_paper_recovery_owner_callable_without_opl_attempt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    quest_root.mkdir(parents=True, exist_ok=True)
    fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    supervisor_decision = {
        "surface_kind": "paper_autonomy_supervisor_decision",
        "schema_version": 1,
        "decision": "materialize_recovery_action",
        "decision_id": (
            "supervisor-decision::materialize_recovery_action::paper-autonomy::"
            f"{study_id}::publication_supervision::run_quality_repair_batch::{work_unit_id}::{fingerprint}"
        ),
        "next_safe_action": {
            "kind": "materialize_recovery_work_unit_or_receipt",
            "source_next_safe_action": {
                "kind": "run_mas_owner_callable",
                "provider_admission_allowed": False,
                "owner": "write",
                "owner_callable": {
                    "owner": "quality_repair_batch",
                    "action_type": "run_quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                },
            },
        },
        "paper_autonomy_obligation": {
            "surface_kind": "paper_autonomy_obligation",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route.update(
        {
            "quest_id": study_id,
            "truth_epoch": fingerprint,
            "route_epoch": fingerprint,
            "runtime_health_epoch": fingerprint,
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
            "current_owner": "MedAutoScience",
            "owner_reason": work_unit_id,
            "failure_signature": work_unit_id,
            "idempotency_key": f"paper-recovery::{study_id}::run_quality_repair_batch::{fingerprint}",
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
                "source_surface": "paper_recovery_state",
                "supervisor_authority": "paper_autonomy_supervisor_decision",
                "supervisor_decision_ref": supervisor_decision["decision_id"],
                "owner_route_currentness_basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload.pop("opl_execution_authorization", None)
    dispatch_payload["prompt_contract"].pop("opl_execution_authorization", None)
    dispatch_payload["source_action"] = {
        "authority": "paper_recovery_state",
        "source_surface": "paper_recovery_state",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "supervisor_decision": supervisor_decision,
        "supervisor_decision_ref": supervisor_decision["decision_id"],
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "write",
            "next_executable_owner": "write",
            "owner_pickup": {"state": "pending"},
            "owner_route": route,
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [
                {**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}
            ],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_route_basis"] == "paper_recovery_owner_callable"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["study_id"] == study_id
    assert called["quest_id"] == study_id
    assert called["authority_route_context"]["work_unit_id"] == work_unit_id


def test_execute_dispatch_selects_same_tick_paper_recovery_successor_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True, exist_ok=True)
    action_type = "run_gate_clearing_batch"
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    supervisor_decision_ref = "supervisor-decision::materialize_recovery_action::dm003"
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    route.update(
        {
            "quest_id": quest_id,
            "truth_epoch": fingerprint,
            "route_epoch": fingerprint,
            "runtime_health_epoch": fingerprint,
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
            "current_owner": "MedAutoScience",
            "owner_reason": "current_owner_route_missing",
            "failure_signature": "current_owner_route_missing",
            "idempotency_key": f"paper-recovery::{study_id}::{action_type}::{fingerprint}",
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
                "source_surface": "paper_recovery_state",
                "successor_source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "successor_source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "supervisor_authority": "paper_autonomy_supervisor_decision",
                "supervisor_decision_ref": supervisor_decision_ref,
                "owner_route_currentness_basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload.update(
        {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
            "source_action": {
                "authority": "paper_recovery_state",
                "source_surface": "paper_recovery_state",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": supervisor_decision_ref,
                },
                "supervisor_decision_ref": supervisor_decision_ref,
            },
        }
    )
    _write_json(dispatch_path, dispatch_payload)
    stale_action_type = "complete_medical_paper_readiness_surface"
    stale_route = _owner_route(
        study_id=study_id,
        action_type=stale_action_type,
        owner="MedAutoScience",
    )
    stale_fingerprint = "current-readiness-typed-blocker::003-dm::stale"
    stale_route.update(
        {
            "quest_id": quest_id,
            "truth_epoch": stale_fingerprint,
            "route_epoch": stale_fingerprint,
            "runtime_health_epoch": stale_fingerprint,
            "work_unit_fingerprint": stale_fingerprint,
            "source_fingerprint": stale_fingerprint,
            "source_refs": {
                "work_unit_id": stale_action_type,
                "work_unit_fingerprint": stale_fingerprint,
                "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
                "source_surface": "paper_recovery_state",
            },
        }
    )
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{stale_action_type}.json"
    )
    stale_dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=stale_action_type,
        owner="MedAutoScience",
        required_output_surface="artifacts/medical_paper/readiness.json",
        owner_route=stale_route,
    )
    stale_dispatch_payload.update(
        {
            "work_unit_id": stale_action_type,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "refs": {"dispatch_path": str(stale_dispatch_path)},
            "source_action": {
                "authority": "paper_recovery_state",
                "source_surface": "paper_recovery_state",
                "action_type": stale_action_type,
                "work_unit_id": stale_action_type,
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
            },
        }
    )
    _write_json(stale_dispatch_path, stale_dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "one-person-lab",
                        "action_type": action_type,
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "stage-native-next-action::run_quality_repair_batch",
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "current_stage_id": "08-publication_package_handoff",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "next_work_unit": "medical_publication_surface_blocked_write_repair",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "current_work_unit_binding": {
                "source": "canonical_current_work_unit",
                "work_unit_id": "run_quality_repair_batch",
                "work_unit_fingerprint": (
                    "stage-native-next-action::08-publication_package_handoff::"
                    "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
                ),
            },
            "stage_transition_authority_boundary": {
                "stage_transition_authority": "one-person-lab",
                "intent_can_write_stage_current_pointer": False,
                "intent_can_write_stage_run_terminal_state": False,
                "intent_can_publish_current_owner_delta": False,
            },
        },
    )
    consumer_payload = {
        "surface": "domain_action_request_materializer",
        "schema_version": 1,
        "default_executor_dispatch_count": 1,
        "default_executor_dispatches": [stale_dispatch_payload, dispatch_payload],
    }

    def fake_read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "current_owner_route_missing",
                    "owner": "one-person-lab",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "owner": "one-person-lab",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": supervisor_decision_ref,
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "gate_clearing_batch",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": action_type,
                        "owner": "gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                    },
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)
    called: list[str] = []

    def fake_execute_owner_dispatch_action(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_id"]))
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        }

    monkeypatch.setattr(
        module,
        "_execute_owner_dispatch_action",
        fake_execute_owner_dispatch_action,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
        consumer_payload=consumer_payload,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 1
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] is None
    execution = result["executions"][0]
    assert execution["action_type"] == action_type
    assert {item["action_type"] for item in result["executions"]} == {action_type}
    assert execution["prompt_contract"]["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert execution["owner_route_basis"] == "paper_recovery_owner_callable"
    assert called == [study_id]
