from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def test_ai_reviewer_record_dry_run_rejects_stale_authoring_target_stale_record_ref(
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
    prose_review_path = study_root / "paper" / "medical_prose_review.json"
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    stale_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260609T011045Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, prose_review_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    prose_review_path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "medical_prose_review": {"path": str(prose_review_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(prose_review_path.resolve())],
                },
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
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "stale_record_ref": stale_record_ref,
            "required_currentness_refs": [str(prose_review_path.resolve())],
            "required_input_refs": {"medical_prose_review": str(prose_review_path.resolve())},
            "record_payload": {
                "eval_id": "publication-eval::002::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "medical_prose_review": str(prose_review_path.resolve()),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "payload_currentness_mismatch"
    assert result["payload_guard"]["matched"] is False
    assert result["payload_guard"]["mismatches"] == [
        {"surface": "stale_record_ref", "expected": current_record_ref, "observed": stale_record_ref}
    ]
    assert result["written_files"] == []


def test_ai_reviewer_payload_guard_refreshes_target_metadata_before_record_payload_currentness(
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
    current_prose_review = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_prose_review.json"
    )
    old_prose_review = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    old_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260609T011045Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, current_prose_review, old_prose_review):
        path.parent.mkdir(parents=True, exist_ok=True)
    current_prose_review.write_text("{}", encoding="utf-8")
    old_prose_review.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "medical_prose_review": {"path": str(current_prose_review.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(current_prose_review.resolve())],
                },
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
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                ),
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode="owner_consumption_payload_guard",
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "stale_record_ref": old_record_ref,
            "required_currentness_refs": [],
            "required_input_refs": {"medical_prose_review": str(old_prose_review.resolve())},
            "record_payload": {
                "eval_id": "publication-eval::002::stale",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "medical_prose_review": str(old_prose_review.resolve()),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="return_to_ai_reviewer_workflow",
        expected_work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        expected_work_unit_fingerprint=(
            "domain-transition::ai_reviewer_re_eval::"
            "produce_ai_reviewer_publication_eval_record_against_current_inputs"
        ),
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "record_payload_currentness_mismatch"
    assert result["identity_guard"]["matched"] is True
    refresh = result["payload_target_metadata_refresh"]
    assert refresh["enabled"] is True
    assert refresh["refreshed_in_memory"] is True
    assert refresh["changed_fields"] == [
        "stale_record_ref",
        "required_input_refs",
        "required_currentness_refs",
    ]
    assert refresh["current_metadata"]["stale_record_ref"] == current_record_ref
    assert refresh["current_metadata"]["required_input_refs"]["medical_prose_review"] == str(
        current_prose_review.resolve()
    )
    assert refresh["record_payload_preserved"] is True
    assert refresh["record_payload_prefilled_by_mas"] is False
    assert result["payload_guard"]["mismatches"] == []
    assert result["payload_guard"]["matched"] is False
    assert result["payload_guard"]["reason"] == "record_payload_currentness_mismatch"
    assert result["payload_guard"]["record_payload_mismatches"] == [
        {
            "surface": "medical_prose_review",
            "expected": str(current_prose_review.resolve()),
            "observed": str(old_prose_review.resolve()),
        }
    ]
    assert old_record_ref not in json.dumps(refresh["current_metadata"])
    assert str(old_prose_review.resolve()) not in json.dumps(refresh["current_metadata"])
    assert result["written_files"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()
