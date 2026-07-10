from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_TARGET_SKILL_REFS = [
    "external_repo:mas-scholar-skills/skills/medical-manuscript-writing/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-manuscript-review/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-statistical-review/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-table-design/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-figure-design/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-submission-prep/SKILL.md",
]


def write_oma_materialization_request(
    *,
    request: dict[str, Any],
    request_path: Path,
    suite_path: str | None,
    ai_reviewer_evaluation_ref: str,
    opl_bin: str,
) -> tuple[Path, dict[str, Any]]:
    output_path = Path(request_path).expanduser().resolve().with_name("oma_materialization_request.json")
    payload = _oma_materialization_request_payload(
        request=request,
        request_path=request_path,
        output_path=output_path,
        suite_path=suite_path,
        ai_reviewer_evaluation_ref=ai_reviewer_evaluation_ref,
        opl_bin=opl_bin,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path, payload


def _oma_materialization_request_payload(
    *,
    request: dict[str, Any],
    request_path: Path,
    output_path: Path,
    suite_path: str | None,
    ai_reviewer_evaluation_ref: str,
    opl_bin: str,
) -> dict[str, Any]:
    request_ref = str(Path(request_path).expanduser().resolve())
    output_dir = output_path.parent / _oma_output_dir_name(request)
    target_agent_dir = _resolve_target_agent_dir(request)
    target_skill_refs = _target_skill_refs(request)
    blockers = _oma_materialization_blockers(
        suite_path=suite_path,
        ai_reviewer_evaluation_ref=ai_reviewer_evaluation_ref,
        target_agent_dir=target_agent_dir,
        target_skill_refs=target_skill_refs,
    )
    command_contract = "opl-meta-agent.improve-from-external-agent-lab-suite"
    target_owner_closeout_ref = f"paper_mission_readback_ref:{request.get('study_id')}"
    payload: dict[str, Any] = {
        "surface_kind": "mas_oma_external_suite_materialization_request",
        "schema_version": 1,
        "status": (
            "ready_for_oma_work_order_materialization"
            if not blockers
            else "blocked_oma_materialization_prerequisites_missing"
        ),
        "study_id": request.get("study_id"),
        "source_feedbackops_dispatch_request_ref": request_ref,
        "source_feedback_ref": request.get("feedback_ref"),
        "source_delivery_ref": request.get("delivery_ref"),
        "source_suite_ref": suite_path,
        "ai_reviewer_evaluation_ref": ai_reviewer_evaluation_ref,
        "target_agent": {
            "agent_id": request.get("target_agent_id") or "med-autoscience",
            "repo_dir": str(target_agent_dir) if target_agent_dir is not None else None,
            "descriptor_ref": _existing_child_ref(target_agent_dir, "contracts/domain_descriptor.json"),
            "capability_map_ref": _existing_child_ref(target_agent_dir, "contracts/capability_map.json"),
            "agent_lab_handoff_ref": _existing_child_ref(target_agent_dir, "contracts/agent_lab_handoff.json"),
        },
        "target_skill_refs": target_skill_refs,
        "skill_writeback_status": (
            "target_skill_refs_bound_for_oma_work_order"
            if target_skill_refs
            else "blocked_missing_target_skill_refs"
        ),
        "target_owner_closeout_ref": target_owner_closeout_ref,
        "target_owner_closeout_readback": {
            "owner": "med-autoscience",
            "required": True,
            "closeout_requires_one_of": [
                "mas_owner_receipt_ref",
                "stable_typed_blocker_ref",
                "reviewer_receipt_ref",
                "route_back_evidence_ref",
                "human_gate_ref",
            ],
            "readback_refs": [
                target_owner_closeout_ref,
                "action_catalog:study_progress",
            ],
        },
        "authority_write_route_context": _oma_authority_write_route_context(request),
        "oma_command_contract": command_contract,
        "oma_materialization_command": {
            "command_contract": command_contract,
            "cwd": _resolve_oma_agent_dir(request),
            "argv": [
                "node",
                "--experimental-strip-types",
                "scripts/improve-from-agent-lab-suite.ts",
                "--suite",
                suite_path,
                "--target-agent-dir",
                str(target_agent_dir) if target_agent_dir is not None else None,
                "--output-dir",
                str(output_dir),
                "--feedback-ref",
                str(request.get("feedback_ref") or ""),
                "--ai-reviewer-evaluation",
                ai_reviewer_evaluation_ref,
                "--opl-bin",
                opl_bin,
            ],
        },
        "oma_execute_command_contract": "opl-meta-agent.execute-external-work-order",
        "oma_execute_request": {
            "work_order_ref_expected": str(output_dir / "developer-patch-work-order.json"),
            "output_ref_expected": str(output_dir / "external-work-order-delegation.json"),
            "command_contract": "opl-meta-agent.execute-external-work-order",
            "owner_gated": True,
        },
        "blocked_reason": None,
        "typed_blocker": None,
        "authority_boundary": {
            "writes_study_truth": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_runtime_queue_or_provider_attempt": False,
            "writes_manuscript_or_current_package": False,
            "can_authorize_publication_ready": False,
            "can_authorize_submission_ready": False,
            "candidate_is_authority": False,
        },
    }
    if blockers:
        payload["blocked_reason"] = "OMA work-order materialization request is missing required refs."
        payload["typed_blocker"] = {
            "blocker_kind": "oma_materialization_prerequisites_missing",
            "missing_fields": blockers,
            "owner": "med-autoscience",
            "legal_next_action": "repair_dispatch_request_or_target_repo_refs_then_rerun_feedbackops_dispatch",
        }
    payload["oma_materialization_command"]["argv"] = [
        item for item in payload["oma_materialization_command"]["argv"] if item is not None
    ]
    return payload


def _oma_output_dir_name(request: dict[str, Any]) -> str:
    study_id = _text(request.get("study_id")) or "unknown-study"
    slug = "".join(char if char.isalnum() else "_" for char in study_id.lower()).strip("_")
    return f"oma_external_suite_{slug or 'unknown_study'}"


def _resolve_target_agent_dir(request: dict[str, Any]) -> Path | None:
    explicit = _text(request.get("target_agent_dir")) or _text(os.environ.get("MAS_OMA_TARGET_AGENT_DIR"))
    candidates = [Path(explicit).expanduser()] if explicit else []
    candidates.extend([_nearest_repo_root(Path.cwd()), _nearest_repo_root(Path(__file__).resolve())])
    for candidate in candidates:
        if candidate is not None and (candidate / "contracts" / "domain_descriptor.json").exists():
            return candidate.resolve()
    return None


def _resolve_oma_agent_dir(request: dict[str, Any]) -> str | None:
    explicit = _text(request.get("oma_agent_dir")) or _text(os.environ.get("OPL_META_AGENT_REPO"))
    candidates = [Path(explicit).expanduser()] if explicit else []
    candidates.append(Path("/Users/gaofeng/workspace/opl-meta-agent"))
    for candidate in candidates:
        if (candidate / "scripts" / "improve-from-agent-lab-suite.ts").exists():
            return str(candidate.resolve())
    return None


def _nearest_repo_root(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists() and (candidate / "contracts").exists():
            return candidate
    return None


def _existing_child_ref(parent: Path | None, child: str) -> str | None:
    if parent is None:
        return None
    path = parent / child
    return str(path) if path.exists() else None


def _target_skill_refs(request: dict[str, Any]) -> list[str]:
    return _unique_texts([*_strings(request.get("target_skill_refs")), *DEFAULT_TARGET_SKILL_REFS])


def _oma_materialization_blockers(
    *,
    suite_path: str | None,
    ai_reviewer_evaluation_ref: str,
    target_agent_dir: Path | None,
    target_skill_refs: list[str],
) -> list[str]:
    blockers: list[str] = []
    if _text(suite_path) is None:
        blockers.append("source_suite_ref")
    if _text(ai_reviewer_evaluation_ref) is None:
        blockers.append("ai_reviewer_evaluation_ref")
    if target_agent_dir is None:
        blockers.append("target_agent.repo_dir")
    if not target_skill_refs:
        blockers.append("target_skill_refs")
    return blockers


def _oma_authority_write_route_context(request: dict[str, Any]) -> dict[str, Any]:
    boundary = dict(request.get("authority_boundary") or {})
    return {
        "target_owner": "med-autoscience",
        "meta_agent_owner": request.get("meta_agent_owner") or "opl-meta-agent.oma-agent-evolution",
        "target_owner_closeout_owner": request.get("target_owner_closeout_owner") or "med-autoscience",
        "candidate_is_authority": False,
        "forbidden_authority_writes": {
            "study_truth": boundary.get("can_write_study_truth") is True,
            "owner_receipt": boundary.get("can_write_owner_receipt") is True,
            "typed_blocker": boundary.get("can_write_typed_blocker") is True,
            "human_gate": boundary.get("can_write_human_gate") is True,
            "current_package": boundary.get("can_mutate_current_package") is True,
            "runtime_queue_or_provider_attempt": boundary.get("can_write_runtime_queue_or_provider_attempt") is True,
        },
        "oma_may_emit": [
            "developer_patch_work_order",
            "refs_only_improvement_proposal",
            "typed_blocker_candidate",
        ],
        "oma_must_not_emit_as_authority": [
            "publication_ready",
            "submission_ready",
            "owner_accepted",
            "current_package_authority",
            "domain_truth_written",
        ],
    }


def _unique_texts(values: list[object]) -> list[str]:
    items: list[str] = []
    for value in values:
        text = _text(value)
        if text is not None and text not in items:
            items.append(text)
    return items


def _strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
