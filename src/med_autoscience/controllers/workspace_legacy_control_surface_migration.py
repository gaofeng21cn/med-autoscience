from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from med_autoscience.profiles import load_profile


SURFACE_KIND = "workspace_legacy_control_surface_migration"
TOMBSTONE_SURFACE_KIND = "legacy_control_surface_tombstone"
MIGRATION_ROOT_RELPATH = Path("artifacts") / "runtime" / "legacy_control_surface_migration"
HISTORY_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "history"
ACTIVE_CONTROL_ROOTS = (
    Path("artifacts/supervision/hourly"),
    Path("artifacts/supervision/reconcile"),
    Path("artifacts/supervision/consumer"),
    Path("artifacts/supervision/install_proof"),
    Path("artifacts/supervision/scheduler"),
)
STUDY_CONTROL_ROOTS = (
    Path("artifacts/supervision/consumer"),
)
REQUEST_ROOT_RELPATH = Path("artifacts/supervision/requests")
CURRENT_CONTROL_STATE_RELPATH = Path("artifacts/supervision/opl_current_control_state/latest.json")
CONSUMER_LATEST_RELPATH = Path("artifacts/supervision/consumer/latest.json")
LEGACY_CONTROL_TOKENS = (
    "_".join(("runtime", "supervisor")),
    "-".join(("runtime", "supervisor")),
    " ".join(("runtime", "supervisor-")),
    "_".join(("portable", "runtime", "supervisor", "scan")),
    "_".join(("supervision", "scheduler")),
    "_".join(("mas", "supervision", "scheduler")),
    "supervisor-scan",
    "supervisor-consume",
    "supervisor-execute-dispatch",
    "watch-runtime",
    "study-runtime-status",
    "ensure-study-runtime",
)
TEXT_FILE_SUFFIXES = {
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".txt",
}
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


def run_workspace_legacy_control_surface_migration(*, profile_path: Path, apply: bool) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    workspace_root = profile.workspace_root.expanduser().resolve()
    recorded_at = _utc_now()
    stamp = _history_stamp(recorded_at)
    legacy_active_items = _legacy_active_items(workspace_root=workspace_root)
    request_refresh_items = _request_refresh_items(workspace_root=workspace_root, studies_root=profile.studies_root)
    request_retirement_items = _retirable_request_items(workspace_root=workspace_root, request_items=request_refresh_items)
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(workspace_root),
        "authority_boundary": {
            "legacy_control_artifact_migration": True,
            "paper_content_mutation": False,
            "publication_truth_mutation": False,
            "controller_decision_mutation": False,
            "runtime_queue_mutation": False,
            "medical_verdict_generation": False,
            "compatibility_alias_created": False,
        },
        "migration_policy": {
            "legacy_private_control_surfaces_after_migration": "provenance_only",
            "replacement_active_surfaces": [
                "artifacts/supervision/opl_current_control_state/latest.json",
                "artifacts/supervision/requests/**",
                "artifacts/supervision/consumer/default_executor_dispatches/*.json",
                "OPL provider/runtime manager current_control_state",
            ],
            "active_request_packets": (
                "archive_to_legacy_control_surface_migration_when_current_owner_route_or_dispatch_replaces_packet"
            ),
            "paper_work_unit_outbox": "retain_as_owner_receipt_provenance_and_ignore_legacy_private_control_receipts_for_duplicate_worker_start",
            "no_resurrection_policy": "do_not_restore_retired_private_control_or_local_scheduler_entrypoints",
        },
        "legacy_active_item_count": len(legacy_active_items),
        "legacy_active_items": legacy_active_items,
        "request_refresh_item_count": len(request_refresh_items),
        "request_refresh_items": request_refresh_items,
        "request_retirement_item_count": len(request_retirement_items),
        "request_retirement_items": request_retirement_items,
        "archive_root": str(workspace_root / HISTORY_ROOT_RELPATH / stamp),
        "latest_path": str(workspace_root / MIGRATION_ROOT_RELPATH / "latest.json"),
        "next_required_actions": _next_required_actions(
            legacy_active_items=legacy_active_items,
            request_refresh_items=request_refresh_items,
            request_retirement_items=request_retirement_items,
        ),
        "writes_performed": False,
    }
    if apply:
        migrated_items = [
            _archive_and_tombstone_item(
                workspace_root=workspace_root,
                item=item,
                recorded_at=recorded_at,
                stamp=stamp,
            )
            for item in [*legacy_active_items, *request_retirement_items]
        ]
        report["writes_performed"] = bool(migrated_items)
        report["migrated_items"] = migrated_items
        report["legacy_active_items_after_apply"] = _legacy_active_items(workspace_root=workspace_root)
        request_refresh_items_after_apply = _request_refresh_items(
            workspace_root=workspace_root,
            studies_root=profile.studies_root,
        )
        report["remaining_legacy_active_item_count"] = len(report["legacy_active_items_after_apply"])
        report["request_refresh_items_after_apply"] = request_refresh_items_after_apply
        report["remaining_request_refresh_item_count"] = len(request_refresh_items_after_apply)
        report["next_required_actions"] = _next_required_actions(
            legacy_active_items=report["legacy_active_items_after_apply"],
            request_refresh_items=request_refresh_items_after_apply,
            request_retirement_items=_retirable_request_items(
                workspace_root=workspace_root,
                request_items=request_refresh_items_after_apply,
            ),
        )
        _write_migration_report(report=report, workspace_root=workspace_root, recorded_at=recorded_at)
    return report


