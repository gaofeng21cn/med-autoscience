from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.test_study_runtime_execution_control_intent import (
    _base_status_payload,
    _write_controller_decision_authorization,
    _write_publication_eval_work_unit_authority,
    _write_runtime_state,
)


def test_execute_noop_runtime_decision_adopts_quality_repair_receipt_with_targeted_specificity_targets(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "002-dm"
    quest_root = tmp_path / "runtime" / "quest-002"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-19T18:57:00+00:00",
        work_unit_fingerprint="publication-blockers::5a8873627ce31c8b",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair current claim-display traceability blockers.",
        },
    )
    _write_publication_eval_work_unit_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-002"},
        recorded_at="2026-05-19T18:58:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": "run-002"},
        recorded_at="2026-05-19T19:00:00+00:00",
    )
    report_path = quest_root / "artifacts" / "reports" / "analysis_claim_evidence_repair" / "latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "receipt_id": "analysis-claim-evidence-repair::002-dm::run-002",
                "study_id": "002-dm",
                "quest_id": "quest-002",
                "run_id": "run-002",
                "created_at": "2026-05-19T19:05:42Z",
                "lane": "analysis-campaign",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::5a8873627ce31c8b",
                "controller_action_invoked_first": {
                    "action": "run_quality_repair_batch",
                    "status": "executed",
                    "paper_write_authorized": True,
                    "generated_delivery_surfaces_authorized": False,
                },
                "targeted_publication_specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": "paper/claim_evidence_map.json",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": "paper/figures/figure_catalog.json",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": "artifacts/reports/medical_publication_surface/latest.json",
                    },
                ],
                "canonical_artifact_delta": {
                    "meaningful_artifact_delta": True,
                    "generated_package_surfaces_changed": False,
                    "changed_artifacts": [
                        {"path": "paper/results_narrative_map.json"},
                        {"path": "paper/figures/figure_catalog.json"},
                    ],
                },
                "verification": {
                    "json_validation": {"status": "passed"},
                    "medical_publication_surface_replay": {
                        "status": "blocked",
                        "table_figure_claim_map_status": "clear",
                        "mapped_claim_count": 3,
                        "figure_catalog_valid": True,
                        "claim_evidence_map_valid": True,
                        "results_narrative_map_valid": True,
                        "cleared_blocker": "table_figure_claim_map_missing_or_incomplete",
                        "remaining_blockers": ["methods_completeness_incomplete"],
                    },
                },
                "remaining_authority_boundaries": {
                    "publication_gate_allow_write": False,
                    "current_package_write_authorized": False,
                    "submission_minimal_refresh_authorized": False,
                    "next_required_owner_surface": "MAS/controller or publication gate",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": "run-002", "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["quest_id"] = "quest-002"
    status_payload["execution"]["quest_id"] = "quest-002"
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("DM002-style repair receipt must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    next_route = status.to_dict()["controller_work_unit_next_route"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate", "artifact_written"]
    assert lifecycle["terminal_consumed"] is False
    assert adoption["report_ref"] == str(report_path)
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert adoption["result"]["specificity_targets_repaired_or_classified"] == 3
    assert adoption["result"]["changed_artifacts_count"] == 2
    assert adoption["result"]["publication_gate_recheck_required"] is True
    assert next_route == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "publication_gate",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }
