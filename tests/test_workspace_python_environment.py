from __future__ import annotations

import importlib
from types import SimpleNamespace


def test_workspace_python_environment_syncs_workspace_project_without_workspace_extra(monkeypatch, tmp_path) -> None:
    module = importlib.import_module("med_autoscience.workspace_python_environment")
    workspace_root = tmp_path / "paper-workspace"
    python_path = workspace_root / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    python_path.chmod(0o755)
    monkeypatch.setattr(module.shutil, "which", lambda executable: "/tmp/uv" if executable == "uv" else None)

    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        _ = kwargs
        calls.append(list(args))
        if args[0] == "/tmp/uv":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout='{"ready": true}\n', stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.ensure_workspace_python_environment(workspace_root=workspace_root)

    assert result["status"] == "ready"
    assert result["ready"] is True
    assert calls[0] == ["/tmp/uv", "sync", "--directory", str(workspace_root.resolve()), "--inexact"]
    assert "--extra" not in calls[0]
