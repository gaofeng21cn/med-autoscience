from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import domain_health_diagnostic as dhd


def test_domain_health_diagnostic_entrypoints_are_retired() -> None:
    quest = dhd.run_domain_health_diagnostic_for_quest(quest_root=Path("/tmp/quest"), apply=True)
    runtime = dhd.run_domain_health_diagnostic_for_runtime(runtime_root=Path("/tmp/runtime"), apply=True)

    assert quest["status"] == "retired"
    assert runtime["status"] == "retired"
    assert quest["dhd_is_control_plane"] is False
    assert runtime["apply_supported"] is False
