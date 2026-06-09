from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    source_fingerprint = f"truth-source::{study_id}::{owner_reason}"
    truth_epoch = f"truth-epoch::{study_id}"
    runtime_health_epoch = f"runtime-health::{study_id}::{owner_reason}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": source_fingerprint,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "source_refs": {
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": source_fingerprint,
            "owner_route_currentness_basis": {
                "truth_epoch": truth_epoch,
                "runtime_health_epoch": runtime_health_epoch,
                "work_unit_id": owner_reason,
                "work_unit_fingerprint": source_fingerprint,
            },
        },
    }


def test_materialize_domain_action_requests_prefers_fresh_repair_followup_without_ticket_allowed_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": stale_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "latest_owner_answer_kind": "typed_blocker",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "next_owner": "MedAutoScience",
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "owner_route": stale_route,
                        }
                    ],
                }
            ],
        },
    )
    fresh_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-08T04:40:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
            "current_owner_ticket": None,
            "owner_route": fresh_route,
            "paper_progress_delta": {"count": 1},
            "deliverable_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert dispatch["source_action"]["authority"] == "study_progress.current_executable_owner_action"
    assert dispatch["source_action"]["source_surface"] == "study_progress.current_executable_owner_action"
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "complete_medical_paper_readiness_surface": (
            "superseded_by_fresh_study_progress_current_owner_ticket"
        ),
        "run_quality_repair_batch": "stage_native_workspace_next_action_requires_authority_binding",
    }


def test_materialize_domain_action_requests_allows_repair_followup_when_readiness_blocker_envelope_remains(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    readiness_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": readiness_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "owner_route": readiness_route,
                        }
                    ],
                }
            ],
        },
    )
    followup_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-08T06:41:51+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {
                    "paper_delta_observed": True,
                    "accepted_owner_receipt": True,
                    "superseded_stage_native_action": "run_quality_repair_batch",
                    "superseded_readiness_action": "complete_medical_paper_readiness_surface",
                    "source_work_unit_id": "analysis_claim_evidence_repair",
                },
            },
            "current_owner_ticket": None,
            "owner_route": followup_route,
            "paper_progress_delta": {"count": 1},
            "deliverable_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["source_action"]["current_action_source"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "complete_medical_paper_readiness_surface": (
            "superseded_by_fresh_study_progress_current_owner_ticket"
        ),
        "run_quality_repair_batch": "stage_native_workspace_next_action_requires_authority_binding",
    }


def test_materialize_domain_action_requests_prefers_repair_followup_over_provider_admission_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    provider_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="write",
        owner_reason="dm002_current_publication_hardening_after_current_ai_reviewer_eval",
        allowed_actions=["run_quality_repair_batch"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": provider_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "authority": "mas_provider_admission_identity",
                            "action_id": f"provider-admission::{study_id}::run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "recommended_owner": "write",
                            "reason": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "owner_route": provider_route,
                        }
                    ],
                }
            ],
        },
    )
    fresh_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-08T06:05:14+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {
                    "paper_delta_observed": True,
                    "accepted_owner_receipt": True,
                    "superseded_stage_native_action": "run_quality_repair_batch",
                    "source_work_unit_id": "analysis_claim_evidence_repair",
                },
            },
            "current_owner_ticket": None,
            "owner_route": fresh_route,
            "paper_progress_delta": {"count": 1},
            "deliverable_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["source_action"]["current_action_source"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "run_quality_repair_batch": "superseded_by_fresh_study_progress_current_owner_ticket",
    }


def test_materialize_domain_action_requests_does_not_bridge_repair_followup_to_old_reviewer_routeback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript after claim/evidence repair.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260608T060000Z_publication_eval_record.json",
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            study_id=study_id,
            quest_id=study_id,
            eval_id="publication-eval::dm002::old-routeback::2026-06-08T06:00:00+00:00",
            emitted_at="2026-06-08T06:00:00+00:00",
        ),
    )
    provider_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="write",
        owner_reason="dm002_current_publication_hardening_after_current_ai_reviewer_eval",
        allowed_actions=["run_quality_repair_batch"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": provider_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "authority": "mas_provider_admission_identity",
                            "action_id": f"provider-admission::{study_id}::run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "recommended_owner": "write",
                            "reason": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "owner_route": provider_route,
                        }
                    ],
                }
            ],
        },
    )
    fresh_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-08T06:30:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {
                    "paper_delta_observed": True,
                    "accepted_owner_receipt": True,
                    "source_work_unit_id": "analysis_claim_evidence_repair",
                },
            },
            "current_owner_ticket": None,
            "owner_route": fresh_route,
            "paper_progress_delta": {"count": 1},
            "deliverable_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert dispatch["source_action"]["current_action_source"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    assert dispatch["source_action"]["reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert dispatch["source_action"]["next_work_unit"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
