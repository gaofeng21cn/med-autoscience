from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.ars_learning_projection import build_ars_learning_projection
from med_autoscience.external_learning_adoption_closure import FORBIDDEN_WRITES


SCHEMA_VERSION = 1
ARS_SURFACE_KIND = "mas_ars_claim_support_advisory"
ARIS_SURFACE_KIND = "mas_aris_review_import_advisory"
ARS_CALLABLE_REF = (
    "med_autoscience.external_learning_review_advisory."
    "build_ars_claim_support_advisory"
)
ARIS_CALLABLE_REF = (
    "med_autoscience.external_learning_review_advisory."
    "build_aris_review_import_advisory"
)

ARS_FRAMEWORK_ID = "academic_research_skills"
ARIS_FRAMEWORK_ID = "aris"

_ARS_UNSUPPORTED_CLAIM_GAP_REFS = (
    "paper/evidence/evidence_ledger.json#unsupported_claim_gap_refs",
    "paper/review/review_ledger.json#unsupported_claim_gap_refs",
    "artifacts/publication_eval/latest.json#unsupported_claims",
)

_FORBIDDEN_AUTHORITY = (
    "domain_truth",
    "publication_eval",
    "controller_decisions",
    "paper_or_package",
    "evidence_ledger",
    "review_ledger",
    "memory_body",
    "artifact_body",
    "owner_receipt",
    "typed_blocker",
    "current_owner_action",
    "source_readiness",
    "publication_quality",
    "publication_readiness",
    "submission_readiness",
    "artifact_authority",
    "quality_gate_closure",
    "stage_closure",
)

_AUTHORITY_FALSE_FLAGS = (
    "can_write_domain_truth",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_write_paper_or_package",
    "can_write_evidence_ledger",
    "can_write_review_ledger",
    "can_write_memory_body",
    "can_write_artifact_body",
    "can_write_owner_receipt",
    "can_write_typed_blocker",
    "can_authorize_current_owner_action",
    "can_authorize_source_readiness",
    "can_authorize_publication_quality",
    "can_authorize_publication_readiness",
    "can_authorize_submission_readiness",
    "can_authorize_artifact_authority",
    "can_close_quality_gate",
    "can_close_stage",
)


