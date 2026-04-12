from __future__ import annotations

import importlib
import sqlite3
import subprocess
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def test_inspect_hermes_runtime_contract_reports_missing_external_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.hermes_runtime_contract")

    result = module.inspect_hermes_runtime_contract(
        hermes_agent_repo_root=tmp_path / "missing-hermes-agent",
        hermes_home_root=tmp_path / "missing-hermes-home",
    )

    assert result["configured"] is True
    assert result["repo_exists"] is False
    assert result["launcher_exists"] is False
    assert result["gateway_launcher_exists"] is False
    assert result["hermes_home_exists"] is False
    assert result["state_db_exists"] is False
    assert result["provider_ready"] is False
    assert result["gateway_service_loaded"] is False
    assert result["ready"] is False
    assert "external_runtime.repo_missing" in result["issues"]
    assert "external_runtime.provider_not_configured" in result["issues"]


def test_inspect_hermes_runtime_contract_accepts_ready_external_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.hermes_runtime_contract")

    repo_root = tmp_path / "hermes-agent"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / "scripts").mkdir()
    (repo_root / ".venv" / "bin").mkdir(parents=True)
    (repo_root / "pyproject.toml").write_text("[project]\nname = 'hermes-agent'\n", encoding="utf-8")
    _write_executable(repo_root / "hermes", "#!/usr/bin/env bash\nexit 0\n")
    _write_executable(repo_root / "scripts" / "hermes-gateway", "#!/usr/bin/env bash\nexit 0\n")
    _write_executable(repo_root / ".venv" / "bin" / "python", "#!/usr/bin/env bash\nexit 0\n")

    hermes_home = tmp_path / ".hermes"
    (hermes_home / "logs").mkdir(parents=True)
    (hermes_home / "sessions").mkdir()
    (hermes_home / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
    (hermes_home / "config.yaml").write_text("provider: openai\nmodel: gpt-5\n", encoding="utf-8")
    (hermes_home / "state.db").touch()

    with sqlite3.connect(hermes_home / "state.db") as conn:
        conn.execute("create table sessions (id integer primary key)")
        conn.execute("create table messages (id integer primary key)")
        conn.execute("insert into sessions default values")
        conn.execute("insert into messages default values")
        conn.commit()

    monkeypatch.setattr(
        module,
        "_inspect_gateway_service",
        lambda **_: {
            "manager": "launchd",
            "service_label": "ai.hermes.gateway",
            "service_file_exists": True,
            "loaded": True,
            "issues": [],
        },
    )

    result = module.inspect_hermes_runtime_contract(
        hermes_agent_repo_root=repo_root,
        hermes_home_root=hermes_home,
    )

    assert result["configured"] is True
    assert result["repo_exists"] is True
    assert result["launcher_exists"] is True
    assert result["gateway_launcher_exists"] is True
    assert result["managed_python_exists"] is True
    assert result["hermes_home_exists"] is True
    assert result["state_db_exists"] is True
    assert result["provider_ready"] is True
    assert result["session_count"] == 1
    assert result["message_count"] == 1
    assert result["gateway_service_loaded"] is True
    assert result["ready"] is True
    assert result["issues"] == []
