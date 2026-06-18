from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
from pathlib import Path
import sqlite3
import subprocess
from typing import Any

from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.workspace_artifacts import workspace_runtime_artifact_path


SURFACE_KIND = "mas_runtime_refs_only_state_index_pilot"
SCHEMA_VERSION = 1
DEFAULT_DB_FILENAME = "mas_refs_only_state_index_pilot.sqlite"
INDEX_VERSION = "mas-runtime-refs-only-state-index-pilot.v1"
FORBIDDEN_REF_SAMPLE_LIMIT = 20
FORBIDDEN_BODY_MARKERS = (
    "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE",
    "PUBLICATION_TRUTH_MUST_NOT_ENTER_SQLITE",
    "MANUSCRIPT_BODY_MUST_NOT_ENTER_SQLITE",
)
FORBIDDEN_BODY_MARKER_ROLES = (
    "owner_receipt_body_fixture",
    "publication_truth_body_fixture",
    "manuscript_body_fixture",
)

_AUTHORITY_BOUNDARY = {
    "sqlite_role": "rebuildable_refs_only_sidecar_index",
    "state_index_owner": "one-person-lab",
    "mas_state_index_authority": False,
    "body_included": False,
    "rebuildable": True,
    "refs_projection_only": True,
    "body_free": True,
    "stores_study_truth": False,
    "stores_manuscript_body": False,
    "stores_artifact_body": False,
    "stores_owner_receipt_body": False,
    "can_drive_lifecycle": False,
    "can_select_next_action": False,
    "can_authorize_currentness": False,
    "can_generate_next_action_authority": False,
    "can_authorize_provider_admission": False,
    "can_create_worker_attempt": False,
    "can_create_outbox_record": False,
    "sqlite_record_counts_as_stage_complete": False,
    "generic_state_index_owner": "one-person-lab",
}
_LEGACY_SURFACE_POLICY = {
    "runtime_events": "tombstone_provenance_only",
    "runtime_snapshots": "tombstone_provenance_only",
    "lineage_nodes": "tombstone_provenance_only",
    "workspace_allocations": "tombstone_provenance_only",
    "turn_receipts": "tombstone_provenance_only",
    "surface_refs": "tombstone_provenance_only",
    "report_index": "tombstone_provenance_only",
}
_PROJECTION_POLICY = {
    "surface_kind": "mas_refs_only_state_index_projection_policy",
    "projection_status": "temporary_refs_projection",
    "projection_role": "diagnostic_refs_index_only",
    "rebuildable": True,
    "started_worker": False,
    "outbox_record": False,
    "state_body_store": False,
    "lifecycle_authority": False,
    "attempt_lifecycle_authority": False,
    "retry_or_dead_letter_authority": False,
    "worker_residency_authority": False,
    "can_authorize_currentness": False,
    "can_generate_next_action_authority": False,
    "can_authorize_provider_admission": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_ready": False,
    "can_authorize_stage_completion": False,
}
_PRIVATE_CONTROL_PLANE_BOUNDARY = {
    "surface_role": "temporary_refs_projection",
    "opt_in_only": True,
    "default_runtime_path": False,
    "legacy_backend_result_authority": False,
    "can_change_storage_maintenance_outcome": False,
    "can_start_worker": False,
    "can_create_attempt": False,
    "can_create_outbox_record": False,
    "can_generate_provider_admission": False,
    "can_generate_next_action": False,
    "can_claim_runtime_currentness": False,
    "can_claim_stage_progress": False,
    "replacement_owner_surface": "one-person-lab StateIndexKernel",
}
_OPL_STATE_INDEX_READBACK_REQUIREMENT = {
    "surface_kind": "opl_state_index_kernel_readback_requirement",
    "required_owner_surface": "one-person-lab StateIndexKernel",
    "mas_surface_role": "temporary_refs_projection",
    "mas_can_satisfy_readback": False,
    "required_readback_identity_fields": [
        "domain_id",
        "program_id",
        "stage_id",
        "attempt_id",
        "surface_id",
        "source_ref",
        "receipt_ref",
        "content_hash",
        "observed_at",
        "indexed_at",
        "index_version",
        "rebuild_epoch",
    ],
    "required_authority_boundary": {
        "state_index_owner": "one-person-lab",
        "mas_state_index_authority": False,
        "refs_projection_only": True,
        "body_free": True,
        "can_drive_lifecycle": False,
        "can_select_next_action": False,
        "can_authorize_currentness": False,
        "can_authorize_provider_admission": False,
    },
    "mas_projection_cannot_replace": [
        "opl_state_index_kernel_readback",
        "opl_lifecycle_index",
        "opl_operator_read_model",
        "opl_artifact_index",
        "opl_queue_index",
    ],
}


