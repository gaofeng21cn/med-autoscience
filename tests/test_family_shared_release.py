from __future__ import annotations

from pathlib import Path

from med_autoscience import family_shared_release as module


def test_current_checkout_family_shared_pins_align_with_opl_release_contract() -> None:
    inspection = module.inspect_current_repo_family_shared_alignment()

    assert inspection["status"] == "aligned"
    assert len(inspection["owner_commit"]) == 40
    assert [item["status"] for item in inspection["findings"]] == ["aligned", "aligned"]
    assert all(item["pins"] == [inspection["owner_commit"]] for item in inspection["findings"])


def test_family_shared_alignment_uses_repo_root_by_default() -> None:
    inspection = module.inspect_current_repo_family_shared_alignment()

    assert inspection["repo_id"] == "medautoscience"
    assert Path(inspection["repo_root"]) == module.repo_root()
