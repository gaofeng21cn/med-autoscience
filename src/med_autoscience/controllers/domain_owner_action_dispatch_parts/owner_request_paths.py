from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


OWNER_REQUEST_RELATIVE_PATHS = {
    "publication_gate_specificity_required": Path("artifacts/supervision/requests/publication_gate_specificity/latest.json"),
    "publication_handoff_owner_gate": Path("artifacts/supervision/requests/publication_handoff_owner_gate/latest.json"),
    "current_package_freshness_required": Path("artifacts/supervision/requests/current_package_freshness/latest.json"),
    "artifact_display_surface_materialization_required": Path(
        "artifacts/supervision/requests/artifact_display_materialization/latest.json"
    ),
    "return_to_ai_reviewer_workflow": Path("artifacts/supervision/requests/ai_reviewer/latest.json"),
    "run_gate_clearing_batch": Path("artifacts/supervision/requests/gate_clearing_batch/latest.json"),
    "canonical_paper_inputs_rehydrate_required": Path(
        "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    ),
    "run_quality_repair_batch": Path("artifacts/supervision/requests/quality_repair_batch/latest.json"),
    "unit_harmonized_external_validation_rerun": Path("artifacts/supervision/requests/analysis_harmonization/latest.json"),
    "recover_transport_model_provenance": Path("artifacts/supervision/requests/source_provenance/latest.json"),
    "methodology_reframe_route_decision": Path("artifacts/supervision/requests/decision/latest.json"),
    "provenance_limited_harmonization_audit": Path(
        "artifacts/supervision/requests/provenance_limited_harmonization/latest.json"
    ),
}


def owner_request_payload(profile: WorkspaceProfile, study_id: str, action_type: str) -> dict[str, Any] | None:
    path = owner_request_path(profile, study_id, action_type)
    if path is None:
        return None
    return _read_json_object(path)


def owner_request_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path | None:
    relative_path = OWNER_REQUEST_RELATIVE_PATHS.get(action_type)
    if relative_path is None:
        return None
    return profile.studies_root / study_id / relative_path


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


__all__ = ["OWNER_REQUEST_RELATIVE_PATHS", "owner_request_payload", "owner_request_path"]
