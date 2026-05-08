from __future__ import annotations

import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from med_autoscience.controllers import workspace_entry_rendering as workspace_entry_rendering_controller
from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.runtime_backend import DEFAULT_MANAGED_RUNTIME_BACKEND_ID, engine_id_for_backend_id
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout


SURFACE_KIND = "workspace_monolith_migration"
MIGRATION_ROOT_RELPATH = Path("artifacts") / "runtime" / "monolith_migration"
PARKED_RUNTIME_STATUSES = {
    "completed",
    "manual_hold",
    "paused",
    "parked",
    "stopped",
    "waiting_for_user",
    "awaiting_user_wakeup",
    "package_ready_handoff",
}
LIVE_RUNTIME_STATUSES = {"active", "running", "live"}


def run_workspace_monolith_migration(*, profile_path: Path, apply: bool) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    workspace_root = profile.workspace_root.expanduser().resolve()
    target_layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    source_runtime_root = _legacy_runtime_root(profile=profile, target_runtime_home=target_layout.runtime_root)
    source_quests_root = source_runtime_root / "quests"
    target_runtime_home = target_layout.runtime_root
    target_quests_root = target_layout.quests_root
    recorded_at = _utc_now()

    inventory = _build_inventory(
        profile=profile,
        source_quests_root=source_quests_root,
        target_quests_root=target_quests_root,
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(workspace_root),
        "source_topology": {
            "runtime_home": str(source_runtime_root),
            "runtime_quests_root": str(source_quests_root),
            "semantic_role": "legacy_diagnostic.read_only",
        },
        "target_topology": {
            "runtime_home": str(target_runtime_home),
            "runtime_quests_root": str(target_quests_root),
            "runtime_os": "MAS Runtime OS",
        },
        "migrated": inventory["migrated"],
        "skipped": inventory["skipped"],
        "orphan": inventory["orphan"],
        "duplicate": inventory["duplicate"],
        "quest_mapping": inventory["quest_mapping"],
        "archive_refs": inventory["archive_refs"],
        "restore_proofs": inventory["restore_proofs"],
        "hardcoded_study_id_policy": {
            "dynamic_discovery_only": True,
            "study_selection_source": "profile.studies_root and runtime quest metadata",
        },
        "mutation_policy": {
            "paper_package_mutation": False,
            "publication_gate_mutation": False,
            "live_study_auto_wakeup": False,
        },
    }
    if apply:
        _apply_migration(
            profile=profile,
            profile_path=resolved_profile_path,
            report=report,
            target_runtime_home=target_runtime_home,
            target_quests_root=target_quests_root,
            source_runtime_root=source_runtime_root,
        )
    return report


