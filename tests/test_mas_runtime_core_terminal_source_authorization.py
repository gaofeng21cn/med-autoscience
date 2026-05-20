from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess


def _write_workspace_python(quest_root: Path) -> None:
    python_path = quest_root.parents[2] / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True, exist_ok=True)
    python_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_path.chmod(0o755)


def test_codex_exec_runner_prefers_current_route_after_terminal_source_provenance_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    workspace_root = tmp_path / "workspace"
    quest_id = "002-dm"
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    runtime_root = workspace_root / "runtime"
    study_root = workspace_root / "studies" / quest_id
    _write_workspace_python(quest_root)
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {quest_id}\n", encoding="utf-8")
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "running",
                "quest_id": quest_id,
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
                "last_controller_decision_authorization": {
                    "decision_id": "unit-harmonized-uncertainty-routeback",
                    "controller_actions": ["ensure_study_runtime"],
                    "route_target": "analysis-campaign",
                    "work_unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
                    ),
                    "next_work_unit": {
                        "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                        "lane": "analysis-campaign",
                        "summary": "Add uncertainty intervals to the unit-harmonized validation.",
                    },
                },
                "last_explicit_user_wakeup": {
                    "source": "user_explicit_wakeup",
                    "recorded_at": "2026-05-20T20:30:31+00:00",
                    "cleared_keys": ["blocked_turn_closeout", "retry_state"],
                    "cleared_wait_owner": "source_provenance_owner",
                    "previous_continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                    "owner_handoff_authorization": {
                        "authorization_basis": "blocked_turn_closeout_owner_handoff",
                        "blocked_reason": "transport_model_provenance_recovery_required",
                        "controller_actions": ["recover_transport_model_provenance"],
                        "next_owner": "source_provenance_owner",
                        "work_unit_id": "recover_transport_model_provenance",
                        "work_unit_fingerprint": (
                            "source-provenance::recover_transport_model_provenance::"
                            "transport_model_provenance_recovery_required"
                        ),
                        "next_work_unit": {
                            "unit_id": "recover_transport_model_provenance",
                            "lane": "analysis-campaign",
                            "owner": "source_provenance_owner",
                        },
                        "owner_callable_surface": (
                            "source_provenance_owner.recover_transport_model_provenance_or_typed_blocker"
                        ),
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_terminal_source_provenance_result(study_root=study_root, quest_id=quest_id)
    _write_unit_harmonized_uncertainty_decision(study_root=study_root, quest_id=quest_id)

    class StartedProcess:
        pid = 12345

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: StartedProcess())

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id="run-unit-harmonized-uncertainty",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert "unit_harmonized_validation_uncertainty_and_grouped_calibration" in prompt
    assert "--action-types recover_transport_model_provenance" not in prompt
    assert authorization["authorization_basis"] == "current_controller_decision"
    assert authorization["active_run_id"] == "run-unit-harmonized-uncertainty"
    assert authorization["work_unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    assert authorization["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::"
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )


def test_codex_exec_runner_prefers_current_route_after_methodology_reframe_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    workspace_root = tmp_path / "workspace"
    quest_id = "002-dm"
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    runtime_root = workspace_root / "runtime"
    study_root = workspace_root / "studies" / quest_id
    _write_workspace_python(quest_root)
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {quest_id}\n", encoding="utf-8")
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "running",
                "quest_id": quest_id,
                "active_run_id": "old-methodology-reframe-run",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
                "last_controller_decision_authorization": {
                    "decision_id": "unit-harmonized-uncertainty-routeback",
                    "controller_actions": ["ensure_study_runtime"],
                    "route_target": "analysis-campaign",
                    "work_unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
                    ),
                    "next_work_unit": {
                        "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                        "lane": "analysis-campaign",
                        "summary": "Add uncertainty intervals to the unit-harmonized validation.",
                    },
                },
                "last_explicit_user_wakeup": {
                    "source": "user_explicit_wakeup",
                    "recorded_at": "2026-05-20T21:57:21+00:00",
                    "owner_handoff_authorization": {
                        "authorization_basis": "blocked_turn_closeout_owner_handoff",
                        "blocked_reason": "transport_model_provenance_recovery_required",
                        "controller_actions": ["methodology_reframe_route_decision"],
                        "next_owner": "decision",
                        "work_unit_id": "methodology_reframe_route_decision",
                        "work_unit_fingerprint": (
                            "decision::methodology_reframe_route_decision::"
                            "transport_model_provenance_recovery_required"
                        ),
                        "next_work_unit": {
                            "unit_id": "methodology_reframe_route_decision",
                            "lane": "analysis-campaign",
                            "owner": "decision",
                        },
                        "owner_callable_surface": "decision_owner.methodology_reframe_route_decision",
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_unit_harmonized_uncertainty_decision(study_root=study_root, quest_id=quest_id)

    class StartedProcess:
        pid = 12345

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: StartedProcess())

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id="run-unit-harmonized-uncertainty",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert "unit_harmonized_validation_uncertainty_and_grouped_calibration" in prompt
    assert "--action-types methodology_reframe_route_decision" not in prompt
    assert authorization["authorization_basis"] == "current_controller_decision"
    assert authorization["active_run_id"] == "run-unit-harmonized-uncertainty"
    assert authorization["work_unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    assert authorization["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::"
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )


def _write_terminal_source_provenance_result(*, study_root: Path, quest_id: str) -> None:
    source_result_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    source_result_path.parent.mkdir(parents=True, exist_ok=True)
    source_result_path.write_text(
        json.dumps(
            {
                "surface": "source_provenance_owner_result",
                "study_id": quest_id,
                "owner": "source_provenance_owner",
                "work_unit": "recover_transport_model_provenance",
                "status": "blocked",
                "blocked_reason": "transport_model_provenance_recovery_required",
                "typed_blocker_owner": "source_provenance_owner",
                "typed_blocker": {
                    "blocker_id": "transport_model_provenance_recovery_required",
                },
                "transport_model_provenance_recovered": False,
                "terminal_source_provenance_blocker": True,
                "next_owner": "decision",
                "next_work_unit": "methodology_reframe_route_decision",
                "provenance_search": {
                    "searched": True,
                    "accepted_bundle_ref": None,
                    "result_summary_acceptance_allowed": False,
                    "substitute_refit_allowed": False,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_unit_harmonized_uncertainty_decision(*, study_root: Path, quest_id: str) -> None:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::002-dm::latest",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "unit-harmonized-uncertainty-routeback",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-20T18:49:43+00:00",
                "decision_type": "route_back_same_line",
                "charter_ref": {
                    "charter_id": "charter::002-dm::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::002-dm::unit-harmonized-uncertainty",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::002-dm::latest",
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "ensure_study_runtime",
                        "payload_ref": str(decision_path),
                    }
                ],
                "reason": "Add uncertainty and grouped calibration to the unit-harmonized validation.",
                "route_target": "analysis-campaign",
                "route_key_question": (
                    "unit_harmonized_validation_uncertainty_and_grouped_calibration: "
                    "Add uncertainty intervals, grouped calibration evidence, and reproducibility details "
                    "to the unit-harmonized external validation."
                ),
                "route_rationale": "The AI reviewer requires publication-strength validation evidence.",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "unit_harmonized_validation_uncertainty_and_grouped_calibration"
                ),
                "next_work_unit": {
                    "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "lane": "analysis-campaign",
                    "summary": (
                        "Add uncertainty intervals, grouped calibration evidence, and reproducibility details "
                        "to the unit-harmonized external validation."
                    ),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
