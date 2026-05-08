from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "docs" / "references" / "mds_webui_cleanroom_behavior_spec.md"
ORACLE_PATH = REPO_ROOT / "tests" / "fixtures" / "live_console" / "mds_webui_cleanroom_oracle.json"


def test_live_console_cleanroom_spec_has_behavior_oracle_without_old_code_identity() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(oracle, ensure_ascii=False)

    assert oracle["clean_room"] is True
    assert oracle["fixture_kind"] == "mds_webui_cleanroom_behavior_oracle"
    assert oracle["source_policy"] == {
        "imports_old_mds_code": False,
        "imports_old_webui_bundle": False,
        "contains_contributor_metadata": False,
        "contains_commit_history": False,
        "uses_old_product_identity": False,
    }
    assert "Do not copy old MDS React/WebUI source" in spec
    assert "MedDeepScientist" not in serialized
    assert "DeepScientist" not in serialized
    assert "author_email" not in serialized
    assert _find_forbidden_identity_refs(oracle) == []


def test_live_console_cleanroom_oracle_covers_required_stream_topics_and_authority_boundary() -> None:
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    required_topics = set(oracle["required_topics"])

    assert required_topics == {
        "workspace.status",
        "study.status",
        "runtime.health",
        "runtime.supervision",
        "terminal.tail",
        "log.tail",
        "artifact.delta",
    }
    assert {"workspace.status", "study.status", "terminal.tail"} <= {event["topic"] for event in oracle["events"]}
    for event in oracle["events"]:
        assert {"sequence", "topic", "status", "source_ref", "observed_at", "local_time"} <= set(event)
    assert "publication_eval/latest.json" in oracle["forbidden_writes"]
    assert "paper/current_package" in oracle["forbidden_writes"]


def _find_forbidden_identity_refs(value: object, path: str = "$") -> list[str]:
    forbidden_exact_keys = {
        "author",
        "author_name",
        "author_email",
        "commit",
        "commit_hash",
        "commit_sha",
        "contributor",
        "contributor_name",
        "contributor_email",
    }
    forbidden_value_markers = {
        "author_email",
        "commit_hash",
        "commit_sha",
        "contributor_email",
    }
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden_exact_keys:
                findings.append(child_path)
            findings.extend(_find_forbidden_identity_refs(item, child_path))
        return findings
    if isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_find_forbidden_identity_refs(item, f"{path}[{index}]"))
        return findings
    if isinstance(value, str) and any(marker in value for marker in forbidden_value_markers):
        findings.append(path)
    return findings
