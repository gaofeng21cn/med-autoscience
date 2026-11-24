"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt

from .constants import (
    _DEFAULT_MAIN_TABLE_INFORMATION_BUDGET,
)
from .request import (
    _is_reviewer_revision,
)

def _aggregate_review_status(request: Mapping[str, Any]) -> str:
    verdicts = {
        item["receipt"]["verdict"]
        for item in request["generation_manifest"]["independent_review_receipts"]
    }
    if "rejected" in verdicts:
        return "rejected"
    if "revision_required" in verdicts:
        return "revision_required"
    return "passed"


def _review_quality_debt(
    request: Mapping[str, Any],
) -> tuple[list[str], list[dict[str, str]]]:
    codes: list[str] = []
    refs: list[dict[str, str]] = []
    for wrapper in request["generation_manifest"]["independent_review_receipts"]:
        receipt = wrapper["receipt"]
        codes.extend(receipt["quality_debt_codes"])
        refs.extend(receipt["defect_refs"])
    unique_refs = {(item["ref"], item["sha256"]): item for item in refs}
    return dedupe(codes), list(unique_refs.values())


def _first_draft_quality_issue(
    request: Mapping[str, Any],
) -> tuple[str, list[str], str] | None:
    manifest = request["generation_manifest"]
    if (
        manifest["schema_version"] != 2
        or manifest["manifest_scope"] == "analysis_generation"
        or request["mission"]["stage_id"]
        not in {
            "manuscript_authoring",
            "review_and_quality_gate",
            "finalize_and_publication_handoff",
        }
    ):
        return None
    application = manifest.get("first_draft_quality_application")
    if application is None:
        return (
            "baseline_and_evidence_setup",
            ["first_draft_quality_application_missing"],
            "materialize the current Scholar preflight application and exact upstream refs",
        )

    if application["schema_version"] != 2:
        return (
            "baseline_and_evidence_setup",
            ["first_draft_candidate_dispositions_missing"],
            "regenerate the first-draft application with canonical candidate dispositions",
        )

    dispositions = application["candidate_dispositions"]
    for owner in FIRST_DRAFT_QUALITY_ROUTE_PRIORITY:
        owner_dispositions = [
            disposition
            for disposition in dispositions.values()
            if disposition["status"] == "route_back_required"
            and disposition["earliest_route_back_owner"] == owner
        ]
        if owner_dispositions:
            return (
                owner,
                dedupe(
                    [
                        reason_code
                        for disposition in owner_dispositions
                        for reason_code in disposition["reason_codes"]
                    ]
                ),
                "resolve the earliest canonical first-draft preflight findings and "
                "regenerate their exact candidate refs",
            )

    candidate_refs = application["candidate_refs"]
    owner_by_field = {
        "clinical_analysis_input_identity_ref": "baseline_and_evidence_setup",
        "citation_source_coverage_ref": "baseline_and_evidence_setup",
        "validation_partition_integrity_ref": "bounded_analysis_campaign",
        "endpoint_analysis_set_reconciliation_ref": "bounded_analysis_campaign",
        "model_complexity_sparse_event_ref": "bounded_analysis_campaign",
        "fixed_horizon_risk_semantics_ref": "bounded_analysis_campaign",
        "competing_risk_ref": "bounded_analysis_campaign",
        "decision_curve_validity_ref": "bounded_analysis_campaign",
        "external_transportability_ref": "bounded_analysis_campaign",
        "medical_initial_draft_preflight_candidate_ref": "manuscript_authoring",
        "author_stance_integrity_ref": "manuscript_authoring",
        "baseline_table_traceability_ref": "manuscript_authoring",
        "document_display_scope_coverage_ref": "manuscript_authoring",
        "claim_guardrail_ref": "manuscript_authoring",
    }
    applicable_fields = first_draft_applicable_ref_fields(application)
    for owner in FIRST_DRAFT_QUALITY_ROUTE_PRIORITY:
        missing = [
            f"first_draft_{field.removesuffix('_ref')}_missing"
            for field in owner_by_field
            if field in applicable_fields
            and owner_by_field[field] == owner
            and candidate_refs[field] is None
        ]
        if missing:
            return (
                owner,
                missing,
                "materialize the exact candidate refs required by the accepted dispositions",
            )

    triggers = application["triggers"]
    missing_authoring = []
    if triggers["requires_reader_pdf"] and not any(
        artifact["role"] == "pdf" for artifact in manifest["artifacts"]
    ):
        missing_authoring.append("first_draft_composed_paper_pdf_missing")
    if missing_authoring:
        return (
            "manuscript_authoring",
            missing_authoring,
            "close manuscript, Table 1, claim, and composed-reader display refs",
        )
    return None


