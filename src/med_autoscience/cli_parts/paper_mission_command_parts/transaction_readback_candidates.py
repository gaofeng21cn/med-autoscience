from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _first_text,
    _load_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
    _slug,
)
from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)


def _candidate_manifest_transaction(candidate: str | Path | None) -> dict[str, Any]:
    if candidate is None:
        return {}
    path = Path(candidate).expanduser()
    if not path.exists():
        return {}
    try:
        payload = _load_json_object(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    package_candidate_ref = _optional_text(
        _mapping(payload.get("artifact_refs")).get("candidate_manifest")
    )
    if package_candidate_ref is not None:
        package_candidate_path = Path(package_candidate_ref).expanduser()
        if not package_candidate_path.is_absolute():
            package_candidate_path = path.parent / package_candidate_path
        if package_candidate_path != path:
            package_transaction = _candidate_manifest_transaction(package_candidate_path)
            if package_transaction:
                return package_transaction
    inline = _mapping(payload.get("paper_mission_transaction"))
    if inline:
        return inline
    reviewer_revision_transaction = _reviewer_revision_candidate_transaction(
        payload=payload,
        candidate_path=path,
    )
    if reviewer_revision_transaction:
        return reviewer_revision_transaction
    sidecar_refs = _mapping(payload.get("mission_candidate_sidecar_refs"))
    readback_ref = _optional_text(sidecar_refs.get("paper_mission_readback"))
    if readback_ref is not None:
        try:
            readback = _load_json_object(Path(readback_ref).expanduser())
        except (OSError, json.JSONDecodeError, ValueError):
            readback = {}
        transaction = _mapping(readback.get("paper_mission_transaction"))
        if transaction:
            return transaction
    mission_ref = _optional_text(sidecar_refs.get("paper_mission_run"))
    if mission_ref is not None:
        try:
            mission = _load_json_object(Path(mission_ref).expanduser())
        except (OSError, json.JSONDecodeError, ValueError):
            mission = {}
        transaction = _mapping(mission.get("paper_mission_transaction"))
        if transaction:
            return transaction
    default_readback_ref = _optional_text(sidecar_refs.get("default_readback"))
    if default_readback_ref is None:
        return {}
    try:
        default_readback = _load_json_object(Path(default_readback_ref).expanduser())
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return _mapping(default_readback.get("paper_mission_transaction"))


def _reviewer_revision_candidate_transaction(
    *,
    payload: Mapping[str, Any],
    candidate_path: Path,
) -> dict[str, Any]:
    if _optional_text(payload.get("milestone_kind")) != "reviewer_revision_candidate":
        return {}
    if payload.get("candidate_is_authority") is not False:
        return {}
    study_id = _optional_text(payload.get("study_id"))
    mission_id = _optional_text(payload.get("mission_id"))
    if not study_id or not mission_id:
        return {}
    artifact_refs = _mapping(payload.get("artifact_refs"))
    owner_request = _load_candidate_ref_mapping(
        artifact_refs.get("owner_consumption_request"),
        base_path=candidate_path.parent,
    )
    requested_action = _optional_text(owner_request.get("requested_action"))
    if requested_action != "consume_external_sci_registry_review_as_reviewer_revision":
        return {}
    stage_id = "external_sci_registry_reviewer_revision"
    next_work_unit = "ai_reviewer_medical_prose_quality_review"
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "reviewer_revision_candidate_ready",
        "reason": (
            "External SCI registry review candidate accepted for MAS AI reviewer "
            "recheck and downstream analysis/write routing."
        ),
        "next_owner": "ai_reviewer",
        "next_work_unit": next_work_unit,
        "reviewer_revision_candidate_ref": str(candidate_path),
        "recommended_next_route": _first_text(
            payload.get("recommended_next_route"),
            owner_request.get("recommended_next_route"),
            "analysis-campaign_then_write",
        ),
    }
    artifact_delta_refs = _reviewer_revision_artifact_refs(
        artifact_refs=artifact_refs,
        base_path=candidate_path.parent,
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=f"paper-mission-candidate://{study_id}/{stage_id}",
        terminal_decision=terminal_decision,
        artifact_delta_refs=artifact_delta_refs,
        paper_audit_pack_refs={
            family: [
                {
                    "ref_id": f"{family}::reviewer_revision_candidate",
                    "ref_kind": "reviewer_revision_candidate_ref",
                    "uri": str(candidate_path),
                }
            ]
            for family in PAPER_AUDIT_PACK_FAMILIES
        },
        idempotency_basis=(
            f"reviewer-revision-candidate-consumed::{candidate_path}"
        ),
    )


