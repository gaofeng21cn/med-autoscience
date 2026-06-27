from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from med_autoscience.paper_mission import (
    build_paper_mission_one_shot_migration_pack,
    paper_mission_by_study,
    paper_mission_candidate_artifact_delta,
    paper_mission_canary_candidate_manifest,
    paper_mission_owner_decision_packet,
)
from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from med_autoscience.paper_mission_candidate_materializer import (
    CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
    adopted_external_paper_delta_authority_boundary,
    materialized_paper_facing_candidate_artifact_payload,
    materialized_paper_facing_candidate_delta,
)
from med_autoscience.paper_mission_candidate_package import (
    AI_OWNER_DECISION_SIDECAR_REFS,
    SUBMISSION_MILESTONE_KIND,
    paper_mission_owner_blocker_packet,
    paper_mission_owner_consumption_request,
    paper_mission_submission_milestone_checklist,
)
from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_consumption_ledger import (
    write_paper_mission_consumption_ledger_outputs,
)
from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
)
from med_autoscience.paper_mission_opl_readback import (
    attach_opl_runtime_carrier_readback,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_next_decision,
    terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    stage_terminal_next_owner_or_human_decision,
    terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback,
    terminal_owner_gate_from_stage_terminal_decision,
    terminal_owner_gate_next_decision,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransaction,
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


PAPER_MISSION_CONTRACT_REF = "contracts/paper_mission_run_contract.json"
PAPER_MISSION_CONTRACT_VERSION = "paper-mission-run.v1"
PAPER_MISSION_CONTRACT_COMMIT = "a410db5c0c874187c8b1ddecee79c2e00c8fe691"
PAPER_MISSION_START_OR_RESUME_TASK_KIND = "paper_mission/start_or_resume"
YANG_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang")
PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_one_shot_migration"
)
PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_candidate_package"
)
PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_consumption_ledger"
)
PAPER_MISSION_ROUTE_BACK_BUDGET_LEDGER_FILENAME = "route_back_budget_ledger.json"
PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS = 2
DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT = 2
OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS = 15
NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS = (
    "owner_decision_packet",
    "human_gate_question",
    "paper_facing_delta",
    "typed_blocker_materialization",
)

FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "/Users/gaofeng/workspace/Yang/**",
)
ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_one_shot_migration",
)
CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_candidate_package",
)
CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_consumption_ledger",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "publication_ready",
    "submission_ready",
    "current_package",
    "owner_receipt_written",
    "typed_blocker_written",
    "human_gate_written",
    "controller_decision_written",
    "publication_eval_written",
    "quality_verdict",
    "artifact_authority",
    "runtime_queue_written",
    "provider_attempt_written",
    "yang_workspace_written",
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


def register_paper_mission_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("paper-mission")
    mission_subparsers = parser.add_subparsers(dest="paper_mission_command", required=True)

    inspect_parser = mission_subparsers.add_parser("inspect")
    _add_common_args(inspect_parser)
    inspect_parser.add_argument("--one-shot-migration", action="store_true")
    inspect_parser.add_argument("--study-progress-payload")
    inspect_parser.add_argument("--domain-health-diagnostic-payload")
    inspect_parser.add_argument("--output-root")

    package_parser = mission_subparsers.add_parser("package-candidate")
    _add_common_args(package_parser)
    package_parser.add_argument("--output-root", required=True)
    package_parser.add_argument("--paper-facing-delta-ref")

    drive_parser = mission_subparsers.add_parser("drive")
    _add_common_args(drive_parser)
    drive_parser.add_argument("--run-id")
    drive_parser.add_argument("--output-root")
    drive_parser.add_argument(
        "--submit-opl-runtime",
        dest="submit_opl_runtime",
        action="store_true",
        default=None,
    )
    drive_parser.add_argument(
        "--no-submit-opl-runtime",
        dest="submit_opl_runtime",
        action="store_false",
    )
    drive_parser.add_argument("--opl-bin")

    start_parser = mission_subparsers.add_parser("start")
    _add_common_args(start_parser)
    start_parser.add_argument("--objective")
    _add_dry_run_only(start_parser)

    resume_parser = mission_subparsers.add_parser("resume")
    _add_common_args(resume_parser)
    resume_parser.add_argument("--mission-id")
    _add_dry_run_only(resume_parser)

    consume_parser = mission_subparsers.add_parser("consume-candidate")
    _add_common_args(consume_parser)
    consume_parser.add_argument("--candidate")
    consume_mode = consume_parser.add_mutually_exclusive_group(required=True)
    consume_mode.add_argument("--dry-run", action="store_true")
    consume_mode.add_argument("--output-root")


def handle_paper_mission_command(
    args: argparse.Namespace,
    *,
    load_profile: Callable[[str | Path], Any],
) -> int | None:
    if args.command != "paper-mission":
        return None
    profile_ref = Path(args.profile)
    profile = load_profile(profile_ref)
    result = build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=args.study_id,
        paper_mission_command=args.paper_mission_command,
        objective=getattr(args, "objective", None),
        mission_id=getattr(args, "mission_id", None),
        candidate=getattr(args, "candidate", None),
        run_id=getattr(args, "run_id", None),
        submit_opl_runtime=getattr(args, "submit_opl_runtime", None),
        opl_bin=getattr(args, "opl_bin", None),
        one_shot_migration=bool(getattr(args, "one_shot_migration", False)),
        study_progress_payload=getattr(args, "study_progress_payload", None),
        domain_health_diagnostic_payload=getattr(
            args,
            "domain_health_diagnostic_payload",
            None,
        ),
        output_root=getattr(args, "output_root", None),
        paper_facing_delta_ref=getattr(args, "paper_facing_delta_ref", None),
        dry_run=bool(getattr(args, "dry_run", False)),
        source="cli",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_paper_mission_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    objective: str | None = None,
    mission_id: str | None = None,
    candidate: str | Path | None = None,
    run_id: str | None = None,
    submit_opl_runtime: bool | None = None,
    opl_bin: str | Path | None = None,
    one_shot_migration: bool = False,
    study_progress_payload: str | Path | None = None,
    domain_health_diagnostic_payload: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_facing_delta_ref: str | Path | None = None,
    dry_run: bool = False,
    source: str = "unknown",
    enable_opl_live_probe: bool = False,
) -> dict[str, Any]:
    if one_shot_migration:
        return _build_one_shot_migration_cli_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            study_progress_payload=study_progress_payload,
            domain_health_diagnostic_payload=domain_health_diagnostic_payload,
            output_root=output_root,
            source=source,
        )
    if paper_mission_command == "package-candidate":
        return _build_materialized_candidate_package_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=output_root,
            paper_facing_delta_ref=paper_facing_delta_ref,
            source=source,
        )
    if paper_mission_command == "drive":
        return _build_paper_mission_drive_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=output_root,
            run_id=run_id,
            submit_opl_runtime=submit_opl_runtime,
            opl_bin=opl_bin,
            source=source,
        )
    if paper_mission_command in {"inspect", "start", "resume"}:
        materialized = _build_materialized_mission_readback_if_available(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command=paper_mission_command,
            dry_run=dry_run,
            source=source,
            enable_opl_live_probe=True,
            opl_bin=opl_bin,
        )
        if materialized is not None:
            return materialized
    selected_objective = _objective_for_command(
        paper_mission_command=paper_mission_command,
        objective=objective,
    )
    selected_mission_id = _mission_id(
        mission_id=mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
    )
    candidate_ref = _resolve_consume_candidate_ref(
        profile=profile,
        study_id=study_id,
        candidate=candidate,
    ) if paper_mission_command == "consume-candidate" else (
        str(candidate) if candidate is not None else None
    )
    authority_consume_readback = (
        consume_paper_mission_candidate(candidate_ref)
        if paper_mission_command == "consume-candidate" and candidate_ref is not None
        else None
    )
    if paper_mission_command == "consume-candidate" and authority_consume_readback is None:
        return _consume_candidate_missing_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command=paper_mission_command,
            source=source,
            dry_run=dry_run,
        )
    previous_consumption_readback = (
        latest_paper_mission_consumption_transaction_readback(
            workspace_root=Path(profile.workspace_root),
            study_id=study_id,
        )
        if paper_mission_command == "consume-candidate"
        else None
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=selected_mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
        study_root=Path(profile.studies_root) / study_id,
        mission=None,
        candidate=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        enable_opl_live_probe=enable_opl_live_probe,
    )
    candidate_mission_id = _candidate_mission_id_for_readback(
        selected_mission_id=selected_mission_id,
        transaction_readback=transaction_readback,
        authority_consume_readback=authority_consume_readback,
    )
    if (
        transaction_readback["source"] == "placeholder_no_write"
        and candidate_mission_id != selected_mission_id
    ):
        transaction_readback = _paper_mission_transaction_readback(
            mission_id=candidate_mission_id,
            study_id=study_id,
            objective=selected_objective,
            paper_mission_command=paper_mission_command,
            study_root=Path(profile.studies_root) / study_id,
            mission=None,
            candidate=candidate_ref,
            authority_consume_readback=authority_consume_readback,
            enable_opl_live_probe=enable_opl_live_probe,
        )
    if authority_consume_readback is not None:
        transaction_readback["authority_consume_readback"] = authority_consume_readback
    mission_candidate = _paper_mission_run_candidate(
        mission_id=candidate_mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
        profile_ref=profile_ref,
        study_root=Path(profile.studies_root) / study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        paper_mission_transaction=transaction_readback["paper_mission_transaction"],
    )
    consume_output_manifest = (
        _write_paper_mission_consumption_ledger_outputs(
            output_root=Path(output_root),
            study_id=study_id,
            candidate_ref=str(candidate_ref),
            authority_consume_readback=authority_consume_readback,
            transaction_readback=transaction_readback,
            mission_candidate=mission_candidate,
            source=source,
        )
        if (
            paper_mission_command == "consume-candidate"
            and output_root is not None
            and candidate_ref is not None
            and authority_consume_readback is not None
        )
        else None
    )
    candidate_source_transaction = (
        _candidate_manifest_transaction(candidate_ref)
        if paper_mission_command == "consume-candidate"
        else {}
    )
    return {
        "surface_kind": "paper_mission_no_write_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": paper_mission_command,
        "action_intent": _action_intent(paper_mission_command),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "mission_id": candidate_mission_id,
        "objective": selected_objective,
        **({"candidate_ref": candidate_ref} if candidate_ref is not None else {}),
        **_transaction_readback_output_fields(transaction_readback),
        **(
            {"candidate_source_transaction": candidate_source_transaction}
            if candidate_source_transaction
            else {}
        ),
        "consume_candidate_status": _consume_candidate_status_for_transaction_readback(
            transaction_readback=transaction_readback,
            authority_consume_readback=authority_consume_readback,
        ),
        "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "paper_mission_run_candidate": mission_candidate,
        **(
            {"authority_consume_readback": authority_consume_readback}
            if authority_consume_readback is not None
            else {}
        ),
        **(
            {"consume_output_manifest": consume_output_manifest}
            if consume_output_manifest is not None
            else {}
        ),
        **_paper_mission_consume_non_advancing_fields(
            paper_mission_command=paper_mission_command,
            transaction_readback=transaction_readback,
            consume_output_manifest=consume_output_manifest,
            previous_consumption_readback=previous_consumption_readback,
        ),
        "contract_validation": _validate_with_contract_if_available(mission_candidate),
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": (
                "governed_consume_record"
                if consume_output_manifest is not None
                else "dry_run_no_write"
            ),
            "old_default_executor_dispatch_role": "diagnostic_or_migration_only",
        },
    }


def _paper_mission_consume_non_advancing_fields(
    *,
    paper_mission_command: str,
    transaction_readback: Mapping[str, Any],
    consume_output_manifest: Mapping[str, Any] | None,
    previous_consumption_readback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if paper_mission_command != "consume-candidate" or previous_consumption_readback is None:
        return {}
    handoff = _mapping(_mapping(consume_output_manifest).get("opl_route_handoff"))
    if not handoff:
        handoff = _mapping(transaction_readback.get("opl_route_handoff"))
    current_readback = _paper_mission_semantic_progress_readback(transaction_readback)
    previous_readback = _paper_mission_semantic_progress_readback(
        previous_consumption_readback
    )
    guard = _paper_mission_semantic_progress_guard(
        consume_readback=current_readback,
        handoff=handoff,
        previous_guard=_paper_mission_semantic_progress_guard(
            consume_readback=previous_readback,
            handoff=_mapping(previous_consumption_readback.get("opl_route_handoff")),
        ),
    )
    if guard.get("status") != "non_advancing_route_back":
        return {}
    return {
        "semantic_progress_guard": guard,
        "non_advancing_route_back": guard,
        "requires_mas_owned_executor_delta": True,
    }


def _paper_mission_semantic_progress_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(readback.get("paper_mission_transaction"))
    return {
        **dict(readback),
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(
            readback.get("stage_terminal_decision")
        )
        or _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(readback.get("opl_route_command"))
        or _mapping(transaction.get("opl_route_command")),
        "next_owner_or_human_decision": _mapping(
            readback.get("next_owner_or_human_decision")
        ),
        "authority_consume_readback": _mapping(
            readback.get("authority_consume_readback")
        ),
        "terminal_owner_gate": _mapping(readback.get("terminal_owner_gate")),
        "terminal_owner_gate_owner_answer_readback": _mapping(
            readback.get("terminal_owner_gate_owner_answer_readback")
        ),
    }


def _build_paper_mission_drive_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    run_id: str | None,
    submit_opl_runtime: bool | None,
    opl_bin: str | Path | None,
    source: str,
) -> dict[str, Any]:
    output_roots = _paper_mission_drive_output_roots(
        profile=profile,
        output_root=output_root,
        run_id=run_id,
    )
    root = output_roots["root"]
    package_root = output_roots["candidate_package"]
    ledger_root = output_roots["consumption_ledger"]
    route_back_budget_ledger_ref = _paper_mission_route_back_budget_ledger_path(
        profile=profile,
        output_root=root,
        ledger_root=ledger_root,
        study_id=study_id,
    )
    route_back_budget_ledger = _load_paper_mission_route_back_budget_ledger(
        ledger_ref=route_back_budget_ledger_ref,
        study_id=study_id,
    )
    package_readback = _build_materialized_candidate_package_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        output_root=package_root,
        source=f"{source}:drive:package-candidate",
    )
    candidate_ref = package_readback["output_manifest"]["package_manifest_ref"]
    consume_readback = build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="consume-candidate",
        candidate=candidate_ref,
        output_root=ledger_root,
        source=f"{source}:drive:consume-candidate",
        enable_opl_live_probe=True,
    )
    handoff = _mapping(
        _mapping(consume_readback.get("consume_output_manifest")).get(
            "opl_route_handoff"
        )
    )
    if not handoff:
        handoff_ref = _optional_text(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff_ref"
            )
        )
        handoff = _load_json_object(Path(handoff_ref)) if handoff_ref else {}
    runtime_submit_requested = submit_opl_runtime is not False
    opl_runtime_submission = _opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=runtime_submit_requested,
        opl_bin=opl_bin,
    )
    consume_readback = _refresh_consume_readback_after_opl_submission(
        consume_readback=consume_readback,
        opl_runtime_submission=opl_runtime_submission,
    )
    handoff = _mapping(
        _mapping(consume_readback.get("consume_output_manifest")).get(
            "opl_route_handoff"
        )
    ) or handoff
    initial_progress_guard = _paper_mission_semantic_progress_guard(
        consume_readback=consume_readback,
        handoff=handoff,
        route_back_budget_ledger=route_back_budget_ledger,
    )
    route_back_budget_ledger = _record_paper_mission_route_back_budget_ledger(
        ledger=route_back_budget_ledger,
        ledger_ref=route_back_budget_ledger_ref,
        progress_guard=initial_progress_guard,
        consume_readback=consume_readback,
        handoff=handoff,
        trigger="drive-initial",
        source=source,
    )
    followthrough = _paper_mission_drive_followthrough(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        root=root,
        package_root=package_root,
        ledger_root=ledger_root,
        source=source,
        opl_bin=opl_bin,
        submit_opl_runtime=runtime_submit_requested,
        initial_package_readback=package_readback,
        initial_consume_readback=consume_readback,
        initial_handoff=handoff,
        initial_opl_runtime_submission=opl_runtime_submission,
        initial_progress_guard=initial_progress_guard,
        route_back_budget_ledger=route_back_budget_ledger,
        route_back_budget_ledger_ref=route_back_budget_ledger_ref,
    )
    if followthrough["rounds"]:
        final_round = _mapping(followthrough["rounds"][-1])
        package_readback = _mapping(final_round.get("candidate_package_readback"))
        consume_readback = _mapping(final_round.get("consume_readback"))
        handoff = _mapping(final_round.get("opl_route_handoff"))
        opl_runtime_submission = _mapping(final_round.get("opl_runtime_submission"))
    mas_executor_delta = _paper_mission_mas_owned_executor_delta_checkpoint(
        package_readback=package_readback,
        consume_readback=consume_readback,
        handoff=handoff,
        progress_guard=followthrough["semantic_progress_guard"],
    )
    drive_result = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
        mas_owned_executor_delta=mas_executor_delta,
    )
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "dry_run": False,
        "profile": package_readback["profile"],
        "requested_study_id": package_readback["requested_study_id"],
        "study_id": package_readback["study_id"],
        "study_root": package_readback["study_root"],
        "study_root_exists": package_readback["study_root_exists"],
        "mission_id": consume_readback["mission_id"],
        "objective": consume_readback["objective"],
        "output_root": str(root),
        "candidate_package_readback": package_readback,
        "authority_consume_readback": consume_readback.get(
            "authority_consume_readback"
        ),
        "consume_readback": consume_readback,
        "stage_terminal_decision": consume_readback["stage_terminal_decision"],
        "opl_route_command": consume_readback["opl_route_command"],
        "opl_runtime_carrier": consume_readback["opl_runtime_carrier"],
        "opl_runtime_carrier_readback": consume_readback[
            "opl_runtime_carrier_readback"
        ],
        "opl_runtime_readback_status": consume_readback[
            "opl_runtime_readback_status"
        ],
        "terminal_owner_gate": consume_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": consume_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": consume_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "opl_route_handoff": handoff or None,
        "opl_runtime_submission": opl_runtime_submission,
        "followthrough": followthrough,
        "semantic_progress_guard": followthrough["semantic_progress_guard"],
        "non_advancing_route_back": followthrough["non_advancing_route_back"],
        "route_back_budget_ledger": followthrough["route_back_budget_ledger"],
        "route_back_budget_ledger_ref": followthrough["route_back_budget_ledger_ref"],
        "mas_owned_executor_delta": mas_executor_delta,
        "mas_owned_executor_stage": _mapping(mas_executor_delta).get(
            "mas_owned_executor_stage"
        ),
        "requires_mas_owned_executor_delta": followthrough[
            "requires_mas_owned_executor_delta"
        ],
        "transaction_state": consume_readback["transaction_state"],
        "consume_candidate_status": consume_readback["consume_candidate_status"],
        "next_owner_or_human_decision": consume_readback[
            "next_owner_or_human_decision"
        ],
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": runtime_submit_requested
            and opl_runtime_submission.get("status") == "submitted",
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(
                package_root
            ),
            "writes_yang_ops_consumption_ledger": _is_yang_ops_consumption_ledger_root(
                ledger_root
            ),
            "writes_paper_body": False,
            "writes_candidate_workspace": True,
            "dry_run_only": False,
            "forbidden_authority_writes": list(CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES),
        },
        "output_manifest": {
            "mode": "paper_mission_drive",
            "output_root": str(root),
            "candidate_package": package_readback["output_manifest"],
            "consumption_ledger": consume_readback.get("consume_output_manifest"),
            "route_back_budget_ledger_ref": followthrough[
                "route_back_budget_ledger_ref"
            ],
            "followthrough_round_count": followthrough["round_count"],
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_runtime": runtime_submit_requested
            and opl_runtime_submission.get("status") == "submitted",
        },
        "forbidden_authority_writes": list(CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "drive_result": drive_result,
    }


