from __future__ import annotations

import json
from typing import Any, Mapping

from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    mapping,
    sequence,
    text,
    texts,
    unique,
)


def stage_attempt_closeout_typed_blocker_evidence(
    *,
    profile: Any,
    study_id: str,
    target_identity: Mapping[str, Any],
    dispatch_identity: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any] | None:
    stage_attempt_id = text(target_identity.get("stage_attempt_id"))
    if stage_attempt_id is None or action_type is None:
        return None
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json"
    )
    closeout = _read_json_object(closeout_path)
    if closeout is None:
        return None
    domain_blocker = mapping(closeout.get("domain_blocker"))
    typed_blocker_ref = text(closeout.get("typed_blocker_ref"))
    if (
        text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet"
        or text(closeout.get("stage_attempt_id")) != stage_attempt_id
        or text(closeout.get("stage_id")) != text(target_identity.get("stage_id"))
        or text(closeout.get("study_id")) != study_id
        or text(closeout.get("action_type")) != action_type
        or text(closeout.get("status")) != "blocked"
        or text(closeout.get("blocked_reason")) is None
        or text(domain_blocker.get("surface_kind")) != "mas_domain_typed_blocker"
        or typed_blocker_ref is None
        or closeout.get("provider_completion_is_domain_completion") is not False
    ):
        return None
    return {
        "closeout_ref": relative_stage_attempt_closeout_ref(
            study_id=study_id,
            stage_attempt_id=stage_attempt_id,
        ),
        "closeout_refs": sequence(closeout.get("closeout_refs")),
        "typed_blocker_refs": [typed_blocker_ref],
        "dispatch_ref": text(dispatch_identity.get("dispatch_ref")),
        "blocked_reason": text(closeout.get("blocked_reason")),
        "domain_blocker_reason": text(domain_blocker.get("reason")),
        "domain_blocker_next_owner": text(domain_blocker.get("next_owner")),
        "execution_blocked_reason": text(mapping(closeout.get("execution_observation")).get("blocked_reason")),
    }


def stage_attempt_closeout_owner_receipt_evidence(
    *,
    profile: Any,
    study_id: str,
    target_identity: Mapping[str, Any],
    dispatch_identity: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any] | None:
    stage_attempt_id = text(target_identity.get("stage_attempt_id"))
    if stage_attempt_id is None or action_type is None:
        return None
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json"
    )
    closeout = _read_json_object(closeout_path)
    if closeout is None:
        return None
    owner_receipt = mapping(closeout.get("owner_receipt"))
    domain_execution = mapping(closeout.get("domain_execution"))
    verification = mapping(closeout.get("verification"))
    closeout_ref = relative_stage_attempt_closeout_ref(
        study_id=study_id,
        stage_attempt_id=stage_attempt_id,
    )
    owner_receipt_ref = f"{closeout_ref}#owner_receipt"
    if not _is_matching_owner_receipt_closeout(
        closeout=closeout,
        owner_receipt=owner_receipt,
        domain_execution=domain_execution,
        target_identity=target_identity,
        study_id=study_id,
        stage_attempt_id=stage_attempt_id,
        action_type=action_type,
    ):
        return None
    return {
        "closeout_ref": closeout_ref,
        "closeout_refs": sequence(closeout.get("closeout_refs")),
        "owner_receipt_refs": [owner_receipt_ref],
        "dispatch_ref": text(dispatch_identity.get("dispatch_ref")),
        "owner": text(owner_receipt.get("owner")),
        "owner_callable_surface": text(owner_receipt.get("owner_callable_surface")),
        "request_ref": text(owner_receipt.get("request_ref")),
        "publication_eval_ref": text(owner_receipt.get("publication_eval_ref")),
        "route_outcome": text(closeout.get("route_outcome")),
        "quality_status": text(verification.get("quality_status")),
        "claim_evidence_alignment_status": text(verification.get("claim_evidence_alignment_status")),
        "artifact_delta_refs": sequence(closeout.get("artifact_delta_refs")),
    }