def _build_inventory(
    *,
    profile: WorkspaceProfile,
    source_quests_root: Path,
    target_quests_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    studies = _discover_studies(profile.studies_root)
    quests = _discover_quests(source_quests_root=source_quests_root, target_quests_root=target_quests_root)
    quest_ids_by_study_id: dict[str, list[str]] = {}
    for quest_id, quest in quests.items():
        study_id = _text(quest.get("study_id"))
        if study_id:
            quest_ids_by_study_id.setdefault(study_id, []).append(quest_id)

    migrated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    duplicate: list[dict[str, Any]] = []
    quest_mapping: list[dict[str, Any]] = []
    archive_refs: list[dict[str, Any]] = []
    restore_proofs: list[dict[str, Any]] = []

    for study_id, study in sorted(studies.items()):
        binding_quest_id = _text(study["binding"].get("quest_id"))
        candidate_ids = sorted(set([item for item in quest_ids_by_study_id.get(study_id, []) if item] + ([binding_quest_id] if binding_quest_id else [])))
        if len(candidate_ids) > 1:
            duplicate.append(
                {
                    "study_id": study_id,
                    "study_root": str(study["study_root"]),
                    "quest_ids": candidate_ids,
                    "reason": "multiple_quest_roots_for_study",
                }
            )
            continue
        if not candidate_ids:
            skipped.append(
                {
                    "study_id": study_id,
                    "study_root": str(study["study_root"]),
                    "reason": "missing_runtime_binding_quest",
                }
            )
            continue
        quest_id = candidate_ids[0]
        quest = quests.get(quest_id)
        if quest is None:
            skipped.append(
                {
                    "study_id": study_id,
                    "study_root": str(study["study_root"]),
                    "quest_id": quest_id,
                    "reason": "quest_root_missing",
                }
            )
            continue
        old_quest_root = Path(quest["quest_root"])
        new_quest_root = target_quests_root / quest_id
        runtime_state = quest["runtime_state"] if isinstance(quest.get("runtime_state"), dict) else {}
        status = _runtime_status(runtime_state)
        active_run_id = _text(runtime_state.get("active_run_id"))
        worker_running = runtime_state.get("worker_running")
        if active_run_id or worker_running is True or status in LIVE_RUNTIME_STATUSES:
            skipped.append(
                {
                    "study_id": study_id,
                    "study_root": str(study["study_root"]),
                    "quest_id": quest_id,
                    "old_quest_root": str(old_quest_root),
                    "new_quest_root": str(new_quest_root),
                    "reason": "live_study_requires_controller_pause_quiesce_relaunch",
                    "next_required_action": "controller_pause_quiesce_relaunch",
                    "checkpoint_only": True,
                    "active_run_id": active_run_id,
                    "runtime_status": status,
                }
            )
            continue
        if status not in PARKED_RUNTIME_STATUSES:
            skipped.append(
                {
                    "study_id": study_id,
                    "study_root": str(study["study_root"]),
                    "quest_id": quest_id,
                    "old_quest_root": str(old_quest_root),
                    "new_quest_root": str(new_quest_root),
                    "reason": "runtime_state_not_safe_for_binding_migration",
                    "runtime_status": status,
                }
            )
            continue
        entry = {
            "study_id": study_id,
            "study_root": str(study["study_root"]),
            "quest_id": quest_id,
            "old_runtime_root": str(source_quests_root.parent),
            "new_runtime_root": str(target_quests_root.parent),
            "old_quest_root": str(old_quest_root),
            "new_quest_root": str(new_quest_root),
            "reason": "legacy_binding_to_mas_runtime_os",
            "runtime_status": status,
            "auto_wakeup": False,
        }
        migrated.append(entry)
        quest_mapping.append(entry)
        _collect_restore_and_archive_refs(
            study_id=study_id,
            quest_id=quest_id,
            quest_root=old_quest_root,
            archive_refs=archive_refs,
            restore_proofs=restore_proofs,
        )

    known_study_ids = set(studies)
    orphan = [
        {
            "quest_id": quest_id,
            "quest_root": str(quest["quest_root"]),
            "declared_study_id": _text(quest.get("study_id")),
            "reason": "quest_has_no_matching_profile_study",
        }
        for quest_id, quest in sorted(quests.items())
        if _text(quest.get("study_id")) not in known_study_ids
    ]
    return {
        "migrated": migrated,
        "skipped": skipped,
        "orphan": orphan,
        "duplicate": duplicate,
        "quest_mapping": quest_mapping,
        "archive_refs": archive_refs,
        "restore_proofs": restore_proofs,
    }


def _apply_migration(
    *,
    profile: WorkspaceProfile,
    profile_path: Path,
    report: dict[str, Any],
    target_runtime_home: Path,
    target_quests_root: Path,
    source_runtime_root: Path,
) -> None:
    target_runtime_home.mkdir(parents=True, exist_ok=True)
    target_quests_root.mkdir(parents=True, exist_ok=True)
    _write_profile_runtime_projection(
        profile_path=profile_path,
        profile=profile,
        target_runtime_home=target_runtime_home,
        target_quests_root=target_quests_root,
        source_runtime_root=source_runtime_root,
    )
    _write_runtime_configs(profile=profile, profile_path=profile_path)
    for item in report["migrated"]:
        _write_runtime_binding_for_item(
            item=item,
            target_runtime_home=target_runtime_home,
            target_quests_root=target_quests_root,
            source_runtime_root=source_runtime_root,
            recorded_at=str(report["recorded_at"]),
        )
    _write_migration_report(report=report, workspace_root=profile.workspace_root)


def _write_profile_runtime_projection(
    *,
    profile_path: Path,
    profile: WorkspaceProfile,
    target_runtime_home: Path,
    target_quests_root: Path,
    source_runtime_root: Path,
) -> None:
    payload = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    text = profile_path.read_text(encoding="utf-8")
    replacements = {
        "runtime_root": str(target_quests_root),
        "managed_runtime_home": str(target_runtime_home),
    }
    for key, value in replacements.items():
        text = _upsert_top_level_toml_string(text, key, value)
    text = _remove_top_level_toml_key(text, "med_deepscientist_runtime_root")
    text = _remove_top_level_toml_key(text, "med_deepscientist_repo_root")
    legacy = payload.get("legacy_diagnostic")
    legacy_payload = dict(legacy) if isinstance(legacy, dict) else {}
    legacy_payload.update(
        {
            "runtime_root": str(source_runtime_root),
            "med_deepscientist_runtime_root": str(source_runtime_root),
            "read_only": True,
            "restore_provenance_ref": "artifacts/runtime/monolith_migration/latest.json",
        }
    )
    if profile.med_deepscientist_repo_root is not None:
        legacy_payload["controlled_backend_repo_root"] = str(profile.med_deepscientist_repo_root)
    text = _replace_table(text, "legacy_diagnostic", legacy_payload)
    profile_path.write_text(text if text.endswith("\n") else f"{text}\n", encoding="utf-8")


def _write_runtime_configs(*, profile: WorkspaceProfile, profile_path: Path) -> None:
    workspace_root = profile.workspace_root
    profile_relpath = _relative_or_absolute(profile_path, workspace_root)
    med_config_path = workspace_root / "ops" / "medautoscience" / "config.env"
    med_config_path.parent.mkdir(parents=True, exist_ok=True)
    med_config_path.write_text(
        workspace_entry_rendering_controller.render_medautoscience_config(
            workspace_root=workspace_root,
            profile_relpath=profile_relpath,
        ),
        encoding="utf-8",
    )
    mas_config_path = workspace_root / "ops" / "mas" / "config.env"
    mas_config_path.parent.mkdir(parents=True, exist_ok=True)
    mas_config_path.write_text(
        workspace_entry_rendering_controller.render_mas_runtime_bridge_config(),
        encoding="utf-8",
    )


def _relative_or_absolute(path: Path, workspace_root: Path) -> Path:
    try:
        return path.relative_to(workspace_root)
    except ValueError:
        return path


def _write_runtime_binding_for_item(
    *,
    item: Mapping[str, Any],
    target_runtime_home: Path,
    target_quests_root: Path,
    source_runtime_root: Path,
    recorded_at: str,
) -> None:
    study_root = Path(str(item["study_root"]))
    quest_id = str(item["quest_id"])
    binding_path = study_root / "runtime_binding.yaml"
    previous = _read_yaml_mapping(binding_path)
    payload = {
        **previous,
        "schema_version": 1,
        "engine": engine_id_for_backend_id(DEFAULT_MANAGED_RUNTIME_BACKEND_ID),
        "runtime_backend_id": DEFAULT_MANAGED_RUNTIME_BACKEND_ID,
        "runtime_backend": DEFAULT_MANAGED_RUNTIME_BACKEND_ID,
        "runtime_engine_id": engine_id_for_backend_id(DEFAULT_MANAGED_RUNTIME_BACKEND_ID),
        "runtime_home": str(target_runtime_home),
        "study_id": str(item["study_id"]),
        "study_root": str(study_root),
        "quest_id": quest_id,
        "runtime_root": str(target_quests_root),
        "runtime_quests_root": str(target_quests_root),
        "legacy_diagnostic": {
            "med_deepscientist_runtime_root": str(source_runtime_root),
            "old_quest_root": str(item["old_quest_root"]),
            "restore_provenance_ref": "artifacts/runtime/monolith_migration/latest.json",
            "read_only": True,
        },
        "last_action": "workspace_monolith_migrate",
        "last_action_at": recorded_at,
        "last_source": "medautosci runtime workspace-monolith-migrate",
    }
    _write_yaml(binding_path, payload)


def _write_migration_report(*, report: dict[str, Any], workspace_root: Path) -> None:
    root = workspace_root / MIGRATION_ROOT_RELPATH
    history_root = root / "history"
    history_root.mkdir(parents=True, exist_ok=True)
    stamp = _history_stamp(str(report["recorded_at"]))
    history_path = history_root / f"{stamp}.json"
    latest_path = root / "latest.json"
    report["history_path"] = str(history_path)
    report["latest_path"] = str(latest_path)
    _write_json(history_path, report)
    _write_json(latest_path, report)


def _discover_studies(studies_root: Path) -> dict[str, dict[str, Any]]:
    if not studies_root.exists():
        return {}
    studies: dict[str, dict[str, Any]] = {}
    for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()):
        if not (study_root / "study.yaml").exists() and not (study_root / "runtime_binding.yaml").exists():
            continue
        binding = _read_yaml_mapping(study_root / "runtime_binding.yaml")
        study_payload = _read_yaml_mapping(study_root / "study.yaml")
        study_id = _text(binding.get("study_id")) or _text(study_payload.get("study_id")) or study_root.name
        studies[study_id] = {"study_root": study_root.resolve(), "binding": binding, "study": study_payload}
    return studies


