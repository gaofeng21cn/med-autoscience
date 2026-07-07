from __future__ import annotations


LIGHT_OBSERVED_HEAD = "d71033733bc4b357f3a2f0b6460ad7d8da070954"

LIGHT_BASE_OUTPUT_REF_KINDS: tuple[str, ...] = (
    "verified_asset_ref",
    "collision_check_ref",
    "refusal_rehearsal_ref",
    "fresh_evidence_gate_ref",
)

LIGHT_SKILL_CONTENT_OUTPUT_REF_KINDS: tuple[str, ...] = (
    "source_search_discipline_ref",
    "data_access_sink_ref",
    "citation_edge_retraction_ref",
    "citation_locator_audit_ref",
    "prisma_flow_reconciliation_ref",
    "figure_manifest_check_ref",
    "experiment_matrix_backlink_ref",
    "statistical_analysis_triage_ref",
    "overclaim_lint_warning_ref",
    "argument_review_hint_ref",
    "figure_integrity_warning_ref",
    "style_fingerprint_hint_ref",
)

LIGHT_MATERIALIZER_OUTPUT_REF_KINDS: tuple[str, ...] = (
    *LIGHT_BASE_OUTPUT_REF_KINDS,
    *LIGHT_SKILL_CONTENT_OUTPUT_REF_KINDS,
)


def build_light_materializer_contract() -> dict[str, object]:
    return {
        "surface_kind": "light_external_advisory_materializer_contract",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "controller_ref": "med_autoscience.controllers.light_advisory_materializer.materialize_light_advisory_refs",
        "cli_entry": "medautosci study light-advisory-materialize",
        "flat_cli_entry": "medautosci light-advisory-materialize",
        "writes": [
            "artifacts/stage_outputs/<stage>/advisory/light_external_pattern_refs.json",
            *[
                f"artifacts/stage_outputs/<stage>/advisory/refs/{ref_kind}.json"
                for ref_kind in LIGHT_MATERIALIZER_OUTPUT_REF_KINDS
            ],
            "artifacts/stage_outputs/<stage>/advisory/typed_blocker_candidate.json",
        ],
        "does_not_write": [
            "study truth",
            "paper body",
            "artifact body",
            "memory body",
            "owner receipt",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "submission package",
            "current_package",
        ],
        "output_ref_kinds": list(LIGHT_MATERIALIZER_OUTPUT_REF_KINDS),
        "optional_ref_kind_policy": "materialize_when_payload_present_or_route_required_only",
        "typed_blocker_materialization": "candidate_only_current_delta_hard_gate_required",
        "missing_advisory_behavior": "do_not_block_dispatch",
        "blocks_unrelated_owner_dispatch": False,
        "external_light_runtime_dependency": False,
        "external_light_router_dependency": False,
        "external_light_db09_dependency": False,
    }


__all__ = [
    "LIGHT_BASE_OUTPUT_REF_KINDS",
    "LIGHT_MATERIALIZER_OUTPUT_REF_KINDS",
    "LIGHT_OBSERVED_HEAD",
    "LIGHT_SKILL_CONTENT_OUTPUT_REF_KINDS",
    "build_light_materializer_contract",
]
