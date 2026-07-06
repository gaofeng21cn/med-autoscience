from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_opl_readback import attach_opl_runtime_carrier_readback
from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_opl_readback_parts.route_identity import (
    route_ref_matches,
)
from med_autoscience.paper_mission_transaction import PaperMissionTransactionContractError
from med_autoscience.paper_mission_stage_closure_ledger import (
    write_paper_mission_stage_closure_decision,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback as _terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback as _terminal_owner_gate_from_carrier_readback,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback as _terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_readback as _terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.cli_parts.paper_mission_output_roots import (
    _assert_safe_stage_closure_output_root,
)
from med_autoscience.cli_parts.paper_mission_command_parts.command_metadata import (
    action_intent as _action_intent,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback import (
    build_materialized_mission_readback_if_available as _build_materialized_mission_readback_if_available,
    _domain_transition_direct_next_action_runtime_readback as _build_domain_transition_direct_next_action_runtime_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _first_text,
    _load_optional_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer import (
    FORBIDDEN_AUTHORITY_CLAIMS as STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS,
    STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    stage_closure_source_readback_summary as _stage_closure_source_readback_summary,
    stage_closure_terminalizer_output_root as _stage_closure_terminalizer_output_root,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_next_action import (
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from med_autoscience.controllers.stage_closure_terminalizer import stage_closure_decision_missing
from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    align_carrier_readback_with_owner_consumption as _align_carrier_readback_with_owner_consumption,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.study_progress_parts.canonical_next_action_selection import (
    domain_transition_canonical_next_action as _domain_transition_canonical_next_action,
)


def _build_paper_mission_readback(**kwargs: Any) -> dict[str, Any]:
    from med_autoscience.cli_parts import paper_mission_commands

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
        terminalizer_status = (
            "legacy_terminalizer_outcome_superseded"
            if existing_decision
            else "terminalizer_outcome_materialized"
        )
    output_manifest = None
    resolved_output_root = _stage_closure_terminalizer_output_root(
        profile=profile,
        output_root=output_root,
    )
    if not dry_run:
        root = resolved_output_root
        _assert_safe_stage_closure_output_root(root)
        output_manifest = write_paper_mission_stage_closure_decision(
            output_root=root,
            study_id=study_id,
            decision=decision,
            source_readback=source_readback,
            source=source,
            forbidden_authority_writes=STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
            forbidden_authority_claims=STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS,
        )
        decision = {
            **decision,
            "decision_ref": output_manifest["stage_closure_decision_ref"],
            "source_ref": output_manifest["stage_closure_decision_ref"],
        }
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
        **({"output_manifest": output_manifest} if output_manifest is not None else {}),
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
        "opl_runtime_carrier_readback",
        "current_opl_runtime_carrier_readback",
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
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if source_readback is not None:
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
        direct_stage_attempt = _domain_transition_direct_terminal_source_readback(
            materialized_readback=source_readback,
            study_root=Path(profile.studies_root) / study_id,
            profile=profile,
            study_id=study_id,
            enable_opl_live_probe=True,
            opl_bin=None,
        )
        if direct_stage_attempt is not None:
            if allow_stage_packet_autodiscovery:
                stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                    source_readback=direct_stage_attempt,
                    source=source,
                )
                if (
                    stage_attempt_source is not None
                    and _terminal_source_readback_newer(
                        candidate=stage_attempt_source,
                        current=direct_stage_attempt,
                        workspace_root=Path(profile.workspace_root),
                    )
                ):
                    return stage_attempt_source
            return direct_stage_attempt
    generic_source_readback = None
    if source_readback is None:
        generic_source_readback = _build_paper_mission_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="inspect",
            dry_run=False,
            source=source,
            enable_opl_live_probe=True,
        )
        if _readback_has_current_transaction_terminal_closeout(
            generic_source_readback,
            workspace_root=Path(profile.workspace_root),
        ):
            return generic_source_readback
        direct_stage_attempt = _domain_transition_direct_terminal_source_readback(
            materialized_readback=generic_source_readback,
            study_root=Path(profile.studies_root) / study_id,
            profile=profile,
            study_id=study_id,
            enable_opl_live_probe=True,
            opl_bin=None,
        )
        if direct_stage_attempt is not None:
            if allow_stage_packet_autodiscovery:
                stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                    source_readback=direct_stage_attempt,
                    source=source,
                )
                if (
                    stage_attempt_source is not None
                    and _terminal_source_readback_newer(
                        candidate=stage_attempt_source,
                        current=direct_stage_attempt,
                        workspace_root=Path(profile.workspace_root),
                    )
                ):
                    return stage_attempt_source
            return direct_stage_attempt
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
    consumption_readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    if consumption_readback is not None:
        return attach_opl_runtime_carrier_readback(
            readback={
                **consumption_readback,
                "paper_mission_command": "terminalize-stage",
                "source": "paper_mission_consumption_ledger",
            },
            study_root=Path(profile.studies_root) / study_id,
            enable_opl_live_probe=True,
            opl_bin=None,
        )
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
        enable_opl_live_probe=True,
    )


def _terminal_source_readback_newer(
    *,
    candidate: Mapping[str, Any],
    current: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    candidate_closeout = _mapping(
        _mapping(candidate.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    current_closeout = _mapping(
        _mapping(current.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    return _terminal_closeout_newer(
        candidate=candidate_closeout,
        current=current_closeout,
        workspace_root=workspace_root,
    )


def _stage_closure_matches_current_transaction_with_terminal_closeout(
    readback: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> bool:
    if _optional_text(readback.get("consume_candidate_status")) in {
        "not_consumed",
        "not_applicable",
    }:
        return False
    if _optional_text(readback.get("mission_state")) in {"planned", "draft"}:
        return False
    stage_closure = _mapping(readback.get("stage_closure_decision"))
    transaction = _mapping(readback.get("paper_mission_transaction"))
    transaction_ref = _optional_text(transaction.get("transaction_id"))
    closure_ref = _optional_text(
        _mapping(stage_closure.get("identity")).get("paper_mission_transaction_ref")
    ) or _optional_text(stage_closure.get("paper_mission_transaction_ref"))
    if transaction_ref is None or closure_ref != transaction_ref:
        return False
    opl_closeout = _mapping(stage_closure.get("opl_closeout"))
    stage_attempt_id = _optional_text(opl_closeout.get("stage_attempt_id"))
    live_terminal_closeout = _mapping(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    live_stage_attempt_id = _optional_text(live_terminal_closeout.get("stage_attempt_id"))
    if not _terminal_closeout_uses_stage_attempt_packet(live_terminal_closeout):
        return False
    direct_terminal_closeout = _mapping(
        _mapping(readback.get("current_opl_runtime_carrier_readback")).get(
            "terminal_closeout"
        )
    )
    if _terminal_closeout_newer(
        candidate=direct_terminal_closeout,
        current=live_terminal_closeout,
        workspace_root=workspace_root,
    ):
        return False
    return (
        stage_attempt_id is not None
        and stage_attempt_id == live_stage_attempt_id
        and _optional_text(opl_closeout.get("status"))
        == "opl_runtime_terminal_readback_observed"
    )


def _readback_has_current_transaction_terminal_closeout(
    readback: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> bool:
    if _optional_text(readback.get("consume_candidate_status")) in {
        "not_consumed",
        "not_applicable",
    }:
        return False
    if _optional_text(readback.get("mission_state")) in {"planned", "draft"}:
        return False
    transaction_ref = _optional_text(
        _mapping(readback.get("paper_mission_transaction")).get("transaction_id")
    )
    if transaction_ref is None:
        return False
    terminal_closeout = _mapping(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    if not _terminal_closeout_uses_stage_attempt_packet(terminal_closeout):
        return False
    if _terminal_closeout_mtime(terminal_closeout, workspace_root=workspace_root) is None:
        return False
    closeout_transaction_ref = _first_non_empty_text(
        terminal_closeout.get("paper_mission_transaction_ref"),
        terminal_closeout.get("stage_packet_ref"),
    )
    return route_ref_matches(closeout_transaction_ref, transaction_ref)


def _stage_closure_decision_uses_stale_terminal_closeout(
    *,
    existing_decision: Mapping[str, Any],
    source_readback: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    if not _readback_has_current_transaction_terminal_closeout(
        source_readback,
        workspace_root=workspace_root,
    ):
        return False
    current_stage_attempt_id = _optional_text(
        _mapping(
            _mapping(source_readback.get("opl_runtime_carrier_readback")).get(
                "terminal_closeout"
            )
        ).get("stage_attempt_id")
    )
    existing_stage_attempt_id = _optional_text(
        _mapping(existing_decision.get("opl_closeout")).get("stage_attempt_id")
    )
    return (
        current_stage_attempt_id is not None
        and existing_stage_attempt_id is not None
        and current_stage_attempt_id != existing_stage_attempt_id
    )


def _terminal_closeout_uses_stage_attempt_packet(closeout: Mapping[str, Any]) -> bool:
    refs = [_optional_text(closeout.get("closeout_ref"))]
    closeout_refs = closeout.get("closeout_refs")
    if isinstance(closeout_refs, (list, tuple)):
        refs.extend(_optional_text(item) for item in closeout_refs)
    return any(
        ref is not None
        and "paper_mission_stage_attempts" in ref
        and ref.endswith("stage_attempt_closeout_packet.json")
        for ref in refs
    )


def _terminal_closeout_newer(
    *,
    candidate: Mapping[str, Any],
    current: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    candidate_mtime = _terminal_closeout_mtime(candidate, workspace_root=workspace_root)
    current_mtime = _terminal_closeout_mtime(current, workspace_root=workspace_root)
    if candidate_mtime is None:
        return False
    if current_mtime is None:
        return True
    return candidate_mtime > current_mtime


def _terminal_closeout_mtime(
    closeout: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> float | None:
    refs = [_optional_text(closeout.get("closeout_ref"))]
    closeout_refs = closeout.get("closeout_refs")
    if isinstance(closeout_refs, (list, tuple)):
        refs.extend(_optional_text(item) for item in closeout_refs)
    for ref in refs:
        if ref is None or ref.startswith(("opl://", "temporal://")):
            continue
        path = Path(ref).expanduser()
        if not path.is_absolute():
            path = workspace_root.expanduser().resolve() / path
        try:
            return path.stat().st_mtime
        except OSError:
            continue
    return None


def _domain_transition_direct_terminal_source_readback(
    *,
    materialized_readback: Mapping[str, Any] | None,
    study_root: Path,
    profile: Any | None = None,
    study_id: str | None = None,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any] | None:
    readback = _mapping(materialized_readback)
    direct = _mapping(readback.get("domain_transition_direct_stage_attempt"))
    if not direct and profile is not None and study_id:
        next_action = _mapping(readback.get("next_action"))
        canonical_next_action_source = _optional_text(
            readback.get("canonical_next_action_source")
        )
        domain_transition = _mapping(readback.get("domain_transition"))
        stage_closure_outcome = _mapping(
            _mapping(readback.get("stage_closure_decision")).get("outcome")
        )
        if (
            canonical_next_action_source != "domain_transition.next_action"
            and stage_closure_outcome.get("kind") != "typed_blocker"
        ):
            domain_transition_next_action = _domain_transition_canonical_next_action(
                {"domain_transition": domain_transition}
            )
            if not domain_transition_next_action and readback:
                domain_transition = study_domain_transition_table.project_domain_transition(
                    study_id=study_id,
                    study_root=study_root,
                    status={},
                    macro_state={},
                    active_run_id=None,
                )
                domain_transition_next_action = _domain_transition_canonical_next_action(
                    {"domain_transition": domain_transition}
                )
            if domain_transition_next_action:
                next_action = domain_transition_next_action
                canonical_next_action_source = "domain_transition.next_action"
        direct = _build_domain_transition_direct_next_action_runtime_readback(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            inspect_readback=readback,
            next_action=next_action,
            canonical_next_action_source=canonical_next_action_source,
            enable_opl_live_probe=enable_opl_live_probe,
            opl_bin=opl_bin,
        )
    if not direct:
        return None
    direct = attach_opl_runtime_carrier_readback(
        readback=direct,
        study_root=study_root,
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if _optional_text(direct.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return None
    return {
        **direct,
        "paper_mission_command": "terminalize-stage",
        "source": "paper_mission_domain_transition_direct_stage_attempt",
        "study_id": _optional_text(direct.get("study_id"))
        or _optional_text(readback.get("study_id")),
        "mission_id": _optional_text(direct.get("mission_id"))
        or _optional_text(readback.get("mission_id")),
        "objective": _optional_text(readback.get("objective")),
        "current_package": _mapping(readback.get("current_package")),
        "domain_transition": _mapping(readback.get("domain_transition")),
        "source_ref": _optional_text(
            _mapping(direct.get("next_action")).get("outcome_ref")
        )
        or _optional_text(_mapping(direct.get("next_action")).get("action_id")),
    }


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
        carrier = paper_mission_opl_runtime_carrier(run_transaction)
    except (KeyError, TypeError, ValueError, PaperMissionTransactionContractError):
        return None
    readback = attach_opl_runtime_carrier_readback(
        readback={"opl_runtime_carrier": carrier},
        study_root=study_root,
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if _optional_text(readback.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return None
    return {
        **dict(materialized_readback),
        "paper_mission_command": "terminalize-stage",
        "source": "paper_mission_run_legacy_transaction",
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": _mapping(
            readback.get("opl_runtime_carrier_readback")
        ),
        "opl_runtime_readback_status": _optional_text(
            readback.get("opl_runtime_readback_status")
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
        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
        "opl_runtime_carrier_readback": _stage_packet_opl_runtime_carrier_readback(
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
    candidates: list[tuple[int, int, int, float, int, str, Path]] = []
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
        candidates.append(
            (
                transaction_priority,
                bucket_priority,
                semantic_priority if transaction_priority or bucket_priority else 0,
                packet_ref.stat().st_mtime,
                semantic_priority,
                str(packet_ref),
                packet_ref,
            )
        )
    if not candidates:
        return None
    packet_ref = max(
        candidates,
        key=lambda item: (item[0], item[1], item[2], item[3], item[4]),
    )[5]
    return _build_terminalizer_source_readback_from_stage_packet(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        stage_packet=packet_ref,
        source=f"{source}:autodiscovered-stage-packet",
    )

def _preferred_terminal_stage_attempt_ids(
    readback: Mapping[str, Any],
) -> set[str]:
    stage_attempt_ids = set()
    for carrier_key in (
        "opl_runtime_carrier_readback",
        "current_opl_runtime_carrier_readback",
    ):
        terminal_closeout = _mapping(
            _mapping(readback.get(carrier_key)).get("terminal_closeout")
        )
        stage_attempt_id = _optional_text(terminal_closeout.get("stage_attempt_id"))
        if stage_attempt_id is not None and (
            carrier_key == "current_opl_runtime_carrier_readback"
            or _terminal_closeout_is_live_runtime_observed(terminal_closeout)
        ):
            stage_attempt_ids.add(stage_attempt_id)
    return stage_attempt_ids


def _terminal_closeout_is_live_runtime_observed(
    closeout: Mapping[str, Any],
) -> bool:
    closeout_ref = _optional_text(closeout.get("closeout_ref"))
    return (
        closeout_ref is not None
        and closeout_ref.startswith("opl://family-runtime/tasks/")
    ) or _optional_text(closeout.get("runtime_readback_source")) in {
        "opl_family_runtime_queue_inspect",
        "opl_family_runtime_queue_list",
    }
def _expected_stage_attempt_identity(readback: Mapping[str, Any]) -> dict[str, set[str]]:
    next_action = _mapping(readback.get("next_action"))
    domain_transition = _mapping(readback.get("domain_transition"))
    transition_work_unit = _mapping(domain_transition.get("next_work_unit"))
    stage_decision = _mapping(readback.get("stage_terminal_decision"))
    transaction = _mapping(readback.get("paper_mission_transaction"))
    return {
        "stage_ids": {
            value
            for value in (
                _optional_text(next_action.get("stage_id")),
                _optional_text(domain_transition.get("route_target")),
                _optional_text(transaction.get("stage_id")),
                _optional_text(stage_decision.get("target_stage_id")),
            )
            if value is not None
        },
        "work_unit_ids": {
            value
            for value in (
                _optional_text(next_action.get("work_unit_id")),
                _optional_text(transition_work_unit.get("unit_id")),
                _optional_text(transaction.get("work_unit_id")),
                _optional_text(stage_decision.get("next_work_unit")),
                _optional_text(stage_decision.get("target_work_unit_id")),
            )
            if value is not None
        },
    }


def _load_stage_packet_route_back_evidence(
    *,
    workspace_root: Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    ref = _optional_text(packet.get("route_back_evidence_ref"))
    if ref is None:
        return {}
    path = Path(ref).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    if not path.exists():
        return {}
    return _load_json_object(path)


def _stage_packet_route_stage_id(
    *,
    study_id: str,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
    stage_packet_ref: str | None,
) -> str | None:
    derived = _paper_mission_transaction_stage_id(
        stage_packet_ref,
        study_id=study_id,
    )
    packet_stage_id = _optional_text(packet.get("stage_id"))
    route_stage_id = _optional_text(route_back.get("stage_id"))
    route_work_unit_id = _optional_text(route_back.get("work_unit_id"))
    return (
        derived
        or (
            route_stage_id
            if packet_stage_id is not None
            and route_work_unit_id is not None
            and packet_stage_id == route_work_unit_id
            else None
        )
        or packet_stage_id
        or route_stage_id
    )


def _paper_mission_transaction_stage_id(
    transaction_ref: str | None,
    *,
    study_id: str,
) -> str | None:
    if transaction_ref is None:
        return None
    prefix = f"paper-mission-transaction::{study_id}::"
    suffix = "::paper-mission::"
    if not transaction_ref.startswith(prefix) or suffix not in transaction_ref:
        return None
    stage_segment = transaction_ref[len(prefix) : transaction_ref.index(suffix)]
    return stage_segment.split("::followthrough::", 1)[0] if stage_segment else None


def _stage_packet_transaction_priority(
    *,
    stage_packet_ref: str | None,
    current_transaction_ref: str | None,
    study_id: str,
) -> int:
    if stage_packet_ref is None or current_transaction_ref is None:
        return 0
    if stage_packet_ref == current_transaction_ref:
        return 1
    if stage_packet_ref.startswith(f"{current_transaction_ref}::followthrough::"):
        return 2
    if current_transaction_ref.startswith(f"{stage_packet_ref}::followthrough::"):
        return 1
    current_stage = _paper_mission_transaction_stage_id(
        current_transaction_ref, study_id=study_id
    )
    stage_packet_stage = _paper_mission_transaction_stage_id(
        stage_packet_ref, study_id=study_id
    )
    if current_stage is None or stage_packet_stage is None:
        return 0
    if stage_packet_stage.startswith(f"{current_stage}::followthrough::"):
        return 2
    if current_stage.startswith(f"{stage_packet_stage}::followthrough::"):
        return 1
    return 0


def _stage_packet_route_back_semantic_priority(
    *,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> int:
    route_impact = _mapping(packet.get("route_impact"))
    priority = 0
    if _first_non_empty_text(
        packet.get("paper_facing_delta_ref"),
        route_impact.get("paper_facing_delta_ref"),
        route_back.get("paper_facing_delta_ref"),
    ) is not None:
        priority += 2
    if _first_non_empty_text(
        packet.get("progress_events_ref"),
        route_back.get("progress_events_ref"),
    ) is not None:
        priority += 1
    if _first_non_empty_text(
        route_impact.get("stage_log_summary"),
        route_impact.get("user_stage_log"),
        route_impact.get("human_stage_log"),
    ) is not None:
        priority += 1
    if _first_non_empty_text(
        route_back.get("owner_gate_verdict"),
        route_back.get("next_forced_paper_action"),
        route_back.get("source_readiness_checklist_ref"),
        route_back.get("remaining_blocker"),
    ) is not None:
        priority += 1
    if _mapping(route_back.get("source_evidence")):
        priority += 1
    return priority


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _stage_packet_opl_runtime_carrier_readback(
    *,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
    stage_attempt_id: str | None,
    stage_id: str | None,
    work_unit_id: str | None,
    provider_attempt_ref: str | None,
    closeout_ref: str,
) -> dict[str, Any]:
    closeout_receipt_status = (
        _optional_text(packet.get("closeout_receipt_status"))
        or "accepted_stage_attempt_closeout"
    )
    blocked_reason = (
        _optional_text(packet.get("blocked_reason"))
        or "paper_mission_stage_route_domain_gate_pending"
    )
    receipt_ref = provider_attempt_ref or closeout_ref
    receipt_evidence = {
        "receipt_kind": "opl_transition_receipt",
        "receipt_ref": receipt_ref,
        "runtime_closeout_ref": closeout_ref,
        "stage_attempt_ref": receipt_ref,
        "can_claim_paper_progress": False,
    }
    return {
        "surface_kind": "paper_mission_opl_runtime_carrier_readback",
        "schema_version": 1,
        "carrier_status": "opl_runtime_terminal_readback_observed",
        "runtime_readback_status": "terminal_closeout_observed",
        "dispatch_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "terminal_closeout": {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": _optional_text(packet.get("status")) or "completed",
            "study_id": _optional_text(packet.get("study_id"))
            or _optional_text(route_back.get("study_id")),
            "stage_id": stage_id,
            "stage_attempt_id": stage_attempt_id,
            "work_unit_id": work_unit_id,
            "provider_attempt_ref": provider_attempt_ref,
            "blocked_reason": blocked_reason,
            "closeout_refs": [closeout_ref],
            "closeout_receipt_status": closeout_receipt_status,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "domain_completion_claimed": False,
            "domain_ready_claimed": False,
        },
        "opl_transition_receipt": {
            "surface_kind": "opl_transition_receipt",
            "receipt_status": "terminal_closeout_observed",
            "role": "transport_receipt_only",
            "stage_attempt_id": stage_attempt_id,
            "stage_attempt_ref": receipt_ref,
            "closeout_receipt_status": closeout_receipt_status,
            "blocked_reason": blocked_reason,
            "can_claim_paper_progress": False,
        },
        "receipt_evidence": receipt_evidence,
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
            "next_legal_action": (
                "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            ),
            "forbidden_next_action": "synonymous_route_back_redrive",
            "receipt_ref": receipt_ref,
            "runtime_closeout_ref": closeout_ref,
            "durable_stop_allowed": False,
        },
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return dict(payload)


def _typed_blocker_resolution_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
) -> bool:
    if not typed_blocker_resolution_readback:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return False
    return bool(_mapping(typed_blocker_resolution_readback.get("next_owner_action")))


def _stage_closure_next_action_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
) -> bool:
    action = _mapping(next_action)
    if not action:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if (
        _mapping(domain_transition_next_action)
        and outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    ):
        if _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption_readback):
            return not _owner_consumed_route_checkpoint_yields_to_domain_transition(
                stage_closure_decision=stage_closure_decision,
                domain_transition_next_action=domain_transition_next_action,
            )
        return _route_checkpoint_matches_domain_transition(
            stage_closure_decision=stage_closure_decision,
            outcome=outcome,
            domain_transition_next_action=domain_transition_next_action,
        )
    if _optional_text(action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return True
    return (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    )


def _receipt_owner_consumed_route_checkpoint(
    readback: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping(readback)
    if _optional_text(payload.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(payload.get("mas_receipt_consumption"))
    return _optional_text(consumption.get("status")) == "owner_consumed_route_checkpoint"


def _align_current_carrier_owner_consumption(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> dict[str, Any]:
    fields = dict(transaction_output_fields)
    changed = False
    current = _mapping(fields.get("current_opl_runtime_carrier_readback"))
    aligned_current = current
    preserve_direct_successor = _preserve_direct_successor_runtime_readback(
        transaction_output_fields=fields,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    )
    if current and not preserve_direct_successor:
        aligned_current = _align_carrier_readback_with_owner_consumption(
            carrier_readback=current,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
        if aligned_current != current:
            fields["current_opl_runtime_carrier_readback"] = aligned_current
            changed = True
    direct = _mapping(fields.get("domain_transition_direct_stage_attempt"))
    if direct and aligned_current != current:
        fields["domain_transition_direct_stage_attempt"] = {
            **direct,
            "opl_runtime_carrier_readback": aligned_current,
        }
    carrier = _mapping(fields.get("opl_runtime_carrier_readback"))
    if carrier:
        aligned_carrier = _align_carrier_readback_with_owner_consumption(
            carrier_readback=carrier,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
        if aligned_carrier != carrier:
            fields["opl_runtime_carrier_readback"] = aligned_carrier
            changed = True
            aligned_gate = _terminal_owner_gate_from_carrier_readback(aligned_carrier)
            owner_answer_readback = {}
            transaction_readback = _mapping(fields.get("paper_mission_transaction_readback"))
            if transaction_readback:
                paper_mission_transaction = _mapping(
                    transaction_readback.get("paper_mission_transaction")
                )
                if paper_mission_transaction and aligned_gate:
                    owner_answer_readback = _terminal_owner_gate_owner_answer_readback(
                        terminal_owner_gate=aligned_gate,
                        paper_mission_transaction=paper_mission_transaction,
                        artifact_delta_refs=_mapping_list(
                            transaction_readback.get("artifact_delta_refs")
                        )
                        or _mapping_list(
                            paper_mission_transaction.get("artifact_delta_refs")
                        ),
                        paper_audit_pack_refs=_mapping(
                            transaction_readback.get("paper_audit_pack_refs")
                        )
                        or _mapping(
                            paper_mission_transaction.get("paper_audit_pack_refs")
                        ),
                    )
                authority_readback = _terminal_owner_gate_authority_readback(aligned_gate)
                if owner_answer_readback:
                    authority_readback = _terminal_owner_gate_authority_consume_readback(
                        terminal_owner_gate_authority_readback=authority_readback,
                        owner_answer_readback=owner_answer_readback,
                    )
                fields["paper_mission_transaction_readback"] = {
                    **transaction_readback,
                    "opl_runtime_carrier_readback": aligned_carrier,
                    "terminal_owner_gate": aligned_gate or None,
                    "terminal_owner_gate_authority_readback": authority_readback or None,
                    "terminal_owner_gate_owner_answer_readback": (
                        owner_answer_readback or None
                    ),
                }
            if aligned_gate:
                fields["terminal_owner_gate"] = aligned_gate
                authority_readback = _terminal_owner_gate_authority_readback(aligned_gate)
                if owner_answer_readback:
                    authority_readback = _terminal_owner_gate_authority_consume_readback(
                        terminal_owner_gate_authority_readback=authority_readback,
                        owner_answer_readback=owner_answer_readback,
                    )
                fields["terminal_owner_gate_authority_readback"] = authority_readback or None
                fields["terminal_owner_gate_owner_answer_readback"] = (
                    owner_answer_readback or None
                )
    return fields if changed else transaction_output_fields


def _preserve_direct_successor_runtime_readback(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> bool:
    direct = _mapping(transaction_output_fields.get("domain_transition_direct_stage_attempt"))
    if not direct:
        return False
    handoff = _mapping(direct.get("opl_route_handoff"))
    successor_owner_consumption_ref = _optional_text(
        handoff.get("owner_consumption_readback_ref")
    )
    if successor_owner_consumption_ref is None:
        return False
    applied_owner_consumption_ref = _first_text(
        receipt_owner_consumption_readback.get("source_ref"),
        receipt_owner_consumption_readback.get("decision_ref"),
    )
    if successor_owner_consumption_ref != applied_owner_consumption_ref:
        return False
    carrier_readback = _mapping(direct.get("opl_runtime_carrier_readback"))
    if _carrier_matches_owner_consumed_stage_attempt(
        carrier_readback=carrier_readback,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    ):
        return False
    carrier_status = _optional_text(carrier_readback.get("carrier_status"))
    return carrier_status in {
        "opl_runtime_attempt_running_observed",
        "opl_runtime_terminal_readback_observed",
    }


def _carrier_matches_owner_consumed_stage_attempt(
    *,
    carrier_readback: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> bool:
    carrier_identities = _carrier_stage_attempt_identities(carrier_readback)
    receipt_identities = _receipt_owner_consumption_stage_attempt_identities(
        receipt_owner_consumption_readback
    )
    return bool(carrier_identities and receipt_identities & carrier_identities)


def _carrier_stage_attempt_identities(carrier_readback: Mapping[str, Any]) -> set[str]:
    identities: set[str] = set()
    for surface in (
        carrier_readback,
        _mapping(carrier_readback.get("opl_transition_receipt")),
        _mapping(carrier_readback.get("receipt_evidence")),
        _mapping(carrier_readback.get("terminal_closeout")),
    ):
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_id"))
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_evidence_ref"))
    return identities


def _receipt_owner_consumption_stage_attempt_identities(
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> set[str]:
    identities: set[str] = set()
    stage_closure_decision = _mapping(
        receipt_owner_consumption_readback.get("stage_closure_decision")
    )
    for surface in (
        receipt_owner_consumption_readback,
        _mapping(receipt_owner_consumption_readback.get("mas_receipt_consumption")),
        _mapping(receipt_owner_consumption_readback.get("opl_transition_receipt")),
        _mapping(receipt_owner_consumption_readback.get("receipt_evidence")),
        _mapping(stage_closure_decision.get("opl_closeout")),
    ):
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_id"))
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_evidence_ref"))
    return identities


def _add_stage_attempt_identity(identities: set[str], value: object) -> None:
    text = _optional_text(value)
    if text is None:
        return
    identities.add(text)
    prefix = "opl://stage-attempts/"
    if text.startswith(prefix):
        identities.add(text.removeprefix(prefix))


def _route_checkpoint_matches_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    outcome: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    if not _route_checkpoint_identity_matches_domain_transition(
        stage_closure_decision=stage_closure_decision,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return False
    return (
        stage_closure_decision.get("authority_materialized") is True
        or _optional_text(outcome.get("route_checkpoint_evidence_ref")) is not None
        or _optional_text(
            _mapping(stage_closure_decision.get("opl_closeout")).get("stage_attempt_id")
        )
        is not None
    )


def _owner_consumed_route_checkpoint_yields_to_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    if _route_checkpoint_identity_matches_domain_transition(
        stage_closure_decision=stage_closure_decision,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return True
    action = _mapping(domain_transition_next_action)
    if _optional_text(action.get("surface_kind")) != "mas_next_action_envelope":
        return False
    if _optional_text(action.get("action_type")) != "request_opl_stage_attempt":
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if action_stage is None or action_work_unit is None:
        return False
    return decision_stage in {action_stage, "submission_milestone_candidate"}


def _route_checkpoint_identity_matches_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping(domain_transition_next_action)
    if not action:
        return False
    decision_work_unit = _optional_text(stage_closure_decision.get("work_unit_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if (
        decision_work_unit is not None
        and action_work_unit is not None
        and decision_work_unit != action_work_unit
    ):
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    if (
        decision_stage is not None
        and action_stage is not None
        and decision_stage != action_stage
    ):
        return False
    return True


def _domain_transition_next_action_requests_stage_attempt(
    next_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping(next_action)
    if _optional_text(action.get("surface_kind")) != "mas_next_action_envelope":
        return False
    if _optional_text(action.get("action_type")) == "request_opl_stage_attempt":
        return True
    return (
        _optional_text(action.get("action_family")) is not None
        and _optional_text(action.get("owner")) is not None
        and _optional_text(action.get("work_unit_id")) is not None
    )


def _override_next_action_from_direct_terminal_closeout(
    *,
    direct_next_action_runtime: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
    next_action_override: Mapping[str, Any] | None,
    canonical_next_action_source: str | None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
) -> tuple[Mapping[str, Any], Mapping[str, Any] | None, str | None]:
    direct = _mapping(direct_next_action_runtime)
    if _optional_text(direct.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return stage_closure_decision, next_action_override, canonical_next_action_source
    receipt_owner_consumption = _mapping(receipt_owner_consumption_readback)
    if (
        _optional_text(receipt_owner_consumption.get("status"))
        == "owner_consumption_applied"
        and _optional_text(
            _mapping(receipt_owner_consumption.get("mas_receipt_consumption")).get(
                "status"
            )
        )
        == "owner_consumed_route_checkpoint"
    ):
        handoff = _mapping(direct.get("opl_route_handoff"))
        applied_owner_consumption_ref = _first_text(
            receipt_owner_consumption.get("source_ref"),
            receipt_owner_consumption.get("decision_ref"),
        )
        if applied_owner_consumption_ref is not None and _optional_text(
            handoff.get("owner_consumption_readback_ref")
        ) == applied_owner_consumption_ref:
            return (
                stage_closure_decision,
                next_action_override,
                canonical_next_action_source,
            )
    carrier_readback = _mapping(direct.get("opl_runtime_carrier_readback"))
    if _optional_text(_mapping(carrier_readback.get("mas_receipt_consumption")).get("status")) != (
        "requires_mas_owner_consumption"
    ):
        return stage_closure_decision, next_action_override, canonical_next_action_source
    refreshed_stage_closure_decision = _terminalize_stage_closure_from_readback(direct)
    refreshed_next_action = _next_action_for_stage_closure_decision(
        stage_closure_decision=refreshed_stage_closure_decision,
        transaction_readback=transaction_readback,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
    )
    return (
        refreshed_stage_closure_decision,
        refreshed_next_action,
        "stage_closure.next_action"
        if refreshed_next_action is not None
        else canonical_next_action_source,
    )
