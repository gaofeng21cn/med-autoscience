from __future__ import annotations

import importlib
from pathlib import Path
import subprocess


def test_codex_exec_runner_prompt_requires_auditable_turn_closeout(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"

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


def test_codex_exec_runner_prompt_includes_active_controller_work_unit(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
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
    assert "Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this controller work unit" in prompt
    assert "runtime/watch/health/control-plane receipt alone is not a meaningful artifact delta" in prompt
