from .shared import *

def inspect_required_json_contract(
    *,
    path: Path,
    validator,
    pattern_id: str,
    label: str,
    payload_override: Any | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    if not path.exists():
        return False, [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": pattern_id,
                "phrase": path.name,
                "excerpt": f"Required {label} is missing.",
            }
        ]

    payload = payload_override if payload_override is not None else load_json(path, default=None)
    errors = validator(payload)
    if errors:
        return False, [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": pattern_id,
                "phrase": path.name,
                "excerpt": "; ".join(errors),
            }
        ]
    return True, []


def inspect_required_text_contract(
    *,
    path: Path,
    validator,
    pattern_id: str,
    label: str,
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    if not path.exists():
        return False, None, [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": pattern_id,
                "phrase": path.name,
                "excerpt": f"Required {label} is missing.",
            }
        ]
    text = path.read_text(encoding="utf-8")
    errors = validator(text)
    if errors:
        return False, text, [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": pattern_id,
                "phrase": path.name,
                "excerpt": "; ".join(errors),
            }
        ]
    return True, text, []


def load_required_display_catalog_ids(path: Path) -> tuple[set[str], set[str]]:
    if not path.exists():
        return set(), set()
    payload = load_json(path, default={}) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"medical_reporting_contract at {path} must be a JSON object")
    figure_ids: set[str] = set()
    table_ids: set[str] = set()
    display_shell_plan = payload.get("display_shell_plan")
    if not isinstance(display_shell_plan, list):
        return figure_ids, table_ids
    for item in display_shell_plan:
        if not isinstance(item, dict):
            continue
        catalog_id = str(item.get("catalog_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()
        if not catalog_id:
            continue
        if display_kind == "figure":
            figure_ids.add(catalog_id)
        elif display_kind == "table":
            table_ids.add(catalog_id)
    return figure_ids, table_ids


def load_display_catalog_story_roles(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = load_json(path, default={}) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"medical_reporting_contract at {path} must be a JSON object")
    story_roles: dict[str, str] = {}
    role_sources = []
    display_shell_plan = payload.get("display_shell_plan")
    if isinstance(display_shell_plan, list):
        role_sources.append(display_shell_plan)
    recommended_main_text_figures = payload.get("recommended_main_text_figures")
    if isinstance(recommended_main_text_figures, list):
        role_sources.append(recommended_main_text_figures)
    for source in role_sources:
        for item in source:
            if not isinstance(item, dict):
                continue
            catalog_id = str(item.get("catalog_id") or "").strip()
            if not catalog_id:
                continue
            story_role = str(item.get("story_role") or "").strip() or display_story_role_for_requirement_key(
                item.get("requirement_key")
            )
            if story_role:
                story_roles[catalog_id] = story_role
    return story_roles


def figure_ids_from_catalog(path: Path, *, include_all_roles: bool = False) -> set[str]:
    payload = load_json(path, default={}) or {}
    figure_ids: set[str] = set()
    for item in payload.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        if not include_all_roles and str(item.get("paper_role") or "").strip() != "main_text":
            continue
        figure_id = str(item.get("figure_id") or "").strip()
        if figure_id:
            figure_ids.add(figure_id)
    return figure_ids


def table_ids_from_catalog(path: Path) -> set[str]:
    payload = load_json(path, default={}) or {}
    table_ids: set[str] = set()
    for item in payload.get("tables", []) or []:
        if not isinstance(item, dict):
            continue
        table_id = str(item.get("table_id") or "").strip()
        if table_id:
            table_ids.add(table_id)
    return table_ids


def inspect_results_narrative_display_items(
    *,
    path: Path,
    payload: object,
    figure_ids: set[str],
    table_ids: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    known_display_items = figure_ids | table_ids
    hits: list[dict[str, Any]] = []
    for index, section in enumerate(payload.get("sections", []) or []):
        if not isinstance(section, dict):
            continue
        for item in section.get("supporting_display_items", []) or []:
            display_item = str(item or "").strip()
            if not display_item or display_item in known_display_items:
                continue
            hits.append(
                {
                    "path": str(path),
                    "location": f"sections[{index}].supporting_display_items",
                    "pattern_id": "results_narrative_map_unknown_display_item",
                    "phrase": display_item,
                    "excerpt": f"Supporting display item `{display_item}` does not map to the current figure/table catalog.",
                }
            )
    return hits


def inspect_results_narrative_figure_coverage(
    *,
    path: Path,
    payload: object,
    figure_ids: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    referenced_figures: set[str] = set()
    for section in payload.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for item in section.get("supporting_display_items", []) or []:
            display_item = str(item or "").strip()
            if display_item in figure_ids:
                referenced_figures.add(display_item)
    hits: list[dict[str, Any]] = []
    missing = sorted(figure_ids - referenced_figures)
    for figure_id in missing:
        hits.append(
            {
                "path": str(path),
                "location": "sections[].supporting_display_items",
                "pattern_id": "results_narrative_map_missing_main_figure_reference",
                "phrase": figure_id,
                "excerpt": f"Main-text figure `{figure_id}` is not cited by any results section in the results narrative map.",
            }
        )
    return hits


def inspect_results_display_surface_coverage(
    *,
    path: Path,
    payload: object,
    display_story_roles: dict[str, str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    sections_with_display_support: list[tuple[int, str, list[str], bool]] = []
    for index, section in enumerate(payload.get("sections", []) or []):
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("section_id") or section.get("section_title") or index).strip() or str(index)
        supporting_items = [
            str(item or "").strip()
            for item in (section.get("supporting_display_items") or [])
            if str(item or "").strip()
        ]
        known_items = [item for item in supporting_items if item in display_story_roles]
        if not known_items:
            continue
        has_result_facing_display = any(display_story_roles.get(item) != "study_setup" for item in known_items)
        sections_with_display_support.append((index, section_id, known_items, has_result_facing_display))

    first_result_facing_index = next(
        (index for index, _, _, has_result_facing_display in sections_with_display_support if has_result_facing_display),
        None,
    )
    hits: list[dict[str, Any]] = []
    for index, section_id, known_items, has_result_facing_display in sections_with_display_support:
        if has_result_facing_display:
            continue
        if first_result_facing_index is not None and index < first_result_facing_index:
            continue
        hits.append(
            {
                "path": str(path),
                "location": f"sections[{index}].supporting_display_items",
                "pattern_id": "results_narrative_map_setup_only_display_support",
                "phrase": section_id,
                "excerpt": (
                    f"Results section `{section_id}` is still supported only by study-setup displays "
                    f"({', '.join(known_items)}). Add at least one result-facing figure or table for the section's main finding."
                ),
            }
        )
    return hits


def inspect_figure_semantics_coverage(
    *,
    path: Path,
    payload: object,
    figure_ids: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    semantic_ids = {
        str(item.get("figure_id") or "").strip()
        for item in payload.get("figures", []) or []
        if isinstance(item, dict) and str(item.get("figure_id") or "").strip()
    }
    hits: list[dict[str, Any]] = []
    missing = sorted(figure_ids - semantic_ids)
    for figure_id in missing:
        hits.append(
            {
                "path": str(path),
                "location": "figures",
                "pattern_id": "figure_semantics_missing_figure_coverage",
                "phrase": figure_id,
                "excerpt": f"Main-text figure `{figure_id}` is present in the figure catalog but missing from the figure semantics manifest.",
            }
        )
    return hits


def inspect_claim_evidence_display_bindings(
    *,
    path: Path,
    payload: object,
    known_display_items: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    hits: list[dict[str, Any]] = []
    for index, claim in enumerate(payload.get("claims", []) or []):
        if not isinstance(claim, dict):
            continue
        paper_role = str(claim.get("paper_role") or "").strip()
        status = str(claim.get("status") or "").strip().lower()
        if paper_role != "main_text":
            continue
        if status.startswith("unsupported") or status.startswith("deferred"):
            continue
        for item in claim.get("display_bindings", []) or []:
            display_item = str(item or "").strip()
            if not display_item or display_item in known_display_items:
                continue
            hits.append(
                {
                    "path": str(path),
                    "location": f"claims[{index}].display_bindings",
                    "pattern_id": "claim_evidence_map_missing_display_binding",
                    "phrase": display_item,
                    "excerpt": (
                        f"Main-text claim `{str(claim.get('claim_id') or index)}` still binds display item "
                        f"`{display_item}`, but that item is not materialized in the current figure/table catalog."
                    ),
                }
            )
    return hits


def inspect_figure_semantic_renderer_alignment(
    *,
    path: Path,
    figure_catalog_payload: object,
    figure_semantics_payload: object,
) -> list[dict[str, Any]]:
    if not isinstance(figure_catalog_payload, dict) or not isinstance(figure_semantics_payload, dict):
        return []
    semantics_by_id = {
        str(item.get("figure_id") or "").strip(): item
        for item in figure_semantics_payload.get("figures", []) or []
        if isinstance(item, dict) and str(item.get("figure_id") or "").strip()
    }
    hits: list[dict[str, Any]] = []
    for figure in figure_catalog_payload.get("figures", []) or []:
        if not isinstance(figure, dict):
            continue
        if str(figure.get("paper_role") or "").strip() != "main_text":
            continue
        figure_id = str(figure.get("figure_id") or "").strip()
        if not figure_id:
            continue
        semantics_entry = semantics_by_id.get(figure_id)
        if not isinstance(semantics_entry, dict):
            continue
        renderer_contract = semantics_entry.get("renderer_contract")
        if not isinstance(renderer_contract, dict):
            hits.append(
                {
                    "path": str(path),
                    "location": f"figures[{figure_id}].renderer_contract",
                    "pattern_id": "figure_semantics_renderer_contract_missing",
                    "phrase": figure_id,
                    "excerpt": f"Figure semantics entry `{figure_id}` is missing renderer_contract.",
                }
            )
            continue
        expected_pairs = (
            ("template_id", "template_id"),
            ("renderer_family", "renderer_family"),
            ("layout_qc_profile", "qc_profile"),
        )
        for semantics_field, catalog_field in expected_pairs:
            expected_value = str(renderer_contract.get(semantics_field) or "").strip()
            observed_value = str(figure.get(catalog_field) or "").strip()
            if expected_value and observed_value == expected_value:
                continue
            hits.append(
                {
                    "path": str(path),
                    "location": f"figures[{figure_id}].renderer_contract.{semantics_field}",
                    "pattern_id": "figure_semantics_renderer_contract_mismatch",
                    "phrase": figure_id,
                    "excerpt": (
                        f"Figure `{figure_id}` catalog field `{catalog_field}` is `{observed_value}` but "
                        f"renderer_contract expects `{expected_value}`."
                    ),
                }
            )
    return hits


def inspect_required_display_catalog_coverage(
    *,
    reporting_contract_path: Path,
    figure_ids: set[str],
    table_ids: set[str],
) -> tuple[bool, list[dict[str, Any]]]:
    try:
        required_figure_ids, required_table_ids = load_required_display_catalog_ids(reporting_contract_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return False, [
            {
                "path": str(reporting_contract_path),
                "location": "file",
                "pattern_id": "required_display_catalog_contract_invalid",
                "phrase": reporting_contract_path.name,
                "excerpt": str(exc),
            }
        ]
    hits: list[dict[str, Any]] = []
    for figure_id in sorted(required_figure_ids - figure_ids):
        hits.append(
            {
                "path": str(reporting_contract_path),
                "location": "display_shell_plan",
                "pattern_id": "required_display_catalog_item_missing",
                "phrase": figure_id,
                "excerpt": (
                    f"Required figure catalog item `{figure_id}` declared by "
                    "medical_reporting_contract.display_shell_plan is missing from the current figure catalog."
                ),
            }
        )
    for table_id in sorted(required_table_ids - table_ids):
        hits.append(
            {
                "path": str(reporting_contract_path),
                "location": "display_shell_plan",
                "pattern_id": "required_display_catalog_item_missing",
                "phrase": table_id,
                "excerpt": (
                    f"Required table catalog item `{table_id}` declared by "
                    "medical_reporting_contract.display_shell_plan is missing from the current table catalog."
                ),
            }
        )
    return not hits, hits


def inspect_derived_analysis_links(
    *,
    path: Path,
    payload: object,
    known_display_items: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    hits: list[dict[str, Any]] = []
    for index, analysis in enumerate(payload.get("analyses", []) or []):
        if not isinstance(analysis, dict):
            continue
        for item in analysis.get("linked_display_items", []) or []:
            display_item = str(item or "").strip()
            if not display_item or display_item in known_display_items:
                continue
            hits.append(
                {
                    "path": str(path),
                    "location": f"analyses[{index}].linked_display_items",
                    "pattern_id": "derived_analysis_unknown_display_item",
                    "phrase": display_item,
                    "excerpt": f"Derived analysis display item `{display_item}` does not map to the current figure/table catalog.",
                }
            )
    return hits


def inspect_missing_data_policy_consistency(
    *,
    methods_path: Path,
    methods_payload: object,
    derived_analysis_path: Path,
    derived_analysis_payload: object,
    reproducibility_path: Path,
    reproducibility_payload: object,
) -> list[dict[str, Any]]:
    if not isinstance(methods_payload, dict):
        return []
    study_design = methods_payload.get("study_design")
    if not isinstance(study_design, dict):
        return []
    reference_policy_id = str(study_design.get("missing_data_policy_id") or "").strip()
    if not reference_policy_id:
        return []

    hits: list[dict[str, Any]] = []

    reproducibility_policy_id = ""
    if isinstance(reproducibility_payload, dict):
        reproducibility_policy_id = str(reproducibility_payload.get("missing_data_policy_id") or "").strip()
    if reproducibility_policy_id and reproducibility_policy_id != reference_policy_id:
        hits.append(
            {
                "path": str(reproducibility_path),
                "location": "missing_data_policy_id",
                "pattern_id": "missing_data_policy_inconsistent",
                "phrase": reproducibility_policy_id,
                "excerpt": (
                    f"Reproducibility supplement missing_data_policy_id `{reproducibility_policy_id}` "
                    f"does not match study_design missing_data_policy_id `{reference_policy_id}`."
                ),
            }
        )

    if not isinstance(derived_analysis_payload, dict):
        return hits
    for index, analysis in enumerate(derived_analysis_payload.get("analyses", []) or []):
        if not isinstance(analysis, dict):
            continue
        analysis_policy_id = str(analysis.get("missing_data_policy_id") or "").strip()
        if not analysis_policy_id or analysis_policy_id == reference_policy_id:
            continue
        hits.append(
            {
                "path": str(derived_analysis_path),
                "location": f"analyses[{index}].missing_data_policy_id",
                "pattern_id": "missing_data_policy_inconsistent",
                "phrase": analysis_policy_id,
                "excerpt": (
                    f"Derived analysis missing_data_policy_id `{analysis_policy_id}` does not match "
                    f"study_design missing_data_policy_id `{reference_policy_id}`."
                ),
            }
        )
    return hits


def discover_endpoint_provenance_caveat_sources(quest_root: Path) -> list[dict[str, str]]:
    candidate_paths = [
        *quest_root.glob("baselines/**/verification.md"),
        quest_root / "artifacts" / "intake" / "state_audit.md",
        quest_root / "plan.md",
        quest_root / "protocol.md",
        quest_root / "brief.md",
    ]
    sources: list[dict[str, str]] = []
    pattern = re.compile(
        r"`(?P<endpoint>[A-Za-z0-9_]+)`.*?(?:(?:provenance caveat|caveat).*?(?:3-month MRI|MRI provenance)|(?:3-month MRI|MRI provenance).*?(?:provenance caveat|caveat))",
        flags=re.IGNORECASE,
    )
    for path in candidate_paths:
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = pattern.search(line)
            if match:
                sources.append(
                    {
                        "path": str(path),
                        "location": f"line {line_number}",
                        "endpoint_name": match.group("endpoint"),
                        "excerpt": line.strip(),
                    }
                )
    return sources


def read_review_defaults(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def ama_pdf_defaults_present(review_defaults_path: Path, ama_csl_path: Path) -> bool:
    if not review_defaults_path.exists() or not ama_csl_path.exists():
        return False
    defaults_text = read_review_defaults(review_defaults_path)
    return bool(medical_surface_policy.ama_defaults_regex().search(defaults_text))

