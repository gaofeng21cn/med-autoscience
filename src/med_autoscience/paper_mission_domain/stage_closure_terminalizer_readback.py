from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_stage_run_readback import attach_opl_stage_attempt_readback
from med_autoscience.paper_mission_stage_run_context import paper_mission_stage_run_context
from med_autoscience.paper_mission_transaction import PaperMissionTransactionContractError
from med_autoscience.paper_mission_domain.command_metadata import (
    action_intent as _action_intent,
)
from med_autoscience.paper_mission_domain.materialized_mission_readback import (
    build_materialized_mission_readback_if_available as _build_materialized_mission_readback_if_available,
)
from med_autoscience.paper_mission_domain.common import (
    _load_optional_json_object,
    _mapping,
    _optional_text,
)
from med_autoscience.paper_mission_domain.readback_next_action_precedence import (
    _stage_closure_next_action_should_own_next_action as _shared_stage_closure_next_action_should_own_next_action,
)
from med_autoscience.paper_mission_domain.stage_packet_route_back_readback import (
    _expected_stage_attempt_identity,
    _first_non_empty_text,
    _load_json_object,
    _load_stage_packet_route_back_evidence,
    _paper_mission_transaction_stage_id,
    _preferred_terminal_stage_attempt_ids,
    _stage_packet_opl_stage_attempt_readback,
    _stage_packet_route_back_semantic_priority,
    _stage_packet_route_stage_id,
    _stage_packet_transaction_priority,
    _terminal_closeout_is_live_runtime_observed,
)
from med_autoscience.paper_mission_domain.terminal_source_readback import (
    _readback_has_current_transaction_terminal_closeout,
    _stage_closure_decision_uses_stale_terminal_closeout,
    _stage_closure_matches_current_transaction_with_terminal_closeout,
    _terminal_closeout_mtime,
    _terminal_closeout_newer,
    _terminal_closeout_uses_stage_attempt_packet,
    _terminal_source_readback_newer,
)
from med_autoscience.paper_mission_domain.stage_closure_terminalizer import (
    FORBIDDEN_AUTHORITY_CLAIMS as STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS,
    STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    stage_closure_source_readback_summary as _stage_closure_source_readback_summary,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from med_autoscience.paper_mission_domain.stage_closure_next_action import (
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from med_autoscience.controllers.stage_closure_terminalizer import stage_closure_decision_missing


def _build_paper_mission_readback(**kwargs: Any) -> dict[str, Any]:
    from med_autoscience import paper_mission_domain as paper_mission_commands

    return paper_mission_commands.build_paper_mission_readback(**kwargs)


def _build_stage_closure_terminalizer_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    stage_packet: str | Path | None,
    dry_run: bool,
    source: str,
) -> dict[str, Any]:
    if stage_packet is not None:
        source_readback = _build_terminalizer_source_readback_from_stage_packet(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            stage_packet=stage_packet,
            source=f"{source}:terminalize-stage:stage-packet",
        )
    else:
        source_readback = _build_terminalizer_source_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            source=f"{source}:terminalize-stage:inspect",
        )
    existing_decision = _mapping(source_readback.get("stage_closure_decision"))
    existing_decision_uses_stale_terminal_closeout = (
        _stage_closure_decision_uses_stale_terminal_closeout(
            existing_decision=existing_decision,
            source_readback=source_readback,
            workspace_root=Path(profile.workspace_root),
        )
    )
    if (
        existing_decision
        and not stage_closure_decision_missing(existing_decision)
        and not _stage_closure_decision_requires_reterminalize(
            existing_decision,
            current_package=_mapping(source_readback.get("current_package")),
        )
        and not existing_decision_uses_stale_terminal_closeout
    ):
        decision = existing_decision
        terminalizer_status = "terminalizer_outcome_already_observed"
    else:
        terminalizer_source_readback = source_readback
        if existing_decision_uses_stale_terminal_closeout:
            terminalizer_source_readback = {
                **source_readback,
                "stage_closure_decision": {},
                "stage_closure_decision_ref": None,
                "stage_closure_outcome": None,
            }
        decision = _terminalize_stage_closure_from_readback(terminalizer_source_readback)
        terminalizer_status = "terminalizer_outcome_derived"
    return {
        "surface_kind": "paper_mission_stage_closure_terminalizer_readback",
        "schema_version": 1,
        "contract_ref": "contracts/mas-stage-closure-terminalizer.json",
        "paper_mission_command": "terminalize-stage",
        "action_intent": _action_intent("terminalize-stage"),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "mission_id": source_readback.get("mission_id"),
        "materialized_mission_ref": source_readback.get("materialized_mission_ref"),
        "status": terminalizer_status,
        "stage_closure_decision": decision,
        "stage_closure_decision_ref": decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(decision.get("outcome")).get("kind"),
        "source_readback_summary": _stage_closure_source_readback_summary(
            source_readback
        ),
        **_stage_closure_receipt_passthrough(source_readback),
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
        "forbidden_authority_writes": list(STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS),
        "required_next_owner": _mapping(decision.get("outcome")).get("next_owner"),
        "required_next_action": _mapping(decision.get("outcome")).get("next_action"),
    }


