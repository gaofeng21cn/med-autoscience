from __future__ import annotations

import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"


def test_materializer_local_carrier_persistence_api_is_physically_retired() -> None:
    try:
        importlib.import_module(
            "med_autoscience.controllers.domain_action_request_materializer_parts.persistence"
        )
    except ModuleNotFoundError:
        return
    raise AssertionError("legacy materializer local carrier persistence module must stay retired")


def test_owner_callable_projection_does_not_accept_legacy_dispatch_alias() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    assert projection.owner_callable_adapters(
        {
            "default_executor_dispatches": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        }
    ) == []
    assert projection.adapter_count(
        {
            "default_executor_dispatches": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        }
    ) == 0
    assert projection.adapter_status_count(
        {
            "default_executor_dispatches": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        },
        "ready",
    ) == 0
    assert projection.adapter_count(
        {
            "owner_callable_adapter_count": 7,
            "ready_owner_callable_adapter_count": 6,
        }
    ) == 0
    assert projection.adapter_status_count(
        {
            "owner_callable_adapter_count": 7,
            "ready_owner_callable_adapter_count": 6,
        },
        "ready",
    ) == 0
    assert projection.legacy_owner_callable_adapter_count(
        {
            "legacy_owner_callable_adapter_diagnostics": {
                "legacy_dispatch_count": 2,
                "legacy_dispatch_refs": [
                    {"dispatch_status": "ready"},
                    {"dispatch_status": "blocked"},
                ],
            }
        }
    ) == 2
    assert projection.domain_progress_transition_requests(
        {
            "default_executor_dispatches": [
                {
                    "dispatch_status": "ready",
                    "action_type": "legacy_dispatch",
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                    },
                },
            ],
        }
    ) == []
    assert projection.transition_request_count(
        {
            "default_executor_dispatches": [
                {
                    "dispatch_status": "transition_request_pending",
                    "action_type": "legacy_dispatch",
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                    },
                },
            ],
        }
    ) == 0


def test_transition_request_counts_are_canonical_not_legacy_adapter_counts() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "dispatch_status": "ready",
                "action_type": "legacy_ready",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
                "source_action": {
                    "work_unit_id": "legacy-body-work",
                    "work_unit_fingerprint": "legacy-body-fingerprint",
                },
            },
        ],
        "domain_progress_transition_requests": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
            },
            {
                "study_id": "study-1",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "gate-work",
                "work_unit_fingerprint": "fingerprint-2",
                "dispatch_status": "blocked",
            },
        ],
    }

    assert projection.owner_callable_adapters(payload) == []
    assert projection.legacy_owner_callable_adapter_count(payload) == 1
    assert projection.legacy_owner_callable_adapter_status_count(payload, "ready") == 1
    assert projection.adapter_count(payload) == projection.legacy_owner_callable_adapter_count(payload)
    assert projection.adapter_status_count(
        payload,
        "ready",
    ) == projection.legacy_owner_callable_adapter_status_count(payload, "ready")
    assert projection.transition_request_count(payload) == 2
    assert projection.transition_request_status_count(payload, "transition_request_pending") == 1
    assert projection.transition_request_status_count(payload, "blocked") == 1
    diagnostics = projection.legacy_owner_callable_adapter_diagnostics(payload)
    assert diagnostics["surface"] == "legacy_owner_callable_adapter_diagnostics"
    assert diagnostics["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["counts_authority"] is False
    assert diagnostics["readiness_authority"] is False
    assert diagnostics["can_create_success_outcome"] is False
    assert diagnostics["body_authority"] is False
    assert diagnostics["body_projection"] is False
    assert diagnostics["legacy_payload_scope"] == "identity_refs_only"
    assert diagnostics["legacy_dispatch_count"] == 1
    assert diagnostics["legacy_ready_count"] == 1
    assert diagnostics["legacy_blocked_count"] == 0
    assert diagnostics["legacy_transition_request_pending_count"] == 0
    assert diagnostics["legacy_dispatches"] == [
        {
            "diagnostic_ref_only": True,
            "payload_body_omitted": True,
            "study_id": "study-1",
            "action_type": "legacy_ready",
            "work_unit_id": "legacy-body-work",
            "work_unit_fingerprint": "legacy-body-fingerprint",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
        }
    ]
    assert diagnostics["legacy_dispatch_refs"] == diagnostics["legacy_dispatches"]
    assert diagnostics["legacy_dispatch_body_omitted"] is True
    assert "source_action" not in diagnostics["legacy_dispatches"][0]
    assert "owner_route" not in diagnostics["legacy_dispatches"][0]
    assert "prompt_contract" not in diagnostics["legacy_dispatches"][0]


def test_owner_callable_projection_requires_canonical_transition_request_surface() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    legacy_payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
                "target_runtime_owner": "one-person-lab",
                "refs": {
                    "dispatch_path": (
                        "artifacts/supervision/consumer/default_executor_dispatches/"
                        "run_quality_repair_batch.json"
                    )
                },
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "study_id": "study-1",
                    "quest_id": "quest-1",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-work",
                    "work_unit_fingerprint": "fingerprint-1",
                },
            }
        ]
    }

    assert projection.domain_progress_transition_requests(legacy_payload) == []
    assert projection.owner_callable_adapters(legacy_payload) == []
    assert projection.legacy_owner_callable_adapter_count(legacy_payload) == 1
    assert projection.with_owner_callable_adapter_projection(legacy_payload)[
        "domain_progress_transition_request_count"
    ] == 0
    legacy_projected = projection.with_owner_callable_adapter_projection(legacy_payload)
    assert "owner_callable_adapter_list_diagnostic_only" not in legacy_projected
    assert "owner_callable_adapter_count" not in legacy_projected
    assert "owner_callable_adapters" in legacy_payload
    assert "owner_callable_adapters" not in legacy_projected
    assert legacy_projected["legacy_owner_callable_adapter_diagnostics"]["diagnostic_only"] is True
    assert legacy_projected["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatch_count"] == 1
    assert legacy_projected["canonical_transition_request_surface"] == (
        "domain_progress_transition_requests"
    )

    canonical_payload = {
        "domain_progress_transition_requests": [
            {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
                "target_runtime_owner": "one-person-lab",
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "study_id": "study-1",
                    "quest_id": "quest-1",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-work",
                    "work_unit_fingerprint": "fingerprint-1",
                },
            }
        ]
    }

    requests = projection.domain_progress_transition_requests(canonical_payload)

    assert len(requests) == 1
    assert requests[0]["surface"] == "mas_domain_progress_transition_request_projection"
    assert requests[0]["study_id"] == "study-1"
    assert requests[0]["action_type"] == "run_quality_repair_batch"
    assert requests[0]["work_unit_fingerprint"] == "fingerprint-1"
    assert requests[0]["mas_dispatch_authority"] is False
    assert requests[0]["mas_creates_owner_callable_carrier"] is False
    assert requests[0]["mas_creates_opl_outbox"] is False
    assert requests[0]["provider_admission_pending"] is False
    assert requests[0]["provider_admission_requires_opl_runtime_result"] is True
    projected = projection.with_owner_callable_adapter_projection(canonical_payload)
    assert projected["domain_progress_transition_request_count"] == 1
    assert "owner_callable_adapter_list_diagnostic_only" not in projected
    assert "owner_callable_adapter_count" not in projected
    assert "owner_callable_adapters" not in projected


