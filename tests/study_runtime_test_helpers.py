from __future__ import annotations

import importlib
import json
from pathlib import Path

import yaml


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    return profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline", "write", "finalize"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
        hermes_agent_repo_root=tmp_path / "_external" / "hermes-agent",
        hermes_home_root=tmp_path / ".hermes",
        default_startup_anchor_policy="scout_first_for_continue_existing_state",
        legacy_code_execution_policy="forbid_without_user_approval",
        startup_boundary_requirements=("paper_framing", "journal_shortlist", "evidence_package"),
    )


def make_startup_hydration_report(quest_root: Path) -> dict[str, object]:
    return {
        "status": "hydrated",
        "recorded_at": "2026-04-03T09:00:00+00:00",
        "quest_root": str(quest_root),
        "entry_state_summary": f"Study root: {quest_root}",
        "literature_report": {"record_count": 0},
        "written_files": [str(quest_root / "paper" / "medical_analysis_contract.json")],
        "report_path": str(quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"),
    }


def make_startup_hydration_validation_report(
    quest_root: Path,
    *,
    status: str = "clear",
    blockers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "recorded_at": "2026-04-03T09:05:00+00:00",
        "quest_root": str(quest_root),
        "blockers": blockers or [],
        "contract_statuses": {
            "medical_analysis_contract": "resolved",
            "medical_reporting_contract": "resolved",
        },
        "checked_paths": {
            "medical_analysis_contract_path": str(quest_root / "paper" / "medical_analysis_contract.json"),
            "medical_reporting_contract_path": str(quest_root / "paper" / "medical_reporting_contract.json"),
        },
        "report_path": str(
            quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"
        ),
    }


def make_startup_contract_validation_payload(
    *,
    status: str = "clear",
    blockers: list[str] | None = None,
    medical_analysis_contract_status: str | None = "resolved",
    medical_reporting_contract_status: str | None = "resolved",
    medical_analysis_reason_code: str | None = None,
    medical_reporting_reason_code: str | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "blockers": list(blockers or []),
        "contract_statuses": {
            "medical_analysis_contract": medical_analysis_contract_status,
            "medical_reporting_contract": medical_reporting_contract_status,
        },
        "reason_codes": {
            "medical_analysis_contract": medical_analysis_reason_code,
            "medical_reporting_contract": medical_reporting_reason_code,
        },
    }


def make_completion_sync_payload(
    *,
    quest_id: str = "quest-001",
    status: str = "completed",
    summary: str = "Study completed.",
    approval_text: str = "同意结题",
) -> dict[str, object]:
    return {
        "completion_request": {
            "status": "ok",
            "interaction_id": "interaction-001",
            "snapshot": {"quest_id": quest_id, "status": "running"},
        },
        "approval_message": {
            "ok": True,
            "message": {
                "id": "msg-approval",
                "content": approval_text,
            },
        },
        "completion": {
            "ok": True,
            "status": status,
            "snapshot": {"quest_id": quest_id, "status": status},
            "message": summary,
        },
    }


def make_analysis_bundle_result(*, ready: bool = True) -> dict[str, object]:
    before = {
        "ready": ready,
        "python": {"ready": ready},
        "r": {"ready": ready},
    }
    return {
        "action": "already_ready" if ready else "ensure_bundle",
        "before": before,
        "after": before,
        "ready": ready,
    }


def make_runtime_overlay_result(*, all_roots_ready: bool = True) -> dict[str, object]:
    return {
        "authority": {"selected_action": "noop", "post_status": {"all_targets_ready": True}},
        "materialization": {"materialized_surface_count": 1, "surfaces": []},
        "audit": {
            "all_roots_ready": all_roots_ready,
            "surface_count": 1,
            "surfaces": [],
        },
    }


def make_startup_context_sync_payload(*, quest_id: str = "quest-001") -> dict[str, object]:
    return {
        "ok": True,
        "quest_id": quest_id,
        "snapshot": {
            "quest_id": quest_id,
            "startup_contract": {"schema_version": 4},
            "requested_baseline_ref": None,
        },
    }


def make_partial_quest_recovery_payload(*, quest_id: str = "quest-001") -> dict[str, object]:
    return {
        "status": "archived_invalid_partial_quest_root",
        "quest_root": f"/tmp/runtime/quests/{quest_id}",
        "archived_root": f"/tmp/runtime/recovery/invalid_partial_quest_roots/{quest_id}-20260403T000000Z",
        "missing_required_files": ["quest.yaml"],
    }


def write_submission_metadata_only_bundle(quest_root: Path, *, blocking_item_ids: list[str]) -> None:
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    write_text(
        paper_root / "paper_bundle_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "paper_branch": "paper/main",
                "compile_report_path": str(paper_root / "build" / "compile_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "build" / "compile_report.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "compiled_with_open_submission_items",
                "author_metadata_status": "placeholder_external_input_required",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "review" / "submission_checklist.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "proof_ready_with_author_metadata_and_submission_declarations_pending",
                "blocking_items": [
                    {
                        "id": item_id,
                        "status": "external_input_required",
                        "detail": f"{item_id} pending",
                    }
                    for item_id in blocking_item_ids
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )


def write_study(
    workspace_root: Path,
    study_id: str,
    *,
    study_status: str = "ready",
    quest_id: str | None = None,
    study_archetype: str | None = None,
    preferred_study_archetype: str | None = None,
    paper_framing_summary: str | None = None,
    paper_urls: list[str] | None = None,
    journal_shortlist: list[str] | None = None,
    journal_shortlist_evidence: list[dict[str, object]] | None = None,
    minimum_sci_ready_evidence_package: list[str] | None = None,
    launch_profile: str = "continue_existing_state",
    endpoint_type: str | None = None,
    manuscript_family: str | None = None,
    submission_targets_mode: str | None = None,
    submission_targets: list[dict[str, object]] | None = None,
    study_completion: dict[str, object] | None = None,
    runtime_reentry_required_paths: list[str] | None = None,
    runtime_reentry_execution_root: str | None = None,
    runtime_reentry_first_unit: str | None = None,
    runtime_reentry_require_startup_hydration: bool | None = None,
    runtime_reentry_require_managed_skill_audit: bool | None = None,
) -> Path:
    study_root = workspace_root / "studies" / study_id
    write_text(workspace_root / "ops" / "med-deepscientist" / "startup_briefs" / f"{study_id}.md", "# Startup brief\n")
    lines = [
        f"study_id: {study_id}",
        "title: Diabetes mortality risk paper",
        f"status: {study_status}",
        "primary_question: >",
        "  Build a submission-ready survival-risk study.",
        "brief_file: brief.md",
        "protocol_file: protocol.md",
        f"startup_brief: ../../ops/med-deepscientist/startup_briefs/{study_id}.md",
    ]
    if study_archetype is not None:
        lines.append(f"study_archetype: {study_archetype}")
    if preferred_study_archetype is not None:
        lines.append(f"preferred_study_archetype: {preferred_study_archetype}")
    if paper_framing_summary is not None:
        lines.extend(
            [
                "paper_framing_summary: >",
                f"  {paper_framing_summary}",
            ]
        )
    if endpoint_type is not None:
        lines.append(f"endpoint_type: {endpoint_type}")
    if manuscript_family is not None:
        lines.append(f"manuscript_family: {manuscript_family}")
    if paper_urls:
        lines.append("paper_urls:")
        lines.extend(f"  - {url}" for url in paper_urls)
    if journal_shortlist:
        lines.append("journal_shortlist:")
        lines.extend(f"  - {item}" for item in journal_shortlist)
    if journal_shortlist_evidence is None and journal_shortlist:
        journal_shortlist_evidence = [
            {
                "journal_name": journal_name,
                "selection_band": "primary_fit" if index == 0 else "strong_alternative",
                "fit_summary": f"{journal_name} fits the paper framing.",
                "risk_summary": f"{journal_name} still requires a full evidence package.",
                "official_scope_sources": [f"https://example.org/{index}/scope"],
                "similar_paper_examples": [
                    {
                        "title": f"Example paper {index}",
                        "journal": journal_name,
                        "year": 2024,
                        "source_url": f"https://example.org/{index}/paper",
                        "similarity_rationale": "Same clinical prediction surface.",
                    }
                ],
                "tier_snapshot": {
                    "source": "manual_snapshot",
                    "retrieved_on": "2026-03-30",
                    "quartile": "Q1",
                },
                "confidence": "medium",
            }
            for index, journal_name in enumerate(journal_shortlist)
        ]
    if journal_shortlist_evidence:
        lines.append("journal_shortlist_evidence:")
        lines.extend(
            f"  {line}" if line else line
            for line in yaml.safe_dump(journal_shortlist_evidence, allow_unicode=True, sort_keys=False).splitlines()
        )
    if minimum_sci_ready_evidence_package:
        lines.append("minimum_sci_ready_evidence_package:")
        lines.extend(f"  - {item}" for item in minimum_sci_ready_evidence_package)
    if submission_targets_mode is not None:
        lines.append(f"submission_targets_mode: {submission_targets_mode}")
    if submission_targets:
        lines.append("submission_targets:")
        lines.extend(
            f"  {line}" if line else line
            for line in yaml.safe_dump(submission_targets, allow_unicode=True, sort_keys=False).splitlines()
        )
    if study_completion:
        lines.append("study_completion:")
        lines.extend(
            f"  {line}" if line else line
            for line in yaml.safe_dump(study_completion, allow_unicode=True, sort_keys=False).splitlines()
        )
    lines.extend(
        [
            "execution:",
            "  engine: med-deepscientist",
            "  auto_entry: on_managed_research_intent",
            "  auto_resume: true",
            f"  quest_id: {quest_id or study_id}",
            "  default_entry_mode: full_research",
            "  startup_contract_profile: paper_required_autonomous",
            f"  launch_profile: {launch_profile}",
            "  decision_policy: autonomous",
        ]
    )
    if runtime_reentry_required_paths is not None:
        lines.extend(
            [
                "  runtime_reentry_gate:",
                "    enabled: true",
                f"    execution_root: {runtime_reentry_execution_root or 'analysis/clean_room_execution'}",
                f"    first_runtime_unit: {runtime_reentry_first_unit or '00_entry_validation'}",
                f"    require_startup_hydration: {'true' if runtime_reentry_require_startup_hydration else 'false'}",
                f"    require_managed_skill_audit: {'true' if runtime_reentry_require_managed_skill_audit else 'false'}",
                "    required_paths:",
            ]
        )
        lines.extend(f"      - {path}" for path in runtime_reentry_required_paths)
    lines.extend(
        [
            "",
        ]
    )
    write_text(
        study_root / "study.yaml",
        "\n".join(lines),
    )
    write_text(study_root / "brief.md", "# Brief\n")
    write_text(study_root / "protocol.md", "# Protocol\n")
    return study_root


def _clear_readiness_report(workspace_root: Path, study_id: str) -> dict[str, object]:
    return {
        "status": "clear",
        "study_summary": {
            "study_count": 1,
            "review_needed_count": 0,
            "clear_count": 1,
            "review_needed_study_ids": [],
            "clear_study_ids": [study_id],
            "outdated_private_release_study_ids": [],
            "unresolved_contract_study_ids": [],
            "public_extension_study_ids": [],
        },
    }
