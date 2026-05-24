from __future__ import annotations

import json

from tests.product_entry_cases.cockpit_status_and_entry_status_focus_cases.test_medical_paper_readiness import (
    _base_progress_payload,
    _ready_doctor_report,
    _ready_mainline_status,
    _ready_supervision,
    make_profile,
    write_study,
)


def _provider_payload(*, query: str = "diabetes mortality prediction") -> dict[str, object]:
    return {
        "search_strategy": {
            "query": query,
            "mesh_terms": ["Diabetes Mellitus"],
            "keywords": ["mortality", "risk prediction", "diabetes"],
        },
        "study_rationale": "A transportable mortality risk model addresses a clinically actionable prognostic gap.",
        "search_date": "2026-05-04",
        "why_worth_doing": "Guideline-bound evidence and recent neighboring papers support the study question.",
        "providers": [
            {
                "provider_name": "pubmed",
                "query": query,
                "retrieved_at": "2026-05-04T01:00:00+08:00",
                "source_refs": ["pubmed:query:001"],
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:PUBMED_API_KEY"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 8,
                    "reset_at": "2026-05-04T02:00:00+08:00",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-04T01:05:00+08:00",
                    "expires_at": "2026-05-05T01:05:00+08:00",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/pubmed-2026-05-04.json"],
                "items": [
                    {
                        "category": "anchor_papers",
                        "ref": "pmid:1",
                        "citation_ledger_ref": "paper/citation_ledger.json#pmid-1",
                    },
                    {
                        "category": "guidelines",
                        "ref": "guideline:tripod-ai",
                        "citation_ledger_ref": "paper/citation_ledger.json#tripod-ai",
                    },
                ],
            },
            {
                "provider_name": "crossref",
                "query": query,
                "retrieved_at": "2026-05-04T01:01:00+08:00",
                "source_refs": ["crossref:query:001"],
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:CROSSREF_MAILTO"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 42,
                    "reset_at": "2026-05-04T02:00:00+08:00",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-04T01:05:00+08:00",
                    "expires_at": "2026-05-05T01:05:00+08:00",
                },
                "provider_response_ledger_refs": ["ops/provider_responses/crossref-2026-05-04.json"],
                "items": [
                    {
                        "category": "systematic_reviews",
                        "ref": "doi:10.1000/review",
                        "citation_ledger_ref": "paper/citation_ledger.json#systematic-review",
                    },
                ],
            },
            {
                "provider_name": "semantic_scholar",
                "query": query,
                "retrieved_at": "2026-05-04T01:02:00+08:00",
                "source_refs": ["semantic-scholar:query:001"],
                "response_status": "ok",
                "credential_status": {"status": "ready", "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY"},
                "rate_limit_status": {
                    "status": "ok",
                    "remaining": 12,
                    "reset_at": "2026-05-04T02:00:00+08:00",
                    "backoff": {"policy": "exponential", "retry_after_seconds": 0},
                },
                "cache_freshness": {
                    "status": "fresh",
                    "checked_at": "2026-05-04T01:05:00+08:00",
                    "expires_at": "2026-05-05T01:05:00+08:00",
                },
                "provider_response_ledger_refs": [
                    "ops/provider_responses/semantic-scholar-2026-05-04.json"
                ],
                "items": [
                    {
                        "category": "journal_neighbor_refs",
                        "ref": "semantic_scholar:neighbor",
                        "score": 0.91,
                        "score_source_ref": "ops/literature_scores/neighbor.json",
                        "citation_ledger_ref": "paper/citation_ledger.json#journal-neighbor",
                    },
                ],
            }
        ],
        "screening_decisions": [{"decision": "include", "reason": "same endpoint"}],
        "citation_ledger_refs": [
            "paper/citation_ledger.json#pmid-1",
            "paper/citation_ledger.json#tripod-ai",
            "paper/citation_ledger.json#systematic-review",
            "paper/citation_ledger.json#journal-neighbor",
        ],
    }


def _v2_workflow_readiness() -> dict[str, object]:
    return {
        "surface": "medical_paper_readiness",
        "overall_status": "blocked",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 0,
        "required_count": 6,
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_provider_runtime",
            "summary": "补齐 provider-backed 文献摄取。",
        },
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "label": "Literature Provider Runtime",
                "status": "missing",
                "missing_reason": "missing_provider_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "route_decision_orchestrator",
                "label": "Route Decision Orchestrator",
                "status": "missing",
                "missing_reason": "missing_controller_decision_projection",
                "required_for_ready": True,
            },
            {
                "surface_key": "statistical_discipline_operations",
                "label": "Statistical Discipline Operations",
                "status": "blocked",
                "missing_reason": "open_precision_and_validation_blockers",
                "required_for_ready": True,
            },
            {
                "surface_key": "revision_rebuttal_loop",
                "label": "Revision / Rebuttal Loop",
                "status": "blocked",
                "missing_reason": "missing_reviewer_comment_intake",
                "required_for_ready": True,
            },
            {
                "surface_key": "authoring_runtime_authorization",
                "label": "Authoring Runtime Authorization",
                "status": "missing",
                "missing_reason": "missing_ai_reviewer_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "real_workspace_soak_monitor",
                "label": "Real Workspace Soak Monitor",
                "status": "partial",
                "missing_reason": "missing_required_archetype",
                "required_for_ready": True,
            },
        ],
    }


