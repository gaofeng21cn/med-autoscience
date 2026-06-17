from __future__ import annotations

from med_autoscience.controllers.domain_action_request_materializer_parts import currentness_identity
from med_autoscience.runtime_control import owner_route_attempt_protocol


def test_currentness_identity_preserves_non_empty_source_eval_id_across_route_and_transition() -> None:
    route = {
        "publication_eval_id": "publication-eval::route-fallback",
        "source_refs": {
            "source_eval_id": None,
            "publication_eval_ref": {"eval_id": "publication-eval::ref-fallback"},
            "owner_route_currentness_basis": {
                "source_eval_id": None,
                "work_unit_id": "work-unit-a",
            },
        },
        "currentness_contract": {
            "basis": {
                "source_eval_id": None,
                "work_unit_fingerprint": "fingerprint-a",
            },
        },
    }
    transition = {
        "completion_receipt_consumption": {"eval_id": "publication-eval::current"},
        "publication_eval_ref": {"eval_id": "publication-eval::older"},
    }
    basis = currentness_identity.currentness_basis(
        currentness_identity.owner_route_basis(route),
        {"source_eval_id": currentness_identity.source_eval_id_from_domain_transition(transition)},
        {"source_eval_id": None, "runtime_health_epoch": "runtime-a"},
    )

    normalized_route = currentness_identity.with_owner_route_basis(route, basis=basis)
    normalized_request = currentness_identity.with_transition_request_basis(
        {"currentness_basis": {"source_eval_id": None, "truth_epoch": "truth-a"}},
        basis=currentness_identity.owner_route_basis(normalized_route),
    )
    normalized_action = currentness_identity.with_action_handoff_basis(
        {
            "source_eval_id": None,
            "handoff_packet": {
                "source_eval_id": None,
                "owner_route": route,
            },
        },
        basis=basis,
    )

    assert basis == {
        "work_unit_id": "work-unit-a",
        "work_unit_fingerprint": "fingerprint-a",
        "source_eval_id": "publication-eval::current",
        "runtime_health_epoch": "runtime-a",
    }
    assert normalized_route["source_refs"]["source_eval_id"] == "publication-eval::current"
    assert normalized_route["source_refs"]["owner_route_currentness_basis"]["source_eval_id"] == (
        "publication-eval::current"
    )
    assert normalized_route["currentness_contract"]["basis"]["source_eval_id"] == (
        "publication-eval::current"
    )
    assert normalized_request["currentness_basis"]["source_eval_id"] == "publication-eval::current"
    assert normalized_request["currentness_basis"]["truth_epoch"] == "truth-a"
    assert normalized_action["source_eval_id"] == "publication-eval::current"
    assert normalized_action["handoff_packet"]["source_eval_id"] == "publication-eval::current"
    assert normalized_action["owner_route"]["source_refs"]["owner_route_currentness_basis"][
        "source_eval_id"
    ] == "publication-eval::current"
    assert normalized_action["handoff_packet"]["owner_route"]["currentness_contract"]["basis"][
        "source_eval_id"
    ] == "publication-eval::current"


def test_normalize_currentness_sources_is_the_shared_non_empty_merge_contract() -> None:
    normalized = currentness_identity.normalize_currentness_sources(
        {
            "source_eval_id": "publication-eval::old",
            "source_fingerprint": "source-fingerprint::old",
            "work_unit_id": "work-unit-old",
            "work_unit_fingerprint": "fingerprint-old",
            "truth_epoch": "truth-old",
            "runtime_health_epoch": "runtime-old",
            "route_epoch": "route-old",
        },
        {
            "source_eval_id": None,
            "source_fingerprint": "",
            "work_unit_id": "work-unit-current",
            "work_unit_fingerprint": None,
            "truth_epoch": "truth-current",
            "runtime_health_epoch": None,
            "route_epoch": "route-current",
            "private_queue_ref": "must-not-leak",
        },
    )

    assert normalized == {
        "source_eval_id": "publication-eval::old",
        "source_fingerprint": "source-fingerprint::old",
        "work_unit_id": "work-unit-current",
        "work_unit_fingerprint": "fingerprint-old",
        "truth_epoch": "truth-current",
        "runtime_health_epoch": "runtime-old",
        "route_epoch": "route-current",
    }
    assert normalized == owner_route_attempt_protocol.normalize_currentness_sources(
        {
            "source_eval_id": "publication-eval::old",
            "source_fingerprint": "source-fingerprint::old",
            "work_unit_id": "work-unit-old",
            "work_unit_fingerprint": "fingerprint-old",
            "truth_epoch": "truth-old",
            "runtime_health_epoch": "runtime-old",
            "route_epoch": "route-old",
        },
        {
            "source_eval_id": None,
            "source_fingerprint": "",
            "work_unit_id": "work-unit-current",
            "work_unit_fingerprint": None,
            "truth_epoch": "truth-current",
            "runtime_health_epoch": None,
            "route_epoch": "route-current",
            "private_queue_ref": "must-not-leak",
        },
    )


