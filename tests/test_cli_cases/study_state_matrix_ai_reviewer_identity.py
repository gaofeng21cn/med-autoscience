from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_existing_ai_reviewer_summary_redrives_when_consumed_identity_differs(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "next_owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "lane": "review",
                    "fingerprint": "sha256:current-reviewer-record",
                },
                "source_refs": {
                    "owner_route_currentness_basis": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                        "work_unit_fingerprint": "sha256:current-reviewer-record",
                    }
                },
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/previous.json",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:previous-reviewer-record",
                    "owner_route_currentness_basis": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        "work_unit_fingerprint": "sha256:previous-reviewer-record",
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    accounting = payload["progress_first_tick_accounting"]
    study = accounting["studies"][0]
    monitoring = payload["studies"][0]["monitoring"]

    assert exit_code == 0
    assert accounting["expected_owner_action_count"] == 1
    assert accounting["ready_for_owner_action_count"] == 1
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["owner_action_current"] is True
    assert study["monitoring_status"] == "ready_for_dispatch"
    assert study["throughput_bottleneck"] == "ready_owner_action"


def test_existing_ai_reviewer_summary_consumes_same_work_unit_when_receipt_has_fingerprint(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "owner_action_current": True,
                "next_owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "review",
                },
                "next_forced_delta": {
                    "owner_action": {
                        "work_unit_id": work_unit_id,
                    },
                },
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                    "canonical_work_unit_identity": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    accounting = payload["progress_first_tick_accounting"]
    study = accounting["studies"][0]
    monitoring = payload["studies"][0]["monitoring"]

    assert exit_code == 0
    assert accounting["expected_owner_action_count"] == 0
    assert accounting["ready_for_owner_action_count"] == 0
    assert monitoring["execution_state_kind"] == "receipt_consumed"
    assert monitoring["owner_action_current"] is False
    assert monitoring["dispatch_consumption"]["work_unit_id"] == work_unit_id
    assert monitoring["dispatch_consumption"]["work_unit_fingerprint"] == "sha256:current-ai-reviewer-record"
    assert study["monitoring_status"] == "receipt_consumed"
    assert study["throughput_bottleneck"] == "observability_only"


def test_existing_ai_reviewer_summary_consumes_scalar_work_unit_with_receipt_identity(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "owner_action_current": True,
                "next_owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": work_unit_id,
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "truth-snapshot::current-inputs",
                    "canonical_work_unit_identity": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": "truth-snapshot::current-inputs",
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    accounting = payload["progress_first_tick_accounting"]
    study = accounting["studies"][0]
    monitoring = payload["studies"][0]["monitoring"]

    assert exit_code == 0
    assert accounting["expected_owner_action_count"] == 0
    assert accounting["ready_for_owner_action_count"] == 0
    assert monitoring["execution_state_kind"] == "receipt_consumed"
    assert monitoring["owner_action_current"] is False
    assert study["monitoring_status"] == "receipt_consumed"
    assert study["throughput_bottleneck"] == "observability_only"


def test_existing_ai_reviewer_summary_consumes_action_type_handoff_with_same_receipt_identity(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    consumed_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    consumed_work_unit_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "owner_action_current": True,
                "next_owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": "return_to_ai_reviewer_workflow",
                "next_forced_delta": {
                    "owner_action": {
                        "next_owner": "ai_reviewer",
                        "work_unit_id": "return_to_ai_reviewer_workflow",
                        "allowed_actions": ["return_to_ai_reviewer_workflow"],
                    }
                },
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/latest.json",
                    "work_unit_id": consumed_work_unit_id,
                    "work_unit_fingerprint": consumed_work_unit_fingerprint,
                    "canonical_work_unit_identity": {
                        "work_unit_id": consumed_work_unit_id,
                        "work_unit_fingerprint": consumed_work_unit_fingerprint,
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    accounting = payload["progress_first_tick_accounting"]
    study = accounting["studies"][0]
    monitoring = payload["studies"][0]["monitoring"]

    assert exit_code == 0
    assert accounting["expected_owner_action_count"] == 0
    assert accounting["ready_for_owner_action_count"] == 0
    assert monitoring["execution_state_kind"] == "receipt_consumed"
    assert monitoring["owner_action_current"] is False
    assert monitoring["dispatch_consumption"]["work_unit_id"] == consumed_work_unit_id
    assert study["monitoring_status"] == "receipt_consumed"
    assert study["throughput_bottleneck"] == "observability_only"
