from __future__ import annotations

import importlib
import json
from pathlib import Path


def _missing_reference_context_request() -> dict[str, object]:
    return {
        "input_contract": {
            "all_required_refs_present": False,
            "missing_or_invalid_refs": ["stage_knowledge_packet"],
            "required_refs": {
                "stage_knowledge_packet": {
                    "relative_path": "artifacts/stage_knowledge/review/latest.json",
                    "status": "missing",
                    "missing_reasons": ["missing_ref:study_reference_context"],
                }
            },
        },
        "stage_knowledge_status": "missing",
        "stage_knowledge_missing_reasons": ["missing_ref:study_reference_context"],
    }


def test_should_refresh_startup_hydration_while_blocked_accepts_ai_reviewer_reference_context_gap() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")

    assert (
        module.should_refresh_startup_hydration_while_blocked(
            {
                "decision": "blocked",
                "quest_exists": True,
                "quest_status": "active",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "ai_reviewer_request": _missing_reference_context_request(),
            }
        )
        is True
    )


def test_should_refresh_startup_hydration_while_blocked_reads_ai_reviewer_reference_context_gap(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    study_root = tmp_path / "studies" / "S1"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(_missing_reference_context_request(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    assert (
        module.should_refresh_startup_hydration_while_blocked(
            {
                "decision": "blocked",
                "quest_exists": True,
                "quest_status": "active",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "study_root": str(study_root),
            }
        )
        is True
    )
