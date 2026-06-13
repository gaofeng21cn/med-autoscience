from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity import (
    closeout_core_identity_matches_candidate as _closeout_core_identity_matches_candidate,
    closeout_evidence_with_identity as _closeout_evidence_with_identity,
    closeout_identity_matches_current as _closeout_identity_matches_current,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.profiles import WorkspaceProfile


def with_candidate_root_closeout_scans(
    *,
    profile: WorkspaceProfile,
    candidates: list[dict[str, Any]],
    scanned_studies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    studies = [dict(study) for study in scanned_studies]
    study_index_by_id = {
        study_id: index
        for index, study in enumerate(studies)
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id is None:
            continue
        closeout_evidence = study_root_closeout_evidence(
            study_root=Path(profile.studies_root) / study_id,
            identity=candidate,
        )
        unconsumed_closeout_evidence = (
            []
            if closeout_evidence
            else study_root_unconsumed_closeout_evidence(
                study_root=Path(profile.studies_root) / study_id,
                identity=candidate,
            )
        )
        if not closeout_evidence and not unconsumed_closeout_evidence:
            continue
        if study_id in study_index_by_id:
            study = dict(studies[study_index_by_id[study_id]])
            study["accepted_closeout_evidence"] = [
                *_mapping_list(study.get("accepted_closeout_evidence")),
                *closeout_evidence,
                *unconsumed_closeout_evidence,
            ]
            studies[study_index_by_id[study_id]] = study
            continue
        studies.append(
            {
                "study_id": study_id,
                "quest_id": _non_empty_text(candidate.get("quest_id")) or study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": [
                    *closeout_evidence,
                    *unconsumed_closeout_evidence,
                ],
                "current_execution_envelope": {
                    "state_kind": "terminal_closeout_observed"
                    if closeout_evidence
                    else "unconsumed_closeout_observed",
                    "owner": _non_empty_text(candidate.get("next_executable_owner"))
                    or _non_empty_text(candidate.get("recommended_owner"))
                    or _non_empty_text(candidate.get("request_owner")),
                    "next_work_unit": _non_empty_text(candidate.get("work_unit_id")),
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "candidate_root_closeout_evidence",
                },
            }
        )
        study_index_by_id[study_id] = len(studies) - 1
    return studies


def study_root_closeout_evidence(
    *,
    study_root: Path,
    identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not identity:
        return []
    evidence: list[dict[str, Any]] = []
    for execution, execution_ref in default_executor_execution_candidates(study_root=study_root):
        closeout = _closeout_evidence_with_identity(execution, identity=identity)
        if not _closeout_identity_matches_current(closeout, identity=identity):
            continue
        closeout["source_path"] = _non_empty_text(closeout.get("source_path")) or execution_ref
        evidence.append(closeout)
    return evidence


def study_root_unconsumed_closeout_evidence(
    *,
    study_root: Path,
    identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not identity:
        return []
    evidence: list[dict[str, Any]] = []
    for execution, execution_ref in default_executor_execution_candidates(study_root=study_root):
        closeout = _closeout_evidence_with_identity(execution, identity=identity)
        if _closeout_identity_matches_current(closeout, identity=identity):
            continue
        if not _closeout_core_identity_matches_candidate(closeout, identity=identity):
            continue
        closeout["source_path"] = _non_empty_text(closeout.get("source_path")) or execution_ref
        evidence.append(closeout)
    return evidence


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


__all__ = [
    "study_root_closeout_evidence",
    "study_root_unconsumed_closeout_evidence",
    "with_candidate_root_closeout_scans",
]
