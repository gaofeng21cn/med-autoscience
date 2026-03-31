from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.runtime_protocol import paper_artifacts, quest_state, user_message
from med_autoscience.runtime_transport import medicaldeepscientist as medicaldeepscientist_transport


@dataclass
class SurfaceState:
    quest_root: Path
    runtime_state: dict[str, Any]
    paper_root: Path
    review_defaults_path: Path
    ama_csl_path: Path
    paper_pdf_path: Path
    draft_path: Path
    review_manuscript_path: Path
    figure_catalog_path: Path
    table_catalog_path: Path
    methods_implementation_manifest_path: Path
    results_narrative_map_path: Path
    figure_semantics_manifest_path: Path
    derived_analysis_manifest_path: Path
    reproducibility_supplement_path: Path
    endpoint_provenance_note_path: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


def build_surface_state(quest_root: Path) -> SurfaceState:
    runtime_state = quest_state.load_runtime_state(quest_root) or {}
    paper_root = paper_artifacts.resolve_latest_paper_root(quest_root)
    return SurfaceState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        paper_root=paper_root,
        review_defaults_path=paper_root / "latex" / "review_defaults.yaml",
        ama_csl_path=paper_root / "latex" / "american-medical-association.csl",
        paper_pdf_path=paper_root / "paper.pdf",
        draft_path=paper_root / "draft.md",
        review_manuscript_path=paper_root / "build" / "review_manuscript.md",
        figure_catalog_path=paper_root / "figures" / "figure_catalog.json",
        table_catalog_path=paper_root / "tables" / "table_catalog.json",
        methods_implementation_manifest_path=paper_root / medical_surface_policy.METHODS_IMPLEMENTATION_MANIFEST_BASENAME,
        results_narrative_map_path=paper_root / medical_surface_policy.RESULTS_NARRATIVE_MAP_BASENAME,
        figure_semantics_manifest_path=paper_root / medical_surface_policy.FIGURE_SEMANTICS_MANIFEST_BASENAME,
        derived_analysis_manifest_path=paper_root / medical_surface_policy.DERIVED_ANALYSIS_MANIFEST_BASENAME,
        reproducibility_supplement_path=paper_root / medical_surface_policy.REPRODUCIBILITY_SUPPLEMENT_BASENAME,
        endpoint_provenance_note_path=paper_root / medical_surface_policy.ENDPOINT_PROVENANCE_NOTE_BASENAME,
    )


