from .shared import *
from .asset_scans import *
from .catalog_checks import *
from .manuscript_checks import *
from med_autoscience.medical_journal_style_corpus import (
    ensure_current_medical_journal_style_corpus,
    stable_medical_journal_style_corpus_path,
)
from med_autoscience.medical_prose_review_request import (
    materialize_medical_prose_review_request,
    stable_medical_prose_review_request_path,
)
from med_autoscience.policies.medical_reporting_checklist import build_structured_reporting_checklist


def _materialization_error_hit(*, state: SurfaceState, artifact_path: Path, error: Exception) -> dict[str, str]:
    return {
        "path": str(artifact_path),
        "location": "file",
        "pattern_id": "medical_prose_review_request",
        "phrase": artifact_path.name,
        "excerpt": f"Medical prose review request materialization is blocked: {error}",
    }


def _append_materialization_error(report: dict[str, Any], hit: dict[str, str]) -> dict[str, Any]:
    blockers = list(report.get("blockers") or [])
    if "medical_prose_review_request_missing_or_incomplete" not in blockers:
        blockers.append("medical_prose_review_request_missing_or_incomplete")
    top_hits = list(report.get("top_hits") or [])
    top_hits.insert(0, hit)
    updated = dict(report)
    updated["blockers"] = blockers
    updated["top_hits"] = top_hits[:80]
    updated["status"] = "blocked"
    updated["recommended_action"] = medical_surface_policy.BLOCKED_RECOMMENDED_ACTION
    return updated

