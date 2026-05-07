from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path


def _guard_git_subprocess(monkeypatch) -> list[tuple[str, tuple[object, ...], dict[str, object]]]:
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def fail(name: str):
        def _inner(*args, **kwargs):
            calls.append((name, args, kwargs))
            raise AssertionError(f"quest materializer must not call subprocess.{name}")

        return _inner

    monkeypatch.setattr(subprocess, "run", fail("run"))
    monkeypatch.setattr(subprocess, "check_call", fail("check_call"))
    monkeypatch.setattr(subprocess, "check_output", fail("check_output"))
    monkeypatch.setattr(subprocess, "Popen", fail("Popen"))
    return calls


def test_dry_run_returns_plain_directory_materialization_plan_without_git(tmp_path: Path, monkeypatch) -> None:
    calls = _guard_git_subprocess(monkeypatch)
    module = importlib.import_module("med_autoscience.runtime_protocol.quest_materializer")
    workspace_root = tmp_path / "workspace"

    result = module.materialize_quest_workspace(
        workspace_root=workspace_root,
        quest_id="quest-001",
        node_id="node-a",
    )

    target_path = workspace_root / "runtime" / "quests" / "quest-001"
    manifest_path = target_path / "artifacts" / "runtime" / "materialization_manifest.json"
    assert result["status"] == "planned"
    assert result["action"] == "create_plain_directory"
    assert result["mode"] == "dry_run"
    assert result["target_path"] == str(target_path)
    assert result["manifest_path"] == str(manifest_path)
    assert result["manifest"]["git_runtime_used"] is False
    assert result["manifest"]["quest_git_active_path_retired"] is True
    assert result["manifest"]["legacy_sources"] == [
        {
            "kind": "legacy_quest_git_runtime",
            "path": str(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"),
            "access": "read_only",
        }
    ]
    assert not workspace_root.exists()
    assert calls == []


def test_apply_creates_plain_quest_directory_and_manifest_without_dot_git(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls = _guard_git_subprocess(monkeypatch)
    module = importlib.import_module("med_autoscience.runtime_protocol.quest_materializer")
    workspace_root = tmp_path / "workspace"

    result = module.materialize_quest_workspace(
        workspace_root=workspace_root,
        quest_id="quest-001",
        node_id="node-a",
        mode="apply",
    )

    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    manifest_path = quest_root / "artifacts" / "runtime" / "materialization_manifest.json"
    assert result["status"] == "materialized"
    assert result["created_paths"] == [str(quest_root), str(manifest_path.parent), str(manifest_path)]
    assert quest_root.is_dir()
    assert manifest_path.is_file()
    assert not (quest_root / ".git").exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["quest_id"] == "quest-001"
    assert manifest["node_id"] == "node-a"
    assert manifest["target_path"] == str(quest_root)
    assert manifest["git_runtime_used"] is False
    assert manifest["quest_git_active_path_retired"] is True
    assert manifest["materialization_state"] == "materialized"
    assert manifest["legacy_sources"][0]["access"] == "read_only"
    assert calls == []


def test_apply_blocks_existing_quest_local_git_surface(tmp_path: Path, monkeypatch) -> None:
    calls = _guard_git_subprocess(monkeypatch)
    module = importlib.import_module("med_autoscience.runtime_protocol.quest_materializer")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    quest_git = quest_root / ".git"
    quest_git.mkdir(parents=True)

    result = module.materialize_quest_workspace(
        workspace_root=workspace_root,
        quest_id="quest-001",
        node_id="node-a",
        mode="apply",
    )

    manifest_path = quest_root / "artifacts" / "runtime" / "materialization_manifest.json"
    assert result["status"] == "blocked"
    assert result["action"] == "audit_only"
    assert result["block_reason"] == "quest_local_git_retired_policy_violation"
    assert result["destructive_allowed"] is False
    assert quest_git.is_dir()
    assert not manifest_path.exists()
    assert calls == []


def test_apply_is_audit_only_for_live_materialized_workspace(tmp_path: Path, monkeypatch) -> None:
    calls = _guard_git_subprocess(monkeypatch)
    module = importlib.import_module("med_autoscience.runtime_protocol.quest_materializer")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    manifest_path = quest_root / "artifacts" / "runtime" / "materialization_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"schema_version": 1, "materialization_state": "live"}, indent=2) + "\n",
        encoding="utf-8",
    )

    result = module.materialize_quest_workspace(
        workspace_root=workspace_root,
        quest_id="quest-001",
        node_id="node-a",
        mode="apply",
    )

    assert result["status"] == "blocked"
    assert result["action"] == "audit_only"
    assert result["block_reason"] == "quest_workspace_state_is_live"
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["materialization_state"] == "live"
    assert calls == []


def test_apply_is_audit_only_for_pinned_materialized_workspace(tmp_path: Path, monkeypatch) -> None:
    calls = _guard_git_subprocess(monkeypatch)
    module = importlib.import_module("med_autoscience.runtime_protocol.quest_materializer")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    manifest_path = quest_root / "artifacts" / "runtime" / "materialization_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"schema_version": 1, "materialization_state": "pinned"}, indent=2) + "\n",
        encoding="utf-8",
    )

    result = module.materialize_quest_workspace(
        workspace_root=workspace_root,
        quest_id="quest-001",
        node_id="node-a",
        mode="apply",
    )

    assert result["status"] == "blocked"
    assert result["action"] == "audit_only"
    assert result["block_reason"] == "quest_workspace_state_is_pinned"
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["materialization_state"] == "pinned"
    assert calls == []
