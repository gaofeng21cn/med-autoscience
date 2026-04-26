from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from med_autoscience.controllers._medical_display_surface_support import resolve_required_display_surface_stub
from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.policies.medical_reporting_checklist import build_structured_reporting_checklist
from med_autoscience.runtime_protocol import paper_artifacts
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json_dict(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _quality_gate_expectation(reporting_contract: dict[str, object]) -> dict[str, object]:
    candidates: list[object] = [
        reporting_contract.get("quality_gate_expectation"),
    ]
    structured_contract = reporting_contract.get("structured_reporting_contract")
    if isinstance(structured_contract, dict):
        candidates.append(structured_contract.get("quality_gate_expectation"))
    reporting_guideline_expectation = reporting_contract.get("reporting_guideline_expectation")
    if isinstance(reporting_guideline_expectation, dict):
        candidates.append(reporting_guideline_expectation.get("quality_gate_expectation"))
    for candidate in candidates:
        if isinstance(candidate, dict):
            return dict(candidate)
    return {}


def _quality_gate_relaxation_allowed(reporting_contract: dict[str, object]) -> bool:
    expectation = _quality_gate_expectation(reporting_contract)
    if expectation.get("gate_relaxation_allowed") is False:
        return False
    return True


def _normalize_display_shell_plan(reporting_contract: dict[str, object]) -> list[dict[str, str]]:
    plan = reporting_contract.get("display_shell_plan")
    normalized: list[dict[str, str]] = []
    if isinstance(plan, list):
        for item in plan:
            if not isinstance(item, dict):
                continue
            display_id = str(item.get("display_id") or "").strip()
            display_kind = str(item.get("display_kind") or "").strip()
            requirement_key = str(item.get("requirement_key") or "").strip()
            if not display_id or not display_kind or not requirement_key:
                continue
            normalized.append(
                {
                    "display_id": display_id,
                    "display_kind": display_kind,
                    "requirement_key": requirement_key,
                }
            )
        return normalized

    figure_shell_requirements = list(reporting_contract.get("figure_shell_requirements") or [])
    table_shell_requirements = list(reporting_contract.get("table_shell_requirements") or [])
    cohort_flow_required = reporting_contract.get("cohort_flow_required")
    baseline_required = reporting_contract.get("baseline_characteristics_required")
    if cohort_flow_required is False:
        cohort_flow_enabled = False
    elif figure_shell_requirements:
        cohort_flow_enabled = "cohort_flow_figure" in figure_shell_requirements
    else:
        cohort_flow_enabled = True
    if baseline_required is False:
        baseline_enabled = False
    elif table_shell_requirements:
        baseline_enabled = "table1_baseline_characteristics" in table_shell_requirements
    else:
        baseline_enabled = True

    if cohort_flow_enabled:
        normalized.append(
            {
                "display_id": "Figure1",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
            }
        )
    if baseline_enabled:
        normalized.append(
            {
                "display_id": "Table1",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
            }
        )
    return normalized


def _medical_story_contract_is_valid(paper_root: Path) -> bool:
    required_contracts = (
        (
            paper_root / medical_surface_policy.RESULTS_NARRATIVE_MAP_BASENAME,
            medical_surface_policy.validate_results_narrative_map,
        ),
        (
            paper_root / medical_surface_policy.FIGURE_SEMANTICS_MANIFEST_BASENAME,
            medical_surface_policy.validate_figure_semantics_manifest,
        ),
        (
            paper_root / medical_surface_policy.CLAIM_EVIDENCE_MAP_BASENAME,
            medical_surface_policy.validate_claim_evidence_map,
        ),
    )
    for path, validator in required_contracts:
        try:
            payload = _load_json_dict(path)
        except (OSError, ValueError, json.JSONDecodeError):
            return False
        if payload is None or validator(payload):
            return False
    return True


def render_audit_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Medical Reporting Audit Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_root: `{report['quest_root']}`",
        f"- status: `{report['status']}`",
        f"- action: `{report['action']}`",
        f"- blockers: `{', '.join(report.get('blockers') or ['none'])}`",
        f"- advisories: `{', '.join(report.get('advisories') or ['none'])}`",
        "",
    ]
    return "\n".join(lines)


def write_audit_files(quest_root: Path, report: dict[str, object]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="medical_reporting_audit",
        timestamp=str(report["generated_at"]),
        report=report,
        markdown=render_audit_markdown(report),
    )


