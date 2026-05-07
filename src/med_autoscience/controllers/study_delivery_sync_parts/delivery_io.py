from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def create_staging_root(*, target_root: Path) -> Path:
    return Path(
        tempfile.mkdtemp(
            dir=target_root.parent,
            prefix=f".{target_root.name}.tmp-",
        )
    ).resolve()


def remap_staging_path_string(*, value: str, staging_root: Path, target_root: Path) -> str:
    resolved_value = Path(value).expanduser().resolve()
    try:
        relative = resolved_value.relative_to(staging_root.expanduser().resolve())
    except ValueError:
        return str(resolved_value)
    return str((target_root.expanduser().resolve() / relative).resolve())


def remap_staging_file_records(
    *,
    records: list[dict[str, Any]],
    staging_root: Path,
    target_root: Path,
) -> list[dict[str, Any]]:
    remapped: list[dict[str, Any]] = []
    for record in records:
        updated = dict(record)
        for key in ("target_path", "path"):
            value = updated.get(key)
            if isinstance(value, str) and value.strip():
                updated[key] = remap_staging_path_string(
                    value=value,
                    staging_root=staging_root,
                    target_root=target_root,
                )
        remapped.append(updated)
    return remapped


def replace_directory_atomically(*, staging_root: Path, target_root: Path) -> None:
    resolved_staging_root = staging_root.expanduser().resolve()
    resolved_target_root = target_root.expanduser().resolve()
    backup_root = resolved_target_root.parent / (
        f".{resolved_target_root.name}.bak-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    )
    replaced_existing_root = False
    try:
        if resolved_target_root.exists():
            resolved_target_root.replace(backup_root)
            replaced_existing_root = True
        resolved_staging_root.replace(resolved_target_root)
    except Exception:
        if resolved_target_root.exists():
            shutil.rmtree(resolved_target_root, ignore_errors=True)
        if replaced_existing_root and backup_root.exists():
            backup_root.replace(resolved_target_root)
        raise
    finally:
        if backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)


def clear_directory_contents(path: Path, *, keep_names: tuple[str, ...] = ()) -> list[str]:
    path.mkdir(parents=True, exist_ok=True)
    cleared_paths: list[str] = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.name in keep_names:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        cleared_paths.append(str(child.resolve()))
    return cleared_paths


def copy_file(
    *,
    source: Path,
    target: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    if not source.exists():
        raise FileNotFoundError(f"missing delivery source: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied_files.append(
        {
            "category": category,
            "source_path": str(source.resolve()),
            "target_path": str(target.resolve()),
        }
    )


def copy_tree(
    *,
    source_root: Path,
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
    ignore_filenames: tuple[str, ...] = (),
) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"missing delivery source directory: {source_root}")
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        if source.name in ignore_filenames:
            continue
        relative = source.relative_to(source_root)
        copy_file(
            source=source,
            target=target_root / relative,
            category=category,
            copied_files=copied_files,
        )


def build_zip_from_directory(*, source_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(source_root.rglob("*")):
            if not source.is_file():
                continue
            archive.write(source, source.relative_to(source_root).as_posix())
