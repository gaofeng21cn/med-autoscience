from __future__ import annotations

import importlib
from pathlib import Path


def _truth_snapshot() -> dict[str, object]:
    return {
        "surface": "study_truth_snapshot",
        "truth_epoch": "truth-event-000004-live",
        "authority_epoch": "truth-event-000004-live",
        "canonical_next_action": "supervise_runtime",
        "blocking_reasons": [
            "execution_owner_guard.supervisor_only",
            "publication_supervisor_state.bundle_tasks_downstream_only",
        ],
        "dominant_authority_refs": [
            {
                "event_id": "truth-event-000004-live",
                "event_type": "runtime_supervision_tick",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "allowed_controller_actions": ["read_runtime_status", "open_monitoring_entry"],
        "package_state": {
            "authority_state": "provisionally_current_for_epoch",
            "writer_epoch": "writer::run-e52f5574",
            "source_signature": "source::abc",
        },
        "writer_epoch": "writer::run-e52f5574",
        "source_signature": "truth-snapshot::abc",
    }


def _control_plane_snapshot() -> dict[str, object]:
    return {
        "surface": "control_plane_snapshot",
        "control_state": "supervisor_gated",
        "canonical_next_action": "supervise_runtime",
        "canonical_runtime_action": "continue_supervising_runtime",
        "dispatch_gate": {
            "state": "blocked",
            "dispatch_allowed": False,
            "blocking_reasons": ["execution_owner_guard.supervisor_only"],
        },
        "route_authorization": {
            "authorized": False,
            "paper_write_allowed": False,
            "bundle_build_allowed": False,
        },
        "blocking_reasons": ["execution_owner_guard.supervisor_only"],
        "allowed_controller_actions": ["read_runtime_status", "open_monitoring_entry"],
        "authority_refs": {
            "study_truth": {"epoch": "truth-event-000004-live"},
            "runtime_health": {"epoch": "runtime-health-event-000004-live"},
        },
    }


def _study_macro_state() -> dict[str, object]:
    return {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": "003-dpcc",
        "writer_state": "parked",
        "user_next": "submit_info",
        "reason": "external_info",
        "details": {
            "truth_epoch": "truth-event-000004-live",
            "missing_external_info": ["authors", "ethics"],
            "package_delivered": True,
            "reopen_allowed": True,
            "reopen_mode": "external_info_or_revision_intake",
        },
        "conditions": [
            {
                "type": "ExternalInfoPending",
                "status": "true",
                "summary": "submission package waits for external metadata",
            }
        ],
        "source_fingerprint": "macro::003-dpcc",
    }


def test_study_progress_compact_payload_derives_macro_state_from_current_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    payload = module._normalize_study_progress_payload(
        {
            "study_id": "003-dpcc",
            "quest_status": "paused",
            "reason": "quest_waiting_for_submission_metadata",
            "auto_runtime_parked": {"parked": True, "parked_state": "external_metadata_pending"},
            "submission_metadata": {"missing_external_info": ["authors", "ethics"]},
            "study_truth_snapshot": {
                **_truth_snapshot(),
                "package_state": {"authority_state": "current"},
            },
        }
    )

    assert payload["study_macro_state"]["writer_state"] == "parked"
    assert payload["study_macro_state"]["user_next"] == "submit_info"
    assert payload["study_macro_state"]["reason"] == "external_info"


def test_mcp_progress_compact_projection_carries_truth_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(
        {
            "study_id": "003-dpcc",
            "truth_epoch": "truth-event-000004-live",
            "current_stage": "runtime_supervision",
            "study_truth_snapshot": _truth_snapshot(),
            "control_plane_snapshot": _control_plane_snapshot(),
            "refs": {"study_truth_snapshot_path": "/workspace/studies/003/artifacts/truth/latest.json"},
        }
    )

    assert compact["truth_epoch"] == "truth-event-000004-live"
    assert compact["study_truth_snapshot"] == {
        "truth_epoch": "truth-event-000004-live",
        "authority_epoch": "truth-event-000004-live",
        "canonical_next_action": "supervise_runtime",
        "blocking_reasons": [
            "execution_owner_guard.supervisor_only",
            "publication_supervisor_state.bundle_tasks_downstream_only",
        ],
        "dominant_authority_refs": [
            {
                "event_id": "truth-event-000004-live",
                "event_type": "runtime_supervision_tick",
                "recorded_at": "2026-05-01T00:00:00+00:00",
            }
        ],
        "allowed_controller_actions": ["read_runtime_status", "open_monitoring_entry"],
        "package_state": {
            "authority_state": "provisionally_current_for_epoch",
            "writer_epoch": "writer::run-e52f5574",
            "source_signature": "source::abc",
        },
        "writer_epoch": "writer::run-e52f5574",
        "source_signature": "truth-snapshot::abc",
    }
    assert compact["control_plane_snapshot"]["control_state"] == "supervisor_gated"
    assert compact["control_plane_snapshot"]["dispatch_gate"]["state"] == "blocked"


def test_mcp_progress_markdown_renders_medical_paper_readiness_summary() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    payload = {
        "study_id": "003-dpcc",
        "current_stage": "writing",
        "medical_paper_readiness": {
            "surface": "medical_paper_readiness",
            "overall_status": "blocked",
            "ready_count": 4,
            "required_count": 7,
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
            "next_action": {
                "summary": "补齐 Stop-loss Memo 后再继续自动论文链路。",
            },
            "capability_surfaces": [
                {
                    "surface_key": "stop_loss_memo",
                    "status": "missing",
                    "missing_reason": "missing_canonical_artifact",
                    "required_for_ready": True,
                }
            ],
        },
    }

    compact = module.compact_study_progress_projection(payload)
    readiness = compact["medical_paper_readiness"]
    markdown = module.render_mcp_study_progress_markdown(payload)

    assert readiness["surface"] == "medical_paper_readiness"
    assert readiness["overall_status"] == "blocked"
    assert readiness["ready_count"] == 4
    assert readiness["required_count"] == 7
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    assert readiness["missing_surfaces"][0]["surface_key"] == "stop_loss_memo"
    assert readiness["missing_surfaces"][0]["missing_reason"] == "missing_canonical_artifact"
    assert markdown.strip()


def test_workspace_cockpit_study_item_carries_truth_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    item = module._study_item(
        progress_payload={
            "study_id": "003-dpcc",
            "truth_epoch": "truth-event-000004-live",
            "study_truth_snapshot": {**_truth_snapshot(), "study_macro_state": _study_macro_state()},
            "control_plane_snapshot": _control_plane_snapshot(),
            "supervision": {"active_run_id": "run-e52f5574"},
        },
        profile_ref="/tmp/profile.toml",
    )

    assert item["truth_epoch"] == "truth-event-000004-live"
    assert item["control_plane_snapshot"]["control_state"] == "supervisor_gated"
    assert item["study_truth_snapshot"]["canonical_next_action"] == "supervise_runtime"
    assert item["study_truth_snapshot"]["package_state"]["authority_state"] == "provisionally_current_for_epoch"
    assert item["study_macro_state"]["writer_state"] == "live"
    assert item["study_macro_state"]["user_next"] == "watch"
    assert item["study_macro_state"]["reason"] == "runtime"
    assert item["study_macro_state"]["details"]["active_run_id"] == "run-e52f5574"


def test_mcp_compact_projection_carries_study_macro_state() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(
        {
            "study_id": "003-dpcc",
            "truth_epoch": "truth-event-000004-live",
            "current_stage": "metadata_wait",
            "study_macro_state": _study_macro_state(),
        }
    )

    assert compact["study_macro_state"] == {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": "003-dpcc",
        "writer_state": "parked",
        "user_next": "submit_info",
        "reason": "external_info",
        "details": {
            "truth_epoch": "truth-event-000004-live",
            "missing_external_info": ["authors", "ethics"],
            "package_delivered": True,
            "reopen_allowed": True,
            "reopen_mode": "external_info_or_revision_intake",
        },
        "conditions": [
            {
                "type": "ExternalInfoPending",
                "status": "true",
                "summary": "submission package waits for external metadata",
            }
        ],
        "source_fingerprint": "macro::003-dpcc",
    }


def test_runtime_watch_managed_study_action_carries_truth_snapshot_summary() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_parts.managed_wakeup")

    action = module._serialize_managed_study_action(
        {
            "study_id": "003-dpcc",
            "decision": "blocked",
            "reason": "study_completion_publishability_gate_blocked",
            "study_truth_snapshot": _truth_snapshot(),
        }
    )

    assert action["truth_epoch"] == "truth-event-000004-live"
    assert action["study_truth_snapshot"]["canonical_next_action"] == "supervise_runtime"
    assert action["study_truth_snapshot"]["allowed_controller_actions"] == [
        "read_runtime_status",
        "open_monitoring_entry",
    ]


def test_product_entry_surfaces_expose_medical_writing_quality_artifacts() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    artifact_inventory = module._build_artifact_inventory_surface(
        profile=type("Profile", (), {"workspace_root": Path("/tmp/workspace"), "runtime_root": Path("/tmp/runtime")})(),
        progress_projection={},
        product_entry_shell={"launch_study": {"command": "launch"}, "study_progress": {"command": "progress"}},
        study_runtime_status_command="status",
    )

    file_ids = {item["file_id"] for item in artifact_inventory["supporting_files"]}
    assert "medical_manuscript_blueprint" in file_ids
    assert "medical_journal_style_corpus" in file_ids
    assert "medical_prose_review_request" in file_ids
    assert "medical_prose_review" in file_ids
    assert "retrospective_medical_prose_audit" in file_ids

    control_projection = module._build_research_runtime_control_projection(
        resume_command="launch",
        check_progress_command="progress",
        check_runtime_status_command="status",
        surface_kind="research_runtime_control_projection",
    )
    assert control_projection["medical_writing_quality_surface"]["subjective_quality_owner"] == "ai_reviewer"
    assert control_projection["medical_writing_quality_surface"]["mechanical_flags_role"] == (
        "evidence_snippets_only"
    )
    assert "refs.medical_prose_review_path" in control_projection["artifact_pickup_surface"]["fallback_fields"]
