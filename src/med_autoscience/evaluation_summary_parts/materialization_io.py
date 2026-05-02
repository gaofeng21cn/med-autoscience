from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.study_charter import read_study_charter

from .refs_and_validation import (
    _build_promotion_gate_payload,
    _normalize_gate_report,
    _normalize_runtime_escalation_ref,
    _read_json_object,
    _required_mapping,
    resolve_evaluation_summary_ref,
    resolve_promotion_gate_ref,
    stable_evaluation_summary_path,
    stable_promotion_gate_path,
)


def read_promotion_gate(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    from . import materialization

    gate_path = materialization.resolve_promotion_gate_ref(study_root=study_root, ref=ref)
    payload = materialization._read_json_object(gate_path, label="promotion gate")
    return materialization._normalized_promotion_gate(payload)


def read_evaluation_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    from . import materialization

    summary_path = materialization.resolve_evaluation_summary_ref(study_root=study_root, ref=ref)
    payload = materialization._read_json_object(summary_path, label="evaluation summary")
    return materialization._normalized_evaluation_summary(payload, study_root=study_root)


def materialize_evaluation_summary_artifacts(
    *,
    study_root: Path,
    runtime_escalation_ref: str | Path | dict[str, Any],
    publishability_gate_report_ref: str | Path,
) -> dict[str, dict[str, str]]:
    from . import materialization

    resolved_study_root = Path(study_root).expanduser().resolve()
    publication_eval = materialization.read_publication_eval_latest(study_root=resolved_study_root)
    charter_context_ref = materialization._required_mapping(
        "publication eval",
        "charter_context_ref",
        publication_eval.get("charter_context_ref"),
    )
    charter_payload = materialization.read_study_charter(
        study_root=resolved_study_root,
        ref=charter_context_ref.get("ref"),
    )
    normalized_runtime_escalation_ref = materialization._normalize_runtime_escalation_ref(
        study_root=resolved_study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    gate_report_path = Path(publishability_gate_report_ref).expanduser()
    if gate_report_path.is_absolute():
        gate_report_path = gate_report_path.resolve()
    else:
        gate_report_path = (resolved_study_root / gate_report_path).resolve()
    gate_report = materialization._normalize_gate_report(gate_report_path)
    promotion_gate_payload = materialization._build_promotion_gate_payload(
        study_root=resolved_study_root,
        publication_eval=publication_eval,
        runtime_escalation_ref=normalized_runtime_escalation_ref,
        gate_report=gate_report,
    )
    promotion_gate_path = materialization.stable_promotion_gate_path(study_root=resolved_study_root)
    promotion_gate_path.parent.mkdir(parents=True, exist_ok=True)
    promotion_gate_path.write_text(
        json.dumps(materialization._normalized_promotion_gate(promotion_gate_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    promotion_gate_ref = {
        "gate_id": str(promotion_gate_payload["gate_id"]),
        "artifact_path": str(promotion_gate_path),
    }
    evaluation_summary_payload = materialization._build_evaluation_summary_payload(
        study_root=resolved_study_root,
        publication_eval=publication_eval,
        charter_payload=charter_payload,
        runtime_escalation_ref=normalized_runtime_escalation_ref,
        promotion_gate_ref=promotion_gate_ref,
        promotion_gate_payload=promotion_gate_payload,
    )
    evaluation_summary_path = materialization.stable_evaluation_summary_path(study_root=resolved_study_root)
    evaluation_summary_path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_summary_path.write_text(
        json.dumps(
            materialization._normalized_evaluation_summary(evaluation_summary_payload, study_root=resolved_study_root),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "evaluation_summary_ref": {
            "summary_id": str(evaluation_summary_payload["summary_id"]),
            "artifact_path": str(evaluation_summary_path),
        },
        "promotion_gate_ref": promotion_gate_ref,
    }
