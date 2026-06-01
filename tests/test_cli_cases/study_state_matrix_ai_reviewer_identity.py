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
