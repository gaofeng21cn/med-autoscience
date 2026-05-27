from __future__ import annotations

import pytest

from med_autoscience.medical_material_passport import build_life_science_source_adapter_output


def test_life_science_source_adapter_output_is_refs_only_and_currentness_bound() -> None:
    output = build_life_science_source_adapter_output(
        adapter_name="openai-life-science-research-pattern",
        adapter_version="603a6e80711116e3584c33ecb8897548ed03d4f6",
        records=[
            {
                "record_id": "opentargets:IL6R-asthma",
                "source_pointer": "opentargets:ENSG00000160712:EFO_0000270",
                "refs": ["source_refs/opentargets/il6r_asthma.json"],
                "metadata": {
                    "source_family_id": "human_genetics_and_variant_evidence",
                    "provider_id": "opentargets-skill",
                    "accessed_at": "2026-05-27T00:00:00Z",
                    "query_fingerprint": "sha256:abc123",
                    "identifier_crosswalk": {
                        "gene": "IL6R",
                        "ensembl_id": "ENSG00000160712",
                        "phenotype_ref": "EFO_0000270",
                    },
                    "version_or_release": "platform-current-at-access",
                    "limitation_flags": ["association_not_causality"],
                    "checked_at": "2026-05-27T00:00:00Z",
                    "expires_or_stale_after": "2026-06-26T00:00:00Z",
                },
            }
        ],
        rejected=[
            {
                "source": "gnomad-graphql-skill",
                "reason": "missing_required_field",
                "missing_fields": ["query_fingerprint"],
            }
        ],
    )

    assert output["surface_kind"] == "mas_source_adapter_output"
    assert output["source_pattern"] == "openai_life_science_research_clean_room"
    assert output["records_write_mas_truth"] is False
    assert output["records"][0]["body_included"] is False
    assert output["records"][0]["write_mas_truth"] is False
    assert output["records"][0]["metadata"]["source_family_id"] == "human_genetics_and_variant_evidence"
    assert output["records"][0]["metadata"]["provider_id"] == "opentargets-skill"
    assert output["records"][0]["metadata"]["limitation_flags"] == ["association_not_causality"]
    assert output["authority_boundary"] == {
        "can_write_mas_truth": False,
        "can_authorize_source_readiness_verdict": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
    }
    assert output["rejection_log"]["rejected"][0]["reason"] == "missing_required_field"


def test_life_science_source_adapter_output_rejects_missing_required_metadata() -> None:
    with pytest.raises(ValueError, match="metadata requires query_fingerprint"):
        build_life_science_source_adapter_output(
            adapter_name="openai-life-science-research-pattern",
            adapter_version="603a6e80711116e3584c33ecb8897548ed03d4f6",
            records=[
                {
                    "record_id": "clinicaltrials:NCT",
                    "source_pointer": "clinicaltrials:NCT00000000",
                    "refs": ["source_refs/clinicaltrials/nct00000000.json"],
                    "metadata": {
                        "source_family_id": "clinical_translational_and_pharmacology",
                        "provider_id": "clinicaltrials-skill",
                        "accessed_at": "2026-05-27T00:00:00Z",
                        "checked_at": "2026-05-27T00:00:00Z",
                        "expires_or_stale_after": "2026-06-26T00:00:00Z",
                    },
                }
            ],
            rejected=[],
        )

