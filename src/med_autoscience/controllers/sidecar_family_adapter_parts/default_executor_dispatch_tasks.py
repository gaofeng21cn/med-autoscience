from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile


TASK_KIND = "domain_owner/default-executor-dispatch"
DISPATCH_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_dispatches")
REQUIRED_SURFACE = "default_executor_dispatch_request"
REQUIRED_EXECUTOR_KIND = "codex_cli_default"
REQUIRED_NEXT_OWNER = "write"


def default_executor_dispatch_tasks(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    dispatch_root = profile.studies_root / study_id / DISPATCH_RELATIVE_ROOT
    if not dispatch_root.is_dir():
        return []
    tasks: list[dict[str, Any]] = []
    for dispatch_path in sorted(dispatch_root.glob("*.json")):
        dispatch = _read_json_object(dispatch_path)
        if not _dispatch_ready_for_opl_attempt(dispatch):
            continue
        action_type = _text(dispatch.get("action_type"))
        if action_type is None:
            continue
        dispatch_authority = _text(dispatch.get("dispatch_authority")) or "consumer_default_executor_dispatch"
        dispatch_ref = _workspace_relative(dispatch_path, workspace_root=profile.workspace_root)
        prompt_contract_ref = f"{dispatch_ref}#prompt_contract"
        quest_id = _text(dispatch.get("quest_id")) or study_id
        next_owner = _text(dispatch.get("next_executable_owner")) or REQUIRED_NEXT_OWNER
        executor_kind = _text(dispatch.get("executor_kind")) or REQUIRED_EXECUTOR_KIND
        source_fingerprint = _source_fingerprint(dispatch=dispatch, dispatch_path=dispatch_path)
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": TASK_KIND,
                "priority": 65,
                "source": "mas-sidecar-export",
                "requires_approval": False,
                "dedupe_key": (
                    f"mas:{profile.name}:{study_id}:default-executor:"
                    f"{action_type}:{dispatch_authority}"
                ),
                "source_fingerprint": source_fingerprint,
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": action_type,
                    "dispatch_authority": dispatch_authority,
                    "next_executable_owner": next_owner,
                    "executor_kind": executor_kind,
                    "dispatch_ref": dispatch_ref,
                    "authority_boundary": "mas_default_executor_dispatch_request_only",
                },
                "source_refs": [
                    {
                        "role": "default_executor_dispatch_request",
                        "ref": dispatch_ref,
                        "exists": True,
                        "body_included": False,
                    },
                    {
                        "role": "default_executor_prompt_contract",
                        "ref": prompt_contract_ref,
                        "exists": True,
                        "body_included": False,
                    },
                ],
                "dispatch_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "queue_owner": "one-person-lab",
                "profile_name": profile.name,
            }
        )
    return tasks


def _dispatch_ready_for_opl_attempt(dispatch: Mapping[str, Any] | None) -> bool:
    if dispatch is None:
        return False
    return (
        _text(dispatch.get("surface")) == REQUIRED_SURFACE
        and _text(dispatch.get("dispatch_status")) == "ready"
        and _text(dispatch.get("executor_kind")) == REQUIRED_EXECUTOR_KIND
        and _text(dispatch.get("next_executable_owner")) == REQUIRED_NEXT_OWNER
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _source_fingerprint(*, dispatch: Mapping[str, Any], dispatch_path: Path) -> str:
    digest_payload = {
        "path": str(dispatch_path),
        "idempotency_key": _text(dispatch.get("idempotency_key")),
        "action_type": _text(dispatch.get("action_type")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        "owner_route_fingerprint": _text(_mapping(dispatch.get("owner_route")).get("work_unit_fingerprint")),
        "file_digest": hashlib.sha256(dispatch_path.read_bytes()).hexdigest(),
    }
    rendered = json.dumps(digest_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["TASK_KIND", "default_executor_dispatch_tasks"]