def build_surface_report(state: SurfaceState) -> dict[str, Any]:
    forbidden_hits: list[dict[str, Any]] = []
    forbidden_hits.extend(scan_text_file(state.draft_path))
    forbidden_hits.extend(scan_text_file(state.review_manuscript_path))
    forbidden_hits.extend(scan_catalog_strings(state.figure_catalog_path, collection_key="figures"))
    forbidden_hits.extend(scan_catalog_strings(state.table_catalog_path, collection_key="tables"))
    figure_catalog_valid, figure_catalog_hits = inspect_required_json_contract(
        path=state.figure_catalog_path,
        validator=medical_surface_policy.validate_figure_catalog,
        pattern_id="figure_catalog",
        label="figure catalog",
    )
    table_catalog_valid, table_catalog_hits = inspect_required_json_contract(
        path=state.table_catalog_path,
        validator=medical_surface_policy.validate_table_catalog,
        pattern_id="table_catalog",
        label="table catalog",
    )
    for path in discover_figure_text_assets(state.paper_root, state.figure_catalog_path):
        forbidden_hits.extend(scan_text_file(path))
    for path in discover_table_text_assets(
        state.paper_root,
        state.table_catalog_path,
        table_shell_ids={display_registry.get_table_shell_spec("table3_clinical_interpretation_summary").shell_id},
    ):
        forbidden_hits.extend(scan_markdown_table_body(path))
    figure_ids = figure_ids_from_catalog(state.figure_catalog_path)
    all_figure_ids = figure_ids_from_catalog(state.figure_catalog_path, include_all_roles=True)
    table_ids = table_ids_from_catalog(state.table_catalog_path)
    reporting_contract_path = state.paper_root / "medical_reporting_contract.json"
    reporting_contract_payload = load_json(reporting_contract_path, default={})
    if not isinstance(reporting_contract_payload, dict):
        reporting_contract_payload = {}
    structured_reporting_checklist = build_structured_reporting_checklist(reporting_contract_payload)
    display_story_roles = load_display_catalog_story_roles(reporting_contract_path)
    required_display_catalog_coverage_valid, required_display_catalog_hits = inspect_required_display_catalog_coverage(
        reporting_contract_path=reporting_contract_path,
        figure_ids=all_figure_ids,
        table_ids=table_ids,
    )
    methods_manifest_valid, methods_manifest_hits = inspect_required_json_contract(
        path=state.methods_implementation_manifest_path,
        validator=medical_surface_policy.validate_methods_implementation_manifest,
        pattern_id="methods_implementation_manifest",
        label="medical methods implementation manifest",
    )
    review_ledger_valid, review_ledger_hits = inspect_required_json_contract(
        path=state.review_ledger_path,
        validator=medical_surface_policy.validate_review_ledger,
        pattern_id="review_ledger",
        label="review ledger",
    )
    statistical_reviewer_audit_payload = load_json(state.statistical_reviewer_audit_path, default=None)
    statistical_reviewer_audit_validation = (
        validate_statistical_reviewer_audit(statistical_reviewer_audit_payload)
        if isinstance(statistical_reviewer_audit_payload, dict)
        else {"status": "blocked", "reason_code": "missing_statistical_reviewer_audit"}
    )
    statistical_reviewer_audit_valid = statistical_reviewer_audit_validation["status"] == "present"
    statistical_reviewer_audit_hits = (
        []
        if statistical_reviewer_audit_valid
        else [
            {
                "path": str(state.statistical_reviewer_audit_path),
                "location": "file",
                "pattern_id": "statistical_reviewer_audit",
                "phrase": statistical_reviewer_audit_validation["reason_code"],
                "excerpt": (
                    "Statistical reviewer audit is missing or unresolved: "
                    f"{statistical_reviewer_audit_validation['reason_code']}."
                ),
            }
        ]
    )
    structured_disclosure_audit_valid, structured_disclosure_audit_hits = inspect_required_json_contract(
        path=state.structured_disclosure_audit_path,
        validator=medical_disclosure_contract.validate_structured_disclosure_audit,
        pattern_id="structured_disclosure_audit",
        label="structured disclosure audit",
    )
    medical_manuscript_blueprint_valid, medical_manuscript_blueprint_hits = inspect_required_json_contract(
        path=state.medical_manuscript_blueprint_path,
        validator=medical_surface_policy.validate_medical_manuscript_blueprint,
        pattern_id="medical_manuscript_blueprint",
        label="medical manuscript blueprint",
    )
    medical_prose_review_payload = load_json(state.medical_prose_review_path, default=None)
    medical_prose_review_valid, medical_prose_review_hits = inspect_required_json_contract(
        path=state.medical_prose_review_path,
        validator=medical_surface_policy.validate_medical_prose_review,
        pattern_id="medical_prose_review",
        label="AI-first medical prose review",
        payload_override=medical_prose_review_payload,
    )
    results_narrative_valid, results_narrative_hits = inspect_required_json_contract(
        path=state.results_narrative_map_path,
        validator=medical_surface_policy.validate_results_narrative_map,
        pattern_id="results_narrative_map",
        label="results narrative map",
    )
    figure_semantics_valid, figure_semantics_hits = inspect_required_json_contract(
        path=state.figure_semantics_manifest_path,
        validator=medical_surface_policy.validate_figure_semantics_manifest,
        pattern_id="figure_semantics_manifest",
        label="figure semantics manifest",
    )
    claim_evidence_map_payload = load_json(state.claim_evidence_map_path, default=None)
    evidence_ledger_payload = _backfill_evidence_ledger_claims_from_claim_map(
        load_json(state.evidence_ledger_path, default=None),
        claim_evidence_map_payload,
    )
    claim_evidence_map_valid, claim_evidence_map_hits = inspect_required_json_contract(
        path=state.claim_evidence_map_path,
        validator=medical_surface_policy.validate_claim_evidence_map,
        pattern_id="claim_evidence_map",
        label="claim evidence map",
        payload_override=claim_evidence_map_payload,
    )
    numeric_trace_valid, numeric_trace_hits = inspect_required_json_contract(
        path=state.numeric_trace_path,
        validator=medical_surface_policy.validate_numeric_trace,
        pattern_id="numeric_trace",
        label="numeric trace",
    )
    evidence_ledger_valid, evidence_ledger_hits = inspect_required_json_contract(
        path=state.evidence_ledger_path,
        validator=medical_surface_policy.validate_evidence_ledger,
        pattern_id="evidence_ledger",
        label="evidence ledger",
        payload_override=evidence_ledger_payload,
    )
    derived_analysis_valid, derived_analysis_hits = inspect_required_json_contract(
        path=state.derived_analysis_manifest_path,
        validator=medical_surface_policy.validate_derived_analysis_manifest,
        pattern_id="derived_analysis_manifest",
        label="derived analysis manifest",
    )
    reproducibility_valid, reproducibility_hits = inspect_required_json_contract(
        path=state.reproducibility_supplement_path,
        validator=medical_surface_policy.validate_reproducibility_supplement,
        pattern_id="manuscript_safe_reproducibility_supplement",
        label="manuscript-safe reproducibility supplement",
    )
    endpoint_note_valid, endpoint_note_text, endpoint_note_hits = inspect_required_text_contract(
        path=state.endpoint_provenance_note_path,
        validator=medical_surface_policy.validate_endpoint_provenance_note,
        pattern_id="endpoint_provenance_note",
        label="endpoint provenance note",
    )
    results_narrative_payload = load_json(state.results_narrative_map_path, default=None)
    results_narrative_display_hits = inspect_results_narrative_display_items(
        path=state.results_narrative_map_path,
        payload=results_narrative_payload,
        figure_ids=figure_ids,
        table_ids=table_ids,
    )
    if results_narrative_display_hits:
        results_narrative_valid = False
        results_narrative_hits.extend(results_narrative_display_hits)
    results_narrative_figure_coverage_hits = inspect_results_narrative_figure_coverage(
        path=state.results_narrative_map_path,
        payload=results_narrative_payload,
        figure_ids=figure_ids,
    )
    if results_narrative_figure_coverage_hits:
        results_narrative_valid = False
        results_narrative_hits.extend(results_narrative_figure_coverage_hits)
    results_display_surface_hits = inspect_results_display_surface_coverage(
        path=state.results_narrative_map_path,
        payload=results_narrative_payload,
        display_story_roles=display_story_roles,
    )
    figure_semantics_payload = load_json(state.figure_semantics_manifest_path, default=None)
    figure_catalog_payload = load_json(state.figure_catalog_path, default=None)
    figure_layout_sidecar_hits = inspect_figure_layout_sidecar_contract(
        paper_root=state.paper_root,
        figure_catalog_payload=figure_catalog_payload,
    )
    figure_semantics_coverage_hits = inspect_figure_semantics_coverage(
        path=state.figure_semantics_manifest_path,
        payload=figure_semantics_payload,
        figure_ids=figure_ids,
    )
    if figure_semantics_coverage_hits:
        figure_semantics_valid = False
        figure_semantics_hits.extend(figure_semantics_coverage_hits)
    figure_semantics_renderer_alignment_hits = inspect_figure_semantic_renderer_alignment(
        path=state.figure_semantics_manifest_path,
        figure_catalog_payload=figure_catalog_payload,
        figure_semantics_payload=figure_semantics_payload,
    )
    if figure_semantics_renderer_alignment_hits:
        figure_semantics_valid = False
        figure_semantics_hits.extend(figure_semantics_renderer_alignment_hits)
    claim_evidence_display_hits = inspect_claim_evidence_display_bindings(
        path=state.claim_evidence_map_path,
        payload=claim_evidence_map_payload,
        known_display_items=figure_ids | table_ids,
    )
    if claim_evidence_display_hits:
        claim_evidence_map_valid = False
        claim_evidence_map_hits.extend(claim_evidence_display_hits)
    methods_manifest_payload = load_json(state.methods_implementation_manifest_path, default=None)
    derived_analysis_payload = load_json(state.derived_analysis_manifest_path, default=None)
    reproducibility_payload = load_json(state.reproducibility_supplement_path, default=None)
    derived_analysis_link_hits = inspect_derived_analysis_links(
        path=state.derived_analysis_manifest_path,
        payload=derived_analysis_payload,
        known_display_items=figure_ids | table_ids,
    )
    if derived_analysis_link_hits:
        derived_analysis_valid = False
        derived_analysis_hits.extend(derived_analysis_link_hits)
    missing_data_policy_hits = inspect_missing_data_policy_consistency(
        methods_path=state.methods_implementation_manifest_path,
        methods_payload=methods_manifest_payload,
        derived_analysis_path=state.derived_analysis_manifest_path,
        derived_analysis_payload=derived_analysis_payload,
        reproducibility_path=state.reproducibility_supplement_path,
        reproducibility_payload=reproducibility_payload,
    )
    analysis_plane_patterns = medical_surface_policy.get_analysis_plane_jargon_patterns()
    analysis_plane_jargon_hits: list[dict[str, Any]] = []
    analysis_plane_jargon_hits.extend(
        scan_manuscript_surface_sections_for_patterns(state.draft_path, patterns=analysis_plane_patterns)
    )
    analysis_plane_jargon_hits.extend(
        scan_manuscript_surface_sections_for_patterns(state.review_manuscript_path, patterns=analysis_plane_patterns)
    )
    analysis_plane_jargon_hits.extend(
        scan_main_text_catalog_surface_for_patterns(
            state.figure_catalog_path,
            collection_key="figures",
            patterns=analysis_plane_patterns,
        )
    )
    analysis_plane_jargon_hits.extend(
        scan_main_text_catalog_surface_for_patterns(
            state.table_catalog_path,
            collection_key="tables",
            patterns=analysis_plane_patterns,
        )
    )
    analysis_plane_jargon_hits.extend(
        inspect_results_narrative_surface_language(
            path=state.results_narrative_map_path,
            payload=results_narrative_payload,
            patterns=analysis_plane_patterns,
        )
    )
    analysis_plane_jargon_hits.extend(
        inspect_claim_evidence_surface_language(
            path=state.claim_evidence_map_path,
            payload=claim_evidence_map_payload,
            patterns=analysis_plane_patterns,
        )
    )
    publication_surface_residue_patterns = medical_surface_policy.get_publication_surface_residue_patterns()
    publication_surface_residue_hits: list[dict[str, Any]] = []
    publication_surface_residue_hits.extend(
        scan_text_file_for_patterns(state.draft_path, patterns=publication_surface_residue_patterns)
    )
    publication_surface_residue_hits.extend(
        scan_text_file_for_patterns(state.review_manuscript_path, patterns=publication_surface_residue_patterns)
    )
    publication_surface_residue_hits.extend(
        scan_catalog_strings_for_patterns(
            state.figure_catalog_path,
            collection_key="figures",
            patterns=publication_surface_residue_patterns,
        )
    )
    publication_surface_residue_hits.extend(
        scan_catalog_strings_for_patterns(
            state.table_catalog_path,
            collection_key="tables",
            patterns=publication_surface_residue_patterns,
        )
    )
    for path in (
        state.methods_implementation_manifest_path,
        state.review_ledger_path,
        state.statistical_reviewer_audit_path,
        state.structured_disclosure_audit_path,
        state.medical_manuscript_blueprint_path,
        state.medical_prose_review_path,
        state.results_narrative_map_path,
        state.figure_semantics_manifest_path,
        state.claim_evidence_map_path,
        state.evidence_ledger_path,
        state.derived_analysis_manifest_path,
        state.reproducibility_supplement_path,
        state.endpoint_provenance_note_path,
    ):
        publication_surface_residue_hits.extend(
            scan_text_file_for_patterns(path, patterns=publication_surface_residue_patterns)
        )
    publication_surface_residue_hits = unique_hits(publication_surface_residue_hits)
    medical_journal_prose_patterns = medical_surface_policy.get_medical_journal_prose_patterns()
    medical_journal_prose_hits: list[dict[str, Any]] = []
    medical_journal_prose_hits.extend(
        scan_text_file_for_patterns(state.draft_path, patterns=medical_journal_prose_patterns)
    )
    medical_journal_prose_hits.extend(
        scan_text_file_for_patterns(state.review_manuscript_path, patterns=medical_journal_prose_patterns)
    )
    medical_journal_prose_hits.extend(
        inspect_results_narrative_surface_language(
            path=state.results_narrative_map_path,
            payload=results_narrative_payload,
            patterns=medical_journal_prose_patterns,
        )
    )
    medical_journal_prose_hits = unique_hits(medical_journal_prose_hits)
    medical_journal_prose_blocking_hits = [
        hit
        for hit in medical_journal_prose_hits
        if str(hit.get("pattern_id") or "").strip()
        in medical_surface_policy.medical_journal_prose_blocking_pattern_ids()
    ]
    medical_journal_prose_quality = {}
    medical_journal_prose_ai_verdict = None
    medical_journal_prose_ai_route_back = None
    if medical_prose_review_valid and isinstance(medical_prose_review_payload, dict):
        medical_journal_prose_quality = (
            dict(medical_prose_review_payload.get("medical_journal_prose_quality") or {})
            if isinstance(medical_prose_review_payload.get("medical_journal_prose_quality"), dict)
            else {}
        )
        medical_journal_prose_ai_verdict = (
            str(medical_journal_prose_quality.get("overall_style_verdict") or "").strip()
            or None
        )
        route_back = medical_journal_prose_quality.get("route_back_recommendation")
        if isinstance(route_back, dict):
            medical_journal_prose_ai_route_back = str(route_back.get("route_target") or "").strip() or None
    results_narration_hits: list[dict[str, Any]] = []
    results_narration_hits.extend(scan_results_narration_text_file(state.draft_path))
    results_narration_hits.extend(scan_results_narration_text_file(state.review_manuscript_path))
    introduction_structure_hits: list[dict[str, Any]] = []
    introduction_structure_hits.extend(inspect_introduction_structure(state.draft_path))
    introduction_structure_hits.extend(inspect_introduction_structure(state.review_manuscript_path))
    methods_section_structure_hits: list[dict[str, Any]] = []
    methods_section_structure_hits.extend(inspect_methods_section_structure(state.draft_path))
    methods_section_structure_hits.extend(inspect_methods_section_structure(state.review_manuscript_path))
    results_section_structure_hits: list[dict[str, Any]] = []
    results_section_structure_hits.extend(inspect_results_section_structure(state.draft_path))
    results_section_structure_hits.extend(inspect_results_section_structure(state.review_manuscript_path))
    non_formal_question_hits: list[dict[str, Any]] = []
    non_formal_question_hits.extend(scan_non_formal_question_sentences(state.draft_path))
    non_formal_question_hits.extend(scan_non_formal_question_sentences(state.review_manuscript_path))
    medical_prose_reviewer_evidence_hits = unique_hits(
        [*medical_journal_prose_hits, *results_narration_hits, *non_formal_question_hits]
    )
    methodology_label_hits: list[dict[str, Any]] = []
    methodology_label_hits.extend(scan_methodology_labels_text_file(state.draft_path))
    methodology_label_hits.extend(scan_methodology_labels_text_file(state.review_manuscript_path))
    endpoint_caveat_sources = discover_endpoint_provenance_caveat_sources(state.quest_root)
    endpoint_note_payload = medical_surface_policy.parse_endpoint_provenance_note(endpoint_note_text or "")
    endpoint_statement = str(endpoint_note_payload.get("manuscript_required_statement") or "").strip()
    manuscript_surface_text = ""
    if state.draft_path.exists():
        manuscript_surface_text += state.draft_path.read_text(encoding="utf-8") + "\n"
    if state.review_manuscript_path.exists():
        manuscript_surface_text += state.review_manuscript_path.read_text(encoding="utf-8")
    endpoint_note_applied = (not endpoint_caveat_sources) or (
        endpoint_note_valid and bool(endpoint_statement) and endpoint_statement in manuscript_surface_text
    )
    if endpoint_caveat_sources and not endpoint_note_applied:
        endpoint_note_hits.append(
            {
                "path": str(state.endpoint_provenance_note_path),
                "location": "file",
                "pattern_id": "endpoint_provenance_note_unapplied",
                "phrase": state.endpoint_provenance_note_path.name,
                "excerpt": "Endpoint provenance caveat is documented upstream but not durably projected onto the manuscript-facing surface.",
            }
        )
    defined_method_labels = medical_surface_policy.extract_defined_method_labels(methods_manifest_payload)
    undefined_methodology_label_hits: list[dict[str, Any]] = []
    for hit in methodology_label_hits:
        label = str(hit["phrase"]).strip().lower()
        definition = defined_method_labels.get(label)
        if definition and definition.get("operational_definition") and definition.get("implementation_anchor"):
            continue
        undefined_methodology_label_hits.append(hit)
    public_evidence_surface_state = inspect_public_evidence_surface(
        state=state,
        derived_analysis_payload=derived_analysis_payload,
    )
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=state.study_root,
        evidence_ledger_path=state.evidence_ledger_path,
        review_ledger_path=state.review_ledger_path,
    )
    charter_expectation_closure_summary = build_charter_expectation_closure_summary(
        charter_contract_linkage=charter_contract_linkage,
        evidence_ledger_payload=evidence_ledger_payload,
        review_ledger_payload=load_json(state.review_ledger_path, default=None),
        evidence_ledger_path=state.evidence_ledger_path,
        review_ledger_path=state.review_ledger_path,
    )
    charter_expectation_closure_gaps = list(charter_expectation_closure_summary.get("blocking_items") or [])
    charter_expectation_closure_hits = [
        {
            "path": str(item["ledger_path"] or state.paper_root),
            "location": "file",
            "pattern_id": "charter_expectation_closure_blocker",
            "phrase": item["expectation_key"],
            "excerpt": (
                "Study charter expectation "
                f"`{item['expectation_text']}` is explicitly declared in {item['ledger_name']} "
                f"with closure status `{item['closure_status']}`."
            ),
        }
        for item in (charter_expectation_closure_summary.get("blocking_items") or [])
    ]
    public_data_surface_hits = public_evidence_surface_state.get("surface_hits") or []
    public_evidence_decision_hits = public_evidence_surface_state.get("decision_hits") or []
    medical_story_contract_structural_valid = (
        results_narrative_valid and figure_semantics_valid and claim_evidence_map_valid
    )
    medical_story_contract_valid = medical_story_contract_structural_valid and not analysis_plane_jargon_hits
    hits: list[dict[str, Any]] = []
    hits.extend(figure_catalog_hits)
    hits.extend(table_catalog_hits)
    hits.extend(required_display_catalog_hits)
    hits.extend(methods_manifest_hits)
    hits.extend(review_ledger_hits)
    hits.extend(statistical_reviewer_audit_hits)
    hits.extend(structured_disclosure_audit_hits)
    hits.extend(medical_manuscript_blueprint_hits)
    hits.extend(medical_prose_review_hits)
    hits.extend(results_narrative_hits)
    hits.extend(results_display_surface_hits)
    hits.extend(figure_semantics_hits)
    hits.extend(figure_layout_sidecar_hits)
    hits.extend(claim_evidence_map_hits)
    hits.extend(evidence_ledger_hits)
    hits.extend(derived_analysis_hits)
    hits.extend(reproducibility_hits)
    hits.extend(missing_data_policy_hits)
    hits.extend(introduction_structure_hits)
    hits.extend(methods_section_structure_hits)
    hits.extend(results_section_structure_hits)
    hits.extend(non_formal_question_hits)
    hits.extend(endpoint_note_hits)
    hits.extend(undefined_methodology_label_hits)
    hits.extend(results_narration_hits)
    hits.extend(numeric_trace_hits)
    hits.extend(analysis_plane_jargon_hits)
    hits.extend(publication_surface_residue_hits)
    hits.extend(medical_journal_prose_hits)
    hits.extend(forbidden_hits)
    hits.extend(public_data_surface_hits)
    hits.extend(public_evidence_decision_hits)
    hits.extend(charter_expectation_closure_hits)
    hits = unique_hits(hits)

    blockers: list[str] = []
    if forbidden_hits or publication_surface_residue_hits:
        blockers.append("forbidden_manuscript_terms_present")
    if not medical_story_contract_structural_valid:
        blockers.append("missing_medical_story_contract")
    if not figure_catalog_valid:
        blockers.append("figure_catalog_missing_or_incomplete")
    if not table_catalog_valid:
        blockers.append("table_catalog_missing_or_incomplete")
    if not required_display_catalog_coverage_valid:
        blockers.append("required_display_catalog_coverage_incomplete")
    ama_csl_present = state.ama_csl_path.exists()
    ama_defaults_present = ama_pdf_defaults_present(state.review_defaults_path, state.ama_csl_path)
    if not ama_defaults_present:
        blockers.append("ama_pdf_defaults_missing")
    if not methods_manifest_valid:
        blockers.append("methods_implementation_manifest_missing_or_incomplete")
    if not review_ledger_valid:
        blockers.append("review_ledger_missing_or_incomplete")
    if not statistical_reviewer_audit_valid:
        blockers.append("statistical_reviewer_audit_missing_or_incomplete")
    if not structured_disclosure_audit_valid:
        blockers.append("structured_disclosure_audit_missing_or_incomplete")
    if not medical_manuscript_blueprint_valid:
        blockers.append("medical_manuscript_blueprint_missing_or_incomplete")
    if not medical_prose_review_valid:
        blockers.append("ai_medical_prose_review_missing_or_incomplete")
    elif medical_journal_prose_ai_verdict in {"block", "revise"} or medical_journal_prose_blocking_hits:
        blockers.append("medical_journal_prose_style_not_met")
    if not results_narrative_valid:
        blockers.append("results_narrative_map_missing_or_incomplete")
    if results_display_surface_hits:
        blockers.append("results_display_surface_incomplete")
    if introduction_structure_hits:
        blockers.append("introduction_structure_missing_or_incomplete")
    if methods_section_structure_hits:
        blockers.append("methods_section_structure_missing_or_incomplete")
    if results_section_structure_hits:
        blockers.append("results_section_structure_missing_or_incomplete")
    if not figure_semantics_valid:
        blockers.append("figure_semantics_manifest_missing_or_incomplete")
    if figure_layout_sidecar_hits:
        blockers.append("figure_layout_sidecar_missing_or_incomplete")
    if not claim_evidence_map_valid:
        blockers.append("claim_evidence_map_missing_or_incomplete")
    if not numeric_trace_valid:
        blockers.append("numeric_trace_missing_or_incomplete")
    if not evidence_ledger_valid:
        blockers.append("evidence_ledger_missing_or_incomplete")
    if not derived_analysis_valid:
        blockers.append("derived_analysis_manifest_missing_or_incomplete")
    if not reproducibility_valid:
        blockers.append("manuscript_safe_reproducibility_supplement_missing_or_incomplete")
    if missing_data_policy_hits:
        blockers.append("missing_data_policy_inconsistent")
    if endpoint_caveat_sources and not endpoint_note_applied:
        blockers.append("endpoint_provenance_note_missing_or_unapplied")
    if undefined_methodology_label_hits:
        blockers.append("undefined_methodology_labels_present")
    if analysis_plane_jargon_hits:
        blockers.append("analysis_plane_jargon_present_on_manuscript_surface")
    if any(hit["pattern_id"] == "public_evidence_decisions_missing_or_incomplete" for hit in public_evidence_decision_hits):
        blockers.append("public_evidence_decisions_missing_or_incomplete")
    if any(
        hit["pattern_id"] == "paper_facing_public_data_without_earned_evidence"
        for hit in public_evidence_decision_hits
    ):
        blockers.append("paper_facing_public_data_without_earned_evidence")
    charter_contract_linkage_status = str(charter_contract_linkage.get("status") or "").strip()
    if charter_contract_linkage_status in {"study_charter_missing", "study_charter_invalid"}:
        blockers.append(charter_contract_linkage_status)
    if charter_expectation_closure_summary.get("blocking_items"):
        blockers.append("charter_expectation_closure_incomplete")
    blockers.extend(structured_reporting_checklist["blockers"])

    return {
        "schema_version": 1,
        "gate_kind": "medical_publication_surface_control",
        "generated_at": utc_now(),
        "quest_id": str(state.runtime_state.get("quest_id") or state.quest_root.name),
        "status": "blocked" if blockers else "clear",
        "recommended_action": (
            medical_surface_policy.BLOCKED_RECOMMENDED_ACTION
            if blockers
            else medical_surface_policy.CLEAR_RECOMMENDED_ACTION
        ),
        "blockers": blockers,
        "paper_root": str(state.paper_root),
        "study_root": str(state.study_root) if state.study_root is not None else None,
        "review_defaults_path": str(state.review_defaults_path),
        "ama_csl_path": str(state.ama_csl_path),
        "ama_csl_present": ama_csl_present,
        "ama_pdf_defaults_present": ama_defaults_present,
        "figure_catalog_path": str(state.figure_catalog_path),
        "figure_catalog_present": state.figure_catalog_path.exists(),
        "figure_catalog_valid": figure_catalog_valid,
        "table_catalog_path": str(state.table_catalog_path),
        "table_catalog_present": state.table_catalog_path.exists(),
        "table_catalog_valid": table_catalog_valid,
        "required_display_catalog_contract_path": str(reporting_contract_path),
        "required_display_catalog_contract_present": reporting_contract_path.exists(),
        "required_display_catalog_coverage_valid": required_display_catalog_coverage_valid,
        "methods_implementation_manifest_path": str(state.methods_implementation_manifest_path),
        "methods_implementation_manifest_present": state.methods_implementation_manifest_path.exists(),
        "methods_implementation_manifest_valid": methods_manifest_valid,
        "review_ledger_path": str(state.review_ledger_path),
        "review_ledger_present": state.review_ledger_path.exists(),
        "review_ledger_valid": review_ledger_valid,
        "statistical_reviewer_audit_path": str(state.statistical_reviewer_audit_path),
        "statistical_reviewer_audit_present": state.statistical_reviewer_audit_path.exists(),
        "statistical_reviewer_audit_valid": statistical_reviewer_audit_valid,
        "statistical_reviewer_audit_reason_code": statistical_reviewer_audit_validation["reason_code"],
        "structured_disclosure_audit_path": str(state.structured_disclosure_audit_path),
        "structured_disclosure_audit_present": state.structured_disclosure_audit_path.exists(),
        "structured_disclosure_audit_valid": structured_disclosure_audit_valid,
        "medical_manuscript_blueprint_path": str(state.medical_manuscript_blueprint_path),
        "medical_manuscript_blueprint_present": state.medical_manuscript_blueprint_path.exists(),
        "medical_manuscript_blueprint_valid": medical_manuscript_blueprint_valid,
        "medical_prose_review_path": str(state.medical_prose_review_path),
        "medical_prose_review_present": state.medical_prose_review_path.exists(),
        "medical_prose_review_valid": medical_prose_review_valid,
        "medical_prose_review_owner": (
            str(((medical_prose_review_payload or {}).get("assessment_provenance") or {}).get("owner") or "").strip()
            if isinstance(medical_prose_review_payload, dict)
            and isinstance(medical_prose_review_payload.get("assessment_provenance"), dict)
            else None
        ),
        "medical_journal_prose_ai_verdict": medical_journal_prose_ai_verdict,
        "medical_journal_prose_ai_route_back": medical_journal_prose_ai_route_back,
        "medical_prose_review_status": (
            str(medical_journal_prose_quality.get("status") or "").strip() or None
        ),
        "medical_prose_review_summary": (
            str(medical_journal_prose_quality.get("summary") or "").strip() or None
        ),
        "medical_prose_review_section_level_diagnosis": (
            dict(medical_journal_prose_quality.get("section_level_diagnosis") or {})
            if isinstance(medical_journal_prose_quality.get("section_level_diagnosis"), dict)
            else {}
        ),
        "medical_prose_review_representative_rewrites": [
            dict(item)
            for item in (medical_journal_prose_quality.get("representative_rewrites") or [])
            if isinstance(item, dict)
        ],
        "medical_prose_review_representative_bad_sentences": [
            str(item).strip()
            for item in (medical_journal_prose_quality.get("representative_bad_sentences") or [])
            if str(item).strip()
        ],
        "introduction_structure_valid": not introduction_structure_hits,
        "methods_section_structure_valid": not methods_section_structure_hits,
        "results_section_structure_valid": not results_section_structure_hits,
        "results_narrative_map_path": str(state.results_narrative_map_path),
        "results_narrative_map_present": state.results_narrative_map_path.exists(),
        "results_narrative_map_valid": results_narrative_valid,
        "medical_story_contract_structural_valid": medical_story_contract_structural_valid,
        "medical_story_contract_valid": medical_story_contract_valid,
        "manuscript_rhetoric_medical_publication_native": not analysis_plane_jargon_hits,
        "medical_journal_prose_style_valid": (
            medical_prose_review_valid
            and medical_journal_prose_ai_verdict == "clear"
            and not medical_journal_prose_blocking_hits
        ),
        "medical_journal_prose_mechanical_flag_count": len(medical_prose_reviewer_evidence_hits),
        "medical_journal_prose_blocking_hit_count": len(medical_journal_prose_blocking_hits),
        "medical_prose_reviewer_evidence_hit_count": len(medical_prose_reviewer_evidence_hits),
        "medical_prose_review_mechanical_safety_flags": medical_prose_reviewer_evidence_hits,
        "results_display_surface_valid": not results_display_surface_hits,
        "figure_semantics_manifest_path": str(state.figure_semantics_manifest_path),
        "figure_semantics_manifest_present": state.figure_semantics_manifest_path.exists(),
        "figure_semantics_manifest_valid": figure_semantics_valid,
        "claim_evidence_map_path": str(state.claim_evidence_map_path),
        "claim_evidence_map_present": state.claim_evidence_map_path.exists(),
        "claim_evidence_map_valid": claim_evidence_map_valid,
        "numeric_trace_path": str(state.numeric_trace_path),
        "numeric_trace_present": state.numeric_trace_path.exists(),
        "numeric_trace_valid": numeric_trace_valid,
        "evidence_ledger_path": str(state.evidence_ledger_path),
        "evidence_ledger_present": state.evidence_ledger_path.exists(),
        "evidence_ledger_valid": evidence_ledger_valid,
        "derived_analysis_manifest_path": str(state.derived_analysis_manifest_path),
        "derived_analysis_manifest_present": state.derived_analysis_manifest_path.exists(),
        "derived_analysis_manifest_valid": derived_analysis_valid,
        "reproducibility_supplement_path": str(state.reproducibility_supplement_path),
        "reproducibility_supplement_present": state.reproducibility_supplement_path.exists(),
        "reproducibility_supplement_valid": reproducibility_valid,
        "missing_data_policy_consistent": not missing_data_policy_hits,
        "endpoint_provenance_note_path": str(state.endpoint_provenance_note_path),
        "endpoint_provenance_note_present": state.endpoint_provenance_note_path.exists(),
        "endpoint_provenance_note_valid": endpoint_note_valid,
        "endpoint_provenance_note_applied": endpoint_note_applied,
        "endpoint_provenance_caveat_source_count": len(endpoint_caveat_sources),
        "paper_pdf_path": str(state.paper_pdf_path),
        "paper_pdf_present": state.paper_pdf_path.exists(),
        "charter_contract_linkage": charter_contract_linkage,
        "charter_expectation_closure_summary": charter_expectation_closure_summary,
        "charter_expectation_closure_gaps": charter_expectation_closure_gaps,
        "structured_reporting_checklist": structured_reporting_checklist,
        "public_data_anchor_count": int(public_evidence_surface_state.get("anchor_count") or 0),
        "public_data_surface_reference_count": len(public_data_surface_hits),
        "public_evidence_decision_count": int(public_evidence_surface_state.get("decision_count") or 0),
        "public_evidence_earned_count": int(public_evidence_surface_state.get("earned_count") or 0),
        "analysis_plane_jargon_hit_count": len(analysis_plane_jargon_hits),
        "medical_journal_prose_style_hit_count": len(medical_journal_prose_hits),
        "forbidden_hit_count": len(hits),
        "undefined_methodology_label_hit_count": len(undefined_methodology_label_hits),
        "results_narration_hit_count": len(results_narration_hits),
        "non_formal_question_hit_count": len(non_formal_question_hits),
        "top_hits": hits[:80],
    }


