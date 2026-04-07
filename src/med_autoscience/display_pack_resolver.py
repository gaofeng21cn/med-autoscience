from __future__ import annotations


def split_full_template_id(full_template_id: str) -> tuple[str, str]:
    normalized = str(full_template_id or "").strip()
    if "::" not in normalized:
        raise ValueError("full template id must use '<pack_id>::<template_id>'")

    pack_id, template_id = normalized.split("::", 1)
    if not pack_id or not template_id:
        raise ValueError("full template id must use '<pack_id>::<template_id>'")
    return pack_id, template_id