def _reviewer_revision_generation_issue(
    request: Mapping[str, Any],
) -> tuple[str, list[str], str] | None:
    manifest = request["generation_manifest"]
    if (
        not _is_reviewer_revision(request)
        or manifest["schema_version"] != 2
        or request["mission"]["stage_id"]
        not in {
            "manuscript_authoring",
            "review_and_quality_gate",
            "finalize_and_publication_handoff",
        }
    ):
        return None
    selected_build = manifest.get("selected_build_binding")
    if selected_build is None:
        return (
            "manuscript_authoring",
            ["selected_build_binding_missing"],
            "bind the selected archive, build receipt, dependency manifest, and exact root reader bytes",
        )
    selected_build_codes: list[str] = []
    if selected_build["dependency_currentness"] != "current":
        selected_build_codes.append("selected_build_dependencies_not_current")
    if not selected_build["root_matches_selected_bytes"]:
        selected_build_codes.append("root_reader_output_differs_from_selected_build")
    if selected_build_codes:
        return (
            "manuscript_authoring",
            selected_build_codes,
            "rebuild from current dependencies and select a root reader output with exact byte equality",
        )
    response_sync = manifest.get("reviewer_response_sync")
    if response_sync is None:
        return (
            "manuscript_authoring",
            ["reviewer_response_sync_missing"],
            "bind the current reviewer response, action matrix, artifact inventory, and affected exact refs before freeze",
        )
    response_codes: list[str] = []
    if response_sync["sync_status"] != "synchronized":
        response_codes.append("reviewer_response_sync_route_back_required")
    if any(item["status"] == "planned" for item in response_sync["items"]):
        response_codes.append("reviewer_response_items_not_implemented")
    if (
        response_sync["post_freeze_disposition"]
        == "scientific_change_requires_new_revision"
    ):
        response_codes.append("post_freeze_scientific_change_requires_new_revision_cycle")
    if response_codes:
        return (
            "manuscript_authoring",
            response_codes,
            "synchronize every response item to current exact artifacts or start the bound new revision cycle",
        )
    return None


def _professional_figure_skill_quality_debt(
    request: Mapping[str, Any],
) -> list[str]:
    manifest = request["generation_manifest"]
    figure_artifacts = {
        item["member_id"]: item
        for item in manifest["artifacts"]
        if item["role"] == "figure_file" and "member_id" in item
    }
    if not figure_artifacts:
        return []

    invocations = [
        item
        for item in manifest.get("professional_skill_invocations", [])
        if item["surface_kind"] == "mas_professional_figure_skill_invocation_candidate"
    ]
    if not invocations:
        return ["professional_figure_skill_consumption_evidence_missing"]
    requires_exact_receipts = manifest.get("first_draft_quality_application") is not None

    groups: dict[str, list[Mapping[str, Any]]] = {}
    for invocation in invocations:
        groups.setdefault(invocation["figure_id"], []).append(invocation)

    codes: list[str] = []
    covered_members: set[str] = set()
    for figure_id, group in sorted(groups.items()):
        if requires_exact_receipts and any(
            item["schema_version"] != 2 for item in group
        ):
            codes.append("professional_figure_exact_receipt_binding_missing")
        skills = {item["skill_id"] for item in group}
        required = {"medical-figure-design", "medical-figure-style"}
        composition_modes = {item["composition_mode"] for item in group}
        figure_kinds = {item["figure_kind"] for item in group}
        if len(composition_modes) != 1 or len(figure_kinds) != 1:
            codes.append("professional_figure_skill_receipt_scope_mismatch")
            continue
        if composition_modes == {"assembled_panels"}:
            required.add("medical-figure-composer")
        missing = required - skills
        if "medical-figure-design" in missing:
            codes.append("professional_figure_design_consumption_missing")
        if "medical-figure-style" in missing:
            codes.append("professional_figure_style_consumption_missing")
        if "medical-figure-composer" in missing:
            codes.append("professional_figure_composer_consumption_missing")
        unexpected_composer = (
            composition_modes == {"single_canvas_direct"}
            and "medical-figure-composer" in skills
        )
        if unexpected_composer:
            codes.append("professional_figure_composer_receipt_not_applicable")

        output_sets = {
            tuple(
                sorted(
                    binding["member_id"] for binding in item["output_artifact_bindings"]
                )
            )
            for item in group
        }
        if len(output_sets) != 1:
            codes.append("professional_figure_skill_output_binding_mismatch")
            continue
        member_ids = set(next(iter(output_sets)))
        if not member_ids.issubset(figure_artifacts):
            codes.append("professional_figure_skill_output_binding_invalid")
            continue
        if any(
            binding
            != {
                key: figure_artifacts[binding["member_id"]][key]
                for key in ("member_id", "role", "ref", "size_bytes", "sha256")
            }
            for item in group
            for binding in item["output_artifact_bindings"]
        ):
            codes.append("professional_figure_skill_output_binding_stale")
        covered_members.update(member_ids)
        if not figure_id.strip():
            codes.append("professional_figure_skill_figure_identity_missing")

    if covered_members != set(figure_artifacts):
        codes.append("professional_figure_skill_output_coverage_incomplete")
    return dedupe(codes)


