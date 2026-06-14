from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import *  # noqa: F403,F401


def test_domain_handler_export_suppresses_ordinary_tasks_when_fresh_current_work_unit_is_typed_blocker(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})
    _write_json(
        study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json",
        {
            "surface_kind": "mas_runtime_owner_route_handoff_record",
            "source": "runtime_controller_redrive_required",
            "recorded_at": "2026-06-09T12:00:00Z",
            "handoff": {
                "surface_kind": "mas_runtime_owner_route_handoff",
                "recommended_task_kind": "domain_route/reconcile-apply",
                "reason": "runtime_controller_redrive_required",
                "recorded_at": "2026-06-09T12:00:00Z",
                "runtime_state_path": "runtime/quests/002/.ds/runtime_state.json",
                "owner_route_currentness_basis": {
                    "truth_epoch": "stale-truth",
                    "runtime_health_epoch": "stale-runtime",
                    "work_unit_id": "stale_redrive",
                    "work_unit_fingerprint": "stale-redrive-fingerprint",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "decision-route-back-stale",
            "emitted_at": "2026-06-09T12:05:00Z",
            "decision_type": "route_back_same_line",
            "requires_human_confirmation": False,
            "route_target": "write",
            "route_key_question": "stale route-back should not beat current typed blocker",
            "route_rationale": "historical route-back residue",
            "work_unit_fingerprint": "stale-route-back-fingerprint",
            "next_work_unit": {
                "unit_id": "stale_writer_repair",
                "lane": "write",
                "summary": "Historical writer repair residue.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "study_id": study_id,
            "state": "breach",
            "progress_pressure": {
                "status": "advance_now",
                "continuation_required": True,
                "next_action_type": "domain_route/reconcile-apply",
                "next_work_unit_id": "stale_progress_pressure",
                "stop_allowed": False,
            },
        },
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "next_work_unit": None,
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                },
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    stale_task_kinds = {
        task["task_kind"]
        for task in payload["pending_family_tasks"]
        if task.get("study_id") == study_id or task.get("payload", {}).get("study_id") == study_id
    }
    assert not (
        stale_task_kinds
        & {
            "paper_autonomy/repair-recheck",
            "publication_aftercare/analysis-queue-progress",
            "publication_aftercare/reviewer-refresh",
            "domain_route/reconcile-apply",
            "domain_owner/default-executor-dispatch",
        }
    )


def test_domain_handler_export_materializes_opl_typed_blocker_owner_resolution_task(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-current",
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "terminal_closeout_typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "opl_execution_authorization_required",
                        "owner": "one-person-lab",
                        "required_input": (
                            "OPL provider attempt, lease, or closeout receipt binding"
                        ),
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "next_work_unit": None,
                "typed_blocker": {
                    "blocker_id": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                    "required_input": "OPL provider attempt, lease, or closeout receipt binding",
                },
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task.get("payload", {}).get("study_id") == study_id
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["task_kind"] == "domain_route/reconcile-apply"
    assert task["reason"] == "current_work_unit_typed_blocker_owner_resolution"
    assert task["queue_owner"] == "one-person-lab"
    assert task["payload"]["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert task["payload"]["current_work_unit"]["work_unit_fingerprint"] == "sha256:gate-replay-current"
    assert task["payload"]["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert task["payload"]["authority_boundary"] == "mas_domain_route_refs_only_opl_stage_attempt_owner"
    assert task["domain_dispatch_evidence_record_payload"]["task_kind"] == "domain_route/reconcile-apply"


def test_domain_handler_export_materializes_mas_dispatch_selection_blocker_resolution_task(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    work_unit_fingerprint = "sha256:gate-replay-current"
    write_profile(profile_path, workspace_root=workspace_root)
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "MedAutoScience",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": work_unit_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "terminal_closeout_typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "no_selected_dispatch_for_requested_action_types",
                        "blocker_type": "no_selected_dispatch_for_requested_action_types",
                        "owner": "MedAutoScience",
                        "required_input": (
                            "current selected MAS dispatch for action_type run_gate_clearing_batch "
                            "or an accepted owner receipt for the already materialized "
                            "gate_clearing_batch artifact"
                        ),
                        "source_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_556faaef7e4a16f309819eb3.closeout.json"
                        ),
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "next_work_unit": None,
                "typed_blocker": {
                    "blocker_id": "no_selected_dispatch_for_requested_action_types",
                    "blocker_type": "no_selected_dispatch_for_requested_action_types",
                    "owner": "MedAutoScience",
                },
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task.get("payload", {}).get("study_id") == study_id
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["task_kind"] == "domain_route/reconcile-apply"
    assert task["reason"] == "current_work_unit_typed_blocker_owner_resolution"
    assert task["queue_owner"] == "one-person-lab"
    assert task["payload"]["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert task["payload"]["current_work_unit"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert task["payload"]["typed_blocker"]["blocker_id"] == "no_selected_dispatch_for_requested_action_types"
    required_owner_action = task["payload"]["required_owner_action"]
    assert required_owner_action["owner"] == "MedAutoScience"
    assert required_owner_action["action_type"] == "run_gate_clearing_batch"
    assert required_owner_action["work_unit_id"] == "publication_gate_replay"
    assert required_owner_action["work_unit_fingerprint"] == work_unit_fingerprint
    assert "current_selected_mas_dispatch" in required_owner_action["accepted_resolution_shapes"]
    assert task["domain_dispatch_evidence_record_payload"]["task_kind"] == "domain_route/reconcile-apply"


def test_domain_handler_export_materializes_supervisor_stable_blocker_owner_resolution_task(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    work_unit_id = "publication_gate_replay"
    work_unit_fingerprint = "sha256:current-publication-gate-replay"
    decision_id = (
        "supervisor-decision::stop_with_stable_typed_blocker::"
        f"{study_id}::{work_unit_id}"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def _read_study_progress(**_: object) -> dict[str, object]:
        currentness_basis = {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "idempotency_key": "idem-current-publication-gate-replay",
            "stage_attempt_id": "sat_current_publication_gate_replay",
        }
        supervisor_decision = {
            "surface_kind": "paper_autonomy_supervisor_decision",
            "schema_version": 1,
            "decision_id": decision_id,
            "decision": "stop_with_stable_typed_blocker",
            "identity_match": True,
            "paper_autonomy_obligation": {
                "surface_kind": "paper_autonomy_obligation",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "publication_supervision",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "route_identity_key": (
                    f"{study_id}:run_gate_clearing_batch:{work_unit_id}:"
                    f"{work_unit_fingerprint}"
                ),
                "attempt_idempotency_key": "idem-current-publication-gate-replay",
                "desired_delta": {
                    "owner": "publication_gate",
                    "required_output_ref_family": [
                        "domain_owner_receipt_ref",
                        "quality_gate_receipt_ref",
                        "typed_blocker_ref",
                        "human_gate_ref",
                        "route_back_evidence_ref",
                    ],
                },
            },
            "paper_autonomy_obligation_ref": (
                f"paper-autonomy::{study_id}::publication_supervision::"
                f"run_gate_clearing_batch::{work_unit_id}::{work_unit_fingerprint}"
            ),
            "evidence_refs": [
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_current_publication_gate_replay.closeout.json"
            ],
            "next_owner": "publication_gate",
            "next_safe_action": {
                "kind": "publish_stable_blocker_and_stop_same_identity_redrive"
            },
        }
        typed_blocker = {
            "blocker_id": "publication_gate_replay_blocked",
            "blocker_type": "publication_gate_replay_blocked",
            "owner": "publication_gate",
            "source_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_current_publication_gate_replay.closeout.json"
            ),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        }
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "currentness_basis": currentness_basis,
                "required_output_contract": {
                    "owner_receipt_required": True,
                    "typed_blocker_accepted": True,
                    "accepted_return_shape": [
                        "domain_owner_receipt_ref",
                        "quality_gate_receipt_ref",
                        "typed_blocker_ref",
                        "human_gate_ref",
                        "route_back_evidence_ref",
                    ],
                    "provider_completion_is_domain_completion": False,
                    "domain_ready_authorized": False,
                },
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": typed_blocker,
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "publication_gate",
                "next_work_unit": None,
                "typed_blocker": typed_blocker,
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "domain_blocked",
                "next_safe_action": {
                    "kind": "resolve_typed_blocker",
                    "owner": "publication_gate",
                    "provider_admission_allowed": False,
                },
                "supervisor_decision": supervisor_decision,
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task.get("payload", {}).get("study_id") == study_id
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["task_kind"] == "domain_route/reconcile-apply"
    assert task["reason"] == "current_work_unit_typed_blocker_owner_resolution"
    assert task["payload"]["paper_autonomy_supervisor_decision"]["decision"] == (
        "stop_with_stable_typed_blocker"
    )
    assert task["payload"]["paper_autonomy_supervisor_decision"]["decision_id"] == decision_id
    required_owner_action = task["payload"]["required_owner_action"]
    assert required_owner_action["owner"] == "publication_gate"
    assert required_owner_action["work_unit_id"] == work_unit_id
    assert required_owner_action["work_unit_fingerprint"] == work_unit_fingerprint
    assert required_owner_action["accepted_resolution_shapes"][:5] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert any(
        ref["role"] == "paper_autonomy_supervisor_decision" and ref["decision"] == (
            "stop_with_stable_typed_blocker"
        )
        for ref in task["source_refs"]
    )
    assert task["domain_dispatch_evidence_record_payload"]["task_kind"] == "domain_route/reconcile-apply"


def test_domain_handler_export_materializes_owner_gate_route_back_dispatch_under_stage_packet_blocker(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    work_unit_fingerprint = "publication-blockers::497d1260db522f01"
    route_back_ref = "route_back:owner-gate-decision:c7027de42ca336cfe0782428"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="consumer_default_executor_dispatch",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason=work_unit_id,
            action_type="run_quality_repair_batch",
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            runtime_health_epoch=work_unit_fingerprint,
            blocked_actions=["run_gate_clearing_batch"],
        ),
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": work_unit_fingerprint,
                    "runtime_health_epoch": work_unit_fingerprint,
                },
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "stage_packet_not_current_selected_dispatch",
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": work_unit_fingerprint,
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                    "owner": "one-person-lab",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "supervisor_decision": {
                    "surface_kind": "paper_autonomy_supervisor_decision",
                    "decision": "execute_current_owner_delta",
                    "identity_match": True,
                    "paper_autonomy_obligation": {
                        "surface_kind": "paper_autonomy_obligation",
                        "study_id": study_id,
                        "quest_id": study_id,
                        "stage_id": "publication_supervision",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "route_identity_key": f"provider-admission::{study_id}::{work_unit_fingerprint}",
                        "attempt_idempotency_key": f"provider-admission::{study_id}::{work_unit_fingerprint}",
                    },
                    "evidence_refs": [
                        f"provider-admission::{study_id}::{work_unit_fingerprint}",
                        f"stage-run-identity::{study_id}::{work_unit_fingerprint}",
                        route_back_ref,
                    ],
                    "missing_evidence_refs": [],
                },
                "next_safe_action": {
                    "kind": "route_back_to_owner_or_repair_materialization",
                    "owner": "MedAutoScience",
                    "provider_admission_allowed": False,
                    "accepted_owner_gate_decision": {
                        "decision": "route_back_to_mas_packet_materialization_bug",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "route_back_evidence_ref": route_back_ref,
                    },
                },
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
        and task.get("study_id") == study_id
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["action_type"] == "run_quality_repair_batch"
    assert task["work_unit_id"] == work_unit_id
    assert task["work_unit_fingerprint"] == work_unit_fingerprint
    assert task["payload"]["work_unit_id"] == work_unit_id
    assert task["payload"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert task["payload"]["owner_route_currentness_basis"]["work_unit_fingerprint"] == (
        work_unit_fingerprint
    )


def test_export_current_owner_action_suppresses_residual_action_under_typed_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export")

    action = module._export_current_owner_action(
        study={
            "current_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
        },
        current_progress={
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
            "current_execution_envelope": {"state_kind": "typed_blocker"},
        },
    )

    assert action == {}


def test_export_current_owner_action_merges_projection_route_currentness_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export")
    currentness_basis = {
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": "sha256:current-route",
        "truth_epoch": "truth::current",
        "runtime_health_epoch": "runtime::current",
    }
    route = {
        "surface": "domain_route_owner_route",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "next_owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
    }

    action = module._export_current_owner_action(
        study={
            "current_owner_action": {
                "source": "opl_current_control_state_action_queue",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "owner_route": route,
                "owner_route_currentness_basis": currentness_basis,
                "source_fingerprint": "sha256:current-route",
                "work_unit_fingerprint": "sha256:current-route",
            },
        },
        current_progress={
            "current_executable_owner_action": {
                "source": "current_work_unit",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "current_work_unit": {"status": "executable_owner_action"},
            "current_execution_envelope": {"state_kind": "executable_owner_action"},
        },
    )

    assert action["source"] == "current_work_unit"
    assert action["owner_route"] == {
        **route,
        "source_refs": {"owner_route_currentness_basis": currentness_basis},
    }
    assert action["owner_route_currentness_basis"] == currentness_basis
    assert action["source_fingerprint"] == "sha256:current-route"
    assert action["work_unit_fingerprint"] == "sha256:current-route"


def test_domain_handler_export_suppresses_legacy_route_tasks_under_current_owner_action(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})
    _write_json(
        study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json",
        {
            "surface_kind": "mas_runtime_owner_route_handoff_record",
            "source": "runtime_controller_redrive_required",
            "recorded_at": "2026-06-09T12:00:00Z",
            "handoff": {
                "surface_kind": "mas_runtime_owner_route_handoff",
                "recommended_task_kind": "domain_route/reconcile-apply",
                "reason": "runtime_controller_redrive_required",
                "recorded_at": "2026-06-09T12:00:00Z",
                "owner_route_currentness_basis": {
                    "truth_epoch": "stale-truth",
                    "runtime_health_epoch": "stale-runtime",
                    "work_unit_id": "stale_redrive",
                    "work_unit_fingerprint": "stale-redrive-fingerprint",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "decision-route-back-stale",
            "emitted_at": "2026-06-09T12:05:00Z",
            "decision_type": "route_back_same_line",
            "requires_human_confirmation": False,
            "route_target": "write",
            "work_unit_fingerprint": "stale-route-back-fingerprint",
            "next_work_unit": {
                "unit_id": "stale_writer_repair",
                "lane": "write",
                "summary": "Historical writer repair residue.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "study_id": study_id,
            "state": "breach",
            "progress_pressure": {
                "status": "advance_now",
                "continuation_required": True,
                "next_action_type": "domain_route/reconcile-apply",
                "next_work_unit_id": "stale_progress_pressure",
                "stop_allowed": False,
            },
        },
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "work_unit_fingerprint": "current-write-repair-fingerprint",
                "action_fingerprint": "current-write-repair-fingerprint",
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "opl_current_control_state_action_queue",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "manuscript_story_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "work_unit_fingerprint": "current-write-repair-fingerprint",
                "allowed_actions": ["run_quality_repair_batch"],
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study_tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task.get("study_id") == study_id or task.get("payload", {}).get("study_id") == study_id
    ]
    assert [
        task
        for task in study_tasks
        if task["task_kind"] == "domain_route/reconcile-apply"
        or task["task_kind"].startswith("publication_aftercare/")
        or task["task_kind"] == "paper_autonomy/repair-recheck"
    ] == []
