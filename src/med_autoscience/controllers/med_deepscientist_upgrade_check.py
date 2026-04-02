from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from med_autoscience.med_deepscientist_repo_manifest import inspect_med_deepscientist_repo_manifest
from med_autoscience.doctor import build_doctor_report, overlay_request_from_profile
from med_autoscience.overlay import describe_medical_overlay
from med_autoscience.profiles import WorkspaceProfile


def _run_git(repo_root: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, output


def _resolve_comparison_target(manifest_info: dict[str, Any]) -> tuple[str, str, str]:
    upstream_remote_name = str(manifest_info.get("upstream_remote_name") or "").strip()
    upstream_branch = str(manifest_info.get("upstream_branch") or "").strip() or "main"
    upstream_ref = str(manifest_info.get("upstream_ref") or "").strip()
    is_controlled_fork = bool(manifest_info.get("is_controlled_fork"))

    if upstream_ref:
        return upstream_remote_name or upstream_ref.split("/", 1)[0], upstream_branch, upstream_ref
    if upstream_remote_name:
        return upstream_remote_name, upstream_branch, f"{upstream_remote_name}/{upstream_branch}"
    if is_controlled_fork:
        return "upstream", "main", "upstream/main"
    return "origin", "main", "origin/main"


def inspect_med_deepscientist_repo(*, repo_root: Path | None, refresh: bool = False) -> dict[str, Any]:
    manifest_info = inspect_med_deepscientist_repo_manifest(repo_root)
    comparison_remote_name, comparison_branch, comparison_ref = _resolve_comparison_target(manifest_info)
    if repo_root is None:
        return {
            "configured": False,
            "repo_root": None,
            "repo_exists": False,
            "is_git_repo": False,
            "refresh_attempted": refresh,
            "refresh_succeeded": False,
            "current_branch": None,
            "head_commit": None,
            "origin_main_commit": None,
            "comparison_remote_name": comparison_remote_name,
            "comparison_branch": comparison_branch,
            "comparison_ref": comparison_ref,
            "comparison_main_commit": None,
            "comparison_ref_resolved": False,
            "ahead_count": None,
            "behind_count": None,
            "working_tree_clean": None,
            "upstream_update_available": False,
            "repo_manifest": manifest_info,
        }

    resolved_repo_root = Path(repo_root).expanduser().resolve()
    result: dict[str, Any] = {
        "configured": True,
        "repo_root": str(resolved_repo_root),
        "repo_exists": resolved_repo_root.exists(),
        "is_git_repo": False,
        "refresh_attempted": refresh,
        "refresh_succeeded": False,
        "current_branch": None,
        "head_commit": None,
        "origin_main_commit": None,
        "comparison_remote_name": comparison_remote_name,
        "comparison_branch": comparison_branch,
        "comparison_ref": comparison_ref,
        "comparison_main_commit": None,
        "comparison_ref_resolved": False,
        "ahead_count": None,
        "behind_count": None,
        "working_tree_clean": None,
        "upstream_update_available": False,
    }
    result["repo_manifest"] = manifest_info
    if not result["repo_exists"]:
        return result

    exit_code, inside_work_tree = _run_git(resolved_repo_root, "rev-parse", "--is-inside-work-tree")
    if exit_code != 0 or inside_work_tree.lower() != "true":
        return result
    result["is_git_repo"] = True

    if refresh:
        refresh_code, _ = _run_git(resolved_repo_root, "fetch", comparison_remote_name, "--prune")
        result["refresh_succeeded"] = refresh_code == 0

    branch_code, branch_name = _run_git(resolved_repo_root, "branch", "--show-current")
    if branch_code == 0 and branch_name:
        result["current_branch"] = branch_name

    head_code, head_commit = _run_git(resolved_repo_root, "rev-parse", "--short", "HEAD")
    if head_code == 0 and head_commit:
        result["head_commit"] = head_commit

    comparison_code, comparison_commit = _run_git(resolved_repo_root, "rev-parse", "--short", comparison_ref)
    if comparison_code == 0 and comparison_commit:
        result["comparison_main_commit"] = comparison_commit
        result["comparison_ref_resolved"] = True
        if comparison_remote_name == "origin" and comparison_branch == "main":
            result["origin_main_commit"] = comparison_commit
        count_code, counts = _run_git(resolved_repo_root, "rev-list", "--left-right", "--count", f"HEAD...{comparison_ref}")
        if count_code == 0 and counts:
            left_right = counts.split()
            if len(left_right) == 2:
                ahead_count = int(left_right[0])
                behind_count = int(left_right[1])
                result["ahead_count"] = ahead_count
                result["behind_count"] = behind_count
                result["upstream_update_available"] = behind_count > 0

    status_code, status_output = _run_git(resolved_repo_root, "status", "--porcelain")
    if status_code == 0:
        result["working_tree_clean"] = not bool(status_output)

    return result


def _overlay_summary(profile: WorkspaceProfile) -> dict[str, Any]:
    if not profile.enable_medical_overlay:
        return {
            "enabled": False,
            "all_targets_ready": False,
            "target_statuses": {},
        }
    status = describe_medical_overlay(**overlay_request_from_profile(profile))
    return {
        "enabled": True,
        "all_targets_ready": bool(status.get("all_targets_ready")),
        "target_statuses": {
            str(item.get("skill_id")): str(item.get("status"))
            for item in status.get("targets", [])
            if isinstance(item, dict) and item.get("skill_id")
        },
    }


def _workspace_summary(profile: WorkspaceProfile) -> dict[str, Any]:
    doctor_report = build_doctor_report(profile)
    runtime_contract: dict[str, object]
    if isinstance(doctor_report.runtime_contract, dict) and doctor_report.runtime_contract:
        runtime_contract = dict(doctor_report.runtime_contract)
    else:
        runtime_contract = {"ready": bool(doctor_report.runtime_exists and doctor_report.med_deepscientist_runtime_exists), "checks": {}}

    launcher_contract: dict[str, object]
    if isinstance(doctor_report.launcher_contract, dict) and doctor_report.launcher_contract:
        launcher_contract = dict(doctor_report.launcher_contract)
    else:
        launcher_contract = {"ready": True, "checks": {}}

    behavior_gate: dict[str, object]
    if isinstance(doctor_report.behavior_gate, dict) and doctor_report.behavior_gate:
        behavior_gate = dict(doctor_report.behavior_gate)
    else:
        behavior_gate = {"ready": True, "phase_25_ready": True, "checks": {}, "critical_overrides": []}

    return {
        "workspace_exists": doctor_report.workspace_exists,
        "runtime_exists": doctor_report.runtime_exists,
        "studies_exists": doctor_report.studies_exists,
        "portfolio_exists": doctor_report.portfolio_exists,
        "med_deepscientist_runtime_exists": doctor_report.med_deepscientist_runtime_exists,
        "medical_overlay_enabled": doctor_report.medical_overlay_enabled,
        "medical_overlay_ready": doctor_report.medical_overlay_ready,
        "runtime_contract": runtime_contract,
        "launcher_contract": launcher_contract,
        "behavior_gate": behavior_gate,
    }


def _determine_decision(
    *,
    repo_check: dict[str, Any],
    workspace_check: dict[str, Any],
    overlay_check: dict[str, Any],
) -> tuple[str, list[str]]:
    actions: list[str] = []
    repo_manifest = repo_check.get("repo_manifest")
    is_controlled_fork = bool(repo_manifest.get("is_controlled_fork")) if isinstance(repo_manifest, dict) else False
    current_branch = str(repo_check.get("current_branch") or "").strip() or None
    ahead_count = int(repo_check.get("ahead_count") or 0)
    upstream_update_available = bool(repo_check.get("upstream_update_available"))
    comparison_ref_resolved = bool(repo_check.get("comparison_ref_resolved"))

    behavior_gate = workspace_check.get("behavior_gate")
    phase_25_ready = bool(behavior_gate.get("phase_25_ready")) if isinstance(behavior_gate, dict) else True
    if not phase_25_ready:
        actions.append("complete_phase_25_behavior_equivalence_gate")
        return "blocked_behavior_equivalence_gate", actions

    runtime_contract = workspace_check.get("runtime_contract")
    runtime_contract_ready = bool(runtime_contract.get("ready")) if isinstance(runtime_contract, dict) else True
    if (
        not workspace_check["workspace_exists"]
        or not workspace_check["runtime_exists"]
        or not workspace_check["med_deepscientist_runtime_exists"]
        or not runtime_contract_ready
    ):
        actions.append("repair_workspace_and_runtime_contract_first")
        return "blocked_workspace_not_ready", actions

    launcher_contract = workspace_check.get("launcher_contract")
    launcher_contract_ready = bool(launcher_contract.get("ready")) if isinstance(launcher_contract, dict) else True
    if not launcher_contract_ready:
        actions.append("repair_launcher_contract_first")
        return "blocked_launcher_contract_not_ready", actions

    if not repo_check["configured"]:
        actions.append("configure_med_deepscientist_repo_root_in_profile")
        return "blocked_repo_not_configured", actions

    if not repo_check["repo_exists"]:
        actions.append("ensure_med_deepscientist_repo_root_exists_locally")
        return "blocked_repo_missing", actions

    if not repo_check["is_git_repo"]:
        actions.append("point_profile_to_a_valid_med_deepscientist_git_repo")
        return "blocked_not_git_repo", actions

    if repo_check["refresh_attempted"] and not repo_check["refresh_succeeded"]:
        actions.append("verify_origin_remote_then_refresh_again")
        return "blocked_refresh_failed", actions

    if repo_check["working_tree_clean"] is False:
        actions.append("clean_or_commit_med_deepscientist_repo_before_upgrade")
        return "blocked_dirty_repo", actions

    if is_controlled_fork and not comparison_ref_resolved:
        actions.append("configure_controlled_fork_upstream_tracking")
        return "blocked_controlled_fork_upstream_tracking_missing", actions

    if current_branch != "main":
        actions.append("review_local_branch_before_upgrade")
        if upstream_update_available:
            actions.append("pull_origin_main_then_reapply_medical_overlay")
        return "needs_branch_review", actions

    if ahead_count > 0 and not is_controlled_fork:
        actions.append("review_local_branch_before_upgrade")
        if upstream_update_available:
            actions.append("pull_origin_main_then_reapply_medical_overlay")
        return "needs_branch_review", actions

    if upstream_update_available:
        if is_controlled_fork:
            actions.append("run_controlled_fork_intake_workflow")
        else:
            actions.append("pull_origin_main_then_reapply_medical_overlay")
        return "upgrade_available", actions

    if overlay_check["enabled"] and not overlay_check["all_targets_ready"]:
        actions.append("reapply_medical_overlay")
        return "overlay_reapply_needed", actions

    actions.append("no_upgrade_action_required")
    return "up_to_date", actions


def run_upgrade_check(profile: WorkspaceProfile, *, refresh: bool = False) -> dict[str, Any]:
    workspace_check = _workspace_summary(profile)
    behavior_gate = workspace_check.get("behavior_gate")
    phase_25_ready = bool(behavior_gate.get("phase_25_ready")) if isinstance(behavior_gate, dict) else True
    if not phase_25_ready:
        return {
            "profile": profile.name,
            "decision": "blocked_behavior_equivalence_gate",
            "recommended_actions": ["complete_phase_25_behavior_equivalence_gate"],
            "repo_check": {
                "inspection_skipped": True,
                "skip_reason": "blocked_by_behavior_equivalence_gate",
                "refresh_attempted": refresh,
            },
            "workspace_check": workspace_check,
            "overlay_check": {
                "inspection_skipped": True,
                "skip_reason": "blocked_by_behavior_equivalence_gate",
            },
        }

    overlay_check = _overlay_summary(profile)
    repo_check = inspect_med_deepscientist_repo(repo_root=profile.med_deepscientist_repo_root, refresh=refresh)
    decision, recommended_actions = _determine_decision(
        repo_check=repo_check,
        workspace_check=workspace_check,
        overlay_check=overlay_check,
    )
    return {
        "profile": profile.name,
        "decision": decision,
        "recommended_actions": recommended_actions,
        "repo_check": repo_check,
        "workspace_check": workspace_check,
        "overlay_check": overlay_check,
    }
