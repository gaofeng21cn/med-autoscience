from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


def test_codex_exec_runner_uses_quest_local_python_cache(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    workspace_python = tmp_path / "workspace" / ".venv" / "bin" / "python3"
    workspace_python.parent.mkdir(parents=True)
    workspace_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    workspace_python.chmod(0o755)
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
    assert seen["args"][0] == str(workspace_python)
    assert seen["args"][0] != sys.executable
    assert "med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper" in seen["args"]
    assert "--codex-binary" in seen["args"]
    assert "codex" in seen["args"]
    assert seen["cwd"] == str(quest_root)
    assert seen["env"]["PYTHONPYCACHEPREFIX"] == str(quest_root / ".ds" / "python_pycache")
    assert "PYTHONDONTWRITEBYTECODE" not in seen["env"]
    assert seen["stdin"] is subprocess.DEVNULL


def test_worker_wrapper_module_entrypoint_does_not_eager_load_runtime_backend(tmp_path: Path) -> None:
    env = os.environ.copy()
    src_path = str((Path(__file__).resolve().parents[1] / "src").resolve())
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])
    env["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper",
            "--help",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "MAS per-run Codex worker watchdog wrapper" in result.stdout
    assert "RuntimeWarning" not in result.stderr
    assert "managed runtime backend must expose non-empty BACKEND_ID" not in result.stderr


def test_worker_wrapper_isolates_codex_child_from_user_home(monkeypatch, tmp_path: Path) -> None:
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
    user_home = tmp_path / "user-home"
    codex_home = user_home / ".codex"
    codex_home.mkdir(parents=True)
    (codex_home / "auth.json").write_text('{"OPENAI_API_KEY":"test-token"}\n', encoding="utf-8")
    (codex_home / "config.toml").write_text(
        "\n".join(
            [
                'model_provider = "gflab"',
                'model = "gpt-5.5"',
                'model_reasoning_effort = "medium"',
                'sandbox_mode = "danger-full-access"',
                'notify = ["osascript"]',
                "",
                "[model_providers.gflab]",
                'name = "gflab"',
                'base_url = "https://example.test/v1"',
                'wire_api = "responses"',
                'experimental_bearer_token = "secret-provider-token"',
                "",
                "[mcp_servers.sentrux]",
                'command = "/opt/homebrew/bin/sentrux"',
                'args = ["mcp"]',
                "",
                "[marketplaces.openai-bundled]",
                'source = "builtin"',
                "",
                "[plugins.computer-use]",
                "enabled = true",
                "",
                "[skills]",
                'config = ["computer-use"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(user_home))
    seen = {}

    class CompletedProcess:
        pid = 12345

        def poll(self):
            return 0

        def wait(self):
            return 0

    def fake_popen(args, **kwargs):
        seen["args"] = list(args)
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
    assert "--ephemeral" in seen["args"]
    assert "-c" not in seen["args"]
    assert "mcp_servers={}" not in seen["args"]
    assert "plugins={}" not in seen["args"]
    assert "notify=[]" not in seen["args"]
    assert "secret-provider-token" not in " ".join(seen["args"])
    runtime_home = quest_root / ".ds" / "codex_homes" / "run-001"
    runtime_codex_home = runtime_home / ".codex"
    assert seen["env"]["HOME"] == str(runtime_home)
    assert seen["env"]["CODEX_HOME"] == str(runtime_codex_home)
    assert seen["env"]["XDG_CACHE_HOME"] == str(runtime_home / ".cache")
    assert seen["env"]["XDG_CONFIG_HOME"] == str(runtime_home / ".config")
    assert seen["env"]["XDG_DATA_HOME"] == str(runtime_home / ".local" / "share")
    assert seen["env"]["NPM_CONFIG_CACHE"] == str(runtime_home / ".npm")
    assert seen["env"]["UV_CACHE_DIR"] == str(runtime_home / ".cache" / "uv")
    assert seen["env"]["MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER"] == "1"
    assert seen["env"]["MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT"] == str(quest_root)
    assert seen["env"]["MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID"] == "quest-001"
    assert seen["env"]["MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID"] == "run-001"
    assert (runtime_codex_home / "auth.json").read_text(encoding="utf-8") == '{"OPENAI_API_KEY":"test-token"}\n'
    config = tomllib.loads((runtime_codex_home / "config.toml").read_text(encoding="utf-8"))
    assert config["model_provider"] == "gflab"
    assert config["model"] == "gpt-5.5"
    assert config["model_providers"]["gflab"]["experimental_bearer_token"] == "secret-provider-token"
    assert "mcp_servers" not in config
    assert "plugins" not in config
    assert "notify" not in config
    assert "marketplaces" not in config
    assert "skills" not in config


def test_worker_wrapper_preserves_host_nvm_codex_for_isolated_home(monkeypatch, tmp_path: Path) -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    user_home = tmp_path / "user-home"
    host_codex = user_home / ".nvm" / "versions" / "node" / "v22.16.0" / "bin" / "codex"
    host_codex.parent.mkdir(parents=True)
    host_codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    host_codex.chmod(0o755)
    monkeypatch.setenv("HOME", str(user_home))
    monkeypatch.setenv("NVM_DIR", str(user_home / ".nvm"))
    monkeypatch.delenv("CODEX_CANONICAL_BIN", raising=False)

    env = wrapper_module.quest_python_runtime_env(quest_root=quest_root, run_id="run-001")

    assert env["HOME"] == str(quest_root / ".ds" / "codex_homes" / "run-001")
    assert env["CODEX_CANONICAL_BIN"] == str(host_codex)
    assert env["MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER"] == "1"
    assert env["MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT"] == str(quest_root)
    assert env["MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID"] == "quest-001"
    assert env["MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID"] == "run-001"


def test_launch_report_write_truncates_stale_tail(tmp_path: Path) -> None:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    launch_report_path = tmp_path / "study" / "artifacts" / "runtime" / "last_launch_report.json"
    launch_report_path.parent.mkdir(parents=True)
    launch_report_path.write_text(
        '{"schema_version":1,"old_payload":"' + ("x" * 5000) + '"}\n',
        encoding="utf-8",
    )

    protocol.write_launch_report(
        launch_report_path=launch_report_path,
        status={
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "running",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-001",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-001",
                    "worker_running": True,
                },
            },
        },
        source="study_runtime_status",
        force=False,
        startup_payload_path=None,
        daemon_result=None,
        recorded_at="2026-05-11T04:00:00+00:00",
    )

    payload = json.loads(launch_report_path.read_text(encoding="utf-8"))
    assert payload["active_run_id"] == "run-001"
    assert "old_payload" not in payload


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


def test_codex_exec_runner_blocks_when_workspace_python_missing(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"

    def fail_popen(*_args, **_kwargs):
        raise AssertionError("runner must fail closed before spawning without workspace Python")

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    assert result["live"] is False
    assert result["fail_closed"] is True
    assert result["error"] == "workspace_python_missing_or_not_executable"


def test_worker_wrapper_command_uses_workspace_python_from_quest_root(tmp_path: Path) -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    workspace_root = tmp_path / "workspace"
    runtime_root = workspace_root / "runtime"
    quest_root = runtime_root / "quests" / "quest-001"
    workspace_python = workspace_root / ".venv" / "bin" / "python3"
    workspace_python.parent.mkdir(parents=True)
    workspace_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    workspace_python.chmod(0o755)

    command = wrapper_module.wrapper_command(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        prompt_path=quest_root / ".ds" / "runs" / "run-001" / "prompt.md",
        stdout_path=quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl",
        stderr_path=quest_root / ".ds" / "runs" / "run-001" / "stderr.txt",
        codex_binary="codex",
    )

    assert command[0] == str(workspace_python)
    assert command[0] != sys.executable
    assert command[1:3] == ["-m", "med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper"]


def test_worker_wrapper_codex_command_disables_desktop_mcp_for_background_runs() -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")

    command = wrapper_module._codex_exec_command(codex_binary="codex", prompt="continue")

    assert command[:5] == ["codex", "exec", "--json", "--skip-git-repo-check", "--ephemeral"]
    assert "--ignore-user-config" not in command
    assert "continue" == command[-1]
    assert "-c" not in command
    assert "mcp_servers={}" not in command
    assert "plugins={}" not in command
    assert "notify=[]" not in command


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


def test_quest_python_runtime_env_adds_configured_tool_dirs_to_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    wrapper_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    repo_root = tmp_path / "med-autoscience"
    uv_bin = tmp_path / "tools" / "uv-bin" / "uv"
    node_bin = tmp_path / "tools" / "node-bin" / "node"
    for binary in (uv_bin, node_bin):
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)
    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    config_env.parent.mkdir(parents=True)
    config_env.write_text(
        "\n".join(
            [
                f'MED_AUTOSCIENCE_REPO="{repo_root}"',
                f'MED_AUTOSCIENCE_UV_BIN="{uv_bin}"',
                f'MED_AUTOSCIENCE_NODE_BIN="{node_bin}"',
                'MED_AUTOSCIENCE_PROFILE="${WORKSPACE_ROOT}/profile.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    existing_bin = tmp_path / "existing-bin"
    existing_bin.mkdir()
    monkeypatch.setenv("PATH", str(existing_bin))
    monkeypatch.delenv("MED_AUTOSCIENCE_UV_BIN", raising=False)
    monkeypatch.delenv("MED_AUTOSCIENCE_NODE_BIN", raising=False)

    env = wrapper_module.quest_python_runtime_env(quest_root=quest_root)

    path_entries = env["PATH"].split(os.pathsep)
    assert path_entries[:2] == [str(uv_bin.parent), str(node_bin.parent)]
    assert str(existing_bin) in path_entries
    assert env["MED_AUTOSCIENCE_UV_BIN"] == str(uv_bin)
    assert env["MED_AUTOSCIENCE_NODE_BIN"] == str(node_bin)


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