def _stage_closure_receipt_passthrough(
    source_readback: Mapping[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "current_package",
        "opl_stage_attempt_readback",
        "current_opl_stage_attempt_readback",
    ):
        value = _mapping(source_readback.get(key))
        if value:
            result[key] = value
    return result


def _build_terminalizer_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
    allow_stage_packet_autodiscovery: bool = True,
) -> dict[str, Any]:
    source_readback = _build_materialized_mission_readback_if_available(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source=source,
    )
    if source_readback is not None:
        if _source_readback_has_owner_repair_receipt(source_readback):
            return source_readback
        if allow_stage_packet_autodiscovery:
            stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
                source_readback=source_readback,
                source=source,
            )
            if (
                stage_attempt_source is not None
                and _terminal_source_readback_newer(
                    candidate=stage_attempt_source,
                    current=source_readback,
                    workspace_root=Path(profile.workspace_root),
                )
            ):
                return stage_attempt_source
        if _stage_closure_matches_current_transaction_with_terminal_closeout(
            source_readback,
            workspace_root=Path(profile.workspace_root),
        ):
            return source_readback
        if _readback_has_current_transaction_terminal_closeout(
            source_readback,
            workspace_root=Path(profile.workspace_root),
        ):
            return source_readback
    generic_source_readback = None
    if source_readback is None:
        generic_source_readback = _build_paper_mission_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="inspect",
            dry_run=False,
            source=source,
        )
        if _readback_has_current_transaction_terminal_closeout(
            generic_source_readback,
            workspace_root=Path(profile.workspace_root),
        ):
            return generic_source_readback
    if allow_stage_packet_autodiscovery:
        stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            source_readback=source_readback or generic_source_readback or {},
            source=source,
        )
        if stage_attempt_source is not None:
            return stage_attempt_source
    if source_readback is not None:
        materialized_run_stage_attempt = (
            _materialized_run_terminal_source_readback(
                materialized_readback=source_readback,
                study_root=Path(profile.studies_root) / study_id,
            )
        )
        if materialized_run_stage_attempt is not None:
            return materialized_run_stage_attempt
        return source_readback
    if generic_source_readback is not None:
        return generic_source_readback
    return _build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source=source,
    )


