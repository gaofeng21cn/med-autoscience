from __future__ import annotations

import importlib
import json
from pathlib import Path


def _missing_reference_context_request() -> dict[str, object]:
    return {
        "input_contract": {
            "all_required_refs_present": False,
            "missing_or_invalid_refs": ["opl_stage_folder_state_index_refs"],
            "required_refs": {
                "opl_stage_folder_state_index_refs": {
                    "relative_path": "opl-stage-folder://review/latest.json",
                    "status": "missing",
                    "missing_reasons": ["missing_ref:study_reference_context"],
                }
            },
        },
        "stage_knowledge_status": "missing",
        "stage_knowledge_missing_reasons": ["missing_ref:study_reference_context"],
    }


def test_runtime_escalation_ref_accepts_ai_reviewer_reference_context_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    assert (
        module.should_attach_runtime_escalation_ref(
            {
                "decision": "handoff_required",
                "quest_exists": True,
                "quest_status": "active",
                "reason": "opl_stage_attempt_admission_required",
                "ai_reviewer_request": _missing_reference_context_request(),
            }
        )
        is True
    )


def test_runtime_escalation_ref_reads_ai_reviewer_reference_context_gap(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    study_root = tmp_path / "studies" / "S1"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(_missing_reference_context_request(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    assert (
        module.should_attach_runtime_escalation_ref(
            {
                "decision": "handoff_required",
                "quest_exists": True,
                "quest_status": "active",
                "reason": "opl_stage_attempt_admission_required",
                "study_root": str(study_root),
            }
        )
        is True
    )


def test_runtime_escalation_ref_ignores_migrated_ai_reviewer_request_tombstone(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    study_root = tmp_path / "studies" / "S1"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "surface_kind": "legacy_control_surface_tombstone",
                "status": "migrated_to_provenance",
                "active_path_role": "domain_action_request_packet",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    assert (
        module.should_attach_runtime_escalation_ref(
            {
                "decision": "handoff_required",
                "quest_exists": True,
                "quest_status": "active",
                "reason": "opl_stage_attempt_admission_required",
                "study_root": str(study_root),
            }
        )
        is False
    )
