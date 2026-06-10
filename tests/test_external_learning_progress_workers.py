from __future__ import annotations

import importlib


FORBIDDEN_TRUTH_WRITES = {
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
}


def test_ark_progress_worker_advisory_emits_required_refs_only_candidates() -> None:
    module = importlib.import_module("med_autoscience.external_learning_progress_workers")

    advisory = module.build_ark_progress_worker_advisory(
        {
            "action_type": "run_gate_clearing_batch",
            "action_id": "dispatch-ark-001",
            "owner_route": {
                "owner": "publication_gate",
                "work_unit_id": "gate-clearing",
            },
            "refs": {"dispatch_path": "artifacts/supervision/current.json"},
        }
    )

    assert advisory["surface_kind"] == "mas_ark_progress_worker_advisory"
    assert advisory["schema_version"] == 1
    assert advisory["status"] == "candidate_refs_emitted"
    assert advisory["framework_id"] == "ark_progress_first"
    assert advisory["source_contract_ref"] == (
        "med_autoscience.progress_first_external_learning_contract."
        "build_ark_progress_first_learning_contract"
    )
    assert advisory["refs_only"] is True
    assert advisory["body_included"] is False
    assert advisory["advisory_only"] is True
    assert advisory["nonblocking"] is True
    assert advisory["mainline_waits_for_worker"] is False
    assert advisory["can_block_current_owner_action"] is False
    assert advisory["allowed_writes"] == []
    assert FORBIDDEN_TRUTH_WRITES <= set(advisory["forbidden_writes"])
    assert advisory["current_owner_action"] == {
        "action_type": "run_gate_clearing_batch",
        "action_id": "dispatch-ark-001",
        "owner": "publication_gate",
        "work_unit_id": "gate-clearing",
        "work_unit_fingerprint": None,
        "dispatch_path": "artifacts/supervision/current.json",
    }

    assert {
        "micro_canary_ref",
        "human_decision_request_ref",
        "executor_real_run_closeout_ref",
        "citation_lifecycle_queue_ref",
        "semantic_no_progress_evidence_ref",
    } <= set(advisory)
    assert advisory["candidate_ref_families"] == [
        "micro_canary_ref",
        "human_decision_request_ref",
        "executor_real_run_closeout_ref",
        "citation_lifecycle_queue_ref",
        "semantic_no_progress_evidence_ref",
    ]
    assert advisory["micro_canary_ref"] == "external-learning:ark_progress_first:dispatch-ark-001:micro_canary"
    assert advisory["human_decision_request_ref"] == (
        "external-learning:ark_progress_first:dispatch-ark-001:human_decision_request"
    )
    assert advisory["executor_real_run_closeout_ref"] == (
        "external-learning:ark_progress_first:dispatch-ark-001:executor_real_run_closeout"
    )
    assert advisory["citation_lifecycle_queue_ref"] == (
        "external-learning:ark_progress_first:dispatch-ark-001:citation_lifecycle_queue"
    )
    assert advisory["semantic_no_progress_evidence_ref"] == (
        "external-learning:ark_progress_first:dispatch-ark-001:semantic_no_progress_evidence"
    )


def test_autosci_source_experiment_advisory_emits_required_refs_only_candidate_lists() -> None:
    module = importlib.import_module("med_autoscience.external_learning_progress_workers")

    advisory = module.build_autosci_source_experiment_advisory(
        {
            "action_type": "unit_harmonized_external_validation_rerun",
            "source_action": {"action_id": "dispatch-autosci-source"},
            "owner_route": {
                "owner": "source_truth",
                "unit_id": "external-validation",
                "work_unit_fingerprint": "fp-autosci",
            },
            "refs": {"dispatch_path": "artifacts/supervision/autosci.json"},
        }
    )

    assert advisory["surface_kind"] == "mas_autosci_source_experiment_advisory"
    assert advisory["schema_version"] == 1
    assert advisory["status"] == "candidate_refs_emitted"
    assert advisory["framework_id"] == "autosci_omegawiki"
    assert advisory["source_projection_ref"] == (
        "med_autoscience.autosci_learning_projection.build_autosci_learning_projection"
    )
    assert advisory["refs_only"] is True
    assert advisory["body_included"] is False
    assert advisory["advisory_only"] is True
    assert advisory["nonblocking"] is True
    assert advisory["mainline_waits_for_worker"] is False
    assert advisory["can_block_current_owner_action"] is False
    assert advisory["allowed_writes"] == []
    assert FORBIDDEN_TRUTH_WRITES <= set(advisory["forbidden_writes"])
    assert advisory["current_owner_action"] == {
        "action_type": "unit_harmonized_external_validation_rerun",
        "action_id": "dispatch-autosci-source",
        "owner": "source_truth",
        "work_unit_id": "external-validation",
        "work_unit_fingerprint": "fp-autosci",
        "dispatch_path": "artifacts/supervision/autosci.json",
    }

    assert advisory["candidate_ref_families"] == [
        "source_candidate_proposal_refs",
        "source_ingest_authorization_gap_refs",
        "experiment_lifecycle_receipt_refs",
        "negative_route_memory_refs",
        "artifact_render_qa_refs",
    ]
    for family in advisory["candidate_ref_families"]:
        refs = advisory[family]
        assert len(refs) == 1
        assert refs[0].startswith("external-learning:autosci_omegawiki:dispatch-autosci-source:")
    assert advisory["source_candidate_proposal_refs"] == [
        "external-learning:autosci_omegawiki:dispatch-autosci-source:source_candidate_proposal"
    ]
    assert advisory["source_ingest_authorization_gap_refs"] == [
        "external-learning:autosci_omegawiki:dispatch-autosci-source:source_ingest_authorization_gap"
    ]
    assert advisory["experiment_lifecycle_receipt_refs"] == [
        "external-learning:autosci_omegawiki:dispatch-autosci-source:experiment_lifecycle_receipt"
    ]
    assert advisory["negative_route_memory_refs"] == [
        "external-learning:autosci_omegawiki:dispatch-autosci-source:negative_route_memory"
    ]
    assert advisory["artifact_render_qa_refs"] == [
        "external-learning:autosci_omegawiki:dispatch-autosci-source:artifact_render_qa"
    ]