def _professional_manuscript_skill_quality_debt(
    request: Mapping[str, Any],
) -> list[str]:
    manifest = request["generation_manifest"]
    if manifest["schema_version"] != 2 or manifest["manifest_scope"] == (
        "analysis_generation"
    ):
        return []
    artifacts = {
        item["member_id"]: item for item in manifest["artifacts"] if "member_id" in item
    }
    invocations = [
        item
        for item in manifest.get("professional_skill_invocations", [])
        if item["surface_kind"]
        == ("mas_professional_manuscript_skill_invocation_candidate")
    ]
    invocations_by_skill = {item["skill_id"]: item for item in invocations}
    artifact_roles = {item["role"] for item in artifacts.values()}
    required_skills = {"medical-manuscript-writing"}
    application = manifest.get("first_draft_quality_application")
    if application is not None:
        required_skills.add("medical-reference-integrity-auditor")
        if application["triggers"]["uses_clinical_or_registry_data"]:
            required_skills.add(
                "medical-data-freeze-and-analysis-readiness-reviewer"
            )
        if application["paper_type"] == "prediction_model":
            required_skills.add("medical-statistical-review")
        triggers = application["triggers"]
        if (
            triggers["reports_fixed_horizon_risk"]
            or triggers["competing_risk_relevant"]
        ):
            required_skills.add("medical-survival-analysis-plan")
        if application["validation_design"] == "external_validation":
            required_skills.add("medical-risk-model-transportability-reviewer")
        if triggers["includes_table_one"]:
            required_skills.add("medical-table-design")
        if triggers["requires_reader_pdf"]:
            required_skills.add("medical-display-qc")
    if artifact_roles & {"analysis_output", "numeric_trace"}:
        required_skills.add("medical-statistical-review")
    if artifact_roles & {"table_catalog", "table_file"}:
        required_skills.add("medical-table-design")
    if manifest["manifest_scope"] == "publication_generation":
        required_skills.add("medical-submission-prep")
    missing_codes = {
        "medical-manuscript-writing": (
            "professional_manuscript_writing_consumption_missing"
        ),
        "medical-data-freeze-and-analysis-readiness-reviewer": (
            "professional_data_freeze_readiness_consumption_missing"
        ),
        "medical-reference-integrity-auditor": (
            "professional_reference_integrity_consumption_missing"
        ),
        "medical-statistical-review": (
            "professional_statistical_review_consumption_missing"
        ),
        "medical-survival-analysis-plan": (
            "professional_survival_analysis_consumption_missing"
        ),
        "medical-risk-model-transportability-reviewer": (
            "professional_transportability_review_consumption_missing"
        ),
        "medical-table-design": "professional_table_design_consumption_missing",
        "medical-display-qc": "professional_display_qc_consumption_missing",
        "medical-submission-prep": (
            "professional_submission_prep_consumption_missing"
        ),
    }
    coverage_codes = {
        "medical-manuscript-writing": (
            "professional_manuscript_writing_output_coverage_incomplete"
        ),
        "medical-registry-atlas-story-architect": (
            "professional_registry_story_output_coverage_incomplete"
        ),
        "medical-data-freeze-and-analysis-readiness-reviewer": (
            "professional_data_freeze_output_coverage_incomplete"
        ),
        "medical-reference-integrity-auditor": (
            "professional_reference_integrity_output_coverage_incomplete"
        ),
        "medical-statistical-review": (
            "professional_statistical_review_output_coverage_incomplete"
        ),
        "medical-survival-analysis-plan": (
            "professional_survival_analysis_output_coverage_incomplete"
        ),
        "medical-risk-model-transportability-reviewer": (
            "professional_transportability_output_coverage_incomplete"
        ),
        "medical-table-design": (
            "professional_table_design_output_coverage_incomplete"
        ),
        "medical-display-qc": "professional_display_qc_output_coverage_incomplete",
        "medical-submission-prep": (
            "professional_submission_prep_output_coverage_incomplete"
        ),
    }
    codes: list[str] = []
    for skill_id in sorted(required_skills):
        if skill_id not in invocations_by_skill:
            codes.append(missing_codes[skill_id])
    if (
        application is not None
        and application["validation_design"] != "external_validation"
        and "medical-risk-model-transportability-reviewer" in invocations_by_skill
    ):
        codes.append("professional_transportability_review_not_applicable")
    for invocation in invocations:
        allowed_roles = PROFESSIONAL_MANUSCRIPT_SKILL_ROLES[invocation["skill_id"]]
        expected_member_ids = {
            member_id
            for member_id, artifact in artifacts.items()
            if artifact["role"] in allowed_roles
        }
        covered_member_ids = {
            binding["member_id"] for binding in invocation["output_artifact_bindings"]
        }
        if covered_member_ids != expected_member_ids:
            codes.append(coverage_codes[invocation["skill_id"]])
        for binding in invocation["output_artifact_bindings"]:
            expected = artifacts.get(binding["member_id"])
            if (
                expected is None
                or expected["role"] not in allowed_roles
                or any(
                    binding[key] != expected[key]
                    for key in ("member_id", "role", "ref", "size_bytes", "sha256")
                )
            ):
                codes.append("professional_manuscript_skill_output_binding_stale")
        if application is not None:
            if invocation["schema_version"] != 2:
                codes.append("professional_skill_exact_receipt_binding_missing")
            else:
                required_input_roles = PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES[
                    invocation["skill_id"]
                ]
                if (
                    invocation["skill_id"] == "medical-manuscript-writing"
                    and not application["triggers"][
                        "uses_clinical_or_registry_data"
                    ]
                ):
                    required_input_roles = required_input_roles - {
                        "clinical_analysis_input_identity"
                    }
                covered_input_roles = {
                    binding["role"]
                    for binding in invocation["input_artifact_bindings"]
                }
                if not required_input_roles.issubset(covered_input_roles):
                    codes.append("professional_skill_input_coverage_incomplete")
        if invocation["skill_id"] == "medical-table-design":
            codes.extend(_professional_table_quality_debt(invocation))
    return dedupe(codes)


