from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any


EVIDENCE_PACKET_ALLOWED_KEYS = frozenset(
    {
        "ref",
        "role",
        "freshness",
        "owner",
        "receipt_id",
        "no_forbidden_write_proof",
    }
)
FORBIDDEN_PACKET_BODY_KEYS = frozenset(
    {
        "body",
        "payload",
        "memory_body",
        "artifact_body",
        "publication_verdict",
        "publication_verdict_body",
        "current_package",
        "current_package_body",
    }
)


def build_body_free_evidence_packet(
    *,
    ref: str | Path,
    role: str,
    owner: str,
    receipt_id: str | None = None,
    freshness: Mapping[str, Any] | None = None,
    no_forbidden_write_proof: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ref_text = _required_text("ref", ref)
    role_text = _required_text("role", role)
    owner_text = _required_text("owner", owner)
    packet = {
        "ref": ref_text,
        "role": role_text,
        "freshness": dict(freshness) if isinstance(freshness, Mapping) else freshness_for_ref(ref_text),
        "owner": owner_text,
        "receipt_id": _text(receipt_id) or receipt_id_for_ref(role=role_text, ref=ref_text),
        "no_forbidden_write_proof": dict(no_forbidden_write_proof)
        if isinstance(no_forbidden_write_proof, Mapping)
        else build_no_forbidden_write_proof(),
    }
    assert_body_free_evidence_packet(packet)
    return packet


def build_no_forbidden_write_proof(*, result: str = "body_free_ref_no_forbidden_write") -> dict[str, Any]:
    return {
        "result": result,
        "write_permitted": False,
        "forbidden_writes_performed": False,
        "domain_truth_write_performed": False,
        "memory_body_write_performed": False,
        "artifact_body_write_performed": False,
        "publication_verdict_write_performed": False,
        "current_package_write_performed": False,
    }


def freshness_for_ref(ref: str | Path) -> dict[str, Any]:
    ref_text = _text(ref)
    path = _local_path_for_ref(ref_text)
    if path is None or not path.exists():
        return {
            "status": "missing_or_external_ref",
            "exists": False,
            "mtime_epoch": None,
            "size_bytes": 0,
        }
    stat = path.stat()
    return {
        "status": "observed",
        "exists": True,
        "mtime_epoch": stat.st_mtime,
        "size_bytes": stat.st_size,
    }


def receipt_id_for_ref(*, role: str, ref: str) -> str:
    digest = hashlib.sha256(f"{role}\0{ref}".encode("utf-8")).hexdigest()[:16]
    return f"{role}:{digest}"


def assert_body_free_evidence_packet(packet: Mapping[str, Any]) -> None:
    keys = set(packet)
    if keys != EVIDENCE_PACKET_ALLOWED_KEYS:
        raise ValueError(
            "body-free evidence packet keys must be exactly "
            f"{sorted(EVIDENCE_PACKET_ALLOWED_KEYS)}; got {sorted(keys)}"
        )
    forbidden = sorted(_find_forbidden_body_keys(packet))
    if forbidden:
        raise ValueError(f"body-free evidence packet contains forbidden body fields: {forbidden}")
    proof = packet.get("no_forbidden_write_proof")
    if not isinstance(proof, Mapping):
        raise ValueError("body-free evidence packet requires a no-forbidden-write proof mapping")
    if proof.get("write_permitted") is not False or proof.get("forbidden_writes_performed") is not False:
        raise ValueError("body-free evidence packet must prove no forbidden writes were performed")


def _find_forbidden_body_keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_PACKET_BODY_KEYS:
                found.add(key_text)
            found.update(_find_forbidden_body_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_find_forbidden_body_keys(child))
    return found


def _local_path_for_ref(ref: str) -> Path | None:
    if not ref or "://" in ref or ref.startswith("${"):
        return None
    path = Path(ref).expanduser()
    if "#" in path.name:
        return None
    return path


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "EVIDENCE_PACKET_ALLOWED_KEYS",
    "assert_body_free_evidence_packet",
    "build_body_free_evidence_packet",
    "build_no_forbidden_write_proof",
    "freshness_for_ref",
    "receipt_id_for_ref",
]
