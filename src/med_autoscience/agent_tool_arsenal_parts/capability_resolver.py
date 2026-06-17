from __future__ import annotations

from typing import Any, Mapping, Sequence

from med_autoscience.agent_tool_arsenal_parts.runtime_boundary import (
    merge_opl_capability_runtime_boundary,
    opl_capability_runtime_boundary,
)


EXACT_CONTRACT_MATCH = "exact_contract_match"
SOFT_DISCOVERY_MATCH = "soft_discovery_match"
ADAPTABLE_BASELINE_POLICY = "adaptable_baseline_not_exact_contract"
INSUFFICIENT_FIT = "insufficient_fit"
ORDINARY_PLANNING_ROOT = "current_owner_delta"
STAGE_ATTEMPT_REF = "opl_stage_attempt_or_lease"


def capability_resolution_view(
    *,
    current_owner_delta: Mapping[str, Any],
    task_intent: str = "",
    available_refs: Sequence[str] | None = None,
    tool_cards: Sequence[Mapping[str, Any]],
    owner_callable_cards: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    refs = _normalized_available_refs(available_refs)
    candidates = [
        _candidate_from_card(
            card=card,
            current_owner_delta=current_owner_delta,
            task_intent=task_intent,
            available_refs=refs,
        )
        for card in list(tool_cards) + list(owner_callable_cards)
        if isinstance(card, Mapping)
    ]
    retained = [item for item in candidates if int(item["fit_score"]) > 0]
    retained.sort(
        key=lambda item: (
            int(item["fit_score"]),
            item["hard_gate_status"] == "ready",
            str(item["tool_id"]),
        ),
        reverse=True,
    )
    return {
        "surface_kind": "mas_capability_resolution",
        "planning_root": ORDINARY_PLANNING_ROOT,
        "resolver_layers": [
            "soft_discovery",
            "scored_fit",
            "hard_invocation_gate",
        ],
        "discovery_fail_closed": False,
        "hard_gate_fail_closed": True,
        "selection_policy": {
            "discovery": "soft_match_high_recall",
            "selection": "scored_explainable_fit",
            "invocation": "hard_contract_fail_closed",
            "missing_refs_filter_candidates": False,
            "candidate_count_cap": 8,
        },
        "authority_boundary": opl_capability_runtime_boundary(),
        "current_owner_delta_summary": _current_owner_delta_summary(current_owner_delta),
        "candidate_tools": retained[:8],
        "typed_blocker_policy": {
            "emit_when_no_candidate": True,
            "emit_when_hard_gate_blocks_selected_invocation": True,
            "discovery_miss_is_not_invocation_failure": True,
        },
    }


def resolve_capability_candidates_from_arsenal(
    *,
    current_owner_delta: Mapping[str, Any],
    task_intent: str = "",
    available_refs: Sequence[str] | None = None,
    arsenal: Mapping[str, Any],
) -> dict[str, Any]:
    tool_cards = [
        item for item in list(arsenal.get("tool_cards") or []) if isinstance(item, Mapping)
    ]
    owner_cards = [
        item
        for item in list(arsenal.get("owner_callable_cards") or [])
        if isinstance(item, Mapping)
    ]
    return capability_resolution_view(
        current_owner_delta=current_owner_delta,
        task_intent=task_intent,
        available_refs=available_refs,
        tool_cards=tool_cards,
        owner_callable_cards=owner_cards,
    )


def attach_capability_invocation_os_fields(
    card: dict[str, Any],
    *,
    planning_root: str = ORDINARY_PLANNING_ROOT,
) -> None:
    card["discovery_hint"] = discovery_hint_for_action_card(
        card,
        planning_root=planning_root,
    )
    card["fit_signal"] = fit_signal_for_card(card)
    card["invocation_gate"] = invocation_gate_for_card(card)
    card["adaptation_policy"] = adaptation_policy_for_card(card)


def capability_resolver_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_resolver_contract",
        "planning_root": ORDINARY_PLANNING_ROOT,
        "resolver_layers": [
            {
                "layer": "soft_discovery",
                "policy": "high_recall",
                "missing_required_refs_filter_candidates": False,
            },
            {
                "layer": "scored_fit",
                "policy": "explainable_fit_score",
                "must_emit_reasons": True,
            },
            {
                "layer": "hard_invocation_gate",
                "policy": "fail_closed",
                "required_refs_and_authority_boundary_block_invocation": True,
            },
        ],
        "display_pack_policy_ref": (
            "src/med_autoscience/display_pack_agent_parts/template_fit.py::"
            "ADAPTABLE_TEMPLATE_FIT_POLICY"
        ),
        "authority_boundary": opl_capability_runtime_boundary(),
        "non_authority_rule": (
            "Capability resolution can rank and explain candidates, but it cannot write "
            "domain truth, owner receipts, typed blockers, publication quality, or "
            "submission readiness."
        ),
    }


