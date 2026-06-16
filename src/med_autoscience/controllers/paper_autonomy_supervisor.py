from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any


SURFACE_KIND = "paper_autonomy_supervisor_decision"
OBLIGATION_SURFACE_KIND = "paper_autonomy_obligation"
SCHEMA_VERSION = 1
SOURCE_OF_TRUTH_CHAIN = (
    "DomainIntent",
    "OPL Command/Event/Outbox/StageRun",
    "MAS OwnerAnswer",
    "Derived Projection",
)

ALLOWED_DECISIONS = {
    "execute_current_owner_delta",
    "consume_terminal_closeout",
    "materialize_recovery_action",
    "wait_for_owner_with_resume_token",
    "stop_with_stable_typed_blocker",
    "stop_with_owner_receipt",
}

FORBIDDEN_TERMINAL_INTERPRETATIONS = [
    "operator_decision_required",
    "human_gate",
    "typed_blocker",
    "provider_admission_pending_count=0",
    "action_queue=[]",
    "queue_empty",
    "idle",
    "observe_only",
    "read_model_refreshed",
]

AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_paper_progress_policy_projection",
    "authority_role": "paper_policy_projection_only_opl_transition_runtime_consumer",
    "adapter_kind": "mas_policy_adapter",
    "projection_role": "derived_policy_adapter_projection",
    "opl_transition_runtime_owner": "one-person-lab",
    "opl_recovery_obligation_store_owner": "one-person-lab",
    "opl_human_gate_transport_owner": "one-person-lab",
    "opl_stage_run_owner": "one-person-lab",
    "top_level_truth": "decision",
    "allowed_decisions": sorted(ALLOWED_DECISIONS),
    "read_models_can_create_decision": False,
    "can_store_recovery_obligation": False,
    "can_generate_supervisor_decision_authority": False,
    "provider_admission_requires_execute_decision": True,
    "provider_admission_requires_opl_stage_run_readback": True,
    "provider_completion_is_paper_progress": False,
    "can_write_study_truth": False,
    "can_authorize_publication_ready": False,
    "can_write_paper_or_package": False,
    "can_own_generic_event_log_or_outbox": False,
    "can_create_opl_command_event_or_outbox": False,
    "can_own_stage_run": False,
    "can_generate_human_gate_resume_token": False,
    "can_run_fixed_point_runtime": False,
}


