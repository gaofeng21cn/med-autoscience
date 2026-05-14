from __future__ import annotations

from pathlib import Path


RETIRED_WORKSPACE_SERVICE_ENTRY_SUFFIXES: tuple[tuple[str, ...], ...] = (
    ("ops", "medautoscience", "bin", "install-watch-runtime-service"),
    ("ops", "medautoscience", "bin", "watch-runtime-service-status"),
    ("ops", "medautoscience", "bin", "uninstall-watch-runtime-service"),
    ("ops", "medautoscience", "bin", "watch-runtime-service-runner"),
)


def retired_workspace_service_paths(workspace_root: Path) -> list[Path]:
    return [
        Path(workspace_root).joinpath(*suffix)
        for suffix in RETIRED_WORKSPACE_SERVICE_ENTRY_SUFFIXES
    ]


def retired_file_cleanup_reason(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        existing_content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return retired_workspace_service_entry_reason(path=path, existing_content=existing_content)


def retired_workspace_service_entry_reason(*, path: Path, existing_content: str) -> str | None:
    suffix = path.parts[-4:]
    if suffix not in RETIRED_WORKSPACE_SERVICE_ENTRY_SUFFIXES:
        return None
    generated_or_legacy_markers = (
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"',
        "WATCH_RUNTIME_RUNNER",
        "watch-runtime-service-runner",
        "runtime ensure-supervision",
        "runtime supervision-status",
        "runtime remove-supervision",
        "launchctl bootstrap",
        "systemctl --user",
    )
    if any(marker in existing_content for marker in generated_or_legacy_markers):
        return "retired_workspace_service_wrapper"
    return None
