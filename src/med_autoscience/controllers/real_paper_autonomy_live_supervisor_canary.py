from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_health_diagnostic, study_progress
from med_autoscience.controllers.paper_autonomy_supervisor import (
    ALLOWED_DECISIONS,
    build_supervisor_decision,
)
from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
from med_autoscience.profiles import WorkspaceProfile, load_profile


SURFACE_KIND = "real_paper_autonomy_live_supervisor_canary"
SCHEMA_VERSION = 1
DEFAULT_TARGET_STUDIES = (
    "002-dm-china-us-mortality-attribution",
    "003-dpcc-primary-care-phenotype-treatment-gap",
)

READ_ONLY_CONTRACT = {
    "surface_kind": SURFACE_KIND,
    "mode": "read_only_live_canary",
    "may_call_study_progress": True,
    "may_call_domain_health_diagnostic_dry_run": True,
    "may_apply_domain_health_diagnostic": False,
    "may_hydrate": False,
    "may_tick": False,
    "may_redrive": False,
    "may_start_provider_attempt": False,
    "may_write_yang_study_or_runtime_artifacts": False,
}

FORBIDDEN_PROGRESS_AUTHORITIES = (
    "queue_empty",
    "dry_run",
    "old_attempt_completion",
    "transport_success",
    "provider_admission_pending_count=0",
    "read_model_refreshed",
    "refs_only",
)

FORBIDDEN_TERMINAL_DECISIONS = {
    "idle",
    "observe_only",
    "queue_empty",
    "provider_healthy",
    "read_model_refreshed",
    "operator_decision_required",
}

PROGRESS_CREDIT_DECISIONS = {
    "stop_with_owner_receipt",
    "consume_terminal_closeout",
    "stop_with_stable_typed_blocker",
    "wait_for_owner_with_resume_token",
    "execute_current_owner_delta",
    "materialize_recovery_action",
}

TERMINAL_CLOSEOUT_DECISIONS = {
    "consume_terminal_closeout",
}

OWNER_RECEIPT_DECISIONS = {
    "stop_with_owner_receipt",
}

STABLE_TYPED_BLOCKER_DECISIONS = {
    "stop_with_stable_typed_blocker",
}

HUMAN_GATE_DECISIONS = {
    "wait_for_owner_with_resume_token",
}

RUNNING_DECISIONS = {
    "execute_current_owner_delta",
}


ProgressReader = Callable[[WorkspaceProfile, str], Mapping[str, Any]]
DhdReader = Callable[[WorkspaceProfile, Sequence[str]], Mapping[str, Any]]


def run_live_supervisor_canary(
    *,
    profile_path: str | Path,
    study_ids: Sequence[str] = DEFAULT_TARGET_STUDIES,
    progress_reader: ProgressReader | None = None,
    dhd_reader: DhdReader | None = None,
) -> dict[str, Any]:
    profile = load_profile(profile_path)
    return build_live_supervisor_canary(
        profile=profile,
        profile_ref=str(Path(profile_path).expanduser().resolve()),
        study_ids=study_ids,
        progress_reader=progress_reader,
        dhd_reader=dhd_reader,
    )


