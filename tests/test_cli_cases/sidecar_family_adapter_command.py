from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_opl_production_proof(path: Path) -> None:
    checks = {
        "external_temporal_server_reachable": True,
        "managed_worker_ready": True,
        "worker_completed_attempt": True,
        "worker_restart_requery": True,
        "signal_history_preserved": True,
        "typed_closeout_required_for_completed": True,
        "missing_closeout_blocks_completion": True,
        "retry_or_dead_letter_boundary_observed": True,
        "domain_truth_boundary_preserved": True,
    }
    _write_json(
        path,
        {
            "family_runtime_residency_proof": {
                "surface_kind": "opl_temporal_production_residency_proof",
                "provider_kind": "temporal",
                "closeout_status": "production_residency_proven",
                "production_residency_proof": {
                    "surface_kind": "opl_temporal_external_production_residency_proof",
                    "provider_kind": "temporal",
                    "closeout_status": "production_residency_proven",
                    "runtime_snapshot": {
                        "address_source": "managed_local_service_state",
                        "lifecycle_status": "ready",
                        "server_reachable": True,
                        "worker_ready": True,
                        "task_queue": "opl-stage-attempts",
                    },
                    "proof_receipt": {
                        "receipt_kind": "temporal_production_residency_proof",
                        "receipt_status": "proven",
                        "completed_workflow_id": "wf-complete",
                        "blocked_workflow_id": "wf-blocked",
                    },
                    "checks": checks,
                },
            }
        },
    )


def _ai_reviewer_blocking_eval(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    main_result_ref = str(quest_root / "artifacts" / "results" / "main_result.json")
    manuscript_ref = str(study_root / "paper" / "manuscript.md")
    study_charter_ref = str(study_root / "artifacts" / "controller" / "study_charter.json")
    review_ledger_ref = str(study_root / "paper" / "review" / "review_ledger.json")
    input_bundle = {
        "manuscript": manuscript_ref,
        "study_charter": study_charter_ref,
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": review_ledger_ref,
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    rubric_scores = {
        "clinical_significance": {
            "status": "ready",
            "rationale": "Clinical framing is stable.",
            "evidence_refs": [study_charter_ref],
        },
        "evidence_strength": {
            "status": "partial",
            "rationale": "Bounded sensitivity analysis is still missing.",
            "evidence_refs": [main_result_ref],
        },
        "novelty_positioning": {
            "status": "ready",
            "rationale": "Contribution boundary is defined.",
            "evidence_refs": [study_charter_ref],
        },
        "medical_journal_prose_quality": {
            "status": "partial",
            "rationale": "The discussion overstates observational evidence.",
            "evidence_refs": [manuscript_ref],
        },
        "human_review_readiness": {
            "status": "ready",
            "rationale": "Administrative human review can wait until repair is complete.",
            "evidence_refs": [review_ledger_ref],
        },
    }
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-10T00:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-10T00:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": study_charter_ref,
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": main_result_ref,
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [manuscript_ref, main_result_ref],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Evidence strength and claim wording require repair.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": {
            "clinical_significance": {
                "status": "ready",
                "summary": "Clinical framing is stable.",
                "evidence_refs": [study_charter_ref],
            },
            "evidence_strength": {
                "status": "partial",
                "summary": "Main result supports direction but not final claim strength.",
                "evidence_refs": [main_result_ref],
                "reviewer_revision_advice": "Add bounded sensitivity analysis before acceptance.",
            },
            "novelty_positioning": {
                "status": "ready",
                "summary": "Contribution boundary is defined.",
                "evidence_refs": [study_charter_ref],
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "summary": "Discussion wording is too strong for observational evidence.",
                "evidence_refs": [manuscript_ref],
                "reviewer_revision_advice": "Revise text to restrained association language.",
            },
            "human_review_readiness": {
                "status": "ready",
                "summary": "Human review can wait until evidence and prose repair are complete.",
                "evidence_refs": [review_ledger_ref],
            },
        },
        "reviewer_operating_system": {
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
            "provenance_checks": {
                "assessment_owner": "ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "route_back_decision": {
                "recommended_action": "route_back_same_line",
                "rationale": "Repair before acceptance.",
            },
        },
        "gaps": [
            {
                "gap_id": "claim-strength",
                "gap_type": "claim",
                "severity": "must_fix",
                "summary": "Claim strength exceeds the current evidence ledger.",
                "evidence_refs": [main_result_ref],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "route-back-claim-strength",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Repair claim wording within the same paper line.",
                "route_target": "write",
                "route_key_question": "Which claim sentence exceeds evidence strength?",
                "route_rationale": "AI reviewer requires same-line manuscript repair before package advance.",
                "evidence_refs": [main_result_ref],
                "requires_controller_decision": True,
            }
        ],
    }


