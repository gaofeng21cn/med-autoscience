from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _mds_repo_root() -> Path:
    for candidate in (
        REPO_ROOT.parent / "med-deepscientist",
        REPO_ROOT.parents[1] / "med-deepscientist",
        Path("/Users/gaofeng/workspace/med-deepscientist"),
    ):
        if (candidate / "src" / "deepscientist").exists():
            return candidate
    raise AssertionError("med-deepscientist repo root is required for AI-first drift audit tests")


def test_ai_first_drift_audit_passes_current_mas_and_mds_surfaces() -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")

    result = module.run_ai_first_drift_audit(
        repo_root=REPO_ROOT,
        med_deepscientist_repo_root=_mds_repo_root(),
    )

    assert result["surface"] == "ai_first_drift_audit"
    assert result["status"] == "pass"
    assert result["ready"] is True
    assert result["summary"]["fail_count"] == 0
    assert result["summary"]["skipped_count"] == 0
    assert "ready_wording_without_ai_provenance" in result["categories"]
    assert "pattern_only_subjective_blockers" in result["categories"]
    assert "coverage_as_quality" in result["categories"]
    assert "stale_ai_cache" in result["categories"]


def test_ai_first_drift_audit_fails_when_ai_reviewer_provenance_guard_drifts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")
    audit_root = tmp_path / "med-autoscience"
    shutil.copytree(
        REPO_ROOT / "src" / "med_autoscience" / "quality",
        audit_root / "src" / "med_autoscience" / "quality",
    )
    target = audit_root / "src" / "med_autoscience" / "quality" / "study_quality.py"
    target.write_text(
        target.read_text(encoding="utf-8").replace(
            'provenance["owner"] == "ai_reviewer"',
            'provenance["owner"] in {"ai_reviewer", "mechanical_projection"}',
        ),
        encoding="utf-8",
    )

    result = module.run_ai_first_drift_audit(repo_root=audit_root)

    assert result["status"] == "fail"
    failed = {check["check_id"]: check for check in result["checks"] if check["status"] == "fail"}
    assert "quality_ready_requires_ai_reviewer_provenance" in failed
    assert 'provenance["owner"] == "ai_reviewer"' in failed[
        "quality_ready_requires_ai_reviewer_provenance"
    ]["missing_required_markers"]


def test_doctor_report_renders_ai_first_drift_audit(tmp_path: Path) -> None:
    workspace_tests = importlib.import_module("tests.test_workspace_contracts")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = workspace_tests.make_profile(tmp_path)

    rendered = doctor.render_doctor_report(doctor.build_doctor_report(profile))

    assert "ai_first_drift_audit: " in rendered
    assert '"surface": "ai_first_drift_audit"' in rendered
    assert '"doctor_meta_test_surface"' in rendered
