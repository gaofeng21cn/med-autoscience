from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)


def provider_probe_has_matching_attempt(
    scan_result: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_study_id = _non_empty_text(identity.get("study_id"))
    for study in scan_result.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        if expected_study_id is not None and _non_empty_text(study.get("study_id")) != expected_study_id:
            continue
        if not study_has_running_provider_attempt(study):
            continue
        live_attempt = _mapping(study.get("opl_provider_attempt")) or study
        if provider_attempt_matches_identity(live_attempt, identity=identity):
            return True
    return False


def study_has_running_provider_attempt(study: Mapping[str, Any]) -> bool:
    return study.get("running_provider_attempt") is True and (
        _non_empty_text(study.get("active_stage_attempt_id"))
        or _non_empty_text(study.get("active_run_id"))
        or _non_empty_text(study.get("active_workflow_id"))
    ) is not None


def provider_attempt_matches_identity(
    live_attempt: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    strong_match = False
    expected_action = _non_empty_text(identity.get("action_type"))
    if expected_action is not None and _non_empty_text(live_attempt.get("action_type")) != expected_action:
        return False
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if expected_work_unit is not None and _non_empty_text(live_attempt.get("work_unit_id")) != expected_work_unit:
        return False
    if expected_work_unit is not None:
        strong_match = True
    expected_fingerprints = {
        text
        for value in (identity.get("action_fingerprint"), identity.get("work_unit_fingerprint"))
        if (text := _non_empty_text(value)) is not None
    }
    if expected_fingerprints:
        live_fingerprints = _provider_attempt_fingerprints(live_attempt)
        if not live_fingerprints or (
            live_fingerprints.isdisjoint(expected_fingerprints)
            and not _gate_replay_identity_source_eval_matches(
                live_attempt=live_attempt,
                identity=identity,
            )
        ):
            return False
        strong_match = True
    expected_dispatch = _non_empty_text(identity.get("dispatch_path"))
    live_dispatch = _non_empty_text(live_attempt.get("dispatch_ref")) or _non_empty_text(
        live_attempt.get("dispatch_path")
    )
    if expected_dispatch is None:
        return strong_match
    if live_dispatch is None:
        return False
    normalized_expected = expected_dispatch.replace("\\", "/")
    normalized_live = live_dispatch.replace("\\", "/")
    if normalized_expected == normalized_live or normalized_expected.endswith(f"/{normalized_live}"):
        return True
    return False


def provider_probe_has_non_running_actions(scan_result: Mapping[str, Any]) -> bool:
    running_study_ids = {
        study_id
        for study in scan_result.get("studies") or []
        if isinstance(study, Mapping)
        and study.get("running_provider_attempt") is True
        and (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    for action in scan_result.get("action_queue") or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None or study_id not in running_study_ids:
            return True
    return False


def _provider_attempt_fingerprints(live_attempt: Mapping[str, Any]) -> set[str]:
    owner_route = _mapping(live_attempt.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return {
        text
        for value in (
            live_attempt.get("action_fingerprint"),
            live_attempt.get("work_unit_fingerprint"),
            owner_route.get("work_unit_fingerprint"),
            source_refs.get("work_unit_fingerprint"),
            basis.get("work_unit_fingerprint"),
        )
        if (text := _non_empty_text(value)) is not None
    }


def _gate_replay_identity_source_eval_matches(
    *,
    live_attempt: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> bool:
    action_type = _non_empty_text(identity.get("action_type"))
    if action_type != "run_gate_clearing_batch":
        return False
    work_unit_id = _non_empty_text(identity.get("work_unit_id"))
    live_work_unit_id = _non_empty_text(live_attempt.get("work_unit_id"))
    if (
        work_unit_id not in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
        or live_work_unit_id not in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
    ):
        return False
    expected_source_eval = _source_eval_id_for_identity(identity)
    live_source_eval = _source_eval_id_for_identity(live_attempt)
    return expected_source_eval is not None and expected_source_eval == live_source_eval


def _source_eval_id_for_identity(identity: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(identity.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(identity.get("source_eval_id"))
        or _non_empty_text(source_refs.get("source_eval_id"))
        or _non_empty_text(basis.get("source_eval_id"))
    )


__all__ = [
    "provider_attempt_matches_identity",
    "provider_probe_has_matching_attempt",
    "provider_probe_has_non_running_actions",
    "study_has_running_provider_attempt",
]