def _source_readback_has_owner_repair_receipt(readback: Mapping[str, Any]) -> bool:
    if (
        _optional_text(_mapping(readback.get("mas_receipt_consumption")).get("status"))
        == "owner_consumed_mas_repair_delta"
    ):
        return True
    decision = _mapping(readback.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    return (
        _optional_text(decision.get("source")) == "study_controller_owner_repair_receipt"
        and _optional_text(outcome.get("kind")) == "owner_receipt"
    )


def _materialized_run_terminal_source_readback(
    *,
    materialized_readback: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any] | None:
    materialized_ref = _optional_text(materialized_readback.get("materialized_mission_ref"))
    raw_materialized = (
        _mapping(_load_optional_json_object(Path(materialized_ref)))
        if materialized_ref is not None
        else {}
    )
    paper_mission_run = _mapping(raw_materialized) or _mapping(
        materialized_readback.get("paper_mission_run")
    )
    run_transaction = _mapping(paper_mission_run.get("paper_mission_transaction"))
    if not run_transaction:
        return None
    if _optional_text(run_transaction.get("transaction_id")) == _optional_text(
        _mapping(materialized_readback.get("paper_mission_transaction")).get(
            "transaction_id"
        )
    ):
        return None
    try:
        carrier = paper_mission_stage_run_context(run_transaction)
    except (KeyError, TypeError, ValueError, PaperMissionTransactionContractError):
        return None
    readback = attach_opl_stage_attempt_readback(
        readback={"opl_stage_run_context": carrier},
        study_root=study_root,
    )
    if _optional_text(readback.get("opl_stage_attempt_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return None
    return {
        **dict(materialized_readback),
        "paper_mission_command": "terminalize-stage",
        "source": "paper_mission_run_legacy_transaction",
        "opl_stage_run_context": carrier,
        "opl_stage_attempt_readback": _mapping(
            readback.get("opl_stage_attempt_readback")
        ),
        "opl_stage_attempt_readback_status": _optional_text(
            readback.get("opl_stage_attempt_readback_status")
        ),
    }


def _build_terminalizer_source_readback_from_stage_packet(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    stage_packet: str | Path,
    source: str,
) -> dict[str, Any]:
    packet_ref = Path(stage_packet).expanduser()
    if not packet_ref.is_absolute():
        packet_ref = Path(profile.workspace_root).expanduser().resolve() / packet_ref
    packet = _load_json_object(packet_ref)
    packet_study_id = _optional_text(packet.get("study_id"))
    if packet_study_id is not None and packet_study_id != study_id:
        raise ValueError(
            f"stage packet study_id mismatch: expected {study_id}, got {packet_study_id}"
        )
    base_readback = _build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        source=f"{source}:base-current-package",
        allow_stage_packet_autodiscovery=False,
    )
    route_back = _load_stage_packet_route_back_evidence(
        workspace_root=Path(profile.workspace_root).expanduser().resolve(),
        packet=packet,
    )
    stage_attempt_id = _optional_text(packet.get("stage_attempt_id"))
    work_unit_id = _optional_text(packet.get("work_unit_id")) or _optional_text(
        route_back.get("work_unit_id")
    )
    stage_packet_ref = _first_non_empty_text(
        packet.get("stage_packet_ref"),
        route_back.get("stage_packet_ref"),
        _mapping(route_back.get("source_evidence")).get("paper_mission_transaction_ref"),
    )
    stage_id = _stage_packet_route_stage_id(
        study_id=study_id,
        packet=packet,
        route_back=route_back,
        stage_packet_ref=stage_packet_ref,
    )
    if stage_packet_ref is None:
        stage_packet_ref = str(packet_ref)
    route_back_ref = _optional_text(packet.get("route_back_evidence_ref"))
    candidate_ref = _optional_text(packet.get("owner_answer_ref")) or _optional_text(
        route_back.get("owner_answer_ref")
    )
    provider_attempt_ref = _optional_text(packet.get("provider_attempt_ref")) or (
        f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else None
    )
    closeout_ref = str(packet_ref)
    return {
        **base_readback,
        "surface_kind": "paper_mission_stage_attempt_closeout_readback",
        "source": source,
        "source_ref": closeout_ref,
        "study_id": study_id,
        "mission_id": base_readback.get("mission_id"),
        "candidate_ref": candidate_ref,
        "candidate_manifest_ref": candidate_ref,
        "route_back_evidence_ref": route_back_ref,
        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        "stage_closure_decision": {},
        "stage_closure_decision_ref": None,
        "stage_closure_outcome": None,
        "paper_mission_transaction": {
            "schema_version": "paper-mission-transaction.v1",
            "transaction_id": stage_packet_ref,
            "mission_id": base_readback.get("mission_id"),
            "study_id": study_id,
            "stage_id": stage_id,
            "work_unit_id": work_unit_id,
            "stage_terminal_decision": {
                "decision_kind": "route_back",
                "status": "route_back_evidence_observed",
                "reason": "paper_mission_stage_route_domain_gate_pending",
                "next_owner": "MedAutoScience",
                "next_work_unit": work_unit_id,
                "source_route_back_evidence_ref": route_back_ref,
                "route_back_evidence_ref": route_back_ref,
            },
            "transaction_state": "route_back",
        },
        "stage_terminal_decision": {
            "decision_kind": "route_back",
            "status": "route_back_evidence_observed",
            "reason": "paper_mission_stage_route_domain_gate_pending",
            "next_owner": "MedAutoScience",
            "next_work_unit": work_unit_id,
            "source_route_back_evidence_ref": route_back_ref,
            "route_back_evidence_ref": route_back_ref,
        },
        "transaction_state": "route_back",
        "consume_candidate_status": "route_back",
        "opl_stage_attempt_readback_status": "opl_runtime_terminal_readback_observed",
        "opl_stage_attempt_readback": _stage_packet_opl_stage_attempt_readback(
            packet=packet,
            route_back=route_back,
            stage_attempt_id=stage_attempt_id,
            stage_id=stage_id,
            work_unit_id=work_unit_id,
            provider_attempt_ref=provider_attempt_ref,
            closeout_ref=closeout_ref,
        ),
        "stage_attempt_closeout_packet": packet,
    }


def _latest_stage_attempt_route_back_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source_readback: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    packets_root = (
        Path(profile.workspace_root).expanduser().resolve()
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
    )
    if not packets_root.exists():
        return None
    expected = _expected_stage_attempt_identity(source_readback)
    current_transaction_ref = _optional_text(
        _mapping(source_readback.get("paper_mission_transaction")).get("transaction_id")
    )
    preferred_stage_attempt_ids = _preferred_terminal_stage_attempt_ids(source_readback)
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    current_terminal_mtime = _terminal_closeout_mtime_from_readback(
        source_readback,
        workspace_root=workspace_root,
    )
    candidates: list[tuple[int, int, int, int, float, int, str, Path]] = []
    for packet_ref in packets_root.glob("**/stage_attempt_closeout_packet.json"):
        packet = _load_optional_json_object(packet_ref)
        if not isinstance(packet, Mapping):
            continue
        if _optional_text(packet.get("study_id")) != study_id:
            continue
        route_back = _load_stage_packet_route_back_evidence(
            workspace_root=Path(profile.workspace_root).expanduser().resolve(),
            packet=packet,
        )
        route_ref = _optional_text(packet.get("route_back_evidence_ref")) or _optional_text(
            route_back.get("route_back_evidence_ref")
        )
        if route_ref is None and _optional_text(packet.get("owner_answer_kind")) != (
            "route_back_evidence_ref"
        ):
            continue
        stage_packet_ref = _first_non_empty_text(
            packet.get("stage_packet_ref"),
            route_back.get("stage_packet_ref"),
            _mapping(route_back.get("source_evidence")).get(
                "paper_mission_transaction_ref"
            ),
        )
        stage_id = _stage_packet_route_stage_id(
            study_id=study_id,
            packet=packet,
            route_back=route_back,
            stage_packet_ref=stage_packet_ref,
        )
        work_unit_id = _first_non_empty_text(
            packet.get("work_unit_id"),
            route_back.get("work_unit_id"),
        )
        stage_attempt_id = _optional_text(packet.get("stage_attempt_id"))
        transaction_priority = _stage_packet_transaction_priority(
            stage_packet_ref=stage_packet_ref,
            current_transaction_ref=current_transaction_ref,
            study_id=study_id,
        )
        matches_expected_identity = (
            (not expected["stage_ids"] or stage_id in expected["stage_ids"])
            and (
                not expected["work_unit_ids"]
                or work_unit_id in expected["work_unit_ids"]
            )
        )
        bucket_priority = 0
        if (
            preferred_stage_attempt_ids
            and stage_attempt_id is not None
            and stage_attempt_id in preferred_stage_attempt_ids
            and matches_expected_identity
        ):
            bucket_priority = 2
        elif matches_expected_identity:
            bucket_priority = 1
        semantic_priority = _stage_packet_route_back_semantic_priority(
            packet=packet,
            route_back=route_back,
        )
        packet_mtime = packet_ref.stat().st_mtime
        newer_successor_priority = (
            1
            if (
                matches_expected_identity
                and current_terminal_mtime is not None
                and packet_mtime > current_terminal_mtime
            )
            else 0
        )
        successor_priority = newer_successor_priority
        candidates.append(
            (
                successor_priority,
                bucket_priority,
                transaction_priority,
                semantic_priority if transaction_priority or bucket_priority else 0,
                packet_mtime,
                semantic_priority,
                str(packet_ref),
                packet_ref,
            )
        )
    if not candidates:
        return None
    packet_ref = max(
        candidates,
        key=lambda item: (item[0], item[1], item[2], item[3], item[4], item[5]),
    )[6]
    return _build_terminalizer_source_readback_from_stage_packet(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        stage_packet=packet_ref,
        source=f"{source}:autodiscovered-stage-packet",
    )


def _terminal_closeout_mtime_from_readback(
    readback: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> float | None:
    mtimes: list[float] = []
    for carrier_key in (
        "current_opl_stage_attempt_readback",
        "opl_stage_attempt_readback",
    ):
        mtime = _terminal_closeout_mtime(
            _mapping(_mapping(readback.get(carrier_key)).get("terminal_closeout")),
            workspace_root=workspace_root,
        )
        if mtime is not None:
            mtimes.append(mtime)
    return max(mtimes) if mtimes else None


def _stage_closure_next_action_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
) -> bool:
    return _shared_stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=next_action,
        domain_transition_next_action=domain_transition_next_action,
        include_delivery_sync_actions=False,
    )
