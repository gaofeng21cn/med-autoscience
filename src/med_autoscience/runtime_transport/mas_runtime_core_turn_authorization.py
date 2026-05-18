from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers.study_runtime_execution_parts.controller_authorization_context import (
    _load_controller_decision_authorization_context,
)
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


_QUALITY_REPAIR_BATCH_WORK_UNIT_IDS = frozenset(
    {
        "analysis_claim_evidence_repair",
        "figure_results_trace_repair",
        "manuscript_story_repair",
        "treatment_gap_reporting_repair",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
        "display_reporting_contract_repair",
        "controller_owned_publication_repair",
        "local_architecture_overview_repair",
        "medical_prose_quality_analysis_source_documentation_repair",
    }
)
_GATE_CLEARING_BATCH_WORK_UNIT_IDS = frozenset(
    {
        "publication_gate_replay",
        "submission_authority_sync_closure",
        "submission_delivery_sync_closure",
        "submission_minimal_refresh",
    }
)
_RUNTIME_REDRIVE_ACTION_NAMES = frozenset(
    {
        "ensure_study_runtime",
        "ensure_study_runtime_relaunch_stopped",
    }
)
_SUPERVISOR_DISPATCH_ACTION_NAMES = frozenset({"return_to_ai_reviewer_workflow"})
_SPECIFICITY_WORK_UNIT_IDS = frozenset({"gate_needs_specificity", "needs_specificity"})


