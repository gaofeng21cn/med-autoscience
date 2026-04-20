from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience import display_registry
from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.policies.medical_reporting_contract import display_story_role_for_requirement_key
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout, resolve_runtime_root_from_quest_root
from med_autoscience.runtime_protocol import (
    paper_artifacts,
    quest_state,
    report_store as runtime_protocol_report_store,
    resolve_paper_root_context,
    user_message,
)


managed_runtime_backend = runtime_backend_contract.get_managed_runtime_backend(
    runtime_backend_contract.DEFAULT_MANAGED_RUNTIME_BACKEND_ID
)
managed_runtime_transport = managed_runtime_backend
med_deepscientist_transport = managed_runtime_transport


@dataclass
class SurfaceState:
    quest_root: Path
    runtime_state: dict[str, Any]
    paper_root: Path
    study_root: Path | None
    review_defaults_path: Path
    ama_csl_path: Path
    paper_pdf_path: Path
    draft_path: Path
    review_manuscript_path: Path
    figure_catalog_path: Path
    table_catalog_path: Path
    methods_implementation_manifest_path: Path
    review_ledger_path: Path
    results_narrative_map_path: Path
    figure_semantics_manifest_path: Path
    claim_evidence_map_path: Path
    evidence_ledger_path: Path
    derived_analysis_manifest_path: Path
    reproducibility_supplement_path: Path
    endpoint_provenance_note_path: Path


@dataclass(frozen=True)
class MarkdownHeadingBlock:
    level: int
    heading: str
    start_line: int
    end_line: int
    body: str


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
    study_root: Path | None = None
    try:
        paper_context = resolve_paper_root_context(paper_root)
    except (FileNotFoundError, ValueError):
        paper_context = None
    if paper_context is not None:
        study_root = paper_context.study_root
    if study_root is None:
        study_root = resolve_study_root_from_live_quest_root(quest_root, runtime_state)
    return SurfaceState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        paper_root=paper_root,
        study_root=study_root,
        review_defaults_path=paper_root / "latex" / "review_defaults.yaml",
        ama_csl_path=paper_root / "latex" / "american-medical-association.csl",
        paper_pdf_path=paper_root / "paper.pdf",
        draft_path=paper_root / "draft.md",
        review_manuscript_path=paper_root / "build" / "review_manuscript.md",
        figure_catalog_path=paper_root / "figures" / "figure_catalog.json",
        table_catalog_path=paper_root / "tables" / "table_catalog.json",
        methods_implementation_manifest_path=paper_root / medical_surface_policy.METHODS_IMPLEMENTATION_MANIFEST_BASENAME,
        review_ledger_path=paper_root / "review" / medical_surface_policy.REVIEW_LEDGER_BASENAME,
        results_narrative_map_path=paper_root / medical_surface_policy.RESULTS_NARRATIVE_MAP_BASENAME,
        figure_semantics_manifest_path=paper_root / medical_surface_policy.FIGURE_SEMANTICS_MANIFEST_BASENAME,
        claim_evidence_map_path=paper_root / medical_surface_policy.CLAIM_EVIDENCE_MAP_BASENAME,
        evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        derived_analysis_manifest_path=paper_root / medical_surface_policy.DERIVED_ANALYSIS_MANIFEST_BASENAME,
        reproducibility_supplement_path=paper_root / medical_surface_policy.REPRODUCIBILITY_SUPPLEMENT_BASENAME,
        endpoint_provenance_note_path=paper_root / medical_surface_policy.ENDPOINT_PROVENANCE_NOTE_BASENAME,
    )


