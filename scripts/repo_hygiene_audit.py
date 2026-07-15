from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


BANNED_DIRECTORY_NAMES = frozenset(
    {
        "ops",
        "build",
        "dist",
        "tmp",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    }
)
BANNED_FILE_NAMES = frozenset({".DS_Store"})
BANNED_SUFFIXES = (".egg-info",)
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
ENTRYPOINT_PATHS = frozenset(
    {
        "src/med_autoscience/mcp_server/__init__.py",
        "src/med_autoscience/cli/__init__.py",
        "src/med_autoscience/cli/parser.py",
    }
)
ENTRYPOINT_TOKEN_DENYLIST = {
    "domain-health-diagnostic": "retired_domain_health_diagnostic_entrypoint",
    "domain-owner-action-dispatch": "retired_domain_owner_action_dispatch_entrypoint",
    "owner-route-reconcile": "retired_owner_route_reconcile_entrypoint",
    "default-executor": "retired_default_executor_entrypoint",
    "progress-portal": "retired_progress_portal_entrypoint",
}
EXPECTED_STANDARD_AGENT_SOURCE_FILES = frozenset(
    {
        "src/med_autoscience/__init__.py",
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


def _is_banned_directory(name: str) -> bool:
    return name in BANNED_DIRECTORY_NAMES or name.endswith(BANNED_SUFFIXES)


def _is_banned_file(name: str) -> bool:
    return name in BANNED_FILE_NAMES or name.endswith(BANNED_SUFFIXES)


def audit_tracked_paths(tracked_paths: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for raw_path in tracked_paths:
        parts = Path(raw_path).parts
        if any(_is_banned_directory(part) for part in parts[:-1]):
            violations.append(raw_path)
        elif parts and _is_banned_file(parts[-1]):
            violations.append(raw_path)
    return violations


def audit_active_surface_residue(
    root: Path,
    tracked_paths: tuple[str, ...],
) -> list[str]:
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

    entrypoint_paths = ENTRYPOINT_PATHS | frozenset(
        path
        for path in tracked_paths
        if path.startswith("src/med_autoscience/") and path.endswith("/parser.py")
    )
    for raw_path in tracked_paths:
        if not raw_path.startswith(ACTIVE_SURFACE_ROOTS):
            continue
        for pattern, reason in ACTIVE_PATH_DENYLIST:
            if pattern.search(raw_path):
                violations.append(f"{raw_path}: {reason}")
                break
        if raw_path not in entrypoint_paths:
            continue
        path = root / raw_path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for token, reason in ENTRYPOINT_TOKEN_DENYLIST.items():
            if token in text:
                violations.append(f"{raw_path}: {reason}")
    return violations


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit tracked repository paths and retired active surfaces."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root to audit. Defaults to the current git root.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or []))
    root = (args.root or _default_repo_root()).resolve()
    if not root.is_dir():
        print(f"repo hygiene audit: root is not a directory: {root}", file=sys.stderr)
        return 2

    tracked_paths = _git_tracked_paths(root)
    violations = sorted(
        set(
            audit_tracked_paths(tracked_paths)
            + audit_active_surface_residue(root, tracked_paths)
        )
    )
    if violations:
        print(
            "repo hygiene audit failed: tracked residue or retired active surfaces detected",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("repo hygiene audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
