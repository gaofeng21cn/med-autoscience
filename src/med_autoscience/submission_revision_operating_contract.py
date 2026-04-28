from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE_KIND = "submission_revision_operating_contract"

SUPPORTED_STATES = (
    "reviewer_revision",
    "manual_finishing",
    "manuscript_fast_lane",
    "bundle_only_closeout",
    "submission_package_refresh",
)

_STATE_LABELS = {
    "reviewer_revision": "Reviewer/user manuscript revision",
    "manual_finishing": "Legacy parked handoff compatibility guard",
    "manuscript_fast_lane": "Controller-visible manuscript fast lane",
    "bundle_only_closeout": "Bundle-only closeout",
    "submission_package_refresh": "Submission package refresh",
}

_STATE_ACTIONS = {
    "reviewer_revision": "route_same_study_line_back_to_write_or_analysis",
    "manual_finishing": "preserve_controller_authority_and_projection_boundary",
    "manuscript_fast_lane": "run_controller_visible_existing_evidence_text_revision",
    "bundle_only_closeout": "refresh_delivery_projection_after_quality_close",
    "submission_package_refresh": "rerun_export_sync_qc_and_package_freshness",
}

_STATE_PRECONDITION_EXTRAS = {
    "reviewer_revision": (
        "durable reviewer/user feedback intake is present",
        "same study line reactivation has not been superseded by newer closeout proof",
    ),
    "manual_finishing": (
        "legacy manual_finishing state is explicit and current",
        "user-visible parked state is projected by auto_runtime_parked",
        "foreground action stays under MAS controller supervision",
    ),
    "manuscript_fast_lane": (
        "entry mode explicitly requests manuscript_fast_lane",
        "runtime is inactive or foreground takeover is explicitly allowed",
        "all edits are existing-evidence-only",
    ),
    "bundle_only_closeout": (
        "AI reviewer-backed quality closure is current",
        "publication gate allows bundle-stage continuation",
    ),
    "submission_package_refresh": (
        "submission source signature is stale or package freshness is blocked",
        "refresh is deterministic and does not alter scientific claims",
    ),
}

INCIDENT_GUARD_TYPES = (
    "duplicate_figure_legends",
    "study_specific_hardcoding_in_platform_code",
    "projection_as_authority",
    "stale_submission_source",
    "wrong_milestone_claim",
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def build_submission_revision_operating_contract(
    state: str,
    *,
    status: str = "active",
    trigger: str | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_state = _text(state)
    if normalized_state not in SUPPORTED_STATES:
        raise ValueError(f"unsupported submission revision operating state: {state!r}")
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "state": normalized_state,
        "state_label": _STATE_LABELS[normalized_state],
        "status": _text(status) or "active",
        "trigger": _text(trigger),
        "owner": "MedAutoScience controller",
        "backend_role": "MDS may execute controlled runtime work but does not own submission authority",
        "canonical_write_surface": "paper/",
        "projection_surface": "manuscript/current_package/",
        "source_package_surface": "paper/submission_minimal/",
        "current_required_action": _STATE_ACTIONS[normalized_state],
        "preconditions": [
            "canonical paper authority is resolved",
            "AI-first quality boundary remains fail-closed",
            "publication gate has not been bypassed",
            "source signature and package freshness are checked after export",
            *_STATE_PRECONDITION_EXTRAS[normalized_state],
        ],
        "allowed_scope": [
            "controller-authorized paper text or structure changes",
            "existing-evidence repackaging without new scientific claims",
            "submission_minimal export and study_delivery_sync projection refresh",
            "mechanical QC and package consistency checks",
        ],
        "forbidden_scope": [
            "direct manuscript/current_package authority edits",
            "new analysis or new result claims unless routed through MAS analysis gates",
            "mechanical projection presented as AI reviewer judgment",
            "MDS-owned publication or submission readiness claims",
        ],
        "required_validations": [
            "AI reviewer-backed quality record when claiming quality closure",
            "publication gate replay or current clear gate",
            "submission source signature freshness",
            "submission package freshness",
            "submission surface QC",
        ],
        "completion_claim_policy": {
            "projection_exists_equals_submission_ready": False,
            "current_package_direct_edit_completes_task": False,
            "authority_note_is_manuscript_surface": False,
            "requires_ai_reviewer_backed_quality_record": True,
            "requires_publication_gate_clear": True,
            "requires_source_signature_current": True,
            "requires_package_freshness": True,
        },
        "incident_guard_types": list(INCIDENT_GUARD_TYPES),
        "evidence": dict(evidence or {}),
    }


def build_submission_revision_operating_catalog() -> dict[str, Any]:
    return {
        "surface_kind": "submission_revision_operating_catalog",
        "schema_version": SCHEMA_VERSION,
        "supported_states": [
            build_submission_revision_operating_contract(state, status="catalog")
            for state in SUPPORTED_STATES
        ],
        "incident_guard_types": list(INCIDENT_GUARD_TYPES),
    }
