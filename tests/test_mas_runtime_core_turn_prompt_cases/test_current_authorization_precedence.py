from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess

from tests.test_cli_cases.shared import write_profile


def _write_workspace_python(quest_root: Path) -> None:
    python_path = quest_root.parents[2] / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True, exist_ok=True)
    python_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_path.chmod(0o755)


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


def test_codex_exec_runner_prompt_prefers_story_surface_delta_blocker_over_stale_gate_decision(
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
    "decision_id": "old-gate-recheck",
    "controller_actions": ["run_gate_clearing_batch"],
    "route_target": "publication_gate",
    "work_unit_id": "publication_gate_recheck",
    "work_unit_fingerprint": "publication-blockers::old-gate"
  }
}
""",
        encoding="utf-8",
    )
    eval_id = "publication-eval::dm002::story-current"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": eval_id,
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "route_target": "write",
                        "route_key_question": "Rewrite the manuscript around the clean external-validation story.",
                        "route_rationale": "The current manuscript still carries internal correction-history language.",
                        "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
                        "next_work_unit": {
                            "unit_id": "manuscript_story_repair",
                            "lane": "write",
                            "summary": "Repair manuscript story from current evidence without internal QA history.",
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    quality_batch_path.parent.mkdir(parents=True, exist_ok=True)
    quality_batch_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "blocked",
                "source_eval_id": eval_id,
                "next_owner": "write",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "repair_execution_evidence": {
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    controller_decision_path.parent.mkdir(parents=True, exist_ok=True)
    controller_decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "stale-publication-gate-recheck",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-19T12:00:00+00:00",
                "decision_type": "publication_gate_blocker",
                "publication_eval_ref": {
                    "eval_id": eval_id,
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "run_gate_clearing_batch",
                        "payload_ref": str(controller_decision_path),
                    }
                ],
                "reason": "Stale gate recheck should not supersede write-owner story repair.",
                "route_target": "publication_gate",
                "route_key_question": "Recheck publication gate.",
                "route_rationale": "Old lifecycle route.",
                "work_unit_fingerprint": "publication-blockers::old-gate",
                "next_work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "publication_gate",
                    "summary": "Recheck publication gate after upstream repairs.",
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
        run_id="run-story-repair",
        reason="explicit_user_wakeup",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert "Active MAS controller work unit" in prompt
    assert '"work_unit_id": "manuscript_story_repair"' in prompt
    assert '"route_target": "write"' in prompt
    assert '"controller_actions": [\n    "run_quality_repair_batch"\n  ]' in prompt
    assert "Manuscript story repair follow-through contract" in prompt
    assert "publication_gate_recheck" not in prompt
    assert "run_gate_clearing_batch" not in prompt
    assert authorization["authorization_basis"] == "quality_repair_story_surface_delta_blocker"
    assert authorization["work_unit_id"] == "manuscript_story_repair"
    assert authorization["route_target"] == "write"
    assert authorization["controller_actions"] == ["run_quality_repair_batch"]
    assert authorization["active_run_id"] == "run-story-repair"


def test_codex_exec_runner_prompt_prefers_medical_prose_delta_blocker_over_stale_gate_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    workspace_root = tmp_path / "workspace"
    quest_id = "003-dpcc-primary-care-phenotype-treatment-gap"
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
    "decision_id": "old-gate-recheck",
    "controller_actions": ["run_gate_clearing_batch"],
    "route_target": "publication_gate",
    "work_unit_id": "publication_gate_recheck",
    "work_unit_fingerprint": "publication-blockers::old-gate"
  }
}
""",
        encoding="utf-8",
    )
    eval_id = "publication-eval::dm003::medical-prose-current"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": eval_id,
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "route_target": "write",
                        "route_key_question": "Repair medical manuscript prose quality.",
                        "route_rationale": "The current manuscript has not absorbed medical prose quality feedback.",
                        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": "Revise the manuscript to medical journal prose standards.",
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    quality_batch_path.parent.mkdir(parents=True, exist_ok=True)
    quality_batch_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "blocked",
                "source_eval_id": eval_id,
                "next_owner": "write",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    controller_decision_path.parent.mkdir(parents=True, exist_ok=True)
    controller_decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "stale-publication-gate-recheck",
                "study_id": quest_id,
                "quest_id": quest_id,
                "decision_type": "publication_gate_blocker",
                "publication_eval_ref": {"eval_id": eval_id, "artifact_path": str(publication_eval_path)},
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
                "route_target": "publication_gate",
                "work_unit_fingerprint": "publication-blockers::old-gate",
                "next_work_unit": {"unit_id": "publication_gate_recheck", "lane": "publication_gate"},
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
        run_id="run-medical-prose-repair",
        reason="explicit_user_wakeup",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    authorization = runtime_state["current_controller_authorization"]

    assert '"work_unit_id": "medical_prose_write_repair"' in prompt
    assert '"controller_actions": [\n    "run_quality_repair_batch"\n  ]' in prompt
    assert "Manuscript story repair follow-through contract" in prompt
    assert "`medical_prose_write_repair`" in prompt
    assert "publication_gate_recheck" not in prompt
    assert authorization["authorization_basis"] == "quality_repair_story_surface_delta_blocker"
    assert authorization["work_unit_id"] == "medical_prose_write_repair"
    assert authorization["controller_actions"] == ["run_quality_repair_batch"]
    assert authorization["active_run_id"] == "run-medical-prose-repair"