def build_live_supervisor_canary(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | None = None,
    study_ids: Sequence[str] = DEFAULT_TARGET_STUDIES,
    progress_reader: ProgressReader | None = None,
    dhd_reader: DhdReader | None = None,
) -> dict[str, Any]:
    target_study_ids = tuple(dict.fromkeys(_text_items(study_ids)))
    read_progress = progress_reader or _read_study_progress
    read_dhd = dhd_reader or _read_dhd_dry_run

    progress_by_study = {
        study_id: dict(read_progress(profile, study_id)) for study_id in target_study_ids
    }
    dhd_report = dict(read_dhd(profile, target_study_ids))
    diagnostic = _diagnostic_context(dhd_report)
    dhd_progress_by_study = _dhd_progress_currentness(dhd_report)

    study_results = []
    for study_id in target_study_ids:
        progress_payload = progress_by_study.get(study_id) or {}
        dhd_progress_payload = dhd_progress_by_study.get(study_id) or {}
        study_results.append(
            _study_canary_result(
                study_id=study_id,
                progress_payload=progress_payload,
                dhd_progress_payload=dhd_progress_payload,
                diagnostic=diagnostic,
            )
        )

    failures = [
        failure
        for study in study_results
        for failure in study.get("failures", [])
        if isinstance(failure, str) and failure
    ]
    stale_diagnostics = [
        study["study_id"]
        for study in study_results
        if study.get("classification") == "stale_diagnostic"
    ]
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile": profile.name,
        "profile_ref": profile_ref or str(profile.profile_ref or ""),
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "read_only_contract": dict(READ_ONLY_CONTRACT),
        "target_studies": list(target_study_ids),
        "dhd_dry_run_summary": {
            "action_class": _text(dhd_report.get("action_class")),
            "will_start_llm": bool(dhd_report.get("will_start_llm")),
            "codex_dispatch_count": _int(dhd_report.get("codex_dispatch_count")),
            "provider_admission_pending_count": _int(
                dhd_report.get("provider_admission_pending_count")
            ),
            "progress_currentness_count": len(dhd_progress_by_study),
            "provider_admission_candidate_count": _sequence_len(
                dhd_report.get("managed_study_opl_provider_admission_candidates")
            ),
        },
        "study_results": study_results,
        "summary": {
            "status": "pass" if not failures else "fail",
            "study_count": len(study_results),
            "failure_count": len(failures),
            "failures": failures,
            "stale_diagnostic_studies": stale_diagnostics,
            "exactly_one_supervisor_decision_per_study": not any(
                study.get("supervisor_decision_count") != 1 for study in study_results
            ),
            "forbidden_progress_authorities_rejected": not any(
                study.get("forbidden_authority_claimed") for study in study_results
            ),
            "writes_performed": False,
        },
    }


def _study_canary_result(
    *,
    study_id: str,
    progress_payload: Mapping[str, Any],
    dhd_progress_payload: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    progress_decision = _decision_from_progress(progress_payload, diagnostic=diagnostic)
    dhd_decision = _decision_from_progress(dhd_progress_payload, diagnostic=diagnostic)
    selected_decision = progress_decision or dhd_decision
    decision_count = 1 if selected_decision else 0

    if not progress_payload:
        failures.append(f"{study_id}:missing_study_progress")
    if not dhd_progress_payload:
        failures.append(f"{study_id}:missing_dhd_progress_currentness")
    if selected_decision is None:
        failures.append(f"{study_id}:missing_supervisor_decision")
    elif _text(selected_decision.get("decision")) not in ALLOWED_DECISIONS:
        failures.append(f"{study_id}:unsupported_supervisor_decision")

    identity_match = bool(selected_decision and selected_decision.get("identity_match") is True)
    if selected_decision is not None and not identity_match:
        failures.append(f"{study_id}:supervisor_decision_identity_incomplete")
    if selected_decision is not None and _text(selected_decision.get("decision")) in FORBIDDEN_TERMINAL_DECISIONS:
        failures.append(f"{study_id}:forbidden_terminal_decision")

    identities_match = _identity_matches(progress_decision, dhd_decision)
    if (progress_decision is None) != (dhd_decision is None) or (
        progress_decision is not None and dhd_decision is not None and not identities_match
    ):
        failures.append(f"{study_id}:progress_dhd_identity_mismatch")

    forbidden_claims = _forbidden_authority_claims(progress_payload, selected_decision)
    failures.extend(f"{study_id}:{claim}" for claim in forbidden_claims)

    classification = _classification(
        selected_decision,
        identity_match=identity_match,
        identities_match=identities_match,
        has_progress=bool(progress_payload),
        has_dhd_progress=bool(dhd_progress_payload),
    )
    return {
        "study_id": study_id,
        "classification": classification,
        "current_work_unit": _current_work_unit_summary(progress_payload),
        "current_execution_envelope": _current_execution_envelope_summary(progress_payload),
        "provider_admission": _provider_admission_summary(progress_payload),
        "strict_running_proof": _strict_running_proof_summary(progress_payload),
        "terminal_closeout": _terminal_closeout_summary(progress_payload),
        "supervisor_decision_count": decision_count,
        "supervisor_decision": selected_decision or {},
        "progress_decision_id": _text((progress_decision or {}).get("decision_id")),
        "dhd_decision_id": _text((dhd_decision or {}).get("decision_id")),
        "identity_match": identity_match,
        "progress_dhd_identity_match": identities_match,
        "forbidden_authority_claimed": bool(forbidden_claims),
        "forbidden_authority_claims": forbidden_claims,
        "forbidden_progress_authorities": list(FORBIDDEN_PROGRESS_AUTHORITIES),
        "paper_progress_authority": _paper_progress_authority(selected_decision),
        "failures": failures,
    }


def _decision_from_progress(
    progress_payload: Mapping[str, Any],
    *,
    diagnostic: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not progress_payload:
        return None
    recovery_state = _mapping(progress_payload.get("paper_recovery_state"))
    embedded_decision = _mapping(recovery_state.get("supervisor_decision"))
    if embedded_decision:
        return dict(embedded_decision)
    recovery_state = build_paper_recovery_state(progress_payload, diagnostic_report=diagnostic)
    return build_supervisor_decision(progress_payload, paper_recovery_state=recovery_state)


def _read_study_progress(profile: WorkspaceProfile, study_id: str) -> Mapping[str, Any]:
    return study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile.profile_ref,
        study_id=study_id,
        sync_runtime_summary=False,
        materialize_read_model_artifacts=False,
    )


def _read_dhd_dry_run(profile: WorkspaceProfile, study_ids: Sequence[str]) -> Mapping[str, Any]:
    return domain_health_diagnostic.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=False,
        persist_diagnostic_reports=False,
        profile=profile,
        study_ids=tuple(study_ids),
        request_opl_stage_attempts=True,
    )