def test_external_learning_progress_workers_fail_open_without_dispatch() -> None:
    module = importlib.import_module("med_autoscience.external_learning_progress_workers")

    ark = module.build_ark_progress_worker_advisory(None)
    autosci = module.build_autosci_source_experiment_advisory(None)

    assert ark["status"] == "candidate_refs_emitted"
    assert autosci["status"] == "candidate_refs_emitted"
    assert ark["fail_open"] is True
    assert autosci["fail_open"] is True
    assert ark["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert autosci["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert ark["current_owner_action"]["action_type"] is None
    assert autosci["current_owner_action"]["action_id"] is None
    assert ark["can_block_current_owner_action"] is False
    assert autosci["can_block_current_owner_action"] is False


def test_external_learning_progress_workers_preserve_authority_boundary() -> None:
    module = importlib.import_module("med_autoscience.external_learning_progress_workers")

    advisories = [
        module.build_ark_progress_worker_advisory({"action_id": "dispatch-authority"}),
        module.build_autosci_source_experiment_advisory({"action_id": "dispatch-authority"}),
    ]

    for advisory in advisories:
        boundary = advisory["authority_boundary"]
        assert boundary["surface_role"] == "refs_only_progress_worker_candidate"
        assert boundary["can_write_domain_truth"] is False
        assert boundary["can_write_publication_eval"] is False
        assert boundary["can_write_controller_decisions"] is False
        assert boundary["can_write_paper_or_package"] is False
        assert boundary["can_write_memory_body"] is False
        assert boundary["can_authorize_owner_action"] is False
        assert boundary["can_authorize_source_readiness"] is False
        assert boundary["can_authorize_artifact_mutation"] is False
        assert boundary["can_authorize_quality_verdict"] is False
        assert boundary["can_authorize_publication_readiness"] is False
        assert boundary["can_authorize_submission_readiness"] is False
        assert boundary["can_close_stage"] is False

        readiness = advisory["readiness_authorization"]
        assert readiness == {
            "may_authorize_publication_readiness": False,
            "may_authorize_source_readiness": False,
            "may_authorize_artifact_readiness": False,
            "may_authorize_artifact_mutation": False,
            "may_authorize_quality_verdict": False,
            "may_authorize_submission_readiness": False,
        }


def test_external_learning_progress_worker_candidates_do_not_write_mas_truth(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_progress_workers")
    dispatch = {
        "action_type": "run_gate_clearing_batch",
        "action_id": "dispatch-no-writes",
        "study_root": str(tmp_path),
    }

    ark = module.build_ark_progress_worker_advisory(dispatch)
    autosci = module.build_autosci_source_experiment_advisory(dispatch)

    assert ark["written_refs"] == []
    assert autosci["written_refs"] == []
    assert not (tmp_path / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (tmp_path / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (tmp_path / "paper").exists()
    assert not (tmp_path / "manuscript").exists()


def test_external_learning_adoption_closure_names_ark_autosci_worker_candidates() -> None:
    module = importlib.import_module("med_autoscience.external_learning_adoption_closure")

    closure = module.build_external_learning_adoption_closure()
    frameworks = {item["framework_id"]: item for item in closure["frameworks"]}

    ark = frameworks["ark_progress_first"]
    autosci = frameworks["autosci_omegawiki"]
    assert ark["closure_status"] == "sidecar_or_worker_landed"
    assert autosci["closure_status"] == "sidecar_or_worker_landed"
    assert (
        "med_autoscience.external_learning_progress_workers."
        "build_ark_progress_worker_advisory"
    ) in ark["source_refs"]
    assert (
        "med_autoscience.external_learning_progress_workers."
        "build_autosci_source_experiment_advisory"
    ) in autosci["source_refs"]
    assert "refs-only advisory worker" in ark["worker_or_executor_landing"]
    assert "refs-only source/experiment advisory worker" in autosci["worker_or_executor_landing"]
