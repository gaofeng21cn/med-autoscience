from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "STABLE_STUDY_CHARTER_RELATIVE_PATH",
    "materialize_study_charter",
    "read_study_charter",
    "resolve_study_charter_ref",
    "stable_study_charter_path",
]


STABLE_STUDY_CHARTER_RELATIVE_PATH = Path("artifacts/controller/study_charter.json")
AUTONOMOUS_SCIENTIFIC_DECISIONS = (
    "analysis_plan_within_locked_direction",
    "evidence_generation_and_sufficiency_judgment",
    "manuscript_argumentation_and_revision",
    "journal_target_tradeoffs_within_frozen_quality_contract",
)
HUMAN_GATE_DECISIONS = (
    "direction_reset_or_primary_question_change",
    "major_claim_boundary_expansion",
    "external_release_or_submission_authorization",
)
FINAL_SCIENTIFIC_AUDIT_CHECKS = (
    "claim_traceability_to_evidence_ledger",
    "review_closure_against_review_ledger",
    "submission_readiness_against_paper_quality_contract",
)
DOWNSTREAM_CONTRACT_ROLES = {
    "evidence_ledger": "records evidence against evidence_expectations",
    "review_ledger": "records review closure against review_expectations",
    "final_audit": "audits scientific and paper-quality readiness against this charter",
}
DEFAULT_BOUNDED_ANALYSIS_ALLOWED_SCENARIOS = (
    "close_predeclared_evidence_gap_within_locked_direction",
    "close_predeclared_review_gap_within_locked_direction",
    "close_predeclared_submission_gap_within_locked_direction",
)
DEFAULT_BOUNDED_ANALYSIS_ALLOWED_TARGETS = (
    "minimum_sci_ready_evidence_package",
    "scientific_followup_questions",
    "manuscript_conclusion_redlines",
)
DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY = {
    "max_analysis_rounds_per_gate_window": 2,
    "max_targets_per_round": 3,
    "max_new_primary_claims": 0,
}
DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY = {
    "return_to_main_gate": "publication_eval",
    "return_to_mainline_action": "return_to_controller",
    "completion_criteria": [
        "all_requested_targets_closed",
        "budget_boundary_reached",
        "major_boundary_signal_detected",
    ],
    "required_updates": [
        "evidence_ledger",
        "review_ledger",
        "publication_eval",
    ],
}
def stable_study_charter_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_STUDY_CHARTER_RELATIVE_PATH).resolve()


def _non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _extract_target_journals(study_payload: dict[str, Any]) -> list[str]:
    shortlist = _string_list(study_payload.get("journal_shortlist"))
    if shortlist:
        return _dedupe_preserve_order(shortlist)

    raw_submission_targets = study_payload.get("submission_targets")
    if not isinstance(raw_submission_targets, list):
        return []

    names: list[str] = []
    for item in raw_submission_targets:
        if isinstance(item, dict):
            for key in ("journal_name", "journal", "name", "target"):
                text = _non_empty_string(item.get(key))
                if text is not None:
                    names.append(text)
                    break
            continue
        text = str(item).strip()
        if text:
            names.append(text)
    return _dedupe_preserve_order(names)


def _mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return dict(value)


