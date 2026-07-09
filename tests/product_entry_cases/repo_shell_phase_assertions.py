from __future__ import annotations


def assert_manifest_phase_and_readiness_surfaces(*, module, payload, profile, profile_ref) -> None:
    phase3 = payload["phase3_clearance_lane"]
    assert phase3["surface_kind"] == "phase3_host_clearance_lane"
    assert phase3["recommended_step_id"] == "mas_domain_refs_boundary"
    assert {target["target_id"] for target in phase3["clearance_targets"]} == {
        "mas_domain_refs_boundary",
        "supervisor_service",
        "study_recovery_proof",
    }
    assert {surface["surface_kind"] for surface in phase3["proof_surfaces"]} >= {
        "doctor.runtime_contract",
        "paper_mission_readback",
    }

    phase4 = payload["phase4_backend_deconstruction"]
    assert phase4["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert "frozen MedDeepScientist source archive" in phase4["backend_retained_now"]
    assert phase4["promotion_rules"] == [
        "no claim of platform runtime ingest without owner + contract + tests + proof",
        "executor replacement must be explicit and proof-backed",
        "do not restore external MDS as a default runtime dependency",
    ]

    phase5 = payload["phase5_platform_target"]
    assert phase5["surface_kind"] == "phase5_platform_target"
    assert phase5["sequence_scope"] == "monorepo_landing_readiness"
    assert phase5["completed_step_ids"] == [
        "freeze_stage_runtime_truth",
        "mds_no_history_absorb",
        "runtime_core_ingest",
        "functional_monolith_completion",
    ]
    assert phase5["remaining_step_ids"] == [
        "optional_hosted_frontend_packaging",
        "future_upstream_source_intake_review",
    ]

    assert set(payload["product_entry_shell"]) >= {
        "workspace_cockpit",
        "product_entry_status",
        "submit_study_task",
        "launch_study",
        "study_progress",
    }
    assert payload["family_orchestration"]["resume_contract"]["surface_kind"] == "launch_study"
    assert payload["family_orchestration"]["human_gates"] == [
        {"gate_id": "study_user_decision_gate", "title": "Study user decision gate"},
        {"gate_id": "publication_release_gate", "title": "Publication release gate"},
    ]
    assert [node["node_id"] for node in payload["family_orchestration"]["action_graph"]["nodes"]] == [
        "step:open_product_entry",
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
        "step:export_inspection_package",
    ]
    start = payload["product_entry_start"]
    assert start["surface_kind"] == "product_entry_start"
    assert start["recommended_mode_id"] == "open_product_entry"
    assert start["resume_surface"] == payload["family_orchestration"]["resume_contract"]