def _codex_turn_prompt(
    *,
    quest_id: str,
    run_id: str,
    reason: str,
    claimed_user_messages: tuple[dict[str, Any], ...],
    runtime_state: Mapping[str, Any] | None = None,
    quest_root: Path | None = None,
) -> str:
    authorization = _controller_authorization(
        runtime_state,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    claimed_user_messages = _claimed_messages_for_prompt(
        claimed_user_messages=claimed_user_messages,
        authorization=authorization,
    )
    messages = json.dumps(list(claimed_user_messages), ensure_ascii=False, indent=2, sort_keys=True)
    authorization_section = _controller_authorization_prompt_section(
        authorization=authorization,
        quest_id=quest_id,
    )
    closeout_path = f"artifacts/runtime/turn_closeouts/{run_id}.json"
    return (
        f"You are running a MAS runtime turn for quest `{quest_id}`.\n"
        f"Run id: `{run_id}`.\n"
        f"Turn reason: `{reason}`.\n\n"
        "Read the quest-local runtime files, continue the research workflow according to MAS contracts, "
        "and leave durable artifacts/receipts in the quest workspace. Do not bypass MAS quality gates.\n\n"
        "Runtime worker role:\n"
        "- This Codex process is the MAS managed runtime worker for this run. "
        "`execution_owner_guard.supervisor_only=true` protects foreground/manual agents from taking over a live run; "
        "it does not block this managed runtime worker from executing MAS-authorized quest-local work inside the stated "
        "quality and authority boundaries.\n"
        "- Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this runtime turn. "
        "If another control-plane gate blocks a specific write surface, produce the allowed durable repair artifact "
        "or a blocked closeout that names that non-supervisor gate precisely.\n\n"
        f"{authorization_section}"
        "Turn closeout contract:\n"
        f"- Before ending this turn, write `{closeout_path}`.\n"
        "- The closeout must be valid JSON with this shape:\n"
        "```json\n"
        "{\n"
        '  "schema_version": 1,\n'
        f'  "quest_id": "{quest_id}",\n'
        f'  "run_id": "{run_id}",\n'
        '  "status": "completed",\n'
        '  "completed_at": "<UTC ISO-8601 timestamp>",\n'
        '  "meaningful_artifact_delta": true,\n'
        '  "artifact_refs": ["relative/path/to/new-or-updated-durable-artifact"],\n'
        '  "blocked_reason": null,\n'
        '  "next_owner": null\n'
        "}\n"
        "```\n"
        "- If no safe meaningful artifact delta is possible, write a blocked closeout instead: set "
        '`"status": "blocked"`, `"meaningful_artifact_delta": false`, include a concrete `"blocked_reason"`, '
        'and set `"next_owner"` to the MAS/controller owner that must act next.\n'
        "- Do not exit silently with only console output; MAS treats a successful Codex process without this closeout as incomplete.\n"
        "- Do not mutate paper/current_package, manuscript/current_package, submission_minimal/current_package, "
        "publication gate conclusions, or medical claims unless an explicit MAS controller contract authorizes that surface.\n"
        "- Do not relax MAS quality gates, quality thresholds, publication gates, or authority boundaries.\n\n"
        f"Claimed user messages:\n```json\n{messages}\n```\n"
    )


def _read_runtime_state(*, quest_root: Path) -> dict[str, Any]:
    path = quest_root / ".ds" / "runtime_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sanitize_runtime_state_before_turn(
    *,
    runtime_state: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    sanitized = dict(runtime_state)
    cleared_keys: list[str] = []
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        value = sanitized.get(key)
        if not isinstance(value, Mapping):
            continue
        closed = _closed_publication_work_unit_for_authorization(
            authorization=dict(value),
            quest_root=quest_root,
            quest_id=quest_id,
        )
        if closed is None:
            continue
        sanitized.pop(key, None)
        cleared_keys.append(key)
    if not cleared_keys:
        return sanitized
    sanitized["quest_id"] = _text(sanitized.get("quest_id")) or quest_id
    sanitized["continuation_policy"] = "auto"
    sanitized["continuation_anchor"] = "decision"
    sanitized["continuation_reason"] = "closed_controller_work_unit_authorization_cleared"
    sanitized["continuation_updated_at"] = _utc_now()
    sanitized["same_fingerprint_auto_turn_count"] = 0
    sanitized["last_runtime_turn_state_sanitization"] = {
        "reason": "publication_work_unit_lifecycle_done",
        "cleared_keys": cleared_keys,
        "applied_at": _utc_now(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }
    _write_runtime_state(quest_root=quest_root, runtime_state=sanitized)
    return sanitized


def _sync_current_controller_authorization_for_turn(
    *,
    runtime_state: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
    run_id: str,
) -> dict[str, Any]:
    current_authorization = _current_controller_decision_authorization(
        quest_root=quest_root,
        quest_id=quest_id,
    )
    if not current_authorization:
        if _current_controller_decision_exists(quest_root=quest_root, quest_id=quest_id):
            updated = dict(runtime_state)
            if "current_controller_authorization" in updated:
                updated.pop("current_controller_authorization", None)
                updated["current_controller_authorization_sync_status"] = "current_controller_decision_not_runtime_authorizing"
                updated["current_controller_authorization_synced_at"] = _utc_now()
                _write_runtime_state(quest_root=quest_root, runtime_state=updated)
            return updated
        return dict(runtime_state)
    if _closed_publication_work_unit_for_authorization(
        authorization=current_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
    ) is not None:
        return dict(runtime_state)
    updated = dict(runtime_state)
    authorization = _bind_authorization_to_turn(
        authorization=current_authorization,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
    )
    if _mapping(updated.get("current_controller_authorization")) == authorization:
        return updated
    updated["quest_id"] = _text(updated.get("quest_id")) or quest_id
    updated["current_controller_authorization"] = authorization
    updated["current_controller_authorization_synced_at"] = _utc_now()
    _write_runtime_state(quest_root=quest_root, runtime_state=updated)
    return updated


def _controller_authorization(
    runtime_state: Mapping[str, Any] | None,
    *,
    quest_root: Path | None = None,
    quest_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    current_controller_authorization = _current_controller_decision_authorization(
        quest_root=quest_root,
        quest_id=quest_id,
    )
    if current_controller_authorization:
        if _closed_publication_work_unit_for_authorization(
            authorization=current_controller_authorization,
            quest_root=quest_root,
            quest_id=quest_id,
        ) is None:
            return current_controller_authorization
    if _current_controller_decision_exists(quest_root=quest_root, quest_id=quest_id):
        return {}
    for key in ("current_controller_authorization", "last_controller_decision_authorization"):
        value = runtime_state.get(key)
        if isinstance(value, Mapping):
            authorization = dict(value)
            if _closed_publication_work_unit_for_authorization(
                authorization=authorization,
                quest_root=quest_root,
                quest_id=quest_id,
            ) is not None:
                return {}
            return authorization
    return {}


def _current_controller_decision_authorization(
    *,
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {}
    study_root = _resolve_study_root_from_quest_root_light(quest_root=Path(quest_root), quest_id=quest_id)
    if study_root is None:
        return {}
    authorization = _load_controller_decision_authorization_context(study_root=study_root)
    if not isinstance(authorization, Mapping):
        return {}
    if bool(authorization.get("requires_human_confirmation")):
        return {}
    action_names = _controller_action_names(authorization)
    if not action_names:
        return {}
    normalized = dict(authorization)
    normalized["authorization_basis"] = "current_controller_decision"
    next_work_unit = _mapping(normalized.get("next_work_unit"))
    next_work_unit_id = _text(next_work_unit.get("unit_id"))
    if next_work_unit_id is not None:
        normalized.setdefault("work_unit_id", next_work_unit_id)
    normalized.setdefault(
        "work_unit_fingerprint",
        _text(normalized.get("blocker_authority_fingerprint")) or _text(next_work_unit.get("fingerprint")),
    )
    return normalized


def _current_controller_decision_exists(
    *,
    quest_root: Path | None,
    quest_id: str | None,
) -> bool:
    if quest_root is None:
        return False
    study_root = _resolve_study_root_from_quest_root_light(quest_root=Path(quest_root), quest_id=quest_id)
    if study_root is None:
        return False
    return (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def _bind_authorization_to_turn(
    *,
    authorization: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
    run_id: str,
) -> dict[str, Any]:
    bound = dict(authorization)
    bound["active_run_id"] = run_id
    bound.setdefault("run_id", run_id)
    bound["quest_id"] = _text(bound.get("quest_id")) or quest_id
    bound["study_id"] = _text(bound.get("study_id")) or _study_id_for_quest_root(quest_root=quest_root, quest_id=quest_id)
    next_work_unit = _mapping(bound.get("next_work_unit"))
    next_work_unit_id = _text(next_work_unit.get("unit_id"))
    if _text(bound.get("work_unit_id")) is None and next_work_unit_id is not None:
        bound["work_unit_id"] = next_work_unit_id
    if _text(bound.get("work_unit_fingerprint")) is None:
        bound["work_unit_fingerprint"] = _text(next_work_unit.get("fingerprint"))
    return bound


def _study_id_for_quest_root(*, quest_root: Path, quest_id: str) -> str:
    study_root = _resolve_study_root_from_quest_root_light(quest_root=quest_root, quest_id=quest_id)
    if study_root is None:
        return quest_id
    return _yaml_string_field(study_root / "study.yaml", "study_id") or study_root.name


def _closed_publication_work_unit_for_authorization(
    *,
    authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any] | None:
    if quest_root is None:
        return None
    study_root = _resolve_study_root_from_quest_root_light(quest_root=Path(quest_root), quest_id=quest_id)
    if study_root is None:
        return None
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=study_root,
    )
    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(dict(payload)):
        return None
    source_eval_id = _text(payload.get("source_eval_id"))
    authorization_eval_id = _authorization_publication_eval_id(
        authorization=authorization,
        study_root=study_root,
    )
    if source_eval_id is None or authorization_eval_id is None or source_eval_id != authorization_eval_id:
        return None
    lifecycle_work_unit = _mapping(payload.get("work_unit"))
    lifecycle_work_unit_id = _text(lifecycle_work_unit.get("unit_id"))
    authorization_work_unit_ids = set(_controller_work_unit_ids(authorization))
    if lifecycle_work_unit_id is None or lifecycle_work_unit_id not in authorization_work_unit_ids:
        return None
    return {
        "reason": "publication_work_unit_lifecycle_done",
        "source_eval_id": source_eval_id,
        "work_unit_id": lifecycle_work_unit_id,
        "lifecycle_path": str(lifecycle_path),
    }


def _authorization_publication_eval_id(
    *,
    authorization: Mapping[str, Any],
    study_root: Path,
) -> str | None:
    direct_eval_id = _text(
        authorization.get("publication_eval_id")
        or authorization.get("source_eval_id")
        or _mapping(authorization.get("publication_eval_ref")).get("eval_id")
    )
    if direct_eval_id is not None:
        return direct_eval_id
    decision = _read_json_mapping(study_root / "artifacts" / "controller_decisions" / "latest.json")
    if not _authorization_matches_controller_decision(authorization=authorization, decision=decision):
        return None
    return _text(
        decision.get("publication_eval_id")
        or decision.get("source_eval_id")
        or _mapping(decision.get("publication_eval_ref")).get("eval_id")
    )


def _authorization_matches_controller_decision(
    *,
    authorization: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> bool:
    if not decision:
        return False
    authorization_decision_id = _text(authorization.get("decision_id"))
    decision_id = _text(decision.get("decision_id"))
    if authorization_decision_id is not None and decision_id is not None:
        return authorization_decision_id == decision_id
    authorization_work_units = set(_controller_work_unit_ids(authorization))
    decision_work_units = set(_controller_work_unit_ids(decision))
    if not authorization_work_units or not authorization_work_units.intersection(decision_work_units):
        return False
    authorization_fingerprint = _text(authorization.get("work_unit_fingerprint"))
    decision_fingerprint = _text(decision.get("work_unit_fingerprint"))
    return (
        authorization_fingerprint is None
        or decision_fingerprint is None
        or authorization_fingerprint == decision_fingerprint
    )


def _resolve_study_root_from_quest_root_light(*, quest_root: Path, quest_id: str | None) -> Path | None:
    resolved = Path(quest_root).expanduser().resolve()
    if resolved.parent.name != "quests" or resolved.parent.parent.name != "runtime":
        return None
    if len(resolved.parents) >= 3 and resolved.parents[2].name != "ops":
        workspace_root = resolved.parents[2]
    elif len(resolved.parents) >= 5 and resolved.parents[3].name == "ops":
        workspace_root = resolved.parents[4]
    else:
        return None
    quest_name = _text(quest_id) or resolved.name
    candidate_ids = [quest_name]
    declared_study_id = _yaml_string_field(resolved / "quest.yaml", "study_id")
    if declared_study_id is not None and declared_study_id not in candidate_ids:
        candidate_ids.insert(0, declared_study_id)
    studies_root = workspace_root / "studies"
    for study_id in candidate_ids:
        candidate = (studies_root / study_id).resolve()
        if (candidate / "study.yaml").exists():
            return candidate
    if not studies_root.exists():
        return None
    for binding_path in sorted(studies_root.glob("*/runtime_binding.yaml")):
        binding_text = _yaml_string_field(binding_path, "quest_id")
        if binding_text != quest_name:
            continue
        candidate = binding_path.parent.resolve()
        if (candidate / "study.yaml").exists():
            return candidate
    return None


def _controller_authorization_prompt_section(*, authorization: Mapping[str, Any], quest_id: str) -> str:
    if not authorization:
        return ""
    payload = _compact_controller_authorization(authorization)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    controller_action_contract = _controller_action_execution_contract_prompt_section(
        authorization=authorization,
        quest_id=quest_id,
    )
    return (
        "Active MAS controller work unit:\n"
        "```json\n"
        f"{rendered}\n"
        "```\n"
        "- Treat this controller work unit as the first execution target for this turn.\n"
        "- This Codex process is the MAS managed runtime worker for this run. "
        "`execution_owner_guard.supervisor_only=true` protects foreground/manual agents from taking over a live run; "
        "it does not block this managed runtime worker from executing this controller work unit inside the stated "
        "MAS quality and authority boundaries.\n"
        "- Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this controller work unit. "
        "If another control-plane gate blocks a specific write surface, produce the allowed durable repair artifact "
        "or a blocked closeout that names that non-supervisor gate precisely.\n"
        "- MAS-managed analysis-campaign/write controller work units may revise canonical `paper/` surfaces needed by "
        "the listed `work_unit_id`, `next_work_unit`, and `specificity_targets`. "
        "Foreground/manual takeover remains barred by `execution_owner_guard.supervisor_only=true`; this allowance applies "
        "only to this managed runtime worker through the active MAS controller work unit.\n"
        "- publication gate `allow_write=false` blocks generated package/submission writes such as `current_package`, "
        "`submission_minimal`, bundle builds, and submission proofing. It does not by itself block controller-authorized "
        "canonical `paper/` revisions for upstream analysis-campaign/write work units.\n"
        "- Produce a MAS-authorized durable artifact that addresses `work_unit_id`, `next_work_unit`, and any listed "
        "`specificity_targets`, or write a blocked closeout naming the missing controller/owner surface.\n"
        "- A runtime/watch/health/control-plane receipt alone is not a meaningful artifact delta for this work unit.\n\n"
        f"{controller_action_contract}"
    )


def _controller_action_execution_contract_prompt_section(
    *,
    authorization: Mapping[str, Any],
    quest_id: str,
) -> str:
    action_names = _controller_action_names(authorization)
    if not action_names:
        return ""
    ai_reviewer_redrive_contract = _ai_reviewer_redrive_execution_contract_prompt_section(
        authorization=authorization,
        action_names=action_names,
        quest_id=quest_id,
    )
    if ai_reviewer_redrive_contract:
        return ai_reviewer_redrive_contract
    command_lines = [
        command
        for action_name in action_names
        if (command := _controller_action_command(action_name=action_name, quest_id=quest_id)) is not None
    ]
    if not command_lines:
        return (
            "Controller action execution contract:\n"
            f"- Requested controller actions: {', '.join(action_names)}.\n"
            "- No callable MAS CLI command is registered in this prompt for those action names. Write the turn closeout "
            "with status=blocked, meaningful_artifact_delta=false, blocked_reason=owner_callable_surface_missing, "
            "and next_owner=MAS/controller.\n\n"
        )
    rendered_commands = "\n".join(f"  {command}" for command in command_lines)
    return (
        "Controller action execution contract:\n"
        f"- Controller action names: {', '.join(action_names)}.\n"
        "- Invoke the listed controller command before freeform artifact writing:\n"
        "```bash\n"
        f"{rendered_commands}\n"
        "```\n"
        "- Resolve `<workspace MAS profile>` from `MED_AUTOSCIENCE_PROFILE`, "
        "`ops/medautoscience/profiles/*.workspace.toml`, or `ops/medautoscience/profiles/*.local.toml`; "
        "resolve `<study_id>` from the active authorization, "
        "study runtime status, or quest/study directory identity.\n"
        "- A repair packet, gate audit, controller handoff, runtime/watch receipt, or console-only summary is not "
        "sufficient unless the controller command itself produced the durable paper-facing artifact delta or returned "
        "a concrete owner block.\n"
        "- If the command cannot be resolved or invoked safely, write the blocked closeout with "
        "blocked_reason=owner_callable_surface_missing and next_owner=MAS/controller.\n\n"
    )


def _ai_reviewer_redrive_execution_contract_prompt_section(
    *,
    authorization: Mapping[str, Any],
    action_names: list[str],
    quest_id: str,
) -> str:
    if "return_to_ai_reviewer_workflow" not in action_names:
        return ""
    work_unit_ids = set(_controller_work_unit_ids(authorization))
    if not work_unit_ids.intersection({"ai_reviewer_recheck", "ai_reviewer_medical_prose_quality_review"}):
        return ""
    prose_command = _ai_medical_prose_review_command(quest_id=quest_id)
    dispatch_command = _controller_action_command(
        action_name="return_to_ai_reviewer_workflow",
        quest_id=quest_id,
    )
    return (
        "AI reviewer redrive execution contract:\n"
        f"- Controller action names: {', '.join(action_names)}.\n"
        "- This is an AI-reviewer-owner turn. Do not treat the supervisor dispatch command as sufficient by itself: "
        "that command can only consume an already-written AI reviewer record.\n"
        "- First run `medical-publication-surface --apply` if `artifacts/publication_eval/medical_prose_review_request.json` "
        "is missing or stale; then read the request, manuscript, study charter, evidence ledger, review ledger, "
        "medical manuscript blueprint, claim-evidence map, and publication gate projection.\n"
        "- The AI reviewer must judge the manuscript as a medical original research article, including manuscript "
        "completeness, Methods reproducibility, Results numeric specificity, table/figure adequacy, clinical context, "
        "defensive-language overuse, and reference-style maturity. A mechanical checklist or script output is not "
        "quality authority.\n"
        "- Write the AI reviewer response as a JSON object with the exact fields required by the request's "
        "`structured_response_contract`. Non-clear verdicts must route back to blueprint, analysis, write, or review; "
        "clear verdicts must include representative rewrite evidence.\n"
        "- Materialize that response through the MAS validator before any publication-eval dispatch:\n"
        "```bash\n"
        f"  {prose_command}\n"
        "```\n"
        "- After `medical_prose_review.json` is current and AI-reviewer-owned, run the supervisor dispatch so the "
        "AI-reviewer publication-eval workflow can validate currentness, reviewer OS trace, and any remaining owner "
        "blockers:\n"
        "```bash\n"
        f"  {dispatch_command}\n"
        "```\n"
        "- If the prose review routes back to writing/analysis or the publication-eval workflow blocks on package "
        "freshness or missing reviewer record fields, write a blocked closeout naming that owner surface. Do not "
        "fabricate a clear review, fake package freshness, or relax the AI reviewer operating-system contract.\n\n"
    )


def _controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    raw_actions = authorization.get("controller_actions")
    if isinstance(raw_actions, str):
        actions: list[object] = [raw_actions]
    elif isinstance(raw_actions, (list, tuple)):
        actions = list(raw_actions)
    else:
        actions = []
    names: list[str] = []
    for item in actions:
        if isinstance(item, Mapping):
            raw_name = item.get("action_type") or item.get("action") or item.get("name")
        else:
            raw_name = item
        name = str(raw_name or "").strip()
        if name and name not in names:
            names.append(name)
    if _specificity_targets_ready_for_quality_repair(authorization):
        names = [name for name in names if name != "request_gate_specificity"]
        if "run_quality_repair_batch" not in names:
            names.append("run_quality_repair_batch")
    elif (
        not _controller_callable_action_present(names)
        and _runtime_redrive_action_present(names)
        and _gate_clearing_work_unit_present(authorization)
    ):
        names.append("run_gate_clearing_batch")
    elif "run_quality_repair_batch" not in names and _quality_repair_work_unit_present(authorization):
        names.append("run_quality_repair_batch")
    elif not _controller_callable_action_present(names) and _gate_clearing_work_unit_present(authorization):
        names.append("run_gate_clearing_batch")
    return names


def _controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    candidates: list[object] = [
        authorization.get("work_unit_id"),
        authorization.get("next_work_unit"),
        authorization.get("blocking_work_units"),
        authorization.get("work_unit_targets"),
    ]
    unit_ids: list[str] = []

    def append_unit_id(value: object) -> None:
        if isinstance(value, Mapping):
            raw_value = value.get("unit_id") or value.get("work_unit_id") or value.get("id")
        else:
            raw_value = value
        unit_id = str(raw_value or "").strip()
        if unit_id and unit_id not in unit_ids:
            unit_ids.append(unit_id)

    for candidate in candidates:
        if isinstance(candidate, (list, tuple)):
            for item in candidate:
                append_unit_id(item)
        else:
            append_unit_id(candidate)
    return unit_ids


def _primary_controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    candidates: list[object] = [
        authorization.get("work_unit_id"),
        authorization.get("next_work_unit"),
    ]
    unit_ids: list[str] = []

    def append_unit_id(value: object) -> None:
        if isinstance(value, Mapping):
            raw_value = value.get("unit_id") or value.get("work_unit_id") or value.get("id")
        else:
            raw_value = value
        unit_id = str(raw_value or "").strip()
        if unit_id and unit_id not in unit_ids:
            unit_ids.append(unit_id)

    for candidate in candidates:
        append_unit_id(candidate)
    return unit_ids


def _controller_action_command(*, action_name: str, quest_id: str) -> str | None:
    if action_name in _SUPERVISOR_DISPATCH_ACTION_NAMES:
        return (
            '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}" '
            "python -m med_autoscience.cli runtime-supervisor-execute-dispatch "
            '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --studies <study_id> '
            f"--action-types {action_name} --mode developer_apply_safe --apply --managed-runtime-worker"
        )
    command_by_action = {
        "run_quality_repair_batch": "quality-repair-batch",
        "run_gate_clearing_batch": "gate-clearing-batch",
    }
    command_name = command_by_action.get(action_name)
    if command_name is None:
        return None
    return (
        '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}" '
        f"python -m med_autoscience.cli {command_name} "
        '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --study-id <study_id> '
        f"--quest-id {quest_id}"
    )


def _ai_medical_prose_review_command(*, quest_id: str) -> str:
    return (
        '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}" '
        "python -m med_autoscience.cli materialize-ai-medical-prose-review "
        '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --study-id <study_id> '
        "--payload-file <ai_reviewer_response.json>"
    )


def _compact_controller_authorization(authorization: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "decision_id",
        "controller_actions",
        "route_target",
        "route_key_question",
        "route_rationale",
        "work_unit_id",
        "work_unit_fingerprint",
        "next_work_unit",
        "blocking_work_units",
        "specificity_targets",
        "work_unit_targets",
        "blocking_artifact_refs",
        "blocker_details",
        "gate_blocker_details",
        "gaps",
        "source_path",
    )
    return {key: authorization[key] for key in keys if key in authorization and authorization[key] not in (None, "", [], {})}


def _claimed_messages_for_prompt(
    *,
    claimed_user_messages: tuple[dict[str, Any], ...],
    authorization: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    if not authorization:
        return claimed_user_messages
    return tuple(message for message in claimed_user_messages if not _controller_authorization_message(message))


def _controller_authorization_message(message: Mapping[str, Any]) -> bool:
    content = str(message.get("content") or "")
    return (
        "MAS controller authorization." in content
        and "artifacts/controller_decisions/latest.json" in content
        and "active MAS authorization for this runtime turn" in content
    )


def _write_runtime_state(*, quest_root: Path, runtime_state: Mapping[str, Any]) -> None:
    path = quest_root / ".ds" / "runtime_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(runtime_state), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _yaml_string_field(path: Path, field_name: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    prefix = f"{field_name}:"
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip().strip("\"'")
        return value or None
    return None


def _controller_callable_action_present(action_names: list[str]) -> bool:
    return any(
        name in {"run_quality_repair_batch", "run_gate_clearing_batch"} or name in _SUPERVISOR_DISPATCH_ACTION_NAMES
        for name in action_names
    )


def _runtime_redrive_action_present(action_names: list[str]) -> bool:
    return any(name in _RUNTIME_REDRIVE_ACTION_NAMES for name in action_names)


def _quality_repair_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    for unit_id in _controller_work_unit_ids(authorization):
        if unit_id in _QUALITY_REPAIR_BATCH_WORK_UNIT_IDS:
            return True
    return False


def _gate_clearing_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    for unit_id in _primary_controller_work_unit_ids(authorization):
        if unit_id in _GATE_CLEARING_BATCH_WORK_UNIT_IDS:
            return True
    return False


def _specificity_targets_ready_for_quality_repair(authorization: Mapping[str, Any]) -> bool:
    if not any(unit_id in _SPECIFICITY_WORK_UNIT_IDS for unit_id in _controller_work_unit_ids(authorization)):
        return False
    return specificity_target_status(authorization.get("specificity_targets")).get("complete") is True


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
