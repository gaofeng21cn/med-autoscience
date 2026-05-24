from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_quality_repair_writer_handoff_requires_typed_closeout_packet(tmp_path: Path) -> None:
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"

    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=f"quest-{study_id}",
        schema_version=1,
        source_eval_id="publication-eval::dm003",
        source_eval_artifact_path="artifacts/publication_eval/latest.json",
        source_summary_artifact_path="artifacts/eval_hygiene/evaluation_summary/latest.json",
        repair_execution_evidence_path=profile.studies_root / study_id / "artifacts/controller/repair_execution_evidence/latest.json",
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "controller_route_context": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            },
        },
    )

    closeout_contract = handoff["required_closeout_packet"]
    assert closeout_contract["typed_closeout_required_for_completion"] is True
    assert closeout_contract["free_text_closeout_accepted"] is False
    assert "stage_attempt_closeout_packet" in closeout_contract["accepted_surface_kinds"]
    assert handoff["prompt_contract"]["required_closeout_packet"] == closeout_contract
    assert "exactly one JSON object" in handoff["terminal_output_instruction"]
    assert handoff["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/quality_repair_batch/latest.json"
    )
    assert handoff["refs"]["request_path"].endswith(
        "artifacts/supervision/requests/quality_repair_batch/latest.json"
    )


def test_quality_repair_writer_handoff_bridges_runtime_owner_route_currentness(tmp_path: Path) -> None:
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    attempt_protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = "publication-eval::dm003::medical-prose-routeback"
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    current_route.update(
        {
            "truth_epoch": source_eval_id,
            "runtime_health_epoch": "runtime-health-dm003-write-route",
            "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
            "source_fingerprint": "truth-source::dm003::medical-prose",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "source_refs": {
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "runtime_health_epoch": "runtime-health-dm003-write-route",
                "study_truth_epoch": source_eval_id,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            },
        }
    )

    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=f"quest-{study_id}",
        schema_version=1,
        source_eval_id=source_eval_id,
        source_eval_artifact_path="artifacts/publication_eval/latest.json",
        source_summary_artifact_path="artifacts/eval_hygiene/evaluation_summary/latest.json",
        repair_execution_evidence_path=(
            profile.studies_root
            / study_id
            / "artifacts/controller/repair_execution_evidence/latest.json"
        ),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": current_route,
            "controller_route_context": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
            },
        },
    )

    envelope = attempt_protocol.default_executor_attempt_envelope(dispatch=handoff)

    assert envelope["dispatchable"] is True
    assert envelope["owner_reason_contract"]["reason"] == "manuscript_story_surface_delta_missing"
    assert envelope["owner_route_currentness_basis"] == {
        "source_eval_id": source_eval_id,
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
        "truth_epoch": source_eval_id,
        "runtime_health_epoch": "runtime-health-dm003-write-route",
        "owner_reason": "manuscript_story_surface_delta_missing",
    }
    assert handoff["owner_route"]["source_refs"]["bridged_from_owner_reason"] == (
        "quest_waiting_opl_runtime_owner_route"
    )
    assert handoff["owner_route"]["source_refs"]["blocked_reason"] == (
        "manuscript_story_surface_delta_missing"
    )


def test_execute_dispatch_treats_quality_repair_writer_handoff_as_dispatchable_not_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["work_unit_fingerprint"] = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route["source_fingerprint"] = "truth-source::dm003::medical-prose"
    route["idempotency_key"] = "owner-route::dm003::medical-prose"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_work_unit": {
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
        },
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "next_owner": "write",
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
                "required_closeout_packet": {
                    "typed_closeout_required_for_completion": True,
                    "free_text_closeout_accepted": False,
                    "accepted_surface_kinds": ["stage_attempt_closeout_packet"],
                },
                "terminal_output_instruction": "End with exactly one JSON object.",
            },
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["paper_work_unit_lifecycle"]["owner"] == "quality_repair_batch"
    assert execution["paper_work_unit_lifecycle"]["allowed_writes"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "artifacts/controller/quality_repair_batch/latest.json",
        "artifacts/controller/repair_execution_evidence/latest.json",
        "artifacts/supervision/requests/ai_reviewer/latest.json",
        "artifacts/controller/gate_replay_requests/latest.json",
    ]
    assert "artifacts/publication_eval/latest.json" in execution["paper_work_unit_lifecycle"]["forbidden_writes"]
    assert execution["paper_work_unit_lifecycle"]["completion_proof"][
        "requires_owner_receipt_or_typed_blocker"
    ] is True
    assert execution["writer_worker_handoff"]["next_executable_owner"] == "write"
    closeout_contract = execution["writer_worker_handoff"]["required_closeout_packet"]
    assert closeout_contract["typed_closeout_required_for_completion"] is True
    assert closeout_contract["free_text_closeout_accepted"] is False
    assert "stage_attempt_closeout_packet" in closeout_contract["accepted_surface_kinds"]
    assert "terminal_output_instruction" in execution["writer_worker_handoff"]
    assert "exactly one JSON object" in execution["writer_worker_handoff"]["terminal_output_instruction"]
    assert called["study_id"] == study_id
    assert called["quest_id"] == f"quest-{study_id}"
    route_context = called["authority_route_context"]
    assert route_context["controller_action_type"] == "run_quality_repair_batch"
    assert route_context["work_unit_id"] == "medical_prose_write_repair"


def test_execute_dispatch_picks_quality_repair_writer_handoff_without_request_packet(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    route["work_unit_fingerprint"] = "medical-prose-routeback::write::sha256-dm003"
    route["idempotency_key"] = "owner-route::dm003::write::story-surface"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": "publication-eval::dm003::medical-prose-routeback",
        "repair_execution_evidence_ref": str(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
    }
    dispatch_payload["source_action"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [],
        },
    )
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    assert not request_path.exists()
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["authority_route_context"]["work_unit_id"] == "medical_prose_write_repair"


def test_execute_dispatch_does_not_empty_spin_consumed_quality_repair_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    route["work_unit_fingerprint"] = "medical-prose-routeback::write::sha256-dm003"
    route["idempotency_key"] = "owner-route::dm003::write::story-surface"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": "publication-eval::dm003::medical-prose-routeback",
        "repair_execution_evidence_ref": str(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
    }
    dispatch_payload["source_action"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "next_owner": "write",
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    assert result["codex_dispatch_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert execution["typed_blocker"] == "manuscript_story_surface_delta_missing"
    assert execution["owner_route_current"] is True
    assert execution["will_start_llm"] is False
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["consumed_writer_handoff_empty_spin_blocked"] is True
    assert execution["required_next_owner"] == "write"
    assert called["authority_route_context"]["work_unit_id"] == "medical_prose_write_repair"


def test_quality_repair_writer_handoff_rejects_package_write_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/current_package/proof.json",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["dispatch_contract_valid"] is False
    assert execution["dispatch_contract_blocked_reason"] == "medical_claim_authoring_allowed_guard_missing"


def test_quality_repair_writer_handoff_retries_after_guard_block(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    route["work_unit_fingerprint"] = "medical-prose-routeback::write::sha256-dm003"
    route["idempotency_key"] = "owner-route::dm003::write::story-surface"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "medical_claim_authoring_allowed_guard_missing",
                    "dispatch_contract_valid": False,
                    "dispatch_contract_blocked_reason": "medical_claim_authoring_allowed_guard_missing",
                    "owner_route": route,
                    "prompt_contract": dispatch_payload["prompt_contract"],
                    "repeat_suppression_key": "medical-prose-routeback::write::sha256-dm003",
                }
            ],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["repeat_suppression"]["repeat_suppressed"] is False
