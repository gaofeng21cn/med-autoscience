from __future__ import annotations

import argparse
from importlib import import_module
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import journal_package as journal_package_controller, study_delivery_sync, submission_minimal
from med_autoscience.journal_requirements import (
    describe_journal_submission_package,
    journal_requirements_json_path,
    load_journal_requirements,
    slugify_journal_name,
)
from med_autoscience.policies import publication_gate as publication_gate_policy
from med_autoscience.runtime_protocol import (
    paper_artifacts,
    quest_state,
    resolve_paper_root_context,
    user_message,
)
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store

PUBLICATION_SUPERVISOR_KEYS: tuple[str, ...] = (
    "supervisor_phase",
    "phase_owner",
    "upstream_scientific_anchor_ready",
    "bundle_tasks_downstream_only",
    "current_required_action",
    "deferred_downstream_actions",
    "controller_stage_note",
)
_NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS = (
    paper_artifacts.SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS | frozenset({"full_manuscript_pageproof"})
)
_BUNDLE_STAGE_ONLY_BLOCKERS = frozenset(
    {
        "missing_paper_compile_report",
        "missing_submission_minimal",
        "missing_journal_package",
        "submission_surface_qc_failure_present",
        "unmanaged_submission_surface_present",
    }
)
_MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS = frozenset(
    {
        "review_ledger_missing_or_incomplete",
        "forbidden_manuscript_terms_present",
        "analysis_plane_jargon_present_on_manuscript_surface",
        "figure_table_led_results_narration_present",
        "non_formal_question_sentence_present",
    }
)
_MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS = frozenset(
    {
        "missing_medical_story_contract",
        "claim_evidence_map_missing_or_incomplete",
        "evidence_ledger_missing_or_incomplete",
        "paper_facing_public_data_without_earned_evidence",
    }
)
_MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS = frozenset(
    {
        "figure_catalog_missing_or_incomplete",
        "table_catalog_missing_or_incomplete",
        "required_display_catalog_coverage_incomplete",
        "ama_pdf_defaults_missing",
        "methods_implementation_manifest_missing_or_incomplete",
        "results_narrative_map_missing_or_incomplete",
        "results_display_surface_incomplete",
        "introduction_structure_missing_or_incomplete",
        "methods_section_structure_missing_or_incomplete",
        "results_section_structure_missing_or_incomplete",
        "figure_semantics_manifest_missing_or_incomplete",
        "figure_layout_sidecar_missing_or_incomplete",
        "derived_analysis_manifest_missing_or_incomplete",
        "manuscript_safe_reproducibility_supplement_missing_or_incomplete",
        "missing_data_policy_inconsistent",
        "endpoint_provenance_note_missing_or_unapplied",
        "undefined_methodology_labels_present",
        "public_evidence_decisions_missing_or_incomplete",
    }
)
_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS = {
    "reviewer_first_concerns_unresolved": "return_to_write",
    "claim_evidence_consistency_failed": "return_to_analysis_campaign",
    "submission_hardening_incomplete": "return_to_finalize",
}
_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES = {
    "reviewer_first_concerns_unresolved": (
        "route back to `write` to close reviewer-first publication-surface concerns"
    ),
    "claim_evidence_consistency_failed": (
        "route back to `analysis-campaign` to close claim-evidence consistency gaps"
    ),
    "submission_hardening_incomplete": "route back to `finalize` to close submission-readiness gaps",
}
_DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES = 4


@dataclass
class GateState:
    quest_root: Path
    runtime_state: dict[str, Any]
    study_root: Path | None
    charter_contract_linkage: dict[str, Any]
    anchor_kind: str
    anchor_path: Path
    paper_line_state_path: Path | None
    paper_line_state: dict[str, Any] | None
    main_result_path: Path | None
    main_result: dict[str, Any] | None
    paper_root: Path | None
    compile_report_path: Path | None
    compile_report: dict[str, Any] | None
    latest_gate_path: Path | None
    latest_gate: dict[str, Any] | None
    latest_medical_publication_surface_path: Path | None
    latest_medical_publication_surface: dict[str, Any] | None
    active_run_stdout_path: Path | None
    recent_stdout_lines: list[str]
    write_drift_detected: bool
    missing_deliverables: list[str]
    present_deliverables: list[str]
    paper_bundle_manifest_path: Path | None
    paper_bundle_manifest: dict[str, Any] | None
    submission_checklist_path: Path | None
    submission_checklist: dict[str, Any] | None
    submission_minimal_manifest_path: Path | None
    submission_minimal_manifest: dict[str, Any] | None
    submission_minimal_docx_present: bool
    submission_minimal_pdf_present: bool
    submission_surface_qc_failures: list[dict[str, Any]]
    archived_submission_surface_roots: list[str]
    unmanaged_submission_surface_roots: list[str]
    manuscript_terminology_violations: list[dict[str, str]]
    study_delivery: dict[str, Any] | None
    draft_handoff_delivery: dict[str, Any] | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_blocker_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item or "").strip() for item in value if str(item or "").strip()}


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


