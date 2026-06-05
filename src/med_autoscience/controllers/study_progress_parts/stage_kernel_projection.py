from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .shared import _mapping_copy, _non_empty_text
from med_autoscience.controllers.opl_stage_lineage_retention import (
    stage_lineage_retention_drilldown,
)
from med_autoscience.controllers.opl_stage_promotion_runtime import (
    promotion_audit_from_stage_projection,
)
from med_autoscience.controllers.opl_state_index_kernel import build_state_index_kernel_rows
from med_autoscience.controllers.stage_run_kernel import (
    stage_run_kernel_projection_from_stage_state,
)


def stage_kernel_projection_from_artifact_index(
    stage_artifact_index: Mapping[str, Any],
) -> dict[str, Any]:
    current_stage = _mapping_copy(stage_artifact_index.get("current_stage"))
    stage_id = _non_empty_text(current_stage.get("stage_id")) or _non_empty_text(
        stage_artifact_index.get("current_stage")
    )
    stages = [
        dict(item)
        for item in stage_artifact_index.get("stages") or []
        if isinstance(item, Mapping)
    ]
    selected_stage = _first_stage(stages=stages, stage_id=stage_id) or (
        stages[0] if stages else {}
    )
    artifact_classification = _mapping_copy(selected_stage.get("artifact_classification"))
    current_pointer = _mapping_copy(selected_stage.get("current_pointer"))
    physical_kernel = _mapping_copy(selected_stage.get("physical_stage_folder_kernel"))
    consumability = _mapping_copy(artifact_classification.get("consumability"))
    semantic_validation = _mapping_copy(artifact_classification.get("semantic_validation"))
    stage_run_kernel = stage_run_kernel_projection_from_stage_state(
        selected_stage=selected_stage,
        study_root=_non_empty_text(stage_artifact_index.get("study_root")),
    )
    blocker = _stage_kernel_blocker(
        selected_stage=selected_stage,
        artifact_classification=artifact_classification,
        consumability=consumability,
        semantic_validation=semantic_validation,
    )
    stage_run = _stage_run_projection(
        stage_artifact_index=stage_artifact_index,
        selected_stage=selected_stage,
        artifact_classification=artifact_classification,
        semantic_validation=semantic_validation,
        consumability=consumability,
        current_pointer=current_pointer,
        physical_kernel=physical_kernel,
    )
    projection = {
        "surface_kind": "stage_kernel_projection",
        "schema_version": 1,
        "stage_run_profile_ref": "contracts/stage_run_kernel_profile.json",
        "current_truth_source": "opl_physical_stage_folder_kernel"
        if physical_kernel.get("status") == "observed"
        else "mas_declared_stage_artifact_projection",
        "current_stage": stage_id,
        "stage_progress_status": _non_empty_text(selected_stage.get("stage_progress_status")),
        "artifact_roles": [
            {
                "role": _non_empty_text(item.get("role")),
                "ref": _non_empty_text(item.get("ref")),
            }
            for item in selected_stage.get("required_output_refs") or []
            if isinstance(item, Mapping)
        ],
        "missing_outputs": _text_list(artifact_classification.get("missing")),
        "accepted_receipts": _text_list(artifact_classification.get("owner_receipt_refs")),
        "semantic_validation": semantic_validation,
        "consumability": consumability,
        "lineage": _mapping_copy(artifact_classification.get("lineage")),
        "retention": _mapping_copy(artifact_classification.get("retention")),
        "current_pointer": current_pointer,
        "promotion": _promotion_projection(
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
            semantic_validation=semantic_validation,
            consumability=consumability,
            current_pointer=current_pointer,
            physical_kernel=physical_kernel,
        ),
        "lineage_retention": _lineage_retention_projection(
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
            current_pointer=current_pointer,
            physical_kernel=physical_kernel,
        ),
        "stage_run": stage_run,
        "current_owner_delta": _current_owner_delta(
            stage_run=stage_run,
            next_owner_action=_mapping_copy(stage_artifact_index.get("next_owner_action")),
        ),
        "blocker": blocker,
        "next_owner": _mapping_copy(stage_artifact_index.get("next_owner_action")),
        "provider_liveness": _mapping_copy(stage_artifact_index.get("provider_liveness")),
        "state_index": _state_index_projection(stage_artifact_index),
        "source_refs": _stage_kernel_source_refs(
            stage_artifact_index=stage_artifact_index,
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
        ),
        "authority": {
            "derived_projection": True,
            "writes_mas_truth": False,
            "claims_publication_ready": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
        },
    }
    if stage_run_kernel is not None:
        projection["stage_run_kernel"] = stage_run_kernel
        projection["current_owner_delta"] = dict(stage_run_kernel["current_owner_delta"])
    return projection