def _professional_table_quality_debt(
    invocation: Mapping[str, Any],
) -> list[str]:
    application = invocation.get("table_quality_application")
    if not isinstance(application, Mapping):
        return ["professional_table_quality_application_missing"]
    codes: list[str] = []
    if (
        "medical-table-design#main-table-information-budget"
        not in invocation["consumed_rule_refs"]
    ):
        codes.append("professional_table_information_budget_rule_not_consumed")
    for table in application["main_tables"]:
        exceeded = any(
            table[field] > limit
            for field, limit in _DEFAULT_MAIN_TABLE_INFORMATION_BUDGET.items()
        )
        if exceeded and table["budget_status"] != "documented_exception":
            codes.append("professional_main_table_information_budget_exceeded")
        if (
            exceeded
            and table["budget_status"] != "documented_exception"
            and not table["supplementary_detail_refs"]
        ):
            codes.append("professional_main_table_supplementary_route_missing")
        if table["standalone_notes_heading_present"]:
            codes.append("professional_main_table_notes_heading_present")
        if (
            table["final_embedding_status"] != "passed"
            or table["final_embedding_page_span"]
            > _DEFAULT_MAIN_TABLE_INFORMATION_BUDGET[
                "final_embedding_page_span"
            ]
        ):
            codes.append("professional_main_table_final_embedding_incomplete")
    return dedupe(codes)
