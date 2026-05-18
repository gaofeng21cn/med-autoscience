from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "mas_audit_bucket_compaction"
ALLOWED_WORKSPACE_CLASSIFICATIONS = frozenset({"stopped_cold", "archived_workspace"})
FAIL_CLOSED_BUCKET_CLASSIFICATIONS = frozenset({"live_active", "pinned", "unknown"})
ALLOWED_BUCKET_CLASSIFICATIONS = frozenset({"stopped_cold", "archived_workspace", "cold_bucket"})
RESTORE_INDEX_BASENAME = "restore_index.json"
PROVENANCE_LEDGER_BASENAME = "provenance_ledger.jsonl"


@dataclass(frozen=True)
class AuditCompactionResult:
    surface: str
    schema_version: int
    apply: bool
    ok: bool
    source_path: str
    workspace_classification: str
    bucket_classification: str
    archive_path: str | None
    restore_index_path: str | None
    provenance_ledger_path: str | None
    source_removed: bool
    entries: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "schema_version": self.schema_version,
            "apply": self.apply,
            "ok": self.ok,
            "source_path": self.source_path,
            "workspace_classification": self.workspace_classification,
            "bucket_classification": self.bucket_classification,
            "archive_path": self.archive_path,
            "restore_index_path": self.restore_index_path,
            "provenance_ledger_path": self.provenance_ledger_path,
            "source_removed": self.source_removed,
            "entries": [dict(item) for item in self.entries],
            "blockers": list(self.blockers),
        }