def test_public_owner_callable_adapter_reader_is_not_active_carrier() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "dispatch_status": "ready",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
                "source_action": {
                    "work_unit_id": "legacy-work",
                    "work_unit_fingerprint": "legacy-fingerprint",
                },
                "owner_route": {"next_owner": "write"},
                "prompt_contract": {"action_type": "run_quality_repair_batch"},
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                },
            }
        ]
    }

    assert projection.owner_callable_adapters(payload) == []
    assert projection.adapter_count(payload) == 1
    assert projection.adapter_status_count(payload, "ready") == 1
    refs = projection.legacy_owner_callable_adapter_refs(payload)
    assert refs == [
        {
            "diagnostic_ref_only": True,
            "payload_body_omitted": True,
            "study_id": "study-1",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-work",
            "work_unit_fingerprint": "legacy-fingerprint",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
        }
    ]
    assert "owner_route" not in refs[0]
    assert "prompt_contract" not in refs[0]
    assert "source_action" not in refs[0]
    assert "opl_domain_progress_transition_request" not in refs[0]


def test_materializer_canonical_projection_preserves_strong_identity_without_legacy_body() -> None:
    transition_request_projection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.transition_request_projection"
    )
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    dispatch = {
        "study_id": "study-1",
        "quest_id": "quest-1",
        "action_type": "run_quality_repair_batch",
        "dispatch_status": "transition_request_pending",
        "refs": {
            "dispatch_path": "studies/study-1/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
            "route_identity_key": "route::from-refs",
            "attempt_idempotency_key": "attempt::from-refs",
        },
        "owner_route": {
            "next_owner": "write",
            "work_unit_fingerprint": "fingerprint-from-route",
            "route_identity_key": "route::from-owner-route",
            "attempt_idempotency_key": "attempt::from-owner-route",
            "source_refs": {
                "work_unit_id": "work-unit-from-route-refs",
                "work_unit_fingerprint": "fingerprint-from-route-refs",
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-1",
                    "runtime_health_epoch": "runtime-1",
                    "work_unit_id": "work-unit-from-currentness",
                    "work_unit_fingerprint": "fingerprint-from-currentness",
                    "route_identity_key": "route::from-currentness",
                    "attempt_idempotency_key": "attempt::from-currentness",
                },
            },
        },
        "prompt_contract": {
            "study_id": "study-1",
            "quest_id": "quest-1",
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-1",
                "runtime_health_epoch": "runtime-1",
            },
            "opl_domain_progress_transition_request": {
                "surface_kind": "mas_domain_progress_transition_request",
                "target_runtime_owner": "one-person-lab",
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "route_identity_key": "route::from-request",
                "attempt_idempotency_key": "attempt::from-request",
            },
        },
        "source_action": {
            "work_unit_id": "work-unit-from-source-action",
            "work_unit_fingerprint": "fingerprint-from-source-action",
        },
    }

    requests = transition_request_projection.domain_progress_transition_request_projection([dispatch])

    assert len(requests) == 1
    request = requests[0]
    assert request["surface"] == "mas_domain_progress_transition_request_projection"
    assert request["route_identity_key"] == "route::from-request"
    assert request["attempt_idempotency_key"] == "attempt::from-request"
    assert request["work_unit_id"] == "work-unit-from-source-action"
    assert request["work_unit_fingerprint"] == "fingerprint-from-source-action"
    assert request["currentness_basis"] == {
        "truth_epoch": "truth-1",
        "runtime_health_epoch": "runtime-1",
        "work_unit_id": "work-unit-from-source-action",
        "work_unit_fingerprint": "fingerprint-from-source-action",
        "route_identity_key": "route::from-currentness",
        "attempt_idempotency_key": "attempt::from-currentness",
    }
    assert request["provider_admission_pending"] is False
    assert request["provider_admission_requires_opl_runtime_result"] is True
    assert request["mas_creates_opl_outbox"] is False
    assert request["mas_creates_opl_event"] is False
    assert request["mas_creates_opl_stage_run"] is False

    diagnostics = projection.legacy_owner_callable_adapter_diagnostics(
        {"owner_callable_adapters": [dispatch]}
    )
    assert diagnostics["legacy_dispatch_body_omitted"] is True
    assert diagnostics["legacy_dispatches"] == diagnostics["legacy_dispatch_refs"]
    legacy_ref = diagnostics["legacy_dispatches"][0]
    assert legacy_ref["diagnostic_ref_only"] is True
    assert legacy_ref["payload_body_omitted"] is True
    assert "owner_route" not in legacy_ref
    assert "prompt_contract" not in legacy_ref
    assert "source_action" not in legacy_ref
    assert "opl_domain_progress_transition_request" not in legacy_ref