def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    del apply
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    try:
        paper_root = paper_artifacts.resolve_latest_paper_root(resolved_quest_root)
    except FileNotFoundError:
        paper_root = resolved_quest_root / "paper"
    blockers: list[str] = []
    advisories: list[str] = []
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(resolved_quest_root)
    submission_checklist = paper_artifacts.load_submission_checklist(paper_bundle_manifest_path)
    submission_checklist_handoff_ready = bool(
        isinstance(submission_checklist, dict) and submission_checklist.get("handoff_ready") is True
    )
    submission_checklist_unclassified_blocking_items = list(
        paper_artifacts.normalize_submission_checklist_blocking_item_keys(submission_checklist)
    )
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    if not reporting_contract_path.exists():
        blockers.append("missing_medical_reporting_contract")
        reporting_contract: dict[str, object] = {}
    else:
        try:
            reporting_contract = _load_json_dict(reporting_contract_path) or {}
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("invalid_medical_reporting_contract")
            reporting_contract = {}
    quality_gate_expectation = _quality_gate_expectation(reporting_contract)
    quality_gate_relaxation_allowed = _quality_gate_relaxation_allowed(reporting_contract)

    display_shell_plan = _normalize_display_shell_plan(reporting_contract)
    if bool(reporting_contract.get("display_registry_required", bool(display_shell_plan))):
        display_registry_path = paper_root / "display_registry.json"
        if not display_registry_path.exists():
            blockers.append("missing_display_registry")
        else:
            try:
                display_registry = _load_json_dict(display_registry_path) or {}
            except (OSError, ValueError, json.JSONDecodeError):
                blockers.append("invalid_display_registry")
                display_registry = {}
            registry_items = display_registry.get("displays")
            if isinstance(registry_items, list):
                registry_keys = {
                    (
                        str(item.get("display_id") or "").strip(),
                        str(item.get("display_kind") or "").strip(),
                        str(item.get("requirement_key") or "").strip(),
                    )
                    for item in registry_items
                    if isinstance(item, dict)
                }
                contract_keys = {
                    (item["display_id"], item["display_kind"], item["requirement_key"])
                    for item in display_shell_plan
                }
                if registry_keys != contract_keys:
                    blockers.append("registry_contract_mismatch")
            else:
                blockers.append("invalid_display_registry")

    for item in display_shell_plan:
        if item["display_kind"] == "figure":
            shell_path = paper_root / "figures" / f"{item['display_id']}.shell.json"
            if not shell_path.exists():
                blockers.append(f"missing_{item['display_id'].lower()}_shell")
        else:
            shell_path = paper_root / "tables" / f"{item['display_id']}.shell.json"
            if not shell_path.exists():
                blockers.append(f"missing_{item['display_id'].lower()}_shell")

        stub = resolve_required_display_surface_stub(item["requirement_key"])
        if stub is None:
            continue
        if not (paper_root / stub.filename).exists():
            blockers.append(stub.blocker_key)

    if not (paper_root / "reporting_guideline_checklist.json").exists():
        if (
            quality_gate_relaxation_allowed
            and submission_checklist_handoff_ready
            and not submission_checklist_unclassified_blocking_items
        ):
            advisories.append("missing_reporting_guideline_checklist")
        else:
            blockers.append("missing_reporting_guideline_checklist")
    structured_reporting_checklist = build_structured_reporting_checklist(reporting_contract)
    blockers.extend(structured_reporting_checklist["blockers"])
    medical_story_contract_valid = _medical_story_contract_is_valid(paper_root)
    if not medical_story_contract_valid:
        blockers.append("missing_medical_story_contract")
    report = {
        "generated_at": utc_now(),
        "status": "blocked" if blockers else ("advisory" if advisories else "clear"),
        "blockers": blockers,
        "advisories": advisories,
        "action": "clear",
        "quest_root": str(resolved_quest_root),
        "medical_story_contract_valid": medical_story_contract_valid,
        "structured_reporting_checklist": structured_reporting_checklist,
        "quality_gate_expectation": quality_gate_expectation,
        "quality_gate_relaxation_allowed": quality_gate_relaxation_allowed,
        "submission_checklist_handoff_ready": submission_checklist_handoff_ready,
        "submission_checklist_unclassified_blocking_items": submission_checklist_unclassified_blocking_items,
    }
    json_path, md_path = write_audit_files(resolved_quest_root, report)
    return {
        "status": str(report["status"]),
        "blockers": blockers,
        "advisories": advisories,
        "action": "clear",
        "quest_root": str(resolved_quest_root),
        "report_json": str(json_path),
        "report_markdown": str(md_path),
    }