def discovery_hint_for_action_card(
    card: Mapping[str, Any],
    *,
    planning_root: str = ORDINARY_PLANNING_ROOT,
) -> dict[str, Any]:
    action_id = _text(card.get("action_id"))
    tool_id = _text(card.get("tool_id"))
    tool_mode = _text(card.get("tool_mode"))
    capability_tags = _capability_tags(card)
    aliases = _dedupe(
        [
            action_id,
            tool_id,
            f"{tool_id}:{tool_mode}" if tool_id and tool_mode else "",
            *capability_tags,
        ]
    )
    return {
        "surface_kind": "mas_tool_discovery_hint",
        "planning_root": planning_root,
        "aliases": aliases,
        "capability_tags": capability_tags,
        "task_intents": _dedupe([action_id.replace("_", " "), *capability_tags]),
        "when_to_use": _text(card.get("when_to_use")),
        "examples": _examples_for_card(card),
        "current_delta_fields": [
            "action_type",
            "action_id",
            "capability_families",
            "display_intent",
            "figure_request",
        ],
    }


def fit_signal_for_card(card: Mapping[str, Any]) -> dict[str, Any]:
    tags = _capability_tags(card)
    return {
        "surface_kind": "mas_tool_fit_signal",
        "match_fields": [
            "current_owner_delta.action_type",
            "current_owner_delta.action_id",
            "task_intent",
            "capability_tags",
            "aliases",
            "when_to_use",
            "examples",
        ],
        "capability_tags": tags,
        "soft_match_min_score": 10,
        "required_refs_are_selection_blockers": False,
        "missing_refs_reduce_readiness_not_discovery": True,
        "fit_policy_candidates": [
            EXACT_CONTRACT_MATCH,
            SOFT_DISCOVERY_MATCH,
            ADAPTABLE_BASELINE_POLICY,
            INSUFFICIENT_FIT,
        ],
    }


def invocation_gate_for_card(card: Mapping[str, Any]) -> dict[str, Any]:
    required_refs = _required_refs_for_card(card)
    required_refs = _dedupe(required_refs + _extra_gate_refs(card))
    return {
        "surface_kind": "mas_tool_invocation_gate",
        "fail_closed": True,
        "required_refs": required_refs,
        "preflight_checks": list(card.get("preflight_checks") or []),
        "allowed_writes": list(card.get("allowed_writes") or []),
        "forbidden_authority": list(card.get("forbidden_authority") or []),
        "requires_human_gate": bool(_mapping(card.get("risk_annotations")).get("requires_human_gate")),
        "requires_opl_stage_attempt_or_lease": bool(
            _mapping(card.get("risk_annotations")).get("requires_opl_stage_attempt_or_lease")
        ),
        "owner_receipt_or_typed_blocker_required": bool(
            _mapping(card.get("closeout_contract")).get("requires_owner_receipt_or_typed_blocker")
            or _mapping(card.get("authority_boundary")).get(
                "owner_receipt_or_typed_blocker_required"
            )
        ),
    }


def adaptation_policy_for_card(card: Mapping[str, Any]) -> dict[str, Any]:
    policy = ADAPTABLE_BASELINE_POLICY if _is_display_pack_adaptable_card(card) else EXACT_CONTRACT_MATCH
    return {
        "surface_kind": "mas_tool_adaptation_policy",
        "policy": policy,
        "quality_floor_only": policy == ADAPTABLE_BASELINE_POLICY,
        "can_authorize_publication_readiness": False,
        "can_replace_owner_receipt": False,
        "can_replace_visual_audit": False,
        "adaptation_boundary_ref": (
            "src/med_autoscience/display_pack_agent_parts/template_fit.py"
            if policy == ADAPTABLE_BASELINE_POLICY
            else ""
        ),
        "adaptable_baseline_policy_ref": (
            "display_pack_agent_parts.template_fit.ADAPTABLE_TEMPLATE_FIT_POLICY"
            if policy == ADAPTABLE_BASELINE_POLICY
            else ""
        ),
    }