def _paper_mission_drive_followthrough(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    root: Path,
    package_root: Path,
    ledger_root: Path,
    source: str,
    opl_bin: str | Path | None,
    submit_opl_runtime: bool,
    initial_package_readback: Mapping[str, Any],
    initial_consume_readback: Mapping[str, Any],
    initial_handoff: Mapping[str, Any],
    initial_opl_runtime_submission: Mapping[str, Any],
    initial_progress_guard: Mapping[str, Any],
    route_back_budget_ledger: Mapping[str, Any],
    route_back_budget_ledger_ref: Path,
) -> dict[str, Any]:
    rounds: list[dict[str, Any]] = []
    current_package_readback = dict(initial_package_readback)
    current_consume_readback = dict(initial_consume_readback)
    current_handoff = dict(initial_handoff)
    current_submission = dict(initial_opl_runtime_submission)
    current_progress_guard = dict(initial_progress_guard)
    current_route_back_budget_ledger = dict(route_back_budget_ledger)
    non_advancing_route_back: dict[str, Any] | None = None
    for index in range(DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT):
        if _paper_mission_route_back_budget_exhausted(current_progress_guard):
            non_advancing_route_back = current_progress_guard
            break
        trigger = _paper_mission_followthrough_trigger(
            consume_readback=current_consume_readback,
            opl_runtime_submission=current_submission,
        )
        if trigger is None:
            break
        round_id = f"followthrough-{index + 1:02d}"
        package_round_root = package_root / round_id
        ledger_round_root = ledger_root / round_id
        package_readback = _build_materialized_candidate_package_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=package_round_root,
            source=f"{source}:drive:{round_id}:package-candidate",
            source_readback_override=current_consume_readback,
        )
        candidate_ref = package_readback["output_manifest"]["package_manifest_ref"]
        consume_readback = build_paper_mission_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="consume-candidate",
            candidate=candidate_ref,
            output_root=ledger_round_root,
            source=f"{source}:drive:{round_id}:consume-candidate",
            enable_opl_live_probe=True,
            opl_bin=opl_bin,
        )
        handoff = _mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        )
        if not handoff:
            handoff_ref = _optional_text(
                _mapping(consume_readback.get("consume_output_manifest")).get(
                    "opl_route_handoff_ref"
                )
            )
            handoff = _load_json_object(Path(handoff_ref)) if handoff_ref else {}
        submission = _opl_runtime_submission_readback(
            handoff=handoff,
            submit_opl_runtime=submit_opl_runtime,
            opl_bin=opl_bin,
        )
        consume_readback = _refresh_consume_readback_after_opl_submission(
            consume_readback=consume_readback,
            opl_runtime_submission=submission,
        )
        handoff = _mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ) or handoff
        next_progress_guard = _paper_mission_semantic_progress_guard(
            consume_readback=consume_readback,
            handoff=handoff,
            previous_guard=current_progress_guard,
            route_back_budget_ledger=current_route_back_budget_ledger,
        )
        current_route_back_budget_ledger = _record_paper_mission_route_back_budget_ledger(
            ledger=current_route_back_budget_ledger,
            ledger_ref=route_back_budget_ledger_ref,
            progress_guard=next_progress_guard,
            consume_readback=consume_readback,
            handoff=handoff,
            trigger=round_id,
            source=source,
        )
        round_readback = {
            "round": index + 1,
            "round_id": round_id,
            "trigger": trigger,
            "output_root": str(root / round_id),
            "candidate_package_readback": package_readback,
            "consume_readback": consume_readback,
            "opl_route_handoff": handoff or None,
            "opl_runtime_submission": submission,
            "drive_result": _paper_mission_drive_result(
                consume_readback=consume_readback,
                handoff=handoff,
                opl_runtime_submission=submission,
            ),
            "semantic_progress_guard": next_progress_guard,
        }
        rounds.append(round_readback)
        current_package_readback = package_readback
        current_consume_readback = consume_readback
        current_handoff = handoff
        current_submission = submission
        current_progress_guard = next_progress_guard
        if _paper_mission_route_back_budget_exhausted(next_progress_guard):
            non_advancing_route_back = next_progress_guard
            break
    mas_executor_delta = _paper_mission_mas_owned_executor_delta_checkpoint(
        package_readback=current_package_readback,
        consume_readback=current_consume_readback,
        handoff=current_handoff,
        progress_guard=current_progress_guard,
    )
    stop_reason = (
        "mas_owned_executor_delta_ready"
        if mas_executor_delta is not None and not non_advancing_route_back
        else _paper_mission_followthrough_stop_reason(
            consume_readback=current_consume_readback,
            opl_runtime_submission=current_submission,
            exhausted=len(rounds) >= DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT
            and _paper_mission_followthrough_trigger(
                consume_readback=current_consume_readback,
                opl_runtime_submission=current_submission,
            )
            is not None,
            non_advancing_route_back=non_advancing_route_back is not None,
        )
    )
    final_drive_result = _paper_mission_drive_result(
        consume_readback=current_consume_readback,
        handoff=current_handoff,
        opl_runtime_submission=current_submission,
        mas_owned_executor_delta=mas_executor_delta,
    )
    return {
        "surface_kind": "paper_mission_drive_followthrough_readback",
        "schema_version": 1,
        "attempted": bool(rounds),
        "round_count": len(rounds),
        "max_rounds": DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT,
        "rounds": rounds,
        "stop_reason": stop_reason,
        "semantic_progress_guard": current_progress_guard,
        "non_advancing_route_back": non_advancing_route_back,
        "route_back_budget_ledger": current_route_back_budget_ledger,
        "route_back_budget_ledger_ref": str(route_back_budget_ledger_ref),
        "mas_owned_executor_delta": mas_executor_delta,
        "mas_owned_executor_stage": _mapping(mas_executor_delta).get(
            "mas_owned_executor_stage"
        ),
        "requires_mas_owned_executor_delta": non_advancing_route_back is not None,
        "final_drive_result": final_drive_result,
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": bool(
                [
                    item
                    for item in (
                        [initial_opl_runtime_submission]
                        + [round_item["opl_runtime_submission"] for round_item in rounds]
                    )
                    if _optional_text(_mapping(item).get("status"))
                    in {"submitted", "idempotent_noop"}
                ]
            ),
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }


def _paper_mission_mas_owned_executor_delta_checkpoint(
    *,
    package_readback: Mapping[str, Any],
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    progress_guard: Mapping[str, Any],
) -> dict[str, Any] | None:
    output_manifest = _mapping(package_readback.get("output_manifest"))
    owner_decision_packet_ref = _optional_text(
        output_manifest.get("owner_decision_packet_ref")
    )
    paper_facing_delta_ref = _optional_text(
        output_manifest.get("paper_facing_candidate_delta_ref")
    )
    if owner_decision_packet_ref is None and paper_facing_delta_ref is None:
        return None
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    next_decision = _mapping(consume_readback.get("next_owner_or_human_decision"))
    next_owner = _first_text(
        decision.get("next_owner"),
        handoff.get("next_owner"),
        next_decision.get("next_owner"),
    )
    if next_owner != "mission_executor":
        return None
    runtime_status = _optional_text(consume_readback.get("opl_runtime_readback_status"))
    if runtime_status not in {
        "waiting_for_opl_runtime_live_readback",
        "opl_runtime_readback_missing",
        None,
    }:
        return None
    signature = _optional_text(progress_guard.get("signature")) or _stable_sha256(
        _mapping(progress_guard.get("signature_payload"))
    )
    signature_payload = _mapping(progress_guard.get("signature_payload")) or {
        "study_id": _optional_text(consume_readback.get("study_id")),
        "mission_id": _optional_text(consume_readback.get("mission_id")),
        "paper_mission_transaction_ref": _optional_text(
            handoff.get("paper_mission_transaction_ref")
        ),
        "route_command": _first_text(
            handoff.get("route_command_kind"),
            _mapping(consume_readback.get("opl_route_command")).get("command_kind"),
        ),
        "route_target": _first_text(
            handoff.get("route_target"),
            _mapping(consume_readback.get("opl_route_command")).get("target"),
        ),
    }
    produced_outputs = _compact_non_null_mapping(
        {
            "owner_decision_packet_ref": owner_decision_packet_ref,
            "paper_facing_delta_ref": paper_facing_delta_ref,
            "owner_consumption_request_ref": _optional_text(
                output_manifest.get("owner_consumption_request_ref")
            ),
            "owner_blocker_packet_ref": _optional_text(
                output_manifest.get("owner_blocker_packet_ref")
            ),
            "submission_milestone_checklist_ref": _optional_text(
                output_manifest.get("submission_milestone_checklist_ref")
            ),
            "package_manifest_ref": _optional_text(
                output_manifest.get("package_manifest_ref")
            ),
            "consume_readback_ref": _optional_text(
                _mapping(consume_readback.get("consume_output_manifest")).get(
                    "consume_readback_ref"
                )
            ),
        }
    )
    return {
        "surface_kind": "paper_mission_mas_owned_executor_delta_checkpoint",
        "schema_version": 1,
        "status": "mas_owned_executor_delta_ready",
        "owner": "MedAutoScience",
        "executor": "Codex CLI",
        "trigger": "opl_runtime_live_readback_missing_after_candidate_materialization",
        "next_owner": "mission_executor",
        "semantic_progress_signature": signature,
        "semantic_progress_signature_payload": signature_payload,
        "mas_owned_executor_stage": _paper_mission_mas_owned_executor_stage_packet(
            signature=signature,
            signature_payload=signature_payload,
        ),
        "produced_outputs": produced_outputs,
        "stop_same_semantic_redrive": True,
        "forbidden_next_action": "synonymous_route_back_redrive",
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_paper_progress": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
    }


def _paper_mission_followthrough_trigger(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
) -> str | None:
    drive_result = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=_mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ),
        opl_runtime_submission=opl_runtime_submission,
    )
    if drive_result.get("provider_attempt_running_observed") is True:
        return None
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    next_decision = _mapping(consume_readback.get("next_owner_or_human_decision"))
    terminal_gate = _mapping(consume_readback.get("terminal_owner_gate"))
    owner_answer = _mapping(
        consume_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    owner_answer_decision = _mapping(owner_answer.get("stage_terminal_decision"))
    terminal_route_back_observed = drive_result.get("terminal_closeout_observed") is True
    owner_answer_route_back_observed = (
        _optional_text(owner_answer.get("status")) == "route_back"
        and _optional_text(owner_answer.get("owner_answer_shape"))
        == "route_back_evidence_ref"
        and _optional_text(owner_answer_decision.get("decision_kind")) == "route_back"
    )
    if not terminal_route_back_observed and not owner_answer_route_back_observed:
        return None
    if _optional_text(terminal_gate.get("gate_kind")) == "human_gate":
        return None
    if _optional_text(next_decision.get("human_decision_required")) == "true":
        return None
    decision_kind = _first_text(
        owner_answer_decision.get("decision_kind"),
        decision.get("decision_kind"),
    )
    if decision_kind != "route_back":
        return None
    if _first_text(
        owner_answer_decision.get("next_owner"),
        decision.get("next_owner"),
        next_decision.get("next_owner"),
    ) != "mission_executor":
        return None
    return (
        "terminal_owner_answer_route_back_followthrough"
        if owner_answer_route_back_observed
        else "terminal_route_back_followthrough"
    )


def _paper_mission_followthrough_stop_reason(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
    exhausted: bool,
    non_advancing_route_back: bool = False,
) -> str:
    if non_advancing_route_back:
        return "non_advancing_route_back"
    if exhausted:
        return "followthrough_round_limit_reached"
    trigger = _paper_mission_followthrough_trigger(
        consume_readback=consume_readback,
        opl_runtime_submission=opl_runtime_submission,
    )
    if trigger is not None:
        return "followthrough_available"
    drive_status = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=_mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ),
        opl_runtime_submission=opl_runtime_submission,
    ).get("status")
    return _optional_text(drive_status) or "no_followthrough_needed"


def _paper_mission_drive_output_roots(
    *,
    profile: Any,
    output_root: str | Path | None,
    run_id: str | None,
) -> dict[str, Path]:
    if output_root is not None:
        root = Path(output_root).expanduser().resolve()
        if _is_under_yang_workspace(root):
            selected_run_id = _optional_text(run_id) or root.name or "paper_mission_drive"
            workspace_root = _yang_workspace_root_for_path(root)
            return {
                "root": root,
                "candidate_package": (
                    workspace_root / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / selected_run_id
                ),
                "consumption_ledger": (
                    workspace_root / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH / selected_run_id
                ),
            }
        selected_run_id = _optional_text(run_id) or "paper_mission_drive"
        return {
            "root": root,
            "candidate_package": root / "candidate_package",
            "consumption_ledger": root / "consumption_ledger",
        }
    else:
        selected_run_id = _optional_text(run_id) or "paper_mission_drive"
        workspace_root = Path(profile.workspace_root).expanduser().resolve()
        return {
            "root": workspace_root / "ops" / "medautoscience",
            "candidate_package": (
                workspace_root / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / selected_run_id
            ),
            "consumption_ledger": (
                workspace_root / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH / selected_run_id
            ),
        }


def _yang_workspace_root_for_path(path: Path) -> Path:
    normalized = path.expanduser().resolve()
    relative = normalized.relative_to(YANG_WORKSPACE_ROOT)
    return YANG_WORKSPACE_ROOT / relative.parts[0]


def _opl_runtime_submission_readback(
    *,
    handoff: Mapping[str, Any],
    submit_opl_runtime: bool,
    opl_bin: str | Path | None,
) -> dict[str, Any]:
    if not submit_opl_runtime:
        return {
            "status": "not_requested",
            "writes_runtime": False,
            "required_next_action": (
                "Submit opl_route_handoff to OPL DomainProgressTransitionRuntime "
                "through the legal OPL intake surface."
            ),
        }
    if _optional_text(handoff.get("handoff_status")) != "ready_for_opl_route_command":
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_route_handoff_not_ready",
        }
    runtime_request = _opl_stage_route_runtime_request_from_handoff(handoff)
    if runtime_request is None:
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_stage_route_runtime_request_not_materialized",
        }
    selected_opl_bin = _resolve_opl_bin(opl_bin)
    if selected_opl_bin is None:
        return {
            "status": "not_configured",
            "writes_runtime": False,
            "reason": "opl_bin_not_found",
            "expected_command": "opl family-runtime enqueue --domain medautoscience --task-kind paper_mission/stage-route",
        }
    command = [
        selected_opl_bin,
        "family-runtime",
        "enqueue",
        "--domain",
        "medautoscience",
        "--task-kind",
        "paper_mission/stage-route",
        "--payload",
        json.dumps(runtime_request["payload"], ensure_ascii=False, separators=(",", ":")),
        "--dedupe-key",
        runtime_request["dedupe_key"],
        "--priority",
        "100",
        "--source",
        "mas-paper-mission-drive",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except OSError as exc:
        return {
            "status": "failed",
            "writes_runtime": False,
            "reason": "opl_enqueue_exec_failed",
            "error": str(exc),
            "opl_bin": selected_opl_bin,
            "command_preview": _opl_command_preview(command),
            "runtime_request_input": runtime_request,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "writes_runtime": False,
            "reason": "opl_enqueue_timeout",
            "error": str(exc),
            "opl_bin": selected_opl_bin,
            "command_preview": _opl_command_preview(command),
            "runtime_request_input": runtime_request,
        }
    parsed = _parse_json_object(completed.stdout)
    enqueue = _mapping(parsed.get("family_runtime_enqueue"))
    accepted = enqueue.get("accepted") is True
    idempotent_noop = enqueue.get("idempotent_noop") is True
    tick_readback = (
        _opl_runtime_tick_readback(
            opl_bin=selected_opl_bin,
            runtime_request=runtime_request,
        )
        if accepted or idempotent_noop
        else {}
    )
    return {
        "status": (
            "submitted"
            if accepted
            else "idempotent_noop"
            if idempotent_noop
            else "failed"
        ),
        "writes_runtime": bool(accepted or idempotent_noop),
        "writes_runtime_owner": "one-person-lab",
        "writes_mas_authority": False,
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "opl_bin": selected_opl_bin,
        "command_preview": _opl_command_preview(command),
        "exit_code": completed.returncode,
        "runtime_request_input": runtime_request,
        "enqueue_readback": enqueue or parsed,
        **({"tick_readback": tick_readback} if tick_readback else {}),
        "stage_route_followthrough_attempted": bool(tick_readback),
        **(
            {"stderr": completed.stderr.strip()}
            if completed.stderr.strip()
            else {}
        ),
    }


def _opl_runtime_tick_readback(
    *,
    opl_bin: str,
    runtime_request: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _mapping(runtime_request.get("payload"))
    transaction_ref = _optional_text(payload.get("paper_mission_transaction_ref"))
    study_id = _optional_text(payload.get("study_id"))
    command = [
        opl_bin,
        "family-runtime",
        "tick",
        "--source",
        "mas-paper-mission-drive-followthrough",
        "--hydrate",
        "--limit",
        "1",
        "--domain",
        "medautoscience",
        "--task-kind",
        "paper_mission/stage-route",
    ]
    if study_id is not None:
        command.extend(["--study", study_id])
    if transaction_ref is not None:
        command.extend(["--payload-match", f"paper_mission_transaction_ref={transaction_ref}"])
    try:
        # A hydrated OPL tick may launch a long-running provider activity; drive
        # only needs a bounded followthrough readback after enqueue succeeds.
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS,
        )
    except OSError as exc:
        return {
            "status": "failed",
            "reason": "opl_tick_exec_failed",
            "error": str(exc),
            "command_preview": _opl_command_preview(command),
            "can_claim_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "reason": "opl_tick_followthrough_timeout",
            "error": str(exc),
            "command_preview": _opl_command_preview(command),
            "followthrough_observation_window_seconds": (
                OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS
            ),
            "can_claim_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
        }
    parsed = _parse_json_object(completed.stdout)
    tick = _mapping(parsed.get("family_runtime_tick"))
    dispatches = _mapping_list(tick.get("dispatches"))
    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "command_preview": _opl_command_preview(command),
        "tick_readback": tick or parsed,
        "selected_count": tick.get("selected_count"),
        "dispatch_count": len(dispatches),
        "dispatch_statuses": [
            _optional_text(dispatch.get("status")) for dispatch in dispatches
        ],
        "can_claim_stage_run_created": any(
            _dispatch_started_stage_route_attempt(dispatch) for dispatch in dispatches
        ),
        "can_claim_provider_running": any(
            _dispatch_reports_provider_running(dispatch) for dispatch in dispatches
        ),
        "can_claim_paper_progress": False,
        **(
            {"stderr": completed.stderr.strip()}
            if completed.stderr.strip()
            else {}
        ),
    }


