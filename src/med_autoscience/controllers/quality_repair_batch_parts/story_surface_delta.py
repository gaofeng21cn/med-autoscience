from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.story_surface_work_units import (
    STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS,
    is_story_surface_delta_write_work_unit,
)


BLOCKED_REASON = "manuscript_story_surface_delta_missing"
WORK_UNIT_ID = "manuscript_story_repair"
AI_REVIEWER_RECHECK_WORK_UNIT_ID = "ai_reviewer_medical_prose_quality_review"


def blocker_supersedes_lifecycle(
    *,
    study_root: Path,
    lifecycle: Mapping[str, Any],
    batch_path: Path,
) -> bool:
    work_unit = lifecycle.get("work_unit")
    if not isinstance(work_unit, Mapping):
        return False
    if not is_story_surface_delta_write_work_unit(work_unit.get("unit_id")):
        return False
    source_eval_id = _non_empty_text(lifecycle.get("source_eval_id"))
    if source_eval_id is None:
        return False
    batch = _read_json_object(batch_path)
    if _non_empty_text(batch.get("source_eval_id")) != source_eval_id:
        return False
    if _non_empty_text(batch.get("next_owner")) != "write":
        return False
    if _non_empty_text(batch.get("blocked_reason")) == BLOCKED_REASON:
        return True
    evidence = batch.get("repair_execution_evidence")
    if isinstance(evidence, Mapping) and BLOCKED_REASON in _string_set(evidence.get("blockers")):
        return True
    repair_evidence = _read_json_object(
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "repair_execution_evidence"
        / "latest.json"
    )
    return BLOCKED_REASON in _string_set(repair_evidence.get("blockers"))


def ai_reviewer_recheck_supersedes_lifecycle(
    *,
    study_root: Path,
    lifecycle: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    repair_evidence_path: Path,
) -> bool:
    work_unit = lifecycle.get("work_unit")
    if not isinstance(work_unit, Mapping):
        return False
    if not is_story_surface_delta_write_work_unit(work_unit.get("unit_id")):
        return False
    source_eval_id = _non_empty_text(lifecycle.get("source_eval_id"))
    if source_eval_id is None:
        return False
    if _non_empty_text(publication_eval.get("eval_id")) != source_eval_id:
        return False
    repair_evidence = _read_json_object(repair_evidence_path)
    if not _repair_evidence_matches_completed_story_delta(
        repair_evidence,
        source_eval_id=source_eval_id,
    ):
        return False
    recheck_ref = _non_empty_text(repair_evidence.get("ai_reviewer_recheck_request_ref"))
    if recheck_ref is None or not Path(recheck_ref).expanduser().exists():
        return False
    return True


def ai_reviewer_recheck_action_from_story_delta(
    *,
    study_id: str,
    source_refs: list[str],
    completion_receipt_consumption: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "study_id": study_id,
        "decision_type": "ai_reviewer_re_eval",
        "route_target": "review",
        "next_work_unit": {
            "unit_id": AI_REVIEWER_RECHECK_WORK_UNIT_ID,
            "lane": "review",
            "summary": (
                "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair."
            ),
        },
        "controller_action": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "typed_blocker": None,
        "guard_boundary": {
            "runner_boundary": "mas_domain_read_model_only",
            "can_write_domain_truth": False,
            "can_execute_generic_state_machine": False,
            "opl_generic_runner_may_resume": False,
            "mas_owner_apply_receipt_required": False,
            "required_owner_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        },
        "source_refs": list(source_refs),
    }
    if completion_receipt_consumption:
        payload["completion_receipt_consumption"] = dict(completion_receipt_consumption)
    return payload


def _repair_evidence_matches_completed_story_delta(
    repair_evidence: Mapping[str, Any],
    *,
    source_eval_id: str,
) -> bool:
    if _non_empty_text(repair_evidence.get("status")) != "progress_delta_candidate":
        return False
    if repair_evidence.get("ai_reviewer_recheck_required") is not True:
        return False
    if repair_evidence.get("ai_reviewer_recheck_done") is not True:
        return False
    if _string_set(repair_evidence.get("blockers")):
        return False
    finding = repair_evidence.get("review_finding")
    if isinstance(finding, Mapping) and _non_empty_text(finding.get("source_eval_id")) != source_eval_id:
        return False
    repair_work_unit = repair_evidence.get("repair_work_unit")
    if not isinstance(repair_work_unit, Mapping):
        return False
    if not is_story_surface_delta_write_work_unit(repair_work_unit.get("unit_id")):
        return False
    hygiene = repair_evidence.get("manuscript_surface_hygiene")
    if not isinstance(hygiene, Mapping):
        return False
    return (
        _non_empty_text(hygiene.get("status")) == "clear"
        and hygiene.get("story_surface_delta_present") is True
        and bool(hygiene.get("story_surface_delta_refs"))
        and BLOCKED_REASON not in _string_set(hygiene.get("blockers"))
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        item = value.strip()
        return {item} if item else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _non_empty_text(item)) is not None}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AI_REVIEWER_RECHECK_WORK_UNIT_ID",
    "BLOCKED_REASON",
    "STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS",
    "WORK_UNIT_ID",
    "ai_reviewer_recheck_action_from_story_delta",
    "ai_reviewer_recheck_supersedes_lifecycle",
    "blocker_supersedes_lifecycle",
]
