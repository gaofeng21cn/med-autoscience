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


def test_codex_exec_runner_syncs_current_controller_decision_for_quality_repair_turn(
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
        """
{
  "quest_id": "002-dm",
  "active_run_id": "old-run",
  "current_controller_authorization": {
    "decision_id": "old-ai-reviewer-decision",
    "active_run_id": "old-run",
    "controller_actions": ["return_to_ai_reviewer_workflow"],
    "route_target": "review",
    "work_unit_id": "ai_reviewer_recheck",
    "work_unit_fingerprint": "domain-transition::stale-ai-reviewer"
  }
}
""",
        encoding="utf-8",
    )
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "quality-repair-decision",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-17T13:16:53+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::002-dm::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::002-dm::quality-repair",
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
                        "action_type": "run_quality_repair_batch",
                        "payload_ref": str(decision_path),
                    }
                ],
                "reason": "Run one controller-owned quality repair batch.",
                "route_target": "write",
                "route_key_question": "刷新 canonical manuscript draft/review manuscript。",
                "route_rationale": "The active paper line needs manuscript story repair.",
                "work_unit_fingerprint": "publication-blockers::current-quality",
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Repair the paper story around the current evidence and claim boundary.",
                },
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
        run_id="run-quality-repair",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert '"decision_id": "quality-repair-decision"' in prompt
    assert '"work_unit_id": "manuscript_story_repair"' in prompt
    assert "domain-transition::stale-ai-reviewer" not in prompt
    assert "-m med_autoscience.cli quality-repair-batch" in prompt
    assert authorization["decision_id"] == "quality-repair-decision"
    assert authorization["active_run_id"] == "run-quality-repair"
    assert authorization["controller_actions"] == ["run_quality_repair_batch"]
    assert authorization["work_unit_id"] == "manuscript_story_repair"
    assert authorization["work_unit_fingerprint"] == "publication-blockers::current-quality"


