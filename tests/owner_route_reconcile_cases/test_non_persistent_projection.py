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


def test_scan_domain_routes_can_project_without_overwriting_workspace_latest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    quest_root = profile.runtime_root / "quest-dpcc"
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "opl_current_control_state_handoff",
            "generated_at": "2026-05-05T00:00:00+00:00",
            "studies": [
                {"study_id": "001-dm-cvd-mortality-risk"},
                {"study_id": study_id},
            ],
            "action_queue": [{"study_id": "001-dm-cvd-mortality-risk", "action_id": "existing"}],
        },
    )
    before = latest_path.read_text(encoding="utf-8")

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dpcc",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    assert result["studies"][0]["study_id"] == study_id
    assert latest_path.read_text(encoding="utf-8") == before
    assert not (profile.workspace_root / "runtime" / "artifacts" / "supervision" / "hourly" / "history.jsonl").exists()


def test_external_observe_scan_reads_progress_without_materializing_controller_decisions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    calls: dict[str, dict[str, object]] = {}

    def status_reader(**kwargs: object) -> dict[str, object]:
        calls["status"] = dict(kwargs)
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_status": "active",
            "publication_eval": {
                "assessment_provenance": {"owner": "ai_reviewer"},
                "recommended_actions": [],
            },
        }

    def progress_reader(**kwargs: object) -> dict[str, object]:
        calls["progress"] = dict(kwargs)
        if kwargs.get("sync_runtime_summary") is not False:
            raise AssertionError("owner-route read-only scans must not sync runtime summary")
        if kwargs.get("materialize_read_model_artifacts") is not False:
            raise AssertionError("owner-route read-only scans must not materialize read-model artifacts")
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None},
        }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", status_reader)
    monkeypatch.setattr(module.study_progress, "read_study_progress", progress_reader)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        developer_supervisor_mode="external_observe",
        persist_surfaces=False,
    )

    assert result["studies"][0]["study_id"] == study_id
    assert calls["status"]["sync_runtime_summary"] is False
    assert calls["status"]["include_progress_projection"] is False
    assert calls["progress"]["sync_runtime_summary"] is False
    assert calls["progress"]["materialize_read_model_artifacts"] is False
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def test_persisted_single_study_scan_preserves_unscanned_study_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    retained_study_id = "002-dm-china-us-mortality-attribution"
    scanned_study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    retained_root = write_study(profile.workspace_root, retained_study_id, quest_id="quest-dm002")
    scanned_root = write_study(profile.workspace_root, scanned_study_id, quest_id="quest-dpcc")
    scanned_quest_root = profile.runtime_root / "quest-dpcc"
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-27T17:00:00+00:00",
            "studies": [
                {
                    "study_id": retained_study_id,
                    "study_root": str(retained_root),
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "blocked_reason": "paper_surface_blocked",
                    "action_queue": [
                        {
                            "action_id": "supervisor-action::dm002::write-repair",
                            "action_type": "return_to_write",
                            "status": "queued",
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": retained_study_id,
                    "action_id": "supervisor-action::dm002::write-repair",
                    "action_type": "return_to_write",
                    "status": "queued",
                }
            ],
            "current_execution_envelopes": {
                retained_study_id: {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "current_manuscript_repair",
                    "typed_blocker": None,
                }
            },
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": scanned_study_id,
            "study_root": str(scanned_root),
            "quest_id": "quest-dpcc",
            "quest_root": str(scanned_quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": scanned_study_id,
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(scanned_study_id,),
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    assert [study["study_id"] for study in result["studies"]] == [retained_study_id, scanned_study_id]
    assert result["studies"][0]["handoff_generated_at"] == "2026-05-27T17:00:00+00:00"
    assert result["studies"][0]["handoff_scan_status"] == "retained_from_previous_scan"
    assert result["studies"][1]["handoff_scan_status"] == "scanned"
    assert retained_study_id in [action["study_id"] for action in result["action_queue"]]
    persisted = json.loads(latest_path.read_text(encoding="utf-8"))
    assert [study["study_id"] for study in persisted["studies"]] == [retained_study_id, scanned_study_id]
    assert persisted["studies"][0]["handoff_generated_at"] == "2026-05-27T17:00:00+00:00"
    assert persisted["studies"][0]["handoff_scan_status"] == "retained_from_previous_scan"
    assert persisted["studies"][1]["handoff_scan_status"] == "scanned"
    assert retained_study_id in [action["study_id"] for action in persisted["action_queue"]]
    assert persisted["current_execution_envelopes"][retained_study_id] == {
        "state_kind": "executable_owner_action",
        "owner": "write",
        "next_work_unit": "current_manuscript_repair",
        "typed_blocker": None,
    }
    assert persisted["current_execution_envelopes"][scanned_study_id] == result["current_execution_envelopes"][
        scanned_study_id
    ]


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
