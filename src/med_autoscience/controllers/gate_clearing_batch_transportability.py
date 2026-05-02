from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.profiles import WorkspaceProfile


LEGACY_DIRECT_MIGRATION_FEATURE_SHIFT_KEYS = frozenset(
    {
        "collapse_metrics_path",
        "feature_shift_csv_path",
        "risk_distribution_csv_path",
        "primary_driver",
    }
)
TRANSPORTABILITY_REQUIREMENT_KEY = "center_transportability_governance_summary_panel"
TRANSPORTABILITY_INPUT_SCHEMA_ID = "center_transportability_governance_summary_panel_inputs_v1"
TRANSPORTABILITY_INPUT_FILENAME = "center_transportability_governance_summary_panel_inputs.json"


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists() and _read_json(path) == payload:
        return False
    _write_json(path, payload)
    return True


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def transportability_reporting_contract_required(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any] | None:
    from med_autoscience.controllers import medical_reporting_contract as medical_reporting_contract_controller

    resolved_study_root = Path(study_root).expanduser().resolve()
    study_payload = _read_yaml(resolved_study_root / "study.yaml")
    if not study_payload:
        return None
    contract = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
        study_root=resolved_study_root,
        study_payload=study_payload,
        profile=profile,
    )
    if _non_empty_text(contract.get("status")) != "resolved":
        return None
    display_shell_plan = contract.get("display_shell_plan")
    if not isinstance(display_shell_plan, list):
        return None
    if any(
        isinstance(item, dict) and _non_empty_text(item.get("requirement_key")) == TRANSPORTABILITY_REQUIREMENT_KEY
        for item in display_shell_plan
    ):
        return contract
    return None


def legacy_feature_shift_f5_payload(*, paper_root: Path) -> tuple[Path, dict[str, Any]] | None:
    payload_path = Path(paper_root) / "multicenter_generalizability_inputs.json"
    payload = _read_json(payload_path)
    if str(payload.get("input_schema_id") or "").strip() != "multicenter_generalizability_inputs_v1":
        return None
    displays = payload.get("displays")
    if not isinstance(displays, list):
        return None
    for item in displays:
        if not isinstance(item, dict):
            continue
        present_feature_shift_keys = {
            key
            for key in LEGACY_DIRECT_MIGRATION_FEATURE_SHIFT_KEYS
            if _non_empty_text(item.get(key)) is not None
        }
        if present_feature_shift_keys:
            return payload_path, dict(item)
    return None


def _resolve_paper_payload_path(*, paper_root: Path, raw_path: object) -> Path | None:
    from med_autoscience.controllers import submission_minimal

    text = _non_empty_text(raw_path)
    if text is None:
        return None
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
        relocated = _relocate_legacy_runtime_path(candidate=resolved, paper_root=Path(paper_root))
        if relocated is not None:
            return relocated
        return resolved
    workspace_root = submission_minimal.workspace_root_from_paper_root(Path(paper_root))
    workspace_candidate = submission_minimal.resolve_relpath(workspace_root, text).expanduser().resolve()
    if workspace_candidate.exists():
        return workspace_candidate
    return (Path(paper_root).expanduser().resolve() / text).resolve()


def _relocate_legacy_runtime_path(*, candidate: Path, paper_root: Path) -> Path | None:
    text = str(candidate)
    marker = "/ops/med-the research workflow/runtime/quests/"
    replacement = "/ops/med-deepscientist/runtime/quests/"
    if marker not in text:
        return None
    relocated = Path(text.replace(marker, replacement)).expanduser().resolve()
    if relocated.exists():
        return relocated
    quest_marker = "/.ds/worktrees/"
    if quest_marker not in text:
        return None
    suffix = text.split(quest_marker, 1)[1]
    current_quest_root = _quest_root_from_paper_root(paper_root)
    quest_relocated = (current_quest_root / ".ds" / "worktrees" / suffix).expanduser().resolve()
    if quest_relocated.exists():
        return quest_relocated
    return None


def _quest_root_from_paper_root(paper_root: Path) -> Path:
    resolved = Path(paper_root).expanduser().resolve()
    parts = resolved.parts
    if ".ds" in parts:
        ds_index = parts.index(".ds")
        return Path(*parts[:ds_index])
    return resolved.parent


