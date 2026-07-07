from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


def freeze_contract_mapping(mapping: Mapping[str, tuple[str, ...]] | None) -> Mapping[str, tuple[str, ...]]:
    frozen = {str(key): tuple(value) for key, value in (mapping or {}).items()}
    return MappingProxyType(frozen)