def find_latest_parseable_json(paths: list[Path]) -> Path | None:
    for path in sorted(paths, key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            load_json(path)
        except json.JSONDecodeError:
            continue
        return path
    return None


def _normalize_medical_surface_paper_root(paper_root: Path) -> Path:
    resolved = paper_root.expanduser().resolve()
    if resolved.name != "paper":
        return resolved
    payload = load_json(resolved / "paper_line_state.json", default=None)
    if isinstance(payload, dict):
        candidate_value = _non_empty_text(payload.get("paper_root"))
        if candidate_value:
            candidate = Path(candidate_value).expanduser().resolve()
            if candidate.name == "paper":
                return candidate
    return resolved


def _medical_surface_report_matches_paper_root(
    report_payload: Any,
    *,
    paper_root: Path | None,
) -> bool:
    if paper_root is None:
        return True
    if not isinstance(report_payload, dict):
        return False
    raw_report_root = _non_empty_text(report_payload.get("paper_root"))
    if raw_report_root is None:
        return True
    return _normalize_medical_surface_paper_root(Path(raw_report_root)) == _normalize_medical_surface_paper_root(
        paper_root
    )


def _medical_surface_report_matches_study_root(
    report_payload: Any,
    *,
    study_root: Path | None,
) -> bool:
    if study_root is None:
        return False
    if not isinstance(report_payload, dict):
        return False
    raw_study_root = _non_empty_text(report_payload.get("study_root"))
    if raw_study_root is None:
        return False
    return Path(raw_study_root).expanduser().resolve() == study_root.expanduser().resolve()


def find_latest_gate_report(quest_root: Path) -> Path | None:
    return find_latest_parseable_json(
        list((quest_root / "artifacts" / "reports" / "publishability_gate").glob("*.json"))
    )


def find_latest_medical_publication_surface_report(
    quest_root: Path,
    *,
    paper_root: Path | None = None,
    study_root: Path | None = None,
) -> Path | None:
    report_paths = sorted(
        (quest_root / "artifacts" / "reports" / "medical_publication_surface").glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in report_paths:
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue
        if _medical_surface_report_matches_paper_root(payload, paper_root=paper_root):
            return path
    if study_root is not None:
        for path in report_paths:
            try:
                payload = load_json(path)
            except json.JSONDecodeError:
                continue
            if _medical_surface_report_matches_study_root(payload, study_root=study_root):
                return path
    return None


def _write_drift_text_surfaces(line: str) -> list[str]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return [line]
    if not isinstance(payload, dict):
        return []
    item = payload.get("item")
    if not isinstance(item, dict):
        return []
    item_type = _non_empty_text(item.get("type"))
    if item_type == "agent_message":
        text = _non_empty_text(item.get("text"))
        return [text] if text else []
    if item_type != "mcp_tool_call":
        return []
    if _non_empty_text(item.get("server")) != "artifact":
        return []
    texts: list[str] = []
    arguments = item.get("arguments")
    if isinstance(arguments, dict):
        if message := _non_empty_text(arguments.get("message")):
            texts.append(message)
    return texts


def detect_write_drift(lines: list[str]) -> bool:
    for line in lines:
        if any(
            re.search(pattern, line, flags=re.IGNORECASE)
            for pattern in publication_gate_policy.WRITE_DRIFT_STRUCTURED_PATTERNS
        ):
            return True
        for text in _write_drift_text_surfaces(line):
            if any(
                re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
                for pattern in publication_gate_policy.WRITE_DRIFT_PATTERNS
            ):
                return True
    return False


def _paper_line_open_supplementary_count(paper_line_state: dict[str, Any] | None) -> int:
    if not isinstance(paper_line_state, dict):
        return 0
    raw_value = paper_line_state.get("open_supplementary_count")
    try:
        return max(0, int(raw_value or 0))
    except (TypeError, ValueError):
        return 0


def _paper_line_recommended_action(paper_line_state: dict[str, Any] | None) -> str | None:
    if not isinstance(paper_line_state, dict):
        return None
    return _non_empty_text(paper_line_state.get("recommended_action"))


def _paper_line_blocking_reasons(paper_line_state: dict[str, Any] | None) -> list[str]:
    if not isinstance(paper_line_state, dict):
        return []
    reasons = paper_line_state.get("blocking_reasons")
    if not isinstance(reasons, list):
        return []
    return [text for item in reasons if (text := _non_empty_text(item))]


def _paper_line_requires_required_supplementary(paper_line_state: dict[str, Any] | None) -> bool:
    if _paper_line_open_supplementary_count(paper_line_state) > 0:
        return True
    return _paper_line_recommended_action(paper_line_state) == "complete_required_supplementary"


def _medical_publication_surface_named_blockers(surface_report: dict[str, Any] | None) -> list[str]:
    if not isinstance(surface_report, dict):
        return []
    surface_blockers = _normalized_blocker_set(surface_report.get("blockers"))
    named_blockers: list[str] = []
    if (
        surface_report.get("review_ledger_valid") is False
        or surface_blockers.intersection(_MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS)
    ):
        named_blockers.append("reviewer_first_concerns_unresolved")
    if (
        surface_report.get("claim_evidence_map_valid") is False
        or surface_report.get("evidence_ledger_valid") is False
        or surface_report.get("medical_story_contract_valid") is False
        or surface_blockers.intersection(_MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS)
    ):
        named_blockers.append("claim_evidence_consistency_failed")
    if surface_blockers.intersection(_MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS):
        named_blockers.append("submission_hardening_incomplete")
    return named_blockers


def _medical_publication_surface_route_back_recommendation(named_blockers: list[str]) -> str | None:
    for blocker in named_blockers:
        recommendation = _MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS.get(blocker)
        if recommendation:
            return recommendation
    return None


def _medical_publication_surface_stage_note(
    *,
    base_note: str,
    named_blockers: list[str],
    route_back_recommendation: str | None,
) -> str:
    if not named_blockers:
        return base_note
    route_back_clauses = [
        clause
        for blocker in named_blockers
        if (clause := _MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES.get(blocker))
    ]
    if not route_back_clauses:
        return base_note
    route_back_closure_text = "; ".join(route_back_clauses)
    recommended_route_back = route_back_recommendation or "return_to_publishability_gate"
    return (
        f"{base_note}; medical publication surface is blocked; {route_back_closure_text}. "
        f"Recommended route-back: `{recommended_route_back}`."
    )


def _dedupe_resolved_paths(paths: list[Path]) -> list[Path]:
    resolved: dict[str, Path] = {}
    for path in paths:
        resolved[str(path.resolve())] = path.resolve()
    return [resolved[key] for key in sorted(resolved)]


def _bundle_manifest_branch(manifest_payload: dict[str, Any] | None) -> str | None:
    if not isinstance(manifest_payload, dict):
        return None
    return _non_empty_text(manifest_payload.get("paper_branch"))


def _paper_line_branch(paper_line_state: dict[str, Any] | None) -> str | None:
    if not isinstance(paper_line_state, dict):
        return None
    return _non_empty_text(paper_line_state.get("paper_branch"))


def _projected_bundle_manifest_path(quest_root: Path) -> Path:
    return quest_root.resolve() / "paper" / "paper_bundle_manifest.json"


def _resolve_worktree_bundle_manifest_by_branch(*, quest_root: Path, paper_branch: str | None) -> Path | None:
    if paper_branch is None:
        return None
    candidates: list[Path] = []
    for candidate in quest_root.resolve().glob(".ds/worktrees/*/paper/paper_bundle_manifest.json"):
        payload = load_json(candidate, default=None)
        if _bundle_manifest_branch(payload) != paper_branch:
            continue
        candidates.append(candidate.resolve())
    if not candidates:
        return None

    def rank(path: Path) -> tuple[int, float]:
        try:
            worktree_name = path.relative_to(quest_root.resolve()).parts[2]
        except (ValueError, IndexError):
            worktree_name = ""
        return (1 if worktree_name.startswith("paper-") else 0, path.stat().st_mtime)

    return max(candidates, key=rank)


def resolve_bundle_authority_paper_root(
    *,
    quest_root: Path,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
    paper_line_state: dict[str, Any] | None,
) -> Path | None:
    if paper_bundle_manifest_path is None:
        return None
    resolved_manifest_path = paper_bundle_manifest_path.resolve()
    bundle_paper_root = resolved_manifest_path.parent.resolve()
    if resolved_manifest_path != _projected_bundle_manifest_path(quest_root):
        return bundle_paper_root

    manifest_branch = _bundle_manifest_branch(paper_bundle_manifest)
    line_branch = _paper_line_branch(paper_line_state)
    paper_line_root_value = _non_empty_text((paper_line_state or {}).get("paper_root"))
    if manifest_branch is not None and line_branch is not None and manifest_branch == line_branch and paper_line_root_value:
        candidate = Path(paper_line_root_value).expanduser().resolve()
        if candidate.exists():
            return candidate

    if manifest_branch is not None and line_branch is not None and manifest_branch != line_branch:
        authoritative_manifest = _resolve_worktree_bundle_manifest_by_branch(
            quest_root=quest_root,
            paper_branch=manifest_branch,
        )
        if authoritative_manifest is not None:
            return authoritative_manifest.parent.resolve()

    if paper_line_root_value:
        candidate = Path(paper_line_root_value).expanduser().resolve()
        if candidate.exists():
            return candidate
    return bundle_paper_root


def resolve_submission_checklist_path(*, paper_root: Path | None) -> Path | None:
    if paper_root is None:
        return None
    candidate = paper_root / "review" / "submission_checklist.json"
    return candidate if candidate.exists() else None


def load_submission_checklist(*, paper_root: Path | None) -> dict[str, Any] | None:
    checklist_path = resolve_submission_checklist_path(paper_root=paper_root)
    if checklist_path is None:
        return None
    return load_json(checklist_path, default=None)


def resolve_submission_minimal_manifest(*, paper_root: Path | None) -> Path | None:
    if paper_root is None:
        return None
    candidate = paper_root / "submission_minimal" / "submission_manifest.json"
    return candidate if candidate.exists() else None


def resolve_submission_minimal_output_paths(
    *,
    paper_root: Path | None,
    submission_minimal_manifest: dict[str, Any] | None,
) -> tuple[Path | None, Path | None]:
    if paper_root is None or submission_minimal_manifest is None:
        return None, None
    workspace_root = paper_root.parent
    manuscript = submission_minimal_manifest.get("manuscript") or {}
    docx_relpath = _non_empty_text(manuscript.get("docx_path"))
    pdf_relpath = _non_empty_text(manuscript.get("pdf_path"))
    docx_path = workspace_root / docx_relpath if docx_relpath else None
    pdf_path = workspace_root / pdf_relpath if pdf_relpath else None
    return docx_path, pdf_path


def classify_deliverables(main_result_path: Path, main_result: dict[str, Any]) -> tuple[list[str], list[str]]:
    required = list(main_result.get("metric_contract", {}).get("required_non_scalar_deliverables") or [])
    manifest_path = paper_artifacts.resolve_artifact_manifest_from_main_result(main_result)
    manifest_payload = load_json(manifest_path, default={}) if manifest_path else {}
    manifest_blob = json.dumps(manifest_payload, ensure_ascii=False).lower()
    present: list[str] = []
    missing: list[str] = []
    for item in required:
        if item.lower() in manifest_blob:
            present.append(item)
        else:
            missing.append(item)
    return present, missing


def resolve_paper_root(
    *,
    quest_root: Path,
    main_result: dict[str, Any] | None,
    paper_line_state: dict[str, Any] | None,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> Path | None:
    if bundle_authority_paper_root := resolve_bundle_authority_paper_root(
        quest_root=quest_root,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
        paper_line_state=paper_line_state,
    ):
        return bundle_authority_paper_root
    worktree_root_value = str((main_result or {}).get("worktree_root") or "").strip()
    if worktree_root_value:
        candidate = Path(worktree_root_value).expanduser().resolve() / "paper"
        if candidate.exists():
            return candidate
    return None


def collect_manuscript_surface_paths(paper_root: Path | None) -> list[Path]:
    if paper_root is None or not paper_root.exists():
        return []
    candidates: list[Path] = []
    for pattern in publication_gate_policy.MANUSCRIPT_SURFACE_GLOBS:
        candidates.extend(path for path in paper_root.glob(pattern) if path.is_file())
    for managed_root in paper_artifacts.resolve_managed_submission_surface_roots(paper_root):
        for pattern in publication_gate_policy.MANAGED_SUBMISSION_SURFACE_GLOBS:
            candidates.extend(path for path in managed_root.glob(pattern) if path.is_file())
    return _dedupe_resolved_paths(candidates)


def detect_manuscript_terminology_violations(paper_root: Path | None) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in collect_manuscript_surface_paths(paper_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for rule in publication_gate_policy.MANUSCRIPT_TERMINOLOGY_REDLINE_PATTERNS:
            label = str(rule["label"])
            pattern = str(rule["pattern"])
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                key = (str(path.resolve()), label, match.group(0))
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    {
                        "path": key[0],
                        "label": key[1],
                        "match": key[2],
                    }
                )
    return violations


def _load_catalog_entries(
    *,
    paper_root: Path | None,
    relative_path: str,
    collection_key: str,
) -> list[dict[str, Any]] | None:
    if paper_root is None:
        return None
    catalog_path = paper_root / relative_path
    if not catalog_path.exists():
        return None
    payload = load_json(catalog_path, default={})
    if not isinstance(payload, dict):
        return None
    entries = payload.get(collection_key)
    if not isinstance(entries, list):
        return None
    return [item for item in entries if isinstance(item, dict)]


def active_manuscript_figure_count(paper_root: Path | None) -> int | None:
    entries = _load_catalog_entries(
        paper_root=paper_root,
        relative_path="figures/figure_catalog.json",
        collection_key="figures",
    )
    if entries is None:
        return None
    count = 0
    for item in entries:
        paper_role = str(item.get("paper_role") or "").strip().lower()
        manuscript_status = str(item.get("manuscript_status") or "").strip().lower()
        if paper_role in {"appendix_legacy_inactive", "reference_only", "deprecated"}:
            continue
        if manuscript_status in {"appendix_context_only", "reference_only", "deprecated"}:
            continue
        count += 1
    return count


def active_main_text_figure_count(paper_root: Path | None) -> int | None:
    entries = _load_catalog_entries(
        paper_root=paper_root,
        relative_path="figures/figure_catalog.json",
        collection_key="figures",
    )
    if entries is None:
        return None
    count = 0
    for item in entries:
        paper_role = str(item.get("paper_role") or "").strip().lower()
        manuscript_status = str(item.get("manuscript_status") or "").strip().lower()
        if paper_role != "main_text":
            continue
        if manuscript_status in {"appendix_context_only", "reference_only", "deprecated"}:
            continue
        count += 1
    return count


def infer_submission_publication_profile(submission_minimal_manifest: dict[str, Any]) -> str:
    for key in ("publication_profile", "requested_publication_profile"):
        value = _non_empty_text(submission_minimal_manifest.get(key))
        if value:
            return value
    manuscript = submission_minimal_manifest.get("manuscript") or {}
    output_candidates = [
        _non_empty_text(manuscript.get("docx_path")),
        _non_empty_text(manuscript.get("pdf_path")),
    ]
    if any(candidate and "journal_submissions/frontiers_family_harvard/" in candidate for candidate in output_candidates):
        return submission_minimal.FRONTIERS_FAMILY_HARVARD_PROFILE
    return submission_minimal.GENERAL_MEDICAL_JOURNAL_PROFILE


def collect_submission_surface_qc_failures(
    submission_minimal_manifest: dict[str, Any] | None,
    *,
    paper_bundle_manifest_path: Path | None,
    paper_root: Path | None,
) -> list[dict[str, Any]]:
    if not isinstance(submission_minimal_manifest, dict):
        return []
    failures: list[dict[str, Any]] = []
    for collection_key, item_id_key, descriptor_key in (
        ("figures", "figure_id", "template_id"),
        ("tables", "table_id", "table_shell_id"),
    ):
        for index, item in enumerate(submission_minimal_manifest.get(collection_key, []) or []):
            if not isinstance(item, dict):
                continue
            qc_result = item.get("qc_result")
            if not isinstance(qc_result, dict):
                continue
            qc_status = str(qc_result.get("status") or "").strip().lower()
            if qc_status != "fail":
                continue
            failures.append(
                {
                    "collection": collection_key,
                    "item_id": str(item.get(item_id_key) or f"{collection_key}[{index}]").strip(),
                    "descriptor": str(item.get(descriptor_key) or "").strip(),
                    "qc_profile": str(item.get("qc_profile") or qc_result.get("qc_profile") or "").strip(),
                    "failure_reason": str(qc_result.get("failure_reason") or "").strip(),
                    "audit_classes": list(qc_result.get("audit_classes") or []),
                }
            )
    expected_main_figure_count = active_main_text_figure_count(paper_root) or 0
    manuscript_payload = submission_minimal_manifest.get("manuscript") or {}
    if expected_main_figure_count > 0:
        source_markdown_rel = _non_empty_text(manuscript_payload.get("source_markdown_path"))
        authoritative_submission_manifest_path = paper_artifacts.resolve_submission_minimal_manifest(
            paper_bundle_manifest_path
        )
        worktree_root = (
            authoritative_submission_manifest_path.resolve().parent.parent.parent
            if authoritative_submission_manifest_path is not None
            else (paper_bundle_manifest_path.resolve().parent.parent if paper_bundle_manifest_path else None)
        )
        source_markdown_path = (
            (worktree_root / source_markdown_rel).resolve()
            if worktree_root is not None and source_markdown_rel is not None
            else ((worktree_root / "__missing_submission_source_markdown__.md").resolve() if worktree_root else Path("/__missing_submission_source_markdown__.md"))
        )
        docx_path, pdf_path = paper_artifacts.resolve_submission_minimal_output_paths(
            paper_bundle_manifest_path=paper_bundle_manifest_path,
            submission_minimal_manifest=submission_minimal_manifest,
        )
        manuscript_surface_qc = submission_minimal.build_submission_manuscript_surface_qc(
            publication_profile=infer_submission_publication_profile(submission_minimal_manifest),
            source_markdown_path=source_markdown_path,
            docx_path=docx_path or Path(""),
            pdf_path=pdf_path or Path(""),
            expected_main_figure_count=expected_main_figure_count,
        )
        failures.extend(manuscript_surface_qc.get("failures") or [])
    return failures


def gate_allows_write(
    latest_gate: dict[str, Any] | None,
    latest_gate_path: Path | None,
    main_result_path: Path | None,
) -> bool:
    if latest_gate is None or latest_gate_path is None or main_result_path is None:
        return False
    if latest_gate_path.stat().st_mtime < main_result_path.stat().st_mtime:
        return False
    gate_status = str(latest_gate.get("status") or "").strip().lower()
    if gate_status:
        return gate_status == "clear"
    return bool(latest_gate.get("allow_write"))


def resolve_write_drift_stdout_path(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    main_result: dict[str, Any] | None,
) -> Path | None:
    main_result_run_id = _non_empty_text((main_result or {}).get("run_id"))
    active_run_id = _non_empty_text(runtime_state.get("active_run_id"))
    if main_result is not None and (main_result_run_id is None or active_run_id != main_result_run_id):
        return None
    return quest_state.resolve_active_stdout_path(quest_root=quest_root, runtime_state=runtime_state)


def medical_publication_surface_report_current(
    *,
    latest_surface_path: Path | None,
    anchor_path: Path,
) -> bool:
    if latest_surface_path is None or not latest_surface_path.exists():
        return False
    return latest_surface_path.stat().st_mtime >= anchor_path.stat().st_mtime


def medical_publication_surface_currentness_anchor(state: GateState) -> Path:
    if state.anchor_kind == "paper_bundle" and state.paper_root is not None:
        authoritative_bundle_manifest = state.paper_root / "paper_bundle_manifest.json"
        if authoritative_bundle_manifest.exists():
            return authoritative_bundle_manifest
    return state.anchor_path


def resolve_compile_report_path(
    *,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> Path | None:
    if paper_bundle_manifest_path is None or paper_bundle_manifest is None:
        return None
    candidates = [
        str(paper_bundle_manifest.get("compile_report_path") or "").strip(),
        str((paper_bundle_manifest.get("bundle_inputs") or {}).get("compile_report_path") or "").strip(),
    ]
    worktree_root = paper_bundle_manifest_path.resolve().parent.parent
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if not path.is_absolute():
            path = worktree_root / path
        resolved = path.resolve()
        if resolved.exists():
            return resolved
    return None


def _resolve_gate_study_root(*, paper_root: Path | None) -> Path | None:
    if paper_root is None:
        return None
    try:
        context = study_delivery_sync._resolve_delivery_context(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return None
    return Path(context["study_root"]).expanduser().resolve()


def resolve_primary_journal_target(*, paper_root: Path | None) -> dict[str, Any] | None:
    if paper_root is None:
        return None
    payload = load_json(paper_root / "submission_targets.resolved.json", default=None)
    if not isinstance(payload, dict):
        return None
    primary = payload.get("primary_target")
    if not isinstance(primary, dict):
        return None
    journal_name = _non_empty_text(primary.get("journal_name"))
    official_guidelines_url = _non_empty_text(primary.get("official_guidelines_url"))
    if journal_name is None and official_guidelines_url is None:
        return None
    journal_slug = _non_empty_text(primary.get("journal_slug"))
    if journal_slug is None and journal_name is not None:
        journal_slug = slugify_journal_name(journal_name)
    if journal_slug is None:
        return None
    return {
        "journal_name": journal_name,
        "journal_slug": journal_slug,
        "official_guidelines_url": official_guidelines_url,
        "publication_profile": _non_empty_text(primary.get("publication_profile")),
        "citation_style": _non_empty_text(primary.get("citation_style")),
        "package_required": bool(primary.get("package_required", True)),
        "resolution_status": _non_empty_text(primary.get("resolution_status")),
    }


def resolve_journal_requirement_state(*, paper_root: Path | None) -> dict[str, Any]:
    study_root = _resolve_gate_study_root(paper_root=paper_root)
    primary_target = resolve_primary_journal_target(paper_root=paper_root)
    if study_root is None or primary_target is None or primary_target["package_required"] is not True:
        return {
            "status": "not_applicable",
            "study_root": str(study_root) if study_root is not None else None,
            "requirements_path": None,
        }
    requirements = load_journal_requirements(
        study_root=study_root,
        journal_slug=str(primary_target["journal_slug"]),
    )
    requirements_path = journal_requirements_json_path(
        study_root=study_root,
        journal_slug=str(primary_target["journal_slug"]),
    )
    return {
        "status": "resolved" if requirements is not None else "missing",
        "study_root": str(study_root),
        "requirements_path": str(requirements_path),
    }


def resolve_journal_package_state(*, paper_root: Path | None) -> dict[str, Any]:
    study_root = _resolve_gate_study_root(paper_root=paper_root)
    primary_target = resolve_primary_journal_target(paper_root=paper_root)
    if study_root is None or primary_target is None or primary_target["package_required"] is not True:
        return {
            "status": "not_applicable",
            "package_root": None,
            "submission_manifest_path": None,
            "zip_path": None,
        }
    return describe_journal_submission_package(
        study_root=study_root,
        journal_slug=str(primary_target["journal_slug"]),
    )


def resolve_primary_anchor(
    *,
    quest_root: Path,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> tuple[str, Path, Path | None, dict[str, Any] | None]:
    try:
        main_result_path = quest_state.find_latest_main_result_path(quest_root)
    except FileNotFoundError:
        main_result_path = None
    if main_result_path is not None:
        return "main_result", main_result_path, main_result_path, load_json(main_result_path)
    if paper_bundle_manifest_path is not None and paper_bundle_manifest is not None:
        return "paper_bundle", paper_bundle_manifest_path, None, None
    return "missing", quest_root, None, None


def build_gate_state(quest_root: Path) -> GateState:
    runtime_state = quest_state.load_runtime_state(quest_root)
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(quest_root)
    paper_bundle_manifest = load_json(paper_bundle_manifest_path) if paper_bundle_manifest_path else None
    projected_paper_line_state_path = (
        paper_bundle_manifest_path.parent / "paper_line_state.json"
        if paper_bundle_manifest_path is not None
        else None
    )
    projected_paper_line_state = (
        load_json(projected_paper_line_state_path)
        if projected_paper_line_state_path is not None and projected_paper_line_state_path.exists()
        else None
    )
    anchor_kind, anchor_path, main_result_path, main_result = resolve_primary_anchor(
        quest_root=quest_root,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    paper_root = resolve_paper_root(
        quest_root=quest_root,
        main_result=main_result,
        paper_line_state=projected_paper_line_state,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    study_root = _resolve_gate_study_root(paper_root=paper_root)
    charter_contract_linkage = study_delivery_sync.build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=None,
        review_ledger_path=None,
    )
    authoritative_paper_line_state_path = paper_root / "paper_line_state.json" if paper_root is not None else None
    authoritative_paper_line_state = (
        load_json(authoritative_paper_line_state_path)
        if authoritative_paper_line_state_path is not None and authoritative_paper_line_state_path.exists()
        else None
    )
    paper_line_state_path = authoritative_paper_line_state_path or projected_paper_line_state_path
    paper_line_state = (
        authoritative_paper_line_state
        if authoritative_paper_line_state is not None
        else projected_paper_line_state
    )
    compile_report_path = resolve_compile_report_path(
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    compile_report = load_json(compile_report_path) if compile_report_path else None
    latest_gate_path = find_latest_gate_report(quest_root)
    latest_gate = load_json(latest_gate_path) if latest_gate_path else None
    latest_medical_publication_surface_path = find_latest_medical_publication_surface_report(
        quest_root,
        paper_root=paper_root,
        study_root=study_root,
    )
    latest_medical_publication_surface = (
        load_json(latest_medical_publication_surface_path) if latest_medical_publication_surface_path else None
    )
    stdout_path = resolve_write_drift_stdout_path(
        quest_root=quest_root,
        runtime_state=runtime_state,
        main_result=main_result if anchor_kind == "main_result" else None,
    )
    recent_lines = quest_state.read_recent_stdout_lines(stdout_path)
    if main_result_path is not None and main_result is not None:
        present_deliverables, missing_deliverables = classify_deliverables(main_result_path, main_result)
    else:
        present_deliverables, missing_deliverables = [], []
    submission_checklist_path = resolve_submission_checklist_path(paper_root=paper_root)
    submission_checklist = load_submission_checklist(paper_root=paper_root)
    submission_minimal_manifest_path = resolve_submission_minimal_manifest(paper_root=paper_root)
    submission_minimal_manifest = (
        load_json(submission_minimal_manifest_path) if submission_minimal_manifest_path else None
    )
    submission_minimal_docx_path, submission_minimal_pdf_path = resolve_submission_minimal_output_paths(
        paper_root=paper_root,
        submission_minimal_manifest=submission_minimal_manifest,
    )
    submission_surface_qc_failures = collect_submission_surface_qc_failures(
        submission_minimal_manifest,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_root=paper_root,
    )
    archived_submission_surface_roots = (
        [str(path) for path in paper_artifacts.resolve_archived_submission_surface_roots(paper_root)]
        if paper_root is not None
        else []
    )
    unmanaged_submission_surface_roots = (
        [str(path) for path in paper_artifacts.find_unmanaged_submission_surface_roots(paper_root)]
        if paper_root is not None
        else []
    )
    manuscript_terminology_violations = detect_manuscript_terminology_violations(paper_root)
    study_delivery = (
        study_delivery_sync.describe_submission_delivery(paper_root=paper_root)
        if paper_root is not None and study_delivery_sync.can_sync_study_delivery(paper_root=paper_root)
        else None
    )
    draft_handoff_delivery = (
        study_delivery_sync.describe_draft_handoff_delivery(paper_root=paper_root)
        if paper_root is not None and study_delivery_sync.can_sync_study_delivery(paper_root=paper_root)
        else None
    )
    return GateState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        study_root=study_root,
        charter_contract_linkage=charter_contract_linkage,
        anchor_kind=anchor_kind,
        anchor_path=anchor_path,
        paper_line_state_path=paper_line_state_path if paper_line_state is not None else None,
        paper_line_state=paper_line_state,
        main_result_path=main_result_path,
        main_result=main_result,
        paper_root=paper_root,
        compile_report_path=compile_report_path,
        compile_report=compile_report,
        latest_gate_path=latest_gate_path,
        latest_gate=latest_gate,
        latest_medical_publication_surface_path=latest_medical_publication_surface_path,
        latest_medical_publication_surface=latest_medical_publication_surface,
        active_run_stdout_path=stdout_path,
        recent_stdout_lines=recent_lines,
        write_drift_detected=detect_write_drift(recent_lines),
        missing_deliverables=missing_deliverables,
        present_deliverables=present_deliverables,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
        submission_checklist_path=submission_checklist_path,
        submission_checklist=submission_checklist,
        submission_minimal_manifest_path=submission_minimal_manifest_path,
        submission_minimal_manifest=submission_minimal_manifest,
        submission_minimal_docx_present=bool(submission_minimal_docx_path and submission_minimal_docx_path.exists()),
        submission_minimal_pdf_present=bool(submission_minimal_pdf_path and submission_minimal_pdf_path.exists()),
        submission_surface_qc_failures=submission_surface_qc_failures,
        archived_submission_surface_roots=archived_submission_surface_roots,
        unmanaged_submission_surface_roots=unmanaged_submission_surface_roots,
        manuscript_terminology_violations=manuscript_terminology_violations,
        study_delivery=study_delivery,
        draft_handoff_delivery=draft_handoff_delivery,
    )


def build_gate_report(state: GateState) -> dict[str, Any]:
    baseline_items = (state.main_result or {}).get("baseline_comparisons", {}).get("items") or []
    primary_delta = None
    for item in baseline_items:
        if item.get("metric_id") == "roc_auc":
            primary_delta = item.get("delta")
            break
    latest_gate_up_to_date = (
        state.latest_gate_path is not None and state.latest_gate_path.stat().st_mtime >= state.anchor_path.stat().st_mtime
    )
    medical_publication_surface_current = medical_publication_surface_report_current(
        latest_surface_path=state.latest_medical_publication_surface_path,
        anchor_path=medical_publication_surface_currentness_anchor(state),
    )
    charter_contract_linkage_status = str((state.charter_contract_linkage or {}).get("status") or "").strip()
    submission_checklist_blocking_items = list(
        paper_artifacts.normalize_submission_checklist_blocking_item_keys(state.submission_checklist)
    )
    submission_checklist_handoff_ready = bool(
        isinstance(state.submission_checklist, dict) and state.submission_checklist.get("handoff_ready") is True
    )
    non_scientific_handoff_gaps = [
        item for item in submission_checklist_blocking_items if item in _NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS
    ]
    submission_checklist_unclassified_blocking_items = [
        item for item in submission_checklist_blocking_items if item not in _NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS
    ]
    closure_bundle_ready = submission_checklist_handoff_ready and not submission_checklist_unclassified_blocking_items
    study_delivery = state.study_delivery or {}
    study_delivery_status = str(study_delivery.get("status") or "").strip() or "not_applicable"
    draft_handoff_delivery = state.draft_handoff_delivery or {}
    primary_journal_target = resolve_primary_journal_target(paper_root=state.paper_root)
    journal_requirements_state = resolve_journal_requirement_state(paper_root=state.paper_root)
    journal_package_state = resolve_journal_package_state(paper_root=state.paper_root)
    paper_line_open_supplementary_count = _paper_line_open_supplementary_count(state.paper_line_state)
    paper_line_recommended_action = _paper_line_recommended_action(state.paper_line_state)
    paper_line_blocking_reasons = _paper_line_blocking_reasons(state.paper_line_state)
    active_figure_count = active_manuscript_figure_count(state.paper_root)
    prebundle_display_advisories: list[str] = []
    prebundle_display_floor_pending = False
    prebundle_display_floor_gap: int | None = None
    if active_figure_count is not None and active_figure_count < _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES:
        prebundle_display_floor_pending = True
        prebundle_display_floor_gap = _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES - active_figure_count
        prebundle_display_advisories.append("submission_grade_active_figure_floor_unmet")
    draft_handoff_delivery_required = bool(
        submission_checklist_handoff_ready
        and state.submission_minimal_manifest is None
        and draft_handoff_delivery.get("applicable") is True
    )
    draft_handoff_delivery_status = (
        str(draft_handoff_delivery.get("status") or "").strip() or "not_applicable"
    )
    blockers: list[str] = []
    bundle_stage_ready = bool(
        state.paper_bundle_manifest_path is not None
        and state.paper_bundle_manifest is not None
        and state.compile_report_path is not None
        and state.compile_report is not None
        and (
            closure_bundle_ready
            or (
                state.submission_minimal_manifest is not None
                and state.submission_minimal_docx_present
                and state.submission_minimal_pdf_present
            )
        )
    )
    if state.anchor_kind == "main_result":
        prior_gate_allows_write = gate_allows_write(state.latest_gate, state.latest_gate_path, state.main_result_path)
        allow_write = prior_gate_allows_write
        if not latest_gate_up_to_date:
            blockers.append("missing_post_main_publishability_gate")
        if state.missing_deliverables:
            blockers.append("missing_required_non_scalar_deliverables")
        if state.write_drift_detected and not prior_gate_allows_write:
            blockers.append("active_run_drifting_into_write_without_gate_approval")
    elif state.anchor_kind == "paper_bundle":
        allow_write = (
            state.compile_report_path is not None
            and state.compile_report is not None
            and (
                closure_bundle_ready
                or (
                    state.submission_minimal_manifest is not None
                    and state.submission_minimal_docx_present
                    and state.submission_minimal_pdf_present
                )
            )
        )
        if state.compile_report_path is None or state.compile_report is None:
            blockers.append("missing_paper_compile_report")
        if submission_checklist_handoff_ready and submission_checklist_unclassified_blocking_items:
            blockers.append("submission_checklist_contains_unclassified_blocking_items")
        if (
            not closure_bundle_ready
            and (
                state.submission_minimal_manifest is None
                or not state.submission_minimal_docx_present
                or not state.submission_minimal_pdf_present
            )
        ):
            blockers.append("missing_submission_minimal")
        if not medical_publication_surface_current and not closure_bundle_ready:
            blockers.append("missing_current_medical_publication_surface_report")
        if _paper_line_requires_required_supplementary(state.paper_line_state):
            blockers.append("paper_line_required_supplementary_pending")
        if (
            active_figure_count is not None
            and active_figure_count < _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES
        ):
            blockers.append("submission_grade_active_figure_floor_unmet")
    else:
        allow_write = False
        blockers.append("missing_publication_anchor")

    results_summary = None
    conclusion = None
    if state.main_result is not None:
        results_summary = state.main_result.get("results_summary")
        conclusion = state.main_result.get("conclusion")
    if not results_summary:
        results_summary = (state.compile_report or {}).get("summary") or (state.paper_bundle_manifest or {}).get("summary")
    if not conclusion:
        conclusion = (state.paper_bundle_manifest or {}).get("summary") or (state.compile_report or {}).get("summary")
    if state.unmanaged_submission_surface_roots:
        blockers.append("unmanaged_submission_surface_present")
    if charter_contract_linkage_status in {"study_charter_missing", "study_charter_invalid"}:
        blockers.append(charter_contract_linkage_status)
    if study_delivery_status.startswith("stale"):
        blockers.append("stale_study_delivery_mirror")
    medical_publication_surface_status = str((state.latest_medical_publication_surface or {}).get("status") or "").strip()
    if medical_publication_surface_current:
        medical_publication_surface_named_blockers = _medical_publication_surface_named_blockers(
            state.latest_medical_publication_surface
        )
        medical_publication_surface_route_back_recommendation = _medical_publication_surface_route_back_recommendation(
            medical_publication_surface_named_blockers
        )
    else:
        medical_publication_surface_named_blockers = []
        medical_publication_surface_route_back_recommendation = None
    if medical_publication_surface_current and medical_publication_surface_status and medical_publication_surface_status != "clear":
        blockers.append("medical_publication_surface_blocked")
        blockers.extend(medical_publication_surface_named_blockers)
    if state.submission_surface_qc_failures:
        blockers.append("submission_surface_qc_failure_present")
    if state.manuscript_terminology_violations:
        blockers.append("forbidden_manuscript_terminology")
    if primary_journal_target is not None and primary_journal_target["package_required"] is True:
        if journal_requirements_state["status"] == "missing":
            blockers.append("missing_journal_requirements")
        elif journal_package_state["status"] != "current":
            blockers.append("missing_journal_package")
    if state.anchor_kind == "main_result":
        allow_write = not blockers
    else:
        allow_write = allow_write and not blockers
    if allow_write:
        paper_line_recommended_action = publication_gate_policy.CLEAR_RECOMMENDED_ACTION
        paper_line_blocking_reasons = []
    supervisor_state = build_publication_supervisor_state(
        anchor_kind=state.anchor_kind,
        allow_write=allow_write,
        blockers=blockers,
        bundle_stage_ready=bundle_stage_ready,
    )
    if charter_contract_linkage_status == "study_charter_missing":
        supervisor_state = {
            **supervisor_state,
            "controller_stage_note": (
                "stable study charter artifact is missing; restore the controller-owned paper-direction contract "
                "before autonomous publication work continues"
            ),
        }
    elif charter_contract_linkage_status == "study_charter_invalid":
        supervisor_state = {
            **supervisor_state,
            "controller_stage_note": (
                "stable study charter artifact is invalid; repair the controller-owned paper-direction contract "
                "before autonomous publication work continues"
            ),
        }
    controller_stage_note = _medical_publication_surface_stage_note(
        base_note=str(supervisor_state["controller_stage_note"]),
        named_blockers=medical_publication_surface_named_blockers,
        route_back_recommendation=medical_publication_surface_route_back_recommendation,
    )

    return {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": utc_now(),
        "anchor_kind": state.anchor_kind,
        "anchor_path": str(state.anchor_path),
        "quest_id": (state.main_result or {}).get("quest_id") or state.quest_root.name,
        "run_id": (
            (state.main_result or {}).get("run_id")
            or (state.paper_line_state or {}).get("paper_line_id")
            or state.runtime_state.get("active_run_id")
        ),
        "main_result_path": str(state.main_result_path) if state.main_result_path else None,
        "paper_line_state_path": str(state.paper_line_state_path) if state.paper_line_state_path else None,
        "paper_root": str(state.paper_root) if state.paper_root else None,
        "compile_report_path": str(state.compile_report_path) if state.compile_report_path else None,
        "latest_gate_path": str(state.latest_gate_path) if state.latest_gate_path else None,
        "medical_publication_surface_report_path": (
            str(state.latest_medical_publication_surface_path) if state.latest_medical_publication_surface_path else None
        ),
        "medical_publication_surface_current": medical_publication_surface_current,
        "allow_write": allow_write,
        "recommended_action": (
            publication_gate_policy.BLOCKED_RECOMMENDED_ACTION
            if blockers
            else publication_gate_policy.CLEAR_RECOMMENDED_ACTION
        ),
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "write_drift_detected": state.write_drift_detected,
        "required_non_scalar_deliverables": list(
            (state.main_result or {}).get("metric_contract", {}).get("required_non_scalar_deliverables") or []
        ),
        "present_non_scalar_deliverables": state.present_deliverables,
        "missing_non_scalar_deliverables": state.missing_deliverables,
        "paper_bundle_manifest_path": str(state.paper_bundle_manifest_path) if state.paper_bundle_manifest_path else None,
        "submission_checklist_path": str(state.submission_checklist_path) if state.submission_checklist_path else None,
        "submission_checklist_present": state.submission_checklist is not None,
        "submission_checklist_overall_status": (
            str((state.submission_checklist or {}).get("overall_status") or "").strip() or None
        ),
        "submission_checklist_handoff_ready": submission_checklist_handoff_ready,
        "submission_checklist_blocking_items": submission_checklist_blocking_items,
        "submission_checklist_unclassified_blocking_items": submission_checklist_unclassified_blocking_items,
        "non_scientific_handoff_gaps": non_scientific_handoff_gaps,
        "closure_bundle_ready": closure_bundle_ready,
        "submission_minimal_manifest_path": (
            str(state.submission_minimal_manifest_path) if state.submission_minimal_manifest_path else None
        ),
        "submission_minimal_present": state.submission_minimal_manifest is not None,
        "submission_minimal_docx_present": state.submission_minimal_docx_present,
        "submission_minimal_pdf_present": state.submission_minimal_pdf_present,
        "study_delivery_status": study_delivery_status,
        "study_delivery_stale_reason": _non_empty_text(study_delivery.get("stale_reason")),
        "study_delivery_manifest_path": _non_empty_text(study_delivery.get("delivery_manifest_path")),
        "study_delivery_current_package_root": _non_empty_text(study_delivery.get("current_package_root")),
        "study_delivery_current_package_zip": _non_empty_text(study_delivery.get("current_package_zip")),
        "study_delivery_missing_source_paths": list(study_delivery.get("missing_source_paths") or []),
        "primary_journal_target": primary_journal_target,
        "journal_requirements_status": journal_requirements_state["status"],
        "journal_requirements_path": journal_requirements_state.get("requirements_path"),
        "journal_requirements_study_root": journal_requirements_state.get("study_root"),
        "journal_package_status": journal_package_state["status"],
        "journal_package_root": journal_package_state.get("package_root"),
        "journal_package_manifest_path": journal_package_state.get("submission_manifest_path"),
        "journal_package_zip_path": journal_package_state.get("zip_path"),
        "draft_handoff_delivery_required": draft_handoff_delivery_required,
        "draft_handoff_delivery_status": draft_handoff_delivery_status,
        "draft_handoff_delivery_manifest_path": _non_empty_text(draft_handoff_delivery.get("delivery_manifest_path")),
        "draft_handoff_current_package_root": _non_empty_text(draft_handoff_delivery.get("current_package_root")),
        "draft_handoff_current_package_zip": _non_empty_text(draft_handoff_delivery.get("current_package_zip")),
        "paper_line_open_supplementary_count": paper_line_open_supplementary_count,
        "paper_line_recommended_action": paper_line_recommended_action,
        "paper_line_blocking_reasons": paper_line_blocking_reasons,
        "active_manuscript_figure_count": active_figure_count,
        "submission_grade_min_active_figures": _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES,
        "prebundle_display_floor_pending": prebundle_display_floor_pending,
        "prebundle_display_floor_gap": prebundle_display_floor_gap,
        "prebundle_display_advisories": prebundle_display_advisories,
        "medical_publication_surface_status": medical_publication_surface_status or None,
        "charter_contract_linkage": dict(state.charter_contract_linkage or {}),
        "charter_contract_linkage_status": charter_contract_linkage_status or None,
        "medical_publication_surface_named_blockers": medical_publication_surface_named_blockers,
        "medical_publication_surface_route_back_recommendation": medical_publication_surface_route_back_recommendation,
        "submission_surface_qc_failures": list(state.submission_surface_qc_failures),
        "archived_submission_surface_roots": list(state.archived_submission_surface_roots),
        "unmanaged_submission_surface_roots": list(state.unmanaged_submission_surface_roots),
        "manuscript_terminology_violations": list(state.manuscript_terminology_violations),
        "headline_metrics": (state.main_result or {}).get("metrics_summary") or {},
        "primary_metric_delta_vs_baseline": primary_delta,
        "results_summary": results_summary,
        "conclusion": conclusion,
        "controller_note": publication_gate_policy.CONTROLLER_NOTE,
        **supervisor_state,
        "controller_stage_note": controller_stage_note,
    }


def _bundle_stage_is_on_critical_path(*, blockers: list[str]) -> bool:
    normalized_blockers = {str(item or "").strip() for item in blockers if str(item or "").strip()}
    return bool(normalized_blockers) and normalized_blockers.issubset(_BUNDLE_STAGE_ONLY_BLOCKERS)


def build_publication_supervisor_state(
    *,
    anchor_kind: str,
    allow_write: bool,
    blockers: list[str],
    bundle_stage_ready: bool = False,
) -> dict[str, Any]:
    deferred_downstream_actions: list[str] = []
    if anchor_kind == "missing":
        return {
            "supervisor_phase": "scientific_anchor_missing",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": False,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": (
                "bundle suggestions are downstream-only until the publication gate allows write"
            ),
        }
    if anchor_kind == "main_result":
        if allow_write:
            if bundle_stage_ready:
                return {
                    "supervisor_phase": "bundle_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_bundle_stage",
                    "deferred_downstream_actions": deferred_downstream_actions,
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            return {
                "supervisor_phase": "write_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_write_stage",
                "deferred_downstream_actions": deferred_downstream_actions,
                "controller_stage_note": "the publication gate allows write; writing-stage work is now on the critical path",
            }
        return {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        }
    if allow_write:
        return {
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        }
    if not _bundle_stage_is_on_critical_path(blockers=blockers):
        return {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": (
                "paper bundle exists, but the active blockers still belong to the publishability surface; "
                "bundle suggestions stay downstream-only until the gate clears"
            ),
        }
    return {
        "supervisor_phase": "bundle_stage_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "complete_bundle_stage",
        "deferred_downstream_actions": deferred_downstream_actions,
        "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
    }


def extract_publication_supervisor_state(report: dict[str, Any]) -> dict[str, Any]:
    return {key: report[key] for key in PUBLICATION_SUPERVISOR_KEYS}


def render_gate_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("blockers") or []
    medical_surface_named_blockers = report.get("medical_publication_surface_named_blockers") or []
    medical_surface_route_back_recommendation = report.get("medical_publication_surface_route_back_recommendation")
    missing = report.get("missing_non_scalar_deliverables") or []
    metrics = report.get("headline_metrics") or {}
    terminology_violations = report.get("manuscript_terminology_violations") or []
    submission_surface_qc_failures = report.get("submission_surface_qc_failures") or []
    non_scientific_handoff_gaps = report.get("non_scientific_handoff_gaps") or []
    submission_checklist_unclassified = report.get("submission_checklist_unclassified_blocking_items") or []
    lines = [
        "# Publishability Gate Control Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_id: `{report['quest_id']}`",
        f"- run_id: `{report['run_id']}`",
        f"- status: `{report['status']}`",
        f"- allow_write: `{str(report['allow_write']).lower()}`",
        f"- recommended_action: `{report['recommended_action']}`",
        "",
        "## Why Blocked" if blockers else "## Status",
        "",
    ]
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- No controller-level blocker detected.")
    if medical_surface_named_blockers:
        lines.extend(
            [
                "",
                "## Medical Publication Surface Route-Back",
                "",
            ]
        )
        lines.extend(f"- `{item}`" for item in medical_surface_named_blockers)
        lines.append(
            f"- route_back_recommendation: `{medical_surface_route_back_recommendation or 'return_to_publishability_gate'}`"
        )
    lines.extend(
        [
            "",
            "## Headline Metrics",
            "",
            f"- `roc_auc`: `{metrics.get('roc_auc')}`",
            f"- `average_precision`: `{metrics.get('average_precision')}`",
            f"- `brier_score`: `{metrics.get('brier_score')}`",
            f"- `calibration_intercept`: `{metrics.get('calibration_intercept')}`",
            f"- `calibration_slope`: `{metrics.get('calibration_slope')}`",
            "",
            "## Missing Contract Deliverables",
            "",
        ]
    )
    if missing:
        lines.extend(f"- `{item}`" for item in missing)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Paper Package Status",
            "",
            f"- `anchor_kind`: `{report.get('anchor_kind')}`",
            f"- `anchor_path`: `{report.get('anchor_path')}`",
            f"- `paper_root`: `{report.get('paper_root')}`",
            f"- `paper_bundle_manifest_path`: `{report.get('paper_bundle_manifest_path')}`",
            f"- `submission_checklist_path`: `{report.get('submission_checklist_path')}`",
            f"- `submission_checklist_handoff_ready`: `{str(report.get('submission_checklist_handoff_ready')).lower()}`",
            f"- `closure_bundle_ready`: `{str(report.get('closure_bundle_ready')).lower()}`",
            f"- `compile_report_path`: `{report.get('compile_report_path')}`",
            f"- `submission_minimal_manifest_path`: `{report.get('submission_minimal_manifest_path')}`",
            f"- `submission_minimal_present`: `{str(report.get('submission_minimal_present')).lower()}`",
            f"- `submission_minimal_docx_present`: `{str(report.get('submission_minimal_docx_present')).lower()}`",
            f"- `submission_minimal_pdf_present`: `{str(report.get('submission_minimal_pdf_present')).lower()}`",
            f"- `draft_handoff_delivery_required`: `{str(report.get('draft_handoff_delivery_required')).lower()}`",
            f"- `draft_handoff_delivery_status`: `{report.get('draft_handoff_delivery_status')}`",
            f"- `draft_handoff_delivery_manifest_path`: `{report.get('draft_handoff_delivery_manifest_path')}`",
            f"- `draft_handoff_current_package_root`: `{report.get('draft_handoff_current_package_root')}`",
            f"- `paper_line_open_supplementary_count`: `{report.get('paper_line_open_supplementary_count')}`",
            f"- `paper_line_recommended_action`: `{report.get('paper_line_recommended_action')}`",
            f"- `active_manuscript_figure_count`: `{report.get('active_manuscript_figure_count')}`",
            f"- `submission_grade_min_active_figures`: `{report.get('submission_grade_min_active_figures')}`",
            f"- `study_delivery_current_package_root`: `{report.get('study_delivery_current_package_root')}`",
            f"- `medical_publication_surface_report_path`: `{report.get('medical_publication_surface_report_path')}`",
            f"- `medical_publication_surface_status`: `{report.get('medical_publication_surface_status')}`",
            f"- `medical_publication_surface_current`: `{str(report.get('medical_publication_surface_current')).lower()}`",
        ]
    )
    paper_line_blocking_reasons = report.get("paper_line_blocking_reasons") or []
    if paper_line_blocking_reasons:
        lines.extend(
            [
                "",
                "## Paper-Line Scientific Blockers",
                "",
                *[f"- `{item}`" for item in paper_line_blocking_reasons],
            ]
        )
    if non_scientific_handoff_gaps:
        lines.extend(
            [
                "",
                "## Non-Scientific Handoff Gaps",
                "",
                *[f"- `{item}`" for item in non_scientific_handoff_gaps],
            ]
        )
    if submission_checklist_unclassified:
        lines.extend(
            [
                "",
                "## Unclassified Submission Checklist Gaps",
                "",
                *[f"- `{item}`" for item in submission_checklist_unclassified],
            ]
        )
    unmanaged_roots = report.get("unmanaged_submission_surface_roots") or []
    archived_roots = report.get("archived_submission_surface_roots") or []
    if archived_roots:
        lines.extend(
            [
                "",
                "## Archived Legacy Submission Surfaces",
                "",
                *[f"- `{item}`" for item in archived_roots],
            ]
        )
    if unmanaged_roots:
        lines.extend(
            [
                "",
                "## Unmanaged Submission Surfaces",
                "",
                *[f"- `{item}`" for item in unmanaged_roots],
            ]
        )
    if submission_surface_qc_failures:
        lines.extend(
            [
                "",
                "## Submission Surface QC Failures",
                "",
            ]
        )
        lines.extend(
            "- `{collection}` `{item_id}` ({descriptor}) failed `{qc_profile}` with `{failure_reason}` audit classes {audit_classes}".format(
                collection=item.get("collection"),
                item_id=item.get("item_id"),
                descriptor=item.get("descriptor") or "unlabeled",
                qc_profile=item.get("qc_profile") or "unknown_qc_profile",
                failure_reason=item.get("failure_reason") or "unspecified_failure",
                audit_classes=item.get("audit_classes") or [],
            )
            for item in submission_surface_qc_failures
        )
    else:
        lines.extend(
            [
                "",
                "## Submission Surface QC Failures",
                "",
                "- None",
            ]
        )
    if terminology_violations:
        lines.extend(
            [
                "",
                "## Forbidden Manuscript Terminology",
                "",
            ]
        )
        lines.extend(
            f"- `{item['label']}` matched `{item['match']}` in `{item['path']}`" for item in terminology_violations
        )
    else:
        lines.extend(
            [
                "",
                "## Forbidden Manuscript Terminology",
                "",
                "- None",
            ]
        )
    lines.extend(
        [
            "",
            "## Result Context",
            "",
            f"- {report.get('results_summary')}",
            f"- {report.get('conclusion')}",
            "",
            "## Controller Scope",
            "",
            f"- {report.get('controller_note')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_gate_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="publishability_gate",
        timestamp=str(report["generated_at"]),
        report=report,
        markdown=render_gate_markdown(report),
    )


def _materialize_publication_eval_latest(
    *,
    state: GateState,
    report: dict[str, Any],
) -> dict[str, str] | None:
    if state.paper_root is None:
        return None
    try:
        paper_context = resolve_paper_root_context(state.paper_root)
    except (FileNotFoundError, ValueError):
        return None
    decision_module = import_module("med_autoscience.controllers.study_runtime_decision")
    return decision_module._materialize_publication_eval_from_gate_report(
        study_root=paper_context.study_root,
        study_id=paper_context.study_id,
        quest_root=state.quest_root,
        quest_id=paper_context.quest_id,
        publication_gate_report=report,
    )


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    source: str = "codex-publication-gate",
) -> dict[str, Any]:
    state = build_gate_state(quest_root)
    report = build_gate_report(state)
    draft_handoff_delivery_sync = None
    study_delivery_stale_sync = None
    journal_package_sync = None
    if (
        apply
        and report.get("draft_handoff_delivery_required") is True
        and report.get("draft_handoff_delivery_status") in {"missing", "stale", "invalid"}
        and state.paper_root is not None
        and study_delivery_sync.can_sync_study_delivery(paper_root=state.paper_root)
    ):
        draft_handoff_delivery_sync = study_delivery_sync.sync_study_delivery(
            paper_root=state.paper_root,
            stage="draft_handoff",
        )
        state = build_gate_state(quest_root)
        report = build_gate_report(state)
    if (
        apply
        and str(report.get("study_delivery_status") or "").strip().startswith("stale")
        and state.paper_root is not None
        and study_delivery_sync.can_sync_study_delivery(paper_root=state.paper_root)
    ):
        stale_reason = str(report.get("study_delivery_stale_reason") or "current_submission_source_missing")
        if stale_reason in {
            "delivery_projection_missing",
            "delivery_manifest_source_changed",
            "delivery_manifest_source_mismatch",
        }:
            study_delivery_stale_sync = study_delivery_sync.sync_study_delivery(
                paper_root=state.paper_root,
                stage="submission_minimal",
            )
        else:
            study_delivery_stale_sync = study_delivery_sync.materialize_submission_delivery_stale_notice(
                paper_root=state.paper_root,
                stale_reason=stale_reason,
                missing_source_paths=list(report.get("study_delivery_missing_source_paths") or []),
        )
        state = build_gate_state(quest_root)
        report = build_gate_report(state)
    if (
        apply
        and state.paper_root is not None
        and isinstance(report.get("primary_journal_target"), dict)
        and str(report.get("journal_requirements_status") or "").strip() == "resolved"
        and str(report.get("journal_package_status") or "").strip() in {"missing", "incomplete"}
        and _non_empty_text(report.get("journal_requirements_study_root"))
    ):
        primary_journal_target = report["primary_journal_target"]
        journal_package_sync = journal_package_controller.materialize_journal_package(
            paper_root=state.paper_root,
            study_root=Path(str(report["journal_requirements_study_root"])),
            journal_slug=str(primary_journal_target["journal_slug"]),
            publication_profile=_non_empty_text(primary_journal_target.get("publication_profile")),
        )
        state = build_gate_state(quest_root)
        report = build_gate_report(state)
    json_path, md_path = write_gate_files(quest_root, report)
    if apply:
        _materialize_publication_eval_latest(
            state=state,
            report={
                **report,
                "latest_gate_path": str(json_path),
            },
        )
    intervention = None
    if apply and report["blockers"]:
        intervention = user_message.enqueue_user_message(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=publication_gate_policy.build_intervention_message(report),
            source=source,
        )
    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "allow_write": report["allow_write"],
        "blockers": report["blockers"],
        "missing_non_scalar_deliverables": report["missing_non_scalar_deliverables"],
        "submission_minimal_present": report["submission_minimal_present"],
        "draft_handoff_delivery_required": report["draft_handoff_delivery_required"],
        "draft_handoff_delivery_status": report["draft_handoff_delivery_status"],
        "draft_handoff_delivery_manifest_path": report["draft_handoff_delivery_manifest_path"],
        "draft_handoff_delivery_sync": draft_handoff_delivery_sync,
        "study_delivery_stale_sync": study_delivery_stale_sync,
        "journal_package_sync": journal_package_sync,
        "intervention_enqueued": bool(intervention),
        "message_id": intervention.get("message_id") if intervention else None,
        "source": source,
        **extract_publication_supervisor_state(report),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_controller(quest_root=args.quest_root, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