def render_surface_markdown(report: dict[str, Any]) -> str:
    charter_contract_linkage = report.get("charter_contract_linkage") or {}
    charter_expectation_closure_summary = report.get("charter_expectation_closure_summary") or {}
    study_charter_ref = charter_contract_linkage.get("study_charter_ref") or {}
    paper_quality_contract = charter_contract_linkage.get("paper_quality_contract") or {}
    ledger_linkages = charter_contract_linkage.get("ledger_linkages") or {}
    evidence_linkage = ledger_linkages.get("evidence_ledger") or {}
    review_linkage = ledger_linkages.get("review_ledger") or {}
    lines = [
        "# Medical Publication Surface Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_id: `{report['quest_id']}`",
        f"- status: `{report['status']}`",
        f"- recommended_action: `{report['recommended_action']}`",
        f"- blockers: `{', '.join(report.get('blockers') or ['none'])}`",
        f"- ama_csl_present: `{report['ama_csl_present']}`",
        f"- ama_pdf_defaults_present: `{report['ama_pdf_defaults_present']}`",
        f"- figure_catalog_present: `{report['figure_catalog_present']}`",
        f"- figure_catalog_valid: `{report['figure_catalog_valid']}`",
        f"- table_catalog_present: `{report['table_catalog_present']}`",
        f"- table_catalog_valid: `{report['table_catalog_valid']}`",
        f"- required_display_catalog_contract_present: `{report.get('required_display_catalog_contract_present', False)}`",
        f"- required_display_catalog_coverage_valid: `{report.get('required_display_catalog_coverage_valid', True)}`",
        f"- methods_implementation_manifest_present: `{report['methods_implementation_manifest_present']}`",
        f"- methods_implementation_manifest_valid: `{report['methods_implementation_manifest_valid']}`",
        f"- review_ledger_present: `{report['review_ledger_present']}`",
        f"- review_ledger_valid: `{report['review_ledger_valid']}`",
        f"- medical_manuscript_blueprint_present: `{report.get('medical_manuscript_blueprint_present', False)}`",
        f"- medical_manuscript_blueprint_valid: `{report.get('medical_manuscript_blueprint_valid', False)}`",
        f"- medical_prose_review_present: `{report.get('medical_prose_review_present', False)}`",
        f"- medical_prose_review_valid: `{report.get('medical_prose_review_valid', False)}`",
        f"- medical_journal_prose_ai_verdict: `{report.get('medical_journal_prose_ai_verdict') or 'none'}`",
        f"- introduction_structure_valid: `{report.get('introduction_structure_valid', True)}`",
        f"- methods_section_structure_valid: `{report.get('methods_section_structure_valid', True)}`",
        f"- results_section_structure_valid: `{report.get('results_section_structure_valid', True)}`",
        f"- results_narrative_map_present: `{report['results_narrative_map_present']}`",
        f"- results_narrative_map_valid: `{report['results_narrative_map_valid']}`",
        f"- medical_story_contract_valid: `{report.get('medical_story_contract_valid', False)}`",
        (
            f"- manuscript_rhetoric_medical_publication_native: "
            f"`{report.get('manuscript_rhetoric_medical_publication_native', True)}`"
        ),
        f"- medical_journal_prose_style_valid: `{report.get('medical_journal_prose_style_valid', True)}`",
        f"- figure_semantics_manifest_present: `{report['figure_semantics_manifest_present']}`",
        f"- figure_semantics_manifest_valid: `{report['figure_semantics_manifest_valid']}`",
        f"- claim_evidence_map_present: `{report.get('claim_evidence_map_present', False)}`",
        f"- claim_evidence_map_valid: `{report.get('claim_evidence_map_valid', False)}`",
        f"- evidence_ledger_present: `{report.get('evidence_ledger_present', False)}`",
        f"- evidence_ledger_valid: `{report.get('evidence_ledger_valid', False)}`",
        f"- derived_analysis_manifest_present: `{report['derived_analysis_manifest_present']}`",
        f"- derived_analysis_manifest_valid: `{report['derived_analysis_manifest_valid']}`",
        f"- reproducibility_supplement_present: `{report['reproducibility_supplement_present']}`",
        f"- reproducibility_supplement_valid: `{report['reproducibility_supplement_valid']}`",
        f"- missing_data_policy_consistent: `{report['missing_data_policy_consistent']}`",
        f"- endpoint_provenance_note_present: `{report['endpoint_provenance_note_present']}`",
        f"- endpoint_provenance_note_valid: `{report['endpoint_provenance_note_valid']}`",
        f"- endpoint_provenance_note_applied: `{report['endpoint_provenance_note_applied']}`",
        "",
        "## Charter Contract Linkage",
        "",
        f"- charter_contract_linkage_status: `{charter_contract_linkage.get('status', 'study_root_unresolved')}`",
        f"- study_charter_ref: `{study_charter_ref.get('charter_id')}`",
        f"- study_charter_path: `{study_charter_ref.get('artifact_path')}`",
        f"- paper_quality_contract_present: `{paper_quality_contract.get('present', False)}`",
        f"- evidence_ledger_linkage_status: `{evidence_linkage.get('status', 'study_root_unresolved')}`",
        f"- review_ledger_linkage_status: `{review_linkage.get('status', 'study_root_unresolved')}`",
        f"- charter_expectation_closure_status: `{charter_expectation_closure_summary.get('status', 'clear')}`",
        f"- charter_expectation_declared_record_count: `{charter_expectation_closure_summary.get('declared_record_count', 0)}`",
        f"- charter_expectation_closed_item_count: `{charter_expectation_closure_summary.get('closed_item_count', 0)}`",
        f"- charter_expectation_advisory_item_count: `{len(charter_expectation_closure_summary.get('advisory_items') or [])}`",
        f"- structured_reporting_checklist_status: `{(report.get('structured_reporting_checklist') or {}).get('status', 'not_available')}`",
        f"- public_data_anchor_count: `{report.get('public_data_anchor_count', 0)}`",
        f"- public_data_surface_reference_count: `{report.get('public_data_surface_reference_count', 0)}`",
        f"- public_evidence_decision_count: `{report.get('public_evidence_decision_count', 0)}`",
        f"- public_evidence_earned_count: `{report.get('public_evidence_earned_count', 0)}`",
        f"- forbidden_hit_count: `{report['forbidden_hit_count']}`",
        f"- medical_journal_prose_style_hit_count: `{report.get('medical_journal_prose_style_hit_count', 0)}`",
        f"- undefined_methodology_label_hit_count: `{report['undefined_methodology_label_hit_count']}`",
        f"- results_narration_hit_count: `{report['results_narration_hit_count']}`",
        f"- non_formal_question_hit_count: `{report.get('non_formal_question_hit_count', 0)}`",
        "",
        "## Charter Expectation Closure Gaps",
        "",
    ]
    charter_expectation_closure_gaps = report.get("charter_expectation_closure_gaps") or []
    if not charter_expectation_closure_gaps:
        lines.append("- none")
    else:
        for item in charter_expectation_closure_gaps:
            note_clause = f"; note={item['note']}" if item.get("note") else ""
            lines.append(
                f"- `{item['expectation_text']}` (expectation_key=`{item['expectation_key']}`, "
                f"ledger=`{item['ledger_name']}`, closure_status=`{item['closure_status']}`, "
                f"record_count=`{item['record_count']}`, "
                f"contract_json_pointer=`{item['contract_json_pointer']}`{note_clause})"
            )
    lines.extend(
        [
            "",
            "## Charter Expectation Closure Summary",
            "",
        ]
    )
    for category in charter_expectation_closure_summary.get("categories") or []:
        lines.extend(
            [
                f"### {category['label']}",
                "",
                f"- ledger_name: `{category['ledger_name']}`",
                f"- charter_item_count: `{category['charter_item_count']}`",
                f"- declared_count: `{category['declared_count']}`",
                f"- closed_count: `{category['closed_count']}`",
                f"- blocker_count: `{category['blocker_count']}`",
                f"- advisory_count: `{category.get('advisory_count', 0)}`",
            ]
        )
        category_items = category.get("items") or []
        if not category_items:
            lines.append("- none")
        else:
            for item in category_items:
                note_clause = f"; note={item['note']}" if item.get("note") else ""
                lines.append(
                    f"- `{item['expectation_text']}` -> `{item['closure_status']}` "
                    f"(ledger=`{item['ledger_name']}`, blocker=`{item['blocker']}`{note_clause})"
                )
        lines.append("")
    lines.extend(
        [
            "## Top Hits",
            "",
        ]
    )
    hits = report.get("top_hits") or []
    if not hits:
        lines.append("- none")
    else:
        for hit in hits:
            lines.append(f"- `{hit['phrase']}` at `{hit['path']}` ({hit['location']}): {hit['excerpt']}")
    return "\n".join(lines) + "\n"




from .controller import (  # noqa: E402
    main,
    parse_args,
    run_controller,
    write_surface_files,
)
