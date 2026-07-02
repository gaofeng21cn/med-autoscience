from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def test_ai_reviewer_record_dry_run_plan_blocks_when_expected_identity_is_unavailable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {"state": "requested"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {"study_id": study_id, "quest_id": study_id, "study_root": str(study_root)},
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "current_owner_identity_unavailable_for_guard"
    assert result["identity_guard"]["matched"] is False
    assert result["identity_guard"]["missing_observed_fields"] == [
        "owner",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
    ]
    assert result["expected_current_work_unit"] == {
        "owner": "ai_reviewer",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
    }
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_plan_accepts_canonical_next_action_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "obesity_multicenter_phenotype_atlas"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {"state": "requested"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.review.ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review",
            },
            "canonical_next_action_source": "domain_transition.next_action",
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="ai_reviewer",
        expected_action_type="return_to_ai_reviewer_workflow",
        expected_work_unit_id="ai_reviewer_medical_prose_quality_review",
        expected_work_unit_fingerprint="domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review",
    )

    assert result["status"] == "dry_run"
    assert result["current_work_unit"]["status"] == "canonical_next_action"
    assert result["identity_guard"]["matched"] is True
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_plan_fails_closed_on_expected_owner_mismatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {"state": "requested"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    matched_result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="analysis-campaign",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )
    mismatch_result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert matched_result["status"] == "dry_run"
    assert matched_result["identity_guard"]["matched"] is True
    assert matched_result["written_files"] == []
    assert mismatch_result["status"] == "blocked"
    assert mismatch_result["blocked_reason"] == "current_owner_identity_mismatch"
    assert mismatch_result["identity_guard"]["matched"] is False
    assert mismatch_result["identity_guard"]["mismatches"] == [
        {"field": "owner", "expected": "ai_reviewer", "observed": "analysis-campaign"}
    ]
    assert mismatch_result["identity_guard"]["missing_observed_fields"] == []
    assert mismatch_result["written_files"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()
