from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def test_ai_reviewer_record_dry_run_rejects_stale_payload_currentness_refs(
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
    current_evidence_path = study_root / "paper" / "evidence_ledger.json"
    current_claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    stale_evidence_path = study_root / "old" / "evidence_ledger.json"
    stale_claim_map_path = study_root / "old" / "claim_evidence_map.json"
    for path in (request_path, current_evidence_path, current_claim_map_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    current_evidence_path.write_text("{}", encoding="utf-8")
    current_claim_map_path.write_text("{}", encoding="utf-8")
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
                        "evidence_ledger": {"path": str(current_evidence_path)},
                        "claim_evidence_map": {"path": str(current_claim_map_path)},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": str(
                        study_root
                        / "artifacts"
                        / "publication_eval"
                        / "ai_reviewer_responses"
                        / "20260620T120049Z_publication_eval_record.json"
                    ),
                    "required_currentness_refs": [str(current_evidence_path), str(current_claim_map_path)],
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
            "required_input_refs": {
                "evidence_ledger": str(stale_evidence_path),
                "claim_evidence_map": str(stale_claim_map_path),
            },
            "record_payload": {
                "eval_id": "publication-eval::002::stale",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "evidence_ledger": str(stale_evidence_path),
                        "claim_evidence_map": str(stale_claim_map_path),
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
    assert result["identity_guard"]["matched"] is True
    assert result["payload_guard"]["matched"] is False
    assert result["payload_guard"]["reason"] == "payload_currentness_mismatch"
    assert result["payload_guard"]["mismatches"] == [
        {
            "surface": "evidence_ledger",
            "expected": str(current_evidence_path),
            "observed": str(stale_evidence_path),
        },
        {
            "surface": "claim_evidence_map",
            "expected": str(current_claim_map_path),
            "observed": str(stale_claim_map_path),
        },
    ]
    assert result["written_files"] == []
    assert result["expected_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_record_dry_run_accepts_current_payload_currentness_refs(
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
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    for path in (request_path, evidence_path, claim_map_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("{}", encoding="utf-8")
    claim_map_path.write_text("{}", encoding="utf-8")
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
                        "evidence_ledger": {"path": str(evidence_path)},
                        "claim_evidence_map": {"path": str(claim_map_path)},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "required_currentness_refs": [str(evidence_path), str(claim_map_path)],
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
            "required_input_refs": {
                "evidence_ledger": str(evidence_path),
                "claim_evidence_map": str(claim_map_path),
            },
            "record_payload": {
                "eval_id": "publication-eval::002::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "evidence_ledger": str(evidence_path),
                        "claim_evidence_map": str(claim_map_path),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "dry_run"
    assert result["identity_guard"]["matched"] is True
    assert result["payload_guard"]["matched"] is True
    assert result["payload_guard"]["reason"] is None
    assert result["payload_guard"]["mismatches"] == []
    assert result["written_files"] == []
    assert result["expected_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_record_dry_run_normalizes_stale_lifecycle_refs_to_current_input_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    current_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    evidence_path = current_paper_root / "evidence_ledger.json"
    claim_map_path = current_paper_root / "claim_evidence_map.json"
    current_prose_review_path = current_paper_root / "medical_prose_review.json"
    current_gate_projection_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    old_prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    old_gate_projection_path = (
        workspace_root
        / "runtime"
        / "quests"
        / study_id
        / "artifacts"
        / "reports"
        / "publishability_gate"
        / "latest.json"
    )
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (
        request_path,
        evidence_path,
        claim_map_path,
        current_prose_review_path,
        current_gate_projection_path,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
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
                        "evidence_ledger": {"path": str(evidence_path.resolve())},
                        "claim_evidence_map": {"path": str(claim_map_path.resolve())},
                        "medical_prose_review": {"path": str(current_prose_review_path.resolve())},
                        "publication_gate_projection": {"path": str(current_gate_projection_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [
                        str(old_gate_projection_path.resolve()),
                        str(evidence_path.resolve()),
                        str(claim_map_path.resolve()),
                        str(old_prose_review_path.resolve()),
                    ],
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
                "status": "executable_owner_action",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
                ),
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
            "stale_record_ref": current_record_ref,
            "required_currentness_refs": [
                str(current_gate_projection_path.resolve()),
                str(evidence_path.resolve()),
                str(claim_map_path.resolve()),
                str(current_prose_review_path.resolve()),
            ],
            "required_input_refs": {
                "evidence_ledger": str(evidence_path.resolve()),
                "claim_evidence_map": str(claim_map_path.resolve()),
                "medical_prose_review": str(current_prose_review_path.resolve()),
                "publication_gate_projection": str(current_gate_projection_path.resolve()),
            },
            "record_payload": {
                "eval_id": "publication-eval::003::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "evidence_ledger": str(evidence_path.resolve()),
                        "claim_evidence_map": str(claim_map_path.resolve()),
                        "medical_prose_review": str(current_prose_review_path.resolve()),
                        "publication_gate_projection": str(current_gate_projection_path.resolve()),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="return_to_ai_reviewer_workflow",
        expected_work_unit_id="ai_reviewer_medical_prose_quality_review",
        expected_work_unit_fingerprint=(
            "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
        ),
    )

    assert result["status"] == "dry_run"
    assert result["payload_guard"]["matched"] is True
    assert result["payload_guard"]["missing_observed_fields"] == []
    assert result["required_currentness_refs"] == [
        str(current_gate_projection_path.resolve()),
        str(evidence_path.resolve()),
        str(claim_map_path.resolve()),
        str(current_prose_review_path.resolve()),
    ]
    assert str(old_gate_projection_path.resolve()) not in result["required_currentness_refs"]
    assert str(old_prose_review_path.resolve()) not in result["required_currentness_refs"]
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_accepts_current_authoring_target_metadata(
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
    prose_review_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_prose_review.json"
    )
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
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
            "stale_record_ref": current_record_ref,
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

    assert result["status"] == "dry_run"
    assert result["payload_guard"]["matched"] is True
    assert result["payload_guard"]["mismatches"] == []
    assert result["payload_guard"]["missing_observed_fields"] == []
    assert result["written_files"] == []
