from .shared import *

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


