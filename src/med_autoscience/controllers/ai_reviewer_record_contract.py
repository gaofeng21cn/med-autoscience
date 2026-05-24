from __future__ import annotations

from collections.abc import Mapping


def ai_reviewer_record_has_valid_evaluation_scope(record: Mapping[str, object]) -> bool:
    if "evaluation_scope" not in record:
        return True
    evaluation_scope = record.get("evaluation_scope")
    return isinstance(evaluation_scope, str) and evaluation_scope.strip() == "publication"


__all__ = ["ai_reviewer_record_has_valid_evaluation_scope"]
