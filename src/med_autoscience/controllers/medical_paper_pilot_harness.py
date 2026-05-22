from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import real_workspace_soak_monitor


SCHEMA_VERSION = 1
SURFACE = "medical_paper_pilot_harness"
READ_MODEL = "medical_paper_pilot_harness_read_model"
PILOT_REF = Path("artifacts/medical_paper/medical_paper_pilot_harness.json")

REQUIRED_ARCHETYPES = (
    "prediction_model/external_validation",
    "observational_real_world",
    "subtype_or_triage",
)

PILOT_FIELDS = (
    "literature",
    "route_decision",
    "statistical_discipline",
    "stop_loss_switch_line",
    "authoring",
    "ai_reviewer",
    "soak",
    "finalize_rebuild",
)

FIELD_LABELS = {
    "literature": "文献理解",
    "route_decision": "路线裁决",
    "statistical_discipline": "统计纪律",
    "stop_loss_switch_line": "止损/换线",
    "authoring": "写作授权",
    "ai_reviewer": "AI reviewer",
    "soak": "真实 soak",
    "finalize_rebuild": "投稿包重建",
}

FIELD_NEXT_ACTIONS = {
    "literature": "补文献 scout、筛选理由和 citation ledger",
    "route_decision": "写入路线裁决 durable memo",
    "statistical_discipline": "处理统计 blocker 或机器可检查 waiver",
    "stop_loss_switch_line": "形成 stop-loss、switch-line 或 human gate memo",
    "authoring": "补目标期刊层、claim/display map 和 evidence/review ledger",
    "ai_reviewer": "补 AI reviewer provenance 和 recheck 记录",
    "soak": "运行真实/脱敏 workspace 只读 soak proof",
    "finalize_rebuild": "补 canonical-source-first finalize rebuild proof",
}

FIELD_ALIASES = {
    "literature": ("literature", "literature_scout", "literature_provider_runtime"),
    "route_decision": ("route_decision", "study_line_selection", "route_decision_orchestrator"),
    "statistical_discipline": (
        "statistical_discipline",
        "archetype_analysis_contract",
        "statistical_discipline_operations",
        "bounded_analysis_candidate_board",
    ),
    "stop_loss_switch_line": ("stop_loss_switch_line", "stop_loss_memo", "switch_line_memo"),
    "authoring": ("authoring", "authoring_runtime_authorization", "target_journal_writing_layer"),
    "ai_reviewer": (
        "ai_reviewer",
        "ai_reviewer_provenance",
        "revision_rebuttal_loop",
        "ai_reviewer_recheck",
    ),
    "soak": ("soak", "real_workspace_soak_monitor", "real_study_soak_matrix_evidence"),
    "finalize_rebuild": ("finalize_rebuild", "submission_package_rebuild", "current_package_rebuild"),
}


def authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_read_model_only",
        "read_model_only": True,
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def read_only_contract() -> dict[str, Any]:
    return {
        "mode": "read_only_pilot_harness",
        "writes_runtime_owned_surfaces": False,
        "writable_surfaces": [SURFACE],
        "prohibited_runtime_owned_surfaces": [
            "progress_projection",
            "domain_health_diagnostic",
            "publication_eval/latest.json",
            "runtime_escalation_record.json",
            "controller_decisions/latest.json",
            "quality_authorization",
            "submission_authorization",
            "finalize_authorization",
        ],
    }