def _finite_number(value: object, *, default: float | None = None) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return default
    number = float(value)
    if not math.isfinite(number):
        return default
    return number


def _require_finite_number(payload: dict[str, Any], key: str, *, context: str) -> float:
    number = _finite_number(payload.get(key), default=None)
    if number is None:
        raise ValueError(f"{context} requires finite numeric `{key}`")
    return number


def _positive_number(value: object, *, default: float) -> float:
    number = _finite_number(value, default=None)
    if number is None or number <= 0.0:
        return default
    return number


def _require_probability(payload: dict[str, Any], key: str, *, context: str) -> float:
    number = _require_finite_number(payload, key, context=context)
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{context} requires probability `{key}` between 0 and 1")
    return number


def _event_count_from_rate(*, support_count: int, rate: float | None) -> int:
    if rate is None:
        return 0
    return max(0, min(support_count, int(round(support_count * max(0.0, min(1.0, rate))))))


def _transportability_verdict(
    *,
    c_index_delta: float | None,
    iqr_ratio: float,
    oe_ratio: float,
    max_shift: float,
) -> str:
    if iqr_ratio < 0.5 or oe_ratio > 1.5 or max_shift > 0.5:
        return "recalibration_required"
    if c_index_delta is not None and c_index_delta <= -0.1:
        return "context_dependent"
    return "stable"


def _transportability_metrics_summary(
    *,
    study_root: Path,
    metrics_payload: dict[str, Any],
) -> dict[str, Any]:
    embedded = metrics_payload.get("source_metrics_summary")
    if isinstance(embedded, dict) and embedded:
        return dict(embedded)
    summary_path = (
        Path(study_root).expanduser().resolve()
        / "analysis"
        / "clean_room_execution"
        / "20_transportability"
        / "metrics_summary.json"
    )
    summary_payload = _read_json(summary_path)
    if not summary_payload:
        raise ValueError("transportability F5 migration requires clean-room transportability metrics_summary.json")
    return summary_payload


