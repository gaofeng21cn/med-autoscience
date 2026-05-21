from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core_hard_methodology
from med_autoscience.runtime_transport import mas_runtime_core_turn_actions
from med_autoscience.controllers.story_surface_work_units import (
    STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS,
)


def controller_authorization_prompt_section(*, authorization: Mapping[str, Any], quest_id: str) -> str:
    if not authorization:
        return ""
    payload = _compact_controller_authorization(authorization)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    controller_action_contract = _controller_action_execution_contract_prompt_section(
        authorization=authorization,
        quest_id=quest_id,
    )
    hard_methodology_contract = _hard_methodology_contract_prompt_section(authorization)
    manuscript_story_contract = _manuscript_story_repair_followthrough_prompt_section(authorization)
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
        f"{hard_methodology_contract}"
        f"{manuscript_story_contract}"
        f"{controller_action_contract}"
    )


def claimed_messages_for_prompt(
    *,
    claimed_user_messages: tuple[dict[str, Any], ...],
    authorization: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    if not authorization:
        return claimed_user_messages
    return tuple(message for message in claimed_user_messages if not _controller_authorization_message(message))


def _manuscript_story_repair_followthrough_prompt_section(authorization: Mapping[str, Any]) -> str:
    work_unit_ids = set(_controller_work_unit_ids(authorization))
    story_surface_units = work_unit_ids & STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS
    if not story_surface_units:
        return ""
    rendered_units = ", ".join(f"`{unit_id}`" for unit_id in sorted(story_surface_units))
    return (
        "Manuscript story repair follow-through contract:\n"
        f"- This is a MAS write-owner story-surface work unit: {rendered_units}. Invoke the controller command first, then inspect the returned "
        "`quality_repair_batch` and `repair_execution_evidence` surfaces.\n"
        "- If the controller command returns status=blocked with "
        "blocked_reason=manuscript_story_surface_delta_missing and next_owner=write, do not treat that as a "
        "terminal blocked closeout. It is same-owner evidence that the controller packet did not revise the "
        "manuscript story surface yet.\n"
        "- Continue as the write owner by reading the current study charter, manuscript draft, review manuscript, "
        "claim-evidence map, evidence ledger, review ledger, publication-eval request, and current quality blockers. "
        "Revise canonical manuscript story surfaces at `paper/draft.md` and/or "
        "`paper/build/review_manuscript.md` so the paper tells the current clean evidence-backed story.\n"
        "- Keep internal correction history, preprocessing-error provenance, runtime status, QA language, and "
        "submission-readiness notes out of the manuscript body. Those belong in ledgers, handoff records, or typed "
        "blockers, not in the paper narrative.\n"
        "- Close the turn with meaningful_artifact_delta=true only when `artifact_refs` include "
        "`paper/draft.md` and/or `paper/build/review_manuscript.md`. Ledger-only deltas do not close "
        "story-surface write repair work units.\n"
        "- If those canonical manuscript surfaces are missing, unwritable, or the evidence needed to revise them is "
        "not available to the MAS write owner, write a blocked closeout with "
        "status=blocked, meaningful_artifact_delta=false, blocked_reason=write_owner_callable_surface_missing, "
        "and next_owner=MAS/write.\n\n"
    )


def _hard_methodology_contract_prompt_section(authorization: Mapping[str, Any]) -> str:
    return mas_runtime_core_hard_methodology.contract_prompt_section(
        authorization=authorization,
        work_unit_ids=_controller_work_unit_ids(authorization),
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
    prose_command = _ai_medical_prose_review_command()
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


def _ai_medical_prose_review_command() -> str:
    return (
        '"${MED_AUTOSCIENCE_REPO}/scripts/run-python-clean.sh" '
        "-m med_autoscience.cli materialize-ai-medical-prose-review "
        '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --study-id <study_id> '
        "--payload-file <ai_reviewer_response.json>"
    )


def _compact_controller_authorization(authorization: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "decision_id",
        "authorization_basis",
        "controller_actions",
        "route_target",
        "route_key_question",
        "route_rationale",
        "work_unit_id",
        "work_unit_fingerprint",
        "publication_eval_id",
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


def _controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    return mas_runtime_core_turn_actions.controller_action_names(authorization)


def _controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    return mas_runtime_core_turn_actions.controller_work_unit_ids(authorization)


def _controller_action_command(*, action_name: str, quest_id: str) -> str | None:
    return mas_runtime_core_turn_actions.controller_action_command(action_name=action_name, quest_id=quest_id)


def _controller_authorization_message(message: Mapping[str, Any]) -> bool:
    content = str(message.get("content") or "")
    return (
        "MAS controller authorization." in content
        and "artifacts/controller_decisions/latest.json" in content
        and "active MAS authorization for this runtime turn" in content
    )
