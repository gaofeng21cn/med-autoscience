from __future__ import annotations

from collections.abc import Mapping
import shlex


def expand_subprocess_entrypoint(entrypoint: str, *, placeholders: Mapping[str, str]) -> list[str]:
    raw_argv = shlex.split(entrypoint)
    if not raw_argv:
        raise ValueError("subprocess display template entrypoint must not be empty")
    expanded: list[str] = []
    for token in raw_argv:
        expanded_token = token
        for placeholder, value in placeholders.items():
            expanded_token = expanded_token.replace("{" + placeholder + "}", value)
        if "{" in expanded_token or "}" in expanded_token:
            raise ValueError(f"unsupported subprocess renderer placeholder in `{entrypoint}`")
        expanded.append(expanded_token)
    return expanded


__all__ = ["expand_subprocess_entrypoint"]