def build_supervisor_decision(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any] | None = None,
    diagnostic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    progress = _mapping(payload)
    diagnostic = _mapping(diagnostic_report)
    recovery = _mapping(paper_recovery_state) or _mapping(progress.get("paper_recovery_state"))
    if not recovery:
        recovery = _build_paper_recovery_state(progress, diagnostic_report=diagnostic)
    obligation = build_paper_autonomy_obligation(progress, paper_recovery_state=recovery)
    phase = _text(recovery.get("phase"))
    next_safe_action = _mapping(recovery.get("next_safe_action"))

    if phase == "terminal_closeout_ready":
        return _decision(
            progress,
            recovery,
            obligation,
            decision="consume_terminal_closeout",
            next_owner="MedAutoScience",
            next_safe_action="consume_or_reject_terminal_closeout",
            evidence_refs=[
                _obligation_ref(obligation),
                *_evidence_refs(recovery),
            ],
            paper_progress_classification="depends_on_mas_closeout_consumer_output",
            platform_repair_classification="transport_closeout_consumption",
        )

    if phase == "owner_receipt_recorded":
        owner_receipt_ref = _owner_receipt_ref(recovery)
        return _decision(
            progress,
            recovery,
            obligation,
            decision="stop_with_owner_receipt",
            next_owner=_owner(recovery, obligation) or "MedAutoScience",
            next_safe_action={
                "kind": "consume_owner_receipt",
                "owner_receipt_ref": owner_receipt_ref,
            },
            evidence_refs=[
                _obligation_ref(obligation),
                *_owner_receipt_refs(recovery),
            ],
            paper_progress_classification="mas_owner_receipt_credit",
            platform_repair_classification="none",
        )

    if phase == "human_gate" or _resume_token_payload(progress, recovery):
        resume = _resume_token_payload(progress, recovery)
        resume_token = _text(resume.get("resume_token"))
        human_gate_ref = _first_text(
            resume.get("human_gate_ref"),
            *_evidence_refs(recovery),
        )
        next_safe_action = _clean_mapping(
            {
                "kind": "consume_opl_human_gate_resume_token",
                "resume_token": resume_token,
                "human_gate_ref": human_gate_ref,
                "resume_token_owner": "one-person-lab",
                "mas_can_generate_resume_token": False,
                "allowed_decisions": [
                    "materialize_recovery_action",
                    "stop_with_stable_typed_blocker",
                ],
                "timeout_policy": _timeout_policy(progress),
                "default_safe_branch": "stop_with_stable_typed_blocker",
                "current_identity": _identity(obligation),
            }
        )
        return _decision(
            progress,
            recovery,
            obligation,
            decision="wait_for_owner_with_resume_token",
            next_owner=_owner(recovery, obligation) or "Human or named owner",
            next_safe_action=next_safe_action,
            evidence_refs=[
                _obligation_ref(obligation),
                *_human_gate_refs(progress, recovery),
            ],
            paper_progress_classification="human_gate_pending_no_credit",
            platform_repair_classification="wait_state",
        )

    if phase == "admission_pending" or phase == "attempt_running":
        execute_ready, missing = _execute_decision_ready(progress, recovery, obligation)
        if execute_ready:
            return _decision(
                progress,
                recovery,
                obligation,
                decision="execute_current_owner_delta",
                next_owner="OPL Framework",
                next_safe_action="admit_or_resume_stage_run",
                evidence_refs=[
                    _obligation_ref(obligation),
                    *_provider_admission_refs(progress),
                    *_stage_run_identity_refs(progress, recovery),
                    *_running_proof_refs(progress, recovery),
                ],
                paper_progress_classification="none_until_mas_owner_result",
                platform_repair_classification="transport_execution",
            )
        return _decision(
            progress,
            recovery,
            obligation,
            decision="materialize_recovery_action",
            next_owner="MedAutoScience / OPL Framework",
            next_safe_action={
                "kind": "materialize_recovery_work_unit_or_receipt",
                "recovery_kind": "opl_runtime_repair",
                "required_evidence": missing,
            },
            evidence_refs=[
                _obligation_ref(obligation),
                *_provider_admission_refs(progress),
            ],
            missing_evidence_refs=missing,
            paper_progress_classification="none_until_owner_receipt_or_stable_blocker",
            platform_repair_classification="platform_repair_delta",
        )

    if _stable_stop_decision(recovery):
        return _decision(
            progress,
            recovery,
            obligation,
            decision="stop_with_stable_typed_blocker",
            next_owner=_owner(recovery, obligation) or "MedAutoScience / OPL Framework",
            next_safe_action="publish_stable_blocker_and_stop_same_identity_redrive",
            evidence_refs=[
                _obligation_ref(obligation),
                *_typed_blocker_refs(progress, recovery),
            ],
            paper_progress_classification="stable_stop_loss_credit",
            platform_repair_classification="stop_loss",
        )

    return _decision(
        progress,
        recovery,
        obligation,
        decision="materialize_recovery_action",
        next_owner=_materialization_owner(recovery, obligation),
        next_safe_action={
            "kind": "materialize_recovery_work_unit_or_receipt",
            "recovery_kind": _recovery_kind(recovery),
            "source_next_safe_action": _clean_mapping(next_safe_action),
        },
        evidence_refs=[
            _obligation_ref(obligation),
            *_evidence_refs(recovery),
            *_no_progress_refs(progress, diagnostic),
        ],
        paper_progress_classification="none_until_owner_receipt_or_stable_blocker",
        platform_repair_classification="platform_repair_delta",
    )


