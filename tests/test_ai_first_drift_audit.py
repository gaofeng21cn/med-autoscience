from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_mds_audit_fixture(root: Path) -> Path:
    _write_text(
        root / "src" / "deepscientist" / "quest" / "service.py",
        '\n'.join(
            (
                '_MAS_MEDICAL_BLUEPRINT_AUTHORING_PROVENANCE_FIELD = "authoring_provenance"',
                "mas_required_trigger_relpaths = (",
                "mas_medical_preflight_required = bool(managed_study_root) or any",
                "MAS medical manuscript blueprint lacks AI authorization/provenance",
            )
        ),
    )
    _write_text(
        root / "src" / "deepscientist" / "artifact" / "service.py",
        '\n'.join(
            (
                "mas_ai_first_surface_summaries",
                '"mas_ai_first_surfaces": mas_ai_first_surface_summaries',
                '"artifacts/publication_eval/medical_prose_review.json"',
                '"paper/review/review_ledger.json"',
                "sha256_text(path.read_text",
                '"mechanical_coverage_only": True',
                '"quality_authority": "mas_ai_preflight_prose_review_publication_eval"',
                "_PAPER_QUALITY_AUTHORITY_SEMANTICS",
            )
        ),
    )
    _write_text(
        root / "src" / "skills" / "finalize" / "SKILL.md",
        "mechanical coverage\npaper contract health\nMAS AI preflight/prose review\n",
    )
    _write_text(
        root / "src" / "skills" / "decision" / "SKILL.md",
        "mechanical coverage check\npaper_contract_health\nMAS AI preflight\n",
    )
    return root


def test_ai_first_drift_audit_passes_current_mas_and_mds_surfaces() -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")

    result = module.run_ai_first_drift_audit(repo_root=REPO_ROOT)

    assert result["surface"] == "ai_first_drift_audit"
    assert result["status"] == "pass"
    assert result["ready"] is True
    assert result["summary"]["fail_count"] == 0
    assert result["summary"]["skipped_count"] == 0
    assert result["summary"]["external_mds_rules_included"] is False
    assert result["summary"]["external_mds_rule_count"] > 0
    assert "ready_wording_without_ai_provenance" in result["categories"]
    assert "pattern_only_subjective_blockers" in result["categories"]
    assert "stale_ai_cache" not in result["categories"]


def test_ai_first_drift_audit_can_include_explicit_mds_backend_audit_rules(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")
    mds_root = _write_mds_audit_fixture(tmp_path / "med-deepscientist")

    result = module.run_ai_first_drift_audit(
        repo_root=REPO_ROOT,
        med_deepscientist_repo_root=mds_root,
        include_external_mds_rules=True,
    )

    assert result["status"] == "pass"
    assert result["summary"]["fail_count"] == 0
    assert result["summary"]["skipped_count"] == 0
    assert result["summary"]["external_mds_rules_included"] is True
    assert "coverage_as_quality" in result["categories"]
    assert "stale_ai_cache" in result["categories"]


def test_ai_first_governance_regression_os_covers_core_drift_defenses() -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")

    summary = module.build_ai_first_governance_regression_os_summary()

    assert summary["surface"] == "ai_first_governance_regression_os"
    assert summary["mechanical_system_role"] == "evidence_only"
    assert summary["mechanical_projection_can_authorize_quality"] is False
    defenses = {defense["defense_id"]: defense for defense in summary["drift_defenses"]}
    assert set(defenses) == {
        "mechanical_ready_overreach",
        "coverage_as_quality",
        "prompt_only_gate",
        "marker_only_stop_loss",
        "stale_ai_cache",
        "mds_quality_owner_drift",
    }
    for defense in defenses.values():
        assert defense["mechanical_inputs_can_only_supply"] == "evidence_only"
        assert defense["ai_reviewer_or_mas_authority_required"] is True
        assert defense["regression_surface"]
        assert defense["failure_action"] == "fail_closed_to_review_required"
    assert summary["continuous_regression_entrypoints"] == [
        "tests/test_ai_first_drift_audit.py",
        "make test-meta",
        "scripts/verify.sh",
    ]


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
