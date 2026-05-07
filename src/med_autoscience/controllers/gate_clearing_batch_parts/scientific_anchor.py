from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.study_charter import materialize_study_charter
from med_autoscience.controllers.gate_clearing_batch_parts.io_utils import (
    non_empty_text,
    read_json,
    read_yaml,
    string_list,
    write_yaml,
)
from med_autoscience.controllers.gate_clearing_batch_parts.runtime_paths import (
    latest_scientific_anchor_mapping_path,
)


def eligible_mapping_payload(*, quest_root: Path, study_root: Path) -> tuple[Path | None, dict[str, Any]]:
    mapping_path = latest_scientific_anchor_mapping_path(quest_root=quest_root)
    if mapping_path is None:
        return None, {}
    stable_charter_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller" / "study_charter.json"
    stable_charter = read_json(stable_charter_path)
    if string_list(stable_charter.get("scientific_followup_questions")) and string_list(
        stable_charter.get("explanation_targets")
    ):
        return mapping_path, {}
    payload = read_json(mapping_path)
    if not payload:
        return mapping_path, {}
    proposed_questions = string_list(payload.get("proposed_scientific_followup_questions"))
    proposed_targets = string_list(payload.get("proposed_explanation_targets"))
    if not proposed_questions or not proposed_targets:
        return mapping_path, {}
    return mapping_path, payload


def freeze_scientific_anchor_fields(
    *,
    study_root: Path,
    study_id: str,
    profile: WorkspaceProfile,
    mapping_path: Path,
    study_runtime_router_controller: Any,
) -> dict[str, Any]:
    study_yaml_path = Path(study_root).expanduser().resolve() / "study.yaml"
    study_payload = read_yaml(study_yaml_path)
    mapping_payload = read_json(mapping_path)
    proposed_questions = string_list(mapping_payload.get("proposed_scientific_followup_questions"))
    proposed_targets = string_list(mapping_payload.get("proposed_explanation_targets"))
    clinician_target = non_empty_text(mapping_payload.get("clinician_facing_interpretation_target"))
    if clinician_target is not None and clinician_target not in proposed_targets:
        proposed_targets.append(clinician_target)
    if not proposed_questions or not proposed_targets:
        return {
            "status": "skipped",
            "reason": "scientific anchor mapping did not expose non-empty proposed targets",
            "mapping_path": str(mapping_path),
        }
    study_payload["scientific_followup_questions"] = proposed_questions
    study_payload["explanation_targets"] = proposed_targets
    write_yaml(study_yaml_path, study_payload)
    charter_ref = materialize_study_charter(
        study_root=study_root,
        study_id=study_id,
        study_payload=study_payload,
        execution=study_runtime_router_controller._execution_payload(study_payload, profile=profile),
        required_first_anchor=non_empty_text((study_payload.get("execution") or {}).get("required_first_anchor")),
    )
    return {
        "status": "updated",
        "mapping_path": str(mapping_path),
        "study_yaml_path": str(study_yaml_path),
        "charter_ref": charter_ref,
        "scientific_followup_question_count": len(proposed_questions),
        "explanation_target_count": len(proposed_targets),
    }