def _dhd_progress_currentness(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    direct = _mapping(report.get("progress_currentness"))
    if direct:
        return {str(key): _mapping(value) for key, value in direct.items()}
    evidence = _mapping(report.get("current_execution_evidence"))
    nested = _mapping(evidence.get("progress_currentness"))
    return {str(key): _mapping(value) for key, value in nested.items()}


def _diagnostic_context(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "action_class": report.get("action_class"),
        "will_start_llm": report.get("will_start_llm"),
        "codex_dispatch_count": report.get("codex_dispatch_count"),
        "provider_admission_pending_count": report.get("provider_admission_pending_count"),
    }


def _classification(
    decision: Mapping[str, Any] | None,
    *,
    identity_match: bool,
    identities_match: bool,
    has_progress: bool,
    has_dhd_progress: bool,
) -> str:
    if (
        decision is None
        or not identity_match
        or not identities_match
        or not has_progress
        or not has_dhd_progress
    ):
        return "stale_diagnostic"
    decision_type = _text(decision.get("decision"))
    if decision_type in RUNNING_DECISIONS:
        return "identity_bound_provider_handoff_or_running_candidate"
    if decision_type in TERMINAL_CLOSEOUT_DECISIONS:
        return "terminal_closeout_requires_mas_consumption"
    if decision_type in OWNER_RECEIPT_DECISIONS:
        return "owner_receipt_recorded"
    if decision_type in STABLE_TYPED_BLOCKER_DECISIONS:
        return "stable_typed_blocker"
    if decision_type in HUMAN_GATE_DECISIONS:
        return "human_gate"
    if decision_type == "materialize_recovery_action":
        return "recovery_action_required"
    return "stale_diagnostic"


def _paper_progress_authority(decision: Mapping[str, Any] | None) -> dict[str, Any]:
    if decision is None:
        return {
            "paper_progress_credit": False,
            "control_outcome_credit": False,
            "authority": "none",
        }
    decision_type = _text(decision.get("decision"))
    progress_classification = _text(decision.get("paper_progress_classification"))
    paper_credit = (
        decision_type in OWNER_RECEIPT_DECISIONS
        or progress_classification == "mas_owner_receipt_credit"
    )
    control_credit = paper_credit or progress_classification == "stable_stop_loss_credit"
    return {
        "paper_progress_credit": paper_credit,
        "control_outcome_credit": control_credit,
        "authority": "supervisor_decision_identity_bound",
        "decision": decision_type,
        "paper_progress_classification": progress_classification,
        "forbidden_authorities_rejected": list(FORBIDDEN_PROGRESS_AUTHORITIES),
    }


def _forbidden_authority_claims(
    progress_payload: Mapping[str, Any],
    decision: Mapping[str, Any] | None,
) -> list[str]:
    claims: list[str] = []
    decision_type = _text((decision or {}).get("decision"))
    progress_classification = _text((decision or {}).get("paper_progress_classification"))
    if decision is None or decision_type not in PROGRESS_CREDIT_DECISIONS:
        claims.append("decision_not_in_supervisor_closure_set")
    if progress_classification in {
        "queue_empty",
        "dry_run",
        "old_attempt_completion",
        "transport_success",
        "read_model_refreshed",
        "refs_only",
    }:
        claims.append(f"forbidden_progress_classification:{progress_classification}")
    if _provider_pending_count(progress_payload) == 0 and decision_type in {
        "stop_with_owner_receipt",
        "stop_with_stable_typed_blocker",
    }:
        return claims
    return claims


def _identity_matches(
    left_decision: Mapping[str, Any] | None,
    right_decision: Mapping[str, Any] | None,
) -> bool:
    if left_decision is None or right_decision is None:
        return False
    left = _identity(left_decision)
    right = _identity(right_decision)
    return bool(left) and left == right


def _identity(decision: Mapping[str, Any]) -> dict[str, str]:
    obligation = _mapping(decision.get("paper_autonomy_obligation"))
    return {
        key: value
        for key in (
            "study_id",
            "quest_id",
            "stage_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        )
        if (value := _text(obligation.get(key))) is not None
    }


def _current_work_unit_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    unit = _mapping(payload.get("current_work_unit"))
    return {
        "status": _text(unit.get("status")),
        "owner": _text(unit.get("owner")),
        "action_type": _text(unit.get("action_type")),
        "work_unit_id": _text(unit.get("work_unit_id")),
        "work_unit_fingerprint": _text(
            unit.get("work_unit_fingerprint") or unit.get("action_fingerprint")
        ),
        "owner_receipt_ref": _text(_mapping(unit.get("state")).get("owner_receipt_ref")),
        "typed_blocker_type": _text(
            _mapping(unit.get("typed_blocker")).get("blocker_type")
            or _mapping(_mapping(unit.get("state")).get("typed_blocker")).get("blocker_type")
        ),
    }


def _current_execution_envelope_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    envelope = _mapping(payload.get("current_execution_envelope"))
    return {
        "state_kind": _text(envelope.get("state_kind")),
        "owner": _text(envelope.get("owner")),
        "active_run_id": _text(envelope.get("active_run_id")),
        "owner_receipt_ref": _text(envelope.get("owner_receipt_ref")),
        "typed_blocker_type": _text(
            _mapping(envelope.get("typed_blocker")).get("blocker_type")
        ),
    }


def _provider_admission_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    candidates = _sequence(payload.get("provider_admission_candidates"))
    pending_count = _provider_pending_count(payload)
    return {
        "pending_count": pending_count,
        "candidate_count": len(candidates),
        "candidate_identity_bound": all(
            bool(_mapping(candidate).get("provider_admission_identity"))
            or bool(_mapping(candidate).get("stage_run_identity_packet"))
            for candidate in candidates
        )
        if candidates
        else False,
    }


def _strict_running_proof_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    control = _mapping(payload.get("opl_current_control_state"))
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    running = (
        control.get("running_provider_attempt") is True
        or handoff.get("running_provider_attempt") is True
    )
    return {
        "running_provider_attempt": bool(running),
        "active_run_id": _text(payload.get("active_run_id"))
        or _text(control.get("active_run_id"))
        or _text(handoff.get("active_run_id")),
        "attempt_id": _text(control.get("attempt_id")) or _text(handoff.get("attempt_id")),
        "workflow_id": _text(control.get("workflow_id")) or _text(handoff.get("workflow_id")),
    }


def _terminal_closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = _terminal_closeout_refs(payload)
    return {
        "ref_count": len(refs),
        "refs": refs,
    }


def _terminal_closeout_refs(payload: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "terminal_closeout_refs",
        "terminal_closeout_ref",
        "closeout_refs",
        "closeout_ref",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            refs.extend(_text_items(value))
    envelope = _mapping(payload.get("current_execution_envelope"))
    refs.extend(_text_items(envelope.get("terminal_closeout_refs") or []))
    if ref := _text(envelope.get("terminal_closeout_ref")):
        refs.append(ref)
    return sorted(dict.fromkeys(refs))


def _provider_pending_count(payload: Mapping[str, Any]) -> int:
    return _int(payload.get("provider_admission_pending_count"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _sequence_len(value: object) -> int:
    return len(_sequence(value))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(values: object) -> list[str]:
    return [
        text
        for value in _sequence(values)
        if (text := _text(value)) is not None
    ]


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


__all__ = [
    "DEFAULT_TARGET_STUDIES",
    "READ_ONLY_CONTRACT",
    "SURFACE_KIND",
    "build_live_supervisor_canary",
    "run_live_supervisor_canary",
]