def _build_transportability_governance_display_from_legacy_f5(
    *,
    study_root: Path,
    paper_root: Path,
    legacy_display: dict[str, Any],
    contract_item: dict[str, Any],
) -> dict[str, Any]:
    from med_autoscience.controllers import display_surface_materialization

    metrics_path = _resolve_paper_payload_path(paper_root=paper_root, raw_path=legacy_display.get("collapse_metrics_path"))
    if metrics_path is None or not metrics_path.exists():
        raise ValueError("transportability F5 migration requires collapse_metrics_path")
    metrics_payload = _read_json(metrics_path)
    if not metrics_payload:
        raise ValueError("transportability F5 migration requires readable collapse metrics JSON")
    metrics = dict(metrics_payload.get("metrics") or {}) if isinstance(metrics_payload.get("metrics"), dict) else {}
    if not metrics:
        raise ValueError("transportability F5 migration requires collapse metrics.metrics")
    source_metrics = _transportability_metrics_summary(study_root=study_root, metrics_payload=metrics_payload)
    discrimination = (
        dict(source_metrics.get("discrimination") or {})
        if isinstance(source_metrics.get("discrimination"), dict)
        else {}
    )
    calibration = (
        dict(source_metrics.get("calibration_drift") or {})
        if isinstance(source_metrics.get("calibration_drift"), dict)
        else {}
    )
    if not discrimination or not calibration:
        raise ValueError("transportability F5 migration requires discrimination and calibration_drift metrics")

    context = "transportability F5 migration"
    china_n = max(1, int(_require_finite_number(discrimination, "china_n", context=context)))
    nhanes_n = max(1, int(_require_finite_number(discrimination, "nhanes_n", context=context)))
    china_c = _require_probability(discrimination, "china_c_index", context=context)
    nhanes_c = _require_probability(discrimination, "nhanes_c_index", context=context)
    c_index_delta = nhanes_c - china_c
    iqr_ratio = _positive_number(
        _require_finite_number(metrics, "predicted_risk_iqr_ratio_nhanes_to_china", context=context),
        default=1.0,
    )
    max_shift = _require_probability(metrics, "dominant_shift_feature_abs_share", context=context)
    china_observed_rate = _require_probability(calibration, "china_observed_5y_rate", context=context)
    nhanes_observed_rate = _require_probability(calibration, "nhanes_observed_5y_rate", context=context)
    china_predicted_rate = _positive_number(
        calibration.get("china_predicted_mean_5y_risk", metrics.get("china_predicted_mean_5y_risk")),
        default=0.0,
    )
    nhanes_predicted_rate = _positive_number(
        calibration.get("nhanes_predicted_mean_5y_risk", metrics.get("nhanes_predicted_mean_5y_risk")),
        default=0.0,
    )
    if china_predicted_rate <= 0.0 or nhanes_predicted_rate <= 0.0:
        raise ValueError("transportability F5 migration requires positive predicted mean risks")
    china_oe = china_observed_rate / china_predicted_rate
    nhanes_oe = nhanes_observed_rate / nhanes_predicted_rate
    dominant_feature = _non_empty_text(metrics.get("dominant_shift_feature")) or _non_empty_text(
        legacy_display.get("primary_driver")
    )
    if dominant_feature is None:
        raise ValueError("transportability F5 migration requires a dominant shift feature")
    reviewer_takeaway = _non_empty_text(metrics_payload.get("reviewer_facing_takeaway"))
    nhanes_verdict = _transportability_verdict(
        c_index_delta=c_index_delta,
        iqr_ratio=iqr_ratio,
        oe_ratio=nhanes_oe,
        max_shift=max_shift,
    )
    nhanes_action = (
        "Require recalibration and bounded transportability wording before submission"
        if nhanes_verdict == "recalibration_required"
        else "Report as context-dependent external transportability evidence"
        if nhanes_verdict == "context_dependent"
        else "Retain as stable external transportability evidence"
    )
    return {
        "display_id": _non_empty_text(contract_item.get("display_id")) or "transportability_governance",
        "template_id": display_surface_materialization.display_registry.get_evidence_figure_spec(
            TRANSPORTABILITY_REQUIREMENT_KEY
        ).template_id,
        "catalog_id": _non_empty_text(contract_item.get("catalog_id")) or "F5",
        "paper_role": _non_empty_text(legacy_display.get("paper_role")) or "main_text",
        "title": _non_empty_text(legacy_display.get("title"))
        or "China-US transportability governance and attribution-shift boundary",
        "caption": _non_empty_text(legacy_display.get("caption"))
        or "Transportability governance summary built from audited feature-shift and calibration-drift evidence.",
        "metric_family": "discrimination",
        "metric_panel_title": "Transportability performance and support",
        "metric_x_label": "C-index",
        "metric_reference_value": china_c,
        "batch_shift_threshold": 0.20,
        "slope_acceptance_lower": 0.90,
        "slope_acceptance_upper": 1.10,
        "oe_ratio_acceptance_lower": 0.90,
        "oe_ratio_acceptance_upper": 1.10,
        "summary_panel_title": "Governance action",
        "centers": [
            {
                "center_id": "china_reference",
                "center_label": "China",
                "cohort_role": "Reference cohort",
                "support_count": china_n,
                "event_count": _event_count_from_rate(support_count=china_n, rate=china_observed_rate),
                "metric_estimate": china_c,
                "metric_lower": china_c,
                "metric_upper": china_c,
                "max_shift": 0.0,
                "slope": 1.0,
                "oe_ratio": china_oe,
                "verdict": "stable",
                "action": "Reference fit retained for manuscript contrast",
                "detail": "Reference cohort anchors the audited 5-year all-cause mortality risk surface.",
            },
            {
                "center_id": "nhanes_external",
                "center_label": "NHANES",
                "cohort_role": "External comparative population",
                "support_count": nhanes_n,
                "event_count": _event_count_from_rate(support_count=nhanes_n, rate=nhanes_observed_rate),
                "metric_estimate": nhanes_c,
                "metric_lower": nhanes_c,
                "metric_upper": nhanes_c,
                "max_shift": max_shift,
                "slope": iqr_ratio,
                "oe_ratio": nhanes_oe,
                "verdict": nhanes_verdict,
                "action": nhanes_action,
                "detail": reviewer_takeaway
                or f"{dominant_feature} dominated the feature-shift and score-compression evidence.",
            },
        ],
    }


