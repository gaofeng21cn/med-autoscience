from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import progress_portal, runtime_live_console
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_portal_console_soak"
SOAK_REPORT_REF = "artifacts/runtime/portal_console_soak/latest.json"
FORBIDDEN_IDENTITY_TOKENS = (
    "MDS WebUI",
    "DeepScientist",
    "med-deepscientist",
)
FORBIDDEN_TRUTH_REF_TOKENS = (
    "med-deepscientist",
    "/ops/med-deepscientist/",
    "last_launch_report.json/.ds",
)


def run_portal_console_soak(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
    materialize: bool = True,
) -> dict[str, Any]:
    generated = _text(generated_at) or _utc_now()
    selected_study_root = Path(study_root) if study_root is not None else None
    portal_result = progress_portal.materialize_progress_portal(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=selected_study_root,
        generated_at=generated,
        sync_runtime_summary=False,
    )
    console_result = runtime_live_console.serve_live_console_stream(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=selected_study_root,
        generated_at=generated,
        host="127.0.0.1",
        port=0,
        interval_seconds=30,
    )
    report = build_portal_console_soak_report(
        profile=profile,
        profile_ref=profile_ref,
        portal_result=portal_result,
        console_result=console_result,
        generated_at=generated,
    )
    if materialize:
        report_path = profile.workspace_root / SOAK_REPORT_REF
        _write_json(report_path, report)
        report["report_path"] = str(report_path)
    return report