def refs_only_state_index_path(workspace_root: Path) -> Path:
    return workspace_runtime_artifact_path(workspace_root, DEFAULT_DB_FILENAME)


def rebuild_refs_only_state_index(
    *,
    workspace_root: Path,
    quest_root: Path,
    study_root: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_study_root = Path(study_root).expanduser().resolve() if study_root is not None else None
    resolved_db_path = Path(db_path).expanduser().resolve() if db_path is not None else refs_only_state_index_path(
        resolved_workspace_root
    )
    observed_at = _utc_now()
    rebuild_epoch = _rebuild_epoch(observed_at)
    candidates = _candidate_refs(
        workspace_root=resolved_workspace_root,
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
    )
    skipped = _forbidden_existing_refs(
        workspace_root=resolved_workspace_root,
        study_root=resolved_study_root,
    )
    rows = [
        _row_for_candidate(
            workspace_root=resolved_workspace_root,
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            candidate=candidate,
            observed_at=observed_at,
            rebuild_epoch=rebuild_epoch,
        )
        for candidate in candidates
        if candidate.path.is_file()
    ]
    family_counts = Counter(str(row["ref_family"]) for row in rows)
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        conn.execute("DELETE FROM small_file_refs WHERE quest_root = ?", (str(resolved_quest_root),))
        conn.executemany(
            """
            INSERT INTO small_file_refs(
                workspace_root, study_root, quest_root, ref_family, source_ref,
                source_path, payload_role, content_hash, byte_size, mtime_ns,
                observed_at, indexed_at, index_version, rebuild_epoch,
                body_included, authority_classification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["workspace_root"],
                    row["study_root"],
                    row["quest_root"],
                    row["ref_family"],
                    row["source_ref"],
                    row["source_path"],
                    row["payload_role"],
                    row["content_hash"],
                    row["byte_size"],
                    row["mtime_ns"],
                    row["observed_at"],
                    row["indexed_at"],
                    row["index_version"],
                    row["rebuild_epoch"],
                    row["body_included"],
                    row["authority_classification"],
                )
                for row in rows
            ],
        )
        sqlite_total_indexed_count = int(conn.execute("SELECT COUNT(*) FROM small_file_refs").fetchone()[0])
        _write_metadata(
            conn,
            {
                "surface_kind": SURFACE_KIND,
                "schema_version": str(SCHEMA_VERSION),
                "index_version": INDEX_VERSION,
                "body_included": "false",
                "rebuild_epoch": rebuild_epoch,
                "indexed_at": observed_at,
            },
        )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA optimize")
        sqlite_no_body_proof = _sqlite_no_body_proof(conn)
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "indexed",
        "workspace_root": str(resolved_workspace_root),
        "study_root": str(resolved_study_root) if resolved_study_root is not None else None,
        "quest_root": str(resolved_quest_root),
        "sqlite_ref": {
            "db_path": str(resolved_db_path),
            "workspace_relative_path": _sqlite_relative_ref(resolved_db_path, resolved_workspace_root),
        },
        "indexed_count": len(rows),
        "sqlite_total_indexed_count": sqlite_total_indexed_count,
        "family_counts": dict(sorted(family_counts.items())),
        "skipped_forbidden_count": len(skipped),
        "skipped_forbidden_refs_inlined": False,
        "skipped_forbidden_ref_sample_count": min(len(skipped), FORBIDDEN_REF_SAMPLE_LIMIT),
        "skipped_forbidden_ref_sample": skipped[:FORBIDDEN_REF_SAMPLE_LIMIT],
        "body_included": False,
        "payload_role": "ref_metadata_only",
        "projection_policy": dict(_PROJECTION_POLICY),
        "private_control_plane_boundary": dict(_PRIVATE_CONTROL_PLANE_BOUNDARY),
        "opl_state_index_kernel_readback_requirement": dict(_OPL_STATE_INDEX_READBACK_REQUIREMENT),
        "index_version": INDEX_VERSION,
        "rebuild_epoch": rebuild_epoch,
        "stage_folder_attempt_projection": _stage_folder_attempt_projection(
            workspace_root=resolved_workspace_root,
            quest_root=resolved_quest_root,
            db_path=resolved_db_path,
            family_counts=family_counts,
        ),
        "sqlite_no_body_proof": sqlite_no_body_proof,
        "legacy_surface_policy": dict(_LEGACY_SURFACE_POLICY),
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }


class _Candidate:
    def __init__(self, *, path: Path, family: str) -> None:
        self.path = path
        self.family = family


def _candidate_refs(
    *,
    workspace_root: Path,
    study_root: Path | None,
    quest_root: Path,
) -> tuple[_Candidate, ...]:
    candidates: list[_Candidate] = []
    canonical_runtime_state = quest_state.canonical_runtime_state_path(quest_root)
    legacy_runtime_state = quest_state.legacy_runtime_state_path(quest_root)
    candidates.append(_Candidate(path=canonical_runtime_state, family="lifecycle"))
    if not canonical_runtime_state.exists():
        candidates.append(_Candidate(path=legacy_runtime_state, family="lifecycle"))
    elif legacy_runtime_state.exists():
        candidates.append(_Candidate(path=legacy_runtime_state, family="legacy_lifecycle"))
    if study_root is not None:
        candidates.extend(_glob_candidates(study_root / "artifacts" / "runtime" / "owner_route", "*.json", "receipt_ref"))
        candidates.extend(
            _glob_candidates(
                study_root / "artifacts" / "runtime" / "opl_family_domain_handler" / "dispatch_receipts",
                "*.json",
                "receipt_ref",
            )
        )
        candidates.extend(
            _glob_candidates(
                study_root / "artifacts" / "runtime" / "paper_progress_transition_refs",
                "*.jsonl",
                "paper_progress_transition_ref",
            )
        )
        candidates.extend(_glob_candidates(study_root / "artifacts" / "runtime" / "cursors", "*.json", "cursor"))
        candidates.extend(_glob_candidates(study_root / "artifacts" / "runtime" / "indexes", "*.json", "index"))
        candidates.extend(
            _glob_candidates(
                study_root / "artifacts" / "runtime" / "evo_scientist_sidecar",
                "*.json",
                "evo_scientist_sidecar_ref",
            )
        )
    return tuple(
        candidate
        for candidate in candidates
        if candidate.path.exists() and _path_is_inside(candidate.path, workspace_root)
    )


def _glob_candidates(root: Path, pattern: str, family: str) -> Iterable[_Candidate]:
    if not root.exists():
        return ()
    return tuple(_Candidate(path=path, family=family) for path in sorted(root.rglob(pattern)) if path.is_file())


def _forbidden_existing_refs(*, workspace_root: Path, study_root: Path | None) -> list[dict[str, str]]:
    if study_root is None:
        return []
    forbidden_roots = (
        (study_root / "artifacts" / "publication_eval", "publication_eval_body"),
        (study_root / "artifacts" / "controller_decisions", "controller_decision_body"),
        (study_root / "manuscript", "manuscript_body"),
        (study_root / "paper", "paper_package_body"),
        (study_root / "artifacts" / "memory", "memory_body"),
        (study_root / "artifacts" / "evidence", "evidence_ledger_body"),
        (study_root / "artifacts" / "review", "review_ledger_body"),
    )
    skipped: list[dict[str, str]] = []
    for root, role in forbidden_roots:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if not _path_is_inside(path, workspace_root):
                continue
            skipped.append(
                {
                    "source_ref": _relative_ref(path, workspace_root),
                    "forbidden_payload_role": role,
                    "reason": "domain_truth_or_body_surface_not_indexed",
                }
            )
    return skipped


def _row_for_candidate(
    *,
    workspace_root: Path,
    study_root: Path | None,
    quest_root: Path,
    candidate: _Candidate,
    observed_at: str,
    rebuild_epoch: str,
) -> dict[str, Any]:
    stat = candidate.path.stat()
    return {
        "workspace_root": str(workspace_root),
        "study_root": str(study_root) if study_root is not None else None,
        "quest_root": str(quest_root),
        "ref_family": candidate.family,
        "source_ref": _relative_ref(candidate.path, workspace_root),
        "source_path": str(candidate.path),
        "payload_role": "ref_metadata_only",
        "content_hash": _file_sha256(candidate.path),
        "byte_size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
        "observed_at": observed_at,
        "indexed_at": observed_at,
        "index_version": INDEX_VERSION,
        "rebuild_epoch": rebuild_epoch,
        "body_included": 0,
        "authority_classification": "refs_only_no_body",
    }


def _connect(db_path: Path) -> sqlite3.Connection:
    _assert_db_not_tracked(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS state_index_metadata(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS small_file_refs(
            workspace_root TEXT NOT NULL,
            study_root TEXT,
            quest_root TEXT NOT NULL,
            ref_family TEXT NOT NULL,
            source_ref TEXT NOT NULL PRIMARY KEY,
            source_path TEXT NOT NULL,
            payload_role TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            byte_size INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            observed_at TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            index_version TEXT NOT NULL,
            rebuild_epoch TEXT NOT NULL,
            body_included INTEGER NOT NULL,
            authority_classification TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS small_file_refs_quest_root_idx ON small_file_refs(quest_root)")


def _write_metadata(conn: sqlite3.Connection, values: Mapping[str, str]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO state_index_metadata(key, value) VALUES (?, ?)",
        tuple(values.items()),
    )


def _stage_folder_attempt_projection(
    *,
    workspace_root: Path,
    quest_root: Path,
    db_path: Path,
    family_counts: Counter[str],
) -> dict[str, Any]:
    return {
        "surface_kind": "opl_stage_folder_attempt_projection_evidence",
        "projection_role": "refs_only_attempt_read_model_evidence",
        "source_of_truth": "physical_stage_folder_manifest_receipt_refs",
        "stage_completion_signal": False,
        "body_included": False,
        "attempt_root_ref": _relative_ref(quest_root, workspace_root),
        "indexed_ref_families": dict(sorted(family_counts.items())),
        "sqlite_summary_ref": _sqlite_relative_ref(db_path, workspace_root),
    }


def _sqlite_no_body_proof(conn: sqlite3.Connection) -> dict[str, Any]:
    small_file_ref_columns = [
        str(row[1])
        for row in conn.execute("PRAGMA table_info(small_file_refs)").fetchall()
    ]
    forbidden_column_names = {
        "artifact_body",
        "body",
        "body_json",
        "content",
        "controller_decision_body",
        "evidence_ledger_body",
        "manuscript_body",
        "memory_body",
        "owner_receipt_body",
        "payload",
        "payload_body",
        "publication_eval_body",
        "raw_body",
        "review_ledger_body",
        "study_truth_body",
        "text_body",
    }
    forbidden_columns_present = [
        column
        for column in small_file_ref_columns
        if column in forbidden_column_names
    ]
    body_included_values = [
        int(row[0])
        for row in conn.execute("SELECT DISTINCT body_included FROM small_file_refs ORDER BY body_included").fetchall()
    ]
    indexed_text = "\n".join(
        "|".join(str(cell) for cell in row)
        for row in conn.execute(
            """
            SELECT ref_family, source_ref, source_path, payload_role, content_hash,
                   authority_classification
            FROM small_file_refs
            ORDER BY source_ref
            """
        ).fetchall()
    )
    metadata_text = "\n".join(
        "|".join(str(cell) for cell in row)
        for row in conn.execute("SELECT key, value FROM state_index_metadata ORDER BY key").fetchall()
    )
    sqlite_text = "\n".join((indexed_text, metadata_text))
    return {
        "surface_kind": "mas_refs_only_sqlite_no_body_proof",
        "schema_columns_forbid_body": not forbidden_columns_present,
        "body_column_present": "body" in small_file_ref_columns,
        "body_included_values": body_included_values,
        "forbidden_body_marker_found": any(marker in sqlite_text for marker in FORBIDDEN_BODY_MARKERS),
        "checked_forbidden_marker_count": len(FORBIDDEN_BODY_MARKERS),
        "checked_forbidden_marker_roles": list(FORBIDDEN_BODY_MARKER_ROLES),
        "checked_tables": ["small_file_refs", "state_index_metadata"],
        "forbidden_columns_present": forbidden_columns_present,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_ref(path: Path, workspace_root: Path) -> str:
    resolved_path = Path(path).expanduser().resolve()
    try:
        return resolved_path.relative_to(workspace_root).as_posix()
    except ValueError:
        return str(resolved_path)


def _sqlite_relative_ref(path: Path, workspace_root: Path) -> str:
    relative = _relative_ref(path, workspace_root)
    if relative.startswith("runtime/artifacts/"):
        return f"artifacts/runtime/{relative.removeprefix('runtime/artifacts/')}"
    return relative


def _path_is_inside(path: Path, root: Path) -> bool:
    try:
        Path(path).expanduser().resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _assert_db_not_tracked(db_path: Path) -> None:
    git_root = _git_root_for_path(db_path.parent)
    if git_root is None:
        return
    tracked: list[str] = []
    for candidate in (db_path, Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
        try:
            relative = candidate.relative_to(git_root)
        except ValueError:
            continue
        result = subprocess.run(
            ["git", "-C", str(git_root), "ls-files", "--cached", "--error-unmatch", "--", relative.as_posix()],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            tracked.append(relative.as_posix())
    if tracked:
        raise RuntimeError(f"refs-only state index SQLite must not be tracked by Git: {', '.join(tracked)}")


def _git_root_for_path(path: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=False,
        text=True,
        capture_output=True,
    )
    root = result.stdout.strip()
    return Path(root).resolve() if result.returncode == 0 and root else None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _rebuild_epoch(observed_at: str) -> str:
    digest = hashlib.sha256(observed_at.encode("utf-8")).hexdigest()[:16]
    return f"{INDEX_VERSION}:{digest}"


__all__ = [
    "DEFAULT_DB_FILENAME",
    "INDEX_VERSION",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "rebuild_refs_only_state_index",
    "refs_only_state_index_path",
]
