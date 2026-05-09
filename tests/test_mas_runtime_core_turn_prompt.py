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
