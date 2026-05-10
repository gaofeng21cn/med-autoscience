from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess


def test_codex_exec_runner_uses_quest_local_python_cache(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    seen = {}

    class StartedProcess:
        pid = 12345

    def fake_popen(args, **kwargs):
        seen["args"] = list(args)
        seen["cwd"] = kwargs.get("cwd")
        seen["env"] = kwargs.get("env")
        seen["stdin"] = kwargs.get("stdin")
        return StartedProcess()

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    assert result["live"] is True
    assert result["command"] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert result["start_mode"] == "worker_wrapper_subprocess"
    assert result["monitor_kind"] == "mas_per_run_worker_wrapper"
    assert result["monitor_pid"] == 12345
    assert "med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper" in seen["args"]
    assert "--codex-binary" in seen["args"]
    assert "codex" in seen["args"]
    assert seen["cwd"] == str(quest_root)
    assert seen["env"]["PYTHONPYCACHEPREFIX"] == str(quest_root / ".ds" / "python_pycache")
    assert "PYTHONDONTWRITEBYTECODE" not in seen["env"]
    assert seen["stdin"] is subprocess.DEVNULL


def test_codex_exec_runner_legacy_direct_mode_uses_quest_local_python_cache(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    seen = {}

    class StartedProcess:
        pid = 12345

    def fake_popen(args, **kwargs):
        seen["args"] = list(args)
        seen["cwd"] = kwargs.get("cwd")
        seen["env"] = kwargs.get("env")
        seen["stdin"] = kwargs.get("stdin")
        return StartedProcess()

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = runner_module.CodexExecTurnRunner(use_worker_wrapper=False).start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    assert result["live"] is True
    assert result["start_mode"] == "subprocess"
    assert seen["args"][:4] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert seen["cwd"] == str(quest_root)
    assert seen["env"]["PYTHONPYCACHEPREFIX"] == str(quest_root / ".ds" / "python_pycache")
    assert "PYTHONDONTWRITEBYTECODE" not in seen["env"]
    assert seen["stdin"] is subprocess.DEVNULL


def test_worker_wrapper_runs_codex_with_quest_local_python_cache(monkeypatch, tmp_path: Path) -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    run_id = "run-001"
    run_root = quest_root / ".ds" / "runs" / run_id
    prompt_path = run_root / "prompt.md"
    stdout_path = run_root / "stdout.jsonl"
    stderr_path = run_root / "stderr.txt"
    prompt_path.parent.mkdir(parents=True)
    prompt_path.write_text("continue", encoding="utf-8")
    seen = {}

    class CompletedProcess:
        pid = 12345

        def poll(self):
            return 0

        def wait(self):
            return 0

    def fake_popen(args, **kwargs):
        seen["args"] = list(args)
        seen["cwd"] = kwargs.get("cwd")
        seen["env"] = kwargs.get("env")
        return CompletedProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(wrapper_module, "_complete_turn", lambda **_kwargs: None)

    result = wrapper_module.run_wrapper(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id=run_id,
        prompt_path=prompt_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        codex_binary="codex",
    )

    assert result == 0
    assert seen["args"][:4] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert seen["cwd"] == str(quest_root)
    assert seen["env"]["PYTHONPYCACHEPREFIX"] == str(quest_root / ".ds" / "python_pycache")
    assert "PYTHONDONTWRITEBYTECODE" not in seen["env"]


def test_quest_python_runtime_env_loads_workspace_mas_config_for_checkout_bound_commands(
    monkeypatch,
    tmp_path: Path,
) -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    repo_root = tmp_path / "med-autoscience"
    uv_bin = tmp_path / "bin" / "uv"
    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    config_env.parent.mkdir(parents=True)
    config_env.write_text(
        "\n".join(
            [
                f'MED_AUTOSCIENCE_REPO="{repo_root}"',
                f'MED_AUTOSCIENCE_UV_BIN="{uv_bin}"',
                'MED_AUTOSCIENCE_PROFILE="${WORKSPACE_ROOT}/ignored.toml"',
                "OPENAI_API_KEY=should-not-load",
                "MED_AUTOSCIENCE_NODE_BIN=/usr/bin/node extra-token",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MED_AUTOSCIENCE_REPO", raising=False)
    monkeypatch.delenv("MED_AUTOSCIENCE_UV_BIN", raising=False)
    monkeypatch.setenv("MED_AUTOSCIENCE_PROFILE", "/already/exported/profile.toml")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env = wrapper_module.quest_python_runtime_env(quest_root=quest_root)

    assert env["MED_AUTOSCIENCE_REPO"] == str(repo_root)
    assert env["MED_AUTOSCIENCE_UV_BIN"] == str(uv_bin)
    assert env["MED_AUTOSCIENCE_PROFILE"] == "/already/exported/profile.toml"
    assert env["WORKSPACE_ROOT"] == str(workspace_root)
    assert "OPENAI_API_KEY" not in env
    assert "MED_AUTOSCIENCE_NODE_BIN" not in env


def test_quest_python_runtime_env_removes_development_virtualenv(monkeypatch, tmp_path: Path) -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    dev_venv = tmp_path / "repo" / ".venv"
    dev_bin = dev_venv / "bin"
    other_bin = tmp_path / "bin"
    dev_bin.mkdir(parents=True)
    other_bin.mkdir()
    monkeypatch.setenv("VIRTUAL_ENV", str(dev_venv))
    monkeypatch.setenv("__PYVENV_LAUNCHER__", str(dev_bin / "python3"))
    monkeypatch.setenv("PATH", f"{dev_bin}{os.pathsep}{other_bin}")

    env = wrapper_module.quest_python_runtime_env(quest_root=quest_root)

    assert env["PYTHONPYCACHEPREFIX"] == str(quest_root / ".ds" / "python_pycache")
    assert "VIRTUAL_ENV" not in env
    assert "__PYVENV_LAUNCHER__" not in env
    assert str(dev_bin) not in env["PATH"].split(os.pathsep)
    assert str(other_bin) in env["PATH"].split(os.pathsep)
