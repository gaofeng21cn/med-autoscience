from __future__ import annotations

import hashlib
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


def test_ai_reviewer_record_materializer_rejects_stale_authoring_target_before_write(
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

    result = module.materialize_ai_reviewer_publication_eval_record(
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
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "payload_currentness_mismatch"
    assert result["payload_guard"]["matched"] is False
    assert result["publication_eval_record_surface"] == "not_written"
    assert result["written_files"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


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
    old_prose_review = study_root / "paper" / "review" / "legacy_medical_prose_review.json"
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


def test_ai_reviewer_record_observe_writes_non_authority_authoring_target(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260629T010203Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, evidence_path, claim_map_path):
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
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [
                        str(evidence_path.resolve()),
                        str(claim_map_path.resolve()),
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
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                ),
            },
        },
    )
    output_path = tmp_path / "authoring_target.json"

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-record",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--entry-mode",
            "owner_consumption_payload_guard",
            "--observe",
            "--authoring-target-output",
            str(output_path),
            "--expected-owner",
            "ai_reviewer",
            "--expected-action-type",
            "return_to_ai_reviewer_workflow",
            "--expected-work-unit-id",
            "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "--expected-work-unit-fingerprint",
            "domain-transition::ai_reviewer_re_eval::"
            "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        ]
    )
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["status"] == "dry_run"
    assert result["authoring_target"]["output_ref"] == str(output_path.resolve())
    assert result["authoring_target"]["writes_authority_surfaces"] is False
    assert result["written_files"] == [str(output_path.resolve())]
    assert written["surface"] == "ai_reviewer_record_payload_authoring_target"
    assert written["stale_record_ref"] == current_record_ref
    assert written["required_input_refs"] == {
        "evidence_ledger": str(evidence_path.resolve()),
        "claim_evidence_map": str(claim_map_path.resolve()),
    }
    assert written["required_currentness_refs"] == [
        str(evidence_path.resolve()),
        str(claim_map_path.resolve()),
    ]
    assert written["record_payload"] == {}
    assert written["authority_boundary"]["publication_eval_latest_write_allowed"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_authoring_target_output_refuses_study_root_write(
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
    for path in (request_path, evidence_path):
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
                "input_contract": {"required_refs": {"evidence_ledger": {"path": str(evidence_path.resolve())}}},
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "required_currentness_refs": [str(evidence_path.resolve())],
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
            "current_work_unit": {"owner": "ai_reviewer"},
        },
    )

    try:
        module.plan_ai_reviewer_publication_eval_record_materialization(
            profile=profile,
            study_id=study_id,
            study_root=None,
            entry_mode="owner_consumption_payload_guard",
            source="cli",
            authoring_target_output=study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "record_production_payloads" / "return_to_ai_reviewer_workflow_payload.json",
        )
    except ValueError as exc:
        assert "must not be inside the study root" in str(exc)
    else:
        raise AssertionError("expected study-root authoring target output to be rejected")