def test_codex_exec_runner_refreshes_domain_transition_decision_before_prompt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    workspace_root = tmp_path / "workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "dm.local.toml"
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    write_profile(profile_path, workspace_root=workspace_root)
    config_env_path.parent.mkdir(parents=True, exist_ok=True)
    config_env_path.write_text(f"MED_AUTOSCIENCE_PROFILE={profile_path}\n", encoding="utf-8")
    quest_id = "003-dpcc-primary-care-phenotype-treatment-gap"
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
                "quest_id": quest_id,
                "status": "running",
                "active_run_id": "old-run",
                "worker_running": True,
                "current_controller_authorization": {
                    "decision_id": "stale-publication-gate-recheck",
                    "active_run_id": "old-run",
                    "controller_actions": ["run_gate_clearing_batch"],
                    "route_target": "review",
                    "work_unit_id": "publication_gate_recheck",
                    "work_unit_fingerprint": "publication-gate-recheck::closed-work-unit",
                    "next_work_unit": {
                        "unit_id": "publication_gate_recheck",
                        "lane": "review",
                    },
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
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "stale-publication-gate-recheck",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-20T16:24:17+00:00",
                "decision_type": "route_back_same_line",
                "charter_ref": {
                    "charter_id": f"charter::{quest_id}::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": f"runtime-escalation::{quest_id}::stale",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::003::current",
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "run_gate_clearing_batch",
                        "payload_ref": str(decision_path),
                    }
                ],
                "reason": "Stale gate recheck should be superseded by AI reviewer redrive.",
                "route_target": "review",
                "route_key_question": "publication_gate_recheck: Replay the publication gate.",
                "route_rationale": "Old gate replay route.",
                "work_unit_fingerprint": "publication-gate-recheck::closed-work-unit",
                "next_work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "review",
                    "summary": "Replay publication gate.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    publication_eval_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::003::current",
                "study_id": quest_id,
                "quest_id": quest_id,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    tick_request = {
        "charter_ref": {
            "charter_id": f"charter::{quest_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::003::current",
            "artifact_path": str(publication_eval_path),
        },
        "decision_type": "continue_same_line",
        "route_target": "review",
        "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
        "route_rationale": "Mechanical projection cannot authorize quality closure.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "payload_ref": str(decision_path),
            }
        ],
        "reason": "Re-run AI reviewer manuscript-quality review after reviewer revision intake.",
        "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review",
        "next_work_unit": {
            "unit_id": "ai_reviewer_medical_prose_quality_review",
            "lane": "review",
            "summary": "Re-run AI reviewer manuscript-quality review after reviewer revision intake.",
        },
        "blocking_work_units": [
            {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
            }
        ],
    }
    status_payload = {
        "study_id": quest_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "quest_status": "running",
        "active_run_id": "old-run",
        "runtime_liveness_audit": {"status": "live", "active_run_id": "old-run", "worker_running": True},
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "route_target": "review",
            "next_work_unit": tick_request["next_work_unit"],
        },
    }

    monkeypatch.setattr(
        "med_autoscience.controllers.study_runtime_router.progress_projection",
        lambda **_: dict(status_payload),
    )
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: dict(tick_request))

    def materialize_non_dispatching_outer_loop_decision(**_: object) -> dict[str, object]:
        decision_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "decision_id": "fresh-ai-reviewer-medical-prose-quality",
                    "study_id": quest_id,
                    "quest_id": quest_id,
                    "emitted_at": "2026-05-21T16:13:10+00:00",
                    "decision_type": "continue_same_line",
                    "charter_ref": tick_request["charter_ref"],
                    "runtime_escalation_ref": {
                        "record_id": f"runtime-escalation::{quest_id}::ai-reviewer",
                        "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                        "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    },
                    "publication_eval_ref": tick_request["publication_eval_ref"],
                    "requires_human_confirmation": False,
                    "controller_actions": tick_request["controller_actions"],
                    "reason": tick_request["reason"],
                    "route_target": "review",
                    "route_key_question": tick_request["route_key_question"],
                    "route_rationale": tick_request["route_rationale"],
                    "work_unit_fingerprint": tick_request["work_unit_fingerprint"],
                    "next_work_unit": tick_request["next_work_unit"],
                    "blocking_work_units": tick_request["blocking_work_units"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {"artifact_path": str(decision_path)},
        }

    class StartedProcess:
        pid = 12345

    monkeypatch.setattr(outer_loop, "materialize_non_dispatching_outer_loop_decision", materialize_non_dispatching_outer_loop_decision)
    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: StartedProcess())

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id="run-fresh-ai-reviewer",
        reason="auto_continue",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    current_authorization = runtime_state["current_controller_authorization"]

    assert '"decision_id": "fresh-ai-reviewer-medical-prose-quality"' in prompt
    assert '"work_unit_id": "ai_reviewer_medical_prose_quality_review"' in prompt
    assert "return_to_ai_reviewer_workflow" in prompt
    assert "AI reviewer redrive execution contract" in prompt
    assert "materialize-ai-medical-prose-review" in prompt
    assert "run_gate_clearing_batch" not in prompt
    assert "publication_gate_recheck" not in prompt
    assert current_authorization["decision_id"] == "fresh-ai-reviewer-medical-prose-quality"
    assert current_authorization["active_run_id"] == "run-fresh-ai-reviewer"
    assert current_authorization["controller_actions"] == ["return_to_ai_reviewer_workflow"]
    assert current_authorization["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert runtime_state["current_controller_authorization_currentness"]["status"] == "materialized"
