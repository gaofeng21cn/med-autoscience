from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_run import (
    PaperMissionRun,
    REQUIRED_PAPER_AUDIT_PACK_FAMILIES,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransaction,
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


def _summary_helpers():
    from med_autoscience.controllers.study_progress import mission_summary

    return mission_summary


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return _summary_helpers()._compact(value)


def _dedupe_texts(values) -> list[str]:
    return _summary_helpers()._dedupe_texts(values)


def _first_text(*values: object) -> str | None:
    return _summary_helpers()._first_text(*values)


def _mapping(value: object) -> dict[str, Any]:
    return _summary_helpers()._mapping(value)


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return _summary_helpers()._mapping_list(value)


def _non_empty_text(value: object) -> str | None:
    return _summary_helpers()._non_empty_text(value)


def _ref_kind(ref: str) -> str:
    return _summary_helpers()._ref_kind(ref)


def _slug(value: object) -> str:
    return _summary_helpers()._slug(value)


def _text_list(value: object) -> list[str]:
    return _summary_helpers()._text_list(value)


def _study_id(progress: Mapping[str, Any]) -> str:
    return _summary_helpers()._study_id(progress)


def _mission_id(
    *,
    study_id: str,
    objective: str,
    progress: Mapping[str, Any],
    current_objective: Mapping[str, Any],
) -> str:
    return _summary_helpers()._mission_id(
        study_id=study_id,
        objective=objective,
        progress=progress,
        current_objective=current_objective,
    )


def _paper_mission_run_payload(
    *,
    progress: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
    artifact_delta_ledger: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    helpers = _summary_helpers()
    study_id = _study_id(progress)
    objective = (
        _non_empty_text(current_objective.get("objective"))
        or "inspect next paper artifact delta"
    )
    mission_id = _mission_id(
        study_id=study_id,
        objective=objective,
        progress=progress,
        current_objective=current_objective,
    )
    consume_result = _consume_result(
        mission_state=mission_state,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    mission = {
        "schema_version": helpers.PAPER_MISSION_RUN_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": mission_state,
        "artifact_delta_ledger": artifact_delta_ledger,
        "source_refs": source_refs,
        "paper_audit_pack": _paper_audit_pack(
            study_id=study_id,
            mission_id=mission_id,
            objective=objective,
            artifact_delta_ledger=artifact_delta_ledger,
            source_refs=source_refs,
            platform_diagnostics=platform_diagnostics,
            next_owner_or_human_decision=next_owner_or_human_decision,
            current_objective=current_objective,
        ),
        "authority_touchpoints": _authority_touchpoints(
            platform_diagnostics=platform_diagnostics,
        ),
        "forbidden_write_guard": _forbidden_write_guard(),
        "consume_result": consume_result,
        "claim_permissions": {
            "can_claim_artifact_delta": bool(artifact_delta_ledger),
            "can_claim_owner_handoff": bool(next_owner_or_human_decision),
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": [],
        },
    }
    mission["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission=mission,
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=artifact_delta_ledger,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    return PaperMissionRun.from_payload(mission).to_dict()


def _normalize_paper_mission_run_payload(
    *,
    progress: Mapping[str, Any],
    mission: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
    artifact_delta_ledger: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    helpers = _summary_helpers()
    study_id = _non_empty_text(mission.get("study_id")) or _study_id(progress)
    objective = _non_empty_text(mission.get("objective")) or _first_text(
        current_objective.get("objective"),
        "inspect materialized paper mission",
    )
    mission_id = _non_empty_text(mission.get("mission_id")) or _mission_id(
        study_id=study_id,
        objective=objective,
        progress=progress,
        current_objective=current_objective,
    )
    if not source_refs:
        source_refs = _source_refs(progress)
    if not source_refs:
        source_refs = [
            {
                "ref_id": "source_ref::missing",
                "ref_kind": "missing_readback_ref",
                "uri": f"mission://{study_id}/source-refs/missing",
            }
        ]
    payload = {
        **dict(mission),
        "schema_version": helpers.PAPER_MISSION_RUN_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": mission_state,
        "artifact_delta_ledger": artifact_delta_ledger,
        "source_refs": source_refs,
        "authority_touchpoints": _mapping_list(mission.get("authority_touchpoints"))
        or _authority_touchpoints(platform_diagnostics=platform_diagnostics),
        "forbidden_write_guard": _mapping(mission.get("forbidden_write_guard"))
        or _forbidden_write_guard(),
        "consume_result": _mapping(mission.get("consume_result"))
        or _consume_result(
            mission_state=mission_state,
            next_owner_or_human_decision=next_owner_or_human_decision,
        ),
        "claim_permissions": _mapping(mission.get("claim_permissions"))
        or {
            "can_claim_artifact_delta": bool(artifact_delta_ledger),
            "can_claim_owner_handoff": bool(next_owner_or_human_decision),
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": [],
        },
    }
    payload["paper_audit_pack"] = _mapping(
        mission.get("paper_audit_pack")
    ) or _paper_audit_pack(
        study_id=study_id,
        mission_id=mission_id,
        objective=objective,
        artifact_delta_ledger=artifact_delta_ledger,
        source_refs=source_refs,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
        current_objective=current_objective,
    )
    payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission=payload,
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=artifact_delta_ledger,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    return PaperMissionRun.from_payload(payload).to_dict()


def _paper_mission_transaction_payload(
    *,
    mission: Mapping[str, Any],
    progress: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
    artifact_delta_ledger: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _mapping(mission.get("paper_mission_transaction"))
    if existing:
        try:
            transaction = PaperMissionTransaction.from_payload(existing)
        except ValueError:
            transaction = None
        if (
            transaction is not None
            and transaction.mission_id == _non_empty_text(mission.get("mission_id"))
            and transaction.study_id == _non_empty_text(mission.get("study_id"))
        ):
            return transaction.to_dict()
    stage_id = _materialized_transaction_stage_id(mission) or _stage_id(
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
    )
    consume_result = _mapping(mission.get("consume_result")) or _consume_result(
        mission_state=mission_state,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    mission_id = _non_empty_text(mission.get("mission_id")) or "paper-mission::unknown"
    study_id = _non_empty_text(mission.get("study_id")) or _study_id(progress)
    terminal_decision = stage_terminal_decision_for_consume_result(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        consume_result=consume_result,
        default_next_owner=_first_text(
            next_owner_or_human_decision.get("next_owner"),
            current_objective.get("next_owner"),
            "mas_authority_kernel",
        )
        or "mas_authority_kernel",
        default_next_stage_id=_next_stage_id(stage_id=stage_id),
        default_next_work_unit=_first_text(
            current_objective.get("work_unit_id"),
            current_objective.get("objective"),
            stage_id,
        )
        or stage_id,
        default_reason=_first_text(
            consume_result.get("reason"),
            next_owner_or_human_decision.get("summary"),
            "stage terminalized from artifact-first paper mission summary",
        )
        or "stage terminalized from artifact-first paper mission summary",
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=(
            f"opl-stage-run://paper-mission-summary/{_study_id(progress)}/{stage_id}"
        ),
        terminal_decision=terminal_decision,
        artifact_delta_refs=_artifact_delta_refs_for_transaction(
            artifact_delta_ledger=artifact_delta_ledger,
            study_id=_study_id(progress),
        ),
        paper_audit_pack_refs=_paper_audit_pack_refs(
            _mapping(mission.get("paper_audit_pack"))
        ),
        idempotency_basis=_first_text(
            consume_result.get("status"),
            current_objective.get("work_unit_id"),
            "projection",
        )
        or "projection",
    )


def _paper_audit_pack(
    *,
    study_id: str,
    mission_id: str,
    objective: str,
    artifact_delta_ledger: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
    current_objective: Mapping[str, Any],
) -> dict[str, Any]:
    source_uris = [
        uri for item in source_refs if (uri := _non_empty_text(item.get("uri"))) is not None
    ]
    artifact_uris = [
        uri
        for item in artifact_delta_ledger
        if (uri := _non_empty_text(item.get("artifact_ref"))) is not None
    ]
    diagnostic_refs = _text_list(platform_diagnostics.get("refs"))
    next_owner = _non_empty_text(next_owner_or_human_decision.get("next_owner"))
    work_unit_id = _non_empty_text(current_objective.get("work_unit_id"))
    refs_by_family = {
        "analysis_rationale_log": [
            mission_id,
            f"mission://{study_id}/objective/{_slug(objective)}",
        ],
        "decision_trace": [
            f"mission://{study_id}/stage-terminal-decision/{_slug(work_unit_id or objective)}",
            next_owner or "mas_authority_kernel",
        ],
        "evidence_ledger_delta": source_uris,
        "review_ledger_delta": [
            _non_empty_text(next_owner_or_human_decision.get("summary")) or "",
            f"mission://{study_id}/review-ledger/projection",
        ],
        "revision_log_delta": [
            f"mission://{study_id}/revision-log/{_slug(objective)}",
        ],
        "failed_path_ledger": diagnostic_refs
        or [f"mission://{study_id}/failed-path/no-current-diagnostic-ref"],
        "artifact_lineage": artifact_uris
        or [f"mission://{study_id}/artifact-lineage/no-artifact-delta-yet"],
        "reproducibility_refs": diagnostic_refs
        or source_uris
        or [f"mission://{study_id}/reproducibility/projection"],
    }
    return {
        family: {
            "status": "projection_ref_chain",
            "refs": _audit_refs(family=family, refs=refs_by_family.get(family, [])),
        }
        for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    }


def _audit_refs(*, family: str, refs: list[object]) -> list[dict[str, str]]:
    clean_refs = _dedupe_texts(refs)
    if not clean_refs:
        clean_refs = [f"mission://audit-pack/{family}/missing"]
    return [
        {
            "ref_id": f"{family}::{index}",
            "ref_kind": _ref_kind(ref),
            "uri": ref,
        }
        for index, ref in enumerate(clean_refs, start=1)
    ]


def _artifact_delta_refs_for_transaction(
    *,
    artifact_delta_ledger: list[dict[str, Any]],
    study_id: str,
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, delta in enumerate(artifact_delta_ledger, start=1):
        uri = _non_empty_text(delta.get("artifact_ref"))
        if not uri:
            continue
        refs.append(
            {
                "ref_id": _non_empty_text(delta.get("delta_id"))
                or f"artifact_delta::{index}",
                "ref_kind": _non_empty_text(delta.get("delta_kind"))
                or "artifact_delta",
                "uri": uri,
            }
        )
    return refs or [
        {
            "ref_id": "artifact_delta::missing",
            "ref_kind": "missing_artifact_delta",
            "uri": f"mission://{study_id}/artifact-delta/missing",
        }
    ]


def _paper_audit_pack_refs(audit_pack: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    refs_by_family: dict[str, list[dict[str, str]]] = {}
    for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES:
        family_payload = _mapping(audit_pack.get(family))
        refs = [
            {
                "ref_id": _non_empty_text(ref.get("ref_id")) or f"{family}::{index}",
                "ref_kind": _non_empty_text(ref.get("ref_kind")) or "artifact_ref",
                "uri": _non_empty_text(ref.get("uri"))
                or f"mission://audit-pack/{family}/missing",
            }
            for index, ref in enumerate(
                _mapping_list(family_payload.get("refs")), start=1
            )
        ]
        refs_by_family[family] = refs or [
            {
                "ref_id": f"{family}::missing",
                "ref_kind": "missing_audit_ref",
                "uri": f"mission://audit-pack/{family}/missing",
            }
        ]
    return refs_by_family


def _stage_id(
    *,
    progress: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
) -> str:
    raw = _first_text(
        progress.get("paper_stage"),
        progress.get("current_stage"),
        current_objective.get("objective"),
        current_objective.get("action_type"),
        mission_state,
    ) or "paper_mission_projection_stage"
    return _slug(raw).replace("-", "_")


def _materialized_transaction_stage_id(mission: Mapping[str, Any]) -> str | None:
    readback = _mapping(mission.get("one_shot_migration_readback"))
    if not readback:
        return None
    current_mission = _mapping(readback.get("current_mission"))
    required_output = _mapping(readback.get("required_output"))
    return _first_text(
        current_mission.get("objective_kind"),
        required_output.get("objective_kind"),
        current_mission.get("objective_id"),
    )


def _next_stage_id(*, stage_id: str) -> str:
    if stage_id == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if stage_id == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


def _transaction_state(transaction: Mapping[str, Any]) -> dict[str, Any]:
    helpers = _summary_helpers()
    decision = _mapping(transaction.get("stage_terminal_decision"))
    route = _mapping(transaction.get("ai_route_context"))
    boundary = _mapping(transaction.get("authority_boundary"))
    return _compact(
        {
            "transaction_id": _non_empty_text(transaction.get("transaction_id")),
            "contract_ref": helpers.PAPER_MISSION_TRANSACTION_CONTRACT_REF,
            "validator": helpers.PAPER_MISSION_TRANSACTION_VALIDATOR,
            "decision_kind": _non_empty_text(decision.get("decision_kind")),
            "route_command_kind": _non_empty_text(route.get("command_kind")),
            "mas_authority_owner": _non_empty_text(boundary.get("mas_authority_owner")),
            "runtime_owner": _non_empty_text(boundary.get("runtime_owner")),
            "projection_only": True,
            "writes_authority_surface": boundary.get("writes_authority_surface"),
            "writes_runtime_queue": boundary.get("writes_runtime_queue"),
            "writes_provider_attempt": boundary.get("writes_provider_attempt"),
        }
    )


def _source_refs(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs = _mapping(progress.get("refs"))
    result: list[dict[str, Any]] = []
    for key, value in refs.items():
        if text := _non_empty_text(value):
            result.append({"ref_id": str(key), "ref_kind": str(key), "uri": text})
    for ref in _text_list(progress.get("source_refs")):
        result.append(
            {"ref_id": f"source::{len(result) + 1}", "ref_kind": "source_ref", "uri": ref}
        )
    return result


def _authority_touchpoints(*, platform_diagnostics: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "touchpoint_id": "touchpoint::mas-authority-kernel",
            "owner": "MedAutoScience",
            "surface": "MAS Authority Kernel",
            "status": "not_touched",
        },
        {
            "touchpoint_id": "touchpoint::opl-runtime-readback",
            "owner": "one-person-lab",
            "surface": "OPL runtime/readback",
            "status": "not_touched",
        },
    ]


def _forbidden_write_guard() -> dict[str, Any]:
    return {
        "blocked_paths": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "current_package",
            "runtime queue/provider attempts",
            "/Users/gaofeng/workspace/Yang/**",
        ],
        "forbidden_claims": [
            "publication_ready",
            "current_package",
            "owner_receipt_written",
        ],
        "candidate_writes_authority": False,
    }


def _consume_result(
    *,
    mission_state: str,
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    if mission_state == "consumed":
        return {"status": "accepted"}
    if mission_state == "route_back":
        return {"status": "route_back"}
    if mission_state == "stable_blocker":
        result = {"status": "typed_blocker"}
        if ref := _non_empty_text(next_owner_or_human_decision.get("typed_blocker_ref")):
            result["ref"] = ref
        return result
    if mission_state == "waiting_human_decision":
        return {"status": "human_gate"}
    return {
        "status": "human_gate",
        "outcome": "paper_mission_readback_missing",
        "reason": "authoritative_stage_terminal_outcome_missing",
        "question": (
            "Authoritative MAS stage terminal outcome is missing; do not infer "
            "the next runtime action from legacy progress projections."
        ),
        "required_receipt": "paper_mission_readback_missing",
    }
