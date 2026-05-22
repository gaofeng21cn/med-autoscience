from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _work_unit(work_unit_type: str, *, unit_id: str = "unit-1") -> dict[str, object]:
    unit: dict[str, object] = {
        "unit_id": unit_id,
        "work_unit_type": work_unit_type,
        "owner": "quality_repair_batch",
        "callable_surface": "paper_repair_executor.dispatch_repair_work_unit",
        "source_fingerprint": f"sha256:{work_unit_type}",
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "gate_replay_target": "publication_eval/latest.json",
        "target_claim": "The original claim is supported.",
        "repair_instruction": "Use restrained association language and close the review ledger.",
    }
    if work_unit_type == "text_repair":
        unit["canonical_patch"] = {
            "target_text": "The original claim is supported.",
            "replacement_text": "The association is directionally consistent but requires restrained interpretation.",
        }
    return unit


def test_paper_repair_executor_executes_text_repair_on_canonical_sources(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    manuscript = study_root / "paper" / "draft.md"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-1"})
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")

    result = module.dispatch_repair_work_unit(
        study_id="001-risk",
        quest_id="quest-001",
        study_root=study_root,
        repair_work_unit=_work_unit("text_repair"),
        apply=True,
    )

    assert result["accepted"] is True
    assert result["execution_status"] == "executed"
    assert result["typed_blocker"] is None
    text = manuscript.read_text(encoding="utf-8")
    assert "restrained interpretation" in text
    assert "Repair note" not in text
    assert result["owner_receipt"]["work_unit_type"] == "text_repair"
    assert result["owner_receipt"]["direct_current_package_write"] is False
    assert result["owner_receipt"]["canonical_artifact_delta_refs"][0]["artifact_role"] == "canonical_manuscript_story_surface"
    assert result["canonical_artifact_delta"]["meaningful_artifact_delta"] is True
    assert result["repair_execution_evidence"]["progress_delta_candidate"] is True
    assert (study_root / "paper" / "review" / "review_ledger.json").is_file()
    assert (study_root / "paper" / "revision_log.jsonl").is_file()
    assert (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_downgrades_claim_and_updates_evidence_ledger(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "002-negative"
    manuscript = study_root / "paper" / "draft.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")

    result = module.dispatch_repair_work_unit(
        study_id="002-negative",
        quest_id="quest-002",
        study_root=study_root,
        repair_work_unit={
            **_work_unit("claim_downgrade"),
            "claim_policy": {
                "claim_id": "claim.primary",
                "supported": False,
                "allowed_status": "downgraded",
                "reason": "negative_result_cannot_support_original_claim",
            },
        },
        apply=True,
    )

    ledger = json.loads((study_root / "paper" / "evidence_ledger.json").read_text(encoding="utf-8"))
    assert result["execution_status"] == "executed"
    assert ledger["claim_updates"][0]["claim_policy"]["supported"] is False
    assert "downgraded" in manuscript.read_text(encoding="utf-8")
    assert result["repair_execution_evidence"]["canonical_artifact_delta"]["meaningful_artifact_delta"] is True


def test_paper_repair_executor_returns_typed_blocker_for_missing_owner_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")

    result = module.dispatch_repair_work_unit(
        study_id="003-risk",
        quest_id="quest-003",
        study_root=tmp_path / "workspace" / "studies" / "003-risk",
        repair_work_unit=_work_unit("display_rebuild"),
        apply=True,
    )

    assert result["accepted"] is False
    assert result["execution_status"] == "blocked"
    assert result["typed_blocker"] == "owner_callable_surface_missing"
    assert result["owner_receipt"]["blocked_reason"] == "owner_callable_surface_missing"
    assert result["repair_execution_evidence"]["status"] == "blocked"


def test_paper_repair_executor_blocks_unstructured_text_repair(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "003b-risk"
    manuscript = study_root / "paper" / "draft.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")
    work_unit = _work_unit("text_repair")
    work_unit.pop("canonical_patch")

    result = module.dispatch_repair_work_unit(
        study_id="003b-risk",
        quest_id="quest-003b",
        study_root=study_root,
        repair_work_unit=work_unit,
        apply=True,
    )

    assert result["accepted"] is False
    assert result["execution_status"] == "blocked"
    assert result["typed_blocker"] == "owner_callable_surface_missing"
    assert manuscript.read_text(encoding="utf-8") == "The original claim is supported.\n"


def test_paper_repair_executor_routes_quality_repair_batch_callable_without_structured_patch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    quality_module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "005-dpcc"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    calls: list[dict[str, object]] = []

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        evidence = {
            "surface": "repair_execution_evidence",
            "progress_delta_candidate": True,
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
        }
        _write_json(evidence_path, evidence)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
            "repair_execution_evidence": evidence,
            "repair_execution_evidence_path": str(evidence_path),
        }

    monkeypatch.setattr(quality_module, "run_quality_repair_batch", fake_run_quality_repair_batch)
    work_unit = _work_unit("text_repair", unit_id="unit-quality-batch")
    work_unit["callable_surface"] = "quality_repair_batch.run_quality_repair_batch"
    work_unit.pop("canonical_patch")

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id="005-dpcc",
        quest_id="quest-005",
        study_root=study_root,
        repair_work_unit=work_unit,
        apply=True,
    )

    assert result["accepted"] is True
    assert result["execution_status"] == "executed"
    assert result["typed_blocker"] is None
    assert result["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert calls == [
        {
            "profile": profile,
            "study_id": "005-dpcc",
            "study_root": study_root.resolve(),
            "quest_id": "quest-005",
            "source": "paper_repair_executor",
            "control_plane_route_context": None,
            "route_context": None,
        }
    ]
    assert result["owner_receipt"]["direct_current_package_write"] is False
    assert result["owner_result"]["status"] == "executed"
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_accepts_quality_repair_writer_handoff_without_terminal_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    quality_module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "005-dpcc"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        evidence = {
            "surface": "repair_execution_evidence",
            "status": "blocked",
            "progress_delta_candidate": False,
            "canonical_artifact_delta": {"meaningful_artifact_delta": False},
            "manuscript_surface_hygiene": {
                "story_surface_delta_required": True,
                "story_surface_delta_present": False,
            },
        }
        _write_json(evidence_path, evidence)
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "next_owner": "write",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
            "repair_execution_evidence": evidence,
            "repair_execution_evidence_path": str(evidence_path),
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
        }

    monkeypatch.setattr(quality_module, "run_quality_repair_batch", fake_run_quality_repair_batch)
    work_unit = _work_unit("text_repair", unit_id="unit-quality-batch-handoff")
    work_unit["callable_surface"] = "quality_repair_batch.run_quality_repair_batch"
    work_unit.pop("canonical_patch")

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id="005-dpcc",
        quest_id="quest-005",
        study_root=study_root,
        repair_work_unit=work_unit,
        apply=True,
    )

    assert result["accepted"] is True
    assert result["execution_status"] == "handoff_ready"
    assert result["typed_blocker"] is None
    assert result["owner_receipt"]["direct_current_package_write"] is False
    assert result["writer_worker_handoff"]["next_executable_owner"] == "write"
    assert "canonical manuscript story-surface delta" in result["writer_worker_handoff"]["required_output_surface"]
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_routes_ai_reviewer_callable_to_owner_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    owner_dispatch = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "006-dpcc"
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "execution_status": "executed",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(owner_dispatch, "dispatch_domain_owner_actions", fake_dispatch_domain_owner_actions)

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id="006-dpcc",
        quest_id="quest-006",
        study_root=study_root,
        repair_work_unit={
            **_work_unit("ai_reviewer_recheck", unit_id="unit-ai-reviewer"),
            "owner": "ai_reviewer",
            "callable_surface": (
                "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
            ),
        },
        apply=True,
    )

    assert result["accepted"] is True
    assert result["execution_status"] == "executed"
    assert result["typed_blocker"] is None
    assert result["owner_callable_surface"] == (
        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    )
    assert result["owner_result"]["executed_count"] == 1
    assert len(calls) == 1
    call = calls[0]
    assert call["profile"] == profile
    assert call["study_ids"] == ("006-dpcc",)
    assert call["action_types"] == ("return_to_ai_reviewer_workflow",)
    assert call["mode"] == "developer_apply_safe"
    assert call["apply"] is True
    consumer_payload = call["consumer_payload"]
    dispatch = consumer_payload["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["owner_route"]["next_owner"] == "ai_reviewer"
    assert "return_to_ai_reviewer_workflow" in dispatch["owner_route"]["allowed_actions"]
    assert (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").is_file()
    assert (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_ai_reviewer_handoff_preserves_runtime_health_epoch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    owner_dispatch = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    attempt_protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "006c-dpcc"
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 0,
            "blocked_count": 1,
            "executions": [
                {
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(owner_dispatch, "dispatch_domain_owner_actions", fake_dispatch_domain_owner_actions)
    work_unit = {
        **_work_unit("ai_reviewer_recheck", unit_id="unit-ai-reviewer-currentness"),
        "owner": "ai_reviewer",
        "callable_surface": (
            "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
        ),
    }
    route_context = {
        "controller_route_context": {
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "work_unit_fingerprint": "domain-transition::ai-reviewer-current",
            "runtime_health_epoch": "runtime-health-event-current",
        },
        "current_owner_route": {
            "runtime_health_epoch": "runtime-health-event-current",
            "truth_epoch": "study-decision::ai-reviewer-current",
        },
    }

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id="006c-dpcc",
        quest_id="quest-006c",
        study_root=study_root,
        repair_work_unit=work_unit,
        control_plane_route_context=route_context,
        apply=True,
    )

    assert result["accepted"] is False
    dispatch = calls[0]["consumer_payload"]["default_executor_dispatches"][0]
    assert dispatch["owner_route"]["runtime_health_epoch"] == "runtime-health-event-current"
    assert dispatch["prompt_contract"]["owner_route"]["runtime_health_epoch"] == "runtime-health-event-current"
    envelope = attempt_protocol.default_executor_attempt_envelope(dispatch=dispatch)
    assert envelope["owner_route_currentness_basis"]["runtime_health_epoch"] == (
        "runtime-health-event-current"
    )
    assert envelope["dispatchable"] is True


def test_paper_repair_executor_ai_reviewer_callable_materializes_dispatch_before_execution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    workflow = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    profile = make_profile(tmp_path)
    study_id = "006d-dpcc"
    quest_id = "quest-006d"
    study_root = profile.studies_root / study_id
    manuscript = study_root / "paper" / "draft.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("Methods need clearer reporting.\n", encoding="utf-8")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"study_id": study_id})
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "medical_prose_review",
                "ai_reviewer_required": False,
                "request_digest": "sha256:test-request",
                "manuscript_ref": str(manuscript),
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "summary": "Methods reporting remains incomplete.",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Methods reproducibility and treatment-gap definitions need repair.",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": "stale-eval", "verdict": {"overall_verdict": "mixed"}},
    )
    calls: list[dict[str, object]] = []

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "eval_id": "publication-eval-current",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {"status": "partial"},
                },
                "future_facing_limitations_plan": [{"limitation": "test"}],
            },
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval-current",
        }

    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(workflow, "run_ai_reviewer_publication_eval_workflow", fake_run_ai_reviewer_publication_eval_workflow)

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        repair_work_unit={
            **_work_unit("ai_reviewer_recheck", unit_id="unit-ai-reviewer-inline"),
            "owner": "ai_reviewer",
            "callable_surface": (
                "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
            ),
        },
        apply=True,
    )

    assert result["accepted"] is True
    assert result["execution_status"] == "executed"
    assert result["typed_blocker"] is None
    assert result["owner_result"]["execution_count"] == 1
    execution = result["owner_result"]["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["action_type"] == "return_to_ai_reviewer_workflow"
    assert execution["dispatch_authority"] == "paper_repair_executor_inline_owner_dispatch"
    assert execution["owner_route_current"] is True
    assert calls
    assert calls[0]["manuscript_ref"] == str(manuscript.resolve())
    request = json.loads(
        (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert request["owner_route"]["next_owner"] == "ai_reviewer"
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_preserves_ai_reviewer_dispatch_blocked_reason(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    owner_dispatch = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "006b-dpcc"

    def fake_dispatch_domain_owner_actions(**_kwargs) -> dict[str, object]:
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "executions": [
                {
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_request_missing",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(owner_dispatch, "dispatch_domain_owner_actions", fake_dispatch_domain_owner_actions)

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id="006b-dpcc",
        quest_id="quest-006b",
        study_root=study_root,
        repair_work_unit={
            **_work_unit("ai_reviewer_recheck", unit_id="unit-ai-reviewer-blocked"),
            "owner": "ai_reviewer",
            "callable_surface": (
                "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
            ),
        },
        apply=True,
    )

    assert result["accepted"] is False
    assert result["execution_status"] == "blocked"
    assert result["typed_blocker"] == "ai_reviewer_request_missing"
    assert result["owner_receipt"]["blocked_reason"] == "ai_reviewer_request_missing"


def test_paper_repair_executor_preserves_ai_reviewer_repeat_suppressed_reason(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    owner_dispatch = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "006c-dpcc"

    def fake_dispatch_domain_owner_actions(**_kwargs) -> dict[str, object]:
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 0,
            "blocked_count": 0,
            "repeat_suppressed_count": 1,
            "executions": [
                {
                    "execution_status": "repeat_suppressed",
                    "blocked_reason": "repeat_suppressed",
                    "why_not_applied": "repeat_suppressed",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(owner_dispatch, "dispatch_domain_owner_actions", fake_dispatch_domain_owner_actions)

    result = module.dispatch_repair_work_unit(
        profile=profile,
        study_id="006c-dpcc",
        quest_id="quest-006c",
        study_root=study_root,
        repair_work_unit={
            **_work_unit("ai_reviewer_recheck", unit_id="unit-ai-reviewer-repeat"),
            "owner": "ai_reviewer",
            "callable_surface": (
                "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
            ),
        },
        apply=True,
    )

    assert result["accepted"] is False
    assert result["execution_status"] == "blocked"
    assert result["typed_blocker"] == "repeat_suppressed"
    assert result["owner_result"]["repeat_suppressed_count"] == 1


def test_paper_repair_executor_dry_run_does_not_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "004-dry-run"

    result = module.dispatch_repair_work_unit(
        study_id="004-dry-run",
        quest_id="quest-004",
        study_root=study_root,
        repair_work_unit=_work_unit("text_repair"),
        apply=False,
    )

    assert result["execution_status"] == "dry_run"
    assert result["typed_blocker"] is None
    assert not (study_root / "paper" / "manuscript.md").exists()
    assert not (study_root / "artifacts" / "controller" / "repair_execution_receipts").exists()
