from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

RUNTIME_FACT_CONSUMERS = (
    "src/med_autoscience/controllers/study_outer_loop_recovery_policy.py",
    "src/med_autoscience/controllers/study_outer_loop/runtime_refs.py",
    "src/med_autoscience/controllers/study_progress/projection.py",
    "src/med_autoscience/controllers/study_progress/runtime_efficiency.py",
    "src/med_autoscience/controllers/study_progress/runtime_liveness_projection.py",
)


def test_control_plane_consumers_use_canonical_runtime_facts() -> None:
    for relative_path in RUNTIME_FACT_CONSUMERS:
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "opl_runtime_refs" in source, relative_path

    projection_surface = (
        REPO_ROOT
        / "src/med_autoscience/controllers/study_progress/projection_runtime_surfaces.py"
    ).read_text(encoding="utf-8")
    assert "runtime_facts" in projection_surface
    assert "runtime_liveness_audit" not in projection_surface
    assert "status_payload" not in projection_surface
