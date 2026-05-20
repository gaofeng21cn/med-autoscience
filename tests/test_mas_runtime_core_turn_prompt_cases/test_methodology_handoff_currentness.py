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


def test_codex_exec_runner_prefers_provenance_audit_over_completed_methodology_handoff(
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
                "status": "active",
                "quest_id": quest_id,
                "last_explicit_user_wakeup": {
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
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "methodology-route-selected-provenance-audit",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-20T22:17:48+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::002-dm::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::002-dm::methodology-reframe",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::002-dm::latest",
                    "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "ensure_study_runtime",
                        "payload_ref": str(decision_path),
                    }
                ],
                "reason": "The decision owner selected the next methodology route.",
                "route_target": "analysis-campaign",
                "route_key_question": "Can the line continue after terminal provenance loss?",
                "route_rationale": "Continue only through a provenance-limited harmonization audit.",
                "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
                "next_work_unit": {
                    "unit_id": "provenance_limited_harmonization_audit",
                    "lane": "analysis-campaign",
                    "summary": "Materialize provenance-limited audit and rebuild or stop-loss route.",
                    "hard_methodology": True,
                    "selected_route_option": "provenance_limited_harmonization_audit",
                    "terminal_source_provenance_blocker_consumed": True,
                    "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
                    "route_options": [
                        "stop_loss_current_transport_claim",
                        "provenance_limited_harmonization_audit",
                        "rebuild_reproducible_model_route",
                        "human_gate",
                    ],
                },
                "blocking_work_units": [
                    {"unit_id": "recover_transport_model_provenance"},
                    {
                        "unit_id": "methodology_reframe_route_decision",
                        "selected_route_option": "provenance_limited_harmonization_audit",
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    class StartedProcess:
        pid = 12345

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: StartedProcess())

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id="run-provenance-audit",
        reason="auto_continue",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert '"authorization_basis": "current_controller_decision"' in prompt
    assert '"work_unit_id": "provenance_limited_harmonization_audit"' in prompt
    assert "Hard methodology/provenance-limited reframe contract" in prompt
    assert "--action-types provenance_limited_harmonization_audit" in prompt
    assert "decision.methodology_reframe_route_decision" not in prompt
    assert "--action-types methodology_reframe_route_decision" not in prompt
    assert authorization["authorization_basis"] == "current_controller_decision"
    assert authorization["active_run_id"] == "run-provenance-audit"
    assert authorization["work_unit_id"] == "provenance_limited_harmonization_audit"
    assert authorization["controller_actions"] == ["provenance_limited_harmonization_audit"]