def build_paper_autonomy_obligation(
    payload: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    progress = _mapping(payload)
    recovery = _mapping(paper_recovery_state) or _mapping(progress.get("paper_recovery_state"))
    recovery_obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    currentness_basis = (
        _mapping(recovery_obligation.get("currentness_basis"))
        or _mapping(current_work_unit.get("owner_route_currentness_basis"))
        or _mapping(current_work_unit.get("currentness_basis"))
    )
    study_id = _first_text(
        recovery_obligation.get("study_id"),
        recovery.get("study_id"),
        progress.get("study_id"),
        current_work_unit.get("study_id"),
        current_work_unit.get("quest_id"),
    )
    quest_id = _first_text(
        recovery_obligation.get("quest_id"),
        recovery.get("quest_id"),
        progress.get("quest_id"),
        current_work_unit.get("quest_id"),
        study_id,
    )
    stage_id = _first_text(
        current_work_unit.get("stage_id"),
        _mapping(progress.get("current_owner_delta")).get("stage_id"),
        _mapping(progress.get("stage_kernel_projection")).get("stage_id"),
        "publication_supervision",
    )
    action_type = _first_text(
        recovery_obligation.get("action_type"),
        current_work_unit.get("action_type"),
        _mapping(progress.get("current_executable_owner_action")).get("action_type"),
    )
    work_unit_id = _first_text(
        recovery_obligation.get("work_unit_id"),
        current_work_unit.get("work_unit_id"),
        _mapping(progress.get("current_executable_owner_action")).get("work_unit_id"),
    )
    fingerprint = _first_text(
        recovery_obligation.get("work_unit_fingerprint"),
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        currentness_basis.get("source_fingerprint"),
    )
    provider_identity = _provider_admission_identity(
        progress,
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    route_identity_key = _first_text(
        currentness_basis.get("route_identity_key"),
        current_work_unit.get("route_identity_key"),
        provider_identity.get("route_identity_key"),
        f"{study_id}:{action_type}:{work_unit_id}:{fingerprint}"
        if study_id and action_type and work_unit_id and fingerprint
        else None,
    )
    attempt_idempotency_key = _first_text(
        currentness_basis.get("attempt_idempotency_key"),
        currentness_basis.get("idempotency_key"),
        current_work_unit.get("attempt_idempotency_key"),
        current_work_unit.get("idempotency_key"),
        provider_identity.get("attempt_idempotency_key"),
        provider_identity.get("route_identity_key"),
    )
    currentness_basis = _clean_mapping(
        {
            **dict(currentness_basis),
            "route_identity_key": route_identity_key,
            "attempt_idempotency_key": attempt_idempotency_key,
        }
    )
    identity = {
        "study_id": study_id,
        "quest_id": quest_id,
        "stage_id": stage_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
        "owner_route_currentness_basis": _clean_mapping(currentness_basis),
    }
    obligation_id = _paper_autonomy_obligation_id(identity)
    owner = _first_text(
        recovery_obligation.get("owner"),
        _mapping(recovery.get("current_authority")).get("owner"),
        current_work_unit.get("owner"),
    )
    return _clean_mapping(
        {
            "surface_kind": OBLIGATION_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "paper_autonomy_obligation_id": obligation_id,
            "recovery_obligation_id": _text(recovery.get("recovery_obligation_id"))
            or _text(recovery_obligation.get("recovery_obligation_id")),
            **identity,
            "desired_delta": {
                "owner": owner,
                "target_surface": _target_surface(progress, recovery),
                "required_output_ref_family": _required_output_ref_family(progress),
            },
            "expected_next_evidence_allowed": [
                "provider_admission_identity",
                "running_proof",
                "terminal_closeout",
                "owner_receipt",
                "typed_blocker",
                "human_gate_ref",
                "route_back_evidence_ref",
                "migration_receipt",
            ],
            "timeout_policy": _timeout_policy(progress),
            "source_recovery_phase": _text(recovery.get("phase")),
        }
    )


def _decision(
    progress: Mapping[str, Any],
    recovery: Mapping[str, Any],
    obligation: Mapping[str, Any],
    *,
    decision: str,
    next_owner: str,
    next_safe_action: str | Mapping[str, Any],
    evidence_refs: list[str],
    paper_progress_classification: str,
    platform_repair_classification: str,
    missing_evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"unsupported supervisor decision: {decision}")
    evidence = _dedupe([ref for ref in evidence_refs if ref])
    payload = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "projection_role": "mas_policy_adapter_decision_projection",
        "authority": False,
        "source_of_truth_chain": list(SOURCE_OF_TRUTH_CHAIN),
        "runtime_substrate_owner": "one-person-lab",
        "decision_id": _decision_id(obligation, decision=decision, evidence_refs=evidence),
        "decision": decision,
        "identity_match": _identity_complete(obligation),
        "paper_autonomy_obligation": dict(obligation),
        "paper_autonomy_obligation_ref": _obligation_ref(obligation),
        "source_recovery_obligation_ref": _text(obligation.get("recovery_obligation_id")),
        "source_paper_recovery_phase": _text(recovery.get("phase")),
        "evidence_refs": evidence,
        "missing_evidence_refs": _dedupe(missing_evidence_refs or []),
        "forbidden_interpretations": _forbidden_interpretations(progress),
        "next_owner": next_owner,
        "next_safe_action": (
            {"kind": next_safe_action}
            if isinstance(next_safe_action, str)
            else _clean_mapping(next_safe_action)
        ),
        "paper_progress_classification": paper_progress_classification,
        "platform_repair_classification": platform_repair_classification,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    return _clean_mapping(payload)


def _execute_decision_ready(
    progress: Mapping[str, Any],
    recovery: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    missing: list[str] = []
    if not _provider_admission_refs(progress):
        missing.append("provider_admission_identity")
    if not _admission_obligation_identity_complete(obligation):
        missing.append("complete_paper_autonomy_obligation_identity")
    if not _stage_run_identity_refs(progress, recovery):
        missing.append("opl_stage_run_readback")
    if _terminal_closeout_refs(progress, recovery):
        missing.append("no_terminal_closeout_for_same_identity")
    return not missing, missing


def _admission_obligation_identity_complete(obligation: Mapping[str, Any]) -> bool:
    return all(
        _text(obligation.get(key)) is not None
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
    )


def _stable_stop_decision(recovery: Mapping[str, Any]) -> bool:
    phase = _text(recovery.get("phase"))
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if phase == "domain_blocked" and _text(next_safe_action.get("kind")) == "run_mas_owner_callable":
        return False
    if phase in {"domain_blocked", "admission_blocked"}:
        return _text(next_safe_action.get("kind")) in {
            "resolve_typed_blocker",
            "honor_stable_typed_blocker",
            "publish_stable_blocker_and_stop_same_identity_redrive",
        }
    return False


def _materialization_owner(recovery: Mapping[str, Any], obligation: Mapping[str, Any]) -> str:
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    return (
        _text(next_safe_action.get("owner"))
        or _owner(recovery, obligation)
        or "MedAutoScience / OPL Framework"
    )


def _recovery_kind(recovery: Mapping[str, Any]) -> str:
    phase = _text(recovery.get("phase"))
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    kind = _text(next_safe_action.get("kind"))
    if kind == "run_mas_owner_callable":
        return "mas_control_plane_repair"
    if phase in {"admission_blocked", "projection_inconsistent"}:
        return "opl_runtime_repair"
    if phase == "manual_foreground_unadopted":
        return "operator_policy_materialization"
    return "mas_control_plane_repair"


def _build_paper_recovery_state(
    progress: Mapping[str, Any],
    *,
    diagnostic_report: Mapping[str, Any],
) -> dict[str, Any]:
    from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state

    return build_paper_recovery_state(progress, diagnostic_report=diagnostic_report)


def _paper_autonomy_obligation_id(identity: Mapping[str, Any]) -> str:
    return "::".join(
        [
            "paper-autonomy",
            _text(identity.get("study_id")) or "unknown-study",
            _text(identity.get("stage_id")) or "unknown-stage",
            _text(identity.get("action_type")) or "unknown-action",
            _text(identity.get("work_unit_id")) or "unknown-work-unit",
            _text(identity.get("work_unit_fingerprint")) or _short_hash(identity),
        ]
    )


def _decision_id(
    obligation: Mapping[str, Any],
    *,
    decision: str,
    evidence_refs: list[str],
) -> str:
    return "::".join(
        [
            "supervisor-decision",
            decision,
            _text(obligation.get("paper_autonomy_obligation_id")) or _short_hash(obligation),
            _short_hash({"evidence_refs": evidence_refs}),
        ]
    )


def _obligation_ref(obligation: Mapping[str, Any]) -> str:
    return _text(obligation.get("paper_autonomy_obligation_id")) or _short_hash(obligation)


def _identity(obligation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: obligation.get(key)
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
        if obligation.get(key) not in (None, "", [], {})
    }


def _identity_complete(obligation: Mapping[str, Any]) -> bool:
    required = [
        "study_id",
        "quest_id",
        "stage_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
    ]
    return all(_text(obligation.get(key)) is not None for key in required)


def _target_surface(progress: Mapping[str, Any], recovery: Mapping[str, Any]) -> dict[str, Any]:
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    owner_callable = _mapping(next_safe_action.get("owner_callable"))
    if owner_callable:
        return _clean_mapping(
            {
                "surface_ref": owner_callable.get("callable_surface"),
                "action_id": owner_callable.get("action_id"),
            }
        )
    action = _mapping(progress.get("current_executable_owner_action"))
    target = _mapping(action.get("target_surface"))
    return _clean_mapping(target or {"surface_ref": action.get("target_surface_ref")})


def _required_output_ref_family(progress: Mapping[str, Any]) -> list[str]:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    contract = _mapping(current_work_unit.get("required_output_contract"))
    values = _text_items(contract.get("accepted_return_shape"))
    return values or [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]


def _resume_token_payload(
    progress: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> Mapping[str, Any]:
    for candidate in (
        recovery.get("human_gate"),
        recovery.get("resume_token"),
        progress.get("human_gate"),
        progress.get("human_gate_transport"),
        progress.get("owner_gate_resume"),
    ):
        mapping = _mapping(candidate)
        if mapping:
            return mapping
    return {}


def _timeout_policy(progress: Mapping[str, Any]) -> dict[str, Any]:
    policy = _mapping(progress.get("timeout_policy"))
    return _clean_mapping(
        policy
        or {
            "heartbeat_budget": "not_configured",
            "wall_clock_budget_seconds": "not_configured",
            "on_timeout": "stop_with_stable_typed_blocker",
        }
    )


def _provider_admission_refs(progress: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for candidate in progress.get("provider_admission_candidates") or []:
        item = _mapping(candidate)
        refs.extend(
            [
                _text(item.get("provider_admission_ref")),
                _text(item.get("stage_packet_ref")),
                _text(item.get("selected_dispatch_ref")),
                _text(item.get("dispatch_ref")),
            ]
        )
        refs.extend(_text_items(item.get("stage_packet_refs")))
    admission = _mapping(progress.get("owner_action_admission"))
    refs.extend(
        [
            _text(admission.get("provider_admission_ref")),
            _text(admission.get("stage_packet_ref")),
            _text(admission.get("selected_dispatch_ref")),
        ]
    )
    if _mapping(progress.get("current_work_unit")).get("state"):
        state = _mapping(_mapping(progress.get("current_work_unit")).get("state"))
        if state.get("provider_admission_pending") is True:
            refs.append("current_work_unit.provider_admission_pending")
    return _dedupe(refs)


def _provider_admission_identity(
    progress: Mapping[str, Any],
    *,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    fingerprint: str | None,
) -> Mapping[str, Any]:
    for candidate in progress.get("provider_admission_candidates") or []:
        item = _mapping(candidate)
        if not item:
            continue
        candidate_study_id = _first_text(item.get("study_id"), item.get("quest_id"))
        if study_id is not None and candidate_study_id != study_id:
            continue
        if action_type is not None and _text(item.get("action_type")) != action_type:
            continue
        if work_unit_id is not None and _text(item.get("work_unit_id")) != work_unit_id:
            continue
        candidate_fingerprint = _first_text(
            item.get("work_unit_fingerprint"),
            item.get("action_fingerprint"),
        )
        if fingerprint is not None and candidate_fingerprint != fingerprint:
            continue
        owner_route = _mapping(item.get("owner_route"))
        source_refs = _mapping(owner_route.get("source_refs"))
        currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
        return _clean_mapping(
            {
                "route_identity_key": _first_text(
                    item.get("route_identity_key"),
                    source_refs.get("route_identity_key"),
                    currentness_basis.get("route_identity_key"),
                ),
                "attempt_idempotency_key": _first_text(
                    item.get("attempt_idempotency_key"),
                    source_refs.get("attempt_idempotency_key"),
                    currentness_basis.get("attempt_idempotency_key"),
                    currentness_basis.get("idempotency_key"),
                ),
            }
        )
    return {}


def _stage_run_identity_refs(progress: Mapping[str, Any], recovery: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "stage_run_identity_packet",
        "stage_run_identity",
        "active_stage_attempt",
        "opl_current_control_state_handoff",
    ):
        item = _mapping(progress.get(key)) or _mapping(recovery.get(key))
        refs.extend(
            [
                _text(item.get("stage_run_identity_packet_ref")),
                _text(item.get("stage_run_id")),
                _text(item.get("stage_attempt_id")),
                _text(item.get("active_stage_attempt_id")),
                _text(item.get("lease_ref")),
                _text(item.get("provider_attempt_ref")),
                _text(item.get("workflow_id")),
            ]
        )
    return _dedupe(refs)


def _running_proof_refs(progress: Mapping[str, Any], recovery: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "running_provider_attempt",
        "provider_attempt_running_proof",
        "opl_current_control_state_handoff",
    ):
        value = progress.get(key) if key in progress else recovery.get(key)
        item = _mapping(value)
        if value is True:
            refs.append(key)
        refs.extend(
            [
                _text(item.get("running_proof_ref")),
                _text(item.get("active_run_id")),
                _text(item.get("active_stage_attempt_id")),
            ]
        )
        if item.get("running_provider_attempt") is True:
            refs.append(f"{key}.running_provider_attempt")
    return _dedupe(refs)


def _terminal_closeout_refs(progress: Mapping[str, Any], recovery: Mapping[str, Any]) -> list[str]:
    refs = []
    for source in (progress, recovery):
        for key in (
            "terminal_closeout",
            "terminal_closeout_precedence_evidence",
            "accepted_closeout_evidence",
        ):
            value = source.get(key)
            if isinstance(value, list):
                for item in value:
                    refs.extend(_closeout_ref_items(_mapping(item)))
            else:
                refs.extend(_closeout_ref_items(_mapping(value)))
    return _dedupe(refs)


def _closeout_ref_items(item: Mapping[str, Any]) -> list[str]:
    return [
        ref
        for ref in (
            _text(item.get("closeout_ref")),
            _text(item.get("source_path")),
            _text(item.get("receipt_ref")),
            *_text_items(item.get("closeout_refs")),
        )
        if ref
    ]


def _owner_receipt_refs(recovery: Mapping[str, Any]) -> list[str]:
    return _dedupe([_owner_receipt_ref(recovery), *_evidence_refs(recovery)])


def _owner_receipt_ref(recovery: Mapping[str, Any]) -> str | None:
    next_action = _mapping(recovery.get("next_safe_action"))
    return _first_text(next_action.get("owner_receipt_ref"), recovery.get("owner_receipt_ref"))


def _typed_blocker_refs(progress: Mapping[str, Any], recovery: Mapping[str, Any]) -> list[str]:
    refs = list(_evidence_refs(recovery))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    typed_blocker = _mapping(_mapping(current_work_unit.get("state")).get("typed_blocker")) or _mapping(
        current_work_unit.get("typed_blocker")
    )
    refs.extend(
        [
            _text(typed_blocker.get("typed_blocker_ref")),
            _text(typed_blocker.get("source_ref")),
            _text(typed_blocker.get("latest_owner_answer_ref")),
        ]
    )
    if not refs and _text(recovery.get("phase")) == "domain_blocked":
        refs.append("paper_recovery_state.domain_blocked")
    return _dedupe(refs)


def _human_gate_refs(progress: Mapping[str, Any], recovery: Mapping[str, Any]) -> list[str]:
    refs = list(_evidence_refs(recovery))
    for source in (progress, recovery):
        for key in ("human_gate_ref", "owner_gate_decision_ref", "route_back_evidence_ref"):
            text = _text(source.get(key))
            if text:
                refs.append(text)
    resume = _resume_token_payload(progress, recovery)
    refs.append(_text(resume.get("human_gate_ref")))
    return _dedupe(refs)


def _evidence_refs(recovery: Mapping[str, Any]) -> list[str]:
    return _dedupe(_text_items(recovery.get("evidence_refs")))


def _no_progress_refs(progress: Mapping[str, Any], diagnostic: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(progress.get("no_progress_ref")),
        _text(diagnostic.get("no_progress_ref")),
        _text(diagnostic.get("report_ref")),
    ]
    if progress.get("provider_admission_pending_count") == 0:
        refs.append("provider_admission_pending_count=0")
    if progress.get("action_queue") == []:
        refs.append("action_queue=[]")
    return _dedupe(refs)


def _forbidden_interpretations(progress: Mapping[str, Any]) -> list[str]:
    forbidden = list(FORBIDDEN_TERMINAL_INTERPRETATIONS)
    if progress.get("provider_admission_pending_count") == 0:
        forbidden.append("provider_admission_pending_count=0_is_not_terminal")
    if progress.get("action_queue") == []:
        forbidden.append("action_queue=[]_is_not_terminal")
    return _dedupe(forbidden)


def _owner(recovery: Mapping[str, Any], obligation: Mapping[str, Any]) -> str | None:
    return _first_text(
        _mapping(recovery.get("current_authority")).get("owner"),
        _mapping(obligation.get("desired_delta")).get("owner"),
    )


def _clean_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in dict(value).items()
        if value not in (None, "", [], {})
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _first_text(*values: Any) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _dedupe(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _short_hash(value: Any) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()[:16]


__all__ = [
    "build_paper_autonomy_obligation",
    "build_supervisor_decision",
]
