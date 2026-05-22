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


def test_codex_exec_runner_uses_status_domain_transition_when_outer_loop_tick_is_stale(
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
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    charter_path.parent.mkdir(parents=True, exist_ok=True)
    charter_path.write_text(
        json.dumps({"charter_id": f"charter::{quest_id}::v1"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps({"quest_id": quest_id, "status": "running"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    eval_id = "publication-eval::dm003::stale-write-route"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_path.parent.mkdir(parents=True, exist_ok=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": eval_id,
                "study_id": quest_id,
                "quest_id": quest_id,
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "route_target": "write",
                        "route_key_question": "Repair medical manuscript prose quality.",
                        "route_rationale": "Stale write route from the previous evaluation.",
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
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "stale-medical-prose-write-repair",
                "study_id": quest_id,
                "quest_id": quest_id,
                "emitted_at": "2026-05-22T09:00:15+00:00",
                "decision_type": "route_back_same_line",
                "charter_ref": {"charter_id": f"charter::{quest_id}::v1", "artifact_path": str(charter_path)},
                "publication_eval_ref": {"eval_id": eval_id, "artifact_path": str(publication_eval_path)},
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "run_quality_repair_batch", "payload_ref": str(decision_path)}],
                "route_target": "write",
                "route_key_question": "Repair medical manuscript prose quality.",
                "route_rationale": "Old write route.",
                "reason": "Old write route.",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Revise the manuscript to medical journal prose standards.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    stale_tick_request = {
        "charter_ref": {"charter_id": f"charter::{quest_id}::v1", "artifact_path": str(charter_path)},
        "publication_eval_ref": {"eval_id": eval_id, "artifact_path": str(publication_eval_path)},
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "route_key_question": "Repair medical manuscript prose quality.",
        "route_rationale": "Old write route.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [{"action_type": "run_quality_repair_batch", "payload_ref": str(decision_path)}],
        "reason": "Old write route.",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_work_unit": {
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
            "summary": "Revise the manuscript to medical journal prose standards.",
        },
        "blocking_work_units": [
            {"unit_id": "medical_prose_write_repair", "lane": "write"},
        ],
    }
    status_payload = {
        "study_id": quest_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "quest_status": "active",
        "active_run_id": "old-run",
        "runtime_liveness_audit": {"status": "live", "active_run_id": "old-run", "worker_running": True},
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "route_target": "review",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
        },
    }

    monkeypatch.setattr(
        "med_autoscience.controllers.study_runtime_router.progress_projection",
        lambda **_: dict(status_payload),
    )
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: dict(stale_tick_request))

    def materialize_non_dispatching_outer_loop_decision(**kwargs: object) -> dict[str, object]:
        decision_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "decision_id": "fresh-ai-reviewer-from-status-domain-transition",
                    "study_id": quest_id,
                    "quest_id": quest_id,
                    "emitted_at": "2026-05-22T09:35:10+00:00",
                    "decision_type": kwargs["decision_type"],
                    "charter_ref": kwargs["charter_ref"],
                    "runtime_escalation_ref": {
                        "record_id": f"runtime-escalation::{quest_id}::ai-reviewer",
                        "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                        "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    },
                    "publication_eval_ref": kwargs["publication_eval_ref"],
                    "requires_human_confirmation": False,
                    "controller_actions": kwargs["controller_actions"],
                    "reason": kwargs["reason"],
                    "route_target": kwargs["route_target"],
                    "route_key_question": kwargs["route_key_question"],
                    "route_rationale": kwargs["route_rationale"],
                    "work_unit_fingerprint": kwargs["work_unit_fingerprint"],
                    "next_work_unit": kwargs["next_work_unit"],
                    "blocking_work_units": kwargs["blocking_work_units"],
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
        run_id="run-status-domain-transition",
        reason="auto_continue",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    current_authorization = runtime_state["current_controller_authorization"]

    assert '"decision_id": "fresh-ai-reviewer-from-status-domain-transition"' in prompt
    assert '"work_unit_id": "ai_reviewer_medical_prose_quality_review"' in prompt
    assert "return_to_ai_reviewer_workflow" in prompt
    assert "AI reviewer redrive execution contract" in prompt
    assert "medical_prose_write_repair" not in prompt
    assert "run_quality_repair_batch" not in prompt
    assert current_authorization["decision_id"] == "fresh-ai-reviewer-from-status-domain-transition"
    assert current_authorization["active_run_id"] == "run-status-domain-transition"
    assert current_authorization["controller_actions"] == ["return_to_ai_reviewer_workflow"]
    assert current_authorization["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert runtime_state["current_controller_authorization_currentness"]["status"] == "materialized"
    assert (
        runtime_state["current_controller_authorization_currentness"]["currentness_basis"]
        == "status_domain_transition"
    )