def excerpt_around(text: str, start: int, end: int, *, width: int = 96) -> str:
    left = max(0, start - width // 2)
    right = min(len(text), end + width // 2)
    excerpt = text[left:right].replace("\n", " ").strip()
    return excerpt


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def resolve_study_root_from_live_quest_root(quest_root: Path, runtime_state: dict[str, Any]) -> Path | None:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    try:
        workspace_root = resolved_quest_root.parents[4]
    except IndexError:
        return None
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    if resolved_quest_root.parent != layout.quests_root or resolved_quest_root.parent.parent != layout.runtime_root:
        return None
    quest_id = str(runtime_state.get("quest_id") or resolved_quest_root.name).strip()
    if not quest_id:
        return None
    direct_study_root = (workspace_root / "studies" / quest_id).resolve()
    if (direct_study_root / "study.yaml").exists():
        return direct_study_root
    studies_root = workspace_root / "studies"
    if not studies_root.exists():
        return None
    for runtime_binding_path in sorted(studies_root.glob("*/runtime_binding.yaml")):
        payload = load_yaml_mapping(runtime_binding_path)
        if str(payload.get("quest_id") or "").strip() != quest_id:
            continue
        study_root = runtime_binding_path.parent.resolve()
        if (study_root / "study.yaml").exists():
            return study_root
    return None


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
MARKDOWN_TABLE_ROW_RE = re.compile(r"^\s*\|?.+\|.+\|?\s*$")
MARKDOWN_TABLE_DELIMITER_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
URL_RE = re.compile(r"https?://\S+", flags=re.IGNORECASE)
QUESTION_MARK_CHARS = frozenset({"?", "？"})
SENTENCE_TERMINATOR_CHARS = frozenset({".", "!", "?", "。", "！", "？"})
QUESTION_SENTENCE_CONTEXT_LIMIT = 400
PUBLIC_DATA_GENERIC_REFERENCE_PHRASES = (
    "public data",
    "public dataset",
    "public datasets",
    "public mri",
    "public omics",
    "public mri and omics",
    "public mri and omics datasets",
    "public anchor",
    "public anchors",
    "public anatomy anchor",
    "public anatomy anchors",
    "public biology anchor",
    "public biology anchors",
    "public anatomy and biology anchor",
    "public anatomy and biology anchors",
    "anatomy anchor",
    "anatomy anchors",
    "biology anchor",
    "biology anchors",
)


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

    payload = load_json(figure_catalog_path, default={}) or {}
    for item in payload.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("paper_role") or "").strip() != "main_text":
            continue
        figure_id = str(item.get("figure_id") or "").strip()
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
        if not figure_id or not generated_root.exists():
            continue
        for path in sorted(generated_root.glob(f"{figure_id}*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_ASSET_SUFFIXES:
                continue
            if path.name.lower() == "readme.md" or path.name.endswith(".layout.json"):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(resolved)
    return candidates


def extract_svg_text_nodes(path: Path) -> list[str]:
    if not path.exists() or path.suffix.lower() != ".svg":
        return []
    text = path.read_text(encoding="utf-8")
    matches = re.findall(r"<text\b[^>]*>(.*?)</text>", text, flags=re.IGNORECASE | re.DOTALL)
    nodes: list[str] = []
    for raw in matches:
        cleaned = re.sub(r"<[^>]+>", "", raw).strip()
        if cleaned:
            nodes.append(cleaned)
    return nodes


def inspect_figure_layout_sidecar_contract(
    *,
    paper_root: Path,
    figure_catalog_payload: object,
) -> list[dict[str, Any]]:
    if not isinstance(figure_catalog_payload, dict):
        return []
    hits: list[dict[str, Any]] = []
    generated_root = paper_root / "figures" / "generated"
    for figure in figure_catalog_payload.get("figures", []) or []:
        if not isinstance(figure, dict):
            continue
        if str(figure.get("paper_role") or "").strip() != "main_text":
            continue
        figure_id = str(figure.get("figure_id") or "").strip()
        qc_result = figure.get("qc_result")
        if not figure_id or not isinstance(qc_result, dict):
            continue
        layout_sidecar_rel = str(qc_result.get("layout_sidecar_path") or "").strip()
        if not layout_sidecar_rel:
            continue
        layout_sidecar_path = resolve_paper_relative_path(paper_root, layout_sidecar_rel)
        if not layout_sidecar_path.exists():
            continue
        layout_payload = load_json(layout_sidecar_path, default=None)
        layout_boxes = layout_payload.get("layout_boxes") if isinstance(layout_payload, dict) else None
        metrics = layout_payload.get("metrics") if isinstance(layout_payload, dict) else None
        if not isinstance(layout_boxes, list) or not layout_boxes or not isinstance(metrics, dict) or not metrics:
            hits.append(
                {
                    "path": str(layout_sidecar_path),
                    "location": "file",
                    "pattern_id": "figure_layout_sidecar_missing_publication_metrics",
                    "phrase": figure_id,
                    "excerpt": (
                        "Main-text figure layout sidecar must expose publication-facing layout boxes and metrics "
                        "for auditability."
                    ),
                }
            )
        panel_labels: set[str] = set()
        if isinstance(metrics, dict):
            for panel in metrics.get("panels", []) or []:
                if not isinstance(panel, dict):
                    continue
                label = str(panel.get("panel_label") or "").strip()
                if label:
                    panel_labels.add(label)
        if isinstance(layout_boxes, list):
            for box in layout_boxes:
                if not isinstance(box, dict):
                    continue
                box_id = str(box.get("box_id") or "").strip()
                if box_id.startswith("panel_label_"):
                    label = box_id.removeprefix("panel_label_").strip()
                    if label:
                        panel_labels.add(label)
        svg_candidates = []
        for raw_path in figure.get("export_paths", []) or []:
            if isinstance(raw_path, str) and raw_path.strip().lower().endswith(".svg"):
                svg_candidates.append(resolve_paper_relative_path(paper_root, raw_path))
        if not svg_candidates and generated_root.exists():
            svg_candidates.extend(sorted(generated_root.glob(f"{figure_id}*.svg")))
        first_text_node = ""
        for svg_path in svg_candidates:
            text_nodes = extract_svg_text_nodes(svg_path)
            if text_nodes:
                first_text_node = text_nodes[0]
                break
        if first_text_node == "A" and len(panel_labels) <= 1:
            hits.append(
                {
                    "path": str(svg_candidates[0]) if svg_candidates else str(layout_sidecar_path),
                    "location": "file",
                    "pattern_id": "single_panel_figure_contains_panel_label",
                    "phrase": figure_id,
                    "excerpt": (
                        "Single-panel figure surface starts with panel label `A` without durable multipanel layout evidence."
                    ),
                }
            )
    return hits


def discover_table_text_assets(
    paper_root: Path,
    table_catalog_path: Path,
    *,
    table_shell_ids: set[str] | None = None,
) -> list[Path]:
    payload = load_json(table_catalog_path, default={}) or {}
    candidates: list[Path] = []
    seen: set[Path] = set()
    allowed_shell_ids = {str(item).strip() for item in (table_shell_ids or set()) if str(item).strip()}
    for item in payload.get("tables", []) or []:
        if not isinstance(item, dict):
            continue
        shell_id = str(item.get("table_shell_id") or "").strip()
        if allowed_shell_ids and shell_id not in allowed_shell_ids:
            continue
        raw_paths: list[str] = []
        asset_paths = item.get("asset_paths")
        if isinstance(asset_paths, list):
            raw_paths.extend(str(path).strip() for path in asset_paths if str(path).strip())
        path_value = str(item.get("path") or "").strip()
        if path_value:
            raw_paths.append(path_value)
        for raw_path in raw_paths:
            resolved = resolve_paper_relative_path(paper_root, raw_path)
            if resolved.suffix.lower() != ".md":
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(resolved)
    return candidates


def scan_markdown_table_body(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    hits: list[dict[str, Any]] = []
    line_index = 0
    while line_index + 1 < len(lines):
        header_line = lines[line_index]
        delimiter_line = lines[line_index + 1]
        if not MARKDOWN_TABLE_ROW_RE.fullmatch(header_line) or not MARKDOWN_TABLE_DELIMITER_RE.fullmatch(delimiter_line):
            line_index += 1
            continue
        body_index = line_index + 2
        while body_index < len(lines):
            row_line = lines[body_index]
            if not MARKDOWN_TABLE_ROW_RE.fullmatch(row_line) or MARKDOWN_TABLE_DELIMITER_RE.fullmatch(row_line):
                break
            hits.extend(scan_string_value(path, f"line {body_index + 1}", row_line))
            body_index += 1
        line_index = body_index
    return hits


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


def compile_phrase_pattern(phrase: str) -> re.Pattern[str]:
    tokens = [token for token in re.split(r"[\s_-]+", str(phrase).strip()) if token]
    if not tokens:
        return re.compile(r"$^")
    pattern = r"\b" + r"[\s_-]*".join(re.escape(token) for token in tokens) + r"\b"
    return re.compile(pattern, flags=re.IGNORECASE)


def dataset_reference_phrases(dataset_id: str) -> set[str]:
    normalized = str(dataset_id or "").strip()
    if not normalized:
        return set()
    phrases = {normalized}
    if normalized.lower().startswith("geo-"):
        phrases.add(normalized[4:])
    if normalized.lower().startswith("dryad-"):
        phrases.add(normalized[6:])
    return {phrase for phrase in phrases if phrase}


def load_public_data_anchors(study_root: Path | None) -> list[dict[str, str]]:
    if study_root is None:
        return []
    study_payload = load_yaml_mapping(study_root / "study.yaml")
    raw_anchors = study_payload.get("public_data_anchors")
    if not isinstance(raw_anchors, list):
        return []
    anchors: list[dict[str, str]] = []
    for item in raw_anchors:
        if not isinstance(item, dict):
            continue
        dataset_id = str(item.get("dataset_id") or "").strip()
        role = str(item.get("role") or "").strip()
        if not dataset_id and not role:
            continue
        anchors.append({"dataset_id": dataset_id, "role": role})
    return anchors


def build_public_data_reference_patterns(public_data_anchors: list[dict[str, str]]) -> list[tuple[str, re.Pattern[str]]]:
    phrases = {phrase for phrase in PUBLIC_DATA_GENERIC_REFERENCE_PHRASES}
    roles = {str(item.get("role") or "").strip().replace("_", " ") for item in public_data_anchors if item}
    if "anatomy anchor" in roles and "biology anchor" in roles:
        phrases.add("public anatomy and biology anchors")
    for anchor in public_data_anchors:
        dataset_id = str(anchor.get("dataset_id") or "").strip()
        role = str(anchor.get("role") or "").strip().replace("_", " ")
        phrases.update(dataset_reference_phrases(dataset_id))
        if role:
            phrases.add(role)
            phrases.add(f"public {role}")
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for phrase in sorted(phrase for phrase in phrases if phrase):
        patterns.append((phrase, compile_phrase_pattern(phrase)))
    return patterns


def scan_string_value_for_patterns(
    path: Path,
    location: str,
    value: str,
    *,
    patterns: list[tuple[str, re.Pattern[str]]] | list[tuple[str, str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in patterns:
        if len(item) == 2:
            pattern_id = "paper_facing_public_data_reference"
            phrase, compiled = item
        else:
            pattern_id, phrase, compiled = item
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


def scan_text_file_for_patterns(path: Path, *, patterns: list[tuple[str, re.Pattern[str]]]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        hits.extend(scan_string_value_for_patterns(path, f"line {line_number}", line, patterns=patterns))
    return hits


def scan_catalog_strings_for_patterns(
    path: Path,
    *,
    collection_key: str,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    payload = load_json(path, default={}) or {}
    hits: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get(collection_key, []) or []):
        for field in ("title", "caption", "manuscript_purpose", "note", "next_action"):
            value = str(item.get(field) or "")
            if not value:
                continue
            hits.extend(
                scan_string_value_for_patterns(path, f"{collection_key}[{index}].{field}", value, patterns=patterns)
            )
        if collection_key == "figures":
            for panel_index, panel in enumerate(item.get("panel_plan", []) or []):
                for field in ("title", "focus"):
                    value = str(panel.get(field) or "")
                    if not value:
                        continue
                    hits.extend(
                        scan_string_value_for_patterns(
                            path,
                            f"{collection_key}[{index}].panel_plan[{panel_index}].{field}",
                            value,
                            patterns=patterns,
                        )
                    )
        summary = item.get("summary")
        if isinstance(summary, dict):
            for field in ("purpose", "must_highlight", "scope_rule"):
                value = str(summary.get(field) or "")
                if not value:
                    continue
                hits.extend(
                    scan_string_value_for_patterns(
                        path,
                        f"{collection_key}[{index}].summary.{field}",
                        value,
                        patterns=patterns,
                    )
                )
    return hits


def scan_main_text_catalog_surface_for_patterns(
    path: Path,
    *,
    collection_key: str,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    payload = load_json(path, default={}) or {}
    hits: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get(collection_key, []) or []):
        if str(item.get("paper_role") or "").strip() != "main_text":
            continue
        for field in ("title", "caption", "manuscript_purpose"):
            value = str(item.get(field) or "")
            if not value:
                continue
            hits.extend(
                scan_string_value_for_patterns(path, f"{collection_key}[{index}].{field}", value, patterns=patterns)
            )
    return hits


def inspect_public_evidence_surface(
    *,
    state: SurfaceState,
    derived_analysis_payload: object,
) -> dict[str, Any]:
    public_data_anchors = load_public_data_anchors(state.study_root)
    anchor_count = len(public_data_anchors)
    if not public_data_anchors:
        return {
            "public_data_anchors": [],
            "surface_hits": [],
            "decision_hits": [],
            "decision_count": 0,
            "earned_count": 0,
        }

    patterns = build_public_data_reference_patterns(public_data_anchors)
    surface_hits: list[dict[str, Any]] = []
    surface_hits.extend(scan_text_file_for_patterns(state.draft_path, patterns=patterns))
    surface_hits.extend(scan_text_file_for_patterns(state.review_manuscript_path, patterns=patterns))
    surface_hits.extend(scan_catalog_strings_for_patterns(state.figure_catalog_path, collection_key="figures", patterns=patterns))
    surface_hits.extend(scan_catalog_strings_for_patterns(state.table_catalog_path, collection_key="tables", patterns=patterns))
    surface_hits = unique_hits(surface_hits)

    decision_hits: list[dict[str, Any]] = []
    decision_count = 0
    earned_count = 0
    if not surface_hits:
        return {
            "public_data_anchors": public_data_anchors,
            "surface_hits": [],
            "decision_hits": [],
            "decision_count": 0,
            "earned_count": 0,
        }

    public_evidence_decisions = None
    if isinstance(derived_analysis_payload, dict):
        public_evidence_decisions = derived_analysis_payload.get(medical_surface_policy.PUBLIC_EVIDENCE_DECISIONS_KEY)
        if isinstance(public_evidence_decisions, list):
            decision_count = len(public_evidence_decisions)
            earned_count = sum(
                1
                for item in public_evidence_decisions
                if isinstance(item, dict)
                and str(item.get("paper_surface_decision") or "").strip()
                in medical_surface_policy.PUBLIC_EVIDENCE_EARNED_DECISIONS
            )
    decision_errors = medical_surface_policy.validate_public_evidence_decisions(public_evidence_decisions)
    if decision_errors:
        decision_hits.append(
            {
                "path": str(state.derived_analysis_manifest_path),
                "location": "file",
                "pattern_id": "public_evidence_decisions_missing_or_incomplete",
                "phrase": medical_surface_policy.PUBLIC_EVIDENCE_DECISIONS_KEY,
                "excerpt": "; ".join(decision_errors),
            }
        )
    elif earned_count == 0:
        decision_hits.append(
            {
                "path": str(state.derived_analysis_manifest_path),
                "location": "file",
                "pattern_id": "paper_facing_public_data_without_earned_evidence",
                "phrase": medical_surface_policy.PUBLIC_EVIDENCE_DECISIONS_KEY,
                "excerpt": (
                    "Paper-facing public-data references are present, but no public_evidence_decisions entry earned "
                    "a manuscript-facing role."
                ),
            }
        )
    return {
        "public_data_anchors": public_data_anchors,
        "surface_hits": surface_hits,
        "decision_hits": decision_hits,
        "decision_count": decision_count,
        "earned_count": earned_count,
        "anchor_count": anchor_count,
    }


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
    display_shell_plan = payload.get("display_shell_plan")
    if not isinstance(display_shell_plan, list):
        return story_roles
    for item in display_shell_plan:
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


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower().replace("&", "and"))


def parse_markdown_heading_blocks(text: str) -> list[MarkdownHeadingBlock]:
    lines = text.splitlines()
    headings: list[tuple[int, str, int]] = []
    in_front_matter = False
    in_code_block = False

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if line_number == 1 and stripped == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if stripped == "---":
                in_front_matter = False
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = MARKDOWN_HEADING_RE.match(raw_line)
        if match is None:
            continue
        headings.append((len(match.group(1)), match.group(2).strip(), line_number))

    blocks: list[MarkdownHeadingBlock] = []
    total_lines = len(lines)
    for index, (level, heading, start_line) in enumerate(headings):
        end_line = total_lines
        for next_level, _, next_start_line in headings[index + 1 :]:
            if next_level <= level:
                end_line = next_start_line - 1
                break
        body_start_index = start_line
        body_end_index = end_line
        body = "\n".join(lines[body_start_index:body_end_index]).strip()
        blocks.append(
            MarkdownHeadingBlock(
                level=level,
                heading=heading,
                start_line=start_line,
                end_line=end_line,
                body=body,
            )
        )
    return blocks


def find_heading_block(
    blocks: list[MarkdownHeadingBlock],
    *,
    level: int,
    headings: tuple[str, ...],
) -> MarkdownHeadingBlock | None:
    normalized_targets = {normalize_heading(item) for item in headings}
    for block in blocks:
        if block.level != level:
            continue
        if normalize_heading(block.heading) in normalized_targets:
            return block
    return None


def find_heading_block_with_fallback_levels(
    blocks: list[MarkdownHeadingBlock],
    *,
    levels: tuple[int, ...],
    headings: tuple[str, ...],
) -> MarkdownHeadingBlock | None:
    for level in levels:
        block = find_heading_block(blocks, level=level, headings=headings)
        if block is not None:
            return block
    return None


def child_heading_blocks(
    blocks: list[MarkdownHeadingBlock],
    *,
    parent: MarkdownHeadingBlock,
    level: int,
) -> list[MarkdownHeadingBlock]:
    return [
        block
        for block in blocks
        if block.level == level and parent.start_line < block.start_line <= parent.end_line
    ]


def first_subsection_heading_blocks(
    blocks: list[MarkdownHeadingBlock],
    *,
    parent: MarkdownHeadingBlock,
) -> list[MarkdownHeadingBlock]:
    descendant_blocks = [
        block
        for block in blocks
        if parent.start_line < block.start_line <= parent.end_line and block.level > parent.level
    ]
    if not descendant_blocks:
        return []
    subsection_level = min(block.level for block in descendant_blocks)
    return [block for block in descendant_blocks if block.level == subsection_level]


def extract_nonempty_paragraphs(text: str) -> list[str]:
    without_headings = re.sub(r"(?m)^#{1,6}\s+.+$", "", text)
    return [block.strip() for block in re.split(r"\n\s*\n", without_headings) if block.strip()]


def scan_manuscript_surface_sections_for_patterns(
    path: Path,
    *,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    hits: list[dict[str, Any]] = []
    for headings in (("Abstract",), ("Results",)):
        block = find_heading_block_with_fallback_levels(blocks, levels=(2, 1), headings=headings)
        if block is None or not block.body.strip():
            continue
        hits.extend(
            scan_string_value_for_patterns(path, f"line {block.start_line}", block.body, patterns=patterns)
        )
    return hits


def inspect_results_narrative_surface_language(
    *,
    path: Path,
    payload: object,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return []
    hits: list[dict[str, Any]] = []
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        for field in ("section_title", "research_question", "direct_answer", "clinical_meaning", "boundary"):
            value = str(section.get(field) or "").strip()
            if not value:
                continue
            hits.extend(
                scan_string_value_for_patterns(path, f"sections[{index}].{field}", value, patterns=patterns)
            )
    return hits


def inspect_claim_evidence_surface_language(
    *,
    path: Path,
    payload: object,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    claims = payload.get("claims")
    if not isinstance(claims, list):
        return []
    hits: list[dict[str, Any]] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        if str(claim.get("paper_role") or "").strip() != "main_text":
            continue
        statement = str(claim.get("statement") or "").strip()
        if statement:
            hits.extend(
                scan_string_value_for_patterns(path, f"claims[{index}].statement", statement, patterns=patterns)
            )
    return hits


def inspect_introduction_structure(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    introduction_block = find_heading_block_with_fallback_levels(
        blocks,
        levels=(2, 1),
        headings=("Introduction",),
    )
    if introduction_block is None:
        return [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": "introduction_structure",
                "phrase": "Introduction",
                "excerpt": "Manuscript is missing a second-level `Introduction` section.",
            }
        ]
    paragraphs = extract_nonempty_paragraphs(introduction_block.body)
    if len(paragraphs) >= medical_surface_policy.INTRODUCTION_REQUIRED_PARAGRAPH_COUNT:
        return []
    return [
        {
            "path": str(path),
            "location": f"line {introduction_block.start_line}",
            "pattern_id": "introduction_structure",
            "phrase": introduction_block.heading,
            "excerpt": (
                "Introduction must contain at least "
                f"{medical_surface_policy.INTRODUCTION_REQUIRED_PARAGRAPH_COUNT} formal paragraphs "
                "covering clinical context, current evidence gap, and present-study objective."
            ),
        }
    ]


def inspect_methods_section_structure(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    methods_block = find_heading_block_with_fallback_levels(
        blocks,
        levels=(2, 1),
        headings=("Materials and Methods", "Materials & Methods", "Methods"),
    )
    if methods_block is None:
        return [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": "methods_section_structure",
                "phrase": "Materials and Methods",
                "excerpt": "Manuscript is missing a second-level Methods section.",
            }
        ]
    subsection_blocks = first_subsection_heading_blocks(blocks, parent=methods_block)
    subsection_map = {normalize_heading(block.heading): block for block in subsection_blocks if block.body.strip()}
    missing_headings = [
        heading
        for heading in medical_surface_policy.METHODS_REQUIRED_SUBSECTION_HEADINGS
        if normalize_heading(heading) not in subsection_map
    ]
    if not missing_headings:
        return []
    return [
        {
            "path": str(path),
            "location": f"line {methods_block.start_line}",
            "pattern_id": "methods_section_structure",
            "phrase": methods_block.heading,
            "excerpt": (
                "Methods section must include the reviewer-facing subsections: "
                + ", ".join(medical_surface_policy.METHODS_REQUIRED_SUBSECTION_HEADINGS)
                + f". Missing: {', '.join(missing_headings)}."
            ),
        }
    ]


def inspect_results_section_structure(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    blocks = parse_markdown_heading_blocks(path.read_text(encoding="utf-8"))
    results_block = find_heading_block_with_fallback_levels(
        blocks,
        levels=(2, 1),
        headings=("Results",),
    )
    if results_block is None:
        return [
            {
                "path": str(path),
                "location": "file",
                "pattern_id": "results_section_structure",
                "phrase": "Results",
                "excerpt": "Manuscript is missing a second-level `Results` section.",
            }
        ]
    subsection_blocks = [block for block in first_subsection_heading_blocks(blocks, parent=results_block) if block.body.strip()]
    if len(subsection_blocks) >= medical_surface_policy.RESULTS_MIN_SUBSECTION_COUNT:
        return []
    return [
        {
            "path": str(path),
            "location": f"line {results_block.start_line}",
            "pattern_id": "results_section_structure",
            "phrase": results_block.heading,
            "excerpt": (
                "Results section must be broken into at least "
                f"{medical_surface_policy.RESULTS_MIN_SUBSECTION_COUNT} subsection headings with non-empty prose."
            ),
        }
    ]


def scan_non_formal_question_sentences(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    in_front_matter = False
    in_code_block = False
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if line_number == 1 and stripped == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if stripped == "---":
                in_front_matter = False
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        sanitized = URL_RE.sub("", raw_line).strip()
        if not sanitized:
            continue
        for sentence in iter_non_formal_question_sentences(sanitized):
            if not sentence:
                continue
            hits.append(
                {
                    "path": str(path),
                    "location": f"line {line_number}",
                    "pattern_id": "non_formal_question_sentence",
                    "phrase": sentence,
                    "excerpt": sentence,
                }
            )
    return hits


def iter_non_formal_question_sentences(line: str) -> list[str]:
    sentences: list[str] = []
    sentence_start = 0
    for index, char in enumerate(line):
        if char not in SENTENCE_TERMINATOR_CHARS:
            continue
        if char in QUESTION_MARK_CHARS:
            excerpt_start = max(sentence_start, index - QUESTION_SENTENCE_CONTEXT_LIMIT)
            sentence = line[excerpt_start : index + 1].strip()
            if any(letter.isascii() and letter.isalpha() for letter in sentence):
                sentences.append(sentence)
        sentence_start = index + 1
    return sentences


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
    claim_evidence_map_valid, claim_evidence_map_hits = inspect_required_json_contract(
        path=state.claim_evidence_map_path,
        validator=medical_surface_policy.validate_claim_evidence_map,
        pattern_id="claim_evidence_map",
        label="claim evidence map",
    )
    evidence_ledger_valid, evidence_ledger_hits = inspect_required_json_contract(
        path=state.evidence_ledger_path,
        validator=medical_surface_policy.validate_evidence_ledger,
        pattern_id="evidence_ledger",
        label="evidence ledger",
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
    claim_evidence_map_payload = load_json(state.claim_evidence_map_path, default=None)
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
    hits.extend(analysis_plane_jargon_hits)
    hits.extend(forbidden_hits)
    hits.extend(public_data_surface_hits)
    hits.extend(public_evidence_decision_hits)
    hits = unique_hits(hits)

    blockers: list[str] = []
    if forbidden_hits:
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
    if results_narration_hits:
        blockers.append("figure_table_led_results_narration_present")
    if non_formal_question_hits:
        blockers.append("non_formal_question_sentence_present")
    if analysis_plane_jargon_hits:
        blockers.append("analysis_plane_jargon_present_on_manuscript_surface")
    if any(hit["pattern_id"] == "public_evidence_decisions_missing_or_incomplete" for hit in public_evidence_decision_hits):
        blockers.append("public_evidence_decisions_missing_or_incomplete")
    if any(
        hit["pattern_id"] == "paper_facing_public_data_without_earned_evidence"
        for hit in public_evidence_decision_hits
    ):
        blockers.append("paper_facing_public_data_without_earned_evidence")

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
        "introduction_structure_valid": not introduction_structure_hits,
        "methods_section_structure_valid": not methods_section_structure_hits,
        "results_section_structure_valid": not results_section_structure_hits,
        "results_narrative_map_path": str(state.results_narrative_map_path),
        "results_narrative_map_present": state.results_narrative_map_path.exists(),
        "results_narrative_map_valid": results_narrative_valid,
        "medical_story_contract_structural_valid": medical_story_contract_structural_valid,
        "medical_story_contract_valid": medical_story_contract_valid,
        "manuscript_rhetoric_medical_publication_native": not analysis_plane_jargon_hits,
        "results_display_surface_valid": not results_display_surface_hits,
        "figure_semantics_manifest_path": str(state.figure_semantics_manifest_path),
        "figure_semantics_manifest_present": state.figure_semantics_manifest_path.exists(),
        "figure_semantics_manifest_valid": figure_semantics_valid,
        "claim_evidence_map_path": str(state.claim_evidence_map_path),
        "claim_evidence_map_present": state.claim_evidence_map_path.exists(),
        "claim_evidence_map_valid": claim_evidence_map_valid,
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
        "public_data_anchor_count": int(public_evidence_surface_state.get("anchor_count") or 0),
        "public_data_surface_reference_count": len(public_data_surface_hits),
        "public_evidence_decision_count": int(public_evidence_surface_state.get("decision_count") or 0),
        "public_evidence_earned_count": int(public_evidence_surface_state.get("earned_count") or 0),
        "analysis_plane_jargon_hit_count": len(analysis_plane_jargon_hits),
        "forbidden_hit_count": len(hits),
        "undefined_methodology_label_hit_count": len(undefined_methodology_label_hits),
        "results_narration_hit_count": len(results_narration_hits),
        "non_formal_question_hit_count": len(non_formal_question_hits),
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
        f"- public_data_anchor_count: `{report.get('public_data_anchor_count', 0)}`",
        f"- public_data_surface_reference_count: `{report.get('public_data_surface_reference_count', 0)}`",
        f"- public_evidence_decision_count: `{report.get('public_evidence_decision_count', 0)}`",
        f"- public_evidence_earned_count: `{report.get('public_evidence_earned_count', 0)}`",
        f"- forbidden_hit_count: `{report['forbidden_hit_count']}`",
        f"- undefined_methodology_label_hit_count: `{report['undefined_methodology_label_hit_count']}`",
        f"- results_narration_hit_count: `{report['results_narration_hit_count']}`",
        f"- non_formal_question_hit_count: `{report.get('non_formal_question_hit_count', 0)}`",
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
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="medical_publication_surface",
        timestamp=report["generated_at"],
        report=report,
        markdown=render_surface_markdown(report),
    )


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
            stop_result = managed_runtime_transport.stop_quest(
                daemon_url=daemon_url,
                runtime_root=resolve_runtime_root_from_quest_root(state.quest_root),
                quest_id=report["quest_id"],
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
