from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers import ai_reviewer_calibration, literature_provider_runtime


SCHEMA_VERSION = 1
SURFACE = "outcome_provider_ops_projection"
LANE_ID = "L3_outcome_calibration_and_provider_ops"
REQUIRED_JOURNAL_FIXTURE_COVERAGE = (
    "cover_letter",
    "submission_checklist",
    "supplement_naming",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _text(value: object) -> str:
    return str(value or "").strip()


def _dict_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in _sequence(value) if isinstance(item, Mapping)]


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_projection_only",
        "read_model_only": True,
        "observability_only": True,
        "can_authorize_quality": False,
        "can_authorize_drafting": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "can_bypass_ai_reviewer": False,
        "can_bypass_publication_gate": False,
        "required_authority_surfaces": [
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
            "AI reviewer publication gate",
        ],
    }


def _outcome_calibration_projection(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    learning = ai_reviewer_calibration.build_ai_reviewer_calibration_learning_read_model(
        payload or {}
    )
    regression = dict(_mapping(learning.get("outcome_learning_regression")))
    return {
        "learning_surface": learning["surface"],
        "regression_surface": regression.get("surface"),
        "status": regression.get("status") or "blocked",
        "planning_mode": regression.get("planning_mode"),
        "supported_outcomes": list(learning.get("supported_outcomes") or []),
        "outcome_counts": dict(_mapping(learning.get("outcome_counts"))),
        "failure_mode_counts": dict(_mapping(learning.get("failure_mode_counts"))),
        "required_failure_modes": list(learning.get("required_failure_modes") or []),
        "missing_required_failure_modes": list(
            regression.get("missing_required_failure_modes") or []
        ),
        "required_calibration_refs": list(learning.get("required_calibration_refs") or []),
        "failure_mode_projection": list(learning.get("failure_mode_projection") or []),
        "authority_contract": dict(_mapping(learning.get("authority_contract"))),
    }


def _provider_ops_projection(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    provider_projection = literature_provider_runtime.build_literature_provider_runtime_projection(
        payload or {}
    )
    provider_health = dict(_mapping(provider_projection.get("provider_health")))
    diagnostics = _dict_list(provider_health.get("diagnostics"))
    citation_freshness = dict(_mapping(provider_health.get("citation_freshness")))
    citation_ledger = dict(_mapping(provider_health.get("citation_ledger")))
    return {
        "runtime_surface": provider_projection["surface"],
        "health_surface": provider_health.get("contract"),
        "runtime_status": provider_projection.get("status"),
        "provider_health_status": provider_health.get("status"),
        "missing_reason": provider_projection.get("missing_reason"),
        "providers": list(provider_projection.get("providers") or []),
        "provider_response_ledger_refs": list(
            provider_projection.get("provider_response_ledger_refs") or []
        ),
        "provider_health_checks": list(provider_health.get("checks") or []),
        "partial_outage_providers": [
            _text(item.get("provider_name"))
            for item in diagnostics
            if item.get("category") == "provider_partial_outage" and _text(item.get("provider_name"))
        ],
        "citation_ledger_drift": {
            "status": "drifted"
            if citation_freshness.get("stale") is True
            or bool(citation_ledger.get("missing_providers"))
            else "stable",
            "stale_refs": list(citation_freshness.get("stale_refs") or []),
            "missing_providers": list(citation_ledger.get("missing_providers") or []),
        },
        "query_fingerprint_drift": dict(_mapping(provider_health.get("query_fingerprint_drift"))),
        "cache_freshness": dict(_mapping(provider_projection.get("cache_freshness"))),
        "diagnostics": diagnostics,
        "authority_contract": dict(_mapping(provider_health.get("authority_contract"))),
    }


def _journal_family_fixture_matrix(fixtures: object) -> dict[str, Any]:
    entries = _dict_list(fixtures)
    normalized_entries: list[dict[str, Any]] = []
    missing_coverage: dict[str, list[str]] = {}
    diagnostics: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        family = _text(entry.get("journal_family")) or f"journal_family:{index}"
        coverage = _mapping(entry.get("coverage"))
        missing = [
            key for key in REQUIRED_JOURNAL_FIXTURE_COVERAGE if coverage.get(key) is not True
        ]
        if missing:
            missing_coverage[family] = missing
            for key in missing:
                diagnostics.append(
                    {
                        "reason_code": f"journal_family_fixture_missing_{key}",
                        "severity": "blocking",
                        "category": "journal_family_fixture_matrix",
                        "journal_family": family,
                    }
                )
        normalized_entries.append(
            {
                "journal_family": family,
                "fixture_ref": _text(entry.get("fixture_ref")),
                "profile_ref": _text(entry.get("profile_ref")),
                "coverage": {
                    key: coverage.get(key) is True
                    for key in REQUIRED_JOURNAL_FIXTURE_COVERAGE
                },
            }
        )
    return {
        "surface": "journal_family_fixture_matrix",
        "status": "ready" if entries and not missing_coverage else "blocked",
        "required_coverage": list(REQUIRED_JOURNAL_FIXTURE_COVERAGE),
        "covered_families": sorted(
            entry["journal_family"] for entry in normalized_entries if not missing_coverage.get(entry["journal_family"])
        ),
        "missing_coverage": missing_coverage,
        "fixtures": normalized_entries,
        "diagnostics": diagnostics,
        "authority_contract": _authority_contract(),
    }


def build_outcome_provider_ops_projection(
    *,
    outcome_calibration_payload: Mapping[str, Any] | None = None,
    provider_runtime_payload: Mapping[str, Any] | None = None,
    journal_family_fixture_matrix: object = None,
) -> dict[str, Any]:
    outcome = _outcome_calibration_projection(outcome_calibration_payload)
    provider_ops = _provider_ops_projection(provider_runtime_payload)
    journal_matrix = _journal_family_fixture_matrix(journal_family_fixture_matrix)
    diagnostics = [
        *list(provider_ops.get("diagnostics") or []),
        *list(journal_matrix.get("diagnostics") or []),
    ]
    blocked = (
        outcome["status"] == "blocked"
        or provider_ops["provider_health_status"] == "blocked"
        or journal_matrix["status"] == "blocked"
        or bool(diagnostics)
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "owner": "MedAutoScience Observability OS",
        "authority_mode": "observability_only",
        "observability_only": True,
        "status": "blocked" if blocked else "ready",
        "source_surfaces": [
            outcome["learning_surface"],
            outcome["regression_surface"],
            provider_ops["runtime_surface"],
            provider_ops["health_surface"],
            journal_matrix["surface"],
        ],
        "outcome_calibration": outcome,
        "provider_ops": provider_ops,
        "journal_family_fixture_matrix": journal_matrix,
        "diagnostics": diagnostics,
        "authority_contract": _authority_contract(),
        "quality_claim_authorized": False,
        "submission_ready_authorized": False,
        "finalize_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "can_bypass_ai_reviewer": False,
        "can_bypass_publication_gate": False,
    }
