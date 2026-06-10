from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1
ARK_SURFACE_KIND = "mas_ark_progress_worker_advisory"
AUTOSCI_SURFACE_KIND = "mas_autosci_source_experiment_advisory"
ARK_FRAMEWORK_ID = "ark_progress_first"
AUTOSCI_FRAMEWORK_ID = "autosci_omegawiki"
ARK_SOURCE_CONTRACT_REF = (
    "med_autoscience.progress_first_external_learning_contract."
    "build_ark_progress_first_learning_contract"
)
AUTOSCI_SOURCE_PROJECTION_REF = (
    "med_autoscience.autosci_learning_projection.build_autosci_learning_projection"
)

ARK_REF_FAMILIES = (
    "micro_canary_ref",
    "human_decision_request_ref",
    "executor_real_run_closeout_ref",
    "citation_lifecycle_queue_ref",
    "semantic_no_progress_evidence_ref",
)
AUTOSCI_REF_FAMILIES = (
    "source_candidate_proposal_refs",
    "source_ingest_authorization_gap_refs",
    "experiment_lifecycle_receipt_refs",
    "negative_route_memory_refs",
    "artifact_render_qa_refs",
)

_ARK_REF_SUFFIXES = {
    "micro_canary_ref": "micro_canary",
    "human_decision_request_ref": "human_decision_request",
    "executor_real_run_closeout_ref": "executor_real_run_closeout",
    "citation_lifecycle_queue_ref": "citation_lifecycle_queue",
    "semantic_no_progress_evidence_ref": "semantic_no_progress_evidence",
}
_AUTOSCI_REF_SUFFIXES = {
    "source_candidate_proposal_refs": "source_candidate_proposal",
    "source_ingest_authorization_gap_refs": "source_ingest_authorization_gap",
    "experiment_lifecycle_receipt_refs": "experiment_lifecycle_receipt",
    "negative_route_memory_refs": "negative_route_memory",
    "artifact_render_qa_refs": "artifact_render_qa",
}

FORBIDDEN_WRITES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
)


def build_ark_progress_worker_advisory(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    context = _dispatch_context(dispatch)
    payload = _base_advisory(
        surface_kind=ARK_SURFACE_KIND,
        framework_id=ARK_FRAMEWORK_ID,
        dispatch=context,
    )
    payload["source_contract_ref"] = ARK_SOURCE_CONTRACT_REF
    payload["candidate_ref_families"] = list(ARK_REF_FAMILIES)
    for family in ARK_REF_FAMILIES:
        payload[family] = _candidate_ref(
            framework_id=ARK_FRAMEWORK_ID,
            dispatch_id=context["candidate_dispatch_id"],
            suffix=_ARK_REF_SUFFIXES[family],
        )
    return payload


def build_autosci_source_experiment_advisory(
    dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    context = _dispatch_context(dispatch)
    payload = _base_advisory(
        surface_kind=AUTOSCI_SURFACE_KIND,
        framework_id=AUTOSCI_FRAMEWORK_ID,
        dispatch=context,
    )
    payload["source_projection_ref"] = AUTOSCI_SOURCE_PROJECTION_REF
    payload["candidate_ref_families"] = list(AUTOSCI_REF_FAMILIES)
    for family in AUTOSCI_REF_FAMILIES:
        payload[family] = [
            _candidate_ref(
                framework_id=AUTOSCI_FRAMEWORK_ID,
                dispatch_id=context["candidate_dispatch_id"],
                suffix=_AUTOSCI_REF_SUFFIXES[family],
            )
        ]
    return payload


def _base_advisory(
    *,
    surface_kind: str,
    framework_id: str,
    dispatch: dict[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_refs_emitted",
        "framework_id": framework_id,
        "refs_only": True,
        "body_included": False,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "mainline_waits_for_worker": False,
        "can_block_current_owner_action": False,
        "current_owner_action": dispatch["current_owner_action"],
        "diagnostic": dispatch["diagnostic"],
        "allowed_writes": [],
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "written_refs": [],
        "authority_boundary": _authority_boundary(),
        "readiness_authorization": _readiness_authorization(),
    }


def _dispatch_context(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    dispatch_mapping = _mapping(dispatch)
    action_id = _dispatch_text(dispatch_mapping, "action_id")
    return {
        "candidate_dispatch_id": action_id or "unknown_dispatch",
        "current_owner_action": _current_owner_action(dispatch_mapping),
        "diagnostic": (
            {"reason": "missing_or_invalid_dispatch"} if not dispatch_mapping else None
        ),
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, str | None]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    return {
        "action_type": _dispatch_text(dispatch, "action_type"),
        "action_id": _dispatch_text(dispatch, "action_id"),
        "owner": _text(owner_route.get("owner")) or _dispatch_text(dispatch, "owner"),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "surface_role": "refs_only_progress_worker_candidate",
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_authorize_owner_action": False,
        "can_authorize_source_readiness": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_close_stage": False,
    }


def _readiness_authorization() -> dict[str, bool]:
    return {
        "may_authorize_publication_readiness": False,
        "may_authorize_source_readiness": False,
        "may_authorize_artifact_readiness": False,
        "may_authorize_artifact_mutation": False,
        "may_authorize_quality_verdict": False,
        "may_authorize_submission_readiness": False,
    }


def _candidate_ref(*, framework_id: str, dispatch_id: str, suffix: str) -> str:
    return f"external-learning:{framework_id}:{dispatch_id}:{suffix}"


def _dispatch_text(dispatch: Mapping[str, Any], key: str) -> str | None:
    return _text(dispatch.get(key)) or _text(_mapping(dispatch.get("source_action")).get(key))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ARK_FRAMEWORK_ID",
    "ARK_REF_FAMILIES",
    "ARK_SOURCE_CONTRACT_REF",
    "ARK_SURFACE_KIND",
    "AUTOSCI_FRAMEWORK_ID",
    "AUTOSCI_REF_FAMILIES",
    "AUTOSCI_SOURCE_PROJECTION_REF",
    "AUTOSCI_SURFACE_KIND",
    "FORBIDDEN_WRITES",
    "SCHEMA_VERSION",
    "build_ark_progress_worker_advisory",
    "build_autosci_source_experiment_advisory",
]
