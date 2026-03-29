from __future__ import annotations

import importlib
from pathlib import Path


def test_detect_tooluniverse_prefers_explicit_root_and_reports_roles(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.tooluniverse")
    tooluniverse_root = tmp_path / "ToolUniverse"
    tooluniverse_root.mkdir(parents=True, exist_ok=True)
    (tooluniverse_root / "pyproject.toml").write_text("[project]\nname='tooluniverse'\n", encoding="utf-8")

    monkeypatch.setattr(module, "which", lambda command: f"/usr/local/bin/{command}")

    result = module.detect_tooluniverse(tooluniverse_root=tooluniverse_root)

    assert result["available"] is True
    assert result["root"] == str(tooluniverse_root)
    assert result["commands"]["tooluniverse"] == "/usr/local/bin/tooluniverse"
    assert "知识检索" in result["roles"]
    assert "功能分析" in result["roles"]


def test_detect_tooluniverse_reports_missing_when_no_root_and_commands_absent(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.tooluniverse")

    monkeypatch.setattr(module, "which", lambda command: None)

    result = module.detect_tooluniverse(workspace_root=tmp_path / "workspace")

    assert result["available"] is False
    assert result["root"] is None
    assert result["commands"]["tooluniverse"] is None
