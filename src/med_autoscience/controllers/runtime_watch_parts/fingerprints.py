from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def _publication_gate_fingerprint_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "allow_write": result.get("allow_write"),
        "blockers": result.get("blockers") or [],
        "missing_non_scalar_deliverables": result.get("missing_non_scalar_deliverables") or [],
        "submission_minimal_present": result.get("submission_minimal_present"),
        "draft_handoff_delivery_required": result.get("draft_handoff_delivery_required"),
        "draft_handoff_delivery_status": result.get("draft_handoff_delivery_status"),
        "supervisor_phase": result.get("supervisor_phase"),
        "phase_owner": result.get("phase_owner"),
        "upstream_scientific_anchor_ready": result.get("upstream_scientific_anchor_ready"),
        "bundle_tasks_downstream_only": result.get("bundle_tasks_downstream_only"),
        "current_required_action": result.get("current_required_action"),
        "deferred_downstream_actions": result.get("deferred_downstream_actions") or [],
        "controller_stage_note": result.get("controller_stage_note"),
    }


def _medical_publication_surface_fingerprint_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    top_hits = result.get("top_hits") or []
    return {
        "status": result.get("status"),
        "blockers": result.get("blockers") or [],
        "top_hits": [
            {
                "path": item.get("path"),
                "location": item.get("location"),
                "phrase": item.get("phrase"),
            }
            for item in top_hits[:10]
            if isinstance(item, Mapping)
        ],
    }


def _data_asset_gate_fingerprint_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "blockers": result.get("blockers") or [],
        "advisories": result.get("advisories") or [],
        "study_id": result.get("study_id"),
        "outdated_dataset_ids": result.get("outdated_dataset_ids") or [],
        "unresolved_dataset_ids": result.get("unresolved_dataset_ids") or [],
        "public_support_dataset_ids": result.get("public_support_dataset_ids") or [],
    }


def _figure_loop_guard_fingerprint_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "blockers": result.get("blockers") or [],
        "dominant_figure_id": result.get("dominant_figure_id"),
        "dominant_figure_mentions": result.get("dominant_figure_mentions"),
        "reference_count": result.get("reference_count"),
    }


def _medical_literature_audit_fingerprint_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "blockers": result.get("blockers") or [],
        "action": result.get("action"),
        "missing_pmids": result.get("missing_pmids") or [],
    }


def _medical_reporting_audit_fingerprint_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "blockers": result.get("blockers") or [],
        "action": result.get("action"),
    }


_FINGERPRINT_PAYLOAD_BUILDERS = {
    "publication_gate": _publication_gate_fingerprint_payload,
    "medical_publication_surface": _medical_publication_surface_fingerprint_payload,
    "data_asset_gate": _data_asset_gate_fingerprint_payload,
    "figure_loop_guard": _figure_loop_guard_fingerprint_payload,
    "medical_literature_audit": _medical_literature_audit_fingerprint_payload,
    "medical_reporting_audit": _medical_reporting_audit_fingerprint_payload,
}


def build_fingerprint(controller_name: str, result: dict[str, Any]) -> str:
    builder = _FINGERPRINT_PAYLOAD_BUILDERS.get(controller_name)
    payload: Mapping[str, Any] = builder(result) if builder is not None else result
    canonical = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = ["build_fingerprint"]
