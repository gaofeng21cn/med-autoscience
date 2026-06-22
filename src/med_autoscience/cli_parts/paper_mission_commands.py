from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


PAPER_MISSION_CONTRACT_REF = "contracts/paper_mission_run_contract.json"
PAPER_MISSION_CONTRACT_VERSION = "paper-mission-run.v1"
PAPER_MISSION_CONTRACT_COMMIT = "a410db5c0c874187c8b1ddecee79c2e00c8fe691"
PAPER_MISSION_START_OR_RESUME_TASK_KIND = "paper_mission/start_or_resume"

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


def register_paper_mission_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("paper-mission")
    mission_subparsers = parser.add_subparsers(dest="paper_mission_command", required=True)

    inspect_parser = mission_subparsers.add_parser("inspect")
    _add_common_args(inspect_parser)

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
    _add_dry_run_only(consume_parser)


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
    dry_run: bool = False,
    source: str = "unknown",
) -> dict[str, Any]:
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
    mission_candidate = _paper_mission_run_candidate(
        mission_id=selected_mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
        profile_ref=profile_ref,
        study_root=Path(profile.studies_root) / study_id,
        candidate_ref=candidate_ref,
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
        "mission_id": selected_mission_id,
        "objective": selected_objective,
        **({"candidate_ref": candidate_ref} if candidate_ref is not None else {}),
        "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "paper_mission_run_candidate": mission_candidate,
        "contract_validation": _validate_with_contract_if_available(mission_candidate),
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "dry_run_no_write",
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
            "execution_policy": "paper_mission_no_write_dry_run",
            "recommended_domain_command": (
                f"uv run python -m med_autoscience.cli paper-mission inspect "
                f"--profile {profile_ref} --study-id {study_id} --format json"
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
    return "paper_mission/inspect"


def _objective_for_command(*, paper_mission_command: str, objective: str | None) -> str:
    explicit = _optional_text(objective)
    if explicit:
        return explicit
    defaults = {
        "inspect": "inspect current paper mission entry",
        "start": "start or resume next paper-facing mission objective",
        "resume": "resume current paper-facing mission objective",
        "consume-candidate": "dry-run consume candidate paper mission output",
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
) -> dict[str, Any]:
    source_refs = [
        {"ref_id": "profile", "ref_kind": "profile_ref", "uri": str(profile_ref)},
        {"ref_id": "study_root", "ref_kind": "workspace_path", "uri": str(study_root)},
    ]
    if candidate_ref is not None:
        source_refs.append(
            {"ref_id": "candidate", "ref_kind": "candidate_ref", "uri": candidate_ref}
        )
    return {
        "schema_version": PAPER_MISSION_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": "planned",
        "artifact_delta_ledger": [
            {
                "delta_id": f"{paper_mission_command}_no_write_plan",
                "artifact_ref": str(study_root / "paper"),
                "delta_kind": "no_write_plan",
                "status": "planned",
            }
        ],
        "source_refs": source_refs,
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
        "consume_result": {"status": "not_consumed"},
        "claim_permissions": {
            "can_claim_artifact_delta": False,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": ["paper_mission_no_write_plan"],
        },
    }


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