def _non_negative_int(value: object, *, default: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return default
    return value


def _materialize_bounded_analysis_contract(study_payload: dict[str, Any]) -> dict[str, Any]:
    raw_contract = _mapping(study_payload.get("bounded_analysis"))
    raw_budget_boundary = _mapping(raw_contract.get("budget_boundary"))
    raw_completion_boundary = _mapping(raw_contract.get("completion_boundary"))
    allowed_scenarios = _string_list(raw_contract.get("allowed_scenarios")) or list(
        DEFAULT_BOUNDED_ANALYSIS_ALLOWED_SCENARIOS
    )
    allowed_targets = _string_list(raw_contract.get("allowed_targets")) or list(
        DEFAULT_BOUNDED_ANALYSIS_ALLOWED_TARGETS
    )
    completion_criteria = _string_list(raw_completion_boundary.get("completion_criteria")) or list(
        DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["completion_criteria"]
    )
    required_updates = _string_list(raw_completion_boundary.get("required_updates")) or list(
        DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["required_updates"]
    )
    return {
        "default_owner": "mas",
        "allowed_scenarios": allowed_scenarios,
        "allowed_targets": allowed_targets,
        "budget_boundary": {
            "max_analysis_rounds_per_gate_window": _non_negative_int(
                raw_budget_boundary.get("max_analysis_rounds_per_gate_window"),
                default=DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY["max_analysis_rounds_per_gate_window"],
            ),
            "max_targets_per_round": _non_negative_int(
                raw_budget_boundary.get("max_targets_per_round"),
                default=DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY["max_targets_per_round"],
            ),
            "max_new_primary_claims": _non_negative_int(
                raw_budget_boundary.get("max_new_primary_claims"),
                default=DEFAULT_BOUNDED_ANALYSIS_BUDGET_BOUNDARY["max_new_primary_claims"],
            ),
        },
        "completion_boundary": {
            "return_to_main_gate": _non_empty_string(raw_completion_boundary.get("return_to_main_gate"))
            or str(DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["return_to_main_gate"]),
            "return_to_mainline_action": _non_empty_string(
                raw_completion_boundary.get("return_to_mainline_action")
            )
            or str(DEFAULT_BOUNDED_ANALYSIS_COMPLETION_BOUNDARY["return_to_mainline_action"]),
            "completion_criteria": completion_criteria,
            "required_updates": required_updates,
        },
    }


def resolve_study_charter_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_study_charter_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("study charter reader only accepts the stable controller artifact")
    return stable_path


def read_study_charter(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    charter_path = resolve_study_charter_ref(study_root=study_root, ref=ref)
    payload = json.loads(charter_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"study charter payload must be a JSON object: {charter_path}")
    return payload


def materialize_study_charter(
    *,
    study_root: Path,
    study_id: str,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
    required_first_anchor: str | None = None,
) -> dict[str, str]:
    charter_path = stable_study_charter_path(study_root=study_root)
    title = _non_empty_string(study_payload.get("title")) or study_id
    paper_framing_summary = _non_empty_string(study_payload.get("paper_framing_summary"))
    minimum_sci_ready_evidence_package = _string_list(study_payload.get("minimum_sci_ready_evidence_package"))
    scientific_followup_questions = _string_list(study_payload.get("scientific_followup_questions"))
    explanation_targets = _string_list(study_payload.get("explanation_targets"))
    manuscript_conclusion_redlines = _string_list(study_payload.get("manuscript_conclusion_redlines"))
    publication_objective = (
        _non_empty_string(study_payload.get("primary_question"))
        or paper_framing_summary
        or title
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "charter_id": f"charter::{study_id}::v1",
        "study_id": study_id,
        "title": title,
        "publication_objective": publication_objective,
        "paper_framing_summary": paper_framing_summary,
        "minimum_sci_ready_evidence_package": minimum_sci_ready_evidence_package,
        "scientific_followup_questions": scientific_followup_questions,
        "explanation_targets": explanation_targets,
        "manuscript_conclusion_redlines": manuscript_conclusion_redlines,
        "autonomy_envelope": {
            "decision_policy": _non_empty_string(execution.get("decision_policy")) or "autonomous",
            "launch_profile": _non_empty_string(execution.get("launch_profile")) or "continue_existing_state",
            "required_first_anchor": _non_empty_string(required_first_anchor),
            "direction_lock_state": "startup_frozen",
            "autonomous_scientific_decision_scope": {
                "phase": "post_direction_lock",
                "default_owner": "mas",
                "covered_decisions": list(AUTONOMOUS_SCIENTIFIC_DECISIONS),
            },
            "human_gate_boundary": {
                "policy": "major_boundary_only",
                "required_human_decisions": list(HUMAN_GATE_DECISIONS),
            },
            "final_scientific_audit_boundary": {
                "audit_surfaces": ["evidence_ledger", "review_ledger", "final_audit"],
                "required_checks": list(FINAL_SCIENTIFIC_AUDIT_CHECKS),
            },
        },
        "paper_quality_contract": {
            "frozen_at_startup": True,
            "target_journals": _extract_target_journals(study_payload),
            "reporting_expectations": {
                "paper_framing_summary": paper_framing_summary,
                "explanation_targets": explanation_targets,
            },
            "evidence_expectations": {
                "minimum_sci_ready_evidence_package": minimum_sci_ready_evidence_package,
            },
            "review_expectations": {
                "scientific_followup_questions": scientific_followup_questions,
                "manuscript_conclusion_redlines": manuscript_conclusion_redlines,
            },
            "bounded_analysis": _materialize_bounded_analysis_contract(study_payload),
            "downstream_contract_roles": dict(DOWNSTREAM_CONTRACT_ROLES),
        },
    }
    charter_path.parent.mkdir(parents=True, exist_ok=True)
    charter_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "charter_id": str(payload["charter_id"]),
        "artifact_path": str(charter_path),
    }