def build_ars_claim_support_advisory(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    dispatch_payload = _mapping(dispatch)
    has_dispatch_input = bool(dispatch_payload)
    projection = build_ars_learning_projection()
    truth_mapping = _mapping(projection.get("truth_surface_mapping"))

    claim_support_audit_refs = _unique_refs(
        [
            *_refs_from_dispatch(dispatch_payload, "ars_refs", "claim_support_audit_refs"),
            *(truth_mapping.get("claim_support_audit_refs") if has_dispatch_input else []),
        ]
    )
    data_access_oversight_refs = _unique_refs(
        [
            *_refs_from_dispatch(dispatch_payload, "ars_refs", "data_access_oversight_refs"),
            *(truth_mapping.get("data_access_oversight_refs") if has_dispatch_input else []),
        ]
    )
    material_passport_refs = _unique_refs(
        [
            *_refs_from_dispatch(dispatch_payload, "ars_refs", "material_passport_refs"),
            *_refs_from_dispatch(
                dispatch_payload, "ars_refs", "medical_material_passport_refs"
            ),
            *(truth_mapping.get("medical_material_passport_refs") if has_dispatch_input else []),
        ]
    )
    unsupported_claim_gap_refs = _unique_refs(
        [
            *_refs_from_dispatch(dispatch_payload, "ars_refs", "unsupported_claim_gap_refs"),
            *(_ARS_UNSUPPORTED_CLAIM_GAP_REFS if has_dispatch_input else []),
        ]
    )

    return {
        **_base_advisory(
            surface_kind=ARS_SURFACE_KIND,
            framework_id=ARS_FRAMEWORK_ID,
            callable_ref=ARS_CALLABLE_REF,
            dispatch=dispatch_payload,
            has_dispatch_input=has_dispatch_input,
        ),
        "source_projection_ref": (
            "med_autoscience.ars_learning_projection.build_ars_learning_projection"
        ),
        "source_projection_status": projection.get("status"),
        "claim_support_audit_refs": claim_support_audit_refs,
        "data_access_oversight_refs": data_access_oversight_refs,
        "material_passport_refs": material_passport_refs,
        "unsupported_claim_gap_refs": unsupported_claim_gap_refs,
        "output_ref_keys": [
            "claim_support_audit_refs",
            "data_access_oversight_refs",
            "material_passport_refs",
            "unsupported_claim_gap_refs",
        ],
    }


def build_aris_review_import_advisory(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    dispatch_payload = _mapping(dispatch)
    has_dispatch_input = bool(dispatch_payload)
    context_ref = _context_ref(dispatch_payload) if has_dispatch_input else None

    typed_input_contract_ref = (
        _single_ref_from_dispatch(dispatch_payload, "aris_refs", "typed_input_contract_ref")
        or (f"external-learning:aris:{context_ref}:typed-input-contract" if context_ref else None)
    )
    result_import_receipt_ref = (
        _single_ref_from_dispatch(dispatch_payload, "aris_refs", "result_import_receipt_ref")
        or (f"external-learning:aris:{context_ref}:result-import-receipt" if context_ref else None)
    )
    cross_model_reviewer_receipt_refs = _unique_refs(
        [
            *_refs_from_dispatch(
                dispatch_payload, "aris_refs", "cross_model_reviewer_receipt_refs"
            ),
            *(
                [f"external-learning:aris:{context_ref}:cross-model-reviewer-receipt"]
                if context_ref
                else []
            ),
        ]
    )
    experiment_queue_hint_refs = _unique_refs(
        [
            *_refs_from_dispatch(dispatch_payload, "aris_refs", "experiment_queue_hint_refs"),
            *_refs_from_dispatch(dispatch_payload, "aris_refs", "experiment_queue_refs"),
            *(
                [
                    "artifacts/analysis_queue/latest.json#aris_experiment_queue_hint",
                    f"external-learning:aris:{context_ref}:experiment-queue-hint",
                ]
                if context_ref
                else []
            ),
        ]
    )

    return {
        **_base_advisory(
            surface_kind=ARIS_SURFACE_KIND,
            framework_id=ARIS_FRAMEWORK_ID,
            callable_ref=ARIS_CALLABLE_REF,
            dispatch=dispatch_payload,
            has_dispatch_input=has_dispatch_input,
        ),
        "source_projection_ref": (
            "med_autoscience.external_learning_adoption_closure."
            "build_external_learning_adoption_closure#frameworks.aris"
        ),
        "typed_input_contract_ref": typed_input_contract_ref,
        "result_import_receipt_ref": result_import_receipt_ref,
        "cross_model_reviewer_receipt_refs": cross_model_reviewer_receipt_refs,
        "experiment_queue_hint_refs": experiment_queue_hint_refs,
        "output_ref_keys": [
            "typed_input_contract_ref",
            "result_import_receipt_ref",
            "cross_model_reviewer_receipt_refs",
            "experiment_queue_hint_refs",
        ],
    }


def _base_advisory(
    *,
    surface_kind: str,
    framework_id: str,
    callable_ref: str,
    dispatch: Mapping[str, Any],
    has_dispatch_input: bool,
) -> dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if has_dispatch_input else "skipped_missing_dispatch",
        "framework_id": framework_id,
        "callable_ref": callable_ref,
        "refs_only": True,
        "body_included": False,
        "advisory_only": True,
        "can_block_current_owner_action": False,
        "mainline_waits_for_advisory": False,
        "allowed_writes": [],
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "forbidden_authority": list(_FORBIDDEN_AUTHORITY),
        "current_owner_action": _current_owner_action(dispatch),
        "missing_inputs": [] if has_dispatch_input else ["dispatch"],
        "failure_policy": "fail_open_continue_current_owner_action",
        "authority_boundary": _authority_boundary(),
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "surface_role": "refs_only_review_claim_support_advisory",
        **{flag: False for flag in _AUTHORITY_FALSE_FLAGS},
        "forbidden_authority": list(_FORBIDDEN_AUTHORITY),
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    source_action = _mapping(dispatch.get("source_action"))
    return {
        "action_type": _text(dispatch.get("action_type"))
        or _text(source_action.get("action_type")),
        "action_id": _text(dispatch.get("action_id")) or _text(source_action.get("action_id")),
        "owner": _text(owner_route.get("owner")) or _text(dispatch.get("owner")),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _refs_from_dispatch(dispatch: Mapping[str, Any], namespace: str, key: str) -> list[str]:
    refs: list[str] = []
    source_action = _mapping(dispatch.get("source_action"))
    for source in (
        dispatch,
        _mapping(dispatch.get("refs")),
        _mapping(dispatch.get("advisory_refs")),
        _mapping(dispatch.get(namespace)),
        source_action,
        _mapping(source_action.get("refs")),
        _mapping(source_action.get("advisory_refs")),
        _mapping(source_action.get(namespace)),
    ):
        refs.extend(_text_list(source.get(key)))
    return _unique_refs(refs)


def _single_ref_from_dispatch(dispatch: Mapping[str, Any], namespace: str, key: str) -> str | None:
    refs = _refs_from_dispatch(dispatch, namespace, key)
    return refs[0] if refs else None


def _context_ref(dispatch: Mapping[str, Any]) -> str:
    current_owner = _current_owner_action(dispatch)
    raw_ref = (
        current_owner.get("work_unit_fingerprint")
        or current_owner.get("work_unit_id")
        or current_owner.get("action_id")
        or current_owner.get("action_type")
        or "unbound-dispatch"
    )
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "-", str(raw_ref)).strip("-") or "unbound-dispatch"


def _unique_refs(values: Sequence[Any] | Any) -> list[str]:
    refs: list[str] = []
    for value in _iter_values(values):
        text = _text(value)
        if text is not None and text not in refs:
            refs.append(text)
    return refs


def _text_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return _unique_refs(
            [
                value.get("ref"),
                value.get("source_ref"),
                value.get("path"),
                value.get("href"),
            ]
        )
    if isinstance(value, str):
        return [value] if _text(value) else []
    if isinstance(value, Sequence):
        refs: list[str] = []
        for item in value:
            refs.extend(_text_list(item))
        return _unique_refs(refs)
    return [_text(value)] if _text(value) else []


def _iter_values(values: Sequence[Any] | Any) -> list[Any]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, Sequence):
        return list(values)
    return [values]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ARIS_CALLABLE_REF",
    "ARIS_FRAMEWORK_ID",
    "ARIS_SURFACE_KIND",
    "ARS_CALLABLE_REF",
    "ARS_FRAMEWORK_ID",
    "ARS_SURFACE_KIND",
    "SCHEMA_VERSION",
    "build_aris_review_import_advisory",
    "build_ars_claim_support_advisory",
]