def test_dhd_same_tick_admission_consumes_only_canonical_transition_requests(tmp_path: Path) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_report"
    )
    source = (
        REPO_ROOT
        / "src"
        / "med_autoscience"
        / "controllers"
        / "provider_admission_parts"
        / "provider_admission_report.py"
    ).read_text(encoding="utf-8")

    assert "import owner_callable_adapters" not in source
    assert "owner_callable_adapters(materialize_result)" not in source

    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "dispatch_status": "transition_request_pending",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
        },
    }

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "domain_action_request_materialization_preview": {
                "owner_callable_adapters": [dispatch],
            },
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_executable_owner_action": {
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        },
                    },
                },
            },
            "managed_study_actions": [{"study_id": study_id}],
        },
        apply=False,
        generated_at="2026-06-18T00:00:00+00:00",
    )

    assert result is None or result["transition_request_pending_count"] == 0
    assert result is None or result["provider_admission_pending_count"] == 0


def test_dhd_same_tick_blocker_summary_ignores_legacy_adapter_list() -> None:
    same_tick = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.developer_supervisor_same_tick"
    )
    legacy_blocked = {
        "study_id": "study-1",
        "action_type": "run_gate_clearing_batch",
        "dispatch_status": "blocked",
        "blocked_reason": "legacy_adapter_blocker_should_not_drive_summary",
    }
    canonical_blocked = {
        "study_id": "study-1",
        "action_type": "run_quality_repair_batch",
        "dispatch_status": "blocked",
        "blocked_reason": "canonical_transition_request_blocked",
    }

    diagnostic = same_tick._same_tick_terminal_diagnostic(
        stop_reason="typed_blocker_or_dispatch_blocker_observed",
        iterations=[
            {
                "materialize": {
                    "owner_callable_adapters": [legacy_blocked],
                    "domain_progress_transition_requests": [canonical_blocked],
                },
                "dispatch": {"executions": []},
                "progress_first_delta": {
                    "blocked_owner_callable_adapter_count": 1,
                    "legacy_blocked_owner_callable_adapter_count": 1,
                    "dispatch_blocked_count": 0,
                },
            }
        ],
    )

    summary = diagnostic["dispatch_blocker_summary"]
    assert summary["blocked_owner_callable_adapter_count"] == 1
    assert summary["legacy_blocked_owner_callable_adapter_count"] == 1
    assert summary["blocked_reasons"] == ["canonical_transition_request_blocked"]
    assert summary["blocked_actions"] == ["run_quality_repair_batch"]
    assert "legacy_adapter_blocker_should_not_drive_summary" not in summary["blocked_reasons"]