def _candidate_from_card(
    *,
    card: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    task_intent: str,
    available_refs: set[str],
) -> dict[str, Any]:
    score, reasons = _fit_score(card, current_owner_delta=current_owner_delta, task_intent=task_intent)
    required_refs = _required_refs_for_card(card)
    missing_refs = _missing_refs(required_refs + _extra_gate_refs(card), available_refs)
    ready = not missing_refs
    fit_policy = _fit_policy(card, score=score, exact=_has_exact_current_delta_match(card, current_owner_delta))
    return {
        "surface_kind": "mas_capability_candidate",
        "card_kind": _text(card.get("card_kind")),
        "tool_id": _text(card.get("tool_id")),
        **({"tool_mode": _text(card.get("tool_mode"))} if _text(card.get("tool_mode")) else {}),
        **(
            {"action_id": _text(card.get("action_id") or card.get("action_type"))}
            if _text(card.get("action_id") or card.get("action_type"))
            else {}
        ),
        **({"action_type": _text(card.get("action_type"))} if _text(card.get("action_type")) else {}),
        "callability": _text(card.get("callability")),
        "fit_score": score,
        "fit_policy": fit_policy,
        "fit_reasons": reasons,
        "recommendation_score": score,
        "recommendation_reasons": reasons,
        "required_refs": required_refs,
        "missing_refs": missing_refs,
        "candidate_retained_despite_missing_refs": bool(missing_refs and score > 0),
        "hard_gate_status": "ready" if ready else "blocked_until_refs",
        "hard_gate_reasons": [] if ready else ["missing_required_refs"],
        "invocation_gate": dict(_mapping(card.get("invocation_gate"))),
        "authority_boundary": merge_opl_capability_runtime_boundary(
            _mapping(card.get("authority_boundary"))
        ),
        "adaptation_policy": dict(_mapping(card.get("adaptation_policy"))),
        "requires": _requires_for_card(card),
        "next_safe_actions": _candidate_next_safe_actions(card, missing_refs=missing_refs),
        "default_invocation": dict(_mapping(card.get("default_invocation"))),
    }


