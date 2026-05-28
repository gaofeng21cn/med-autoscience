from __future__ import annotations

import importlib
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.reviewer_os_fixture_helpers import (
    claim_evidence_alignment_digest,
    claim_evidence_map_payload,
    evidence_ledger_payload,
    ready_claim_evidence_alignment_gate,
)


MODULE_NAME = "med_autoscience.publication_eval_latest"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _minimal_payload(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "External validation cohort is still missing.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "results" / "main_result.json"),
                ],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Controller must decide whether to invest in external validation.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                ],
                "requires_controller_decision": True,
            }
        ],
    }


def _quality_assessment(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical framing is stable.",
            "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Core evidence is traceable.",
            "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
        },
        "novelty_positioning": {
            "status": "partial",
            "summary": "Contribution boundary is defined but still needs tightening.",
            "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
        },
        "medical_journal_prose_quality": {
            "status": "partial",
            "summary": "AI reviewer found prose that needs a journal-voice revision pass before closure.",
            "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
            "reviewer_reason": "Results flow still follows displays more than clinical findings.",
            "reviewer_revision_advice": "Rewrite representative figure-led sentences as finding-led sentences.",
            "reviewer_next_round_focus": "Results main finding and Discussion principal finding paragraphs.",
        },
        "human_review_readiness": {
            "status": "partial",
            "summary": "Human-facing package is not ready yet.",
            "evidence_refs": [str(study_root / "paper" / "submission_minimal" / "submission_manifest.json")],
        },
    }


def _reviewer_operating_system(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "c" * 64
    input_bundle = {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    rubric_scores = {
        dimension: {
            "status": "partial" if dimension in {"novelty_positioning", "human_review_readiness"} else "ready",
            "rationale": f"{dimension} was judged from manuscript and ledger evidence.",
            "evidence_refs": [
                str(study_root / "paper" / "manuscript.md"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
        }
        for dimension in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "medical_journal_prose_quality",
            "human_review_readiness",
        )
    }
    claim_alignment = ready_claim_evidence_alignment_gate(
        claim_evidence_map_ref=input_bundle["claim_evidence_map"],
        evidence_ledger_ref=input_bundle["evidence_ledger"],
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": input_bundle,
        "rubric_scores": rubric_scores,
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": score["status"],
                "rationale": score["rationale"],
            }
            for dimension, score in rubric_scores.items()
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": request_digest,
                "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
                "manuscript_digest": manuscript_digest,
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            },
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "ready",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": "sha256:" + "d" * 64,
            "claim_evidence_alignment_digest": claim_evidence_alignment_digest(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": "ai-reviewer-publication-eval::publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "fail_closed_when_missing": True,
            "missing_required_fields": [],
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Current AI reviewer closure depends on the manuscript and ledger snapshot.",
                "impact_on_claim": "Claim strength must remain tied to the reviewed evidence snapshot.",
                "required_future_analysis_data_or_design": "Rerun AI reviewer if the manuscript or evidence ledger changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "revise_medical_journal_prose",
            "rationale": "The next pass should repair prose and human-review readiness before closure.",
        },
    }


def test_resolve_publication_eval_latest_ref_defaults_to_eval_owned_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_publication_eval_latest_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "publication_eval" / "latest.json").resolve()


def test_read_publication_eval_latest_reads_typed_latest_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved == {
        **payload,
        "assessment_provenance": {
            **payload["assessment_provenance"],
            "mechanical_projection_used_as_quality_authority": False,
        },
    }


