from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


_CONTROL_SURFACE_PARTS = frozenset({"reports", "publication_eval", "runtime_supervision", "runtime_watch"})
_CONTENT_FILE_NAMES = frozenset(
    {
        "RESULT.json",
        "main_result.json",
        "claim_evidence_map.json",
        "evidence_ledger.json",
        "evidence_ledger.md",
        "paper_bundle_manifest.json",
        "references.bib",
        "manuscript.md",
        "manuscript_submission.md",
        "manuscript_source.md",
    }
)


def _iso(timestamp: datetime | None) -> str | None:
    if timestamp is None:
        return None
    return timestamp.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _latest_file_mtime(root: Path) -> datetime | None:
    if not root.exists():
        return None
    if root.is_file():
        return datetime.fromtimestamp(root.stat().st_mtime, timezone.utc)
    candidates = [
        path
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    ]
    if not candidates:
        return None
    return datetime.fromtimestamp(max(path.stat().st_mtime for path in candidates), timezone.utc)


def _evidence_refs(payload: Mapping[str, Any] | None) -> list[Path]:
    if not isinstance(payload, Mapping):
        return []
    refs: list[Path] = []
    for key in ("evidence_refs", "source_paths"):
        raw_refs = payload.get(key)
        if isinstance(raw_refs, list):
            refs.extend(Path(str(item)).expanduser() for item in raw_refs if str(item or "").strip())
        elif isinstance(raw_refs, Mapping):
            refs.extend(Path(str(item)).expanduser() for item in raw_refs.values() if str(item or "").strip())
    for gap in payload.get("gaps") or []:
        if isinstance(gap, Mapping):
            refs.extend(_evidence_refs(gap))
    for action in payload.get("recommended_actions") or []:
        if isinstance(action, Mapping):
            refs.extend(_evidence_refs(action))
    return refs


def _is_content_authority_ref(path: Path) -> bool:
    parts = set(path.parts)
    if path.name in _CONTENT_FILE_NAMES:
        return True
    if "paper" in parts:
        return True
    if "experiments" in parts and path.name.lower().endswith(".json"):
        return True
    return False


def _is_control_surface_ref(path: Path) -> bool:
    return path.name == "latest.json" or bool(set(path.parts) & _CONTROL_SURFACE_PARTS)


def _source(path: Path, *, source_type: str) -> dict[str, Any] | None:
    latest = _latest_file_mtime(path)
    if latest is None:
        return None
    return {
        "source_type": source_type,
        "path": str(path.resolve()),
        "latest_mtime": _iso(latest),
    }


def _latest_source(sources: list[dict[str, Any]]) -> dict[str, Any] | None:
    latest: tuple[datetime, dict[str, Any]] | None = None
    for source in sources:
        parsed = datetime.fromisoformat(str(source["latest_mtime"]))
        if latest is None or parsed > latest[0]:
            latest = (parsed, source)
    return latest[1] if latest else None


def package_currentness(
    *,
    study_root: Path,
    publication_eval_latest: Mapping[str, Any] | None,
    publishability_gate_latest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    content_sources = [
        source
        for source in (
            _source(study_root / "paper", source_type="study_paper"),
        )
        if source is not None
    ]
    control_sources: list[dict[str, Any]] = []
    for payload in (publication_eval_latest, publishability_gate_latest):
        for ref in _evidence_refs(payload):
            if not ref.exists():
                continue
            if _is_content_authority_ref(ref):
                source = _source(ref, source_type="evidence_ref_content")
                if source is not None:
                    content_sources.append(source)
            elif _is_control_surface_ref(ref):
                source = _source(ref, source_type="control_surface")
                if source is not None:
                    control_sources.append(source)
    current_package_latest = max(
        (
            timestamp
            for timestamp in (
                _latest_file_mtime(study_root / "manuscript" / "current_package"),
                _latest_file_mtime(study_root / "manuscript" / "current_package.zip"),
            )
            if timestamp is not None
        ),
        default=None,
    )
    authority_source = _latest_source(content_sources)
    authority_latest = (
        datetime.fromisoformat(str(authority_source["latest_mtime"]))
        if authority_source is not None
        else None
    )
    control_source = _latest_source(control_sources)
    control_latest = (
        datetime.fromisoformat(str(control_source["latest_mtime"]))
        if control_source is not None
        else None
    )
    if current_package_latest is None:
        status = "missing"
        status_reason = "current_package_missing"
    elif authority_latest is not None and current_package_latest < authority_latest:
        status = "stale"
        status_reason = "content_authority_newer_than_current_package"
    else:
        status = "fresh"
        status_reason = "content_authority_not_newer_than_current_package"
    stale_seconds = (
        int((authority_latest - current_package_latest).total_seconds())
        if authority_latest is not None and current_package_latest is not None and current_package_latest < authority_latest
        else 0
    )
    return {
        "status": status,
        "status_reason": status_reason,
        "authority_latest_mtime": _iso(authority_latest),
        "authority_source": authority_source,
        "authority_source_count": len(content_sources),
        "control_surface_latest_mtime": _iso(control_latest),
        "control_surface_source_count": len(control_sources),
        "current_package_latest_mtime": _iso(current_package_latest),
        "stale_seconds": stale_seconds,
    }