def excerpt_around(text: str, start: int, end: int, *, width: int = 96) -> str:
    left = max(0, start - width // 2)
    right = min(len(text), end + width // 2)
    excerpt = text[left:right].replace("\n", " ").strip()
    return excerpt


def scan_text_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern_id, phrase, compiled in medical_surface_policy.get_forbidden_patterns():
            for match in compiled.finditer(line):
                hits.append(
                    {
                        "path": str(path),
                        "location": f"line {line_number}",
                        "pattern_id": pattern_id,
                        "phrase": phrase,
                        "excerpt": excerpt_around(line, match.start(), match.end()),
                    }
                )
    return hits


TEXT_ASSET_SUFFIXES = {".svg", ".md", ".txt", ".html", ".xml", ".json"}


def resolve_paper_relative_path(paper_root: Path, raw_path: str) -> Path:
    candidate = Path(str(raw_path).strip())
    if candidate.is_absolute():
        return candidate
    if candidate.parts and candidate.parts[0] == "paper":
        return (paper_root.parent / candidate).resolve()
    return (paper_root / candidate).resolve()


def discover_figure_text_assets(paper_root: Path, figure_catalog_path: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    generated_root = paper_root / "figures" / "generated"
    if generated_root.exists():
        for path in sorted(generated_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_ASSET_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(resolved)

    payload = load_json(figure_catalog_path, default={}) or {}
    for item in payload.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("paper_role") or "").strip() != "main_text":
            continue
        for key in ("export_paths", "asset_paths"):
            values = item.get(key)
            if not isinstance(values, list):
                continue
            for raw_path in values:
                if not isinstance(raw_path, str) or not raw_path.strip():
                    continue
                resolved = resolve_paper_relative_path(paper_root, raw_path)
                if resolved.suffix.lower() not in TEXT_ASSET_SUFFIXES:
                    continue
                if resolved in seen:
                    continue
                seen.add(resolved)
                candidates.append(resolved)
    return candidates


def scan_catalog_strings(path: Path, *, collection_key: str) -> list[dict[str, Any]]:
    payload = load_json(path, default={}) or {}
    hits: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get(collection_key, []) or []):
        for field in ("title", "caption", "manuscript_purpose", "note", "next_action"):
            value = str(item.get(field) or "")
            if not value:
                continue
            hits.extend(scan_string_value(path, f"{collection_key}[{index}].{field}", value))
        if collection_key == "figures":
            for panel_index, panel in enumerate(item.get("panel_plan", []) or []):
                for field in ("title", "focus"):
                    value = str(panel.get(field) or "")
                    if not value:
                        continue
                    hits.extend(
                        scan_string_value(
                            path,
                            f"{collection_key}[{index}].panel_plan[{panel_index}].{field}",
                            value,
                        )
                    )
        summary = item.get("summary")
        if isinstance(summary, dict):
            for field in ("purpose", "must_highlight", "scope_rule"):
                value = str(summary.get(field) or "")
                if not value:
                    continue
                hits.extend(scan_string_value(path, f"{collection_key}[{index}].summary.{field}", value))
    return hits


def scan_string_value(path: Path, location: str, value: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for pattern_id, phrase, compiled in medical_surface_policy.get_forbidden_patterns():
        for match in compiled.finditer(value):
            hits.append(
                {
                    "path": str(path),
                    "location": location,
                    "pattern_id": pattern_id,
                    "phrase": phrase,
                    "excerpt": excerpt_around(value, match.start(), match.end()),
                }
            )
    return hits


def scan_results_narration_text_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    hits: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern_id, phrase, compiled in medical_surface_policy.get_results_narration_patterns():
            for match in compiled.finditer(line):
                hits.append(
                    {
                        "path": str(path),
                        "location": f"line {line_number}",
                        "pattern_id": pattern_id,
                        "phrase": line[match.start() : match.end()],
                        "excerpt": excerpt_around(line, match.start(), match.end()),
                    }
                )
    return hits


def scan_methodology_labels_text_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    hits: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern_id, phrase, compiled in medical_surface_policy.get_methodology_label_patterns():
            for match in compiled.finditer(line):
                hits.append(
                    {
                        "path": str(path),
                        "location": f"line {line_number}",
                        "pattern_id": f"methodology_label::{pattern_id}",
                        "phrase": line[match.start() : match.end()],
                        "excerpt": excerpt_around(line, match.start(), match.end()),
                    }
                )
    return hits


def inspect_required_json_contract(
    *,
    path: Path,
    validator,
    pattern_id: str,
    label: str,
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

    payload = load_json(path, default=None)
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


def figure_ids_from_catalog(path: Path) -> set[str]:
    payload = load_json(path, default={}) or {}
    figure_ids: set[str] = set()
    for item in payload.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("paper_role") or "").strip() != "main_text":
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


def unique_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for hit in hits:
        key = (hit["path"], hit["location"], hit["pattern_id"], hit["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


def build_surface_report(state: SurfaceState) -> dict[str, Any]:
    forbidden_hits: list[dict[str, Any]] = []
    forbidden_hits.extend(scan_text_file(state.draft_path))
    forbidden_hits.extend(scan_text_file(state.review_manuscript_path))
    forbidden_hits.extend(scan_catalog_strings(state.figure_catalog_path, collection_key="figures"))
    forbidden_hits.extend(scan_catalog_strings(state.table_catalog_path, collection_key="tables"))
    for path in discover_figure_text_assets(state.paper_root, state.figure_catalog_path):
        forbidden_hits.extend(scan_text_file(path))
    figure_ids = figure_ids_from_catalog(state.figure_catalog_path)
    table_ids = table_ids_from_catalog(state.table_catalog_path)
    methods_manifest_valid, methods_manifest_hits = inspect_required_json_contract(
        path=state.methods_implementation_manifest_path,
        validator=medical_surface_policy.validate_methods_implementation_manifest,
        pattern_id="methods_implementation_manifest",
        label="medical methods implementation manifest",
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
    figure_semantics_payload = load_json(state.figure_semantics_manifest_path, default=None)
    figure_semantics_coverage_hits = inspect_figure_semantics_coverage(
        path=state.figure_semantics_manifest_path,
        payload=figure_semantics_payload,
        figure_ids=figure_ids,
    )
    if figure_semantics_coverage_hits:
        figure_semantics_valid = False
        figure_semantics_hits.extend(figure_semantics_coverage_hits)
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
    results_narration_hits: list[dict[str, Any]] = []
    results_narration_hits.extend(scan_results_narration_text_file(state.draft_path))
    results_narration_hits.extend(scan_results_narration_text_file(state.review_manuscript_path))
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
    hits: list[dict[str, Any]] = []
    hits.extend(methods_manifest_hits)
    hits.extend(results_narrative_hits)
    hits.extend(figure_semantics_hits)
    hits.extend(derived_analysis_hits)
    hits.extend(reproducibility_hits)
    hits.extend(missing_data_policy_hits)
    hits.extend(endpoint_note_hits)
    hits.extend(undefined_methodology_label_hits)
    hits.extend(results_narration_hits)
    hits.extend(forbidden_hits)
    hits = unique_hits(hits)

    blockers: list[str] = []
    if forbidden_hits:
        blockers.append("forbidden_manuscript_terms_present")
    ama_csl_present = state.ama_csl_path.exists()
    ama_defaults_present = ama_pdf_defaults_present(state.review_defaults_path, state.ama_csl_path)
    if not ama_defaults_present:
        blockers.append("ama_pdf_defaults_missing")
    if not methods_manifest_valid:
        blockers.append("methods_implementation_manifest_missing_or_incomplete")
    if not results_narrative_valid:
        blockers.append("results_narrative_map_missing_or_incomplete")
    if not figure_semantics_valid:
        blockers.append("figure_semantics_manifest_missing_or_incomplete")
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
    if results_narration_hits:
        blockers.append("figure_table_led_results_narration_present")

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
        "review_defaults_path": str(state.review_defaults_path),
        "ama_csl_path": str(state.ama_csl_path),
        "ama_csl_present": ama_csl_present,
        "ama_pdf_defaults_present": ama_defaults_present,
        "methods_implementation_manifest_path": str(state.methods_implementation_manifest_path),
        "methods_implementation_manifest_present": state.methods_implementation_manifest_path.exists(),
        "methods_implementation_manifest_valid": methods_manifest_valid,
        "results_narrative_map_path": str(state.results_narrative_map_path),
        "results_narrative_map_present": state.results_narrative_map_path.exists(),
        "results_narrative_map_valid": results_narrative_valid,
        "figure_semantics_manifest_path": str(state.figure_semantics_manifest_path),
        "figure_semantics_manifest_present": state.figure_semantics_manifest_path.exists(),
        "figure_semantics_manifest_valid": figure_semantics_valid,
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
        "forbidden_hit_count": len(hits),
        "undefined_methodology_label_hit_count": len(undefined_methodology_label_hits),
        "results_narration_hit_count": len(results_narration_hits),
        "top_hits": hits[:40],
    }


def render_surface_markdown(report: dict[str, Any]) -> str:
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
        f"- methods_implementation_manifest_present: `{report['methods_implementation_manifest_present']}`",
        f"- methods_implementation_manifest_valid: `{report['methods_implementation_manifest_valid']}`",
        f"- results_narrative_map_present: `{report['results_narrative_map_present']}`",
        f"- results_narrative_map_valid: `{report['results_narrative_map_valid']}`",
        f"- figure_semantics_manifest_present: `{report['figure_semantics_manifest_present']}`",
        f"- figure_semantics_manifest_valid: `{report['figure_semantics_manifest_valid']}`",
        f"- derived_analysis_manifest_present: `{report['derived_analysis_manifest_present']}`",
        f"- derived_analysis_manifest_valid: `{report['derived_analysis_manifest_valid']}`",
        f"- reproducibility_supplement_present: `{report['reproducibility_supplement_present']}`",
        f"- reproducibility_supplement_valid: `{report['reproducibility_supplement_valid']}`",
        f"- missing_data_policy_consistent: `{report['missing_data_policy_consistent']}`",
        f"- endpoint_provenance_note_present: `{report['endpoint_provenance_note_present']}`",
        f"- endpoint_provenance_note_valid: `{report['endpoint_provenance_note_valid']}`",
        f"- endpoint_provenance_note_applied: `{report['endpoint_provenance_note_applied']}`",
        f"- forbidden_hit_count: `{report['forbidden_hit_count']}`",
        f"- undefined_methodology_label_hit_count: `{report['undefined_methodology_label_hit_count']}`",
        f"- results_narration_hit_count: `{report['results_narration_hit_count']}`",
        "",
        "## Top Hits",
        "",
    ]
    hits = report.get("top_hits") or []
    if not hits:
        lines.append("- none")
    else:
        for hit in hits:
            lines.append(f"- `{hit['phrase']}` at `{hit['path']}` ({hit['location']}): {hit['excerpt']}")
    return "\n".join(lines) + "\n"


def write_surface_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    stamp = report["generated_at"].replace(":", "").replace("+00:00", "Z")
    base = quest_root / "artifacts" / "reports" / "medical_publication_surface"
    json_path = base / f"{stamp}.json"
    md_path = base / f"{stamp}.md"
    dump_json(json_path, report)
    md_path.write_text(render_surface_markdown(report), encoding="utf-8")
    return json_path, md_path


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    daemon_url: str | None = None,
    source: str = "codex-medical-publication-surface",
) -> dict[str, Any]:
    state = build_surface_state(quest_root)
    report = build_surface_report(state)
    json_path, md_path = write_surface_files(quest_root, report)
    stop_result = None
    intervention = None
    if apply and report["blockers"]:
        current_status = str(state.runtime_state.get("status") or "").strip().lower()
        if current_status in {"running", "active"} and daemon_url:
            stop_result = medicaldeepscientist_transport.post_quest_control(
                daemon_url=daemon_url,
                quest_id=report["quest_id"],
                action="stop",
                source=source,
            )
        intervention = user_message.enqueue_user_message(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=medical_surface_policy.build_intervention_message(report),
            source=source,
        )
    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "blockers": report["blockers"],
        "top_hits": report["top_hits"],
        "stop_result": stop_result,
        "intervention_enqueued": bool(intervention),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--daemon-url", default="http://127.0.0.1:20999")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_controller(
        quest_root=args.quest_root,
        apply=args.apply,
        daemon_url=args.daemon_url,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