def test_normalize_transition_request_currentness_preserves_existing_non_empty_fields() -> None:
    normalized = currentness_identity.normalize_transition_request_currentness(
        {
            "currentness_basis": {
                "source_eval_id": "publication-eval::request",
                "source_fingerprint": "request-source",
                "work_unit_id": "request-work-unit",
            }
        },
        {
            "source_eval_id": None,
            "source_fingerprint": "source-current",
            "work_unit_id": None,
            "work_unit_fingerprint": "fingerprint-current",
            "route_epoch": "route-current",
        },
    )

    assert normalized["currentness_basis"] == {
        "source_eval_id": "publication-eval::request",
        "source_fingerprint": "source-current",
        "work_unit_id": "request-work-unit",
        "work_unit_fingerprint": "fingerprint-current",
        "route_epoch": "route-current",
    }


def test_currentness_identity_normalizes_request_handoff_and_route_without_none_overwrites() -> None:
    owner_route = {
        "source_refs": {
            "owner_route_currentness_basis": {
                "source_eval_id": "publication-eval::route",
                "work_unit_id": "route-work-unit",
                "work_unit_fingerprint": "route-fingerprint",
                "truth_epoch": "truth-route",
                "runtime_health_epoch": "runtime-route",
            }
        },
        "currentness_contract": {
            "basis": {
                "source_eval_id": None,
                "source_fingerprint": "source-route",
                "work_unit_id": None,
                "route_epoch": "route-old",
            }
        },
    }
    transition_request = {
        "currentness_basis": {
            "source_eval_id": "publication-eval::request",
            "work_unit_id": "request-work-unit",
            "work_unit_fingerprint": "request-fingerprint",
            "truth_epoch": "truth-request",
        }
    }
    action_handoff = {
        "source_eval_id": "publication-eval::action",
        "source_fingerprint": "source-action",
        "work_unit_id": "action-work-unit",
        "work_unit_fingerprint": "action-fingerprint",
        "handoff_packet": {
            "source_eval_id": None,
            "owner_route": owner_route,
        },
    }
    basis = currentness_identity.normalize_currentness_sources(
        currentness_identity.owner_route_basis(owner_route),
        {"source_eval_id": None, "work_unit_id": None, "truth_epoch": "truth-current"},
        currentness_identity.action_basis(action_handoff),
    )

    normalized_route = currentness_identity.normalize_owner_route_currentness(
        owner_route,
        basis,
    )
    normalized_request = currentness_identity.normalize_transition_request_currentness(
        transition_request,
        {"source_eval_id": None, "work_unit_id": None, "runtime_health_epoch": "runtime-current"},
        currentness_identity.owner_route_basis(normalized_route),
    )
    normalized_handoff = currentness_identity.normalize_action_handoff_currentness(
        action_handoff,
        {"source_eval_id": None, "work_unit_id": None},
        currentness_identity.owner_route_basis(normalized_route),
    )

    assert basis == {
        "source_eval_id": "publication-eval::action",
        "source_fingerprint": "source-action",
        "work_unit_id": "action-work-unit",
        "work_unit_fingerprint": "action-fingerprint",
        "truth_epoch": "truth-current",
        "runtime_health_epoch": "runtime-route",
        "route_epoch": "route-old",
    }
    assert normalized_route["source_refs"]["owner_route_currentness_basis"][
        "source_eval_id"
    ] == "publication-eval::action"
    assert normalized_route["currentness_contract"]["basis"]["work_unit_id"] == "action-work-unit"
    assert normalized_request["currentness_basis"] == {
        "source_eval_id": "publication-eval::action",
        "source_fingerprint": "source-action",
        "work_unit_id": "action-work-unit",
        "work_unit_fingerprint": "action-fingerprint",
        "truth_epoch": "truth-current",
        "runtime_health_epoch": "runtime-route",
        "route_epoch": "route-old",
    }
    assert normalized_handoff["source_eval_id"] == "publication-eval::action"
    assert normalized_handoff["work_unit_id"] == "action-work-unit"
    assert normalized_handoff["handoff_packet"]["source_eval_id"] == "publication-eval::action"
    assert normalized_handoff["owner_route"]["currentness_contract"]["basis"][
        "work_unit_fingerprint"
    ] == "action-fingerprint"


def test_currentness_identity_uses_existing_owner_route_protocol_fallbacks() -> None:
    route = {
        "publication_eval_id": "publication-eval::route",
        "source_refs": {
            "source_eval_id": None,
            "owner_route_currentness_basis": {"source_eval_id": None},
            "publication_eval_ref": {"eval_id": "publication-eval::ref"},
        },
        "currentness_contract": {"basis": {"source_eval_id": None}},
    }

    assert currentness_identity.owner_route_basis(route)["source_eval_id"] == "publication-eval::ref"
