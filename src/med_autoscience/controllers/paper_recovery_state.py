from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    OPL_EXECUTION_AUTHORIZATION_OWNER,
    OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT,
)


SURFACE_KIND = "paper_recovery_state"
SCHEMA_VERSION = 1
AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_paper_recovery_state_reducer",
    "top_level_truth": "phase",
    "source_of_truth": "MAS current owner obligation and owner receipt or typed blocker",
    "derived_surfaces": [
        "current_work_unit",
        "current_execution_envelope",
        "provider_admission_candidates",
        "operator_status_card",
    ],
    "opl_authority": "generic_obligation_execution_substrate_only",
    "opl_can_issue_mas_owner_receipt": False,
    "opl_can_authorize_publication_ready": False,
    "provider_completion_is_domain_completion": False,
    "manual_foreground_file_edit_is_domain_completion": False,
}


def build_paper_recovery_state(
    payload: Mapping[str, Any],
    *,
    diagnostic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    progress = _mapping(payload)
    diagnostic = _mapping(diagnostic_report)
    current_work_unit = _mapping(progress.get("current_work_unit"))
    obligation = _obligation(progress, current_work_unit=current_work_unit)

    typed_blocker = _current_typed_blocker(current_work_unit)
    if typed_blocker:
        blocker_reason = _typed_blocker_reason(typed_blocker)
        owner = _typed_blocker_recovery_owner(
            typed_blocker,
            current_work_unit=current_work_unit,
            blocker_reason=blocker_reason,
        )
        return _state(
            progress,
            obligation=obligation,
            phase=_typed_blocker_phase(typed_blocker),
            conditions=[
                {
                    "condition": "current_work_unit_typed_blocker",
                    "blocker_type": blocker_reason,
                }
            ],
            next_safe_action=_typed_blocker_next_action(
                typed_blocker,
                blocker_reason=blocker_reason,
                owner=owner,
            ),
            current_owner=owner,
            suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
        )

    contradiction = _projection_contradiction(progress, obligation=obligation)
    if contradiction is not None:
        return _state(
            progress,
            obligation=obligation,
            phase="projection_inconsistent",
            conditions=[contradiction],
            next_safe_action=_next_action(
                "repair_projection_before_admission",
                provider_admission_allowed=False,
                owner="MedAutoScience",
            ),
            current_owner="MedAutoScience",
        )

    terminal_closeout = _matching_terminal_closeout(progress, obligation=obligation)
    if terminal_closeout is not None:
        closeout_typed_blocker = _typed_blocker_from_closeout(terminal_closeout, obligation=obligation)
        if closeout_typed_blocker:
            blocker_reason = _typed_blocker_reason(closeout_typed_blocker)
            owner = _typed_blocker_recovery_owner(
                closeout_typed_blocker,
                current_work_unit=current_work_unit,
                obligation=obligation,
                blocker_reason=blocker_reason,
            )
            return _state(
                progress,
                obligation=obligation,
                phase=_typed_blocker_phase(closeout_typed_blocker),
                conditions=[
                    {
                        "condition": "accepted_closeout_typed_blocker",
                        "blocker_type": blocker_reason,
                    }
                ],
                next_safe_action=_typed_blocker_next_action(
                    closeout_typed_blocker,
                    blocker_reason=blocker_reason,
                    owner=owner,
                ),
                current_owner=owner,
                evidence_refs=_closeout_refs(terminal_closeout),
            )
        return _state(
            progress,
            obligation=obligation,
            phase="terminal_closeout_ready",
            conditions=[
                {
                    "condition": "terminal_closeout_matches_recovery_obligation",
                    "stage_attempt_id": _text(terminal_closeout.get("stage_attempt_id")),
                }
            ],
            next_safe_action=_next_action(
                "consume_terminal_closeout",
                provider_admission_allowed=False,
                owner="MedAutoScience",
            ),
            evidence_refs=_closeout_refs(terminal_closeout),
        )

    manual_delta = _mapping(progress.get("manual_foreground_delta"))
    if manual_delta.get("changed") is True and _text(manual_delta.get("owner_receipt_ref")) is None:
        return _state(
            progress,
            obligation=obligation,
            phase="manual_foreground_unadopted",
            conditions=[
                {
                    "condition": "foreground_delta_missing_mas_owner_receipt",
                    "path_count": len(_text_items(manual_delta.get("paths"))),
                }
            ],
            next_safe_action=_next_action(
                "adopt_manual_delta_through_mas_owner_receipt",
                provider_admission_allowed=False,
                owner="MedAutoScience",
            ),
            current_owner="MedAutoScience",
        )

    if _has_running_provider_attempt(progress, current_work_unit=current_work_unit):
        owner = _text(current_work_unit.get("owner")) or _text(obligation.get("owner"))
        return _state(
            progress,
            obligation=obligation,
            phase="attempt_running",
            conditions=[{"condition": "running_attempt_identity_bound"}],
            next_safe_action=_next_action(
                "watch_running_attempt",
                provider_admission_allowed=False,
                owner=owner,
            ),
            current_owner=owner,
        )

    admission_blocked = _admission_blocked_condition(progress, diagnostic)
    if admission_blocked is not None:
        owner = _text(obligation.get("owner"))
        return _state(
            progress,
            obligation=obligation,
            phase="admission_blocked",
            conditions=[admission_blocked],
            next_safe_action=_next_action(
                "run_admission_apply_or_report_operator_gate",
                provider_admission_allowed=False,
                owner=owner,
            ),
            current_owner=owner,
        )

    if _provider_admission_pending(progress):
        owner = _text(obligation.get("owner"))
        return _state(
            progress,
            obligation=obligation,
            phase="admission_pending",
            conditions=[{"condition": "provider_admission_pending"}],
            next_safe_action=_next_action(
                "admit_provider_attempt",
                provider_admission_allowed=True,
                owner=owner,
            ),
            current_owner=owner,
        )

    if _current_work_unit_status(current_work_unit) == "executable_owner_action":
        owner = _text(obligation.get("owner"))
        return _state(
            progress,
            obligation=obligation,
            phase="owner_action_ready",
            conditions=[{"condition": "current_owner_action_ready"}],
            next_safe_action=_next_action(
                "materialize_provider_admission_or_owner_callable",
                provider_admission_allowed=True,
                owner=owner,
            ),
            current_owner=owner,
        )

    return _state(
        progress,
        obligation=obligation,
        phase="human_gate",
        conditions=[{"condition": "no_current_machine_executable_recovery_obligation"}],
        next_safe_action=_next_action(
            "record_human_or_owner_gate",
            provider_admission_allowed=False,
            owner="MedAutoScience",
        ),
        current_owner="MedAutoScience",
    )


def _state(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
    phase: str,
    conditions: list[dict[str, Any]],
    next_safe_action: Mapping[str, Any],
    current_owner: str | None = None,
    suppressed_surfaces: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    owner = current_owner or _text(obligation.get("owner")) or "MedAutoScience"
    payload = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "study_id": _study_id(progress),
        "quest_id": _text(progress.get("quest_id")),
        "recovery_obligation_id": _text(obligation.get("recovery_obligation_id")),
        "phase": phase,
        "current_authority": {
            "owner": owner,
            "authority": "med-autoscience" if owner != "one-person-lab" else "one-person-lab",
            "obligation": dict(obligation),
        },
        "conditions": _clean_conditions(conditions),
        "next_safe_action": dict(next_safe_action),
        "suppressed_surfaces": list(suppressed_surfaces or []),
        "evidence_refs": list(evidence_refs or []),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _obligation(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    typed_blocker = _current_typed_blocker(current_work_unit)
    blocker_reason = _typed_blocker_reason(typed_blocker)
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    action_type = _obligation_action_type(progress, current_work_unit=current_work_unit)
    work_unit_id = _obligation_work_unit_id(progress, current_work_unit=current_work_unit)
    fingerprint = _obligation_fingerprint(
        progress,
        current_work_unit=current_work_unit,
        currentness_basis=currentness_basis,
    )
    identity = _obligation_identity(
        blocker_reason=blocker_reason,
        fingerprint=fingerprint,
        current_work_unit=current_work_unit,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    study_id = _study_id(progress)
    return {
        "recovery_obligation_id": "::".join(
            [
                "paper-recovery",
                study_id or "unknown-study",
                action_type or "unknown-action",
                work_unit_id or "unknown-work-unit",
                identity,
            ]
        ),
        "study_id": study_id,
        "quest_id": _text(progress.get("quest_id")) or _text(current_work_unit.get("quest_id")),
        "owner": (
            _text(current_work_unit.get("owner"))
            or _text(_mapping(progress.get("current_executable_owner_action")).get("next_owner"))
            or _text(_mapping(progress.get("current_execution_envelope")).get("owner"))
        ),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "blocker_type": blocker_reason,
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
    }


def _obligation_action_type(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> str | None:
    return _first_text(
        current_work_unit.get("action_type"),
        _mapping(progress.get("current_executable_owner_action")).get("action_type"),
        _mapping(progress.get("current_execution_envelope")).get("action_type"),
    )


def _obligation_work_unit_id(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> str | None:
    return _first_text(
        current_work_unit.get("work_unit_id"),
        _mapping(progress.get("current_execution_envelope")).get("next_work_unit"),
        _mapping(progress.get("current_executable_owner_action")).get("work_unit_id"),
    )


def _obligation_fingerprint(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    currentness_basis: Mapping[str, Any],
) -> str | None:
    action = _mapping(progress.get("current_executable_owner_action"))
    return _first_text(
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        currentness_basis.get("source_fingerprint"),
        action.get("work_unit_fingerprint"),
        action.get("action_fingerprint"),
    )


def _obligation_identity(
    *,
    blocker_reason: str | None,
    fingerprint: str | None,
    current_work_unit: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
) -> str:
    if blocker_reason is not None:
        return blocker_reason
    if fingerprint is not None:
        return fingerprint
    return _short_hash(
        {
            "phase": _current_work_unit_status(current_work_unit),
            "action_type": action_type,
            "work_unit_id": work_unit_id,
        }
    )


def _projection_contradiction(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    operator_status = _mapping(progress.get("operator_status_card"))
    auto_parked = _mapping(progress.get("auto_runtime_parked"))
    if (
        operator_status
        and _text(operator_status.get("handling_state")) == "explicit_resume_pending"
        and auto_parked.get("parked") is False
        and auto_parked.get("superseded_by_current_owner_action") is True
        and not _has_current_provider_admission_candidate(progress, obligation=obligation)
    ):
        return {
            "condition": "operator_card_contradicts_auto_runtime_parked",
            "operator_handling_state": "explicit_resume_pending",
            "auto_runtime_parked": False,
        }
    envelope = _mapping(progress.get("current_execution_envelope"))
    if _text(envelope.get("state_kind")) == "running_provider_attempt":
        handoff = _mapping(progress.get("opl_current_control_state_handoff"))
        if not _running_attempt_has_obligation_identity(handoff, obligation=obligation):
            return {
                "condition": "running_attempt_missing_obligation_identity",
                "active_stage_attempt_id": _text(handoff.get("active_stage_attempt_id")),
                "active_run_id": _text(handoff.get("active_run_id")),
            }
    return None


def _has_current_provider_admission_candidate(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _current_work_unit_status(current_work_unit) == "executable_owner_action"
        and _mapping(current_work_unit.get("state")).get("provider_admission_pending") is True
        and _current_work_unit_matches_obligation(current_work_unit, obligation=obligation)
    ):
        return True
    return any(
        _provider_admission_candidate_matches_obligation(candidate, obligation=obligation)
        for candidate in progress.get("provider_admission_candidates") or []
        if isinstance(candidate, Mapping)
    )


def _provider_admission_candidate_matches_obligation(
    candidate: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    study_id = _text(obligation.get("study_id"))
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    candidate_study_id = _first_text(candidate.get("study_id"), candidate.get("quest_id"))
    if study_id is None or candidate_study_id != study_id:
        return False
    if action_type and _text(candidate.get("action_type")) != action_type:
        return False
    if work_unit_id and _text(candidate.get("work_unit_id")) != work_unit_id:
        return False
    if fingerprint is None:
        return False
    candidate_fingerprints = {
        value
        for value in (
            _text(candidate.get("work_unit_fingerprint")),
            _text(candidate.get("action_fingerprint")),
            *_text_items(candidate.get("work_unit_fingerprints")),
        )
        if value is not None
    }
    return fingerprint in candidate_fingerprints


def _current_work_unit_matches_obligation(
    current_work_unit: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    study_id = _text(obligation.get("study_id"))
    if study_id is not None and _text(current_work_unit.get("study_id")) != study_id:
        return False
    action_type = _text(obligation.get("action_type"))
    if action_type is not None and _text(current_work_unit.get("action_type")) != action_type:
        return False
    work_unit_id = _text(obligation.get("work_unit_id"))
    if work_unit_id is not None and _text(current_work_unit.get("work_unit_id")) != work_unit_id:
        return False
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if fingerprint is None:
        return False
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    current_fingerprints = {
        value
        for value in (
            _text(current_work_unit.get("work_unit_fingerprint")),
            _text(current_work_unit.get("action_fingerprint")),
            _text(currentness_basis.get("work_unit_fingerprint")),
            _text(currentness_basis.get("action_fingerprint")),
        )
        if value is not None
    }
    return fingerprint in current_fingerprints


def _matching_terminal_closeout(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for key in (
        "terminal_closeout_precedence_evidence",
        "terminal_closeout",
        "accepted_closeout_evidence",
    ):
        value = progress.get(key)
        if isinstance(value, list):
            for item in value:
                candidate = _mapping(item)
                if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                    return dict(candidate)
        else:
            candidate = _mapping(value)
            if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                return dict(candidate)
    return None


def _closeout_matches_obligation(
    closeout: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    obligation_id = _text(obligation.get("recovery_obligation_id"))
    closeout_obligation_id = _text(closeout.get("recovery_obligation_id"))
    if obligation_id and closeout_obligation_id and closeout_obligation_id != obligation_id:
        return False
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if action_type and _text(closeout.get("action_type")) not in {None, action_type}:
        return False
    if work_unit_id and _text(closeout.get("work_unit_id")) not in {None, work_unit_id}:
        return False
    if fingerprint and closeout_obligation_id != obligation_id:
        closeout_fingerprints = {
            value
            for value in (
                _text(closeout.get("work_unit_fingerprint")),
                _text(closeout.get("action_fingerprint")),
            )
            if value is not None
        }
        if closeout_fingerprints and fingerprint not in closeout_fingerprints:
            return False
    return bool(
        _text(closeout.get("stage_attempt_id"))
        or _text(closeout.get("active_stage_attempt_id"))
        or _closeout_refs(closeout)
    )


def _closeout_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(closeout.get("closeout_ref")),
        _text(closeout.get("source_path")),
        *_text_items(closeout.get("closeout_refs")),
    ]
    return list(dict.fromkeys(ref for ref in refs if ref is not None))


def _running_attempt_has_obligation_identity(
    handoff: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    obligation_id = _text(obligation.get("recovery_obligation_id"))
    handoff_obligation_id = _text(handoff.get("recovery_obligation_id"))
    fingerprint_matches = fingerprint is not None and fingerprint in {
        _text(handoff.get("work_unit_fingerprint")),
        _text(handoff.get("action_fingerprint")),
    }
    obligation_matches = (
        obligation_id is not None
        and handoff_obligation_id is not None
        and handoff_obligation_id == obligation_id
    )
    return (
        action_type is not None
        and _text(handoff.get("action_type")) == action_type
        and work_unit_id is not None
        and _text(handoff.get("work_unit_id")) == work_unit_id
        and (fingerprint_matches or obligation_matches)
    )


def _admission_blocked_condition(
    progress: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _provider_admission_pending(progress):
        return None
    runtime_health = _mapping(progress.get("runtime_health_snapshot"))
    if (
        _text(runtime_health.get("canonical_runtime_action")) == "external_supervisor_required"
        or (
            runtime_health.get("retry_budget_remaining") is not None
            and int(runtime_health.get("retry_budget_remaining") or 0) <= 0
        )
    ):
        return {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "runtime_recovery_retry_budget_exhausted",
        }
    if diagnostic.get("will_start_llm") is False and _text(diagnostic.get("action_class")) == "observe_only":
        return {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "dhd_report_observe_only",
        }
    if diagnostic.get("will_start_llm") is False and int(diagnostic.get("codex_dispatch_count") or 0) == 0:
        return {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "dhd_report_no_codex_dispatch",
        }
    return None


def _provider_admission_pending(progress: Mapping[str, Any]) -> bool:
    if int(progress.get("provider_admission_pending_count") or 0) > 0:
        return True
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _current_work_unit_status(current_work_unit) == "executable_owner_action"
        and _mapping(current_work_unit.get("state")).get("provider_admission_pending") is True
    ):
        return True
    return bool([item for item in progress.get("provider_admission_candidates") or [] if isinstance(item, Mapping)])


def _current_typed_blocker(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    if _current_work_unit_status(current_work_unit) not in {"typed_blocker", "blocked_current_work_unit"}:
        return {}
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = _mapping(state.get("typed_blocker")) or _mapping(current_work_unit.get("typed_blocker"))
    if not typed_blocker:
        typed_blocker = {
            "blocker_type": _text(state.get("blocker_type")),
            "blocked_reason": _text(state.get("blocked_reason")),
        }
    for key in ("owner", "action_type", "work_unit_id", "work_unit_fingerprint"):
        if key not in typed_blocker and _text(current_work_unit.get(key)) is not None:
            typed_blocker[key] = _text(current_work_unit.get(key))
    return {key: value for key, value in typed_blocker.items() if value not in (None, "", [], {})}


def _typed_blocker_from_closeout(
    closeout: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any]:
    embedded = _mapping(closeout.get("typed_blocker"))
    domain_blocker = _mapping(closeout.get("domain_blocker"))
    owner_result = _mapping(closeout.get("owner_result"))
    paper_log = _mapping(closeout.get("paper_stage_log"))
    blocker_type = _first_text(
        embedded.get("blocked_reason"),
        embedded.get("blocker_type"),
        embedded.get("blocker_kind"),
        embedded.get("reason"),
        embedded.get("blocker_id"),
        domain_blocker.get("blocked_reason"),
        domain_blocker.get("blocker_type"),
        domain_blocker.get("blocker_kind"),
        domain_blocker.get("reason"),
        domain_blocker.get("blocker_id"),
        closeout.get("typed_blocker_reason"),
        closeout.get("blocked_reason"),
        owner_result.get("blocked_reason"),
        *_text_items(paper_log.get("remaining_blockers")),
    )
    if blocker_type is None:
        progress_delta = _text(paper_log.get("progress_delta_classification"))
        if progress_delta != "typed_blocker" and _text(closeout.get("typed_blocker_ref")) is None:
            return {}
        blocker_type = "typed_blocker"
    explicit_typed_signal = any(
        value is not None
        for value in (
            _text(closeout.get("typed_blocker_ref")),
            _text(closeout.get("typed_blocker_reason")),
            _text(closeout.get("blocked_reason")),
            _text(owner_result.get("blocked_reason")),
            _text(paper_log.get("progress_delta_classification"))
            if _text(paper_log.get("progress_delta_classification")) == "typed_blocker"
            else None,
        )
    ) or bool(embedded) or bool(domain_blocker) or bool(_text_items(paper_log.get("remaining_blockers")))
    if not explicit_typed_signal:
        return {}
    owner = (
        _text(embedded.get("owner"))
        or _text(embedded.get("next_owner"))
        or _text(domain_blocker.get("owner"))
        or _text(domain_blocker.get("next_owner"))
        or _text(owner_result.get("owner"))
        or _text(closeout.get("next_owner"))
        or _text(obligation.get("owner"))
        or "MedAutoScience"
    )
    return {
        key: value
        for key, value in {
            **embedded,
            **domain_blocker,
            "blocker_type": blocker_type,
            "blocked_reason": blocker_type,
            "owner": owner,
            "action_type": _text(closeout.get("action_type")) or _text(obligation.get("action_type")),
            "work_unit_id": _text(closeout.get("work_unit_id")) or _text(obligation.get("work_unit_id")),
            "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint"))
            or _text(closeout.get("action_fingerprint"))
            or _text(obligation.get("work_unit_fingerprint")),
        }.items()
        if value not in (None, "", [], {})
    }


def _typed_blocker_reason(typed_blocker: Mapping[str, Any]) -> str | None:
    for key in ("blocked_reason", "blocker_type", "blocker_kind", "reason", "blocker_id"):
        if text := _text(typed_blocker.get(key)):
            return text
    anti_loop = _mapping(typed_blocker.get("anti_loop_budget"))
    if _text(anti_loop.get("status")) == "exhausted":
        return "anti_loop_budget_exhausted"
    return None


def _typed_blocker_phase(typed_blocker: Mapping[str, Any]) -> str:
    if _text(typed_blocker.get("requires_human_gate")) == "true":
        return "human_gate"
    if _text(typed_blocker.get("owner")) in {"user", "human", "PI"}:
        return "human_gate"
    return "domain_blocked"


def _typed_blocker_recovery_owner(
    typed_blocker: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any] | None = None,
    obligation: Mapping[str, Any] | None = None,
    blocker_reason: str | None = None,
) -> str:
    if blocker_reason == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return OPL_EXECUTION_AUTHORIZATION_OWNER
    return (
        _text(typed_blocker.get("owner"))
        or _text(_mapping(current_work_unit).get("owner"))
        or _text(_mapping(obligation).get("owner"))
        or "MedAutoScience"
    )


def _typed_blocker_next_action(
    typed_blocker: Mapping[str, Any],
    *,
    blocker_reason: str | None,
    owner: str,
) -> dict[str, Any]:
    if blocker_reason == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return _next_action(
            "provide_opl_execution_authorization_or_human_gate",
            provider_admission_allowed=False,
            owner=owner,
            required_input=_text(typed_blocker.get("required_input")) or OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT,
        )
    return _next_action(
        "resolve_typed_blocker",
        provider_admission_allowed=False,
        owner=owner,
    )


def _suppressed_surfaces_for_typed_blocker(progress: Mapping[str, Any]) -> list[str]:
    suppressed: list[str] = []
    if _mapping(progress.get("current_executable_owner_action")):
        suppressed.append("current_executable_owner_action")
    if _provider_admission_pending(progress):
        suppressed.append("provider_admission_candidates")
    return suppressed


def _next_action(
    kind: str,
    *,
    provider_admission_allowed: bool,
    owner: str | None = None,
    required_input: str | None = None,
) -> dict[str, Any]:
    payload = {
        "kind": kind,
        "owner": owner,
        "provider_admission_allowed": provider_admission_allowed,
        "required_input": required_input,
    }
    return {key: value for key, value in payload.items() if value is not None}


def _clean_conditions(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in condition.items() if value not in (None, "", [], {})}
        for condition in conditions
    ]


def _current_work_unit_status(current_work_unit: Mapping[str, Any]) -> str | None:
    return _text(current_work_unit.get("status"))


def _has_running_provider_attempt(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> bool:
    if _current_work_unit_status(current_work_unit) == "running_provider_attempt":
        return True
    envelope = _mapping(progress.get("current_execution_envelope"))
    return _text(envelope.get("state_kind")) == "running_provider_attempt"


def _study_id(progress: Mapping[str, Any]) -> str | None:
    return _text(progress.get("study_id")) or _text(_mapping(progress.get("current_work_unit")).get("study_id"))


def _short_hash(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]