def _load_candidate_ref_mapping(ref: Any, *, base_path: Path) -> dict[str, Any]:
    ref_text = _optional_text(ref)
    if ref_text is None:
        return {}
    path = Path(ref_text).expanduser()
    if not path.is_absolute():
        path = base_path / path
    try:
        return _mapping(_load_json_object(path))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _reviewer_revision_artifact_refs(
    *,
    artifact_refs: Mapping[str, Any],
    base_path: Path,
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for ref_id in (
        "reviewer_action_matrix",
        "review_gap_root_cause",
        "owner_consumption_request",
    ):
        ref_text = _optional_text(artifact_refs.get(ref_id))
        if ref_text is None:
            continue
        path = Path(ref_text).expanduser()
        if not path.is_absolute():
            path = base_path / path
        refs.append(
            {
                "ref_id": ref_id,
                "ref_kind": "reviewer_revision_candidate_artifact",
                "uri": str(path),
            }
        )
    return refs or [
        {
            "ref_id": "reviewer_revision_candidate_manifest",
            "ref_kind": "reviewer_revision_candidate_ref",
            "uri": str(base_path / "package_manifest.json"),
        }
    ]


def _candidate_mission_id_for_readback(
    *,
    selected_mission_id: str,
    transaction_readback: dict[str, Any],
    authority_consume_readback: dict[str, Any] | None,
) -> str:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    if transaction_readback.get("source") != "placeholder_no_write":
        transaction_mission_id = _optional_text(transaction.get("mission_id"))
        if transaction_mission_id:
            return transaction_mission_id
    readback_mission_id = _optional_text((authority_consume_readback or {}).get("mission_id"))
    if readback_mission_id and readback_mission_id != "unknown_mission":
        return readback_mission_id
    return selected_mission_id


def _placeholder_paper_mission_transaction(
    *,
    mission_id: str,
    study_id: str,
    objective: str,
    paper_mission_command: str,
    study_root: Path,
    consume_result: dict[str, Any],
) -> dict[str, Any]:
    stage_id = f"paper-mission-cli::{paper_mission_command}"
    stage_run_ref = f"paper-mission-cli://{study_id}/{paper_mission_command}"
    transaction_id = f"paper-mission-transaction::{study_id}::{paper_mission_command}::{_slug(mission_id)}"
    next_work_unit = objective or "paper mission no-write readback"
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "not_materialized",
        "reason": (
            "No MAS-authored PaperMissionTransaction was materialized; CLI reports "
            "a no-write placeholder only."
        ),
        "next_owner": "mission_executor",
        "next_work_unit": next_work_unit,
        "authority_materialized": False,
        "consume_result_status": _optional_text(consume_result.get("status"))
        or "not_consumed",
    }
    route_command = {
        "command_kind": "resume_stage",
        "target": next_work_unit,
        "reason": "No materialized MAS stage terminal decision is available.",
        "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
        "stage_run_ref": stage_run_ref,
        "runtime_owner": "one-person-lab",
        "authority_materialized": False,
    }
    transaction = {
        "schema_version": "paper-mission-transaction.v1",
        "transaction_id": transaction_id,
        "mission_id": mission_id,
        "study_id": study_id,
        "stage_id": stage_id,
        "stage_run_ref": stage_run_ref,
        "stage_terminal_decision": terminal_decision,
        "opl_route_command": route_command,
        "artifact_delta_refs": [
            {
                "ref_id": "paper_mission_cli_no_write_plan",
                "ref_kind": "workspace_path",
                "uri": str(study_root / "paper"),
            }
        ],
        "paper_audit_pack_refs": {
            family: [
                {
                    "ref_id": f"{family}::paper-mission-cli",
                    "ref_kind": "paper_mission_cli_readback",
                    "uri": f"paper-mission-cli://{study_id}/{paper_mission_command}/{family}",
                }
            ]
            for family in PAPER_AUDIT_PACK_FAMILIES
        },
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
        },
        "idempotency": {
            "idempotency_key": f"{study_id}::{stage_id}::{_slug(mission_id)}",
            "transaction_fingerprint": (
                f"{mission_id}::{stage_id}::continue_same_stage::not_materialized"
            ),
        },
        "transaction_state": "not_materialized",
    }
    return transaction


