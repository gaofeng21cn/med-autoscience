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
from med_autoscience.policies.medical_reporting_checklist import REPORTING_CHECKLIST_BLOCKER_KEYS
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
        "stale_submission_minimal_authority",
        "missing_journal_package",
        "stale_study_delivery_mirror",
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
        *REPORTING_CHECKLIST_BLOCKER_KEYS,
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


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


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
    expectation_gap_ledgers = {
        str(item.get("ledger_name") or "").strip()
        for item in _medical_publication_surface_expectation_gaps(surface_report)
    }
    named_blockers: list[str] = []
    if (
        surface_report.get("review_ledger_valid") is False
        or surface_blockers.intersection(_MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS)
        or "review_ledger" in expectation_gap_ledgers
    ):
        _append_unique(named_blockers, "reviewer_first_concerns_unresolved")
    if (
        surface_report.get("claim_evidence_map_valid") is False
        or surface_report.get("evidence_ledger_valid") is False
        or surface_report.get("medical_story_contract_valid") is False
        or surface_blockers.intersection(_MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS)
        or "evidence_ledger" in expectation_gap_ledgers
    ):
        _append_unique(named_blockers, "claim_evidence_consistency_failed")
    if surface_blockers.intersection(_MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS):
        _append_unique(named_blockers, "submission_hardening_incomplete")
    return named_blockers


def _medical_publication_surface_expectation_gaps(surface_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(surface_report, dict):
        return []
    raw_gaps = surface_report.get("charter_expectation_closure_gaps")
    if not isinstance(raw_gaps, list):
        summary = surface_report.get("charter_expectation_closure_summary")
        raw_gaps = summary.get("blocking_items") if isinstance(summary, dict) else []
    if not isinstance(raw_gaps, list):
        return []

    gaps: list[dict[str, Any]] = []
    for raw_gap in raw_gaps:
        if not isinstance(raw_gap, dict):
            continue
        expectation_key = str(raw_gap.get("expectation_key") or "").strip()
        expectation_text = str(raw_gap.get("expectation_text") or "").strip()
        ledger_name = str(raw_gap.get("ledger_name") or "").strip()
        contract_json_pointer = str(raw_gap.get("contract_json_pointer") or "").strip()
        closure_status = str(raw_gap.get("closure_status") or "").strip()
        if (
            not expectation_key
            or not expectation_text
            or not ledger_name
            or not contract_json_pointer
            or not closure_status
        ):
            continue
        gaps.append(
            {
                "expectation_key": expectation_key,
                "expectation_text": expectation_text,
                "ledger_name": ledger_name,
                "ledger_path": _non_empty_text(raw_gap.get("ledger_path")),
                "contract_json_pointer": contract_json_pointer,
                "closure_status": closure_status,
                "recorded": bool(raw_gap.get("recorded")),
                "record_count": int(raw_gap.get("record_count") or 0),
                "blocker": bool(raw_gap.get("blocker")),
                "closed_at": _non_empty_text(raw_gap.get("closed_at")),
                "note": _non_empty_text(raw_gap.get("note")),
            }
        )
    return gaps


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