def test_dhd_dry_run_preview_does_not_consume_legacy_adapter_list_as_carrier() -> None:
    source = (
        REPO_ROOT
        / "src"
        / "med_autoscience"
        / "controllers"
        / "provider_admission_parts"
        / "runtime_dry_run_previews.py"
    ).read_text(encoding="utf-8")

    assert "import owner_callable_adapters" not in source
    assert "owner_callable_adapters(preview)" not in source
    assert "domain_progress_transition_requests(preview)" in source


def test_owner_action_execution_payloads_do_not_recommend_retired_private_cli_aliases() -> None:
    action_execution_root = (
        SRC_ROOT
        / "controllers"
        / "stage_outcome_authority_parts"
        / "action_execution"
    )
    forbidden_tokens = (
        "domain-action-request-materialize",
        "stage-outcome-authority",
    )
    violations: list[str] = []
    for path in sorted(action_execution_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_domain_owner_controller_refresh_public_wrapper_is_retired() -> None:
    dispatch_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority")
    public_surface = importlib.import_module("med_autoscience.cli_public_surface")

    assert not hasattr(dispatch_module, "refresh_controller_decisions_for_current_publication_eval")
    assert "refresh_controller_decisions_for_current_publication_eval" not in getattr(
        dispatch_module,
        "__all__",
        (),
    )
    assert (
        "runtime",
        "domain-owner-action-refresh-controller-decisions",
    ) not in public_surface.GROUPED_COMMAND_ALIASES


def test_retired_domain_owner_refresh_controller_command_is_not_active_cli_surface() -> None:
    retired_command = "domain-owner-action-refresh-controller-decisions"
    allowed_refs = {
        "tests/test_adapter_retirement_boundary.py",
        "tests/test_adapter_retirement_boundary_cases/owner_callable_projection.py",
        "tests/test_cli_cases/domain_action_request_materializer_command.py",
    }
    violations: list[str] = []
    for root in (SRC_ROOT, REPO_ROOT / "tests"):
        for path in sorted(root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if retired_command not in text:
                continue
            relative_path = str(path.relative_to(REPO_ROOT))
            if relative_path not in allowed_refs:
                violations.append(relative_path)

    assert violations == []


def test_current_controller_decision_refresh_does_not_emit_legacy_domain_owner_action_surface() -> None:
    source = (
        SRC_ROOT
        / "controllers"
        / "stage_outcome_authority_parts"
        / "controller_refresh.py"
    ).read_text(encoding="utf-8")

    assert "domain_owner_action_controller_decision_refresh" not in source
    assert 'SURFACE = "current_controller_decision_refresh"' in source


def test_paper_recovery_export_no_longer_materializes_default_executor_tasks(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.paper_recovery_owner_callable_tasks"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "dispatch_status": "transition_request_pending",
        "next_executable_owner": "write",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
        },
    }
    current_progress = {
        "study_id": study_id,
        "quest_id": study_id,
        "paper_recovery_state": {
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "run_mas_owner_callable",
            },
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
            },
        },
    }
    assert not hasattr(module, "domain_action_request_materializer")

    owner_callable_only_tasks = module.paper_recovery_owner_callable_stage_tasks(
        current_progress={
            **current_progress,
            "owner_callable_adapters": [dict(dispatch)],
        },
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
    )

    canonical_request_tasks = module.paper_recovery_owner_callable_stage_tasks(
        current_progress={
            **current_progress,
            "domain_progress_transition_requests": [dict(dispatch)],
        },
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
    )

    assert owner_callable_only_tasks == []
    assert canonical_request_tasks == []


def test_current_default_executor_dispatch_preview_api_is_physically_retired() -> None:
    materializer = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")

    assert not hasattr(materializer, "current_default_executor_dispatches")
    assert hasattr(materializer, "current_owner_callable_adapters")

    try:
        importlib.import_module(
            "med_autoscience.controllers.domain_action_request_materializer_parts.current_default_executor_dispatches"
        )
    except ModuleNotFoundError:
        return
    raise AssertionError("legacy current_default_executor_dispatches part module must stay retired")


__all__ = [name for name in globals() if name.startswith("test_")]
