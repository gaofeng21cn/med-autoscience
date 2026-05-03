from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "artifact_retention_operations_plan"
ALLOWED_PHYSICAL_ACTIONS = ("delete-safe-cache",)
_KEEP_ONLINE_ROLES = frozenset(
    {
        "canonical_source",
        "data_release",
        "audit_log",
        "human_handoff_mirror",
    }
)


def build_artifact_retention_operations_plan(
    *,
    workspace_root: Path,
    artifacts: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    operations = [
        _retention_operation(workspace_root=resolved_workspace_root, artifact=dict(artifact))
        for artifact in artifacts
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "workspace_root": str(resolved_workspace_root),
        "mutation_policy": {
            "read_only": True,
            "writes_workspace": False,
            "physical_cleanup_performed": False,
            "allowed_physical_actions": list(ALLOWED_PHYSICAL_ACTIONS),
            "archive_compress_apply_supported": False,
        },
        "summary": _summary(operations),
        "operations": operations,
    }


def _retention_operation(*, workspace_root: Path, artifact: Mapping[str, Any]) -> dict[str, Any]:
    role = _text(artifact.get("role"))
    lifecycle = _text(artifact.get("lifecycle"))
    cleanup_candidate_action = _text(artifact.get("cleanup_candidate_action") or artifact.get("cleanup_candidate"))
    blockers = _string_list(artifact.get("cleanup_blockers"))
    base = {
        "path": _artifact_path(artifact),
        "workspace_relative_path": _workspace_relative_path(artifact, workspace_root),
        "role": role,
        "lifecycle": lifecycle,
        "cleanup_candidate_action": cleanup_candidate_action,
        "blockers": blockers,
        "physical_delete_allowed": False,
        "physical_archive_compress_allowed": False,
        "canonical_regeneration_gate": {"required": False, "status": "not_required"},
        "restore_contract_gate": {"required": False, "status": "not_required"},
        "projection_status": "not_projection",
        "runtime_retention_mode": "not_runtime",
    }
    if cleanup_candidate_action == "delete-safe-cache":
        return {
            **base,
            "retention_action": "delete_safe_cache",
            "physical_delete_allowed": True,
        }
    if role in _KEEP_ONLINE_ROLES or cleanup_candidate_action == "keep-online":
        return {
            **base,
            "retention_action": "keep_online",
        }
    if role == "derived_projection" or lifecycle == "rebuildable_projection":
        return {
            **base,
            "retention_action": "regenerate_projection_then_remove_stale",
            "projection_status": "stale_or_rebuildable_projection",
            "canonical_regeneration_gate": {
                "required": True,
                "status": "required_before_physical_removal",
            },
            "blockers": _dedupe(
                [
                    *blockers,
                    "canonical_regeneration_required_before_projection_removal",
                ]
            ),
        }
    if role == "runtime_ephemeral" and cleanup_candidate_action == "archive-compress":
        return {
            **base,
            "retention_action": "archive_compress_candidate_blocked",
            "runtime_retention_mode": "terminal_archive_compress_candidate",
            "restore_contract_gate": {
                "required": True,
                "status": "apply_implementation_required",
            },
            "blockers": _dedupe(
                [
                    *blockers,
                    "physical_archive_compress_not_open",
                    "restore_contract_apply_implementation_required",
                ]
            ),
        }
    if role == "runtime_ephemeral":
        return {
            **base,
            "retention_action": "keep_online",
            "runtime_retention_mode": "audit_only",
        }
    if role == "cold_archive" or cleanup_candidate_action == "restore-gated":
        return {
            **base,
            "retention_action": "restore_contract_required",
            "restore_contract_gate": {
                "required": True,
                "status": "required_before_cleanup",
            },
        }
    return {
        **base,
        "retention_action": "keep_online",
    }


def _summary(operations: list[Mapping[str, Any]]) -> dict[str, Any]:
    action_counts = Counter(str(operation.get("retention_action") or "") for operation in operations)
    applyable_action_counts = Counter(
        str(operation.get("retention_action") or "")
        for operation in operations
        if bool(operation.get("physical_delete_allowed"))
    )
    return {
        "operation_count": len(operations),
        "action_counts": dict(sorted(action_counts.items())),
        "applyable_action_counts": dict(sorted(applyable_action_counts.items())),
    }


def _artifact_path(artifact: Mapping[str, Any]) -> str:
    raw_path = _text(artifact.get("path"))
    return raw_path


def _workspace_relative_path(artifact: Mapping[str, Any], workspace_root: Path) -> str:
    raw_relative = _text(artifact.get("workspace_relative_path"))
    if raw_relative:
        return raw_relative
    raw_path = _text(artifact.get("path"))
    if not raw_path:
        return ""
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(workspace_root))
        except ValueError:
            return str(path)
    return str(path)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


__all__ = [
    "ALLOWED_PHYSICAL_ACTIONS",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_artifact_retention_operations_plan",
]