def test_workspace_cockpit_exposes_long_horizon_paper_operations_action_cards(
    monkeypatch,
    tmp_path,
) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = {
        "surface": "medical_paper_readiness",
        "overall_status": "blocked",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ready_count": 0,
        "required_count": 7,
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_provider_runtime",
            "summary": "补齐 provider-backed 文献摄取。",
        },
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "label": "Literature Provider Runtime",
                "status": "missing",
                "missing_reason": "missing_provider_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "revision_rebuttal_loop",
                "label": "Revision / Rebuttal Loop",
                "status": "blocked",
                "missing_reason": "missing_reviewer_comment_intake",
                "required_for_ready": True,
            },
            {
                "surface_key": "real_workspace_soak_monitor",
                "label": "Real Workspace Soak Monitor",
                "status": "partial",
                "missing_reason": "missing_required_archetype",
                "required_for_ready": True,
            },
        ],
    }

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    cards = payload["studies"][0]["medical_paper_readiness"]["action_cards"]
    v4_operations = payload["studies"][0]["medical_paper_v4_operations"]

    assert [card["action_id"] for card in cards] == ["run_provider_literature_scout"]
    assert [card["label"] for card in cards] == ["联网补文献"]
    assert all(card["authority"] == "observability_projection_only" for card in cards)
    assert all(card["quality_claim_authorized"] is False for card in cards)
    command = cards[0]["guarded_operator_command"]
    assert command["surface"] == "medical_paper_v3_guarded_operator_command"
    assert command["action_id"] == "run_provider_literature_scout"
    assert command["surface_key"] == "literature_provider_runtime"
    assert command["entrypoint"] == "product_entry.dispatch_guarded_medical_paper_operator_action"
    assert command["guard"] == "existing_product_entry_controller_guard"
    assert command["requires"] == ["profile_ref", "study_id", "operator_payload"]
    assert command["status"] == "guarded_pending"
    assert command["action_instance_id"].startswith("guarded-operator-action::")
    assert command["idempotency_key"].startswith("guarded-operator-action::sha256:")
    assert command["input_digest"].startswith("sha256:")
    action_result = cards[0]["action_result"]
    assert action_result == {
        "status": "guarded_pending",
        "durable_ref": None,
        "missing_reason": "missing_provider_provenance",
        "next_action": "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
        "authority_contract": cards[0]["authority_contract"],
        "action_instance_id": command["action_instance_id"],
        "idempotency_key": command["idempotency_key"],
        "input_digest": command["input_digest"],
    }
    assert cards[0]["authority_contract"]["can_mutate_runtime"] is False
    assert cards[0]["authority_contract"]["can_authorize_quality"] is False
    assert v4_operations["surface"] == "medical_paper_v4_operations_dashboard"
    assert v4_operations["overall_status"] == "blocked"
    assert v4_operations["health"]["provider_health"]["missing_reason"] == "missing_provider_provenance"
    assert v4_operations["health"]["operator_action_health"]["pending_action_count"] == 1
    assert v4_operations["health"]["operator_action_health"]["action_ids"] == [
        "run_provider_literature_scout"
    ]
    assert v4_operations["health"]["soak_monitor_health"]["status"] == "partial"
    assert v4_operations["authority_contract"]["can_authorize_quality"] is False


def test_product_entry_status_promotes_v2_action_cards_to_workflow_steps(
    monkeypatch,
    tmp_path,
) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _v2_workflow_readiness()

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    payload = module.build_product_entry_status(profile=profile, profile_ref=profile_ref)
    workflow_steps = payload["phase2_user_product_loop"]["workflow_steps"]

    assert [step["step_id"] for step in workflow_steps] == [
        "run_provider_literature_scout",
        "materialize_route_decision",
        "resolve_statistical_blockers",
        "start_revision_rebuttal_loop",
        "authorize_manuscript_drafting",
        "run_real_workspace_soak_monitor",
    ]
    assert [step["title"] for step in workflow_steps] == [
        "联网补文献",
        "写入路线裁决",
        "处理统计 blocker",
        "启动返修",
        "授权写作",
        "运行真实 soak",
    ]
    assert all(step["authority"] == "observability_projection_only" for step in workflow_steps)
    assert all(step["quality_claim_authorized"] is False for step in workflow_steps)
    assert all(step["surface_kind"] == "medical_paper_readiness_action_card" for step in workflow_steps)
    assert all(step["authority_contract"]["guard"] == "existing_product_entry_controller_guard" for step in workflow_steps)
    assert workflow_steps[0]["guarded_operator_command"]["status"] == "guarded_pending"
    assert workflow_steps[0]["action_result"]["status"] == "guarded_pending"
    assert workflow_steps[0]["command"].endswith(
        "workspace cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["operator_brief"]["recommended_step_id"] == "run_provider_literature_scout"


def test_workspace_cockpit_markdown_renders_v2_action_card_status_and_missing_reason(
    monkeypatch,
    tmp_path,
) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    readiness = _v2_workflow_readiness()

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_doctor_report())
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: _ready_supervision())
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", _ready_mainline_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {**_base_progress_payload(study_id="001-risk"), "medical_paper_readiness": readiness},
    )

    markdown = module.render_workspace_cockpit_markdown(
        module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    )

    assert markdown.strip()


