from __future__ import annotations

from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _optional_text,
    _slug,
)

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


def no_write_output_manifest() -> dict[str, Any]:
    return {
        "mode": "readback_only",
        "written_files": [],
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_yang_ops_candidate_package": False,
        "writes_yang_ops_consumption_ledger": False,
    }


def action_intent(paper_mission_command: str) -> str:
    if paper_mission_command in {"start", "resume"}:
        return PAPER_MISSION_START_OR_RESUME_TASK_KIND
    if paper_mission_command == "consume-candidate":
        return "paper_mission/consume_candidate"
    if paper_mission_command == "package-candidate":
        return "paper_mission/package_candidate"
    if paper_mission_command == "drive":
        return "paper_mission/drive"
    if paper_mission_command == "terminalize-stage":
        return "paper_mission/terminalize_stage"
    if paper_mission_command == "typed-blocker-resolution":
        return "paper_mission/typed_blocker_resolution"
    return "paper_mission/inspect"


def objective_for_command(*, paper_mission_command: str, objective: str | None) -> str:
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


def mission_id(
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


def mutation_policy(*, paper_mission_command: str) -> dict[str, Any]:
    return {
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang": False,
        "writes_paper_body": False,
        "writes_candidate_workspace": False,
        "dry_run_only": paper_mission_command != "inspect",
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def validate_with_contract_if_available(payload: dict[str, Any]) -> dict[str, Any]:
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


__all__ = [
    "FORBIDDEN_AUTHORITY_WRITES",
    "PAPER_MISSION_CONTRACT_COMMIT",
    "PAPER_MISSION_CONTRACT_REF",
    "PAPER_MISSION_CONTRACT_VERSION",
    "PAPER_MISSION_START_OR_RESUME_TASK_KIND",
    "action_intent",
    "mission_id",
    "mutation_policy",
    "no_write_output_manifest",
    "objective_for_command",
    "validate_with_contract_if_available",
]