def compact_audit_bucket(
    source_path: Path | str,
    *,
    archive_dir: Path | str | None = None,
    workspace_classification: str,
    bucket_classification: str,
    lifecycle_export_ref: str | None = None,
    apply: bool = False,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    source = Path(source_path)
    archive_root = Path(archive_dir) if archive_dir is not None else source.parent / "cold_archive"
    blockers = _compaction_blockers(source, archive_root, workspace_classification, bucket_classification)
    if blockers:
        return AuditCompactionResult(
            surface=SURFACE,
            schema_version=SCHEMA_VERSION,
            apply=apply,
            ok=False,
            source_path=str(source),
            workspace_classification=workspace_classification,
            bucket_classification=bucket_classification,
            archive_path=None,
            restore_index_path=None,
            provenance_ledger_path=None,
            source_removed=False,
            entries=(),
            blockers=tuple(blockers),
        ).as_dict()

    entries = tuple(_source_entries(source))
    archive_path = archive_root / f"{source.name}.tar.gz" if source.is_dir() else archive_root / f"{source.name}.gz"
    restore_index_path = archive_root / RESTORE_INDEX_BASENAME
    provenance_ledger_path = archive_root / PROVENANCE_LEDGER_BASENAME

    if not apply:
        return AuditCompactionResult(
            surface=SURFACE,
            schema_version=SCHEMA_VERSION,
            apply=False,
            ok=True,
            source_path=str(source),
            workspace_classification=workspace_classification,
            bucket_classification=bucket_classification,
            archive_path=str(archive_path),
            restore_index_path=str(restore_index_path),
            provenance_ledger_path=str(provenance_ledger_path),
            source_removed=False,
            entries=entries,
        ).as_dict()

    archive_root.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        raise FileExistsError(f"audit compaction archive already exists: {archive_path}")
    if restore_index_path.exists():
        raise FileExistsError(f"audit compaction restore index already exists: {restore_index_path}")

    recorded_at = _timestamp(timestamp)
    if source.is_dir():
        _write_tar_gz(source, archive_path)
    else:
        _write_gzip(source, archive_path)
    archive_sha256 = _file_sha256(archive_path)
    restore_index = _restore_index(
        source=source,
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        entries=entries,
        workspace_classification=workspace_classification,
        bucket_classification=bucket_classification,
        recorded_at=recorded_at,
    )
    _write_json(restore_index_path, restore_index)
    _append_provenance_ledger(
        provenance_ledger_path,
        restore_index=restore_index,
        archive_sha256=archive_sha256,
        entries=entries,
    )
    _verify_restore_index(restore_index_path)
    _remove_source(source)

    return AuditCompactionResult(
        surface=SURFACE,
        schema_version=SCHEMA_VERSION,
        apply=True,
        ok=True,
        source_path=str(source),
        workspace_classification=workspace_classification,
        bucket_classification=bucket_classification,
        archive_path=str(archive_path),
        restore_index_path=str(restore_index_path),
        provenance_ledger_path=str(provenance_ledger_path),
        source_removed=not source.exists(),
        entries=entries,
    ).as_dict() | {
        "audit_compaction_contract": _audit_compaction_contract(
            restore_index_path=restore_index_path,
            provenance_ledger_path=provenance_ledger_path,
            lifecycle_export_ref=lifecycle_export_ref,
        )
    }


def restore_audit_bucket(
    restore_index_path: Path | str,
    *,
    restore_root: Path | str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    index_path = Path(restore_index_path)
    restore_index = json.loads(index_path.read_text(encoding="utf-8"))
    archive_path = _resolve_index_path(index_path, _require_text(restore_index, "archive_path"))
    expected_archive_sha256 = _require_text(restore_index, "archive_sha256")
    if _file_sha256(archive_path) != expected_archive_sha256:
        raise ValueError("audit compaction archive sha256 mismatch")

    target_root = Path(restore_root) if restore_root is not None else Path(_require_text(restore_index, "source_parent"))
    source_name = _require_text(restore_index, "source_name")
    target_source = target_root / source_name
    if target_source.exists() and not overwrite:
        raise FileExistsError(f"audit compaction restore target already exists: {target_source}")
    if target_source.exists():
        _remove_source(target_source)
    target_source.parent.mkdir(parents=True, exist_ok=True)

    if _require_text(restore_index, "archive_format") == "tar.gz":
        target_source.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                target = _safe_restore_target(target_source, member.name)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise ValueError(f"unsupported archive member type: {member.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ValueError(f"missing archive member bytes: {member.name}")
                target.write_bytes(extracted.read())
    elif _require_text(restore_index, "archive_format") == "gzip":
        target_source.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(archive_path, "rb") as source_bytes:
            target_source.write_bytes(source_bytes.read())
    else:
        raise ValueError("unsupported audit compaction archive format")

    restored_entries = tuple(_source_entries(target_source))
    _assert_entries_match(restore_index, restored_entries)
    return {
        "surface": "mas_audit_bucket_restore",
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "restore_index_path": str(index_path),
        "archive_path": str(archive_path),
        "restored_source_path": str(target_source),
        "entries": [dict(item) for item in restored_entries],
    }


def _compaction_blockers(
    source: Path,
    archive_root: Path,
    workspace_classification: str,
    bucket_classification: str,
) -> list[str]:
    blockers: list[str] = []
    if workspace_classification not in ALLOWED_WORKSPACE_CLASSIFICATIONS:
        blockers.append("workspace_not_stopped_cold_or_archived")
    if bucket_classification in FAIL_CLOSED_BUCKET_CLASSIFICATIONS:
        blockers.append(f"bucket_classification_fail_closed:{bucket_classification}")
    elif bucket_classification not in ALLOWED_BUCKET_CLASSIFICATIONS:
        blockers.append("bucket_classification_not_cold")
    if not source.exists():
        blockers.append("source_path_missing")
    elif not (source.is_dir() or source.is_file()):
        blockers.append("source_path_not_file_or_directory")
    elif _is_relative_to(archive_root, source):
        blockers.append("archive_dir_inside_source_path")
    return blockers


def _source_entries(source: Path) -> list[dict[str, Any]]:
    if source.is_file():
        return [_entry(source, Path(source.name))]
    return [_entry(path, path.relative_to(source)) for path in sorted(source.rglob("*")) if path.is_file()]


def _entry(path: Path, relative_path: Path) -> dict[str, Any]:
    return {
        "source_path": str(path),
        "relative_path": relative_path.as_posix(),
        "original_sha256": _file_sha256(path),
        "bytes": path.stat().st_size,
    }


def _write_tar_gz(source: Path, archive_path: Path) -> None:
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(source).as_posix(), recursive=False)


def _write_gzip(source: Path, archive_path: Path) -> None:
    with source.open("rb") as source_bytes, gzip.open(archive_path, "wb") as archive_bytes:
        shutil.copyfileobj(source_bytes, archive_bytes)


def _restore_index(
    *,
    source: Path,
    archive_path: Path,
    archive_sha256: str,
    entries: tuple[dict[str, Any], ...],
    workspace_classification: str,
    bucket_classification: str,
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface": "mas_audit_bucket_restore_index",
        "schema_version": SCHEMA_VERSION,
        "source_path": str(source),
        "source_parent": str(source.parent),
        "source_name": source.name,
        "source_kind": "directory" if source.is_dir() else "file",
        "workspace_classification": workspace_classification,
        "bucket_classification": bucket_classification,
        "archive_path": str(archive_path),
        "archive_format": "tar.gz" if source.is_dir() else "gzip",
        "archive_sha256": archive_sha256,
        "timestamp": recorded_at,
        "entries": [dict(item, archive_sha256=archive_sha256, timestamp=recorded_at) for item in entries],
    }


def _append_provenance_ledger(
    provenance_ledger_path: Path,
    *,
    restore_index: dict[str, Any],
    archive_sha256: str,
    entries: tuple[dict[str, Any], ...],
) -> None:
    timestamp = _require_text(restore_index, "timestamp")
    with provenance_ledger_path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(
                json.dumps(
                    {
                        "surface": "mas_audit_bucket_compaction_provenance",
                        "schema_version": SCHEMA_VERSION,
                        "source_path": entry["source_path"],
                        "relative_path": entry["relative_path"],
                        "original_sha256": entry["original_sha256"],
                        "archive_sha256": archive_sha256,
                        "bytes": entry["bytes"],
                        "timestamp": timestamp,
                    },
                    sort_keys=True,
                )
                + "\n"
            )


def _audit_compaction_contract(
    *,
    restore_index_path: Path,
    provenance_ledger_path: Path,
    lifecycle_export_ref: str | None,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "gates": [
            {"gate_id": "restore", "status": "passed"},
            {"gate_id": "index", "status": "passed"},
            {"gate_id": "provenance", "status": "passed"},
        ],
        "restore_index_ref": str(restore_index_path),
        "provenance_ref": str(provenance_ledger_path),
    }
    if lifecycle_export_ref:
        contract["lifecycle_export_ref"] = lifecycle_export_ref
    return contract


def _verify_restore_index(restore_index_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        restore_audit_bucket(restore_index_path, restore_root=Path(tmp_dir))


def _assert_entries_match(restore_index: dict[str, Any], restored_entries: tuple[dict[str, Any], ...]) -> None:
    expected = {
        _require_text(entry, "relative_path"): (_require_text(entry, "original_sha256"), int(entry["bytes"]))
        for entry in restore_index.get("entries", [])
        if isinstance(entry, dict)
    }
    restored = {entry["relative_path"]: (entry["original_sha256"], entry["bytes"]) for entry in restored_entries}
    if restored != expected:
        raise ValueError("audit compaction restored bytes do not match restore index")


def _safe_restore_target(target_source: Path, relative_name: str) -> Path:
    relative_path = Path(relative_name)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"unsafe archive member path: {relative_name}")
    target = target_source / relative_path
    target.resolve().relative_to(target_source.resolve())
    return target


def _resolve_index_path(index_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return index_path.parent / path


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def _remove_source(source: Path) -> None:
    if source.is_dir():
        shutil.rmtree(source)
    else:
        source.unlink()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp(value: datetime | None) -> str:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"audit compaction payload missing text field: {key}")
    return value
