from __future__ import annotations

import importlib
import json
from pathlib import Path
import shlex
import subprocess


def _write_workspace_python(quest_root: Path) -> None:
    python_path = quest_root.parents[2] / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True, exist_ok=True)
    python_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_path.chmod(0o755)


def test_codex_exec_runner_prompt_requires_auditable_turn_closeout(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)

    class StartedProcess:
        pid = 12345

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: StartedProcess())

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "artifacts/runtime/turn_closeouts/run-001.json" in prompt
    assert '"schema_version"' in prompt
    assert '"quest_id": "quest-001"' in prompt
    assert '"run_id": "run-001"' in prompt
    assert '"status": "completed"' in prompt
    assert '"meaningful_artifact_delta"' in prompt
    assert '"artifact_refs"' in prompt
    assert '"blocked_reason"' in prompt
    assert '"next_owner"' in prompt
    assert "write a blocked closeout" in prompt
    assert "Do not mutate paper/current_package" in prompt
    assert "Do not relax MAS quality gates" in prompt
    assert "This Codex process is the MAS managed runtime worker for this run" in prompt
    assert "Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this runtime turn" in prompt


def test_codex_exec_runner_prompt_includes_active_controller_work_unit(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "active_run_id": null,
  "last_controller_decision_authorization": {
    "decision_id": "decision-analysis-001",
    "controller_actions": ["run_quality_repair_batch"],
    "route_target": "write",
    "work_unit_id": "analysis_claim_evidence_repair",
    "work_unit_fingerprint": "publication-blockers::current",
    "next_work_unit": {
      "unit_id": "analysis_claim_evidence_repair",
      "lane": "analysis-campaign",
      "summary": "Repair claim-evidence blockers."
    },
    "specificity_targets": [
      {
        "target_kind": "claim",
        "target_id": "claim_evidence_map",
        "source_path": "paper/claim_evidence_map.json"
      }
    ]
  }
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
        quest_id="quest-001",
        run_id="run-001",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Active MAS controller work unit" in prompt
    assert '"work_unit_id": "analysis_claim_evidence_repair"' in prompt
    assert '"work_unit_fingerprint": "publication-blockers::current"' in prompt
    assert '"target_id": "claim_evidence_map"' in prompt
    assert "Treat this controller work unit as the first execution target" in prompt
    assert "This Codex process is the MAS managed runtime worker for this run" in prompt
    assert "Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this runtime turn" in prompt
    assert "Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this controller work unit" in prompt
    assert "analysis-campaign/write controller work units may revise canonical `paper/` surfaces" in prompt
    assert "publication gate `allow_write=false` blocks generated package/submission writes" in prompt
    assert "runtime/watch/health/control-plane receipt alone is not a meaningful artifact delta" in prompt


def test_codex_exec_runner_prompt_names_unit_harmonized_rerun_for_hard_methodology_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-002"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "active_run_id": null,
  "last_controller_decision_authorization": {
    "decision_id": "decision-hdl-unit",
    "controller_actions": ["run_quality_repair_batch"],
    "route_target": "analysis-campaign",
    "route_key_question": "unit-harmonized external validation rerun or typed blocker",
    "work_unit_id": "medical_prose_quality_analysis_source_documentation_repair",
    "work_unit_fingerprint": "publication-blockers::hdl-unit",
    "next_work_unit": {
      "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
      "lane": "analysis-campaign",
      "summary": "Close or type-block HDL harmonization and model reproducibility gaps."
    },
    "specificity_targets": [
      {
        "target_kind": "metric",
        "target_id": "hdl_unit_standardized_sensitivity",
        "source_path": "artifacts/analysis/harmonization_route_back/latest.md",
        "blocking_reason": "unit_standardized_model_application_or_sensitivity"
      }
    ]
  }
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
        quest_id="quest-002",
        run_id="run-hdl-unit",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Hard methodology/unit-harmonization contract" in prompt
    assert "unit_harmonized_external_validation_rerun" in prompt
    assert "blocked_reason=unit_harmonized_rerun_required" in prompt
    assert "next_owner=source_provenance_owner" in prompt
    assert "next_work_unit=recover_transport_model_provenance" in prompt
    assert "next_owner=analysis_harmonization_owner" in prompt
    assert "next_work_unit=unit_harmonized_external_validation_rerun" in prompt
    assert "A prose/source-documentation note or generic completed closeout is not sufficient" in prompt


def test_codex_exec_runner_prompt_omits_queued_controller_authorization_when_active_authorization_exists(
    monkeypatch, tmp_path: Path
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-analysis-001",
    "controller_actions": ["ensure_study_runtime"],
    "route_target": "analysis-campaign",
    "route_key_question": "paper/rebuttal/review_matrix.md and action_plan.md",
    "work_unit_id": "paper/rebuttal/review_matrix.md and action_plan.md"
  }
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
        quest_id="quest-001",
        run_id="run-001",
        reason="queued_user_messages",
        claimed_user_messages=(
            {
                "message_id": "msg-stale-review",
                "source": "domain_health_diagnostic",
                "content": (
                    "MAS controller authorization. `/workspace/studies/001/artifacts/controller_decisions/latest.json` "
                    "is the active MAS authorization for this runtime turn.\n\n"
                    "- route_target: `review` (质量复评)\n"
                    "- route_key_question: publication_gate_blocker_review: Review the current publication gate blockers.\n"
                    "- active_work_unit_id: `publication_gate_blocker_review`"
                ),
            },
            {
                "message_id": "msg-user",
                "source": "user",
                "content": "Please preserve this ordinary user instruction.",
            },
        ),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Active MAS controller work unit" in prompt
    assert '"route_target": "analysis-campaign"' in prompt
    assert "publication_gate_blocker_review" not in prompt
    assert "Please preserve this ordinary user instruction." in prompt


def test_codex_exec_runner_prompt_skips_closed_publication_work_unit_authorization(
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
    (study_root).mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 002-dm\n", encoding="utf-8")
    lifecycle_path = study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        """
{
  "schema_version": 1,
  "source_eval_id": "publication-eval::002-dm::002-dm::2026-05-12T10:36:52+00:00",
  "study_id": "002-dm",
  "quest_id": "002-dm",
  "status": "done",
  "work_unit": {
    "unit_id": "submission_authority_sync_closure",
    "lane": "controller"
  },
  "unit_statuses": [
    {"unit_id": "create_submission_minimal_package", "status": "ok"},
    {"unit_id": "sync_submission_minimal_delivery", "status": "settled_by_current_gate"}
  ],
  "gate_replay_status": "clear"
}
""",
        encoding="utf-8",
    )
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "active_run_id": "run-live-001",
  "last_controller_decision_authorization": {
    "decision_id": "decision-authority-sync-stale",
    "controller_actions": ["ensure_study_runtime"],
    "route_target": "finalize",
    "work_unit_id": "submission_authority_sync_closure",
    "work_unit_fingerprint": "publication-blockers::authority-sync",
    "next_work_unit": {
      "unit_id": "submission_authority_sync_closure",
      "lane": "controller",
      "summary": "Regenerate submission authority signatures, then replay the publication gate."
    },
    "controller_work_unit_lifecycle": {
      "lifecycle_state": "new",
      "terminal_consumed": false
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
  "decision_id": "decision-authority-sync-stale",
  "publication_eval_ref": {
    "eval_id": "publication-eval::002-dm::002-dm::2026-05-12T10:36:52+00:00",
    "artifact_path": "/tmp/publication_eval/latest.json"
  },
  "next_work_unit": {
    "unit_id": "submission_authority_sync_closure",
    "lane": "controller"
  },
  "work_unit_fingerprint": "publication-blockers::authority-sync"
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
        run_id="run-002",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert "Active MAS controller work unit" not in prompt
    assert "submission_authority_sync_closure" not in prompt
    assert "Turn closeout contract" in prompt
    assert "last_controller_decision_authorization" not in runtime_state
    assert runtime_state["last_runtime_turn_state_sanitization"]["reason"] == "publication_work_unit_lifecycle_done"
    assert runtime_state["continuation_reason"] == "closed_controller_work_unit_authorization_cleared"


def test_codex_exec_runner_prompt_skips_owner_handoff_publication_work_unit_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    workspace_root = tmp_path / "workspace"
    quest_id = "obesity_multicenter_phenotype_atlas"
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    runtime_root = workspace_root / "runtime"
    study_root = workspace_root / "studies" / quest_id
    _write_workspace_python(quest_root)
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {quest_id}\n", encoding="utf-8")
    lifecycle_path = study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        """
{
  "schema_version": 1,
  "source_eval_id": "publication-eval::obesity::latest",
  "study_id": "obesity_multicenter_phenotype_atlas",
  "quest_id": "obesity_multicenter_phenotype_atlas",
  "status": "owner_handoff",
  "work_unit": {
    "unit_id": "analysis_claim_evidence_repair",
    "lane": "analysis-campaign"
  },
  "unit_statuses": [
    {"unit_id": "analysis_claim_evidence_repair", "status": "owner_handoff"}
  ],
  "terminal_consumed": true,
  "recommended_next_route": "handoff_to_next_owner",
  "next_owner": "write/ai_reviewer"
}
""",
        encoding="utf-8",
    )
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "active_run_id": "run-live-obesity",
  "last_controller_decision_authorization": {
    "decision_id": "decision-analysis-obesity-stale",
    "publication_eval_id": "publication-eval::obesity::latest",
    "controller_actions": ["run_quality_repair_batch"],
    "route_target": "analysis-campaign",
    "work_unit_id": "analysis_claim_evidence_repair",
    "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
    "next_work_unit": {
      "unit_id": "analysis_claim_evidence_repair",
      "lane": "analysis-campaign",
      "summary": "Repair claim-evidence blockers."
    },
    "controller_work_unit_lifecycle": {
      "lifecycle_state": "owner_handoff",
      "terminal_consumed": true
    }
  }
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
        run_id="run-obesity",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert "Active MAS controller work unit" not in prompt
    assert "analysis_claim_evidence_repair" not in prompt
    assert "publication-blockers::f11710a114497b27" not in prompt
    assert "last_controller_decision_authorization" not in runtime_state
    assert runtime_state["last_runtime_turn_state_sanitization"]["reason"] == "publication_work_unit_lifecycle_done"
    assert runtime_state["last_runtime_turn_state_sanitization"]["cleared_keys"] == [
        "last_controller_decision_authorization"
    ]


def test_codex_exec_runner_default_turn_is_not_terminal_attach_capable(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    popen_calls = []

    class StartedProcess:
        pid = 12345

    def fake_popen(*args, **kwargs):
        popen_calls.append((args, kwargs))
        return StartedProcess()

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_resume",
        claimed_user_messages=({"content": "do not become stdin", "source": "test"},),
    )

    popen_kwargs = popen_calls[0][1]
    assert popen_kwargs["stdin"] is subprocess.DEVNULL
    assert "--terminal-attach-capable" not in result["wrapper_command"]
    assert result["terminal_attach_capable"] is False
    assert result["terminal_bridge_status"] == "disabled_by_run_capability"
    assert result["chat_quest_input_allowed"] is False


def test_codex_exec_runner_explicit_terminal_attach_capability_uses_controlled_bridge(
    monkeypatch, tmp_path: Path
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    popen_calls = []

    class StartedProcess:
        pid = 12345

    def fake_popen(*args, **kwargs):
        popen_calls.append((args, kwargs))
        return StartedProcess()

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_terminal_attach_test",
        claimed_user_messages=(),
        terminal_attach_capable=True,
    )

    popen_kwargs = popen_calls[0][1]
    assert popen_kwargs["stdin"] is subprocess.DEVNULL
    assert "--terminal-attach-capable" in result["wrapper_command"]
    assert result["start_mode"] == "terminal_bridge_worker_wrapper_subprocess"
    assert result["monitor_kind"] == "mas_per_run_terminal_bridge_wrapper"
    assert result["terminal_attach_capable"] is True
    assert result["terminal_bridge_status"] == "enabled"
    assert result["terminal_bridge_kind"] == "mas_controlled_pty"
    assert result["terminal_input_owner"] == "mas_terminal_attach_contract"
    assert result["chat_quest_input_allowed"] is False
    assert result["terminal_bridge_path"].endswith("/.ds/runs/run-001/terminal_bridge.json")
    assert result["terminal_transcript_path"].endswith("/.ds/runs/run-001/terminal.log")


def test_codex_exec_runner_prompt_maps_controller_action_to_callable_command(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    workspace_root = tmp_path / "workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "profile with spaces.local.toml"
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    quest_root = workspace_root / "runtime" / "quests" / "quest-002"
    runtime_root = workspace_root / "runtime"
    study_root = workspace_root / "studies" / "study with spaces"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text("profile = 'test'\n", encoding="utf-8")
    config_env_path.write_text(
        "\n".join(
            [
                f"MED_AUTOSCIENCE_REPO={shlex.quote(str(tmp_path / 'MAS repo'))}",
                f"MED_AUTOSCIENCE_PROFILE={shlex.quote(str(profile_path))}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    study_root.mkdir(parents=True, exist_ok=True)
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
    "last_controller_decision_authorization": {
      "decision_id": "decision-quality-002",
      "controller_actions": ["run_quality_repair_batch"],
      "study_id": "study with spaces",
      "work_unit_id": "analysis_claim_evidence_repair",
      "next_work_unit": {
        "unit_id": "analysis_claim_evidence_repair"
    }
  }
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
        quest_id="quest-002",
        run_id="run-002",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Controller action execution contract" in prompt
    assert "run_quality_repair_batch" in prompt
    assert f"{tmp_path / 'MAS repo'!s}" in prompt
    assert f"{shlex.quote(str(tmp_path / 'MAS repo'))}/scripts/run-python-clean.sh" in prompt
    assert "-m med_autoscience.cli quality-repair-batch" in prompt
    assert "MED_AUTOSCIENCE_UV_BIN" not in prompt
    assert "uv run --directory" not in prompt
    assert f"--profile '{profile_path!s}'" in prompt
    assert "--study-id 'study with spaces'" in prompt
    assert "--quest-id quest-002" in prompt
    assert "Resolved MAS runtime context" in prompt
    assert "med_autoscience_repo" in prompt
    assert "med_autoscience_profile" in prompt
    assert "Do not use `git status`, `rg --files`, broad `find`, or repository discovery" in prompt
    assert "ops/medautoscience/profiles/*.workspace.toml" not in prompt
    assert "ops/medautoscience/profiles/*.local.toml" not in prompt
    assert "Invoke the listed controller command before freeform artifact writing" in prompt
    assert "repair packet, gate audit, controller handoff, runtime/watch receipt, or console-only summary is not sufficient" in prompt
    assert "blocked_reason=owner_callable_surface_missing" in prompt


def test_codex_exec_runner_prompt_maps_gate_clearing_action_to_callable_command(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-002"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-gate-002",
    "controller_actions": ["run_gate_clearing_batch"],
    "work_unit_id": "publication_gate_replay",
    "next_work_unit": {
      "unit_id": "publication_gate_replay",
      "lane": "controller"
    }
  }
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
        quest_id="quest-002",
        run_id="run-002",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Controller action execution contract" in prompt
    assert "run_gate_clearing_batch" in prompt
    assert "-m med_autoscience.cli gate-clearing-batch" in prompt
    assert "--profile <med_autoscience_profile>" in prompt
    assert "--study-id quest-002" in prompt
    assert "--quest-id quest-002" in prompt
    assert "blocked_reason=managed_runtime_context_missing" in prompt
    assert "No callable MAS CLI command is registered" not in prompt


def test_codex_exec_runner_prompt_infers_gate_clearing_command_from_authority_sync_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-002"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-authority-sync-002",
    "controller_actions": ["ensure_study_runtime"],
    "route_target": "finalize",
    "work_unit_id": "submission_authority_sync_closure",
    "work_unit_fingerprint": "publication-blockers::current",
    "next_work_unit": {
      "unit_id": "submission_authority_sync_closure",
      "lane": "controller",
      "summary": "Regenerate submission authority signatures, then replay the publication gate."
    }
  }
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
        quest_id="quest-002",
        run_id="run-002",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Controller action execution contract" in prompt
    assert "ensure_study_runtime" in prompt
    assert "run_gate_clearing_batch" in prompt
    assert "-m med_autoscience.cli gate-clearing-batch" in prompt
    assert "--quest-id quest-002" in prompt
    assert "No callable MAS CLI command is registered" not in prompt


def test_codex_exec_runner_prompt_infers_quality_repair_command_from_blocking_work_units(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-003"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-quality-003",
    "blocking_work_units": [
      {"unit_id": "analysis_claim_evidence_repair"},
      {"unit_id": "manuscript_story_repair"},
      {"unit_id": "submission_minimal_refresh"}
    ]
  }
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
        quest_id="quest-003",
        run_id="run-003",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Controller action execution contract" in prompt
    assert "run_quality_repair_batch" in prompt
    assert '"${MED_AUTOSCIENCE_REPO}/scripts/run-python-clean.sh"' in prompt
    assert "-m med_autoscience.cli quality-repair-batch" in prompt
    assert "--quest-id quest-003" in prompt


def test_codex_exec_runner_prompt_maps_complete_specificity_request_to_quality_repair_command(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-004"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-specificity-004",
    "controller_actions": ["request_gate_specificity"],
    "work_unit_id": "gate_needs_specificity",
    "next_work_unit": {
      "unit_id": "gate_needs_specificity"
    },
    "specificity_targets": [
      {
        "target_kind": "claim",
        "target_id": "claim_evidence_map",
        "source_path": "paper/claim_evidence_map.json",
        "blocking_reason": "missing_publication_anchor"
      },
      {
        "target_kind": "figure",
        "target_id": "figure_catalog",
        "source_path": "paper/figures/figure_catalog.json",
        "blocking_reason": "missing_publication_anchor"
      },
      {
        "target_kind": "table",
        "target_id": "submission_manifest",
        "source_path": "paper/submission_minimal/submission_manifest.json",
        "blocking_reason": "missing_publication_anchor"
      },
      {
        "target_kind": "metric",
        "target_id": "main_result_metrics",
        "source_path": "artifacts/results/main_result.json",
        "blocking_reason": "missing_publication_anchor"
      },
      {
        "target_kind": "source_path",
        "target_id": "publication_gate_source_path",
        "source_path": "artifacts/reports/publishability_gate/latest.json",
        "blocking_reason": "missing_publication_anchor"
      }
    ]
  }
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
        quest_id="quest-004",
        run_id="run-004",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "Controller action execution contract" in prompt
    assert "Controller action names: run_quality_repair_batch." in prompt
    assert '"${MED_AUTOSCIENCE_REPO}/scripts/run-python-clean.sh"' in prompt
    assert "-m med_autoscience.cli quality-repair-batch" in prompt
    assert "--quest-id quest-004" in prompt
    assert "No callable MAS CLI command is registered" not in prompt
    assert "Requested controller actions: request_gate_specificity" not in prompt


def test_codex_exec_runner_prompt_maps_ai_reviewer_workflow_to_reviewer_owner_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-003"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-ai-reviewer-003",
    "controller_actions": ["return_to_ai_reviewer_workflow"],
    "route_target": "review",
    "work_unit_id": "ai_reviewer_recheck",
    "next_work_unit": {
      "unit_id": "ai_reviewer_recheck",
      "lane": "review",
      "summary": "Return current manuscript and evidence refs to the AI reviewer workflow."
    }
  }
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
        quest_id="quest-003",
        run_id="run-003",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "AI reviewer redrive execution contract" in prompt
    assert "return_to_ai_reviewer_workflow" in prompt
    assert "This is an AI-reviewer-owner turn" in prompt
    assert "Do not treat the supervisor dispatch command as sufficient by itself" in prompt
    assert "medical-publication-surface --apply" in prompt
    assert "manuscript completeness, Methods reproducibility, Results numeric specificity" in prompt
    assert "A mechanical checklist or script output is not quality authority" in prompt
    assert "-m med_autoscience.cli materialize-ai-medical-prose-review" in prompt
    assert "--profile <med_autoscience_profile>" in prompt
    assert "--study-id quest-003" in prompt
    assert "--payload-file <ai_reviewer_response.json>" in prompt
    assert "-m med_autoscience.cli domain-owner-action-dispatch" in prompt
    assert "--action-types return_to_ai_reviewer_workflow" in prompt
    assert "--mode developer_apply_safe --apply" in prompt
    assert "--managed-runtime-worker" in prompt
    assert "fake package freshness" in prompt
    assert "No callable MAS CLI command is registered" not in prompt


def test_codex_exec_runner_prompt_maps_current_manuscript_record_production_to_record_only_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-003"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-ai-reviewer-record-003",
    "controller_actions": ["return_to_ai_reviewer_workflow"],
    "route_target": "review",
    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    "next_work_unit": {
      "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
      "lane": "review",
      "summary": "Produce an AI reviewer publication-eval record against the current manuscript only."
    }
  }
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
        quest_id="quest-003",
        run_id="run-003",
        reason="runtime_platform_repair_redrive",
        claimed_user_messages=(),
    )

    prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")

    assert "AI reviewer publication-eval record production contract" in prompt
    assert "produce_ai_reviewer_publication_eval_record_against_current_manuscript" in prompt
    assert "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json" in prompt
    assert "-m med_autoscience.cli materialize-ai-reviewer-publication-eval-record" in prompt
    assert "--payload-file <ai_reviewer_publication_eval_record.json>" in prompt
    assert "-m med_autoscience.cli domain-action-request-materialize" in prompt
    assert "domain-action-request-materialize" in prompt
    assert "domain-action-request-materialize --profile <med_autoscience_profile> --studies quest-003 --mode developer_apply_safe --apply" in prompt
    assert "domain-action-request-materialize --profile <med_autoscience_profile> --studies quest-003 --action-types" not in prompt
    assert "-m med_autoscience.cli domain-owner-action-dispatch" in prompt
    assert "--action-types return_to_ai_reviewer_workflow" in prompt
    assert "Do not write `artifacts/publication_eval/latest.json`" in prompt
    assert "medical-publication-surface --apply" not in prompt
    assert "materialize-ai-medical-prose-review" not in prompt
