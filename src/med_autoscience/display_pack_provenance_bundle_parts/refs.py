from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


PROVENANCE_INDEX_REF = "paper/build/provenance/figure_provenance_index.json"
PROVENANCE_BUNDLE_REF_PREFIX = "paper/build/provenance/figures"
PUBLICATION_MANIFEST_REF = "paper/build/display_pack_publication_manifest.json"
DISPLAY_PACK_LOCK_REF = "paper/build/display_pack_lock.json"
FIGURE_RENDER_RECEIPT_REF = "paper/figure_render_receipt.json"
FIGURE_VISUAL_AUDIT_RECEIPT_REF = "paper/figure_visual_audit_receipt.json"
FIGURE_POLISH_LIFECYCLE_REF = "paper/figure_polish_lifecycle.json"
FIGURE_WORKFLOW_PACKET_REF = "paper/figure_workflow_packet.json"
AGENT_TRACE_REFS_REF = "paper/build/provenance/agent_trace_refs.json"
_REF_SECTION_NAMES = (
    "source_surfaces",
    "code",
    "input",
    "output",
    "environment",
    "agent_trace",
    "reviews",
    "replay",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_figure_dir(figure_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in figure_id.strip())
    if not safe:
        raise ValueError("figure_id must be non-empty")
    return safe


def _workspace_ref(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.resolve().parent).as_posix()


def _split_ref_pointer(ref: str) -> tuple[str, str]:
    ref_text = str(ref or "").strip()
    if "#" not in ref_text:
        return ref_text, ""
    path_ref, pointer = ref_text.split("#", 1)
    return path_ref, f"#{pointer}"


def _resolve_ref_path(ref: str, *, paper_root: Path) -> Path:
    path_ref, _pointer = _split_ref_pointer(ref)
    path = Path(path_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _resolve_existing_ref_path(ref: str, *, paper_root: Path, repo_root: Path) -> Path:
    path_ref, _pointer = _split_ref_pointer(ref)
    path = Path(path_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    paper_candidate = _resolve_ref_path(path_ref, paper_root=paper_root)
    if paper_candidate.exists():
        return paper_candidate
    return (repo_root / path).resolve()


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _file_ref(
    ref: str,
    *,
    paper_root: Path,
    repo_root: Path,
    label: str,
    required: bool = True,
    include_sha256: bool = True,
    sha256_omitted_reason: str = "",
) -> dict[str, Any]:
    path_ref, pointer = _split_ref_pointer(ref)
    resolved = _resolve_existing_ref_path(path_ref, paper_root=paper_root, repo_root=repo_root)
    payload: dict[str, Any] = {
        "label": label,
        "ref": ref,
        "required": required,
    }
    if pointer:
        payload["json_pointer"] = pointer
    if not resolved.exists():
        return {
            **payload,
            "status": "missing",
            "reason": "path_not_found",
        }
    if not (_is_under(resolved, paper_root.parent) or _is_under(resolved, repo_root)):
        return {
            **payload,
            "status": "restricted",
            "restricted_locator": {
                "kind": "absolute_path_outside_paper_or_repo",
                "basename": resolved.name,
                "path_sha256": _sha256_text(str(resolved)),
            },
        }
    if not include_sha256:
        return {
            **payload,
            "status": "present",
            "path": str(resolved),
            "sha256_status": "omitted",
            "sha256_omitted_reason": sha256_omitted_reason or "hash_not_required_for_this_ref",
        }
    return {
        **payload,
        "status": "present",
        "path": str(resolved),
        "sha256": _sha256_file(resolved),
    }


def _ref_from_path(path: str, *, paper_root: Path) -> str:
    if not path:
        return ""
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        try:
            return _workspace_ref(candidate, paper_root=paper_root)
        except ValueError:
            return str(candidate)
    return path


def _list_file_refs(
    refs: list[str],
    *,
    paper_root: Path,
    repo_root: Path,
    label_prefix: str,
    required: bool = True,
) -> list[dict[str, Any]]:
    return [
        _file_ref(ref, paper_root=paper_root, repo_root=repo_root, label=f"{label_prefix}_{index}", required=required)
        for index, ref in enumerate(refs)
        if str(ref or "").strip()
    ]


def _figure_id(item: Mapping[str, Any]) -> str:
    return str(item.get("figure_id") or "").strip()


def _figures_by_id(payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    figures = payload.get("figures") if payload is not None else None
    if not isinstance(figures, list):
        return {}
    return {
        figure_id: dict(item)
        for item in figures
        if isinstance(item, Mapping) and (figure_id := _figure_id(item))
    }


def _global_surface_refs() -> list[tuple[str, str, bool]]:
    return [
        ("publication_manifest", PUBLICATION_MANIFEST_REF, False),
        ("display_pack_lock", DISPLAY_PACK_LOCK_REF, True),
        ("figure_render_receipt", FIGURE_RENDER_RECEIPT_REF, False),
        ("figure_visual_audit_receipt", FIGURE_VISUAL_AUDIT_RECEIPT_REF, True),
        ("figure_polish_lifecycle", FIGURE_POLISH_LIFECYCLE_REF, True),
        ("figure_workflow_packet", FIGURE_WORKFLOW_PACKET_REF, True),
    ]


def _template_lock_entry(
    *,
    display_pack_lock: Mapping[str, Any] | None,
    template_id: str,
) -> dict[str, Any]:
    packs = display_pack_lock.get("enabled_packs") if display_pack_lock is not None else []
    if not isinstance(packs, list):
        return {}
    for pack in packs:
        if not isinstance(pack, Mapping):
            continue
        templates = pack.get("templates")
        if not isinstance(templates, list):
            continue
        for template in templates:
            if not isinstance(template, Mapping):
                continue
            if template_id in {
                str(template.get("template_id") or ""),
                str(template.get("full_template_id") or ""),
            }:
                return dict(template)
    return {}


def _renderer_code_ref(
    *,
    render_result: Mapping[str, Any],
    paper_root: Path,
    repo_root: Path,
) -> dict[str, Any] | None:
    argv = render_result.get("argv")
    cwd_text = str(render_result.get("cwd") or "").strip()
    if not isinstance(argv, list) or not cwd_text:
        return None
    cwd = Path(cwd_text).expanduser()
    for token in argv:
        token_text = str(token or "").strip()
        if not token_text or token_text.startswith("-"):
            continue
        candidate = Path(token_text)
        if candidate.suffix not in {".R", ".py"}:
            continue
        resolved = candidate if candidate.is_absolute() else cwd / candidate
        return _file_ref(
            str(resolved),
            paper_root=paper_root,
            repo_root=repo_root,
            label="renderer_entrypoint_file",
            required=True,
        )
    return None


def _bundle_missing_refs(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for section_name in _REF_SECTION_NAMES:
        section = bundle.get(section_name)
        if not isinstance(section, Mapping):
            continue
        refs = section.get("refs")
        if not isinstance(refs, list):
            continue
        missing.extend(
            dict(item)
            for item in refs
            if isinstance(item, Mapping) and item.get("status") == "missing"
        )
    return missing


def _bundle_restricted_refs(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    restricted: list[dict[str, Any]] = []
    for section_name in _REF_SECTION_NAMES:
        section = bundle.get(section_name)
        if not isinstance(section, Mapping):
            continue
        refs = section.get("refs")
        if not isinstance(refs, list):
            continue
        restricted.extend(
            dict(item)
            for item in refs
            if isinstance(item, Mapping) and item.get("status") == "restricted"
        )
    return restricted


def _ref_values(refs: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for item in refs:
        ref = str(item.get("ref") or "").strip()
        if ref:
            values.append(ref)
    return values


def _hashes_from_refs(*sections: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    hashes: dict[str, dict[str, str]] = {}
    for refs in sections:
        for item in refs:
            ref = str(item.get("ref") or "").strip()
            digest = str(item.get("sha256") or "").strip()
            if not ref or not digest:
                continue
            key = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in ref)[:160]
            hashes[key or f"ref_{len(hashes)}"] = {"algorithm": "sha256", "value": digest}
    return hashes


def _issue(
    *,
    code: str,
    section: str,
    message: str,
    severity: str = "error",
    label: str = "",
    ref: str = "",
) -> dict[str, str]:
    payload = {
        "code": code,
        "severity": severity,
        "section": section,
        "message": message,
    }
    if label:
        payload["label"] = label
    if ref:
        payload["ref"] = ref
    return payload


def _dedupe_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for issue in issues:
        key = (
            str(issue.get("code") or ""),
            str(issue.get("section") or ""),
            str(issue.get("label") or ""),
            str(issue.get("ref") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def _expected_output_entries(
    rendered: Mapping[str, Any],
    *,
    paper_root: Path,
    repo_root: Path,
) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for artifact_kind, ref_key, hash_key in (
        ("png", "png_ref", "png_sha256"),
        ("pdf", "pdf_ref", "pdf_sha256"),
        ("layout_sidecar", "layout_sidecar_ref", "layout_sidecar_sha256"),
    ):
        ref = str(rendered.get(ref_key) or "").strip()
        expected_sha256 = str(rendered.get(hash_key) or "").strip()
        if not ref:
            expected.append(
                {
                    "artifact_kind": artifact_kind,
                    "label": f"expected_{artifact_kind}",
                    "ref": "",
                    "status": "missing",
                    "reason": "output_ref_missing",
                    "expected_sha256": expected_sha256,
                }
            )
            continue
        entry = _file_ref(
            ref,
            paper_root=paper_root,
            repo_root=repo_root,
            label=f"expected_{artifact_kind}",
        )
        observed_sha256 = str(entry.get("sha256") or "")
        status = str(entry.get("status") or "")
        if status == "present" and expected_sha256:
            status = "present" if observed_sha256 == expected_sha256 else "hash_mismatch"
        elif status == "present" and not expected_sha256:
            status = "missing_expected_hash"
        expected.append(
            {
                **entry,
                "artifact_kind": artifact_kind,
                "status": status,
                "expected_sha256": expected_sha256,
                "observed_sha256": observed_sha256,
            }
        )
    return expected


def _replay_status(
    *,
    render_result: Mapping[str, Any],
    replay_refs: list[dict[str, Any]],
    expected_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    argv = render_result.get("argv")
    cwd_text = str(render_result.get("cwd") or "").strip()
    entrypoint = str(render_result.get("entrypoint") or "").strip()
    request_ref = str(render_result.get("request_ref") or "").strip()
    if not isinstance(argv, list) or not argv:
        issues.append(
            _issue(
                code="missing_replay_command",
                section="replay",
                message="render_result.argv is missing; replay can only report a blocker",
            )
        )
    if not entrypoint:
        issues.append(
            _issue(
                code="missing_replay_command",
                section="replay",
                message="render_result.entrypoint is missing",
                severity="warning",
            )
        )
    if not cwd_text:
        issues.append(
            _issue(
                code="missing_replay_cwd",
                section="replay",
                message="render_result.cwd is missing",
            )
        )
    elif not Path(cwd_text).expanduser().exists():
        issues.append(
            _issue(
                code="missing_replay_cwd",
                section="replay",
                message="render_result.cwd does not exist",
                ref=cwd_text,
            )
        )
    request_ref_entries = [item for item in replay_refs if item.get("label") == "render_request"]
    if not request_ref:
        issues.append(
            _issue(
                code="missing_replay_request",
                section="replay",
                message="render_result.request_ref is missing",
            )
        )
    elif not request_ref_entries or any(item.get("status") != "present" for item in request_ref_entries):
        issues.append(
            _issue(
                code="missing_replay_request",
                section="replay",
                label="render_request",
                ref=request_ref,
                message="render request ref is not present",
            )
        )
    if not expected_outputs:
        issues.append(
            _issue(
                code="missing_output_ref",
                section="output",
                message="replay expected output refs are missing",
            )
        )
    for entry in expected_outputs:
        label = str(entry.get("label") or "")
        ref = str(entry.get("ref") or "")
        status = str(entry.get("status") or "")
        if status in {"missing", "restricted"}:
            issues.append(
                _issue(
                    code="missing_output_ref" if status == "missing" else "restricted_ref",
                    section="output",
                    label=label,
                    ref=ref,
                    message=f"expected output ref status is {status}",
                )
            )
        elif status == "missing_expected_hash":
            issues.append(
                _issue(
                    code="missing_output_hash",
                    section="output",
                    label=label,
                    ref=ref,
                    message="expected output hash is missing",
                )
            )
        elif status == "hash_mismatch":
            issues.append(
                _issue(
                    code="output_hash_mismatch",
                    section="output",
                    label=label,
                    ref=ref,
                    message="expected output hash does not match current ref",
                )
            )
    deduped = _dedupe_issues(issues)
    return {
        "mode": "refs_only_dry_run",
        "status": "pass" if not deduped else "blocked",
        "checked_at": _utc_now(),
        "checks": {
            "argv_present": isinstance(argv, list) and bool(argv),
            "cwd_present": bool(cwd_text),
            "cwd_exists": bool(cwd_text and Path(cwd_text).expanduser().exists()),
            "request_ref_present": bool(request_ref),
            "request_ref_exists": bool(request_ref_entries and all(item.get("status") == "present" for item in request_ref_entries)),
            "expected_output_count": len(expected_outputs),
            "expected_outputs_present": all(item.get("status") == "present" for item in expected_outputs),
        },
        "issue_codes": sorted({issue["code"] for issue in deduped}),
        "typed_issues": deduped,
    }


def _bundle_typed_issues(
    *,
    metadata: Mapping[str, Any],
    missing_refs: list[dict[str, Any]],
    restricted_refs: list[dict[str, Any]],
    replay_status: Mapping[str, Any],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = [
        dict(item)
        for item in replay_status.get("typed_issues", [])
        if isinstance(item, Mapping)
    ]
    agent_trace = metadata.get("agent_trace")
    if isinstance(agent_trace, Mapping) and not agent_trace.get("external_trace_refs"):
        issues.append(
            _issue(
                code="missing_agent_trace",
                section="agent_trace",
                message="no transcript or agent trace ref was declared",
                severity="warning",
            )
        )
    reviews = metadata.get("reviews")
    if isinstance(reviews, Mapping):
        visual_status = str(reviews.get("visual_audit_final_status") or "").strip()
        review_refs = reviews.get("refs") if isinstance(reviews.get("refs"), list) else []
        if not visual_status or any(isinstance(item, Mapping) and item.get("status") == "missing" for item in review_refs):
            issues.append(
                _issue(
                    code="missing_review",
                    section="reviews",
                    label="visual_audit",
                    ref=FIGURE_VISUAL_AUDIT_RECEIPT_REF,
                    message="visual review receipt is missing or lacks final status",
                )
            )
    for item in missing_refs:
        label = str(item.get("label") or "")
        ref = str(item.get("ref") or "")
        section = "source_surfaces"
        for section_name in _REF_SECTION_NAMES:
            section_payload = metadata.get(section_name)
            refs = section_payload.get("refs") if isinstance(section_payload, Mapping) else []
            if isinstance(refs, list) and item in refs:
                section = section_name
                break
        code = "missing_output_ref" if section == "output" else "missing_ref"
        if section == "replay" and label == "render_request":
            code = "missing_replay_request"
        if section == "reviews":
            code = "missing_review"
        issues.append(
            _issue(
                code=code,
                section=section,
                label=label,
                ref=ref,
                message="required ref is missing",
            )
        )
    for item in restricted_refs:
        issues.append(
            _issue(
                code="restricted_ref",
                section="restricted_refs",
                label=str(item.get("label") or ""),
                ref=str(item.get("ref") or ""),
                message="ref resolves outside the paper workspace or repo root",
            )
        )
    return _dedupe_issues(issues)


def _agent_trace_ref_specs(payload: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if payload is None:
        return []
    raw_refs = payload.get("refs") or payload.get("agent_trace_refs") or []
    if not isinstance(raw_refs, list):
        return []
    refs: list[dict[str, Any]] = []
    for index, item in enumerate(raw_refs):
        if isinstance(item, str):
            refs.append({"label": f"agent_trace_{index}", "ref": item, "required": False})
            continue
        if not isinstance(item, Mapping):
            continue
        ref = str(item.get("ref") or "").strip()
        if not ref:
            continue
        refs.append(
            {
                "label": str(item.get("label") or f"agent_trace_{index}").strip() or f"agent_trace_{index}",
                "ref": ref,
                "required": bool(item.get("required", False)),
            }
        )
    return refs
