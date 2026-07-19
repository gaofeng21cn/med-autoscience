from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


MAS_POLICY_DIRECTORY_NAMES = frozenset(
    {
        "ops",
        "build",
        "tmp",
        ".ruff_cache",
        ".mypy_cache",
    }
)
MAS_POLICY_FILE_NAMES = frozenset({".DS_Store"})
ACTIVE_SURFACE_ROOTS = (
    "src/",
    "tests/",
    "contracts/",
    "profiles/",
    "agent/",
    "runtime/authority_functions/",
)
ACTIVE_PATH_DENYLIST = (
    (
        re.compile(r"(^|/)(dhd|domain[-_]health[-_]diagnostic)(/|\.|_|-|$)", re.I),
        "retired_dhd_active_path",
    ),
    (
        re.compile(r"(^|/)owner[-_]route[-_]reconcile(/|\.|_|-|$)", re.I),
        "retired_owner_route_reconcile_active_path",
    ),
    (
        re.compile(r"(^|/)domain[-_]owner[-_]action[-_]dispatch(/|\.|_|-|$)", re.I),
        "retired_domain_owner_action_dispatch_active_path",
    ),
    (
        re.compile(r"(^|/)default[-_]executor(/|\.|_|-|$)", re.I),
        "retired_default_executor_active_path",
    ),
    (
        re.compile(r"(^|/)progress[-_]portal(/|\.|_|-|$)", re.I),
        "retired_progress_portal_active_path",
    ),
    (
        re.compile(r"(^|/)runtime[-_]storage[-_]maintenance(/|\.|_|-|$)", re.I),
        "retired_runtime_storage_maintenance_active_path",
    ),
    (
        re.compile(r"(^|/)sqlite[-_]sidecars?(/|\.|_|-|$)", re.I),
        "retired_sqlite_sidecars_active_path",
    ),
    (
        re.compile(
            r"(^|/)(local[-_]launchd[-_]scheduler|workspace[-_]local[-_]scheduler|"
            r"mas[-_]supervision[-_]scheduler|supervision[-_]scheduler|"
            r"mas[-_]default[-_]generic[-_]scheduler|mas[-_]owned[-_]generic[-_]scheduler|"
            r"mas[-_]runtime[-_]scheduler|scheduler[-_]owner.*(mas|med[-_]autoscience|local|workspace)|"
            r"(mas|med[-_]autoscience|local|workspace).*scheduler[-_]owner)(/|\.|_|-|$)",
            re.I,
        ),
        "retired_mas_local_scheduler_active_path",
    ),
)
EXPECTED_STANDARD_AGENT_SOURCE_FILES = frozenset(
    {
        "src/med_autoscience/__init__.py",
        "src/med_autoscience/authority_handlers/_generation_manifest.py",
        "src/med_autoscience/authority_handlers/_record_validation.py",
        "src/med_autoscience/authority_handlers/candidate_admission.py",
        "src/med_autoscience/authority_handlers/paper_mission.py",
        "src/med_autoscience/authority_handlers/self_evolution_closeout.py",
        "src/med_autoscience/styles/__init__.py",
        "src/med_autoscience/styles/frontiers.csl",
    }
)


def _default_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip()).resolve()


def _git_tracked_paths(root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=True,
        capture_output=True,
        check=True,
    )
    tracked_paths: list[str] = []
    for path in result.stdout.split("\0"):
        candidate = root / path
        if path and (candidate.exists() or candidate.is_symlink()):
            tracked_paths.append(path)
    return tuple(tracked_paths)


def audit_mas_repository_policy(tracked_paths: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for raw_path in tracked_paths:
        parts = Path(raw_path).parts
        if any(part in MAS_POLICY_DIRECTORY_NAMES for part in parts[:-1]):
            violations.append(raw_path)
        elif parts and parts[-1] in MAS_POLICY_FILE_NAMES:
            violations.append(raw_path)
    return violations


def audit_active_surface_residue(tracked_paths: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    observed_source_files = {
        path for path in tracked_paths if path.startswith("src/med_autoscience/")
    }
    for relative_path in sorted(
        observed_source_files - EXPECTED_STANDARD_AGENT_SOURCE_FILES
    ):
        violations.append(f"{relative_path}: nonstandard_mas_private_source_surface")
    for relative_path in sorted(
        EXPECTED_STANDARD_AGENT_SOURCE_FILES - observed_source_files
    ):
        violations.append(f"{relative_path}: required_standard_agent_source_missing")

    for raw_path in tracked_paths:
        if not raw_path.startswith(ACTIVE_SURFACE_ROOTS):
            continue
        for pattern, reason in ACTIVE_PATH_DENYLIST:
            if pattern.search(raw_path):
                violations.append(f"{raw_path}: {reason}")
                break
    return violations


def main() -> int:
    root = _default_repo_root()
    tracked_paths = _git_tracked_paths(root)
    violations = sorted(
        set(
            audit_mas_repository_policy(tracked_paths)
            + audit_active_surface_residue(tracked_paths)
        )
    )
    if violations:
        print(
            "MAS repository policy failed: tracked residue or retired active surfaces detected",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("MAS repository policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