def test_sidecar_export_projects_mas_owned_runtime_surfaces(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {"state": "running", "owner_route": {"owner": "mas_controller"}},
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "worker_recovery"},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "recovery_intent" / "latest.json",
        {"current_action": "safe_reconcile_ready", "retry_budget": {"remaining": 2}},
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"decision_id": "decision-001", "owner_route": {"owner": "publication_controller"}},
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_export"
    assert payload["target_domain_id"] == "medautoscience"
    framework = payload["online_runtime_framework"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert framework["executor_adapter_requirement"] == {
        "owner": "one-person-lab",
        "generic_executor_adapter_owner": "one-person-lab",
        "default_executor_kind": "codex_cli_default",
        "required_capability": "opl_executor_adapter_receipt",
        "mas_accepts": "typed_closeout_or_domain_task_receipt",
        "mas_local_codex_cli_scope": "standalone_diagnostics_only",
        "external_executor_opt_in_policy": "explicit_opl_opt_in_then_typed_receipt_only",
        "mas_owned_hermes_or_claude_executor": False,
        "mas_does_not_provide": ["hosted_executor", "hermes_executor_adapter", "claude_executor_adapter"],
    }
    assert "diagnostic_providers" not in framework
    assert framework["optional_executor_adapters"] == [
        {
            "adapter_id": "hermes_agent",
            "display_name": "Hermes-Agent",
            "classification": "explicit_optional_executor_adapter",
            "runtime_policy": "explicit_opl_opt_in_then_typed_receipt_only",
            "executor_policy": "not_a_mas_executor_adapter",
            "default_provider": False,
        }
    ]
    assert payload["authority_boundary"]["domain_truth_owner"] == "med-autoscience"
    assert payload["authority_boundary"]["online_runtime_provider_owner"] == "opl_family_runtime_provider"
    assert payload["authority_boundary"]["mas_domain_authority"] == [
        "study_truth",
        "runtime_health_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "owner_route_decision",
    ]
    assert payload["authority_boundary"]["opl_receipt_policy"] == "transport_receipt_only_no_domain_truth_authority"
    assert payload["authority_boundary"]["forbidden_authorities"] == [
        "study_truth_write",
        "publication_quality_verdict",
        "artifact_gate_override",
        "current_package_write",
    ]
    assert payload["profile"]["profile_ref"] == str(profile_path)
    assert payload["workspace"]["workspace_root"] == str(workspace_root)
    provider = payload["provider_ready_adapter"]
    assert provider["surface_kind"] == "mas_opl_provider_ready_contract"
    assert provider["provider_topology"]["target_provider"] == "temporal"
    assert provider["provider_topology"]["provider_attempt_is_truth"] is False
    assert "legacy_provider" not in provider["provider_topology"]
    assert "legacy_provider_classification" not in provider["provider_topology"]
    assert provider["legacy_retirement_tombstone_proof"]["status"] == "no_active_default_caller_proven"
    assert provider["executor_requirements"] == {
        "adapter_owner": "one-person-lab",
        "generic_executor_adapter_owner": "one-person-lab",
        "default_executor_kind": "codex_cli_default",
        "required_adapter": "opl_executor_adapter",
        "accepted_receipts": ["opl_provider_attempt_receipt", "typed_closeout_receipt"],
        "domain_action_authority": "med-autoscience",
        "mas_builtin_executor_adapter": False,
        "mas_local_codex_cli_scope": "standalone_diagnostics_only",
        "non_default_executor_opt_in_owner": "one-person-lab",
        "non_default_executor_opt_in_policy": "explicit_opt_in_only_receipt_to_mas",
        "mas_owned_hermes_or_claude_executor": False,
    }
    assert provider["direct_mas_path"]["status"] == "authoritative"
    assert provider["truth_source_precedence"]["direct_mas_skill_path"] == "authoritative"
    assert provider["truth_source_precedence"]["provider_completion_can_advance_paper_progress"] is False
    assert provider["workspace_runtime_artifact_root_locator"]["repo_root_tracks_real_artifacts"] is False
    assert provider["sidecar_contract"]["queue_hydration_source"] == "/pending_family_tasks"
    assert payload["dispatch"]["receipt_refs"]["dispatch_receipt_root"] == (
        "artifacts/runtime/opl_family_sidecar/dispatch_receipts"
    )
    assert payload["studies"][0]["study_id"] == "001-risk"
    assert payload["studies"][0]["runtime_supervision"]["state"] == "running"
    assert payload["studies"][0]["slo_status"]["state"] == "breach"
    assert payload["studies"][0]["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert payload["pending_family_tasks"][0]["domain_id"] == "medautoscience"
    assert payload["pending_family_tasks"][0]["task_kind"] == "runtime_supervisor/reconcile-apply"
    assert payload["pending_family_tasks"][0]["payload"]["profile"] == str(profile_path)
    assert payload["pending_family_tasks"][0]["payload"]["study_id"] == "001-risk"
    assert payload["pending_family_tasks"][0]["requires_approval"] is False
    assert payload["pending_family_tasks"][0]["dedupe_key"].startswith("mas:nfpitnet:001-risk:autonomy-continuation:")


def test_sidecar_export_projects_memory_paper_soak_proof_refs_readonly(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "stage_knowledge" / "paper_soak_memory_apply_proof" / "latest.json",
        {
            "surface": "paper_soak_memory_apply_proof",
            "schema_version": 1,
            "study_id": "001-risk",
            "stage": "decision",
            "status": "ready",
            "stage_entry": {
                "publication_route_memory_refs": [
                    {
                        "memory_id": "publication_route_memory_seed__negative_result_stoploss",
                        "memory_pack_ref": "portfolio/research_memory/publication_route_memory/memory_pack.json",
                    }
                ]
            },
            "typed_closeout_writeback_proposals": [{"ref": "closeouts/decision.json", "body_included": False}],
            "mas_router_receipt_refs": [{"ref": "router/r1.json", "status": "applied", "body_included": False}],
            "opl_aion_readonly_receipt_refs": [
                {
                    "ref_kind": "memory_write_router_receipt",
                    "ref": "router/r1.json",
                    "status": "applied",
                    "display_role": "receipt_ref_only",
                    "consumer": "OPL/Aion",
                    "body_included": False,
                }
            ],
            "source_fingerprint": "proof-fp",
            "authority_boundary": {"can_authorize_publication_quality": False},
            "read_only_display_policy": {
                "consumer_role": "OPL/Aion read-only display",
                "repo_tracks_memory_body": False,
                "repo_tracks_receipt_instances": False,
                "can_write_study_truth": False,
            },
        },
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    projection = payload["studies"][0]["memory_paper_soak_proof"]
    assert projection["surface_kind"] == "mas_memory_paper_soak_proof_projection"
    assert projection["status"] == "ready"
    assert projection["proof_ref"] == (
        "studies/001-risk/artifacts/stage_knowledge/paper_soak_memory_apply_proof/latest.json"
    )
    assert projection["route_memory_ref_count"] == 1
    assert projection["router_receipt_ref_count"] == 1
    assert projection["writeback_proposal_ref_count"] == 1
    assert projection["receipt_refs"] == [
        {
            "ref_kind": "memory_write_router_receipt",
            "ref": "router/r1.json",
            "status": "applied",
            "display_role": "receipt_ref_only",
            "consumer": "OPL/Aion",
            "body_included": False,
        }
    ]
    assert projection["read_only_display_policy"]["repo_tracks_memory_body"] is False
    assert projection["read_only_display_policy"]["can_write_study_truth"] is False
    assert "prose_summary" not in json.dumps(projection, ensure_ascii=False)


def test_sidecar_export_consumes_opl_production_proof_without_domain_authority(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root / "studies" / "001-risk" / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {"state": "running"},
    )
    _write_opl_production_proof(proof_ref)

    exit_code = cli.main(
        [
            "sidecar",
            "export",
            "--profile",
            str(profile_path),
            "--opl-production-proof",
            str(proof_ref),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    read_model = payload["provider_ready_adapter"]["provider_guarded_soak_read_model"]
    availability = read_model["provider_availability"]

    assert exit_code == 0
    assert payload["provider_ready_adapter"]["provider_topology"]["provider_state"] == (
        "production_residency_proven"
    )
    assert availability["status"] == "available"
    assert availability["provider_attempt_available"] is True
    assert availability["proof_ref"] == str(proof_ref)
    assert availability["semantics"]["provider_completion_is_paper_closure"] is False
    assert availability["semantics"]["mas_runtime_watch_role"] == "domain_truth_and_local_diagnostics"
    managed_state = payload["managed_temporal_state_consistency"]
    assert managed_state["surface_kind"] == "mas_opl_managed_temporal_state_consistency"
    assert managed_state["status"] == "consistent"
    assert managed_state["provider_state"] == "production_residency_proven"
    assert managed_state["managed_state"] == {
        "address_source": "managed_local_service_state",
        "lifecycle_status": "ready",
        "server_reachable": True,
        "worker_ready": True,
        "task_queue": "opl-stage-attempts",
    }
    assert managed_state["opl_status_projection"]["managed_service_state"] == "ready"
    assert managed_state["opl_status_projection"]["worker_state"] == "ready"
    assert managed_state["opl_status_projection"]["attempt_query_ready"] is True
    assert managed_state["authority_boundary"]["can_write_domain_truth"] is False
    tombstone = payload["legacy_retirement_tombstone_proof"]
    assert tombstone["surface_kind"] == "mas_legacy_retirement_tombstone_proof"
    assert tombstone["status"] == "no_active_default_caller_proven"
    assert tombstone["active_default_callers"] == []
    assert {item["surface_id"] for item in tombstone["retired_or_tombstoned_surfaces"]} == {
        "hermes_agent_executor_adapter",
        "hermes_scheduler_hosted_runtime",
        "mds_deepscientist_backend",
        "workspace_local_scheduler",
    }
    assert tombstone["authority_boundary"]["can_authorize_publication_quality"] is False
    assert read_model["provider_completion_semantics"] == {
        "provider_completion_is_paper_closure": False,
        "queue_completion_is_paper_closure": False,
        "paper_closure_requires_mas_owner_receipt": True,
        "mutation_proof_surface": "MAS owner receipt",
    }
    assert read_model["authority_boundary"]["can_write_domain_truth"] is False
    assert read_model["authority_boundary"]["can_authorize_publication_quality"] is False
    assert all(
        item["status"] == "provider_available_guarded_apply_pending"
        for item in read_model["target_coverage"]
    )
    closure = payload["mas_functional_closure_status_projection"]
    assert closure["surface_kind"] == "mas_functional_closure_status_projection"
    assert closure["summary"]["production_evidence_pending_count"] == 2
    assert closure["authority_boundary"]["provider_completion_is_paper_closure"] is False
    by_line = {line["line_id"]: line for line in closure["lines"]}
    assert by_line["p2_provider_residency_and_activity_soak"]["status"] == (
        "provider_residency_projected_domain_activity_soak_pending"
    )
    assert by_line["p0_live_paper_autonomy_acceptance"]["typed_blockers"][0]["blocker_id"] == (
        "provider_hosted_live_paper_apply_pending"
    )
    assert by_line["legacy_residue_retirement"]["status"] == (
        "no_active_default_caller_proven_cleanup_policy_satisfied"
    )
    guarded_apply_tasks = [
        task for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ]
    assert guarded_apply_tasks == [
        {
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "priority": 30,
            "source": "mas-sidecar-export",
            "requires_approval": False,
            "dedupe_key": "mas:nfpitnet:DM002:provider-hosted-guarded-apply:opl-temporal",
            "payload": {
                "profile": str(profile_path),
                "study_id": "DM002",
                "target_studies": ["DM002"],
                "provider_attempt_id": "opl-temporal:nfpitnet:DM002:provider-hosted-guarded-apply",
                "idempotency_key": "mas:nfpitnet:DM002:provider-hosted-guarded-apply:opl-temporal",
                "paper_autonomy_reason": "provider_hosted_guarded_apply_soak",
                "authority_boundary": "mas_owner_guarded_apply_only",
            },
            "dispatch_owner": "med-autoscience",
            "profile_name": "nfpitnet",
            "source_refs": [
                {
                    "role": "opl_production_proof",
                    "ref": str(proof_ref),
                    "exists": True,
                },
                {
                    "role": "provider_guarded_soak_read_model",
                    "ref": "/provider_ready_adapter/provider_guarded_soak_read_model",
                    "exists": True,
                },
            ],
        }
    ]


def test_sidecar_export_projects_ai_reviewer_repair_recheck_tasks(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["paper_autonomy_loop"]["status"] == "repair_recheck_ready"
    assert study["paper_autonomy_loop"]["eligible_for_auto_dispatch"] is True
    repair_tasks = [
        task for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/repair-recheck"
    ]
    assert repair_tasks
    first_task = repair_tasks[0]
    assert first_task["payload"]["profile"] == str(profile_path)
    assert first_task["payload"]["study_id"] == "001-risk"
    assert first_task["payload"]["authority_boundary"] == "mas_owner_reconcile_only"
    assert first_task["dispatch_owner"] == "med-autoscience"
    unit = first_task["payload"]["repair_work_unit"]
    assert unit["owner"] in {"quality_repair_batch", "ai_reviewer"}
    assert unit["callable_surface"]
    assert unit["gate_replay_target"] in {
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
    }
    assert unit["direct_package_mutation_allowed"] is False
    assert unit["current_package_mutation_allowed"] is False
    assert unit["quality_authorization_allowed"] is False
    assert unit["submission_authorization_allowed"] is False
    assert unit["prohibited_outputs"] == [
        "paper/current_package",
        "manuscript/current_package",
        "quality_override",
        "submission_authorization",
    ]


def test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_001",
            "domain_id": "medautoscience",
            "task_kind": "runtime_supervision/recover",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
            "attempts": 1,
            "source": "opl_family_runtime",
            "authority_boundary": {
                "provider": "online_runtime_transport_only",
                "opl": "typed_queue_and_dispatch_only",
                "domain": "truth_quality_artifact_gate_owner",
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert payload["accepted"] is True
    assert payload["will_start_llm_worker"] is False
    assert payload["dispatch"]["action_type"] == "runtime_supervisor_recover"
    assert payload["dispatch"]["recommended_domain_command"].startswith("uv run python -m med_autoscience.cli runtime-supervisor-scan")
    assert payload["authority_boundary"]["writes_domain_truth"] is False
    assert payload["authority_boundary"]["writes_artifact_gate"] is False
    assert payload["forbidden_write_guard_proof"]["result"] == "accepted_no_forbidden_writes"
    assert payload["forbidden_write_guard_proof"]["can_write_domain_truth"] is False


def test_sidecar_dispatch_executes_reconcile_apply_inside_mas_owner(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.sidecar_family_adapter")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_supervisor_reconcile(*, profile, study_ids, mode: str, apply: bool) -> dict[str, object]:
        calls.append({"profile": profile.name, "study_ids": tuple(study_ids), "mode": mode, "apply": apply})
        return {
            "surface": "runtime_supervisor_reconcile_receipt",
            "resolved_studies": list(study_ids),
            "will_start_llm": True,
            "codex_dispatch_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(adapter.runtime_supervisor_reconcile, "supervisor_reconcile", fake_supervisor_reconcile)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_reconcile",
            "domain_id": "medautoscience",
            "task_kind": "runtime_supervisor/reconcile-apply",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert calls == [{"profile": "nfpitnet", "study_ids": ("001-risk",), "mode": "developer_apply_safe", "apply": True}]
    assert payload["accepted"] is True
    assert payload["will_start_llm_worker"] is True
    assert payload["dispatch"]["execution_policy"] == "mas_owner_reconcile_apply"
    assert payload["dispatch"]["result"]["surface"] == "runtime_supervisor_reconcile_receipt"
    assert payload["authority_boundary"]["writes_domain_truth"] is False


def test_sidecar_dispatch_executes_paper_repair_work_unit_inside_mas_owner(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    manuscript = study_root / "paper" / "manuscript.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-001",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-1",
                    "work_unit_type": "text_repair",
                    "owner": "quality_repair_batch",
                    "callable_surface": "paper_repair_executor.dispatch_repair_work_unit",
                    "source_fingerprint": "sha256:unit-1",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "publication_eval/latest.json",
                    "canonical_patch": {
                        "target_text": "The original claim is supported.",
                        "replacement_text": "The association is directionally consistent but requires restrained interpretation.",
                    },
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    assert payload["will_start_llm_worker"] is False
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["execution_status"] == "executed"
    assert paper_receipt["repair_execution_evidence"]["progress_delta_candidate"] is True
    assert paper_receipt["owner_receipt"]["direct_current_package_write"] is False
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_sidecar_dispatch_routes_paper_ai_reviewer_recheck_to_supervisor_executor(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.sidecar_family_adapter")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_execute_default_executor_dispatches(*, profile, study_ids, action_types, mode: str, apply: bool) -> dict[str, object]:
        calls.append(
            {
                "profile": profile.name,
                "study_ids": tuple(study_ids),
                "action_types": tuple(action_types),
                "mode": mode,
                "apply": apply,
            }
        )
        return {
            "surface": "runtime_supervisor_default_executor_execution",
            "executed_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(
        adapter.runtime_supervisor_dispatch_executor,
        "execute_default_executor_dispatches",
        fake_execute_default_executor_dispatches,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-ai-reviewer-001",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/ai-reviewer-recheck",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["dispatch"]["action_type"] == "ai_reviewer_recheck_execute_dispatch"
    assert payload["dispatch"]["result"]["executed_count"] == 1
    assert calls == [
        {
            "profile": "nfpitnet",
            "study_ids": ("001-risk",),
            "action_types": ("return_to_ai_reviewer_workflow",),
            "mode": "developer_apply_safe",
            "apply": True,
        }
    ]


def test_sidecar_export_does_not_auto_ticket_stop_loss_or_human_gate(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    stop_loss_root = workspace_root / "studies" / "stop-loss-study"
    human_gate_root = workspace_root / "studies" / "human-gate-study"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        stop_loss_root / "artifacts" / "controller_decisions" / "latest.json",
        {"decision_type": "stop_loss", "route_target": "stop"},
    )
    _write_json(
        stop_loss_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "same_fingerprint_loop"},
    )
    _write_json(
        human_gate_root / "artifacts" / "controller_decisions" / "latest.json",
        {"requires_human_confirmation": True, "family_human_gates": [{"gate_id": "confirm-target"}]},
    )
    _write_json(
        human_gate_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "same_fingerprint_loop"},
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["pending_family_tasks"] == []
    assert payload["studies"][0]["autonomy_continuation"]["eligible_for_auto_dispatch"] is False
    assert payload["studies"][1]["autonomy_continuation"]["eligible_for_auto_dispatch"] is False


def test_sidecar_export_exposes_domain_declared_transition_spec_without_domain_truth_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "publication-blocked"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "status": "blocked",
            "blockers": ["claim_specificity_gap"],
            "assessment_provenance": {"owner": "publication_gate"},
        },
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    descriptor = payload["family_transition_spec_descriptor"]
    assert descriptor["surface_kind"] == "family_transition_spec_descriptor"
    assert descriptor["target_domain_id"] == "medautoscience"
    assert descriptor["spec_surface_kind"] == "family_transition_spec"
    assert descriptor["contract_version"] == "family-transition-runner.v1"
    assert descriptor["authority_boundary"]["runner_owner"] == "OPL Framework"
    assert descriptor["authority_boundary"]["can_write_domain_truth"] is False
    assert descriptor["authority_boundary"]["opl_interprets_domain_quality"] is False
    assert descriptor["locator_refs"]["study_state_matrix_spec"] == "/study_state_matrix/domain_transition_table/family_transition_spec"
    assert payload["authority_boundary"]["writes_domain_truth"] is False


def test_sidecar_dispatch_rejects_domain_truth_writes(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_forbidden",
            "domain_id": "medautoscience",
            "task_kind": "artifact/override",
            "payload": {"domain_truth_write": True, "profile": "/tmp/profile.toml"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert payload["accepted"] is False
    assert payload["forbidden_domain_truth_write"] is True
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == ["domain_truth_write"]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["surface_kind"] == "mas_opl_forbidden_write_guard_proof"
    assert guard["result"] == "blocked"
    assert guard["guard_mode"] == "fail_closed"
    assert guard["can_write_domain_truth"] is False


def test_sidecar_dispatch_rejects_opl_attempt_truth_substitution(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "attempt-substitution",
            "domain_id": "medautoscience",
            "task_kind": "runtime_supervision/recover",
            "payload": {
                "profile": "/tmp/profile.toml",
                "study_id": "001-risk",
                "requested_writes": ["controller_decisions", "publication_eval"],
                "opl_attempt_status": "completed",
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == ["controller_decisions", "publication_eval"]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["forbidden_requested_writes"] == ["controller_decisions", "publication_eval"]
    assert guard["can_authorize_publication_quality"] is False


def test_sidecar_dispatch_rejects_opl_memory_body_or_router_acceptance_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "memory-body-write",
            "domain_id": "medautoscience",
            "task_kind": "study_progress/read",
            "payload": {
                "profile": "/tmp/profile.toml",
                "study_id": "001-risk",
                "requested_writes": [
                    "publication_route_memory_body",
                    "memory_write_router_accept",
                ],
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == [
        "publication_route_memory_body",
        "memory_write_router_accept",
    ]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["guard_owner"] == "med-autoscience"
    assert guard["can_write_domain_truth"] is False
