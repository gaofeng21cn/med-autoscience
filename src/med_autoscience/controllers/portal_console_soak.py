from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import progress_portal, runtime_live_console
from med_autoscience.controllers.portal_console_soak_parts import (
    build_soak_evidence,
    mapping,
    read_json_object,
    read_text,
    text,
    utc_now,
    write_json,
)
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_portal_console_soak"
SOAK_REPORT_REF = "artifacts/runtime/portal_console_soak/latest.json"


def run_portal_console_soak(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
    materialize: bool = True,
) -> dict[str, Any]:
    generated = text(generated_at) or utc_now()
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
    conversation_result = runtime_live_console.materialize_conversation_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=selected_study_root,
        generated_at=generated,
    )
    report = build_portal_console_soak_report(
        profile=profile,
        profile_ref=profile_ref,
        portal_result=portal_result,
        console_result=console_result,
        conversation_result=conversation_result,
        generated_at=generated,
    )
    if materialize:
        report_path = profile.workspace_root / SOAK_REPORT_REF
        write_json(report_path, report)
        report["report_path"] = str(report_path)
    return report


def build_portal_console_soak_report(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    portal_result: Mapping[str, Any],
    console_result: Mapping[str, Any],
    conversation_result: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = text(generated_at) or utc_now()
    portal_payload_path = Path(str(portal_result.get("payload_path") or ""))
    portal_html_path = Path(str(portal_result.get("html_path") or ""))
    console_payload_path = Path(str(console_result.get("payload_path") or ""))
    console_html_path = Path(str(console_result.get("html_path") or ""))
    console_ui_payload_path = Path(str(console_result.get("ui_payload_path") or ""))
    conversation_payload_path = Path(
        str(
            mapping(conversation_result).get("payload_path")
            or profile.workspace_root / "artifacts" / "runtime" / "conversation_read_model" / "latest.json"
        )
    )

    portal_payload = read_json_object(portal_payload_path)
    console_payload = read_json_object(console_payload_path)
    console_ui_payload = read_json_object(console_ui_payload_path)
    conversation_payload = mapping(mapping(conversation_result).get("conversation_read_model")) or read_json_object(
        conversation_payload_path
    )
    portal_html = read_text(portal_html_path)
    console_html = read_text(console_html_path)
    console_snapshot = mapping(console_result.get("session_read_model")) or console_payload

    evidence = build_soak_evidence(
        profile=profile,
        portal_result=portal_result,
        portal_payload=portal_payload,
        portal_html_path=portal_html_path,
        portal_html=portal_html,
        console_result=console_result,
        console_payload=console_payload,
        console_ui_payload=console_ui_payload,
        console_snapshot=console_snapshot,
        console_html=console_html,
        conversation_payload=conversation_payload,
    )
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
            "conversation_read_model": str(conversation_payload_path),
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


__all__ = [
    "SOAK_REPORT_REF",
    "SURFACE_KIND",
    "build_portal_console_soak_report",
    "run_portal_console_soak",
]