def _fit_score(
    card: Mapping[str, Any],
    *,
    current_owner_delta: Mapping[str, Any],
    task_intent: str,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    requested = _text(current_owner_delta.get("action_type") or current_owner_delta.get("action_id"))
    if requested:
        for field in ("action_type", "action_id", "tool_id"):
            if requested == _text(card.get(field)):
                score += 100
                reasons.append(f"exact_current_delta:{field}")
                break
    tokens = _token_set(
        " ".join(
            [
                task_intent,
                _text(current_owner_delta.get("display_intent")),
                _text(current_owner_delta.get("intent")),
                _text(current_owner_delta.get("capability_family")),
                " ".join(str(item) for item in list(current_owner_delta.get("capability_families") or [])),
            ]
        )
    )
    searchable = _token_set(
        " ".join(
            [
                _text(card.get("summary")),
                _text(card.get("when_to_use")),
                " ".join(str(item) for item in _mapping(card.get("discovery_hint")).get("aliases", [])),
                " ".join(str(item) for item in _mapping(card.get("discovery_hint")).get("capability_tags", [])),
            ]
        )
    )
    overlap = sorted(tokens & searchable)
    if overlap:
        score += min(len(overlap) * 8, 40)
        reasons.append("soft_token_overlap:" + ",".join(overlap[:6]))
    if _is_display_pack_adaptable_card(card) and {"display", "figure", "visual", "pack", "roc"} & tokens:
        score += 30
        reasons.append("display_pack_adaptable_baseline")
    if _text(card.get("card_kind")) == "owner_callable" and requested == _text(card.get("action_type")):
        score += 20
        reasons.append("owner_callable_priority")
    return score, reasons or ["low_signal_candidate"]


def _fit_policy(card: Mapping[str, Any], *, score: int, exact: bool) -> str:
    if score <= 0:
        return INSUFFICIENT_FIT
    if _is_display_pack_adaptable_card(card):
        return ADAPTABLE_BASELINE_POLICY
    if exact:
        return EXACT_CONTRACT_MATCH
    return SOFT_DISCOVERY_MATCH


def _has_exact_current_delta_match(
    card: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> bool:
    requested = _text(current_owner_delta.get("action_type") or current_owner_delta.get("action_id"))
    return bool(
        requested
        and requested
        in {
            _text(card.get("action_type")),
            _text(card.get("action_id")),
            _text(card.get("tool_id")),
        }
    )


def _candidate_next_safe_actions(
    card: Mapping[str, Any],
    *,
    missing_refs: list[str],
) -> list[dict[str, Any]]:
    if missing_refs:
        return [
            {
                "action": "collect_missing_refs",
                "missing_refs": list(missing_refs),
            },
            {
                "action": "load_tool_card",
                "tool_id": _text(card.get("tool_id")),
                **({"tool_mode": _text(card.get("tool_mode"))} if _text(card.get("tool_mode")) else {}),
            },
            {
                "action": "emit_typed_blocker_candidate",
                "when": "hard_gate_still_missing_refs",
            },
        ]
    return list(card.get("next_safe_actions") or [])


def _requires_for_card(card: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "input_refs": _required_refs_for_card(card),
        "allowed_writes": list(card.get("allowed_writes") or []),
        "owner_receipt_or_typed_blocker": bool(
            _mapping(card.get("closeout_contract")).get("requires_owner_receipt_or_typed_blocker")
            or _mapping(card.get("authority_boundary")).get(
                "owner_receipt_or_typed_blocker_required"
            )
        ),
    }


def _required_refs_for_card(card: Mapping[str, Any]) -> list[str]:
    return _dedupe([str(item) for item in list(card.get("required_refs") or card.get("input_refs") or [])])


def _extra_gate_refs(card: Mapping[str, Any]) -> list[str]:
    risk = _mapping(card.get("risk_annotations"))
    return [STAGE_ATTEMPT_REF] if bool(risk.get("requires_opl_stage_attempt_or_lease")) else []


def _missing_refs(required_refs: Sequence[str], available_refs: set[str]) -> list[str]:
    return [ref for ref in _dedupe([str(item) for item in required_refs]) if not _ref_available(ref, available_refs)]


def _ref_available(ref: str, available_refs: set[str]) -> bool:
    normalized = _normalize_ref(ref)
    if not normalized:
        return True
    if normalized in available_refs:
        return True
    return any(
        item.endswith("/" + normalized)
        or normalized.endswith("/" + item)
        for item in available_refs
    )


def _normalized_available_refs(values: Sequence[str] | None) -> set[str]:
    return {_normalize_ref(item) for item in list(values or []) if _normalize_ref(item)}


def _normalize_ref(value: object) -> str:
    text = _text(value).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.strip("/")


def _capability_tags(card: Mapping[str, Any]) -> list[str]:
    action_id = _text(card.get("action_id") or card.get("action_type"))
    tool_id = _text(card.get("tool_id"))
    summary = _text(card.get("summary"))
    tags: list[str] = []
    haystack = " ".join((action_id, tool_id, summary)).lower()
    if "display_pack" in haystack or "figure" in haystack or "visual" in haystack:
        tags.extend(["display_pack", "medical_display", "figure", "visual"])
    if "scientific_capability" in haystack or "external_learning" in haystack:
        tags.extend(["scientific_capability", "refs_only_capability"])
    if "study_progress" in haystack:
        tags.extend(["study_progress", "progress_projection"])
    if "authority" in haystack:
        tags.append("authority_operation")
    if "quality_repair" in haystack or "repair" in haystack:
        tags.extend(["quality_repair", "owner_callable"])
    if _text(card.get("card_kind")) == "owner_callable":
        tags.append("owner_callable")
    return _dedupe(tags)


def _examples_for_card(card: Mapping[str, Any]) -> list[dict[str, str]]:
    action = _text(card.get("action_id") or card.get("action_type") or card.get("tool_id"))
    if not action:
        return []
    return [
        {
            "current_owner_delta_field": "action_type",
            "value": action,
        }
    ]


def _is_display_pack_adaptable_card(card: Mapping[str, Any]) -> bool:
    return _text(card.get("tool_id")) == "display_pack_agent" or _text(card.get("action_id")).startswith(
        "display_pack_"
    )


def _current_owner_delta_summary(value: Mapping[str, Any]) -> dict[str, str]:
    return {
        "action_type": _text(value.get("action_type")),
        "action_id": _text(value.get("action_id")),
        "source_ref": _text(value.get("source_ref")),
        "work_unit_fingerprint": _text(value.get("work_unit_fingerprint")),
    }


def _token_set(value: str) -> set[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return {item for item in normalized.split() if len(item) >= 3}


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "ADAPTABLE_BASELINE_POLICY",
    "EXACT_CONTRACT_MATCH",
    "INSUFFICIENT_FIT",
    "SOFT_DISCOVERY_MATCH",
    "adaptation_policy_for_card",
    "attach_capability_invocation_os_fields",
    "capability_resolution_view",
    "capability_resolver_contract",
    "discovery_hint_for_action_card",
    "fit_signal_for_card",
    "invocation_gate_for_card",
    "resolve_capability_candidates_from_arsenal",
]