def _legacy_active_items(*, workspace_root: Path) -> list[dict[str, Any]]:
    roots = [workspace_root / relpath for relpath in ACTIVE_CONTROL_ROOTS]
    studies_root = workspace_root / "studies"
    if studies_root.is_dir():
        for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()):
            roots.extend(study_root / relpath for relpath in STUDY_CONTROL_ROOTS)
    items: list[dict[str, Any]] = []
    for path in _iter_files(roots=roots, workspace_root=workspace_root):
        content = _read_text(path)
        if content is None:
            continue
        matched = _matched_legacy_tokens(content)
        if not matched:
            continue
        items.append(
            {
                "path": str(path),
                "relpath": _relative_path(path, workspace_root).as_posix(),
                "candidate_action": "archive_to_legacy_control_surface_migration_and_leave_tombstone",
                "legacy_tokens": matched,
                "surface": _json_surface(path),
                "sha256": _sha256_text(content),
                "bytes": len(content.encode("utf-8")),
                "active_path_role": _active_path_role(path=path, workspace_root=workspace_root),
            }
        )
    return items


def _request_refresh_items(*, workspace_root: Path, studies_root: Path) -> list[dict[str, Any]]:
    roots: list[Path] = []
    if studies_root.is_dir():
        roots.extend(study_root / REQUEST_ROOT_RELPATH for study_root in sorted(studies_root.iterdir()) if study_root.is_dir())
    items: list[dict[str, Any]] = []
    for path in _iter_files(roots=roots, workspace_root=workspace_root):
        content = _read_text(path)
        if content is None:
            continue
        matched = _matched_legacy_tokens(content)
        if not matched:
            continue
        items.append(
            {
                "path": str(path),
                "relpath": _relative_path(path, workspace_root).as_posix(),
                "candidate_action": "archive_when_replaced_or_refresh_with_domain_action_request_materialize",
                "legacy_tokens": matched,
                "surface": _json_surface(path),
                "sha256": _sha256_text(content),
                "active_path_role": "domain_action_request_packet",
                "archive_by_this_migration": False,
            }
        )
    return items


