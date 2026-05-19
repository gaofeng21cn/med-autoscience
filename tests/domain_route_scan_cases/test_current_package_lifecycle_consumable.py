from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _submission_qc_targets(*, study_root: Path, quest_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "submission_surface_qc_failure_present",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "submission_surface_qc_failure_present",
        },
        {
            "target_kind": "table",
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"),
            "blocking_reason": "submission_surface_qc_failure_present",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "submission_surface_qc_failure_present",
        },
        {
            "target_kind": "source_path",
            "target_id": "publication_gate_source_path",
            "source_path": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "blocking_reason": "submission_surface_qc_failure_present",
        },
    ]


def test_scan_domain_routes_keeps_current_package_freshness_lifecycle_consumable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    work_unit_fingerprint = "publication-blockers::submission-qc"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::submission-qc",
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_minimal_refresh",
                    "lane": "finalize",
                    "summary": "Refresh submission surfaces after submission QC failure.",
                },
                "specificity_targets": _submission_qc_targets(study_root=study_root, quest_root=quest_root),
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-submission-qc-refresh",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh submission surfaces after submission QC failure.",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-submission-qc",
            "source_signature": "truth-source-submission-qc",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "runtime_blocked",
        "paper_stage": "bundle_stage_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "current_package_freshness_required",
            "next_owner": "artifact_os",
            "external_supervisor_required": False,
            "auto_apply_allowed": True,
            "top_action": {
                "action_type": "controller_repair",
                "repair_kind": "bounded_work_unit_redrive",
                "owner": "mas_controller",
                "auto_apply_allowed": True,
            },
        },
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in result["action_queue"]] == ["current_package_freshness_required"]
    assert study["owner_route"]["next_owner"] == "artifact_os"
    assert study["owner_route"]["allowed_actions"] == ["current_package_freshness_required"]
