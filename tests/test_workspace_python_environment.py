from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace


def test_workspace_python_environment_reads_existing_workspace_runtime(monkeypatch, tmp_path) -> None:
    module = importlib.import_module("med_autoscience.workspace_python_environment")
    workspace_root = tmp_path / "paper-workspace"
    python_path = workspace_root / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    python_path.chmod(0o755)
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout='{"ready": true}\n', stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.inspect_workspace_python_environment(workspace_root=workspace_root)

    assert result["status"] == "ready"
    assert result["ready"] is True
    assert calls == [[str(python_path), "-c", calls[0][2]]]
    assert result["analysis_bundle"]["payload"] == {"ready": True}
    assert result["provisioning"]["owner_surface"] == "uv sync"
    assert result["provisioning"]["effect"] == "read_only"


def test_workspace_python_environment_does_not_create_or_sync_runtime(monkeypatch, tmp_path) -> None:
    module = importlib.import_module("med_autoscience.workspace_python_environment")
    workspace_root = tmp_path / "paper-workspace"
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("missing runtime inspection must not spawn")),
    )

    result = module.inspect_workspace_python_environment(workspace_root=workspace_root)

    assert result["status"] == "workspace_python_missing"
    assert result["ready"] is False
    assert result["analysis_bundle"] is None
    assert not (workspace_root / ".venv").exists()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "uv sync" not in source.replace('"owner_surface": "uv sync"', "")
    assert not hasattr(module, "ensure_workspace_python_environment")
