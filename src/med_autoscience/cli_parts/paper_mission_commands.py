from __future__ import annotations

import argparse
import hashlib
import json
import re
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
    terminal_owner_gate_next_decision,
)
from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


PAPER_MISSION_CONTRACT_REF = "contracts/paper_mission_run_contract.json"
PAPER_MISSION_CONTRACT_VERSION = "paper-mission-run.v1"
PAPER_MISSION_CONTRACT_COMMIT = "a410db5c0c874187c8b1ddecee79c2e00c8fe691"
PAPER_MISSION_START_OR_RESUME_TASK_KIND = "paper_mission/start_or_resume"
YANG_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang")
PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_one_shot_migration"
)
PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_candidate_package"
)
PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_consumption_ledger"
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
    consume_parser.add_argument("--candidate", required=True)
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
        one_shot_migration=bool(getattr(args, "one_shot_migration", False)),
        study_progress_payload=getattr(args, "study_progress_payload", None),
        domain_health_diagnostic_payload=getattr(
            args,
            "domain_health_diagnostic_payload",
            None,
        ),
        output_root=getattr(args, "output_root", None),
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
    one_shot_migration: bool = False,
    study_progress_payload: str | Path | None = None,
    domain_health_diagnostic_payload: str | Path | None = None,
    output_root: str | Path | None = None,
    dry_run: bool = False,
    source: str = "unknown",
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
    candidate_ref = str(candidate) if candidate is not None else None
    authority_consume_readback = (
        consume_paper_mission_candidate(candidate)
        if paper_mission_command == "consume-candidate" and candidate is not None
        else None
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=selected_mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
        study_root=Path(profile.studies_root) / study_id,
        mission=None,
        candidate=candidate,
        authority_consume_readback=authority_consume_readback,
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
            candidate=candidate,
            authority_consume_readback=authority_consume_readback,
        )
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
            candidate_ref=str(candidate),
            authority_consume_readback=authority_consume_readback,
            transaction_readback=transaction_readback,
            mission_candidate=mission_candidate,
            source=source,
        )
        if (
            paper_mission_command == "consume-candidate"
            and output_root is not None
            and candidate is not None
            and authority_consume_readback is not None
        )
        else None
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
    readback = build_paper_mission_readback(
        profile=profile,
        profile_ref=Path(str(profile_ref)),
        study_id=study_id,
        paper_mission_command=str(payload.get("paper_mission_command") or "start"),
        objective=_optional_text(payload.get("objective")),
        mission_id=_optional_text(payload.get("mission_id")),
        candidate=_optional_text(payload.get("candidate")),
        one_shot_migration=bool(payload.get("one_shot_migration", False)),
        study_progress_payload=_optional_text(payload.get("study_progress_payload")),
        domain_health_diagnostic_payload=_optional_text(
            payload.get("domain_health_diagnostic_payload")
        ),
        output_root=_optional_text(payload.get("output_root")),
        dry_run=bool(payload.get("dry_run", True)),
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


def _build_materialized_mission_readback_if_available(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    dry_run: bool,
    source: str,
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
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=str(mission["mission_id"]),
        study_id=resolved_study_id,
        objective=str(mission["objective"]),
        paper_mission_command=paper_mission_command,
        study_root=resolved_study_root,
        mission=mission,
        authority_consume_readback=None,
    )
    mission = {
        **mission,
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
    }
    validation = _validate_with_contract_if_available(mission)
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
        "materialized_mission_ref": str(mission_path),
        **_transaction_readback_output_fields(transaction_readback),
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
        "consume_candidate_status": transaction_readback.get(
            "consume_candidate_status_override"
        )
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


def _build_materialized_candidate_package_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    source: str,
) -> dict[str, Any]:
    if output_root is None:
        raise ValueError("--output-root is required for package-candidate")
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
    output_manifest = _write_materialized_candidate_package_outputs(
        output_root=Path(output_root),
        study_id=str(readback["study_id"]),
        paper_mission_readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
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
    if readback.get("surface_kind") == "paper_mission_materialized_readback":
        return "paper_mission_materialized_readback_no_write"
    return "paper_mission_no_write_dry_run"


def _recommended_domain_command(
    *,
    profile_ref: object,
    study_id: str,
    readback: dict[str, Any],
) -> str:
    command = (
        "uv run python -m med_autoscience.cli paper-mission inspect "
        f"--profile {profile_ref} --study-id {study_id} --format json"
    )
    if readback.get("surface_kind") == "paper_mission_materialized_readback":
        return f"{command} # reads materialized PaperMissionRun"
    return command


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
    }
    sidecar_refs = {
        "paper_mission_readback": str(outputs["paper_mission_readback"]),
        "mission_candidate_artifact_delta": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet": str(outputs["owner_decision_packet"]),
        "foreground_owner_decision_summary": str(
            outputs["foreground_owner_decision_summary"]
        ),
    }
    candidate_manifest_payload = {
        **candidate_manifest,
        "mission_candidate_sidecar_refs": sidecar_refs,
    }
    payloads = {
        "paper_mission_readback": paper_mission_readback,
        "candidate_manifest": candidate_manifest_payload,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "foreground_owner_decision_summary": foreground_owner_decision_summary,
    }
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "study_id": study_id,
        "mission_id": paper_mission_readback.get("mission_id"),
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "authority_materialized_by_this_package": False,
        "source_refs": foreground_owner_decision_summary["input_refs"],
        "current_terminal_decision": foreground_owner_decision_summary[
            "current_terminal_decision"
        ],
        "next_owner": foreground_owner_decision_summary["next_owner"],
        "blocked_reason": foreground_owner_decision_summary["blocked_reason"],
        "required_owner_action": foreground_owner_decision_summary[
            "required_owner_action"
        ],
        "artifact_refs": sidecar_refs,
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
    }
    payloads["package_manifest"] = package_manifest
    written_files: list[str] = []
    file_sha256: dict[str, str] = {}
    for key, path in outputs.items():
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
) -> dict[str, Any]:
    transaction = _first_mapping(
        _mapping((mission or {}).get("paper_mission_transaction")),
        _transaction_from_materialized_legacy_mission(
            mission=mission,
            study_id=study_id,
        ),
        _candidate_manifest_transaction(candidate),
        _mapping((authority_consume_readback or {}).get("paper_mission_transaction")),
    )
    source = "materialized_paper_mission_run" if transaction else "placeholder_no_write"
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
        enable_opl_live_probe=paper_mission_command != "consume-candidate",
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
    )
    terminal_gate_authority_readback = terminal_owner_gate_authority_consume_readback(
        terminal_owner_gate_authority_readback=terminal_gate_authority_readback,
        owner_answer_readback=owner_answer_readback,
    )
    if owner_answer_readback:
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
    readback["next_owner_or_human_decision"] = (
        terminal_owner_gate_owner_answer_next_decision(owner_answer_readback)
        or _next_owner_or_human_decision_from_transaction_readback(
        readback=readback,
        terminal_owner_gate=terminal_owner_gate,
        )
    )
    return readback


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
    return terminal_owner_gate_from_carrier_readback(
        _mapping(readback.get("opl_runtime_carrier_readback"))
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


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


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