def test_read_publication_eval_latest_accepts_quality_assessment(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = {
        "clinical_significance": {
            "status": "partial",
            "summary": "Clinical framing exists but interpretation targets remain incomplete.",
            "evidence_refs": [payload["delivery_context_refs"]["paper_root_ref"]],
        },
        "evidence_strength": {
            "status": "blocked",
            "summary": "Paper-facing evidence surface is still incomplete.",
            "evidence_refs": [payload["runtime_context_refs"]["main_result_ref"]],
        },
        "novelty_positioning": {
            "status": "underdefined",
            "summary": "Novelty framing has not been frozen in the charter.",
            "evidence_refs": [payload["charter_context_ref"]["ref"]],
        },
        "human_review_readiness": {
            "status": "blocked",
            "summary": "Human-facing package is not ready yet.",
            "evidence_refs": [payload["delivery_context_refs"]["submission_minimal_ref"]],
        },
    }
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved == {
        **payload,
        "assessment_provenance": {
            **payload["assessment_provenance"],
            "mechanical_projection_used_as_quality_authority": False,
        },
    }


def test_read_publication_eval_latest_marks_legacy_payload_as_projection_only(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    payload.pop("assessment_provenance")
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved["assessment_provenance"] == {
        "owner": "mechanical_projection",
        "source_kind": "legacy_publication_eval_projection",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [
            payload["charter_context_ref"]["ref"],
            payload["runtime_context_refs"]["runtime_escalation_ref"],
            payload["runtime_context_refs"]["main_result_ref"],
            payload["delivery_context_refs"]["paper_root_ref"],
            payload["delivery_context_refs"]["submission_minimal_ref"],
        ],
        "ai_reviewer_required": True,
        "mechanical_projection_used_as_quality_authority": False,
    }


def test_read_publication_eval_latest_rejects_legacy_ai_reviewer_recheck_route_verdict(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "ai_reviewer",
        "source_kind": "publication_eval_ai_reviewer_recheck",
        "policy_id": "medical_publication_critique_v1",
        "source_refs": [
            str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            str(study_root / "paper" / "draft.md"),
        ],
        "ai_reviewer_required": False,
        "mechanical_projection_used_as_quality_authority": False,
    }
    payload["verdict"] = {
        "overall_verdict": "review_owner_clear_for_bundle_stage",
        "primary_claim_status": "supported_with_limitations",
        "summary": "AI-reviewer recheck completed and selected downstream bundle-stage continuation.",
        "stop_loss_pressure": "watch",
    }
    payload["recommended_actions"] = [
        {
            "action_id": "continue-bundle-stage",
            "action_type": "continue_same_line",
            "priority": "next",
            "reason": "Continue downstream bundle-stage handling after AI-reviewer recheck.",
            "route_target": "controller",
            "route_key_question": "Continue downstream bundle-stage handling.",
            "route_rationale": "The AI reviewer recheck closed the review-workflow blocker.",
            "evidence_refs": [str(study_root / "paper" / "review" / "review_ledger.json")],
            "requires_controller_decision": False,
        }
    ]
    _write_json(latest_path, payload)

    with pytest.raises(ValueError, match="overall_verdict must be one of"):
        module.read_publication_eval_latest(study_root=study_root)


def test_ai_reviewer_publication_eval_materializer_rejects_gate_projection_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_report",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [payload["runtime_context_refs"]["runtime_escalation_ref"]],
        "ai_reviewer_required": True,
    }

    with pytest.raises(ValueError, match="owner=ai_reviewer"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)


def test_ai_reviewer_publication_eval_materializer_rejects_gate_source_kind(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["assessment_provenance"]["source_kind"] = "publication_gate_report"

    with pytest.raises(ValueError, match="source_kind=publication_eval_ai_reviewer"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)


def test_ai_reviewer_publication_eval_materializer_writes_review_backed_latest(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)

    result = module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)

    assert result["eval_id"] == payload["eval_id"]
    resolved = module.read_publication_eval_latest(study_root=study_root)
    assert resolved["assessment_provenance"]["owner"] == "ai_reviewer"
    assert resolved["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert resolved["assessment_provenance"]["policy_id"] == "medical_publication_critique_v1"
    assert resolved["reviewer_operating_system"]["contract_id"] == "medical_publication_ai_reviewer_os_v1"
    assert resolved["quality_assessment"]["medical_journal_prose_quality"]["reviewer_revision_advice"] == (
        "Rewrite representative figure-led sentences as finding-led sentences."
    )


def test_ai_reviewer_publication_eval_materializer_promotes_current_manuscript_record(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["assessment_provenance"]["source_kind"] = "publication_eval_ai_reviewer_current_manuscript_record"

    result = module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)

    assert result["eval_id"] == payload["eval_id"]
    resolved = module.read_publication_eval_latest(study_root=study_root)
    assert resolved["assessment_provenance"]["owner"] == "ai_reviewer"
    assert resolved["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"


def test_ai_reviewer_publication_eval_materializer_rejects_missing_reviewer_os_trace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)

    with pytest.raises(ValueError, match="reviewer_operating_system"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)


def test_ai_reviewer_publication_eval_materializer_rejects_missing_prose_quality_dimension(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["quality_assessment"].pop("medical_journal_prose_quality")

    with pytest.raises(ValueError, match="quality_assessment.medical_journal_prose_quality"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)


def test_resolve_publication_eval_latest_ref_rejects_med_deepscientist_runtime_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    runtime_ref = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001" / "artifacts" / "publication_eval" / "latest.json"

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.resolve_publication_eval_latest_ref(study_root=study_root, ref=runtime_ref)


def test_resolve_publication_eval_latest_ref_rejects_cross_repo_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "repo-a" / "studies" / "001-risk"
    cross_repo_ref = tmp_path / "repo-b" / "studies" / "001-risk" / "artifacts" / "publication_eval" / "latest.json"

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.resolve_publication_eval_latest_ref(study_root=study_root, ref=cross_repo_ref)


def test_read_publication_eval_latest_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_publication_eval_latest(study_root=study_root)


def test_ai_reviewer_publication_eval_controller_materializes_runtime_checked_latest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    called: dict[str, object] = {}

    def fake_status(*, profile, study_id: str | None, study_root: Path | None, entry_mode: str | None) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        return {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        }

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", fake_status)

    result = controller.materialize_ai_reviewer_publication_eval(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id=None,
        study_root=study_root,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert called["study_root"] == study_root
    assert result["status"] == "materialized"
    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["assessment_owner"] == "ai_reviewer"
    latest = importlib.import_module(MODULE_NAME).read_publication_eval_latest(study_root=study_root)
    assert latest["eval_id"] == payload["eval_id"]
    record_ref = Path(result["publication_eval_record_ref"])
    assert record_ref.name == "20260405T060000Z_publication_eval_record.json"
    assert record_ref.parent == (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").resolve()
    archived = json.loads(record_ref.read_text(encoding="utf-8"))
    assert archived == latest


def test_ai_reviewer_publication_eval_controller_promotes_current_manuscript_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["assessment_provenance"]["source_kind"] = "publication_eval_ai_reviewer_current_manuscript_record"

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    result = controller.materialize_ai_reviewer_publication_eval(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert result["status"] == "materialized"
    latest = importlib.import_module(MODULE_NAME).read_publication_eval_latest(study_root=study_root)
    assert latest["eval_id"] == payload["eval_id"]
    assert latest["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    record_ref = Path(result["publication_eval_record_ref"])
    archived = json.loads(record_ref.read_text(encoding="utf-8"))
    assert archived == latest


def test_ai_reviewer_publication_eval_record_controller_materializes_owner_record_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["future_facing_limitations_plan"] = [
        {
            "limitation": "Current review is bound to the active manuscript digest.",
            "impact_on_claim": "Claims remain restrained until write repair and re-review.",
            "required_future_analysis_data_or_design": "Rerun AI reviewer after manuscript repair.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    result = controller.materialize_ai_reviewer_publication_eval_record(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert result["status"] == "materialized"
    assert result["publication_eval_surface"] == "not_written"
    record_ref = Path(result["publication_eval_record_ref"])
    assert record_ref.name == "20260405T060000Z_publication_eval_record.json"
    assert record_ref.is_file()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    archived = json.loads(record_ref.read_text(encoding="utf-8"))
    assert archived["eval_id"] == payload["eval_id"]


def test_ai_reviewer_publication_eval_record_controller_rejects_invalid_reviewer_os_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "request_kind": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "authority_contract": {"can_authorize_quality": False},
        "claim_boundary_review": {"status": "partial"},
    }

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    with pytest.raises(ValueError, match="reviewer_operating_system invalid"):
        controller.materialize_ai_reviewer_publication_eval_record(
            profile=SimpleNamespace(name="nfpitnet"),
            study_id="001-risk",
            study_root=None,
            entry_mode=None,
            record=payload,
            source="pytest",
        )

    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_record_controller_rebuilds_production_trace_for_current_manuscript_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["future_facing_limitations_plan"] = [
        {
            "limitation": "Current review is bound to the active manuscript digest.",
            "impact_on_claim": "Claims remain restrained until write repair and re-review.",
            "required_future_analysis_data_or_design": "Rerun AI reviewer after manuscript repair.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]
    manuscript_path = study_root / "paper" / "manuscript.md"
    manuscript_text = "# Current manuscript\n\nAI reviewer judged this current manuscript snapshot.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    manuscript_digest = "sha256:" + hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    current_request_digest = "sha256:" + "b" * 64
    stale_request_digest = "sha256:" + "a" * 64
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": current_request_digest,
            "manuscript": {"path": str(manuscript_path), "digest": manuscript_digest},
        },
    )
    _write_json(
        review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": stale_request_digest,
                "manuscript_ref": str(manuscript_path),
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite manuscript prose against the current evidence.",
                },
            },
        },
    )
    evidence_ledger_ref = str(study_root / "paper" / "evidence_ledger.json")
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        claim_evidence_map_payload(evidence_ledger_ref=evidence_ledger_ref),
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        evidence_ledger_payload(evidence_ledger_ref=evidence_ledger_ref),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"items": []})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_gate" / "latest.json", {"schema_version": 1})
    payload["recommended_actions"] = [
        {
            "action_id": "route-current-record-to-write",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route current manuscript record back to write.",
            "route_target": "write",
            "route_key_question": "Can write repair close the current reviewer record?",
            "route_rationale": "The current record is bound to the live manuscript.",
            "evidence_refs": [str(manuscript_path)],
            "requires_controller_decision": True,
        }
    ]
    payload["reviewer_operating_system"] = {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "request_kind": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "input_bundle": {
            "manuscript": str(manuscript_path),
            "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
            "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
            "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "medical_prose_review": str(review_path),
            "publication_gate_projection": str(study_root / "artifacts" / "publication_gate" / "latest.json"),
        },
        "currentness_checks": {
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": str(manuscript_path),
                "manuscript_digest": manuscript_digest,
            }
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": current_request_digest,
            "evidence_ledger_digest": "sha256:" + "0" * 64,
            "claim_evidence_alignment_digest": "sha256:" + "1" * 64,
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{payload['eval_id']}",
            "fail_closed_when_missing": True,
            "missing_required_fields": ["current_package_freshness"],
        },
    }

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    result = controller.materialize_ai_reviewer_publication_eval_record(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
        build_production_trace=True,
    )

    assert result["status"] == "materialized"
    assert result["publication_eval_surface"] == "not_written"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    archived = json.loads(Path(result["publication_eval_record_ref"]).read_text(encoding="utf-8"))
    reviewer_os = archived["reviewer_operating_system"]
    assert "request_kind" not in reviewer_os
    assert reviewer_os["decision_matrix"]
    assert reviewer_os["claim_evidence_alignment"]["status"] == "ready"
    assert reviewer_os["publication_quality_readiness"]["status"] == "blocked"
    assert reviewer_os["currentness_checks"]["medical_prose_review"]["request_digest"] == current_request_digest
    assert reviewer_os["currentness_checks"]["medical_prose_review"]["durable_medical_prose_review_status"] == (
        "stale_for_current_request"
    )


def test_ai_reviewer_publication_eval_controller_rejects_mechanical_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_report",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [payload["runtime_context_refs"]["runtime_escalation_ref"]],
        "ai_reviewer_required": True,
    }

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    with pytest.raises(ValueError, match="owner=ai_reviewer"):
        controller.materialize_ai_reviewer_publication_eval(
            profile=SimpleNamespace(name="nfpitnet"),
            study_id=None,
            study_root=study_root,
            entry_mode=None,
            record=payload,
            source="pytest",
        )
