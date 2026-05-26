from __future__ import annotations

from pathlib import Path


RETIRED_WORKSPACE_SERVICE_ENTRY_SUFFIXES: tuple[tuple[str, ...], ...] = (
    ("ops", "medautoscience", "bin", "study-runtime-status"),
    ("ops", "medautoscience", "bin", "watch-runtime"),
    ("ops", "medautoscience", "bin", "install-watch-runtime-service"),
    ("ops", "medautoscience", "bin", "watch-runtime-service-status"),
    ("ops", "medautoscience", "bin", "uninstall-watch-runtime-service"),
    ("ops", "medautoscience", "bin", "watch-runtime-service-runner"),
    ("ops", "medautoscience", "bin", "ensure-study-runtime"),
    ("ops", "medautoscience", "bin", "progress-portal"),
    ("ops", "mas", "bin", "start-web"),
    ("ops", "medautoscience", "bin", "domain-route-scan"),
    ("ops", "medautoscience", "bin", "domain-route-reconcile"),
    ("ops", "medautoscience", "bin", "supervisor-scan"),
    ("ops", "medautoscience", "bin", "supervisor-reconcile"),
    ("ops", "medautoscience", "bin", "supervisor-consume"),
    ("ops", "medautoscience", "bin", "supervisor-execute-dispatch"),
    ("ops", "medautoscience", "supervisor", "cron", "supervisor-scan.cron"),
    ("ops", "medautoscience", "supervisor", "launchd", "README.md"),
    (
        "ops",
        "medautoscience",
        "supervisor",
        "systemd",
        "medautoscience-supervisor-scan.service",
    ),
    (
        "ops",
        "medautoscience",
        "supervisor",
        "systemd",
        "medautoscience-supervisor-scan.timer",
    ),
)

RETIRED_WORKSPACE_SERVICE_DIR_SUFFIXES: tuple[tuple[str, ...], ...] = (
    ("ops", "medautoscience", "supervisor", "cron"),
    ("ops", "medautoscience", "supervisor", "launchd"),
    ("ops", "medautoscience", "supervisor", "systemd"),
    ("ops", "medautoscience", "supervisor"),
)


def retired_workspace_service_paths(workspace_root: Path) -> list[Path]:
    return [
        Path(workspace_root).joinpath(*suffix)
        for suffix in RETIRED_WORKSPACE_SERVICE_ENTRY_SUFFIXES
    ]


def retired_workspace_service_dir_paths(workspace_root: Path) -> list[Path]:
    return [
        Path(workspace_root).joinpath(*suffix)
        for suffix in RETIRED_WORKSPACE_SERVICE_DIR_SUFFIXES
    ]


def retired_file_cleanup_reason(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        existing_content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return retired_workspace_service_entry_reason(path=path, existing_content=existing_content)


def retired_empty_dir_cleanup_reason(path: Path) -> str | None:
    if not path.exists() or not path.is_dir():
        return None
    if not any(path.parts[-len(suffix) :] == suffix for suffix in RETIRED_WORKSPACE_SERVICE_DIR_SUFFIXES):
        return None
    try:
        next(path.iterdir())
    except StopIteration:
        return "retired_empty_workspace_service_directory"
    except OSError:
        return None
    return None


def retired_workspace_service_entry_reason(*, path: Path, existing_content: str) -> str | None:
    if not any(path.parts[-len(suffix) :] == suffix for suffix in RETIRED_WORKSPACE_SERVICE_ENTRY_SUFFIXES):
        return None
    generated_or_legacy_markers = (
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"',
        "run_medautosci progress-projection",
        "run_medautosci progress-portal",
        "run_medautosci workspace progress-portal",
        "run_medautosci study-runtime-status",
        "run_medautosci runtime domain-health-diagnostic",
        "run_medautosci watch",
        "run_medautosci ensure-study-runtime",
        "run_medautosci runtime domain-route-scan",
        "run_medautosci runtime domain-route-reconcile",
        "run_medautosci runtime supervisor-scan",
        "run_medautosci runtime supervisor-reconcile",
        "run_medautosci runtime supervisor-consume",
        "run_medautosci runtime supervisor-execute-dispatch",
        "ops/medautoscience/bin/supervisor-scan",
        "--runtime-root",
        "WATCH_RUNTIME_RUNNER",
        "watch-runtime-service-runner",
        "install-watch-runtime-service",
        "watch-runtime-service-status",
        "uninstall-watch-runtime-service",
        "runtime ensure-supervision",
        "runtime supervision-status",
        "runtime remove-supervision",
        "medautoscience-supervisor-scan.service",
        "portable supervisor scan",
        "launchctl bootstrap",
        "systemctl --user",
    )
    if any(marker in existing_content for marker in generated_or_legacy_markers):
        return "retired_workspace_service_wrapper"
    return None