def sync_transportability_reporting_surface(
    *,
    study_root: Path,
    paper_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any]:
    from med_autoscience.controllers import quest_hydration

    contract = transportability_reporting_contract_required(study_root=study_root, profile=profile)
    if contract is None:
        return {"status": "skipped", "reason": "study reporting contract does not require transportability F5"}
    legacy = legacy_feature_shift_f5_payload(paper_root=paper_root)
    reporting_contract_path = Path(paper_root) / "medical_reporting_contract.json"
    current_contract = _read_json(reporting_contract_path)
    legacy_contract_required = "multicenter_generalizability_overview" in {
        _non_empty_text(item.get("requirement_key"))
        for item in (current_contract.get("display_shell_plan") or [])
        if isinstance(item, dict)
    }
    if legacy is None and not legacy_contract_required:
        return {"status": "skipped", "reason": "transportability reporting surface already current"}
    legacy_input_path: Path | None = None
    legacy_display: dict[str, Any] = {}
    if legacy is not None:
        legacy_input_path, legacy_display = legacy
    written_files: list[str] = []
    if _write_json_if_changed(reporting_contract_path, contract):
        written_files.append(str(reporting_contract_path))
    written_files.extend(
        quest_hydration._write_display_surface_stubs(
            paper_root=Path(paper_root),
            reporting_contract=contract,
        )
    )
    display_shell_plan = contract.get("display_shell_plan") if isinstance(contract.get("display_shell_plan"), list) else []
    contract_item = next(
        (
            dict(item)
            for item in display_shell_plan
            if isinstance(item, dict) and _non_empty_text(item.get("requirement_key")) == TRANSPORTABILITY_REQUIREMENT_KEY
        ),
        {},
    )
    migrated = False
    if legacy_display:
        migrated_display = _build_transportability_governance_display_from_legacy_f5(
            study_root=Path(study_root),
            paper_root=Path(paper_root),
            legacy_display=legacy_display,
            contract_item=contract_item,
        )
        migrated_payload = {
            "schema_version": 1,
            "input_schema_id": TRANSPORTABILITY_INPUT_SCHEMA_ID,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "status": "materialized_from_legacy_feature_shift_f5",
            "displays": [migrated_display],
        }
        migrated_path = Path(paper_root) / TRANSPORTABILITY_INPUT_FILENAME
        if _write_json_if_changed(migrated_path, migrated_payload):
            written_files.append(str(migrated_path))
        migrated = True
    return {
        "status": "updated" if written_files or migrated else "current",
        "written_files": sorted(dict.fromkeys(written_files)),
        "legacy_feature_shift_f5_migrated": migrated,
        "legacy_input_path": str(legacy_input_path) if legacy_input_path is not None else None,
        "reporting_contract_path": str(reporting_contract_path),
    }


def transportability_reporting_surface_needs_sync(
    *,
    study_root: Path,
    paper_root: Path,
    profile: WorkspaceProfile,
) -> bool:
    contract = transportability_reporting_contract_required(study_root=study_root, profile=profile)
    if contract is None:
        return False
    if legacy_feature_shift_f5_payload(paper_root=paper_root) is not None:
        return True
    current_contract = _read_json(Path(paper_root) / "medical_reporting_contract.json")
    return current_contract != contract


def legacy_direct_migration_feature_shift_payload_present(
    *,
    paper_root: Path,
    input_schema_id: str,
    display_id: str,
    input_filename_by_schema_id: dict[str, str],
) -> bool:
    filename = input_filename_by_schema_id.get(input_schema_id)
    if filename is None:
        return False
    payload = _read_json(Path(paper_root) / filename)
    if str(payload.get("input_schema_id") or "").strip() != input_schema_id:
        return False
    displays = payload.get("displays")
    if not isinstance(displays, list):
        return False
    for item in displays:
        if not isinstance(item, dict):
            continue
        if str(item.get("display_id") or "").strip() != display_id:
            continue
        present_feature_shift_keys = {
            key
            for key in LEGACY_DIRECT_MIGRATION_FEATURE_SHIFT_KEYS
            if _non_empty_text(item.get(key)) is not None
        }
        if not present_feature_shift_keys:
            return False
        return not item.get("center_event_counts") and not item.get("coverage_panels")
    return False
