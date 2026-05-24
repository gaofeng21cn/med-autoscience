from __future__ import annotations

import importlib

from tests.test_literature_provider_runtime import _provider_backed_intake_payload


def test_provider_backed_semantic_scholar_contract_is_fail_closed() -> None:
    provider_runtime = importlib.import_module(
        "med_autoscience.controllers.literature_provider_runtime"
    )
    baseline = provider_runtime.build_literature_provider_runtime_projection(
        _provider_backed_intake_payload()
    )

    assert baseline["status"] == "ready"
    assert baseline["literature_intelligence_payload"]["journal_neighbor_refs"] == [
        "semantic_scholar:SEMANTIC123"
    ]
    assert baseline["provider_operations"]["credential_status"]["semantic_scholar"] == {
        "status": "ready",
        "ready": True,
        "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY",
    }
    assert baseline["provider_operations"]["provider_response_ledger_refs"][-1] == (
        "ops/provider_responses/semantic-scholar-2026-05-03.json"
    )
    assert baseline["provider_operations"]["provider_query_fingerprints"][
        "semantic_scholar"
    ].startswith("sha256:")

    provider_payloads = list(_provider_backed_intake_payload()["provider_payloads"])  # type: ignore[index]
    semantic_scholar = dict(provider_payloads[2])  # type: ignore[arg-type]
    semantic_scholar["results"] = [
        {
            "title": "Neighboring clinical endocrinology paper",
            "category": "journal_neighbor_refs",
            "score": 0.91,
            "score_source_ref": "semantic-scholar:query-run-2026-05-03",
            "citation_ledger_ref": "paper/evidence_ledger.json#semantic-SEMANTIC123",
        }
    ]
    provider_payloads[2] = semantic_scholar
    payload = _provider_backed_intake_payload()
    payload["provider_payloads"] = provider_payloads

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_journal_neighbor_refs"

    cases = [
        ("credential_status", {"status": "missing"}, "missing_credential_semantic_scholar"),
        (
            "rate_limit_status",
            {
                "status": "rate_limited",
                "remaining": 0,
                "reset_at": "2026-05-03T09:15:00Z",
                "backoff": {"policy": "exponential", "retry_after_seconds": 900},
            },
            "rate_limited_semantic_scholar",
        ),
        ("provider_response_ledger_refs", [], "missing_provider_response_ledger_semantic_scholar"),
    ]
    for key, value, missing_reason in cases:
        provider_payloads = list(_provider_backed_intake_payload()["provider_payloads"])  # type: ignore[index]
        semantic_scholar = dict(provider_payloads[2])  # type: ignore[arg-type]
        semantic_scholar[key] = value
        provider_payloads[2] = semantic_scholar
        payload = _provider_backed_intake_payload()
        payload["provider_payloads"] = provider_payloads

        projection = provider_runtime.build_literature_provider_runtime_projection(payload)

        assert projection["status"] == "blocked"
        assert projection["missing_reason"] == missing_reason

    provider_payloads = list(_provider_backed_intake_payload()["provider_payloads"])  # type: ignore[index]
    semantic_scholar = dict(provider_payloads[2])  # type: ignore[arg-type]
    semantic_scholar["query"] = "changed semantic scholar query"
    provider_payloads[2] = semantic_scholar
    payload = _provider_backed_intake_payload()
    payload["provider_payloads"] = provider_payloads
    payload["expected_provider_query_fingerprints"] = baseline["provider_operations"][
        "provider_query_fingerprints"
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "query_fingerprint_drift_semantic_scholar"

    provider_payloads = list(_provider_backed_intake_payload()["provider_payloads"])  # type: ignore[index]
    semantic_scholar = dict(provider_payloads[2])  # type: ignore[arg-type]
    result = dict(semantic_scholar["results"][0])  # type: ignore[index]
    result.pop("citation_ledger_ref")
    semantic_scholar["results"] = [result]
    provider_payloads[2] = semantic_scholar
    payload = _provider_backed_intake_payload()
    payload["provider_payloads"] = provider_payloads

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_provider_citation_ledger_refs_semantic_scholar"
    assert projection["provider_health"]["citation_ledger"]["missing_providers"] == [
        "semantic_scholar"
    ]

    payload = _provider_backed_intake_payload()
    payload["screening_decisions"] = [
        {"ref": "semantic_scholar:SEMANTIC123", "decision": "include", "reason": ""},
    ]

    projection = provider_runtime.build_literature_provider_runtime_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["missing_reason"] == "missing_screening_decision_reason"
    assert projection["provider_health"]["screening_reasons"]["missing_refs"] == [
        "semantic_scholar:SEMANTIC123"
    ]
