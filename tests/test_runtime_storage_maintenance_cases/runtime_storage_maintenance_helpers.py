from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sqlite3
import time

import pytest

from tests.runtime_storage_boundary_helpers import assert_storage_refs_only_adapter_boundary
from tests.study_runtime_test_helpers import make_profile


def _write_fake_mds_repo(repo_root: Path) -> None:
    script_path = repo_root / "scripts" / "maintain_quest_runtime_storage.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import json",
                "import os",
                "import sys",
                "from pathlib import Path",
                "",
                "quest_root = Path(sys.argv[1]).expanduser().resolve()",
                "print(json.dumps({",
                '    "status": "ok",',
                '    "quest_root": str(quest_root),',
                '    "argv": sys.argv[1:],',
                '    "pythonpath": os.environ.get("PYTHONPATH", ""),',
                '    "roots": [],',
                "}, ensure_ascii=False))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    os.chmod(script_path, 0o755)


def _write_study(study_root: Path, *, study_id: str, quest_id: str) -> None:
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(
        "\n".join(
            [
                f"study_id: {study_id}",
                "title: Runtime storage maintenance study",
                "execution:",
                f"  quest_id: {quest_id}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "schema_version: 1",
                f"study_id: {study_id}",
                f"quest_id: {quest_id}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_quest(quest_root: Path, *, quest_id: str, status: str, active_run_id: str | None = None) -> None:
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\n", encoding="utf-8")
    runtime_state = {"quest_id": quest_id, "status": status, "active_run_id": active_run_id}
    ds_root = quest_root / ".ds"
    ds_root.mkdir(parents=True, exist_ok=True)
    (ds_root / "runtime_state.json").write_text(json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_dataset_release(
    workspace_root: Path,
    *,
    family_id: str,
    version_id: str,
    dataset_id: str,
    supersedes_versions: list[str] | None = None,
    restore_handle: str | None = None,
    restore_index_path: str | None = None,
    checksum: str | None = None,
    rehydrate_verified: bool = False,
) -> Path:
    release_root = workspace_root / "datasets" / family_id / version_id
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    source_lines = ["source_release:"]
    if restore_handle:
        source_lines.append(f"  restore_handle: {restore_handle}")
    if restore_index_path:
        source_lines.append(f"  restore_index_path: {restore_index_path}")
    if checksum:
        source_lines.append(f"  sha256: {checksum}")
    if rehydrate_verified:
        source_lines.extend(
            [
                "  rehydrate_verification:",
                "    status: verified",
            ]
        )
    supersedes_lines = []
    if supersedes_versions is not None:
        supersedes_lines.append("supersedes_versions:")
        supersedes_lines.extend(f"- {version}" for version in supersedes_versions)
    (release_root / "dataset_manifest.yaml").write_text(
        "\n".join(
            [
                f"dataset_id: {dataset_id}",
                f"version: {version_id}",
                "main_outputs:",
                "  analysis_csv: analysis.csv",
                *source_lines,
                *supersedes_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return release_root


__all__ = [
    "importlib",
    "json",
    "os",
    "Path",
    "sqlite3",
    "time",
    "pytest",
    "assert_storage_refs_only_adapter_boundary",
    "make_profile",
    "_write_fake_mds_repo",
    "_write_study",
    "_write_quest",
    "_write_dataset_release",
]
