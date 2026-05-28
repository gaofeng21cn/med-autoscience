from __future__ import annotations

import importlib


def test_autosci_learning_projection_is_clean_room_contract_first_intake() -> None:
    module = importlib.import_module("med_autoscience.autosci_learning_projection")

    projection = module.build_autosci_learning_projection()

    assert projection["surface_kind"] == "mas_autosci_learning_projection"
    assert projection["version"] == "mas-autosci-learning-projection.v1"
    assert projection["source_snapshot"] == {
        "source_project": "AutoSci/OmegaWiki",
        "repository": "https://github.com/skyllwt/AutoSci",
        "observed_head": "d89cc72a884a2d091b6fac5719f30b4c64d2c6bd",
        "intake_doc_ref": "docs/references/mainline/autosci_learning_intake.md",
        "dependency_introduced": False,
    }

    absorbed = {pattern["pattern_id"]: pattern for pattern in projection["absorbed_patterns"]}
    assert set(absorbed) == {
        "typed_research_knowledge_graph",
        "proposal_action_source_discovery_split",
        "negative_research_memory",
        "experiment_deploy_collect_eval_lifecycle",
        "independent_reviewer_verdict_mapping",
        "source_dag_render_qa_artifact_projection",
    }
    assert absorbed["typed_research_knowledge_graph"]["classification"] == "adopt_contract"
    assert absorbed["experiment_deploy_collect_eval_lifecycle"]["classification"] == "adopt_template"
    assert absorbed["source_dag_render_qa_artifact_projection"]["owner_surface"] == (
        "publication_artifact"
    )

    graph = projection["knowledge_graph_contract"]
    assert graph["edge_policy"]["semantic_edges_separate_from_bibliographic_citations"] is True
    assert graph["edge_policy"]["reverse_ref_or_terminal_exception_required"] is True
    assert graph["write_policy"]["partial_authoritative_ingest_forbidden"] is True
    assert graph["entity_shape_policy"]["copy_autosci_taxonomy"] is False

    assert projection["source_discovery_contract"] == {
        "surface_kind": "mas_source_discovery_proposal_action_split",
        "proposal_surface": "source_candidate_shortlist_ref",
        "action_surface": "mas_owner_authorized_ingest_or_source_repair_route",
        "candidate_may_write_mas_truth": False,
        "recommendation_may_authorize_source_readiness": False,
        "auto_ingest_requires_explicit_mode_and_high_confidence": True,
        "degraded_provider_signal_requires_caveat_or_typed_blocker": True,
    }
    assert projection["reviewer_os_contract"]["separate_invocation_required"] is True
    assert projection["reviewer_os_contract"]["self_review_closes_quality_gate"] is False
    assert projection["artifact_projection_contract"]["render_success_is_publication_ready"] is False


def test_autosci_learning_projection_rejects_runtime_and_prompt_only_authority() -> None:
    module = importlib.import_module("med_autoscience.autosci_learning_projection")

    projection = module.build_autosci_learning_projection()

    assert set(projection["rejected_patterns"]) >= {
        "external_claude_slash_skills_as_runtime",
        "ssh_rsync_screen_remote_gpu_runner",
        "prompt_only_permission_as_authority",
        "partial_authoritative_ingest_success",
        "autosci_entity_taxonomy_as_mas_taxonomy",
        "self_review_as_independent_quality_gate",
    }
    assert {pattern["pattern_id"] for pattern in projection["watch_only_patterns"]} == {
        "prompt_level_writer_policy",
        "paper_copilot_cs_venue_ranking",
        "github_actions_daily_scheduler",
    }

    boundary = projection["authority_boundary"]
    assert boundary["source_project_role"] == "external_pattern_source_only"
    assert boundary["can_write_domain_truth"] is False
    assert boundary["can_write_evidence_ledger"] is False
    assert boundary["can_write_review_ledger"] is False
    assert boundary["can_authorize_source_readiness"] is False
    assert boundary["can_authorize_publication_quality"] is False
    assert boundary["can_authorize_artifact_authority"] is False