def _dispatch_started_stage_route_attempt(dispatch: Mapping[str, Any]) -> bool:
    if _optional_text(dispatch.get("status")) == "running":
        return True
    stage_run = _mapping(dispatch.get("stage_run_request"))
    return (
        stage_run.get("stage_run_created") is True
        or stage_run.get("provider_attempt_requested") is True
    )


def _dispatch_reports_provider_running(dispatch: Mapping[str, Any]) -> bool:
    if _optional_text(dispatch.get("status")) == "running":
        return True
    stage_run = _mapping(dispatch.get("stage_run_request"))
    return stage_run.get("provider_running") is True


def _refresh_consume_readback_after_opl_submission(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
) -> dict[str, Any]:
    if _optional_text(opl_runtime_submission.get("status")) not in {
        "submitted",
        "idempotent_noop",
    }:
        return dict(consume_readback)
    submission_source_transaction = _first_mapping(
        _mapping(consume_readback.get("stage_route_submission_source_transaction")),
        _mapping(consume_readback.get("candidate_source_transaction")),
        _mapping(consume_readback.get("paper_mission_transaction")),
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=_optional_text(consume_readback.get("mission_id"))
        or "paper-mission::unknown",
        study_id=_optional_text(consume_readback.get("study_id")) or "unknown_study",
        objective=_optional_text(consume_readback.get("objective"))
        or "PaperMission runtime followthrough readback",
        paper_mission_command="consume-candidate",
        study_root=Path(_optional_text(consume_readback.get("study_root")) or "."),
        mission=None,
        candidate=_optional_text(consume_readback.get("candidate_ref")),
        authority_consume_readback=_mapping(
            consume_readback.get("authority_consume_readback")
        ),
        transaction_override=_mapping(consume_readback.get("paper_mission_transaction")),
        transaction_source_override="paper_mission_consumption_ledger",
        enable_opl_live_probe=True,
        opl_bin=_optional_text(opl_runtime_submission.get("opl_bin")),
    )
    refreshed = dict(consume_readback)
    refreshed.update(_transaction_readback_output_fields(transaction_readback))
    refreshed["stage_route_submission_source_transaction"] = submission_source_transaction
    refreshed["consume_candidate_status"] = (
        _consume_candidate_status_for_transaction_readback(
            transaction_readback=transaction_readback,
            authority_consume_readback=_mapping(
                consume_readback.get("authority_consume_readback")
            ),
        )
    )
    return refreshed


def _resolve_opl_bin(opl_bin: str | Path | None) -> str | None:
    if opl_bin is not None:
        selected = Path(opl_bin).expanduser()
        if selected.exists():
            return str(selected.resolve())
        resolved = shutil.which(str(opl_bin))
        return resolved
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        selected = Path(configured).expanduser()
        if selected.exists():
            return str(selected.resolve())
        return shutil.which(configured)
    path_candidate = shutil.which(PATH_OPL_BIN)
    if path_candidate is not None:
        return path_candidate
    for candidate in (PACKAGED_OPL_BIN, DEV_OPL_BIN):
        if candidate.exists():
            return str(candidate.resolve())
    return None


def _opl_command_preview(command: list[str]) -> list[str]:
    preview = list(command)
    if "--payload" in preview:
        payload_index = preview.index("--payload") + 1
        if payload_index < len(preview):
            preview[payload_index] = "<json>"
    return preview


