from __future__ import annotations

from dataclasses import asdict

import pytest

from med_autoscience.research_integrity import (
    build_reference_verification_attestation,
    build_reference_verification_attestation_dict,
)


def test_reference_authenticity_verifies_cross_provider_identifier_match() -> None:
    attestation = build_reference_verification_attestation(
        {
            "ID": "smith2024",
            "DOI": "https://doi.org/10.1000/ABC",
            "PMID": "12345678",
            "title": "A Mature Classifier Paper",
            "year": "2024",
            "journal": "Medical AI",
        },
        [
            {
                "provider": "crossref",
                "matched_identifiers": {"doi": "10.1000/abc"},
                "metadata": {
                    "title": "A mature classifier paper",
                    "year": 2024,
                    "journal": "Medical AI",
                },
            },
            {
                "provider": "pubmed",
                "matched_identifiers": {"pmid": "12345678"},
                "metadata": {"title": "A Mature Classifier Paper", "publication_year": "2024"},
            },
        ],
    )

    payload = attestation.to_dict()

    assert asdict(attestation) == payload
    assert payload["surface_kind"] == "reference_verification_attestation"
    assert payload["reference_id"] == "smith2024"
    assert payload["status"] == "verified"
    assert payload["source_crosschecks"][0]["provider"] == "crossref"
    assert payload["source_crosschecks"][0]["matched_identifiers"] == ["doi"]
    assert payload["source_crosschecks"][1]["matched_identifiers"] == ["pmid"]
    assert payload["identifier_conflicts"] == []
    assert payload["metadata_mismatches"] == []
    assert payload["retraction_or_update_flags"] == []
    assert payload["authority_boundary"]["can_write_publication_authority"] is False
    assert payload["authority_boundary"]["can_sign_owner_receipt"] is False
    assert payload["authority_boundary"]["can_create_typed_blocker"] is False
    assert payload["authority_boundary"]["can_create_human_gate"] is False
    assert payload["authority_boundary"]["produces_gate_input"] is True
    assert payload["authority_boundary"]["produces_blocker_candidate_evidence"] is True


def test_reference_authenticity_marks_identifier_conflict_as_contradicted() -> None:
    payload = build_reference_verification_attestation_dict(
        {"reference_id": "bad-doi", "doi": "10.1000/source", "title": "Stable title"},
        [
            {
                "provider": "openalex",
                "identifiers": {"doi": "10.1000/other"},
                "metadata": {"title": "Stable title"},
            }
        ],
    )

    assert payload["status"] == "contradicted"
    assert payload["identifier_conflicts"] == [
        {
            "provider": "openalex",
            "identifier": "doi",
            "reference_value": "10.1000/source",
            "evidence_value": "10.1000/other",
        }
    ]


def test_reference_authenticity_marks_metadata_mismatch_and_updates_for_review() -> None:
    payload = build_reference_verification_attestation_dict(
        {"id": "changed-title", "doi": "10.1000/source", "title": "Original title", "year": "2024"},
        [
            {
                "provider": "semantic_scholar",
                "matched_identifiers": {"doi": "10.1000/source", "semantic_scholar_id": "S2-1"},
                "metadata": {"title": "Corrected title", "year": "2024"},
                "retraction_or_update_flags": {"correction": True},
            }
        ],
    )

    assert payload["status"] == "needs_review"
    assert payload["source_crosschecks"][0]["matched_identifiers"] == ["doi"]
    assert payload["metadata_mismatches"] == [
        {
            "provider": "semantic_scholar",
            "field": "title",
            "reference_value": "original title",
            "evidence_value": "corrected title",
        }
    ]
    assert payload["retraction_or_update_flags"] == [
        {"provider": "semantic_scholar", "flag": "correction", "value": True}
    ]


def test_reference_authenticity_prioritizes_retraction_flags() -> None:
    payload = build_reference_verification_attestation_dict(
        {"citation_key": "retracted-ref", "doi": "10.1000/retracted"},
        [
            {
                "provider": "crossmark",
                "matched_identifiers": {"doi": "10.1000/retracted"},
                "retraction_or_update_flags": {"retracted": True},
            },
            {
                "provider": "publisher",
                "matched_identifiers": {"doi": "10.1000/retracted"},
                "update_type": "retraction",
            },
        ],
    )

    assert payload["status"] == "retracted"
    assert payload["retraction_or_update_flags"] == [
        {"provider": "crossmark", "flag": "retracted", "value": True},
        {"provider": "publisher", "flag": "update_type", "value": "retraction"},
    ]


def test_reference_authenticity_ignores_false_string_flags() -> None:
    payload = build_reference_verification_attestation_dict(
        {"id": "not-retracted", "doi": "10.1000/live"},
        [
            {
                "provider": "crossmark",
                "matched_identifiers": {"doi": "10.1000/live"},
                "retraction_or_update_flags": {"retracted": "false", "has_update": "0"},
            }
        ],
    )

    assert payload["status"] == "verified"
    assert payload["retraction_or_update_flags"] == []


def test_reference_authenticity_unresolved_when_evidence_does_not_match_reference() -> None:
    payload = build_reference_verification_attestation_dict(
        {"key": "unmatched-ref", "title": "No identifier"},
        [
            {
                "provider": "publisher",
                "matched_identifiers": {"doi": "10.1000/provider-only"},
                "metadata": {"title": "No identifier"},
            }
        ],
    )

    assert payload["status"] == "unresolved"
    assert payload["source_crosschecks"][0]["status"] == "unmatched"
    assert payload["source_crosschecks"][0]["matched_identifiers"] == []


def test_reference_authenticity_rejects_missing_reference_id_and_unknown_provider() -> None:
    with pytest.raises(ValueError, match="reference_id is required"):
        build_reference_verification_attestation_dict({"doi": "10.1000/no-id"}, [])

    with pytest.raises(ValueError, match="unsupported reference evidence provider"):
        build_reference_verification_attestation_dict(
            {"id": "unknown-provider"},
            [{"provider": "google_scholar"}],
        )
