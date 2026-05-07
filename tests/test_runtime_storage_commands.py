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
        self.quest_maintain_kwargs: dict[str, Any] | None = None

    def audit_workspace_storage(self, **kwargs: Any) -> dict[str, object]:
        self.audit_kwargs = kwargs
        return {"status": "ok"}

    def maintain_quest_runtime_storage(self, **kwargs: Any) -> dict[str, object]:
        self.quest_maintain_kwargs = kwargs
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
            "--reinitialize-empty-workspace-git",
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
    assert runtime_storage.audit_kwargs["reinitialize_empty_workspace_git"] is True
    assert runtime_storage.audit_kwargs["all_studies"] is False
    assert runtime_storage.audit_kwargs["older_than_seconds"] == 3600
    assert '"status": "ok"' in capsys.readouterr().out


def test_workspace_storage_audit_git_only_passes_root_git_retirement_option(capsys: pytest.CaptureFixture[str]) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--git-only",
            "--apply",
            "--retire-workspace-root-git",
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
    assert runtime_storage.audit_kwargs["retire_workspace_root_git"] is True
    assert runtime_storage.audit_kwargs["reinitialize_empty_workspace_git"] is False
    assert runtime_storage.audit_kwargs["all_studies"] is False
    assert '"status": "ok"' in capsys.readouterr().out


def test_workspace_storage_audit_apply_without_git_only_keeps_default_study_scan(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--apply",
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
    assert runtime_storage.audit_kwargs["git_only"] is False
    assert runtime_storage.audit_kwargs["apply"] is True
    assert runtime_storage.audit_kwargs["all_studies"] is True
    assert runtime_storage.audit_kwargs["restore_proof_compaction"] is False
    assert runtime_storage.audit_kwargs["include_parked_controller_stop"] is False
    assert runtime_storage.audit_kwargs["include_operator_confirmed_parked_active"] is False
    assert '"status": "ok"' in capsys.readouterr().out


def test_workspace_storage_audit_restore_proof_compaction_supports_dry_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--study-id",
            "004-completed",
            "--restore-proof-compaction",
            "--include-parked-controller-stop",
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
    assert runtime_storage.audit_kwargs["study_id"] == "004-completed"
    assert runtime_storage.audit_kwargs["apply"] is False
    assert runtime_storage.audit_kwargs["restore_proof_compaction"] is True
    assert runtime_storage.audit_kwargs["restore_proof_buckets"] == ()
    assert runtime_storage.audit_kwargs["include_parked_controller_stop"] is True
    assert runtime_storage.audit_kwargs["include_operator_confirmed_parked_active"] is False
    assert '"status": "ok"' in capsys.readouterr().out


def test_workspace_storage_audit_restore_proof_bucket_option_is_explicit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--study-id",
            "004-completed",
            "--restore-proof-compaction",
            "--restore-proof-bucket",
            "cold_archive",
            "--restore-proof-bucket",
            "events",
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
    assert runtime_storage.audit_kwargs["restore_proof_buckets"] == ("cold_archive", "events")
    assert '"status": "ok"' in capsys.readouterr().out


def test_runtime_maintain_storage_quest_root_dispatches_orphan_quest_entry(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    parser = _parser()
    quest_root = tmp_path / "runtime" / "quests" / "legacy-quest"
    args = parser.parse_args(
        [
            "runtime-maintain-storage",
            "--profile",
            "workspace.toml",
            "--quest-root",
            str(quest_root),
            "--restore-proof-compaction",
            "--restore-proof-bucket",
            "cold_archive",
            "--include-parked-controller-stop",
            "--include-operator-confirmed-parked-active",
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
    assert runtime_storage.quest_maintain_kwargs is not None
    assert runtime_storage.quest_maintain_kwargs["quest_root"] == quest_root
    assert runtime_storage.quest_maintain_kwargs["restore_proof_compaction"] is True
    assert runtime_storage.quest_maintain_kwargs["restore_proof_buckets"] == ("cold_archive",)
    assert runtime_storage.quest_maintain_kwargs["include_parked_controller_stop"] is True
    assert runtime_storage.quest_maintain_kwargs["include_operator_confirmed_parked_active"] is True
    assert runtime_storage.audit_kwargs is None
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


@pytest.mark.parametrize("args_without_required_gate", [["--reinitialize-empty-workspace-git"], ["--git-only", "--reinitialize-empty-workspace-git"]])
def test_workspace_storage_audit_reinitialize_requires_git_only_apply(args_without_required_gate: list[str]) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            *args_without_required_gate,
        ]
    )

    with pytest.raises(SystemExit):
        handle_runtime_storage_command(
            args,
            parser=parser,
            load_profile=lambda profile: {"profile": profile},
            runtime_storage_maintenance=_RuntimeStorageMaintenanceStub(),
        )


@pytest.mark.parametrize("args_without_required_gate", [["--retire-workspace-root-git"], ["--git-only", "--retire-workspace-root-git"]])
def test_workspace_storage_audit_retire_workspace_root_git_requires_git_only_apply(
    args_without_required_gate: list[str],
) -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            *args_without_required_gate,
        ]
    )

    with pytest.raises(SystemExit):
        handle_runtime_storage_command(
            args,
            parser=parser,
            load_profile=lambda profile: {"profile": profile},
            runtime_storage_maintenance=_RuntimeStorageMaintenanceStub(),
        )


def test_workspace_storage_audit_reinitialize_and_retire_are_mutually_exclusive() -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--git-only",
            "--apply",
            "--reinitialize-empty-workspace-git",
            "--retire-workspace-root-git",
        ]
    )

    with pytest.raises(SystemExit):
        handle_runtime_storage_command(
            args,
            parser=parser,
            load_profile=lambda profile: {"profile": profile},
            runtime_storage_maintenance=_RuntimeStorageMaintenanceStub(),
        )


def test_workspace_storage_audit_restore_proof_compaction_rejects_git_only() -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--git-only",
            "--apply",
            "--restore-proof-compaction",
        ]
    )

    with pytest.raises(SystemExit):
        handle_runtime_storage_command(
            args,
            parser=parser,
            load_profile=lambda profile: {"profile": profile},
            runtime_storage_maintenance=_RuntimeStorageMaintenanceStub(),
        )


def test_workspace_storage_audit_parked_controller_stop_requires_restore_proof_compaction() -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--apply",
            "--include-parked-controller-stop",
        ]
    )

    with pytest.raises(SystemExit):
        handle_runtime_storage_command(
            args,
            parser=parser,
            load_profile=lambda profile: {"profile": profile},
            runtime_storage_maintenance=_RuntimeStorageMaintenanceStub(),
        )


def test_workspace_storage_audit_operator_confirmed_parked_active_requires_restore_proof_compaction() -> None:
    parser = _parser()
    args = parser.parse_args(
        [
            "workspace-storage-audit",
            "--profile",
            "workspace.toml",
            "--apply",
            "--include-operator-confirmed-parked-active",
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