def test_ai_reviewer_payload_guard_prefers_stable_medical_prose_review_over_legacy_request_ref(
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
    stable_prose_review = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    legacy_prose_review = (
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
            / "20260628T193408Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, stable_prose_review, legacy_prose_review):
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
                        "medical_prose_review": {"path": str(legacy_prose_review.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(stable_prose_review.resolve())],
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
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review",
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
            "stale_record_ref": current_record_ref,
            "required_currentness_refs": [str(stable_prose_review.resolve())],
            "required_input_refs": {"medical_prose_review": str(stable_prose_review.resolve())},
            "record_payload": {
                "eval_id": "publication-eval::003::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "medical_prose_review": str(stable_prose_review.resolve()),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="return_to_ai_reviewer_workflow",
        expected_work_unit_id="ai_reviewer_medical_prose_quality_review",
        expected_work_unit_fingerprint="domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review",
    )

    assert result["status"] == "dry_run"
    assert result["payload_guard"]["matched"] is True
    assert result["payload_guard"]["mismatches"] == []
    assert result["payload_guard"]["record_payload_mismatches"] == []
    assert result["required_input_refs"]["medical_prose_review"] == str(stable_prose_review.resolve())
    assert result["payload_target_metadata_refresh"]["current_metadata"]["required_input_refs"][
        "medical_prose_review"
    ] == str(stable_prose_review.resolve())
    assert str(legacy_prose_review.resolve()) not in json.dumps(
        result["payload_target_metadata_refresh"]["current_metadata"]
    )
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_rejects_schema_invalid_authoring_target(
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
    paper_root = study_root / "paper"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_path = paper_root / "draft.md"
    evidence_path = paper_root / "evidence_ledger.json"
    review_path = paper_root / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, manuscript_path, evidence_path, review_path, charter_path):
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
                        "manuscript": {"path": str(manuscript_path.resolve())},
                        "evidence_ledger": {"path": str(evidence_path.resolve())},
                        "review_ledger": {"path": str(review_path.resolve())},
                        "study_charter": {"path": str(charter_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(evidence_path.resolve())],
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
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "stale_record_ref": current_record_ref,
            "required_currentness_refs": [str(evidence_path.resolve())],
            "required_input_refs": {
                "manuscript": str(manuscript_path.resolve()),
                "evidence_ledger": str(evidence_path.resolve()),
                "review_ledger": str(review_path.resolve()),
                "study_charter": str(charter_path.resolve()),
            },
            "record_payload": {
                "schema_version": 1,
                "eval_id": "publication-eval::002::current",
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2026-06-29T00:00:00Z",
                "evaluation_scope": "publication",
                "charter_context_ref": {
                    "ref": str(charter_path.resolve()),
                    "charter_id": f"charter::{study_id}::v1",
                    "publication_objective": "Evaluate current inputs.",
                },
                "runtime_context_refs": {
                    "runtime_escalation_ref": str((study_root / "runtime_escalation.json").resolve()),
                    "main_result_ref": str(evidence_path.resolve()),
                    "unexpected_extra_ref": str(evidence_path.resolve()),
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(paper_root.resolve()),
                    "submission_minimal_ref": str((paper_root / "submission_minimal.json").resolve()),
                },
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "source_refs": [str(evidence_path.resolve())],
                    "ai_reviewer_required": False,
                    "mechanical_projection_used_as_quality_authority": False,
                },
                "verdict": {
                    "overall_verdict": "blocked",
                    "primary_claim_status": "partial",
                    "summary": "Current record is not submission-ready.",
                    "stop_loss_pressure": "watch",
                },
                "gaps": [
                    {
                        "gap_id": "schema-invalid-extra-runtime-ref",
                        "gap_type": "delivery",
                        "severity": "must_fix",
                        "summary": "The authoring target must fail in dry-run before materialization.",
                        "evidence_refs": [str(evidence_path.resolve())],
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "route-controller",
                        "action_type": "return_to_controller",
                        "priority": "now",
                        "reason": "Schema-invalid authoring target cannot be consumed.",
                        "evidence_refs": [str(evidence_path.resolve())],
                        "requires_controller_decision": True,
                    }
                ],
                "reviewer_operating_system": {
                    "input_bundle": {
                        "manuscript": str(manuscript_path.resolve()),
                        "evidence_ledger": str(evidence_path.resolve()),
                        "review_ledger": str(review_path.resolve()),
                        "study_charter": str(charter_path.resolve()),
                    }
                },
            },
        },
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "record_payload_schema_invalid"
    assert result["payload_guard"]["matched"] is True
    assert result["record_schema_guard"]["matched"] is False
    assert result["record_schema_guard"]["error"]
    assert result["written_files"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_build_production_trace_covers_extra_required_currentness_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    paper_root = study_root / "paper"
    study_yaml = study_root / "study.yaml"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_path = paper_root / "draft.md"
    evidence_path = paper_root / "evidence_ledger.json"
    review_path = paper_root / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    blueprint_path = paper_root / "medical_manuscript_blueprint.json"
    claim_map_path = paper_root / "claim_evidence_map.json"
    prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    prose_request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    gate_path = study_root / "runtime" / "publishability_gate" / "latest.json"
    submission_path = paper_root / "submission_minimal.json"
    claim_map_payload = {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary care treatment gaps remain clinically important.",
                "status": "draft",
                "paper_role": "primary_result",
                "display_bindings": ["table-1"],
                "sections": ["Results"],
                "evidence_items": [
                    {
                        "item_id": "evidence-primary",
                        "support_level": "partial",
                        "source_paths": [str(evidence_path.resolve())],
                    }
                ],
            }
        ]
    }
    evidence_ledger_payload = {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary care treatment gaps remain clinically important.",
                "status": "draft",
                "submission_scope": "current_submission_minimal",
                "evidence": [
                    {
                        "evidence_id": "evidence-primary",
                        "kind": "analysis_result",
                        "source_paths": [str(evidence_path.resolve())],
                        "support_level": "partial",
                        "summary": "Minimal fixture evidence for trace currentness coverage.",
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "gap-primary",
                        "description": "Fixture gap remains for submission readiness.",
                        "submission_impact": "blocks final submission readiness",
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "repair-primary",
                        "priority": "now",
                        "description": "Repair evidence before submission.",
                    }
                ],
            }
        ]
    }
    for path, body in (
        (request_path, "{}"),
        (manuscript_path, "current manuscript"),
        (evidence_path, json.dumps(evidence_ledger_payload)),
        (review_path, '{"review": true}'),
        (charter_path, '{"charter": true}'),
        (blueprint_path, '{"blueprint": true}'),
        (claim_map_path, json.dumps(claim_map_payload)),
        (prose_review_path, '{"medical_journal_prose_quality": {"route_back_recommendation": {"required": true, "route_target": "write"}}}'),
        (gate_path, '{"gate": "blocked"}'),
        (submission_path, "{}"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    manuscript_digest = "sha256:" + hashlib.sha256(manuscript_path.read_bytes()).hexdigest()
    prose_review_path.write_text(
        json.dumps(
            {
                "assessment_provenance": {
                    "request_digest": "sha256:test-request",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": manuscript_digest,
                },
                "medical_journal_prose_quality": {
                    "status": "partial",
                    "overall_style_verdict": "revise",
                    "route_back_recommendation": {"required": True, "route_target": "write"},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    prose_request_path.write_text(
        json.dumps(
            {
                "request_digest": "sha256:test-request",
                "manuscript": {
                    "path": str(manuscript_path.resolve()),
                    "digest": manuscript_digest,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    study_yaml.write_text(
        f"study_id: {study_id}\nquest_id: {study_id}\n",
        encoding="utf-8",
    )
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260629T010203Z_publication_eval_record.json"
        ).resolve()
    )
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
                        "manuscript": {"path": str(manuscript_path.resolve())},
                        "evidence_ledger": {"path": str(evidence_path.resolve())},
                        "review_ledger": {"path": str(review_path.resolve())},
                        "study_charter": {"path": str(charter_path.resolve())},
                        "medical_manuscript_blueprint": {"path": str(blueprint_path.resolve())},
                        "claim_evidence_map": {"path": str(claim_map_path.resolve())},
                        "medical_prose_review": {"path": str(prose_review_path.resolve())},
                        "publication_gate_projection": {"path": str(gate_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [
                        str(evidence_path.resolve()),
                        str(charter_path.resolve()),
                        str(gate_path.resolve()),
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    contract = importlib.import_module("med_autoscience.policies").build_ai_reviewer_operating_system_contract(
        importlib.import_module("med_autoscience.policies").DEFAULT_PUBLICATION_CRITIQUE_POLICY
    )
    quality_assessment = {
        dimension: {
            "status": "blocked",
            "summary": f"{dimension} needs repair.",
            "reviewer_reason": f"{dimension} needs repair.",
            "evidence_refs": [str(gate_path.resolve())],
        }
        for dimension in contract["rubric_dimensions"]
    }
    record_payload = {
        "stale_record_ref": current_record_ref,
        "required_currentness_refs": [
            str(evidence_path.resolve()),
            str(charter_path.resolve()),
            str(gate_path.resolve()),
        ],
        "required_input_refs": {
            "manuscript": str(manuscript_path.resolve()),
            "evidence_ledger": str(evidence_path.resolve()),
            "review_ledger": str(review_path.resolve()),
            "study_charter": str(charter_path.resolve()),
            "medical_manuscript_blueprint": str(blueprint_path.resolve()),
            "claim_evidence_map": str(claim_map_path.resolve()),
            "medical_prose_review": str(prose_review_path.resolve()),
            "publication_gate_projection": str(gate_path.resolve()),
        },
        "record_payload": {
            "schema_version": 1,
            "eval_id": "publication-eval::003::current",
            "study_id": study_id,
            "quest_id": study_id,
            "emitted_at": "2026-06-29T00:00:00Z",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(charter_path.resolve()),
                "charter_id": f"charter::{study_id}::v1",
                "publication_objective": "Evaluate current inputs.",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str((study_root / "runtime_escalation.json").resolve()),
                "main_result_ref": str(evidence_path.resolve()),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(paper_root.resolve()),
                "submission_minimal_ref": str(submission_path.resolve()),
            },
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [str(evidence_path.resolve())],
                "ai_reviewer_required": False,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "quality_assessment": quality_assessment,
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Current record is not submission-ready.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "extra-currentness-ref",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "The extra required currentness ref must be covered.",
                    "evidence_refs": [str(gate_path.resolve())],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "route-write",
                    "action_type": "route_back_same_line",
                    "route_target": "write",
                    "route_key_question": "Repair the publication gate blockers before submission.",
                    "route_rationale": "The current reviewer record still routes back to writing repair.",
                    "priority": "now",
                    "reason": "Gate remains blocked.",
                    "evidence_refs": [str(gate_path.resolve())],
                    "requires_controller_decision": True,
                }
            ],
            "future_facing_limitations_plan": [
                {
                    "limitation": "Residual reporting gap.",
                    "impact_on_claim": "Limits submission readiness.",
                    "required_future_analysis_data_or_design": "Complete reporting repair.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
            "sci_clinical_registry_review": [
                {
                    "concern_id": f"extra-currentness-ref-{domain}",
                    "domain": domain,
                    "status": "blocked",
                    "severity": "must_fix",
                    "finding": f"{domain} remains part of the reviewer trace.",
                    "evidence_refs": [str(gate_path.resolve())],
                    "required_disposition": "revise",
                }
                for domain in contract["sci_clinical_registry_review"]["required_domains"]
            ],
            "reviewer_operating_system": {
                "input_bundle": {
                    "manuscript": str(manuscript_path.resolve()),
                    "evidence_ledger": str(evidence_path.resolve()),
                        "review_ledger": str(review_path.resolve()),
                        "study_charter": str(charter_path.resolve()),
                        "medical_manuscript_blueprint": str(blueprint_path.resolve()),
                        "claim_evidence_map": str(claim_map_path.resolve()),
                        "medical_prose_review": str(prose_review_path.resolve()),
                        "publication_gate_projection": str(gate_path.resolve()),
                }
            },
        },
    }

    result = module.materialize_ai_reviewer_publication_eval_record(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        record=record_payload["record_payload"],
        source="test",
        build_production_trace=True,
    )

    written = json.loads(Path(result["publication_eval_record_ref"]).read_text(encoding="utf-8"))
    currentness = written["reviewer_operating_system"]["currentness_checks"]
    assert currentness["study_charter"]["ref"] == str(charter_path.resolve())
    assert currentness["study_charter"]["digest"].startswith("sha256:")
    assert currentness["publication_gate_projection"]["ref"] == str(gate_path.resolve())
    assert currentness["publication_gate_projection"]["digest"].startswith("sha256:")
