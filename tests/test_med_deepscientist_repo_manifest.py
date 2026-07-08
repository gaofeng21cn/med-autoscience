import json
from pathlib import Path

from med_autoscience.med_deepscientist_repo_manifest import inspect_med_deepscientist_repo_manifest


def test_inspect_med_deepscientist_repo_manifest_missing_keeps_archive_only_boundary(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    result = inspect_med_deepscientist_repo_manifest(repo_root)

    assert result["manifest_found"] is False
    assert result["manifest_parsable"] is False
    assert result["is_controlled_fork"] is False
    assert result["parity_deconstruction_summary"]["mds_role"] == "frozen_source_archive_or_historical_fixture_only"
    assert result["parity_deconstruction_summary"]["mds_quality_authority"] == "none"
    assert result["parity_deconstruction_summary"]["medical_quality_authority_granted_to_mds"] is False


def test_inspect_med_deepscientist_repo_manifest_parses_controlled_archive_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    payload = {
        "engine_id": "med-deepscientist",
        "engine_family": "MedDeepScientist",
        "freeze_base_commit": "abc123",
        "applied_commits": ["patch111"],
        "upstream_tracking": {
            "remote_name": "upstream",
            "branch": "main",
            "ref": "upstream/main",
        },
    }
    (repo_root / "MEDICAL_FORK_MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = inspect_med_deepscientist_repo_manifest(repo_root)

    assert result["manifest_found"] is True
    assert result["manifest_parsable"] is True
    assert result["engine_family"] == "MedDeepScientist"
    assert result["freeze_base_commit"] == "abc123"
    assert result["applied_commits"] == ("patch111",)
    assert result["is_controlled_fork"] is True
    assert result["upstream_remote_name"] == "upstream"
    assert result["upstream_branch"] == "main"
    assert result["upstream_ref"] == "upstream/main"
    assert result["parity_deconstruction_summary"]["capability_count"] == 6
    assert result["parity_deconstruction_summary"]["medical_quality_authority_granted_to_mds"] is False
