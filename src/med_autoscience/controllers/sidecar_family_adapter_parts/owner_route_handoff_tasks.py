from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile


def owner_route_handoff_task(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    record = _mapping(study.get("owner_route_handoff"))
    handoff = _mapping(record.get("handoff"))
    if _text(handoff.get("recommended_task_kind")) != "domain_route/reconcile-apply":
        return None
    reason = _text(handoff.get("reason")) or _text(record.get("source")) or "owner_route_handoff"
    study_root = Path(_text(study.get("study_root")) or profile.studies_root / study_id)
    return {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/reconcile-apply",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "priority": 55,
        "source": "mas-sidecar-export",
        "requires_approval": False,
        "dedupe_key": f"mas:{profile.name}:{study_id}:owner-route-handoff:{reason}",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "reason": reason,
        "runtime_state_path": _text(handoff.get("runtime_state_path")),
        "owner_route_refs": ["mas_runtime_owner_route_handoff"],
        "opl_runtime_owner_route_handoff": handoff,
        "source_refs": [
            ref
            for ref in (
                _source_ref(
                    study_root=study_root,
                    role="owner_route_handoff",
                    relative_path=Path("artifacts/supervision/owner_route_handoff/latest.json"),
                    workspace_root=profile.workspace_root,
                ),
            )
            if ref["exists"]
        ],
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "continuation_reason": reason,
            "authority_boundary": "mas_owner_reconcile_only",
            "owner_route_handoff_ref": _workspace_relative(
                study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json",
                workspace_root=profile.workspace_root,
            ),
        },
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {
        "ref_kind": "repo_path",
        "role": role,
        "ref": _workspace_relative(path, workspace_root=workspace_root),
        "exists": path.exists(),
    }


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


__all__ = ["owner_route_handoff_task"]