def build_medical_paper_pilot_harness(
    *,
    study_roots: Sequence[Path | str] = (),
    catalog_payload: Mapping[str, Any] | None = None,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    catalog, catalog_ref = _read_catalog(catalog_payload=catalog_payload, catalog_path=catalog_path)
    soak = real_workspace_soak_monitor.build_real_workspace_soak_monitor(
        study_roots=study_roots,
        catalog_payload=catalog,
    )
    entries = _catalog_entries(catalog)
    study_items = [
        _pilot_study_payload(study=study, catalog=_catalog_by_study_id(entries).get(_text(study.get("study_id"))))
        for study in _sequence(soak.get("studies"))
        if isinstance(study, Mapping)
    ]
    missing_archetypes = [
        archetype
        for archetype in REQUIRED_ARCHETYPES
        if archetype not in {_text(study.get("study_archetype")) for study in study_items}
    ]
    status = _overall_status(study_items=study_items, missing_archetypes=missing_archetypes, soak=soak)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "monitor_mode": "read_only",
        "catalog_ref": catalog_ref,
        "overall_status": status,
        "summary": _summary(status=status, study_count=len(study_items), missing_archetypes=missing_archetypes),
        "required_archetypes": list(REQUIRED_ARCHETYPES),
        "covered_archetypes": sorted({_text(study.get("study_archetype")) for study in study_items if _text(study.get("study_archetype"))}),
        "missing_archetypes": missing_archetypes,
        "required_fields": list(PILOT_FIELDS),
        "next_action": _next_action(study_items=study_items, missing_archetypes=missing_archetypes, soak=soak),
        "pilot_studies": study_items,
        "soak_monitor": _compact_soak_monitor(soak),
        "durable_refs": _unique(
            ref
            for study in study_items
            for field in _sequence(study.get("fields"))
            if isinstance(field, Mapping)
            for ref in _sequence(field.get("durable_refs"))
        ),
        "authority_contract": authority_contract(),
        "read_only_contract": read_only_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def materialize_medical_paper_pilot_harness(
    *,
    study_roots: Sequence[Path | str] = (),
    catalog_payload: Mapping[str, Any] | None = None,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    projection = build_medical_paper_pilot_harness(
        study_roots=study_roots,
        catalog_payload=catalog_payload,
        catalog_path=catalog_path,
    )
    roots = [Path(root).expanduser().resolve() for root in study_roots if _text(root)]
    if not roots:
        roots = [
            Path(study["study_root"]).expanduser().resolve()
            for study in _sequence(projection.get("pilot_studies"))
            if isinstance(study, Mapping) and _text(study.get("study_root"))
        ]
    if not roots:
        raise ValueError("study_roots or catalog studies must include at least one study root")
    path = roots[0] / PILOT_REF
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "artifact_path": str(path.resolve()),
        "overall_status": projection["overall_status"],
        "next_action": projection["next_action"],
        "authority_contract": authority_contract(),
        "read_only_contract": read_only_contract(),
    }


def _pilot_study_payload(
    *,
    study: Mapping[str, Any],
    catalog: Mapping[str, Any] | None,
) -> dict[str, Any]:
    field_sources = _field_sources(study=study, catalog=catalog or {})
    fields = [_field_payload(field_key=field_key, source=field_sources.get(field_key, {})) for field_key in PILOT_FIELDS]
    status = _study_status(fields=fields, study=study)
    return {
        "study_id": _text(study.get("study_id")),
        "study_root": _text(study.get("study_root")),
        "study_archetype": _text(study.get("study_archetype")),
        "status": status,
        "next_action": _study_next_action(fields=fields, study=study),
        "fields": fields,
        "durable_refs": _unique(ref for field in fields for ref in _sequence(field.get("durable_refs"))),
        "route_action": _text(study.get("route_action"), "continue"),
        "result_strength": _text(study.get("result_strength"), "unknown"),
        "authority_contract": authority_contract(),
    }


def _field_payload(*, field_key: str, source: Mapping[str, Any]) -> dict[str, Any]:
    durable_refs = _durable_refs(source)
    status = _field_status(source=source, durable_refs=durable_refs)
    missing_reason = _text(source.get("missing_reason")) or ("" if status == "ready" else f"missing_{field_key}_durable_ref")
    return {
        "field_key": field_key,
        "label": FIELD_LABELS[field_key],
        "status": status,
        "missing_reason": missing_reason,
        "next_action": "continue_managed_execution" if status == "ready" else FIELD_NEXT_ACTIONS[field_key],
        "durable_refs": durable_refs,
        "why_it_matters": _why_it_matters(field_key),
        "authority_contract": authority_contract(),
    }


def _field_status(*, source: Mapping[str, Any], durable_refs: Sequence[str]) -> str:
    raw_status = _text(source.get("status") or source.get("overall_status"))
    if raw_status in {"ready", "present", "complete", "selected", "authorized"} and durable_refs:
        return "ready"
    if raw_status in {"partial", "planning"} or durable_refs:
        return "partial"
    return "blocked"


def _study_status(*, fields: Sequence[Mapping[str, Any]], study: Mapping[str, Any]) -> str:
    statuses = {_text(field.get("status")) for field in fields}
    if "blocked" in statuses or _text(study.get("status")) == "blocked":
        return "blocked"
    if "partial" in statuses or _text(study.get("status")) == "partial":
        return "partial"
    return "ready"


def _study_next_action(*, fields: Sequence[Mapping[str, Any]], study: Mapping[str, Any]) -> str:
    if _text(study.get("status")) in {"blocked", "partial"}:
        return _text(study.get("next_action"), "review_real_workspace_soak_gaps")
    for field in fields:
        if field.get("status") != "ready":
            return _text(field.get("next_action"), "review_pilot_harness_gap")
    return "continue_managed_execution"


def _field_sources(*, study: Mapping[str, Any], catalog: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    explicit = _mapping(catalog.get("pilot_fields") or catalog.get("research_loop_fields"))
    sources: dict[str, Mapping[str, Any]] = {}
    for field_key in PILOT_FIELDS:
        source = _lookup_field_source(explicit, field_key)
        if not source:
            source = _lookup_field_source(study, field_key)
        if not source and field_key == "soak":
            source = {
                "status": study.get("status"),
                "missing_reason": study.get("blocked_reason") or study.get("next_action"),
                "durable_refs": study.get("durable_refs"),
            }
        if not source and field_key == "finalize_rebuild" and study.get("finalize_rebuild_seen") is True:
            source = {"status": "ready", "durable_refs": study.get("durable_refs")}
        sources[field_key] = source
    return sources


def _lookup_field_source(source: Mapping[str, Any], field_key: str) -> Mapping[str, Any]:
    for alias in FIELD_ALIASES[field_key]:
        value = source.get(alias)
        if isinstance(value, Mapping):
            return value
        if isinstance(value, list | tuple):
            return {"status": "ready" if value else "blocked", "durable_refs": value}
    return {}


def _overall_status(
    *,
    study_items: Sequence[Mapping[str, Any]],
    missing_archetypes: Sequence[str],
    soak: Mapping[str, Any],
) -> str:
    statuses = {_text(study.get("status")) for study in study_items}
    if "blocked" in statuses:
        return "blocked"
    if "partial" in statuses or missing_archetypes or _text(soak.get("overall_status")) == "partial":
        return "partial"
    return "ready" if study_items and _text(soak.get("overall_status")) == "ready" else "blocked"


def _next_action(
    *,
    study_items: Sequence[Mapping[str, Any]],
    missing_archetypes: Sequence[str],
    soak: Mapping[str, Any],
) -> dict[str, str]:
    if missing_archetypes:
        return {
            "action_id": "add_missing_pilot_archetype",
            "summary": f"补齐 pilot archetype: {missing_archetypes[0]}",
            "study_id": "",
            "field_key": "",
        }
    for study in study_items:
        if study.get("status") in {"blocked", "partial"}:
            for field in _sequence(study.get("fields")):
                if isinstance(field, Mapping) and field.get("status") != "ready":
                    return {
                        "action_id": "repair_pilot_harness_field",
                        "summary": _text(field.get("next_action"), "review_pilot_harness_gap"),
                        "study_id": _text(study.get("study_id")),
                        "field_key": _text(field.get("field_key")),
                    }
            return {
                "action_id": "review_real_workspace_soak_gap",
                "summary": _text(study.get("next_action"), _text(soak.get("next_action"), "review_soak_gap")),
                "study_id": _text(study.get("study_id")),
                "field_key": "",
            }
    return {
        "action_id": "continue_managed_execution",
        "summary": "pilot harness 已证明三类 study 的自动论文闭环可监督。",
        "study_id": "",
        "field_key": "",
    }


def _compact_soak_monitor(soak: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": soak.get("surface"),
        "overall_status": soak.get("overall_status"),
        "next_action": soak.get("next_action"),
        "covered_archetypes": list(_sequence(soak.get("covered_archetypes"))),
        "missing_archetypes": list(_sequence(soak.get("missing_archetypes"))),
        "authority_contract": dict(_mapping(soak.get("authority_contract"))),
    }


def _read_catalog(
    *,
    catalog_payload: Mapping[str, Any] | None,
    catalog_path: Path | str | None,
) -> tuple[Mapping[str, Any], str]:
    if catalog_path is None:
        return catalog_payload or {}, ""
    path = Path(catalog_path).expanduser().resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, str(path)
    return payload if isinstance(payload, Mapping) else {}, str(path)


def _catalog_entries(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("studies", "study_catalog", "items"):
        entries = payload.get(key)
        if isinstance(entries, Mapping):
            return [
                {**entry, "study_id": entry.get("study_id") or str(study_id)}
                for study_id, entry in entries.items()
                if isinstance(entry, Mapping)
            ]
        if isinstance(entries, list | tuple):
            return [entry for entry in entries if isinstance(entry, Mapping)]
    return []


def _catalog_by_study_id(entries: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {_text(entry.get("study_id")): entry for entry in entries if _text(entry.get("study_id"))}


def _durable_refs(source: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("durable_refs", "evidence_refs", "ledger_refs", "source_refs", "required_calibration_refs"):
        refs.extend(_text(ref) for ref in _sequence(source.get(key)) if _text(ref))
    for key in ("durable_ref", "artifact_path", "controller_decision_ref", "rebuild_ref"):
        ref = _text(source.get(key))
        if ref:
            refs.append(ref)
    return _unique(refs)


def _why_it_matters(field_key: str) -> str:
    return {
        "literature": "文献决定研究空白是否真实存在，也决定 claim 能否进入目标期刊语境。",
        "route_decision": "路线裁决决定系统是在执行最强切入点，还是机械推进初始题目。",
        "statistical_discipline": "统计纪律保证每个分析服务 claim，避免 post-hoc 叙事和虚高证据。",
        "stop_loss_switch_line": "止损/换线防止弱路线继续堆分析，保护论文叙事诚实性。",
        "authoring": "写作授权把目标期刊、claim 段落和图表证据绑定起来。",
        "ai_reviewer": "AI reviewer provenance 是科学质量评估来源，机械 projection 不能替代。",
        "soak": "真实 soak 证明链路能在多类型 study 上长期可监督。",
        "finalize_rebuild": "投稿包重建证明交付物来自 canonical source，而不是手工 patch。",
    }[field_key]


def _summary(*, status: str, study_count: int, missing_archetypes: Sequence[str]) -> str:
    if missing_archetypes:
        return f"pilot harness {status}；{study_count} 个 study 已接入，仍缺 {len(missing_archetypes)} 类 study。"
    return f"pilot harness {status}；{study_count} 个 study 已覆盖三类自动论文闭环 proof。"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _text(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _unique(values: object) -> list[str]:
    result: list[str] = []
    for value in values or []:
        text = _text(value)
        if text and text not in result:
            result.append(text)
    return result


__all__ = [
    "PILOT_FIELDS",
    "PILOT_REF",
    "READ_MODEL",
    "REQUIRED_ARCHETYPES",
    "SURFACE",
    "authority_contract",
    "build_medical_paper_pilot_harness",
    "materialize_medical_paper_pilot_harness",
    "read_only_contract",
]