def _discover_quests(*, source_quests_root: Path, target_quests_root: Path) -> dict[str, dict[str, Any]]:
    quests: dict[str, dict[str, Any]] = {}
    for root in (source_quests_root, target_quests_root):
        if not root.exists():
            continue
        for quest_root in sorted(path for path in root.iterdir() if path.is_dir()):
            payload = _read_yaml_mapping(quest_root / "quest.yaml")
            runtime_state = _read_json_mapping(quest_root / ".ds" / "runtime_state.json")
            quest_id = _text(payload.get("quest_id")) or _text(runtime_state.get("quest_id")) or quest_root.name
            existing = quests.get(quest_id)
            if existing is not None and str(existing.get("quest_root")) != str(quest_root.resolve()):
                continue
            quests[quest_id] = {
                "quest_id": quest_id,
                "study_id": _text(payload.get("study_id")) or _text(runtime_state.get("study_id")),
                "quest_root": quest_root.resolve(),
                "runtime_state": runtime_state,
                "source": "target" if root == target_quests_root else "legacy",
            }
    return quests


def _collect_restore_and_archive_refs(
    *,
    study_id: str,
    quest_id: str,
    quest_root: Path,
    archive_refs: list[dict[str, Any]],
    restore_proofs: list[dict[str, Any]],
) -> None:
    proof_root = quest_root / ".ds" / "cold_archive" / "restore_proof_compaction"
    if not proof_root.exists():
        return
    for proof_path in sorted(proof_root.glob("*.restore_proof.json")):
        payload = _read_json_mapping(proof_path)
        restore_proofs.append(
            {
                "study_id": study_id,
                "quest_id": quest_id,
                "restore_proof_path": str(proof_path.resolve()),
                "status": _text(payload.get("status")) or "unknown",
                "archive_sha256": _text(payload.get("archive_sha256")),
                "source_file_count": payload.get("source_file_count"),
                "verified_file_count": payload.get("verified_file_count"),
            }
        )
    for archive_path in sorted(proof_root.glob("*.tar.gz")):
        archive_refs.append(
            {
                "study_id": study_id,
                "quest_id": quest_id,
                "archive_path": str(archive_path.resolve()),
                "restore_proof_ref": str((proof_root / f"{quest_id}.restore_proof.json").resolve()),
            }
        )


