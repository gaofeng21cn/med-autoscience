from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.owner_route_handoff_command_cases.shared import *  # noqa: F403,F401


def test_domain_handler_export_materializes_supervisor_successor_dispatch_under_typed_blocker(
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
    gate_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    successor_fingerprint = "publication-blockers::0915410f804b3697"
    write_profile(profile_path, workspace_root=workspace_root)
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    _write_json(
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [],
            "action_queue": [],
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
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "publication_gate_replay_blocked",
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "publication_gate",
                "typed_blocker": {
                    "blocker_id": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": successor_fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "publication_gate",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "blocker_type": "publication_gate_replay_blocked",
                    },
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": successor_fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough",
                        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
                "supervisor_decision": {
                    "surface_kind": "paper_autonomy_supervisor_decision",
                    "schema_version": 1,
                    "decision": "materialize_recovery_action",
                    "decision_id": (
                        "supervisor-decision::materialize_recovery_action::"
                        f"{study_id}::publication_supervision::"
                        "run_quality_repair_batch::medical_prose_write_repair::"
                        f"{successor_fingerprint}"
                    ),
                    "identity_match": True,
                    "next_owner": "write",
                    "paper_autonomy_obligation": {
                        "surface_kind": "paper_autonomy_obligation",
                        "study_id": study_id,
                        "quest_id": study_id,
                        "stage_id": "publication_supervision",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                    },
                    "next_safe_action": {
                        "kind": "materialize_recovery_work_unit_or_receipt",
                        "source_next_safe_action": {
                            "kind": "materialize_successor_owner_action",
                            "owner": "write",
                        },
                    },
                },
            },
            "current_executable_owner_action": None,
            "authority_snapshot": {
                "allowed_controller_actions": [
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task.get("study_id") == study_id or task.get("payload", {}).get("study_id") == study_id
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["task_kind"] == "domain_owner/default-executor-dispatch"
    assert task["reason"] == "paper_autonomy_supervisor_materialized_default_executor_dispatch"
    assert task["action_type"] == "run_quality_repair_batch"
    assert task["domain_owner"] == "write"
    assert task["work_unit_id"] == "medical_prose_write_repair"
    assert task["work_unit_fingerprint"] == successor_fingerprint
    assert task["provider_completion_is_domain_completion"] is False
    assert task["authority_boundary"]["authority"] == "med_autoscience.paper_progress_policy_adapter"
    assert task["authority_boundary"]["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert task["authority_boundary"]["target_runtime_owner"] == "one-person-lab"
    assert task["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert task["provider_admission_pending"] is False
    assert task["provider_admission_requires_opl_runtime_result"] is True
    assert (
        task["stage_transition_authority_boundary"]["stage_transition_authority"]
        == "one-person-lab"
    )
    assert (
        task["stage_transition_authority_boundary"][
            "provider_completion_counts_as_stage_transition"
        ]
        is False
    )
    assert task["payload"]["provider_completion_is_domain_completion"] is False
    assert task["payload"]["authority_boundary"] == task["authority_boundary"]
    assert (
        task["payload"]["stage_transition_authority_boundary"]
        == task["stage_transition_authority_boundary"]
    )
    transition_request = task["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    assert transition_request["mas_can_create_opl_stage_run"] is False
    assert transition_request["recommended_transition_kind"] == "MaterializeOwnerAction"
    assert transition_request["required_postcondition"]["kind"] == "owner_action_ref"
    assert "provider_admission_identity" not in task
    assert task["payload"]["opl_domain_progress_transition_request"] == transition_request
    assert task["payload"]["provider_admission_pending"] is False
    assert task["payload"]["provider_admission_requires_opl_runtime_result"] is True
    assert task["payload"]["next_executable_owner"] == "write"
    assert task["payload"]["paper_recovery_authority_boundary"] == (
        "mas_domain_progress_transition_request_only"
    )
    assert task["payload"]["paper_autonomy_supervisor_decision"]["decision"] == (
        "materialize_recovery_action"
    )
    assert task["payload"]["paper_recovery_source_action"]["authority"] == "paper_recovery_state"
    assert "default_executor_dispatch_request" not in task["payload"]
    legacy_ref = task["payload"]["legacy_default_executor_dispatch_request_ref"]
    assert legacy_ref["role"] == "default_executor_dispatch_request"
    assert legacy_ref["projection_kind"] == "legacy_default_executor_dispatch_request_ref"
    assert legacy_ref["body_included"] is False
    assert legacy_ref["source_action_body_included"] is False
    assert legacy_ref["dispatch_body_included"] is False
    assert legacy_ref["authority_boundary"] == "mas_domain_progress_transition_request_only"
    assert legacy_ref["mas_can_authorize_provider_admission"] is False
    assert legacy_ref["mas_can_create_opl_stage_run"] is False
    assert legacy_ref["provider_admission_requires_opl_runtime_result"] is True
    assert legacy_ref["source_transition_request_status"] == "transition_request_pending"
    assert "publication_gate_replay_blocked" not in json.dumps(
        legacy_ref,
        sort_keys=True,
        ensure_ascii=False,
    )
    assert any(
        ref["role"] == "paper_autonomy_supervisor_decision"
        and ref["decision"] == "materialize_recovery_action"
        for ref in task["source_refs"]
    )
    assert task["domain_dispatch_evidence_record_payload"]["task_kind"] == (
        "domain_owner/default-executor-dispatch"
    )
