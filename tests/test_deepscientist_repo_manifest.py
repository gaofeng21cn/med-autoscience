import json
from pathlib import Path

from med_autoscience.deepscientist_repo_manifest import inspect_deepscientist_repo_manifest


def test_inspect_deepscientist_repo_manifest_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    result = inspect_deepscientist_repo_manifest(repo_root)

    assert result["manifest_path"] == str(repo_root / "MEDICAL_FORK_MANIFEST.json")
    assert result["manifest_found"] is False
    assert result["manifest_parsable"] is False
    assert result["issues"] == []
    assert result["engine_family"] is None
    assert result["freeze_base_commit"] is None
    assert result["applied_commits"] == ()
    assert result["is_controlled_fork"] is False


def test_inspect_deepscientist_repo_manifest_handles_invalid_json(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "MEDICAL_FORK_MANIFEST.json"
    manifest_path.write_text("{not valid json}", encoding="utf-8")

    result = inspect_deepscientist_repo_manifest(repo_root)

    assert result["manifest_found"] is True
    assert result["manifest_parsable"] is False
    assert any(issue.startswith("manifest_parse_failed:") for issue in result["issues"])
    assert result["engine_family"] is None
    assert result["freeze_base_commit"] is None
    assert result["applied_commits"] == ()
    assert result["is_controlled_fork"] is False


def test_inspect_deepscientist_repo_manifest_parses_expected_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "MEDICAL_FORK_MANIFEST.json"
    payload = {
        "engine_family": "MedicalDeepScientist",
        "freeze_base_commit": "abc123",
        "applied_commits": ["111", "222"],
        "is_controlled_fork": True,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = inspect_deepscientist_repo_manifest(repo_root)

    assert result["manifest_found"] is True
    assert result["manifest_parsable"] is True
    assert result["engine_family"] == payload["engine_family"]
    assert result["freeze_base_commit"] == payload["freeze_base_commit"]
    assert result["applied_commits"] == tuple(payload["applied_commits"])
    assert result["is_controlled_fork"] is True


def test_inspect_deepscientist_repo_manifest_parses_phase1_full_schema(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "MEDICAL_FORK_MANIFEST.json"
    payload = {
        "schema_version": 1,
        "engine_id": "medicaldeepscientist",
        "engine_family": "MedicalDeepScientist",
        "freeze_mode": "thin_fork",
        "upstream_source": {
            "repo_path": "/tmp/DeepScientist",
            "base_commit": "base123",
        },
        "compatibility_contract": {
            "package_rename_applied": False,
            "daemon_api_shape_preserved": True,
            "quest_layout_preserved": True,
            "worktree_layout_preserved": True,
        },
        "applied_commits": [
            {
                "commit": "patch111",
                "kind": "runtime_bugfix",
                "summary": "Fix worktree document asset resolution",
            }
        ],
        "lock_policy": {
            "mode": "regenerate_in_fork",
            "source_repo_was_dirty": True,
            "source_dirty_paths": ["uv.lock"],
            "regenerated_after_commit": "patch111",
        },
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = inspect_deepscientist_repo_manifest(repo_root)

    assert result["manifest_found"] is True
    assert result["manifest_parsable"] is True
    assert result["engine_family"] == "MedicalDeepScientist"
    assert result["freeze_base_commit"] == "base123"
    assert result["applied_commits"] == ("patch111",)
    assert result["is_controlled_fork"] is True
