from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.publication_eval_record import PublicationEvalRecord

from .common import _optional_text


AI_REVIEWER_RESPONSE_RECORD_DIR = Path("artifacts") / "publication_eval" / "ai_reviewer_responses"
AI_REVIEWER_RESPONSE_RECORD_SURFACE = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
PUBLICATION_EVAL_LATEST_SURFACE = "artifacts/publication_eval/latest.json"
CONTROLLER_DECISIONS_LATEST_SURFACE = "artifacts/controller_decisions/latest.json"


def _record_timestamp(record_payload: Mapping[str, Any]) -> str:
    emitted_at = _optional_text(record_payload.get("emitted_at"))
    if emitted_at:
        try:
            parsed = datetime.fromisoformat(emitted_at.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _materialize_ai_reviewer_publication_eval_record(
    *,
    study_root: Path,
    record: PublicationEvalRecord,
) -> Path:
    payload = record.to_dict()
    record_dir = study_root / AI_REVIEWER_RESPONSE_RECORD_DIR
    record_dir.mkdir(parents=True, exist_ok=True)
    record_path = record_dir / f"{_record_timestamp(payload)}_publication_eval_record.json"
    record_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record_path.resolve()


def _normalize_publication_eval_record(record: PublicationEvalRecord | dict[str, Any]) -> PublicationEvalRecord:
    return record if isinstance(record, PublicationEvalRecord) else PublicationEvalRecord.from_payload(record)