def _stage_run_projection(
    *,
    stage_artifact_index: Mapping[str, Any],
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
    consumability: Mapping[str, Any],
    current_pointer: Mapping[str, Any],
    physical_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    stage_id = _non_empty_text(selected_stage.get("stage_id"))
    owner_receipt_refs = _text_list(artifact_classification.get("owner_receipt_refs"))
    typed_blocker_refs = _text_list(artifact_classification.get("typed_blocker_refs"))
    return {
        "surface_kind": "stage_run_kernel_projection",
        "schema_version": 1,
        "stage_id": stage_id,
        "state": _stage_run_state(
            stage_artifact_index=stage_artifact_index,
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
            semantic_validation=semantic_validation,
            consumability=consumability,
        ),
        "attempt_id": _non_empty_text(current_pointer.get("attempt_id"))
        or _non_empty_text(artifact_classification.get("latest_attempt_id"))
        or _non_empty_text(physical_kernel.get("latest_attempt_id")),
        "generation": _non_empty_text(current_pointer.get("attempt_id"))
        or _non_empty_text(artifact_classification.get("latest_attempt_id"))
        or _non_empty_text(physical_kernel.get("latest_attempt_id"))
        or "declared",
        "status_owner": "one-person-lab",
        "domain_authority_owner": "med-autoscience",
        "transition_authority": {
            "owner_receipt_or_typed_blocker_required": True,
            "file_presence_counts_as_completion": False,
            "provider_completion_counts_as_domain_completion": False,
            "latest_projection_counts_as_transition_authority": False,
            "read_model_counts_as_transition_authority": False,
        },
        "domain_outcome": {
            "owner_receipt_refs": owner_receipt_refs,
            "typed_blocker_refs": typed_blocker_refs,
            "domain_accepted": bool(owner_receipt_refs) and not typed_blocker_refs,
            "typed_blocked": bool(typed_blocker_refs),
        },
        "source_refs": _stage_run_source_refs(
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
        ),
        "projection_only": True,
        "body_included": False,
        "authority": {
            "writes_mas_truth": False,
            "writes_opl_status": False,
            "claims_publication_ready": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
        },
    }


def _stage_run_state(
    *,
    stage_artifact_index: Mapping[str, Any],
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
    consumability: Mapping[str, Any],
) -> str:
    if _text_list(artifact_classification.get("typed_blocker_refs")):
        return "TypedBlocked"
    if (
        _text_list(artifact_classification.get("owner_receipt_refs"))
        and _non_empty_text(semantic_validation.get("status")) == "accepted"
        and _non_empty_text(consumability.get("status")) in {"passed", "ready_for_consumability_validation"}
    ):
        return "DomainAccepted"
    provider_liveness = _mapping_copy(stage_artifact_index.get("provider_liveness"))
    if provider_liveness.get("running_provider_attempt") is True:
        return "Running"
    promotion = _mapping_copy(artifact_classification.get("promotion"))
    if _non_empty_text(promotion.get("state")) == "current_pointer_promoted":
        return "Terminalizing"
    if selected_stage:
        missing = _text_list(artifact_classification.get("missing"))
        if missing:
            return "InputsReady"
    return "Declared"


def _stage_run_source_refs(
    *,
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
) -> list[str]:
    refs = [
        _non_empty_text(_mapping_copy(selected_stage.get("stage_folder_contract")).get("manifest_ref")),
        _non_empty_text(_mapping_copy(selected_stage.get("stage_folder_contract")).get("receipt_ref")),
        *_text_list(artifact_classification.get("owner_receipt_refs")),
        *_text_list(artifact_classification.get("typed_blocker_refs")),
    ]
    return _dedupe_text(ref for ref in refs if ref)


def _current_owner_delta(
    *,
    stage_run: Mapping[str, Any],
    next_owner_action: Mapping[str, Any],
) -> dict[str, Any]:
    stage_id = _non_empty_text(stage_run.get("stage_id"))
    domain_outcome = _mapping_copy(stage_run.get("domain_outcome"))
    typed_blocker_refs = _text_list(domain_outcome.get("typed_blocker_refs"))
    owner_receipt_refs = _text_list(domain_outcome.get("owner_receipt_refs"))
    state = _non_empty_text(stage_run.get("state"))
    return {
        "surface_kind": "stage_run_current_owner_delta",
        "schema_version": 1,
        "stage_id": stage_id,
        "state": state,
        "owner": _owner_for_delta(
            state=state,
            next_owner_action=next_owner_action,
            stage_id=stage_id,
        ),
        "action_type": _action_type_for_delta(
            state=state,
            next_owner_action=next_owner_action,
        ),
        "typed_blocker_refs": typed_blocker_refs,
        "owner_receipt_refs": owner_receipt_refs,
        "projection_only": True,
        "writes_transition_authority": False,
    }


def _owner_for_delta(
    *,
    state: str | None,
    next_owner_action: Mapping[str, Any],
    stage_id: str | None,
) -> str | None:
    if state == "TypedBlocked":
        return (
            _non_empty_text(next_owner_action.get("next_owner"))
            or _non_empty_text(next_owner_action.get("owner"))
            or stage_id
        )
    return _non_empty_text(next_owner_action.get("next_owner")) or _non_empty_text(
        next_owner_action.get("owner")
    )


def _action_type_for_delta(
    *,
    state: str | None,
    next_owner_action: Mapping[str, Any],
) -> str | None:
    if state == "TypedBlocked":
        return "resolve_typed_blocker"
    if state == "DomainAccepted":
        return _non_empty_text(next_owner_action.get("action_type")) or "advance_next_stage"
    return _non_empty_text(next_owner_action.get("action_type")) or "materialize_stage_artifact_delta"


def _state_index_projection(stage_artifact_index: Mapping[str, Any]) -> dict[str, Any]:
    projection = build_state_index_kernel_rows(stage_artifact_index=stage_artifact_index)
    return {
        "surface_kind": "stage_kernel_state_index_projection",
        "status": projection["status"],
        "row_count": projection["row_count"],
        "index_authority": projection["index_authority"],
        "derived_index_rebuildable": True,
        "sqlite_record_counts_as_stage_complete": False,
        "violations": list(projection["violations"]),
        "authority_boundary": dict(projection["authority_boundary"]),
    }


def _promotion_projection(
    *,
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
    consumability: Mapping[str, Any],
    current_pointer: Mapping[str, Any],
    physical_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    return promotion_audit_from_stage_projection(
        _stage_kernel_drilldown_source(
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
            semantic_validation=semantic_validation,
            consumability=consumability,
            current_pointer=current_pointer,
            physical_kernel=physical_kernel,
        )
    )


def _lineage_retention_projection(
    *,
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    current_pointer: Mapping[str, Any],
    physical_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    return stage_lineage_retention_drilldown(
        stage_projection=_stage_kernel_drilldown_source(
            selected_stage=selected_stage,
            artifact_classification=artifact_classification,
            semantic_validation=_mapping_copy(artifact_classification.get("semantic_validation")),
            consumability=_mapping_copy(artifact_classification.get("consumability")),
            current_pointer=current_pointer,
            physical_kernel=physical_kernel,
        )
    )


def _stage_kernel_drilldown_source(
    *,
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
    consumability: Mapping[str, Any],
    current_pointer: Mapping[str, Any],
    physical_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    stage_folder = _mapping_copy(selected_stage.get("stage_folder_contract"))
    promotion = _mapping_copy(artifact_classification.get("promotion"))
    lineage = _mapping_copy(artifact_classification.get("lineage"))
    retention = _mapping_copy(artifact_classification.get("retention"))
    return {
        "surface_kind": "mas_opl_physical_stage_folder_projection"
        if physical_kernel.get("status") == "observed"
        else "stage_kernel_projection_drilldown_source",
        "stage_id": _non_empty_text(selected_stage.get("stage_id")),
        "status": "observed" if selected_stage else "missing",
        "latest_attempt_id": _non_empty_text(artifact_classification.get("latest_attempt_id"))
        or _non_empty_text(physical_kernel.get("latest_attempt_id")),
        "latest_pointer_ref": _non_empty_text(stage_folder.get("latest_pointer_ref"))
        or _non_empty_text(physical_kernel.get("latest_pointer_ref")),
        "manifest_ref": _non_empty_text(stage_folder.get("manifest_ref"))
        or _non_empty_text(artifact_classification.get("manifest_ref")),
        "receipt_ref": _non_empty_text(stage_folder.get("receipt_ref"))
        or _non_empty_text(artifact_classification.get("receipt_ref")),
        "current_pointer_ref": _non_empty_text(stage_folder.get("current_pointer_ref"))
        or _non_empty_text(physical_kernel.get("current_pointer_ref")),
        "required_outputs": _required_output_surfaces(selected_stage),
        "current_outputs": _text_list(artifact_classification.get("current")),
        "manifest_hash_refs": list(artifact_classification.get("manifest_hash_refs") or []),
        "owner_receipt_refs": _text_list(artifact_classification.get("owner_receipt_refs")),
        "typed_blocker_refs": _text_list(artifact_classification.get("typed_blocker_refs")),
        "decision_receipt_refs": _text_list(artifact_classification.get("decision_receipt_refs")),
        "restore_refs": _text_list(_mapping_copy(retention).get("restore_refs"))
        or _text_list(physical_kernel.get("restore_refs")),
        "retention_refs": _text_list(_mapping_copy(retention).get("retention_refs"))
        or _text_list(physical_kernel.get("retention_refs")),
        "promotion": promotion,
        "semantic_validation": semantic_validation,
        "consumability": consumability,
        "lineage": lineage,
        "retention": retention,
        "current_pointer": current_pointer,
        "current_pointer_artifact_refs": _text_list(current_pointer.get("artifact_refs")),
        "manifest_artifact_refs": _text_list(artifact_classification.get("current")),
        "body_included": False,
    }


def _required_output_surfaces(selected_stage: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for item in selected_stage.get("required_output_refs") or []:
        if isinstance(item, Mapping):
            ref = _non_empty_text(item.get("ref"))
            if ref is not None:
                result.append(ref)
    return result


def _first_stage(*, stages: list[dict[str, Any]], stage_id: str | None) -> dict[str, Any] | None:
    if stage_id is None:
        return None
    for stage in stages:
        if _non_empty_text(stage.get("stage_id")) == stage_id:
            return stage
    return None


def _stage_kernel_blocker(
    *,
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    consumability: Mapping[str, Any],
    semantic_validation: Mapping[str, Any],
) -> dict[str, Any]:
    fail_reason = _non_empty_text(artifact_classification.get("fail_closed_reason"))
    failed_checks = _text_list(_mapping_copy(artifact_classification.get("consumability")).get("failed_checks"))
    if fail_reason is None and not failed_checks:
        return {}
    return {
        "blocker_id": fail_reason or "consumability_gate_failed",
        "stage_id": _non_empty_text(selected_stage.get("stage_id")),
        "failed_checks": failed_checks,
        "semantic_validation_status": _non_empty_text(semantic_validation.get("status")),
        "consumability_status": _non_empty_text(consumability.get("status")),
        "opl_can_override": False,
    }


def _stage_kernel_source_refs(
    *,
    stage_artifact_index: Mapping[str, Any],
    selected_stage: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
) -> list[str]:
    refs = [
        _non_empty_text(stage_artifact_index.get("domain_stage_pack_ref")),
        _non_empty_text(stage_artifact_index.get("stage_artifact_runtime_contract_ref")),
        _non_empty_text(_mapping_copy(selected_stage.get("stage_folder_contract")).get("manifest_ref")),
        _non_empty_text(_mapping_copy(selected_stage.get("stage_folder_contract")).get("receipt_ref")),
    ]
    conformance_refs = _mapping_copy(artifact_classification.get("conformance_refs"))
    refs.extend(_non_empty_text(value) for value in conformance_refs.values())
    return _dedupe_text(ref for ref in refs if ref)


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


def _dedupe_text(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


__all__ = ["stage_kernel_projection_from_artifact_index"]