def test_guarded_operator_action_dispatch_fails_closed_without_payload(tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    study_root = tmp_path / "studies" / "001-risk"

    result = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_operator_payload"
    assert result["durable_ref"] is None
    assert result["replay_ref"].endswith(".json")
    assert result["blocked_retry_reason"] == "missing_operator_payload"
    assert result["retry_governance"]["retryable"] is False
    assert result["retry_governance"]["blocked_retry_reason"] == "missing_operator_payload"
    assert result["authority_contract"]["guard"] == "existing_product_entry_controller_guard"
    assert result["authority_contract"]["can_mutate_runtime"] is False
    assert result["authority_contract"]["can_authorize_quality"] is False
    assert result["quality_claim_authorized"] is False


def test_guarded_operator_action_replays_duplicate_submit_without_rematerializing(tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    study_root = tmp_path / "studies" / "001-risk"
    payload = _provider_payload()

    first = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=payload,
    )
    durable_path = study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json"
    materialized = json.loads(durable_path.read_text(encoding="utf-8"))
    materialized["duplicate_replay_sentinel"] = "preserved"
    durable_path.write_text(json.dumps(materialized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    replayed = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=payload,
    )

    assert first["status"] == "ready"
    assert first["replay_ref"].startswith("artifacts/medical_paper/actions/ledger/")
    ledger = json.loads((study_root / first["replay_ref"]).read_text(encoding="utf-8"))
    assert ledger["surface"] == "medical_paper_v5_guarded_operator_replay_ledger"
    assert ledger["legacy_surface"] == "medical_paper_v3_guarded_operator_action_ledger"
    assert ledger["action_timeline"][0]["event"] == "new_result"
    assert ledger["input_digest_history"] == [first["input_digest"]]
    assert ledger["authority_contract_snapshot"]["can_write_runtime_owned_artifacts"] is False
    assert ledger["retry_governance"]["retryable"] is True
    assert replayed["status"] == "ready"
    assert replayed["duplicate_submit_detected"] is True
    assert replayed["replay"] is True
    assert replayed["reconciliation"] == "result_replayed"
    assert replayed["replay_ref"] == first["replay_ref"]
    assert replayed["retry_governance"]["duplicate_submit_detected"] is True
    assert replayed["idempotency_key"] == first["idempotency_key"]
    assert replayed["input_digest"] == first["input_digest"]
    assert replayed["durable_ref"] == first["durable_ref"]
    assert "artifacts/medical_paper/actions/" in replayed["action_result_ref"]
    persisted = json.loads(durable_path.read_text(encoding="utf-8"))
    assert persisted["duplicate_replay_sentinel"] == "preserved"


def test_guarded_operator_action_blocks_payload_drift_for_same_idempotency_key(tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    study_root = tmp_path / "studies" / "001-risk"

    first = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=_provider_payload(query="diabetes mortality prediction"),
        action_instance_id="operator-session-001",
        idempotency_key="operator-session-001-key",
    )
    drift = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=_provider_payload(query="changed query"),
        action_instance_id="operator-session-001",
        idempotency_key="operator-session-001-key",
    )

    assert first["status"] == "ready"
    assert drift["status"] == "blocked"
    assert drift["missing_reason"] == "input_digest_drift"
    assert drift["expected_input_digest"] == first["input_digest"]
    assert drift["observed_input_digest"] != first["input_digest"]
    assert drift["durable_ref"] is None
    assert drift["replay_ref"] == first["replay_ref"]
    assert drift["retry_governance"]["retryable"] is False
    assert drift["retry_governance"]["reconciliation"] == "input_digest_drift"
    durable_path = study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json"
    persisted = json.loads(durable_path.read_text(encoding="utf-8"))
    assert persisted["query"] == "diabetes mortality prediction"


def test_guarded_operator_action_reconciles_missing_result_artifact_from_ledger(tmp_path) -> None:
    import importlib

    module = importlib.import_module("med_autoscience.controllers.product_entry")
    study_root = tmp_path / "studies" / "001-risk"
    payload = _provider_payload()

    first = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=payload,
    )
    result_path = first["action_result_ref"]
    (study_root / result_path).unlink()

    replayed = module.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id="run_provider_literature_scout",
        surface_key="literature_provider_runtime",
        operator_payload=payload,
    )

    assert replayed["status"] == "ready"
    assert replayed["duplicate_submit_detected"] is True
    assert replayed["reconciliation"] == "result_recreated_from_ledger"
    assert replayed["replay_ref"] == first["replay_ref"]
    assert replayed["retry_governance"]["reconciliation"] == "result_recreated_from_ledger"
    assert (study_root / result_path).is_file()
