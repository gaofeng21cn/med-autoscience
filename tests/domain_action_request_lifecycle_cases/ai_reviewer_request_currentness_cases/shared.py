from __future__ import annotations

import hashlib
import json

from med_autoscience.controllers.domain_action_requests import (
    build_ai_reviewer_publication_eval_request,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    AI_REVIEWER_REQUIRED_INPUT_SURFACES,
    materialize_ai_reviewer_request,
    project_ai_reviewer_request_lifecycle,
    read_ai_reviewer_request,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

