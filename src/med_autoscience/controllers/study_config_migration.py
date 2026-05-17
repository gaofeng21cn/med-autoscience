from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.profiles import WorkspaceProfile, load_profile


SURFACE_KIND = "study_config_clean_migration"
MIGRATION_ROOT_RELPATH = Path("artifacts") / "migration" / "study_config_clean_migration"
HISTORY_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "history"
_RETIRED_FIELD_PATH = "manual_finish.compatibility_guard_only"
_REPLACEMENT_FIELD_PATH = "manual_finish.manual_finish_guard_only"


def run_study_config_clean_migration(
    *,
    profile_path: Path,
    study_ids: Iterable[str] | None = None,
    apply: bool,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    selected_study_ids = _resolve_study_ids(profile=profile, study_ids=study_ids)
    recorded_at = _utc_now()
    studies = [
        _study_plan(profile=profile, study_id=study_id, recorded_at=recorded_at)
        for study_id in selected_study_ids
    ]
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "authority_boundary": {
            "legacy_reader_compatibility": False,
            "legacy_token_normalization": False,
            "paper_content_mutation": False,
            "runtime_truth_mutation": False,
            "study_config_mutation": bool(apply),
            "unknown_config_policy": "fail_closed_until_clean_migration",
        },
        "migration_policy": {
            "retired_fields_are_not_read_as_active_schema": True,
            "supported_migrations": [
                {
                    "retired_field_path": _RETIRED_FIELD_PATH,
                    "replacement_field_path": _REPLACEMENT_FIELD_PATH,
                }
            ],
        },
        "study_count": len(studies),
        "studies": studies,
        "next_required_actions": _workspace_next_actions(studies),
    }
    if apply:
        for study in studies:
            if study["migration_required"] and not study["blockers"]:
                _apply_study_config_migration(study_plan=study, recorded_at=recorded_at)
        report["studies"] = [
            _study_plan(profile=profile, study_id=study_id, recorded_at=recorded_at)
            for study_id in selected_study_ids
        ]
        report["next_required_actions"] = _workspace_next_actions(report["studies"])
        report["post_apply"] = {
            "remaining_migration_required_count": sum(
                1 for study in report["studies"] if study["migration_required"]
            ),
            "blocked_count": sum(1 for study in report["studies"] if study["blockers"]),
            "receipt_count": sum(1 for study in report["studies"] if study["migration_receipt"]["exists"]),
        }
    return report


def _resolve_study_ids(*, profile: WorkspaceProfile, study_ids: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(item for raw in (study_ids or ()) if (item := _text(raw)) is not None)
    if selected:
        available_study_ids = set(_discover_study_ids(profile))
        for study_id in selected:
            if study_id not in available_study_ids:
                known = ", ".join(sorted(available_study_ids)) or "<none>"
                raise ValueError(f"Unknown study config study_id: {study_id}; known study_ids: {known}")
        return selected
    return _discover_study_ids(profile)


def _discover_study_ids(profile: WorkspaceProfile) -> tuple[str, ...]:
    if not profile.studies_root.is_dir():
        return ()
    return tuple(
        path.name
        for path in sorted(profile.studies_root.iterdir())
        if path.is_dir() and (path / "study.yaml").exists()
    )


def _study_plan(*, profile: WorkspaceProfile, study_id: str, recorded_at: str) -> dict[str, Any]:
    study_root = (profile.studies_root / study_id).expanduser().resolve()
    study_yaml_path = study_root / "study.yaml"
    receipt_path = study_root / MIGRATION_ROOT_RELPATH / "latest.json"
    receipt = _read_json_object(receipt_path)
    field_migrations: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    if study_yaml_path.exists():
        analysis = _manual_finish_retired_field_analysis(study_yaml_path)
        field_migrations.extend(analysis["field_migrations"])
        blockers.extend(analysis["blockers"])
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "config_path": str(study_yaml_path),
        "config_exists": study_yaml_path.exists(),
        "migration_required": bool(field_migrations),
        "field_migrations": field_migrations,
        "blockers": blockers,
        "apply_allowed": bool(field_migrations) and not blockers,
        "migration_receipt": {
            "path": str(receipt_path),
            "exists": bool(receipt),
            "status": _text((receipt or {}).get("status")),
        },
        "archive_root": str(study_root / HISTORY_ROOT_RELPATH / _history_stamp(recorded_at)),
        "next_required_actions": _study_next_actions(
            field_migrations=field_migrations,
            blockers=blockers,
        ),
    }