def test_codex_exec_runner_maps_methodology_analysis_work_unit_to_quality_repair_batch(
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
    runtime_state_path.write_text('{"status": "paused"}\n', encoding="utf-8")
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "methodology-analysis-routeback",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-18T14:38:44+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::002-dm::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::002-dm::methodology-analysis",
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
                "reason": "Route methodology blockers back to analysis/harmonization.",
                "route_target": "analysis-campaign",
                "route_key_question": "unit-harmonized rerun or typed blocker",
                "route_rationale": "HDL/unit harmonization must close before prose review.",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
                ),
                "next_work_unit": {
                    "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                    "lane": "analysis-campaign",
                    "summary": "Close or type-block HDL harmonization and model reproducibility gaps.",
                },
                "blocking_work_units": [
                    {
                        "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                        "lane": "analysis-campaign",
                        "summary": (
                            "Materialize or type-block prediction-model reproducibility, uncertainty, "
                            "calibration, HDL harmonization, and NHANES weighting evidence."
                        ),
                    }
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
        run_id="run-methodology-analysis",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert '"decision_id": "methodology-analysis-routeback"' in prompt
    assert "medical_prose_quality_analysis_source_documentation_repair" in prompt
    assert "-m med_autoscience.cli quality-repair-batch" in prompt
    assert "- Invoke the listed controller command before freeform artifact writing:" in prompt
    assert "No callable MAS CLI command is registered" not in prompt
    assert authorization["decision_id"] == "methodology-analysis-routeback"
    assert authorization["work_unit_id"] == "medical_prose_quality_analysis_source_documentation_repair"
    assert authorization["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
    )


def test_codex_exec_runner_preserves_hard_methodology_route_fields_from_controller_decision(
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
    runtime_state_path.write_text('{"status": "paused"}\n', encoding="utf-8")
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "methodology-hard-routeback",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-19T02:59:11+00:00",
                "decision_type": "route_back_same_line",
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
                "reason": "Route terminal provenance blockers back to methodology reframe.",
                "route_target": "analysis-campaign",
                "route_key_question": "Can DM002 continue without the original transported model provenance?",
                "route_rationale": "HDL/unit harmonization and Cox provenance remain unresolved.",
                "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
                "next_work_unit": {
                    "unit_id": "provenance_limited_harmonization_audit",
                    "lane": "analysis-campaign",
                    "summary": "Materialize a provenance-limited harmonization audit and rebuild or stop-loss route.",
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
        run_id="run-hard-methodology",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert "Hard methodology/provenance-limited reframe contract" in prompt
    assert '"hard_methodology": true' in prompt
    assert '"selected_route_option": "provenance_limited_harmonization_audit"' in prompt
    assert '"terminal_source_provenance_blocker_consumed": true' in prompt
    assert '"current_transport_claim_must_not_be_used_as_medical_conclusion": true' in prompt
    assert "provenance_limited_harmonization_audit" in prompt
    assert "Do not re-run the contaminated transported-score analysis" in prompt
    assert authorization["next_work_unit"]["hard_methodology"] is True
    assert authorization["next_work_unit"]["selected_route_option"] == "provenance_limited_harmonization_audit"


def test_codex_exec_runner_prompt_prefers_current_ai_reviewer_decision_over_stale_runtime_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    workspace_root = tmp_path / "workspace"
    quest_id = "002-dm-china-us-mortality-attribution"
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    runtime_root = workspace_root / "runtime"
    study_root = workspace_root / "studies" / quest_id
    _write_workspace_python(quest_root)
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {quest_id}\n", encoding="utf-8")
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "status": "paused",
  "last_controller_decision_authorization": {
    "decision_id": "stale-analysis-repair",
    "controller_actions": ["run_quality_repair_batch"],
    "route_target": "analysis-campaign",
    "work_unit_id": "analysis_claim_evidence_repair",
    "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
    "next_work_unit": {
      "unit_id": "analysis_claim_evidence_repair",
      "lane": "analysis-campaign",
      "summary": "Repair claim-evidence blockers."
    }
  }
}
""",
        encoding="utf-8",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    controller_decision_path.parent.mkdir(parents=True, exist_ok=True)
    controller_decision_path.write_text(
        """
{
  "schema_version": 1,
  "decision_id": "current-ai-reviewer-redrive",
  "study_id": "002-dm-china-us-mortality-attribution",
  "quest_id": "002-dm-china-us-mortality-attribution",
  "emitted_at": "2026-05-17T14:20:42+00:00",
  "decision_type": "continue_same_line",
  "charter_ref": {
    "charter_id": "charter::002-dm-china-us-mortality-attribution::v1",
    "artifact_path": "/tmp/workspace/studies/002/artifacts/controller/study_charter.json"
  },
  "runtime_escalation_ref": {
    "record_id": "runtime-escalation::002::ai-reviewer-redrive",
    "artifact_path": "/tmp/workspace/studies/002/artifacts/runtime/runtime_escalation_record.json",
    "summary_ref": "/tmp/workspace/studies/002/artifacts/runtime/runtime_escalation_record.json"
  },
  "publication_eval_ref": {
    "eval_id": "publication-eval::002::current",
    "artifact_path": "/tmp/workspace/studies/002/artifacts/publication_eval/latest.json"
  },
  "requires_human_confirmation": false,
  "controller_actions": [
    {
      "action_type": "return_to_ai_reviewer_workflow",
      "payload_ref": "/tmp/workspace/studies/002/artifacts/controller_decisions/latest.json"
    }
  ],
  "reason": "Return the current manuscript and evidence refs to the AI reviewer workflow.",
  "route_target": "review",
  "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
  "route_rationale": "Return the current manuscript and evidence refs to the AI reviewer workflow.",
  "next_work_unit": {
    "unit_id": "ai_reviewer_recheck",
    "lane": "review",
    "summary": "Return the current manuscript and evidence refs to the AI reviewer workflow."
  },
  "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
}
""",
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
        run_id="run-current-ai-reviewer",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert "Active MAS controller work unit" in prompt
    assert '"decision_id": "current-ai-reviewer-redrive"' in prompt
    assert '"work_unit_id": "ai_reviewer_recheck"' in prompt
    assert "return_to_ai_reviewer_workflow" in prompt
    assert "AI reviewer redrive execution contract" in prompt
    assert "materialize-ai-medical-prose-review" in prompt
    assert "-m med_autoscience.cli domain-owner-action-dispatch" in prompt
    assert "--action-types return_to_ai_reviewer_workflow" in prompt
    assert "analysis_claim_evidence_repair" not in prompt
    assert "run_quality_repair_batch" not in prompt
    assert runtime_state["last_controller_decision_authorization"]["work_unit_id"] == "analysis_claim_evidence_repair"
    current_authorization = runtime_state["current_controller_authorization"]
    assert current_authorization["decision_id"] == "current-ai-reviewer-redrive"
    assert current_authorization["authorization_basis"] == "current_controller_decision"
    assert current_authorization["quest_id"] == quest_id
    assert current_authorization["study_id"] == quest_id
    assert current_authorization["active_run_id"] == "run-current-ai-reviewer"
    assert current_authorization["work_unit_id"] == "ai_reviewer_recheck"
    assert (
        current_authorization["work_unit_fingerprint"]
        == "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    )
