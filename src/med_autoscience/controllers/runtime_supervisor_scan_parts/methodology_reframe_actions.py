from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.runtime_supervisor_scan_parts import hard_methodology_currentness

_REBUILD_ROUTE_WORK_UNIT = "unit_harmonized_external_validation_rerun"
_REBUILD_ROUTE_OPTION = "rebuild_reproducible_model_route"
_AUDIT_ROUTE_WORK_UNIT = "provenance_limited_harmonization_audit"
_AUDIT_ROUTE_OPTION = "provenance_limited_harmonization_audit"

def methodology_reframe_route_decision_action(study_root: Path) -> dict[str, Any] | None:
    if _current_hard_methodology_handoff_supersedes_consumers(study_root):
        return None
    source_result_state = source_provenance_owner_result.typed_blocker_state(study_root=study_root)
    if not source_result_state:
        return None
    if _text(source_result_state.get("blocked_reason")) != "methodology_reframe_required":
        return None
    if _text(source_result_state.get("next_owner")) != "decision":
        return None
    if methodology_reframe_route_decision_materialized(study_root):
        return None
    source_result_ref = source_provenance_owner_result.result_path(study_root=study_root)
    return {
        "action_type": "methodology_reframe_route_decision",
        "authority": "observability_only",
        "owner": "decision",
        "request_owner": "decision",
        "recommended_owner": "decision",
        "reason": "methodology_reframe_required",
        "summary": (
            "The original transported model provenance could not be recovered after bounded search; "
            "route the study through decision owner before any renewed manuscript or medical claim work."
        ),
        "next_work_unit": "methodology_reframe_route_decision",
        "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
        "required_output_surface": (
            "controller route decision for a provenance-limited reframe, reproducible-model restart, "
            "stop-loss, or human gate"
        ),
        "source_ref": str(source_result_ref),
        "terminal_source_blocker": dict(source_result_state),
        "allowed_route_options": [
            "stop_loss_current_transport_claim",
            "provenance_limited_harmonization_audit",
            "rebuild_reproducible_model_route",
            "human_gate",
        ],
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def provenance_limited_harmonization_audit_action(study_root: Path) -> dict[str, Any] | None:
    if _current_hard_methodology_handoff_supersedes_consumers(study_root):
        return None
    if provenance_limited_harmonization_owner_result.required_output_satisfied(study_root=study_root):
        return None
    if not methodology_reframe_audit_route_decision_materialized(study_root):
        return None
    decision_ref = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    return {
        "action_type": "provenance_limited_harmonization_audit",
        "authority": "observability_only",
        "owner": "provenance_limited_harmonization_owner",
        "request_owner": "provenance_limited_harmonization_owner",
        "recommended_owner": "provenance_limited_harmonization_owner",
        "reason": "provenance_limited_harmonization_audit_required",
        "summary": (
            "The decision owner selected a provenance-limited harmonization audit after the terminal "
            "transport-model provenance blocker; consume that decision before any manuscript or medical claim work."
        ),
        "next_work_unit": "provenance_limited_harmonization_audit",
        "work_unit_fingerprint": "provenance-limited-harmonization::audit",
        "required_output_surface": (
            "provenance-limited harmonization audit or "
            "typed blocker:provenance_limited_harmonization_audit_required"
        ),
        "source_ref": str(decision_ref),
        "allowed_route_options": [
            "stop_loss_current_transport_claim",
            "provenance_limited_harmonization_audit",
            "rebuild_reproducible_model_route",
            "human_gate",
        ],
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def clean_rebuild_route_action(study_root: Path) -> dict[str, Any] | None:
    if _current_hard_methodology_handoff_supersedes_consumers(study_root):
        return None
    if not methodology_reframe_rebuild_route_decision_materialized(study_root):
        return None
    decision_ref = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    analysis_ref = analysis_harmonization_owner_result.result_path(study_root=study_root)
    if analysis_harmonization_owner_result.required_output_satisfied(
        study_root=study_root
    ) and not _artifact_supersedes(newer_ref=decision_ref, older_ref=analysis_ref):
        return None
    return {
        "action_type": _REBUILD_ROUTE_WORK_UNIT,
        "authority": "observability_only",
        "owner": "analysis_harmonization_owner",
        "request_owner": "analysis_harmonization_owner",
        "recommended_owner": "analysis_harmonization_owner",
        "reason": "unit_harmonized_rerun_required",
        "summary": (
            "The decision owner selected a clean reproducible-model rebuild route after human-gate "
            "authorization; execute or type-block unit-harmonized external validation."
        ),
        "next_work_unit": _REBUILD_ROUTE_WORK_UNIT,
        "work_unit_fingerprint": "clean-rebuild::unit_harmonized_external_validation_rerun::methodology_reframe_decision",
        "required_output_surface": (
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        "source_ref": str(decision_ref),
        "selected_route_option": _REBUILD_ROUTE_OPTION,
        "clean_reproducible_model_rebuild_authorized": True,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def methodology_reframe_route_decision_materialized(study_root: Path) -> bool:
    return (
        methodology_reframe_audit_route_decision_materialized(study_root)
        or methodology_reframe_rebuild_route_decision_materialized(study_root)
    )


def methodology_reframe_audit_route_decision_materialized(study_root: Path) -> bool:
    decision_ref = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    if _any_artifact_supersedes(newer_refs=_methodology_reframe_trigger_paths(study_root), older_ref=decision_ref):
        return False
    decision = _read_json_object(decision_ref)
    next_work_unit = _mapping(decision.get("next_work_unit"))
    return (
        _text(decision.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and _text(decision.get("work_unit_fingerprint")) == "decision::methodology_reframe_route_decision"
        and _text(next_work_unit.get("unit_id")) == _AUDIT_ROUTE_WORK_UNIT
        and _text(next_work_unit.get("selected_route_option")) == _AUDIT_ROUTE_OPTION
        and next_work_unit.get("terminal_source_provenance_blocker_consumed") is True
        and not provenance_limited_harmonization_owner_result.clean_rebuild_authorization_supersedes_audit_decision(
            study_root=study_root
        )
    )


def methodology_reframe_rebuild_route_decision_materialized(study_root: Path) -> bool:
    decision_ref = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    if _any_artifact_supersedes(newer_refs=_methodology_reframe_trigger_paths(study_root), older_ref=decision_ref):
        return False
    decision = _read_json_object(decision_ref)
    next_work_unit = _mapping(decision.get("next_work_unit"))
    return (
        _text(decision.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and _text(decision.get("work_unit_fingerprint")) == "decision::methodology_reframe_route_decision"
        and _text(next_work_unit.get("unit_id")) == _REBUILD_ROUTE_WORK_UNIT
        and _text(next_work_unit.get("selected_route_option")) == _REBUILD_ROUTE_OPTION
        and next_work_unit.get("terminal_source_provenance_blocker_consumed") is True
        and next_work_unit.get("clean_reproducible_model_rebuild_authorized") is True
        and next_work_unit.get("current_transport_claim_must_not_be_used_as_medical_conclusion") is True
    )


def _methodology_reframe_trigger_paths(study_root: Path) -> tuple[Path, ...]:
    return (
        analysis_harmonization_owner_result.result_path(study_root=study_root),
        source_provenance_owner_result.result_path(study_root=study_root),
    )


def _current_hard_methodology_handoff_supersedes_consumers(study_root: Path) -> bool:
    source_ref = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "quality_repair_batch"
        / "latest.json"
    )
    consumer_paths = (
        analysis_harmonization_owner_result.result_path(study_root=study_root),
        source_provenance_owner_result.result_path(study_root=study_root),
        provenance_limited_harmonization_owner_result.result_path(study_root=study_root),
        Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json",
    )
    return hard_methodology_currentness.handoff_supersedes_paths(
        source_ref=source_ref,
        consumer_paths=consumer_paths,
    )


def _any_artifact_supersedes(*, newer_refs: tuple[Path, ...], older_ref: Path) -> bool:
    return any(_artifact_supersedes(newer_ref=newer_ref, older_ref=older_ref) for newer_ref in newer_refs)


def _artifact_supersedes(*, newer_ref: Path, older_ref: Path) -> bool:
    newer_mtime = _path_mtime(newer_ref)
    older_mtime = _path_mtime(older_ref)
    return newer_mtime is not None and older_mtime is not None and newer_mtime > older_mtime


def artifact_supersedes(*, newer_ref: Path, older_ref: Path) -> bool:
    return _artifact_supersedes(newer_ref=newer_ref, older_ref=older_ref)


def _path_mtime(path: Path) -> float | None:
    try:
        return Path(path).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "artifact_supersedes",
    "clean_rebuild_route_action",
    "methodology_reframe_audit_route_decision_materialized",
    "methodology_reframe_rebuild_route_decision_materialized",
    "methodology_reframe_route_decision_action",
    "methodology_reframe_route_decision_materialized",
    "provenance_limited_harmonization_audit_action",
]
