from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from .layout import build_workspace_runtime_layout

MaterializationMode = Literal["dry_run", "apply"]

MANIFEST_NAME = "materialization_manifest.json"
BLOCKED_STATES = frozenset({"live", "pinned"})


def materialize_quest_workspace(
    *,
    workspace_root: Path,
    quest_id: str,
    node_id: str,
    mode: MaterializationMode = "dry_run",
) -> dict[str, Any]:
    """Plan or create the non-git quest workspace directory contract."""
    if mode not in {"dry_run", "apply"}:
        raise ValueError("mode must be 'dry_run' or 'apply'")

    normalized_quest_id = _normalize_quest_id(quest_id)
    normalized_node_id = _normalize_node_id(node_id)
    layout = build_workspace_runtime_layout(workspace_root=Path(workspace_root))
    quest_root = layout.quest_root(normalized_quest_id)
    manifest_path = _manifest_path(quest_root)
    manifest = _build_manifest(
        workspace_root=layout.workspace_root,
        quest_root=quest_root,
        manifest_path=manifest_path,
        quest_id=normalized_quest_id,
        node_id=normalized_node_id,
        state="planned" if mode == "dry_run" else "materialized",
    )

    existing_state = _read_materialization_state(manifest_path)
    if existing_state in BLOCKED_STATES:
        return {
            "schema_version": 1,
            "status": "blocked",
            "action": "audit_only",
            "mode": mode,
            "quest_id": normalized_quest_id,
            "node_id": normalized_node_id,
            "target_path": str(quest_root),
            "manifest_path": str(manifest_path),
            "block_reason": f"quest_workspace_state_is_{existing_state}",
            "destructive_allowed": False,
            "manifest": manifest,
        }
    if (quest_root / ".git").exists():
        return {
            "schema_version": 1,
            "status": "blocked",
            "action": "audit_only",
            "mode": mode,
            "quest_id": normalized_quest_id,
            "node_id": normalized_node_id,
            "target_path": str(quest_root),
            "manifest_path": str(manifest_path),
            "block_reason": "quest_local_git_retired_policy_violation",
            "destructive_allowed": False,
            "manifest": manifest,
        }

    if mode == "dry_run":
        return {
            "schema_version": 1,
            "status": "planned",
            "action": "create_plain_directory",
            "mode": mode,
            "quest_id": normalized_quest_id,
            "node_id": normalized_node_id,
            "target_path": str(quest_root),
            "manifest_path": str(manifest_path),
            "destructive_allowed": False,
            "manifest": manifest,
        }

    quest_root.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(manifest_path, manifest)
    return {
        "schema_version": 1,
        "status": "materialized",
        "action": "create_plain_directory",
        "mode": mode,
        "quest_id": normalized_quest_id,
        "node_id": normalized_node_id,
        "target_path": str(quest_root),
        "manifest_path": str(manifest_path),
        "created_paths": [str(quest_root), str(manifest_path.parent), str(manifest_path)],
        "destructive_allowed": False,
        "manifest": manifest,
    }


def _build_manifest(
    *,
    workspace_root: Path,
    quest_root: Path,
    manifest_path: Path,
    quest_id: str,
    node_id: str,
    state: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "contract": "quest_plain_directory_materialization",
        "quest_id": quest_id,
        "node_id": node_id,
        "target_path": str(quest_root),
        "manifest_path": str(manifest_path),
        "materialization_state": state,
        "git_runtime_used": False,
        "quest_git_active_path_retired": True,
        "destructive_allowed": False,
        "legacy_sources": [
            {
                "kind": "legacy_quest_git_runtime",
                "path": str(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / quest_id),
                "access": "read_only",
            }
        ],
    }


def _manifest_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / MANIFEST_NAME


def _read_materialization_state(manifest_path: Path) -> str | None:
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    state = payload.get("materialization_state")
    return state if isinstance(state, str) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_quest_id(quest_id: str) -> str:
    if not quest_id:
        raise ValueError("quest_id is required")
    quest_path = Path(quest_id)
    if quest_path.is_absolute() or ".." in quest_path.parts or len(quest_path.parts) != 1:
        raise ValueError("quest_id must be a single relative path segment")
    return quest_id


def _normalize_node_id(node_id: str) -> str:
    if not node_id:
        raise ValueError("node_id is required")
    return node_id