def _opl_stage_route_runtime_request_from_handoff(
    handoff: Mapping[str, Any],
) -> dict[str, Any] | None:
    study_id = _optional_text(handoff.get("study_id"))
    transaction_ref = _optional_text(handoff.get("paper_mission_transaction_ref"))
    route = _mapping(handoff.get("opl_route_command"))
    command_kind = _first_text(handoff.get("route_command_kind"), route.get("command_kind"))
    if not study_id or not transaction_ref or command_kind not in {
        "start_next_stage",
        "resume_stage",
        "route_back",
    }:
        return None
    workspace_root = _handoff_workspace_root(handoff)
    if workspace_root is None:
        return None
    dedupe_key = ":".join(
        [
            "paper-mission-route",
            study_id,
            transaction_ref,
            command_kind,
        ]
    )
    progress_guard = _paper_mission_route_request_progress_guard(handoff=handoff)
    payload = {
        "surface_kind": "opl_mas_paper_mission_route_runtime_request",
        "schema_version": 1,
        "runtime_request_status": "queued_request",
        "runtime_request_kind": "mas_paper_mission_stage_route",
        "study_id": study_id,
        "mission_id": _optional_text(handoff.get("mission_id")),
        "candidate_ref": _optional_text(handoff.get("candidate_ref")),
        "paper_mission_transaction_ref": transaction_ref,
        "opl_route_command_ref": _optional_text(handoff.get("opl_route_command_ref")),
        "command_kind": command_kind,
        "route_target": _first_text(handoff.get("route_target"), route.get("target")),
        "workspace_root": workspace_root,
        "domain_workspace_root": workspace_root,
        "route_command_materialized": handoff.get("transaction_materialized") is True,
        "opl_route_command": route,
        "opl_route_handoff_record": dict(handoff),
        "semantic_progress_guard": progress_guard,
        "mas_owned_executor_stage": progress_guard.get("mas_owned_executor_stage"),
        "stage_run_request": {
            "request_status": "requested",
            "requested_by": "mas_paper_mission_route_handoff",
            "domain_truth_owner": "med-autoscience",
            "runtime_owner": "one-person-lab",
            "command_kind": command_kind,
            "route_target": _first_text(handoff.get("route_target"), route.get("target")),
            "stage_run_created": False,
            "provider_attempt_requested": False,
        },
        "authority_boundary": {
            "domain_truth_owner": "med-autoscience",
            "runtime_owner": "one-person-lab",
            "runtime_request_scope": "opl_queue_and_stage_route_request_only",
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_paper_body": False,
            "writes_runtime_queue": False,
            "writes_opl_queue": True,
            "writes_opl_outbox": True,
            "writes_opl_event": True,
            "writes_opl_stage_run": False,
            "writes_provider_attempt": False,
            "can_claim_opl_runtime_enqueued": False,
            "can_claim_opl_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }
    return {
        "domainId": "medautoscience",
        "taskKind": "paper_mission/stage-route",
        "dedupe_key": dedupe_key,
        "priority": 100,
        "source": "mas-paper-mission-drive",
        "payload": payload,
    }


def _handoff_workspace_root(handoff: Mapping[str, Any]) -> str | None:
    explicit = _first_text(
        handoff.get("domain_workspace_root"),
        handoff.get("workspace_root"),
        handoff.get("repo_root"),
    )
    if explicit is not None:
        return str(Path(explicit).expanduser().resolve())
    for key in ("candidate_ref", "source_ref"):
        ref = _optional_text(handoff.get(key))
        if ref is None:
            continue
        resolved = _workspace_root_from_ops_ref(ref)
        if resolved is not None:
            return str(resolved)
    return None


def _workspace_root_from_ops_ref(ref: str) -> Path | None:
    path = Path(ref).expanduser()
    if not path.is_absolute():
        return None
    parts = path.parts
    for index in range(0, len(parts) - 1):
        if parts[index : index + 2] == ("ops", "medautoscience"):
            if index == 0:
                return None
            return Path(*parts[:index]).resolve()
    return None


def _paper_mission_drive_result(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
    mas_owned_executor_delta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    handoff_ready = _optional_text(handoff.get("handoff_status")) == (
        "ready_for_opl_route_command"
    )
    route = _mapping(consume_readback.get("opl_route_command"))
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    carrier_readback = _mapping(consume_readback.get("opl_runtime_carrier_readback"))
    runtime_status = _optional_text(consume_readback.get("opl_runtime_readback_status"))
    submission_status = _optional_text(opl_runtime_submission.get("status"))
    status = _paper_mission_drive_result_status(
        handoff_ready=handoff_ready,
        submission_status=submission_status,
        runtime_status=runtime_status,
        carrier_readback=carrier_readback,
    )
    if (
        _optional_text(_mapping(mas_owned_executor_delta).get("status"))
        == "mas_owned_executor_delta_ready"
        and status == "opl_runtime_submission_pending"
    ):
        status = "mas_owned_executor_delta_ready"
    return {
        "status": status,
        "stage_terminal_decision": decision.get("decision_kind"),
        "route_command": route.get("command_kind"),
        "next_owner": _first_text(
            decision.get("next_owner"),
            handoff.get("next_owner"),
            _mapping(consume_readback.get("next_owner_or_human_decision")).get(
                "next_owner"
            ),
        ),
        "can_submit_to_opl_runtime": bool(handoff.get("can_submit_to_opl_runtime")),
        "opl_runtime_submission_status": submission_status,
        "opl_runtime_readback_status": runtime_status,
        "provider_attempt_running_observed": (
            runtime_status == "opl_runtime_attempt_running_observed"
        ),
        "terminal_closeout_observed": (
            runtime_status == "opl_runtime_terminal_readback_observed"
        ),
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }


def _paper_mission_semantic_progress_guard(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    previous_guard: Mapping[str, Any] | None = None,
    route_back_budget_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    signature_payload = _paper_mission_semantic_progress_signature_payload(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    signature = _stable_sha256(signature_payload)
    previous_signature = _optional_text(_mapping(previous_guard).get("signature"))
    semantic_progress_observed = (
        previous_signature is None or previous_signature != signature
    )
    has_required_delta = _paper_mission_required_executor_delta_present(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    budget_status = _paper_mission_route_back_budget_status(
        signature=signature,
        signature_payload=signature_payload,
        ledger=route_back_budget_ledger,
        has_required_delta=has_required_delta,
    )
    status = (
        "semantic_progress_observed"
        if (semantic_progress_observed and not budget_status["budget_exhausted"])
        or has_required_delta
        else "non_advancing_route_back"
    )
    result = {
        "surface_kind": "paper_mission_semantic_progress_guard",
        "schema_version": 1,
        "status": status,
        "signature": signature,
        "previous_signature": previous_signature,
        "signature_payload": signature_payload,
        "progress_refs": _paper_mission_progress_refs_for_guard(
            consume_readback=consume_readback,
            handoff=handoff,
        ),
        "semantic_progress_observed": semantic_progress_observed,
        "required_executor_delta_present": has_required_delta,
        "route_back_budget": budget_status,
        "required_executor_outputs": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
        "can_claim_paper_progress": False,
        "can_claim_submission_ready": False,
        "can_claim_runtime_ready": False,
    }
    if status == "non_advancing_route_back":
        executor_stage = _paper_mission_mas_owned_executor_stage_packet(
            signature=signature,
            signature_payload=signature_payload,
        )
        result.update(
            {
                "reason": (
                    "MAS observed a route-back/domain-gate handoff with the same "
                    "semantic progress signature and no new owner decision, "
                    "human gate, paper-facing delta, typed blocker, owner receipt, "
                    "or route-back evidence ref."
                ),
                "requires_mas_owned_executor_delta": True,
                "required_next_executor_stage": executor_stage["stage_type"],
                "mas_owned_executor_stage": executor_stage,
                "next_legal_actions": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
                "stop_same_semantic_redrive": True,
                "owner_surface": "med-autoscience PaperMissionRun / MAS authority",
            }
        )
    return result


def _paper_mission_mas_owned_executor_stage_packet(
    *,
    signature: str,
    signature_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_mas_owned_executor_stage_packet",
        "schema_version": 1,
        "stage_type": "paper_mission_semantic_progress_executor",
        "owner": "MedAutoScience",
        "executor": "Codex CLI",
        "trigger": "non_advancing_route_back",
        "semantic_progress_signature": signature,
        "semantic_progress_signature_payload": signature_payload,
        "required_outputs": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
        "next_legal_action": "materialize_mas_owned_executor_delta_before_redrive",
        "forbidden_next_action": "synonymous_route_back_redrive",
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_paper_progress": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
    }


def _paper_mission_route_back_budget_ledger_path(
    *,
    profile: Any,
    output_root: Path,
    ledger_root: Path,
    study_id: str,
) -> Path:
    workspace_root = (
        _yang_workspace_root_for_path(output_root)
        if _is_under_yang_workspace(output_root)
        else None
    )
    profile_workspace_root = Path(profile.workspace_root).expanduser().resolve()
    resolved_ledger_root = ledger_root.expanduser().resolve()
    if workspace_root is not None:
        root = workspace_root / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH
    elif _is_relative_to(resolved_ledger_root, profile_workspace_root):
        root = profile_workspace_root / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH
    else:
        root = resolved_ledger_root.parent
    return (
        root
        / "_route_back_budget"
        / study_id
        / PAPER_MISSION_ROUTE_BACK_BUDGET_LEDGER_FILENAME
    )


def _load_paper_mission_route_back_budget_ledger(
    *,
    ledger_ref: Path,
    study_id: str,
) -> dict[str, Any]:
    if not ledger_ref.exists():
        return _empty_paper_mission_route_back_budget_ledger(study_id=study_id)
    payload = _load_json_object(ledger_ref)
    if (
        payload.get("surface_kind")
        != "paper_mission_route_back_budget_ledger"
        or _optional_text(payload.get("study_id")) != study_id
    ):
        return _empty_paper_mission_route_back_budget_ledger(study_id=study_id)
    signatures = _mapping(payload.get("signatures"))
    return {
        "surface_kind": "paper_mission_route_back_budget_ledger",
        "schema_version": 1,
        "study_id": study_id,
        "budget_kind": "synonymous_route_back_cross_run_budget",
        "max_opl_redrives": PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS,
        "signatures": signatures,
        "authority_boundary": _paper_mission_route_back_budget_authority_boundary(),
    }


def _empty_paper_mission_route_back_budget_ledger(*, study_id: str) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_route_back_budget_ledger",
        "schema_version": 1,
        "study_id": study_id,
        "budget_kind": "synonymous_route_back_cross_run_budget",
        "max_opl_redrives": PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS,
        "signatures": {},
        "authority_boundary": _paper_mission_route_back_budget_authority_boundary(),
    }


def _paper_mission_route_back_budget_authority_boundary() -> dict[str, Any]:
    return {
        "ledger_is_authority": False,
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "writes_owner_receipt": False,
        "writes_typed_blocker": False,
        "writes_human_gate": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
    }


def _paper_mission_route_back_budget_status(
    *,
    signature: str,
    signature_payload: Mapping[str, Any],
    ledger: Mapping[str, Any] | None,
    has_required_delta: bool,
) -> dict[str, Any]:
    eligible_route_back = _paper_mission_signature_is_route_back_to_mission_executor(
        signature_payload
    )
    entry = _mapping(_mapping(ledger).get("signatures")).get(signature)
    observed_count = int(entry.get("observed_count") or 0) if entry else 0
    next_observed_count = (
        observed_count + 1
        if eligible_route_back and not has_required_delta
        else observed_count
    )
    budget_exhausted = (
        eligible_route_back
        and not has_required_delta
        and next_observed_count
        >= PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS
    )
    next_mode = (
        "mas_mission_executor_fallback"
        if budget_exhausted
        else "opl_targeted_redrive_allowed"
    )
    return {
        "surface_kind": "paper_mission_route_back_budget_status",
        "schema_version": 1,
        "budget_kind": "synonymous_route_back_cross_run_budget",
        "signature": signature,
        "signature_payload": dict(signature_payload),
        "eligible_route_back": eligible_route_back,
        "previous_observed_count": observed_count,
        "next_observed_count": next_observed_count,
        "max_opl_redrives": PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS,
        "opl_redrive_budget_remaining": max(
            PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS
            - next_observed_count,
            0,
        ),
        "budget_exhausted": budget_exhausted,
        "next_mode": next_mode,
        "required_next_owner": (
            "mission_executor" if budget_exhausted else "one-person-lab"
        ),
        "stop_same_semantic_redrive": budget_exhausted,
        "authority_boundary": _paper_mission_route_back_budget_authority_boundary(),
    }


def _paper_mission_signature_is_route_back_to_mission_executor(
    signature_payload: Mapping[str, Any],
) -> bool:
    route_back_identity = _mapping(signature_payload.get("route_back_identity"))
    return (
        _optional_text(route_back_identity.get("decision_kind")) == "route_back"
        and _optional_text(route_back_identity.get("next_owner")) == "mission_executor"
    )


def _record_paper_mission_route_back_budget_ledger(
    *,
    ledger: Mapping[str, Any],
    ledger_ref: Path,
    progress_guard: Mapping[str, Any],
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    trigger: str,
    source: str,
) -> dict[str, Any]:
    budget = _mapping(progress_guard.get("route_back_budget"))
    signature = _optional_text(progress_guard.get("signature"))
    if (
        signature is None
        or not budget
        or budget.get("eligible_route_back") is not True
    ):
        return dict(ledger)
    updated = dict(ledger)
    signatures = dict(_mapping(updated.get("signatures")))
    previous = _mapping(signatures.get(signature))
    observed_count = int(budget.get("next_observed_count") or 0)
    signatures[signature] = {
        "signature": signature,
        "signature_payload": _mapping(progress_guard.get("signature_payload")),
        "observed_count": observed_count,
        "budget_exhausted": budget.get("budget_exhausted") is True,
        "next_mode": _optional_text(budget.get("next_mode")),
        "last_trigger": trigger,
        "last_source": source,
        "last_candidate_ref": _first_text(
            consume_readback.get("candidate_ref"),
            handoff.get("candidate_ref"),
        ),
        "last_paper_mission_transaction_ref": _first_text(
            handoff.get("paper_mission_transaction_ref"),
            _mapping(consume_readback.get("paper_mission_transaction")).get(
                "transaction_id"
            ),
        ),
        "first_observed_count": int(previous.get("first_observed_count") or 1),
    }
    updated.update(
        {
            "signatures": signatures,
            "signature_count": len(signatures),
            "latest_signature": signature,
            "latest_budget_status": dict(budget),
        }
    )
    ledger_ref.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
    ledger_ref.write_text(text, encoding="utf-8")
    updated["source_ref"] = str(ledger_ref)
    updated["file_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return updated


def _paper_mission_route_back_budget_exhausted(
    progress_guard: Mapping[str, Any],
) -> bool:
    return _mapping(progress_guard.get("route_back_budget")).get(
        "budget_exhausted"
    ) is True


def _paper_mission_semantic_progress_signature_payload(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(consume_readback.get("paper_mission_transaction"))
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    route = _mapping(consume_readback.get("opl_route_command"))
    next_decision = _mapping(consume_readback.get("next_owner_or_human_decision"))
    terminal_gate = _mapping(consume_readback.get("terminal_owner_gate"))
    owner_answer = _mapping(
        consume_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    owner_answer_decision = _mapping(owner_answer.get("stage_terminal_decision"))
    progress_refs = _paper_mission_progress_refs(
        consume_readback=consume_readback,
        handoff=handoff,
        transaction=transaction,
        owner_answer=owner_answer,
    )
    return {
        "study_id": _first_text(
            consume_readback.get("study_id"),
            handoff.get("study_id"),
            transaction.get("study_id"),
        ),
        "mission_id": _paper_mission_canonical_followthrough_identity(
            _first_text(
                consume_readback.get("mission_id"),
                handoff.get("mission_id"),
                transaction.get("mission_id"),
            )
        ),
        "transaction_identity": {
            "paper_mission_transaction_ref": _paper_mission_canonical_followthrough_identity(
                _first_text(
                    handoff.get("paper_mission_transaction_ref"),
                    route.get("paper_mission_transaction_ref"),
                    transaction.get("transaction_id"),
                )
            ),
            "stage_id": _first_text(
                transaction.get("stage_id"),
                decision.get("target_stage_id"),
                decision.get("next_stage_id"),
            ),
            "stage_run_ref": _optional_text(transaction.get("stage_run_ref")),
        },
        "route_back_identity": {
            "decision_kind": _first_text(
                owner_answer_decision.get("decision_kind"),
                decision.get("decision_kind"),
            ),
            "decision_status": _first_text(
                owner_answer_decision.get("status"),
                decision.get("status"),
            ),
            "next_owner": _first_text(
                owner_answer_decision.get("next_owner"),
                decision.get("next_owner"),
                next_decision.get("next_owner"),
                handoff.get("next_owner"),
            ),
            "route_command": _first_text(
                handoff.get("route_command_kind"),
                route.get("command_kind"),
            ),
            "route_target": _first_text(
                handoff.get("route_target"),
                route.get("target"),
                decision.get("target_stage_id"),
                decision.get("next_stage_id"),
            ),
            "repair_scope": _first_text(
                owner_answer_decision.get("repair_scope"),
                decision.get("repair_scope"),
                decision.get("next_work_unit"),
            ),
            "route_back_evidence_kind": _route_back_evidence_kind(
                _first_text(
                    owner_answer_decision.get("route_back_evidence_ref"),
                    decision.get("route_back_evidence_ref"),
                )
            ),
        },
        "domain_gate_identity": {
            "gate_owner": _optional_text(terminal_gate.get("owner")),
            "gate_kind": _optional_text(terminal_gate.get("gate_kind")),
            "blocked_reason": _first_text(
                terminal_gate.get("blocked_reason"),
                terminal_gate.get("reason"),
                owner_answer.get("blocked_reason"),
            ),
            "owner_answer_shape": _optional_text(owner_answer.get("owner_answer_shape")),
            "owner_answer_status": _optional_text(owner_answer.get("status")),
        },
        "semantic_delta_refs": _paper_mission_semantic_delta_refs(progress_refs),
    }


def _paper_mission_progress_refs_for_guard(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(consume_readback.get("paper_mission_transaction"))
    owner_answer = _mapping(
        consume_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    return _paper_mission_progress_refs(
        consume_readback=consume_readback,
        handoff=handoff,
        transaction=transaction,
        owner_answer=owner_answer,
    )


def _paper_mission_progress_refs(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    transaction: Mapping[str, Any],
    owner_answer: Mapping[str, Any],
) -> dict[str, Any]:
    authority_readback = _mapping(consume_readback.get("authority_consume_readback"))
    consume_result = _mapping(authority_readback.get("consume_result"))
    return {
        "accepted_owner_receipt_ref": _first_text(
            consume_result.get("domain_owner_receipt_ref"),
            consume_result.get("quality_gate_receipt_ref"),
            owner_answer.get("domain_owner_receipt_ref"),
            owner_answer.get("quality_gate_receipt_ref"),
        ),
        "typed_blocker_ref": _first_text(
            consume_result.get("typed_blocker_ref"),
            owner_answer.get("typed_blocker_ref"),
        ),
        "human_gate_ref": _first_text(
            consume_result.get("human_gate_ref"),
            owner_answer.get("human_gate_ref"),
        ),
        "route_back_evidence_ref": _first_text(
            consume_result.get("route_back_evidence_ref"),
            owner_answer.get("route_back_evidence_ref"),
            _mapping(owner_answer.get("stage_terminal_decision")).get(
                "route_back_evidence_ref"
            ),
            _mapping(transaction.get("stage_terminal_decision")).get(
                "route_back_evidence_ref"
            ),
        ),
        "paper_facing_delta_ref": _first_text(
            consume_result.get("paper_facing_delta_ref"),
            owner_answer.get("paper_facing_delta_ref"),
        ),
        "owner_decision_packet_ref": _first_text(
            consume_result.get("owner_decision_packet_ref"),
            owner_answer.get("owner_decision_packet_ref"),
        ),
        "successor_work_unit_ref": _first_text(
            consume_result.get("successor_work_unit_ref"),
            owner_answer.get("successor_work_unit_ref"),
            _mapping(owner_answer.get("stage_terminal_decision")).get(
                "successor_work_unit_ref"
            ),
            _mapping(transaction.get("stage_terminal_decision")).get(
                "successor_work_unit_ref"
            ),
        ),
        "carry_forward_risk_receipt_ref": _first_text(
            consume_result.get("carry_forward_risk_receipt_ref"),
            owner_answer.get("carry_forward_risk_receipt_ref"),
            _mapping(owner_answer.get("stage_terminal_decision")).get(
                "carry_forward_risk_receipt_ref"
            ),
            _mapping(transaction.get("stage_terminal_decision")).get(
                "carry_forward_risk_receipt_ref"
            ),
        ),
        "canonical_paper_or_artifact_delta_ref": _first_text(
            consume_result.get("canonical_paper_or_artifact_delta_ref"),
            owner_answer.get("canonical_paper_or_artifact_delta_ref"),
            consume_result.get("canonical_artifact_delta_ref"),
            owner_answer.get("canonical_artifact_delta_ref"),
        ),
        "ai_reviewer_or_publication_gate_delta_ref": _first_text(
            consume_result.get("ai_reviewer_or_publication_gate_delta_ref"),
            owner_answer.get("ai_reviewer_or_publication_gate_delta_ref"),
            consume_result.get("ai_reviewer_delta_ref"),
            owner_answer.get("ai_reviewer_delta_ref"),
            consume_result.get("publication_gate_delta_ref"),
            owner_answer.get("publication_gate_delta_ref"),
        ),
        "artifact_delta_refs": _paper_mission_artifact_delta_ref_ids(transaction),
        "paper_audit_pack_refs": _paper_mission_sorted_mapping(
            _mapping(transaction.get("paper_audit_pack_refs"))
        ),
    }


def _paper_mission_semantic_delta_refs(progress_refs: Mapping[str, Any]) -> dict[str, Any]:
    return _compact_non_null_mapping(
        {
            "accepted_owner_receipt_ref": progress_refs.get("accepted_owner_receipt_ref"),
            "typed_blocker_ref": progress_refs.get("typed_blocker_ref"),
            "human_gate_ref": progress_refs.get("human_gate_ref"),
            "successor_work_unit_ref": progress_refs.get("successor_work_unit_ref"),
            "carry_forward_risk_receipt_ref": progress_refs.get(
                "carry_forward_risk_receipt_ref"
            ),
            "canonical_paper_or_artifact_delta_ref": progress_refs.get(
                "canonical_paper_or_artifact_delta_ref"
            ),
            "ai_reviewer_or_publication_gate_delta_ref": progress_refs.get(
                "ai_reviewer_or_publication_gate_delta_ref"
            ),
        }
    )


def _compact_non_null_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _paper_mission_canonical_followthrough_identity(value: str | None) -> str | None:
    if value is None:
        return None
    marker = "::followthrough"
    index = value.find(marker)
    if index < 0:
        return value
    return value[:index]


def _paper_mission_compact_followthrough_identity(value: str | None) -> str | None:
    if value is None:
        return None
    marker = "::followthrough"
    index = value.find(marker)
    if index < 0:
        return value
    return f"{value[:index]}{marker}"


def _canonicalize_followthrough_transaction_identity(
    transaction: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(_mapping(transaction))
    mission_id = _paper_mission_canonical_followthrough_identity(
        _optional_text(payload.get("mission_id"))
    )
    if mission_id is not None:
        payload["mission_id"] = mission_id
    transaction_id = _paper_mission_compact_followthrough_identity(
        _optional_text(payload.get("transaction_id"))
    )
    if transaction_id is not None:
        payload["transaction_id"] = transaction_id
    route = dict(_mapping(payload.get("opl_route_command")))
    if route and transaction_id is not None:
        decision = _mapping(payload.get("stage_terminal_decision"))
        if (
            _optional_text(decision.get("decision_kind")) == "route_back"
            and (target_stage_id := _optional_text(decision.get("target_stage_id")))
            is not None
        ):
            route["target"] = target_stage_id
        route["source_terminal_decision_ref"] = f"{transaction_id}#stage_terminal_decision"
        payload["opl_route_command"] = route
    return payload


def _route_back_evidence_kind(ref: str | None) -> str | None:
    if ref is None:
        return None
    if ref.startswith("route-back:"):
        parts = ref.split(":")
        return ":".join(parts[:3]) if len(parts) >= 3 else ref
    return ref


def _paper_mission_required_executor_delta_present(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    signature_payload = _paper_mission_semantic_progress_signature_payload(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    progress_refs = _mapping(signature_payload.get("semantic_delta_refs"))
    return any(
        progress_refs.get(key)
        for key in (
            "accepted_owner_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "successor_work_unit_ref",
            "carry_forward_risk_receipt_ref",
            "canonical_paper_or_artifact_delta_ref",
            "ai_reviewer_or_publication_gate_delta_ref",
        )
    )


def _paper_mission_route_request_progress_guard(
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    route = _mapping(handoff.get("opl_route_command"))
    payload = {
        "study_id": _optional_text(handoff.get("study_id")),
        "mission_id": _optional_text(handoff.get("mission_id")),
        "paper_mission_transaction_ref": _optional_text(
            handoff.get("paper_mission_transaction_ref")
        ),
        "candidate_ref": _optional_text(handoff.get("candidate_ref")),
        "route_command": _first_text(
            handoff.get("route_command_kind"),
            route.get("command_kind"),
        ),
        "route_target": _first_text(handoff.get("route_target"), route.get("target")),
        "semantic_progress_guard_kind": "non_advancing_route_back_detection",
    }
    signature = _stable_sha256(payload)
    executor_stage = _paper_mission_mas_owned_executor_stage_packet(
        signature=signature,
        signature_payload=payload,
    )
    return {
        "surface_kind": "opl_route_semantic_progress_guard",
        "schema_version": 1,
        "guard_kind": "non_advancing_route_back_detection",
        "signature": signature,
        "signature_payload": payload,
        "non_advancing_status": "not_evaluated_by_mas_payload_only",
        "required_executor_outputs": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
        "mas_owned_executor_stage": executor_stage,
        "runtime_owner_expected_action": (
            "If OPL observes the same route-back/domain gate transaction without a "
            "new accepted owner answer, human gate, typed blocker, or paper-facing "
            "delta, stop ordinary redrive and return non_advancing_route_back to MAS."
        ),
        "can_claim_paper_progress": False,
    }


def _paper_mission_artifact_delta_ref_ids(
    transaction: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for item in _mapping_list(transaction.get("artifact_delta_refs")):
        ref = _first_text(item.get("uri"), item.get("ref_id"), item.get("artifact_ref"))
        if ref is not None:
            refs.append(ref)
    return sorted(set(refs))


def _paper_mission_sorted_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in sorted(value)
        if isinstance(key, str) and value.get(key) is not None
    }


def _stable_sha256(value: Mapping[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _paper_mission_drive_result_status(
    *,
    handoff_ready: bool,
    submission_status: str | None,
    runtime_status: str | None,
    carrier_readback: Mapping[str, Any],
) -> str:
    if runtime_status == "opl_runtime_attempt_running_observed":
        return "opl_stage_route_running"
    if runtime_status == "opl_runtime_terminal_readback_observed":
        gate = _mapping(carrier_readback.get("terminal_closeout"))
        if _optional_text(gate.get("gate_kind")) == "human_gate":
            return "waiting_for_human_gate"
        return "opl_terminal_closeout_observed"
    if submission_status in {"submitted", "idempotent_noop"}:
        return "submitted_to_opl_runtime"
    if submission_status in {"not_configured", "failed", "timeout", "not_actionable"}:
        return "opl_runtime_submission_failed"
    return "waiting_for_owner_resolution" if not handoff_ready else "opl_runtime_submission_pending"


def _consume_candidate_missing_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    source: str,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_consume_candidate_missing_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": paper_mission_command,
        "action_intent": _action_intent(paper_mission_command),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "status": "candidate_package_missing",
        "required_next_command": (
            "paper-mission package-candidate --output-root "
            f"{Path(profile.workspace_root) / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / '<run_id>'}"
        ),
        "authority_consume_readback": {
            "surface_kind": "mas_paper_mission_candidate_consume_readback",
            "schema_version": 1,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": {
                "status": "route_back",
                "outcome": "route_back",
                "authority_materialized": False,
            },
            "candidate_is_authority": False,
            "route_back": {
                "reason_code": "candidate_package_missing",
                "next_owner": "mission_executor",
                "resume_condition": (
                    "generate a submission_milestone_candidate package before "
                    "MAS authority consumption"
                ),
            },
            "write_plan": {
                "mode": "readback_only",
                "written_files": [],
            },
        },
        "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "candidate_package_missing_no_write",
            "old_default_executor_dispatch_role": "diagnostic_or_migration_only",
        },
    }


def paper_mission_domain_handler_dispatch_receipt(
    *,
    task: dict[str, Any],
    task_path: Path,
    load_profile: Callable[[str | Path], Any],
) -> dict[str, Any]:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    profile_ref = payload.get("profile") or payload.get("profile_path") or payload.get("profile_ref")
    if not profile_ref:
        return _paper_mission_dispatch_error(
            task=task,
            task_path=task_path,
            reason="missing_profile_ref",
        )
    study_id = str(payload.get("study_id") or "").strip()
    if not study_id:
        return _paper_mission_dispatch_error(
            task=task,
            task_path=task_path,
            reason="missing_study_id",
        )
    profile = load_profile(Path(str(profile_ref)))
    requested_command = _optional_text(payload.get("paper_mission_command"))
    dry_run = payload.get("dry_run") is True
    dispatch_command = _domain_handler_paper_mission_command(
        task=task,
        requested_command=requested_command,
        dry_run=dry_run,
    )
    readback = build_paper_mission_readback(
        profile=profile,
        profile_ref=Path(str(profile_ref)),
        study_id=study_id,
        paper_mission_command=dispatch_command,
        objective=_optional_text(payload.get("objective")),
        mission_id=_optional_text(payload.get("mission_id")),
        candidate=_optional_text(payload.get("candidate")),
        run_id=(
            _optional_text(payload.get("run_id"))
            or _default_domain_handler_drive_run_id(
                task=task,
                study_id=study_id,
            )
        ),
        submit_opl_runtime=(
            bool(payload.get("submit_opl_runtime"))
            if "submit_opl_runtime" in payload
            else None
        ),
        opl_bin=_optional_text(payload.get("opl_bin")),
        one_shot_migration=bool(payload.get("one_shot_migration", False)),
        study_progress_payload=_optional_text(payload.get("study_progress_payload")),
        domain_health_diagnostic_payload=_optional_text(
            payload.get("domain_health_diagnostic_payload")
        ),
        output_root=_optional_text(payload.get("output_root")),
        dry_run=dry_run,
        source="domain-handler-dispatch",
    )
    return {
        "surface_kind": "mas_family_domain_handler_dispatch_receipt",
        "version": "mas-family-domain-handler.v1",
        "accepted": True,
        "task_id": str(task.get("task_id") or "unknown_task"),
        "task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        "source_task_ref": str(task_path),
        "forbidden_domain_truth_write": False,
        "dispatch": {
            "action_type": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "study_id": study_id,
            "execution_policy": _dispatch_execution_policy(readback),
            "recommended_domain_command": (
                _recommended_domain_command(
                    profile_ref=profile_ref,
                    study_id=study_id,
                    readback=readback,
                )
            ),
            "result": readback,
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority": False,
            "writes_runtime": False,
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        },
        "forbidden_write_guard_proof": {
            "result": "accepted_no_forbidden_writes",
            "task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "requested_writes": [],
        },
    }


def _domain_handler_paper_mission_command(
    *,
    task: Mapping[str, Any],
    requested_command: str | None,
    dry_run: bool,
) -> str:
    if dry_run:
        return requested_command or "start"
    if _optional_text(task.get("task_kind")) == PAPER_MISSION_START_OR_RESUME_TASK_KIND:
        if requested_command in {None, "start", "resume"}:
            return "drive"
    return requested_command or "inspect"


def _default_domain_handler_drive_run_id(
    *,
    task: Mapping[str, Any],
    study_id: str,
) -> str | None:
    if _optional_text(task.get("task_kind")) != PAPER_MISSION_START_OR_RESUME_TASK_KIND:
        return None
    task_id = _optional_text(task.get("task_id")) or "paper-mission-start-or-resume"
    return f"domain-handler-dispatch-{_slug(study_id)}-{_slug(task_id)}"


def _build_materialized_mission_readback_if_available(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    dry_run: bool,
    source: str,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any] | None:
    mission_path = _latest_materialized_mission_path(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    if mission_path is None:
        return None
    mission = _normalize_materialized_mission_for_cli_readback(
        mission=_load_json_object(mission_path),
        study_id=study_id,
        paper_mission_command=paper_mission_command,
    )
    default_readback = (
        dict(mission["one_shot_migration_readback"])
        if isinstance(mission.get("one_shot_migration_readback"), dict)
        else {}
    )
    candidate_manifest_path = mission_path.parent / "candidate_manifest.json"
    candidate_manifest = (
        _load_json_object(candidate_manifest_path)
        if candidate_manifest_path.exists()
        else None
    )
    resolved_study_id = _materialized_study_id(
        mission=mission,
        requested_study_id=study_id,
    )
    resolved_study_root = _materialized_study_root(
        profile=profile,
        requested_study_id=study_id,
        mission=mission,
        mission_path=mission_path,
    )
    consumption_ledger_readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=str(mission["mission_id"]),
        study_id=resolved_study_id,
        objective=str(mission["objective"]),
        paper_mission_command=paper_mission_command,
        study_root=resolved_study_root,
        mission=mission,
        transaction_override=_mapping(
            (consumption_ledger_readback or {}).get("paper_mission_transaction")
        ),
        transaction_source_override=(
            "paper_mission_consumption_ledger"
            if consumption_ledger_readback is not None
            else None
        ),
        authority_consume_readback=None,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    if consumption_ledger_readback is not None:
        transaction_readback["next_owner_or_human_decision"] = (
            _next_owner_decision_for_consumption_ledger_readback(
                readback=consumption_ledger_readback,
                fallback=_mapping(transaction_readback.get("next_owner_or_human_decision")),
            )
        )
    mission = {
        **mission,
        "mission_state": _mission_state_for_materialized_readback(
            mission=mission,
            transaction_readback=transaction_readback,
            consumption_ledger_readback=consumption_ledger_readback,
        ),
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        **(
            {
                "consume_result": _consume_result_for_consumption_ledger_readback(
                    consumption_ledger_readback
                )
            }
            if consumption_ledger_readback is not None
            else {}
        ),
    }
    validation = _validate_with_contract_if_available(mission)
    projection_fields = _paper_mission_materialized_projection_fields(
        transaction_readback=transaction_readback
    )
    return {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": paper_mission_command,
        "action_intent": _action_intent(paper_mission_command),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "study_root_exists": resolved_study_root.exists(),
        "mission_id": mission["mission_id"],
        "objective": mission["objective"],
        "mission_state": mission["mission_state"],
        "materialized_mission_ref": str(mission_path),
        **_transaction_readback_output_fields(transaction_readback),
        **projection_fields,
        **(
            {"candidate_manifest_ref": str(candidate_manifest_path)}
            if candidate_manifest_path.exists()
            else {}
        ),
        "paper_mission_run": mission,
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        "stage_terminal_decision": transaction_readback["stage_terminal_decision"],
        "opl_route_command": transaction_readback["opl_route_command"],
        "default_readback": default_readback,
        **(
            {"candidate_manifest": candidate_manifest}
            if candidate_manifest is not None
            else {}
        ),
        **(
            {
                "paper_mission_consumption_ledger_readback": (
                    consumption_ledger_readback
                ),
                "paper_mission_current_transaction_source": (
                    "paper_mission_consumption_ledger"
                ),
            }
            if consumption_ledger_readback is not None
            else {}
        ),
        "consume_candidate_status": transaction_readback.get(
            "consume_candidate_status_override"
        )
        or _optional_text((consumption_ledger_readback or {}).get("consume_candidate_status"))
        or _consume_candidate_status(mission, default_readback),
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": True,
            "forbidden_authority_writes": list(
                ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "forbidden_authority_writes": list(ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "contract_validation": validation,
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "materialized_mission_readback_no_write",
            "old_default_executor_dispatch_role": "diagnostic_or_migration_only",
            "opl_consumes": "paper_mission_transaction.opl_route_command",
            "mas_terminalizes": "paper_mission_transaction.stage_terminal_decision",
        },
        "cutover_proof": {
            "default_readback_surface": "PaperMissionRun",
            "terminalizer_surface": "PaperMissionTransaction",
            "materialized_paper_mission_run_loaded": True,
            "stage_terminal_decision_present": bool(
                _materialized_stage_terminal_decision(mission)
            ),
            "opl_route_command_present": bool(_materialized_opl_route_command(mission)),
            "legacy_blocker_controls_default_execution": False,
            "authority_materialized": False,
        },
    }


def _paper_mission_materialized_projection_fields(
    *,
    transaction_readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    owner_answer = _mapping(
        transaction_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    next_decision = _mapping(transaction_readback.get("next_owner_or_human_decision"))
    artifact_delta_refs = _mapping_list(transaction.get("artifact_delta_refs"))
    return _compact_non_null_mapping(
        {
            "artifact_delta_refs": artifact_delta_refs or None,
            "owner_answer_shape": _first_text(
                owner_answer.get("owner_answer_shape"),
                decision.get("owner_answer_shape"),
                decision.get("decision_kind"),
            ),
            "paper_facing_delta_ref": _first_text(
                owner_answer.get("paper_facing_delta_ref"),
                decision.get("paper_facing_delta_ref"),
            ),
            "semantic_progress_signature": owner_answer.get(
                "semantic_progress_signature"
            ),
            "route_back_budget": owner_answer.get("route_back_budget"),
            "mission_executor_fallback_action": owner_answer.get(
                "mission_executor_fallback_action"
            ),
            "carry_forward_risk_receipt_ref": owner_answer.get(
                "carry_forward_risk_receipt_ref"
            ),
            "next_owner": _first_text(
                next_decision.get("next_owner"),
                decision.get("next_owner"),
            ),
        }
    )


def _latest_materialized_mission_path(
    *,
    workspace_root: Path,
    study_id: str,
) -> Path | None:
    root = (
        workspace_root.expanduser().resolve()
        / PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH
    )
    if not root.exists():
        return None
    candidates = sorted(
        (
            path
            for path in root.glob("*/*/paper_mission_run.json")
            if path.is_file()
            and _materialized_mission_path_matches(path, requested_study_id=study_id)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _latest_candidate_package_manifest_path(
    *,
    workspace_root: Path,
    study_id: str,
) -> Path | None:
    root = (
        workspace_root.expanduser().resolve()
        / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH
    )
    if not root.exists():
        return None
    candidates = sorted(
        (
            path
            for path in root.glob("*/**/package_manifest.json")
            if path.is_file()
            and _materialized_mission_path_matches(path, requested_study_id=study_id)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _resolve_consume_candidate_ref(
    *,
    profile: Any,
    study_id: str,
    candidate: str | Path | None,
) -> str | None:
    explicit = _optional_text(candidate)
    if explicit is not None:
        return explicit
    candidate_package = _latest_candidate_package_manifest_path(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    return str(candidate_package) if candidate_package is not None else None


def _build_materialized_candidate_package_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    source: str,
    source_readback_override: Mapping[str, Any] | None = None,
    paper_facing_delta_ref: str | Path | None = None,
) -> dict[str, Any]:
    if output_root is None:
        raise ValueError("--output-root is required for package-candidate")
    readback = (
        _paper_mission_followthrough_source_readback(
            readback=source_readback_override,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            source=source,
        )
        if source_readback_override is not None
        else None
    )
    if readback is None:
        readback = _build_materialized_mission_readback_if_available(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="package-candidate",
            dry_run=False,
            source=source,
        )
        if readback is None:
            raise ValueError(
                "package-candidate requires a materialized PaperMissionRun under "
                "ops/medautoscience/paper_mission_one_shot_migration"
            )
    mission = dict(readback["paper_mission_run"])
    candidate_manifest = (
        dict(readback["candidate_manifest"])
        if isinstance(readback.get("candidate_manifest"), Mapping)
        else paper_mission_canary_candidate_manifest(mission)
    )
    candidate_artifact_delta = paper_mission_candidate_artifact_delta(mission)
    owner_decision_packet = paper_mission_owner_decision_packet(mission)
    summary = _foreground_owner_decision_summary(
        readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
    )
    mission_executor_handoff = _mission_executor_handoff(
        readback=readback,
        foreground_owner_decision_summary=summary,
    )
    paper_facing_candidate_delta = materialized_paper_facing_candidate_delta(
        readback=readback,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        mission_executor_handoff=mission_executor_handoff,
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    owner_blocker_packet = paper_mission_owner_blocker_packet(
        readback=readback,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=mission_executor_handoff,
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    owner_consumption_request = paper_mission_owner_consumption_request(
        readback=readback,
        candidate_manifest=candidate_manifest,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=mission_executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_blocker_packet=owner_blocker_packet,
        candidate_refs={},
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    output_manifest = _write_materialized_candidate_package_outputs(
        output_root=Path(output_root),
        study_id=str(readback["study_id"]),
        paper_mission_readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=mission_executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_consumption_request=owner_consumption_request,
        owner_blocker_packet=owner_blocker_packet,
        adopted_external_paper_delta_ref=(
            str(Path(paper_facing_delta_ref).expanduser().resolve())
            if paper_facing_delta_ref is not None
            else None
        ),
    )
    return {
        "surface_kind": "paper_mission_candidate_package_write_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "package-candidate",
        "action_intent": _action_intent("package-candidate"),
        "source": source,
        "dry_run": False,
        "profile": readback["profile"],
        "requested_study_id": readback["requested_study_id"],
        "study_id": readback["study_id"],
        "study_root": readback["study_root"],
        "study_root_exists": readback["study_root_exists"],
        "mission_id": readback["mission_id"],
        "objective": readback["objective"],
        "materialized_mission_ref": readback["materialized_mission_ref"],
        "stage_terminal_decision": readback["stage_terminal_decision"],
        "opl_route_command": readback["opl_route_command"],
        "opl_runtime_readback_status": readback["opl_runtime_readback_status"],
        "terminal_owner_gate": readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "next_owner_or_human_decision": readback["next_owner_or_human_decision"],
        "transaction_state": readback["transaction_state"],
        "consume_candidate_status": readback["consume_candidate_status"],
        "candidate_manifest": candidate_manifest,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "foreground_owner_decision_summary": summary,
        "mission_executor_handoff": mission_executor_handoff,
        "paper_facing_candidate_delta": paper_facing_candidate_delta,
        "owner_consumption_request": owner_consumption_request,
        "owner_blocker_packet": owner_blocker_packet,
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(
                output_root
            ),
            "writes_paper_body": False,
            "writes_candidate_workspace": True,
            "dry_run_only": False,
            "forbidden_authority_writes": list(
                CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "output_manifest": output_manifest,
    }


def _paper_mission_followthrough_source_readback(
    *,
    readback: Mapping[str, Any] | None,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
) -> dict[str, Any] | None:
    source_readback = _mapping(readback)
    if not source_readback:
        return None
    transaction = _followthrough_transaction_for_readback(source_readback)
    if not transaction:
        return None
    resolved_study_id = _first_text(transaction.get("study_id"), study_id) or study_id
    mission_id = (
        _first_text(transaction.get("mission_id"), source_readback.get("mission_id"))
        or f"paper-mission::{resolved_study_id}::followthrough"
    )
    objective = (
        _first_text(
            source_readback.get("objective"),
            _mapping(transaction.get("stage_terminal_decision")).get("next_work_unit"),
            _mapping(transaction.get("stage_terminal_decision")).get("repair_scope"),
        )
        or "PaperMission terminal route-back followthrough"
    )
    study_root = Path(getattr(profile, "studies_root")) / resolved_study_id
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=mission_id,
        study_id=resolved_study_id,
        objective=objective,
        paper_mission_command="package-candidate",
        study_root=study_root,
        mission=None,
        transaction_override=transaction,
        transaction_source_override="paper_mission_drive_followthrough",
        authority_consume_readback=None,
        enable_opl_live_probe=False,
    )
    candidate_manifest = _followthrough_candidate_manifest(
        readback=source_readback,
        transaction=transaction,
        mission_id=mission_id,
        study_id=resolved_study_id,
    )
    paper_mission_run = {
        "schema_version": PAPER_MISSION_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": resolved_study_id,
        "objective": objective,
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "terminal_route_back_followthrough_candidate",
                "artifact_ref": (
                    "paper-mission-followthrough://"
                    f"{resolved_study_id}/{_slug(mission_id)}"
                ),
                "delta_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
                "status": "candidate",
            }
        ],
        "source_refs": _followthrough_source_refs(source_readback),
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    return {
        "surface_kind": "paper_mission_followthrough_materialized_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "package-candidate",
        "action_intent": _action_intent("package-candidate"),
        "source": source,
        "dry_run": False,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": resolved_study_id,
        "study_root": str(study_root),
        "study_root_exists": study_root.exists(),
        "mission_id": mission_id,
        "objective": objective,
        "mission_state": "candidate_ready_for_consumption",
        "materialized_mission_ref": _optional_text(
            source_readback.get("materialized_mission_ref")
        )
        or "paper_mission_drive_followthrough",
        **_transaction_readback_output_fields(transaction_readback),
        "candidate_manifest": candidate_manifest,
        "paper_mission_run": paper_mission_run,
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "consume_candidate_status": "accepted_candidate",
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": True,
            "forbidden_authority_writes": list(
                CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
    }


def _followthrough_transaction_for_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    transaction = _first_mapping(
        _canonicalize_followthrough_transaction_identity(
            _mapping(readback.get("stage_route_submission_source_transaction"))
        ),
        _canonicalize_followthrough_transaction_identity(
            _mapping(owner_answer.get("paper_mission_transaction"))
        ),
        _canonicalize_followthrough_transaction_identity(
            _mapping(readback.get("paper_mission_transaction"))
        ),
    )
    decision = _mapping(transaction.get("stage_terminal_decision"))
    decision_kind = _optional_text(decision.get("decision_kind"))
    terminal_closeout_observed = _optional_text(
        readback.get("opl_runtime_readback_status")
    ) == "opl_runtime_terminal_readback_observed" or _optional_text(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("carrier_status")
    ) == "opl_runtime_terminal_readback_observed"
    if decision_kind != "route_back" and not (
        decision_kind == "continue_same_stage" and terminal_closeout_observed
    ):
        return {}
    study_id = _optional_text(transaction.get("study_id"))
    mission_id = _paper_mission_canonical_followthrough_identity(
        _optional_text(transaction.get("mission_id"))
    )
    if study_id is None or mission_id is None:
        return {}
    target_stage = (
        _first_text(
            decision.get("target_stage_id"),
            decision.get("route_target"),
            decision.get("next_stage_id"),
            transaction.get("stage_id"),
        )
        or "submission_milestone_candidate"
    )
    next_work_unit = (
        _first_text(
            decision.get("target_stage_id"),
            decision.get("route_target"),
            decision.get("next_work_unit"),
            decision.get("work_unit_id"),
            decision.get("repair_scope"),
            "continue paper-facing submission milestone work",
        )
        or "continue paper-facing submission milestone work"
    )
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": (
            "MAS mission executor consumed the terminal closeout/route-back as a "
            "fresh paper-facing candidate and is continuing the same PaperMission "
            "stage."
        ),
        "next_owner": "mission_executor",
        "next_work_unit": next_work_unit,
        "source_route_back_evidence_ref": _optional_text(
            decision.get("route_back_evidence_ref")
        ),
    }
    source_transaction_id = _optional_text(transaction.get("transaction_id")) or mission_id
    followthrough_basis = (
        "terminal-route-back-followthrough::"
        f"{_slug(mission_id)}::{_slug(source_transaction_id)}"
    )
    stage_run_ref = f"paper-mission-followthrough://{study_id}/{_slug(mission_id)}"
    return _paper_mission_followthrough_transaction_instance(
        build_paper_mission_transaction(
            mission_id=mission_id,
            study_id=study_id,
            stage_id=target_stage,
            stage_run_ref=stage_run_ref,
            terminal_decision=terminal_decision,
            artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
            paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
            idempotency_basis=followthrough_basis,
        ),
        instance_basis=followthrough_basis,
    )


def _paper_mission_followthrough_transaction_instance(
    transaction: Mapping[str, Any],
    *,
    instance_basis: str,
) -> dict[str, Any]:
    payload = dict(transaction)
    suffix = f"::followthrough::{_stable_sha256(instance_basis)[:12]}"
    payload["transaction_id"] = f"{payload['transaction_id']}{suffix}"
    decision = dict(_mapping(payload.get("stage_terminal_decision")))
    route = dict(_mapping(payload.get("opl_route_command")))
    route["source_terminal_decision_ref"] = (
        f"{payload['transaction_id']}#stage_terminal_decision"
    )
    payload["stage_terminal_decision"] = decision
    payload["opl_route_command"] = route
    idempotency = dict(_mapping(payload.get("idempotency")))
    idempotency["idempotency_key"] = f"{idempotency['idempotency_key']}{suffix}"
    idempotency["transaction_fingerprint"] = (
        f"{idempotency['transaction_fingerprint']}{suffix}"
    )
    payload["idempotency"] = idempotency
    return PaperMissionTransaction.from_payload(payload).to_dict()


def _followthrough_candidate_manifest(
    *,
    readback: Mapping[str, Any],
    transaction: Mapping[str, Any],
    mission_id: str,
    study_id: str,
) -> dict[str, Any]:
    decision = _mapping(transaction.get("stage_terminal_decision"))
    return {
        "candidate_id": f"paper-mission-followthrough::{study_id}::{_slug(mission_id)}",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": "accepted_candidate",
        "candidate_manifest_ref": _optional_text(readback.get("candidate_ref")),
        "candidate_artifact_refs": [
            _optional_text(ref.get("uri")) or _optional_text(ref.get("ref_id"))
            for ref in _mapping_list(transaction.get("artifact_delta_refs"))
            if _optional_text(ref.get("uri")) or _optional_text(ref.get("ref_id"))
        ],
        "source_readiness_refs": _text_list(readback.get("source_readiness_refs")),
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
            "requirement_ref": f"paper-mission-followthrough::{study_id}",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": _first_text(decision.get("next_owner"), "mission_executor"),
        "resume_condition": _first_text(
            decision.get("reason"),
            "MAS consumes the followthrough candidate or routes it again.",
        ),
        "paper_mission_transaction": dict(transaction),
    }


def _followthrough_source_refs(readback: Mapping[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for key in (
        "candidate_ref",
        "materialized_mission_ref",
        "opl_runtime_readback_status",
    ):
        value = _optional_text(readback.get(key))
        if value is not None:
            refs.append({"ref_id": key, "ref_kind": key, "uri": value})
    consume_manifest = _mapping(readback.get("consume_output_manifest"))
    for key in (
        "output_root",
        "opl_route_handoff_ref",
        "paper_mission_transaction_ref",
    ):
        value = _optional_text(consume_manifest.get(key))
        if value is not None:
            refs.append({"ref_id": key, "ref_kind": key, "uri": value})
    return refs


def _materialized_mission_path_matches(
    path: Path,
    *,
    requested_study_id: str,
) -> bool:
    if _study_identity_matches(path.parent.name, requested_study_id):
        return True
    try:
        mission = _load_json_object(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return False
    mission_study_id = mission.get("study_id")
    return isinstance(mission_study_id, str) and _study_identity_matches(
        mission_study_id,
        requested_study_id,
    )


def _normalize_materialized_mission_for_cli_readback(
    *,
    mission: Mapping[str, Any],
    study_id: str,
    paper_mission_command: str,
) -> dict[str, Any]:
    payload = dict(mission)
    resolved_study_id = _optional_text(payload.get("study_id")) or study_id
    source_refs = _mapping_list(payload.get("source_refs"))
    if "paper_audit_pack" not in payload:
        payload["paper_audit_pack"] = _paper_audit_pack_for_cli_readback(
            study_id=resolved_study_id,
            paper_mission_command=paper_mission_command,
            source_refs=source_refs,
        )
    return payload


def _materialized_study_id(
    *,
    mission: dict[str, Any],
    requested_study_id: str,
) -> str:
    mission_study_id = mission.get("study_id")
    return (
        mission_study_id
        if isinstance(mission_study_id, str) and mission_study_id.strip()
        else requested_study_id
    )


def _materialized_study_root(
    *,
    profile: Any,
    requested_study_id: str,
    mission: dict[str, Any],
    mission_path: Path,
) -> Path:
    studies_root = Path(profile.studies_root)
    identities = [
        _materialized_study_id(
            mission=mission,
            requested_study_id=requested_study_id,
        ),
        requested_study_id,
        mission_path.parent.name,
    ]
    for identity in identities:
        candidate = studies_root / identity
        if candidate.exists():
            return candidate
    try:
        study_dirs = sorted(path for path in studies_root.iterdir() if path.is_dir())
    except OSError:
        return studies_root / identities[0]
    for study_dir in study_dirs:
        if any(_study_identity_matches(study_dir.name, identity) for identity in identities):
            return study_dir
    return studies_root / identities[0]


def _study_identity_matches(candidate: str, requested: str) -> bool:
    candidate_text = candidate.strip()
    requested_text = requested.strip()
    if not candidate_text or not requested_text:
        return False
    if candidate_text == requested_text:
        return True
    if candidate_text.lower() == requested_text.lower():
        return True
    candidate_code = _study_numeric_code(candidate_text)
    requested_code = _study_numeric_code(requested_text)
    return bool(candidate_code and requested_code and candidate_code == requested_code)


def _study_numeric_code(value: str) -> str | None:
    match = re.match(r"^(?:dm)?0*(\d+)(?:$|[-_].*)", value.strip(), flags=re.IGNORECASE)
    if match is None:
        return None
    return f"{int(match.group(1)):03d}"


def _consume_candidate_status(
    mission: dict[str, Any],
    default_readback: dict[str, Any],
) -> str:
    status = default_readback.get("consume_candidate_status")
    if isinstance(status, str) and status:
        return status
    consume_result = mission.get("consume_result")
    if isinstance(consume_result, dict):
        result_status = consume_result.get("status")
        if isinstance(result_status, str) and result_status:
            return result_status
    return "not_consumed"


def _materialized_stage_terminal_decision(mission: dict[str, Any]) -> dict[str, Any] | None:
    transaction = mission.get("paper_mission_transaction")
    if isinstance(transaction, dict) and isinstance(
        transaction.get("stage_terminal_decision"),
        dict,
    ):
        return transaction["stage_terminal_decision"]
    readback = mission.get("one_shot_migration_readback")
    if isinstance(readback, dict) and isinstance(readback.get("stage_terminal_decision"), dict):
        return readback["stage_terminal_decision"]
    return None


def _materialized_opl_route_command(mission: dict[str, Any]) -> dict[str, Any] | None:
    transaction = mission.get("paper_mission_transaction")
    if isinstance(transaction, dict) and isinstance(transaction.get("opl_route_command"), dict):
        return transaction["opl_route_command"]
    readback = mission.get("one_shot_migration_readback")
    if isinstance(readback, dict) and isinstance(readback.get("opl_route_command"), dict):
        return readback["opl_route_command"]
    return None


def _dispatch_execution_policy(readback: dict[str, Any]) -> str:
    if readback.get("surface_kind") == "paper_mission_drive_readback":
        return "paper_mission_drive_non_authority_candidate_and_ledger"
    if readback.get("surface_kind") == "paper_mission_materialized_readback":
        return "paper_mission_materialized_readback_no_write"
    return "paper_mission_no_write_dry_run"


def _recommended_domain_command(
    *,
    profile_ref: object,
    study_id: str,
    readback: dict[str, Any],
) -> str:
    inspect_command = (
        "uv run python -m med_autoscience.cli paper-mission inspect "
        f"--profile {profile_ref} --study-id {study_id} --format json"
    )
    if readback.get("surface_kind") == "paper_mission_drive_readback":
        output_root = _optional_text(readback.get("output_root"))
        output_root_arg = f" --output-root {output_root}" if output_root else ""
        return (
            "uv run python -m med_autoscience.cli paper-mission drive "
            f"--profile {profile_ref} --study-id {study_id}{output_root_arg} "
            "--format json # writes non-authority candidate package and "
            "consumption ledger only"
        )
    if readback.get("surface_kind") == "paper_mission_materialized_readback":
        return f"{inspect_command} # reads materialized PaperMissionRun"
    return inspect_command


def _paper_mission_dispatch_error(
    *,
    task: dict[str, Any],
    task_path: Path,
    reason: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_family_domain_handler_dispatch_receipt",
        "version": "mas-family-domain-handler.v1",
        "accepted": False,
        "task_id": str(task.get("task_id") or "unknown_task"),
        "task_kind": str(task.get("task_kind") or PAPER_MISSION_START_OR_RESUME_TASK_KIND),
        "source_task_ref": str(task_path),
        "reason": reason,
        "forbidden_domain_truth_write": False,
    }


def _build_one_shot_migration_cli_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    study_progress_payload: str | Path | None,
    domain_health_diagnostic_payload: str | Path | None,
    output_root: str | Path | None,
    source: str,
) -> dict[str, Any]:
    if study_progress_payload is None:
        raise ValueError("--study-progress-payload is required for --one-shot-migration")
    progress_path = Path(study_progress_payload).expanduser().resolve()
    dhd_path = (
        Path(domain_health_diagnostic_payload).expanduser().resolve()
        if domain_health_diagnostic_payload is not None
        else None
    )
    progress = _load_json_object(progress_path)
    dhd = _load_json_object(dhd_path) if dhd_path is not None else {}
    migration_pack = build_paper_mission_one_shot_migration_pack(
        study_progress_payloads=progress,
        domain_health_diagnostic_payload=dhd,
        profile_ref=str(profile_ref),
    )
    mission = paper_mission_by_study(migration_pack, study_id)
    readback = mission["one_shot_migration_readback"]
    candidate_manifest = paper_mission_canary_candidate_manifest(mission)
    candidate_artifact_delta = paper_mission_candidate_artifact_delta(mission)
    owner_decision_packet = paper_mission_owner_decision_packet(mission)
    output_manifest = (
        _write_one_shot_migration_outputs(
            output_root=Path(output_root),
            study_id=study_id,
            legacy_truth_import_pack=readback["legacy_truth_import_pack"],
            paper_mission_run=mission,
            default_readback=readback,
            candidate_manifest=candidate_manifest,
            candidate_artifact_delta=candidate_artifact_delta,
            owner_decision_packet=owner_decision_packet,
        )
        if output_root is not None
        else _no_write_output_manifest()
    )
    return {
        "surface_kind": "paper_mission_one_shot_migration_cli_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "inspect",
        "action_intent": "paper_mission/inspect",
        "source": source,
        "dry_run": True,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "study_progress_payload_ref": str(progress_path),
        **(
            {"domain_health_diagnostic_payload_ref": str(dhd_path)}
            if dhd_path is not None
            else {}
        ),
        "migration_pack": migration_pack,
        "legacy_truth_import_pack": readback["legacy_truth_import_pack"],
        "paper_mission_run": mission,
        "default_readback": readback,
        "candidate_manifest": candidate_manifest,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "authority_consume_readback": readback["consume_candidate_readback"],
        "consume_candidate_status": readback["consume_candidate_status"],
        **_transaction_readback_output_fields(
            _paper_mission_transaction_readback(
                mission_id=str(mission["mission_id"]),
                study_id=study_id,
                objective=str(mission["objective"]),
                paper_mission_command="inspect",
                study_root=Path(profile.studies_root) / study_id,
                mission=mission,
                authority_consume_readback=readback["consume_candidate_readback"],
            )
        ),
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_root(output_root),
            "writes_paper_body": False,
            "writes_candidate_workspace": output_root is not None,
            "dry_run_only": True,
            "forbidden_authority_writes": list(
                ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "output_manifest": output_manifest,
        "contract_validation": _validate_with_contract_if_available(mission),
        "cutover_proof": {
            "legacy_truth_import_pack_generated": True,
            "formal_paper_mission_run_generated": True,
            "mission_candidate_artifact_delta_generated": True,
            "owner_decision_packet_generated": True,
            "default_readback_surface": "PaperMissionRun",
            "legacy_blocker_controls_default_execution": False,
            "legacy_current_work_unit_role": "mission_input_constraint",
            "authority_materialized": False,
        },
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_one_shot_migration_outputs(
    *,
    output_root: Path,
    study_id: str,
    legacy_truth_import_pack: dict[str, Any],
    paper_mission_run: dict[str, Any],
    default_readback: dict[str, Any],
    candidate_manifest: dict[str, Any],
    candidate_artifact_delta: dict[str, Any],
    owner_decision_packet: dict[str, Any],
) -> dict[str, Any]:
    root = output_root.expanduser().resolve()
    _assert_safe_one_shot_output_root(root)
    study_root = root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "legacy_truth_import_pack": study_root / "legacy_truth_import_pack.json",
        "paper_mission_run": study_root / "paper_mission_run.json",
        "default_readback": study_root / "default_readback.json",
        "candidate_manifest": study_root / "candidate_manifest.json",
        "mission_candidate_artifact_delta": study_root
        / "mission_candidate_artifact_delta.json",
        "owner_decision_packet": study_root / "owner_decision_packet.json",
    }
    payloads = {
        "legacy_truth_import_pack": legacy_truth_import_pack,
        "paper_mission_run": paper_mission_run,
        "default_readback": default_readback,
        "candidate_manifest": {
            **candidate_manifest,
            "mission_candidate_sidecar_refs": {
                "paper_mission_run": str(outputs["paper_mission_run"]),
                "default_readback": str(outputs["default_readback"]),
                "mission_candidate_artifact_delta": str(
                    outputs["mission_candidate_artifact_delta"]
                ),
                "owner_decision_packet": str(outputs["owner_decision_packet"]),
            },
        },
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
    }
    written_files: list[str] = []
    for key, path in outputs.items():
        path.write_text(
            json.dumps(payloads[key], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written_files.append(str(path))
    return {
        "mode": "non_authority_candidate_package",
        "output_root": str(study_root),
        "written_files": written_files,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_yang_ops_candidate_package": _is_yang_ops_candidate_root(root),
        "candidate_manifest_ref": str(outputs["candidate_manifest"]),
        "mission_candidate_artifact_delta_ref": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet_ref": str(outputs["owner_decision_packet"]),
    }


def _write_materialized_candidate_package_outputs(
    *,
    output_root: Path,
    study_id: str,
    paper_mission_readback: dict[str, Any],
    candidate_manifest: dict[str, Any],
    candidate_artifact_delta: dict[str, Any],
    owner_decision_packet: dict[str, Any],
    foreground_owner_decision_summary: dict[str, Any],
    mission_executor_handoff: dict[str, Any],
    paper_facing_candidate_delta: dict[str, Any],
    owner_consumption_request: dict[str, Any],
    owner_blocker_packet: dict[str, Any],
    adopted_external_paper_delta_ref: str | None = None,
) -> dict[str, Any]:
    root = output_root.expanduser().resolve()
    _assert_safe_candidate_package_output_root(root)
    study_root = root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "package_manifest": study_root / "package_manifest.json",
        "paper_mission_readback": study_root / "paper_mission_readback.json",
        "candidate_manifest": study_root / "candidate_manifest.json",
        "mission_candidate_artifact_delta": study_root
        / "mission_candidate_artifact_delta.json",
        "owner_decision_packet": study_root / "owner_decision_packet.json",
        "foreground_owner_decision_summary": study_root
        / "foreground_owner_decision_summary.json",
        "mission_executor_handoff": study_root / "mission_executor_handoff.json",
        "paper_facing_candidate_delta": study_root
        / "paper_facing_candidate_delta.json",
        "owner_consumption_request": study_root / "owner_consumption_request.json",
        "owner_blocker_packet": study_root / "owner_blocker_packet.json",
        "submission_milestone_checklist": study_root
        / "submission_milestone_checklist.json",
    }
    paper_facing_artifact_outputs = {
        kind: study_root / "paper_facing_candidate_artifacts" / f"{kind}.json"
        for kind in _paper_facing_output_kinds(paper_facing_candidate_delta)
    }
    ai_owner_decision_sidecar_outputs = {
        kind: study_root / relpath
        for kind, relpath in AI_OWNER_DECISION_SIDECAR_REFS.items()
    }
    for path in paper_facing_artifact_outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for path in ai_owner_decision_sidecar_outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_refs = {
        "paper_mission_readback": str(outputs["paper_mission_readback"]),
        "mission_candidate_artifact_delta": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet": str(outputs["owner_decision_packet"]),
        "foreground_owner_decision_summary": str(
            outputs["foreground_owner_decision_summary"]
        ),
        "mission_executor_handoff": str(outputs["mission_executor_handoff"]),
        "paper_facing_candidate_delta": str(outputs["paper_facing_candidate_delta"]),
        "owner_consumption_request": str(outputs["owner_consumption_request"]),
        "owner_blocker_packet": str(outputs["owner_blocker_packet"]),
        "submission_milestone_checklist": str(
            outputs["submission_milestone_checklist"]
        ),
    }
    paper_facing_artifact_refs = {
        kind: str(path) for kind, path in paper_facing_artifact_outputs.items()
    }
    ai_owner_decision_sidecar_refs = {
        kind: str(path) for kind, path in ai_owner_decision_sidecar_outputs.items()
    }
    paper_facing_candidate_delta_payload = {
        **paper_facing_candidate_delta,
        "paper_facing_artifact_refs": paper_facing_artifact_refs,
        "paper_facing_outputs": [
            {
                **_mapping(item),
                **(
                    {"artifact_ref": paper_facing_artifact_refs[_mapping(item)["kind"]]}
                    if _mapping(item).get("kind") in paper_facing_artifact_refs
                    else {}
                ),
            }
            for item in paper_facing_candidate_delta.get("paper_facing_outputs", [])
            if isinstance(item, Mapping)
        ],
    }
    if adopted_external_paper_delta_ref is not None:
        paper_facing_candidate_delta_payload.update(
            {
                "adopted_external_paper_delta_ref": adopted_external_paper_delta_ref,
                "source_paper_facing_delta_ref": adopted_external_paper_delta_ref,
                "adopted_external_paper_delta_authority_boundary": (
                    adopted_external_paper_delta_authority_boundary()
                ),
            }
        )
    paper_facing_candidate_delta.clear()
    paper_facing_candidate_delta.update(paper_facing_candidate_delta_payload)
    owner_consumption_candidate_refs = {
        **sidecar_refs,
        "candidate_manifest": str(outputs["candidate_manifest"]),
        "package_manifest": str(outputs["package_manifest"]),
    }
    if adopted_external_paper_delta_ref is not None:
        owner_consumption_candidate_refs["adopted_external_paper_delta"] = (
            adopted_external_paper_delta_ref
        )
    owner_blocker_packet_payload = {
        **owner_blocker_packet,
        "candidate_refs": owner_consumption_candidate_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
    }
    _attach_candidate_manifest_to_next_command(
        owner_blocker_packet_payload,
        candidate_manifest_ref=str(outputs["package_manifest"]),
    )
    owner_blocker_packet.clear()
    owner_blocker_packet.update(owner_blocker_packet_payload)
    owner_consumption_request_payload = {
        **owner_consumption_request,
        "candidate_refs": owner_consumption_candidate_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        "consume_path": {
            **_mapping(owner_consumption_request.get("consume_path")),
            "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        },
    }
    _attach_candidate_manifest_to_next_command(
        owner_consumption_request_payload,
        candidate_manifest_ref=str(outputs["package_manifest"]),
    )
    owner_consumption_request.clear()
    owner_consumption_request.update(owner_consumption_request_payload)
    candidate_manifest_payload = {
        **candidate_manifest,
        "candidate_artifact_refs": _candidate_artifact_refs_with_paper_delta(
            candidate_manifest,
            paper_facing_candidate_delta_ref=str(
                outputs["paper_facing_candidate_delta"]
            ),
        ),
        "mission_candidate_sidecar_refs": sidecar_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
    }
    ai_owner_decision_sidecars = _mapping(
        owner_consumption_request_payload.get("ai_owner_decision_sidecars")
    ) or _mapping(owner_blocker_packet_payload.get("ai_owner_decision_sidecars"))
    payloads = {
        "paper_mission_readback": paper_mission_readback,
        "candidate_manifest": candidate_manifest_payload,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "foreground_owner_decision_summary": foreground_owner_decision_summary,
        "mission_executor_handoff": mission_executor_handoff,
        "paper_facing_candidate_delta": paper_facing_candidate_delta_payload,
        "owner_consumption_request": owner_consumption_request_payload,
        "owner_blocker_packet": owner_blocker_packet_payload,
        "submission_milestone_checklist": paper_mission_submission_milestone_checklist(
            output_kinds=list(paper_facing_artifact_outputs),
            owner_blocker_context=_optional_text(
                owner_blocker_packet_payload.get("status")
            )
            == "owner_blocker_candidate_ready",
        ),
    }
    if adopted_external_paper_delta_ref is not None:
        payloads["submission_milestone_checklist"][
            "adopted_external_paper_delta_ref"
        ] = adopted_external_paper_delta_ref
        payloads["submission_milestone_checklist"][
            "adopted_external_paper_delta_authority_boundary"
        ] = adopted_external_paper_delta_authority_boundary()
    payloads.update(
        {
            f"ai_owner_decision_sidecar::{kind}": {
                **_mapping(ai_owner_decision_sidecars.get(kind)),
                "sidecar_ref": ai_owner_decision_sidecar_refs[kind],
            }
            for kind in ai_owner_decision_sidecar_outputs
        }
    )
    payloads.update(
        {
            f"paper_facing_artifact::{kind}": materialized_paper_facing_candidate_artifact_payload(
                kind=kind,
                path=path,
                paper_facing_candidate_delta=paper_facing_candidate_delta_payload,
                mission_executor_handoff=mission_executor_handoff,
                forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
                forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
            )
            for kind, path in paper_facing_artifact_outputs.items()
        }
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": SUBMISSION_MILESTONE_KIND,
        "study_id": study_id,
        "mission_id": paper_mission_readback.get("mission_id"),
        "counts_as_paper_progress": True,
        "mission_executor_materialized": True,
        "candidate_content_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "authority_materialized_by_this_package": False,
        "source_refs": foreground_owner_decision_summary["input_refs"],
        "source_document_refs": paper_facing_candidate_delta_payload.get(
            "source_document_refs", []
        ),
        "current_terminal_decision": foreground_owner_decision_summary[
            "current_terminal_decision"
        ],
        "next_owner": foreground_owner_decision_summary["next_owner"],
        "blocked_reason": foreground_owner_decision_summary["blocked_reason"],
        "required_owner_action": foreground_owner_decision_summary[
            "required_owner_action"
        ],
        "artifact_refs": sidecar_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        **(
            {"adopted_external_paper_delta_ref": adopted_external_paper_delta_ref}
            if adopted_external_paper_delta_ref is not None
            else {}
        ),
        "mission_executor_handoff_ref": str(outputs["mission_executor_handoff"]),
        "paper_facing_candidate_delta_ref": str(
            outputs["paper_facing_candidate_delta"]
        ),
        "owner_consumption_request_ref": str(outputs["owner_consumption_request"]),
        "owner_blocker_packet_ref": str(outputs["owner_blocker_packet"]),
        "submission_milestone_checklist_ref": str(
            outputs["submission_milestone_checklist"]
        ),
        "paper_facing_artifact_refs": paper_facing_artifact_refs,
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
    }
    payloads["package_manifest"] = package_manifest
    written_files: list[str] = []
    file_sha256: dict[str, str] = {}
    all_outputs = {
        **outputs,
        **{
            f"paper_facing_artifact::{kind}": path
            for kind, path in paper_facing_artifact_outputs.items()
        },
        **{
            f"ai_owner_decision_sidecar::{kind}": path
            for kind, path in ai_owner_decision_sidecar_outputs.items()
        },
    }
    for key, path in all_outputs.items():
        text = json.dumps(payloads[key], ensure_ascii=False, indent=2) + "\n"
        path.write_text(text, encoding="utf-8")
        written_files.append(str(path))
        file_sha256[str(path)] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "mode": "non_authority_candidate_package",
        "output_root": str(study_root),
        "written_files": written_files,
        "file_sha256": file_sha256,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(root),
        "package_manifest_ref": str(outputs["package_manifest"]),
        "paper_mission_readback_ref": str(outputs["paper_mission_readback"]),
        "candidate_manifest_ref": str(outputs["candidate_manifest"]),
        "mission_candidate_artifact_delta_ref": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet_ref": str(outputs["owner_decision_packet"]),
        "foreground_owner_decision_summary_ref": str(
            outputs["foreground_owner_decision_summary"]
        ),
        "mission_executor_handoff_ref": str(outputs["mission_executor_handoff"]),
        "paper_facing_candidate_delta_ref": str(
            outputs["paper_facing_candidate_delta"]
        ),
        "owner_consumption_request_ref": str(outputs["owner_consumption_request"]),
        "owner_blocker_packet_ref": str(outputs["owner_blocker_packet"]),
        "submission_milestone_checklist_ref": str(
            outputs["submission_milestone_checklist"]
        ),
        "paper_facing_artifact_refs": paper_facing_artifact_refs,
        "ai_owner_decision_sidecar_refs": ai_owner_decision_sidecar_refs,
        **(
            {"adopted_external_paper_delta_ref": adopted_external_paper_delta_ref}
            if adopted_external_paper_delta_ref is not None
            else {}
        ),
    }


def _attach_candidate_manifest_to_next_command(
    payload: dict[str, Any],
    *,
    candidate_manifest_ref: str,
) -> None:
    command = payload.get("next_legal_command")
    if not isinstance(command, dict):
        return
    argv = command.get("argv_template")
    if not isinstance(argv, list):
        return
    command["argv_template"] = [
        candidate_manifest_ref if item == "<package_manifest_ref>" else item
        for item in argv
    ]


def _paper_facing_output_kinds(
    paper_facing_candidate_delta: Mapping[str, Any],
) -> list[str]:
    kinds: list[str] = []
    for item in paper_facing_candidate_delta.get("paper_facing_outputs", []):
        if not isinstance(item, Mapping):
            continue
        kind = _optional_text(item.get("kind"))
        if kind is not None and kind not in kinds:
            kinds.append(kind)
    return kinds


def _candidate_artifact_refs_with_paper_delta(
    candidate_manifest: Mapping[str, Any],
    *,
    paper_facing_candidate_delta_ref: str,
) -> list[str]:
    refs = [
        ref
        for ref in _text_list(candidate_manifest.get("candidate_artifact_refs"))
        if ref != paper_facing_candidate_delta_ref
    ]
    refs.append(paper_facing_candidate_delta_ref)
    return refs


def _mission_executor_handoff(
    *,
    readback: Mapping[str, Any],
    foreground_owner_decision_summary: Mapping[str, Any],
) -> dict[str, Any]:
    terminal_decision = _mapping(readback.get("stage_terminal_decision"))
    route_command = _mapping(readback.get("opl_route_command"))
    next_decision = _mapping(readback.get("next_owner_or_human_decision"))
    next_owner = _first_text(
        next_decision.get("next_owner"),
        foreground_owner_decision_summary.get("next_owner"),
        terminal_decision.get("next_owner"),
    )
    decision_kind = _optional_text(terminal_decision.get("decision_kind"))
    is_route_back = decision_kind == "route_back" or next_owner == "mission_executor"
    handoff_status = (
        "ready_for_mission_executor"
        if is_route_back
        else "not_routed_to_mission_executor"
    )
    return {
        "surface_kind": "paper_mission_executor_handoff",
        "schema_version": 1,
        "status": handoff_status,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "next_owner": next_owner,
        "handoff_reason": _first_text(
            terminal_decision.get("reason"),
            foreground_owner_decision_summary.get("blocked_reason"),
            readback.get("consume_candidate_status"),
        ),
        "route_back_evidence_ref": terminal_decision.get("route_back_evidence_ref"),
        "repair_scope": terminal_decision.get("repair_scope"),
        "target_stage_id": terminal_decision.get("target_stage_id")
        or terminal_decision.get("next_stage_id"),
        "current_terminal_decision": {
            "decision_kind": decision_kind,
            "status": terminal_decision.get("status"),
            "route_command": route_command.get("command_kind"),
            "source_terminal_decision_ref": route_command.get(
                "source_terminal_decision_ref"
            ),
        },
        "input_refs": foreground_owner_decision_summary.get("input_refs", {}),
        "runtime_touchpoint": foreground_owner_decision_summary.get(
            "runtime_touchpoint", {}
        ),
        "expected_paper_facing_outputs": [
            {
                "kind": "manuscript_patch_plan",
                "required": True,
                "authority_note": "candidate plan only until MAS consumes it",
            },
            {
                "kind": "claim_evidence_ledger_delta",
                "required": True,
                "authority_note": "candidate delta only until MAS consumes it",
            },
            {
                "kind": "figure_table_caption_delta",
                "required": True,
                "authority_note": "candidate delta only until MAS consumes it",
            },
            {
                "kind": "reviewer_gate_response_draft",
                "required": True,
                "authority_note": "candidate response only until MAS consumes it",
            },
            {
                "kind": "owner_decision_packet",
                "required": True,
                "authority_note": "submit through MAS authority consume path",
            },
        ],
        "resume_path": (
            "Mission executor should use this handoff to produce a paper-facing "
            "candidate artifact delta and owner decision packet; MAS remains the "
            "authority that accepts, rejects, routes back, blocks, or asks a human."
        ),
        "authority_boundary": {
            "candidate_is_authority": False,
            "authority_materialized_by_this_handoff": False,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_authorize_provider_admission": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
    }


def _write_paper_mission_consumption_ledger_outputs(
    *,
    output_root: Path,
    study_id: str,
    candidate_ref: str,
    authority_consume_readback: dict[str, Any],
    transaction_readback: dict[str, Any],
    mission_candidate: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    root = output_root.expanduser().resolve()
    _assert_safe_consumption_ledger_output_root(root)
    return write_paper_mission_consumption_ledger_outputs(
        output_root=root,
        study_id=study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        transaction_readback=transaction_readback,
        mission_candidate=mission_candidate,
        source=source,
        writes_yang_ops_consumption_ledger=_is_yang_ops_consumption_ledger_root(root),
        forbidden_authority_writes=CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )


def _foreground_owner_decision_summary(
    *,
    readback: Mapping[str, Any],
    candidate_manifest: Mapping[str, Any],
    candidate_artifact_delta: Mapping[str, Any],
    owner_decision_packet: Mapping[str, Any],
) -> dict[str, Any]:
    terminal_decision = _mapping(readback.get("stage_terminal_decision"))
    next_decision = _mapping(readback.get("next_owner_or_human_decision"))
    terminal_owner_gate = _mapping(readback.get("terminal_owner_gate"))
    owner_packet_next_owner = _optional_text(owner_decision_packet.get("next_owner"))
    candidate_next_owner = _optional_text(candidate_manifest.get("next_owner"))
    decision_next_owner = _optional_text(terminal_decision.get("next_owner"))
    selected_next_owner = _first_text(
        next_decision.get("next_owner"),
        terminal_owner_gate.get("owner"),
        decision_next_owner,
        owner_packet_next_owner,
        candidate_next_owner,
        "mas_authority_kernel",
    )
    blocked_reason = _first_text(
        terminal_owner_gate.get("blocked_reason"),
        terminal_decision.get("blocker_id"),
        terminal_decision.get("reason"),
        readback.get("consume_candidate_status"),
        "owner_decision_required",
    )
    required_owner_action = _required_owner_action(
        readback=readback,
        next_owner=selected_next_owner or "mas_authority_kernel",
        blocked_reason=blocked_reason or "owner_decision_required",
    )
    return {
        "surface_kind": "paper_mission_foreground_owner_decision_summary",
        "schema_version": 1,
        "candidate_is_authority": False,
        "governed_runtime_truth": False,
        "authority_materialized_by_this_packet": False,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "objective": readback.get("objective"),
        "input_refs": {
            "profile_ref": _mapping(readback.get("profile")).get("profile_ref"),
            "materialized_mission_ref": readback.get("materialized_mission_ref"),
            "candidate_manifest_ref": readback.get("candidate_manifest_ref"),
            "candidate_id": candidate_manifest.get("candidate_id"),
            "artifact_delta_ref": candidate_artifact_delta.get("artifact_ref"),
            "owner_decision_packet_id": owner_decision_packet.get("packet_id"),
            "source_readiness_refs": candidate_manifest.get("source_readiness_refs", []),
        },
        "current_terminal_decision": {
            "decision_kind": terminal_decision.get("decision_kind"),
            "status": terminal_decision.get("status"),
            "reason": terminal_decision.get("reason"),
            "next_owner": decision_next_owner,
            "next_stage_id": terminal_decision.get("next_stage_id"),
            "target_stage_id": terminal_decision.get("target_stage_id"),
            "next_work_unit": terminal_decision.get("next_work_unit"),
            "work_unit_id": terminal_decision.get("work_unit_id"),
            "repair_scope": terminal_decision.get("repair_scope"),
            "blocker_id": terminal_decision.get("blocker_id"),
            "unblock_condition": terminal_decision.get("unblock_condition"),
        },
        "runtime_touchpoint": {
            "opl_runtime_readback_status": readback.get("opl_runtime_readback_status"),
            "terminal_owner_gate": terminal_owner_gate or None,
            "next_owner_or_human_decision": next_decision,
        },
        "next_owner": selected_next_owner,
        "blocked_reason": blocked_reason,
        "required_owner_action": required_owner_action,
        "remaining_owner_gap": (
            "MAS/OPL owner surface must consume, route back, materialize a governed "
            "typed blocker or human gate, or accept an owner receipt before this "
            "candidate can be treated as runtime truth."
        ),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
    }


def _required_owner_action(
    *,
    readback: Mapping[str, Any],
    next_owner: str,
    blocked_reason: str,
) -> str:
    consume_status = _optional_text(readback.get("consume_candidate_status"))
    if consume_status == "accepted":
        return (
            f"{next_owner} must consume the accepted candidate through governed "
            "MAS authority or route it back with a governed receipt; foreground "
            "package alone does not authorize paper progress."
        )
    if consume_status == "typed_blocker":
        return (
            f"{next_owner} must materialize or reject the governed typed blocker "
            f"request for `{blocked_reason}`."
        )
    if consume_status == "human_gate":
        return (
            f"{next_owner} must record the governed human-gate decision for "
            f"`{blocked_reason}`."
        )
    return (
        f"{next_owner} must decide whether to consume, route back, block, or ask a "
        f"human question for `{blocked_reason}`."
    )


def _no_write_output_manifest() -> dict[str, Any]:
    return {
        "mode": "readback_only",
        "written_files": [],
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_yang_ops_candidate_package": False,
        "writes_yang_ops_consumption_ledger": False,
    }


def _assert_safe_candidate_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=None,
    )


def _assert_safe_one_shot_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH,
    )


def _assert_safe_candidate_package_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    )


def _assert_safe_consumption_ledger_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH,
    )


def _assert_safe_non_authority_output_root(
    path: Path,
    *,
    allowed_yang_relpath: Path | None,
) -> None:
    normalized_path = path.expanduser().resolve()
    normalized = normalized_path.as_posix()
    forbidden_parts = (
        "/studies/",
        "/runtime/",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "owner_receipt",
        "typed_blocker",
        "human_gate",
        "current_package",
        "runtime/queue",
        "provider_attempt",
    )
    if (
        _is_under_yang_workspace(normalized_path)
        and allowed_yang_relpath is not None
        and not _is_yang_ops_root(normalized_path, allowed_yang_relpath)
    ):
        raise ValueError(f"forbidden paper mission output root: {path}")
    if (
        _is_under_yang_workspace(normalized_path)
        and allowed_yang_relpath is None
        and not _is_yang_ops_non_authority_candidate_root(normalized_path)
    ):
        raise ValueError(f"forbidden paper mission output root: {path}")
    for forbidden in forbidden_parts:
        if forbidden in normalized:
            raise ValueError(f"forbidden paper mission output root: {path}")


def _is_yang_ops_candidate_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH)


def _is_yang_ops_candidate_package_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH)


def _is_yang_ops_non_authority_candidate_root(path: str | Path | None) -> bool:
    return (
        _is_yang_ops_candidate_root(path)
        or _is_yang_ops_candidate_package_root(path)
        or _is_yang_ops_consumption_ledger_root(path)
    )


def _is_yang_ops_consumption_ledger_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH)


def _is_yang_ops_root(path: str | Path | None, relpath: Path) -> bool:
    if path is None:
        return False
    normalized = Path(path).expanduser().resolve()
    try:
        relative = normalized.relative_to(YANG_WORKSPACE_ROOT)
    except ValueError:
        return False
    parts = relative.parts
    if len(parts) < len(relpath.parts) + 2:
        return False
    return Path(*parts[1 : 1 + len(relpath.parts)]) == relpath


def _is_under_yang_workspace(path: Path) -> bool:
    try:
        path.relative_to(YANG_WORKSPACE_ROOT)
    except ValueError:
        return False
    return True


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", required=True)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--format", choices=("json",), default="json")


def _add_dry_run_only(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")


def _action_intent(paper_mission_command: str) -> str:
    if paper_mission_command in {"start", "resume"}:
        return PAPER_MISSION_START_OR_RESUME_TASK_KIND
    if paper_mission_command == "consume-candidate":
        return "paper_mission/consume_candidate"
    if paper_mission_command == "package-candidate":
        return "paper_mission/package_candidate"
    if paper_mission_command == "drive":
        return "paper_mission/drive"
    return "paper_mission/inspect"


def _objective_for_command(*, paper_mission_command: str, objective: str | None) -> str:
    explicit = _optional_text(objective)
    if explicit:
        return explicit
    defaults = {
        "inspect": "inspect current paper mission entry",
        "start": "start or resume next paper-facing mission objective",
        "resume": "resume current paper-facing mission objective",
        "consume-candidate": "consume candidate paper mission output",
        "drive": "drive current paper mission to terminal decision and OPL route handoff",
    }
    return defaults.get(paper_mission_command, "paper mission no-write plan")


def _mission_id(
    *,
    mission_id: str | None,
    study_id: str,
    objective: str,
    paper_mission_command: str,
) -> str:
    explicit = _optional_text(mission_id)
    if explicit:
        return explicit
    return f"paper-mission::{study_id}::{_slug(objective)}::{paper_mission_command}-dry-run"


def _paper_mission_run_candidate(
    *,
    mission_id: str,
    study_id: str,
    objective: str,
    paper_mission_command: str,
    profile_ref: str | Path,
    study_root: Path,
    candidate_ref: str | None,
    authority_consume_readback: dict[str, Any] | None = None,
    paper_mission_transaction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_refs = [
        {"ref_id": "profile", "ref_kind": "profile_ref", "uri": str(profile_ref)},
        {"ref_id": "study_root", "ref_kind": "workspace_path", "uri": str(study_root)},
    ]
    if candidate_ref is not None:
        source_refs.append(
            {"ref_id": "candidate", "ref_kind": "candidate_ref", "uri": candidate_ref}
        )
    consume_result = (
        dict(authority_consume_readback.get("consume_result") or {})
        if authority_consume_readback is not None
        else {"status": "not_consumed"}
    )
    mission_state = _mission_state_for_consume_result(consume_result)
    artifact_delta_status = (
        "candidate_consumed"
        if consume_result.get("status") == "accepted"
        else "planned"
        if consume_result.get("status") == "not_consumed"
        else "candidate_consume_result_recorded"
    )
    transaction = paper_mission_transaction or _placeholder_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        objective=objective,
        paper_mission_command=paper_mission_command,
        study_root=study_root,
        consume_result=consume_result,
    )
    return {
        "schema_version": PAPER_MISSION_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": mission_state,
        "artifact_delta_ledger": [
            {
                "delta_id": f"{paper_mission_command}_no_write_plan",
                "artifact_ref": str(study_root / "paper"),
                "delta_kind": "no_write_plan",
                "status": artifact_delta_status,
            }
        ],
        "source_refs": source_refs,
        "paper_audit_pack": _paper_audit_pack_for_cli_readback(
            study_id=study_id,
            paper_mission_command=paper_mission_command,
            source_refs=source_refs,
        ),
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            },
            {
                "touchpoint_id": "controller_decisions",
                "owner": "MedAutoScience",
                "surface": "controller_decisions/latest.json",
                "status": "not_touched",
            },
            {
                "touchpoint_id": "runtime_provider_attempts",
                "owner": "one-person-lab",
                "surface": "runtime queue/provider attempts",
                "status": "not_touched",
            },
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        },
        "consume_result": consume_result,
        "claim_permissions": {
            "can_claim_artifact_delta": False,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": ["paper_mission_no_write_plan"],
        },
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "transaction_state": _transaction_state(transaction),
    }


def _paper_mission_transaction_readback(
    *,
    mission_id: str,
    study_id: str,
    objective: str,
    paper_mission_command: str,
    study_root: Path,
    mission: dict[str, Any] | None,
    candidate: str | Path | None = None,
    authority_consume_readback: dict[str, Any] | None = None,
    transaction_override: dict[str, Any] | None = None,
    transaction_source_override: str | None = None,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any]:
    transaction = _first_mapping(
        _mapping(transaction_override),
        _mapping((authority_consume_readback or {}).get("paper_mission_transaction")),
        _mapping((mission or {}).get("paper_mission_transaction")),
        _transaction_from_materialized_legacy_mission(
            mission=mission,
            study_id=study_id,
        ),
        _candidate_manifest_transaction(candidate),
    )
    source = (
        transaction_source_override
        if transaction_override
        else "materialized_paper_mission_run"
        if transaction
        else "placeholder_no_write"
    )
    if not transaction:
        consume_result = (
            _mapping((authority_consume_readback or {}).get("consume_result"))
            or _mapping((mission or {}).get("consume_result"))
            or {"status": "not_consumed"}
        )
        transaction = _placeholder_paper_mission_transaction(
            mission_id=mission_id,
            study_id=study_id,
            objective=objective,
            paper_mission_command=paper_mission_command,
            study_root=study_root,
            consume_result=consume_result,
        )
    elif mission is None and candidate is not None:
        source = "candidate_manifest"

    owner_answer_readback_prefill = (
        _owner_answer_readback_for_route_back_without_artifact_delta(transaction)
        if transaction_source_override != "paper_mission_consumption_ledger"
        else {}
    )
    if owner_answer_readback_prefill:
        owner_answer_transaction = _mapping(
            owner_answer_readback_prefill.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            transaction = owner_answer_transaction

    readback = {
        "surface_kind": "paper_mission_transaction_pickup_readback",
        "schema_version": 1,
        "contract_ref": "contracts/paper_mission_transaction_contract.json",
        "contract_version": "paper-mission-transaction.v1",
        "source": source,
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "opl_runtime_carrier": paper_mission_opl_runtime_carrier(transaction),
        "transaction_state": _transaction_state(transaction),
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "validation": _validate_paper_mission_transaction_if_available(transaction),
    }
    readback = attach_opl_runtime_carrier_readback(
        readback=readback,
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    terminal_owner_gate = _terminal_owner_gate_from_transaction_readback(readback)
    readback["terminal_owner_gate"] = terminal_owner_gate or None
    terminal_gate_authority_readback = terminal_owner_gate_authority_readback(
        terminal_owner_gate
    )
    owner_answer_readback = terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate=terminal_owner_gate,
        paper_mission_transaction=transaction,
        artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
        paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
    ) if not owner_answer_readback_prefill else dict(owner_answer_readback_prefill)
    terminal_gate_authority_readback = terminal_owner_gate_authority_consume_readback(
        terminal_owner_gate_authority_readback=terminal_gate_authority_readback,
        owner_answer_readback=owner_answer_readback,
    )
    if owner_answer_readback and transaction_source_override != "paper_mission_consumption_ledger":
        owner_answer_transaction = _mapping(
            owner_answer_readback.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            readback["source"] = "terminal_owner_gate_owner_answer"
            readback["paper_mission_transaction"] = owner_answer_transaction
            readback["stage_terminal_decision"] = _mapping(
                owner_answer_transaction.get("stage_terminal_decision")
            )
            readback["opl_route_command"] = _mapping(
                owner_answer_transaction.get("opl_route_command")
            )
            readback["opl_runtime_carrier"] = paper_mission_opl_runtime_carrier(
                owner_answer_transaction
            )
            readback["transaction_state"] = _transaction_state(owner_answer_transaction)
            readback["consume_candidate_status_override"] = "route_back"
    readback["terminal_owner_gate_authority_readback"] = (
        terminal_gate_authority_readback or None
    )
    readback["terminal_owner_gate_owner_answer_readback"] = (
        owner_answer_readback or None
    )
    owner_answer_next_decision = (
        {}
        if transaction_source_override == "paper_mission_consumption_ledger"
        else terminal_owner_gate_owner_answer_next_decision(owner_answer_readback)
    )
    readback["next_owner_or_human_decision"] = (
        owner_answer_next_decision
        or _next_owner_or_human_decision_from_transaction_readback(
            readback=readback,
            terminal_owner_gate=terminal_owner_gate,
        )
    )
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    if owner_answer:
        readback["semantic_progress_signature"] = owner_answer.get(
            "semantic_progress_signature"
        )
        readback["route_back_budget"] = owner_answer.get("route_back_budget")
        readback["mission_executor_fallback_action"] = owner_answer.get(
            "mission_executor_fallback_action"
        )
        readback["carry_forward_risk_receipt_ref"] = owner_answer.get(
            "carry_forward_risk_receipt_ref"
        )
    return readback


def _owner_answer_readback_for_route_back_without_artifact_delta(
    transaction: Mapping[str, Any],
) -> dict[str, Any]:
    if _mapping_list(transaction.get("artifact_delta_refs")):
        return {}
    terminal_owner_gate = terminal_owner_gate_from_stage_terminal_decision(
        stage_terminal_decision=_mapping(transaction.get("stage_terminal_decision")),
        paper_mission_transaction=transaction,
    )
    if not terminal_owner_gate:
        return {}
    return terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate=terminal_owner_gate,
        paper_mission_transaction=transaction,
        artifact_delta_refs=[],
        paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
    )


def _mission_state_for_materialized_readback(
    *,
    mission: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    consumption_ledger_readback: Mapping[str, Any] | None,
) -> str:
    if consumption_ledger_readback is not None:
        status = _optional_text(consumption_ledger_readback.get("consume_candidate_status"))
        if status in {"typed_blocker", "human_gate"}:
            return "stable_blocker" if status == "typed_blocker" else "waiting_human_decision"
        if status in {"route_back", "rejected"}:
            return "route_back"
        return "consumed"
    if transaction_readback.get("consume_candidate_status_override") == "route_back":
        return "route_back"
    return _optional_text(mission.get("mission_state")) or "planned"


def _consume_result_for_consumption_ledger_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    status = _optional_text(readback.get("consume_candidate_status"))
    selected_outcome = _optional_text(readback.get("selected_outcome"))
    if status == "route_back":
        result_status = "route_back"
    elif status == "human_gate":
        result_status = "human_gate"
    elif status == "typed_blocker":
        result_status = "typed_blocker"
    elif status == "rejected":
        result_status = "rejected"
    elif status:
        result_status = "accepted"
    else:
        result_status = "not_consumed"
    return {
        "status": result_status,
        "outcome": status or selected_outcome or result_status,
        "authority_materialized": False,
    }


def _consume_candidate_status_for_transaction_readback(
    *,
    transaction_readback: Mapping[str, Any],
    authority_consume_readback: Mapping[str, Any] | None,
) -> str:
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    decision_kind = _optional_text(decision.get("decision_kind"))
    if decision_kind == "route_back":
        return "route_back"
    if decision_kind == "typed_blocker":
        return "typed_blocker"
    if decision_kind == "human_gate":
        return "human_gate"
    if decision_kind == "mission_complete":
        return "mission_complete"
    authority = _mapping(authority_consume_readback)
    selected = _optional_text(authority.get("selected_outcome"))
    status = _optional_text(authority.get("status"))
    if decision_kind in {"advance", "continue_same_stage"}:
        return selected or status or "accepted"
    if selected == "typed_blocker_required" or status == "typed_blocker_required":
        return "typed_blocker"
    if selected == "human_gate_required" or status == "human_gate_required":
        return "human_gate"
    if selected == "rejected_candidate" or status == "rejected_candidate":
        return "rejected"
    return selected or status or "not_consumed"


def _next_owner_decision_for_consumption_ledger_readback(
    *,
    readback: Mapping[str, Any],
    fallback: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(readback.get("stage_terminal_decision"))
    handoff = _mapping(readback.get("opl_route_handoff"))
    route = _mapping(readback.get("opl_route_command"))
    next_owner = _first_text(
        decision.get("next_owner"),
        handoff.get("next_owner"),
        readback.get("next_owner"),
        fallback.get("next_owner"),
    )
    status = _first_text(
        readback.get("consume_candidate_status"),
        readback.get("selected_outcome"),
        decision.get("decision_kind"),
        fallback.get("summary"),
    )
    return {
        "kind": (
            "human_decision"
            if _optional_text(decision.get("decision_kind")) == "human_gate"
            else "owner_or_route"
        ),
        "next_owner": next_owner,
        "human_decision_required": (
            _optional_text(decision.get("decision_kind")) == "human_gate"
        ),
        "summary": status,
        **(
            {"route_command": route_command}
            if (route_command := _optional_text(route.get("command_kind"))) is not None
            else {}
        ),
        **(
            {"route_target": route_target}
            if (
                route_target := _first_text(
                    route.get("target"),
                    route.get("route_target"),
                    handoff.get("route_target"),
                )
            )
            is not None
            else {}
        ),
        **(
            {"opl_route_handoff_ref": handoff_ref}
            if (handoff_ref := _optional_text(handoff.get("source_ref"))) is not None
            else {}
        ),
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }


def _paper_audit_pack_for_cli_readback(
    *,
    study_id: str,
    paper_mission_command: str,
    source_refs: list[dict[str, str]],
) -> dict[str, Any]:
    refs = list(source_refs) or [
        {
            "ref_id": "paper_mission_cli_readback",
            "ref_kind": "paper_mission_cli_readback",
            "uri": f"paper-mission-cli://{study_id}/{paper_mission_command}",
        }
    ]
    return {
        family: {
            "status": "refs_only_no_write_readback",
            "refs": refs,
        }
        for family in PAPER_AUDIT_PACK_FAMILIES
    }


def _transaction_readback_output_fields(
    transaction_readback: dict[str, Any],
) -> dict[str, Any]:
    return {
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        "stage_terminal_decision": transaction_readback["stage_terminal_decision"],
        "opl_route_command": transaction_readback["opl_route_command"],
        "opl_runtime_carrier": transaction_readback["opl_runtime_carrier"],
        "opl_runtime_carrier_readback": transaction_readback[
            "opl_runtime_carrier_readback"
        ],
        "opl_runtime_readback_status": transaction_readback[
            "opl_runtime_readback_status"
        ],
        "terminal_owner_gate": transaction_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": transaction_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": transaction_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "semantic_progress_signature": transaction_readback.get(
            "semantic_progress_signature"
        ),
        "route_back_budget": transaction_readback.get("route_back_budget"),
        "mission_executor_fallback_action": transaction_readback.get(
            "mission_executor_fallback_action"
        ),
        "carry_forward_risk_receipt_ref": transaction_readback.get(
            "carry_forward_risk_receipt_ref"
        ),
        "next_owner_or_human_decision": transaction_readback[
            "next_owner_or_human_decision"
        ],
        "transaction_state": transaction_readback["transaction_state"],
        **(
            {
                "consume_candidate_status_override": transaction_readback[
                    "consume_candidate_status_override"
                ]
            }
            if transaction_readback.get("consume_candidate_status_override")
            else {}
        ),
        "paper_mission_transaction_readback": transaction_readback,
    }


def _terminal_owner_gate_from_transaction_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    carrier_gate = terminal_owner_gate_from_carrier_readback(
        _mapping(readback.get("opl_runtime_carrier_readback"))
    )
    if carrier_gate:
        return carrier_gate
    return terminal_owner_gate_from_stage_terminal_decision(
        stage_terminal_decision=_mapping(readback.get("stage_terminal_decision")),
        paper_mission_transaction=_mapping(readback.get("paper_mission_transaction")),
    )


def _next_owner_or_human_decision_from_transaction_readback(
    *,
    readback: Mapping[str, Any],
    terminal_owner_gate: Mapping[str, Any],
) -> dict[str, Any]:
    if terminal_owner_gate:
        return terminal_owner_gate_next_decision(terminal_owner_gate)
    return stage_terminal_next_owner_or_human_decision(
        stage_terminal_decision=_mapping(readback.get("stage_terminal_decision")),
        opl_route_command=_mapping(readback.get("opl_route_command")),
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


def _next_stage_id_for_materialized(stage_id: str) -> str:
    if stage_id == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if stage_id == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


def _transaction_state(transaction: dict[str, Any]) -> str:
    explicit = _optional_text(transaction.get("transaction_state"))
    if explicit:
        return explicit
    terminal_status = _optional_text(
        _mapping(transaction.get("stage_terminal_decision")).get("status")
    )
    return terminal_status or "not_materialized"


def _validate_paper_mission_transaction_if_available(
    transaction: dict[str, Any],
) -> dict[str, Any]:
    try:
        from med_autoscience.paper_mission_transaction import PaperMissionTransaction
    except ModuleNotFoundError:
        return {
            "status": "pending_contract_module_not_available",
            "validator": (
                "med_autoscience.paper_mission_transaction.PaperMissionTransaction"
            ),
        }
    try:
        PaperMissionTransaction.from_payload(transaction)
    except Exception as exc:  # pragma: no cover - exact type belongs to contract lane.
        return {
            "status": "failed",
            "validator": (
                "med_autoscience.paper_mission_transaction.PaperMissionTransaction"
            ),
            "error": str(exc),
        }
    return {
        "status": "validated",
        "validator": "med_autoscience.paper_mission_transaction.PaperMissionTransaction",
    }


def _mission_state_for_consume_result(consume_result: dict[str, Any]) -> str:
    status = consume_result.get("status")
    if status == "accepted":
        return "consumed"
    if status == "route_back":
        return "route_back"
    if status == "typed_blocker":
        return "stable_blocker"
    if status == "human_gate":
        return "waiting_human_decision"
    if status == "rejected":
        return "route_back"
    return "planned"


def _mutation_policy(*, paper_mission_command: str) -> dict[str, Any]:
    return {
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang": False,
        "writes_paper_body": False,
        "writes_candidate_workspace": False,
        "dry_run_only": paper_mission_command != "inspect",
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _validate_with_contract_if_available(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        from med_autoscience.paper_mission_run import PaperMissionRun
    except ModuleNotFoundError:
        return {
            "status": "pending_contract_module_not_available",
            "required_commit": PAPER_MISSION_CONTRACT_COMMIT,
            "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
        }
    try:
        PaperMissionRun.from_payload(payload)
    except Exception as exc:  # pragma: no cover - exact error type lives in contract lane.
        return {
            "status": "failed",
            "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
            "error": str(exc),
        }
    return {
        "status": "validated",
        "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
    }


def _first_mapping(*values: dict[str, Any]) -> dict[str, Any]:
    for value in values:
        if value:
            return value
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    items: list[str] = []
    for item in value:
        text = _optional_text(item)
        if text is not None:
            items.append(text)
    return items


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug[:64] or "paper-mission"


__all__ = [
    "PAPER_MISSION_START_OR_RESUME_TASK_KIND",
    "build_paper_mission_readback",
    "handle_paper_mission_command",
    "paper_mission_domain_handler_dispatch_receipt",
    "register_paper_mission_parsers",
]