def _legacy_runtime_root(*, profile: WorkspaceProfile, target_runtime_home: Path) -> Path:
    legacy = profile.med_deepscientist_runtime_root.expanduser().resolve()
    if legacy == target_runtime_home:
        return profile.workspace_root / "ops" / "med-deepscientist" / "runtime"
    return legacy


def _runtime_status(runtime_state: Mapping[str, Any]) -> str:
    return _text(runtime_state.get("status")) or _text(runtime_state.get("quest_status")) or "unknown"


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return dict(payload)


def _write_yaml(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(dict(payload), allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def _read_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return dict(payload)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _upsert_top_level_toml_string(text: str, key: str, value: str) -> str:
    rendered = f"{key} = {json.dumps(value, ensure_ascii=False)}"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            break
        if stripped.startswith(f"{key} "):
            lines[index] = rendered
            return "\n".join(lines) + "\n"
    insert_at = 0
    for index, line in enumerate(lines):
        if line.strip().startswith("["):
            break
        insert_at = index + 1
    lines.insert(insert_at, rendered)
    return "\n".join(lines) + "\n"


def _remove_top_level_toml_key(text: str, key: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    in_top_level = True
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            in_top_level = False
        if in_top_level and stripped.startswith(f"{key} "):
            continue
        kept.append(line)
    return "\n".join(kept) + "\n"


def _replace_table(text: str, table_name: str, payload: Mapping[str, Any]) -> str:
    lines = text.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() == f"[{table_name}]":
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("["):
                index += 1
            continue
        output.append(lines[index])
        index += 1
    while output and not output[-1].strip():
        output.pop()
    output.extend(["", f"[{table_name}]"])
    for key, value in payload.items():
        if isinstance(value, bool):
            rendered_value = "true" if value else "false"
        else:
            rendered_value = json.dumps(str(value), ensure_ascii=False)
        output.append(f"{key} = {rendered_value}")
    return "\n".join(output) + "\n"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _history_stamp(recorded_at: str) -> str:
    normalized = recorded_at.replace("+00:00", "Z").replace(":", "").replace("-", "")
    return normalized
