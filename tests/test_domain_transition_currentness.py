from __future__ import annotations

import importlib
from pathlib import Path


def _status_payload(*, next_action: dict[str, object] | None = None) -> dict[str, object]:
    transition: dict[str, object] = {
        "decision_type": "ai_reviewer_re_eval",
        "route_target": "review",
        "controller_action": "return_to_ai_reviewer_workflow",
        "next_work_unit": {
            "unit_id": "ai_reviewer_medical_prose_quality_review",
            "summary": "Review current manuscript.",
        },
    }
    if next_action is not None:
        transition["next_action"] = next_action
    return {"domain_transition": transition}


def _canonical_next_action() -> dict[str, object]:
    return {
        "surface_kind": "mas_next_action_envelope",
        "action_id": "next-action-ai-reviewer",
        "idempotency_key": "next-action-key-ai-reviewer",
        "action_family": "runtime.opl_route",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": "sha256:ai-reviewer-current",
        "expected_output_contract": {"output_kind": "opl_transition_receipt"},
    }


def _write_controller_refs(study_root: Path) -> None:
    charter = study_root / "artifacts" / "controller" / "study_charter.json"
    publication_eval = study_root / "artifacts" / "publication_eval" / "latest.json"
    charter.parent.mkdir(parents=True)
    publication_eval.parent.mkdir(parents=True)
    charter.write_text('{"charter_id":"charter-001"}\n', encoding="utf-8")
    publication_eval.write_text('{"eval_id":"eval-001"}\n', encoding="utf-8")


def test_status_domain_transition_tick_request_ignores_legacy_only_transition(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_transition_currentness")
    _write_controller_refs(tmp_path)

    result = module.status_domain_transition_tick_request(
        study_root=tmp_path,
        status_payload=_status_payload(),
    )

    assert result is None


def test_status_domain_transition_tick_request_requires_canonical_next_action(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_transition_currentness")
    _write_controller_refs(tmp_path)

    result = module.status_domain_transition_tick_request(
        study_root=tmp_path,
        status_payload=_status_payload(next_action=_canonical_next_action()),
    )

    assert result["currentness_basis"] == "status_domain_transition"
    assert result["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert result["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    )
