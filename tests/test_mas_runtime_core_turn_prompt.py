from __future__ import annotations

import importlib
from pathlib import Path
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
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-002"
    runtime_root = tmp_path / "workspace" / "runtime"
    _write_workspace_python(quest_root)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        """
{
  "last_controller_decision_authorization": {
    "decision_id": "decision-quality-002",
    "controller_actions": ["run_quality_repair_batch"],
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
    assert '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}"' in prompt
    assert "python -m med_autoscience.cli quality-repair-batch" in prompt
    assert '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}"' in prompt
    assert "--study-id <study_id>" in prompt
    assert "--quest-id quest-002" in prompt
    assert "ops/medautoscience/profiles/*.workspace.toml" in prompt
    assert "ops/medautoscience/profiles/*.local.toml" in prompt
    assert "Invoke the listed controller command before freeform artifact writing" in prompt
    assert "repair packet, gate audit, controller handoff, runtime/watch receipt, or console-only summary is not sufficient" in prompt
    assert "blocked_reason=owner_callable_surface_missing" in prompt


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
    assert '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}"' in prompt
    assert "python -m med_autoscience.cli quality-repair-batch" in prompt
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
    assert '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}"' in prompt
    assert "python -m med_autoscience.cli quality-repair-batch" in prompt
    assert "--quest-id quest-004" in prompt
    assert "No callable MAS CLI command is registered" not in prompt
    assert "Requested controller actions: request_gate_specificity" not in prompt