def closeout_evidence_refs(closeout_evidence: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend(texts([closeout_evidence.get("dispatch_ref"), closeout_evidence.get("closeout_ref")]))
    refs.extend(texts(sequence(closeout_evidence.get("closeout_refs"))))
    refs.extend(texts(sequence(closeout_evidence.get("typed_blocker_refs"))))
    refs.extend(
        texts(
            [
                f"stage-attempt-closeout:blocked_reason={text(closeout_evidence.get('blocked_reason'))}",
                (
                    "stage-attempt-closeout:domain_blocker_reason="
                    f"{text(closeout_evidence.get('domain_blocker_reason'))}"
                ),
                (
                    "stage-attempt-closeout:domain_blocker_next_owner="
                    f"{text(closeout_evidence.get('domain_blocker_next_owner'))}"
                ),
                (
                    "stage-attempt-closeout:execution_blocked_reason="
                    f"{text(closeout_evidence.get('execution_blocked_reason'))}"
                ),
            ]
        )
    )
    return unique(refs)


def owner_receipt_closeout_evidence_refs(closeout_evidence: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend(
        texts(
            [
                closeout_evidence.get("dispatch_ref"),
                closeout_evidence.get("closeout_ref"),
                closeout_evidence.get("request_ref"),
                closeout_evidence.get("publication_eval_ref"),
            ]
        )
    )
    refs.extend(texts(sequence(closeout_evidence.get("closeout_refs"))))
    refs.extend(texts(sequence(closeout_evidence.get("artifact_delta_refs"))))
    refs.extend(
        texts(
            [
                f"stage-attempt-closeout:status=executed",
                (
                    "stage-attempt-closeout:route_outcome="
                    f"{text(closeout_evidence.get('route_outcome'))}"
                ),
                (
                    "stage-attempt-closeout:owner="
                    f"{text(closeout_evidence.get('owner'))}"
                ),
                (
                    "stage-attempt-closeout:owner_callable_surface="
                    f"{text(closeout_evidence.get('owner_callable_surface'))}"
                ),
                (
                    "stage-attempt-closeout:quality_status="
                    f"{text(closeout_evidence.get('quality_status'))}"
                ),
                (
                    "stage-attempt-closeout:claim_evidence_alignment_status="
                    f"{text(closeout_evidence.get('claim_evidence_alignment_status'))}"
                ),
            ]
        )
    )
    return unique(refs)


def relative_stage_attempt_closeout_ref(*, study_id: str, stage_attempt_id: str) -> str:
    return (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
        f"{stage_attempt_id}.closeout.json"
    )


def _is_matching_owner_receipt_closeout(
    *,
    closeout: Mapping[str, Any],
    owner_receipt: Mapping[str, Any],
    domain_execution: Mapping[str, Any],
    target_identity: Mapping[str, Any],
    study_id: str,
    stage_attempt_id: str,
    action_type: str,
) -> bool:
    return (
        _matches_stage_attempt_identity(
            closeout=closeout,
            target_identity=target_identity,
            study_id=study_id,
            stage_attempt_id=stage_attempt_id,
            action_type=action_type,
        )
        and text(closeout.get("status")) == "executed"
        and _owner_receipt_is_refs_only(owner_receipt)
        and text(domain_execution.get("execution_status")) == "executed"
        and _closeout_does_not_claim_domain_completion(closeout)
    )


def _matches_stage_attempt_identity(
    *,
    closeout: Mapping[str, Any],
    target_identity: Mapping[str, Any],
    study_id: str,
    stage_attempt_id: str,
    action_type: str,
) -> bool:
    return (
        text(closeout.get("surface_kind")) == "stage_attempt_closeout_packet"
        and text(closeout.get("stage_attempt_id")) == stage_attempt_id
        and text(closeout.get("stage_id")) == text(target_identity.get("stage_id"))
        and text(closeout.get("study_id")) == study_id
        and text(closeout.get("action_type")) == action_type
    )


def _owner_receipt_is_refs_only(owner_receipt: Mapping[str, Any]) -> bool:
    return (
        text(owner_receipt.get("status")) == "executed"
        and text(owner_receipt.get("owner")) is not None
        and text(owner_receipt.get("publication_eval_ref")) is not None
        and owner_receipt.get("quality_authorized") is False
        and owner_receipt.get("submission_authorized") is False
        and owner_receipt.get("current_package_write_authorized") is False
    )


def _closeout_does_not_claim_domain_completion(closeout: Mapping[str, Any]) -> bool:
    return (
        closeout.get("provider_completion_is_domain_completion") is False
        and closeout.get("provider_completion_is_domain_ready") is False
        and closeout.get("domain_completion_claimed") is False
    )


def _read_json_object(path: object) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None
