from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import tarfile
from typing import Any


ARCHIVE_FORMAT = "tar.gz"
SCHEMA_VERSION = 1


def artifact_slug(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def safe_artifact_id(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in str(value).strip())
    return safe.strip("-._") or "quest"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def restore_proof(
    *,
    archive_path: Path,
    manifest: Mapping[str, Any],
    archive_sha256: str,
    verified_at: str,
) -> dict[str, Any]:
    expected = {str(item["path"]): dict(item) for item in manifest.get("source_files", []) if isinstance(item, Mapping)}
    errors: list[dict[str, Any]] = []
    observed: dict[str, dict[str, Any]] = {}
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            file_observations: dict[str, dict[str, Any]] = {}
            hardlink_refs: list[tuple[str, str, int]] = []
            for member in tar.getmembers():
                if member.isfile():
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        errors.append({"path": member.name, "reason": "member_not_readable"})
                        continue
                    digest = hashlib.sha256(extracted.read()).hexdigest()
                    payload = {
                        "path": member.name,
                        "entry_type": "file",
                        "size_bytes": member.size,
                        "sha256": digest,
                    }
                    observed[member.name] = payload
                    file_observations[member.name] = payload
                    continue
                if member.issym():
                    observed[member.name] = {
                        "path": member.name,
                        "entry_type": "symlink",
                        "link_target": member.linkname,
                    }
                    continue
                if member.islnk():
                    hardlink_refs.append((member.name, member.linkname, member.size))
                    continue
            for member_name, link_name, member_size in hardlink_refs:
                target = file_observations.get(link_name)
                if target is None:
                    errors.append({"path": member_name, "reason": "hardlink_target_missing", "target": link_name})
                    continue
                observed[member_name] = {
                    "path": member_name,
                    "entry_type": "file",
                    "size_bytes": member_size or int(target.get("size_bytes") or 0),
                    "sha256": target.get("sha256"),
                }
    except tarfile.TarError as exc:
        errors.append({"path": str(archive_path), "reason": "archive_not_readable", "error": str(exc)})
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    mismatch = [
        path
        for path in sorted(set(expected) & set(observed))
        if _restore_entry_mismatch(expected[path], observed[path])
    ]
    errors.extend({"path": path, "reason": "missing_from_archive"} for path in missing)
    errors.extend({"path": path, "reason": "unexpected_archive_member"} for path in extra)
    errors.extend({"path": path, "reason": "archive_member_hash_or_size_mismatch"} for path in mismatch)
    return {
        "surface_kind": "runtime_restore_proof",
        "schema_version": SCHEMA_VERSION,
        "status": "verified" if not errors else "failed",
        "verified_at": verified_at,
        "archive_path": str(archive_path),
        "archive_format": ARCHIVE_FORMAT,
        "archive_sha256": archive_sha256,
        "source_file_count": len(expected),
        "verified_file_count": len(observed),
        "verified_entries": [observed[path] for path in sorted(observed)],
        "errors": errors,
    }


def _restore_entry_mismatch(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> bool:
    expected_type = str(expected.get("entry_type") or "file")
    observed_type = str(observed.get("entry_type") or "file")
    if expected_type != observed_type:
        return True
    if expected_type == "symlink":
        return str(expected.get("link_target") or "") != str(observed.get("link_target") or "")
    return int(expected.get("size_bytes") or 0) != int(observed.get("size_bytes") or 0) or str(
        expected.get("sha256") or ""
    ) != str(observed.get("sha256") or "")
