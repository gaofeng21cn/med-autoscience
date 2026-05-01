from __future__ import annotations

import argparse
from typing import Any

import pytest

from med_autoscience.cli_parts.runtime_storage_commands import (
    handle_runtime_storage_command,
    register_runtime_storage_parsers,
)


class _RuntimeStorageMaintenanceStub:
    def __init__(self) -> None:
        self.audit_kwargs: dict[str, Any] | None = None

    def audit_workspace_storage(self, **kwargs: Any) -> dict[str, object]:
        self.audit_kwargs = kwargs
        return {"status": "ok"}


def test_workspace_storage_audit_git_only_passes_fast_path_options(capsys: pytest.CaptureFixture[str]) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--git-only",
            "--apply",
            "--older-than-hours",
            "1",
        ]
    )
    runtime_storage = _RuntimeStorageMaintenanceStub()

    exit_code = handle_runtime_storage_command(
        args,
        parser=parser,
        load_profile=lambda profile: {"profile": profile},
        runtime_storage_maintenance=runtime_storage,
    )

    assert exit_code == 0
    assert runtime_storage.audit_kwargs is not None
    assert runtime_storage.audit_kwargs["git_only"] is True
    assert runtime_storage.audit_kwargs["apply"] is True
    assert runtime_storage.audit_kwargs["all_studies"] is False
    assert runtime_storage.audit_kwargs["older_than_seconds"] == 3600
    assert '"status": "ok"' in capsys.readouterr().out


@pytest.mark.parametrize("conflicting_args", [["--study-id", "001-risk"], ["--all-studies"]])
def test_workspace_storage_audit_git_only_rejects_study_selection(conflicting_args: list[str]) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--git-only",
            *conflicting_args,
        ]
    )

    with pytest.raises(SystemExit):
        handle_runtime_storage_command(
            args,
            parser=parser,
            load_profile=lambda profile: {"profile": profile},
            runtime_storage_maintenance=_RuntimeStorageMaintenanceStub(),
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="medautosci")
    subparsers = parser.add_subparsers(dest="command")
    register_runtime_storage_parsers(subparsers)
    return parser