def _retirable_request_items(
    *,
    workspace_root: Path,
    request_items: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in request_items:
        path = Path(str(item["path"])).expanduser().resolve()
        packet = _read_json_object(path)
        replacement = _request_replacement_evidence(workspace_root=workspace_root, request_path=path, packet=packet)
        if replacement is None:
            continue
        payload = dict(item)
        payload["candidate_action"] = "archive_replaced_domain_action_request_packet_and_leave_tombstone"
        payload["archive_by_this_migration"] = True
        payload["replacement_evidence"] = replacement
        items.append(payload)
    return items


def _request_replacement_evidence(
    *,
    workspace_root: Path,
    request_path: Path,
    packet: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    action_type = _text(_mapping(packet).get("request_kind")) or _text(_mapping(packet).get("action_type"))
    study_id = _text(_mapping(packet).get("study_id")) or _study_id_from_request_path(
        workspace_root=workspace_root,
        request_path=request_path,
    )
    if action_type is None or study_id is None:
        return None

    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    dispatch = _read_json_object(dispatch_path)
    if _is_current_dispatch(dispatch=dispatch, action_type=action_type, study_id=study_id):
        return {
            "kind": "current_default_executor_dispatch",
            "ref": _relative_path(dispatch_path, workspace_root).as_posix(),
            "dispatch_status": _text(_mapping(dispatch).get("dispatch_status")),
        }

    current_control = _read_json_object(workspace_root / CURRENT_CONTROL_STATE_RELPATH)
    if _current_control_state_has_action(current_control=current_control, action_type=action_type, study_id=study_id):
        return {
            "kind": "current_control_state_action",
            "ref": CURRENT_CONTROL_STATE_RELPATH.as_posix(),
        }

    consumer = _read_json_object(workspace_root / CONSUMER_LATEST_RELPATH)
    if _consumer_has_action(consumer=consumer, action_type=action_type, study_id=study_id):
        return {
            "kind": "domain_action_request_materializer_consumer",
            "ref": CONSUMER_LATEST_RELPATH.as_posix(),
        }
    return None


def _study_id_from_request_path(*, workspace_root: Path, request_path: Path) -> str | None:
    try:
        relpath = request_path.resolve().relative_to((workspace_root / "studies").resolve())
    except ValueError:
        return None
    if not relpath.parts:
        return None
    return relpath.parts[0]


def _is_current_dispatch(*, dispatch: Mapping[str, Any] | None, action_type: str, study_id: str) -> bool:
    if not dispatch:
        return False
    if _text(dispatch.get("surface")) != "default_executor_dispatch_request":
        return False
    if _text(dispatch.get("action_type")) != action_type:
        return False
    if _text(dispatch.get("study_id")) != study_id:
        return False
    return _text(dispatch.get("dispatch_status")) in {"ready", "blocked", "repeat_suppressed"}


def _current_control_state_has_action(
    *,
    current_control: Mapping[str, Any] | None,
    action_type: str,
    study_id: str,
) -> bool:
    if not current_control:
        return False
    if _text(current_control.get("surface")) not in {
        "opl_current_control_state_handoff",
        "portable_owner_route_reconcile",
    }:
        return False
    return _actions_include(current_control.get("action_queue"), action_type=action_type, study_id=study_id) or any(
        _text(_mapping(study).get("study_id")) == study_id
        and _actions_include(_mapping(study).get("action_queue"), action_type=action_type, study_id=study_id)
        for study in current_control.get("studies") or []
        if isinstance(study, Mapping)
    )


def _consumer_has_action(
    *,
    consumer: Mapping[str, Any] | None,
    action_type: str,
    study_id: str,
) -> bool:
    if not consumer:
        return False
    if _text(consumer.get("surface")) != "domain_action_request_materializer":
        return False
    return _actions_include(consumer.get("request_tasks"), action_type=action_type, study_id=study_id) or _actions_include(
        consumer.get("default_executor_dispatches"),
        action_type=action_type,
        study_id=study_id,
    )


def _actions_include(value: object, *, action_type: str, study_id: str) -> bool:
    if not isinstance(value, list):
        return False
    return any(
        isinstance(action, Mapping)
        and _text(action.get("action_type")) == action_type
        and _text(action.get("study_id")) == study_id
        for action in value
    )


def _archive_and_tombstone_item(
    *,
    workspace_root: Path,
    item: Mapping[str, Any],
    recorded_at: str,
    stamp: str,
) -> dict[str, Any]:
    source_path = Path(str(item["path"])).expanduser().resolve()
    relpath = Path(str(item["relpath"]))
    archive_path = workspace_root / HISTORY_ROOT_RELPATH / stamp / relpath
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.exists():
        shutil.move(str(source_path), str(archive_path))
    tombstone = _tombstone_payload(
        item=item,
        archive_ref=_relative_path(archive_path, workspace_root).as_posix(),
        recorded_at=recorded_at,
    )
    _write_tombstone(source_path, tombstone)
    return {
        "source_path": str(source_path),
        "source_relpath": relpath.as_posix(),
        "archive_path": str(archive_path),
        "archive_ref": _relative_path(archive_path, workspace_root).as_posix(),
        "tombstone_written": True,
    }


def _tombstone_payload(*, item: Mapping[str, Any], archive_ref: str, recorded_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": TOMBSTONE_SURFACE_KIND,
        "recorded_at": recorded_at,
        "status": "migrated_to_provenance",
        "original_relpath": str(item.get("relpath")),
        "archive_ref": archive_ref,
        "legacy_tokens_removed_from_active_path": True,
        "legacy_token_count": len(item.get("legacy_tokens") or []),
        "legacy_token_fingerprints": [_sha256_text(str(token)) for token in item.get("legacy_tokens") or []],
        "previous_sha256": item.get("sha256"),
        "active_replacement_owner": "one-person-lab",
        "active_path_role": item.get("active_path_role"),
        "replacement_evidence": dict(_mapping(item.get("replacement_evidence"))),
        "mas_active_replacement_refs": [
            "artifacts/supervision/opl_current_control_state/latest.json",
            "artifacts/supervision/requests/**",
            "artifacts/supervision/consumer/default_executor_dispatches/*.json",
        ],
        "authority_boundary": {
            "tombstone_is_executable": False,
            "runtime_control_owner": "one-person-lab",
            "mas_domain_truth_owner": "med-autoscience",
            "compatibility_alias_created": False,
            "publication_truth_mutation": False,
            "controller_decision_mutation": False,
            "paper_content_mutation": False,
        },
    }


def _write_tombstone(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".jsonl":
        path.write_text(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return
    path.write_text(_json_dumps(payload), encoding="utf-8")


def _write_migration_report(*, report: Mapping[str, Any], workspace_root: Path, recorded_at: str) -> None:
    root = workspace_root / MIGRATION_ROOT_RELPATH
    report_root = root / "reports"
    report_root.mkdir(parents=True, exist_ok=True)
    stamp = _history_stamp(recorded_at)
    report_path = report_root / f"{stamp}.json"
    latest_path = root / "latest.json"
    payload = dict(report)
    payload["report_path"] = str(report_path)
    payload["latest_path"] = str(latest_path)
    report_path.write_text(_json_dumps(payload), encoding="utf-8")
    latest_path.write_text(_json_dumps(payload), encoding="utf-8")


def _iter_files(*, roots: Iterable[Path], workspace_root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path in seen or not path.is_file():
                continue
            if _should_skip_path(path=path, workspace_root=workspace_root):
                continue
            if path.suffix.lower() not in TEXT_FILE_SUFFIXES:
                continue
            seen.add(path)
            yield path


def _should_skip_path(*, path: Path, workspace_root: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    if _path_is_under(path, workspace_root / MIGRATION_ROOT_RELPATH):
        return True
    if _path_is_under(path, workspace_root / "runtime" / "archives"):
        return True
    return False


def _active_path_role(*, path: Path, workspace_root: Path) -> str:
    relpath = _relative_path(path, workspace_root)
    parts = relpath.parts
    if parts[:3] == ("artifacts", "supervision", "hourly"):
        return "retired_workspace_scheduler_projection"
    if parts[:3] == ("artifacts", "supervision", "reconcile"):
        return "retired_runtime_reconcile_projection"
    if parts[:3] == ("artifacts", "supervision", "consumer"):
        return "retired_workspace_consumer_projection"
    if parts[:3] == ("artifacts", "supervision", "install_proof"):
        return "retired_local_scheduler_install_proof"
    if parts[:3] == ("artifacts", "supervision", "scheduler"):
        return "retired_local_scheduler_runtime_proof"
    if "default_executor_execution" in parts:
        return "retired_default_executor_execution_projection"
    if "default_executor_dispatches" in parts:
        return "retired_default_executor_dispatch_projection"
    if "consumer" in parts:
        return "retired_study_consumer_projection"
    return "legacy_control_surface_projection"


def _json_surface(path: Path) -> str | None:
    if path.suffix.lower() != ".json":
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return _text(payload.get("surface")) or _text(payload.get("surface_kind"))


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _matched_legacy_tokens(content: str) -> list[str]:
    return [token for token in LEGACY_CONTROL_TOKENS if token in content]


def _next_required_actions(
    *,
    legacy_active_items: list[Mapping[str, Any]],
    request_refresh_items: list[Mapping[str, Any]],
    request_retirement_items: list[Mapping[str, Any]],
) -> list[str]:
    actions: list[str] = []
    retirable_request_refs = {str(item.get("relpath")) for item in request_retirement_items}
    if legacy_active_items:
        actions.append("apply_workspace_legacy_control_surface_migration")
    if request_retirement_items:
        actions.append("apply_workspace_legacy_control_surface_migration_for_replaced_request_packets")
    if any(str(item.get("relpath")) not in retirable_request_refs for item in request_refresh_items):
        actions.append("run_domain_action_request_materialize_apply_to_refresh_request_packets")
    if not actions:
        actions.append("no_legacy_control_surface_migration_required")
    return actions


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
        return True
    except ValueError:
        return False


def _relative_path(path: Path, root: Path) -> Path:
    try:
        return path.expanduser().resolve().relative_to(root.expanduser().resolve())
    except ValueError:
        return path


def _sha256_text(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_stamp(recorded_at: str) -> str:
    return recorded_at.replace("+00:00", "Z").replace("+0000", "Z").replace("-", "").replace(":", "").replace(".", "")


def _json_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "LEGACY_CONTROL_TOKENS",
    "MIGRATION_ROOT_RELPATH",
    "SURFACE_KIND",
    "TOMBSTONE_SURFACE_KIND",
    "run_workspace_legacy_control_surface_migration",
]
