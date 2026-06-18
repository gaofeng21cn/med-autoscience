from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_receipt_consumption,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_default_executor_consumed_receipt_exposes_canonical_work_unit_identity(tmp_path: Path) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    work_unit_id = "dm002_same_line_publication_paper_repair"
    work_unit_fingerprint = "dm002_same_line_publication_paper_repair_20260521"
    owner_route = {
        "route_epoch": "truth-event-000017-bac190eb1c889a78",
        "truth_epoch": "truth-event-000017-bac190eb1c889a78",
        "runtime_health_epoch": "runtime-health-after-execution",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000017-bac190eb1c889a78",
                "runtime_health_epoch": "runtime-health-after-execution",
                "source_eval_id": "publication-eval::dm002::ai-reviewer-routeback",
                "work_unit_fingerprint": work_unit_fingerprint,
                "work_unit_id": work_unit_id,
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
            },
            "study_truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "runtime_health_epoch": "runtime-health-after-execution",
            "source_eval_id": "publication-eval::dm002::ai-reviewer-routeback",
            "work_unit_fingerprint": work_unit_fingerprint,
            "work_unit_id": work_unit_id,
        },
        "idempotency_key": "owner-route::dm002::same-line-repair",
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "owner_callable_adapter_receipt",
                    "schema_version": 1,
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::identity",
                    "idempotency_key": owner_route["idempotency_key"],
                    "current_owner_route": owner_route,
                    "prompt_contract": {"owner_route": owner_route},
                    "owner_result": {
                        "status": "executed",
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [{"path": str(study_root / "paper" / "draft.md")}],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["canonical_work_unit_identity"] == {
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_id": "publication-eval::dm002::ai-reviewer-routeback",
        "truth_epoch": "truth-event-000017-bac190eb1c889a78",
        "runtime_health_epoch": "runtime-health-after-execution",
    }
    assert receipt["owner_route_currentness_basis"] == receipt["canonical_work_unit_identity"]
