from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import live_console_observation
from med_autoscience.runtime_protocol import live_console_read_model_io as io
from med_autoscience.runtime_protocol import local_time_projection
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import context_projection
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import stream_projection
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import study_projection


SCHEMA_VERSION = 1
SESSION_SURFACE_KIND = "mas_live_console_session_read_model"
OWNER = "MedAutoScience"


def build_live_console_session_read_model(
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = io.text(generated_at) or _utc_now()
    selected_study_id, selected_study_root = context_projection.resolve_selection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    contexts = context_projection.study_contexts(
        profile=profile,
        selected_study_id=selected_study_id,
        selected_study_root=selected_study_root,
    )
    studies = [
        study_projection.study_projection(context, selected_study_id=selected_study_id)
        for context in contexts
    ]
    runs = study_projection.runs(contexts)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SESSION_SURFACE_KIND,
        "owner": OWNER,
        "generated_at": generated,
        "generated_at_local": local_time_projection.local_time_projection(generated, timezone_name=None),
        "authority": {
            "kind": "read_model_display_artifact",
            "mode": "read_only",
            "writes_authority_surface": False,
            "can_write_paper_or_package": False,
        },
        "workspace": study_projection.workspace_projection(
            profile=profile,
            profile_ref=profile_ref,
            study_contexts=contexts,
        ),
        "studies": studies,
        "selected_study_id": selected_study_id,
        "runs": runs,
        "empty_state": live_console_observation.empty_state(studies, runs),
        "stream_sources": stream_projection.stream_sources(contexts),
        "events": stream_projection.events(generated_at=generated, study_contexts=contexts),
        "controller_action_intents": controller_action_intents(
            profile_ref=profile_ref,
            selected_study_id=selected_study_id,
        ),
        "source_refs": study_projection.workspace_source_refs(contexts),
    }


def stream_events(materialized: dict[str, Any], *, default_payload_ref: str) -> list[dict[str, Any]]:
    return stream_projection.stream_events(materialized, default_payload_ref=default_payload_ref)


def controller_action_intents(
    *,
    profile_ref: str | Path | None,
    selected_study_id: str | None,
) -> list[dict[str, Any]]:
    profile_arg = str(profile_ref) if profile_ref is not None else "<profile>"
    study_arg = f" --study-id {selected_study_id}" if selected_study_id else ""
    return [
        {
            "intent": "inspect_progress",
            "authority": "controller_required",
            "executes_directly": False,
            "command": f"medautosci study progress --profile {profile_arg}{study_arg}",
        },
        {
            "intent": "open_study_runtime_status",
            "authority": "controller_required",
            "executes_directly": False,
            "command": f"medautosci study-runtime-status --profile {profile_arg}{study_arg}",
        },
        {
            "intent": "request_reconcile",
            "authority": "controller_required",
            "executes_directly": False,
            "command": f"medautosci runtime domain-route-reconcile --profile {profile_arg}{study_arg}",
        },
    ]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "SESSION_SURFACE_KIND",
    "build_live_console_session_read_model",
    "controller_action_intents",
    "stream_events",
]