def _manual_finish_retired_field_analysis(study_yaml_path: Path) -> dict[str, list[dict[str, Any]]]:
    text = study_yaml_path.read_text(encoding="utf-8")
    blockers: list[dict[str, Any]] = []
    field_migrations: list[dict[str, Any]] = []
    try:
        payload = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        return {
            "field_migrations": [],
            "blockers": [
                {
                    "field_path": _RETIRED_FIELD_PATH,
                    "reason": "study_yaml_parse_failed",
                    "detail": str(exc),
                }
            ],
        }
    if not isinstance(payload, dict):
        return {"field_migrations": [], "blockers": []}
    raw_manual_finish = payload.get("manual_finish")
    if not isinstance(raw_manual_finish, dict):
        return {"field_migrations": [], "blockers": []}
    if "compatibility_guard_only" not in raw_manual_finish:
        return {"field_migrations": [], "blockers": []}
    if "manual_finish_guard_only" in raw_manual_finish:
        blockers.append(
            {
                "field_path": _RETIRED_FIELD_PATH,
                "reason": "manual_finish_guard_key_conflict",
                "detail": "Both retired and replacement guard keys are present.",
            }
        )
    line_indices = _retired_manual_finish_line_indices(text)
    if len(line_indices) != 1:
        blockers.append(
            {
                "field_path": _RETIRED_FIELD_PATH,
                "reason": "manual_finish_retired_field_text_update_ambiguous",
                "match_count": len(line_indices),
            }
        )
    field_migrations.append(
        {
            "field_path": _RETIRED_FIELD_PATH,
            "replacement_field_path": _REPLACEMENT_FIELD_PATH,
            "value": raw_manual_finish.get("compatibility_guard_only"),
            "line": line_indices[0] + 1 if len(line_indices) == 1 else None,
            "candidate_action": "rename_retired_active_config_field",
        }
    )
    return {"field_migrations": field_migrations, "blockers": blockers}


def _retired_manual_finish_line_indices(text: str) -> list[int]:
    lines = text.splitlines(keepends=True)
    manual_finish_line: tuple[int, int] | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "manual_finish:":
            manual_finish_line = (index, _indent_width(line))
            break
    if manual_finish_line is None:
        return []
    start_index, manual_indent = manual_finish_line
    matches: list[int] = []
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = _indent_width(line)
        if indent <= manual_indent:
            break
        if stripped.startswith("compatibility_guard_only:"):
            matches.append(index)
    return matches


def _apply_study_config_migration(*, study_plan: Mapping[str, Any], recorded_at: str) -> None:
    study_root = Path(str(study_plan["study_root"])).expanduser().resolve()
    study_yaml_path = Path(str(study_plan["config_path"])).expanduser().resolve()
    before_text = study_yaml_path.read_text(encoding="utf-8")
    before_sha256 = _sha256_bytes(before_text.encode("utf-8"))
    updated_text = _rename_retired_manual_finish_key(before_text)
    if updated_text == before_text:
        raise ValueError(f"no study config migration delta for {study_yaml_path}")
    study_yaml_path.write_text(updated_text, encoding="utf-8")
    receipt = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": "applied",
        "recorded_at": recorded_at,
        "study_id": str(study_plan["study_id"]),
        "study_root": str(study_root),
        "config_path": str(study_yaml_path),
        "field_migrations": list(study_plan.get("field_migrations") or []),
        "authority_boundary": {
            "legacy_reader_compatibility": False,
            "legacy_token_normalization": False,
            "paper_content_mutation": False,
            "runtime_truth_mutation": False,
            "study_config_mutation": True,
            "reader_fail_closed_for_retired_field": True,
        },
        "fingerprints": {
            "before_sha256": before_sha256,
            "after_sha256": _sha256_bytes(updated_text.encode("utf-8")),
        },
    }
    _write_receipt(study_root=study_root, receipt=receipt, recorded_at=recorded_at)


def _rename_retired_manual_finish_key(text: str) -> str:
    lines = text.splitlines(keepends=True)
    indices = _retired_manual_finish_line_indices(text)
    if len(indices) != 1:
        raise ValueError("manual_finish retired field text update is ambiguous")
    index = indices[0]
    line = lines[index]
    stripped = line.lstrip(" \t")
    indent = line[: len(line) - len(stripped)]
    suffix = stripped[len("compatibility_guard_only:") :]
    lines[index] = f"{indent}manual_finish_guard_only:{suffix}"
    return "".join(lines)


def _write_receipt(*, study_root: Path, receipt: Mapping[str, Any], recorded_at: str) -> None:
    root = study_root / MIGRATION_ROOT_RELPATH
    history_root = study_root / HISTORY_ROOT_RELPATH
    history_root.mkdir(parents=True, exist_ok=True)
    history_path = history_root / f"{_history_stamp(recorded_at)}.json"
    latest_path = root / "latest.json"
    payload = {
        **dict(receipt),
        "latest_path": str(latest_path),
        "history_path": str(history_path),
    }
    history_path.write_text(_json_dumps(payload), encoding="utf-8")
    latest_path.write_text(_json_dumps(payload), encoding="utf-8")


def _study_next_actions(*, field_migrations: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> list[str]:
    if blockers:
        return ["resolve_study_config_migration_blocker"]
    if field_migrations:
        return ["apply_study_config_clean_migration"]
    return []


def _workspace_next_actions(studies: list[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    for study in studies:
        for action in study.get("next_required_actions") or []:
            if isinstance(action, str) and action not in actions:
                actions.append(action)
    return actions


def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _history_stamp(recorded_at: str) -> str:
    return recorded_at.replace("+00:00", "Z").replace("+0000", "Z").replace("-", "").replace(":", "").replace(".", "")


def _json_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["run_study_config_clean_migration"]