def _transaction_from_materialized_legacy_mission(
    *,
    mission: dict[str, Any] | None,
    study_id: str,
) -> dict[str, Any]:
    if not mission:
        return {}
    consume_result = _mapping(mission.get("consume_result"))
    if not consume_result:
        return {}
    mission_id = _optional_text(mission.get("mission_id")) or "paper-mission::unknown"
    readback = _mapping(mission.get("one_shot_migration_readback"))
    current_mission = _mapping(readback.get("current_mission"))
    required_output = _mapping(readback.get("required_output"))
    stage_id = _first_text(
        current_mission.get("objective_kind"),
        required_output.get("objective_kind"),
        "paper_mission_materialized_legacy_stage",
    )
    terminal_decision = stage_terminal_decision_for_consume_result(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        consume_result=_enriched_materialized_consume_result(
            consume_result=consume_result,
            readback=readback,
        ),
        default_next_owner=_first_text(
            required_output.get("next_owner"),
            readback.get("next_owner"),
            "mas_authority_kernel",
        )
        or "mas_authority_kernel",
        default_next_stage_id=_next_stage_id_for_materialized(stage_id),
        default_next_work_unit=_first_text(
            required_output.get("work_unit_id"),
            current_mission.get("objective_id"),
            stage_id,
        )
        or stage_id,
        default_reason=_first_text(
            consume_result.get("reason"),
            readback.get("consume_candidate_status"),
            "materialized legacy PaperMissionRun terminalized by CLI readback",
        )
        or "materialized legacy PaperMissionRun terminalized by CLI readback",
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=f"opl-stage-run://paper-mission-materialized/{study_id}/{stage_id}/{_slug(mission_id)}",
        terminal_decision=terminal_decision,
        artifact_delta_refs=_artifact_delta_refs_for_transaction(mission),
        paper_audit_pack_refs=_paper_audit_pack_refs_for_transaction(mission),
        idempotency_basis=_first_text(
            consume_result.get("outcome"),
            consume_result.get("status"),
            stage_id,
        )
        or stage_id,
    )


def _enriched_materialized_consume_result(
    *,
    consume_result: dict[str, Any],
    readback: dict[str, Any],
) -> dict[str, Any]:
    enriched = dict(consume_result)
    if not _optional_text(enriched.get("status")):
        enriched["status"] = _optional_text(readback.get("consume_candidate_status")) or "not_consumed"
    if not _optional_text(enriched.get("resume_condition")):
        enriched["resume_condition"] = _first_text(
            readback.get("resume_condition"),
            _mapping(readback.get("consume_candidate_readback")).get("resume_condition"),
        )
    blocker = _mapping(_mapping(readback.get("mission_input")).get("legacy_blocker"))
    typed_blocker = _mapping(blocker.get("typed_blocker"))
    if typed_blocker:
        enriched["blocker_id"] = _first_text(
            typed_blocker.get("blocker_id"),
            typed_blocker.get("blocker_type"),
            enriched.get("blocker_id"),
        )
        enriched["unblock_condition"] = _first_text(
            typed_blocker.get("required_input"),
            enriched.get("unblock_condition"),
            enriched.get("resume_condition"),
        )
    return enriched


def _artifact_delta_refs_for_transaction(mission: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, delta in enumerate(_mapping_list(mission.get("artifact_delta_ledger")), start=1):
        uri = _optional_text(delta.get("artifact_ref"))
        if not uri:
            continue
        refs.append(
            {
                "ref_id": _optional_text(delta.get("delta_id")) or f"artifact_delta::{index}",
                "ref_kind": _optional_text(delta.get("delta_kind")) or "artifact_delta",
                "uri": uri,
            }
        )
    return refs or [
        {
            "ref_id": "artifact_delta::missing",
            "ref_kind": "missing_artifact_delta",
            "uri": "mission://artifact-delta/missing",
        }
    ]


def _paper_audit_pack_refs_for_transaction(
    mission: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    audit_pack = _mapping(mission.get("paper_audit_pack"))
    refs_by_family: dict[str, list[dict[str, str]]] = {}
    for family in PAPER_AUDIT_PACK_FAMILIES:
        family_payload = _mapping(audit_pack.get(family))
        refs = [
            {
                "ref_id": _optional_text(ref.get("ref_id")) or f"{family}::{index}",
                "ref_kind": _optional_text(ref.get("ref_kind")) or "artifact_ref",
                "uri": _optional_text(ref.get("uri")) or f"mission://audit-pack/{family}/missing",
            }
            for index, ref in enumerate(_mapping_list(family_payload.get("refs")), start=1)
        ]
        refs_by_family[family] = refs or [
            {
                "ref_id": f"{family}::missing",
                "ref_kind": "missing_audit_ref",
                "uri": f"mission://audit-pack/{family}/missing",
            }
        ]
    return refs_by_family