def build_portal_console_soak_report(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    portal_result: Mapping[str, Any],
    console_result: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = _text(generated_at) or _utc_now()
    portal_payload_path = Path(str(portal_result.get("payload_path") or ""))
    portal_html_path = Path(str(portal_result.get("html_path") or ""))
    console_payload_path = Path(str(console_result.get("payload_path") or ""))
    console_html_path = Path(str(console_result.get("html_path") or ""))
    console_ui_payload_path = Path(str(console_result.get("ui_payload_path") or ""))

    portal_payload = _read_json_object(portal_payload_path)
    console_payload = _read_json_object(console_payload_path)
    console_ui_payload = _read_json_object(console_ui_payload_path)
    portal_html = _read_text(portal_html_path)
    console_html = _read_text(console_html_path)
    console_snapshot = _mapping(console_result.get("session_read_model")) or console_payload

    evidence = {
        "portal_refresh": _portal_refresh_evidence(
            portal_result=portal_result,
            portal_payload=portal_payload,
            portal_html_path=portal_html_path,
        ),
        "live_console_study_run_disambiguation": _live_console_disambiguation(console_snapshot),
        "terminal_log_refs": _terminal_log_refs(console_snapshot),
        "source_ref_cleanliness": _source_ref_cleanliness(
            portal_payload=portal_payload,
            console_payload=console_payload,
            console_ui_payload=console_ui_payload,
        ),
        "product_identity": _product_identity(portal_html=portal_html, console_html=console_html),
        "write_boundary": _write_boundary(
            workspace_root=profile.workspace_root,
            portal_result=portal_result,
            console_result=console_result,
        ),
    }
    status = "passed" if all(item.get("status") == "passed" for item in evidence.values()) else "blocked"
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "owner": "MedAutoScience",
        "generated_at": generated,
        "status": status,
        "read_only": True,
        "authority": {
            "kind": "display_read_model_soak_evidence",
            "writes_authority_surface": False,
            "controller_action_execution_allowed": False,
            "quality_authority_allowed": False,
            "publication_authority_allowed": False,
            "submission_authority_allowed": False,
        },
        "workspace": {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        "evidence": evidence,
        "artifact_refs": {
            "progress_portal_payload": str(portal_payload_path),
            "progress_portal_html": str(portal_html_path),
            "live_console_session_read_model": str(console_payload_path),
            "live_console_ui_payload": str(console_ui_payload_path),
            "live_console_html": str(console_html_path),
            "soak_report": str(profile.workspace_root / SOAK_REPORT_REF),
        },
        "forbidden_authority_writes": [
            "paper/current_package",
            "manuscript/current_package",
            "paper/submission_minimal",
            "manuscript/submission_minimal",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "runtime_lifecycle.sqlite",
            "restore_archive",
        ],
    }


def _portal_refresh_evidence(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
    portal_html_path: Path,
) -> dict[str, Any]:
    portal_view = _mapping(portal_payload.get("portal_view"))
    status = "passed" if portal_result.get("status") == "materialized" and portal_html_path.is_file() else "blocked"
    return {
        "status": status,
        "payload_generated_at": _text(portal_payload.get("generated_at")),
        "html_path": str(portal_html_path),
        "refresh_mode": portal_view.get("refresh_mode"),
    }


def _live_console_disambiguation(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    studies = [dict(item) for item in snapshot.get("studies") or [] if isinstance(item, Mapping)]
    study_ids = [_text(item.get("study_id")) for item in studies]
    run_ids = [
        _text(run.get("run_id"))
        for item in studies
        for run in item.get("runs") or []
        if isinstance(run, Mapping)
    ]
    if not run_ids:
        run_ids = [_text(item.get("active_run_id")) for item in studies]
    distinct_studies = sorted({item for item in study_ids if item})
    distinct_runs = sorted({item for item in run_ids if item})
    return {
        "status": "passed" if len(distinct_studies) >= 2 and len(distinct_runs) >= 1 else "blocked",
        "study_ids": distinct_studies,
        "run_ids": distinct_runs,
        "selected_study_id": _text(snapshot.get("selected_study_id")),
    }


def _terminal_log_refs(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sources = [
        dict(item)
        for item in snapshot.get("stream_sources") or []
        if isinstance(item, Mapping) and item.get("topic") in {"terminal.tail", "log.tail"}
    ]
    if not sources:
        for study in snapshot.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            for key, topic in (("terminal_sources", "terminal.tail"), ("log_sources", "log.tail")):
                for source in study.get(key) or []:
                    if isinstance(source, Mapping):
                        item = dict(source)
                        item["topic"] = topic
                        item["study_id"] = study.get("study_id")
                        sources.append(item)
    readable = [
        source
        for source in sources
        if _text(source.get("source_ref")) and source.get("status", source.get("source_status")) == "available"
    ]
    return {
        "status": "passed" if readable and len(readable) == len(sources) else "blocked",
        "refs": [
            {
                "topic": _text(source.get("topic")),
                "study_id": _text(source.get("study_id")),
                "source_ref": _text(source.get("source_ref")),
                "status": _text(source.get("status")) or _text(source.get("source_status")),
            }
            for source in sources
        ],
    }


def _source_ref_cleanliness(
    *,
    portal_payload: Mapping[str, Any],
    console_payload: Mapping[str, Any],
    console_ui_payload: Mapping[str, Any],
) -> dict[str, Any]:
    refs = [
        *_string_refs(portal_payload.get("source_refs")),
        *_source_ref_objects(console_payload.get("source_refs")),
        *_string_refs(console_ui_payload.get("source_refs")),
    ]
    forbidden = [
        ref
        for ref in refs
        if any(token in ref for token in FORBIDDEN_TRUTH_REF_TOKENS)
    ]
    return {
        "status": "passed" if not forbidden else "blocked",
        "checked_ref_count": len(refs),
        "forbidden_refs": forbidden,
    }


def _product_identity(*, portal_html: str, console_html: str) -> dict[str, Any]:
    combined = f"{portal_html}\n{console_html}"
    forbidden = [token for token in FORBIDDEN_IDENTITY_TOKENS if token in combined]
    return {
        "status": "passed" if "Med Auto Science" in combined and not forbidden else "blocked",
        "brand": "Med Auto Science",
        "forbidden_identity_tokens": forbidden,
    }


def _write_boundary(
    *,
    workspace_root: Path,
    portal_result: Mapping[str, Any],
    console_result: Mapping[str, Any],
) -> dict[str, Any]:
    allowed = {
        str(Path(str(portal_result.get("payload_path"))).resolve()),
        str(Path(str(portal_result.get("html_path"))).resolve()),
        str(Path(str(portal_result.get("hosted_package_path"))).resolve()),
        str(Path(str(console_result.get("payload_path"))).resolve()),
        str(Path(str(console_result.get("history_path"))).resolve()),
        str(Path(str(console_result.get("ui_payload_path"))).resolve()),
        str(Path(str(console_result.get("html_path"))).resolve()),
        str((workspace_root / SOAK_REPORT_REF).resolve()),
    }
    forbidden_paths = [
        workspace_root / "publication_eval" / "latest.json",
        workspace_root / "controller_decisions" / "latest.json",
        workspace_root / "runtime_lifecycle.sqlite",
    ]
    return {
        "status": "passed" if not any(path.exists() for path in forbidden_paths) else "blocked",
        "allowed_written_refs": sorted(allowed),
        "forbidden_existing_refs": [str(path) for path in forbidden_paths if path.exists()],
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _source_ref_objects(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            ref = _text(item.get("source_ref"))
            if ref:
                refs.append(ref)
    return refs


def _string_refs(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [str(item) for item in value if _text(item)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "SOAK_REPORT_REF",
    "SURFACE_KIND",
    "build_portal_console_soak_report",
    "run_portal_console_soak",
]
